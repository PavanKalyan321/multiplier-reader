"""
Pattern Detector - Base class for all pattern detection

Provides common interface for detecting patterns in crash multiplier history.
"""

from abc import ABC, abstractmethod
from typing import List, Dict


class PatternDetector(ABC):
    """
    Abstract base class for pattern detection.

    All pattern detectors must implement:
    - detect(): Detect patterns in historical data
    - get_pattern_features(): Extract pattern-based features for ML
    """

    def __init__(self, name: str):
        """
        Initialize pattern detector.

        Args:
            name: Name of the pattern detector
        """
        self.name = name
        self.patterns_detected = []

    @abstractmethod
    def detect(self, history: List[Dict]) -> List[Dict]:
        """
        Detect patterns in historical data.

        Args:
            history: List of round data dicts with 'crash_multiplier', 'duration', 'timestamp'

        Returns:
            List of detected pattern dictionaries with:
            - type: Pattern type identifier
            - confidence: Confidence score (0.0-1.0)
            - description: Human-readable description
            - position: Optional position in history where pattern was detected
        """
        pass

    def get_pattern_features(self, history: List[Dict]) -> Dict[str, float]:
        """
        Extract pattern-based features for ML models.

        Args:
            history: Historical round data

        Returns:
            Dictionary of pattern features
        """
        patterns = self.detect(history)

        if not patterns:
            return {f'{self.name}_detected': 0.0, f'{self.name}_confidence': 0.0}

        # Return most confident pattern
        max_confidence_pattern = max(patterns, key=lambda p: p.get('confidence', 0))

        return {
            f'{self.name}_detected': 1.0,
            f'{self.name}_confidence': max_confidence_pattern.get('confidence', 0.0),
            f'{self.name}_type': hash(max_confidence_pattern.get('type', '')) % 100  # Simple numeric encoding
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
