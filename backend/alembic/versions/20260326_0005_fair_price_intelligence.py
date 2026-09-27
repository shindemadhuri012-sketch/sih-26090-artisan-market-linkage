"""Fair-Price Intelligence: product cost breakdowns, market price observations, and enhanced price analysis

Revision ID: 20260326_0005
Revises: 20260326_0004
Create Date: 2026-03-26 22:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260326_0005'
down_revision: Union[str, None] = '20260326_0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Product Cost Breakdowns table
    op.create_table(
        'product_cost_breakdowns',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('product_id', sa.String(length=36), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('artisan_id', sa.String(length=36), sa.ForeignKey('artisan_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('materials', sa.JSON(), nullable=False),
        sa.Column('total_material_cost', sa.Numeric(12, 2), nullable=False, server_default='0.00'),
        sa.Column('labor_calculation_method', sa.String(length=30), nullable=False, server_default='HOURLY_RATE'),
        sa.Column('labor_hours', sa.Numeric(6, 2), nullable=True),
        sa.Column('hourly_labor_rate', sa.Numeric(8, 2), nullable=True),
        sa.Column('total_labor_cost', sa.Numeric(12, 2), nullable=False, server_default='0.00'),
        sa.Column('packaging_cost', sa.Numeric(10, 2), nullable=False, server_default='0.00'),
        sa.Column('transport_cost', sa.Numeric(10, 2), nullable=False, server_default='0.00'),
        sa.Column('overhead_cost', sa.Numeric(10, 2), nullable=False, server_default='0.00'),
        sa.Column('overhead_allocation_basis', sa.String(length=40), nullable=False, server_default='PER_PRODUCT'),
        sa.Column('other_costs', sa.Numeric(10, 2), nullable=False, server_default='0.00'),
        sa.Column('other_costs_description', sa.Text(), nullable=True),
        sa.Column('batch_quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='INR'),
        sa.Column('current_selling_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('desired_margin_percentage', sa.Numeric(5, 2), nullable=False, server_default='25.00'),
        sa.Column('total_production_cost', sa.Numeric(12, 2), nullable=False, server_default='0.00'),
        sa.Column('cost_baseline_unit_cost', sa.Numeric(12, 2), nullable=False, server_default='0.00'),
        sa.Column('cost_baseline_recommended_price', sa.Numeric(12, 2), nullable=False, server_default='0.00'),
        sa.Column('provenance_status', sa.String(length=40), nullable=False, server_default='ARTISAN_PROVIDED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('idx_cost_breakdowns_product_id', 'product_cost_breakdowns', ['product_id'])
    op.create_index('idx_cost_breakdowns_artisan_id', 'product_cost_breakdowns', ['artisan_id'])

    # 2. Market Price Observations table
    op.create_table(
        'market_price_observations',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('craft_id', sa.String(length=36), sa.ForeignKey('crafts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('craft_category_id', sa.String(length=36), sa.ForeignKey('craft_categories.id', ondelete='SET NULL'), nullable=True),
        sa.Column('product_title', sa.String(length=255), nullable=True),
        sa.Column('observed_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='INR'),
        sa.Column('source_name', sa.String(length=255), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('source_type', sa.String(length=50), nullable=False, server_default='GOVERNMENT'),
        sa.Column('geography_state', sa.String(length=100), nullable=True),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('observation_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('retrieval_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('original_source_id', sa.String(length=100), nullable=True),
        sa.Column('license_or_usage_info', sa.Text(), nullable=True),
        sa.Column('attributes_json', sa.JSON(), nullable=False),
        sa.Column('comparability_tags', sa.JSON(), nullable=False),
        sa.Column('evidence_quality_status', sa.String(length=30), nullable=False, server_default='MEDIUM'),
        sa.Column('verification_status', sa.String(length=30), nullable=False, server_default='DOCUMENTED'),
        sa.Column('data_source_id', sa.String(length=36), sa.ForeignKey('data_sources.id', ondelete='SET NULL'), nullable=True),
        sa.Column('data_provenance_level', sa.String(length=50), nullable=False, server_default='SOURCE_BACKED'),
        sa.Column('is_sample_or_demo', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('provenance_metadata', sa.JSON(), nullable=False),
        sa.Column('ingestion_batch_id', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('idx_mkt_obs_craft_id', 'market_price_observations', ['craft_id'])
    op.create_index('idx_mkt_obs_category_id', 'market_price_observations', ['craft_category_id'])
    op.create_index('idx_mkt_obs_state', 'market_price_observations', ['geography_state'])
    op.create_index('idx_mkt_obs_date', 'market_price_observations', ['observation_date'])
    op.create_index('idx_mkt_obs_sample', 'market_price_observations', ['is_sample_or_demo'])
    op.create_index('idx_mkt_obs_batch', 'market_price_observations', ['ingestion_batch_id'])

    # 3. Enhance Price Analyses table
    op.add_column('price_analyses', sa.Column('artisan_id', sa.String(length=36), sa.ForeignKey('artisan_profiles.id', ondelete='CASCADE'), nullable=True))
    op.add_column('price_analyses', sa.Column('cost_breakdown_id', sa.String(length=36), sa.ForeignKey('product_cost_breakdowns.id', ondelete='SET NULL'), nullable=True))
    op.add_column('price_analyses', sa.Column('engine_version', sa.String(length=50), nullable=False, server_default='FAIR_PRICE_ENGINE_V1'))
    op.add_column('price_analyses', sa.Column('currency', sa.String(length=3), nullable=False, server_default='INR'))
    op.add_column('price_analyses', sa.Column('fair_price_min', sa.Numeric(10, 2), nullable=True))
    op.add_column('price_analyses', sa.Column('fair_price_max', sa.Numeric(10, 2), nullable=True))
    op.add_column('price_analyses', sa.Column('fair_price_recommended', sa.Numeric(10, 2), nullable=True))
    op.add_column('price_analyses', sa.Column('evidence_status', sa.String(length=50), nullable=False, server_default='COST_ONLY_BASELINE'))
    op.add_column('price_analyses', sa.Column('market_sample_size', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('price_analyses', sa.Column('market_median_price', sa.Numeric(10, 2), nullable=True))
    op.add_column('price_analyses', sa.Column('market_min_price', sa.Numeric(10, 2), nullable=True))
    op.add_column('price_analyses', sa.Column('market_max_price', sa.Numeric(10, 2), nullable=True))
    op.add_column('price_analyses', sa.Column('market_iqr_low', sa.Numeric(10, 2), nullable=True))
    op.add_column('price_analyses', sa.Column('market_iqr_high', sa.Numeric(10, 2), nullable=True))
    op.add_column('price_analyses', sa.Column('input_snapshot_json', sa.JSON(), nullable=False, server_default='{}'))
    op.add_column('price_analyses', sa.Column('comparable_observations_json', sa.JSON(), nullable=False, server_default='[]'))
    op.add_column('price_analyses', sa.Column('explanation_steps', sa.JSON(), nullable=False, server_default='[]'))
    op.add_column('price_analyses', sa.Column('limitations_notes', sa.JSON(), nullable=False, server_default='[]'))
    op.add_column('price_analyses', sa.Column('provenance_state', sa.String(length=50), nullable=False, server_default='CALCULATED'))
    op.add_column('price_analyses', sa.Column('is_confirmed_by_artisan', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('price_analyses', sa.Column('confirmed_price_inr', sa.Numeric(10, 2), nullable=True))
    op.add_column('price_analyses', sa.Column('artisan_notes', sa.Text(), nullable=True))
    op.add_column('price_analyses', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))

    op.create_index('idx_price_analyses_artisan_id', 'price_analyses', ['artisan_id'])
    op.create_index('idx_price_analyses_cost_breakdown_id', 'price_analyses', ['cost_breakdown_id'])


def downgrade() -> None:
    # 1. Revert Price Analyses additions
    op.drop_index('idx_price_analyses_cost_breakdown_id', 'price_analyses')
    op.drop_index('idx_price_analyses_artisan_id', 'price_analyses')
    op.drop_column('price_analyses', 'updated_at')
    op.drop_column('price_analyses', 'artisan_notes')
    op.drop_column('price_analyses', 'confirmed_price_inr')
    op.drop_column('price_analyses', 'is_confirmed_by_artisan')
    op.drop_column('price_analyses', 'provenance_state')
    op.drop_column('price_analyses', 'limitations_notes')
    op.drop_column('price_analyses', 'explanation_steps')
    op.drop_column('price_analyses', 'comparable_observations_json')
    op.drop_column('price_analyses', 'input_snapshot_json')
    op.drop_column('price_analyses', 'market_iqr_high')
    op.drop_column('price_analyses', 'market_iqr_low')
    op.drop_column('price_analyses', 'market_max_price')
    op.drop_column('price_analyses', 'market_min_price')
    op.drop_column('price_analyses', 'market_median_price')
    op.drop_column('price_analyses', 'market_sample_size')
    op.drop_column('price_analyses', 'evidence_status')
    op.drop_column('price_analyses', 'fair_price_recommended')
    op.drop_column('price_analyses', 'fair_price_max')
    op.drop_column('price_analyses', 'fair_price_min')
    op.drop_column('price_analyses', 'currency')
    op.drop_column('price_analyses', 'engine_version')
    op.drop_column('price_analyses', 'cost_breakdown_id')
    op.drop_column('price_analyses', 'artisan_id')

    # 2. Drop Market Price Observations table
    op.drop_index('idx_mkt_obs_batch', 'market_price_observations')
    op.drop_index('idx_mkt_obs_sample', 'market_price_observations')
    op.drop_index('idx_mkt_obs_date', 'market_price_observations')
    op.drop_index('idx_mkt_obs_state', 'market_price_observations')
    op.drop_index('idx_mkt_obs_category_id', 'market_price_observations')
    op.drop_index('idx_mkt_obs_craft_id', 'market_price_observations')
    op.drop_table('market_price_observations')

    # 3. Drop Product Cost Breakdowns table
    op.drop_index('idx_cost_breakdowns_artisan_id', 'product_cost_breakdowns')
    op.drop_index('idx_cost_breakdowns_product_id', 'product_cost_breakdowns')
    op.drop_table('product_cost_breakdowns')
