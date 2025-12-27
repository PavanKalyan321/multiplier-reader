# Test that predictions start after 5 rounds
from ml_predictor import CrashPredictor
import time

print("=" * 80)
print("TEST: ML Predictions Start After 5 Rounds")
print("=" * 80)
print()

# Create predictor with 5 round minimum
predictor = CrashPredictor(history_size=1000, min_rounds_for_prediction=5)

print(f"Predictor initialized")
print(f"Minimum rounds needed: {predictor.min_rounds_for_prediction}")
print()

# Simulate 5 rounds
test_rounds = [
    {'multiplier': 2.45, 'duration': 3.2},
    {'multiplier': 1.89, 'duration': 2.1},
    {'multiplier': 5.67, 'duration': 5.8},
    {'multiplier': 3.21, 'duration': 3.9},
    {'multiplier': 2.98, 'duration': 3.5},
]

print("Adding 5 rounds of test data...")
print("-" * 80)

for i, round_data in enumerate(test_rounds, 1):
    timestamp = time.time()
    predictor.add_round(
        crash_multiplier=round_data['multiplier'],
        duration=round_data['duration'],
        timestamp=timestamp
    )
    print(f"Round {i}: {round_data['multiplier']:.2f}x (duration: {round_data['duration']:.1f}s)")
    time.sleep(0.1)

print()
print(f"Total rounds in history: {len(predictor.round_history)}")
print()

# Try to train
print("-" * 80)
print("Training model with 5 rounds...")
print("-" * 80)

success = predictor.train(lookback=5)

if success:
    print()
    print("SUCCESS! Model trained with only 5 rounds")
    print()

    # Make a prediction
    print("-" * 80)
    print("Making prediction for round 6...")
    print("-" * 80)

    prediction = predictor.predict(lookback=5)

    if prediction:
        print()
        print(f"PREDICTION:")
        print(f"  Predicted Multiplier: {prediction['predicted_multiplier']:.2f}x")
        print(f"  Confidence: {prediction['confidence'] * 100:.1f}%")
        print(f"  Model: {prediction['model_type']}")
        print(f"  Training Samples: {prediction['training_samples']}")
        print()
        print("=" * 80)
        print("SUCCESS! Predictions work after just 5 rounds")
        print("=" * 80)
    else:
        print("FAILED: Could not make prediction")
else:
    print("FAILED: Could not train model")

print()
print("Summary:")
print(f"  Minimum rounds required: 5")
print(f"  Rounds collected: {len(predictor.round_history)}")
print(f"  Model trained: {predictor.is_trained}")
print(f"  Predictions made: {predictor.predictions_made}")
print()
