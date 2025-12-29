"""
ML System Configuration

Centralized configuration for all ML system settings.
"""


class MLSystemConfig:
    """Central configuration for advanced ML system"""

    # ===== Model Groups =====
    ENABLE_LEGACY_MODELS = True          # 5 existing models
    ENABLE_AUTOML_MODELS = True          # 16 simulated AutoML models
    ENABLE_TRAINED_MODELS = True         # 4 real trained models
    ENABLE_BINARY_CLASSIFIERS = True     # 4 binary classifiers

    # ===== Feature Settings =====
    NUM_FEATURES = 21                    # Number of base features
    USE_FEATURE_ADAPTER = True           # Enable 21→50 feature expansion for trained models

    # ===== Prediction Settings =====
    LOOKBACK_WINDOW = 10                 # Number of rounds to look back for features
    MIN_ROUNDS_FOR_PREDICTION = 5        # Minimum rounds before making predictions
    HISTORY_SIZE = 1000                  # Maximum rounds to keep in history

    # ===== Betting Strategy =====
    HYBRID_CONFIDENCE_THRESHOLD = 0.75   # Confidence required for Position 1 (ML classifiers)
    COLD_STREAK_THRESHOLD = 8            # Low rounds required for Position 2
    INDIVIDUAL_MODEL_BET_THRESHOLD = 0.6 # Confidence threshold for individual model betting

    # ===== Pattern Detection =====
    ENABLE_PATTERN_DETECTION = True      # Enable pattern detection systems
    STEPPING_STONE_THRESHOLD = 0.362     # Probability for stepping stone pattern
    ENABLE_COLOR_DETECTION = True        # Enable color-based pattern detection
    ENABLE_ZONE_DETECTION = True         # Enable zone detection
    ENABLE_TIME_PATTERNS = True          # Enable time-based patterns

    # ===== Performance =====
    ENABLE_PARALLEL_PREDICTIONS = False  # Enable multiprocessing for predictions
    MAX_PREDICTION_TIME_MS = 100         # Maximum time allowed for prediction

    # ===== Database =====
    MAX_PAYLOAD_SIZE_KB = 50             # Maximum payload size for database
    COMPRESS_PAYLOAD = False             # Enable payload compression

    # ===== Logging =====
    VERBOSE_LOGGING = True               # Enable detailed logging
    LOG_INDIVIDUAL_PREDICTIONS = False   # Log each model's prediction separately

    # ===== Training =====
    RETRAIN_INTERVAL = 10                # Retrain models every N rounds
    ENABLE_ONLINE_LEARNING = False       # Enable incremental learning (future feature)

    @classmethod
    def get_config_summary(cls) -> dict:
        """Get summary of current configuration"""
        return {
            'models': {
                'legacy': cls.ENABLE_LEGACY_MODELS,
                'automl': cls.ENABLE_AUTOML_MODELS,
                'trained': cls.ENABLE_TRAINED_MODELS,
                'classifiers': cls.ENABLE_BINARY_CLASSIFIERS
            },
            'features': {
                'num_features': cls.NUM_FEATURES,
                'use_adapter': cls.USE_FEATURE_ADAPTER
            },
            'prediction': {
                'lookback': cls.LOOKBACK_WINDOW,
                'min_rounds': cls.MIN_ROUNDS_FOR_PREDICTION
            },
            'strategy': {
                'hybrid_threshold': cls.HYBRID_CONFIDENCE_THRESHOLD,
                'cold_streak': cls.COLD_STREAK_THRESHOLD
            },
            'patterns': {
                'enabled': cls.ENABLE_PATTERN_DETECTION,
                'stepping_stone': cls.STEPPING_STONE_THRESHOLD
            }
        }
