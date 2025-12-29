"""
Feature Extractor - Extracts 21 features from round history

Converts raw round history into feature vectors for ML prediction.
"""

import numpy as np
from typing import List, Dict


class FeatureExtractor:
    """
    Extracts 21 features from round history for ML predictions.

    Features include:
    - Statistical (5): mean, std, min, max, median
    - Duration (2): mean duration, std duration
    - Trend (2): trend difference, trend ratio
    - Recent Pattern (3): last 3 multipliers
    - Streaks (2): high streak count, low streak count
    - Time (4): mean/std/last/max time differences
    - Advanced (3): volatility, momentum, range ratio
    """

    def __init__(self):
        self.feature_count = 21
        self.feature_names = [
            # Statistical (5)
            'mean_multiplier', 'std_multiplier', 'min_multiplier', 'max_multiplier', 'median_multiplier',
            # Duration (2)
            'mean_duration', 'std_duration',
            # Trend (2)
            'trend_difference', 'trend_ratio',
            # Recent Pattern (3)
            'last_1_multiplier', 'last_2_multiplier', 'last_3_multiplier',
            # Streaks (2)
            'high_streak_count', 'low_streak_count',
            # Time (4)
            'mean_time_diff', 'std_time_diff', 'last_time_diff', 'max_time_diff',
            # Advanced (3)
            'volatility', 'momentum', 'range_ratio'
        ]

    def extract_features(self, lookback_data: List[Dict]) -> np.ndarray:
        """
        Extract 21 features from lookback data.

        Args:
            lookback_data: List of round data dicts with keys:
                          - 'crash_multiplier': float
                          - 'duration': float
                          - 'timestamp': float

        Returns:
            numpy array of 21 features
        """
        if len(lookback_data) == 0:
            return np.zeros(21)

        multipliers = [r['crash_multiplier'] for r in lookback_data]
        durations = [r['duration'] for r in lookback_data]

        features = []

        # Statistical features (5)
        features.extend([
            np.mean(multipliers),
            np.std(multipliers),
            np.min(multipliers),
            np.max(multipliers),
            np.median(multipliers),
        ])

        # Duration features (2)
        features.extend([
            np.mean(durations),
            np.std(durations),
        ])

        # Trend features (2)
        lookback = len(multipliers)
        if lookback >= 10:
            last_5 = multipliers[-5:]
            prev_5 = multipliers[-10:-5]
            features.extend([
                np.mean(last_5) - np.mean(prev_5),  # Trend difference
                np.mean(last_5) / np.mean(prev_5) if np.mean(prev_5) > 0 else 1.0,  # Trend ratio
            ])
        else:
            features.extend([0, 1])

        # Recent pattern (3)
        if lookback >= 3:
            features.extend([
                multipliers[-1],
                multipliers[-2],
                multipliers[-3],
            ])
        else:
            features.extend([0, 0, 0])

        # Streaks (2)
        high_threshold = np.mean(multipliers) + np.std(multipliers)
        low_threshold = np.mean(multipliers) - np.std(multipliers)
        recent = multipliers[-5:] if len(multipliers) >= 5 else multipliers
        high_streak = sum(1 for m in recent if m > high_threshold)
        low_streak = sum(1 for m in recent if m < low_threshold)
        features.extend([high_streak, low_streak])

        # Time features (4)
        if len(lookback_data) >= 2:
            timestamps = [r['timestamp'] for r in lookback_data]
            time_diffs = np.diff(timestamps)
            features.extend([
                np.mean(time_diffs),
                np.std(time_diffs),
                time_diffs[-1] if len(time_diffs) > 0 else 0,
                np.max(time_diffs) if len(time_diffs) > 0 else 0,
            ])
        else:
            features.extend([0, 0, 0, 0])

        # Advanced features (3)
        volatility = np.std(multipliers) / np.mean(multipliers) if np.mean(multipliers) > 0 else 0
        momentum = (multipliers[-1] - np.mean(multipliers)) / np.std(multipliers) if np.std(multipliers) > 0 else 0
        range_ratio = (np.max(multipliers) - np.min(multipliers)) / np.mean(multipliers) if np.mean(multipliers) > 0 else 0
        features.extend([volatility, momentum, range_ratio])

        return np.array(features)
