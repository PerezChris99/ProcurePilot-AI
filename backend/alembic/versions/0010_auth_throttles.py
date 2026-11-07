"""Persistent shared authentication-throttle counters (Neon fallback).

Revision ID: 0010_auth_throttles
Revises: 0009_delegated_approver
"""
from alembic import op
import sqlalchemy as sa

revision = '0010_auth_throttles'
down_revision = '0009_delegated_approver'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'auth_rate_limit_counters',
        sa.Column('bucket_key', sa.String(length=160), nullable=False),
        sa.Column('hits', sa.Integer(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('bucket_key'),
    )
    op.create_index('ix_auth_rate_limit_counters_expires_at',
                    'auth_rate_limit_counters', ['expires_at'])


def downgrade():
    op.drop_index('ix_auth_rate_limit_counters_expires_at',
                  table_name='auth_rate_limit_counters')
    op.drop_table('auth_rate_limit_counters')
