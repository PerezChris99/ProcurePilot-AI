"""Deterministic buyer mandates and source-evidence eligibility."""
from datetime import datetime,timezone
from decimal import Decimal,InvalidOperation
from urllib.parse import urlsplit
from app.procurement.schemas import ProcurementRequirements


def source_timestamp():
    return datetime.now(timezone.utc).isoformat()


def requirements_for_request(request):
    policy=request.policy_json or {}
    return ProcurementRequirements(
        query=request.request_text, quantity=request.quantity,
        budget=request.budget, currency=request.currency,
        mandatory_attributes=policy.get('mandatory_attributes') or {},
        preferred_attributes=policy.get('preferred_attributes') or {},
    )


def policy_expired(request,*,now=None):
    raw=(request.policy_json or {}).get('expires_at')
    if not raw:
        return False
    try:
        expiry=datetime.fromisoformat(raw) if isinstance(raw,str) else raw
        if expiry.tzinfo is None:
            return True
        return expiry <= (now or datetime.now(timezone.utc))
    except (ValueError,TypeError):
        return True


def evaluate_offer(request,product,offer,*,now=None):
    """Return HARD policy violations. No LLM/text score is purchasing authority."""
    policy=request.policy_json or {}
    reasons=[]
    if policy_expired(request,now=now):
        reasons.append('Buyer mandate expired')
    expected=policy.get('mandatory_attributes') or {}
    attributes={
        str(key).strip().casefold():{str(v).strip().casefold()
            for v in (values if isinstance(values,list) else [values])}
        for key,values in (product.structured_attributes or {}).items()
    }
    for key,value in expected.items():
        if str(value).strip().casefold() not in attributes.get(str(key).strip().casefold(),set()):
            reasons.append('Required '+str(key)+' is not evidenced as '+str(value))
    url=urlsplit(str(offer.url))
    if url.scheme!='https' or not url.hostname or url.username or url.password:
        reasons.append('Offer URL must be a secure merchant link')
    allowed=policy.get('allowed_merchants') or []
    if allowed and not any(url.hostname and (
        url.hostname==domain or url.hostname.endswith('.'+domain)
    ) for domain in allowed):
        reasons.append('Merchant is not on the approved domain list')
    if offer.price.currency!=request.currency:
        reasons.append('Offer currency differs from request')
    if ''.join(c for c in offer.availability.casefold() if c.isalnum())!='instock':
        reasons.append('Stock is not confirmed')
    try:
        price=Decimal(str(offer.price.amount))
        if not price.is_finite() or price<=0:
            raise InvalidOperation()
        if policy.get('max_unit_price') is not None and price>Decimal(str(policy['max_unit_price'])):
            reasons.append('Unit price exceeds buyer mandate')
        if request.budget is not None and price*request.quantity>request.budget:
            reasons.append('Total exceeds purchasing budget')
    except (InvalidOperation,ValueError,TypeError):
        reasons.append('Price is missing or invalid')
    return reasons
