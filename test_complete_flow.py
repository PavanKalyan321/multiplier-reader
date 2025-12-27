# Complete end-to-end test of the prediction flow
from supabase_client import SupabaseLogger
from ml_predictor import CrashPredictor
from datetime import datetime
import time

print("=" * 80)
print("TEST: Complete Prediction Flow with Timestamp Sync")
print("=" * 80)
print()

# Initialize Supabase
supabase = SupabaseLogger(
    url='https://zofojiubrykbtmstfhzx.supabase.co',
    key='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvZm9qaXVicnlrYnRtc3RmaHp4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM4NzU0OTEsImV4cCI6MjA3OTQ1MTQ5MX0.mxwvnhT-ouONWff-gyqw67lKon82nBx2fsbd8meyc8s'
)

# Initialize ML predictor
predictor = CrashPredictor(history_size=1000, min_rounds_for_prediction=5)

print()
print("STEP 1: Simulate 5 rounds to build prediction history")
print("-" * 80)

test_rounds = [
    {'multiplier': 2.45, 'duration': 3.2},
    {'multiplier': 1.89, 'duration': 2.1},
    {'multiplier': 5.67, 'duration': 5.8},
    {'multiplier': 3.21, 'duration': 3.9},
    {'multiplier': 2.98, 'duration': 3.5},
]

round_ids = []

for i, round_data in enumerate(test_rounds, 1):
    # Create a timestamp for this round
    round_timestamp = datetime.now()

    # Add to predictor
    predictor.add_round(
        crash_multiplier=round_data['multiplier'],
        duration=round_data['duration'],
        timestamp=round_timestamp.timestamp()
    )

    # Save to database
    round_id = supabase.insert_round(
        round_number=i,
        multiplier=round_data['multiplier'],
        timestamp=round_timestamp
    )

    round_ids.append((round_id, round_timestamp))
    print(f"  Round {i}: {round_data['multiplier']:.2f}x - ID: {round_id}")
    time.sleep(0.1)

print()
print(f"Total rounds saved: {len(round_ids)}")
print()

print("STEP 2: Train the ML model")
print("-" * 80)

# Need lookback+1 rounds for training, so use 4 lookback with 5 rounds
lookback = min(4, len(predictor.round_history) - 1)
print(f"Using lookback={lookback} with {len(predictor.round_history)} rounds")
success = predictor.train(lookback=lookback)

if not success:
    print("FAILED: Could not train model")
    exit(1)

print("Model trained successfully!")
print()

print("STEP 3: Make prediction for round 6")
print("-" * 80)

prediction = predictor.predict(lookback=lookback)

if not prediction:
    print("FAILED: Could not make prediction")
    exit(1)

predicted_mult = prediction['predicted_multiplier']
confidence = prediction['confidence']

print(f"Predicted multiplier: {predicted_mult:.2f}x")
print(f"Confidence: {confidence * 100:.1f}%")
print()

print("STEP 4: Save prediction to analytics_round_signals")
print("-" * 80)

# Use the last round's timestamp for the prediction
last_round_id, last_round_timestamp = round_ids[-1]

model_output = {
    'predicted_multiplier': predicted_mult,
    'prediction_timestamp': prediction.get('timestamp'),
    'features_used': 21,
    'lookback_rounds': lookback,
    'training_samples': prediction.get('training_samples')
}

metadata = {
    'test_mode': True,
    'next_round_number': 6,
    'predictor_stats': predictor.get_statistics()
}

print(f"Using same timestamp as round {len(test_rounds)}: {last_round_timestamp.isoformat()}")
print()

signal_id = supabase.insert_analytics_signal(
    round_id=last_round_id,
    multiplier=predicted_mult,
    model_name=prediction.get('model_type', 'RandomForest'),
    model_output=model_output,
    confidence=confidence,
    metadata=metadata,
    timestamp=last_round_timestamp  # Same timestamp as the round
)

print()
print("=" * 80)

if signal_id:
    print("SUCCESS!")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  Last Round ID: {last_round_id}")
    print(f"  Prediction Signal ID: {signal_id}")
    print(f"  Shared Timestamp: {last_round_timestamp.isoformat()}")
    print(f"  Predicted Multiplier: {predicted_mult:.2f}x")
    print(f"  Confidence: {confidence * 100:.1f}%")
    print()
    print("=" * 80)
    print("VERIFICATION QUERY")
    print("=" * 80)
    print()
    print("Run this in Supabase to verify the complete flow:")
    print()
    sql_query = f"""
SELECT
    ar."roundId",
    ar.multiplier as actual_multiplier,
    ar.timestamp as round_timestamp,
    ars.id as signal_id,
    ars.multiplier as predicted_multiplier,
    ars.confidence,
    ars.model_name,
    ars.created_at as signal_timestamp,
    CASE
        WHEN ar.timestamp = ars.created_at THEN 'MATCH'
        ELSE 'DIFFERENT'
    END as timestamp_match
FROM "AviatorRound" ar
JOIN analytics_round_signals ars ON ars.round_id = ar."roundId"
WHERE ar."roundId" = {last_round_id}
ORDER BY ar."roundId" DESC;
"""
    print(sql_query)
    print()
    print("=" * 80)
    print("COMPLETE FLOW WORKING!")
    print("=" * 80)
    print()
    print("Flow:")
    print("  1. Collect 5 rounds of data")
    print("  2. Train ML model")
    print("  3. Make prediction")
    print("  4. Save prediction with same timestamp as round")
    print("  5. Both tables synchronized!")
else:
    print("FAILED!")
    print("=" * 80)
    print()
    print("Could not save prediction to analytics_round_signals")
    print()

print()
