"""Add immutable purchase orders, approvals, payments, webhooks and audit history.

Revision ID: 0003_orders
Revises: 0002_requests
"""
from alembic import op
import sqlalchemy as sa
revision='0003_orders'
down_revision='0002_requests'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('purchase_orders',
        sa.Column('id',sa.String(36),primary_key=True),sa.Column('po_number',sa.String(40),nullable=False),
        sa.Column('user_id',sa.String(36),sa.ForeignKey('users.id',ondelete='CASCADE'),nullable=False),
        sa.Column('request_id',sa.String(36),sa.ForeignKey('procurement_requests.id',ondelete='RESTRICT'),nullable=False),
        sa.Column('status',sa.String(32),nullable=False),sa.Column('currency',sa.String(3),nullable=False),
        sa.Column('subtotal',sa.Numeric(14,2),nullable=False),sa.Column('total_amount',sa.Numeric(14,2),nullable=False),
        sa.Column('submitted_at',sa.DateTime(timezone=True)),sa.Column('approved_by',sa.String(36),sa.ForeignKey('users.id',ondelete='SET NULL')),
        sa.Column('approved_at',sa.DateTime(timezone=True)),sa.Column('rejected_by',sa.String(36),sa.ForeignKey('users.id',ondelete='SET NULL')),
        sa.Column('rejected_at',sa.DateTime(timezone=True)),sa.Column('rejection_reason',sa.Text()),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False))
    op.create_index('ix_purchase_orders_po_number','purchase_orders',['po_number'],unique=True)
    op.create_index('ix_purchase_orders_user_id','purchase_orders',['user_id'])
    op.create_index('ix_purchase_orders_request_id','purchase_orders',['request_id'])
    op.create_index('ix_purchase_orders_status','purchase_orders',['status'])
    op.create_table('purchase_order_items',
        sa.Column('id',sa.String(36),primary_key=True),sa.Column('purchase_order_id',sa.String(36),sa.ForeignKey('purchase_orders.id',ondelete='CASCADE'),nullable=False),
        sa.Column('product_id',sa.String(255),nullable=False),sa.Column('product_title',sa.String(500),nullable=False),
        sa.Column('merchant',sa.String(255),nullable=False),sa.Column('offer_url',sa.Text(),nullable=False),
        sa.Column('quantity',sa.Integer(),nullable=False),sa.Column('unit_price',sa.Numeric(14,2),nullable=False),
        sa.Column('line_total',sa.Numeric(14,2),nullable=False),sa.Column('currency',sa.String(3),nullable=False),
        sa.Column('product_snapshot',sa.JSON(),nullable=False))
    op.create_index('ix_purchase_order_items_purchase_order_id','purchase_order_items',['purchase_order_id'])
    op.create_table('approvals',
        sa.Column('id',sa.String(36),primary_key=True),sa.Column('purchase_order_id',sa.String(36),sa.ForeignKey('purchase_orders.id',ondelete='CASCADE'),nullable=False),
        sa.Column('actor_user_id',sa.String(36),sa.ForeignKey('users.id',ondelete='RESTRICT'),nullable=False),
        sa.Column('decision',sa.String(16),nullable=False),sa.Column('comment',sa.Text()),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    op.create_index('ix_approvals_purchase_order_id','approvals',['purchase_order_id'])
    op.create_table('payments',
        sa.Column('id',sa.String(36),primary_key=True),sa.Column('purchase_order_id',sa.String(36),sa.ForeignKey('purchase_orders.id',ondelete='RESTRICT'),nullable=False),
        sa.Column('provider',sa.String(24),nullable=False),sa.Column('paypal_order_id',sa.String(64)),
        sa.Column('capture_id',sa.String(64)),sa.Column('idempotency_key',sa.String(64),nullable=False,unique=True),
        sa.Column('status',sa.String(24),nullable=False),sa.Column('amount',sa.Numeric(14,2),nullable=False),sa.Column('currency',sa.String(3),nullable=False),
        sa.Column('approval_url',sa.Text()),sa.Column('provider_response',sa.JSON()),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),
        sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),sa.UniqueConstraint('purchase_order_id',name='uq_payments_purchase_order'))
    op.create_index('ix_payments_purchase_order_id','payments',['purchase_order_id'])
    op.create_index('ix_payments_paypal_order_id','payments',['paypal_order_id'])
    op.create_index('ix_payments_capture_id','payments',['capture_id'])
    op.create_index('ix_payments_status','payments',['status'])
    op.create_table('webhook_events',
        sa.Column('id',sa.String(36),primary_key=True),sa.Column('provider_event_id',sa.String(128),nullable=False),
        sa.Column('event_type',sa.String(128),nullable=False),sa.Column('verified',sa.Boolean(),nullable=False),
        sa.Column('payload',sa.JSON(),nullable=False),sa.Column('processed_at',sa.DateTime(timezone=True)),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    op.create_index('ix_webhook_events_provider_event_id','webhook_events',['provider_event_id'],unique=True)
    op.create_table('audit_events',
        sa.Column('id',sa.String(36),primary_key=True),sa.Column('user_id',sa.String(36),sa.ForeignKey('users.id',ondelete='SET NULL')),
        sa.Column('purchase_order_id',sa.String(36),sa.ForeignKey('purchase_orders.id',ondelete='SET NULL')),
        sa.Column('request_id',sa.String(36),sa.ForeignKey('procurement_requests.id',ondelete='SET NULL')),
        sa.Column('action',sa.String(80),nullable=False),sa.Column('details',sa.JSON(),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    op.create_index('ix_audit_events_user_id','audit_events',['user_id'])
    op.create_index('ix_audit_events_purchase_order_id','audit_events',['purchase_order_id'])
    op.create_index('ix_audit_events_request_id','audit_events',['request_id'])

def downgrade():
    for table,indexes in [('audit_events',['ix_audit_events_request_id','ix_audit_events_purchase_order_id','ix_audit_events_user_id']),('webhook_events',['ix_webhook_events_provider_event_id']),('payments',['ix_payments_status','ix_payments_capture_id','ix_payments_paypal_order_id','ix_payments_purchase_order_id']),('approvals',['ix_approvals_purchase_order_id']),('purchase_order_items',['ix_purchase_order_items_purchase_order_id']),('purchase_orders',['ix_purchase_orders_status','ix_purchase_orders_request_id','ix_purchase_orders_user_id','ix_purchase_orders_po_number'])]:
        for index in indexes: op.drop_index(index,table_name=table)
    for table in ['audit_events','webhook_events','payments','approvals','purchase_order_items','purchase_orders']: op.drop_table(table)
