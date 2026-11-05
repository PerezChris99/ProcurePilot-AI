"""Permit explicitly assigned, distinct registered human approvers.

Revision ID: 0009_delegated_approver
Revises: 0008_offer_verification
"""
from alembic import op
import sqlalchemy as sa

revision='0009_delegated_approver'
down_revision='0008_offer_verification'
branch_labels=None
depends_on=None


def upgrade():
    with op.batch_alter_table('purchase_orders') as batch:
        batch.add_column(sa.Column('assigned_approver_id',sa.String(36),
            sa.ForeignKey('users.id',ondelete='SET NULL'),nullable=True))
        batch.create_index('ix_purchase_orders_assigned_approver_id',['assigned_approver_id'])


def downgrade():
    with op.batch_alter_table('purchase_orders') as batch:
        batch.drop_index('ix_purchase_orders_assigned_approver_id')
        batch.drop_column('assigned_approver_id')
