"""Store atomic per-user and global daily AI budget reservations.

Revision ID: 0004_ai_budget
Revises: 0003_orders
"""
from alembic import op
import sqlalchemy as sa

revision = '0004_ai_budget'
down_revision = '0003_orders'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'ai_daily_budgets',
        sa.Column('scope', sa.String(80), nullable=False),
        sa.Column('day', sa.Date(), nullable=False),
        sa.Column('calls', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('scope', 'day', name='pk_ai_daily_budgets'),
    )


def downgrade():
    op.drop_table('ai_daily_budgets')
