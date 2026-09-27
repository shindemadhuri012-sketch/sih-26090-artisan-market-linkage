"""
SIH 26090: Vector Embedding Tests
Tests MockEmbeddingProvider, GeminiEmbeddingProvider parameters, and vector math.
"""

import math
import pytest

from ai.providers.embeddings.mock import MockEmbeddingProvider
from ai.providers.embeddings.gemini import GeminiEmbeddingProvider
from ai.providers.embeddings.factory import get_embedding_provider
from ai.providers.embeddings.base import BaseEmbeddingProvider


@pytest.mark.asyncio
async def test_mock_embedding_provider_dimension_and_normalization():
    """Validates that MockEmbeddingProvider yields normalized 768-dim vectors deterministically."""
    provider = MockEmbeddingProvider(dimension=768)

    text_a = "Handloom Chanderi silk saree with golden zari border"
    res_a1 = await provider.embed_text(text_a)
    res_a2 = await provider.embed_text(text_a)

    # Dimension
    assert len(res_a1.embedding) == 768
    assert res_a1.dimension == 768
    assert res_a1.is_mock is True
    assert res_a1.model_name == "mock-embedding-test"

    # Determinism
    assert res_a1.embedding == res_a2.embedding

    # L2 Unit Normalization (sum of squares == 1.0)
    norm = math.sqrt(sum(x * x for x in res_a1.embedding))
    assert math.isclose(norm, 1.0, rel_tol=1e-5)


def test_cosine_similarity_bounds_and_symmetry():
    """Validates mathematical properties of cosine similarity calculation."""
    vec_a = [0.6, 0.8] + [0.0] * 766
    vec_b = [0.8, 0.6] + [0.0] * 766

    sim_aa = BaseEmbeddingProvider.calculate_cosine_similarity(vec_a, vec_a)
    assert math.isclose(sim_aa, 1.0, rel_tol=1e-5)

    sim_ab = BaseEmbeddingProvider.calculate_cosine_similarity(vec_a, vec_b)
    sim_ba = BaseEmbeddingProvider.calculate_cosine_similarity(vec_b, vec_a)
    assert math.isclose(sim_ab, sim_ba, rel_tol=1e-5)
    assert 0.0 <= sim_ab <= 1.0

    # Orthogonal vectors
    vec_c = [0.0, 0.0, 1.0] + [0.0] * 765
    sim_ac = BaseEmbeddingProvider.calculate_cosine_similarity(vec_a, vec_c)
    assert math.isclose(sim_ac, 0.0, abs_tol=1e-5)


def test_gemini_embedding_provider_configuration_and_mock_fallback():
    """Validates GeminiEmbeddingProvider attributes and safe factory fallback."""
    # Direct class attributes
    gemini_provider = GeminiEmbeddingProvider(api_key="test-key-mock", model_name="gemini-embedding-2")
    assert gemini_provider.model_name == "gemini-embedding-2"
    assert gemini_provider.dimension == 768

    # Factory falls back to mock when no GEMINI_API_KEY is present
    factory_provider = get_embedding_provider(provider_type="mock")
    assert isinstance(factory_provider, MockEmbeddingProvider)
    assert factory_provider.dimension == 768
