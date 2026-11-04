"""Align payment uniqueness and cover user-scoped sorted reads with compound B-trees.

Revision ID: 0005_read_indexes
Revises: 0004_ai_budget
"""
from alembic import op

revision = '0005_read_indexes'
down_revision = '0004_ai_budget'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('ix_procurement_requests_user_created','procurement_requests',['user_id','created_at'])
    op.create_index('ix_procurement_requests_user_status_created','procurement_requests',['user_id','status','created_at'])
    op.create_index('ix_purchase_orders_user_created','purchase_orders',['user_id','created_at'])
    op.create_index('ix_purchase_orders_user_status_created','purchase_orders',['user_id','status','created_at'])
    op.create_index('ix_approvals_po_created','approvals',['purchase_order_id','created_at'])
    op.create_index('ix_audit_events_order_created','audit_events',['purchase_order_id','created_at'])
    op.create_index('ix_audit_events_user_created','audit_events',['user_id','created_at'])
    # The ORM declares these as unique; the original migration created them
    # as nonunique. Fail explicitly if legacy duplicates exist rather than
    # silently allowing one PayPal capture/order ID across separate payments.
    op.drop_index('ix_payments_paypal_order_id',table_name='payments')
    op.create_index('ix_payments_paypal_order_id','payments',['paypal_order_id'],unique=True)
    op.drop_index('ix_payments_capture_id',table_name='payments')
    op.create_index('ix_payments_capture_id','payments',['capture_id'],unique=True)


def downgrade():
    op.drop_index('ix_payments_capture_id',table_name='payments')
    op.create_index('ix_payments_capture_id','payments',['capture_id'])
    op.drop_index('ix_payments_paypal_order_id',table_name='payments')
    op.create_index('ix_payments_paypal_order_id','payments',['paypal_order_id'])
    for name, table in (
        ('ix_audit_events_user_created','audit_events'),
        ('ix_audit_events_order_created','audit_events'),
        ('ix_approvals_po_created','approvals'),
        ('ix_purchase_orders_user_status_created','purchase_orders'),
        ('ix_purchase_orders_user_created','purchase_orders'),
        ('ix_procurement_requests_user_status_created','procurement_requests'),
        ('ix_procurement_requests_user_created','procurement_requests'),
    ):
        op.drop_index(name,table_name=table)
