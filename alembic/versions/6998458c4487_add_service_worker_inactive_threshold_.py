"""add service worker inactive threshold type

Revision ID: 6998458c4487
Revises: 4314b0122793
Create Date: 2025-07-20 06:54:57.666256

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6998458c4487'
down_revision: Union[str, None] = '4314b0122793'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - SQLite compatible."""
    # SQLite doesn't support ALTER COLUMN TYPE, so we'll recreate the table
    # Current schema uses VARCHAR, so we just need to extend the length
    
    # Create new table with extended metric_type length
    op.create_table('thresholds_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metric_type', sa.String(length=30), nullable=False),  # Extended from 6 to 30
        sa.Column('condition', sa.String(length=12), nullable=False),
        sa.Column('threshold_value', sa.Float(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('severity', sa.String(length=8), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False),
        sa.Column('source_filter', sa.String(length=100), nullable=True),
        sa.Column('cooldown_minutes', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Copy data from old table to new table
    connection = op.get_bind()
    
    # Check if old table has data
    result = connection.execute(sa.text("SELECT COUNT(*) FROM thresholds")).fetchone()
    if result and result[0] > 0:
        # Copy existing data
        connection.execute(sa.text("""
            INSERT INTO thresholds_new (
                id, name, description, metric_type, condition, threshold_value, 
                duration_minutes, severity, is_enabled, source_filter, 
                cooldown_minutes, created_at, updated_at
            )
            SELECT 
                id, name, description, metric_type, condition, threshold_value,
                duration_minutes, severity, is_enabled, source_filter,
                cooldown_minutes, created_at, updated_at
            FROM thresholds
        """))
    
    # Drop old table and rename new table
    op.drop_table('thresholds')
    op.rename_table('thresholds_new', 'thresholds')
    
    # Recreate indexes
    op.create_index('ix_thresholds_id', 'thresholds', ['id'], unique=False)
    op.create_index('ix_thresholds_name', 'thresholds', ['name'], unique=False)


def downgrade() -> None:
    """Downgrade schema - SQLite compatible."""
    # Create old table structure (back to original length)
    op.create_table('thresholds_old',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metric_type', sa.String(length=6), nullable=False),  # Back to original length
        sa.Column('condition', sa.String(length=12), nullable=False),
        sa.Column('threshold_value', sa.Float(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('severity', sa.String(length=8), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False),
        sa.Column('source_filter', sa.String(length=100), nullable=True),
        sa.Column('cooldown_minutes', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Copy data (excluding SERVICE_WORKER_INACTIVE records)
    connection = op.get_bind()
    connection.execute(sa.text("""
        INSERT INTO thresholds_old (
            id, name, description, metric_type, condition, threshold_value, 
            duration_minutes, severity, is_enabled, source_filter, 
            cooldown_minutes, created_at, updated_at
        )
        SELECT 
            id, name, description, metric_type, condition, threshold_value,
            duration_minutes, severity, is_enabled, source_filter,
            cooldown_minutes, created_at, updated_at
        FROM thresholds
        WHERE metric_type != 'service_worker_inactive'
    """))
    
    # Drop current table and rename old table
    op.drop_table('thresholds')
    op.rename_table('thresholds_old', 'thresholds')
    
    # Recreate indexes
    op.create_index('ix_thresholds_id', 'thresholds', ['id'], unique=False)
    op.create_index('ix_thresholds_name', 'thresholds', ['name'], unique=False)
