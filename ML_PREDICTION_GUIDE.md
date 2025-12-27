# ML Prediction System Guide

This guide explains how to use the ML prediction system to predict crash multipliers.

## Overview

The system uses a **Random Forest** machine learning model to predict the next round's crash multiplier based on historical patterns from the last 1000 rounds.

## Features

- **Automatic Training**: Loads historical data from Supabase and trains automatically
- **Real-time Predictions**: Makes predictions after each round ends
- **Accuracy Tracking**: Monitors prediction accuracy and displays statistics
- **Supabase Integration**: Stores all predictions and actual results for analysis
- **Feature Engineering**: Uses 21 statistical and time-based features

## Installation

### 1. Install ML Dependencies

```bash
pip install scikit-learn joblib
```

Or install all dependencies at once:

```bash
pip install -r requirements.txt
```

### 2. Create Supabase Table

Run the SQL script in your Supabase SQL Editor:

```bash
# Open SUPABASE_PREDICTIONS_TABLE.sql and run it in Supabase
```

This creates the `AviatorPredictions` table with the following columns:
- `predictionId` - Auto-increment primary key
- `predictedMultiplier` - Predicted crash value
- `actualMultiplier` - Actual crash value (filled after round)
- `predictionError` - Absolute error |predicted - actual|
- `confidence` - Model confidence (0-1)
- `modelType` - "RandomForest"
- `trainingSamples` - Number of rounds used for training
- `predictionTimestamp` - When prediction was made
- `actualTimestamp` - When actual result occurred
- `roundNumber` - Round number

## How It Works

### 1. Data Collection (Rounds 1-49)

- System collects data from each round
- Multiplier and duration are recorded
- No predictions are made yet

```
[INFO] Need 50 rounds before ML predictions can start
```

### 2. Initial Training (Round 50)

- Model trains on first 50 rounds
- Extracts features from historical patterns
- Random Forest with 100 decision trees

```
[INFO] Training ML model for first time...
[INFO] Model trained successfully!
```

### 3. Making Predictions (Round 51+)

After each round ends, the system:

1. **Updates Previous Prediction** (if exists)
   - Compares predicted vs actual multiplier
   - Calculates prediction error
   - Stores result in Supabase

2. **Adds Round to History**
   - Adds completed round to training data
   - Maintains rolling window of 1000 rounds

3. **Retrains Model** (every 10 rounds)
   - Updates model with new patterns
   - Improves accuracy over time

4. **Makes New Prediction**
   - Predicts next round's crash multiplier
   - Displays confidence level
   - Saves to Supabase

### Example Output

```
================================================================================
ML PREDICTION FOR ROUND 52
================================================================================
Predicted Crash Multiplier: 3.45x
Confidence: 68.5%
Model: RandomForest
Training Samples: 51
Predictions Made: 1
Average Error: 0.00x
================================================================================
```

## Features Used for Prediction

The model uses 21 features extracted from the last 10 rounds:

### Statistical Features (5)
- Mean of crash multipliers
- Standard deviation (volatility)
- Minimum crash
- Maximum crash
- Median crash

### Duration Features (2)
- Mean round duration
- Duration volatility

### Trend Features (2)
- Trend direction (last 5 vs previous 5)
- Trend ratio

### Recent Pattern (3)
- Most recent crash
- 2nd most recent crash
- 3rd most recent crash

### Streak Detection (2)
- High multiplier streak count
- Low multiplier streak count

### Time-based Features (4)
- Hour of day (cyclical: sin/cos)
- Day of week (cyclical: sin/cos)

### Why These Features?

- **Statistical features**: Capture overall volatility and range
- **Trend features**: Detect if multipliers are increasing/decreasing
- **Recent pattern**: Give more weight to latest rounds
- **Streak detection**: Identify hot/cold streaks
- **Time features**: Account for time-of-day patterns

## Understanding Predictions

### Confidence Score

The confidence score (0-100%) indicates how reliable the prediction is:

- **80-100%**: High confidence - model has low recent error
- **60-80%**: Moderate confidence - typical range
- **40-60%**: Low confidence - high volatility or new patterns
- **0-40%**: Very low confidence - unreliable prediction

### Prediction Error

After each round, the system calculates:

```
Prediction Error = |Predicted Multiplier - Actual Multiplier|
```

Example:
- Predicted: 3.45x
- Actual: 4.12x
- Error: 0.67x

### Accuracy Metrics

The system tracks:
- **Average Error**: Mean absolute error across all predictions
- **Min Error**: Best prediction (closest to actual)
- **Max Error**: Worst prediction (furthest from actual)

## Performance Expectations

### Realistic Expectations

⚠️ **IMPORTANT**: Crash multipliers in games like Aviator are typically **pseudo-random** or **provably fair**, meaning:

- They may follow statistical distributions
- Patterns may exist in short-term volatility
- Long-term results tend toward expected values
- True prediction is theoretically impossible for truly random systems

### What the ML Model Can Do

✅ **Statistical Analysis**
- Identify short-term volatility patterns
- Detect streak tendencies
- Estimate probability ranges
- Suggest conservative cashout points

✅ **Pattern Recognition**
- Recognize if multipliers are trending high/low
- Detect unusual streaks
- Adapt to changing volatility

### What the ML Model CANNOT Do

❌ **Guaranteed Predictions**
- Cannot predict truly random events
- Cannot "beat the house" in fair systems
- Cannot guarantee profit

## Using Predictions Responsibly

### Educational Purpose

This system is designed for:
- Learning about machine learning
- Understanding statistical patterns
- Analyzing game data
- Educational demonstrations

### Risk Warning

🚨 **DO NOT use predictions for gambling decisions**

- Predictions are statistical estimates, not certainties
- Past performance does not guarantee future results
- Random systems cannot be reliably predicted
- Gambling involves risk of loss

## Supabase Queries

### View Prediction Accuracy

```sql
SELECT
    "predictionId",
    "predictedMultiplier",
    "actualMultiplier",
    "predictionError",
    "confidence",
    "roundNumber"
FROM "AviatorPredictions"
WHERE "actualMultiplier" IS NOT NULL
ORDER BY "predictionTimestamp" DESC
LIMIT 50;
```

### Calculate Overall Accuracy

```sql
SELECT
    COUNT(*) as total_predictions,
    AVG("predictionError") as avg_error,
    MIN("predictionError") as best_prediction,
    MAX("predictionError") as worst_prediction,
    AVG("confidence") as avg_confidence
FROM "AviatorPredictions"
WHERE "actualMultiplier" IS NOT NULL;
```

### Find Best Predictions

```sql
SELECT
    "roundNumber",
    "predictedMultiplier",
    "actualMultiplier",
    "predictionError",
    "confidence"
FROM "AviatorPredictions"
WHERE "actualMultiplier" IS NOT NULL
ORDER BY "predictionError" ASC
LIMIT 10;
```

### Analyze Prediction by Confidence Level

```sql
SELECT
    CASE
        WHEN "confidence" >= 0.8 THEN 'High (80-100%)'
        WHEN "confidence" >= 0.6 THEN 'Moderate (60-80%)'
        WHEN "confidence" >= 0.4 THEN 'Low (40-60%)'
        ELSE 'Very Low (0-40%)'
    END as confidence_level,
    COUNT(*) as predictions,
    AVG("predictionError") as avg_error
FROM "AviatorPredictions"
WHERE "actualMultiplier" IS NOT NULL
GROUP BY confidence_level
ORDER BY confidence_level DESC;
```

## Troubleshooting

### ML Libraries Not Found

```
[WARNING] ML libraries not available. Run: pip install scikit-learn
```

**Solution:**
```bash
pip install scikit-learn joblib
```

### Predictions Not Starting

```
[INFO] Need 50 more rounds before ML predictions can start
```

**Solution:** Wait for 50 rounds to complete. The model needs minimum data to make reasonable predictions.

### Supabase Errors

```
[WARNING] Failed to save prediction to Supabase: ...
```

**Solution:**
1. Check that you've created the `AviatorPredictions` table
2. Run the SQL script in `SUPABASE_PREDICTIONS_TABLE.sql`
3. Verify your Supabase credentials are correct

### High Prediction Errors

```
[INFO] Average prediction error: 5.23x
```

**Possible Causes:**
- High volatility in recent rounds
- Unusual patterns or streaks
- Small training dataset
- Truly random outcomes

**Solutions:**
- Collect more training data (wait for more rounds)
- Model retrains every 10 rounds to adapt
- Accept that some variance is normal

## Advanced Configuration

### Adjust Minimum Training Rounds

In `main.py`, line 70:

```python
self.predictor = CrashPredictor(
    history_size=1000,
    min_rounds_for_prediction=50  # Change this value
)
```

- Lower (e.g., 30): Faster predictions but less accurate
- Higher (e.g., 100): Slower start but potentially more accurate

### Adjust Retraining Frequency

In `main.py`, line 240:

```python
if round_summary.round_number % 10 == 0:  # Change 10 to other value
    self.predictor.train(lookback=10)
```

- More frequent (e.g., 5): Adapts faster to changes
- Less frequent (e.g., 20): More stable predictions

### Modify Feature Lookback

In `main.py`, lines 265, 272, 242:

```python
self.predictor.train(lookback=10)  # Change lookback window
prediction = self.predictor.predict(lookback=10)
```

- Smaller window (e.g., 5): Focus on recent patterns
- Larger window (e.g., 20): Consider more history

## Model Architecture

### Random Forest Configuration

From `ml_predictor.py`:

```python
RandomForestRegressor(
    n_estimators=100,      # Number of decision trees
    max_depth=15,          # Max tree depth (prevents overfitting)
    min_samples_split=5,   # Min samples to split a node
    min_samples_leaf=2,    # Min samples in leaf node
    random_state=42,       # For reproducibility
    n_jobs=-1              # Use all CPU cores
)
```

### Why Random Forest?

- **Robust**: Handles non-linear relationships
- **No overfitting**: Ensemble method reduces variance
- **Feature importance**: Can analyze which features matter most
- **Fast**: Parallel training and prediction
- **No scaling needed**: Works with different feature ranges

## Future Enhancements

Potential improvements (not yet implemented):

### 1. XGBoost Support
- More powerful gradient boosting
- Better handling of complex patterns

### 2. LSTM Neural Network
- Sequence-to-sequence prediction
- Better for time-series patterns

### 3. Ensemble Predictions
- Combine multiple models
- Weighted average of predictions

### 4. Feature Importance Analysis
- Identify which features matter most
- Optimize feature selection

### 5. Probability Distribution
- Predict probability ranges instead of single value
- E.g., "70% chance between 2-4x"

### 6. Safe Cashout Recommendation
- Conservative suggestion based on historical risk
- E.g., "Safe cashout: 2.1x (80% success rate)"

## Summary

The ML prediction system:
- ✅ Trains automatically on historical data
- ✅ Makes predictions after each round
- ✅ Tracks accuracy over time
- ✅ Stores results in Supabase
- ✅ Uses 21 engineered features
- ✅ Retrains periodically to adapt

Remember: Use for educational purposes only. Predictions are statistical estimates, not guarantees.
