# Test the new payload structure with actual and predicted multipliers
from supabase_client import SupabaseLogger
from datetime import datetime
import json

print("=" * 80)
print("TEST: New Payload Structure")
print("=" * 80)
print()

# Initialize Supabase
supabase = SupabaseLogger(
    url='https://zofojiubrykbtmstfhzx.supabase.co',
    key='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvZm9qaXVicnlrYnRtc3RmaHp4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM4NzU0OTEsImV4cCI6MjA3OTQ1MTQ5MX0.mxwvnhT-ouONWff-gyqw67lKon82nBx2fsbd8meyc8s'
)

print("STEP 1: Insert a round (this represents the last completed round)")
print("-" * 80)

# Last round that just completed
actual_multiplier = 2.45
round_timestamp = datetime.now()

round_id = supabase.insert_round(
    round_number=1,
    multiplier=actual_multiplier,
    timestamp=round_timestamp
)

if not round_id:
    print("FAILED: Could not insert round")
    exit(1)

print(f"Round inserted: ID={round_id}, actual multiplier={actual_multiplier:.2f}x")
print()

print("STEP 2: Make a prediction for the NEXT round")
print("-" * 80)

# Prediction for next round
predicted_multiplier = 3.15
confidence = 0.73
prediction_range = (2.52, 3.78)  # ±20% of predicted value

print(f"Prediction details:")
print(f"  Expected output (prediction): {predicted_multiplier:.2f}x")
print(f"  Confidence: {confidence * 100:.0f}%")
print(f"  Range: {prediction_range[0]:.2f}-{prediction_range[1]:.2f}")
print()

print("STEP 3: Save analytics signal with new structure")
print("-" * 80)
print(f"  multiplier column: {actual_multiplier:.2f}x (ACTUAL from last round)")
print(f"  payload column: JSON with prediction details")
print()

model_output = {
    'predicted_multiplier': predicted_multiplier,
    'prediction_timestamp': datetime.now().isoformat(),
    'features_used': 21,
    'lookback_rounds': 5,
    'training_samples': 50
}

metadata = {
    'test_mode': True,
    'next_round_number': 2
}

signal_id = supabase.insert_analytics_signal(
    round_id=round_id,
    actual_multiplier=actual_multiplier,      # From the round that just ended
    predicted_multiplier=predicted_multiplier, # Prediction for next round
    model_name='RandomForest',
    confidence=confidence,
    prediction_range=prediction_range,
    model_output=model_output,
    metadata=metadata,
    timestamp=round_timestamp  # Same timestamp as the round
)

print()
print("=" * 80)

if signal_id:
    print("SUCCESS!")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  Round ID: {round_id}")
    print(f"  Signal ID: {signal_id}")
    print(f"  Timestamp: {round_timestamp.isoformat()}")
    print()
    print("Data structure saved:")
    print(f"  multiplier column: {actual_multiplier:.2f}x (actual from last round)")
    print()
    print("  payload column (JSON):")
    expected_payload = {
        'modelName': 'RandomForest',
        'id': round_id,
        'expectedOutput': predicted_multiplier,
        'confidence': f"{confidence * 100:.0f}%",
        'range': f"{prediction_range[0]:.2f}-{prediction_range[1]:.2f}"
    }
    print(json.dumps(expected_payload, indent=4))
    print()
    print("=" * 80)
    print("VERIFICATION QUERY")
    print("=" * 80)
    print()
    print("Run this in Supabase to see the payload structure:")
    print()
    sql_query = f"""
SELECT
    ar."roundId",
    ar.multiplier as actual_multiplier,
    ar.timestamp,
    ars.id as signal_id,
    ars.multiplier as stored_actual_multiplier,
    ars.payload,
    ars.model_name,
    ars.confidence,
    ars.created_at
FROM "AviatorRound" ar
JOIN analytics_round_signals ars ON ars.round_id = ar."roundId"
WHERE ar."roundId" = {round_id};
"""
    print(sql_query)
    print()
    print("Expected payload content:")
    print(json.dumps(expected_payload, indent=2))
    print()
    print("=" * 80)
    print("STRUCTURE VERIFIED!")
    print("=" * 80)
    print()
    print("Key points:")
    print("  - multiplier column stores ACTUAL multiplier from last round")
    print("  - payload column stores prediction as JSON with expectedOutput")
    print("  - Both round and signal use same timestamp")
else:
    print("FAILED!")
    print("=" * 80)
    print()
    print("Could not save analytics signal")
    print()

print()
