from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import AuditEvent, ProcurementRequest, PurchaseOrder, User
from app.security.tokens import get_current_user

router = APIRouter(prefix='/dashboard', tags=['dashboard'])
ACTIVE_STATUSES = ('draft', 'pending_approval', 'approved', 'payment_pending', 'payment_failed')


@router.get('/summary')
def dashboard_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Real workspace counts without mixing unrelated currencies."""
    def order_count(*statuses):
        return db.scalar(select(func.count(PurchaseOrder.id)).where(
            PurchaseOrder.user_id == user.id, PurchaseOrder.status.in_(statuses)
        )) or 0

    requests_with_results = db.scalar(select(func.count(ProcurementRequest.id)).where(
        ProcurementRequest.user_id == user.id,
        ProcurementRequest.status == 'products_discovered'
    )) or 0
    events = db.scalars(select(AuditEvent).join(
        PurchaseOrder, AuditEvent.purchase_order_id == PurchaseOrder.id
    ).where(PurchaseOrder.user_id == user.id).order_by(
        AuditEvent.created_at.desc(), AuditEvent.id.desc()
    ).limit(8)).all()
    return {
        'completed_orders': order_count('paid'),
        'active_orders': order_count(*ACTIVE_STATUSES),
        'pending_approvals': order_count('pending_approval'),
        'requests_with_results': requests_with_results,
        'recent_activity': [
            {'id': event.id, 'action': event.action, 'created_at': event.created_at}
            for event in events
        ],
    }
