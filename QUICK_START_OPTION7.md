# Option 7: Model Signal Listener - Quick Start

## What It Does
Real-time listener for Supabase signals with any of 16 AutoML models. Automatically executes bets when signal predictions meet your criteria.

## How to Use

### Step 1: Run Main Menu
```bash
python main.py
```

### Step 2: Select Option 7
```
AVIATOR BOT - MAIN MENU
1. Start Monitoring
2. Configure Regions
3. Test Configuration
4. WebSocket Automated Trading
5. Supabase Automated Trading
6. Demo Mode
7. Model Signal Listener  ← SELECT THIS
8. Exit
```

### Step 3: Choose Model (or press Enter for default)
```
Available Models:
  1. PyCaret              (DEFAULT - recommended)
  2. H2O_AutoML
  3. AutoSklearn
  4. LSTM_Model
  5. AutoGluon
  6. RandomForest_AutoML
  7. CatBoost
  8. LightGBM_AutoML
  9. XGBoost_AutoML
  10. MLP_NeuralNet
  11. TPOT_Genetic
  12. AutoKeras
  13. AutoPyTorch
  14. MLBox
  15. TransmogrifAI
  16. Google_AutoML

Enter model name or number (default: PyCaret):
→ Just press Enter to use PyCaret
```

### Step 4: Set Betting Thresholds (or press Enter for defaults)
```
Enter min predicted multiplier (default: 1.3):
→ Minimum crash prediction threshold
→ Default: 1.3x (press Enter)

Enter min range start (default: 1.3):
→ Minimum range start threshold
→ Default: 1.3x (press Enter)

Enter safety margin (0.0-1.0, default: 0.8):
→ Cashout at this % of predicted (80% = 20% buffer)
→ Default: 0.8 (press Enter)
```

### Step 5: Watch Real-Time Execution
```
[04:06:52] PYCARET-RT INFO: Connected to Supabase (async client)
[04:06:52] PYCARET-RT INFO: Subscribed to analytics_round_signals
[04:06:55] PYCARET-RT INFO: Signal received - Round #2847
[04:06:55] PYCARET-RT INFO: PyCaret prediction found: 1.52x
[04:06:55] PYCARET-RT INFO: Bet qualified (1.52 >= 1.3 AND 1.40 >= 1.3)
[04:06:56] PYCARET-RT INFO: Bet placed successfully
[04:07:10] PYCARET-RT INFO: Cashout executed at 1.21x (80% of 1.52)
```

### Step 6: Stop and View Statistics
```
Press Ctrl+C to stop

Listener Statistics
═════════════════════════════════════
Total Executions:      42
Qualified Bets:        8
Successful Trades:     7
Failed Trades:         1
Qualification Rate:    19.0%
Success Rate:          87.5%
═════════════════════════════════════
```

## Default Settings
| Setting | Value | Meaning |
|---------|-------|---------|
| Model | PyCaret | First model to try |
| Min Predicted | 1.3x | Only bet if prediction >= 1.3x |
| Min Range | 1.3x | Only bet if range_start >= 1.3x |
| Safety Margin | 80% | Cashout at 80% of predicted (20% buffer) |

## Betting Logic
A bet is placed ONLY when BOTH conditions are true:
1. Model's predicted multiplier >= min_predicted (default: 1.3x)
2. Signal's range start >= min_range (default: 1.3x)

## Example Scenarios

### Scenario 1: Default Settings (Easiest)
```
Press Enter at all prompts
↓
Uses PyCaret model
↓
Bets only when prediction >= 1.3x AND range >= 1.3x
↓
Cashouts at 80% of predicted (safe)
```

### Scenario 2: Conservative Trading
```
Model: PyCaret (default)
Min Predicted: 1.5
Min Range: 1.5
Safety Margin: 0.75
↓
Higher thresholds = fewer bets but higher quality
↓
Cashout at 75% of predicted (more buffer)
```

### Scenario 3: Aggressive Trading
```
Model: XGBoost_AutoML
Min Predicted: 1.2
Min Range: 1.2
Safety Margin: 0.85
↓
Lower thresholds = more bets
↓
Cashout at 85% of predicted (less buffer)
```

## What Gets Tracked

✓ **Total Executions** - Total signals received
✓ **Qualified Bets** - Signals that met your criteria
✓ **Successful Trades** - Bets that won
✓ **Failed Trades** - Bets that lost
✓ **Qualification Rate** - % of signals that qualified
✓ **Success Rate** - % of qualified bets that won

## Troubleshooting

### Issue: Returns to menu immediately
**Solution:** Configuration is incomplete. Run option 2 first to set up regions.

### Issue: Connection failed
**Solution:** Check internet connection and Supabase status.

### Issue: No bets being placed
**Solution:** Thresholds are too high. Lower min_predicted or min_range.

## Features

✓ **Real-Time** - WebSocket <100ms latency
✓ **Model-Agnostic** - Works with any of 16 AutoML models
✓ **Configurable** - Adjust thresholds on the fly
✓ **Safe** - 20% safety margin by default
✓ **Tracked** - Complete round history and statistics
✓ **Easy** - Just select option 7 and use defaults

## Test It First

Before running live, test the setup:
```bash
python test_model_listener.py
```

This verifies:
- Game configuration is loaded
- Components are initialized
- Supabase connection works
- Everything is ready

## Next Steps

1. Run `python main.py`
2. Select option 7
3. Press Enter at all prompts (uses defaults)
4. Watch signals come through in real-time
5. Press Ctrl+C to stop and see statistics

---

**Status:** Production Ready ✓
**Model Support:** 16 AutoML models
**Speed:** <100ms real-time
**Credentials:** Pre-configured
