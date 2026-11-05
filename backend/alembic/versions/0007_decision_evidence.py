"""Freeze the purchase decision's evidence when its order is created.

Revision ID: 0007_decision_evidence
Revises: 0006_purchase_policy
"""
from alembic import op
import sqlalchemy as sa

revision='0007_decision_evidence'
down_revision='0006_purchase_policy'
branch_labels=None
depends_on=None


def upgrade():
    with op.batch_alter_table('purchase_orders') as batch:
        batch.add_column(sa.Column('evidence_json',sa.JSON(),nullable=False,server_default='{}'))
    with op.batch_alter_table('purchase_orders') as batch:
        batch.alter_column('evidence_json',server_default=None)


def downgrade():
    with op.batch_alter_table('purchase_orders') as batch:
        batch.drop_column('evidence_json')
