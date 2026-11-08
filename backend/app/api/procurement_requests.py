"""User-scoped procurement endpoints and evidence-first, budgeted AI orchestration."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session

from app.agents.budget import AiQuotaExceeded, reserve_ai_call
from app.agents.evidence import bounded_evidence_prompt, has_eligible_offer, provider_outage_assessment
from app.core.config import get_settings
from app.core.database import get_db
from app.integrations.channel3.client import (
    Channel3Client, Channel3ConfigurationError, Channel3Unavailable,
)
from app.integrations.channel3.schemas import Channel3Product
from app.models.procurement_request import ProcurementRequest
from app.models.user import User
from app.procurement.schemas import ProcurementRequirements
from app.procurement.scoring import rank_products
from app.procurement.policy import evaluate_offer, requirements_for_request, source_timestamp
from app.schemas.procurement_request import ProcurementRequestCreate, ProcurementRequestResponse
from app.security.tokens import get_current_user

router = APIRouter(prefix='/procurement-requests', tags=['procurement'])


def _owned_request(request_id: str, user: User, db: Session) -> ProcurementRequest:
    request = db.scalar(select(ProcurementRequest).where(
        ProcurementRequest.id == request_id,
        ProcurementRequest.user_id == user.id,
    ))
    if request is None:
        raise HTTPException(status_code=404, detail='Procurement request not found')
    return request


def _release_db_for_provider_io(db: Session, request: ProcurementRequest) -> None:
    """Do not hold a PostgreSQL transaction while an external API responds.

    The database sets idle_in_transaction_session_timeout=15s. Detach the
    fully loaded request before rolling back its read-only transaction so
    request fields remain available to the evidence/policy calculation. The
    endpoint re-fetches the owned row before saving the provider response.
    """
    db.expunge(request)
    db.rollback()


@router.post('', response_model=ProcurementRequestResponse, status_code=status.HTTP_201_CREATED)
def create_request(
    payload: ProcurementRequestCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    request = ProcurementRequest(
        user_id=user.id,
        request_text=payload.request_text,
        quantity=payload.quantity,
        budget=payload.budget,
        currency=payload.currency,
        policy_json=payload.policy_json.model_dump(mode='json',exclude_none=True),
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


@router.get('', response_model=list[ProcurementRequestResponse])
def list_requests(
    limit: int = Query(default=50, ge=1, le=100),
    include_analysis: bool = False,
    before_created_at: datetime | None = None,
    before_id: str | None = Query(default=None, max_length=36),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Keyset pagination and lean list rows keep large catalogue JSON off the hot path.

    Use GET /procurement-requests/{id} for the complete saved evidence. Clients
    needing legacy full list payloads may explicitly set include_analysis=true.
    """
    if (before_created_at is None) != (before_id is None):
        raise HTTPException(status_code=422,detail='Supply both before_created_at and before_id')
    columns=(
        ProcurementRequest.id,ProcurementRequest.request_text,
        ProcurementRequest.quantity,ProcurementRequest.budget,
        ProcurementRequest.currency,ProcurementRequest.status,ProcurementRequest.policy_json,
        ProcurementRequest.created_at,ProcurementRequest.updated_at,
    )
    query=(select(ProcurementRequest) if include_analysis else select(*columns)).where(
        ProcurementRequest.user_id==user.id,
    )
    if before_created_at is not None:
        query=query.where(or_(
            ProcurementRequest.created_at<before_created_at,
            and_(ProcurementRequest.created_at==before_created_at,
                 ProcurementRequest.id<before_id),
        ))
    query=query.order_by(ProcurementRequest.created_at.desc(),ProcurementRequest.id.desc()).limit(limit)
    if include_analysis:
        return db.scalars(query).all()
    return [{**dict(row._mapping),'analysis_json':None} for row in db.execute(query)]


@router.get('/{request_id}', response_model=ProcurementRequestResponse)
def get_request(
    request_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    request = _owned_request(request_id, user, db)
    _upgrade_legacy_snapshot(request, db)
    return request


def _snapshot_product_entry(item, request, by_id):
    """Evaluate each offer exactly once; reuse verdict for URL and UI reasons."""
    product = by_id[item.product_id]
    checks = [
        (str(offer.url), evaluate_offer(request, product, offer))
        for offer in product.offers
    ]
    return {
        'ranking': item.model_dump(mode='json'),
        'product': product.model_dump(mode='json'),
        'policy': {
            'eligible_offer_urls': [url for url, reasons in checks if not reasons],
            'offer_reasons': dict(checks[:30]),
        },
    }


_POLICY_VERSION = 2


def _upgrade_legacy_snapshot(request: ProcurementRequest, db: Session) -> None:
    """Revalidate cached offers when deterministic purchasing rules improve.

    Prevent old product/AI snapshots from continuing to claim affordability
    equals suitability after explicit monitor-diagonal checks were introduced.
    No provider calls or model quota are consumed by this one-time conversion.
    """
    previous = request.analysis_json or {}
    if previous.get('source') != 'Channel3' or previous.get('policy_version') == _POLICY_VERSION:
        return
    try:
        products = [
            Channel3Product.model_validate(entry['product'])
            for entry in previous.get('results', [])
        ]
        by_id = {product.id: product for product in products}
        rankings = rank_products(products, requirements_for_request(request))
        results = [_snapshot_product_entry(item, request, by_id) for item in rankings]
        updated = {**previous, 'results': results, 'policy_version': _POLICY_VERSION}
    except (ValidationError, KeyError, ValueError, TypeError):
        # Corrupted old evidence is not usable purchasing authority.
        updated = {**previous, 'results': [], 'policy_version': _POLICY_VERSION,
                   'next_page_available': False, 'next_page_token': None}
    # A pre-policy model comparison has no right to remain labelled current.
    for key in ('ai_explanation', 'ai_source', 'ai_model', 'ai_usage',
                'ai_prompt_characters', 'ai_retryable'):
        updated.pop(key, None)
    request.analysis_json = updated
    db.add(request)
    db.commit()
    db.refresh(request)


async def _catalogue_snapshot(request: ProcurementRequest, user_id: str, *, current=None, page_token=None):
    """Exactly one Channel3 call; deterministic ranking, no model tokens consumed."""
    requirements = requirements_for_request(request)
    try:
        page = await Channel3Client().search_products(
            requirements.query, limit=20, user_id=user_id, page_token=page_token
        )
    except Channel3ConfigurationError as exc:
        raise HTTPException(status_code=503, detail='Channel3 product discovery is not configured') from exc
    except Channel3Unavailable as exc:
        raise HTTPException(status_code=502, detail='Channel3 product discovery is temporarily unavailable') from exc

    previous = (current or {}).get('results', []) if page_token else []
    # Persistent snapshots must not grow indefinitely from repeated pagination.
    if len(previous)>=120:
        raise HTTPException(status_code=409,detail='Maximum saved catalogue results reached. Create a more specific request.')
    merged = {entry['product']['id']: entry['product'] for entry in previous}
    merged.update({product.id: product.model_dump(mode='json') for product in page.products})
    limited=list(merged.values())[:120]
    products = [Channel3Product.model_validate(entry) for entry in limited]
    rankings = rank_products(products, requirements)
    by_id = {product.id: product for product in products}
    return {
        'source': 'Channel3',
        'policy_version': _POLICY_VERSION,
        'discovered_at': source_timestamp(),
        'results': [
            _snapshot_product_entry(item, request, by_id)
            for item in rankings
        ],
        'next_page_available': page.next_page_token is not None and len(limited)<120,
        'next_page_token': page.next_page_token if len(limited)<120 else None,
    }


@router.post('/{request_id}/discover')
async def discover_products(
    request_id: str,
    next_page: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    request = _owned_request(request_id, user, db)
    current = request.analysis_json or {}
    page_token = current.get('next_page_token') if next_page else None
    if next_page and not page_token:
        raise HTTPException(status_code=409, detail='There is no additional catalogue page to load')
    user_id = user.id
    _release_db_for_provider_io(db, request)
    snapshot = await _catalogue_snapshot(
        request, user_id, current=current if next_page else {}, page_token=page_token
    )
    request = _owned_request(request_id, user, db)
    request.analysis_json = snapshot
    request.status = 'products_discovered'
    db.add(request)
    db.commit()
    db.refresh(request)
    return request.analysis_json


def _next_utc_day_seconds():
    now = datetime.now(timezone.utc)
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return max(1, int((tomorrow - now).total_seconds()))


@router.post('/{request_id}/analyze')
async def analyze_request(
    request_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    request = _owned_request(request_id, user, db)
    _upgrade_legacy_snapshot(request, db)
    current = request.analysis_json or {}

    # Repeated clicks and refreshes must not spend another model call on the same
    # saved evidence. Refreshing Channel3 deliberately invalidates this cache.
    if current.get('ai_explanation') and not current.get('ai_retryable'):
        return {
            'request_id': request.id, 'explanation': current['ai_explanation'],
            'status': request.status, 'cached': True,
            'source': current.get('ai_source', 'gemini'),
            'usage': current.get('ai_usage'),
        }

    # Discovery and analysis are separate, explicit user actions. The AI
    # endpoint must NEVER call the catalogue provider or mutate a request
    # merely because no search has occurred. This also avoids confusing
    # users when two differently-labelled buttons appear to do the same thing.
    if current.get('source') != 'Channel3':
        raise HTTPException(
            status_code=409,
            detail='Search products first to save catalogue evidence, then ask AI to analyze it.',
        )

    # A ranked product without any approved, confirmed in-stock offer is not
    # a payable recommendation. Deterministic policy explains this for zero
    # Gemini tokens, without hiding the catalogue's rejection evidence.
    if not current.get('results') or not has_eligible_offer(
        current['results'], request.currency,
    ):
        if not current.get('results'):
            explanation = (
                'Channel3 returned no catalogue products for this request. '
                'Try more specific product requirements or a different search. '
                'No product prices, inventory or delivery claims have been invented.'
            )
        else:
            explanation = (
                'No eligible, verified in-stock offer meets the current purchasing '
                'rules. Review the saved rejection reasons or refine the search. '
                'No purchase or payment is authorized by this assessment.'
            )
        request.analysis_json = {
            **current, 'ai_explanation': explanation,
            'ai_source': 'catalogue_only', 'ai_usage': None,
        }
        db.add(request)
        db.commit()
        return {
            'request_id': request.id, 'explanation': explanation, 'status': request.status,
            'cached': False, 'source': 'catalogue_only', 'usage': None,
        }

    # Lazy AI import keeps login, catalogue search and payments independent
    # from third-party model SDK startup.
    try:
        from app.agents import runtime
        from app.agents.runtime import AgentConfigurationError, AgentExecutionError
    except (ImportError, RuntimeError) as exc:
        raise HTTPException(
            status_code=503,
            detail='AI analysis service is unavailable. Saved catalogue results are unaffected.',
        ) from exc

    settings = get_settings()
    if not settings.google_api_key and not runtime.configured_fallbacks(settings):
        raise HTTPException(
            status_code=503,
            detail='No AI model provider is configured. Catalogue results remain available.',
        )

    try:
        prompt = bounded_evidence_prompt(
            request, current['results'],
            max_candidates=settings.ai_evidence_candidates,
            max_chars=getattr(settings, 'ai_max_prompt_chars', 3600),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail='The request evidence is too large to analyze') from exc
    try:
        reserve_ai_call(db, user.id, settings=settings)
    except AiQuotaExceeded as exc:
        limit = 'The global' if exc.scope == 'global' else 'Your'
        raise HTTPException(
            status_code=429,
            detail=f'{limit} daily AI analysis allowance is exhausted. Catalogue research and purchasing are still available.',
            headers={'Retry-After': str(_next_utc_day_seconds())},
        ) from exc

    try:
        # Each additional model provider attempt consumes another atomic
        # user/global daily allowance. No unaccounted fallback calls.
        if runtime.configured_fallbacks(settings):
            result = await runtime.run_evidence_analysis(
                user.id, prompt, on_fallback=lambda: reserve_ai_call(
                    db, user.id, settings=settings,
                ),
            )
        else:
            result = await runtime.run_evidence_analysis(user.id, prompt)
    except AiQuotaExceeded as exc:
        scope = 'App-wide' if exc.scope == 'global' else 'Your'
        raise HTTPException(
            status_code=429,
            detail=scope+' daily AI allowance reached before fallback. Saved offers remain available.',
            headers={'Retry-After': str(_next_utc_day_seconds())},
        ) from exc
    except AgentConfigurationError as exc:
        raise HTTPException(status_code=503, detail='The AI model provider is not configured') from exc
    except AgentExecutionError as exc:
        if exc.category in ('provider_unavailable', 'timeout', 'transport',
                            'quota_or_rate_limit'):
            # A provider outage cannot invalidate already verified catalogue
            # data. Surface a truthful non-AI comparison with a retry option.
            explanation = provider_outage_assessment(request, current['results'])
            request.analysis_json = {
                **current, 'ai_explanation': explanation,
                'ai_source': 'catalogue_only', 'ai_usage': None,
                'ai_retryable': True,
            }
            db.add(request)
            db.commit()
            return {
                'request_id': request.id, 'explanation': explanation,
                'status': request.status, 'cached': False,
                'source': 'catalogue_only', 'usage': None, 'retryable': True,
            }
        raise HTTPException(
            status_code=502,
            detail='AI provider authentication or model access failed. Review the integration configuration.',
        ) from exc

    request.analysis_json = {
        **current, 'ai_explanation': result['text'],
        'ai_source': result.get('provider','gemini'), 'ai_model': result['model'],
        'ai_usage': result['usage'], 'ai_prompt_characters': len(prompt),
        'ai_retryable': False,
    }
    db.add(request)
    db.commit()
    return {
        'request_id': request.id,
        'explanation': result['text'],
        'status': request.status,
        'cached': False, 'source': result.get('provider','gemini'), 'usage': result['usage'],
    }
