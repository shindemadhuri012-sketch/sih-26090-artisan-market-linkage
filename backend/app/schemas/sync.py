"""
SIH 26090: Offline Sync Schemas
Pydantic v2 schemas for client mutation items, batch sync requests, and conflict resolutions.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class SyncMutationItem(BaseModel):
    client_mutation_id: str = Field(..., description="Client-generated unique UUID for tracking")
    idempotency_key: str = Field(..., min_length=16, max_length=64, description="Cryptographic idempotency key")
    entity_type: str = Field(..., description="Target entity: PRODUCT, RFQ_RESPONSE")
    entity_id: str = Field(..., description="Target record ID or client temporary ID")
    operation_type: str = Field(..., description="CREATE, UPDATE, DELETE, RESPOND_RFQ")
    payload: Dict[str, Any] = Field(..., description="Complete operation payload body")
    client_created_at: str = Field(..., description="ISO 8601 timestamp of client mutation creation")

    @field_validator("entity_type")
    @classmethod
    def validate_entity(cls, v: str) -> str:
        v_upper = v.strip().upper()
        if v_upper not in {"PRODUCT", "PRODUCT_MEDIA", "RFQ_RESPONSE"}:
            raise ValueError(f"Unsupported offline entity type '{v}'. Allowed: PRODUCT, PRODUCT_MEDIA, RFQ_RESPONSE")
        return v_upper

    @field_validator("operation_type")
    @classmethod
    def validate_op(cls, v: str) -> str:
        v_upper = v.strip().upper()
        if v_upper not in {"CREATE", "UPDATE", "DELETE", "RESPOND_RFQ"}:
            raise ValueError(f"Unsupported offline operation type '{v}'. Allowed: CREATE, UPDATE, DELETE, RESPOND_RFQ")
        return v_upper


class SyncBatchRequest(BaseModel):
    mutations: List[SyncMutationItem] = Field(..., min_length=1, max_length=50)


class SyncMutationResult(BaseModel):
    client_mutation_id: str
    idempotency_key: str
    status: str  # COMMITTED, CONFLICT, REJECTED, ALREADY_PROCESSED
    server_entity_id: Optional[str] = None
    error_message: Optional[str] = None
    conflict_details: Optional[Dict[str, Any]] = None
    response_payload: Optional[Dict[str, Any]] = None


class SyncBatchResponse(BaseModel):
    total_submitted: int
    committed: int
    conflicts: int
    rejected: int
    results: List[SyncMutationResult]
