# Quick Start - Two Table Setup

## Current Status: ✅ Code is Ready!

The application is configured to work with your two-table structure:
1. **AviatorRound** - Stores game rounds with auto-generated IDs
2. **analytics_round_signals** - Stores ML predictions linked to rounds

## Before Running: Fix the Trigger

Your `after_insert_analytics_generate` trigger needs to be fixed because it's calling a function that references `m_std` which doesn't exist.

### Quick Fix Option 1: Disable the Trigger

```sql
-- Run this in Supabase SQL Editor
ALTER TABLE "AviatorRound"
DISABLE TRIGGER after_insert_analytics_generate;
```

### Quick Fix Option 2: Update the Function

```sql
-- Run this in Supabase SQL Editor
CREATE OR REPLACE FUNCTION analytics_generate_round_signal()
RETURNS TRIGGER AS $$
BEGIN
    -- Just return the new row without doing anything
    -- This keeps the trigger but makes it do nothing
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

## Run the Application

```bash
python.exe main.py
```

## What Happens Per Round

### Step 1: Round Completes
Game crashes at some multiplier (e.g., 2.45x)

### Step 2: API Call 1 - Save to AviatorRound
```python
round_id = supabase.insert_round(
    multiplier=2.45,
    timestamp=datetime.now()
)
```

**Output:**
```
[10:15:30] INFO: Round 1 saved to Supabase (ID: 123, multiplier: 2.45x)
```

**Database Result:**
```sql
INSERT INTO "AviatorRound" (multiplier, timestamp)
VALUES (2.45, '2024-12-24T10:15:30');
-- Returns: roundId = 123 (auto-generated)
```

### Step 3: Make ML Prediction
Model analyzes last 1000 rounds and predicts next crash

### Step 4: API Call 2 - Save to analytics_round_signals
```python
signal_id = supabase.insert_analytics_signal(
    round_id=123,  # Links to the round we just saved
    multiplier=3.21,  # Predicted value
    model_name="RandomForest",
    model_output={
        'predicted_multiplier': 3.21,
        'prediction_timestamp': '2024-12-24T10:15:31',
        'features_used': 21
    },
    confidence=0.675,
    metadata={
        'next_round_number': 2,
        'training_samples': 50
    }
)
```

**Output:**
```
================================================================================
ML PREDICTION FOR ROUND 2
================================================================================
Predicted Crash Multiplier: 3.21x
Confidence: 67.5%
Model: RandomForest
Training Samples: 50
================================================================================

[10:15:31] INFO: Analytics signal saved (ID: 456, round: 123, model: RandomForest)
```

**Database Result:**
```sql
INSERT INTO analytics_round_signals
(round_id, multiplier, model_name, model_output, confidence, metadata)
VALUES (
    123,  -- Links to AviatorRound.roundId
    3.21,
    'RandomForest',
    '{"predicted_multiplier": 3.21, ...}'::jsonb,
    0.675,
    '{"next_round_number": 2, ...}'::jsonb
);
-- Returns: id = 456 (auto-generated)
```

## Verify Data in Supabase

### Check Rounds
```sql
SELECT
    "roundId",
    multiplier,
    timestamp
FROM "AviatorRound"
ORDER BY timestamp DESC
LIMIT 10;
```

Expected:
```
roundId | multiplier | timestamp
--------|------------|-------------------
123     | 2.45       | 2024-12-24 10:15:30
124     | 3.67       | 2024-12-24 10:16:15
125     | 1.89       | 2024-12-24 10:17:02
```

### Check Predictions
```sql
SELECT
    id,
    round_id,
    multiplier as predicted,
    model_name,
    confidence,
    created_at
FROM analytics_round_signals
ORDER BY created_at DESC
LIMIT 10;
```

Expected:
```
id  | round_id | predicted | model_name   | confidence | created_at
----|----------|-----------|--------------|------------|-------------------
456 | 123      | 3.21      | RandomForest | 0.675      | 2024-12-24 10:15:31
457 | 124      | 2.95      | RandomForest | 0.682      | 2024-12-24 10:16:16
458 | 125      | 4.12      | RandomForest | 0.701      | 2024-12-24 10:17:03
```

### Join to See Predictions vs Actuals
```sql
SELECT
    ar."roundId",
    ar.multiplier as actual_multiplier,
    ars.multiplier as predicted_multiplier,
    ABS(ar.multiplier - ars.multiplier) as error,
    ars.confidence,
    ar.timestamp
FROM "AviatorRound" ar
LEFT JOIN analytics_round_signals ars ON ars.round_id = ar."roundId"
WHERE ars.model_name = 'RandomForest'
ORDER BY ar.timestamp DESC
LIMIT 10;
```

Expected:
```
roundId | actual | predicted | error | confidence | timestamp
--------|--------|-----------|-------|------------|-------------------
123     | 2.45   | 3.21      | 0.76  | 0.675      | 2024-12-24 10:15:30
124     | 3.67   | 2.95      | 0.72  | 0.682      | 2024-12-24 10:16:15
```

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    ROUND COMPLETES                          │
│                  (e.g., crashes at 2.45x)                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              API CALL 1: Insert Round                       │
│   INSERT INTO "AviatorRound" (multiplier, timestamp)        │
│   VALUES (2.45, '2024-12-24T10:15:30')                      │
│   RETURNING roundId                                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
         ┌─────────────────────────┐
         │   roundId = 123         │
         │   (auto-generated)      │
         └─────────┬───────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│              ML MODEL MAKES PREDICTION                      │
│   Analyzes: Last 1000 rounds                                │
│   Features: 21 statistical indicators                       │
│   Output:   Predicted crash = 3.21x, Confidence = 67.5%     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         API CALL 2: Insert Analytics Signal                 │
│   INSERT INTO analytics_round_signals                       │
│   (round_id, multiplier, model_name, model_output, ...)     │
│   VALUES (123, 3.21, 'RandomForest', {...}, 0.675, {...})   │
│   RETURNING id                                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
         ┌─────────────────────────┐
         │   signal_id = 456       │
         │   (auto-generated)      │
         └─────────────────────────┘
```

## Troubleshooting

### Error: "column m_std does not exist"

**Cause:** The trigger function `analytics_generate_round_signal()` references a column that doesn't exist.

**Solution:**
```sql
-- Option 1: Disable the trigger
ALTER TABLE "AviatorRound" DISABLE TRIGGER after_insert_analytics_generate;

-- Option 2: Fix the function (see above)
```

### Error: "permission denied"

**Cause:** RLS (Row Level Security) is blocking inserts.

**Solution:**
```sql
ALTER TABLE "AviatorRound" DISABLE ROW LEVEL SECURITY;
ALTER TABLE analytics_round_signals DISABLE ROW LEVEL SECURITY;
```

### No predictions appearing

**Cause:** Need 50 rounds before ML starts predicting.

**Solution:** Wait for 50 rounds to complete. You'll see:
```
[10:15:30] INFO: Need 50 rounds before ML predictions can start
```

Once 50 rounds are collected, predictions will start automatically.

## File Structure

Your implementation uses:

- **[supabase_client.py](supabase_client.py)** - Updated with `insert_analytics_signal()`
- **[main.py](main.py)** - Two-step save process
- **[ml_predictor.py](ml_predictor.py)** - Random Forest model

## Summary

✅ **Ready to run:** `python.exe main.py`

✅ **Two API calls per round:**
1. Save round → Get `roundId`
2. Save prediction → Link via `round_id`

✅ **Tables properly linked:**
- `AviatorRound` stores actual results
- `analytics_round_signals` stores predictions

⚠️ **Before first run:** Fix or disable the `after_insert_analytics_generate` trigger

That's it! Your system is ready to go.
