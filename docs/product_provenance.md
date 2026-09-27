# Product Provenance, AI Contracts & Privacy Sanitization

SIH 26090: Artisan Market Linkage & Smart Seller Matching

## 1. Strict Real-Data & Provenance Mandate
A core foundation of the SIH 26090 architecture is that real-world authenticity must never be fabricated. No fake GI certifications, fake sales, fake reviews, or fake artisans are ever created.

---

## 2. Product Provenance Levels

Every product listing tracks its verification tier via `provenance_status`:

| Provenance Level | Definition | Transition Trigger |
|---|---|---|
| `ARTISAN_DECLARED` | Craft parameters and origin declared directly by the registered artisan. | Default status upon product creation. |
| `COMMUNITY_ATTESTED` | Attested by a verified artisan cooperative, self-help group (SHG), or weaver society. | Cooperative head attestation workflow. |
| `GOVERNMENT_GI_CONFIRMED` | Craft belongs to an official Geographical Indication (GI) and listing has been verified by an administrator against official specifications. | Admin approval of GI-associated craft listing. |
| `SAMPLE_DEMO` | Explicitly marked fixture or test demonstration data. | `is_sample_or_demo: true` and `data_provenance_level: "SAMPLE_DEMO"`. |

---

## 3. Future AI Suggestion Data Contract

In Phase 4 and Phase 5, multimodal AI models (computer vision for defect detection, image cataloguing, voice-to-text storytelling, and fair-price estimation) will run.

In Phase 3, **NO AI inference is executed**. Instead, the platform initializes a strict **Data Contract** placeholder in `Product.ai_metadata`:

```json
{
  "title_suggestion": null,
  "description_suggestion": null,
  "suggested_tags": [],
  "suggested_materials": [],
  "confidence": null,
  "model_name": null,
  "timestamp": null,
  "human_confirmed": false
}
```

### Architectural Guarantees:
- `human_confirmed` flag ensures that future AI recommendations never override artisan-declared facts without human verification.
- Confidence scores must be bounded between `0.0` and `1.0`.
- AI models will populate this field asynchronously without schema alterations.

---

## 4. Public API Privacy & PII Sanitization

Artisan welfare and data protection require that private contact and identification information is never exposed on public-facing catalogue endpoints (`GET /api/v1/products` and `GET /api/v1/products/{id}`).

### Public Sanitization Policy:
| Field | Internal (`ProductResponse`) | Public (`ProductPublicResponse`) | Rationale |
|---|---|---|---|
| `title`, `sku`, `price_inr` | Exposed | Exposed | Public commercial data |
| `stock_quantity`, `lead_time_days` | Exposed | Exposed | Necessary for buyer procurement |
| `craft_name`, `gi_tag_number` | Exposed | Exposed | Provenance & authenticity verification |
| `artisan_public_name` | Exposed | Exposed | Public recognition |
| `artisan_district`, `artisan_state` | Exposed | Exposed | Cluster regional authenticity |
| `artisan_id` | Exposed | Withheld | IDOR defense |
| `phone_number` | Withheld from Public | Strictly Excluded | Prevents spam / predatory middlemen |
| `pehchan_id` | Withheld from Public | Strictly Excluded | Government identity privacy |
| `street_address` / `pincode` | Withheld from Public | Strictly Excluded | Personal safety |
| `bank_account_number` | Withheld from Public | Strictly Excluded | Financial privacy |
