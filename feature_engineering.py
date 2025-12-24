"""
Feature Engineering Module for Multiplier Prediction
Extracts statistical features from historical round data
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime, timedelta


class FeatureEngineer:
    """Extract and engineer features from round history"""

    def __init__(self, min_history=10):
        """
        Initialize feature engineer

        Args:
            min_history: Minimum rounds needed to generate features
        """
        self.min_history = min_history

    def extract_features(self, rounds_data: List[Dict]) -> Tuple[np.ndarray, Dict]:
        """
        Extract features from historical rounds

        Args:
            rounds_data: List of round dictionaries with 'multiplier' and 'timestamp'

        Returns:
            Tuple of (feature_vector, feature_dict)
        """
        if len(rounds_data) < self.min_history:
            # Return zero features if not enough data
            features_dict = self._get_default_features()
            return np.zeros(len(features_dict)), features_dict

        # Convert to DataFrame for easier processing
        df = pd.DataFrame(rounds_data)
        df['multiplier'] = pd.to_numeric(df['multiplier'], errors='coerce')
        df = df.dropna(subset=['multiplier'])

        if len(df) < self.min_history:
            features_dict = self._get_default_features()
            return np.zeros(len(features_dict)), features_dict

        # Calculate features
        features_dict = {}

        # 1. Basic Statistics (Multiplier)
        features_dict['mean_multiplier'] = float(df['multiplier'].mean())
        features_dict['std_multiplier'] = float(df['multiplier'].std())
        features_dict['median_multiplier'] = float(df['multiplier'].median())
        features_dict['min_multiplier'] = float(df['multiplier'].min())
        features_dict['max_multiplier'] = float(df['multiplier'].max())

        # 2. Volatility Metrics
        features_dict['volatility'] = float(df['multiplier'].std() / df['multiplier'].mean()) if df['multiplier'].mean() > 0 else 0
        returns = df['multiplier'].pct_change().dropna()
        features_dict['return_volatility'] = float(returns.std()) if len(returns) > 0 else 0

        # 3. Trend Features
        recent_5 = df['multiplier'].tail(5).values
        features_dict['trend_5'] = float(recent_5[-1] - recent_5[0]) if len(recent_5) >= 2 else 0
        features_dict['momentum_5'] = float(np.mean(np.diff(recent_5))) if len(recent_5) >= 2 else 0

        # 4. Crash Frequency (low multiplier rounds)
        crash_threshold = 1.5
        crash_rounds = (df['multiplier'] < crash_threshold).sum()
        features_dict['crash_frequency'] = float(crash_rounds / len(df))

        # 5. High Multiplier Frequency
        high_threshold = 5.0
        high_rounds = (df['multiplier'] >= high_threshold).sum()
        features_dict['high_frequency'] = float(high_rounds / len(df))

        # 6. Win Rate (multiplier > 2.0)
        win_threshold = 2.0
        win_rounds = (df['multiplier'] >= win_threshold).sum()
        features_dict['win_rate'] = float(win_rounds / len(df))

        # 7. Skewness and Kurtosis
        features_dict['skewness'] = float(df['multiplier'].skew())
        features_dict['kurtosis'] = float(df['multiplier'].kurtosis())

        # 8. Percentiles
        features_dict['percentile_25'] = float(df['multiplier'].quantile(0.25))
        features_dict['percentile_75'] = float(df['multiplier'].quantile(0.75))
        features_dict['iqr'] = float(features_dict['percentile_75'] - features_dict['percentile_25'])

        # 9. Moving Averages (if enough data)
        if len(df) >= 10:
            ma_5 = df['multiplier'].tail(5).mean()
            ma_10 = df['multiplier'].tail(10).mean()
            features_dict['ma5_ma10_ratio'] = float(ma_5 / ma_10) if ma_10 > 0 else 1.0
        else:
            features_dict['ma5_ma10_ratio'] = 1.0

        # 10. Recency (weight recent rounds higher)
        if len(df) >= 5:
            recent_3 = df['multiplier'].tail(3).mean()
            all_avg = df['multiplier'].mean()
            features_dict['recent_vs_overall'] = float(recent_3 / all_avg) if all_avg > 0 else 1.0
        else:
            features_dict['recent_vs_overall'] = 1.0

        # 11. Time-based features
        if 'timestamp' in df.columns:
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                df = df.dropna(subset=['timestamp'])
                if len(df) > 1:
                    time_diffs = df['timestamp'].diff().dt.total_seconds().dropna()
                    features_dict['avg_time_between_rounds'] = float(time_diffs.mean())
                    features_dict['rounds_per_minute'] = float(60.0 / time_diffs.mean()) if time_diffs.mean() > 0 else 0
                else:
                    features_dict['avg_time_between_rounds'] = 0.0
                    features_dict['rounds_per_minute'] = 0.0
            except:
                features_dict['avg_time_between_rounds'] = 0.0
                features_dict['rounds_per_minute'] = 0.0

        # Convert to numpy array in consistent order
        feature_vector = np.array([features_dict[key] for key in sorted(features_dict.keys())])

        return feature_vector, features_dict

    def _get_default_features(self) -> Dict:
        """Get default feature dictionary with zeros"""
        return {
            'avg_time_between_rounds': 0.0,
            'crash_frequency': 0.0,
            'high_frequency': 0.0,
            'iqr': 0.0,
            'kurtosis': 0.0,
            'ma5_ma10_ratio': 1.0,
            'max_multiplier': 0.0,
            'mean_multiplier': 0.0,
            'median_multiplier': 0.0,
            'min_multiplier': 0.0,
            'momentum_5': 0.0,
            'percentile_25': 0.0,
            'percentile_75': 0.0,
            'recent_vs_overall': 1.0,
            'return_volatility': 0.0,
            'rounds_per_minute': 0.0,
            'skewness': 0.0,
            'std_multiplier': 0.0,
            'trend_5': 0.0,
            'volatility': 0.0,
            'win_rate': 0.0,
        }

    def get_feature_names(self) -> List[str]:
        """Get sorted list of feature names"""
        return sorted(self._get_default_features().keys())
