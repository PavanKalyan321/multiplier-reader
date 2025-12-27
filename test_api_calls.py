# Test script to verify both API calls work
from supabase_client import SupabaseLogger
from datetime import datetime
import time

print("=" * 80)
print("TESTING SUPABASE API CALLS")
print("=" * 80)
print()

# Initialize Supabase client
supabase = SupabaseLogger(
    url='https://zofojiubrykbtmstfhzx.supabase.co',
    key='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvZm9qaXVicnlrYnRtc3RmaHp4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM4NzU0OTEsImV4cCI6MjA3OTQ1MTQ5MX0.mxwvnhT-ouONWff-gyqw67lKon82nBx2fsbd8meyc8s'
)

print()
print("-" * 80)
print("TEST 1: Insert Round into AviatorRound table")
print("-" * 80)

# Test API Call 1: Insert round
test_multiplier = 2.45
test_timestamp = datetime.now()

print(f"Attempting to insert:")
print(f"  - Multiplier: {test_multiplier}x")
print(f"  - Timestamp: {test_timestamp}")
print()

round_id = supabase.insert_round(
    round_number=1,
    multiplier=test_multiplier,
    timestamp=test_timestamp
)

if round_id:
    print()
    print(f"✅ SUCCESS! Round inserted with ID: {round_id}")
    print()

    # Wait a moment
    time.sleep(1)

    print("-" * 80)
    print("TEST 2: Insert Analytics Signal into analytics_round_signals table")
    print("-" * 80)

    # Test API Call 2: Insert analytics signal
    predicted_multiplier = 3.21

    print(f"Attempting to insert prediction:")
    print(f"  - Round ID (link): {round_id}")
    print(f"  - Predicted Multiplier: {predicted_multiplier}x")
    print(f"  - Model: RandomForest")
    print(f"  - Confidence: 67.5%")
    print()

    model_output = {
        'predicted_multiplier': predicted_multiplier,
        'prediction_timestamp': datetime.now().isoformat(),
        'features_used': 21
    }

    metadata = {
        'test_run': True,
        'next_round_number': 2
    }

    signal_id = supabase.insert_analytics_signal(
        round_id=round_id,
        multiplier=predicted_multiplier,
        model_name='RandomForest',
        model_output=model_output,
        confidence=0.675,
        metadata=metadata
    )

    if signal_id:
        print()
        print(f"✅ SUCCESS! Analytics signal inserted with ID: {signal_id}")
        print()
        print("=" * 80)
        print("BOTH API CALLS SUCCESSFUL!")
        print("=" * 80)
        print()
        print("Verify in Supabase:")
        print()
        print("-- Check the round:")
        print(f"SELECT * FROM \"AviatorRound\" WHERE \"roundId\" = {round_id};")
        print()
        print("-- Check the prediction:")
        print(f"SELECT * FROM analytics_round_signals WHERE id = {signal_id};")
        print()
        print("-- See them joined:")
        print(f"""
SELECT
    ar."roundId",
    ar.multiplier as actual,
    ars.multiplier as predicted,
    ars.confidence,
    ar.timestamp
FROM "AviatorRound" ar
JOIN analytics_round_signals ars ON ars.round_id = ar."roundId"
WHERE ar."roundId" = {round_id};
""")
    else:
        print()
        print("❌ FAILED! Analytics signal not inserted")
        print("Check the error message above")
else:
    print()
    print("❌ FAILED! Round not inserted")
    print("Check the error message above")
    print()
    print("Common issues:")
    print("1. Trigger function 'analytics_generate_round_signal' has errors")
    print("2. RLS (Row Level Security) is blocking inserts")
    print("3. Table doesn't exist or has wrong schema")
    print()
    print("Try running:")
    print("ALTER TABLE \"AviatorRound\" DISABLE TRIGGER after_insert_analytics_generate;")

print()
print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)
