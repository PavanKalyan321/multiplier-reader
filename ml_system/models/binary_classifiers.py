"""
Binary Classifiers - 4 classifiers for specific multiplier targets

Predicts probability of hitting specific targets: 1.5x, 2.0x, 3.0x, 5.0x
Uses SMOTE for class balancing.
"""

import numpy as np
from typing import Dict
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from ml_system.core.base_predictor import BasePredictor

# Try importing SMOTE
try:
    from imblearn.over_sampling import SMOTE
    SMOTE_AVAILABLE = True
except ImportError:
    SMOTE_AVAILABLE = False


class BinaryClassifier(BasePredictor):
    """
    Binary classifier for specific multiplier target.

    Predicts probability that the next round will hit or exceed the target multiplier.
    """

    def __init__(self, target_multiplier: float, feature_extractor):
        super().__init__(f'Classifier_{target_multiplier}x', 'BinaryClassifier', confidence_threshold=0.75)
        self.target = target_multiplier
        self.feature_extractor = feature_extractor
        self.scaler = StandardScaler()
        self.smote = SMOTE() if SMOTE_AVAILABLE else None

    def _create_model(self):
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )

    def train(self, X: np.ndarray, y: np.ndarray) -> bool:
        """
        Train binary classifier with SMOTE for class balance.

        Args:
            X: Feature matrix
            y: Target multipliers (will be converted to binary labels)

        Returns:
            True if training successful
        """
        try:
            # Create binary labels (1 if >= target, 0 otherwise)
            y_binary = (y >= self.target).astype(int)

            # Check class distribution
            unique, counts = np.unique(y_binary, return_counts=True)
            print(f"[INFO] {self.name} class distribution: {dict(zip(unique, counts))}")

            # Apply SMOTE if available and classes are imbalanced
            if self.smote is not None and len(unique) == 2:
                try:
                    X_resampled, y_resampled = self.smote.fit_resample(X, y_binary)
                    print(f"[INFO] {self.name} SMOTE applied: {len(X)} -> {len(X_resampled)} samples")
                except Exception as e:
                    print(f"[WARNING] SMOTE failed for {self.name}, using original data: {e}")
                    X_resampled, y_resampled = X, y_binary
            else:
                X_resampled, y_resampled = X, y_binary

            # Scale and train
            X_scaled = self.scaler.fit_transform(X_resampled)
            self.model.fit(X_scaled, y_resampled)
            self.is_trained = True

            # Get training score
            score = self.model.score(X_scaled, y_resampled)
            print(f"[INFO] {self.name} trained - accuracy: {score:.4f}")

            return True
        except Exception as e:
            print(f"[ERROR] {self.name} training failed: {e}")
            return False

    def predict(self, X: np.ndarray) -> Dict:
        """
        Predict probability of hitting target multiplier.

        Returns:
            Dictionary with probability and betting recommendation
        """
        if not self.is_trained:
            return self._default_prediction()

        try:
            if X.ndim == 1:
                X = X.reshape(1, -1)

            X_scaled = self.scaler.transform(X)

            # Get probability of class 1 (hitting target)
            probabilities = self.model.predict_proba(X_scaled)[0]

            # Probability of hitting target (class 1)
            if len(probabilities) == 2:
                probability = probabilities[1]
            else:
                # Only one class in training data
                probability = 0.5

            # Confidence is the probability itself
            confidence = float(probability)

            # Bet if probability exceeds threshold
            bet = confidence >= self.confidence_threshold

            self.predictions_made += 1

            return {
                'predicted_multiplier': self.target,
                'confidence': confidence,
                'probability': confidence,
                'range': (self.target * 0.9, self.target * 1.1),
                'bet': bet,
                'model_name': self.name,
                'model_type': self.model_type,
                'target': self.target,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"[ERROR] {self.name} prediction failed: {e}")
            return self._default_prediction()

    def _default_prediction(self) -> Dict:
        return {
            'predicted_multiplier': self.target,
            'confidence': 0.5,
            'probability': 0.5,
            'range': (self.target * 0.9, self.target * 1.1),
            'bet': False,
            'model_name': self.name,
            'model_type': self.model_type,
            'target': self.target,
            'timestamp': datetime.now().isoformat()
        }


def create_binary_classifiers(feature_extractor):
    """
    Create all 4 binary classifiers for target multipliers.

    Args:
        feature_extractor: FeatureExtractor instance

    Returns:
        List of 4 binary classifier instances
    """
    targets = [1.5, 2.0, 3.0, 5.0]
    classifiers = []

    for target in targets:
        try:
            classifier = BinaryClassifier(target, feature_extractor)
            classifiers.append(classifier)
        except Exception as e:
            print(f"[WARNING] Could not create classifier for {target}x: {e}")

    if not SMOTE_AVAILABLE:
        print("[WARNING] SMOTE not available. Install with: pip install imbalanced-learn")
        print("[INFO] Binary classifiers will work without SMOTE but may be less accurate")

    return classifiers
