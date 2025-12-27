# Test script to insert prediction into analytics_round_signals table
from supabase_client import SupabaseLogger
from datetime import datetime

print("=" * 80)
print("TEST: Insert Prediction into analytics_round_signals Table")
print("=" * 80)
print()

# Initialize Supabase
supabase = SupabaseLogger(
    url='https://zofojiubrykbtmstfhzx.supabase.co',
    key='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvZm9qaXVicnlrYnRtc3RmaHp4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM4NzU0OTEsImV4cCI6MjA3OTQ1MTQ5MX0.mxwvnhT-ouONWff-gyqw67lKon82nBx2fsbd8meyc8s'
)

print()
print("STEP 1: Insert a test round first")
print("-" * 80)
print()

# Insert a test round to get a round_id
test_multiplier = 2.89
round_id = supabase.insert_round(
    round_number=1,
    multiplier=test_multiplier,
    timestamp=datetime.now()
)

if not round_id:
    print("FAILED: Could not insert round. Cannot proceed with prediction test.")
    exit(1)

print()
print("STEP 2: Insert prediction linked to that round")
print("-" * 80)
print()

# Prepare prediction data
predicted_multiplier = 3.45
model_name = "RandomForest"
confidence = 0.725

model_output = {
    'predicted_multiplier': predicted_multiplier,
    'prediction_timestamp': datetime.now().isoformat(),
    'features_used': 21,
    'lookback_rounds': 10,
    'training_samples': 100
}

metadata = {
    'test_mode': True,
    'next_round_number': 2,
    'algorithm': 'RandomForest',
    'n_estimators': 100
}

print(f"Prediction details:")
print(f"  Round ID (link): {round_id}")
print(f"  Predicted Multiplier: {predicted_multiplier}x")
print(f"  Model: {model_name}")
print(f"  Confidence: {confidence * 100:.1f}%")
print()

# Insert prediction
signal_id = supabase.insert_analytics_signal(
    round_id=round_id,
    multiplier=predicted_multiplier,
    model_name=model_name,
    model_output=model_output,
    confidence=confidence,
    metadata=metadata
)

print()
print("=" * 80)

if signal_id:
    print("SUCCESS!")
    print("=" * 80)
    print()
    print(f"Prediction inserted successfully!")
    print(f"Signal ID: {signal_id}")
    print()
    print("=" * 80)
    print("VERIFICATION QUERIES")
    print("=" * 80)
    print()
    print("1. View the round:")
    print(f"   SELECT * FROM \"AviatorRound\" WHERE \"roundId\" = {round_id};")
    print()
    print("2. View the prediction:")
    print(f"   SELECT * FROM analytics_round_signals WHERE id = {signal_id};")
    print()
    print("3. View them joined together:")
    print(f"""
   SELECT
       ar."roundId",
       ar.multiplier as actual_multiplier,
       ars.multiplier as predicted_multiplier,
       ars.confidence,
       ars.model_name,
       ar.timestamp
   FROM "AviatorRound" ar
   JOIN analytics_round_signals ars ON ars.round_id = ar."roundId"
   WHERE ar."roundId" = {round_id};
""")
    print()
    print("4. View the full prediction details (JSON):")
    print(f"""
   SELECT
       id,
       round_id,
       model_name,
       model_output,
       confidence,
       metadata,
       created_at
   FROM analytics_round_signals
   WHERE id = {signal_id};
""")
    print()
    print("=" * 80)
    print("BOTH API CALLS WORKING!")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  [API Call 1] Round saved with ID: {round_id}")
    print(f"  [API Call 2] Prediction saved with ID: {signal_id}")
    print()
else:
    print("FAILED!")
    print("=" * 80)
    print()
    print("The prediction insert did not succeed.")
    print("Check the error message above for details.")
    print()
    print("Common issues:")
    print("  1. Table 'analytics_round_signals' doesn't exist")
    print("  2. Constraint violation (unique index on round_id + model_name)")
    print("  3. RLS (Row Level Security) blocking inserts")
    print()

print("=" * 80)
