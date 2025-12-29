"""
Time Patterns - Detects time-based patterns

Analyzes patterns based on time intervals and round positions.
"""

import numpy as np
from typing import List, Dict
from datetime import datetime

from ml_system.patterns.pattern_detector import PatternDetector


class TimePatternDetector(PatternDetector):
    """
    Detects time-based patterns in crash multipliers.

    Analyzes:
    - Round position patterns (e.g., every 5th round)
    - Time interval patterns (e.g., 15s, 30s, 45s, 60s)
    - Hour-based patterns
    """

    def __init__(self):
        super().__init__('time_pattern')
        # Observed high-probability minute marks (from research)
        self.high_probability_minutes = [2, 6, 12, 14, 18, 20, 21]

    def detect(self, history: List[Dict]) -> List[Dict]:
        """Detect time-based patterns"""
        if len(history) < 5:
            return []

        patterns = []

        # Check time interval patterns
        if len(history) >= 3:
            timestamps = [r['timestamp'] for r in history[-10:]]
            intervals = np.diff(timestamps)

            # Check for regular intervals
            avg_interval = np.mean(intervals)
            std_interval = np.std(intervals)

            if std_interval < avg_interval * 0.2:  # Low variance = regular
                patterns.append({
                    'type': 'REGULAR_INTERVALS',
                    'confidence': 0.6,
                    'description': f'Regular intervals detected: {avg_interval:.1f}s avg',
                    'avg_interval': avg_interval
                })

        # Check current time for high-probability patterns
        if len(history) > 0:
            current_time = datetime.fromtimestamp(history[-1]['timestamp'])
            current_minute = current_time.minute

            if current_minute in self.high_probability_minutes:
                patterns.append({
                    'type': 'HIGH_PROBABILITY_TIME',
                    'confidence': 0.55,
                    'description': f'Minute {current_minute} has historically high success rate',
                    'minute': current_minute
                })

        # Round position patterns (every Nth round)
        round_count = len(history)
        if round_count % 5 == 0:
            patterns.append({
                'type': 'ROUND_POSITION',
                'confidence': 0.5,
                'description': f'Round position multiple of 5 (round {round_count})',
                'position': round_count
            })

        return patterns if patterns else [{
            'type': 'NO_TIME_PATTERN',
            'confidence': 0.3,
            'description': 'No significant time patterns detected'
        }]
