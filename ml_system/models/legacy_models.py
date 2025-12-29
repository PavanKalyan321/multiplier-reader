"""
Legacy Models - Wraps existing 5 models in new architecture

Provides backward compatibility with current multi_model_predictor.py
"""

import numpy as np
from typing import Dict
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge, Lasso
from sklearn.tree import DecisionTreeRegressor
from sklearn.preprocessing import StandardScaler
from datetime import datetime

from ml_system.core.base_predictor import BasePredictor


class LegacyRandomForest(BasePredictor):
    """RandomForest model - Good for non-linear patterns"""

    def __init__(self, feature_extractor):
        super().__init__('RandomForest', 'Legacy')
        self.feature_extractor = feature_extractor
        self.scaler = StandardScaler()

    def _create_model(self):
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )

    def train(self, X: np.ndarray, y: np.ndarray) -> bool:
        try:
            X_scaled = self.scaler.fit_transform(X)
            self.model.fit(X_scaled, y)
            self.is_trained = True
            return True
        except Exception as e:
            print(f"[ERROR] RandomForest training failed: {e}")
            return False

    def predict(self, X: np.ndarray) -> Dict:
        if not self.is_trained:
            return self._default_prediction()

        try:
            if X.ndim == 1:
                X = X.reshape(1, -1)

            X_scaled = self.scaler.transform(X)
            pred = self.model.predict(X_scaled)[0]
            pred = max(1.0, min(100.0, float(pred)))  # Clamp to realistic range

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
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"[ERROR] RandomForest prediction failed: {e}")
            return self._default_prediction()

    def _default_prediction(self) -> Dict:
        return {
            'predicted_multiplier': 2.0,
            'confidence': 0.5,
            'range': (1.6, 2.4),
            'bet': False,
            'model_name': self.name,
            'model_type': self.model_type,
            'timestamp': datetime.now().isoformat()
        }


class LegacyGradientBoosting(BasePredictor):
    """GradientBoosting model - Good for sequential patterns"""

    def __init__(self, feature_extractor):
        super().__init__('GradientBoosting', 'Legacy')
        self.feature_extractor = feature_extractor
        self.scaler = StandardScaler()

    def _create_model(self):
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )

    def train(self, X: np.ndarray, y: np.ndarray) -> bool:
        try:
            X_scaled = self.scaler.fit_transform(X)
            self.model.fit(X_scaled, y)
            self.is_trained = True
            return True
        except Exception as e:
            print(f"[ERROR] GradientBoosting training failed: {e}")
            return False

    def predict(self, X: np.ndarray) -> Dict:
        if not self.is_trained:
            return self._default_prediction()

        try:
            if X.ndim == 1:
                X = X.reshape(1, -1)

            X_scaled = self.scaler.transform(X)
            pred = self.model.predict(X_scaled)[0]
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
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"[ERROR] GradientBoosting prediction failed: {e}")
            return self._default_prediction()

    def _default_prediction(self) -> Dict:
        return {
            'predicted_multiplier': 2.0,
            'confidence': 0.5,
            'range': (1.6, 2.4),
            'bet': False,
            'model_name': self.name,
            'model_type': self.model_type,
            'timestamp': datetime.now().isoformat()
        }


class LegacyRidge(BasePredictor):
    """Ridge model - Good for linear patterns with regularization"""

    def __init__(self, feature_extractor):
        super().__init__('Ridge', 'Legacy')
        self.feature_extractor = feature_extractor
        self.scaler = StandardScaler()

    def _create_model(self):
        self.model = Ridge(alpha=1.0)

    def train(self, X: np.ndarray, y: np.ndarray) -> bool:
        try:
            X_scaled = self.scaler.fit_transform(X)
            self.model.fit(X_scaled, y)
            self.is_trained = True
            return True
        except Exception as e:
            print(f"[ERROR] Ridge training failed: {e}")
            return False

    def predict(self, X: np.ndarray) -> Dict:
        if not self.is_trained:
            return self._default_prediction()

        try:
            if X.ndim == 1:
                X = X.reshape(1, -1)

            X_scaled = self.scaler.transform(X)
            pred = self.model.predict(X_scaled)[0]
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
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"[ERROR] Ridge prediction failed: {e}")
            return self._default_prediction()

    def _default_prediction(self) -> Dict:
        return {
            'predicted_multiplier': 2.0,
            'confidence': 0.5,
            'range': (1.6, 2.4),
            'bet': False,
            'model_name': self.name,
            'model_type': self.model_type,
            'timestamp': datetime.now().isoformat()
        }


class LegacyLasso(BasePredictor):
    """Lasso model - Good for feature selection"""

    def __init__(self, feature_extractor):
        super().__init__('Lasso', 'Legacy')
        self.feature_extractor = feature_extractor
        self.scaler = StandardScaler()

    def _create_model(self):
        self.model = Lasso(alpha=0.1, max_iter=2000)

    def train(self, X: np.ndarray, y: np.ndarray) -> bool:
        try:
            X_scaled = self.scaler.fit_transform(X)
            self.model.fit(X_scaled, y)
            self.is_trained = True
            return True
        except Exception as e:
            print(f"[ERROR] Lasso training failed: {e}")
            return False

    def predict(self, X: np.ndarray) -> Dict:
        if not self.is_trained:
            return self._default_prediction()

        try:
            if X.ndim == 1:
                X = X.reshape(1, -1)

            X_scaled = self.scaler.transform(X)
            pred = self.model.predict(X_scaled)[0]
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
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"[ERROR] Lasso prediction failed: {e}")
            return self._default_prediction()

    def _default_prediction(self) -> Dict:
        return {
            'predicted_multiplier': 2.0,
            'confidence': 0.5,
            'range': (1.6, 2.4),
            'bet': False,
            'model_name': self.name,
            'model_type': self.model_type,
            'timestamp': datetime.now().isoformat()
        }


class LegacyDecisionTree(BasePredictor):
    """DecisionTree model - Fast and interpretable"""

    def __init__(self, feature_extractor):
        super().__init__('DecisionTree', 'Legacy')
        self.feature_extractor = feature_extractor
        self.scaler = StandardScaler()

    def _create_model(self):
        self.model = DecisionTreeRegressor(
            max_depth=8,
            random_state=42
        )

    def train(self, X: np.ndarray, y: np.ndarray) -> bool:
        try:
            X_scaled = self.scaler.fit_transform(X)
            self.model.fit(X_scaled, y)
            self.is_trained = True
            return True
        except Exception as e:
            print(f"[ERROR] DecisionTree training failed: {e}")
            return False

    def predict(self, X: np.ndarray) -> Dict:
        if not self.is_trained:
            return self._default_prediction()

        try:
            if X.ndim == 1:
                X = X.reshape(1, -1)

            X_scaled = self.scaler.transform(X)
            pred = self.model.predict(X_scaled)[0]
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
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"[ERROR] DecisionTree prediction failed: {e}")
            return self._default_prediction()

    def _default_prediction(self) -> Dict:
        return {
            'predicted_multiplier': 2.0,
            'confidence': 0.5,
            'range': (1.6, 2.4),
            'bet': False,
            'model_name': self.name,
            'model_type': self.model_type,
            'timestamp': datetime.now().isoformat()
        }


def create_legacy_models(feature_extractor):
    """
    Factory function to create all 5 legacy models.

    Args:
        feature_extractor: FeatureExtractor instance

    Returns:
        List of 5 legacy model instances
    """
    return [
        LegacyRandomForest(feature_extractor),
        LegacyGradientBoosting(feature_extractor),
        LegacyRidge(feature_extractor),
        LegacyLasso(feature_extractor),
        LegacyDecisionTree(feature_extractor)
    ]
