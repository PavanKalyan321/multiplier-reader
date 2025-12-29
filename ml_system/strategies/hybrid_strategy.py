"""
Hybrid Betting Strategy - Position 1 (ML) + Position 2 (Cold Streak)

Implements a two-position betting strategy that combines ML predictions
with rule-based cold streak detection.
"""

import numpy as np
from typing import Dict, List
from datetime import datetime


class HybridBettingStrategy:
    """
    Hybrid betting strategy with two positions:

    Position 1 (Conservative - ML Based):
    - Uses binary classifiers for 1.5x and 2.0x targets
    - Requires 75%+ confidence to bet
    - Safest betting approach

    Position 2 (Aggressive - Rule Based):
    - Detects cold streaks (8+ consecutive low rounds)
    - Targets 3.0x multiplier
    - Only triggers when Position 1 doesn't fire
    """

    def __init__(self, binary_classifiers: List, confidence_threshold: float = 0.75, cold_streak_threshold: int = 8):
        """
        Initialize hybrid strategy.

        Args:
            binary_classifiers: List of 4 binary classifiers (1.5x, 2.0x, 3.0x, 5.0x)
            confidence_threshold: Minimum confidence for Position 1 (default 0.75)
            cold_streak_threshold: Minimum low rounds for Position 2 (default 8)
        """
        self.classifiers = {}
        for clf in binary_classifiers:
            if hasattr(clf, 'target'):
                self.classifiers[clf.target] = clf

        self.confidence_threshold = confidence_threshold
        self.cold_streak_threshold = cold_streak_threshold

    def decide(self, features: np.ndarray, recent_history: List[float]) -> Dict:
        """
        Make betting decision using hybrid strategy.

        Args:
            features: Feature vector for current prediction
            recent_history: List of recent crash multipliers

        Returns:
            Dictionary with betting decision:
            {
                'position': 1 | 2 | None,
                'action': 'BET' | 'SKIP',
                'target_multiplier': float,
                'confidence': float,
                'reason': str
            }
        """
        # Position 1: Conservative ML-based
        pos1_decision = self._position_1_decision(features)
        if pos1_decision['action'] == 'BET':
            return pos1_decision

        # Position 2: Aggressive cold streak
        pos2_decision = self._position_2_decision(recent_history)
        if pos2_decision['action'] == 'BET':
            return pos2_decision

        # Skip if neither position triggers
        return {
            'position': None,
            'action': 'SKIP',
            'target_multiplier': None,
            'confidence': 0.0,
            'reason': 'No betting opportunity detected'
        }

    def _position_1_decision(self, features: np.ndarray) -> Dict:
        """
        Position 1: ML binary classifiers for 1.5x-2.0x.

        Returns betting decision based on classifier probabilities.
        """
        # Check 1.5x classifier first (safest)
        if 1.5 in self.classifiers:
            clf_1_5 = self.classifiers[1.5]
            if clf_1_5.is_trained:
                pred_1_5 = clf_1_5.predict(features.reshape(1, -1))

                if pred_1_5['confidence'] >= self.confidence_threshold:
                    return {
                        'position': 1,
                        'action': 'BET',
                        'target_multiplier': 1.5,
                        'confidence': pred_1_5['confidence'],
                        'reason': f"ML Classifier 1.5x: {pred_1_5['confidence']*100:.0f}% confidence"
                    }

        # Check 2.0x classifier (slightly more aggressive)
        if 2.0 in self.classifiers:
            clf_2_0 = self.classifiers[2.0]
            if clf_2_0.is_trained:
                pred_2_0 = clf_2_0.predict(features.reshape(1, -1))

                if pred_2_0['confidence'] >= self.confidence_threshold:
                    return {
                        'position': 1,
                        'action': 'BET',
                        'target_multiplier': 2.0,
                        'confidence': pred_2_0['confidence'],
                        'reason': f"ML Classifier 2.0x: {pred_2_0['confidence']*100:.0f}% confidence"
                    }

        return {'action': 'SKIP'}

    def _position_2_decision(self, recent_history: List[float]) -> Dict:
        """
        Position 2: Cold streak detection for 3.0x target.

        Detects when there are 8+ consecutive low rounds (< 2.0x)
        and recommends betting on 3.0x.
        """
        if len(recent_history) < self.cold_streak_threshold:
            return {'action': 'SKIP'}

        # Get streak length
        streak_length = self._get_cold_streak_length(recent_history)

        # Check if we have a cold streak
        if streak_length >= self.cold_streak_threshold:
            # Check for recent burst (any 5.0x+ in last 10 rounds)
            last_10 = recent_history[-10:] if len(recent_history) >= 10 else recent_history
            has_recent_burst = any(m >= 5.0 for m in last_10)

            if not has_recent_burst:
                # Calculate confidence based on streak length
                # Longer streak = higher confidence
                confidence = min(0.75, 0.45 + (streak_length * 0.05))

                return {
                    'position': 2,
                    'action': 'BET',
                    'target_multiplier': 3.0,
                    'confidence': confidence,
                    'reason': f"Cold streak detected: {streak_length} low rounds (< 2.0x)"
                }

        return {'action': 'SKIP'}

    def _get_cold_streak_length(self, history: List[float]) -> int:
        """
        Count consecutive low multipliers (< 2.0x) from the end of history.

        Args:
            history: List of crash multipliers

        Returns:
            Number of consecutive low rounds
        """
        count = 0
        for m in reversed(history):
            if m < 2.0:
                count += 1
            else:
                break
        return count

    def get_stats(self) -> Dict:
        """Get strategy statistics"""
        return {
            'confidence_threshold': self.confidence_threshold,
            'cold_streak_threshold': self.cold_streak_threshold,
            'classifiers_available': list(self.classifiers.keys()),
            'classifiers_trained': [target for target, clf in self.classifiers.items() if clf.is_trained]
        }
