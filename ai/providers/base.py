"""
SIH 26090: AI Vision Provider Base Interface & Structured Result Schema
Defines the abstract interface for multimodal vision providers and the
structured schema for vision-extracted craft suggestions with immutable provenance.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ProductVisionResult(BaseModel):
    """
    Structured outcome of an AI vision inference on product imagery.
    Contains field-level suggestions, honest confidence scores (or null),
    and provider/model/prompt provenance.
    """
    title: Optional[str] = None
    storytelling_description: Optional[str] = None
    craft_category: Optional[str] = None
    materials: List[str] = Field(default_factory=list)
    technique: Optional[str] = None
    primary_color: Optional[str] = None
    colors: List[str] = Field(default_factory=list)
    pattern_motifs: List[str] = Field(default_factory=list)
    style: Optional[str] = None
    estimated_dimensions: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    cultural_context_clues: Optional[str] = None

    # Field-level calibrated confidence metrics (or null if provider doesn't output calibrated confidence)
    confidence_scores: Dict[str, Optional[float]] = Field(default_factory=dict)

    # Provenance tracking metadata
    provider: str
    model_name: str
    model_version: Optional[str] = None
    prompt_version: str
    is_mock: bool = False
    raw_response: Optional[Dict[str, Any]] = None


class ProductVisionProvider(ABC):
    """Abstract interface for all product vision AI providers."""

    @abstractmethod
    async def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        prompt_version: str = "product_vision_v1",
        craft_context: Optional[Dict[str, Any]] = None
    ) -> ProductVisionResult:
        """
        Processes product image bytes and returns structured craft attribute suggestions.
        Must not fabricate confidence scores or certifications.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if provider credentials and network configuration are active."""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Returns provider name, model identifier, and configuration details."""
        pass


class AIProviderNotConfiguredException(Exception):
    """Raised when an AI provider is requested but required credentials are absent."""
    def __init__(self, message: str = "AI vision provider is not configured. Please set GEMINI_API_KEY in environment."):
        self.message = message
        super().__init__(self.message)


class AIProviderInferenceException(Exception):
    """Raised when an external AI provider call fails or returns an unprocessable response."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)
