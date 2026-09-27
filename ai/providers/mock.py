"""
SIH 26090: Mock Vision Provider (Development & Automated Testing)
Provides deterministic, strictly labeled test output for unit and integration testing.
Explicitly identifies all output with is_mock=True and model_name='mock-vision-test'.
Never presents mock output as genuine production AI inference.
"""

from typing import Optional, Dict, Any, List
from ai.providers.base import (
    ProductVisionProvider,
    ProductVisionResult,
    AIProviderInferenceException
)


class MockVisionProvider(ProductVisionProvider):
    """
    Deterministic provider for automated testing and offline development.
    Returns structured craft suggestions clearly flagged as test mocks.
    """

    def __init__(
        self,
        simulate_failure: bool = False,
        simulate_malformed: bool = False,
        mock_confidence: Optional[float] = None
    ):
        self.simulate_failure = simulate_failure
        self.simulate_malformed = simulate_malformed
        self.mock_confidence = mock_confidence
        self.provider_name = "mock"
        self.model_name = "mock-vision-test"
        self.model_version = "v1.0-test"

    async def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        prompt_version: str = "product_vision_v1",
        craft_context: Optional[Dict[str, Any]] = None
    ) -> ProductVisionResult:
        if self.simulate_failure:
            raise AIProviderInferenceException("Simulated mock provider network failure", status_code=503)

        if self.simulate_malformed:
            raise AIProviderInferenceException("Simulated provider malformed JSON response", status_code=502)

        # Context-aware mock attributes based on craft context if provided
        craft_name = (craft_context or {}).get("craft_name", "Handloom Textile")
        materials = ["Pure Mulberry Silk", "Zari Thread"] if "Silk" in craft_name or "Chanderi" in craft_name else ["Cotton Yarn", "Natural Indigo Dye"]

        return ProductVisionResult(
            title=f"Handcrafted {craft_name} with Traditional Motifs",
            storytelling_description=(
                f"Handcrafted piece reflecting the {craft_name} tradition. "
                "Woven using authentic materials with extra-weft heritage motifs passed down across generations."
            ),
            craft_category="Textiles & Handloom",
            materials=materials,
            technique="Pit Loom Extra-Weft Brocade",
            primary_color="Maroon",
            colors=["Maroon", "Gold", "Ivory"],
            pattern_motifs=["Peacock Motif", "Zari Borders", "Floral Butti"],
            style="Traditional Heritage",
            estimated_dimensions="5.5m x 1.15m",
            tags=["handloom", "heritage", "craft", "traditional", "indian-artisans"],
            cultural_context_clues=f"Visual features align with central Indian {craft_name} aesthetic techniques.",
            confidence_scores={
                "materials": self.mock_confidence,
                "technique": self.mock_confidence,
                "primary_color": self.mock_confidence
            },
            provider=self.provider_name,
            model_name=self.model_name,
            model_version=self.model_version,
            prompt_version=prompt_version,
            is_mock=True,
            raw_response={"mock_status": "success", "note": "Deterministic test mock output"}
        )

    def is_available(self) -> bool:
        return True

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "is_mock": True,
            "status": "ACTIVE_TEST_MOCK"
        }
