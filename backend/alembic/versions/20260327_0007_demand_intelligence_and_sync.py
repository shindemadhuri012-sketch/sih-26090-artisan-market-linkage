"""Demand Intelligence & Offline Sync: DemandObservation extension, DemandForecastRun, DemandForecastPoint, and SyncOperation

Revision ID: 20260327_0007
Revises: 20260326_0006
Create Date: 2026-03-27 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260327_0007'
down_revision: Union[str, None] = '20260326_0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Extend DemandObservation
    op.add_column('demand_observations', sa.Column('craft_category_id', sa.String(length=36), sa.ForeignKey('craft_categories.id', ondelete='SET NULL'), nullable=True))
    op.add_column('demand_observations', sa.Column('signal_tier', sa.String(length=30), nullable=False, server_default='TRANSACTIONAL_CONFIRMED'))
    op.add_column('demand_observations', sa.Column('observation_type', sa.String(length=50), nullable=False, server_default='PLATFORM_NATIVE'))
    op.add_column('demand_observations', sa.Column('unit_volume', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('demand_observations', sa.Column('monetary_volume_inr', sa.Numeric(precision=14, scale=2), nullable=True))
    op.add_column('demand_observations', sa.Column('ingestion_batch_id', sa.String(length=64), nullable=True))
    op.add_column('demand_observations', sa.Column('data_quality_status', sa.String(length=30), nullable=False, server_default='VERIFIED'))

    op.create_index('idx_demand_obs_category', 'demand_observations', ['craft_category_id'])
    op.create_index('idx_demand_obs_signal_tier', 'demand_observations', ['signal_tier'])
    op.create_index('idx_demand_obs_batch_id', 'demand_observations', ['ingestion_batch_id'])

    # 2. Demand Forecast Runs Table
    op.create_table(
        'demand_forecast_runs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('craft_id', sa.String(length=36), sa.ForeignKey('crafts.id', ondelete='CASCADE'), nullable=True),
        sa.Column('craft_category_id', sa.String(length=36), sa.ForeignKey('craft_categories.id', ondelete='SET NULL'), nullable=True),
        sa.Column('geography_state', sa.String(length=100), nullable=True),
        sa.Column('model_name', sa.String(length=50), nullable=False),
        sa.Column('model_version', sa.String(length=30), nullable=False, server_default='DEMAND_ENGINE_V1'),
        sa.Column('training_start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('training_end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('validation_start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('validation_end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('test_start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('test_end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('observation_count', sa.Integer(), nullable=False),
        sa.Column('validation_mape', sa.Float(), nullable=True),
        sa.Column('validation_rmse', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='COMPLETED'),
        sa.Column('limitations_notes', sa.Text(), nullable=True),
        sa.Column('parameters_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_forecast_runs_craft', 'demand_forecast_runs', ['craft_id'])
    op.create_index('idx_forecast_runs_category', 'demand_forecast_runs', ['craft_category_id'])
    op.create_index('idx_forecast_runs_state', 'demand_forecast_runs', ['geography_state'])
    op.create_index('idx_forecast_runs_status', 'demand_forecast_runs', ['status'])

    # 3. Demand Forecast Points Table
    op.create_table(
        'demand_forecast_points',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('run_id', sa.String(length=36), sa.ForeignKey('demand_forecast_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('forecast_period_month', sa.Integer(), nullable=False),
        sa.Column('forecast_period_year', sa.Integer(), nullable=False),
        sa.Column('projected_demand_index', sa.Float(), nullable=True),
        sa.Column('projected_unit_volume', sa.Integer(), nullable=True),
        sa.Column('uncertainty_lower', sa.Float(), nullable=True),
        sa.Column('uncertainty_upper', sa.Float(), nullable=True),
        sa.Column('data_sufficiency_status', sa.String(length=40), nullable=False, server_default='FORECAST_AVAILABLE'),
        sa.Column('explanation_note', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_forecast_points_run_id', 'demand_forecast_points', ['run_id'])
    op.create_index('idx_forecast_points_period', 'demand_forecast_points', ['forecast_period_year', 'forecast_period_month'])

    # 4. Sync Operations Table
    op.create_table(
        'sync_operations',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('idempotency_key', sa.String(length=64), nullable=False, unique=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entity_type', sa.String(length=30), nullable=False),
        sa.Column('entity_id', sa.String(length=36), nullable=False),
        sa.Column('operation_type', sa.String(length=30), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='COMMITTED'),
        sa.Column('client_mutation_id', sa.String(length=36), nullable=True),
        sa.Column('response_payload', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_sync_operations_idempotency_key', 'sync_operations', ['idempotency_key'])
    op.create_index('idx_sync_operations_user', 'sync_operations', ['user_id'])
    op.create_index('idx_sync_operations_entity', 'sync_operations', ['entity_type', 'entity_id'])


def downgrade() -> None:
    op.drop_index('idx_sync_operations_entity', table_name='sync_operations')
    op.drop_index('idx_sync_operations_user', table_name='sync_operations')
    op.drop_index('idx_sync_operations_idempotency_key', table_name='sync_operations')
    op.drop_table('sync_operations')

    op.drop_index('idx_forecast_points_period', table_name='demand_forecast_points')
    op.drop_index('idx_forecast_points_run_id', table_name='demand_forecast_points')
    op.drop_table('demand_forecast_points')

    op.drop_index('idx_forecast_runs_status', table_name='demand_forecast_runs')
    op.drop_index('idx_forecast_runs_state', table_name='demand_forecast_runs')
    op.drop_index('idx_forecast_runs_category', table_name='demand_forecast_runs')
    op.drop_index('idx_forecast_runs_craft', table_name='demand_forecast_runs')
    op.drop_table('demand_forecast_runs')

    op.drop_index('idx_demand_obs_batch_id', table_name='demand_observations')
    op.drop_index('idx_demand_obs_signal_tier', table_name='demand_observations')
    op.drop_index('idx_demand_obs_category', table_name='demand_observations')
    op.drop_column('demand_observations', 'data_quality_status')
    op.drop_column('demand_observations', 'ingestion_batch_id')
    op.drop_column('demand_observations', 'monetary_volume_inr')
    op.drop_column('demand_observations', 'unit_volume')
    op.drop_column('demand_observations', 'observation_type')
    op.drop_column('demand_observations', 'signal_tier')
    op.drop_column('demand_observations', 'craft_category_id')
