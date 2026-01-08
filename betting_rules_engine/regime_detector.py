"""Detect market regime (TIGHT/NORMAL/LOOSE/VOLATILE)"""

import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional


class RegimeFeatures:
    """Statistical features for regime classification"""

    def __init__(self):
        self.median: float = 0.0
        self.mean: float = 0.0
        self.variance: float = 0.0
        self.std_dev: float = 0.0
        self.pct_below_1_5x: float = 0.0
        self.high_tail_freq: float = 0.0  # % of rounds >= 10x
        self.min_mult: float = 0.0
        self.max_mult: float = 0.0


class RegimeClassification:
    """Result of regime detection"""

    def __init__(self, regime: str, confidence: float, features: RegimeFeatures, rounds_analyzed: int):
        self.regime = regime
        self.confidence = confidence
        self.features = features
        self.evaluated_at = datetime.now()
        self.rounds_analyzed = rounds_analyzed

    def __repr__(self):
        return f"Regime({self.regime}, conf={self.confidence:.0%}, rounds={self.rounds_analyzed})"


class RegimeDetector:
    """Detect current market regime from historical data"""

    def __init__(self, thresholds: Dict[str, Any], cache_ttl: int = 180):
        self.thresholds = thresholds
        self.cache: Optional[RegimeClassification] = None
        self.cache_ttl = cache_ttl  # Cache for N seconds

    def detect_regime(self, multipliers: List[float]) -> RegimeClassification:
        """Classify regime from multiplier list"""

        # Check cache validity
        if self.cache and self._is_cache_valid():
            return self.cache

        if not multipliers or len(multipliers) < 5:
            return RegimeClassification("NORMAL", 0.5, self._empty_features(), 0)

        # Calculate features
        features = self._calculate_features(multipliers)

        # Classify based on thresholds
        regime = self._classify(features)

        # Create result and cache
        result = RegimeClassification(
            regime=regime,
            confidence=0.85,
            features=features,
            rounds_analyzed=len(multipliers)
        )

        self.cache = result
        return result

    def _calculate_features(self, multipliers: List[float]) -> RegimeFeatures:
        """Calculate statistical features from multipliers"""
        features = RegimeFeatures()

        arr = np.array(multipliers, dtype=float)

        features.median = float(np.median(arr))
        features.mean = float(np.mean(arr))
        features.variance = float(np.var(arr))
        features.std_dev = float(np.std(arr))
        features.min_mult = float(np.min(arr))
        features.max_mult = float(np.max(arr))

        # Percentage below 1.5x (crashes)
        features.pct_below_1_5x = float((np.sum(arr < 1.5) / len(arr)) * 100)

        # High tail frequency (>= 10x)
        features.high_tail_freq = float((np.sum(arr >= 10.0) / len(arr)) * 100)

        return features

    def _classify(self, features: RegimeFeatures) -> str:
        """Classify regime based on feature thresholds"""

        # TIGHT: Low median, high crash rate
        tight = self.thresholds.get('TIGHT', {})
        if (features.median <= tight.get('median_max', 2.0) and
            features.pct_below_1_5x >= tight.get('pct_below_1_5x_min', 40)):
            return "TIGHT"

        # VOLATILE: High variance, frequent tail events
        volatile = self.thresholds.get('VOLATILE', {})
        if (features.median >= volatile.get('median_min', 3.0) or
            features.high_tail_freq >= volatile.get('high_tail_freq_min', 15)):
            return "VOLATILE"

        # LOOSE: High median, low crashes
        loose = self.thresholds.get('LOOSE', {})
        if features.median >= loose.get('median_min', 2.5):
            return "LOOSE"

        # Default to NORMAL
        return "NORMAL"

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if not self.cache:
            return False
        elapsed = (datetime.now() - self.cache.evaluated_at).total_seconds()
        return elapsed < self.cache_ttl

    def _empty_features(self) -> RegimeFeatures:
        """Return empty features"""
        return RegimeFeatures()

    def clear_cache(self):
        """Clear cached regime classification"""
        self.cache = None
