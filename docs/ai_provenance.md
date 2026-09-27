# AI Provenance, Honesty Charter & Information States

SIH 26090: Artisan Market Linkage & Smart Seller Matching

## 1. The SIH 26090 AI Honesty Charter
Artisanal marketplaces frequently suffer from AI hallucination and deceptive marketing, where automated tools falsely label ordinary items as "Government Certified GI" or "National Award Winner".

SIH 26090 enforces a non-negotiable **AI Honesty Charter**:
1. **No Silent Fact Promotion**: An AI suggestion remains `AI_SUGGESTED` until reviewed and confirmed by an artisan.
2. **Zero Synthetic Confidence**: Synthetic confidence percentages (e.g. 95%, 98%) are strictly prohibited.
3. **No Automated Legal Claims**: The AI vision engine is explicitly instructed via prompt guardrails never to assert GI certification, government awards, or certified purity percentages.

---

## 2. Four Distinct Information States

Every product attribute adheres to one of four verifiable data states:

| Information State | Definition | Example |
|---|---|---|
| **`ARTISAN_PROVIDED`** | Entered directly by the artisan through manual input forms. | Artisan types "Handspun organic cotton". |
| **`SOURCE_BACKED`** | Grounded directly in an official external authority (e.g. CGPDTM GI Registry). | GI Tag "GI-007" linked from official data seed. |
| **`AI_SUGGESTED`** | Extracted by a multimodal vision model; assistive and unverified. | AI model detects "Possible pit loom brocade weave". |
| **`HUMAN_CONFIRMED`** | Explicitly reviewed, accepted, or edited by the authenticated artisan. | Artisan reviews AI weave suggestion and clicks "Accept". |

> [!WARNING]
> **Legal & Trust Boundary**:
> `HUMAN_CONFIRMED` does **NOT** signify:
> - Government certification
> - Official GI verification
> - Independent laboratory authentication
> 
> It strictly indicates that the artisan has reviewed the assistive AI suggestion and confirmed its accuracy for their catalogue listing.

---

## 3. Preserving Immutable Provenance on Edits
When an artisan edits an AI suggestion:
1. `suggested_value` remains permanently intact in `ai_product_suggestions` as an immutable record of what the model originally predicted.
2. `confirmed_value` stores the artisan's corrected or refined text.
3. `status` transitions to `HUMAN_CONFIRMED`.
4. `artisan_notes` records the rationale for the change.

This guarantees complete traceability and provides valuable training signal for future model alignment.
