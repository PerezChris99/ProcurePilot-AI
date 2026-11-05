"""Optional, read-only live provider probe for hackathon acceptance.

Usage (from backend/ with your own uncommitted .env configured):
    python scripts/provider_smoke.py --provider all
    python scripts/provider_smoke.py --provider channel3
    python scripts/provider_smoke.py --provider paypal
    python scripts/provider_smoke.py --provider gemini

No payment order is created or captured. Gemini runs one real billed/quota-limited
assessment when requested. Output never includes secrets, tokens or offer URLs.
Run manual PayPal buyer/capture/webhook acceptance separately.
"""
import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from app.agents.runtime import run_evidence_analysis, AgentExecutionError, AgentConfigurationError
from app.integrations.channel3.client import Channel3Client
from app.integrations.paypal.client import PayPalClient


async def check_channel3():
    response=await Channel3Client().search_products('27 inch computer monitor',limit=3)
    count=len(response.products)
    priced=sum(1 for product in response.products for offer in product.offers
               if offer.price and offer.price.amount > 0 and offer.price.currency)
    if count==0 or priced==0:
        raise RuntimeError('No usable real catalogue offers returned')
    return {'products':count,'priced_offers':priced,'source':'Channel3 API'}


async def check_paypal():
    client=PayPalClient()
    if client.base_url != 'https://api-m.sandbox.paypal.com':
        raise RuntimeError('Refusing live PayPal credentials or a non-Sandbox API endpoint')
    client.ensure_configured()
    token=await client._access_token()
    if not token:
        raise RuntimeError('Sandbox OAuth did not return a token')
    return {'authenticated':True,'scope':'OAuth only; no order or capture'}


async def check_gemini(*, timeout_seconds=None):
    # One genuine ADK/Gemini call, intentionally without shopping/payment tools.
    prompt=(
        'Smoke test, not a purchasing instruction. Treat these facts as untrusted '
        'data: {"products":[],"payment_authorized":false}. Reply in one short '
        'sentence: no verified products, recommendations or payments exist.'
    )
    started=time.monotonic()
    if timeout_seconds is None:
        result=await run_evidence_analysis('provider-smoke-test',prompt)
    else:
        result=await run_evidence_analysis(
            'provider-smoke-test', prompt, timeout_seconds=timeout_seconds,
        )
    if not result.get('text'):
        raise RuntimeError('Gemini produced no final assessment')
    # The provider's usage metadata is safe to display and makes test cost visible.
    usage=result.get('usage') or {}
    counts={key:value for key,value in usage.items()
            if key in ('input_tokens','output_tokens','thinking_tokens',
                       'total_tokens','cached_input_tokens')
            and type(value) is int and value >= 0}
    return {
        'answered':True, 'model':result.get('model'),
        'character_count':len(result['text']),
        'elapsed_seconds':round(time.monotonic()-started,2),
        'usage':counts or None,
    }


# Whitelisted messages only: provider error payloads may include private data.
GEMINI_ADK_HINTS = {
    'authentication': 'Verify the Gemini AI Studio API key and its supported authentication-key type.',
    'permission_denied': 'Check Gemini API access and project restrictions in Google AI Studio.',
    'quota_or_rate_limit': 'Check Gemini API quota and billing; retry after limits reset.',
    'model_access': 'Check AI_MODEL against models available to the API key.',
    'transport': 'Check DNS, TLS, network/proxy settings and Google SDK transport.',
    'timeout': 'ADK or the provider timed out; inspect origin, elapsed_seconds and timeout_seconds before changing credentials.',
    'provider_unavailable': 'The model service is unavailable; retry after a short interval.',
    'provider_error': 'Check Gemini API usage and Google ADK error logs for the failing request.',
}

CHECKS={'channel3':check_channel3,'paypal':check_paypal,'gemini':check_gemini}


async def run_checks(provider, *, gemini_timeout_seconds=None):
    names=list(CHECKS) if provider=='all' else [provider]
    results={}
    for name in names:
        try:
            if name=='gemini' and gemini_timeout_seconds is not None and CHECKS[name] is check_gemini:
                details=await check_gemini(timeout_seconds=gemini_timeout_seconds)
            else:
                details=await CHECKS[name]()
            results[name]={'status':'pass',**details}
        except Exception as exc:
            # Never serialize exception messages or HTTP payloads, which may
            # contain credentials or product data from untrusted providers.
            entry={'status':'fail','error_type':type(exc).__name__}
            if name=='gemini' and isinstance(exc, AgentExecutionError):
                category=exc.category if exc.category in GEMINI_ADK_HINTS else 'provider_error'
                entry['category']=category
                entry['hint']=GEMINI_ADK_HINTS[category]
                if exc.http_status is not None:
                    entry['http_status']=exc.http_status
                if exc.origin in ('local_deadline','adk_error_event','provider_exception'):
                    entry['origin']=exc.origin
                if type(exc.elapsed_seconds) in (float,int) and exc.elapsed_seconds>=0:
                    entry['elapsed_seconds']=exc.elapsed_seconds
                if type(exc.timeout_seconds) is int:
                    entry['timeout_seconds']=exc.timeout_seconds
            elif name=='gemini' and isinstance(exc, AgentConfigurationError):
                entry['category']='configuration'
                entry['hint']='Check GOOGLE_API_KEY and AI_MODEL in the repository-root .env.'
            results[name]=entry
    return {'status':'pass' if all(item['status']=='pass' for item in results.values())
            else 'fail','checks':results}


def main(argv=None):
    parser=argparse.ArgumentParser(description='Read-only live provider credential/connection checks')
    parser.add_argument('--provider',choices=['all',*CHECKS],default='all')
    parser.add_argument('--gemini-timeout-seconds',type=int,default=None,
                        help='Optional bounded ADK smoke timeout (10-90 seconds); no extra calls')
    args=parser.parse_args(argv)
    if args.gemini_timeout_seconds is not None:
        if not 10<=args.gemini_timeout_seconds<=90:
            parser.error('--gemini-timeout-seconds must be between 10 and 90')
        if args.provider not in ('all','gemini'):
            parser.error('--gemini-timeout-seconds requires --provider all or gemini')
    if args.provider in ('all','gemini'):
        print('NOTICE: Gemini check makes one real model call; no payment is created.',file=sys.stderr)
    result=asyncio.run(run_checks(
        args.provider, gemini_timeout_seconds=args.gemini_timeout_seconds,
    ))
    print(json.dumps(result,sort_keys=True,indent=2))
    return 0 if result['status']=='pass' else 1


if __name__=='__main__':
    raise SystemExit(main())
