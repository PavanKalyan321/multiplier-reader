#!/usr/bin/env python
"""Test script for the advanced ML system with simulated rounds"""

import time
from datetime import datetime
from ml_system.prediction_engine import PredictionEngine

def main():
    print("=" * 100)
    print("TESTING ADVANCED ML SYSTEM")
    print("=" * 100)
    print()

    # Initialize prediction engine
    print("Step 1: Initializing PredictionEngine...")
    engine = PredictionEngine(history_size=1000, min_rounds_for_prediction=5)
    print(f"[OK] Engine initialized with {engine.min_rounds_for_prediction} min rounds required\n")

    # Simulate some rounds
    print("Step 2: Simulating 10 rounds...")
    test_rounds = [
        (5.10, 20.17),  # multiplier, duration
        (2.82, 15.32),
        (1.45, 8.21),
        (7.23, 28.45),
        (3.67, 18.90),
        (1.89, 10.12),
        (4.56, 22.34),
        (2.34, 14.56),
        (6.78, 26.89),
        (3.21, 16.78)
    ]

    current_time = time.time()
    for i, (multiplier, duration) in enumerate(test_rounds, 1):
        engine.add_round(
            crash_multiplier=multiplier,
            duration=duration,
            timestamp=current_time + (i * 30)  # 30 seconds apart
        )
        print(f"  Round {i}: {multiplier:.2f}x (duration: {duration:.2f}s)")

    print(f"\n[OK] Added {len(test_rounds)} rounds to history\n")

    # Train the model
    print("Step 3: Training models...")
    if engine.train(lookback=5):
        print("[OK] All models trained successfully\n")
    else:
        print("[ERROR] Training failed\n")
        return 1

    # Make a prediction
    print("Step 4: Making predictions for next round...")
    result = engine.predict_all(lookback=5)

    if not result:
        print("[ERROR] Prediction failed\n")
        return 1

    print("[OK] Prediction complete!\n")

    # Display results
    print("=" * 100)
    print("PREDICTION RESULTS")
    print("=" * 100)

    ensemble = result['ensemble']
    hybrid = result['hybrid_strategy']
    all_predictions = result['all_predictions']
    patterns = result['patterns']

    # Display detailed table of ALL model predictions
    print("\n" + "=" * 120)
    print("ALL MODEL PREDICTIONS - DETAILED VIEW")
    print("=" * 120)
    print(f"{'Model Name':<30} {'Prediction':<12} {'Confidence':<12} {'Range':<20} {'Bet':<8}")
    print("-" * 120)

    # Legacy Models
    if all_predictions.get('legacy'):
        print("\n[LEGACY MODELS]")
        for model in all_predictions['legacy']:
            name = model.get('model_name', 'Unknown')
            pred = model.get('predicted_multiplier', 0)
            conf = model.get('confidence', 0) * 100
            range_min, range_max = model.get('range', (0, 0))
            bet = "YES" if model.get('bet', False) else "NO"
            print(f"{name:<30} {pred:>6.2f}x      {conf:>5.0f}%        {range_min:>5.2f}x - {range_max:<5.2f}x   {bet:<8}")

    # AutoML Models
    if all_predictions.get('automl'):
        print("\n[AUTOML MODELS]")
        for model in all_predictions['automl']:
            name = model.get('model_name', 'Unknown')
            pred = model.get('predicted_multiplier', 0)
            conf = model.get('confidence', 0) * 100
            range_min, range_max = model.get('range', (0, 0))
            bet = "YES" if model.get('bet', False) else "NO"
            print(f"{name:<30} {pred:>6.2f}x      {conf:>5.0f}%        {range_min:>5.2f}x - {range_max:<5.2f}x   {bet:<8}")

    # Trained Models
    if all_predictions.get('trained'):
        print("\n[TRAINED MODELS]")
        for model in all_predictions['trained']:
            name = model.get('model_name', 'Unknown')
            pred = model.get('predicted_multiplier', 0)
            conf = model.get('confidence', 0) * 100
            range_min, range_max = model.get('range', (0, 0))
            bet = "YES" if model.get('bet', False) else "NO"
            print(f"{name:<30} {pred:>6.2f}x      {conf:>5.0f}%        {range_min:>5.2f}x - {range_max:<5.2f}x   {bet:<8}")

    # Binary Classifiers
    if all_predictions.get('classifiers'):
        print("\n[BINARY CLASSIFIERS]")
        for model in all_predictions['classifiers']:
            name = model.get('model_name', 'Unknown')
            target = model.get('target', 0)
            prob = model.get('probability', model.get('confidence', 0)) * 100
            bet = "YES" if model.get('bet', False) else "NO"
            # Classifiers predict probability, not multiplier
            print(f"{name:<30} Target:{target:.1f}x   Prob: {prob:>5.0f}%        N/A                  {bet:<8}")

    print("=" * 120)

    # Ensemble Summary
    print(f"\n[ENSEMBLE PREDICTION]")
    print(f"  Predicted Multiplier: {ensemble['predicted_multiplier']:.2f}x")
    print(f"  Confidence: {ensemble['confidence'] * 100:.0f}%")
    print(f"  Range: {ensemble['range'][0]:.2f}x - {ensemble['range'][1]:.2f}x")
    print(f"  Bet Consensus: {ensemble['bet_votes']}/{len([m for group in all_predictions.values() for m in group])} models recommend BET")

    # Hybrid Strategy
    print(f"\n[HYBRID BETTING STRATEGY]")
    print(f"  Action: {hybrid['action']}")
    if hybrid['action'] == 'BET':
        print(f"  Position: {hybrid['position']}")
        print(f"  Target: {hybrid['target_multiplier']:.1f}x")
        print(f"  Confidence: {hybrid['confidence'] * 100:.0f}%")
    print(f"  Reason: {hybrid['reason']}")

    # Patterns
    print(f"\n[PATTERNS DETECTED]")
    for pattern_name, pattern_data in patterns.items():
        if pattern_data.get('type'):
            conf = pattern_data.get('confidence', 0) * 100
            print(f"  {pattern_name.replace('_', ' ').title()}: {pattern_data['type']} ({conf:.0f}%)")

    # Model Group Summary
    print(f"\n[MODEL PREDICTIONS BY GROUP]")

    import numpy as np

    if all_predictions.get('legacy'):
        legacy = all_predictions['legacy']
        legacy_avg = np.mean([m['predicted_multiplier'] for m in legacy])
        legacy_bets = sum(1 for m in legacy if m.get('bet', False))
        print(f"  Legacy ({len(legacy)} models):      Avg {legacy_avg:.2f}x,  Bets: {legacy_bets}/{len(legacy)}")

    if all_predictions.get('automl'):
        automl = all_predictions['automl']
        automl_avg = np.mean([m['predicted_multiplier'] for m in automl])
        automl_bets = sum(1 for m in automl if m.get('bet', False))
        print(f"  AutoML ({len(automl)} models):     Avg {automl_avg:.2f}x,  Bets: {automl_bets}/{len(automl)}")

    if all_predictions.get('trained'):
        trained = all_predictions['trained']
        trained_avg = np.mean([m['predicted_multiplier'] for m in trained])
        trained_bets = sum(1 for m in trained if m.get('bet', False))
        print(f"  Trained ({len(trained)} models):      Avg {trained_avg:.2f}x,  Bets: {trained_bets}/{len(trained)}")

    if all_predictions.get('classifiers'):
        classifiers = all_predictions['classifiers']
        print(f"\n  [Binary Classifiers]")
        for clf in classifiers:
            bet_str = "YES" if clf.get('bet', False) else "NO"
            prob = clf.get('probability', clf.get('confidence', 0))
            print(f"    {clf.get('target', 0):.1f}x: {prob*100:.0f}% {bet_str}")

    print("\n" + "=" * 100)
    print(f"FINAL RECOMMENDATION: {hybrid['action']}")
    print("=" * 100)

    # Test statistics
    stats = engine.get_statistics()
    print(f"\n[SYSTEM STATISTICS]")
    print(f"  Total Predictions: {stats['predictions_made']}")
    print(f"  Rounds Collected: {stats['rounds_collected']}")
    print(f"  Total Models: {stats['total_models']}")

    print("\n[OK] Test completed successfully!")
    print()

    return 0

if __name__ == "__main__":
    exit(main())
