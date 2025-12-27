# ML Prediction for crash multiplier
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from collections import deque
import warnings
warnings.filterwarnings('ignore')

# Try to import ML libraries (will install if needed)
try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    import joblib
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("[WARNING] ML libraries not available. Run: pip install scikit-learn")


class CrashPredictor:
    """
    Predicts next round crash multiplier using Random Forest
    Based on last 1000 rounds of historical data
    """

    def __init__(self, history_size: int = 1000, min_rounds_for_prediction: int = 50):
        """
        Initialize the predictor

        Args:
            history_size: Number of historical rounds to keep (default: 1000)
            min_rounds_for_prediction: Minimum rounds needed before making predictions (default: 50)
        """
        self.history_size = history_size
        self.min_rounds_for_prediction = min_rounds_for_prediction
        self.round_history = deque(maxlen=history_size)

        # ML model components
        self.model: Optional[RandomForestRegressor] = None
        self.scaler: Optional[StandardScaler] = None
        self.is_trained = False

        # Performance tracking
        self.predictions_made = 0
        self.prediction_errors = []
        self.last_prediction: Optional[Dict] = None

        if ML_AVAILABLE:
            self._initialize_model()
        else:
            print("[WARNING] ML predictor initialized but libraries not available")

    def _initialize_model(self):
        """Initialize the Random Forest model and scaler"""
        if not ML_AVAILABLE:
            return

        # Random Forest configuration
        # n_estimators: number of trees (more = better but slower)
        # max_depth: max tree depth (prevent overfitting)
        # min_samples_split: min samples to split node
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1  # Use all CPU cores
        )
        self.scaler = StandardScaler()

    def add_round(self, crash_multiplier: float, duration: float, timestamp: float):
        """
        Add a completed round to history

        Args:
            crash_multiplier: The multiplier where round crashed
            duration: Round duration in seconds
            timestamp: Unix timestamp of round end
        """
        round_data = {
            'crash_multiplier': crash_multiplier,
            'duration': duration,
            'timestamp': timestamp
        }
        self.round_history.append(round_data)

    def _extract_features(self, lookback: int = 10) -> Optional[np.ndarray]:
        """
        Extract features from historical data for prediction

        Features include:
        - Last N crash multipliers (mean, std, min, max)
        - Last N durations (mean, std)
        - Trend indicators (increasing/decreasing)
        - Time-based features (hour of day, day of week)
        - Statistical features from recent history

        Args:
            lookback: Number of recent rounds to analyze for features

        Returns:
            Feature vector as numpy array, or None if insufficient data
        """
        if len(self.round_history) < lookback:
            return None

        # Get last N rounds
        recent_rounds = list(self.round_history)[-lookback:]
        multipliers = [r['crash_multiplier'] for r in recent_rounds]
        durations = [r['duration'] for r in recent_rounds]

        features = []

        # Statistical features from multipliers
        features.extend([
            np.mean(multipliers),      # Mean of last N crashes
            np.std(multipliers),       # Volatility
            np.min(multipliers),       # Min crash
            np.max(multipliers),       # Max crash
            np.median(multipliers),    # Median crash
        ])

        # Duration features
        features.extend([
            np.mean(durations),        # Mean duration
            np.std(durations),         # Duration volatility
        ])

        # Trend features (last 5 vs previous 5)
        if lookback >= 10:
            last_5 = multipliers[-5:]
            prev_5 = multipliers[-10:-5]
            features.extend([
                np.mean(last_5) - np.mean(prev_5),  # Trend direction
                np.mean(last_5) / np.mean(prev_5),  # Trend ratio
            ])
        else:
            features.extend([0, 1])  # Neutral trend

        # Recent pattern (last 3 rounds)
        if lookback >= 3:
            last_3 = multipliers[-3:]
            features.extend([
                last_3[-1],            # Most recent crash
                last_3[-2],            # 2nd most recent
                last_3[-3],            # 3rd most recent
            ])
        else:
            features.extend([0, 0, 0])

        # Streak detection (high/low streaks)
        high_threshold = np.mean(multipliers) + np.std(multipliers)
        low_threshold = np.mean(multipliers) - np.std(multipliers)

        high_streak = sum(1 for m in multipliers[-5:] if m > high_threshold)
        low_streak = sum(1 for m in multipliers[-5:] if m < low_threshold)

        features.extend([
            high_streak,               # Number of high crashes in last 5
            low_streak,                # Number of low crashes in last 5
        ])

        # Time-based features (cyclical encoding)
        if recent_rounds:
            last_timestamp = recent_rounds[-1]['timestamp']
            dt = datetime.fromtimestamp(last_timestamp)
            hour = dt.hour
            day_of_week = dt.weekday()

            # Cyclical encoding for hour (0-23)
            hour_sin = np.sin(2 * np.pi * hour / 24)
            hour_cos = np.cos(2 * np.pi * hour / 24)

            # Cyclical encoding for day of week (0-6)
            day_sin = np.sin(2 * np.pi * day_of_week / 7)
            day_cos = np.cos(2 * np.pi * day_of_week / 7)

            features.extend([hour_sin, hour_cos, day_sin, day_cos])
        else:
            features.extend([0, 0, 0, 0])

        return np.array(features).reshape(1, -1)

    def _prepare_training_data(self, lookback: int = 10) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Prepare training dataset from historical rounds

        Args:
            lookback: Number of rounds to use for feature extraction

        Returns:
            Tuple of (X, y) where X is features and y is target (next crash multiplier)
            Returns (None, None) if insufficient data
        """
        if len(self.round_history) < lookback + 1:
            return None, None

        X_list = []
        y_list = []

        rounds = list(self.round_history)

        # Create training samples
        # For each position, use lookback rounds to predict the next crash
        for i in range(lookback, len(rounds)):
            # Extract features from rounds[i-lookback:i]
            history_slice = rounds[i-lookback:i]
            multipliers = [r['crash_multiplier'] for r in history_slice]
            durations = [r['duration'] for r in history_slice]

            # Build feature vector
            features = []

            # Statistical features
            features.extend([
                np.mean(multipliers),
                np.std(multipliers),
                np.min(multipliers),
                np.max(multipliers),
                np.median(multipliers),
            ])

            # Duration features
            features.extend([
                np.mean(durations),
                np.std(durations),
            ])

            # Trend features
            if lookback >= 10:
                last_5 = multipliers[-5:]
                prev_5 = multipliers[-10:-5]
                features.extend([
                    np.mean(last_5) - np.mean(prev_5),
                    np.mean(last_5) / np.mean(prev_5),
                ])
            else:
                features.extend([0, 1])

            # Recent pattern
            if lookback >= 3:
                features.extend([
                    multipliers[-1],
                    multipliers[-2],
                    multipliers[-3],
                ])
            else:
                features.extend([0, 0, 0])

            # Streaks
            high_threshold = np.mean(multipliers) + np.std(multipliers)
            low_threshold = np.mean(multipliers) - np.std(multipliers)
            high_streak = sum(1 for m in multipliers[-5:] if m > high_threshold)
            low_streak = sum(1 for m in multipliers[-5:] if m < low_threshold)
            features.extend([high_streak, low_streak])

            # Time features
            last_timestamp = history_slice[-1]['timestamp']
            dt = datetime.fromtimestamp(last_timestamp)
            hour = dt.hour
            day_of_week = dt.weekday()
            features.extend([
                np.sin(2 * np.pi * hour / 24),
                np.cos(2 * np.pi * hour / 24),
                np.sin(2 * np.pi * day_of_week / 7),
                np.cos(2 * np.pi * day_of_week / 7),
            ])

            X_list.append(features)
            y_list.append(rounds[i]['crash_multiplier'])  # Target is the next crash

        if not X_list:
            return None, None

        return np.array(X_list), np.array(y_list)

    def train(self, lookback: int = 10) -> bool:
        """
        Train the model on historical data

        Args:
            lookback: Number of rounds to use for features

        Returns:
            True if training successful, False otherwise
        """
        if not ML_AVAILABLE:
            print("[ERROR] Cannot train: ML libraries not installed")
            return False

        if len(self.round_history) < self.min_rounds_for_prediction:
            print(f"[INFO] Need {self.min_rounds_for_prediction} rounds to train, have {len(self.round_history)}")
            return False

        # Prepare training data
        X, y = self._prepare_training_data(lookback=lookback)

        if X is None or len(X) == 0:
            print("[ERROR] Failed to prepare training data")
            return False

        try:
            # Scale features
            X_scaled = self.scaler.fit_transform(X)

            # Train model
            self.model.fit(X_scaled, y)
            self.is_trained = True

            # Calculate training score
            train_score = self.model.score(X_scaled, y)

            print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Model trained on {len(X)} samples")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Training R² score: {train_score:.4f}")

            return True

        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: Training failed: {e}")
            return False

    def predict(self, lookback: int = 10) -> Optional[Dict]:
        """
        Predict the next round's crash multiplier

        Args:
            lookback: Number of recent rounds to use for prediction

        Returns:
            Dictionary with prediction details, or None if prediction not possible
        """
        if not ML_AVAILABLE or not self.is_trained:
            return None

        if len(self.round_history) < lookback:
            return None

        try:
            # Extract features
            X = self._extract_features(lookback=lookback)
            if X is None:
                return None

            # Scale features
            X_scaled = self.scaler.transform(X)

            # Make prediction
            prediction = self.model.predict(X_scaled)[0]

            # Ensure prediction is reasonable (min 1.0x)
            prediction = max(1.0, prediction)

            # Calculate confidence based on recent prediction accuracy
            confidence = self._calculate_confidence()

            # Create prediction result
            result = {
                'predicted_multiplier': round(prediction, 2),
                'confidence': round(confidence, 2),
                'timestamp': datetime.now().isoformat(),
                'model_type': 'RandomForest',
                'training_samples': len(self.round_history),
                'prediction_number': self.predictions_made + 1
            }

            self.last_prediction = result
            self.predictions_made += 1

            return result

        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: Prediction failed: {e}")
            return None

    def _calculate_confidence(self) -> float:
        """
        Calculate prediction confidence based on recent performance

        Returns:
            Confidence score between 0 and 1
        """
        if len(self.prediction_errors) < 5:
            return 0.5  # Neutral confidence with limited history

        # Use recent errors to estimate confidence
        recent_errors = self.prediction_errors[-20:]
        avg_error = np.mean(recent_errors)
        std_error = np.std(recent_errors)

        # Lower error = higher confidence
        # Normalize to 0-1 range (assuming typical errors are 0-5x)
        confidence = 1.0 - min(avg_error / 5.0, 1.0)

        return max(0.1, min(0.9, confidence))  # Clamp to 0.1-0.9

    def update_prediction_accuracy(self, actual_multiplier: float):
        """
        Update prediction accuracy tracking with actual result

        Args:
            actual_multiplier: The actual crash multiplier that occurred
        """
        if self.last_prediction is None:
            return

        predicted = self.last_prediction['predicted_multiplier']
        error = abs(predicted - actual_multiplier)

        self.prediction_errors.append(error)

        # Keep only last 100 errors
        if len(self.prediction_errors) > 100:
            self.prediction_errors = self.prediction_errors[-100:]

    def get_statistics(self) -> Dict:
        """
        Get predictor performance statistics

        Returns:
            Dictionary with performance metrics
        """
        if not self.prediction_errors:
            return {
                'predictions_made': self.predictions_made,
                'avg_error': 0,
                'accuracy': 0,
                'is_trained': self.is_trained,
                'training_samples': len(self.round_history)
            }

        avg_error = np.mean(self.prediction_errors)

        return {
            'predictions_made': self.predictions_made,
            'avg_error': round(avg_error, 2),
            'min_error': round(min(self.prediction_errors), 2),
            'max_error': round(max(self.prediction_errors), 2),
            'is_trained': self.is_trained,
            'training_samples': len(self.round_history),
            'history_size': len(self.round_history)
        }

    def save_model(self, filepath: str):
        """Save trained model to disk"""
        if not ML_AVAILABLE or not self.is_trained:
            return False

        try:
            joblib.dump({
                'model': self.model,
                'scaler': self.scaler,
                'history': list(self.round_history)
            }, filepath)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save model: {e}")
            return False

    def load_model(self, filepath: str):
        """Load trained model from disk"""
        if not ML_AVAILABLE:
            return False

        try:
            data = joblib.load(filepath)
            self.model = data['model']
            self.scaler = data['scaler']
            self.round_history = deque(data['history'], maxlen=self.history_size)
            self.is_trained = True
            return True
        except Exception as e:
            print(f"[ERROR] Failed to load model: {e}")
            return False
