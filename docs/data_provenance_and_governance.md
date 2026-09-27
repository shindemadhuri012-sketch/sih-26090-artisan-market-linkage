# SIH 26090: DATA PROVENANCE, INTEGRITY & GOVERNANCE
## Specification of Information States, Cryptographic Chaining & Authority Gating

**Project**: SIH 26090 – Artisan Market Linkage & Smart Seller Matching  
**Phase**: Phase 9 — Production Deployment & Judge Pack  

---

## 1. The 9 Information & Governance States

To prevent data corruption, false authority claims, or silent LLM overwrites, the platform strictly segregates records across 9 mutually exclusive information states:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       9 DISTINCT INFORMATION STATES                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. ARTISAN_PROVIDED   : Raw data submitted by the artisan.                  │
│ 2. SOURCE_BACKED      : Grounded in external datasets (GI Registry, ODOP).  │
│ 3. AI_SUGGESTED       : Staged AI suggestion requiring human review.        │
│ 4. CALCULATED         : Deterministic mathematical derivation.              │
│ 5. HUMAN_CONFIRMED    : Explicitly accepted/edited by human artisan/buyer.  │
│ 6. ADMIN_APPROVED     : Approved by internal platform moderator.            │
│ 7. ADMIN_REJECTED     : Rejected by internal platform moderator.            │
│ 8. FLAGGED            : Marked with active review signal for audit.         │
│ 9. SUPERSEDED         : Historic record replaced by a newer version.        │
└─────────────────────────────────────────────────────────────────────────────┘
                                     ▲
                                     │ Strictly Separated
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    INDEPENDENT AUTHORITY VERIFICATION                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ AUTHORITY_VERIFIED    : Formally confirmed by official government registry  │
│                         or recognized certifying authority. Strictly        │
│                         requires authoritative reference & evidence URL.    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Guarding `AUTHORITY_VERIFIED` vs `ADMIN_APPROVED` / `ADMIN_REVIEWED`

A foundational flaw in many digital platforms is conflating internal platform approval with official government certification. The SIH 26090 platform permanently separates these concepts:

- **`ADMIN_APPROVED` / `ADMIN_REVIEWED`**: Represents internal compliance checks performed by platform moderators (checking image appropriateness, vulgarity, basic policy compliance). It confers **zero** government endorsement.
- **`AUTHORITY_VERIFIED`**: Can **never** be granted by platform moderators based solely on visual inspection, uploaded documents, or craft associations. It strictly requires:
  1. `authority_source` (e.g., `"O/o Development Commissioner (Handicrafts)", "Intellectual Property India"`).
  2. `authoritative_registry_reference` (e.g., Pehchan Card Number, GI Authorised User Registration Number).
  3. `evidence_url` (verifiable document or registry URL).
  4. `verified_at` (timestamp of authoritative validation).
  5. `verifier_id` (identity of the auditing official).

### Permanent Elimination of Legacy GI Auto-Promotion Bug
In legacy code, approving a product or verification associated with a GI craft automatically set its status to `GOVERNMENT_VERIFIED_GI` / `GOVERNMENT_GI_CONFIRMED`. This logic has been completely removed. Associating with a GI craft simply links taxonomy; only documented registration under the GI Act grants authority verification. Automated regression tests (`test_legacy_gi_verification_bug_fixed_and_cannot_regress` and `test_admin_reviewed_cannot_grant_authority_verified_regression`) prove this separation cannot regress.

---

## 3. Cryptographic Provenance Chain Architecture

### 3.1 Deterministic Canonical Serialization
To guarantee reproducible hashes across operating systems and database dialects, the platform utilizes strict canonical JSON serialization:
```python
def canonical_json_dumps(obj: Any) -> str:
    """Deterministic JSON: sorted keys, compact separators (',', ':'), UTC ISO-8601."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)
```

### 3.2 SHA-256 Hash Chaining Formula
$$\text{event\_hash} = \text{SHA-256}\left(\text{canonical\_payload} \parallel (\text{prev\_event\_hash} \text{ or } \text{""})\right)$$

- **Genesis Events**: The initial state change for an entity sets `prev_event_hash=None`, hashing the payload against an empty string with `sequence_number=1`.
- **Subsequent Events**: Event $N$ incorporates the exact digest of Event $N-1$, forming an unbreakable cryptographic chain.

### 3.3 Active Tamper Detection Algorithm
The `ProvenanceService.verify_provenance_chain` method validates historical continuity:
1. Recomputes `expected_hash` from the canonical serialized `payload` and `prev_event_hash`.
2. Validates that `event.event_hash == expected_hash`. If mismatched, raises `PAYLOAD_TAMPERED`.
3. Validates that `event.prev_event_hash == previous_event.event_hash`. If mismatched, raises `CHAIN_BROKEN`.
4. Validates that `event.sequence_number == previous_event.sequence_number + 1`. If mismatched, raises `SEQUENCE_GAP`.

---

## 4. Critical-Field Moderation Allowlist

To protect catalogue integrity without creating administrative bottlenecks, product updates are categorized by risk:

```python
CRITICAL_MODERATION_FIELDS = {
    "title",
    "price_inr",
    "materials",
    "craft_id",
    "category_id",
    "storytelling_description",
    "technique",
    "provenance_status",
}
```

- **Critical Updates**: Mutating title, price, craft, materials, or provenance automatically demotes `PUBLISHED` products to `PENDING_APPROVAL`.
- **Operational Updates**: Mutating `stock_quantity`, `lead_time_days`, `dimensions`, `weight_grams`, or search `tags` keeps the product `PUBLISHED`.

---

## 5. Neutral Governance Review Signals

Rather than using accusatory or defamatory labels (such as "FRAUD" or "SCAM"), the platform employs neutral, objective review triggers:

| Review Signal | Severity | Trigger Condition |
|:---|:---|:---|
| `PRICE_ANOMALY_REVIEW` | `MEDIUM` | Price falls below living-wage floor or deviates $>300\%$ from regional baseline. |
| `MISSING_PROVENANCE` | `MEDIUM` | Product or profile lacks craft association or material breakdown. |
| `UNSUPPORTED_CLAIM` | `HIGH` | Claim of GI tag or government award without authoritative registry references. |
| `EXPIRED_EVIDENCE` | `LOW` | Certificate validity date has lapsed. |
| `DUPLICATE_SOURCE` | `MEDIUM` | Identical source URL, Pehchan identifier, or image hash registered across multiple accounts. |
| `STALE_MARKET_DATA` | `LOW` | Benchmark pricing observations have not been updated for $>90$ days. |
| `SAMPLE_EXPOSURE` | `HIGH` | Synthetic demo/mock records exposed in live buyer views. |
