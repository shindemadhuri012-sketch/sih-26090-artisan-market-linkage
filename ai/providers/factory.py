"""
SIH 26090: AI Vision Provider Factory
Instantiates and configures the appropriate vision provider based on environment settings.
"""

from typing import Optional
from backend.app.core.config import settings
from ai.providers.base import ProductVisionProvider
from ai.providers.null import NullVisionProvider
from ai.providers.mock import MockVisionProvider
from ai.providers.gemini import GeminiVisionProvider


def get_vision_provider(provider_override: Optional[str] = None) -> ProductVisionProvider:
    """
    Factory creating a vision provider based on active settings or overrides.
    Defaults to NullVisionProvider if required API credentials are not found.
    """
    provider_name = (provider_override or settings.AI_VISION_PROVIDER).lower().strip()

    if provider_name == "mock":
        return MockVisionProvider()

    if provider_name == "gemini":
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip():
            return GeminiVisionProvider(
                api_key=settings.GEMINI_API_KEY,
                model_name=settings.AI_VISION_MODEL,
                timeout_seconds=settings.AI_VISION_TIMEOUT_SECONDS
            )
        return NullVisionProvider(
            reason="Gemini API key is not configured in GEMINI_API_KEY environment variable."
        )

    return NullVisionProvider(reason=f"Unknown or unconfigured vision provider '{provider_name}'.")
