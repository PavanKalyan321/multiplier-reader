"""
Feature Adapter - Expands 21 features to 50 features

Allows trained models that expect 50 features to work with the 21-feature system
by deriving additional features from the base features.
"""

import numpy as np


class FeatureAdapter:
    """
    Adapts 21-feature vectors to 50-feature vectors for trained models.

    The adapter derives 29 additional features from the base 21:
    - Statistical expansions (7)
    - Trend derivatives (5)
    - Recent pattern derivatives (6)
    - Streak derivatives (4)
    - Time derivatives (4)
    - Advanced derivatives (3)
    """

    def __init__(self):
        self.input_size = 21
        self.output_size = 50

    def expand_features(self, features_21: np.ndarray) -> np.ndarray:
        """
        Expand 21 features to 50 features.

        Args:
            features_21: numpy array of 21 base features

        Returns:
            numpy array of 50 features (21 original + 29 derived)
        """
        if len(features_21) != 21:
            raise ValueError(f"Expected 21 features, got {len(features_21)}")

        # Start with original 21 features (positions 0-20)
        expanded = list(features_21)

        # Group 1: Statistical expansions (7 features, positions 21-27)
        expanded.extend([
            features_21[0] * features_21[1],    # mean * std
            features_21[2] / (features_21[3] + 1e-6),    # min / max
            features_21[4] / (features_21[0] + 1e-6),    # median / mean
            features_21[0] - features_21[4],    # mean - median
            features_21[3] - features_21[2],    # max - min (range)
            features_21[1] / (features_21[0] + 1e-6),    # coefficient of variation
            (features_21[3] - features_21[2]) / (features_21[0] + 1e-6),  # relative range
        ])

        # Group 2: Trend derivatives (5 features, positions 28-32)
        expanded.extend([
            features_21[7] ** 2,                # trend_difference squared
            features_21[7] * features_21[8],    # trend interaction
            abs(features_21[7]),                # absolute trend
            features_21[8] - 1.0,               # trend deviation from 1
            features_21[7] / (features_21[1] + 1e-6),  # normalized trend
        ])

        # Group 3: Recent pattern derivatives (6 features, positions 33-38)
        expanded.extend([
            features_21[9] - features_21[10],   # diff(last_1, last_2)
            features_21[10] - features_21[11],  # diff(last_2, last_3)
            (features_21[9] + features_21[10] + features_21[11]) / 3,  # mean of last 3
            max(features_21[9], features_21[10], features_21[11]),     # max of last 3
            min(features_21[9], features_21[10], features_21[11]),     # min of last 3
            features_21[9] / (features_21[0] + 1e-6),  # last_1 / mean
        ])

        # Group 4: Streak derivatives (4 features, positions 39-42)
        expanded.extend([
            features_21[12] - features_21[13],  # high - low streak
            features_21[12] + features_21[13],  # total streak activity
            features_21[12] / 5.0,              # high streak ratio
            features_21[13] / 5.0,              # low streak ratio
        ])

        # Group 5: Time derivatives (4 features, positions 43-46)
        expanded.extend([
            features_21[14] / (features_21[15] + 1e-6),  # mean / std time
            features_21[16] / (features_21[14] + 1e-6),  # last / mean time
            features_21[17] / (features_21[14] + 1e-6),  # max / mean time
            features_21[15] / (features_21[14] + 1e-6),  # time CV
        ])

        # Group 6: Advanced derivatives (3 features, positions 47-49)
        expanded.extend([
            features_21[18] * features_21[20],  # volatility * range_ratio
            features_21[19] ** 2,               # momentum squared
            abs(features_21[19]),               # absolute momentum
        ])

        return np.array(expanded)

    def validate_expansion(self, features_21: np.ndarray, features_50: np.ndarray) -> bool:
        """
        Validate that expansion was successful.

        Args:
            features_21: Original 21 features
            features_50: Expanded 50 features

        Returns:
            True if validation passes
        """
        if len(features_50) != 50:
            return False

        # Check that first 21 features match
        if not np.allclose(features_21, features_50[:21]):
            return False

        # Check for NaN or inf
        if np.any(np.isnan(features_50)) or np.any(np.isinf(features_50)):
            return False

        return True
