"""
Add chat sessions and messages tables

Revision ID: 0002_add_chat_tables
Revises: 0001_initial_users_sessions
Create Date: 2025-08-13 00:00:10.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_add_chat_tables'
down_revision = '0001_initial_users_sessions'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'chat_messages',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('chat_session_id', sa.Integer(), sa.ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_index('idx_chat_sessions_user_id', 'chat_sessions', ['user_id'])
    op.create_index('idx_chat_messages_session_id', 'chat_messages', ['chat_session_id'])
    op.create_index('idx_chat_messages_user_id', 'chat_messages', ['user_id'])


def downgrade():
    op.drop_index('idx_chat_messages_user_id', table_name='chat_messages')
    op.drop_index('idx_chat_messages_session_id', table_name='chat_messages')
    op.drop_index('idx_chat_sessions_user_id', table_name='chat_sessions')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
