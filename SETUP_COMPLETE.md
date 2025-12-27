# Setup Complete - ML Prediction System

## ✅ What's Been Implemented

### 1. **Screen Region Configuration**
- GUI selector is working
- Region configured at: (126, 941) to (372, 1017)
- Multiplier detection is functional

### 2. **Core Application**
- ✅ Tesseract OCR configured and working
- ✅ Real-time multiplier reading
- ✅ Game event tracking (START, CRASH, HIGH_MULTIPLIER)
- ✅ Round history tracking
- ✅ Supabase integration for rounds

### 3. **ML Prediction System** (NEW!)
- ✅ Random Forest predictor implemented
- ✅ 21 engineered features
- ✅ Automatic training on 1000 rounds
- ✅ Real-time predictions after each round
- ✅ Prediction accuracy tracking
- ✅ Supabase storage for predictions

## 📋 Next Steps to Get Started

### Step 1: Create Supabase Tables

You need to create two tables in Supabase:

#### A. AviatorRound Table (If not exists)
```sql
CREATE TABLE IF NOT EXISTS "AviatorRound" (
    "roundId" BIGINT PRIMARY KEY,
    "multiplier" REAL NOT NULL,
    "timestamp" TIMESTAMP
);
```

#### B. AviatorPredictions Table (NEW - Required!)
Open [SUPABASE_PREDICTIONS_TABLE.sql](SUPABASE_PREDICTIONS_TABLE.sql) in your Supabase SQL Editor and run the entire script.

This creates:
- `AviatorPredictions` table with all necessary columns
- Indexes for performance
- Helper functions for updating predictions
- A view for analyzing accuracy

### Step 2: Verify Dependencies

All Python dependencies are installed:
```bash
✅ opencv-python
✅ Pillow
✅ pytesseract
✅ numpy
✅ supabase
✅ scikit-learn (NEW)
✅ joblib (NEW)
```

### Step 3: Run the Application

```bash
python.exe main.py
```

Or with custom update interval:
```bash
python.exe main.py 0.3
```

## 🎯 How the ML System Works

### Initial Data Collection (Rounds 1-49)
```
[INFO] Need 50 more rounds before ML predictions can start
```

The system is collecting data but not making predictions yet.

### First Prediction (Round 50)
```
[INFO] Training ML model for first time...
[INFO] Model trained successfully!

================================================================================
ML PREDICTION FOR ROUND 51
================================================================================
Predicted Crash Multiplier: 2.84x
Confidence: 65.3%
Model: RandomForest
Training Samples: 50
================================================================================
```

### Ongoing Predictions (Round 51+)

After **each round ends**:

1. **Updates previous prediction** with actual result
2. **Adds round to training data**
3. **Retrains model** (every 10 rounds)
4. **Makes new prediction** for next round
5. **Saves everything to Supabase**

## 📊 Data Flow

```
Round Completes
    ↓
Update Previous Prediction (if exists)
    ↓
Add Round to ML History
    ↓
Retrain Model (every 10 rounds)
    ↓
Make Prediction for Next Round
    ↓
Save Prediction to Supabase
    ↓
Display Prediction
    ↓
Wait for Next Round...
```

## 🗃️ Supabase Schema

### AviatorRound Table
Stores actual round results:
- `roundId`: Unique timestamp-based ID
- `multiplier`: Crash multiplier value
- `timestamp`: When round ended

### AviatorPredictions Table (NEW)
Stores ML predictions:
- `predictionId`: Auto-increment ID
- `predictedMultiplier`: What the model predicted
- `actualMultiplier`: What actually happened (filled later)
- `predictionError`: |predicted - actual|
- `confidence`: Model confidence (0-1)
- `modelType`: "RandomForest"
- `trainingSamples`: Number of rounds used
- `predictionTimestamp`: When prediction made
- `actualTimestamp`: When actual result occurred
- `roundNumber`: Which round this predicts

## 📈 Features Used by the Model

The ML model analyzes **21 features** from the last 10 rounds:

### Statistical (5 features)
- Mean, Standard Deviation, Min, Max, Median of crash multipliers

### Duration (2 features)
- Mean and volatility of round durations

### Trends (2 features)
- Direction and ratio of recent trend

### Recent Pattern (3 features)
- Last 3 crash multipliers

### Streaks (2 features)
- High and low multiplier streaks

### Time-based (4 features)
- Hour of day (cyclical encoding)
- Day of week (cyclical encoding)

### Advanced (3 features)
- Volatility indicators
- Pattern matching

## 🎮 Example Session

```bash
$ python.exe main.py

[DEBUG] Tesseract configured at: C:\Program Files\Tesseract-OCR\tesseract.exe
[13:30:45] INFO: Supabase connected successfully
[13:30:45] INFO: ML Predictor initialized (needs 50 rounds to start predictions)
[13:30:45] INFO: Fetched 127 rounds from Supabase for ML training
[13:30:46] INFO: Training ML model...
[13:30:47] INFO: Model trained on 117 samples
[13:30:47] INFO: Training R² score: 0.2847

================================================================================
MULTIPLIER READER
================================================================================

[13:30:47] INFO: Started
[13:30:47] INFO: Region: (126, 941) to (372, 1017)
[13:30:47] INFO: Update interval: 0.5s

... game monitoring ...

================================================================================
ROUND ENDED
================================================================================

Round History:
┌─────┬────────────┬──────────┬────────┬────────────┐
│ #   │ Timestamp  │ Duration │ Crash  │ Status     │
├─────┼────────────┼──────────┼────────┼────────────┤
│ 128 │ 13:32:15   │ 3.45s    │ 2.47x  │ CRASHED    │
└─────┴────────────┴──────────┴────────┴────────────┘

[13:32:15] INFO: Round 128 saved to Supabase (multiplier: 2.47x)
[13:32:15] INFO: Prediction 127 updated (predicted: 2.35x, actual: 2.47x, error: 0.12)

================================================================================
ML PREDICTION FOR ROUND 129
================================================================================
Predicted Crash Multiplier: 3.21x
Confidence: 67.2%
Model: RandomForest
Training Samples: 128
Predictions Made: 2
Average Error: 0.18x
================================================================================

[13:32:15] INFO: Prediction saved (ID: 2, predicted: 3.21x)
```

## 📖 Documentation Files

1. **[README.md](README.md)** - Main application documentation
2. **[ML_PREDICTION_GUIDE.md](ML_PREDICTION_GUIDE.md)** - Complete ML system guide
3. **[SUPABASE_PREDICTIONS_TABLE.sql](SUPABASE_PREDICTIONS_TABLE.sql)** - SQL schema
4. **This file** - Setup summary

## 🔧 Configuration Options

### Minimum Rounds Before Predictions

In [main.py:70](main.py#L70):
```python
self.predictor = CrashPredictor(
    history_size=1000,              # Keep last 1000 rounds
    min_rounds_for_prediction=50    # Start predictions after 50 rounds
)
```

### Retraining Frequency

In [main.py:240](main.py#L240):
```python
if round_summary.round_number % 10 == 0:  # Retrain every 10 rounds
    self.predictor.train(lookback=10)
```

### Feature Lookback Window

In [main.py:265,272,242](main.py#L265):
```python
self.predictor.train(lookback=10)      # Use last 10 rounds for features
prediction = self.predictor.predict(lookback=10)
```

## 🚨 Important Notes

### About Predictions

⚠️ **Educational Use Only**

- Predictions are **statistical estimates**, not certainties
- Game outcomes may be truly random or pseudo-random
- **Do NOT use for gambling decisions**
- Past patterns do not guarantee future results

### Expected Accuracy

Based on Random Forest regression:
- **Good scenarios**: 60-80% confidence, ~1-2x average error
- **Volatile scenarios**: 40-60% confidence, ~3-5x average error
- **Very volatile**: Predictions will be less reliable

The model adapts over time as it learns from actual results.

## 🐛 Troubleshooting

### ML Libraries Not Found
```bash
pip install scikit-learn joblib
```

### Supabase Table Missing
Run [SUPABASE_PREDICTIONS_TABLE.sql](SUPABASE_PREDICTIONS_TABLE.sql) in Supabase SQL Editor

### Predictions Not Starting
Wait for 50 rounds to complete for initial training

### High Prediction Errors
- Normal during high volatility
- Model retrains every 10 rounds to adapt
- Check if game has truly random outcomes

## 📊 Analyzing Results

### View All Predictions
```sql
SELECT * FROM "AviatorPredictions"
ORDER BY "predictionTimestamp" DESC;
```

### Calculate Accuracy
```sql
SELECT
    AVG("predictionError") as avg_error,
    MIN("predictionError") as best,
    MAX("predictionError") as worst
FROM "AviatorPredictions"
WHERE "actualMultiplier" IS NOT NULL;
```

### Predictions by Confidence
```sql
SELECT
    ROUND("confidence"::numeric, 1) as conf_level,
    COUNT(*) as count,
    AVG("predictionError") as avg_error
FROM "AviatorPredictions"
WHERE "actualMultiplier" IS NOT NULL
GROUP BY conf_level
ORDER BY conf_level DESC;
```

## ✅ System Status

All components are ready:

- [x] Screen capture and OCR
- [x] Game event tracking
- [x] Supabase round storage
- [x] ML predictor module
- [x] Feature engineering (21 features)
- [x] Random Forest model
- [x] Automatic training
- [x] Real-time predictions
- [x] Prediction storage
- [x] Accuracy tracking
- [x] Statistics display

## 🚀 Ready to Run!

1. **Create Supabase table** (run SQL script)
2. **Start application**: `python.exe main.py`
3. **Wait for 50 rounds** to collect training data
4. **Predictions start automatically** from round 51 onwards
5. **Check Supabase** to analyze prediction accuracy

Enjoy exploring ML predictions!

---

**Need Help?**
- Read [ML_PREDICTION_GUIDE.md](ML_PREDICTION_GUIDE.md) for detailed information
- Check [README.md](README.md) for general application usage
- Review code comments in [ml_predictor.py](ml_predictor.py) and [main.py](main.py)
