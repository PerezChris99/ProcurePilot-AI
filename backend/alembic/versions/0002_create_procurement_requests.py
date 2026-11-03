"""Create procurement requests table.

Revision ID: 0002_requests
Revises: 0001_users
"""
from alembic import op
import sqlalchemy as sa
revision='0002_requests'
down_revision='0001_users'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('procurement_requests',sa.Column('id',sa.String(length=36),nullable=False),sa.Column('user_id',sa.String(length=36),nullable=False),sa.Column('request_text',sa.Text(),nullable=False),sa.Column('quantity',sa.Integer(),nullable=False),sa.Column('budget',sa.Numeric(precision=14,scale=2),nullable=True),sa.Column('currency',sa.String(length=3),nullable=False),sa.Column('status',sa.String(length=32),nullable=False),sa.Column('analysis_json',sa.JSON(),nullable=True),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),sa.ForeignKeyConstraint(['user_id'],['users.id'],ondelete='CASCADE'),sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_procurement_requests_user_id'),'procurement_requests',['user_id'],unique=False)
    op.create_index(op.f('ix_procurement_requests_status'),'procurement_requests',['status'],unique=False)

def downgrade():
    op.drop_index(op.f('ix_procurement_requests_status'),table_name='procurement_requests')
    op.drop_index(op.f('ix_procurement_requests_user_id'),table_name='procurement_requests')
    op.drop_table('procurement_requests')
