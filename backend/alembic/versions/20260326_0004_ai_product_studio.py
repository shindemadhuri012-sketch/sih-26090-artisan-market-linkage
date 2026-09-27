"""AI Product Studio tables for staged analysis runs and field-level human confirmation

Revision ID: 20260326_0004
Revises: 20260326_0003
Create Date: 2026-03-26 22:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260326_0004'
down_revision: Union[str, None] = '20260326_0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. AI Product Analyses table
    op.create_table(
        'ai_product_analyses',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('product_id', sa.String(length=36), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('media_id', sa.String(length=36), sa.ForeignKey('product_media.id', ondelete='SET NULL'), nullable=True),
        sa.Column('media_checksum', sa.String(length=64), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=True),
        sa.Column('prompt_version', sa.String(length=50), server_default='product_vision_v1', nullable=False),
        sa.Column('idempotency_key', sa.String(length=128), nullable=True),
        sa.Column('status', sa.String(length=30), server_default='PENDING', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('processing_duration_ms', sa.Integer(), nullable=True),
        sa.Column('input_parameters', sa.JSON(), nullable=False),
        sa.Column('raw_response', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_ai_analyses_product_id', 'ai_product_analyses', ['product_id'])
    op.create_index('idx_ai_analyses_media_id', 'ai_product_analyses', ['media_id'])
    op.create_index('idx_ai_analyses_status', 'ai_product_analyses', ['status'])
    op.create_index('idx_ai_analyses_idempotency_key', 'ai_product_analyses', ['idempotency_key'])
    op.create_index('idx_ai_analyses_created_at', 'ai_product_analyses', ['created_at'])

    # 2. AI Product Suggestions table
    op.create_table(
        'ai_product_suggestions',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('analysis_id', sa.String(length=36), sa.ForeignKey('ai_product_analyses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', sa.String(length=36), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('field_name', sa.String(length=100), nullable=False),
        sa.Column('suggested_value', sa.JSON(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('source_type', sa.String(length=50), server_default='AI_SUGGESTED', nullable=False),
        sa.Column('human_confirmed', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('confirmed_value', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=30), server_default='AI_SUGGESTED', nullable=False),
        sa.Column('artisan_notes', sa.Text(), nullable=True),
        sa.Column('reviewed_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('idx_ai_suggestions_analysis_id', 'ai_product_suggestions', ['analysis_id'])
    op.create_index('idx_ai_suggestions_product_id', 'ai_product_suggestions', ['product_id'])
    op.create_index('idx_ai_suggestions_field_name', 'ai_product_suggestions', ['field_name'])
    op.create_index('idx_ai_suggestions_status', 'ai_product_suggestions', ['status'])
    op.create_index('idx_ai_suggestions_product_status', 'ai_product_suggestions', ['product_id', 'status'])


def downgrade() -> None:
    op.drop_index('idx_ai_suggestions_product_status', table_name='ai_product_suggestions')
    op.drop_index('idx_ai_suggestions_status', table_name='ai_product_suggestions')
    op.drop_index('idx_ai_suggestions_field_name', table_name='ai_product_suggestions')
    op.drop_index('idx_ai_suggestions_product_id', table_name='ai_product_suggestions')
    op.drop_index('idx_ai_suggestions_analysis_id', table_name='ai_product_suggestions')
    op.drop_table('ai_product_suggestions')

    op.drop_index('idx_ai_analyses_created_at', table_name='ai_product_analyses')
    op.drop_index('idx_ai_analyses_idempotency_key', table_name='ai_product_analyses')
    op.drop_index('idx_ai_analyses_status', table_name='ai_product_analyses')
    op.drop_index('idx_ai_analyses_media_id', table_name='ai_product_analyses')
    op.drop_index('idx_ai_analyses_product_id', table_name='ai_product_analyses')
    op.drop_table('ai_product_analyses')
