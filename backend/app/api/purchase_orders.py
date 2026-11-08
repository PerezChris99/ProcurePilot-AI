from collections import defaultdict
import uuid,hashlib
from datetime import datetime,timezone
from decimal import Decimal,InvalidOperation
from fastapi import APIRouter,Depends,HTTPException,Query,status
from fastapi.responses import Response
from sqlalchemy import select,func,or_,and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.database import get_db
from app.integrations.paypal.client import PayPalClient,PayPalConfigurationError,PayPalUnavailable
from app.integrations.channel3.schemas import Channel3Product,Channel3Offer
from app.integrations.channel3.client import Channel3Client,Channel3ConfigurationError,Channel3Unavailable
from app.procurement.policy import evaluate_offer, policy_expired, snapshot_recent
from app.procurement.passport import build_passport,snapshot_for_order
from app.procurement.passport_pdf import passport_pdf_bytes
from app.models import Approval,AuditEvent,Payment,ProcurementRequest,PurchaseOrder,PurchaseOrderItem,User
from app.schemas.purchase_order import ApprovalAction,PayPalCheckoutResponse,PurchaseOrderCreate,PurchaseOrderResponse
from app.security.tokens import get_current_user

router=APIRouter(tags=['purchase orders and payments'])

def _owned_order(order_id,user,db):
    order=db.scalar(select(PurchaseOrder).where(PurchaseOrder.id==order_id,PurchaseOrder.user_id==user.id))
    if order is None: raise HTTPException(status_code=404,detail='Purchase order not found')
    return order

def _can_approve_order(order, actor_id):
    """One shared predicate for delegated vs default owner authorization."""
    return (order.assigned_approver_id or order.user_id)==actor_id


def _approval_order(order_id,user,db):
    """Only an explicitly appointed reviewer, or owner if unassigned, can decide."""
    order=db.scalar(select(PurchaseOrder).where(
        PurchaseOrder.id==order_id,
        or_(
            PurchaseOrder.assigned_approver_id==user.id,
            and_(PurchaseOrder.assigned_approver_id.is_(None),
                 PurchaseOrder.user_id==user.id),
        ),
    ))
    if order is None or not _can_approve_order(order,user.id):
        raise HTTPException(status_code=404,detail='Assigned approval not found')
    return order


def _audit(db,user_id,action,*,order_id=None,request_id=None,details=None):
    db.add(AuditEvent(user_id=user_id,purchase_order_id=order_id,request_id=request_id,action=action,details=details or {}))

def _merchant_fingerprint(client_id: str | None) -> str:
    """One-way server-only checkout binding to the PayPal REST app client ID.

    No client ID, secret or fingerprint is ever sent to the frontend. Changing
    REST apps never silently reuses an order previously issued to a seller.
    """
    return hashlib.sha256(('paypal-sandbox-merchant-v1:'+(client_id or '')).encode()).hexdigest()


def _current_checkout_merchant(payment, *, client_id=None) -> bool:
    evidence=payment.provider_response or {}
    if not isinstance(evidence, dict):
        return False
    known=evidence.get('merchant_fingerprint')
    current=_merchant_fingerprint(client_id if client_id is not None else get_settings().paypal_client_id)
    # Legacy checkouts are unbound and must NOT be trusted for replay after a
    # potential merchant rotation. Keep their evidence/audit trail intact.
    return isinstance(known,str) and known==current


def _payment_data(payment):
    if payment is None: return None
    merchant_current=_current_checkout_merchant(payment) if payment.paypal_order_id else True
    # Fail closed only for pending checkouts; paid evidence remains visible.
    unsafe=not merchant_current and payment.status!='completed'
    return {
        'id':payment.id,'provider':payment.provider,
        'paypal_order_id':payment.paypal_order_id,'capture_id':payment.capture_id,
        'status':payment.status,'amount':payment.amount,'currency':payment.currency,
        'approval_url':None if unsafe else payment.approval_url,
        'checkout_merchant_current':not unsafe,
        'created_at':payment.created_at,
    }

def _serialize(order,db):
    items=db.scalars(select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id==order.id)).all()
    approvals=db.scalars(select(Approval).where(Approval.purchase_order_id==order.id).order_by(Approval.created_at)).all()
    payment=db.scalar(select(Payment).where(Payment.purchase_order_id==order.id))
    events=db.scalars(select(AuditEvent).where(AuditEvent.purchase_order_id==order.id).order_by(AuditEvent.created_at)).all()
    return {'id':order.id,'po_number':order.po_number,'request_id':order.request_id,'assigned_approver_id':order.assigned_approver_id,'status':order.status,'currency':order.currency,'subtotal':order.subtotal,'total_amount':order.total_amount,'submitted_at':order.submitted_at,'approved_by':order.approved_by,'approved_at':order.approved_at,'rejection_reason':order.rejection_reason,'created_at':order.created_at,'updated_at':order.updated_at,'items':items,'approvals':approvals,'payment':_payment_data(payment),'audit_events':events,'offer_verification':order.offer_verification_json or None}

def _serialize_many(orders, db):
    """Load all order details in four bounded queries, not four per order."""
    if not orders:
        return []
    ids = [order.id for order in orders]
    item_map = defaultdict(list)
    for item in db.scalars(select(PurchaseOrderItem).where(
        PurchaseOrderItem.purchase_order_id.in_(ids)
    )):
        item_map[item.purchase_order_id].append(item)
    approval_map = defaultdict(list)
    for approval in db.scalars(select(Approval).where(
        Approval.purchase_order_id.in_(ids)
    ).order_by(Approval.created_at)):
        approval_map[approval.purchase_order_id].append(approval)
    payments = {
        payment.purchase_order_id: payment
        for payment in db.scalars(select(Payment).where(Payment.purchase_order_id.in_(ids)))
    }
    # List summaries retain only the latest 25 events per order. Individual
    # GET /purchase-orders/{id} preserves the full immutable audit history.
    ranked_events=select(
        AuditEvent.id.label('event_id'),
        func.row_number().over(
            partition_by=AuditEvent.purchase_order_id,
            order_by=(AuditEvent.created_at.desc(),AuditEvent.id.desc()),
        ).label('rn'),
    ).where(AuditEvent.purchase_order_id.in_(ids)).subquery()
    event_map = defaultdict(list)
    for event in db.scalars(select(AuditEvent).join(
        ranked_events,AuditEvent.id==ranked_events.c.event_id,
    ).where(ranked_events.c.rn<=25).order_by(AuditEvent.created_at)):
        event_map[event.purchase_order_id].append(event)
    return [
        {
            'id': order.id, 'po_number': order.po_number, 'request_id': order.request_id,
            'assigned_approver_id':order.assigned_approver_id,
            'status': order.status, 'currency': order.currency,
            'subtotal': order.subtotal, 'total_amount': order.total_amount,
            'submitted_at': order.submitted_at, 'approved_by': order.approved_by,
            'approved_at': order.approved_at, 'rejection_reason': order.rejection_reason,
            'created_at': order.created_at, 'updated_at': order.updated_at,
            'items': item_map[order.id], 'approvals': approval_map[order.id],
            'payment': _payment_data(payments.get(order.id)),
            'offer_verification': order.offer_verification_json or None,
            'audit_events': event_map[order.id],
        }
        for order in orders
    ]


def _paypal_order_matches(payload,order,payment):
    """Strictly verify an existing PayPal order BEFORE capturing any funds.

    GET /v2/checkout/orders/{id} is the source of the original custom_id and
    order amount. Never weaken this identity and total check to accommodate
    the differently shaped POST /capture response.
    """
    if not isinstance(payload,dict) or payload.get('id')!=payment.paypal_order_id or payload.get('status') not in ('APPROVED','COMPLETED'):
        return False
    units=payload.get('purchase_units') or []
    if not isinstance(units,list) or len(units)!=1 or not isinstance(units[0],dict):
        return False
    unit=units[0]; amount=unit.get('amount') or {}
    if not isinstance(amount,dict): return False
    try:
        value=Decimal(str(amount.get('value')))
        if not value.is_finite(): return False
    except (InvalidOperation,ValueError,TypeError): return False
    return unit.get('custom_id')==order.id and amount.get('currency_code')==order.currency and value==Decimal(order.total_amount)


def _paypal_completed_capture(payload,order,payment):
    """Validate actual capture evidence, NOT a copy of the order creation body.

    PayPal's POST /capture response commonly omits purchase-unit custom_id
    and original amount; GET /orders/{id} was already strictly matched above.
    Any metadata present in the capture response must still match, and a
    single COMPLETED capture with an exact amount/currency is mandatory.
    """
    if not isinstance(payload,dict) or payload.get('id')!=payment.paypal_order_id or payload.get('status')!='COMPLETED':
        return None
    units=payload.get('purchase_units')
    if not isinstance(units,list) or len(units)!=1 or not isinstance(units[0],dict):
        return None
    unit=units[0]
    if 'custom_id' in unit and unit['custom_id']!=order.id: return None
    if 'reference_id' in unit and unit['reference_id'] not in (order.po_number,'default'):
        return None
    if 'amount' in unit:
        amount=unit['amount']
        if not isinstance(amount,dict) or amount.get('currency_code')!=order.currency:
            return None
        try:
            original=Decimal(str(amount.get('value')))
            if not original.is_finite() or original!=Decimal(order.total_amount):
                return None
        except (InvalidOperation,ValueError,TypeError):
            return None
    payments=unit.get('payments') or {}
    if not isinstance(payments,dict): return None
    captures=payments.get('captures')
    if not isinstance(captures,list) or len(captures)!=1 or not isinstance(captures[0],dict):
        return None
    capture=captures[0]
    if capture.get('status')!='COMPLETED' or not PayPalClient.is_valid_order_id(capture.get('id')):
        return None
    if payment.capture_id and payment.capture_id!=capture['id']:
        return None
    amount=capture.get('amount')
    if not isinstance(amount,dict) or amount.get('currency_code')!=order.currency:
        return None
    try:
        value=Decimal(str(amount.get('value')))
        if not value.is_finite() or value!=Decimal(order.total_amount):
            return None
    except (InvalidOperation,ValueError,TypeError):
        return None
    return capture


def _paypal_capture_response_noncontradictory(payload,order,payment):
    """Only missing capture details permit a read-only GET reconciliation.

    Explicit mismatches in the POST response cannot be excused by a second
    response. Fail closed on any conflicting order ID, PO ref, price, or
    capture amount; never issue a second POST to 'fix' a response mismatch.
    """
    if not isinstance(payload,dict) or payload.get('id')!=payment.paypal_order_id or payload.get('status')!='COMPLETED':
        return False
    units=payload.get('purchase_units')
    if not isinstance(units,list) or len(units)!=1 or not isinstance(units[0],dict):
        return False
    unit=units[0]
    if 'custom_id' in unit and unit['custom_id']!=order.id: return False
    if 'reference_id' in unit and unit['reference_id'] not in (order.po_number,'default'):
        return False
    if 'amount' in unit:
        amount=unit['amount']
        if not isinstance(amount,dict) or amount.get('currency_code')!=order.currency:
            return False
        try:
            value=Decimal(str(amount.get('value')))
            if not value.is_finite() or value!=Decimal(order.total_amount):
                return False
        except (InvalidOperation,ValueError,TypeError):
            return False
    payments=unit.get('payments') or {}
    if not isinstance(payments,dict): return False
    captures=payments.get('captures')
    if captures is None: return True  # No capture details; GET can supply them.
    if not isinstance(captures,list) or len(captures)!=1 or not isinstance(captures[0],dict):
        return False
    capture=captures[0]
    if capture.get('status') not in (None,'COMPLETED'): return False
    if 'id' in capture:
        if not PayPalClient.is_valid_order_id(capture['id']): return False
        if payment.capture_id and capture['id']!=payment.capture_id: return False
    if 'amount' in capture:
        amount=capture['amount']
        if not isinstance(amount,dict) or amount.get('currency_code')!=order.currency:
            return False
        try:
            value=Decimal(str(amount.get('value')))
            if not value.is_finite() or value!=Decimal(order.total_amount):
                return False
        except (InvalidOperation,ValueError,TypeError):
            return False
    return True

@router.post('/procurement-requests/{request_id}/purchase-orders',status_code=status.HTTP_201_CREATED,response_model=PurchaseOrderResponse)
def create_purchase_order(request_id:str,payload:PurchaseOrderCreate,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    request=db.scalar(select(ProcurementRequest).where(ProcurementRequest.id==request_id,ProcurementRequest.user_id==user.id))
    if request is None: raise HTTPException(status_code=404,detail='Procurement request not found')
    snapshot=request.analysis_json or {}
    if not snapshot_recent(snapshot):
        raise HTTPException(status_code=409,detail='Channel3 evidence is missing or older than 24 hours. Refresh product discovery before creating a purchase order.')
    matches=[entry for entry in snapshot.get('results',[]) if entry.get('product',{}).get('id')==payload.product_id]
    if not matches: raise HTTPException(status_code=409,detail='Product is not in this request’s saved Channel3 results. Refresh discovery before creating an order.')
    result=matches[0]; ranking=result.get('ranking') or {}; product=result.get('product') or {}
    if ranking.get('unmet_requirements'): raise HTTPException(status_code=422,detail='This product does not evidence all mandatory requirements and cannot be ordered.')
    offer=next((entry for entry in product.get('offers',[]) if entry.get('url')==payload.offer_url),None)
    if not offer: raise HTTPException(status_code=409,detail='The selected retailer offer is not in the saved product snapshot.')
    reasons=evaluate_offer(request,Channel3Product.model_validate(product),Channel3Offer.model_validate(offer))
    if reasons:
        raise HTTPException(status_code=422,detail='Offer blocked by purchasing policy: '+ '; '.join(reasons[:4]))
    price=offer.get('price') or {}
    if price.get('currency')!=request.currency: raise HTTPException(status_code=422,detail='The selected offer currency does not match the procurement request.')
    if not payload.offer_url.startswith('https://'): raise HTTPException(status_code=422,detail='Retailer offer links must use HTTPS.')
    availability=''.join(char for char in str(offer.get('availability','')).casefold() if char.isalnum())
    if availability!='instock': raise HTTPException(status_code=422,detail='The selected retailer offer is not confirmed in stock.')
    try:
        raw_price=Decimal(str(price.get('amount')))
        if not raw_price.is_finite():
            raise InvalidOperation('Non-finite provider price')
        unit_price=raw_price.quantize(Decimal('0.01'))
        total=(unit_price*request.quantity).quantize(Decimal('0.01'))
    except (InvalidOperation,ValueError,TypeError,OverflowError) as exc:
        raise HTTPException(status_code=422,detail='The selected offer has no valid finite currency amount.') from exc
    if unit_price<=0:
        raise HTTPException(status_code=422,detail='The selected offer price must be greater than zero.')
    if total>Decimal('999999999999.99'):
        raise HTTPException(status_code=422,detail='Order amount exceeds the supported currency range.')
    if request.budget is not None and total>request.budget: raise HTTPException(status_code=422,detail='The selected offer exceeds the procurement budget.')
    approver_email=(request.policy_json or {}).get('approver_email')
    approver_id=None
    if approver_email:
        approver=db.scalar(select(User).where(User.email==approver_email,User.is_active.is_(True)))
        if approver is None:
            raise HTTPException(status_code=422,detail='Independent approver must have a registered active account before ordering.')
        if approver.id==user.id:
            raise HTTPException(status_code=422,detail='For independent approval, select another registered account.')
        approver_id=approver.id
    evidence_snapshot=snapshot_for_order(request,payload.product_id,payload.offer_url)
    po_id=str(uuid.uuid4()); now=datetime.now(timezone.utc)
    order=PurchaseOrder(id=po_id,po_number='PP-'+now.strftime('%Y%m%d')+'-'+po_id[:8].upper(),user_id=user.id,assigned_approver_id=approver_id,request_id=request.id,status='draft',currency=request.currency,subtotal=total,total_amount=total,evidence_json=evidence_snapshot)
    po_item=PurchaseOrderItem(purchase_order_id=po_id,product_id=product['id'],product_title=product.get('title') or 'Catalogue product',merchant=offer.get('domain') or 'Retailer not specified',offer_url=payload.offer_url,quantity=request.quantity,unit_price=unit_price,line_total=total,currency=request.currency,product_snapshot=product)
    # Persist the parent first: the audit and item objects use raw FK IDs, not
    # ORM relationships, so SQLAlchemy cannot always order their inserts.
    # Flush stays within this transaction; any later failure rolls it all back.
    db.add(order)
    db.flush()
    db.add(po_item)
    _audit(db,user.id,'purchase_order.created',order_id=po_id,request_id=request.id,details={'po_number':order.po_number,'amount':str(total),'currency':request.currency,'channel3_product_id':product['id']})
    db.commit(); db.refresh(order)
    return _serialize(order,db)

@router.get('/purchase-orders',response_model=list[PurchaseOrderResponse])
def list_purchase_orders(
    limit: int = Query(default=50, ge=1, le=100),
    status_filter: str | None = Query(
        default=None,
        alias="status",
        pattern=r"^(draft|pending_approval|approved|rejected|payment_pending|payment_failed|paid)$",
    ),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if status_filter=='pending_approval':
        # Delegates can inspect only POs awaiting their own decision, not owner
        # payments or unrelated history; owners still view their own orders.
        owner_or_delegate=or_(
            PurchaseOrder.user_id==user.id,
            PurchaseOrder.assigned_approver_id==user.id,
        )
        query=select(PurchaseOrder).where(owner_or_delegate)
    else:
        query=select(PurchaseOrder).where(PurchaseOrder.user_id==user.id)
    if status_filter:
        query = query.where(PurchaseOrder.status == status_filter)
    orders = db.scalars(
        query.order_by(PurchaseOrder.created_at.desc()).limit(limit)
    ).all()
    records=_serialize_many(orders,db)
    for order,record in zip(orders,records):
        record['can_approve']=_can_approve_order(order,user.id)
    return records

@router.get('/purchase-orders/{order_id}',response_model=PurchaseOrderResponse)
def get_purchase_order(order_id:str,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    return _serialize(_owned_order(order_id,user,db),db)

@router.post('/purchase-orders/{order_id}/submit',response_model=PurchaseOrderResponse)
def submit_purchase_order(order_id:str,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    order=_owned_order(order_id,user,db)
    if order.status!='draft': raise HTTPException(status_code=409,detail='Only draft purchase orders can be submitted.')
    order.status='pending_approval'; order.submitted_at=datetime.now(timezone.utc)
    _audit(db,user.id,'purchase_order.submitted',order_id=order.id,request_id=order.request_id)
    db.commit(); db.refresh(order)
    return _serialize(order,db)

@router.post('/purchase-orders/{order_id}/approve',response_model=PurchaseOrderResponse)
def approve_purchase_order(order_id:str,payload:ApprovalAction,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    order=_approval_order(order_id,user,db)
    if order.status!='pending_approval': raise HTTPException(status_code=409,detail='Only purchase orders awaiting approval can be approved.')
    request=db.get(ProcurementRequest,order.request_id)
    if request and policy_expired(request):
        raise HTTPException(status_code=409,detail='Buyer mandate expired; create a new procurement request.')
    now=datetime.now(timezone.utc); order.status='approved'; order.approved_by=user.id; order.approved_at=now
    db.add(Approval(purchase_order_id=order.id,actor_user_id=user.id,decision='approved',comment=payload.comment))
    _audit(db,order.user_id,'purchase_order.approved',order_id=order.id,request_id=order.request_id,details={'amount':str(order.total_amount),'currency':order.currency,'actor_user_id':user.id})
    db.commit(); db.refresh(order)
    return _serialize(order,db)

@router.post('/purchase-orders/{order_id}/reject',response_model=PurchaseOrderResponse)
def reject_purchase_order(order_id:str,payload:ApprovalAction,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    order=_approval_order(order_id,user,db)
    if order.status!='pending_approval': raise HTTPException(status_code=409,detail='Only purchase orders awaiting approval can be rejected.')
    now=datetime.now(timezone.utc); order.status='rejected'; order.rejected_by=user.id; order.rejected_at=now; order.rejection_reason=payload.comment or 'Rejected by approver'
    db.add(Approval(purchase_order_id=order.id,actor_user_id=user.id,decision='rejected',comment=payload.comment))
    _audit(db,order.user_id,'purchase_order.rejected',order_id=order.id,request_id=order.request_id,details={'reason':order.rejection_reason,'actor_user_id':user.id})
    db.commit(); db.refresh(order)
    return _serialize(order,db)

@router.post('/purchase-orders/{order_id}/payments/paypal/create',response_model=PayPalCheckoutResponse)
async def create_paypal_order(order_id:str,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    order=_owned_order(order_id,user,db)
    if order.status not in ('approved','payment_pending'): raise HTTPException(status_code=409,detail='A human-approved purchase order is required before starting PayPal checkout.')
    verification=order.offer_verification_json or {}
    if verification.get('status') in ('changed','unavailable'):
        raise HTTPException(status_code=409,detail='Channel3 recheck found a changed or missing retailer offer. Refresh discovery and create a new order.')
    request=db.get(ProcurementRequest,order.request_id)
    if order.status=='approved' and request and policy_expired(request):
        raise HTTPException(status_code=409,detail='Buyer mandate expired before checkout.')
    try:
        client=PayPalClient()
        client.ensure_configured()
    except PayPalConfigurationError as exc: raise HTTPException(status_code=503,detail='PayPal Sandbox configuration or credentials are invalid.') from exc
    payment=db.scalar(select(Payment).where(Payment.purchase_order_id==order.id))
    merchant_fingerprint=_merchant_fingerprint(client.client_id)
    if payment and payment.paypal_order_id:
        if not _current_checkout_merchant(payment,client_id=client.client_id):
            raise HTTPException(
                status_code=409,
                detail='This PayPal checkout belongs to a previous merchant configuration. '
                       'For safety, create a fresh procurement purchase order and checkout '
                       'under the current Sandbox Business seller. The old order remains unpaid.',
            )
        if payment.approval_url:
            return {'payment':_payment_data(payment),'approval_url':payment.approval_url,'idempotent_replay':True}
    if payment:
        payment.status='creating'
        payment.provider_response={'merchant_fingerprint':merchant_fingerprint}
    else:
        payment=Payment(purchase_order_id=order.id,idempotency_key=uuid.uuid4().hex,status='creating',amount=order.total_amount,currency=order.currency,provider_response={'merchant_fingerprint':merchant_fingerprint})
        db.add(payment)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        existing=db.scalar(select(Payment).where(Payment.purchase_order_id==order.id))
        if existing and existing.paypal_order_id:
            if not _current_checkout_merchant(existing,client_id=client.client_id):
                raise HTTPException(status_code=409,detail='Checkout belongs to a previous merchant configuration; create a new procurement purchase order.') from exc
            if existing.approval_url:
                return {'payment':_payment_data(existing),'approval_url':existing.approval_url,'idempotent_replay':True}
        raise HTTPException(status_code=409,detail='A PayPal checkout attempt is already being created for this purchase order.') from exc
    db.refresh(payment)
    item=db.scalar(select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id==order.id))
    if item is None:
        raise HTTPException(status_code=409,detail='Purchase order has no saved line item.')
    settings=get_settings()
    pending_payment_id=payment.id
    checkout_args={
        'po_id':order.id, 'po_number':order.po_number,
        'amount':f'{order.total_amount:.2f}', 'currency':order.currency,
        'description':item.product_title, 'quantity':item.quantity,
        'unit_price':f'{item.unit_price:.2f}',
        'idempotency_key':payment.idempotency_key,
        'return_url':settings.frontend_url.rstrip('/')+'/orders?paypal=return&po='+order.id,
        'cancel_url':settings.frontend_url.rstrip('/')+'/orders?paypal=cancel&po='+order.id,
    }
    # Release the read-only transaction before potentially slow PayPal OAuth and
    # create-order HTTP calls (Postgres idle-in-transaction timeout is 15s).
    # The creating record and stable idempotency key are already committed.
    db.rollback()
    try:
        result=await client.create_order(**checkout_args)
    except (PayPalConfigurationError,PayPalUnavailable) as exc:
        payment=db.get(Payment,pending_payment_id)
        if payment and payment.status=='creating':
            payment.status='failed'
            db.commit()
        raise HTTPException(status_code=503 if isinstance(exc,PayPalConfigurationError) else 502,detail='PayPal could not create the checkout order. Check Sandbox connectivity and credentials.') from exc
    payment=db.get(Payment,pending_payment_id)
    order=_owned_order(order_id,user,db)
    if payment is None or payment.purchase_order_id!=order.id or payment.idempotency_key!=checkout_args['idempotency_key']:
        raise HTTPException(status_code=409,detail='Checkout reservation changed while contacting PayPal.')
    if order.status not in ('approved','payment_pending'):
        raise HTTPException(status_code=409,detail='The approved purchase order changed while PayPal checkout was created.')
    links=result.get('links') or []
    approval_url=next((link.get('href') for link in links if link.get('rel') in ('approve','payer-action')),None)
    if not result.get('id') or not approval_url or not PayPalClient.is_valid_order_id(result.get('id')) or not PayPalClient.is_approval_url(approval_url):
        payment.status='failed'; payment.provider_response={'status':'invalid_create_order_response'}; db.commit()
        raise HTTPException(status_code=502,detail='PayPal did not return a usable approval link.')
    payment.paypal_order_id=result['id']; payment.approval_url=approval_url; payment.status='created'; payment.provider_response={'id':result['id'],'status':result.get('status'),'merchant_fingerprint':merchant_fingerprint}
    order.status='payment_pending'
    _audit(db,user.id,'payment.paypal_order_created',order_id=order.id,request_id=order.request_id,details={'paypal_order_id':result['id'],'amount':str(order.total_amount),'currency':order.currency})
    db.commit(); db.refresh(payment)
    return {'payment':_payment_data(payment),'approval_url':approval_url,'idempotent_replay':False}

@router.post('/purchase-orders/{order_id}/payments/paypal/capture',response_model=PurchaseOrderResponse)
async def capture_paypal_order(order_id:str,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    order=_owned_order(order_id,user,db)
    payment=db.scalar(select(Payment).where(Payment.purchase_order_id==order.id))
    if payment is None or not payment.paypal_order_id: raise HTTPException(status_code=409,detail='Create a PayPal checkout order first.')
    if payment.status=='completed' and order.status=='paid': return _serialize(order,db)
    if not _current_checkout_merchant(payment):
        raise HTTPException(status_code=409,detail='Cannot capture a PayPal order from a previous merchant configuration. Create a fresh procurement purchase order.')
    if order.status not in ('approved','payment_pending'): raise HTTPException(status_code=409,detail='Purchase order is not eligible for payment capture.')
    payment_id=payment.id
    paypal_order_id=payment.paypal_order_id
    # Detached records retain the immutable values needed for provider
    # verification, while the database read transaction is released before I/O.
    db.expunge(order)
    db.expunge(payment)
    db.rollback()
    try:
        client=PayPalClient()
        client.ensure_configured()
        remote=await client.get_order(paypal_order_id)
        if remote.get('status')=='COMPLETED':
            # Recovery after a past POST /capture succeeded at PayPal but
            # the former strict response matcher returned a local 502.
            # A completed GET may also omit original purchase-unit metadata.
            # The saved provider order ID, merchant binding, exact completed
            # capture amount and currency must all match; NO SECOND POST.
            if _paypal_completed_capture(remote,order,payment) is None:
                raise HTTPException(status_code=409,detail='This PayPal order reports completed but its capture evidence does not match the approved purchase order. Do not create another payment.')
            result=remote
        else:
            if not _paypal_order_matches(remote,order,payment):
                raise HTTPException(status_code=409,detail='PayPal order details do not match the approved purchase order.')
            # APPROVED is the only status allowed to initiate capture.
            result=await client.capture_order(
                paypal_order_id,
                hashlib.sha256(('capture:'+payment.idempotency_key).encode()).hexdigest()[:32],
            )
    except (PayPalConfigurationError,PayPalUnavailable) as exc:
        raise HTTPException(status_code=503 if isinstance(exc,PayPalConfigurationError) else 502,detail='PayPal could not verify or capture this order.') from exc
    # The Orders v2 POST capture response is *not* a repeat of GET order:
    # it may contain reference_id and payments.captures, without custom_id
    # or the original purchase-unit amount. The GET above validated the PO
    # identity/amount before any POST. Reconcile an already-COMPLETED order
    # with GET only; NEVER send another capture request in that state.
    if not isinstance(result,dict) or result.get('id')!=paypal_order_id:
        raise HTTPException(status_code=502,detail='PayPal returned a different order ID. Capture state is uncertain; verify the saved order before retrying.')
    capture=None
    if result.get('status')=='COMPLETED':
        capture=_paypal_completed_capture(result,order,payment)
        if capture is None:
            if not _paypal_capture_response_noncontradictory(result,order,payment):
                raise HTTPException(status_code=502,detail='PayPal reported conflicting completed capture details. Do not start a new checkout; review this PayPal order.')
            # PayPal can omit complete capture data from the immediate result.
            # Read the same order from PayPal and verify its immutable original
            # PO binding and full capture evidence; no second charge is made.
            try:
                confirmation=await client.get_order(paypal_order_id)
            except (PayPalConfigurationError,PayPalUnavailable) as exc:
                raise HTTPException(status_code=502,detail='PayPal capture may have succeeded but confirmation is unavailable. Retry confirmation on this same purchase order, not a new payment.') from exc
            capture=_paypal_completed_capture(confirmation,order,payment)
            if capture is None:
                raise HTTPException(status_code=409,detail='PayPal has not returned a verified completed capture. This purchase order remains pending; check the provider order before retrying.')
    order=_owned_order(order_id,user,db)
    current_payment=db.scalar(select(Payment).where(Payment.purchase_order_id==order.id))
    if not current_payment or current_payment.id!=payment_id or current_payment.paypal_order_id!=paypal_order_id:
        raise HTTPException(status_code=409,detail='The saved PayPal payment changed during verification.')
    payment=current_payment
    if order.status=='paid' and payment.status=='completed':
        return _serialize(order,db)
    if order.status not in ('approved','payment_pending'):
        raise HTTPException(status_code=409,detail='Purchase order status changed while confirming payment.')
    if result.get('status')!='COMPLETED':
        payment.status='pending'
        # Preserve the one-way REST app fingerprint across pending responses.
        # Otherwise a successful same-merchant retry is falsely classified as
        # a merchant rotation and can no longer reconcile a later capture.
        previous=payment.provider_response if isinstance(payment.provider_response,dict) else {}
        payment.provider_response={**previous,'paypal_status':result.get('status')}
        _audit(db,user.id,'payment.capture_pending',order_id=order.id,request_id=order.request_id,details={'paypal_status':result.get('status')})
        db.commit()
        raise HTTPException(status_code=409,detail='PayPal has not confirmed a completed capture. The order remains unpaid; retry after the provider reports a final status.')
    if capture is None:
        raise HTTPException(status_code=502,detail='Completed PayPal capture evidence was not verified. The order remains pending.')
    if payment.capture_id and payment.capture_id!=capture['id']:
        raise HTTPException(status_code=409,detail='Another capture ID is already recorded for this order.')
    payment.status='completed'; payment.capture_id=capture['id']; payment.provider_response={'paypal_status':'COMPLETED','capture_id':capture['id']}
    order.status='paid'
    _audit(db,user.id,'payment.paypal_capture_completed',order_id=order.id,request_id=order.request_id,details={'capture_id':capture['id'],'amount':str(order.total_amount),'currency':order.currency})
    db.commit(); db.refresh(order)
    return _serialize(order,db)


def _owner_passport(order_id: str, db: Session, user: User):
    order=_owned_order(order_id,user,db)
    items=db.scalars(select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id==order.id)).all()
    approvals=db.scalars(select(Approval).where(Approval.purchase_order_id==order.id).order_by(Approval.created_at)).all()
    payment=db.scalar(select(Payment).where(Payment.purchase_order_id==order.id))
    events=db.scalars(select(AuditEvent).where(AuditEvent.purchase_order_id==order.id).order_by(AuditEvent.created_at)).all()
    return build_passport(order,items,approvals,payment,events)


@router.get('/purchase-orders/{order_id}/passport')
def get_decision_passport(
    order_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Owner-only factual decision and Sandbox payment evidence; no credentials."""
    return _owner_passport(order_id,db,user)


@router.get('/purchase-orders/{order_id}/passport.pdf')
def download_decision_passport(
    order_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    report=_owner_passport(order_id,db,user)
    pdf=passport_pdf_bytes(report)
    return Response(
        content=pdf,
        media_type='application/pdf',
        headers={
            'Content-Disposition':'attachment; filename="ProcurePilot-Decision-Passport.pdf"',
            'Cache-Control':'private, no-store',
            'X-Content-Type-Options':'nosniff',
        },
    )


@router.post('/purchase-orders/{order_id}/verify-offer')
async def verify_retailer_offer(
    order_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Recheck one exact saved Channel3 offer without changing the approved price."""
    order=_owned_order(order_id,user,db)
    if order.status not in ('draft','pending_approval','approved'):
        raise HTTPException(status_code=409,detail='Only unpaid, not-yet-checkout purchase orders can be rechecked.')
    item=db.scalar(select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id==order.id))
    if item is None:
        raise HTTPException(status_code=409,detail='Purchase order has no saved offer')
    previous=order.offer_verification_json or {}
    if previous.get('checked_at'):
        try:
            previous_time=datetime.fromisoformat(previous['checked_at'])
            if previous_time.tzinfo and (datetime.now(timezone.utc)-previous_time).total_seconds()<30:
                return previous
        except (ValueError,TypeError):
            pass
    product_id=item.product_id
    offer_url=item.offer_url
    owner_id=user.id
    # The configured 15s PostgreSQL idle-in-transaction limit must not include
    # the Channel3 network call. No mutations have occurred yet.
    db.rollback()
    try:
        product=await Channel3Client().get_product(product_id,user_id=owner_id)
    except Channel3ConfigurationError as exc:
        raise HTTPException(status_code=503,detail='Channel3 verification is not configured') from exc
    except Channel3Unavailable as exc:
        raise HTTPException(status_code=502,detail='Channel3 verification is temporarily unavailable') from exc

    # Another request may have changed this PO while Channel3 responded.
    # Reload the owner-scoped order and exact frozen line item before writing.
    order=_owned_order(order_id,user,db)
    if order.status not in ('draft','pending_approval','approved'):
        raise HTTPException(status_code=409,detail='The purchase order changed while checking its retailer offer.')
    item=db.scalar(select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id==order.id))
    if item is None or item.product_id!=product_id or item.offer_url!=offer_url:
        raise HTTPException(status_code=409,detail='The frozen offer changed while checking Channel3.')
    offer=next((offer for offer in product.offers if str(offer.url)==offer_url),None)
    request=db.get(ProcurementRequest,order.request_id)
    if offer is None:
        result={'status':'unavailable','reason':'The original retailer offer was not found on the refreshed product.',
                'checked_at':datetime.now(timezone.utc).isoformat(),'source':'Channel3 product lookup'}
    else:
        reasons=evaluate_offer(request,product,offer) if request else ['Original request not found']
        provider_price=Decimal(str(offer.price.amount))
        if provider_price!=item.unit_price or offer.price.currency!=item.currency:
            reasons.append('Quoted price or currency differs from the frozen purchase order')
        result={
            'status':'changed' if reasons else 'unchanged',
            'reason':'; '.join(reasons[:5]) if reasons else 'Exact original offer still matches the frozen amount and mandate',
            'checked_at':datetime.now(timezone.utc).isoformat(),
            'source':'Channel3 product lookup',
            'previous_unit_price':str(item.unit_price),
            'latest_unit_price':str(provider_price),
            'currency':offer.price.currency,
            'availability':offer.availability,
        }
    order.offer_verification_json=result
    _audit(db,user.id,'purchase_order.offer_rechecked',order_id=order.id,request_id=order.request_id,
           details={'status':result['status'],'source':'Channel3'})
    db.commit()
    return result
