"""Matching & RFQ Linkage: RequirementUnderstanding staging, buyer requirements extension, matches extension, and RFQ negotiation fields

Revision ID: 20260326_0006
Revises: 20260326_0005
Create Date: 2026-03-27 08:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260326_0006'
down_revision: Union[str, None] = '20260326_0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Requirement Understanding Staging Table
    op.create_table(
        'requirement_understandings',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('requirement_id', sa.String(length=36), sa.ForeignKey('buyer_requirements.id', ondelete='CASCADE'), nullable=False),
        sa.Column('buyer_id', sa.String(length=36), sa.ForeignKey('buyer_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('raw_input_text', sa.Text(), nullable=False),
        sa.Column('extracted_fields_json', sa.JSON(), nullable=False),
        sa.Column('confidence_scores_json', sa.JSON(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False, server_default='gemini'),
        sa.Column('model_name', sa.String(length=100), nullable=False, server_default='gemini-1.5-flash'),
        sa.Column('prompt_version', sa.String(length=50), nullable=False, server_default='rfq_understanding_v1'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='SUGGESTED'),
        sa.Column('is_confirmed_by_buyer', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('confirmed_fields_json', sa.JSON(), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('idx_req_und_req_id', 'requirement_understandings', ['requirement_id'])
    op.create_index('idx_req_und_buyer_id', 'requirement_understandings', ['buyer_id'])
    op.create_index('idx_req_und_status', 'requirement_understandings', ['status'])

    # 2. Alter buyer_requirements
    op.add_column('buyer_requirements', sa.Column('target_category_id', sa.String(length=36), sa.ForeignKey('craft_categories.id', ondelete='SET NULL'), nullable=True))
    op.add_column('buyer_requirements', sa.Column('desired_materials', sa.JSON(), nullable=False, server_default='[]'))
    op.add_column('buyer_requirements', sa.Column('desired_techniques', sa.JSON(), nullable=False, server_default='[]'))
    op.add_column('buyer_requirements', sa.Column('desired_motifs', sa.JSON(), nullable=False, server_default='[]'))
    op.add_column('buyer_requirements', sa.Column('preferred_region', sa.String(length=100), nullable=True))
    op.add_column('buyer_requirements', sa.Column('max_acceptable_moq', sa.Integer(), nullable=True))
    op.add_column('buyer_requirements', sa.Column('max_lead_time_days', sa.Integer(), nullable=True))
    op.add_column('buyer_requirements', sa.Column('requires_customization', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('buyer_requirements', sa.Column('quality_specifications', sa.Text(), nullable=True))
    op.add_column('buyer_requirements', sa.Column('packaging_requirements', sa.Text(), nullable=True))
    op.add_column('buyer_requirements', sa.Column('destination_state', sa.String(length=100), nullable=True))
    op.add_column('buyer_requirements', sa.Column('destination_pincode', sa.String(length=10), nullable=True))
    op.add_column('buyer_requirements', sa.Column('currency', sa.String(length=3), nullable=False, server_default='INR'))
    op.add_column('buyer_requirements', sa.Column('embedding_model_version', sa.String(length=50), nullable=True, server_default='gemini-embedding-2'))
    op.add_column('buyer_requirements', sa.Column('data_provenance_level', sa.String(length=50), nullable=False, server_default='USER_DECLARED'))
    op.add_column('buyer_requirements', sa.Column('provenance_state', sa.String(length=30), nullable=False, server_default='HUMAN_CONFIRMED'))
    op.create_index('idx_buyer_req_category_id', 'buyer_requirements', ['target_category_id'])

    # 3. Alter matches
    op.add_column('matches', sa.Column('product_id', sa.String(length=36), sa.ForeignKey('products.id', ondelete='SET NULL'), nullable=True))
    op.add_column('matches', sa.Column('engine_version', sa.String(length=50), nullable=False, server_default='MATCHING_ENGINE_V1'))
    op.add_column('matches', sa.Column('data_sufficiency_state', sa.String(length=30), nullable=False, server_default='MATCHABLE'))
    op.add_column('matches', sa.Column('craft_compatibility', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('matches', sa.Column('material_compatibility', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('matches', sa.Column('technique_compatibility', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('matches', sa.Column('is_dismissed_by_buyer', sa.Boolean(), nullable=False, server_default='0'))
    op.create_index('idx_matches_product_id', 'matches', ['product_id'])
    op.create_index('idx_matches_sufficiency', 'matches', ['data_sufficiency_state'])

    # 4. Alter match_explanations
    op.add_column('match_explanations', sa.Column('positive_reasons', sa.JSON(), nullable=False, server_default='[]'))
    op.add_column('match_explanations', sa.Column('limitations', sa.JSON(), nullable=False, server_default='[]'))
    op.add_column('match_explanations', sa.Column('unmatched_fields', sa.JSON(), nullable=False, server_default='[]'))
    op.add_column('match_explanations', sa.Column('missing_fields', sa.JSON(), nullable=False, server_default='[]'))

    # 5. Alter enquiries (RFQ Linkage)
    op.add_column('enquiries', sa.Column('rfq_reference_number', sa.String(length=50), nullable=True))
    op.add_column('enquiries', sa.Column('match_id', sa.String(length=36), sa.ForeignKey('matches.id', ondelete='SET NULL'), nullable=True))
    op.add_column('enquiries', sa.Column('currency', sa.String(length=3), nullable=False, server_default='INR'))
    op.add_column('enquiries', sa.Column('artisan_response_message', sa.Text(), nullable=True))
    op.add_column('enquiries', sa.Column('counter_unit_price', sa.Numeric(10, 2), nullable=True))
    op.add_column('enquiries', sa.Column('counter_lead_time_days', sa.Integer(), nullable=True))
    op.add_column('enquiries', sa.Column('decline_reason', sa.String(length=100), nullable=True))
    op.add_column('enquiries', sa.Column('viewed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('enquiries', sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('enquiries', sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index('idx_enquiries_rfq_ref', 'enquiries', ['rfq_reference_number'], unique=True)
    op.create_index('idx_enquiries_match_id', 'enquiries', ['match_id'])


def downgrade() -> None:
    # 5. Revert enquiries
    op.drop_index('idx_enquiries_match_id', table_name='enquiries')
    op.drop_index('idx_enquiries_rfq_ref', table_name='enquiries')
    op.drop_column('enquiries', 'expires_at')
    op.drop_column('enquiries', 'responded_at')
    op.drop_column('enquiries', 'viewed_at')
    op.drop_column('enquiries', 'decline_reason')
    op.drop_column('enquiries', 'counter_lead_time_days')
    op.drop_column('enquiries', 'counter_unit_price')
    op.drop_column('enquiries', 'artisan_response_message')
    op.drop_column('enquiries', 'currency')
    op.drop_column('enquiries', 'match_id')
    op.drop_column('enquiries', 'rfq_reference_number')

    # 4. Revert match_explanations
    op.drop_column('match_explanations', 'missing_fields')
    op.drop_column('match_explanations', 'unmatched_fields')
    op.drop_column('match_explanations', 'limitations')
    op.drop_column('match_explanations', 'positive_reasons')

    # 3. Revert matches
    op.drop_index('idx_matches_sufficiency', table_name='matches')
    op.drop_index('idx_matches_product_id', table_name='matches')
    op.drop_column('matches', 'is_dismissed_by_buyer')
    op.drop_column('matches', 'technique_compatibility')
    op.drop_column('matches', 'material_compatibility')
    op.drop_column('matches', 'craft_compatibility')
    op.drop_column('matches', 'data_sufficiency_state')
    op.drop_column('matches', 'engine_version')
    op.drop_column('matches', 'product_id')

    # 2. Revert buyer_requirements
    op.drop_index('idx_buyer_req_category_id', table_name='buyer_requirements')
    op.drop_column('buyer_requirements', 'provenance_state')
    op.drop_column('buyer_requirements', 'data_provenance_level')
    op.drop_column('buyer_requirements', 'embedding_model_version')
    op.drop_column('buyer_requirements', 'currency')
    op.drop_column('buyer_requirements', 'destination_pincode')
    op.drop_column('buyer_requirements', 'destination_state')
    op.drop_column('buyer_requirements', 'packaging_requirements')
    op.drop_column('buyer_requirements', 'quality_specifications')
    op.drop_column('buyer_requirements', 'requires_customization')
    op.drop_column('buyer_requirements', 'max_lead_time_days')
    op.drop_column('buyer_requirements', 'max_acceptable_moq')
    op.drop_column('buyer_requirements', 'preferred_region')
    op.drop_column('buyer_requirements', 'desired_motifs')
    op.drop_column('buyer_requirements', 'desired_techniques')
    op.drop_column('buyer_requirements', 'desired_materials')
    op.drop_column('buyer_requirements', 'target_category_id')

    # 1. Revert requirement_understandings
    op.drop_index('idx_req_und_status', table_name='requirement_understandings')
    op.drop_index('idx_req_und_buyer_id', table_name='requirement_understandings')
    op.drop_index('idx_req_und_req_id', table_name='requirement_understandings')
    op.drop_table('requirement_understandings')
