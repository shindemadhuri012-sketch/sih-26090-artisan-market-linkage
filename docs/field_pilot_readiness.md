# FIELD PILOT READINESS PROTOCOL & DEPLOYMENT FRAMEWORK
**SIH 26090 — Artisan Market Linkage & Smart Seller Matching**
**Document Version:** 1.0.0 — Final Project Handover
**Status:** READY_FOR_PILOT / PROPOSED PROTOCOL (Zero Field Pilot Executed to Date)

---

## 1. Executive Summary & Mandatory Disclosure

> [!IMPORTANT]
> **MANDATORY GOVERNANCE DISCLOSURE**
> All pilot metrics, target cohorts, cluster sizes, and success rates described in this document represent a **PROPOSED PILOT DEPLOYMENT PLAN ONLY**.
> - **Zero field pilot activity has been executed to date.**
> - **Zero artisans, buyers, or clusters have been onboarded in live field operations.**
> - Target numbers (50 artisans, 10 institutional buyers, 3 clusters, 30 days) and KPI thresholds ($\ge 85\%$ onboarding, $\ge 70\%$ AI confirmation, $100\%$ sync reconciliation) are **TARGET SUCCESS CRITERIA**, not achieved results.
> - The software platform has been technically verified in laboratory/host environments (128/128 tests passing, PWA compilation verified, offline IndexedDB verified).

---

## 2. Target Pilot Clusters & Regional Demographics (PROPOSED PLAN)

The initial 30-day field pilot is designed for deployment across three culturally distinct, high-heritage geographic clusters in India:

| Cluster | State | Target Craft Focus | GI Registration Reference | Proposed Artisan Cohort | Field Infrastructure Profile |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Jaipur Craft Belt** | Rajasthan | Blue Pottery & Hand Block Printing | GI Application #2 | 20 Master Artisans | Mixed 3G/4G, urban periphery, Hindi/Marwari |
| **Varanasi Heritage Zone** | Uttar Pradesh | Zari Brocades & Wooden Lacquer Toys | GI Application #24 | 15 Weavers / Artisans | Flaky 2G/3G lanes, Bhojpuri/Hindi, indoor workshops |
| **Bastar Tribal Belt** | Chhattisgarh | Bastar Iron Craft & Dhokra Bell Metal | GI Application #83 | 15 Tribal Metalsmiths | Intermittent/Offline, Halbi/Gondi/Hindi, rural hamlet |

**Total Proposed Cohort:** 50 Rural Artisans / 10 Institutional Buyers (B2B Fair Trade / Retail Chains).
**Pilot Duration:** 30 Consecutive Calendar Days.

---

## 3. Field Operating Protocol & Device Compatibility Matrix

Artisans in rural craft clusters operate predominantly on entry-level, cost-constrained mobile devices under unpredictable cellular connectivity. The PWA client is engineered to satisfy the following minimum field baseline:

### Device Compatibility Matrix
- **Minimum OS:** Android 8.0 (Oreo) or iOS 12.2 (Safari WebKit).
- **Recommended OS:** Android 10+ with Chrome 100+ or Samsung Internet.
- **Hardware Profile:** 2 GB RAM, 32 GB Internal Storage (minimum 500 MB free for IndexedDB cache), Quad-core 1.5 GHz.
- **Camera:** 5 MP rear sensor with LED flash for craft macro photography.
- **Network Resilience:** Zero-bandwidth capability via Service Worker Cache API and local Dexie.js (IndexedDB). Tested on simulated 2G (50 kbps, 2000ms latency) and complete airplane-mode disconnections.

### Field Facilitator Protocol
1. **Cluster Anchor Facilitator:** Each cluster is assigned one bilingual local facilitator equipped with an Android tablet (4G dual-SIM hotspot).
2. **Initial Pairing Session:** Facilitator visits artisan workshop; guides PWA installation ("Add to Home Screen" prompt via standalone manifest).
3. **Seed Cache Pre-load:** PWA precaches core application assets (375 kB gzip) and cluster-specific craft taxonomy during initial tethering.

---

## 4. Informed Consent, Vernacular Rights & Data Privacy Framework

Artisan data ownership, copyright protection, and cultural sovereignty are protected through a tripartite consent architecture:

### 4.1 Physical Vernacular Consent Form
Prior to platform onboarding, the artisan signs or thumb-impresses a physical document printed in the local regional language (Hindi, Marwari, Bhojpuri, or Halbi):
1. **Craft Passport Ownership:** All intellectual property, motif traditions, lineage narratives, and workshop photos remain the exclusive property of the artisan.
2. **AI Processing Authorization:** Explicit opt-in permission to process uploaded craft photos through Gemini Vision AI for feature extraction and descriptive cataloguing.
3. **No Automatic Authority Rights:** Artisans are explicitly informed that AI generation is purely assistive (`STAGED`) and does not grant government authority recognition (`AUTHORITY_VERIFIED`).
4. **Data Revocation Right:** The artisan holds the unconditional right to request complete purging of product listings and lineage media upon written or verbal notice.

### 4.2 Voice-Note Audio Consent
For non-literate master artisans, the PWA enables recording a 15-second vernacular voice consent note (`media_type="AUDIO_VOICE_NOTE"`). The audio file is hashed (SHA-256) and anchored to the artisan's profile ledger.

### 4.3 PWA Storage Privacy & KYC Boundary
- **Zero Identity Document Caching:** Aadhaar, Bank Account Passbooks, and government identity cards are **NEVER** stored in browser IndexedDB or Service Worker storage. KYC verification is conducted either online via secure TLS ephemeral stream or verified physically by the anchor facilitator.
- **Session Purge:** Calling `clearOfflineStorage()` completely clears local product drafts, unsent mutation queues, and cached RFQ snippets upon user logout.

---

## 5. Offline Onboarding & Training Checklist

### Phase A: Pre-Deployment Setup (Days -7 to Day 0)
- [ ] Deploy production release containers to hosting infrastructure.
- [ ] Seed master Craft Taxonomy, Material Price Benchmarks, and GI Authority references.
- [ ] Issue digital identity tokens and role credentials to cluster facilitators (`Role.FACILITATOR`).
- [ ] Print vernacular consent documentation and quick-reference visual flashcards.

### Phase B: Cluster Initiation & Onboarding (Days 1 to 5)
- [ ] Conduct group workshop with cluster master artisans explaining Fair Price transparency.
- [ ] Execute physical consent collection and voice-note recording.
- [ ] Install PWA on artisan devices; demonstrate offline product draft creation.
- [ ] Capture initial baseline craft items using offline image compression.

### Phase C: Active Matching & RFQ Linkage (Days 6 to 25)
- [ ] Connect 10 institutional buyers submitting structured RFQ requirements.
- [ ] Execute semantic matching engine (`POST /api/v1/matching/match-rfq`); deliver candidate artisan scorecards.
- [ ] Monitor negotiation cycles, price quotes, and artisan fair-wage guarantees.
- [ ] Weekly facilitator sync audits: reconcile offline mutation queues against PostgreSQL backend.

### Phase D: Pilot Review & Verification Audit (Days 26 to 30)
- [ ] Compute empirical pilot metrics against target success criteria.
- [ ] Conduct structured artisan usability interviews and buyer satisfaction surveys.
- [ ] Export tamper-evident provenance audit trail for all pilot transactions.
- [ ] Convene Pilot Review Board to evaluate Phase 10 pilot outcome.

---

## 6. Target Success Criteria vs Current Technical Status

The table below strictly separates the **PROPOSED PILOT SUCCESS CRITERIA** from the **CURRENT MEASURED SYSTEM STATUS**:

| Dimension | Target Success Criterion (PROPOSED) | Current Status | Current Verification Evidence |
| :--- | :--- | :--- | :--- |
| **Artisan Onboarding** | $\ge 85\%$ completion rate within 48 hours | `READY_FOR_PILOT` (Target) | PWA onboarding wizard verified; zero field users onboarded. |
| **AI Cataloguing Confirmation** | $\ge 70\%$ acceptance rate of AI suggestions without manual re-typing | `READY_FOR_PILOT` (Target) | Staged workflow implemented (`POST /api/v1/ai-studio/confirm`); host test verified. |
| **Offline Sync Reconciliation** | $100\%$ conflict-free sync for valid mutations; zero silent overwrites | `READY_FOR_PILOT` (Target) | Version vector & idempotency tested in `test_offline_sync.py` (3/3 passed). |
| **Data Loss Rate** | $0.00\%$ loss of queued offline drafts | `READY_FOR_PILOT` (Target) | Dexie.js persistence tested across simulated browser reboots. |
| **IDOR / Tenant Isolation** | Zero cross-tenant data leaks or unauthorized price disclosures | `VERIFIED` (Host) | Rigorously tested in `test_pricing_auth_idor.py` (4/4 passed). |
| **Fair Wage Guarantee** | $100\%$ of approved quotes meet or exceed craft minimum wage floor | `VERIFIED` (Engine) | Enforced by deterministic engine in `test_fair_price_engine.py` (5/5 passed). |
| **Buyer Semantic Matching** | $\ge 80\%$ relevance ranking precision at K=5 | `READY_FOR_PILOT` (Target) | Engine verified on synthetic requirements in `test_matching_engine.py` (4/4 passed). |

---

## 7. Failure Modes & Human Escalation Runbook

| Failure Mode | Detection Indicator | Immediate Mitigation | Human Escalation Action |
| :--- | :--- | :--- | :--- |
| **Total Cellular Outage** | PWA network banner displays `OFFLINE`; sync attempts fail with `NetworkError`. | PWA automatically routes mutations to IndexedDB `mutation_queue` with exponential backoff. | Facilitator coordinates hotspot sharing at central cluster panchayat/workshop center. |
| **Image Capture Blur / Low Light** | AI Studio feature extraction returns `CONFIDENCE_LOW` or unparsed attributes. | Frontend client prompts artisan with visual guidelines to retake photo under natural daylight. | Facilitator captures photograph using cluster master device and transfers via local Bluetooth. |
| **Price Floor Dispute** | Buyer quotes below calculated Fair Price Engine cost floor ($C_{floor}$). | Backend API returns HTTP 422 `PRICE_BELOW_FAIR_FLOOR`; rejects quote submission. | Platform Fair Trade Moderator reviews artisan cost breakdown with institutional buyer. |
| **Authority Claim Rejection** | Artisan claims GI origin without authoritative documentation. | System flags claim as `ADMIN_REVIEWED` or `SELF_DECLARED`; denies `AUTHORITY_VERIFIED`. | Facilitator assists artisan in gathering official GI User Certificate from regional directorate. |
| **Sync Version Conflict** | Backend detects concurrent edit on same product with divergent revision ID. | Backend creates conflict log; applies deterministic latest-timestamp branch while preserving backup. | Artisan is presented with side-by-side reconciliation screen on next reconnect. |

---

## 8. Conclusion & Sign-Off Readiness

The technical architecture, client-side resilience, offline persistence layer, and governance protocols are fully prepared for field pilot deployment. Field execution may commence upon authorization of regional cluster deployments.
