"""
SIH 26090: Embedding Provider Layer
Provides abstract interfaces and implementations for 768-dimensional vector generation.
"""

from ai.providers.embeddings.base import BaseEmbeddingProvider, EmbeddingResult
from ai.providers.embeddings.gemini import GeminiEmbeddingProvider
from ai.providers.embeddings.mock import MockEmbeddingProvider
from ai.providers.embeddings.factory import get_embedding_provider

__all__ = [
    "BaseEmbeddingProvider",
    "EmbeddingResult",
    "GeminiEmbeddingProvider",
    "MockEmbeddingProvider",
    "get_embedding_provider"
]
