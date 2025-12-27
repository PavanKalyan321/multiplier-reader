# Test that both AviatorRound and analytics_round_signals use the same timestamp
from supabase_client import SupabaseLogger
from datetime import datetime

print("=" * 80)
print("TEST: Same Timestamp for Round and Analytics Signal")
print("=" * 80)
print()

# Initialize Supabase
supabase = SupabaseLogger(
    url='https://zofojiubrykbtmstfhzx.supabase.co',
    key='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvZm9qaXVicnlrYnRtc3RmaHp4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM4NzU0OTEsImV4cCI6MjA3OTQ1MTQ5MX0.mxwvnhT-ouONWff-gyqw67lKon82nBx2fsbd8meyc8s'
)

print("STEP 1: Create a specific timestamp")
print("-" * 80)

# Create a specific timestamp to use for both inserts
test_timestamp = datetime.now()
print(f"Using timestamp: {test_timestamp.isoformat()}")
print()

print("STEP 2: Insert round with this timestamp")
print("-" * 80)

# Insert round with the specific timestamp
test_multiplier = 3.15
round_id = supabase.insert_round(
    round_number=1,
    multiplier=test_multiplier,
    timestamp=test_timestamp
)

if not round_id:
    print("FAILED: Could not insert round.")
    exit(1)

print()
print("STEP 3: Insert analytics signal with THE SAME timestamp")
print("-" * 80)

# Prepare prediction data
predicted_multiplier = 3.67
model_name = "RandomForest"
confidence = 0.781

model_output = {
    'predicted_multiplier': predicted_multiplier,
    'prediction_timestamp': test_timestamp.isoformat(),
    'features_used': 21,
    'lookback_rounds': 5,
    'training_samples': 5
}

metadata = {
    'test_mode': True,
    'next_round_number': 2,
    'algorithm': 'RandomForest'
}

print(f"Inserting prediction with SAME timestamp: {test_timestamp.isoformat()}")
print()

# Insert analytics signal with the SAME timestamp
signal_id = supabase.insert_analytics_signal(
    round_id=round_id,
    multiplier=predicted_multiplier,
    model_name=model_name,
    model_output=model_output,
    confidence=confidence,
    metadata=metadata,
    timestamp=test_timestamp  # THIS IS THE KEY - Using same timestamp
)

print()
print("=" * 80)

if signal_id:
    print("SUCCESS!")
    print("=" * 80)
    print()
    print(f"Round ID: {round_id}")
    print(f"Signal ID: {signal_id}")
    print(f"Shared Timestamp: {test_timestamp.isoformat()}")
    print()
    print("=" * 80)
    print("VERIFICATION QUERY")
    print("=" * 80)
    print()
    print("Run this in Supabase to verify both use the same timestamp:")
    print()
    sql_query = f"""
SELECT
    ar."roundId",
    ar.multiplier as actual_multiplier,
    ar.timestamp as round_timestamp,
    ars.id as signal_id,
    ars.multiplier as predicted_multiplier,
    ars.created_at as signal_timestamp,
    -- Check if timestamps match
    CASE
        WHEN ar.timestamp = ars.created_at THEN 'MATCH'
        ELSE 'DIFFERENT'
    END as timestamp_match
FROM "AviatorRound" ar
JOIN analytics_round_signals ars ON ars.round_id = ar."roundId"
WHERE ar."roundId" = {round_id};
"""
    print(sql_query)
    print()
    print("Expected result:")
    print(f"  timestamp_match: MATCH")
    print()
    print("=" * 80)
    print("BOTH TIMESTAMPS SHOULD BE IDENTICAL!")
    print("=" * 80)
else:
    print("FAILED!")
    print("=" * 80)
    print()
    print("Could not insert analytics signal.")
    print()

print()
