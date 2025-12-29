"""
Trained Models - 4 real trained ML models with feature adapter support

These models use the FeatureAdapter to work with 21-feature system while expecting 50 features.
"""

import numpy as np
from typing import Dict
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler

from ml_system.core.base_predictor import BasePredictor

# Try importing optional dependencies
try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

try:
    import tensorflow as tf
    from tensorflow import keras
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False


class TrainedRandomForest(BasePredictor):
    """Trained RandomForest with 50-feature support"""

    def __init__(self, feature_extractor, feature_adapter):
        super().__init__('Trained_RandomForest', 'Trained')
        self.feature_extractor = feature_extractor
        self.feature_adapter = feature_adapter
        self.scaler = StandardScaler()

    def _create_model(self):
        self.model = RandomForestRegressor(
            n_estimators=150,
            max_depth=15,
            random_state=42,
            n_jobs=-1
        )

    def train(self, X: np.ndarray, y: np.ndarray) -> bool:
        try:
            # Expand features from 21 to 50
            X_expanded = np.array([self.feature_adapter.expand_features(x) for x in X])
            X_scaled = self.scaler.fit_transform(X_expanded)
            self.model.fit(X_scaled, y)
            self.is_trained = True
            return True
        except Exception as e:
            print(f"[ERROR] Trained RandomForest training failed: {e}")
            return False

    def predict(self, X: np.ndarray) -> Dict:
        if not self.is_trained:
            return self._default_prediction()

        try:
            if X.ndim == 1:
                X = X.reshape(1, -1)

            # Expand and scale features
            X_expanded = self.feature_adapter.expand_features(X[0]).reshape(1, -1)
            X_scaled = self.scaler.transform(X_expanded)

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
            print(f"[ERROR] Trained RandomForest prediction failed: {e}")
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


class TrainedGradientBoosting(BasePredictor):
    """Trained GradientBoosting with 50-feature support"""

    def __init__(self, feature_extractor, feature_adapter):
        super().__init__('Trained_GradientBoosting', 'Trained')
        self.feature_extractor = feature_extractor
        self.feature_adapter = feature_adapter
        self.scaler = StandardScaler()

    def _create_model(self):
        self.model = GradientBoostingRegressor(
            n_estimators=150,
            max_depth=7,
            learning_rate=0.1,
            random_state=42
        )

    def train(self, X: np.ndarray, y: np.ndarray) -> bool:
        try:
            X_expanded = np.array([self.feature_adapter.expand_features(x) for x in X])
            X_scaled = self.scaler.fit_transform(X_expanded)
            self.model.fit(X_scaled, y)
            self.is_trained = True
            return True
        except Exception as e:
            print(f"[ERROR] Trained GradientBoosting training failed: {e}")
            return False

    def predict(self, X: np.ndarray) -> Dict:
        if not self.is_trained:
            return self._default_prediction()

        try:
            if X.ndim == 1:
                X = X.reshape(1, -1)

            X_expanded = self.feature_adapter.expand_features(X[0]).reshape(1, -1)
            X_scaled = self.scaler.transform(X_expanded)

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
            print(f"[ERROR] Trained GradientBoosting prediction failed: {e}")
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


class TrainedLGBM(BasePredictor):
    """Trained LightGBM with 50-feature support"""

    def __init__(self, feature_extractor, feature_adapter):
        if not LIGHTGBM_AVAILABLE:
            raise ImportError("LightGBM not available. Install with: pip install lightgbm")

        super().__init__('Trained_LGBM', 'Trained')
        self.feature_extractor = feature_extractor
        self.feature_adapter = feature_adapter
        self.scaler = StandardScaler()

    def _create_model(self):
        self.model = lgb.LGBMRegressor(
            n_estimators=150,
            max_depth=8,
            num_leaves=31,
            learning_rate=0.05,
            random_state=42,
            n_jobs=-1,
            verbosity=-1
        )

    def train(self, X: np.ndarray, y: np.ndarray) -> bool:
        try:
            X_expanded = np.array([self.feature_adapter.expand_features(x) for x in X])
            X_scaled = self.scaler.fit_transform(X_expanded)
            self.model.fit(X_scaled, y)
            self.is_trained = True
            return True
        except Exception as e:
            print(f"[ERROR] Trained LGBM training failed: {e}")
            return False

    def predict(self, X: np.ndarray) -> Dict:
        if not self.is_trained:
            return self._default_prediction()

        try:
            if X.ndim == 1:
                X = X.reshape(1, -1)

            X_expanded = self.feature_adapter.expand_features(X[0]).reshape(1, -1)
            X_scaled = self.scaler.transform(X_expanded)

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
            print(f"[ERROR] Trained LGBM prediction failed: {e}")
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


class TrainedLSTM(BasePredictor):
    """Trained LSTM Neural Network (optional - requires TensorFlow)"""

    def __init__(self, feature_extractor, feature_adapter):
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow not available. Install with: pip install tensorflow")

        super().__init__('Trained_LSTM', 'Trained')
        self.feature_extractor = feature_extractor
        self.feature_adapter = feature_adapter
        self.scaler = StandardScaler()

    def _create_model(self):
        # Simple sequential model (not true LSTM for this use case)
        self.model = keras.Sequential([
            keras.layers.Dense(128, activation='relu', input_shape=(50,)),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(64, activation='relu'),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(32, activation='relu'),
            keras.layers.Dense(1)
        ])
        self.model.compile(optimizer='adam', loss='mse')

    def train(self, X: np.ndarray, y: np.ndarray) -> bool:
        try:
            X_expanded = np.array([self.feature_adapter.expand_features(x) for x in X])
            X_scaled = self.scaler.fit_transform(X_expanded)
            self.model.fit(X_scaled, y, epochs=50, batch_size=32, verbose=0)
            self.is_trained = True
            return True
        except Exception as e:
            print(f"[ERROR] Trained LSTM training failed: {e}")
            return False

    def predict(self, X: np.ndarray) -> Dict:
        if not self.is_trained:
            return self._default_prediction()

        try:
            if X.ndim == 1:
                X = X.reshape(1, -1)

            X_expanded = self.feature_adapter.expand_features(X[0]).reshape(1, -1)
            X_scaled = self.scaler.transform(X_expanded)

            pred = self.model.predict(X_scaled, verbose=0)[0][0]
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
            print(f"[ERROR] Trained LSTM prediction failed: {e}")
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


def create_trained_models(feature_extractor, feature_adapter):
    """
    Create all available trained models.

    Args:
        feature_extractor: FeatureExtractor instance
        feature_adapter: FeatureAdapter instance

    Returns:
        List of trained model instances
    """
    models = [
        TrainedRandomForest(feature_extractor, feature_adapter),
        TrainedGradientBoosting(feature_extractor, feature_adapter),
    ]

    # Add LGBM if available
    if LIGHTGBM_AVAILABLE:
        try:
            models.append(TrainedLGBM(feature_extractor, feature_adapter))
        except Exception as e:
            print(f"[WARNING] Could not create LGBM model: {e}")

    # Add LSTM if available (optional)
    if TENSORFLOW_AVAILABLE:
        try:
            models.append(TrainedLSTM(feature_extractor, feature_adapter))
        except Exception as e:
            print(f"[WARNING] Could not create LSTM model: {e}")

    return models
