import uuid
from datetime import datetime,timezone
from decimal import Decimal
from sqlalchemy import DateTime,ForeignKey,JSON,Numeric,String,Text,UniqueConstraint,Index
from sqlalchemy.orm import Mapped,mapped_column
from app.core.database import Base

class PurchaseOrder(Base):
    __tablename__='purchase_orders'
    __table_args__=(
        Index('ix_purchase_orders_user_created','user_id','created_at'),
        Index('ix_purchase_orders_user_status_created','user_id','status','created_at'),
    )
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
    po_number: Mapped[str]=mapped_column(String(40),unique=True,index=True,nullable=False)
    user_id: Mapped[str]=mapped_column(ForeignKey('users.id',ondelete='CASCADE'),index=True,nullable=False)
    request_id: Mapped[str]=mapped_column(ForeignKey('procurement_requests.id',ondelete='RESTRICT'),index=True,nullable=False)
    status: Mapped[str]=mapped_column(String(32),default='draft',index=True,nullable=False)
    currency: Mapped[str]=mapped_column(String(3),nullable=False)
    subtotal: Mapped[Decimal]=mapped_column(Numeric(14,2),nullable=False)
    total_amount: Mapped[Decimal]=mapped_column(Numeric(14,2),nullable=False)
    evidence_json: Mapped[dict]=mapped_column(JSON,default=dict,nullable=False)
    submitted_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    approved_by: Mapped[str|None]=mapped_column(ForeignKey('users.id',ondelete='SET NULL'),nullable=True)
    approved_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    rejected_by: Mapped[str|None]=mapped_column(ForeignKey('users.id',ondelete='SET NULL'),nullable=True)
    rejected_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    rejection_reason: Mapped[str|None]=mapped_column(Text,nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),nullable=False)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),onupdate=lambda:datetime.now(timezone.utc),nullable=False)

class PurchaseOrderItem(Base):
    __tablename__='purchase_order_items'
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
    purchase_order_id: Mapped[str]=mapped_column(ForeignKey('purchase_orders.id',ondelete='CASCADE'),index=True,nullable=False)
    product_id: Mapped[str]=mapped_column(String(255),nullable=False)
    product_title: Mapped[str]=mapped_column(String(500),nullable=False)
    merchant: Mapped[str]=mapped_column(String(255),nullable=False)
    offer_url: Mapped[str]=mapped_column(Text,nullable=False)
    quantity: Mapped[int]=mapped_column(nullable=False)
    unit_price: Mapped[Decimal]=mapped_column(Numeric(14,2),nullable=False)
    line_total: Mapped[Decimal]=mapped_column(Numeric(14,2),nullable=False)
    currency: Mapped[str]=mapped_column(String(3),nullable=False)
    product_snapshot: Mapped[dict]=mapped_column(JSON,nullable=False)

class Approval(Base):
    __tablename__='approvals'
    __table_args__=(Index('ix_approvals_po_created','purchase_order_id','created_at'),)
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
    purchase_order_id: Mapped[str]=mapped_column(ForeignKey('purchase_orders.id',ondelete='CASCADE'),index=True,nullable=False)
    actor_user_id: Mapped[str]=mapped_column(ForeignKey('users.id',ondelete='RESTRICT'),nullable=False)
    decision: Mapped[str]=mapped_column(String(16),nullable=False)
    comment: Mapped[str|None]=mapped_column(Text,nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),nullable=False)

class Payment(Base):
    __tablename__='payments'
    __table_args__=(UniqueConstraint('purchase_order_id',name='uq_payments_purchase_order'),)
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
    purchase_order_id: Mapped[str]=mapped_column(ForeignKey('purchase_orders.id',ondelete='RESTRICT'),index=True,nullable=False)
    provider: Mapped[str]=mapped_column(String(24),default='paypal',nullable=False)
    paypal_order_id: Mapped[str|None]=mapped_column(String(64),unique=True,index=True,nullable=True)
    capture_id: Mapped[str|None]=mapped_column(String(64),unique=True,index=True,nullable=True)
    idempotency_key: Mapped[str]=mapped_column(String(64),unique=True,nullable=False)
    status: Mapped[str]=mapped_column(String(24),default='created',index=True,nullable=False)
    amount: Mapped[Decimal]=mapped_column(Numeric(14,2),nullable=False)
    currency: Mapped[str]=mapped_column(String(3),nullable=False)
    approval_url: Mapped[str|None]=mapped_column(Text,nullable=True)
    provider_response: Mapped[dict|None]=mapped_column(JSON,nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),nullable=False)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),onupdate=lambda:datetime.now(timezone.utc),nullable=False)

class WebhookEvent(Base):
    __tablename__='webhook_events'
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
    provider_event_id: Mapped[str]=mapped_column(String(128),unique=True,index=True,nullable=False)
    event_type: Mapped[str]=mapped_column(String(128),nullable=False)
    verified: Mapped[bool]=mapped_column(nullable=False)
    payload: Mapped[dict]=mapped_column(JSON,nullable=False)
    processed_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),nullable=False)

class AuditEvent(Base):
    __tablename__='audit_events'
    __table_args__=(
        Index('ix_audit_events_order_created','purchase_order_id','created_at'),
        Index('ix_audit_events_user_created','user_id','created_at'),
    )
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
    user_id: Mapped[str|None]=mapped_column(ForeignKey('users.id',ondelete='SET NULL'),index=True,nullable=True)
    purchase_order_id: Mapped[str|None]=mapped_column(ForeignKey('purchase_orders.id',ondelete='SET NULL'),index=True,nullable=True)
    request_id: Mapped[str|None]=mapped_column(ForeignKey('procurement_requests.id',ondelete='SET NULL'),index=True,nullable=True)
    action: Mapped[str]=mapped_column(String(80),nullable=False)
    details: Mapped[dict]=mapped_column(JSON,default=dict,nullable=False)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),nullable=False)
