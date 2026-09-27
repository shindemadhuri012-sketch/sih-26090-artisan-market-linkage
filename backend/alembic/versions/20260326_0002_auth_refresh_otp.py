"""Auth refresh token rotation, OTP challenges, and passport verification extensions

Revision ID: 20260326_0002
Revises: 20260326_0001
Create Date: 2026-03-26 15:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20260326_0002'
down_revision: Union[str, None] = '20260326_0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. refresh_token_sessions
    op.create_table(
        'refresh_token_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('token_family', sa.String(length=36), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash')
    )
    op.create_index('idx_refresh_user', 'refresh_token_sessions', ['user_id'])
    op.create_index('idx_refresh_family', 'refresh_token_sessions', ['token_family'])
    op.create_index('idx_refresh_token_hash', 'refresh_token_sessions', ['token_hash'])

    # 2. otp_challenges
    op.create_table(
        'otp_challenges',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('phone_number', sa.String(length=15), nullable=False),
        sa.Column('otp_code_hash', sa.String(length=64), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('is_consumed', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_otp_phone', 'otp_challenges', ['phone_number'])
    op.create_index('idx_otp_expires', 'otp_challenges', ['expires_at'])

    # 3. Add status column to craft_passports
    op.add_column(
        'craft_passports',
        sa.Column('status', sa.String(length=30), nullable=False, server_default='DRAFT')
    )
    op.create_index('idx_craft_passports_status', 'craft_passports', ['status'])

    # 4. Add admin_notes and decision_date to verifications
    op.add_column('verifications', sa.Column('admin_notes', sa.Text(), nullable=True))
    op.add_column('verifications', sa.Column('decision_date', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('verifications', 'decision_date')
    op.drop_column('verifications', 'admin_notes')
    op.drop_index('idx_craft_passports_status', table_name='craft_passports')
    op.drop_column('craft_passports', 'status')
    op.drop_index('idx_otp_expires', table_name='otp_challenges')
    op.drop_index('idx_otp_phone', table_name='otp_challenges')
    op.drop_table('otp_challenges')
    op.drop_index('idx_refresh_token_hash', table_name='refresh_token_sessions')
    op.drop_index('idx_refresh_family', table_name='refresh_token_sessions')
    op.drop_index('idx_refresh_user', table_name='refresh_token_sessions')
    op.drop_table('refresh_token_sessions')
