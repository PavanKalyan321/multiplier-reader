"""
AutoML Models - 16 simulated AutoML models with different strategies

These are simulated models using strategy-based weighting, not actual AutoML frameworks.
Each model uses a different focus strategy for predictions.
"""

import numpy as np
from typing import Dict
from datetime import datetime

from ml_system.core.base_predictor import BasePredictor


class AutoMLSimulatedPredictor(BasePredictor):
    """Base class for simulated AutoML predictors"""

    def __init__(self, name: str, strategy: str):
        super().__init__(name, 'AutoML-Simulated')
        self.strategy = strategy
        self.train_stats = {'mean': 0, 'std': 0, 'median': 0}

    def _create_model(self):
        # Simulated - no actual model
        self.model = None

    def train(self, X: np.ndarray, y: np.ndarray) -> bool:
        """Simulate training by storing statistics"""
        try:
            self.train_stats['mean'] = np.mean(y)
            self.train_stats['std'] = np.std(y)
            self.train_stats['median'] = np.median(y)
            self.is_trained = True
            return True
        except Exception as e:
            print(f"[ERROR] {self.name} training failed: {e}")
            return False

    def predict(self, X: np.ndarray) -> Dict:
        if not self.is_trained:
            return self._default_prediction()

        try:
            if X.ndim == 1:
                features = X
            else:
                features = X[0]

            # Apply strategy-specific prediction
            pred = self._strategy_predict(features)
            pred = max(1.0, min(100.0, float(pred)))

            confidence = self._calculate_confidence()
            range_margin = pred * 0.2
            pred_range = (max(1.0, pred - range_margin), pred + range_margin)

            self.predictions_made += 1

            return {
                'predicted_multiplier': pred,
                'confidence': confidence,
                'range': pred_range,
                'bet': confidence > self.confidence_threshold,
                'model_name': self.name,
                'model_type': self.model_type,
                'strategy': self.strategy,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"[ERROR] {self.name} prediction failed: {e}")
            return self._default_prediction()

    def _strategy_predict(self, features: np.ndarray) -> float:
        """Apply strategy-specific prediction logic"""
        # Feature indices:
        # 0: mean, 1: std, 7: trend_diff, 8: trend_ratio
        # 9-11: last_1, last_2, last_3
        # 18: volatility, 19: momentum

        if self.strategy == 'balanced':
            return features[0]  # mean_multiplier

        elif self.strategy == 'trend':
            return features[0] * features[8]  # mean * trend_ratio

        elif self.strategy == 'recent':
            # 60% last + 25% second-last + 15% third-last
            return 0.6 * features[9] + 0.25 * features[10] + 0.15 * features[11]

        elif self.strategy == 'sequence':
            # LSTM-style: progressive weighting
            weights = [0.5, 0.3, 0.2]
            return sum(w * features[9+i] for i, w in enumerate(weights))

        elif self.strategy == 'stable':
            # Average of mean, median, and last 5 average
            last_3_avg = np.mean(features[9:12])
            return (features[0] + features[4] + last_3_avg) / 3

        elif self.strategy == 'conservative':
            # Minimum of last, median, and recent average
            last_3_avg = np.mean(features[9:12])
            return min(features[9], features[4], last_3_avg)

        elif self.strategy == 'weighted':
            # Progressive weights 40%, 30%, 20%, 10%
            if len(features) >= 12:
                return 0.4 * features[9] + 0.3 * features[10] + 0.2 * features[11] + 0.1 * features[0]
            return features[0]

        elif self.strategy == 'volatility':
            # Incorporate volatility
            return features[0] + features[18] * features[1]

        elif self.strategy == 'distribution':
            # Median-based with std sampling
            return features[4] + np.random.normal(0, features[1] * 0.1)

        elif self.strategy == 'median':
            # 50/50 mix of last value and median
            return 0.5 * features[9] + 0.5 * features[4]

        elif self.strategy == 'pattern':
            # Moving average with trend adjustment
            ma = np.mean(features[9:12])
            return ma + features[7] * 0.5  # Add trend adjustment

        elif self.strategy == 'optimal':
            # Median with momentum adjustment
            return features[4] + features[19] * features[1]

        elif self.strategy == 'deep':
            # 30% last, 40% mean, 30% median
            return 0.3 * features[9] + 0.4 * features[0] + 0.3 * features[4]

        elif self.strategy == 'adaptive':
            # Volatility-adaptive
            if features[18] > 0.5:  # High volatility
                return features[4]  # Use median
            else:  # Low volatility
                return features[0]  # Use mean

        elif self.strategy == 'robust':
            # Median of last, recent avg, and overall median
            last_3_avg = np.mean(features[9:12])
            return np.median([features[9], last_3_avg, features[4]])

        elif self.strategy == 'scalable':
            # 60% last, 40% median
            return 0.6 * features[9] + 0.4 * features[4]

        else:
            return features[0]  # Default to mean

    def _default_prediction(self) -> Dict:
        return {
            'predicted_multiplier': 2.0,
            'confidence': 0.5,
            'range': (1.6, 2.4),
            'bet': False,
            'model_name': self.name,
            'model_type': self.model_type,
            'strategy': self.strategy,
            'timestamp': datetime.now().isoformat()
        }


def create_automl_models(feature_extractor):
    """
    Create all 16 simulated AutoML models.

    Each model uses a different prediction strategy.

    Args:
        feature_extractor: FeatureExtractor instance

    Returns:
        List of 16 AutoML model instances
    """
    models = [
        AutoMLSimulatedPredictor('H2O_AutoML', 'balanced'),
        AutoMLSimulatedPredictor('Google_AutoML', 'trend'),
        AutoMLSimulatedPredictor('AutoSklearn', 'recent'),
        AutoMLSimulatedPredictor('LSTM_Model', 'sequence'),
        AutoMLSimulatedPredictor('AutoGluon', 'stable'),
        AutoMLSimulatedPredictor('PyCaret', 'conservative'),
        AutoMLSimulatedPredictor('RandomForest_AutoML', 'weighted'),
        AutoMLSimulatedPredictor('CatBoost', 'volatility'),
        AutoMLSimulatedPredictor('LightGBM_AutoML', 'distribution'),
        AutoMLSimulatedPredictor('XGBoost_AutoML', 'median'),
        AutoMLSimulatedPredictor('MLP_NeuralNet', 'pattern'),
        AutoMLSimulatedPredictor('TPOT_Genetic', 'optimal'),
        AutoMLSimulatedPredictor('AutoKeras', 'deep'),
        AutoMLSimulatedPredictor('AutoPyTorch', 'adaptive'),
        AutoMLSimulatedPredictor('MLBox', 'robust'),
        AutoMLSimulatedPredictor('TransmogrifAI', 'scalable'),
    ]

    return models
