"""
Prediction Engine - Main orchestrator for the advanced ML prediction system

Integrates all components:
- 25+ ML models (legacy, AutoML, trained, classifiers)
- Hybrid betting strategy
- Pattern detection
- Ensemble voting
"""

import numpy as np
from typing import Dict, List, Optional
from collections import deque
from datetime import datetime

from ml_system.core.feature_extractor import FeatureExtractor
from ml_system.core.feature_adapter import FeatureAdapter
from ml_system.core.model_registry import ModelRegistry, ModelFactory
from ml_system.strategies.hybrid_strategy import HybridBettingStrategy
from ml_system.strategies.ensemble_strategy import EnsembleStrategy
from ml_system.strategies.betting_decision import BettingDecisionMaker
from ml_system.patterns.stepping_stone import SteppingStoneDetector
from ml_system.patterns.color_detector import ColorDetector
from ml_system.patterns.zone_detector import ZoneDetector
from ml_system.patterns.time_patterns import TimePatternDetector
from ml_system.config import MLSystemConfig


class PredictionEngine:
    """
    Main prediction orchestrator for advanced ML system.

    Manages all 25+ models, strategies, and pattern detection to provide
    comprehensive crash multiplier predictions.
    """

    def __init__(self, history_size: int = 1000, min_rounds_for_prediction: int = 5):
        """
        Initialize prediction engine.

        Args:
            history_size: Maximum number of rounds to keep in history
            min_rounds_for_prediction: Minimum rounds before making predictions
        """
        self.history_size = history_size
        self.min_rounds = min_rounds_for_prediction
        self.round_history = deque(maxlen=history_size)

        print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Initializing Advanced ML Prediction Engine...")

        # Initialize feature engineering
        self.feature_extractor = FeatureExtractor()
        self.feature_adapter = FeatureAdapter() if MLSystemConfig.USE_FEATURE_ADAPTER else None

        # Initialize model registry
        self.registry = ModelRegistry()

        # Create all models
        ModelFactory.create_all_models(self.registry, self.feature_extractor, self.feature_adapter)

        # Initialize strategies
        classifiers = self.registry.get_group('classifiers')  # Will be empty list now
        self.hybrid_strategy = HybridBettingStrategy(
            binary_classifiers=classifiers,  # Empty list - only Position 2 (cold streak) active
            confidence_threshold=MLSystemConfig.HYBRID_CONFIDENCE_THRESHOLD,
            cold_streak_threshold=MLSystemConfig.COLD_STREAK_THRESHOLD
        )
        self.ensemble_strategy = EnsembleStrategy(self.registry.get_all_models())
        self.betting_decision = BettingDecisionMaker(self.hybrid_strategy, self.ensemble_strategy)

        # Initialize pattern detectors
        self.pattern_detectors = {}
        if MLSystemConfig.ENABLE_PATTERN_DETECTION:
            self.pattern_detectors['stepping_stone'] = SteppingStoneDetector()
            self.pattern_detectors['color'] = ColorDetector()
            self.pattern_detectors['zone'] = ZoneDetector()
            self.pattern_detectors['time'] = TimePatternDetector()

        # State
        self.is_trained = False
        self.predictions_made = 0

        print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Prediction engine initialized successfully")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: {self.registry}")

    @property
    def min_rounds_for_prediction(self):
        """Compatibility property for main.py"""
        return self.min_rounds

    def add_round(self, crash_multiplier: float, duration: float, timestamp: float):
        """
        Add a completed round to history.

        Args:
            crash_multiplier: Final crash multiplier
            duration: Round duration in seconds
            timestamp: Unix timestamp
        """
        round_data = {
            'crash_multiplier': crash_multiplier,
            'duration': duration,
            'timestamp': timestamp
        }
        self.round_history.append(round_data)

    def train(self, lookback: int = 10) -> bool:
        """
        Train all models on historical data.

        Args:
            lookback: Number of rounds to use for feature extraction

        Returns:
            True if training successful
        """
        if len(self.round_history) < lookback + 1:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: Not enough data for training ({len(self.round_history)} < {lookback + 1})")
            return False

        try:
            rounds = list(self.round_history)
            X_list = []
            y_list = []

            # Create training samples
            for i in range(lookback, len(rounds)):
                history_slice = rounds[i-lookback:i]
                features = self.feature_extractor.extract_features(history_slice)
                target = rounds[i]['crash_multiplier']

                X_list.append(features)
                y_list.append(target)

            if len(X_list) == 0:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: No training samples created")
                return False

            X = np.array(X_list)
            y = np.array(y_list)

            print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Training all models on {len(X)} samples...")

            # Train all models
            successful = 0
            failed = 0

            for model in self.registry.get_all_models():
                try:
                    if model.train(X, y):
                        successful += 1
                    else:
                        failed += 1
                except Exception as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: Failed to train {model.name}: {e}")
                    failed += 1

            print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Training complete - {successful} successful, {failed} failed")

            if successful > 0:
                self.is_trained = True
                return True

            return False

        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: Training failed: {e}")
            return False

    def predict_all(self, lookback: int = 10) -> Optional[Dict]:
        """
        Make predictions using all models and strategies.

        Args:
            lookback: Number of rounds to use for features

        Returns:
            Comprehensive prediction result with:
            - ensemble: Ensemble prediction
            - hybrid_strategy: Hybrid strategy decision
            - all_predictions: All model predictions grouped
            - patterns: Pattern detection results
            - betting_decision: Final betting recommendation
        """
        if not self.is_trained:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: Models not trained yet")
            return None

        if len(self.round_history) < lookback:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: Not enough history for prediction")
            return None

        try:
            # Extract features
            recent_rounds = list(self.round_history)[-lookback:]
            features = self.feature_extractor.extract_features(recent_rounds)

            # Get predictions from all models
            all_predictions = {
                'legacy': [],
                'automl': [],
                'trained': [],
                'classifiers': []
            }

            for group_name in ['legacy', 'automl', 'trained', 'classifiers']:
                for model in self.registry.get_group(group_name):
                    if model.is_trained:
                        try:
                            pred = model.predict(features.reshape(1, -1))
                            all_predictions[group_name].append(pred)
                        except Exception as e:
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: {model.name} prediction failed: {e}")

            # Ensemble prediction
            flat_predictions = []
            for group in all_predictions.values():
                flat_predictions.extend(group)

            ensemble = self.ensemble_strategy.get_ensemble_prediction(flat_predictions)

            # Hybrid strategy decision
            recent_multipliers = [r['crash_multiplier'] for r in self.round_history]
            hybrid_decision = self.hybrid_strategy.decide(features, recent_multipliers)

            # Pattern detection
            patterns = {}
            for name, detector in self.pattern_detectors.items():
                try:
                    detected = detector.detect(list(self.round_history))
                    if detected:
                        patterns[name] = detected[0]
                    else:
                        patterns[name] = {'detected': False, 'type': None, 'confidence': 0.0}
                except Exception as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: Pattern detector '{name}' failed: {e}")
                    patterns[name] = {'detected': False, 'type': None, 'confidence': 0.0}

            # Final betting decision
            betting_decision = self.betting_decision.make_decision(
                hybrid_decision, ensemble, all_predictions
            )

            self.predictions_made += 1

            return {
                'ensemble': ensemble,
                'hybrid_strategy': hybrid_decision,
                'all_predictions': all_predictions,
                'patterns': patterns,
                'betting_decision': betting_decision,
                'prediction_number': self.predictions_made
            }

        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: Prediction failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def update_prediction_accuracy(self, actual_multiplier: float):
        """
        Update accuracy statistics for all models.

        Args:
            actual_multiplier: Actual crash multiplier that occurred
        """
        for model in self.registry.get_trained_models():
            if hasattr(model, 'last_prediction') and model.last_prediction:
                predicted = model.last_prediction.get('predicted_multiplier', 0)
                model.update_accuracy(actual_multiplier, predicted)

    def get_statistics(self) -> Dict:
        """Get overall statistics"""
        group_counts = self.registry.get_group_counts()

        return {
            'predictions_made': self.predictions_made,
            'rounds_collected': len(self.round_history),
            'is_trained': self.is_trained,
            'total_models': self.registry.get_model_count(),
            'models_by_group': group_counts,
            'trained_models': len(self.registry.get_trained_models()),
            'patterns_enabled': len(self.pattern_detectors)
        }
