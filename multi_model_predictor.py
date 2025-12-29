# Multi-Model ML Prediction for crash multiplier
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from collections import deque
import warnings
warnings.filterwarnings('ignore')

# Try to import ML libraries
try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import Ridge, Lasso
    from sklearn.tree import DecisionTreeRegressor
    from sklearn.preprocessing import StandardScaler
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("[WARNING] ML libraries not available. Run: pip install scikit-learn")


class MultiModelPredictor:
    """
    Predicts next round crash multiplier using multiple ML models
    Trains RandomForest, GradientBoosting, Ridge, Lasso, and DecisionTree
    Returns predictions from all models with confidence scores
    """

    def __init__(self, history_size: int = 1000, min_rounds_for_prediction: int = 5):
        """
        Initialize the multi-model predictor

        Args:
            history_size: Number of historical rounds to keep (default: 1000)
            min_rounds_for_prediction: Minimum rounds needed before making predictions (default: 5)
        """
        self.history_size = history_size
        self.min_rounds_for_prediction = min_rounds_for_prediction
        self.round_history = deque(maxlen=history_size)

        # Multiple ML models
        self.models: Dict[str, any] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.is_trained = False

        # Performance tracking per model
        self.model_stats: Dict[str, Dict] = {}
        self.predictions_made = 0
        self.last_predictions: Dict[str, Dict] = {}

        if ML_AVAILABLE:
            self._initialize_models()
        else:
            raise ImportError("ML libraries not available")

    def _initialize_models(self):
        """Initialize all ML models"""
        # RandomForest - Good for non-linear patterns
        self.models['RandomForest'] = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )

        # GradientBoosting - Good for sequential patterns
        self.models['GradientBoosting'] = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )

        # Ridge - Good for linear patterns with regularization
        self.models['Ridge'] = Ridge(alpha=1.0)

        # Lasso - Good for feature selection
        self.models['Lasso'] = Lasso(alpha=0.1, max_iter=2000)

        # DecisionTree - Fast and interpretable
        self.models['DecisionTree'] = DecisionTreeRegressor(
            max_depth=8,
            random_state=42
        )

        # Initialize scalers for each model
        for model_name in self.models.keys():
            self.scalers[model_name] = StandardScaler()
            self.model_stats[model_name] = {
                'predictions_made': 0,
                'prediction_errors': [],
                'avg_error': 0.0
            }

        print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Initialized {len(self.models)} ML models")

    def add_round(self, crash_multiplier: float, duration: float, timestamp: float):
        """
        Add a completed round to history

        Args:
            crash_multiplier: The final crash multiplier
            duration: How long the round lasted in seconds
            timestamp: When the round ended (Unix timestamp)
        """
        round_data = {
            'crash_multiplier': crash_multiplier,
            'duration': duration,
            'timestamp': timestamp
        }
        self.round_history.append(round_data)

    def _extract_features(self, lookback_data: List[Dict]) -> np.ndarray:
        """Extract 21 features from lookback data"""
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
                np.mean(last_5) - np.mean(prev_5),
                np.mean(last_5) / np.mean(prev_5) if np.mean(prev_5) > 0 else 1.0,
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

    def train(self, lookback: int = 10) -> bool:
        """
        Train all models on historical data

        Args:
            lookback: Number of previous rounds to use for feature extraction

        Returns:
            True if training successful, False otherwise
        """
        if len(self.round_history) < lookback + 1:
            return False

        try:
            rounds = list(self.round_history)
            X_list = []
            y_list = []

            # Create training samples
            for i in range(lookback, len(rounds)):
                history_slice = rounds[i-lookback:i]
                features = self._extract_features(history_slice)
                target = rounds[i]['crash_multiplier']

                X_list.append(features)
                y_list.append(target)

            if len(X_list) == 0:
                return False

            X = np.array(X_list)
            y = np.array(y_list)

            # Train each model
            for model_name, model in self.models.items():
                # Scale features
                X_scaled = self.scalers[model_name].fit_transform(X)

                # Train model
                model.fit(X_scaled, y)

                # Calculate training score
                train_score = model.score(X_scaled, y)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: {model_name} trained - R² score: {train_score:.4f}")

            self.is_trained = True
            print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: All models trained on {len(X)} samples")
            return True

        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: Training failed: {e}")
            return False

    def predict_all(self, lookback: int = 10) -> Optional[List[Dict]]:
        """
        Make predictions using all trained models

        Args:
            lookback: Number of previous rounds to use for features

        Returns:
            List of predictions from all models, or None if prediction fails
        """
        if not self.is_trained:
            return None

        if len(self.round_history) < lookback:
            return None

        try:
            # Get recent history
            recent_rounds = list(self.round_history)[-lookback:]
            features = self._extract_features(recent_rounds)
            X = features.reshape(1, -1)

            predictions = []

            # Get prediction from each model
            for model_name, model in self.models.items():
                # Scale features
                X_scaled = self.scalers[model_name].transform(X)

                # Predict
                predicted_value = model.predict(X_scaled)[0]

                # Calculate confidence (simple heuristic based on recent performance)
                stats = self.model_stats[model_name]
                if stats['predictions_made'] > 0:
                    avg_error = stats['avg_error']
                    # Lower error = higher confidence
                    confidence = max(0.3, min(0.95, 1.0 - (avg_error / 10.0)))
                else:
                    confidence = 0.5  # Default confidence

                # Calculate prediction range (±20%)
                range_margin = predicted_value * 0.2
                pred_range = (
                    max(1.0, predicted_value - range_margin),
                    predicted_value + range_margin
                )

                # Determine if bot should bet based on confidence threshold
                # Bet if confidence > 0.6 (60%)
                should_bet = confidence > 0.6

                prediction = {
                    'model_name': model_name,
                    'predicted_multiplier': float(predicted_value),
                    'confidence': float(confidence),
                    'range': pred_range,
                    'bet': should_bet,  # Boolean flag for betting decision
                    'timestamp': datetime.now().isoformat(),
                    'training_samples': len(self.round_history),
                    'prediction_number': stats['predictions_made'] + 1
                }

                predictions.append(prediction)
                self.last_predictions[model_name] = prediction

            self.predictions_made += 1
            return predictions

        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: Prediction failed: {e}")
            return None

    def update_prediction_accuracy(self, actual_multiplier: float):
        """
        Update accuracy statistics for all models after actual result is known

        Args:
            actual_multiplier: The actual crash multiplier that occurred
        """
        for model_name, prediction in self.last_predictions.items():
            error = abs(prediction['predicted_multiplier'] - actual_multiplier)
            stats = self.model_stats[model_name]
            stats['prediction_errors'].append(error)
            stats['predictions_made'] += 1

            # Update average error
            if len(stats['prediction_errors']) > 0:
                stats['avg_error'] = np.mean(stats['prediction_errors'][-50:])  # Last 50 predictions

    def get_statistics(self) -> Dict:
        """Get overall statistics across all models"""
        total_predictions = self.predictions_made

        model_accuracies = {}
        for model_name, stats in self.model_stats.items():
            model_accuracies[model_name] = {
                'predictions_made': stats['predictions_made'],
                'avg_error': stats['avg_error']
            }

        return {
            'predictions_made': total_predictions,
            'models': model_accuracies,
            'rounds_collected': len(self.round_history)
        }

    def get_ensemble_prediction(self, predictions: List[Dict]) -> Dict:
        """
        Get ensemble (weighted average) prediction from all models

        Args:
            predictions: List of predictions from all models

        Returns:
            Ensemble prediction dictionary
        """
        if not predictions:
            return None

        # Weight by confidence
        total_weight = sum(p['confidence'] for p in predictions)
        weighted_prediction = sum(p['predicted_multiplier'] * p['confidence'] for p in predictions) / total_weight

        # Calculate ensemble confidence (average of all)
        ensemble_confidence = np.mean([p['confidence'] for p in predictions])

        # Ensemble range
        range_margin = weighted_prediction * 0.2
        ensemble_range = (
            max(1.0, weighted_prediction - range_margin),
            weighted_prediction + range_margin
        )

        # Ensemble betting decision: bet if majority of models say bet
        bet_votes = sum(1 for p in predictions if p.get('bet', False))
        ensemble_should_bet = bet_votes > len(predictions) / 2

        return {
            'model_name': 'Ensemble',
            'predicted_multiplier': float(weighted_prediction),
            'confidence': float(ensemble_confidence),
            'range': ensemble_range,
            'bet': ensemble_should_bet,  # Majority vote for betting
            'timestamp': datetime.now().isoformat(),
            'num_models': len(predictions),
            'bet_votes': f"{bet_votes}/{len(predictions)}"
        }
