# Multi-Model ML Prediction System

## Overview

The Observer Module now includes a sophisticated multi-model ML prediction system that trains and runs **5 different machine learning algorithms** simultaneously, providing ensemble predictions with betting recommendations.

## Models Included

1. **RandomForest** - Ensemble of decision trees, good for non-linear patterns
2. **GradientBoosting** - Sequential tree boosting, excellent for capturing trends
3. **Ridge** - Linear regression with L2 regularization, good for linear patterns
4. **Lasso** - Linear regression with L1 regularization, good for feature selection
5. **DecisionTree** - Fast single tree, interpretable predictions

## Key Features

### 1. Multi-Model Training
- All 5 models train simultaneously on the same data
- Each model uses 21 engineered features
- Adaptive lookback windows (4-5 rounds)
- Independent scalers for each model

### 2. Ensemble Prediction
- Weighted average of all model predictions
- Confidence-weighted aggregation
- Majority voting for betting decisions

### 3. Bet Flags
- Each model provides a `bet` boolean flag
- Bet threshold: confidence > 60%
- Ensemble uses majority vote (>50% of models)

### 4. Prediction Display
```
================================================================================
ML PREDICTIONS FOR ROUND 7 (Multi-Model)
================================================================================

ENSEMBLE PREDICTION:
  Multiplier: 3.15x
  Confidence: 73%
  Range: 2.52x - 3.78x
  Bet: YES
  Bet Votes: 4/5

Individual Models:
  RandomForest          3.12x  Conf:  68%  Bet: ✓
  GradientBoosting      3.18x  Conf:  71%  Bet: ✓
  Ridge                 3.20x  Conf:  65%  Bet: ✓
  Lasso                 3.10x  Conf:  62%  Bet: ✓
  DecisionTree          3.00x  Conf:  55%  Bet: ✗

Statistics:
  Total Predictions: 2
  Rounds Collected: 6
================================================================================
```

## Payload Structure

The multi-model system saves predictions to the `analytics_round_signals` table with this payload structure:

```json
{
  "roundId": 123,
  "actualMultiplier": 2.45,
  "models": [
    {
      "modelName": "Ensemble",
      "expectedOutput": 3.15,
      "confidence": "73%",
      "range": "2.52-3.78",
      "bet": true
    },
    {
      "modelName": "RandomForest",
      "expectedOutput": 3.12,
      "confidence": "68%",
      "range": "2.50-3.74",
      "bet": true
    },
    {
      "modelName": "GradientBoosting",
      "expectedOutput": 3.18,
      "confidence": "71%",
      "range": "2.54-3.82",
      "bet": true
    },
    {
      "modelName": "Ridge",
      "expectedOutput": 3.20,
      "confidence": "65%",
      "range": "2.56-3.84",
      "bet": true
    },
    {
      "modelName": "Lasso",
      "expectedOutput": 3.10,
      "confidence": "62%",
      "range": "2.48-3.72",
      "bet": true
    },
    {
      "modelName": "DecisionTree",
      "expectedOutput": 3.00,
      "confidence": "55%",
      "range": "2.40-3.60",
      "bet": false
    }
  ],
  "timestamp": "2025-12-24T12:30:45.123456"
}
```

## Database Schema

### analytics_round_signals Table

```sql
{
  "round_id": 123,              -- Links to AviatorRound
  "multiplier": 2.45,            -- Actual multiplier from last round
  "model_name": "MultiModel",    -- Indicates multi-model prediction
  "model_output": {
    "num_models": 6,
    "models": ["Ensemble", "RandomForest", "GradientBoosting", "Ridge", "Lasso", "DecisionTree"]
  },
  "confidence": 0.73,            -- Ensemble confidence
  "metadata": {
    "prediction_count": 6,
    "bet_consensus": 4           -- Number of models that recommend betting
  },
  "payload": "<JSON string above>",
  "created_at": "2025-12-24T12:30:45.123456"
}
```

## Betting Logic

### Individual Model Betting
```python
should_bet = confidence > 0.6  # 60% threshold
```

### Ensemble Betting
```python
bet_votes = sum(1 for model in models if model['bet'] == True)
ensemble_bet = bet_votes > len(models) / 2  # Majority vote
```

**Example:**
- 5 models: RandomForest ✓, GradientBoosting ✓, Ridge ✓, Lasso ✓, DecisionTree ✗
- Bet votes: 4/5
- Ensemble bet: **YES** (4 > 2.5)

## API Reference

### MultiModelPredictor Class

#### Methods

**`predict_all(lookback=10)`**
- Returns predictions from all 5 models
- Each prediction includes: model_name, predicted_multiplier, confidence, range, bet

**`get_ensemble_prediction(predictions)`**
- Calculates weighted ensemble from all predictions
- Returns ensemble prediction with majority-vote bet decision

**`update_prediction_accuracy(actual_multiplier)`**
- Updates accuracy stats for all models
- Tracks last 50 predictions per model

**`get_statistics()`**
- Returns overall statistics
- Includes per-model accuracy metrics

### Supabase Client

**`insert_multi_model_signal(round_id, actual_multiplier, predictions, timestamp=None)`**
- Saves multi-model predictions to database
- Includes all model predictions in payload
- Returns signal_id on success

## Usage

### Running with Multi-Model
```bash
python main.py
```

The system automatically detects and uses the multi-model predictor if available. If sklearn is not installed or multi_model_predictor.py is missing, it falls back to single-model (RandomForest only).

### Querying Multi-Model Data

**Get all model predictions for a round:**
```sql
SELECT
    ar."roundId",
    ar.multiplier as actual,
    ars.payload::json->'models' as all_predictions,
    ars.metadata->'bet_consensus' as bet_consensus
FROM "AviatorRound" ar
JOIN analytics_round_signals ars ON ars.round_id = ar."roundId"
WHERE ars.model_name = 'MultiModel'
ORDER BY ar."roundId" DESC;
```

**Extract individual model predictions:**
```sql
SELECT
    ar."roundId",
    jsonb_array_elements(ars.payload::jsonb->'models') as model_prediction
FROM "AviatorRound" ar
JOIN analytics_round_signals ars ON ars.round_id = ar."roundId"
WHERE ars.model_name = 'MultiModel';
```

**Get betting recommendations:**
```sql
SELECT
    ar."roundId",
    model_pred->>'modelName' as model,
    model_pred->>'expectedOutput' as prediction,
    model_pred->>'confidence' as confidence,
    model_pred->>'bet' as should_bet
FROM "AviatorRound" ar
JOIN analytics_round_signals ars ON ars.round_id = ar."roundId",
LATERAL jsonb_array_elements(ars.payload::jsonb->'models') as model_pred
WHERE ars.model_name = 'MultiModel'
AND ar."roundId" = 123;
```

## Performance Tracking

Each model tracks:
- **Predictions Made**: Total count
- **Prediction Errors**: Last 50 errors
- **Average Error**: Mean of last 50 predictions
- **Confidence Score**: Calculated from historical accuracy

## Configuration

### Confidence Threshold
Edit [multi_model_predictor.py](multi_model_predictor.py:287):
```python
should_bet = confidence > 0.6  # Change to desired threshold (0.0-1.0)
```

### Prediction Range
Edit [multi_model_predictor.py](multi_model_predictor.py:279):
```python
range_margin = predicted_value * 0.2  # Change to desired percentage (e.g., 0.15 for ±15%)
```

### Model Parameters
Each model can be tuned in `_initialize_models()`:
```python
# Example: Increase RandomForest trees
self.models['RandomForest'] = RandomForestRegressor(
    n_estimators=200,  # Changed from 100
    max_depth=10,
    random_state=42,
    n_jobs=-1
)
```

## Benefits

1. **Robustness**: Multiple models reduce prediction variance
2. **Confidence**: Ensemble approach provides more reliable predictions
3. **Transparency**: See predictions from each model
4. **Betting Guidance**: Clear bet/no-bet flags for automation
5. **Model Comparison**: Track which models perform best
6. **Fallback**: Automatically falls back to single model if needed

## Files

- [multi_model_predictor.py](multi_model_predictor.py) - Multi-model prediction engine
- [main.py](main.py) - Integration with main application
- [supabase_client.py](supabase_client.py) - Database operations
- [ml_predictor.py](ml_predictor.py) - Legacy single-model (fallback)

## Future Enhancements

- [ ] Dynamic model weighting based on recent performance
- [ ] Add more models (XGBoost, Neural Networks)
- [ ] Model-specific confidence thresholds
- [ ] Real-time performance dashboard
- [ ] Automated model selection based on market conditions

---

**Version**: observer-v1
**Status**: ✅ Production Ready
**Last Updated**: 2025-12-24
