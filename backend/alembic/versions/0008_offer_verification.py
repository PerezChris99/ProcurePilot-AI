"""Store last on-demand Channel3 offer check without altering frozen PO.

Revision ID: 0008_offer_verification
Revises: 0007_decision_evidence
"""
from alembic import op
import sqlalchemy as sa

revision='0008_offer_verification'
down_revision='0007_decision_evidence'
branch_labels=None
depends_on=None


def upgrade():
    with op.batch_alter_table('purchase_orders') as batch:
        batch.add_column(sa.Column('offer_verification_json',sa.JSON(),nullable=False,server_default='{}'))
    with op.batch_alter_table('purchase_orders') as batch:
        batch.alter_column('offer_verification_json',server_default=None)


def downgrade():
    with op.batch_alter_table('purchase_orders') as batch:
        batch.drop_column('offer_verification_json')
