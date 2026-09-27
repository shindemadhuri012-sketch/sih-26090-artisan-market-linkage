"""
SIH 26090: Smart Matching Service
Orchestrates buyer requirement management, AI understanding extraction/staging,
vector embedding generation, candidate retrieval, hybrid matching scoring, and persistence.
"""

from datetime import datetime, timezone
from decimal import Decimal
import json
import re
from typing import List, Optional, Tuple, Dict, Any

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.config import settings
from backend.app.models.buyer import BuyerProfile, BuyerRequirement, Match, MatchExplanation
from backend.app.models.requirement_understanding import RequirementUnderstanding
from backend.app.models.product import Product, ProductAttributes
from backend.app.models.artisan import ArtisanProfile
from backend.app.models.craft import Craft, CraftCategory
from backend.app.schemas.matching import (
    BuyerRequirementCreate,
    BuyerRequirementUpdate,
    RequirementUnderstandingConfirmRequest
)
from backend.app.services.audit_service import record_audit_event
from ai.providers.embeddings.factory import get_embedding_provider
from ai.matching.engine import MatchingEngine, MatchScorecard, MATCHING_ENGINE_V1
from ai.matching.prompts.understanding_prompts import (
    RFQ_UNDERSTANDING_SYSTEM_PROMPT,
    RFQ_UNDERSTANDING_USER_TEMPLATE
)


class MatchingService:
    """Service layer managing requirements, understanding, and hybrid matching runs."""

    @staticmethod
    async def create_requirement(
        db: AsyncSession,
        buyer_id: str,
        payload: BuyerRequirementCreate
    ) -> BuyerRequirement:
        """Creates a new canonical buyer requirement."""
        requirement = BuyerRequirement(
            buyer_id=buyer_id,
            title=payload.title,
            raw_text=payload.raw_text,
            target_craft_id=payload.target_craft_id,
            target_category_id=payload.target_category_id,
            required_quantity=payload.required_quantity,
            target_unit_price_inr=payload.target_unit_price_inr,
            max_budget_inr=payload.max_budget_inr,
            deadline_date=payload.deadline_date,
            requires_gi_certification=payload.requires_gi_certification,
            desired_materials=payload.desired_materials or [],
            desired_techniques=payload.desired_techniques or [],
            desired_motifs=payload.desired_motifs or [],
            preferred_region=payload.preferred_region,
            max_acceptable_moq=payload.max_acceptable_moq,
            max_lead_time_days=payload.max_lead_time_days,
            requires_customization=payload.requires_customization,
            quality_specifications=payload.quality_specifications,
            packaging_requirements=payload.packaging_requirements,
            destination_state=payload.destination_state,
            destination_pincode=payload.destination_pincode,
            currency="INR",
            status="OPEN",
            embedding_model_version=settings.AI_EMBEDDING_MODEL,
            data_provenance_level="USER_DECLARED",
            provenance_state="HUMAN_CONFIRMED"
        )
        db.add(requirement)
        await db.flush()
        await db.refresh(requirement)

        # Generate semantic vector embedding
        await MatchingService.generate_and_store_embedding(db, requirement)

        await record_audit_event(
            db=db,
            action="BUYER_REQUIREMENT_CREATED",
            entity_type="BuyerRequirement",
            entity_id=requirement.id,
            actor_user_id=buyer_id,
            payload_after={"title": requirement.title, "quantity": requirement.required_quantity}
        )

        return requirement

    @staticmethod
    async def generate_and_store_embedding(
        db: AsyncSession,
        requirement: BuyerRequirement
    ) -> None:
        """Constructs canonical text and persists 768-dimensional embedding."""
        provider = get_embedding_provider()

        craft_name = ""
        if requirement.target_craft_id:
            craft_res = await db.execute(select(Craft).where(Craft.id == requirement.target_craft_id))
            craft = craft_res.scalar_one_or_none()
            if craft:
                craft_name = craft.name

        materials_str = ", ".join(requirement.desired_materials or [])
        techniques_str = ", ".join(requirement.desired_techniques or [])

        canonical_text = (
            f"Requirement: {requirement.title} | "
            f"Craft: {craft_name} | "
            f"Desired Materials: {materials_str} | "
            f"Desired Techniques: {techniques_str} | "
            f"Description: {requirement.raw_text}"
        )

        try:
            embed_res = await provider.embed_text(canonical_text)
            requirement.embedding = embed_res.embedding
            requirement.embedding_model_version = embed_res.model_name
            await db.flush()
        except Exception:
            # Safe degradation: if embedding fails, requirement remains matchable via structured filters
            pass

    @staticmethod
    async def extract_requirement_understanding(
        db: AsyncSession,
        requirement: BuyerRequirement,
        buyer_id: str
    ) -> RequirementUnderstanding:
        """
        Parses raw requirement text into staged structured suggestions.
        Strictly preserves staging isolation: does not overwrite canonical fields.
        """
        raw_text = requirement.raw_text
        extracted: Dict[str, Any] = {}
        confidences: Dict[str, Optional[float]] = {}
        provider_name = "mock"
        model_name = "rule-based-heuristic"

        # Rule-based deterministic extraction fallback
        # Check quantity
        qty_match = re.search(r"(\d+)\s*(units?|pieces?|pcs?|stoles?|sarees?|boxes?|items?)", raw_text, re.IGNORECASE)
        if qty_match:
            try:
                extracted["required_quantity"] = int(qty_match.group(1))
                confidences["required_quantity"] = 0.90
            except ValueError:
                pass

        # Check budget/price (e.g. ₹1200 or Rs. 1200 or under 1500)
        budget_match = re.search(r"(?:₹|rs\.?|inr|under|budget\s*(?:of)?)\s*(\d+(?:,\d+)*(?:\.\d{2})?)", raw_text, re.IGNORECASE)
        if budget_match:
            try:
                val = budget_match.group(1).replace(",", "")
                extracted["target_unit_price_inr"] = float(val)
                confidences["target_unit_price_inr"] = 0.85
            except ValueError:
                pass

        # Check GI
        if re.search(r"\b(gi|geographical indication|certified)\b", raw_text, re.IGNORECASE):
            extracted["requires_gi_certification"] = True
            confidences["requires_gi_certification"] = 0.95

        # Check customization
        if re.search(r"\b(custom|customization|logo|embroidery|bespoke)\b", raw_text, re.IGNORECASE):
            extracted["requires_customization"] = True
            confidences["requires_customization"] = 0.85

        # Check craft keywords from known registry
        crafts_res = await db.execute(select(Craft.id, Craft.name, Craft.category_id))
        all_crafts = crafts_res.fetchall()
        for cid, cname, cat_id in all_crafts:
            if cname.lower() in raw_text.lower():
                extracted["target_craft_id"] = cid
                extracted["craft_name"] = cname
                extracted["target_category_id"] = cat_id
                confidences["craft_name"] = 0.92
                break

        # Check common craft materials
        common_materials = ["silk", "cotton", "wool", "brass", "wood", "clay", "leather", "zari", "terracotta", "jute"]
        found_mat = [m for m in common_materials if re.search(r"\b" + m + r"\b", raw_text, re.IGNORECASE)]
        if found_mat:
            extracted["desired_materials"] = found_mat
            confidences["desired_materials"] = 0.85

        understanding = RequirementUnderstanding(
            requirement_id=requirement.id,
            buyer_id=buyer_id,
            raw_input_text=raw_text,
            extracted_fields_json=extracted,
            confidence_scores_json=confidences,
            provider=provider_name,
            model_name=model_name,
            prompt_version="rfq_understanding_v1",
            status="SUGGESTED",
            is_confirmed_by_buyer=False
        )
        db.add(understanding)
        await db.flush()
        await db.refresh(understanding)

        return understanding

    @staticmethod
    async def confirm_requirement_understanding(
        db: AsyncSession,
        understanding: RequirementUnderstanding,
        requirement: BuyerRequirement,
        overrides: Optional[Dict[str, Any]] = None
    ) -> BuyerRequirement:
        """
        Human confirmation workflow: promotes staged understanding suggestions
        into canonical BuyerRequirement fields.
        """
        merged_fields = dict(understanding.extracted_fields_json)
        if overrides:
            merged_fields.update(overrides)

        # Apply to canonical requirement
        if "target_craft_id" in merged_fields and merged_fields["target_craft_id"]:
            requirement.target_craft_id = merged_fields["target_craft_id"]
        if "target_category_id" in merged_fields and merged_fields["target_category_id"]:
            requirement.target_category_id = merged_fields["target_category_id"]
        if "required_quantity" in merged_fields and merged_fields["required_quantity"]:
            requirement.required_quantity = int(merged_fields["required_quantity"])
        if "target_unit_price_inr" in merged_fields and merged_fields["target_unit_price_inr"] is not None:
            requirement.target_unit_price_inr = Decimal(str(merged_fields["target_unit_price_inr"]))
        if "max_budget_inr" in merged_fields and merged_fields["max_budget_inr"] is not None:
            requirement.max_budget_inr = Decimal(str(merged_fields["max_budget_inr"]))
        if "requires_gi_certification" in merged_fields:
            requirement.requires_gi_certification = bool(merged_fields["requires_gi_certification"])
        if "requires_customization" in merged_fields:
            requirement.requires_customization = bool(merged_fields["requires_customization"])
        if "desired_materials" in merged_fields:
            requirement.desired_materials = list(merged_fields["desired_materials"])
        if "preferred_region" in merged_fields and merged_fields["preferred_region"]:
            requirement.preferred_region = str(merged_fields["preferred_region"])

        understanding.status = "CONFIRMED"
        understanding.is_confirmed_by_buyer = True
        understanding.confirmed_fields_json = merged_fields
        understanding.confirmed_at = datetime.now(timezone.utc)

        await db.flush()

        # Re-index embedding with updated confirmed criteria
        await MatchingService.generate_and_store_embedding(db, requirement)

        return requirement

    @staticmethod
    async def run_matches(
        db: AsyncSession,
        requirement: BuyerRequirement,
        limit: int = 20
    ) -> List[Match]:
        """
        Executes two-stage hybrid matching:
        1. Hard constraint filter
        2. Multi-criteria scoring & explanation synthesis
        3. Atomically persists ranked matches
        """
        # Ensure requirement has embedding if possible
        if not requirement.embedding:
            await MatchingService.generate_and_store_embedding(db, requirement)

        # Clear existing un-enquired matches for this requirement
        existing_matches_query = select(Match).where(
            and_(
                Match.requirement_id == requirement.id,
                Match.status.in_(["PROPOSED", "VIEWED"])
            )
        )
        existing_res = await db.execute(existing_matches_query)
        for old_match in existing_res.scalars().all():
            await db.delete(old_match)
        await db.flush()

        # Stage 1: Candidate Retrieval
        # Query PUBLISHED products with active artisan profiles
        candidates_query = (
            select(Product)
            .options(
                selectinload(Product.artisan),
                selectinload(Product.craft),
                selectinload(Product.category),
                selectinload(Product.attributes)
            )
            .where(Product.status == "PUBLISHED")
            .limit(100)
        )
        res = await db.execute(candidates_query)
        all_candidates = res.scalars().all()

        scored_candidates: List[Tuple[Product, MatchScorecard]] = []

        for prod in all_candidates:
            # 1. Hard constraint evaluation
            eligible, elim_reason = MatchingEngine.evaluate_hard_constraints(requirement, prod)
            if not eligible:
                continue

            # 2. Semantic similarity calculation
            sem_sim: Optional[float] = None
            if requirement.embedding and prod.embedding:
                sem_sim = MatchingEngine_calculate_cosine(requirement.embedding, prod.embedding)

            # 3. Multi-criteria hybrid scoring
            scorecard = MatchingEngine.score_candidate(
                requirement=requirement,
                product=prod,
                semantic_similarity=sem_sim
            )

            scored_candidates.append((prod, scorecard))

        # Deterministic sorting: (composite_score DESC, provenance_bonus DESC, capacity DESC, id ASC)
        scored_candidates.sort(
            key=lambda item: (
                item[1].composite_score,
                item[1].provenance_bonus,
                getattr(item[0], "monthly_production_capacity", 0) or 0,
                item[0].id
            ),
            reverse=True
        )

        top_candidates = scored_candidates[:limit]
        created_matches: List[Match] = []

        for rank, (prod, card) in enumerate(top_candidates, start=1):
            match_record = Match(
                requirement_id=requirement.id,
                artisan_id=prod.artisan_id,
                product_id=prod.id,
                engine_version=card.engine_version,
                data_sufficiency_state=card.data_sufficiency_state,
                composite_score=card.composite_score,
                semantic_similarity=card.semantic_similarity,
                craft_compatibility=card.craft_compatibility,
                material_compatibility=card.material_compatibility,
                technique_compatibility=card.technique_compatibility,
                capacity_compatibility=card.capacity_compatibility,
                price_compatibility=card.price_compatibility,
                lead_time_compatibility=card.lead_time_compatibility,
                provenance_bonus=card.provenance_bonus,
                rank=rank,
                status="PROPOSED",
                is_dismissed_by_buyer=False
            )
            db.add(match_record)
            await db.flush()

            explanation = MatchExplanation(
                match_id=match_record.id,
                summary_explanation=card.summary_explanation,
                capacity_justification=card.capacity_justification,
                price_justification=card.price_justification,
                provenance_justification=card.provenance_justification,
                factors_json=card.active_weights,
                positive_reasons=card.positive_reasons,
                limitations=card.limitations,
                unmatched_fields=card.unmatched_fields,
                missing_fields=card.missing_fields
            )
            db.add(explanation)
            created_matches.append(match_record)

        requirement.status = "MATCHED"
        await db.flush()

        await record_audit_event(
            db=db,
            action="MATCH_RUN_EXECUTED",
            entity_type="BuyerRequirement",
            entity_id=requirement.id,
            actor_user_id=requirement.buyer_id,
            payload_after={
                "matches_count": len(created_matches),
                "top_score": created_matches[0].composite_score if created_matches else 0.0,
                "engine_version": MATCHING_ENGINE_V1
            }
        )

        return created_matches


def MatchingEngine_calculate_cosine(vec_a: List[float], vec_b: List[float]) -> float:
    """Helper computing dot product of normalized vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.50
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    return max(0.0, min(1.0, float(dot)))
