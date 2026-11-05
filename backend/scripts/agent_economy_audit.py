"""Offline and credential-free audit of the procurement evidence token envelope.

This script does not invoke Gemini, Channel3, PayPal or a database. Run from
the repository root with backend/.venv/Scripts/python.exe
backend/scripts/agent_economy_audit.py.
"""
import json
import sys
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agents.evidence import bounded_evidence_prompt, has_eligible_offer
from app.core.config import get_settings


def _entry(number, *, allowed):
    product_id = f'monitor-{number}'
    url = f'https://example.org/product/{product_id}'
    return {
        'product': {
            'id': product_id,
            'title': '27 inch office monitor - representative catalogue item',
            'offers': [
                {'url': url, 'domain': 'example.org', 'availability': 'InStock',
                 'price': {'amount': '125.00', 'currency': 'USD'}},
            ],
        },
        'ranking': {
            'score': '88.50', 'eligible': True, 'unmet_requirements': [],
        },
        'policy': {
            'eligible_offer_urls': [url] if allowed else [],
            'offer_reasons': {url: [] if allowed else ['Budget cap exceeded']},
        },
    }


def main():
    settings = get_settings()
    request = SimpleNamespace(
        request_text='Find two reliable 27-inch monitors within a USD 300 budget',
        quantity=2, budget=Decimal('300.00'), currency='USD',
    )
    # A mixed shortlist demonstrates retaining at least one genuinely eligible
    # product even if earlier products fail server-side offer policy checks.
    entries = [_entry(i, allowed=i == 7) for i in range(8)]
    prompt = bounded_evidence_prompt(
        request, entries,
        max_candidates=settings.ai_evidence_candidates,
        max_chars=settings.ai_max_prompt_chars,
    )
    json_text = prompt.split('\n', 1)[1]
    packet = json.loads(json_text)
    blocked = [_entry(i, allowed=False) for i in range(8)]
    result = {
        'type': 'offline_bound_check_not_provider_billing',
        'input_prompt_characters': len(prompt),
        'input_char_limit': settings.ai_max_prompt_chars,
        'shortlisted_candidates': len(packet['ranked_candidates']),
        'eligible_offer_in_shortlist': any(
            c['eligible'] for c in packet['ranked_candidates']
        ),
        'all_blocked_requires_gemini_call': has_eligible_offer(blocked, 'USD'),
        'max_analysis_llm_calls': 1,
        'max_output_tokens': settings.ai_max_output_tokens,
        'daily_user_call_limit': settings.ai_daily_user_runs,
        'daily_global_call_limit': settings.ai_daily_global_runs,
        'billing': 'Use real ADK response ai_usage; chars are not billed tokens.',
    }
    assert result['input_prompt_characters'] <= result['input_char_limit']
    assert result['eligible_offer_in_shortlist'] is True
    assert result['all_blocked_requires_gemini_call'] is False
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
