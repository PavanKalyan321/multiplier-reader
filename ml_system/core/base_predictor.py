"""
Base Predictor - Abstract base class for all ML predictors

Defines the common interface and functionality that all prediction models must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, List
import numpy as np
from datetime import datetime


class BasePredictor(ABC):
    """
    Abstract base class for all predictors in the ML system.

    All concrete model implementations must inherit from this class and implement:
    - _create_model(): Initialize the specific ML model
    - train(): Train the model on historical data
    - predict(): Make a prediction given features

    The base class provides:
    - Common prediction structure
    - Accuracy tracking
    - Confidence calculation
    - Performance statistics
    """

    def __init__(self, name: str, model_type: str, confidence_threshold: float = 0.6):
        """
        Initialize base predictor

        Args:
            name: Unique name identifier for this model (e.g., "RandomForest", "H2OAutoML")
            model_type: Category of model (e.g., "Legacy", "AutoML", "Trained", "BinaryClassifier")
            confidence_threshold: Minimum confidence for betting recommendation (default 0.6)
        """
        self.name = name
        self.model_type = model_type
        self.confidence_threshold = confidence_threshold

        # Model state
        self.model = None
        self.is_trained = False

        # Performance tracking
        self.predictions_made = 0
        self.prediction_errors: List[float] = []
        self.avg_error = 0.0
        self.last_prediction: Optional[Dict] = None

        # Create the specific model implementation
        self._create_model()

    @abstractmethod
    def _create_model(self):
        """
        Create and configure the specific ML model.

        This method must be implemented by subclasses to initialize
        their specific model type (e.g., RandomForest, LGBM, etc.)

        Example:
            self.model = RandomForestRegressor(n_estimators=100)
        """
        pass

    @abstractmethod
    def train(self, X: np.ndarray, y: np.ndarray) -> bool:
        """
        Train the model on feature matrix X and target vector y.

        Args:
            X: Feature matrix of shape (n_samples, n_features)
            y: Target vector of shape (n_samples,) containing crash multipliers

        Returns:
            True if training successful, False otherwise

        Example:
            X_scaled = self.scaler.fit_transform(X)
            self.model.fit(X_scaled, y)
            self.is_trained = True
            return True
        """
        pass

    @abstractmethod
    def predict(self, X: np.ndarray) -> Dict:
        """
        Make a prediction for given features.

        Args:
            X: Feature vector of shape (1, n_features) or (n_features,)

        Returns:
            Dictionary with prediction details:
            {
                'predicted_multiplier': float,  # Predicted crash multiplier
                'confidence': float,            # Confidence score (0.0-1.0)
                'range': tuple,                 # (min, max) prediction range
                'bet': bool,                    # Betting recommendation
                'model_name': str,              # Name of this model
                'model_type': str,              # Type category
                'timestamp': str                # ISO format timestamp
            }

        Example:
            pred = self.model.predict(X)[0]
            confidence = self._calculate_confidence()
            return {
                'predicted_multiplier': float(pred),
                'confidence': float(confidence),
                'range': (pred * 0.8, pred * 1.2),
                'bet': confidence > self.confidence_threshold,
                'model_name': self.name,
                'model_type': self.model_type,
                'timestamp': datetime.now().isoformat()
            }
        """
        pass

    def update_accuracy(self, actual: float, predicted: float):
        """
        Update prediction accuracy statistics after actual result is known.

        This method tracks prediction errors and maintains a rolling average
        of the last 50 predictions for dynamic confidence adjustment.

        Args:
            actual: The actual crash multiplier that occurred
            predicted: The predicted crash multiplier from this model
        """
        error = abs(actual - predicted)
        self.prediction_errors.append(error)

        # Keep only last 50 errors for rolling average
        if len(self.prediction_errors) > 50:
            self.prediction_errors = self.prediction_errors[-50:]

        # Update average error
        if len(self.prediction_errors) > 0:
            self.avg_error = np.mean(self.prediction_errors)

    def _calculate_confidence(self) -> float:
        """
        Calculate confidence score based on historical performance.

        Confidence is inversely related to average prediction error:
        - Error of 0 → confidence 0.95
        - Error of 5 → confidence 0.50
        - Error of 10+ → confidence 0.30

        Returns:
            Confidence value between 0.3 and 0.95
        """
        if self.predictions_made == 0:
            # Initial confidence after training
            return 0.7

        # Lower error = higher confidence
        # Formula: confidence = 1.0 - (avg_error / 10.0)
        # Clamped between 0.3 and 0.95
        confidence = max(0.3, min(0.95, 1.0 - (self.avg_error / 10.0)))
        return confidence

    def get_stats(self) -> Dict:
        """
        Get model performance statistics.

        Returns:
            Dictionary with performance metrics:
            {
                'model_name': str,
                'model_type': str,
                'predictions_made': int,
                'avg_error': float,
                'is_trained': bool,
                'confidence_threshold': float
            }
        """
        return {
            'model_name': self.name,
            'model_type': self.model_type,
            'predictions_made': self.predictions_made,
            'avg_error': self.avg_error,
            'is_trained': self.is_trained,
            'confidence_threshold': self.confidence_threshold
        }

    def reset_stats(self):
        """Reset performance statistics. Useful for retraining scenarios."""
        self.predictions_made = 0
        self.prediction_errors = []
        self.avg_error = 0.0
        self.last_prediction = None

    def __repr__(self) -> str:
        """String representation of the predictor"""
        return f"{self.model_type}Predictor(name='{self.name}', trained={self.is_trained}, predictions={self.predictions_made})"
