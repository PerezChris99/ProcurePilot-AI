from collections import defaultdict
import uuid,hashlib
from datetime import datetime,timezone
from decimal import Decimal,InvalidOperation
from fastapi import APIRouter,Depends,HTTPException,Query,status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.database import get_db
from app.integrations.paypal.client import PayPalClient,PayPalConfigurationError,PayPalUnavailable
from app.models import Approval,AuditEvent,Payment,ProcurementRequest,PurchaseOrder,PurchaseOrderItem,User
from app.schemas.purchase_order import ApprovalAction,PayPalCheckoutResponse,PurchaseOrderCreate,PurchaseOrderResponse
from app.security.tokens import get_current_user

router=APIRouter(tags=['purchase orders and payments'])

def _owned_order(order_id,user,db):
    order=db.scalar(select(PurchaseOrder).where(PurchaseOrder.id==order_id,PurchaseOrder.user_id==user.id))
    if order is None: raise HTTPException(status_code=404,detail='Purchase order not found')
    return order

def _audit(db,user_id,action,*,order_id=None,request_id=None,details=None):
    db.add(AuditEvent(user_id=user_id,purchase_order_id=order_id,request_id=request_id,action=action,details=details or {}))

def _payment_data(payment):
    if payment is None: return None
    return {'id':payment.id,'provider':payment.provider,'paypal_order_id':payment.paypal_order_id,'capture_id':payment.capture_id,'status':payment.status,'amount':payment.amount,'currency':payment.currency,'approval_url':payment.approval_url,'created_at':payment.created_at}

def _serialize(order,db):
    items=db.scalars(select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id==order.id)).all()
    approvals=db.scalars(select(Approval).where(Approval.purchase_order_id==order.id).order_by(Approval.created_at)).all()
    payment=db.scalar(select(Payment).where(Payment.purchase_order_id==order.id))
    events=db.scalars(select(AuditEvent).where(AuditEvent.purchase_order_id==order.id).order_by(AuditEvent.created_at)).all()
    return {'id':order.id,'po_number':order.po_number,'request_id':order.request_id,'status':order.status,'currency':order.currency,'subtotal':order.subtotal,'total_amount':order.total_amount,'submitted_at':order.submitted_at,'approved_by':order.approved_by,'approved_at':order.approved_at,'rejection_reason':order.rejection_reason,'created_at':order.created_at,'updated_at':order.updated_at,'items':items,'approvals':approvals,'payment':_payment_data(payment),'audit_events':events}

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
    event_map = defaultdict(list)
    for event in db.scalars(select(AuditEvent).where(
        AuditEvent.purchase_order_id.in_(ids)
    ).order_by(AuditEvent.created_at)):
        event_map[event.purchase_order_id].append(event)
    return [
        {
            'id': order.id, 'po_number': order.po_number, 'request_id': order.request_id,
            'status': order.status, 'currency': order.currency,
            'subtotal': order.subtotal, 'total_amount': order.total_amount,
            'submitted_at': order.submitted_at, 'approved_by': order.approved_by,
            'approved_at': order.approved_at, 'rejection_reason': order.rejection_reason,
            'created_at': order.created_at, 'updated_at': order.updated_at,
            'items': item_map[order.id], 'approvals': approval_map[order.id],
            'payment': _payment_data(payments.get(order.id)),
            'audit_events': event_map[order.id],
        }
        for order in orders
    ]


def _paypal_order_matches(payload,order,payment):
    if payload.get('id')!=payment.paypal_order_id or payload.get('status') not in ('APPROVED','COMPLETED'):
        return False
    units=payload.get('purchase_units') or []
    if len(units)!=1: return False
    unit=units[0]; amount=unit.get('amount') or {}
    try: value=Decimal(str(amount.get('value')))
    except (InvalidOperation,ValueError,TypeError): return False
    return unit.get('custom_id')==order.id and amount.get('currency_code')==order.currency and value==Decimal(order.total_amount)

@router.post('/procurement-requests/{request_id}/purchase-orders',status_code=status.HTTP_201_CREATED,response_model=PurchaseOrderResponse)
def create_purchase_order(request_id:str,payload:PurchaseOrderCreate,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    request=db.scalar(select(ProcurementRequest).where(ProcurementRequest.id==request_id,ProcurementRequest.user_id==user.id))
    if request is None: raise HTTPException(status_code=404,detail='Procurement request not found')
    snapshot=request.analysis_json or {}
    matches=[entry for entry in snapshot.get('results',[]) if entry.get('product',{}).get('id')==payload.product_id]
    if not matches: raise HTTPException(status_code=409,detail='Product is not in this request’s saved Channel3 results. Refresh discovery before creating an order.')
    result=matches[0]; ranking=result.get('ranking') or {}; product=result.get('product') or {}
    if ranking.get('unmet_requirements'): raise HTTPException(status_code=422,detail='This product does not evidence all mandatory requirements and cannot be ordered.')
    offer=next((entry for entry in product.get('offers',[]) if entry.get('url')==payload.offer_url),None)
    if not offer: raise HTTPException(status_code=409,detail='The selected retailer offer is not in the saved product snapshot.')
    price=offer.get('price') or {}
    if price.get('currency')!=request.currency: raise HTTPException(status_code=422,detail='The selected offer currency does not match the procurement request.')
    if not payload.offer_url.startswith('https://'): raise HTTPException(status_code=422,detail='Retailer offer links must use HTTPS.')
    availability=''.join(char for char in str(offer.get('availability','')).casefold() if char.isalnum())
    if availability!='instock': raise HTTPException(status_code=422,detail='The selected retailer offer is not confirmed in stock.')
    try: unit_price=Decimal(str(price.get('amount'))).quantize(Decimal('0.01'))
    except (InvalidOperation,ValueError,TypeError): raise HTTPException(status_code=422,detail='The selected offer has no valid price.')
    if unit_price<=0: raise HTTPException(status_code=422,detail='The selected offer price must be greater than zero.')
    total=(unit_price*request.quantity).quantize(Decimal('0.01'))
    if request.budget is not None and total>request.budget: raise HTTPException(status_code=422,detail='The selected offer exceeds the procurement budget.')
    po_id=str(uuid.uuid4()); now=datetime.now(timezone.utc)
    order=PurchaseOrder(id=po_id,po_number='PP-'+now.strftime('%Y%m%d')+'-'+po_id[:8].upper(),user_id=user.id,request_id=request.id,status='draft',currency=request.currency,subtotal=total,total_amount=total)
    po_item=PurchaseOrderItem(purchase_order_id=po_id,product_id=product['id'],product_title=product.get('title') or 'Catalogue product',merchant=offer.get('domain') or 'Retailer not specified',offer_url=payload.offer_url,quantity=request.quantity,unit_price=unit_price,line_total=total,currency=request.currency,product_snapshot=product)
    db.add_all([order,po_item])
    _audit(db,user.id,'purchase_order.created',order_id=po_id,request_id=request.id,details={'po_number':order.po_number,'amount':str(total),'currency':request.currency,'channel3_product_id':product['id']})
    db.commit(); db.refresh(order)
    return _serialize(order,db)

@router.get('/purchase-orders',response_model=list[PurchaseOrderResponse])
def list_purchase_orders(limit:int=Query(default=50,ge=1,le=100),db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    orders=db.scalars(select(PurchaseOrder).where(PurchaseOrder.user_id==user.id).order_by(PurchaseOrder.created_at.desc()).limit(limit)).all()
    return _serialize_many(orders,db)

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
    order=_owned_order(order_id,user,db)
    if order.status!='pending_approval': raise HTTPException(status_code=409,detail='Only purchase orders awaiting approval can be approved.')
    now=datetime.now(timezone.utc); order.status='approved'; order.approved_by=user.id; order.approved_at=now
    db.add(Approval(purchase_order_id=order.id,actor_user_id=user.id,decision='approved',comment=payload.comment))
    _audit(db,user.id,'purchase_order.approved',order_id=order.id,request_id=order.request_id,details={'amount':str(order.total_amount),'currency':order.currency})
    db.commit(); db.refresh(order)
    return _serialize(order,db)

@router.post('/purchase-orders/{order_id}/reject',response_model=PurchaseOrderResponse)
def reject_purchase_order(order_id:str,payload:ApprovalAction,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    order=_owned_order(order_id,user,db)
    if order.status!='pending_approval': raise HTTPException(status_code=409,detail='Only purchase orders awaiting approval can be rejected.')
    now=datetime.now(timezone.utc); order.status='rejected'; order.rejected_by=user.id; order.rejected_at=now; order.rejection_reason=payload.comment or 'Rejected by approver'
    db.add(Approval(purchase_order_id=order.id,actor_user_id=user.id,decision='rejected',comment=payload.comment))
    _audit(db,user.id,'purchase_order.rejected',order_id=order.id,request_id=order.request_id,details={'reason':order.rejection_reason})
    db.commit(); db.refresh(order)
    return _serialize(order,db)

@router.post('/purchase-orders/{order_id}/payments/paypal/create',response_model=PayPalCheckoutResponse)
async def create_paypal_order(order_id:str,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    order=_owned_order(order_id,user,db)
    if order.status not in ('approved','payment_pending'): raise HTTPException(status_code=409,detail='A human-approved purchase order is required before starting PayPal checkout.')
    try:
        client=PayPalClient()
        client.ensure_configured()
    except PayPalConfigurationError as exc: raise HTTPException(status_code=503,detail='PayPal Sandbox configuration or credentials are invalid.') from exc
    payment=db.scalar(select(Payment).where(Payment.purchase_order_id==order.id))
    if payment and payment.paypal_order_id and payment.approval_url:
        return {'payment':_payment_data(payment),'approval_url':payment.approval_url,'idempotent_replay':True}
    if payment:
        payment.status='creating'
    else:
        payment=Payment(purchase_order_id=order.id,idempotency_key=uuid.uuid4().hex,status='creating',amount=order.total_amount,currency=order.currency)
        db.add(payment)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        existing=db.scalar(select(Payment).where(Payment.purchase_order_id==order.id))
        if existing and existing.paypal_order_id and existing.approval_url:
            return {'payment':_payment_data(existing),'approval_url':existing.approval_url,'idempotent_replay':True}
        raise HTTPException(status_code=409,detail='A PayPal checkout attempt is already being created for this purchase order.') from exc
    db.refresh(payment)
    item=db.scalar(select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id==order.id))
    settings=get_settings()
    try:
        result=await client.create_order(po_id=order.id,po_number=order.po_number,amount=f'{order.total_amount:.2f}',currency=order.currency,description=item.product_title,quantity=item.quantity,unit_price=f'{item.unit_price:.2f}',idempotency_key=payment.idempotency_key,return_url=settings.frontend_url.rstrip('/')+'/orders?paypal=return&po='+order.id,cancel_url=settings.frontend_url.rstrip('/')+'/orders?paypal=cancel&po='+order.id)
    except (PayPalConfigurationError,PayPalUnavailable) as exc:
        payment.status='failed'; db.commit()
        raise HTTPException(status_code=503 if isinstance(exc,PayPalConfigurationError) else 502,detail='PayPal could not create the checkout order. Check Sandbox connectivity and credentials.') from exc
    links=result.get('links') or []
    approval_url=next((link.get('href') for link in links if link.get('rel') in ('approve','payer-action')),None)
    if not result.get('id') or not approval_url or not PayPalClient.is_valid_order_id(result.get('id')) or not PayPalClient.is_approval_url(approval_url):
        payment.status='failed'; payment.provider_response={'status':'invalid_create_order_response'}; db.commit()
        raise HTTPException(status_code=502,detail='PayPal did not return a usable approval link.')
    payment.paypal_order_id=result['id']; payment.approval_url=approval_url; payment.status='created'; payment.provider_response={'id':result['id'],'status':result.get('status')}
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
    if order.status not in ('approved','payment_pending'): raise HTTPException(status_code=409,detail='Purchase order is not eligible for payment capture.')
    try:
        client=PayPalClient()
        client.ensure_configured()
        remote=await client.get_order(payment.paypal_order_id)
        if not _paypal_order_matches(remote,order,payment): raise HTTPException(status_code=409,detail='PayPal order details do not match the approved purchase order.')
        result=await client.capture_order(payment.paypal_order_id,hashlib.sha256(('capture:'+payment.idempotency_key).encode()).hexdigest()[:32]) if remote.get('status')=='APPROVED' else remote
    except (PayPalConfigurationError,PayPalUnavailable) as exc:
        raise HTTPException(status_code=503 if isinstance(exc,PayPalConfigurationError) else 502,detail='PayPal could not verify or capture this order.') from exc
    if not _paypal_order_matches(result,order,payment):
        raise HTTPException(status_code=502,detail='PayPal capture response does not match the approved purchase order.')
    if result.get('status')!='COMPLETED':
        payment.status='pending'; payment.provider_response={'paypal_status':result.get('status')}
        _audit(db,user.id,'payment.capture_pending',order_id=order.id,request_id=order.request_id,details={'paypal_status':result.get('status')})
        db.commit()
        raise HTTPException(status_code=409,detail='PayPal has not confirmed a completed capture. The order remains unpaid; retry after the provider reports a final status.')
    captures=[]
    for unit in result.get('purchase_units') or []: captures.extend((unit.get('payments') or {}).get('captures') or [])
    capture=next((entry for entry in captures if entry.get('status')=='COMPLETED' and entry.get('id')),None)
    try: captured_amount=Decimal(str(capture.get('amount',{}).get('value'))) if capture else None
    except (InvalidOperation,ValueError,TypeError): captured_amount=None
    if not capture or captured_amount!=Decimal(order.total_amount) or capture.get('amount',{}).get('currency_code')!=order.currency:
        raise HTTPException(status_code=502,detail='PayPal capture response did not match the approved amount. The order was not marked paid.')
    payment.status='completed'; payment.capture_id=capture['id']; payment.provider_response={'paypal_status':'COMPLETED','capture_id':capture['id']}
    order.status='paid'
    _audit(db,user.id,'payment.paypal_capture_completed',order_id=order.id,request_id=order.request_id,details={'capture_id':capture['id'],'amount':str(order.total_amount),'currency':order.currency})
    db.commit(); db.refresh(order)
    return _serialize(order,db)
