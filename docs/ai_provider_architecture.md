# AI Vision Provider Abstraction Architecture

SIH 26090: Artisan Market Linkage & Smart Seller Matching

## 1. Provider Abstraction Rationale
To prevent proprietary vendor lock-in and ensure testability across disconnected development environments, SIH 26090 defines an abstract provider interface (`ProductVisionProvider`).

```
              ┌───────────────────────────┐
              │   ProductVisionProvider   │ (Abstract Interface)
              └─────────────┬─────────────┘
                            │
       ┌────────────────────┼────────────────────┐
       ▼                    ▼                    ▼
┌──────────────┐    ┌───────────────┐    ┌──────────────┐
│ GeminiVision │    │  MockVision   │    │  NullVision  │
│   Provider   │    │   Provider    │    │   Provider   │
└──────────────┘    └───────────────┘    └──────────────┘
 (Google REST)       (Test Suite & Dev)   (Safe Fallback)
```

---

## 2. Interface Definition (`ai/providers/base.py`)

All providers implement three core methods:
1. `analyze_image(image_bytes, mime_type, prompt_version, craft_context) -> ProductVisionResult`
2. `is_available() -> bool`
3. `get_model_info() -> Dict[str, Any]`

---

## 3. Provider Implementations

### 3.1 `GeminiVisionProvider` (`ai/providers/gemini.py`)
- **Transport**: Async `httpx.AsyncClient` communicating directly with Google Generative Language REST API (`/v1beta/models/{model_name}:generateContent`).
- **Configuration**:
  - Model: `gemini-1.5-flash` (or configurable via `AI_VISION_MODEL`)
  - Temperature: `0.2` (low temperature for deterministic attribute extraction)
  - Output MIME: `application/json`
- **Error Handling**: Explicit HTTP error boundaries for 400 (Bad Request), 401/403 (Invalid Key), 429 (Rate Limit), 503 (Unavailable), and timeouts.
- **AI Honesty Protocol**: Since Gemini generateContent does not return calibrated field-level classification probabilities, all confidence scores are explicitly returned as `None` (`null` in JSON).

### 3.2 `MockVisionProvider` (`ai/providers/mock.py`)
- **Purpose**: Fast, offline, deterministic unit testing and CI/CD pipeline verification.
- **Transparency**: Output explicitly contains `is_mock = True` and `model_name = "mock-vision-test"`. Mock outputs are never misrepresented as live AI inferences.

### 3.3 `NullVisionProvider` (`ai/providers/null.py`)
- **Purpose**: Fallback when `GEMINI_API_KEY` is not present in the environment.
- **Safety**: Does not crash the application and refuses to fabricate fake data. Raises `AIProviderNotConfiguredException` explaining that the vision API key must be supplied.

---

## 4. Backend-Only Credential Security
- `GEMINI_API_KEY` is loaded exclusively into memory by `pydantic-settings` on the backend.
- Neither the API key nor object storage secret keys are ever serialized into API responses, logged in audit trails, or transmitted to the frontend.
