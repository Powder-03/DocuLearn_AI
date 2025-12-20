"""add total_days and time_per_day columns

Revision ID: 002_add_fields
Revises: 001_initial
Create Date: 2025-11-04 07:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_fields'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade():
    """Add total_days and time_per_day columns to learning_sessions"""
    # Add total_days column with default value
    op.add_column(
        'learning_sessions',
        sa.Column('total_days', sa.Integer(), nullable=False, server_default='7')
    )
    
    # Add time_per_day column with default value
    op.add_column(
        'learning_sessions',
        sa.Column('time_per_day', sa.String(), nullable=False, server_default='30 minutes')
    )


def downgrade():
    """Remove total_days and time_per_day columns"""
    op.drop_column('learning_sessions', 'time_per_day')
    op.drop_column('learning_sessions', 'total_days')
