# Models Disabled - Configuration

## Current Active Models

**Only AutoML Models (16 total)**

The system now runs with **16 AutoML models only**. The following model groups have been disabled:

### ❌ Disabled Model Groups

1. **Legacy Models (5)** - Commented out in [ml_system/core/model_registry.py](ml_system/core/model_registry.py#L107-L115)
   - RandomForest
   - GradientBoosting
   - Ridge
   - Lasso
   - DecisionTree

2. **Trained Models (3-4)** - Commented out in [ml_system/core/model_registry.py](ml_system/core/model_registry.py#L127-L138)
   - Trained_RandomForest
   - Trained_GradientBoosting
   - Trained_LGBM
   - Trained_LSTM (optional)

3. **Binary Classifiers (4)** - Commented out in [ml_system/core/model_registry.py](ml_system/core/model_registry.py#L140-L148)
   - Classifier_1.5x
   - Classifier_2.0x
   - Classifier_3.0x
   - Classifier_5.0x

### ✅ Active Model Group

**AutoML Models (16 models)**
1. H2O_AutoML
2. Google_AutoML
3. AutoSklearn
4. LSTM_Model
5. AutoGluon
6. PyCaret
7. RandomForest_AutoML
8. CatBoost
9. LightGBM_AutoML
10. XGBoost_AutoML
11. MLP_NeuralNet
12. TPOT_Genetic
13. AutoKeras
14. AutoPyTorch
15. MLBox
16. TransmogrifAI

## System Behavior Changes

### Hybrid Betting Strategy
- **Position 1 (ML Classifiers):** DISABLED - No binary classifiers available
- **Position 2 (Cold Streak Detection):** ACTIVE - Still detects cold streaks (8+ low rounds) and targets 3.0x

The hybrid strategy will now only trigger on Position 2 (cold streak detection), not on ML classifier recommendations.

### Display Output
The prediction display now shows:
- ✅ AutoML Models table (16 models)
- ❌ Legacy Models (hidden)
- ❌ Trained Models (hidden)
- ❌ Binary Classifiers (hidden)
- ✅ Ensemble prediction (from 16 AutoML models)
- ✅ Hybrid strategy (Position 2 only - cold streak)
- ✅ Pattern detection (all 4 patterns active)
- ✅ Summary statistics (AutoML group only)

## Files Modified

1. **[ml_system/core/model_registry.py](ml_system/core/model_registry.py)**
   - Lines 107-115: Legacy models commented out
   - Lines 127-138: Trained models commented out
   - Lines 140-148: Binary classifiers commented out

2. **[ml_system/prediction_engine.py](ml_system/prediction_engine.py)**
   - Line 62: Added comment about empty classifiers list
   - Line 64: Added comment about Position 2 only

3. **[main.py](main.py)**
   - Line 471: Updated title to "16 AutoML Models"
   - Lines 480-492: Legacy models display commented out
   - Lines 508-520: Trained models display commented out
   - Lines 522-532: Binary classifiers display commented out
   - Lines 565-570: Legacy summary commented out
   - Lines 578-583: Trained summary commented out

## How to Re-enable Models

To re-enable any model group, simply uncomment the relevant sections in the files above:

### Re-enable Legacy Models
Uncomment lines 107-115 in [ml_system/core/model_registry.py](ml_system/core/model_registry.py)

### Re-enable Trained Models
Uncomment lines 127-138 in [ml_system/core/model_registry.py](ml_system/core/model_registry.py)

### Re-enable Binary Classifiers
Uncomment lines 140-148 in [ml_system/core/model_registry.py](ml_system/core/model_registry.py)

### Re-enable Display Sections
Uncomment the corresponding display sections in [main.py](main.py) for the model groups you re-enabled.

## Current System Stats

- **Total Models:** 16 (AutoML only)
- **Active Strategies:** Ensemble + Hybrid (Position 2 only)
- **Pattern Detectors:** 4 (all active)
- **Betting Logic:** Cold streak detection (8+ low rounds → 3.0x target)
