"""governance_moderation_and_provenance

Revision ID: 20260327_0008
Revises: 20260327_0007
Create Date: 2026-09-27 09:05:00.000000

Phase 8 Migration: Admin Moderation, Governance & Provenance Auditing Layer.
Adds governance_flags, moderation_actions, and provenance_events tables.
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260327_0008'
down_revision: Union[str, None] = '20260327_0007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create governance_flags table
    op.create_table(
        'governance_flags',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=36), nullable=False),
        sa.Column('flag_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), server_default='MEDIUM', nullable=False),
        sa.Column('status', sa.String(length=30), server_default='OPEN', nullable=False),
        sa.Column('details_json', sa.JSON(), nullable=False),
        sa.Column('flagged_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('assigned_to_user_id', sa.String(length=36), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('resolved_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['assigned_to_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['flagged_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['resolved_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_governance_flags_created_at'), 'governance_flags', ['created_at'], unique=False)
    op.create_index(op.f('ix_governance_flags_entity_id'), 'governance_flags', ['entity_id'], unique=False)
    op.create_index(op.f('ix_governance_flags_entity_type'), 'governance_flags', ['entity_type'], unique=False)
    op.create_index(op.f('ix_governance_flags_flag_type'), 'governance_flags', ['flag_type'], unique=False)
    op.create_index(op.f('ix_governance_flags_flagged_by_user_id'), 'governance_flags', ['flagged_by_user_id'], unique=False)
    op.create_index(op.f('ix_governance_flags_assigned_to_user_id'), 'governance_flags', ['assigned_to_user_id'], unique=False)
    op.create_index(op.f('ix_governance_flags_severity'), 'governance_flags', ['severity'], unique=False)
    op.create_index(op.f('ix_governance_flags_status'), 'governance_flags', ['status'], unique=False)
    op.create_index('idx_gov_flags_entity_status', 'governance_flags', ['entity_type', 'entity_id', 'status'], unique=False)
    op.create_index('idx_gov_flags_severity_status', 'governance_flags', ['severity', 'status'], unique=False)

    # 2. Create moderation_actions table
    op.create_table(
        'moderation_actions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=36), nullable=False),
        sa.Column('previous_status', sa.String(length=50), nullable=True),
        sa.Column('new_status', sa.String(length=50), nullable=False),
        sa.Column('decision', sa.String(length=50), nullable=False),
        sa.Column('moderator_user_id', sa.String(length=36), nullable=True),
        sa.Column('reason_category', sa.String(length=100), nullable=True),
        sa.Column('moderator_notes', sa.Text(), nullable=True),
        sa.Column('feedback_to_user', sa.Text(), nullable=True),
        sa.Column('evidence_reference', sa.Text(), nullable=True),
        sa.Column('idempotency_key', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['moderator_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_moderation_actions_created_at'), 'moderation_actions', ['created_at'], unique=False)
    op.create_index(op.f('ix_moderation_actions_decision'), 'moderation_actions', ['decision'], unique=False)
    op.create_index(op.f('ix_moderation_actions_entity_id'), 'moderation_actions', ['entity_id'], unique=False)
    op.create_index(op.f('ix_moderation_actions_entity_type'), 'moderation_actions', ['entity_type'], unique=False)
    op.create_index(op.f('ix_moderation_actions_idempotency_key'), 'moderation_actions', ['idempotency_key'], unique=True)
    op.create_index(op.f('ix_moderation_actions_moderator_user_id'), 'moderation_actions', ['moderator_user_id'], unique=False)
    op.create_index('idx_mod_actions_entity_created', 'moderation_actions', ['entity_type', 'entity_id', 'created_at'], unique=False)

    # 3. Create provenance_events table
    op.create_table(
        'provenance_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=36), nullable=False),
        sa.Column('field_name', sa.String(length=100), nullable=False),
        sa.Column('previous_value_json', sa.JSON(), nullable=True),
        sa.Column('new_value_json', sa.JSON(), nullable=False),
        sa.Column('provenance_state', sa.String(length=50), nullable=False),
        sa.Column('actor_user_id', sa.String(length=36), nullable=True),
        sa.Column('actor_role', sa.String(length=30), server_default='artisan', nullable=False),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('source_id', sa.String(length=100), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('evidence_reference', sa.Text(), nullable=True),
        sa.Column('ai_model_version', sa.String(length=50), nullable=True),
        sa.Column('prompt_version', sa.String(length=50), nullable=True),
        sa.Column('human_confirmation_status', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('event_hash', sa.String(length=64), nullable=False),
        sa.Column('previous_event_hash', sa.String(length=64), nullable=False),
        sa.Column('sequence_number', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_provenance_events_created_at'), 'provenance_events', ['created_at'], unique=False)
    op.create_index(op.f('ix_provenance_events_entity_id'), 'provenance_events', ['entity_id'], unique=False)
    op.create_index(op.f('ix_provenance_events_entity_type'), 'provenance_events', ['entity_type'], unique=False)
    op.create_index(op.f('ix_provenance_events_event_hash'), 'provenance_events', ['event_hash'], unique=False)
    op.create_index(op.f('ix_provenance_events_field_name'), 'provenance_events', ['field_name'], unique=False)
    op.create_index(op.f('ix_provenance_events_provenance_state'), 'provenance_events', ['provenance_state'], unique=False)
    op.create_index('idx_prov_events_entity_field', 'provenance_events', ['entity_type', 'entity_id', 'field_name'], unique=False)
    op.create_index('idx_prov_events_entity_seq', 'provenance_events', ['entity_type', 'entity_id', 'sequence_number'], unique=False)


def downgrade() -> None:
    op.drop_table('provenance_events')
    op.drop_table('moderation_actions')
    op.drop_table('governance_flags')
