"""
SIH 26090: Google Gemini Vision Provider Implementation
Uses async HTTP client (httpx) to interact with Google Gemini Vision REST API.
Enforces the strict AI honesty charter: confidence scores remain null unless
calibrated probabilities are genuinely returned by the model.
"""

import base64
import json
import re
from typing import Optional, Dict, Any
import httpx

from ai.providers.base import (
    ProductVisionProvider,
    ProductVisionResult,
    AIProviderNotConfiguredException,
    AIProviderInferenceException
)
from ai.product_studio.prompts.vision_prompts import get_prompt_by_version


class GeminiVisionProvider(ProductVisionProvider):
    """
    Multimodal Vision-Language Model provider powered by Google Gemini (e.g. gemini-1.5-flash).
    Direct REST integration using async httpx without proprietary SDK lock-in.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-1.5-flash",
        timeout_seconds: int = 30
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.provider_name = "google"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "model_name": self.model_name,
            "is_available": self.is_available(),
            "timeout_seconds": self.timeout_seconds
        }

    async def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        prompt_version: str = "product_vision_v1",
        craft_context: Optional[Dict[str, Any]] = None
    ) -> ProductVisionResult:
        if not self.is_available():
            raise AIProviderNotConfiguredException(
                "Gemini API key is not configured. Please supply GEMINI_API_KEY in backend environment."
            )

        prompt_text = get_prompt_by_version(prompt_version)
        if craft_context:
            context_str = f"\nADDITIONAL ARTISAN CONTEXT: Artisan's primary craft is '{craft_context.get('craft_name', 'Unknown')}' from '{craft_context.get('origin_state', 'India')}'."
            prompt_text += context_str

        # Encode image to base64 inline data
        b64_image = base64.b64encode(image_bytes).decode("utf-8")

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt_text},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": b64_image
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "response_mime_type": "application/json"
            }
        }

        endpoint = f"{self.base_url}/models/{self.model_name}:generateContent"
        params = {"key": self.api_key}

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(endpoint, params=params, json=payload)

            if response.status_code == 400:
                raise AIProviderInferenceException(f"Gemini API bad request: {response.text}", status_code=400)
            elif response.status_code in (401, 403):
                raise AIProviderInferenceException("Gemini API authentication failed. Verify GEMINI_API_KEY.", status_code=401)
            elif response.status_code == 429:
                raise AIProviderInferenceException("Gemini API rate limit exceeded.", status_code=429)
            elif response.status_code >= 500:
                raise AIProviderInferenceException("Gemini API service temporarily unavailable.", status_code=503)

            response_json = response.json()
            candidates = response_json.get("candidates", [])
            if not candidates:
                raise AIProviderInferenceException("Gemini API returned no candidates or content was blocked.", status_code=502)

            content_parts = candidates[0].get("content", {}).get("parts", [])
            if not content_parts or "text" not in content_parts[0]:
                raise AIProviderInferenceException("Gemini response missing text part.", status_code=502)

            raw_text = content_parts[0]["text"].strip()
            # Clean possible markdown block wrappers if present
            clean_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text, flags=re.MULTILINE).strip()
            parsed = json.loads(clean_json)

            # Strict Honesty Policy: Gemini generateContent does not return calibrated field-level probabilities.
            # We explicitly store confidence as None (null in DB/JSON). We never manufacture fake numbers!
            confidence_scores = {
                "title": None,
                "materials": None,
                "technique": None,
                "primary_color": None,
                "style": None
            }

            return ProductVisionResult(
                title=parsed.get("title"),
                storytelling_description=parsed.get("storytelling_description"),
                craft_category=parsed.get("craft_category"),
                materials=parsed.get("materials", []) if isinstance(parsed.get("materials"), list) else [],
                technique=parsed.get("technique"),
                primary_color=parsed.get("primary_color"),
                colors=parsed.get("colors", []) if isinstance(parsed.get("colors"), list) else [],
                pattern_motifs=parsed.get("pattern_motifs", []) if isinstance(parsed.get("pattern_motifs"), list) else [],
                style=parsed.get("style"),
                estimated_dimensions=parsed.get("estimated_dimensions"),
                tags=parsed.get("tags", []) if isinstance(parsed.get("tags"), list) else [],
                cultural_context_clues=parsed.get("cultural_context_clues"),
                confidence_scores=confidence_scores,
                provider=self.provider_name,
                model_name=self.model_name,
                model_version=None,
                prompt_version=prompt_version,
                is_mock=False,
                raw_response=parsed
            )

        except httpx.TimeoutException:
            raise AIProviderInferenceException(f"Gemini API request timed out after {self.timeout_seconds}s.", status_code=504)
        except json.JSONDecodeError as jde:
            raise AIProviderInferenceException(f"Gemini API returned malformed non-JSON text: {str(jde)}", status_code=502)
        except AIProviderInferenceException:
            raise
        except Exception as e:
            raise AIProviderInferenceException(f"Unexpected error during vision inference: {str(e)}", status_code=500)
