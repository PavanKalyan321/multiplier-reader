"""
Azure AI Foundry Service Configuration
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')

# Service Configuration
SERVICE_NAME = "Azure AI Foundry Service"
SERVICE_VERSION = "1.0.0"
SERVICE_PORT = int(os.getenv('PORT', 8000))
SERVICE_WORKERS = int(os.getenv('WORKERS', 4))

# Model Configuration
ENABLE_PYCARET = os.getenv('ENABLE_PYCARET', 'true').lower() == 'true'
ENABLE_H2O = os.getenv('ENABLE_H2O', 'true').lower() == 'true'
ENABLE_AUTOSKLEARN = os.getenv('ENABLE_AUTOSKLEARN', 'true').lower() == 'true'
ENABLE_LSTM = os.getenv('ENABLE_LSTM', 'true').lower() == 'true'
ENABLE_AUTOGLUON = os.getenv('ENABLE_AUTOGLUON', 'true').lower() == 'true'

# Feature Flags
ENABLE_PATTERN_DETECTION = os.getenv('ENABLE_PATTERN_DETECTION', 'true').lower() == 'true'
ENABLE_STRATEGY_ENGINE = os.getenv('ENABLE_STRATEGY_ENGINE', 'true').lower() == 'true'
ENABLE_PARALLEL_EXECUTION = os.getenv('ENABLE_PARALLEL_EXECUTION', 'true').lower() == 'true'

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'

# Prediction Configuration
MIN_HISTORICAL_ROUNDS = int(os.getenv('MIN_HISTORICAL_ROUNDS', 5))
MAX_HISTORICAL_HOURS = int(os.getenv('MAX_HISTORICAL_HOURS', 24))
PREDICTION_TIMEOUT = int(os.getenv('PREDICTION_TIMEOUT', 30))

# Performance Configuration
MAX_WORKERS = int(os.getenv('MAX_WORKERS', 5))
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 60))

print("=" * 70)
print("Azure AI Foundry Service Configuration Loaded")
print(f"  Service: {SERVICE_NAME} v{SERVICE_VERSION}")
print(f"  Port: {SERVICE_PORT}")
print(f"  Workers: {SERVICE_WORKERS}")
print(f"  Supabase: {'Connected' if SUPABASE_URL else 'Not configured'}")
print(f"  Pattern Detection: {'Enabled' if ENABLE_PATTERN_DETECTION else 'Disabled'}")
print(f"  Strategy Engine: {'Enabled' if ENABLE_STRATEGY_ENGINE else 'Disabled'}")
print("=" * 70)
