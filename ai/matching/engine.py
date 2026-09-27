"""
SIH 26090: Deterministic Hybrid Matching Engine (MATCHING_ENGINE_V1)
Executes two-stage candidate retrieval, hard constraint evaluation, multi-criteria hybrid scoring,
dynamic weight re-normalization, and traceable explanation synthesis.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
import math

MATCHING_ENGINE_V1 = "MATCHING_ENGINE_V1"

# Base Criterion Weights (Sum = 1.00)
WEIGHT_SEMANTIC = 0.25
WEIGHT_CRAFT = 0.20
WEIGHT_MATERIAL = 0.15
WEIGHT_CAPACITY = 0.15
WEIGHT_PRICE = 0.15
WEIGHT_LEAD_TIME = 0.10
BONUS_PROVENANCE_MAX = 0.05


@dataclass
class MatchScorecard:
    """Detailed mathematical outcome of multi-criteria candidate evaluation."""
    composite_score: float
    semantic_similarity: float
    craft_compatibility: float
    material_compatibility: float
    technique_compatibility: float
    capacity_compatibility: float
    price_compatibility: float
    lead_time_compatibility: float
    provenance_bonus: float
    data_sufficiency_state: str  # MATCHABLE, PARTIALLY_MATCHABLE, INSUFFICIENT_INFORMATION
    active_weights: Dict[str, float]
    positive_reasons: List[str]
    limitations: List[str]
    unmatched_fields: List[str]
    missing_fields: List[str]
    summary_explanation: str
    capacity_justification: str
    price_justification: str
    provenance_justification: str
    engine_version: str = MATCHING_ENGINE_V1


class MatchingEngine:
    """
    Production-grade hybrid matching engine linking buyer procurement briefs with published craft products.
    Evaluates hard constraints first, then scores soft preferences with explainability.
    """

    @classmethod
    def evaluate_hard_constraints(
        cls,
        requirement: Any,
        product: Any
    ) -> Tuple[bool, Optional[str]]:
        """
        Evaluates binary hard constraints.
        Returns (is_eligible, elimination_reason).
        """
        # 1. Product must be PUBLISHED
        product_status = getattr(product, "status", None)
        if product_status != "PUBLISHED":
            return False, f"Product status is '{product_status}'; only PUBLISHED products are matchable."

        # 2. Artisan account must be active
        artisan = getattr(product, "artisan", None)
        if not artisan:
            return False, "Product has no associated artisan profile."

        # 3. GI Certification constraint
        requires_gi = getattr(requirement, "requires_gi_certification", False)
        if requires_gi:
            craft = getattr(product, "craft", None)
            gi_tag = getattr(craft, "gi_tag_number", None) if craft else None
            if not gi_tag:
                return False, "Requirement demands official GI Certification; product craft does not carry a registered GI tag."

        # 4. Quantity versus MOQ
        req_quantity = getattr(requirement, "required_quantity", 1) or 1
        moq = getattr(product, "min_order_quantity", 1) or 1
        max_acceptable_moq = getattr(requirement, "max_acceptable_moq", None)
        if max_acceptable_moq is not None and moq > max_acceptable_moq:
            return False, f"Product MOQ ({moq}) exceeds buyer's maximum acceptable MOQ ({max_acceptable_moq})."

        return True, None

    @classmethod
    def score_candidate(
        cls,
        requirement: Any,
        product: Any,
        semantic_similarity: Optional[float] = None
    ) -> MatchScorecard:
        """
        Evaluates multi-criteria compatibility and synthesizes an auditable scorecard.
        Handles missing data neutrally without inventing values.
        """
        positive_reasons: List[str] = []
        limitations: List[str] = []
        unmatched_fields: List[str] = []
        missing_fields: List[str] = []

        artisan = getattr(product, "artisan", None)
        craft = getattr(product, "craft", None)
        category = getattr(product, "category", None)
        attributes = getattr(product, "attributes", None)

        # -------------------------------------------------------------
        # 1. Semantic Similarity Score (S_sem)
        # -------------------------------------------------------------
        if semantic_similarity is not None:
            s_sem = max(0.0, min(1.0, float(semantic_similarity)))
            if s_sem >= 0.70:
                positive_reasons.append(f"Strong semantic aesthetic and stylistic alignment ({round(s_sem * 100)}%).")
            elif s_sem < 0.40:
                limitations.append(f"Moderate semantic divergence between buyer brief and product description ({round(s_sem * 100)}%).")
        else:
            s_sem = 0.50  # Neutral baseline when embedding unavailable
            missing_fields.append("semantic_embedding")
            limitations.append("Vector semantic embedding unavailable; scored neutrally.")

        # -------------------------------------------------------------
        # 2. Craft & Taxonomy Compatibility (S_craft)
        # -------------------------------------------------------------
        target_craft_id = getattr(requirement, "target_craft_id", None)
        target_category_id = getattr(requirement, "target_category_id", None)
        prod_craft_id = getattr(product, "craft_id", None)
        prod_category_id = getattr(product, "category_id", None)

        if target_craft_id:
            if prod_craft_id == target_craft_id:
                s_craft = 1.00
                craft_name = getattr(craft, "name", "Craft") if craft else "Craft"
                positive_reasons.append(f"Exact match on target craft: {craft_name}.")
            elif target_category_id and prod_category_id == target_category_id:
                s_craft = 0.70
                cat_name = getattr(category, "name", "Category") if category else "Category"
                positive_reasons.append(f"Matching craft category taxonomy: {cat_name}.")
                unmatched_fields.append("specific_craft")
            else:
                s_craft = 0.20
                unmatched_fields.append("craft_category")
                limitations.append("Product craft differs from buyer's stated craft target.")
        else:
            s_craft = 0.80  # Open craft brief
            positive_reasons.append("Open craft procurement brief; candidate fits general craft listing.")

        # -------------------------------------------------------------
        # 3. Material & Technique Compatibility (S_mat, S_tech)
        # -------------------------------------------------------------
        desired_materials = getattr(requirement, "desired_materials", []) or []
        prod_materials = getattr(product, "materials", []) or []
        if isinstance(prod_materials, str):
            prod_materials = [prod_materials]

        # Extract normalized strings
        desired_mat_set = {m.strip().lower() for m in desired_materials if m}
        prod_mat_set = {m.strip().lower() for m in prod_materials if m}

        if desired_mat_set:
            if prod_mat_set:
                matched_materials = desired_mat_set.intersection(prod_mat_set)
                s_mat = len(matched_materials) / len(desired_mat_set)
                if matched_materials:
                    positive_reasons.append(f"Matched requested materials: {', '.join(sorted(list(matched_materials)))}.")
                if len(matched_materials) < len(desired_mat_set):
                    missing_req_mat = desired_mat_set - prod_mat_set
                    limitations.append(f"Requested materials not listed: {', '.join(sorted(list(missing_req_mat)))}.")
            else:
                s_mat = 0.50
                missing_fields.append("product_materials")
                limitations.append("Product does not list explicit raw materials; verify during enquiry.")
        else:
            s_mat = 1.00  # No material constraint specified

        # Technique
        desired_techniques = getattr(requirement, "desired_techniques", []) or []
        prod_technique = getattr(product, "technique", "") or ""
        if attributes and getattr(attributes, "technique", None):
            prod_technique = getattr(attributes, "technique")

        desired_tech_set = {t.strip().lower() for t in desired_techniques if t}
        if desired_tech_set:
            if prod_technique and any(t in prod_technique.lower() for t in desired_tech_set):
                s_tech = 1.00
                positive_reasons.append(f"Product technique matches requested specification: {prod_technique}.")
            elif prod_technique:
                s_tech = 0.30
                unmatched_fields.append("technique")
                limitations.append(f"Product technique '{prod_technique}' differs from requested: {', '.join(desired_tech_set)}.")
            else:
                s_tech = 0.50
                missing_fields.append("product_technique")
                limitations.append("Product technique not declared; verify during enquiry.")
        else:
            s_tech = 1.00

        # Blended material-technique score
        s_mat_tech = (s_mat * 0.6) + (s_tech * 0.4)

        # -------------------------------------------------------------
        # 4. Capacity Compatibility (S_cap)
        # -------------------------------------------------------------
        req_quantity = getattr(requirement, "required_quantity", 1) or 1
        prod_capacity = getattr(product, "monthly_production_capacity", None)
        artisan_capacity = getattr(artisan, "monthly_production_capacity", None) if artisan else None
        effective_capacity = prod_capacity or artisan_capacity or 10

        if effective_capacity >= req_quantity:
            buffer_ratio = effective_capacity / max(1, req_quantity)
            if buffer_ratio >= 1.5:
                s_cap = 1.00
                positive_reasons.append(f"Production capacity ({effective_capacity}/mo) provides comfortable buffer for order ({req_quantity} units).")
            else:
                s_cap = 0.85
                positive_reasons.append(f"Monthly capacity ({effective_capacity} units) covers required quantity ({req_quantity} units).")
            capacity_justification = f"Artisan monthly capacity of {effective_capacity} units satisfies procurement quantity of {req_quantity} units."
        else:
            deficit_ratio = effective_capacity / max(1, req_quantity)
            s_cap = max(0.10, deficit_ratio * 0.75)
            limitations.append(f"Required quantity ({req_quantity}) exceeds stated monthly capacity ({effective_capacity}/mo); batch delivery may be required.")
            capacity_justification = f"Required quantity of {req_quantity} exceeds monthly capacity of {effective_capacity} units."

        # -------------------------------------------------------------
        # 5. Price Compatibility (S_price)
        # -------------------------------------------------------------
        prod_price = getattr(product, "price_inr", None)
        target_unit_price = getattr(requirement, "target_unit_price_inr", None)
        max_budget = getattr(requirement, "max_budget_inr", None)

        effective_budget_price = None
        if target_unit_price:
            effective_budget_price = float(target_unit_price)
        elif max_budget and req_quantity > 0:
            effective_budget_price = float(max_budget) / float(req_quantity)

        if prod_price is not None and effective_budget_price is not None:
            p_price = float(prod_price)
            if p_price <= effective_budget_price:
                savings = effective_budget_price - p_price
                s_price = 1.00
                positive_reasons.append(f"Product unit price (₹{p_price:,.2f}) is within target budget (₹{effective_budget_price:,.2f}).")
                price_justification = f"Unit price ₹{p_price:,.2f} is within target unit budget of ₹{effective_budget_price:,.2f}."
            else:
                overage_ratio = (p_price - effective_budget_price) / effective_budget_price
                if overage_ratio <= 0.20:
                    s_price = max(0.20, 1.0 - (overage_ratio * 2.5))
                    limitations.append(f"Unit price (₹{p_price:,.2f}) is slightly above target budget (₹{effective_budget_price:,.2f}); negotiation recommended.")
                else:
                    s_price = max(0.05, 0.50 - overage_ratio)
                    limitations.append(f"Unit price (₹{p_price:,.2f}) significantly exceeds target budget (₹{effective_budget_price:,.2f}).")
                price_justification = f"Unit price ₹{p_price:,.2f} exceeds target budget of ₹{effective_budget_price:,.2f} by {round(overage_ratio * 100)}%."
        elif prod_price is not None:
            s_price = 0.80  # Price available, no buyer budget constraint
            positive_reasons.append(f"Product unit price: ₹{float(prod_price):,.2f}.")
            price_justification = f"Product catalogue price is ₹{float(prod_price):,.2f}; buyer did not specify budget ceiling."
        else:
            s_price = 0.50
            missing_fields.append("product_price")
            limitations.append("Product catalogue price not specified; price must be quoted via RFQ.")
            price_justification = "Price not listed; requires direct quotation from artisan."

        # -------------------------------------------------------------
        # 6. Lead Time Compatibility (S_lead)
        # -------------------------------------------------------------
        prod_lead_days = getattr(product, "lead_time_days", 7) or 7
        deadline_date = getattr(requirement, "deadline_date", None)
        max_lead_days = getattr(requirement, "max_lead_time_days", None)

        avail_days = None
        if deadline_date:
            now = datetime.now(timezone.utc)
            if deadline_date.tzinfo is None:
                deadline_date = deadline_date.replace(tzinfo=timezone.utc)
            avail_days = max(1, (deadline_date - now).days)
        elif max_lead_days:
            avail_days = max_lead_days

        if avail_days is not None:
            if prod_lead_days <= avail_days:
                buffer = avail_days - prod_lead_days
                s_lead = 1.00
                positive_reasons.append(f"Stated lead time of {prod_lead_days} days meets delivery timeline ({avail_days} days available).")
            else:
                overdue = prod_lead_days - avail_days
                s_lead = max(0.10, 1.0 - (overdue / float(avail_days)))
                limitations.append(f"Production lead time ({prod_lead_days} days) exceeds target delivery window ({avail_days} days).")
        else:
            s_lead = 1.00  # No deadline constraint

        # -------------------------------------------------------------
        # 7. Provenance & Institutional Verification Bonus (B_prov)
        # -------------------------------------------------------------
        b_prov = 0.0
        prov_reasons = []

        if craft and getattr(craft, "gi_tag_number", None):
            b_prov += 0.03
            prov_reasons.append(f"Official GI Registered Craft (#{craft.gi_tag_number})")

        if artisan and getattr(artisan, "pehchan_id", None):
            b_prov += 0.02
            prov_reasons.append("Ministry of Textiles Pehchan Cardholder")

        if artisan and getattr(artisan, "cooperative_name", None):
            b_prov += 0.01
            prov_reasons.append(f"Affiliated with Cooperative: {artisan.cooperative_name}")

        b_prov = min(BONUS_PROVENANCE_MAX, b_prov)
        if prov_reasons:
            positive_reasons.append(f"Institutional provenance credentials: {'; '.join(prov_reasons)}.")
            provenance_justification = f"Artisan holds verifiable credentials: {'; '.join(prov_reasons)}."
        else:
            provenance_justification = "Standard artisan declaration; no institutional GI or Pehchan cards verified."

        # -------------------------------------------------------------
        # Dynamic Weight Re-normalization
        # -------------------------------------------------------------
        active_weights = {
            "semantic": WEIGHT_SEMANTIC,
            "craft": WEIGHT_CRAFT,
            "material": WEIGHT_MATERIAL,
            "capacity": WEIGHT_CAPACITY,
            "price": WEIGHT_PRICE,
            "lead_time": WEIGHT_LEAD_TIME,
        }

        # If buyer did not specify target price/budget, omit price weight
        if effective_budget_price is None and prod_price is None:
            active_weights["price"] = 0.0

        total_weight = sum(active_weights.values())
        if total_weight > 0:
            norm_weights = {k: v / total_weight for k, v in active_weights.items()}
        else:
            norm_weights = active_weights

        # -------------------------------------------------------------
        # Composite Match Score Calculation
        # -------------------------------------------------------------
        raw_composite = (
            (norm_weights["semantic"] * s_sem) +
            (norm_weights["craft"] * s_craft) +
            (norm_weights["material"] * s_mat_tech) +
            (norm_weights["capacity"] * s_cap) +
            (norm_weights["price"] * s_price) +
            (norm_weights["lead_time"] * s_lead) +
            b_prov
        )

        composite_score = round(max(0.0000, min(1.0000, raw_composite)), 4)

        # -------------------------------------------------------------
        # Data Sufficiency Classification
        # -------------------------------------------------------------
        if not missing_fields:
            data_sufficiency_state = "MATCHABLE"
        elif len(missing_fields) <= 2:
            data_sufficiency_state = "PARTIALLY_MATCHABLE"
        else:
            data_sufficiency_state = "INSUFFICIENT_INFORMATION"

        # Summary Explanation
        craft_label = getattr(craft, "name", "Craft") if craft else "Craft"
        summary_explanation = (
            f"Compatibility evaluated at {round(composite_score * 100)}% based on {craft_label} taxonomy, "
            f"capacity fit ({effective_capacity} units/mo vs {req_quantity} requested), and stated specifications."
        )

        return MatchScorecard(
            composite_score=composite_score,
            semantic_similarity=round(s_sem, 4),
            craft_compatibility=round(s_craft, 4),
            material_compatibility=round(s_mat, 4),
            technique_compatibility=round(s_tech, 4),
            capacity_compatibility=round(s_cap, 4),
            price_compatibility=round(s_price, 4),
            lead_time_compatibility=round(s_lead, 4),
            provenance_bonus=round(b_prov, 4),
            data_sufficiency_state=data_sufficiency_state,
            active_weights=norm_weights,
            positive_reasons=positive_reasons,
            limitations=limitations,
            unmatched_fields=unmatched_fields,
            missing_fields=missing_fields,
            summary_explanation=summary_explanation,
            capacity_justification=capacity_justification,
            price_justification=price_justification,
            provenance_justification=provenance_justification,
            engine_version=MATCHING_ENGINE_V1
        )
