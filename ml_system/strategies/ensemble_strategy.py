"""
Ensemble Strategy - Weighted ensemble voting across all models

Combines predictions from multiple models using confidence-weighted averaging
and majority voting for betting decisions.
"""

import numpy as np
from typing import List, Dict
from datetime import datetime


class EnsembleStrategy:
    """
    Ensemble prediction strategy using weighted averaging.

    Combines predictions from all models by:
    - Weighted average (by confidence) for predicted multiplier
    - Average confidence across all models
    - Majority voting for betting decision
    """

    def __init__(self, models: List = None):
        """
        Initialize ensemble strategy.

        Args:
            models: List of BasePredictor instances (optional)
        """
        self.models = models or []

    def get_ensemble_prediction(self, predictions: List[Dict]) -> Dict:
        """
        Combine predictions from all models using confidence weighting.

        Args:
            predictions: List of prediction dictionaries from individual models

        Returns:
            Ensemble prediction dictionary with:
            - weighted_prediction: Confidence-weighted average
            - ensemble_confidence: Average confidence
            - bet: Majority vote
            - num_models: Number of models
            - bet_votes: Voting breakdown
        """
        if not predictions or len(predictions) == 0:
            return None

        # Extract values
        multipliers = [p['predicted_multiplier'] for p in predictions]
        confidences = [p['confidence'] for p in predictions]

        # Weighted average prediction
        total_weight = sum(confidences)
        if total_weight == 0:
            weighted_prediction = np.mean(multipliers)
        else:
            weighted_prediction = sum(
                p['predicted_multiplier'] * p['confidence']
                for p in predictions
            ) / total_weight

        # Ensemble confidence (average of all)
        ensemble_confidence = float(np.mean(confidences))

        # Ensemble range (±20%)
        range_margin = weighted_prediction * 0.2
        ensemble_range = (
            max(1.0, weighted_prediction - range_margin),
            weighted_prediction + range_margin
        )

        # Ensemble betting decision: majority vote
        bet_votes = sum(1 for p in predictions if p.get('bet', False))
        ensemble_bet = bet_votes > len(predictions) / 2

        return {
            'model_name': 'Ensemble',
            'predicted_multiplier': float(weighted_prediction),
            'confidence': float(ensemble_confidence),
            'range': ensemble_range,
            'bet': ensemble_bet,
            'num_models': len(predictions),
            'bet_votes': f"{bet_votes}/{len(predictions)}",
            'timestamp': datetime.now().isoformat()
        }

    def get_group_ensemble(self, predictions: List[Dict], group_name: str) -> Dict:
        """
        Get ensemble prediction for a specific model group.

        Args:
            predictions: List of predictions from a single group
            group_name: Name of the group (e.g., 'legacy', 'automl')

        Returns:
            Group ensemble prediction
        """
        if not predictions:
            return None

        ensemble = self.get_ensemble_prediction(predictions)
        if ensemble:
            ensemble['model_name'] = f'{group_name.capitalize()}_Ensemble'
            ensemble['group'] = group_name

        return ensemble
