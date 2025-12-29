#!/usr/bin/env python3
"""Test signal parsing with new payload format"""
import json
from supabase_signal_listener import SupabaseSignalListener, ModelSignal
from supabase_client import SupabaseLogger

# Test payload (from user's example)
test_payload = {
    "roundId": 980,
    "actualMultiplier": 1.73,
    "models": [
        {
            "modelName": "Ensemble",
            "expectedOutput": 36519609.07172947,
            "confidence": "50%",
            "range": "29215687.26-43823530.89",
            "bet": False
        },
        {
            "modelName": "XGBoost",
            "expectedOutput": 703.795654296875,
            "confidence": "50%",
            "range": "563.04-844.55",
            "bet": False
        },
        {
            "modelName": "LightGBM",
            "expectedOutput": 1131.4195340962697,
            "confidence": "50%",
            "range": "905.14-1357.70",
            "bet": False
        },
        {
            "modelName": "PyTorch_MLP",
            "expectedOutput": 109556992.0,
            "confidence": "50%",
            "range": "87645593.60-131468390.40",
            "bet": False
        }
    ],
    "timestamp": "2025-12-29T10:54:09.064493"
}

# Create a mock row like from Supabase
test_row = {
    "round_id": 980,
    "actualMultiplier": 1.73,
    "payload": json.dumps(test_payload),
    "created_at": "2025-12-29T10:54:09"
}

# Create a simple listener class just for testing _parse_signal
class TestListener:
    def _parse_payload(self, payload_str):
        if isinstance(payload_str, str):
            return json.loads(payload_str)
        elif isinstance(payload_str, dict):
            return payload_str
        return {}

    def _log(self, msg, level="INFO"):
        print(f"[{level}] {msg}")

    def _parse_signal(self, row):
        """Parse database row into ModelSignal (supporting new payload format with models array)"""
        try:
            round_id = row.get('round_id', 0)
            actual_multiplier = row.get('actualMultiplier')
            payload_str = row.get('payload')
            created_at = row.get('created_at')

            # Parse payload
            payload = self._parse_payload(payload_str) if payload_str else {}

            # Look for XGBoost model in the models array
            models = payload.get('models', [])
            xgboost_model = None
            for model in models:
                if model.get('modelName') == 'XGBoost':
                    xgboost_model = model
                    break

            if not xgboost_model:
                self._log(f"XGBoost model not found in payload for round {round_id}", "DEBUG")
                return None

            # Extract XGBoost model data
            model_name = xgboost_model.get('modelName', 'XGBoost')
            expected_output = float(xgboost_model.get('expectedOutput', 0))
            confidence_str = xgboost_model.get('confidence', '0%')
            range_str = xgboost_model.get('range', '0-0')
            bet = xgboost_model.get('bet', False)

            # Parse confidence (handle "50%" format)
            if isinstance(confidence_str, str):
                confidence_str = confidence_str.rstrip('%')
                try:
                    confidence_pct = float(confidence_str)
                except ValueError:
                    confidence_pct = 0.0
            else:
                confidence_pct = float(confidence_str)

            # Parse range (e.g., "563.04-844.55")
            range_min, range_max = 0.0, 0.0
            if '-' in range_str:
                try:
                    min_str, max_str = range_str.split('-')
                    range_min = float(min_str.strip())
                    range_max = float(max_str.strip())
                except ValueError:
                    pass

            # Create signal
            signal = ModelSignal(
                round_id=round_id,
                model_name=model_name,
                confidence=confidence_pct,
                expected_output=expected_output,
                bet=bet,
                confidence_pct=confidence_pct,
                range_min=range_min,
                range_max=range_max,
                actual_multiplier=actual_multiplier,
                payload=payload,
                created_at=created_at
            )

            return signal if signal.is_valid() else None

        except (ValueError, TypeError, KeyError) as e:
            self._log(f"Error parsing signal: {e}", "WARNING")
            return None

# Test parsing
listener = TestListener()
signal = listener._parse_signal(test_row)

print("Signal Parsing Test")
print("=" * 60)
if signal:
    print("[PASS] Signal parsed successfully")
    print(f"  Round ID: {signal.round_id}")
    print(f"  Model: {signal.model_name}")
    print(f"  Expected Output: {signal.expected_output}")
    print(f"  Confidence: {signal.confidence_pct}%")
    print(f"  Bet Flag: {signal.bet}")
    print(f"  Range: {signal.range_min} - {signal.range_max}")
    print(f"  Valid: {signal.is_valid()}")
    print()
    print(f"Signal Summary: {signal}")
else:
    print("[FAIL] Failed to parse signal")

# Test with bet=true
print("\n" + "=" * 60)
print("Testing with bet=true")
print("=" * 60)
test_payload_with_bet = test_payload.copy()
test_payload_with_bet["models"][1]["bet"] = True  # XGBoost with bet=true

test_row_with_bet = {
    "round_id": 981,
    "actualMultiplier": 1.73,
    "payload": json.dumps(test_payload_with_bet),
    "created_at": "2025-12-29T10:54:10"
}

signal2 = listener._parse_signal(test_row_with_bet)
if signal2:
    print("[PASS] Signal parsed successfully")
    print(f"  Round ID: {signal2.round_id}")
    print(f"  Model: {signal2.model_name}")
    print(f"  Expected Output: {signal2.expected_output}")
    print(f"  Confidence: {signal2.confidence_pct}%")
    print(f"  Bet Flag: {signal2.bet}")
    print(f"  Should trade: {signal2.bet}")
    print()
    print(f"Signal Summary: {signal2}")
else:
    print("[FAIL] Failed to parse signal")
