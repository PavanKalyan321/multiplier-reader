# Test complete multi-round flow with new payload structure
from supabase_client import SupabaseLogger
from ml_predictor import CrashPredictor
from datetime import datetime
import time
import json

print("=" * 80)
print("TEST: Multi-Round Flow with New Payload Structure")
print("=" * 80)
print()

# Initialize
supabase = SupabaseLogger(
    url='https://zofojiubrykbtmstfhzx.supabase.co',
    key='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvZm9qaXVicnlrYnRtc3RmaHp4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM4NzU0OTEsImV4cCI6MjA3OTQ1MTQ5MX0.mxwvnhT-ouONWff-gyqw67lKon82nBx2fsbd8meyc8s'
)

predictor = CrashPredictor(history_size=1000, min_rounds_for_prediction=5)

test_rounds = [
    {'multiplier': 2.45, 'duration': 3.2},
    {'multiplier': 1.89, 'duration': 2.1},
    {'multiplier': 5.67, 'duration': 5.8},
    {'multiplier': 3.21, 'duration': 3.9},
    {'multiplier': 2.98, 'duration': 3.5},
    {'multiplier': 4.12, 'duration': 4.5},
]

print("SIMULATING 6 ROUNDS WITH PREDICTIONS")
print("=" * 80)
print()

saved_data = []

for i, round_data in enumerate(test_rounds, 1):
    print(f"Round {i}: {round_data['multiplier']:.2f}x")
    print("-" * 80)

    # Create timestamp for this round
    round_timestamp = datetime.now()

    # Add to predictor history
    predictor.add_round(
        crash_multiplier=round_data['multiplier'],
        duration=round_data['duration'],
        timestamp=round_timestamp.timestamp()
    )

    # Save round to database
    round_id = supabase.insert_round(
        round_number=i,
        multiplier=round_data['multiplier'],
        timestamp=round_timestamp
    )

    if not round_id:
        print("FAILED to save round")
        continue

    # After 5 rounds, start making predictions
    if i >= 5:
        print(f"  Making prediction for round {i+1}...")

        # Train model if not trained
        if not predictor.is_trained:
            lookback = min(4, len(predictor.round_history) - 1)
            if predictor.train(lookback=lookback):
                print(f"  Model trained with lookback={lookback}")

        # Make prediction
        lookback = min(4, len(predictor.round_history) - 1)
        prediction = predictor.predict(lookback=lookback)

        if prediction:
            predicted_mult = prediction['predicted_multiplier']
            confidence = prediction['confidence']

            # Calculate range (±20%)
            range_margin = predicted_mult * 0.2
            prediction_range = (
                max(1.0, predicted_mult - range_margin),
                predicted_mult + range_margin
            )

            print(f"  Prediction: {predicted_mult:.2f}x (confidence: {confidence*100:.0f}%)")
            print(f"  Range: {prediction_range[0]:.2f}-{prediction_range[1]:.2f}")

            # Save analytics signal
            model_output = {
                'predicted_multiplier': predicted_mult,
                'features_used': 21,
                'lookback_rounds': lookback
            }

            signal_id = supabase.insert_analytics_signal(
                round_id=round_id,
                actual_multiplier=round_data['multiplier'],  # Actual from this round
                predicted_multiplier=predicted_mult,          # Prediction for next
                model_name='RandomForest',
                confidence=confidence,
                prediction_range=prediction_range,
                model_output=model_output,
                timestamp=round_timestamp
            )

            if signal_id:
                saved_data.append({
                    'round': i,
                    'round_id': round_id,
                    'signal_id': signal_id,
                    'actual': round_data['multiplier'],
                    'predicted': predicted_mult,
                    'confidence': confidence,
                    'range': prediction_range
                })
                print(f"  Analytics signal saved: ID={signal_id}")

    print()
    time.sleep(0.1)

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()

if saved_data:
    print(f"Total predictions saved: {len(saved_data)}")
    print()

    print("Predictions made:")
    print()
    for data in saved_data:
        print(f"Round {data['round']}:")
        print(f"  Round ID: {data['round_id']}")
        print(f"  Signal ID: {data['signal_id']}")
        print(f"  Actual multiplier: {data['actual']:.2f}x")
        print(f"  Predicted for next: {data['predicted']:.2f}x")
        print(f"  Confidence: {data['confidence']*100:.0f}%")
        print(f"  Range: {data['range'][0]:.2f}-{data['range'][1]:.2f}")
        print()

    print("=" * 80)
    print("VERIFICATION QUERY")
    print("=" * 80)
    print()
    print("Run this to see all predictions with payload structure:")
    print()

    round_ids = [d['round_id'] for d in saved_data]
    round_ids_str = ','.join(map(str, round_ids))

    sql = f"""
SELECT
    ar."roundId",
    ar.multiplier as actual_multiplier,
    ars.id as signal_id,
    ars.multiplier as stored_actual,
    ars.payload::json->>'expectedOutput' as predicted_next,
    ars.payload::json->>'confidence' as confidence,
    ars.payload::json->>'range' as prediction_range,
    ars.payload as full_payload
FROM "AviatorRound" ar
JOIN analytics_round_signals ars ON ars.round_id = ar."roundId"
WHERE ar."roundId" IN ({round_ids_str})
ORDER BY ar."roundId" ASC;
"""
    print(sql)
    print()

    print("=" * 80)
    print("SUCCESS! Complete multi-round flow working!")
    print("=" * 80)
    print()
    print("Each entry has:")
    print("  - multiplier: ACTUAL from that round")
    print("  - payload: JSON with prediction for NEXT round")
    print("  - Same timestamp for round and analytics signal")
else:
    print("No predictions were saved (need at least 5 rounds)")

print()
