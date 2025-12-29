"""
Advanced Multi-Model ML Prediction System

This module provides a comprehensive ML prediction system with:
- 25+ predictive models (5 legacy + 16 AutoML + 4 trained + 4 classifiers)
- Hybrid betting strategy (Position 1: ML classifiers + Position 2: Cold streak)
- Pattern detection (stepping stone, color-based, zone, time patterns)
- Ensemble voting and confidence-based predictions
"""

__version__ = "1.0.0"

from ml_system.prediction_engine import PredictionEngine
from ml_system.config import MLSystemConfig

__all__ = ['PredictionEngine', 'MLSystemConfig']
