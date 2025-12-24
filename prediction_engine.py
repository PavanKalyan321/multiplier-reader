"""
ML Prediction Engine with 5 Models
Fast real-time predictions for round signals
Models retrain after each round with online learning
"""

import numpy as np
import pandas as pd
import json
import os
import joblib
from datetime import datetime
from typing import Dict, Tuple, Optional, List
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import SGDClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB

from feature_engineering import FeatureEngineer


class PredictionEngine:
    """
    Multi-model prediction engine for real-time round signals
    Supports 5 different ML models with online retraining
    """

    MODEL_NAMES = [
        "logistic_regression",
        "random_forest",
        "gradient_boosting",
        "decision_tree",
        "naive_bayes"
    ]

    def __init__(self, model_dir: str = "models"):
        """
        Initialize prediction engine with 5 models

        Args:
            model_dir: Directory to save/load trained models
        """
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)

        self.feature_engineer = FeatureEngineer(min_history=10)
        self.scaler = StandardScaler()
        self.models = self._initialize_models()
        self.is_fitted = False

    def _initialize_models(self) -> Dict:
        """Initialize 5 ML models"""
        models = {
            "logistic_regression": SGDClassifier(loss='log', random_state=42, warm_start=True, n_iter_no_change=100),
            "random_forest": RandomForestClassifier(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1),
            "gradient_boosting": GradientBoostingClassifier(n_estimators=50, max_depth=5, learning_rate=0.1, random_state=42),
            "decision_tree": DecisionTreeClassifier(max_depth=15, random_state=42),
            "naive_bayes": GaussianNB(),
        }
        return models

    def prepare_training_data(self, rounds_data: List[Dict], target_column: str = 'multiplier', threshold: float = 2.0) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Prepare training data from historical rounds

        Args:
            rounds_data: Historical round data
            target_column: Column to predict on
            threshold: Threshold for binary classification (multiplier >= threshold = 1)

        Returns:
            Tuple of (X, y) or (None, None) if insufficient data
        """
        if len(rounds_data) < self.feature_engineer.min_history:
            return None, None

        # Extract features for each round
        all_features = []
        all_targets = []

        for i in range(len(rounds_data) - 1):  # -1 to predict next round
            # Use history up to current round
            history = rounds_data[:i+1]
            X, _ = self.feature_engineer.extract_features(history)

            # Target is next round's multiplier
            next_round = rounds_data[i+1]
            y = 1 if next_round.get(target_column, 0) >= threshold else 0

            all_features.append(X)
            all_targets.append(y)

        if len(all_features) < 5:  # Need at least 5 samples
            return None, None

        X = np.array(all_features)
        y = np.array(all_targets)

        return X, y

    def train(self, rounds_data: List[Dict]) -> bool:
        """
        Train all 5 models on historical data

        Args:
            rounds_data: Historical round data

        Returns:
            True if training successful, False otherwise
        """
        X, y = self.prepare_training_data(rounds_data)

        if X is None or len(np.unique(y)) < 2:
            # Need both classes to train, or insufficient data
            return False

        try:
            # Fit scaler
            X_scaled = self.scaler.fit_transform(X)

            # Train all models
            for model_name, model in self.models.items():
                model.fit(X_scaled, y)

            self.is_fitted = True
            return True
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: Model training failed: {e}")
            return False

    def predict(self, current_rounds: List[Dict]) -> Dict:
        """
        Make predictions for next round based on current history

        Args:
            current_rounds: Historical rounds up to current point

        Returns:
            Dictionary with predictions from all models
        """
        if not self.is_fitted:
            return self._get_empty_predictions()

        try:
            # Extract features from current history
            X, features_dict = self.feature_engineer.extract_features(current_rounds)

            # Scale features
            X_scaled = self.scaler.transform(X.reshape(1, -1))

            predictions = {
                'timestamp': datetime.now().isoformat(),
                'features': features_dict,
                'models': {}
            }

            # Get predictions from all models
            for model_name, model in self.models.items():
                try:
                    # Binary prediction
                    pred = model.predict(X_scaled)[0]

                    # Probability for class 1 (high multiplier)
                    if hasattr(model, 'predict_proba'):
                        proba = model.predict_proba(X_scaled)[0]
                        confidence = float(proba[1]) if len(proba) > 1 else 0.5
                    else:
                        confidence = 0.5

                    predictions['models'][model_name] = {
                        'prediction': int(pred),
                        'confidence': float(confidence),
                        'probability_high': float(confidence),
                    }
                except Exception as e:
                    predictions['models'][model_name] = {
                        'prediction': 0,
                        'confidence': 0.0,
                        'error': str(e)
                    }

            # Calculate ensemble prediction (majority vote)
            ensemble_pred = np.mean([p['prediction'] for p in predictions['models'].values()])
            ensemble_conf = np.mean([p['confidence'] for p in predictions['models'].values()])

            predictions['ensemble'] = {
                'prediction': int(ensemble_pred >= 0.5),
                'confidence': float(ensemble_conf),
                'avg_model_confidence': float(ensemble_conf)
            }

            return predictions

        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: Prediction failed: {e}")
            return self._get_empty_predictions()

    def _get_empty_predictions(self) -> Dict:
        """Get default empty predictions"""
        return {
            'timestamp': datetime.now().isoformat(),
            'features': {},
            'models': {name: {'prediction': 0, 'confidence': 0.0} for name in self.MODEL_NAMES},
            'ensemble': {'prediction': 0, 'confidence': 0.0}
        }

    def save_models(self, suffix: str = '') -> bool:
        """
        Save trained models to disk

        Args:
            suffix: Optional suffix for model files

        Returns:
            True if successful
        """
        try:
            for model_name, model in self.models.items():
                path = os.path.join(self.model_dir, f"{model_name}{suffix}.joblib")
                joblib.dump(model, path)

            # Also save scaler
            scaler_path = os.path.join(self.model_dir, f"scaler{suffix}.joblib")
            joblib.dump(self.scaler, scaler_path)

            return True
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: Failed to save models: {e}")
            return False

    def load_models(self, suffix: str = '') -> bool:
        """
        Load trained models from disk

        Args:
            suffix: Optional suffix for model files

        Returns:
            True if successful
        """
        try:
            for model_name in self.MODEL_NAMES:
                path = os.path.join(self.model_dir, f"{model_name}{suffix}.joblib")
                if os.path.exists(path):
                    self.models[model_name] = joblib.load(path)

            # Load scaler
            scaler_path = os.path.join(self.model_dir, f"scaler{suffix}.joblib")
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)

            self.is_fitted = True
            return True
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: Failed to load models: {e}")
            return False

    def get_signal_type(self, prediction: Dict) -> str:
        """
        Generate signal type based on predictions

        Args:
            prediction: Prediction dictionary from predict()

        Returns:
            Signal type string (NEUTRAL, BULLISH, BEARISH, STRONG_BULLISH, STRONG_BEARISH)
        """
        if not prediction or 'ensemble' not in prediction:
            return "NEUTRAL"

        ensemble = prediction['ensemble']
        confidence = ensemble.get('confidence', 0.0)

        pred = ensemble.get('prediction', 0)

        if confidence < 0.55:
            return "NEUTRAL"
        elif pred == 1 and confidence >= 0.75:
            return "STRONG_BULLISH"
        elif pred == 1 and confidence >= 0.55:
            return "BULLISH"
        elif pred == 0 and confidence >= 0.75:
            return "STRONG_BEARISH"
        else:
            return "BEARISH"

    def calculate_volatility(self, current_rounds: List[Dict]) -> float:
        """
        Calculate volatility measure from current rounds

        Args:
            current_rounds: Historical rounds

        Returns:
            Volatility score (0-1)
        """
        if len(current_rounds) < 2:
            return 0.5

        multipliers = [r.get('multiplier', 0) for r in current_rounds]
        multipliers = [m for m in multipliers if m > 0]

        if len(multipliers) < 2:
            return 0.5

        volatility = np.std(multipliers) / np.mean(multipliers)
        # Normalize to 0-1 range (clipped)
        return min(1.0, volatility / 2.0)

    def calculate_momentum(self, current_rounds: List[Dict]) -> float:
        """
        Calculate momentum score from recent rounds

        Args:
            current_rounds: Historical rounds

        Returns:
            Momentum score (-1 to 1)
        """
        if len(current_rounds) < 3:
            return 0.0

        recent = [r.get('multiplier', 0) for r in current_rounds[-10:]]
        recent = [m for m in recent if m > 0]

        if len(recent) < 3:
            return 0.0

        # Calculate trend
        diffs = np.diff(recent)
        momentum = np.mean(diffs)

        # Normalize
        return np.clip(momentum / 5.0, -1.0, 1.0)
