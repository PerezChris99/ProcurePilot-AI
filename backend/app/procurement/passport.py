"""Auditable, immutable-at-creation sourcing evidence and PayPal proof.

Snapshots are historical *provider claims*, not guaranteed price/stock truth.
No API keys, raw tracking URLs or buyer payment credentials appear in exports.
"""
from datetime import datetime,timezone
from decimal import Decimal,InvalidOperation
import hashlib
import json
from urllib.parse import urlsplit

from app.integrations.channel3.schemas import Channel3Product
from app.procurement.policy import evaluate_offer,source_timestamp


def _price(value):
    try:
        decimal=Decimal(str(value))
        return decimal if decimal.is_finite() and decimal>0 else None
    except (InvalidOperation,TypeError,ValueError):
        return None


def snapshot_for_order(request,product_id,offer_url):
    """Bound historical catalog evidence at PO creation; do not re-query on read."""
    data=request.analysis_json or {}
    collected=[]
    selected=None
    for entry in (data.get('results') or [])[:120]:
        product=Channel3Product.model_validate(entry['product'])
        for offer in product.offers[:30]:
            amount=_price(offer.price.amount)
            reasons=evaluate_offer(request,product,offer)
            record={
                'product_id':product.id[:255],
                'title':product.title[:180],
                'merchant':(offer.domain or urlsplit(str(offer.url)).hostname or '')[:100],
                'unit_price':str(amount) if amount is not None else None,
                'total_price':str(amount*request.quantity) if amount is not None else None,
                'currency':offer.price.currency,
                'availability':offer.availability,
                'eligible':not reasons,
                'blocked_by':reasons[:8],
            }
            if product.id==product_id and str(offer.url)==offer_url:
                selected=record
            if len(collected)<120:
                collected.append(record)
    if selected is None:
        raise ValueError('Selected offer was not in the saved Channel3 evidence')
    if not selected['eligible']:
        raise ValueError('Selected offer does not satisfy the purchasing policy')
    if selected not in collected:
        collected.append(selected)
    return {
        'format_version':1,
        'source':data.get('source','unknown'),
        'discovered_at':data.get('discovered_at'),
        'frozen_at':source_timestamp(),
        'request':{
            'id':request.id,
            'text':request.request_text[:1800],
            'quantity':request.quantity,
            'currency':request.currency,
            'budget':str(request.budget) if request.budget is not None else None,
        },
        'policy':request.policy_json or {},
        'selected':selected,
        'compared_offers':collected,
        'ai':{
            'source':data.get('ai_source'),
            'model':data.get('ai_model'),
            'explanation':str(data.get('ai_explanation') or '')[:3500],
            'usage':data.get('ai_usage'),
        },
        'limitations':[
            'Product and stock data are a historical Channel3 catalogue snapshot.',
            'Shipping, tax, delivery and merchant settlement are not verified.',
            'Gemini describes evidence; deterministic policies decide eligibility.',
            'PayPal Sandbox transfers no real money to a Channel3 retailer.',
        ],
    }


def build_passport(order,items,approvals,payment,events):
    """An owner-scoped endpoint supplies a historical proof record."""
    evidence=order.evidence_json or {}
    selected=evidence.get('selected') or {}
    candidates=evidence.get('compared_offers') or []
    suitable=[]
    for row in candidates:
        if row.get('eligible') and row.get('currency')==order.currency:
            amount=_price(row.get('unit_price'))
            if amount is not None:
                suitable.append((amount*int(evidence.get('request',{}).get('quantity') or 1),row))
    cheapest=min(suitable,key=lambda x:x[0]) if suitable else None
    chosen_total=_price(selected.get('total_price'))
    price_comparison={
        'eligible_offer_count':len(suitable),
        'least_cost_eligible_total':str(cheapest[0]) if cheapest else None,
        'least_cost_eligible_product':cheapest[1].get('product_id') if cheapest else None,
        'selected_total':str(chosen_total) if chosen_total is not None else str(order.total_amount),
        'premium_vs_least_cost':str(max(Decimal(0),chosen_total-cheapest[0]))
            if chosen_total is not None and cheapest else None,
        'note':'Compared only eligible same-currency snapshot offers; not realized savings. Shipping/tax excluded.',
    }
    timeline=[{
        'action':event.action,
        'at':event.created_at.isoformat(),
        'details':event.details or {},
    } for event in events]
    capture_recorded=any(row['action'] in (
        'payment.paypal_capture_completed','payment.webhook_capture_completed',
    ) for row in timeline)
    verified_webhook=any(row['action']=='payment.webhook_capture_completed' for row in timeline)
    payment_proof={
        'provider':'PayPal Sandbox (demo)',
        'status':payment.status if payment else 'not_started',
        'paypal_order_id':payment.paypal_order_id if payment else None,
        'capture_id':payment.capture_id if payment else None,
        'currency':payment.currency if payment else None,
        'amount':str(payment.amount) if payment else None,
        'captured_via_server':capture_recorded,
        'signed_webhook_correlated':verified_webhook,
        'retailer_settlement':False,
    }
    snapshot=json.dumps(evidence,sort_keys=True,separators=(',',':'),default=str).encode('utf-8')
    return {
        'version':1,
        'order_id':order.id,
        'order_number':order.po_number,
        'status':order.status,
        'created_at':order.created_at.isoformat(),
        'buyer_decision':{
            'approved_by_user_id':order.approved_by,
            'approved_at':order.approved_at.isoformat() if order.approved_at else None,
            'approval_model':'Personal workspace; self-approval permitted',
            'entries':[{
                'actor_user_id':record.actor_user_id,
                'decision':record.decision,
                'at':record.created_at.isoformat(),
                'comment':record.comment,
            } for record in approvals],
        },
        'evidence':evidence,
        'comparison':price_comparison,
        'payment_proof':payment_proof,
        'audit_timeline':timeline,
        'snapshot_sha256':hashlib.sha256(snapshot).hexdigest(),
        'integrity_note':'SHA-256 is an export checksum, not independent proof that database content is untampered.',
    }
