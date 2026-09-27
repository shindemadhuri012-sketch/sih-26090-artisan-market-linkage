"""
SIH 26090: Null Vision Provider
Safely handles environments where no external AI provider or API key is configured.
Never fabricates fake model predictions.
"""

from typing import Optional, Dict, Any
from ai.providers.base import (
    ProductVisionProvider,
    ProductVisionResult,
    AIProviderNotConfiguredException
)


class NullVisionProvider(ProductVisionProvider):
    """
    Fallback provider active when no external AI credentials or provider is configured.
    Explicitly refuses to generate fake outputs.
    """

    def __init__(self, reason: str = "AI vision provider is not configured. Please set GEMINI_API_KEY in environment."):
        self.reason = reason

    async def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        prompt_version: str = "product_vision_v1",
        craft_context: Optional[Dict[str, Any]] = None
    ) -> ProductVisionResult:
        raise AIProviderNotConfiguredException(self.reason)

    def is_available(self) -> bool:
        return False

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "none",
            "model_name": "unconfigured",
            "status": "UNCONFIGURED",
            "reason": self.reason
        }
