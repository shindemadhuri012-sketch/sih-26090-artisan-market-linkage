"""
SIH 26090: Embedding Provider Factory
Selects and configures the active embedding provider based on environment settings.
"""

from typing import Optional

from backend.app.core.config import settings
from ai.providers.embeddings.base import BaseEmbeddingProvider
from ai.providers.embeddings.gemini import GeminiEmbeddingProvider
from ai.providers.embeddings.mock import MockEmbeddingProvider


def get_embedding_provider(provider_type: Optional[str] = None) -> BaseEmbeddingProvider:
    """
    Returns configured embedding provider instance.
    Falls back gracefully to MockEmbeddingProvider when external API keys are unavailable.
    """
    active_type = (provider_type or settings.AI_EMBEDDING_PROVIDER or "gemini").lower()

    if active_type == "mock" or not settings.GEMINI_API_KEY:
        return MockEmbeddingProvider(dimension=settings.EMBEDDING_DIMENSION)

    if active_type == "gemini":
        return GeminiEmbeddingProvider(
            api_key=settings.GEMINI_API_KEY,
            model_name=settings.AI_EMBEDDING_MODEL,
            timeout_seconds=settings.AI_EMBEDDING_TIMEOUT_SECONDS
        )

    # Default fallback
    return MockEmbeddingProvider(dimension=settings.EMBEDDING_DIMENSION)
