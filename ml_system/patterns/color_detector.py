"""
Color Detector - Classifies multipliers by color categories

Colors: RED (<1.2x), AMBER (1.2-1.6x), YELLOW (1.6-2.0x), GREEN (2.0-3.5x), PURPLE (≥3.5x)
"""

from typing import List, Dict

from ml_system.patterns.pattern_detector import PatternDetector


class ColorDetector(PatternDetector):
    """
    Detects color-based patterns in multiplier history.

    Color ranges:
    - RED: 1.0-1.2x (crash zone)
    - AMBER: 1.2-1.6x (low)
    - YELLOW: 1.6-2.0x (medium-low)
    - GREEN: 2.0-3.5x (medium-high)
    - PURPLE: 3.5x+ (high)
    """

    COLOR_RANGES = {
        'RED': (1.0, 1.2),
        'AMBER': (1.2, 1.6),
        'YELLOW': (1.6, 2.0),
        'GREEN': (2.0, 3.5),
        'PURPLE': (3.5, float('inf'))
    }

    def __init__(self):
        super().__init__('color')

    def classify_multiplier(self, multiplier: float) -> str:
        """
        Classify a single multiplier by color.

        Args:
            multiplier: Crash multiplier value

        Returns:
            Color name (RED, AMBER, YELLOW, GREEN, PURPLE)
        """
        for color, (low, high) in self.COLOR_RANGES.items():
            if low <= multiplier < high:
                return color
        return 'PURPLE'  # Default for very high values

    def detect(self, history: List[Dict]) -> List[Dict]:
        """Detect color-based patterns"""
        if len(history) < 5:
            return []

        patterns = []
        recent = history[-5:]
        colors = [self.classify_multiplier(r['crash_multiplier']) for r in recent]

        # Detect color streaks
        if all(c == 'RED' for c in colors):
            patterns.append({
                'type': 'RED_STREAK',
                'confidence': 0.7,
                'description': '5 consecutive RED (crash zone) multipliers',
                'current_color': 'RED'
            })

        if all(c in ['RED', 'AMBER'] for c in colors):
            patterns.append({
                'type': 'LOW_STREAK',
                'confidence': 0.65,
                'description': '5 consecutive low multipliers (RED/AMBER)',
                'current_color': colors[-1]
            })

        if all(c in ['GREEN', 'PURPLE'] for c in colors):
            patterns.append({
                'type': 'HIGH_STREAK',
                'confidence': 0.8,
                'description': '5 consecutive high multipliers (GREEN/PURPLE)',
                'current_color': colors[-1]
            })

        # Detect alternating pattern
        if len(set(colors)) >= 4:
            patterns.append({
                'type': 'MIXED_COLORS',
                'confidence': 0.5,
                'description': 'High color variation in last 5 rounds',
                'current_color': colors[-1]
            })

        # Always return current color
        if not patterns:
            patterns.append({
                'type': 'CURRENT_COLOR',
                'confidence': 0.6,
                'description': f'Current color: {colors[-1]}',
                'current_color': colors[-1]
            })

        return patterns
