"""
Betting Decision - Unified betting decision logic

Combines hybrid strategy with ensemble voting to make final betting recommendations.
"""

from typing import Dict, List


class BettingDecisionMaker:
    """
    Makes final betting decisions combining hybrid strategy and ensemble predictions.
    """

    def __init__(self, hybrid_strategy=None, ensemble_strategy=None):
        """
        Initialize betting decision maker.

        Args:
            hybrid_strategy: HybridBettingStrategy instance
            ensemble_strategy: EnsembleStrategy instance
        """
        self.hybrid_strategy = hybrid_strategy
        self.ensemble_strategy = ensemble_strategy

    def make_decision(self, hybrid_decision: Dict, ensemble_prediction: Dict,
                     all_predictions: Dict) -> Dict:
        """
        Make final betting decision combining all information.

        Args:
            hybrid_decision: Decision from hybrid strategy
            ensemble_prediction: Ensemble prediction
            all_predictions: All individual model predictions grouped

        Returns:
            Final betting recommendation with reasoning
        """
        # Primary: Use hybrid strategy decision
        if hybrid_decision['action'] == 'BET':
            return {
                'recommendation': 'BET',
                'primary_source': 'Hybrid Strategy',
                'position': hybrid_decision['position'],
                'target': hybrid_decision['target_multiplier'],
                'confidence': hybrid_decision['confidence'],
                'reason': hybrid_decision['reason'],
                'ensemble_agrees': ensemble_prediction['bet'] if ensemble_prediction else False
            }

        # Secondary: Check ensemble consensus
        if ensemble_prediction and ensemble_prediction['bet']:
            # High ensemble consensus without hybrid trigger
            if ensemble_prediction['confidence'] >= 0.7:
                return {
                    'recommendation': 'BET',
                    'primary_source': 'Ensemble Consensus',
                    'position': None,
                    'target': ensemble_prediction['predicted_multiplier'],
                    'confidence': ensemble_prediction['confidence'],
                    'reason': f"Strong ensemble consensus ({ensemble_prediction['bet_votes']} models)",
                    'ensemble_agrees': True
                }

        # Default: SKIP
        return {
            'recommendation': 'SKIP',
            'primary_source': 'None',
            'position': None,
            'target': None,
            'confidence': 0.0,
            'reason': 'No strong betting signal detected',
            'ensemble_agrees': False
        }

    def get_risk_assessment(self, hybrid_decision: Dict, ensemble_prediction: Dict) -> str:
        """
        Assess risk level of the betting decision.

        Returns:
            'LOW', 'MEDIUM', or 'HIGH'
        """
        if hybrid_decision['action'] == 'BET':
            if hybrid_decision['position'] == 1:
                # Position 1 is conservative
                if hybrid_decision['confidence'] >= 0.8:
                    return 'LOW'
                return 'MEDIUM'
            elif hybrid_decision['position'] == 2:
                # Position 2 is aggressive
                return 'HIGH'

        if ensemble_prediction and ensemble_prediction['bet']:
            if ensemble_prediction['confidence'] >= 0.75:
                return 'MEDIUM'
            return 'HIGH'

        return 'NONE'
