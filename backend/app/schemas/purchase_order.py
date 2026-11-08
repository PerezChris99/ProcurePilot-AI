from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel,ConfigDict,Field

class PurchaseOrderCreate(BaseModel):
    product_id: str = Field(min_length=1,max_length=255)
    offer_url: str = Field(min_length=10,max_length=2048)

class ApprovalAction(BaseModel):
    comment: str|None = Field(default=None,max_length=1000)

class PurchaseOrderItemResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id: str
    product_id: str
    product_title: str
    merchant: str
    offer_url: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal
    currency: str

class ApprovalResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id: str
    actor_user_id: str
    decision: str
    comment: str|None
    created_at: datetime

class AuditEventResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id: str
    action: str
    details: dict
    created_at: datetime

class PaymentResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id: str
    provider: str
    paypal_order_id: str|None
    capture_id: str|None
    status: str
    amount: Decimal
    currency: str
    approval_url: str|None
    checkout_merchant_current: bool = True
    created_at: datetime

class PayPalCheckoutResponse(BaseModel):
    payment: PaymentResponse
    approval_url: str
    idempotent_replay: bool

class PurchaseOrderResponse(BaseModel):
    id: str
    po_number: str
    request_id: str
    assigned_approver_id: str | None = None
    can_approve: bool | None = None
    status: str
    currency: str
    subtotal: Decimal
    total_amount: Decimal
    submitted_at: datetime|None
    approved_by: str|None
    approved_at: datetime|None
    rejection_reason: str|None
    created_at: datetime
    updated_at: datetime
    items: list[PurchaseOrderItemResponse]
    approvals: list[ApprovalResponse]
    payment: PaymentResponse|None
    audit_events: list[AuditEventResponse]
    offer_verification: dict | None = None
