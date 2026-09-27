# SIH 26090: AI Module Foundation & Contracts

This directory contains the independent AI inference pipelines, prompt templates, and evaluation datasets for **SIH 26090: Artisan Market Linkage & Smart Seller Matching**.

---

## 1. Directory Structure

```
ai/
├── common/        # Shared AI client interfaces, base abstract adapters & telemetry
├── embeddings/    # 768-dimensional text embedding generators for semantic retrieval
├── matching/      # Multi-stage explainable matching pipeline & factor scorecard evaluators
├── vision/        # Computer vision craft extraction (weave, color palette, technique)
├── voice/         # Indic voice transcription (ASR) & audio preprocessing
├── pricing/       # Fair-price algorithmic calculation & commodity index comparisons
├── forecasting/   # Real-data demand intelligence with sparse historical data detection
└── README.md      # Specification and governance charter (this file)
```

---

## 2. AI Honesty & Implementation Policy

> [!IMPORTANT]
> **Phase 1 Boundary Enforcement**:
> - No machine learning models are trained during Phase 1.
> - No fake or synthetic model predictions are generated.
> - Full multimodal and matching pipelines will be implemented in Phases 3 and 4 according to `docs/ai_strategy.md`.
