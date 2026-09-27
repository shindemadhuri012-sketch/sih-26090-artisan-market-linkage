"""
SIH 26090: Gemini Embedding Provider
Async REST adapter for Google Gemini gemini-embedding-2 endpoint with output_dimensionality=768.
Credentials and API keys remain backend-only.
"""

import math
from typing import List, Optional
import httpx

from backend.app.core.config import settings
from ai.providers.embeddings.base import BaseEmbeddingProvider, EmbeddingResult


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """
    Connects to Google Generative Language REST API for gemini-embedding-2 embeddings.
    Strictly requests output_dimensionality=768 to maintain vector compatibility.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_seconds: Optional[int] = None
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.AI_EMBEDDING_MODEL or "gemini-embedding-2"
        self.timeout_seconds = timeout_seconds or settings.AI_EMBEDDING_TIMEOUT_SECONDS
        self.dimension = 768

    async def embed_text(self, text: str) -> EmbeddingResult:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured on the server.")

        endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model_name}:embedContent?key={self.api_key}"
        )

        payload = {
            "model": f"models/{self.model_name}",
            "content": {
                "parts": [{"text": text}]
            },
            "outputDimensionality": self.dimension
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            try:
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as e:
                raise RuntimeError(f"Gemini embedding API error: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                raise RuntimeError(f"Gemini embedding request failed: {str(e)}")

        raw_vector = data.get("embedding", {}).get("values", [])
        if not raw_vector or len(raw_vector) != self.dimension:
            raise ValueError(
                f"Expected {self.dimension}-dim embedding from {self.model_name}, "
                f"got {len(raw_vector)} values."
            )

        # Ensure L2 normalization
        norm = math.sqrt(sum(x * x for x in raw_vector))
        if norm > 0.0:
            normalized_vector = [float(x / norm) for x in raw_vector]
        else:
            normalized_vector = [float(x) for x in raw_vector]

        return EmbeddingResult(
            embedding=normalized_vector,
            dimension=self.dimension,
            model_name=self.model_name,
            provider="gemini",
            is_mock=False
        )

    async def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        results = []
        for text in texts:
            res = await self.embed_text(text)
            results.append(res)
        return results
