"""Authenticated, user-scoped dashboard aggregates with bounded read queries."""
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
    """Real saved workspace totals; a single order aggregate avoids 3 round trips."""
    counts=db.execute(select(
        func.count(PurchaseOrder.id).filter(PurchaseOrder.status=='paid'),
        func.count(PurchaseOrder.id).filter(PurchaseOrder.status.in_(ACTIVE_STATUSES)),
        func.count(PurchaseOrder.id).filter(PurchaseOrder.status=='pending_approval'),
    ).where(PurchaseOrder.user_id==user.id)).one()
    requests_with_results=db.scalar(select(func.count(ProcurementRequest.id)).where(
        ProcurementRequest.user_id==user.id,
        ProcurementRequest.status=='products_discovered',
    )) or 0
    # Direct user-owned activity lookup is supported by (user_id,created_at).
    events=db.scalars(select(AuditEvent).where(
        AuditEvent.user_id==user.id,
    ).order_by(AuditEvent.created_at.desc(),AuditEvent.id.desc()).limit(8)).all()
    return {
        'completed_orders':counts[0] or 0,
        'active_orders':counts[1] or 0,
        'pending_approvals':counts[2] or 0,
        'requests_with_results':requests_with_results,
        'recent_activity':[
            {'id':event.id,'action':event.action,'created_at':event.created_at}
            for event in events
        ],
    }
