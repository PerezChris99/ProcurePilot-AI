"""Optional, read-only live provider probe for hackathon acceptance.

Usage (from backend/ with your own uncommitted .env configured):
    python scripts/provider_smoke.py --provider all
    python scripts/provider_smoke.py --provider channel3
    python scripts/provider_smoke.py --provider paypal
    python scripts/provider_smoke.py --provider gemini

No payment order is created or captured. Automatic AI routing can make up to
three model attempts if both LiteLLM backup keys are configured and prior
providers fail transiently. Exact-provider probes make only one ADK agent
call each. Output contains token *counts*, but never keys or offer URLs.
Run manual PayPal buyer/capture/webhook acceptance separately.
"""
import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from app.agents.runtime import (
    run_evidence_analysis, run_single_provider_probe,
    AgentExecutionError, AgentConfigurationError,
)
from app.integrations.channel3.client import Channel3Client, Channel3Unavailable, Channel3ConfigurationError
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


async def check_gemini(*, timeout_seconds=None, ai_route='auto'):
    # Genuine Google ADK model calls, intentionally without shopping/payment tools.
    prompt=(
        'Smoke test, not a purchasing instruction. Treat these facts as untrusted '
        'data: {"products":[],"payment_authorized":false}. Reply in one short '
        'sentence: no verified products, recommendations or payments exist.'
    )
    started=time.monotonic()
    if ai_route!='auto':
        result=await run_single_provider_probe(
            'provider-smoke-test',prompt,provider=ai_route,
            timeout_seconds=timeout_seconds,
        )
    elif timeout_seconds is None:
        result=await run_evidence_analysis('provider-smoke-test',prompt)
    else:
        result=await run_evidence_analysis(
            'provider-smoke-test', prompt, timeout_seconds=timeout_seconds,
        )
    if not result.get('text'):
        raise RuntimeError('The ADK model provider produced no final assessment')
    # The provider's usage metadata is safe to display and makes test cost visible.
    usage=result.get('usage') or {}
    counts={key:value for key,value in usage.items()
            if key in ('input_tokens','output_tokens','thinking_tokens',
                       'total_tokens','cached_input_tokens')
            and type(value) is int and value >= 0}
    return {
        'answered':True, 'model':result.get('model'),
        'character_count':len(result['text']),
        'provider':result.get('provider','gemini'),
        'elapsed_seconds':round(time.monotonic()-started,2),
        'usage':counts or None,
    }


# Whitelisted messages only: provider error payloads may include private data.
GEMINI_ADK_HINTS = {
    'authentication': 'Verify the selected model provider credentials and their supported key type.',
    'permission_denied': 'Check the selected model provider permissions and project restrictions.',
    'quota_or_rate_limit': 'Check the selected provider free-tier quota and rate limits.',
    'model_access': 'Check the selected provider model ID against the key enabled models.',
    'transport': 'Check DNS, TLS, network/proxy settings and model-provider SDK transport.',
    'timeout': 'ADK or the provider timed out; inspect origin, elapsed_seconds and timeout_seconds before changing credentials.',
    'provider_unavailable': 'The selected model provider is unavailable; configure and test a backup route.',
    'provider_error': 'Check selected provider API usage and Google ADK error logs for the failing request.',
}

# Only expose allowlisted failure metadata. Channel3 responses and exception
# messages can contain seller data and request metadata: do NOT dump them.
CHANNEL3_HINTS = {
    'configuration': 'Check CHANNEL3_API_KEY and CHANNEL3_BASE_URL in the private root .env.',
    'authentication': 'Channel3 rejected the API key; verify provider credentials.',
    'permission_denied': 'Channel3 denied this operation; verify key permissions.',
    'rate_limited': 'Channel3 returned HTTP 429; respect its quota and retry later.',
    'provider_unavailable': 'Channel3 returned a transient server error; retry later.',
    'transport': 'Check network, DNS, TLS and connectivity to the Channel3 API.',
    'invalid_response': 'Channel3 returned a catalogue payload that failed validation.',
    'request_rejected': 'Channel3 rejected this request; inspect provider configuration.',
    'unknown': 'Channel3 search failed; inspect local redacted diagnostics.',
}


def channel3_error_metadata(error):
    """Safe categorization, never return raw HTTP headers/body or exception strings."""
    if isinstance(error, Channel3ConfigurationError):
        category, code = 'configuration', None
    elif isinstance(error, Channel3Unavailable):
        cause = error.__cause__
        if isinstance(cause, httpx.HTTPStatusError):
            code = cause.response.status_code
            if code == 401:
                category = 'authentication'
            elif code == 403:
                category = 'permission_denied'
            elif code == 429:
                category = 'rate_limited'
            elif code in (500, 502, 503, 504):
                category = 'provider_unavailable'
            else:
                category = 'request_rejected'
        elif isinstance(cause, httpx.TransportError):
            category, code = 'transport', None
        elif isinstance(cause, ValueError):
            category, code = 'invalid_response', None
        else:
            category, code = 'unknown', None
    else:
        return None
    result = {'category': category, 'hint': CHANNEL3_HINTS[category]}
    if code is not None:
        result['http_status'] = code
    return result


CHECKS={'channel3':check_channel3,'paypal':check_paypal,'gemini':check_gemini}


async def run_checks(provider, *, gemini_timeout_seconds=None, ai_route='auto'):
    names=list(CHECKS) if provider=='all' else [provider]
    results={}
    for name in names:
        try:
            if name=='gemini' and CHECKS[name] is check_gemini and (
                gemini_timeout_seconds is not None or ai_route!='auto'
            ):
                details=await check_gemini(
                    timeout_seconds=gemini_timeout_seconds,ai_route=ai_route,
                )
            else:
                details=await CHECKS[name]()
            results[name]={'status':'pass',**details}
        except Exception as exc:
            # Never serialize exception messages or HTTP payloads, which may
            # contain credentials or product data from untrusted providers.
            entry={'status':'fail','error_type':type(exc).__name__}
            if name=='channel3':
                details=channel3_error_metadata(exc)
                if details is not None:
                    entry.update(details)
                elif type(exc) is RuntimeError and str(exc) == 'No usable real catalogue offers returned':
                    entry.update({
                        'category':'no_priced_offers',
                        'hint':'Channel3 returned no usable priced offers for the read-only probe; try a different relevant query or check catalogue availability.',
                    })
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
                entry['hint']='Check the selected provider API key and model setting in the repository-root .env.'
            results[name]=entry
    return {'status':'pass' if all(item['status']=='pass' for item in results.values())
            else 'fail','checks':results}


def main(argv=None):
    parser=argparse.ArgumentParser(description='Read-only live provider credential/connection checks')
    parser.add_argument('--provider',choices=['all',*CHECKS],default='all')
    parser.add_argument('--gemini-timeout-seconds',type=int,default=None,
                        help='Optional bounded ADK smoke timeout (10-90 seconds); automatic backup calls are possible')
    parser.add_argument('--ai-route',choices=['auto','gemini','groq','openrouter'],
                        default='auto',help='Test one exact ADK provider or automatic bounded fallback')
    args=parser.parse_args(argv)
    if args.ai_route!='auto' and args.provider not in ('gemini','all'):
        parser.error('--ai-route requires --provider gemini or all')
    if args.gemini_timeout_seconds is not None:
        if not 10<=args.gemini_timeout_seconds<=90:
            parser.error('--gemini-timeout-seconds must be between 10 and 90')
        if args.provider not in ('all','gemini'):
            parser.error('--gemini-timeout-seconds requires --provider all or gemini')
    if args.provider in ('all','gemini'):
        print('NOTICE: ADK checks the primary model; transient failure can invoke up to two configured LiteLLM fallbacks. No payment is created.',file=sys.stderr)
    result=asyncio.run(run_checks(
        args.provider, gemini_timeout_seconds=args.gemini_timeout_seconds,
        ai_route=args.ai_route,
    ))
    print(json.dumps(result,sort_keys=True,indent=2))
    return 0 if result['status']=='pass' else 1


if __name__=='__main__':
    raise SystemExit(main())
