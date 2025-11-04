"""Initial schema - create learning_sessions table

Revision ID: 001_initial
Revises: 
Create Date: 2025-11-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create learning_sessions table
    op.create_table(
        'learning_sessions',
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mode', sa.String(), nullable=False, server_default='generation'),
        sa.Column('topic', sa.String(), nullable=True),
        sa.Column('lesson_plan', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('chat_history', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('memory_summary', sa.Text(), nullable=True),
        sa.Column('current_day', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('session_id')
    )
    
    # Create indexes
    op.create_index('ix_learning_sessions_user_id', 'learning_sessions', ['user_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_learning_sessions_user_id', table_name='learning_sessions')
    
    # Drop table
    op.drop_table('learning_sessions')
