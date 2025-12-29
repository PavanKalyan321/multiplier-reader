"""
Signal Validator Module - ML Signal Generation & Validation

Handles:
1. Signal generation for Position 1 and Position 2
2. ML ensemble voting and consensus calculation
3. Confidence thresholding
4. Risk level assessment
"""

import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional


class SignalGenerator:
    """Generates ML signals for specific positions"""

    def __init__(self, prediction_engine, feature_engineer):
        """
        Initialize signal generator

        Args:
            prediction_engine: PredictionEngine instance with predict() method
            feature_engineer: FeatureEngineer instance with extract_features() method
        """
        self.prediction_engine = prediction_engine
        self.feature_engineer = feature_engineer
        self.model_names = [
            'logistic_regression',
            'random_forest',
            'gradient_boosting',
            'decision_tree',
            'naive_bayes'
        ]

    def generate_signal(self, game_history: List[float], position: int = 1) -> Dict:
        """
        Generate ML signal for specific position

        Args:
            game_history: List of recent multiplier values
            position: Position 1 or 2 (determines target multiplier)

        Returns:
            Dict with signal, confidence, model votes, ensemble agreement
        """
        try:
            # Extract features from history
            features = self.feature_engineer.extract_features(game_history)

            # Get ensemble prediction
            prediction = self.prediction_engine.predict(features)

            # Extract individual model votes
            model_votes = self._get_model_votes(prediction)

            # Determine prediction direction
            prediction_dir = 'HIGH' if prediction.get('prediction') == 1 else 'LOW'
            confidence = prediction.get('confidence', 0.5)

            # Calculate ensemble agreement
            ensemble_agreement = self._calculate_ensemble_agreement(model_votes)

            signal_decision = {
                'position': position,
                'prediction': prediction_dir,
                'confidence': confidence,
                'model_votes': model_votes,
                'ensemble_agreement': ensemble_agreement,
                'target_multiplier': 1.5 if position == 1 else 2.0,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'features': features
            }

            return signal_decision

        except Exception as e:
            print(f"Error generating signal: {e}")
            return {
                'position': position,
                'prediction': 'NEUTRAL',
                'confidence': 0.0,
                'model_votes': {},
                'ensemble_agreement': 0.0,
                'error': str(e),
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

    def _get_model_votes(self, prediction: Dict) -> Dict:
        """
        Extract individual model predictions from ensemble

        Args:
            prediction: Prediction dict from prediction_engine.predict()

        Returns:
            Dict mapping model names to their individual predictions
        """
        model_votes = {}

        # Try to extract from prediction dict
        if 'model_predictions' in prediction:
            return prediction['model_predictions']

        # Fallback: all models vote same as ensemble
        direction = 'HIGH' if prediction.get('prediction') == 1 else 'LOW'
        for model_name in self.model_names:
            model_votes[model_name] = direction

        return model_votes

    def _calculate_ensemble_agreement(self, model_votes: Dict) -> float:
        """
        Calculate agreement percentage among models

        Args:
            model_votes: Dict of model votes

        Returns:
            Float (0.0-1.0) representing agreement level
        """
        if not model_votes:
            return 0.0

        votes = list(model_votes.values())
        high_votes = sum(1 for v in votes if v == 'HIGH')
        low_votes = sum(1 for v in votes if v == 'LOW')

        max_agreement = max(high_votes, low_votes)
        return max_agreement / len(votes) if votes else 0.0


class EnsembleValidator:
    """Validates signals meet confidence and consensus thresholds"""

    def __init__(self, min_confidence: float = 0.70, min_consensus: float = 0.50):
        """
        Initialize validator with thresholds

        Args:
            min_confidence: Minimum confidence required (0.0-1.0)
            min_consensus: Minimum consensus among models (0.0-1.0)
        """
        self.min_confidence = min_confidence
        self.min_consensus = min_consensus

    def validate_signal(self, signal_decision: Dict,
                       strategy: str = 'conservative') -> Dict:
        """
        Validate signal meets thresholds

        Args:
            signal_decision: Signal dict from SignalGenerator
            strategy: 'conservative' (strict), 'moderate' (medium), 'aggressive' (loose)

        Returns:
            Dict with validation results
        """
        # Set thresholds based on strategy
        conf_threshold = {
            'conservative': 0.75,
            'moderate': 0.70,
            'aggressive': 0.60
        }.get(strategy, 0.70)

        cons_threshold = {
            'conservative': 0.60,
            'moderate': 0.50,
            'aggressive': 0.40
        }.get(strategy, 0.50)

        # Check confidence
        confidence = signal_decision.get('confidence', 0.0)
        confidence_ok = confidence >= conf_threshold

        # Check consensus
        agreement = signal_decision.get('ensemble_agreement', 0.0)
        consensus_ok = agreement >= cons_threshold

        # Check neutral prediction
        prediction = signal_decision.get('prediction', 'NEUTRAL')
        is_neutral = prediction == 'NEUTRAL'

        # Overall validation
        validation_passed = confidence_ok and consensus_ok and not is_neutral

        validation_result = {
            'valid': validation_passed,
            'position': signal_decision.get('position'),
            'prediction': prediction,
            'confidence': confidence,
            'confidence_ok': confidence_ok,
            'confidence_threshold': conf_threshold,
            'ensemble_agreement': agreement,
            'consensus_ok': consensus_ok,
            'consensus_threshold': cons_threshold,
            'strategy': strategy,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'failure_reason': self._get_failure_reason(
                confidence_ok, consensus_ok, is_neutral,
                confidence, agreement
            )
        }

        return validation_result

    def _get_failure_reason(self, confidence_ok: bool, consensus_ok: bool,
                           is_neutral: bool, confidence: float,
                           agreement: float) -> Optional[str]:
        """Determine why validation failed"""
        if is_neutral:
            return 'neutral_prediction'
        if not confidence_ok:
            return f'low_confidence_{confidence:.2f}'
        if not consensus_ok:
            return f'low_consensus_{agreement:.2f}'
        return None

    def assess_risk_level(self, signal_decision: Dict) -> str:
        """
        Classify signal risk level based on confidence and agreement

        Args:
            signal_decision: Signal dict

        Returns:
            Risk level string: 'LOW', 'MODERATE', or 'HIGH'
        """
        confidence = signal_decision.get('confidence', 0.0)
        agreement = signal_decision.get('ensemble_agreement', 0.0)

        avg_score = (confidence + agreement) / 2

        if avg_score >= 0.75:
            return 'LOW'  # High confidence = low risk
        elif avg_score >= 0.60:
            return 'MODERATE'
        else:
            return 'HIGH'  # Low confidence = high risk

    def assess_win_probability(self, signal_decision: Dict) -> float:
        """
        Estimate win probability based on signal strength

        Args:
            signal_decision: Signal dict

        Returns:
            Estimated win probability (0.0-1.0)
        """
        confidence = signal_decision.get('confidence', 0.5)
        agreement = signal_decision.get('ensemble_agreement', 0.5)

        # Combine confidence and agreement
        estimated_prob = (confidence * 0.6) + (agreement * 0.4)

        return estimated_prob


class PositionDecisionEngine:
    """Makes position-specific betting decisions"""

    def __init__(self, cold_streak_threshold: int = 8,
                 burst_threshold: float = 5.0):
        """
        Initialize position decision engine

        Args:
            cold_streak_threshold: Number of low rounds to trigger position 2
            burst_threshold: Multiplier value that indicates burst pattern
        """
        self.cold_streak_threshold = cold_streak_threshold
        self.burst_threshold = burst_threshold

    def position_1_decision(self, signal_decision: Dict,
                           validation_result: Dict) -> Tuple[bool, str]:
        """
        Decision for position 1 (conservative, targets 1.5x)

        Args:
            signal_decision: Generated signal
            validation_result: Validation results

        Returns:
            Tuple of (should_bet: bool, reason: str)
        """
        if not validation_result['valid']:
            return False, f"signal_invalid: {validation_result['failure_reason']}"

        confidence = signal_decision.get('confidence', 0.0)
        if confidence < 0.75:
            return False, f"confidence_too_low: {confidence:.2f} < 0.75"

        return True, "accepted"

    def position_2_decision(self, signal_decision: Dict,
                           game_history: List[float],
                           last_10_multipliers: List[float]) -> Tuple[bool, str]:
        """
        Decision for position 2 (rule-based cold streak detection)

        Uses conservative rule: needs 8+ low rounds in last 10 AND no recent burst

        Args:
            signal_decision: Generated signal
            game_history: Full game history
            last_10_multipliers: Last 10 multipliers

        Returns:
            Tuple of (should_bet: bool, reason: str)
        """
        if not last_10_multipliers or len(last_10_multipliers) < 10:
            return False, "insufficient_history"

        # Count low rounds (< 2.0x)
        low_count = sum(1 for m in last_10_multipliers if m < 2.0)

        # Check for recent burst (>= 5.0x)
        has_recent_burst = any(m >= self.burst_threshold
                              for m in last_10_multipliers)

        if has_recent_burst:
            return False, "recent_burst_detected"

        if low_count < self.cold_streak_threshold:
            return False, f"cold_streak_low: {low_count} < {self.cold_streak_threshold}"

        confidence = min(0.75, 0.45 + (low_count * 0.05))
        return True, f"accepted_cold_streak_{low_count}"

    def get_stake_for_position(self, position: int,
                              base_stake: float,
                              multiplier: float = 1.5) -> float:
        """
        Calculate stake for specific position

        Args:
            position: Position 1 or 2
            base_stake: Base stake amount
            multiplier: Stake multiplier for position 2

        Returns:
            Stake amount
        """
        if position == 1:
            return base_stake
        else:  # position 2
            return base_stake * multiplier


class SignalValidationOrchestrator:
    """Orchestrates signal generation and validation"""

    def __init__(self, signal_generator: SignalGenerator,
                 ensemble_validator: EnsembleValidator,
                 position_decision_engine: PositionDecisionEngine):
        """Initialize orchestrator"""
        self.signal_gen = signal_generator
        self.validator = ensemble_validator
        self.position_engine = position_decision_engine

    def validate_and_decide(self, game_history: List[float],
                           strategy: str = 'moderate') -> Dict:
        """
        Complete signal validation and position decision

        Args:
            game_history: List of recent multipliers
            strategy: Validation strategy

        Returns:
            Dict with complete validation decision
        """
        # Generate signals for both positions
        signal_pos1 = self.signal_gen.generate_signal(game_history, position=1)
        signal_pos2 = self.signal_gen.generate_signal(game_history, position=2)

        # Validate signals
        valid_pos1 = self.validator.validate_signal(signal_pos1, strategy)
        valid_pos2 = self.validator.validate_signal(signal_pos2, strategy)

        # Position-specific decisions
        pos1_decision, pos1_reason = self.position_engine.position_1_decision(
            signal_pos1, valid_pos1
        )

        pos2_decision, pos2_reason = self.position_engine.position_2_decision(
            signal_pos2, game_history, game_history[-10:] if len(game_history) >= 10 else game_history
        )

        # Risk assessment
        risk_pos1 = self.validator.assess_risk_level(signal_pos1)
        risk_pos2 = self.validator.assess_risk_level(signal_pos2)

        result = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'position_1': {
                'signal': signal_pos1.get('prediction'),
                'confidence': signal_pos1.get('confidence'),
                'valid': valid_pos1['valid'],
                'should_bet': pos1_decision,
                'reason': pos1_reason,
                'risk_level': risk_pos1,
                'win_probability': self.validator.assess_win_probability(signal_pos1),
                'full_signal': signal_pos1,
                'full_validation': valid_pos1
            },
            'position_2': {
                'signal': signal_pos2.get('prediction'),
                'confidence': signal_pos2.get('confidence'),
                'valid': valid_pos2['valid'],
                'should_bet': pos2_decision,
                'reason': pos2_reason,
                'risk_level': risk_pos2,
                'win_probability': self.validator.assess_win_probability(signal_pos2),
                'full_signal': signal_pos2,
                'full_validation': valid_pos2
            },
            'decision': {
                'any_position_valid': pos1_decision or pos2_decision,
                'both_positions_valid': pos1_decision and pos2_decision,
                'recommended_position': 1 if pos1_decision else (2 if pos2_decision else None)
            }
        }

        return result
