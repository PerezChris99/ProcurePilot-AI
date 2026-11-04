from datetime import datetime,timezone
from decimal import Decimal,InvalidOperation
from fastapi import APIRouter,Depends,HTTPException,Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.integrations.paypal.client import PayPalClient,PayPalConfigurationError,PayPalUnavailable
from app.models import AuditEvent,Payment,PurchaseOrder,WebhookEvent

router=APIRouter(tags=['webhooks'])

@router.post('/webhooks/paypal')
async def paypal_webhook(request:Request,db:Session=Depends(get_db)):
    raw_body=await request.body()
    if len(raw_body)>1_000_000: raise HTTPException(status_code=413,detail='Webhook payload is too large')
    try: event=await request.json()
    except Exception as exc: raise HTTPException(status_code=400,detail='Invalid webhook JSON') from exc
    if not isinstance(event,dict) or not event.get('id') or not event.get('event_type'):
        raise HTTPException(status_code=400,detail='Webhook event is missing its ID or type')
    client=PayPalClient()
    try: verified=await client.verify_webhook(request.headers,event)
    except PayPalConfigurationError as exc: raise HTTPException(status_code=503,detail='PayPal webhook verification is not configured') from exc
    except PayPalUnavailable as exc: raise HTTPException(status_code=502,detail='PayPal webhook verification is temporarily unavailable') from exc
    if not verified: raise HTTPException(status_code=400,detail='PayPal webhook signature verification failed')
    existing=db.scalar(select(WebhookEvent).where(WebhookEvent.provider_event_id==event['id']))
    if existing: return {'received':True,'duplicate':True,'processed':existing.processed_at is not None}
    resource=event.get('resource') or {}
    related=(resource.get('supplementary_data') or {}).get('related_ids') or {}
    safe_payload={'id':event['id'],'event_type':event['event_type'],'resource':{'id':resource.get('id'),'status':resource.get('status'),'amount':resource.get('amount'),'related_order_id':related.get('order_id')}}
    record=WebhookEvent(provider_event_id=event['id'],event_type=event['event_type'],verified=True,payload=safe_payload)
    db.add(record)
    try: db.flush()
    except IntegrityError:
        db.rollback()
        return {'received':True,'duplicate':True,'processed':True}
    event_type=event['event_type']
    if event_type in ('PAYMENT.CAPTURE.COMPLETED','PAYMENT.CAPTURE.DENIED'):
        paypal_order_id=related.get('order_id')
        payment=db.scalar(select(Payment).where(Payment.paypal_order_id==paypal_order_id)) if paypal_order_id else None
        if payment:
            order=db.get(PurchaseOrder,payment.purchase_order_id)
            if event_type=='PAYMENT.CAPTURE.COMPLETED' and order:
                try: amount=Decimal(str((resource.get('amount') or {}).get('value')))
                except (InvalidOperation,ValueError,TypeError): amount=None
                currency=(resource.get('amount') or {}).get('currency_code')
                duplicate_capture=db.scalar(select(Payment).where(Payment.capture_id==resource.get('id'))) if resource.get('id') else None
                capture_not_reused=duplicate_capture is None or duplicate_capture.id==payment.id
                eligible_state=order.status in ('approved','payment_pending','paid')
                if resource.get('status')=='COMPLETED' and amount==Decimal(order.total_amount) and currency==order.currency and resource.get('id') and capture_not_reused and eligible_state:
                    payment.status='completed'; payment.capture_id=resource['id']; payment.provider_response={'paypal_status':'COMPLETED','capture_id':resource['id']}
                    order.status='paid'
                    db.add(AuditEvent(user_id=order.user_id,purchase_order_id=order.id,request_id=order.request_id,action='payment.webhook_capture_completed',details={'event_id':event['id'],'capture_id':resource['id'],'amount':str(amount),'currency':currency}))
                else:
                    db.add(AuditEvent(user_id=order.user_id,purchase_order_id=order.id,action='payment.webhook_mismatch',details={'event_id':event['id']}))
            elif event_type=='PAYMENT.CAPTURE.DENIED' and order and order.status!='paid':
                payment.status='failed'; order.status='payment_failed'
                db.add(AuditEvent(user_id=order.user_id,purchase_order_id=order.id,request_id=order.request_id,action='payment.webhook_capture_denied',details={'event_id':event['id']}))
    record.processed_at=datetime.now(timezone.utc)
    db.commit()
    return {'received':True,'duplicate':False,'processed':True}
