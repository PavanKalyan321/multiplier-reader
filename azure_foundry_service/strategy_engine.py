"""
Strategy Engine
Pattern detection and strategy recommendation for game analysis
"""

import numpy as np
from typing import List, Dict
from datetime import datetime


class StrategyEngine:
    """Detects game patterns and recommends strategies"""

    PATTERNS = {
        'CRASH_PRONE': {
            'detection': lambda hist: sum(1 for m in hist if m < 1.5) / len(hist) > 0.4,
            'strategy': 'conservative',
            'description': 'Many crashes detected - play safe',
            'bet_threshold': 0.75
        },
        'HIGH_VOLATILITY': {
            'detection': lambda hist: np.std(hist) > 1.0 if len(hist) > 1 else False,
            'strategy': 'aggressive',
            'description': 'High volatility - aggressive opportunities',
            'bet_threshold': 0.80
        },
        'UPTREND': {
            'detection': lambda hist: np.mean(hist[-10:]) > np.mean(hist[-20:-10]) if len(hist) > 20 else False,
            'strategy': 'moderate',
            'description': 'Uptrend detected - increase bets',
            'bet_threshold': 0.65
        },
        'DOWNTREND': {
            'detection': lambda hist: np.mean(hist[-10:]) < np.mean(hist[-20:-10]) if len(hist) > 20 else False,
            'strategy': 'conservative',
            'description': 'Downtrend detected - reduce bets',
            'bet_threshold': 0.75
        },
        'STABLE': {
            'detection': lambda hist: np.std(hist) < 0.5 if len(hist) > 1 else True,
            'strategy': 'moderate',
            'description': 'Stable market - balanced play',
            'bet_threshold': 0.70
        }
    }

    # Model-specific confidence adjustments
    MODEL_ADJUSTMENTS = {
        'PyCaret': {'confidence_boost': 0.05, 'reliability': 'high'},
        'LSTM_Model': {'confidence_boost': 0.03, 'reliability': 'high'},
        'RandomForest_AutoML': {'confidence_boost': 0.02, 'reliability': 'medium'},
        'XGBoost_AutoML': {'confidence_boost': 0.02, 'reliability': 'medium'},
        'LightGBM_AutoML': {'confidence_boost': 0.01, 'reliability': 'medium'},
        'H2O_AutoML': {'confidence_boost': 0.02, 'reliability': 'medium'},
        'AutoGluon': {'confidence_boost': 0.01, 'reliability': 'medium'},
        'CatBoost': {'confidence_boost': 0.01, 'reliability': 'medium'},
        'AutoSklearn': {'confidence_boost': 0.01, 'reliability': 'low'},
        'MLP_NeuralNet': {'confidence_boost': 0.0, 'reliability': 'low'},
        'TPOT_Genetic': {'confidence_boost': 0.0, 'reliability': 'low'},
        'AutoKeras': {'confidence_boost': 0.0, 'reliability': 'low'},
        'AutoPyTorch': {'confidence_boost': 0.0, 'reliability': 'low'},
        'MLBox': {'confidence_boost': 0.0, 'reliability': 'low'},
        'TransmogrifAI': {'confidence_boost': 0.0, 'reliability': 'low'}
    }

    def __init__(self):
        """Initialize strategy engine"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] INFO: Strategy Engine initialized with {len(self.PATTERNS)} patterns")

    def detect_pattern(self, multipliers: List[float]) -> str:
        """
        Detect dominant pattern in historical data

        Args:
            multipliers: List of historical multiplier values

        Returns:
            Pattern name (CRASH_PRONE, HIGH_VOLATILITY, UPTREND, DOWNTREND, STABLE)
        """
        if not multipliers or len(multipliers) < 2:
            return 'STABLE'

        # Check patterns in order of specificity
        for pattern_name in ['CRASH_PRONE', 'HIGH_VOLATILITY', 'UPTREND', 'DOWNTREND']:
            config = self.PATTERNS[pattern_name]
            try:
                if config['detection'](multipliers):
                    return pattern_name
            except Exception:
                continue

        return 'STABLE'

    def get_strategy_for_model(self, model_name: str, pattern: str,
                              predicted_mult: float) -> Dict:
        """
        Determine strategy parameters for specific model in specific pattern

        Args:
            model_name: Name of the model
            pattern: Detected pattern
            predicted_mult: Model's predicted multiplier

        Returns:
            Dict with strategy, bet_threshold, and confidence adjustments
        """
        pattern_config = self.PATTERNS.get(pattern, self.PATTERNS['STABLE'])
        model_adj = self.MODEL_ADJUSTMENTS.get(model_name, {'confidence_boost': 0.0, 'reliability': 'low'})

        return {
            'strategy': pattern_config['strategy'],
            'bet_threshold': pattern_config['bet_threshold'],
            'confidence_boost': model_adj['confidence_boost'],
            'model_reliability': model_adj['reliability'],
            'pattern': pattern,
            'pattern_description': pattern_config['description']
        }

    def analyze_pattern(self, multipliers: List[float]) -> Dict:
        """
        Comprehensive analysis of historical data patterns

        Args:
            multipliers: Historical multiplier data

        Returns:
            Dict with detailed pattern analysis
        """
        if not multipliers:
            return {
                'pattern': 'STABLE',
                'statistics': {},
                'recommendations': []
            }

        pattern = self.detect_pattern(multipliers)
        pattern_config = self.PATTERNS[pattern]

        # Calculate statistics
        stats = {
            'mean': float(np.mean(multipliers)),
            'std': float(np.std(multipliers)),
            'min': float(np.min(multipliers)),
            'max': float(np.max(multipliers)),
            'median': float(np.median(multipliers)),
            'crash_count': sum(1 for m in multipliers if m < 1.5),
            'total_rounds': len(multipliers),
            'crash_ratio': sum(1 for m in multipliers if m < 1.5) / len(multipliers) if multipliers else 0
        }

        return {
            'pattern': pattern,
            'strategy': pattern_config['strategy'],
            'description': pattern_config['description'],
            'statistics': stats,
            'recommendations': self._generate_recommendations(pattern, stats)
        }

    def _generate_recommendations(self, pattern: str, stats: Dict) -> List[str]:
        """Generate trading recommendations based on pattern and statistics"""
        recommendations = []

        if pattern == 'CRASH_PRONE':
            recommendations.append('Use conservative strategy - target lower multipliers (1.2-1.5x)')
            recommendations.append(f'Crash ratio is {stats["crash_ratio"]:.0%} - play cautiously')
            recommendations.append('Cashout early to avoid losses')

        elif pattern == 'HIGH_VOLATILITY':
            recommendations.append('Use aggressive strategy - larger bets possible')
            recommendations.append(f'Standard deviation is {stats["std"]:.2f} - high variance market')
            recommendations.append('Target medium-high multipliers (1.8-3.0x)')

        elif pattern == 'UPTREND':
            recommendations.append('Uptrend detected - increase bet sizes gradually')
            recommendations.append(f'Recent average exceeds historical - trend is positive')
            recommendations.append('Target moderate multipliers (1.5-2.5x)')

        elif pattern == 'DOWNTREND':
            recommendations.append('Downtrend detected - reduce bet sizes')
            recommendations.append(f'Recent performance declining - be cautious')
            recommendations.append('Target lower multipliers (1.2-1.8x)')

        else:  # STABLE
            recommendations.append('Market is stable - consistent multipliers expected')
            recommendations.append(f'Mean multiplier: {stats["mean"]:.1f}x - reliable target')
            recommendations.append('Use moderate strategy with steady bet sizing')

        return recommendations

    def should_place_bet(self, model_confidence: float, pattern: str,
                        predicted_multiplier: float) -> bool:
        """
        Determine if a bet should be placed based on confidence and pattern

        Args:
            model_confidence: Model's confidence score (0-1)
            pattern: Detected pattern
            predicted_multiplier: Model's prediction

        Returns:
            True if bet should be placed
        """
        pattern_config = self.PATTERNS.get(pattern, self.PATTERNS['STABLE'])
        threshold = pattern_config['bet_threshold']

        # Additional checks
        if predicted_multiplier < 1.0:
            return False

        return model_confidence >= threshold
