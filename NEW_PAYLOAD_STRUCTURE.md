# New Payload Structure - Implementation Complete

## Overview

The `analytics_round_signals` table now uses a new structure with a `payload` column that stores prediction details in JSON format.

## Key Changes

### 1. Column Structure

**`multiplier` column**: Stores the **ACTUAL multiplier from the last round** (not the prediction)

**`payload` column**: Stores the **prediction details** as JSON text with this structure:

```json
{
  "modelName": "RandomForest",
  "id": 401,
  "expectedOutput": 3.15,
  "confidence": "73%",
  "range": "2.52-3.78"
}
```

### 2. Data Flow

```
Round N completes with multiplier = 2.45x
    ↓
Save to AviatorRound (roundId: 401, multiplier: 2.45x, timestamp: T)
    ↓
ML model predicts next round: 3.15x ±20% (range: 2.52-3.78), confidence: 73%
    ↓
Save to analytics_round_signals:
    - round_id: 401 (links to the round that just ended)
    - multiplier: 2.45 (ACTUAL from last round)
    - payload: {
        "modelName": "RandomForest",
        "id": 401,
        "expectedOutput": 3.15,
        "confidence": "73%",
        "range": "2.52-3.78"
      }
    - created_at: T (same timestamp as the round)
```

## Updated Code

### [supabase_client.py](supabase_client.py:79-143)

```python
def insert_analytics_signal(self, round_id: int, actual_multiplier: float,
                            predicted_multiplier: float, model_name: str,
                            confidence: float, prediction_range: tuple,
                            model_output: dict = None, metadata: dict = None,
                            timestamp: datetime = None):
```

**Parameters:**
- `actual_multiplier`: The actual multiplier from the last round (stored in `multiplier` column)
- `predicted_multiplier`: The predicted multiplier for next round (stored in payload as `expectedOutput`)
- `prediction_range`: Tuple of (min, max) for the prediction range

**Payload Structure:**
```python
payload = {
    'modelName': model_name,
    'id': round_id,
    'expectedOutput': predicted_multiplier,
    'confidence': f"{confidence * 100:.0f}%",
    'range': f"{prediction_range[0]:.2f}-{prediction_range[1]:.2f}"
}
```

### [main.py](main.py:255-343)

**Updated method signature:**
```python
def _make_prediction_for_next_round(self, next_round_number, last_round_id=None,
                                    last_round_multiplier=None, round_timestamp=None):
```

**Prediction range calculation:**
```python
# Calculate prediction range (±20% of predicted value)
range_margin = predicted_mult * 0.2
prediction_range = (
    max(1.0, predicted_mult - range_margin),  # Min can't be less than 1.0
    predicted_mult + range_margin
)
```

**Insert call:**
```python
signal_id = self.supabase.insert_analytics_signal(
    round_id=last_round_id,
    actual_multiplier=last_round_multiplier,  # Actual from last round
    predicted_multiplier=predicted_mult,       # Prediction for next round
    model_name=prediction.get('model_type', 'RandomForest'),
    confidence=confidence,
    prediction_range=prediction_range,
    model_output=model_output,
    metadata=metadata,
    timestamp=round_timestamp
)
```

## Test Results

**Test file**: [test_new_payload_structure.py](test_new_payload_structure.py)

```
✅ Round ID: 401
✅ Signal ID: 594
✅ Timestamp: 2025-12-24T12:05:52.034679

Data saved:
  multiplier: 2.45 (actual from last round)
  payload: {
    "modelName": "RandomForest",
    "id": 401,
    "expectedOutput": 3.15,
    "confidence": "73%",
    "range": "2.52-3.78"
  }
```

## Database Verification

Run this query in Supabase to verify the structure:

```sql
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
WHERE ar."roundId" = 401;
```

**Expected result:**
- `actual_multiplier` (from AviatorRound): `2.45`
- `stored_actual_multiplier` (from analytics_round_signals): `2.45`
- `payload`: JSON string with prediction details
- `timestamp` = `created_at` (same timestamp)

## How to Read the Data

### Get prediction for a specific round

```sql
SELECT
    payload::json->>'expectedOutput' as predicted_multiplier,
    payload::json->>'confidence' as confidence,
    payload::json->>'range' as prediction_range,
    multiplier as actual_multiplier_from_previous_round
FROM analytics_round_signals
WHERE round_id = 401;
```

### Compare predictions vs actual results

```sql
SELECT
    ars.round_id,
    ars.multiplier as previous_round_actual,
    ars.payload::json->>'expectedOutput' as predicted_for_next,
    next_round.multiplier as next_round_actual,
    ABS(
        (ars.payload::json->>'expectedOutput')::numeric -
        next_round.multiplier
    ) as prediction_error
FROM analytics_round_signals ars
JOIN "AviatorRound" current_round ON current_round."roundId" = ars.round_id
LEFT JOIN "AviatorRound" next_round
    ON next_round.timestamp > current_round.timestamp
    ORDER BY next_round.timestamp ASC
    LIMIT 1;
```

## Benefits of This Structure

1. **Clear separation**: `multiplier` = actual (historical), `payload` = prediction (forward-looking)
2. **Structured predictions**: Consistent JSON format for all predictions
3. **Timestamp sync**: Both tables use the same timestamp
4. **Easy querying**: Can extract prediction details using JSON operators
5. **Backwards compatible**: Still maintains `model_output` and `metadata` JSONB columns

## Files Modified

1. **[supabase_client.py](supabase_client.py:79-143)**
   - Updated `insert_analytics_signal()` signature and implementation
   - Added payload JSON generation
   - Updated to accept actual and predicted multipliers separately

2. **[main.py](main.py:242-343)**
   - Added `last_round_multiplier` parameter to `_make_prediction_for_next_round()`
   - Calculate prediction range (±20%)
   - Pass separate actual and predicted values to insert method

## Production Ready ✅

The application is ready to use with the new payload structure:

```bash
python.exe main.py
```

Every round will save:
- **AviatorRound**: Actual multiplier from the round
- **analytics_round_signals**:
  - `multiplier`: Actual from the round that just ended
  - `payload`: Prediction for the next round with range and confidence
  - Same timestamp for both entries
