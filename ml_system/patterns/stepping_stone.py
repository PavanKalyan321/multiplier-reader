"""
Stepping Stone Pattern - Detects consecutive high multiplier patterns

Research finding: 36.2% probability of consecutive high multipliers after a high round.
"""

import numpy as np
from typing import List, Dict

from ml_system.patterns.pattern_detector import PatternDetector


class SteppingStoneDetector(PatternDetector):
    """
    Detects stepping stone pattern where high multipliers tend to follow each other.

    Key insight: After a high multiplier (≥2.5x), there's a 36.2% chance
    the next multiplier will also be high.
    """

    def __init__(self, high_threshold: float = 2.5, confidence_base: float = 0.362):
        """
        Initialize stepping stone detector.

        Args:
            high_threshold: Minimum multiplier considered "high" (default 2.5x)
            confidence_base: Base confidence for pattern (default 0.362 = 36.2%)
        """
        super().__init__('stepping_stone')
        self.high_threshold = high_threshold
        self.confidence_base = confidence_base

    def detect(self, history: List[Dict]) -> List[Dict]:
        """Detect stepping stone patterns in history"""
        if len(history) < 3:
            return []

        patterns = []
        multipliers = [r['crash_multiplier'] for r in history[-10:]]

        # Count recent high multipliers
        high_count = sum(1 for m in multipliers if m >= self.high_threshold)

        # Check if last round was high
        if multipliers[-1] >= self.high_threshold:
            # Calculate average spacing between high multipliers
            high_positions = [i for i, m in enumerate(multipliers) if m >= self.high_threshold]

            if len(high_positions) >= 2:
                spacings = np.diff(high_positions)
                avg_spacing = np.mean(spacings)

                # Adjust confidence based on spacing pattern
                confidence = self.confidence_base
                if avg_spacing <= 2:
                    confidence *= 1.2  # Boost for close spacing
                confidence = min(0.8, confidence)  # Cap at 80%

                patterns.append({
                    'type': 'STEPPING_STONE',
                    'confidence': confidence,
                    'description': f'Last round was high ({multipliers[-1]:.2f}x), {self.confidence_base*100:.1f}% chance of consecutive high',
                    'position': len(multipliers) - 1,
                    'high_count': high_count,
                    'avg_spacing': avg_spacing
                })

        # Detect multiple consecutive highs
        consecutive = 0
        for m in reversed(multipliers):
            if m >= self.high_threshold:
                consecutive += 1
            else:
                break

        if consecutive >= 2:
            # Strong stepping stone pattern
            confidence = min(0.75, self.confidence_base * (1 + consecutive * 0.15))
            patterns.append({
                'type': 'CONSECUTIVE_HIGH',
                'confidence': confidence,
                'description': f'{consecutive} consecutive high multipliers detected',
                'position': len(multipliers) - consecutive,
                'consecutive_count': consecutive
            })

        return patterns
