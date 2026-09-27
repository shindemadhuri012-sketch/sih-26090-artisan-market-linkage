"""
SIH 26090: Product Catalogue, Media & Moderation API Endpoints
Provides artisan product management, inventory vs capacity separation,
media metadata handling, deterministic public catalogue search, and audited administrative moderation.
"""

import secrets
from datetime import datetime, timezone
from math import ceil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_async_db
from backend.app.core.permissions import get_current_user, require_roles
from backend.app.models.auth import User
from backend.app.models.artisan import ArtisanProfile
from backend.app.models.craft import Craft, CraftCategory, CraftPassport
from backend.app.models.product import Product, ProductMedia
from backend.app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductPublicResponse,
    ProductListResponse,
    ProductMediaCreate,
    ProductMediaResponse,
    ProductModerationRequest
)
from backend.app.services.audit_service import record_audit_event

router = APIRouter(tags=["Products & Catalogue"])


# ==========================================
# ARTISAN PRODUCT MANAGEMENT
# ==========================================

@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    current_user: User = Depends(require_roles(["artisan"])),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Creates a new artisanal craft product listing in DRAFT status.
    Generates public SKU, initial AI suggestion contract placeholder, and associates craft.
    """
    art_res = await db.execute(select(ArtisanProfile).where(ArtisanProfile.user_id == current_user.id))
    artisan = art_res.scalar_one_or_none()
    if not artisan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must complete your artisan profile before creating products."
        )

    # Verify craft exists
    craft_res = await db.execute(select(Craft).where(Craft.id == payload.craft_id))
    craft = craft_res.scalar_one_or_none()
    if not craft:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Specified craft_id '{payload.craft_id}' does not exist in master catalogue."
        )

    # Optional category verification
    if payload.category_id:
        cat_res = await db.execute(select(CraftCategory).where(CraftCategory.id == payload.category_id))
        if not cat_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Specified category_id '{payload.category_id}' does not exist."
            )

    sku = f"PRD-{secrets.token_hex(4).upper()}"

    # AI Suggestion Data Contract placeholder:
    ai_contract = {
        "title_suggestion": None,
        "description_suggestion": None,
        "suggested_tags": [],
        "suggested_materials": [],
        "confidence": None,
        "model_name": None,
        "timestamp": None,
        "human_confirmed": False
    }

    product = Product(
        artisan_id=artisan.id,
        craft_id=payload.craft_id,
        category_id=payload.category_id,
        sku=sku,
        title=payload.title,
        storytelling_description=payload.storytelling_description,
        price_inr=payload.price_inr,
        currency="INR",
        stock_quantity=payload.stock_quantity,
        monthly_production_capacity=payload.monthly_production_capacity,
        min_order_quantity=payload.min_order_quantity,
        lead_time_days=payload.lead_time_days,
        availability_status=payload.availability_status,
        region=payload.region or f"{artisan.district}, {artisan.state}",
        materials=payload.materials,
        primary_color=payload.primary_color,
        dimensions=payload.dimensions,
        weight_grams=payload.weight_grams,
        technique=payload.technique,
        style=payload.style,
        tags=payload.tags,
        is_customizable=payload.is_customizable,
        status="DRAFT",
        provenance_status="ARTISAN_DECLARED",
        ai_metadata=ai_contract,
        is_sample_or_demo=False,
        data_provenance_level="USER_DECLARED"
    )
    db.add(product)
    await db.flush()
    await db.refresh(product)

    await record_audit_event(
        db=db,
        action="PRODUCT_CREATED",
        entity_type="Product",
        entity_id=product.id,
        actor_user_id=current_user.id,
        payload_after={"title": product.title, "sku": product.sku, "status": "DRAFT"}
    )

    return ProductResponse(
        id=product.id,
        artisan_id=product.artisan_id,
        craft_id=product.craft_id,
        category_id=product.category_id,
        craft_name=craft.name,
        sku=product.sku,
        title=product.title,
        storytelling_description=product.storytelling_description,
        price_inr=float(product.price_inr),
        currency=product.currency,
        stock_quantity=product.stock_quantity,
        monthly_production_capacity=product.monthly_production_capacity,
        min_order_quantity=product.min_order_quantity,
        lead_time_days=product.lead_time_days,
        availability_status=product.availability_status,
        region=product.region,
        materials=product.materials,
        primary_color=product.primary_color,
        dimensions=product.dimensions,
        weight_grams=product.weight_grams,
        technique=product.technique,
        style=product.style,
        tags=product.tags,
        is_customizable=product.is_customizable,
        status=product.status,
        provenance_status=product.provenance_status,
        ai_metadata=product.ai_metadata,
        admin_feedback=product.admin_feedback,
        media=[],
        created_at=product.created_at.isoformat() if product.created_at else "",
        updated_at=product.updated_at.isoformat() if product.updated_at else ""
    )


@router.get("/artisans/me/products", response_model=List[ProductResponse])
async def list_my_products(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_roles(["artisan"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Lists all products created by the authenticated artisan across all lifecycle states."""
    art_res = await db.execute(select(ArtisanProfile).where(ArtisanProfile.user_id == current_user.id))
    artisan = art_res.scalar_one_or_none()
    if not artisan:
        return []

    offset = (page - 1) * page_size
    stmt = (
        select(Product)
        .options(
            selectinload(Product.craft),
            selectinload(Product.category),
            selectinload(Product.media)
        )
        .where(Product.artisan_id == artisan.id)
        .order_by(Product.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    products = result.scalars().all()

    return [
        ProductResponse(
            id=p.id,
            artisan_id=p.artisan_id,
            craft_id=p.craft_id,
            category_id=p.category_id,
            craft_name=p.craft.name if p.craft else None,
            category_name=p.category.name if p.category else None,
            sku=p.sku,
            title=p.title,
            storytelling_description=p.storytelling_description,
            price_inr=float(p.price_inr),
            currency=p.currency,
            stock_quantity=p.stock_quantity,
            monthly_production_capacity=p.monthly_production_capacity,
            min_order_quantity=p.min_order_quantity,
            lead_time_days=p.lead_time_days,
            availability_status=p.availability_status,
            region=p.region,
            materials=p.materials,
            primary_color=p.primary_color,
            dimensions=p.dimensions,
            weight_grams=p.weight_grams,
            technique=p.technique,
            style=p.style,
            tags=p.tags,
            is_customizable=p.is_customizable,
            status=p.status,
            provenance_status=p.provenance_status,
            ai_metadata=p.ai_metadata,
            admin_feedback=p.admin_feedback,
            media=[
                ProductMediaResponse(
                    id=m.id,
                    product_id=m.product_id,
                    media_type=m.media_type,
                    url=m.url,
                    thumbnail_url=m.thumbnail_url,
                    storage_key=m.storage_key,
                    original_filename=m.original_filename,
                    file_size_bytes=m.file_size_bytes,
                    mime_type=m.mime_type,
                    checksum_sha256=m.checksum_sha256,
                    width=m.width,
                    height=m.height,
                    sort_order=m.sort_order,
                    alt_text=m.alt_text,
                    is_primary=m.is_primary,
                    created_at=m.created_at.isoformat() if m.created_at else ""
                )
                for m in p.media
            ],
            created_at=p.created_at.isoformat() if p.created_at else "",
            updated_at=p.updated_at.isoformat() if p.updated_at else ""
        )
        for p in products
    ]


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    payload: ProductUpdate,
    current_user: User = Depends(require_roles(["artisan"])),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Updates an artisan's product details. Enforces strict server-side ownership (IDOR defense).
    If a published product is modified, its status is transitioned back to DRAFT for re-moderation.
    """
    art_res = await db.execute(select(ArtisanProfile).where(ArtisanProfile.user_id == current_user.id))
    artisan = art_res.scalar_one_or_none()
    if not artisan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artisan profile not found.")

    query = (
        select(Product)
        .options(
            selectinload(Product.craft),
            selectinload(Product.category),
            selectinload(Product.media)
        )
        .where(Product.id == product_id)
    )
    result = await db.execute(query)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    # IDOR Defense
    if str(product.artisan_id) != str(artisan.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not own this product listing."
        )

    update_dict = payload.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(product, k, v)

    CRITICAL_MODERATION_FIELDS = {
        "title", "price_inr", "materials", "craft_id", "category_id",
        "storytelling_description", "technique", "provenance_status"
    }

    # Re-moderation policy: modifying critical fields of a published product resets to DRAFT
    if product.status == "PUBLISHED" and any(k in CRITICAL_MODERATION_FIELDS for k in update_dict.keys()):
        product.status = "DRAFT"

    await db.flush()
    await db.refresh(product)

    await record_audit_event(
        db=db,
        action="PRODUCT_UPDATED",
        entity_type="Product",
        entity_id=product.id,
        actor_user_id=current_user.id,
        payload_after={"status": product.status, "updated_fields": list(update_dict.keys())}
    )

    return ProductResponse(
        id=product.id,
        artisan_id=product.artisan_id,
        craft_id=product.craft_id,
        category_id=product.category_id,
        craft_name=product.craft.name if product.craft else None,
        category_name=product.category.name if product.category else None,
        sku=product.sku,
        title=product.title,
        storytelling_description=product.storytelling_description,
        price_inr=float(product.price_inr),
        currency=product.currency,
        stock_quantity=product.stock_quantity,
        monthly_production_capacity=product.monthly_production_capacity,
        min_order_quantity=product.min_order_quantity,
        lead_time_days=product.lead_time_days,
        availability_status=product.availability_status,
        region=product.region,
        materials=product.materials,
        primary_color=product.primary_color,
        dimensions=product.dimensions,
        weight_grams=product.weight_grams,
        technique=product.technique,
        style=product.style,
        tags=product.tags,
        is_customizable=product.is_customizable,
        status=product.status,
        provenance_status=product.provenance_status,
        ai_metadata=product.ai_metadata,
        admin_feedback=product.admin_feedback,
        media=[
            ProductMediaResponse(
                id=m.id,
                product_id=m.product_id,
                media_type=m.media_type,
                url=m.url,
                thumbnail_url=m.thumbnail_url,
                storage_key=m.storage_key,
                original_filename=m.original_filename,
                file_size_bytes=m.file_size_bytes,
                mime_type=m.mime_type,
                checksum_sha256=m.checksum_sha256,
                width=m.width,
                height=m.height,
                sort_order=m.sort_order,
                alt_text=m.alt_text,
                is_primary=m.is_primary,
                created_at=m.created_at.isoformat() if m.created_at else ""
            )
            for m in product.media
        ],
        created_at=product.created_at.isoformat() if product.created_at else "",
        updated_at=product.updated_at.isoformat() if product.updated_at else ""
    )


@router.delete("/products/{product_id}", status_code=status.HTTP_200_OK)
async def delete_product(
    product_id: str,
    current_user: User = Depends(require_roles(["artisan", "admin"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Deletes an artisanal product listing. Enforces IDOR defense."""
    query = select(Product).where(Product.id == product_id)
    result = await db.execute(query)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    if current_user.role == "artisan":
        art_res = await db.execute(select(ArtisanProfile).where(ArtisanProfile.user_id == current_user.id))
        artisan = art_res.scalar_one_or_none()
        if not artisan or str(product.artisan_id) != str(artisan.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: You do not own this product.")

    await db.delete(product)
    await db.flush()

    await record_audit_event(
        db=db,
        action="PRODUCT_DELETED",
        entity_type="Product",
        entity_id=product_id,
        actor_user_id=current_user.id,
        payload_after={"product_id": product_id}
    )

    return {"message": "Product listing deleted successfully."}


@router.post("/products/{product_id}/submit", response_model=ProductResponse)
async def submit_product_for_moderation(
    product_id: str,
    current_user: User = Depends(require_roles(["artisan"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Transitions a product from DRAFT or REJECTED to PENDING_REVIEW for administrator moderation."""
    art_res = await db.execute(select(ArtisanProfile).where(ArtisanProfile.user_id == current_user.id))
    artisan = art_res.scalar_one_or_none()
    if not artisan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artisan profile not found.")

    query = (
        select(Product)
        .options(
            selectinload(Product.craft),
            selectinload(Product.category),
            selectinload(Product.media)
        )
        .where(Product.id == product_id)
    )
    result = await db.execute(query)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    # IDOR Check
    if str(product.artisan_id) != str(artisan.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: You do not own this product.")

    if product.status not in ["DRAFT", "REJECTED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit product currently in state '{product.status}'."
        )

    product.status = "PENDING_REVIEW"
    await db.flush()
    await db.refresh(product)

    await record_audit_event(
        db=db,
        action="PRODUCT_SUBMITTED_FOR_REVIEW",
        entity_type="Product",
        entity_id=product.id,
        actor_user_id=current_user.id,
        payload_after={"status": "PENDING_REVIEW"}
    )

    return ProductResponse(
        id=product.id,
        artisan_id=product.artisan_id,
        craft_id=product.craft_id,
        category_id=product.category_id,
        craft_name=product.craft.name if product.craft else None,
        category_name=product.category.name if product.category else None,
        sku=product.sku,
        title=product.title,
        storytelling_description=product.storytelling_description,
        price_inr=float(product.price_inr),
        currency=product.currency,
        stock_quantity=product.stock_quantity,
        monthly_production_capacity=product.monthly_production_capacity,
        min_order_quantity=product.min_order_quantity,
        lead_time_days=product.lead_time_days,
        availability_status=product.availability_status,
        region=product.region,
        materials=product.materials,
        primary_color=product.primary_color,
        dimensions=product.dimensions,
        weight_grams=product.weight_grams,
        technique=product.technique,
        style=product.style,
        tags=product.tags,
        is_customizable=product.is_customizable,
        status=product.status,
        provenance_status=product.provenance_status,
        ai_metadata=product.ai_metadata,
        admin_feedback=product.admin_feedback,
        media=[],
        created_at=product.created_at.isoformat() if product.created_at else "",
        updated_at=product.updated_at.isoformat() if product.updated_at else ""
    )


# ==========================================
# PRODUCT MEDIA ENDPOINTS
# ==========================================

@router.post("/products/{product_id}/media", response_model=ProductMediaResponse, status_code=status.HTTP_201_CREATED)
async def add_product_media(
    product_id: str,
    payload: ProductMediaCreate,
    current_user: User = Depends(require_roles(["artisan"])),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Attaches media asset metadata (photo/document) to a product.
    Enforces server-side artisan ownership (IDOR defense) and MIME/size security validation.
    """
    art_res = await db.execute(select(ArtisanProfile).where(ArtisanProfile.user_id == current_user.id))
    artisan = art_res.scalar_one_or_none()
    if not artisan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artisan profile not found.")

    prod_res = await db.execute(select(Product).where(Product.id == product_id))
    product = prod_res.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    # IDOR Check
    if str(product.artisan_id) != str(artisan.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: You do not own this product.")

    media = ProductMedia(
        product_id=product.id,
        media_type=payload.media_type,
        url=payload.url,
        thumbnail_url=payload.thumbnail_url,
        storage_key=payload.storage_key,
        original_filename=payload.original_filename,
        file_size_bytes=payload.file_size_bytes,
        mime_type=payload.mime_type,
        checksum_sha256=payload.checksum_sha256,
        width=payload.width,
        height=payload.height,
        sort_order=payload.sort_order,
        alt_text=payload.alt_text,
        is_primary=payload.is_primary
    )
    db.add(media)
    await db.flush()
    await db.refresh(media)

    await record_audit_event(
        db=db,
        action="PRODUCT_MEDIA_ADDED",
        entity_type="ProductMedia",
        entity_id=media.id,
        actor_user_id=current_user.id,
        payload_after={"product_id": product.id, "mime_type": media.mime_type}
    )

    return ProductMediaResponse(
        id=media.id,
        product_id=media.product_id,
        media_type=media.media_type,
        url=media.url,
        thumbnail_url=media.thumbnail_url,
        storage_key=media.storage_key,
        original_filename=media.original_filename,
        file_size_bytes=media.file_size_bytes,
        mime_type=media.mime_type,
        checksum_sha256=media.checksum_sha256,
        width=media.width,
        height=media.height,
        sort_order=media.sort_order,
        alt_text=media.alt_text,
        is_primary=media.is_primary,
        created_at=media.created_at.isoformat() if media.created_at else ""
    )


@router.delete("/products/{product_id}/media/{media_id}", status_code=status.HTTP_200_OK)
async def delete_product_media(
    product_id: str,
    media_id: str,
    current_user: User = Depends(require_roles(["artisan"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Deletes media asset from a product with IDOR check."""
    art_res = await db.execute(select(ArtisanProfile).where(ArtisanProfile.user_id == current_user.id))
    artisan = art_res.scalar_one_or_none()
    if not artisan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artisan profile not found.")

    media_res = await db.execute(
        select(ProductMedia).join(Product).where(
            and_(
                ProductMedia.id == media_id,
                ProductMedia.product_id == product_id
            )
        )
    )
    media = media_res.scalar_one_or_none()
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found.")

    prod_res = await db.execute(select(Product).where(Product.id == product_id))
    product = prod_res.scalar_one_or_none()
    if not product or str(product.artisan_id) != str(artisan.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    await db.delete(media)
    await db.flush()

    await record_audit_event(
        db=db,
        action="PRODUCT_MEDIA_DELETED",
        entity_type="ProductMedia",
        entity_id=media_id,
        actor_user_id=current_user.id,
        payload_after={"product_id": product_id}
    )

    return {"message": "Media asset deleted successfully."}


# ==========================================
# PUBLIC CATALOGUE & FILTERING
# ==========================================

@router.get("/products", response_model=ProductListResponse)
async def list_public_catalogue(
    query: Optional[str] = Query(default=None, description="Search term in title, storytelling, or tags"),
    craft_id: Optional[str] = Query(default=None, description="Filter by craft UUID"),
    category_id: Optional[str] = Query(default=None, description="Filter by category UUID"),
    region: Optional[str] = Query(default=None, description="Filter by origin state or district"),
    material: Optional[str] = Query(default=None, description="Filter by authentic material used"),
    min_price: Optional[float] = Query(default=None, ge=0.0, description="Minimum price in INR"),
    max_price: Optional[float] = Query(default=None, ge=0.0, description="Maximum price in INR"),
    availability_status: Optional[str] = Query(default=None, description="AVAILABLE, MADE_TO_ORDER"),
    min_capacity: Optional[int] = Query(default=None, ge=0, description="Minimum monthly production capacity"),
    max_moq: Optional[int] = Query(default=None, ge=1, description="Maximum acceptable Minimum Order Quantity (MOQ)"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Public sanitized catalogue search for buyers and consumers.
    Strictly filters for PUBLISHED status and returns zero private artisan contact information.
    Deterministic database filtering over price, craft, capacity, and materials.
    """
    stmt = (
        select(Product)
        .options(
            selectinload(Product.craft),
            selectinload(Product.category),
            selectinload(Product.artisan),
            selectinload(Product.media)
        )
        .where(Product.status == "PUBLISHED")
    )

    if craft_id:
        stmt = stmt.where(Product.craft_id == craft_id)
    if category_id:
        stmt = stmt.where(Product.category_id == category_id)
    if region:
        stmt = stmt.where(Product.region.ilike(f"%{region}%"))
    if min_price is not None:
        stmt = stmt.where(Product.price_inr >= min_price)
    if max_price is not None:
        stmt = stmt.where(Product.price_inr <= max_price)
    if availability_status:
        stmt = stmt.where(Product.availability_status == availability_status)
    if min_capacity is not None:
        stmt = stmt.where(Product.monthly_production_capacity >= min_capacity)
    if max_moq is not None:
        stmt = stmt.where(Product.min_order_quantity <= max_moq)
    if query:
        stmt = stmt.where(
            or_(
                Product.title.ilike(f"%{query}%"),
                Product.storytelling_description.ilike(f"%{query}%"),
                Product.technique.ilike(f"%{query}%")
            )
        )

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_res = await db.execute(count_stmt)
    total = total_res.scalar() or 0

    # Pagination and deterministic ordering
    offset = (page - 1) * page_size
    stmt = stmt.order_by(Product.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    products = result.scalars().all()

    items = []
    for p in products:
        craft = p.craft
        artisan = p.artisan
        items.append(
            ProductPublicResponse(
                id=p.id,
                sku=p.sku,
                title=p.title,
                storytelling_description=p.storytelling_description,
                price_inr=float(p.price_inr),
                currency=p.currency,
                stock_quantity=p.stock_quantity,
                monthly_production_capacity=p.monthly_production_capacity,
                min_order_quantity=p.min_order_quantity,
                lead_time_days=p.lead_time_days,
                availability_status=p.availability_status,
                region=p.region,
                materials=p.materials,
                primary_color=p.primary_color,
                dimensions=p.dimensions,
                weight_grams=p.weight_grams,
                technique=p.technique,
                style=p.style,
                tags=p.tags,
                is_customizable=p.is_customizable,
                status=p.status,
                provenance_status=p.provenance_status,
                craft_name=craft.name if craft else None,
                category_name=p.category.name if p.category else None,
                artisan_public_name=artisan.full_name if artisan else "Registered Artisan",
                artisan_district=artisan.district if artisan else None,
                artisan_state=artisan.state if artisan else None,
                has_gi_tag=craft.has_gi_tag if craft else False,
                gi_tag_number=craft.gi_tag_number if craft else None,
                media=[
                    ProductMediaResponse(
                        id=m.id,
                        product_id=m.product_id,
                        media_type=m.media_type,
                        url=m.url,
                        thumbnail_url=m.thumbnail_url,
                        storage_key=m.storage_key,
                        original_filename=m.original_filename,
                        file_size_bytes=m.file_size_bytes,
                        mime_type=m.mime_type,
                        checksum_sha256=m.checksum_sha256,
                        width=m.width,
                        height=m.height,
                        sort_order=m.sort_order,
                        alt_text=m.alt_text,
                        is_primary=m.is_primary,
                        created_at=m.created_at.isoformat() if m.created_at else ""
                    )
                    for m in p.media
                ],
                created_at=p.created_at.isoformat() if p.created_at else ""
            )
        )

    total_pages = ceil(total / page_size) if total > 0 else 1
    return ProductListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/products/{product_id}", response_model=ProductPublicResponse)
async def get_product_details(
    product_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Public sanitized product detail view.
    Exposes authentic craft credentials and media while withholding private artisan contact info.
    """
    query = (
        select(Product)
        .options(
            selectinload(Product.craft),
            selectinload(Product.category),
            selectinload(Product.artisan),
            selectinload(Product.media)
        )
        .where(Product.id == product_id)
    )
    result = await db.execute(query)
    p = result.scalar_one_or_none()

    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    craft = p.craft
    artisan = p.artisan

    return ProductPublicResponse(
        id=p.id,
        sku=p.sku,
        title=p.title,
        storytelling_description=p.storytelling_description,
        price_inr=float(p.price_inr),
        currency=p.currency,
        stock_quantity=p.stock_quantity,
        monthly_production_capacity=p.monthly_production_capacity,
        min_order_quantity=p.min_order_quantity,
        lead_time_days=p.lead_time_days,
        availability_status=p.availability_status,
        region=p.region,
        materials=p.materials,
        primary_color=p.primary_color,
        dimensions=p.dimensions,
        weight_grams=p.weight_grams,
        technique=p.technique,
        style=p.style,
        tags=p.tags,
        is_customizable=p.is_customizable,
        status=p.status,
        provenance_status=p.provenance_status,
        craft_name=craft.name if craft else None,
        category_name=p.category.name if p.category else None,
        artisan_public_name=artisan.full_name if artisan else "Registered Artisan",
        artisan_district=artisan.district if artisan else None,
        artisan_state=artisan.state if artisan else None,
        has_gi_tag=craft.has_gi_tag if craft else False,
        gi_tag_number=craft.gi_tag_number if craft else None,
        media=[
            ProductMediaResponse(
                id=m.id,
                product_id=m.product_id,
                media_type=m.media_type,
                url=m.url,
                thumbnail_url=m.thumbnail_url,
                storage_key=m.storage_key,
                original_filename=m.original_filename,
                file_size_bytes=m.file_size_bytes,
                mime_type=m.mime_type,
                checksum_sha256=m.checksum_sha256,
                width=m.width,
                height=m.height,
                sort_order=m.sort_order,
                alt_text=m.alt_text,
                is_primary=m.is_primary,
                created_at=m.created_at.isoformat() if m.created_at else ""
            )
            for m in p.media
        ],
        created_at=p.created_at.isoformat() if p.created_at else ""
    )


# ==========================================
# ADMINISTRATOR MODERATION
# ==========================================

@router.get("/products/admin/pending", response_model=List[ProductResponse])
async def list_pending_products_for_moderation(
    current_user: User = Depends(require_roles(["admin"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Administrator view: lists products currently in PENDING_REVIEW status."""
    stmt = (
        select(Product)
        .options(
            selectinload(Product.craft),
            selectinload(Product.category),
            selectinload(Product.media)
        )
        .where(Product.status == "PENDING_REVIEW")
        .order_by(Product.updated_at.asc())
    )
    result = await db.execute(stmt)
    products = result.scalars().all()

    return [
        ProductResponse(
            id=p.id,
            artisan_id=p.artisan_id,
            craft_id=p.craft_id,
            category_id=p.category_id,
            craft_name=p.craft.name if p.craft else None,
            category_name=p.category.name if p.category else None,
            sku=p.sku,
            title=p.title,
            storytelling_description=p.storytelling_description,
            price_inr=float(p.price_inr),
            currency=p.currency,
            stock_quantity=p.stock_quantity,
            monthly_production_capacity=p.monthly_production_capacity,
            min_order_quantity=p.min_order_quantity,
            lead_time_days=p.lead_time_days,
            availability_status=p.availability_status,
            region=p.region,
            materials=p.materials,
            primary_color=p.primary_color,
            dimensions=p.dimensions,
            weight_grams=p.weight_grams,
            technique=p.technique,
            style=p.style,
            tags=p.tags,
            is_customizable=p.is_customizable,
            status=p.status,
            provenance_status=p.provenance_status,
            ai_metadata=p.ai_metadata,
            admin_feedback=p.admin_feedback,
            media=[
                ProductMediaResponse(
                    id=m.id,
                    product_id=m.product_id,
                    media_type=m.media_type,
                    url=m.url,
                    thumbnail_url=m.thumbnail_url,
                    storage_key=m.storage_key,
                    original_filename=m.original_filename,
                    file_size_bytes=m.file_size_bytes,
                    mime_type=m.mime_type,
                    checksum_sha256=m.checksum_sha256,
                    width=m.width,
                    height=m.height,
                    sort_order=m.sort_order,
                    alt_text=m.alt_text,
                    is_primary=m.is_primary,
                    created_at=m.created_at.isoformat() if m.created_at else ""
                )
                for m in p.media
            ],
            created_at=p.created_at.isoformat() if p.created_at else "",
            updated_at=p.updated_at.isoformat() if p.updated_at else ""
        )
        for p in products
    ]


@router.post("/products/admin/{product_id}/review", response_model=ProductResponse)
async def review_product(
    product_id: str,
    payload: ProductModerationRequest,
    current_user: User = Depends(require_roles(["admin"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Administrator moderation decision: APPROVE -> PUBLISHED, REJECT -> REJECTED, REQUEST_CORRECTION -> DRAFT."""
    query = (
        select(Product)
        .options(
            selectinload(Product.craft),
            selectinload(Product.category),
            selectinload(Product.media)
        )
        .where(Product.id == product_id)
    )
    result = await db.execute(query)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    now = datetime.now(timezone.utc)
    product.moderated_by = current_user.id
    product.moderated_at = now
    product.admin_feedback = payload.admin_notes or payload.rejection_reason

    if payload.decision == "APPROVE":
        product.status = "PUBLISHED"
        if getattr(payload, "authoritative_evidence_reference", None):
            product.provenance_status = "GOVERNMENT_GI_CONFIRMED"
        else:
            # Check if artisan has an authority-verified CraftPassport for this specific craft
            passport_res = await db.execute(
                select(CraftPassport).where(
                    CraftPassport.artisan_id == product.artisan_id,
                    CraftPassport.craft_id == product.craft_id,
                    CraftPassport.status == "VERIFIED",
                    CraftPassport.verification_level.in_(["GOVERNMENT_VERIFIED_GI", "AUTHORITY_VERIFIED"])
                )
            )
            has_auth_passport = passport_res.scalar_one_or_none() is not None
            if has_auth_passport:
                product.provenance_status = "GOVERNMENT_GI_CONFIRMED"
            else:
                product.provenance_status = "ADMIN_APPROVED"
    elif payload.decision == "REJECT":
        product.status = "REJECTED"
    elif payload.decision == "REQUEST_CORRECTION":
        product.status = "DRAFT"

    await db.flush()
    await db.refresh(product)

    await record_audit_event(
        db=db,
        action=f"PRODUCT_MODERATION_{payload.decision}",
        entity_type="Product",
        entity_id=product.id,
        actor_user_id=current_user.id,
        payload_after={"status": product.status, "decision": payload.decision}
    )

    return ProductResponse(
        id=product.id,
        artisan_id=product.artisan_id,
        craft_id=product.craft_id,
        category_id=product.category_id,
        craft_name=product.craft.name if product.craft else None,
        category_name=product.category.name if product.category else None,
        sku=product.sku,
        title=product.title,
        storytelling_description=product.storytelling_description,
        price_inr=float(product.price_inr),
        currency=product.currency,
        stock_quantity=product.stock_quantity,
        monthly_production_capacity=product.monthly_production_capacity,
        min_order_quantity=product.min_order_quantity,
        lead_time_days=product.lead_time_days,
        availability_status=product.availability_status,
        region=product.region,
        materials=product.materials,
        primary_color=product.primary_color,
        dimensions=product.dimensions,
        weight_grams=product.weight_grams,
        technique=product.technique,
        style=product.style,
        tags=product.tags,
        is_customizable=product.is_customizable,
        status=product.status,
        provenance_status=product.provenance_status,
        ai_metadata=product.ai_metadata,
        admin_feedback=product.admin_feedback,
        media=[
            ProductMediaResponse(
                id=m.id,
                product_id=m.product_id,
                media_type=m.media_type,
                url=m.url,
                thumbnail_url=m.thumbnail_url,
                storage_key=m.storage_key,
                original_filename=m.original_filename,
                file_size_bytes=m.file_size_bytes,
                mime_type=m.mime_type,
                checksum_sha256=m.checksum_sha256,
                width=m.width,
                height=m.height,
                sort_order=m.sort_order,
                alt_text=m.alt_text,
                is_primary=m.is_primary,
                created_at=m.created_at.isoformat() if m.created_at else ""
            )
            for m in product.media
        ],
        created_at=product.created_at.isoformat() if product.created_at else "",
        updated_at=product.updated_at.isoformat() if product.updated_at else ""
    )
