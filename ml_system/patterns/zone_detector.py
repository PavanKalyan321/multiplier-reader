"""
Zone Detector - Detects market zones

Zones: CRASH_ZONE, HIGH_ZONE, OSCILLATING, MIXED
"""

import numpy as np
from typing import List, Dict

from ml_system.patterns.pattern_detector import PatternDetector


class ZoneDetector(PatternDetector):
    """
    Detects the current market zone based on recent multiplier distribution.

    Zones:
    - CRASH_ZONE: Most multipliers < 2.0x (high crash rate)
    - HIGH_ZONE: Most multipliers > 3.0x (high value phase)
    - OSCILLATING: High variance (unpredictable)
    - MIXED: No clear pattern (normal operation)
    """

    def __init__(self):
        super().__init__('zone')

    def detect(self, history: List[Dict]) -> List[Dict]:
        """Detect current market zone"""
        if len(history) < 10:
            return []

        recent = [r['crash_multiplier'] for r in history[-10:]]
        avg = np.mean(recent)
        std = np.std(recent)

        # CRASH_ZONE: 70%+ values < 2.0
        crash_ratio = sum(1 for m in recent if m < 2.0) / len(recent)
        if crash_ratio > 0.7:
            return [{
                'type': 'CRASH_ZONE',
                'confidence': min(0.9, 0.6 + crash_ratio * 0.3),
                'description': f'{crash_ratio*100:.0f}% of recent rounds crashed early',
                'crash_ratio': crash_ratio
            }]

        # HIGH_ZONE: 70%+ values > 3.0
        high_ratio = sum(1 for m in recent if m > 3.0) / len(recent)
        if high_ratio > 0.7:
            return [{
                'type': 'HIGH_ZONE',
                'confidence': min(0.9, 0.6 + high_ratio * 0.3),
                'description': f'{high_ratio*100:.0f}% of recent rounds were high',
                'high_ratio': high_ratio
            }]

        # OSCILLATING: High volatility (std > 50% of mean)
        if std > avg * 0.5:
            return [{
                'type': 'OSCILLATING',
                'confidence': 0.7,
                'description': 'High volatility detected',
                'volatility': std / avg
            }]

        # MIXED: Default zone
        return [{
            'type': 'MIXED',
            'confidence': 0.5,
            'description': 'Normal mixed pattern',
            'avg': avg,
            'std': std
        }]
