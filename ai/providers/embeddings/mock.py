"""
SIH 26090: Mock Embedding Provider
Generates deterministic 768-dimensional unit vectors strictly for automated testing and offline CI.
Must NEVER be presented as real production semantic matching data.
"""

import hashlib
import math
import random
from typing import List

from ai.providers.embeddings.base import BaseEmbeddingProvider, EmbeddingResult


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic pseudo-random vector generator seeded by SHA-256 hash of input text.
    Produces unit-normalized 768-dimensional vectors for reproducible offline testing.
    """

    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.model_name = "mock-embedding-test"
        self.provider = "mock"

    async def embed_text(self, text: str) -> EmbeddingResult:
        # Create deterministic seed from SHA-256 of text
        digest = hashlib.sha256((text or "empty").encode("utf-8")).digest()
        seed = int.from_bytes(digest[:8], byteorder="big")

        rng = random.Random(seed)
        raw_vector = [rng.gauss(0.0, 1.0) for _ in range(self.dimension)]

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in raw_vector))
        if norm > 0.0:
            normalized = [float(x / norm) for x in raw_vector]
        else:
            normalized = [0.0] * self.dimension
            normalized[0] = 1.0

        return EmbeddingResult(
            embedding=normalized,
            dimension=self.dimension,
            model_name=self.model_name,
            provider=self.provider,
            is_mock=True
        )

    async def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        return [await self.embed_text(t) for t in texts]
