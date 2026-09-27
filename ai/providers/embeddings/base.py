"""
SIH 26090: Base Embedding Provider Interface
Defines the abstract contract for 768-dimensional normalized dense vector embedding providers.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import math
from pydantic import BaseModel, Field


class EmbeddingResult(BaseModel):
    """Structured vector embedding outcome with strict model provenance."""
    embedding: List[float] = Field(..., description="768-dimensional dense vector")
    dimension: int = Field(default=768, description="Vector dimension")
    model_name: str = Field(..., description="Generating model name (e.g. gemini-embedding-2)")
    model_version: Optional[str] = Field(default=None, description="Model release version if available")
    provider: str = Field(..., description="Provider identifier (e.g. gemini, mock)")
    is_mock: bool = Field(default=False, description="Flag indicating mock/testing vector")


class BaseEmbeddingProvider(ABC):
    """Abstract interface for all embedding providers."""

    @abstractmethod
    async def embed_text(self, text: str) -> EmbeddingResult:
        """Generates a 768-dimensional normalized embedding for a text string."""
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """Generates 768-dimensional normalized embeddings for a batch of text strings."""
        pass

    @staticmethod
    def calculate_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """
        Computes cosine similarity between two vectors.
        Assumes vectors are normalized, but safely handles unnormalized vectors.
        Returns similarity bounded in [0.0000, 1.0000].
        """
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        raw_sim = dot_product / (norm_a * norm_b)
        # Clamp to [0.0, 1.0] for similarity metric
        return max(0.0, min(1.0, float(raw_sim)))
