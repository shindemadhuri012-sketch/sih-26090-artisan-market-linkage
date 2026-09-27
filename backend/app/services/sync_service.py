"""
SIH 26090: Offline Sync Service
Handles sequential replay of queued client mutations, idempotency checks,
server-side authorization re-verification, and conflict detection.
"""

from datetime import datetime, timezone
from decimal import Decimal
import uuid
from typing import Dict, Any, List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.auth import User
from backend.app.models.artisan import ArtisanProfile
from backend.app.models.product import Product, ProductAttributes
from backend.app.models.market import Enquiry
from backend.app.models.sync import SyncOperation
from backend.app.schemas.sync import (
    SyncBatchRequest,
    SyncBatchResponse,
    SyncMutationItem,
    SyncMutationResult
)
from backend.app.schemas.matching import RFQResponseRequest
from backend.app.services.rfq_service import RFQService
from backend.app.services.audit_service import record_audit_event


class SyncService:
    """Orchestrates batch offline synchronization with idempotency and conflict detection."""

    @staticmethod
    async def process_sync_batch(
        db: AsyncSession,
        current_user: User,
        batch_request: SyncBatchRequest
    ) -> SyncBatchResponse:
        """
        Processes a batch of offline mutations chronologically:
        1. Checks idempotency_key in sync_operations to prevent duplicate execution.
        2. Re-verifies server-side authorization and ownership (IDOR defense).
        3. Detects conflicts using updated_at timestamps.
        4. Applies valid mutations and logs audit events.
        """
        # Fetch artisan profile if applicable
        a_res = await db.execute(select(ArtisanProfile).where(ArtisanProfile.user_id == current_user.id))
        artisan_profile = a_res.scalar_one_or_none()

        results: List[SyncMutationResult] = []
        committed_count = 0
        conflict_count = 0
        rejected_count = 0

        for mutation in batch_request.mutations:
            # 1. Idempotency Check
            existing_op_res = await db.execute(
                select(SyncOperation).where(SyncOperation.idempotency_key == mutation.idempotency_key)
            )
            existing_op = existing_op_res.scalar_one_or_none()
            if existing_op:
                results.append(
                    SyncMutationResult(
                        client_mutation_id=mutation.client_mutation_id,
                        idempotency_key=mutation.idempotency_key,
                        status="ALREADY_PROCESSED",
                        server_entity_id=existing_op.entity_id,
                        response_payload=existing_op.response_payload
                    )
                )
                committed_count += 1
                continue

            # 2. Dispatch by entity_type and operation_type
            try:
                if mutation.entity_type == "PRODUCT":
                    res = await SyncService._handle_product_mutation(
                        db=db,
                        artisan=artisan_profile,
                        mutation=mutation,
                        current_user=current_user
                    )
                elif mutation.entity_type == "RFQ_RESPONSE":
                    res = await SyncService._handle_rfq_mutation(
                        db=db,
                        artisan=artisan_profile,
                        mutation=mutation,
                        current_user=current_user
                    )
                else:
                    res = SyncMutationResult(
                        client_mutation_id=mutation.client_mutation_id,
                        idempotency_key=mutation.idempotency_key,
                        status="REJECTED",
                        error_message=f"Unsupported entity type: {mutation.entity_type}"
                    )
            except Exception as e:
                res = SyncMutationResult(
                    client_mutation_id=mutation.client_mutation_id,
                    idempotency_key=mutation.idempotency_key,
                    status="REJECTED",
                    error_message=str(e)
                )

            # Update counters
            if res.status == "COMMITTED":
                committed_count += 1
                # Record SyncOperation
                sync_record = SyncOperation(
                    idempotency_key=mutation.idempotency_key,
                    user_id=current_user.id,
                    entity_type=mutation.entity_type,
                    entity_id=res.server_entity_id or mutation.entity_id,
                    operation_type=mutation.operation_type,
                    status="COMMITTED",
                    client_mutation_id=mutation.client_mutation_id,
                    response_payload=res.response_payload
                )
                db.add(sync_record)
            elif res.status == "CONFLICT":
                conflict_count += 1
            else:
                rejected_count += 1

            results.append(res)

        await db.flush()

        return SyncBatchResponse(
            total_submitted=len(batch_request.mutations),
            committed=committed_count,
            conflicts=conflict_count,
            rejected=rejected_count,
            results=results
        )

    @staticmethod
    async def _handle_product_mutation(
        db: AsyncSession,
        artisan: Optional[ArtisanProfile],
        mutation: SyncMutationItem,
        current_user: User
    ) -> SyncMutationResult:
        if not artisan:
            return SyncMutationResult(
                client_mutation_id=mutation.client_mutation_id,
                idempotency_key=mutation.idempotency_key,
                status="REJECTED",
                error_message="Only registered artisans can sync product mutations."
            )

        payload = mutation.payload

        if mutation.operation_type == "CREATE":
            # Generate server SKU
            sku_hex = uuid.uuid4().hex[:4].upper()
            sku = f"PRD-{sku_hex}"

            materials_list = payload.get("materials", [])
            techniques_list = payload.get("techniques", [])
            primary_mat = materials_list[0] if (isinstance(materials_list, list) and materials_list) else "Handcrafted Material"
            tech = techniques_list[0] if (isinstance(techniques_list, list) and techniques_list) else "Traditional Craft"

            product = Product(
                artisan_id=artisan.id,
                craft_id=payload.get("craft_id"),
                title=payload.get("title", "Untitled Draft"),
                storytelling_description=payload.get("storytelling_description") or payload.get("description") or "Handcrafted authentic craft product created offline.",
                price_inr=Decimal(str(payload.get("price_inr", "100.00"))),
                stock_quantity=int(payload.get("stock_quantity", 0)),
                monthly_production_capacity=int(payload.get("monthly_production_capacity", 10)),
                min_order_quantity=int(payload.get("min_order_quantity", 1)),
                lead_time_days=int(payload.get("lead_time_days", 14)),
                sku=sku,
                status="DRAFT",
                materials=materials_list if isinstance(materials_list, list) else [],
                technique=tech
            )
            db.add(product)
            await db.flush()

            # Default attributes
            attr = ProductAttributes(
                product_id=product.id,
                primary_material=primary_mat,
                technique=tech,
                colors=payload.get("colors", []),
                raw_attributes_json={"motifs": payload.get("motifs", [])}
            )
            db.add(attr)
            await db.flush()

            await record_audit_event(
                db=db,
                actor_user_id=current_user.id,
                action="OFFLINE_PRODUCT_CREATED",
                entity_type="Product",
                entity_id=product.id,
                payload_after={"sku": product.sku, "client_id": mutation.client_mutation_id}
            )

            return SyncMutationResult(
                client_mutation_id=mutation.client_mutation_id,
                idempotency_key=mutation.idempotency_key,
                status="COMMITTED",
                server_entity_id=product.id,
                response_payload={"id": product.id, "sku": product.sku, "status": product.status}
            )

        elif mutation.operation_type == "UPDATE":
            # Verify ownership
            p_res = await db.execute(select(Product).where(Product.id == mutation.entity_id))
            prod = p_res.scalar_one_or_none()
            if not prod:
                return SyncMutationResult(
                    client_mutation_id=mutation.client_mutation_id,
                    idempotency_key=mutation.idempotency_key,
                    status="REJECTED",
                    error_message=f"Product with ID '{mutation.entity_id}' not found on server."
                )
            if prod.artisan_id != artisan.id:
                return SyncMutationResult(
                    client_mutation_id=mutation.client_mutation_id,
                    idempotency_key=mutation.idempotency_key,
                    status="REJECTED",
                    error_message="Forbidden: You do not own this product listing."
                )

            # Conflict Detection: Compare client base updated_at
            client_base_ts = payload.get("client_base_updated_at")
            if client_base_ts and prod.updated_at:
                client_dt = datetime.fromisoformat(client_base_ts.replace("Z", "+00:00"))
                server_dt = prod.updated_at
                if server_dt.tzinfo is None:
                    server_dt = server_dt.replace(tzinfo=timezone.utc)
                # If server is more recent by > 1 second
                if (server_dt - client_dt).total_seconds() > 1.0:
                    return SyncMutationResult(
                        client_mutation_id=mutation.client_mutation_id,
                        idempotency_key=mutation.idempotency_key,
                        status="CONFLICT",
                        server_entity_id=prod.id,
                        error_message="Product was modified on the server while client was offline.",
                        conflict_details={
                            "server_updated_at": prod.updated_at.isoformat(),
                            "server_title": prod.title,
                            "server_price_inr": str(prod.price_inr),
                            "server_stock": prod.stock_quantity
                        }
                    )

            # Apply updates
            if "title" in payload:
                prod.title = payload["title"]
            if "price_inr" in payload:
                prod.price_inr = Decimal(str(payload["price_inr"]))
            if "stock_quantity" in payload:
                prod.stock_quantity = int(payload["stock_quantity"])
            if "monthly_production_capacity" in payload:
                prod.monthly_production_capacity = int(payload["monthly_production_capacity"])
            if "lead_time_days" in payload:
                prod.lead_time_days = int(payload["lead_time_days"])

            await db.flush()

            return SyncMutationResult(
                client_mutation_id=mutation.client_mutation_id,
                idempotency_key=mutation.idempotency_key,
                status="COMMITTED",
                server_entity_id=prod.id,
                response_payload={"id": prod.id, "sku": prod.sku, "status": prod.status}
            )

        return SyncMutationResult(
            client_mutation_id=mutation.client_mutation_id,
            idempotency_key=mutation.idempotency_key,
            status="REJECTED",
            error_message=f"Unsupported operation '{mutation.operation_type}' on entity PRODUCT"
        )

    @staticmethod
    async def _handle_rfq_mutation(
        db: AsyncSession,
        artisan: Optional[ArtisanProfile],
        mutation: SyncMutationItem,
        current_user: User
    ) -> SyncMutationResult:
        if not artisan:
            return SyncMutationResult(
                client_mutation_id=mutation.client_mutation_id,
                idempotency_key=mutation.idempotency_key,
                status="REJECTED",
                error_message="Only registered artisans can respond to RFQs."
            )

        e_res = await db.execute(select(Enquiry).where(Enquiry.id == mutation.entity_id))
        enquiry = e_res.scalar_one_or_none()
        if not enquiry:
            return SyncMutationResult(
                client_mutation_id=mutation.client_mutation_id,
                idempotency_key=mutation.idempotency_key,
                status="REJECTED",
                error_message=f"RFQ with ID '{mutation.entity_id}' not found."
            )
        if enquiry.artisan_id != artisan.id:
            return SyncMutationResult(
                client_mutation_id=mutation.client_mutation_id,
                idempotency_key=mutation.idempotency_key,
                status="REJECTED",
                error_message="Forbidden: RFQ is not addressed to you."
            )

        # Conflict check: If RFQ reached terminal status on server
        if enquiry.status in {"ACCEPTED", "DECLINED", "CANCELLED"}:
            return SyncMutationResult(
                client_mutation_id=mutation.client_mutation_id,
                idempotency_key=mutation.idempotency_key,
                status="CONFLICT",
                server_entity_id=enquiry.id,
                error_message=f"RFQ has already concluded on server with status '{enquiry.status}'.",
                conflict_details={"server_status": enquiry.status}
            )

        payload_dict = mutation.payload
        rfq_payload = RFQResponseRequest(
            action=payload_dict.get("action", "ACCEPT"),
            counter_unit_price=Decimal(str(payload_dict["counter_unit_price"])) if payload_dict.get("counter_unit_price") is not None else None,
            counter_lead_time_days=payload_dict.get("counter_lead_time_days"),
            artisan_response_message=payload_dict.get("artisan_response_message")
        )

        updated_enquiry = await RFQService.artisan_respond(
            db=db,
            enquiry=enquiry,
            artisan_id=artisan.id,
            payload=rfq_payload
        )

        return SyncMutationResult(
            client_mutation_id=mutation.client_mutation_id,
            idempotency_key=mutation.idempotency_key,
            status="COMMITTED",
            server_entity_id=updated_enquiry.id,
            response_payload={"id": updated_enquiry.id, "status": updated_enquiry.status}
        )
