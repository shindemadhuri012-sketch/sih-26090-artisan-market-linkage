"""
SIH 26090: Craft Directory & Category API Endpoints
Provides search, filtering, and hierarchical category exploration grounded in official GI and ODOP data.
"""

from typing import List, Optional
from math import ceil
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_async_db
from backend.app.core.permissions import require_roles
from backend.app.models.auth import User
from backend.app.models.craft import Craft, CraftCategory
from backend.app.schemas.craft import (
    CraftCreate,
    CraftUpdate,
    CraftResponse,
    CraftListResponse,
    CraftCategoryCreate,
    CraftCategoryResponse,
    CraftCategoryTreeResponse
)
from backend.app.services.audit_service import record_audit_event

router = APIRouter(tags=["Crafts & Categories"])


# ==========================================
# CRAFT CATEGORIES
# ==========================================

@router.get("/craft-categories", response_model=List[CraftCategoryTreeResponse])
async def list_craft_categories(db: AsyncSession = Depends(get_async_db)):
    """
    Returns hierarchical craft categories.
    Top-level parent categories are returned with their nested subcategories.
    """
    query = (
        select(CraftCategory)
        .options(selectinload(CraftCategory.subcategories))
        .where(CraftCategory.parent_id == None)  # noqa: E711
        .order_by(CraftCategory.name.asc())
    )
    result = await db.execute(query)
    categories = result.scalars().all()

    response = []
    for cat in categories:
        subcats = [
            CraftCategoryResponse(
                id=sub.id,
                name=sub.name,
                description=sub.description,
                icon_url=sub.icon_url,
                parent_id=sub.parent_id,
                created_at=sub.created_at.isoformat() if sub.created_at else ""
            )
            for sub in cat.subcategories
        ]
        response.append(
            CraftCategoryTreeResponse(
                id=cat.id,
                name=cat.name,
                description=cat.description,
                icon_url=cat.icon_url,
                parent_id=cat.parent_id,
                created_at=cat.created_at.isoformat() if cat.created_at else "",
                subcategories=subcats
            )
        )
    return response


@router.post("/craft-categories", response_model=CraftCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_craft_category(
    payload: CraftCategoryCreate,
    current_user: User = Depends(require_roles(["admin"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Administrator endpoint: creates a new craft category or nested subcategory."""
    # Check duplicate name
    existing = await db.execute(select(CraftCategory).where(CraftCategory.name == payload.name))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category with name '{payload.name}' already exists."
        )

    # If parent_id provided, verify parent exists
    if payload.parent_id:
        parent = await db.execute(select(CraftCategory).where(CraftCategory.id == payload.parent_id))
        if not parent.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent category with id '{payload.parent_id}' not found."
            )

    cat = CraftCategory(
        name=payload.name,
        description=payload.description,
        icon_url=payload.icon_url,
        parent_id=payload.parent_id
    )
    db.add(cat)
    await db.flush()
    await db.refresh(cat)

    await record_audit_event(
        db=db,
        action="CRAFT_CATEGORY_CREATED",
        entity_type="CraftCategory",
        entity_id=cat.id,
        actor_user_id=current_user.id,
        payload_after={"name": cat.name, "parent_id": cat.parent_id}
    )

    return CraftCategoryResponse(
        id=cat.id,
        name=cat.name,
        description=cat.description,
        icon_url=cat.icon_url,
        parent_id=cat.parent_id,
        created_at=cat.created_at.isoformat() if cat.created_at else ""
    )


# ==========================================
# CRAFT MASTER DIRECTORY
# ==========================================

@router.get("/crafts", response_model=CraftListResponse)
async def list_crafts(
    query: Optional[str] = Query(default=None, description="Search term across craft name, technique, or district"),
    category_id: Optional[str] = Query(default=None, description="Filter by craft category UUID"),
    state: Optional[str] = Query(default=None, description="Filter by origin state"),
    has_gi_tag: Optional[bool] = Query(default=None, description="Filter by official GI certification status"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Public directory of Indian traditional crafts grounded in official GI and ODOP registers.
    Supports deterministic filtering by state, category, GI tag, and text query with safe pagination.
    """
    stmt = select(Craft).options(selectinload(Craft.category)).where(Craft.is_active == True)  # noqa: E712

    if category_id:
        stmt = stmt.where(Craft.category_id == category_id)
    if state:
        stmt = stmt.where(Craft.origin_state.ilike(f"%{state}%"))
    if has_gi_tag is not None:
        stmt = stmt.where(Craft.has_gi_tag == has_gi_tag)
    if query:
        search_filter = (
            Craft.name.ilike(f"%{query}%")
            | Craft.origin_district.ilike(f"%{query}%")
            | Craft.traditional_technique.ilike(f"%{query}%")
        )
        stmt = stmt.where(search_filter)

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_res = await db.execute(count_stmt)
    total = total_res.scalar() or 0

    # Deterministic order and pagination
    offset = (page - 1) * page_size
    stmt = stmt.order_by(Craft.name.asc()).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    crafts = result.scalars().all()

    items = [
        CraftResponse(
            id=c.id,
            category_id=c.category_id,
            category_name=c.category.name if c.category else None,
            name=c.name,
            normalized_name=c.normalized_name,
            gi_tag_number=c.gi_tag_number,
            has_gi_tag=c.has_gi_tag,
            origin_state=c.origin_state,
            origin_district=c.origin_district,
            region=c.region,
            cultural_heritage_description=c.cultural_heritage_description,
            traditional_technique=c.traditional_technique,
            traditional_raw_materials=c.traditional_raw_materials,
            data_source_id=c.data_source_id,
            is_active=c.is_active,
            created_at=c.created_at.isoformat() if c.created_at else ""
        )
        for c in crafts
    ]

    total_pages = ceil(total / page_size) if total > 0 else 1
    return CraftListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/crafts/{craft_id}", response_model=CraftResponse)
async def get_craft_details(craft_id: str, db: AsyncSession = Depends(get_async_db)):
    """Retrieves full details for a specific traditional craft."""
    query = (
        select(Craft)
        .options(selectinload(Craft.category))
        .where(Craft.id == craft_id)
    )
    result = await db.execute(query)
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Craft with id '{craft_id}' not found in master directory."
        )

    return CraftResponse(
        id=c.id,
        category_id=c.category_id,
        category_name=c.category.name if c.category else None,
        name=c.name,
        normalized_name=c.normalized_name,
        gi_tag_number=c.gi_tag_number,
        has_gi_tag=c.has_gi_tag,
        origin_state=c.origin_state,
        origin_district=c.origin_district,
        region=c.region,
        cultural_heritage_description=c.cultural_heritage_description,
        traditional_technique=c.traditional_technique,
        traditional_raw_materials=c.traditional_raw_materials,
        data_source_id=c.data_source_id,
        is_active=c.is_active,
        created_at=c.created_at.isoformat() if c.created_at else ""
    )


@router.post("/crafts", response_model=CraftResponse, status_code=status.HTTP_201_CREATED)
async def create_craft(
    payload: CraftCreate,
    current_user: User = Depends(require_roles(["admin"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Administrator endpoint: registers an authentic craft in the master directory."""
    # Verify category exists
    cat_res = await db.execute(select(CraftCategory).where(CraftCategory.id == payload.category_id))
    category = cat_res.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Specified category_id '{payload.category_id}' does not exist."
        )

    # Check GI uniqueness if present
    if payload.gi_tag_number:
        gi_res = await db.execute(select(Craft).where(Craft.gi_tag_number == payload.gi_tag_number))
        if gi_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A craft with GI tag '{payload.gi_tag_number}' is already registered."
            )

    normalized = payload.name.strip().lower()
    craft = Craft(
        category_id=payload.category_id,
        name=payload.name,
        normalized_name=normalized,
        gi_tag_number=payload.gi_tag_number,
        has_gi_tag=payload.has_gi_tag,
        origin_state=payload.origin_state,
        origin_district=payload.origin_district,
        region=payload.region,
        cultural_heritage_description=payload.cultural_heritage_description,
        traditional_technique=payload.traditional_technique,
        traditional_raw_materials=payload.traditional_raw_materials,
        is_active=payload.is_active,
        is_sample_or_demo=False,
        data_provenance_level="GOVERNMENT_REGISTRY" if payload.has_gi_tag else "CURATED_CATALOGUE"
    )
    db.add(craft)
    await db.flush()
    await db.refresh(craft)

    await record_audit_event(
        db=db,
        action="CRAFT_CREATED",
        entity_type="Craft",
        entity_id=craft.id,
        actor_user_id=current_user.id,
        payload_after={"name": craft.name, "origin_district": craft.origin_district}
    )

    return CraftResponse(
        id=craft.id,
        category_id=craft.category_id,
        category_name=category.name,
        name=craft.name,
        normalized_name=craft.normalized_name,
        gi_tag_number=craft.gi_tag_number,
        has_gi_tag=craft.has_gi_tag,
        origin_state=craft.origin_state,
        origin_district=craft.origin_district,
        region=craft.region,
        cultural_heritage_description=craft.cultural_heritage_description,
        traditional_technique=craft.traditional_technique,
        traditional_raw_materials=craft.traditional_raw_materials,
        data_source_id=craft.data_source_id,
        is_active=craft.is_active,
        created_at=craft.created_at.isoformat() if craft.created_at else ""
    )


@router.put("/crafts/{craft_id}", response_model=CraftResponse)
async def update_craft(
    craft_id: str,
    payload: CraftUpdate,
    current_user: User = Depends(require_roles(["admin"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Administrator endpoint: updates craft directory attributes."""
    query = (
        select(Craft)
        .options(selectinload(Craft.category))
        .where(Craft.id == craft_id)
    )
    result = await db.execute(query)
    craft = result.scalar_one_or_none()
    if not craft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Craft not found.")

    update_dict = payload.model_dump(exclude_unset=True)
    if "name" in update_dict and update_dict["name"]:
        update_dict["normalized_name"] = update_dict["name"].strip().lower()

    for k, v in update_dict.items():
        setattr(craft, k, v)

    await db.flush()
    await db.refresh(craft)

    await record_audit_event(
        db=db,
        action="CRAFT_UPDATED",
        entity_type="Craft",
        entity_id=craft.id,
        actor_user_id=current_user.id,
        payload_after=update_dict
    )

    return CraftResponse(
        id=craft.id,
        category_id=craft.category_id,
        category_name=craft.category.name if craft.category else None,
        name=craft.name,
        normalized_name=craft.normalized_name,
        gi_tag_number=craft.gi_tag_number,
        has_gi_tag=craft.has_gi_tag,
        origin_state=craft.origin_state,
        origin_district=craft.origin_district,
        region=craft.region,
        cultural_heritage_description=craft.cultural_heritage_description,
        traditional_technique=craft.traditional_technique,
        traditional_raw_materials=craft.traditional_raw_materials,
        data_source_id=craft.data_source_id,
        is_active=craft.is_active,
        created_at=craft.created_at.isoformat() if craft.created_at else ""
    )
