"""
SIH 26090: Health Check Schemas
Pydantic v2 schemas for health and system diagnostic responses.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Overall service status")
    environment: str = Field(..., description="Active runtime environment")
    version: str = Field(default="1.0.0", description="API version")
    timestamp: str = Field(..., description="Current ISO 8601 UTC timestamp")
    database: Dict[str, Any] = Field(default_factory=dict, description="Database status details")
    components: Dict[str, str] = Field(default_factory=dict, description="Component readiness map")
