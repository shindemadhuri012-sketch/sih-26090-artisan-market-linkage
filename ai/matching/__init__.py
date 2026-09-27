"""
SIH 26090: Smart Matching Package
Exports MatchingEngine and MatchScorecard for explainable buyer-artisan matching.
"""

from ai.matching.engine import (
    MatchingEngine,
    MatchScorecard,
    MATCHING_ENGINE_V1,
    WEIGHT_SEMANTIC,
    WEIGHT_CRAFT,
    WEIGHT_MATERIAL,
    WEIGHT_CAPACITY,
    WEIGHT_PRICE,
    WEIGHT_LEAD_TIME,
    BONUS_PROVENANCE_MAX
)

__all__ = [
    "MatchingEngine",
    "MatchScorecard",
    "MATCHING_ENGINE_V1",
    "WEIGHT_SEMANTIC",
    "WEIGHT_CRAFT",
    "WEIGHT_MATERIAL",
    "WEIGHT_CAPACITY",
    "WEIGHT_PRICE",
    "WEIGHT_LEAD_TIME",
    "BONUS_PROVENANCE_MAX"
]
