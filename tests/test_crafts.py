"""
SIH 26090: Craft Catalogue & Category Automated Tests
Tests hierarchical categories, craft directory search, GI mapping,
and artisan-craft many-to-many associations with skill tiers.
"""

import pytest
from httpx import AsyncClient
from backend.app.models.craft import Craft


@pytest.mark.asyncio
async def test_hierarchical_category_creation_and_listing(
    client: AsyncClient,
    admin_headers: dict
):
    """
    Verifies that administrators can create parent categories and nested subcategories,
    and that GET /craft-categories returns the hierarchical tree.
    """
    # 1. Create parent category
    r_parent = await client.post("/api/v1/craft-categories", headers=admin_headers, json={
        "name": "Textiles & Weaving",
        "description": "Traditional Indian handloom and embroidery traditions"
    })
    assert r_parent.status_code == 201
    parent_id = r_parent.json()["id"]

    # 2. Create subcategory under parent
    r_sub = await client.post("/api/v1/craft-categories", headers=admin_headers, json={
        "name": "Handloom Brocade",
        "description": "Intricate extra-weft zari weaves",
        "parent_id": parent_id
    })
    assert r_sub.status_code == 201
    assert r_sub.json()["parent_id"] == parent_id

    # 3. Retrieve category tree
    r_tree = await client.get("/api/v1/craft-categories")
    assert r_tree.status_code == 200
    tree = r_tree.json()
    assert len(tree) >= 1
    found_parent = next((c for c in tree if c["id"] == parent_id), None)
    assert found_parent is not None
    assert len(found_parent["subcategories"]) == 1
    assert found_parent["subcategories"][0]["name"] == "Handloom Brocade"


@pytest.mark.asyncio
async def test_craft_creation_and_authorization(
    client: AsyncClient,
    artisan_headers: dict,
    admin_headers: dict
):
    """Verifies that only administrators can create master craft records."""
    # 1. Create category
    r_cat = await client.post("/api/v1/craft-categories", headers=admin_headers, json={
        "name": "Woodcraft & Marquetry"
    })
    cat_id = r_cat.json()["id"]

    craft_payload = {
        "category_id": cat_id,
        "name": "Saharanpur Wood Carving",
        "gi_tag_number": "GI-430",
        "has_gi_tag": True,
        "origin_state": "Uttar Pradesh",
        "origin_district": "Saharanpur",
        "region": "Northern India",
        "cultural_heritage_description": "Centuries-old intricate lattice carving on Sheesham wood.",
        "traditional_technique": "Hand chisel carving and brass inlay",
        "traditional_raw_materials": ["Sheesham Wood", "Brass Wire"]
    }

    # 2. Artisan role cannot create master craft -> 403 Forbidden
    r_forbidden = await client.post("/api/v1/crafts", headers=artisan_headers, json=craft_payload)
    assert r_forbidden.status_code == 403

    # 3. Admin can create master craft -> 201 Created
    r_created = await client.post("/api/v1/crafts", headers=admin_headers, json=craft_payload)
    assert r_created.status_code == 201
    craft_data = r_created.json()
    assert craft_data["name"] == "Saharanpur Wood Carving"
    assert craft_data["normalized_name"] == "saharanpur wood carving"
    assert craft_data["has_gi_tag"] is True


@pytest.mark.asyncio
async def test_craft_directory_search_and_filtering(
    client: AsyncClient,
    seed_craft: Craft
):
    """Verifies deterministic search across craft name, origin state, and GI tag."""
    # Search by state
    r_state = await client.get("/api/v1/crafts", params={"state": "Madhya Pradesh"})
    assert r_state.status_code == 200
    assert r_state.json()["total"] >= 1
    assert any(c["id"] == seed_craft.id for c in r_state.json()["items"])

    # Search by GI tag
    r_gi = await client.get("/api/v1/crafts", params={"has_gi_tag": True})
    assert r_gi.status_code == 200
    assert r_gi.json()["total"] >= 1

    # Search by text query
    r_query = await client.get("/api/v1/crafts", params={"query": "Chanderi"})
    assert r_query.status_code == 200
    assert r_query.json()["total"] >= 1


@pytest.mark.asyncio
async def test_artisan_craft_many_to_many_association(
    client: AsyncClient,
    artisan_headers: dict,
    seed_craft: Craft,
    admin_headers: dict
):
    """
    Verifies that an artisan can link multiple crafts with skill tiers,
    experience, and master techniques.
    """
    # 1. Ensure artisan profile exists
    await client.post("/api/v1/artisans/me", headers=artisan_headers, json={
        "full_name": "Multi-Craft Master",
        "state": "Madhya Pradesh",
        "district": "Ashoknagar",
        "pincode": "473446",
        "primary_craft_id": seed_craft.id,
        "monthly_production_capacity": 30
    })

    # 2. Link primary craft with MASTER_CRAFTSMAN skill level
    r_link = await client.post("/api/v1/artisans/me/crafts", headers=artisan_headers, json={
        "craft_id": seed_craft.id,
        "skill_level": "MASTER_CRAFTSMAN",
        "years_of_experience": 25,
        "is_primary": True,
        "technique": "Fine Zari Eknal Weaving"
    })
    assert r_link.status_code == 201
    assoc = r_link.json()
    assert assoc["skill_level"] == "MASTER_CRAFTSMAN"
    assert assoc["years_of_experience"] == 25
    assert assoc["is_primary"] is True

    # 3. Duplicate linkage returns 409 Conflict
    r_dup = await client.post("/api/v1/artisans/me/crafts", headers=artisan_headers, json={
        "craft_id": seed_craft.id
    })
    assert r_dup.status_code == 409

    # 4. List my crafts
    r_list = await client.get("/api/v1/artisans/me/crafts", headers=artisan_headers)
    assert r_list.status_code == 200
    assert len(r_list.json()) == 1

    # 5. Unlink craft
    r_del = await client.delete(f"/api/v1/artisans/me/crafts/{seed_craft.id}", headers=artisan_headers)
    assert r_del.status_code == 200

    r_empty = await client.get("/api/v1/artisans/me/crafts", headers=artisan_headers)
    assert len(r_empty.json()) == 0
