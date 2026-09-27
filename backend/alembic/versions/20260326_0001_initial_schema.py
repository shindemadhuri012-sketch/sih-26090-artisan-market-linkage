"""Initial database schema with 23 core entities and pgvector support

Revision ID: 20260326_0001
Revises: 
Create Date: 2026-03-26 14:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None

# revision identifiers, used by Alembic.
revision: str = '20260326_0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension if PostgreSQL dialect
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 1. roles
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('permissions_json', sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('idx_roles_name', 'roles', ['name'])

    # 2. users
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('phone_number', sa.String(length=15), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=30), nullable=False, server_default='artisan'),
        sa.Column('preferred_language', sa.String(length=10), nullable=False, server_default='en'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('phone_number'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_users_phone', 'users', ['phone_number'])
    op.create_index('idx_users_role', 'users', ['role'])

    # 3. audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('actor_user_id', sa.String(length=36), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=36), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('payload_before_json', sa.JSON(), nullable=True),
        sa.Column('payload_after_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_entity', 'audit_logs', ['entity_type', 'entity_id'])

    # 4. notifications
    op.create_table(
        'notifications',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('channel', sa.String(length=20), nullable=False, server_default='IN_APP'),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_notifications_user', 'notifications', ['user_id', 'is_read'])

    # 5. data_sources
    op.create_table(
        'data_sources',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('source_identifier', sa.String(length=100), nullable=False),
        sa.Column('source_name', sa.String(length=200), nullable=False),
        sa.Column('custodian_organization', sa.String(length=200), nullable=False),
        sa.Column('official_url', sa.Text(), nullable=False),
        sa.Column('license_type', sa.String(length=100), nullable=False),
        sa.Column('is_active_feed', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_identifier')
    )

    # 6. data_imports
    op.create_table(
        'data_imports',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('data_source_id', sa.String(length=36), nullable=False),
        sa.Column('import_version', sa.String(length=50), nullable=False),
        sa.Column('records_extracted', sa.Integer(), nullable=False),
        sa.Column('records_ingested', sa.Integer(), nullable=False),
        sa.Column('records_failed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('checksum_hash', sa.String(length=64), nullable=False),
        sa.Column('report_json', sa.JSON(), nullable=False),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['data_source_id'], ['data_sources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 7. craft_categories
    op.create_table(
        'craft_categories',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # 8. crafts
    op.create_table(
        'crafts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('category_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('gi_tag_number', sa.String(length=50), nullable=True),
        sa.Column('has_gi_tag', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('origin_state', sa.String(length=100), nullable=False),
        sa.Column('origin_district', sa.String(length=100), nullable=False),
        sa.Column('cultural_heritage_description', sa.Text(), nullable=False),
        sa.Column('traditional_raw_materials', sa.JSON(), nullable=False),
        sa.Column('data_source_id', sa.String(length=36), nullable=True),
        sa.Column('is_sample_or_demo', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('data_provenance_level', sa.String(length=50), nullable=False),
        sa.Column('provenance_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['craft_categories.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['data_source_id'], ['data_sources.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('gi_tag_number')
    )
    op.create_index('idx_crafts_gi', 'crafts', ['gi_tag_number'])
    op.create_index('idx_crafts_origin', 'crafts', ['origin_state', 'origin_district'])

    # 9. artisan_profiles
    op.create_table(
        'artisan_profiles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('full_name', sa.String(length=150), nullable=False),
        sa.Column('cooperative_name', sa.String(length=200), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=False),
        sa.Column('district', sa.String(length=100), nullable=False),
        sa.Column('pincode', sa.String(length=10), nullable=False),
        sa.Column('address_line', sa.Text(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('primary_craft_id', sa.String(length=36), nullable=False),
        sa.Column('years_of_experience', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('monthly_production_capacity', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('pehchan_id', sa.String(length=50), nullable=True),
        sa.Column('verification_status', sa.String(length=30), nullable=False, server_default='PENDING'),
        sa.Column('is_sample_or_demo', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('data_provenance_level', sa.String(length=50), nullable=False),
        sa.Column('provenance_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['primary_craft_id'], ['crafts.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
        sa.UniqueConstraint('pehchan_id')
    )
    op.create_index('idx_artisan_district', 'artisan_profiles', ['state', 'district'])

    # 10. verifications
    op.create_table(
        'verifications',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('artisan_id', sa.String(length=36), nullable=False),
        sa.Column('verifier_user_id', sa.String(length=36), nullable=True),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('document_url', sa.Text(), nullable=False),
        sa.Column('verification_status', sa.String(length=30), nullable=False, server_default='SUBMITTED'),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['artisan_id'], ['artisan_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['verifier_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 11. craft_passports
    op.create_table(
        'craft_passports',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('artisan_id', sa.String(length=36), nullable=False),
        sa.Column('craft_id', sa.String(length=36), nullable=False),
        sa.Column('passport_uuid', sa.String(length=64), nullable=False),
        sa.Column('qr_code_url', sa.Text(), nullable=False),
        sa.Column('authorized_user_gi_certificate', sa.Text(), nullable=True),
        sa.Column('verification_level', sa.String(length=30), nullable=False, server_default='SELF_DECLARED'),
        sa.Column('issued_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('provenance_hash', sa.String(length=64), nullable=False),
        sa.Column('is_sample_or_demo', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('data_provenance_level', sa.String(length=50), nullable=False),
        sa.Column('provenance_metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['artisan_id'], ['artisan_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['craft_id'], ['crafts.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('passport_uuid')
    )

    # 12. products
    vector_type = Vector(768) if bind.dialect.name == "postgresql" and Vector else sa.Text()
    op.create_table(
        'products',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('artisan_id', sa.String(length=36), nullable=False),
        sa.Column('craft_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('storytelling_description', sa.Text(), nullable=False),
        sa.Column('ai_generated_description', sa.Text(), nullable=True),
        sa.Column('is_ai_description_confirmed', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('price_inr', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('estimated_production_days', sa.Integer(), nullable=False, server_default='7'),
        sa.Column('stock_quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_customizable', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('embedding', vector_type, nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='DRAFT'),
        sa.Column('is_sample_or_demo', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('data_provenance_level', sa.String(length=50), nullable=False),
        sa.Column('provenance_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['artisan_id'], ['artisan_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['craft_id'], ['crafts.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_products_artisan', 'products', ['artisan_id'])
    op.create_index('idx_products_craft', 'products', ['craft_id'])

    # 13. product_media
    op.create_table(
        'product_media',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.Column('media_type', sa.String(length=20), nullable=False, server_default='IMAGE'),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('thumbnail_url', sa.Text(), nullable=True),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(length=50), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 14. product_attributes
    op.create_table(
        'product_attributes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.Column('primary_material', sa.String(length=100), nullable=False),
        sa.Column('technique', sa.String(length=100), nullable=False),
        sa.Column('dimensions_cm', sa.JSON(), nullable=True),
        sa.Column('weight_grams', sa.Integer(), nullable=True),
        sa.Column('colors', sa.JSON(), nullable=False),
        sa.Column('care_instructions', sa.Text(), nullable=True),
        sa.Column('ai_confidence_score', sa.Float(), nullable=True),
        sa.Column('raw_attributes_json', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id')
    )

    # 15. price_analyses
    op.create_table(
        'price_analyses',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.Column('raw_material_cost', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('labor_hours', sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column('skill_level_hourly_rate', sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column('consumables_overhead_cost', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('packaging_logistics_cost', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('calculated_total_cost', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('fair_margin_percentage', sa.Numeric(precision=5, scale=2), nullable=False, server_default='25.0'),
        sa.Column('recommended_floor_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('recommended_fair_retail_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('market_benchmark_reference', sa.Text(), nullable=True),
        sa.Column('confidence_indicator', sa.String(length=30), nullable=False, server_default='USER_SELF_REPORTED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 16. buyer_profiles
    op.create_table(
        'buyer_profiles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('company_name', sa.String(length=200), nullable=False),
        sa.Column('buyer_type', sa.String(length=50), nullable=False),
        sa.Column('gstin', sa.String(length=20), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=False, server_default='India'),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('typical_order_volume', sa.String(length=50), nullable=True),
        sa.Column('is_verified_buyer', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('is_sample_or_demo', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('data_provenance_level', sa.String(length=50), nullable=False),
        sa.Column('provenance_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    # 17. buyer_requirements
    op.create_table(
        'buyer_requirements',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('buyer_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=False),
        sa.Column('target_craft_id', sa.String(length=36), nullable=True),
        sa.Column('required_quantity', sa.Integer(), nullable=False),
        sa.Column('target_unit_price_inr', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('max_budget_inr', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('deadline_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('requires_gi_certification', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('material_constraints', sa.JSON(), nullable=False),
        sa.Column('embedding', vector_type, nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='OPEN'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['buyer_id'], ['buyer_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_craft_id'], ['crafts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_buyer_req_buyer', 'buyer_requirements', ['buyer_id'])

    # 18. matches
    op.create_table(
        'matches',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('requirement_id', sa.String(length=36), nullable=False),
        sa.Column('artisan_id', sa.String(length=36), nullable=False),
        sa.Column('composite_score', sa.Float(), nullable=False),
        sa.Column('semantic_similarity', sa.Float(), nullable=False),
        sa.Column('capacity_compatibility', sa.Float(), nullable=False),
        sa.Column('price_compatibility', sa.Float(), nullable=False),
        sa.Column('lead_time_compatibility', sa.Float(), nullable=False),
        sa.Column('provenance_bonus', sa.Float(), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='PROPOSED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['artisan_id'], ['artisan_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['requirement_id'], ['buyer_requirements.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_matches_req_rank', 'matches', ['requirement_id', 'rank'])

    # 19. match_explanations
    op.create_table(
        'match_explanations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('match_id', sa.String(length=36), nullable=False),
        sa.Column('summary_explanation', sa.Text(), nullable=False),
        sa.Column('capacity_justification', sa.Text(), nullable=False),
        sa.Column('price_justification', sa.Text(), nullable=False),
        sa.Column('provenance_justification', sa.Text(), nullable=False),
        sa.Column('factors_json', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('match_id')
    )

    # 20. enquiries
    op.create_table(
        'enquiries',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('buyer_id', sa.String(length=36), nullable=False),
        sa.Column('artisan_id', sa.String(length=36), nullable=False),
        sa.Column('requirement_id', sa.String(length=36), nullable=True),
        sa.Column('product_id', sa.String(length=36), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('proposed_quantity', sa.Integer(), nullable=False),
        sa.Column('proposed_unit_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['artisan_id'], ['artisan_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['buyer_id'], ['buyer_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['requirement_id'], ['buyer_requirements.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 21. orders
    op.create_table(
        'orders',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('enquiry_id', sa.String(length=36), nullable=False),
        sa.Column('order_reference_number', sa.String(length=50), nullable=False),
        sa.Column('total_amount_inr', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('artisan_realization_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('fulfillment_status', sa.String(length=30), nullable=False, server_default='CONFIRMED'),
        sa.Column('tracking_consignment_number', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['enquiry_id'], ['enquiries.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('enquiry_id'),
        sa.UniqueConstraint('order_reference_number')
    )

    # 22. demand_observations
    op.create_table(
        'demand_observations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('craft_id', sa.String(length=36), nullable=False),
        sa.Column('geography_state', sa.String(length=100), nullable=False),
        sa.Column('observation_period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('observation_period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_enquiries', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('fulfilled_orders', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('average_realized_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('seasonal_festival_tag', sa.String(length=50), nullable=True),
        sa.Column('data_source_id', sa.String(length=36), nullable=True),
        sa.Column('is_sample_or_demo', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('data_provenance_level', sa.String(length=50), nullable=False),
        sa.Column('provenance_metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['craft_id'], ['crafts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['data_source_id'], ['data_sources.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_demand_craft_period', 'demand_observations', ['craft_id', 'observation_period_start'])

    # 23. demand_forecasts
    op.create_table(
        'demand_forecasts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('craft_id', sa.String(length=36), nullable=False),
        sa.Column('forecast_period_month', sa.Integer(), nullable=False),
        sa.Column('forecast_period_year', sa.Integer(), nullable=False),
        sa.Column('projected_demand_index', sa.Float(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('data_sufficiency_status', sa.String(length=40), nullable=False, server_default='INSUFFICIENT_HISTORICAL_DATA'),
        sa.Column('explanation_note', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['craft_id'], ['crafts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Drop tables in reverse topological order
    op.drop_table('demand_forecasts')
    op.drop_table('demand_observations')
    op.drop_table('orders')
    op.drop_table('enquiries')
    op.drop_table('match_explanations')
    op.drop_table('matches')
    op.drop_table('buyer_requirements')
    op.drop_table('buyer_profiles')
    op.drop_table('price_analyses')
    op.drop_table('product_attributes')
    op.drop_table('product_media')
    op.drop_table('products')
    op.drop_table('craft_passports')
    op.drop_table('verifications')
    op.drop_table('artisan_profiles')
    op.drop_table('crafts')
    op.drop_table('craft_categories')
    op.drop_table('data_imports')
    op.drop_table('data_sources')
    op.drop_table('notifications')
    op.drop_table('audit_logs')
    op.drop_table('users')
    op.drop_table('roles')
