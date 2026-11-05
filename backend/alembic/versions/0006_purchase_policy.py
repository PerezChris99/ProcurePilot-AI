"""Store per-request deterministic buying mandates.

Revision ID: 0006_purchase_policy
Revises: 0005_read_indexes
"""
from alembic import op
import sqlalchemy as sa

revision='0006_purchase_policy'
down_revision='0005_read_indexes'
branch_labels=None
depends_on=None


def upgrade():
    with op.batch_alter_table('procurement_requests') as batch:
        batch.add_column(sa.Column('policy_json',sa.JSON(),nullable=False,server_default='{}'))
    with op.batch_alter_table('procurement_requests') as batch:
        batch.alter_column('policy_json',server_default=None)


def downgrade():
    with op.batch_alter_table('procurement_requests') as batch:
        batch.drop_column('policy_json')
