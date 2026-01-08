"""Quick validation test for betting rules engine"""

import sys
import os

print("=" * 80)
print("BETTING RULES ENGINE - VALIDATION TEST")
print("=" * 80)

# Test 1: Import rules engine
print("\n[1/5] Testing imports...")
try:
    from betting_rules_engine import BettingRulesEngine
    print("[OK] BettingRulesEngine imported successfully")
except ImportError as e:
    print(f"[FAIL] Import failed: {e}")
    sys.exit(1)

# Test 2: Check config file exists
print("\n[2/5] Checking configuration file...")
config_path = os.path.join(os.path.dirname(__file__), "betting_rules_config.json")
if os.path.exists(config_path):
    print(f"[OK] Config file found: {config_path}")
else:
    print(f"[FAIL] Config file not found: {config_path}")
    sys.exit(1)

# Test 3: Initialize rules engine
print("\n[3/5] Initializing rules engine...")
try:
    engine = BettingRulesEngine(config_path)
    print("[OK] Rules engine initialized successfully")
except Exception as e:
    print(f"[FAIL] Initialization failed: {e}")
    sys.exit(1)

# Test 4: Test regime detection
print("\n[4/5] Testing regime detection...")
try:
    test_mults = [1.5, 1.2, 2.1, 1.8, 2.3, 1.4, 2.5, 1.9, 2.2, 2.0]
    regime_result = engine.regime_detector.detect_regime(test_mults)
    print(f"[OK] Regime detected: {regime_result.regime}")
    print(f"   - Median: {regime_result.features.median:.2f}x")
    print(f"   - Confidence: {regime_result.confidence:.0%}")
except Exception as e:
    print(f"[FAIL] Regime detection failed: {e}")
    sys.exit(1)

# Test 5: Test entry filter
print("\n[5/5] Testing entry filter...")
try:
    # Simulate adding historical data
    from betting_rules_engine.historical_data import RoundData
    engine.historical_cache.add_round(RoundData(1, 2.5))
    engine.historical_cache.add_round(RoundData(2, 2.1))
    engine.historical_cache.add_round(RoundData(3, 1.8))

    entry_approved, reason = engine.evaluate_entry(2.3, 0.85)
    print(f"[OK] Entry filter evaluated")
    print(f"   - Approved: {entry_approved}")
    print(f"   - Reason: {reason}")
except Exception as e:
    print(f"[FAIL] Entry filter failed: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("ALL TESTS PASSED!")
print("=" * 80)
print("\nBetting Rules Engine is ready for use!")
print("Start the bot with: python main.py")
print("Select Option 7 for Model Signal Listener")
