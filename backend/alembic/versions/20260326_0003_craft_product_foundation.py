"""Craft product foundation, category hierarchy, artisan-craft linkage, and product moderation

Revision ID: 20260326_0003
Revises: 20260326_0002
Create Date: 2026-03-26 21:35:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260326_0003'
down_revision: Union[str, None] = '20260326_0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Craft Categories: Hierarchical tree
    op.add_column('craft_categories', sa.Column('parent_id', sa.String(length=36), nullable=True))
    op.create_index('idx_craft_cat_parent', 'craft_categories', ['parent_id'])
    op.create_foreign_key('fk_craft_cat_parent', 'craft_categories', 'craft_categories', ['parent_id'], ['id'], ondelete='SET NULL')

    # 2. Crafts: Enriched search and provenance
    op.add_column('crafts', sa.Column('normalized_name', sa.String(length=150), nullable=True))
    op.add_column('crafts', sa.Column('region', sa.String(length=100), nullable=True))
    op.add_column('crafts', sa.Column('traditional_technique', sa.Text(), nullable=True))
    op.add_column('crafts', sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False))
    op.create_index('idx_crafts_norm_name', 'crafts', ['normalized_name'])
    op.create_index('idx_crafts_region', 'crafts', ['region'])
    op.create_index('idx_crafts_is_active', 'crafts', ['is_active'])

    # 3. ArtisanCrafts: Many-to-Many association
    op.create_table(
        'artisan_crafts',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('artisan_id', sa.String(length=36), sa.ForeignKey('artisan_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('craft_id', sa.String(length=36), sa.ForeignKey('crafts.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('skill_level', sa.String(length=50), server_default='SKILLED', nullable=False),
        sa.Column('years_of_experience', sa.Integer(), server_default='1', nullable=False),
        sa.Column('is_primary', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('technique', sa.String(length=150), nullable=True),
        sa.Column('evidence_url', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=30), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('artisan_id', 'craft_id', name='uq_artisan_craft')
    )
    op.create_index('idx_artisan_craft_artisan', 'artisan_crafts', ['artisan_id'])
    op.create_index('idx_artisan_craft_craft', 'artisan_crafts', ['craft_id'])

    # 4. Products: Capacity, lead time, moderation, provenance, and AI data contracts
    op.add_column('products', sa.Column('category_id', sa.String(length=36), sa.ForeignKey('craft_categories.id', ondelete='SET NULL'), nullable=True))
    op.add_column('products', sa.Column('sku', sa.String(length=64), unique=True, nullable=True))
    op.add_column('products', sa.Column('currency', sa.String(length=3), server_default='INR', nullable=False))
    op.add_column('products', sa.Column('monthly_production_capacity', sa.Integer(), server_default='10', nullable=False))
    op.add_column('products', sa.Column('min_order_quantity', sa.Integer(), server_default='1', nullable=False))
    op.add_column('products', sa.Column('lead_time_days', sa.Integer(), server_default='7', nullable=False))
    op.add_column('products', sa.Column('availability_status', sa.String(length=30), server_default='AVAILABLE', nullable=False))
    op.add_column('products', sa.Column('region', sa.String(length=100), nullable=True))
    op.add_column('products', sa.Column('materials', sa.JSON(), server_default='[]', nullable=False))
    op.add_column('products', sa.Column('primary_color', sa.String(length=50), nullable=True))
    op.add_column('products', sa.Column('dimensions', sa.String(length=100), nullable=True))
    op.add_column('products', sa.Column('weight_grams', sa.Integer(), nullable=True))
    op.add_column('products', sa.Column('technique', sa.String(length=150), nullable=True))
    op.add_column('products', sa.Column('style', sa.String(length=100), nullable=True))
    op.add_column('products', sa.Column('tags', sa.JSON(), server_default='[]', nullable=False))
    op.add_column('products', sa.Column('provenance_status', sa.String(length=50), server_default='ARTISAN_DECLARED', nullable=False))
    op.add_column('products', sa.Column('ai_metadata', sa.JSON(), server_default='{}', nullable=False))
    op.add_column('products', sa.Column('admin_feedback', sa.Text(), nullable=True))
    op.add_column('products', sa.Column('moderated_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))
    op.add_column('products', sa.Column('moderated_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index('idx_products_category', 'products', ['category_id'])
    op.create_index('idx_products_sku', 'products', ['sku'])
    op.create_index('idx_products_avail', 'products', ['availability_status'])
    op.create_index('idx_products_region', 'products', ['region'])

    # 5. ProductMedia: Object storage metadata
    op.add_column('product_media', sa.Column('storage_key', sa.String(length=255), nullable=True))
    op.add_column('product_media', sa.Column('checksum_sha256', sa.String(length=64), nullable=True))
    op.add_column('product_media', sa.Column('width', sa.Integer(), nullable=True))
    op.add_column('product_media', sa.Column('height', sa.Integer(), nullable=True))
    op.add_column('product_media', sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False))
    op.add_column('product_media', sa.Column('alt_text', sa.String(length=255), nullable=True))


def downgrade() -> None:
    # 5. Drop media columns
    op.drop_column('product_media', 'alt_text')
    op.drop_column('product_media', 'sort_order')
    op.drop_column('product_media', 'height')
    op.drop_column('product_media', 'width')
    op.drop_column('product_media', 'checksum_sha256')
    op.drop_column('product_media', 'storage_key')

    # 4. Drop product columns and indexes
    op.drop_index('idx_products_region', table_name='products')
    op.drop_index('idx_products_avail', table_name='products')
    op.drop_index('idx_products_sku', table_name='products')
    op.drop_index('idx_products_category', table_name='products')
    op.drop_column('products', 'moderated_at')
    op.drop_column('products', 'moderated_by')
    op.drop_column('products', 'admin_feedback')
    op.drop_column('products', 'ai_metadata')
    op.drop_column('products', 'provenance_status')
    op.drop_column('products', 'tags')
    op.drop_column('products', 'style')
    op.drop_column('products', 'technique')
    op.drop_column('products', 'weight_grams')
    op.drop_column('products', 'dimensions')
    op.drop_column('products', 'primary_color')
    op.drop_column('products', 'materials')
    op.drop_column('products', 'region')
    op.drop_column('products', 'availability_status')
    op.drop_column('products', 'lead_time_days')
    op.drop_column('products', 'min_order_quantity')
    op.drop_column('products', 'monthly_production_capacity')
    op.drop_column('products', 'currency')
    op.drop_column('products', 'sku')
    op.drop_column('products', 'category_id')

    # 3. Drop artisan_crafts
    op.drop_index('idx_artisan_craft_craft', table_name='artisan_crafts')
    op.drop_index('idx_artisan_craft_artisan', table_name='artisan_crafts')
    op.drop_table('artisan_crafts')

    # 2. Drop craft columns and indexes
    op.drop_index('idx_crafts_is_active', table_name='crafts')
    op.drop_index('idx_crafts_region', table_name='crafts')
    op.drop_index('idx_crafts_norm_name', table_name='crafts')
    op.drop_column('crafts', 'is_active')
    op.drop_column('crafts', 'traditional_technique')
    op.drop_column('crafts', 'region')
    op.drop_column('crafts', 'normalized_name')

    # 1. Drop craft_categories columns and indexes
    op.drop_constraint('fk_craft_cat_parent', 'craft_categories', type_='foreignkey')
    op.drop_index('idx_craft_cat_parent', table_name='craft_categories')
    op.drop_column('craft_categories', 'parent_id')
