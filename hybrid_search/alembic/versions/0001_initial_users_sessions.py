"""
Initial users and user_sessions tables (baseline)

Revision ID: 0001_initial_users_sessions
Revises: 
Create Date: 2025-08-13 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '0001_initial_users_sessions'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(length=50), nullable=False, unique=True),
        sa.Column('email', sa.String(length=100), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'user_sessions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('session_token', sa.String(length=255), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_index('idx_users_username', 'users', ['username'])
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_sessions_token', 'user_sessions', ['session_token'])
    op.create_index('idx_sessions_user_id', 'user_sessions', ['user_id'])


def downgrade():
    op.drop_index('idx_sessions_user_id', table_name='user_sessions')
    op.drop_index('idx_sessions_token', table_name='user_sessions')
    op.drop_index('idx_users_email', table_name='users')
    op.drop_index('idx_users_username', table_name='users')
    op.drop_table('user_sessions')
    op.drop_table('users')
