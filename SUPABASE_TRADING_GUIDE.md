# Supabase Automated Trading System - Complete Guide

## Overview

The Supabase-based automated trading system listens to the `analytics_round_signals` table and executes trades based on:
1. **ML Model predictions** (RandomForest, NeuralNet, XGBoost, Ensemble, Custom)
2. **Confidence levels** (0-100%) - determines trade eligibility
3. **Expected multipliers** - target for cashout

Unlike the WebSocket system which reacts to external signals, this system **polls the Supabase table** for new signals and executes them with confidence-based filtering.

---

## Architecture

### Components

#### 1. SupabaseSignalListener (`supabase_signal_listener.py`)
Polls the Supabase `analytics_round_signals` table for new signals.

**Features:**
- Async polling-based signal retrieval
- Automatic ID tracking to avoid reprocessing
- Payload JSON parsing (handles both string and dict formats)
- Confidence percentage extraction ("10%" → 10.0)
- Range parsing ("6.30-9.46" → min:6.30, max:9.46)
- Multiple model support (RandomForest, NeuralNet, etc.)
- Signal validation (round_id > 0, multiplier > 0, confidence 0-100)

#### 2. SupabaseExecutor (`supabase_trading_executor.py`)
Executes trades with confidence-based decision logic.

**Features:**
- Confidence threshold filtering
- Three confidence strategies: Conservative, Moderate, Aggressive
- Confidence-adjusted target multipliers
- Automatic bet placement via GameActions
- Real-time multiplier monitoring
- Conditional cashout execution
- Comprehensive execution record tracking

#### 3. SupabaseAutomatedTradingSystem (`supabase_automated_trading.py`)
Orchestrates listener and executor.

**Features:**
- Unified system initialization
- Async signal processing loop
- Status reporting and statistics
- Integration with all components
- Test mode support
- Configurable polling interval

---

## Signal Format

### Database Table: analytics_round_signals

```sql
CREATE TABLE public.analytics_round_signals (
  id BIGSERIAL PRIMARY KEY,
  round_id BIGINT NOT NULL,
  multiplier NUMERIC NOT NULL,  -- Expected multiplier
  model_name TEXT NOT NULL,      -- e.g., "RandomForest"
  model_output JSONB,            -- Model output data
  confidence NUMERIC,            -- 0-100 confidence percentage
  metadata JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  payload TEXT                   -- JSON string
);
```

### Payload JSON Structure

```json
{
  "modelName": "RandomForest",
  "id": 681,
  "expectedOutput": 7.88,
  "confidence": "10%",
  "range": "6.30-9.46"
}
```

### Extracted Fields

From **table columns:**
- `round_id` - Unique round identifier
- `multiplier` - Target multiplier for cashout
- `model_name` - ML model used (must be in ModelName enum)
- `confidence` - Confidence percentage (0-100)

From **payload JSON:**
- `modelName` - Model name (validates against table's model_name)
- `expectedOutput` - Expected game output (6.30-9.46 range)
- `confidence` - Confidence with optional "%" suffix
- `range` - Min-max range (e.g., "6.30-9.46")

---

## Supported Models

```python
class ModelName(Enum):
    RANDOM_FOREST = "RandomForest"
    NEURAL_NET = "NeuralNet"
    XGBOOST = "XGBoost"
    ENSEMBLE = "Ensemble"
    CUSTOM = "Custom"
```

**Adding New Models:**
1. Add to ModelName enum in `supabase_signal_listener.py`
2. Signal parsing automatically supports it
3. Optionally add model-specific logic in SupabaseExecutor

---

## Confidence Strategies

### Conservative (Threshold: 80%)
- Only trades with very high confidence
- Adjusts target multiplier DOWN for lower confidence
- Best for: Capital preservation, consistent wins

### Moderate (Threshold: 60%) - Default
- Balanced approach
- Trades when confidence is above 60%
- Minimal target adjustment
- Best for: General use, balanced risk/reward

### Aggressive (Threshold: 40%)
- Trades more frequently
- Allows lower confidence signals
- Adjusts target multiplier UP for high confidence
- Best for: Maximum profit potential, higher risk tolerance

### Confidence-Based Adjustment

```python
# Conservative: Lower target for low-confidence signals
if confidence < 60%:
    target = target - ((60 - confidence) / 100 * 0.1)

# Aggressive: Higher target for high-confidence signals
if confidence > 80%:
    target = target + ((confidence - 80) / 100 * 0.1)
```

---

## Usage

### Basic Setup

```python
import asyncio
from config import load_game_config
from supabase_automated_trading import run_supabase_automated_trading

async def main():
    config = load_game_config()
    if not config or not config.is_valid():
        print("Error: Invalid game configuration")
        return

    await run_supabase_automated_trading(
        game_config=config,
        supabase_url="https://your-project.supabase.co",
        supabase_key="your-anon-key",
        poll_interval=5.0,                    # Check every 5 seconds
        confidence_strategy="moderate",       # Moderate strategy
        enable_trading=True,                  # Execute real trades
        test_mode=False
    )

if __name__ == "__main__":
    asyncio.run(main())
```

### Test Mode (Safe)

```python
await run_supabase_automated_trading(
    game_config=config,
    supabase_url="https://your-project.supabase.co",
    supabase_key="your-anon-key",
    confidence_strategy="moderate",
    enable_trading=False,    # Dry run
    test_mode=True
)
```

### Different Strategies

```python
# Conservative - only high-confidence signals
await run_supabase_automated_trading(
    game_config=config,
    supabase_url="...",
    supabase_key="...",
    confidence_strategy="conservative",
    enable_trading=True
)

# Aggressive - more frequent trades
await run_supabase_automated_trading(
    game_config=config,
    supabase_url="...",
    supabase_key="...",
    confidence_strategy="aggressive",
    enable_trading=True
)
```

---

## Execution Flow

### 1. Signal Reception
```
Supabase Table
    ↓
Listen task polls every 5s
    ↓
Query: SELECT * FROM analytics_round_signals WHERE id > last_checked_id
    ↓
Parse row to ModelSignal
    ↓
Extract payload JSON
    ↓
Validate signal
    ↓
Queue signal
```

### 2. Execution
```
Get signal from queue
    ↓
Check confidence threshold
    ↓
IF confidence >= threshold:
  Place bet (GameActions.click_bet_button)
    ↓
  Wait for bet confirmation
    ↓
  Monitor multiplier every 0.1s
    ↓
  IF current >= target:
    Execute cashout
  ELSE IF timeout (60s):
    Force cashout
  ELSE IF crash (< 1.0):
    Skip cashout
    ↓
  Record execution
ELSE:
  Skip signal (confidence too low)
  Record as skipped
```

### 3. Record Tracking

Each execution creates a `SupabaseExecutionRecord`:
- Signal details (round_id, model_name, confidence)
- Execution status (pending, placed_bet, monitoring, cashout_executed, failed, skipped)
- Timing (bet_placed_at, cashout_executed_at)
- Results (bet_result, cashout_result)
- Multipliers (actual_multiplier_at_cashout, max_multiplier_reached)
- Error messages

---

## Statistics & Reporting

### Execution Summary

```python
system = SupabaseAutomatedTradingSystem(...)
await system.start()
# ... after some trading ...
summary = system.executor.get_execution_summary()

# Output:
{
    'total_executions': 10,
    'successful': 8,           # Cashout executed
    'skipped': 1,              # Confidence too low
    'failed': 1,               # Error during execution
    'success_rate': 80.0,      # Percentage
    'records': [...]           # All execution records
}
```

### System Status

```python
status = system.get_system_status()

# Output:
{
    'running': True,
    'enable_trading': True,
    'confidence_strategy': 'moderate',
    'poll_interval': 5.0,
    'listener': {
        'signals_received': 10,
        'errors': 0,
        'queue_size': 0,
        'last_checked_id': 1234
    },
    'executor': {
        'total_executions': 10,
        'successful': 8,
        'skipped': 1,
        'failed': 1,
        'success_rate': 80.0
    },
    'game_actions': {
        'total_clicks': 18,
        'successful': 18,
        'failed': 0,
        'success_rate': 100.0
    }
}
```

---

## Model-Specific Logic

### RandomForest Model

```python
# Default handling - uses confidence as-is
# High confidence = high probability of correct prediction
# Low confidence = uncertain prediction
```

### Neural Network Model

```python
# Can be added in future
# May require different confidence interpretation
```

### XGBoost Model

```python
# Can be added in future
# May use confidence thresholds differently
```

### Ensemble Model

```python
# Combination of multiple models
# Confidence represents consensus level
```

### Adding Model-Specific Logic

To add model-specific behavior:

```python
# In supabase_trading_executor.py
def _get_target_multiplier(self, signal: ModelSignal) -> float:
    target = signal.multiplier

    # Model-specific adjustments
    if signal.model_name == "RandomForest":
        # RF-specific logic
        pass
    elif signal.model_name == "NeuralNet":
        # NN-specific logic
        pass
    elif signal.model_name == "XGBoost":
        # XGB-specific logic
        pass

    return target
```

---

## Configuration Example

### game_config.json (with Supabase ready)

```json
{
  "balance_region": {
    "x1": 100,
    "y1": 50,
    "x2": 300,
    "y2": 100
  },
  "multiplier_region": {
    "x1": 117,
    "y1": 1014,
    "x2": 292,
    "y2": 1066
  },
  "bet_button_point": {
    "x": 640,
    "y": 900
  }
}
```

### Environment Variables (for Supabase credentials)

Create `.env` file:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

Load in code:
```python
import os
from dotenv import load_dotenv

load_dotenv()
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
```

---

## Error Handling

### Invalid Signal
```
Status: FAILED
Error: "Invalid signal data"
→ Continues listening for next signal
→ Logged and tracked in records
```

### Confidence Too Low
```
Status: SKIPPED
Error: "Confidence 45% below threshold 60%"
→ Signal not executed
→ Tracked separately from failures
→ Listening continues
```

### Bet Placement Failed
```
Status: FAILED
Error: "Bet placement failed"
→ Does not attempt monitoring
→ Execution stops
→ Continues to next signal
```

### Multiplier Read Error
```
→ Retries with 0.1s delay
→ Continues monitoring
→ If timeout (60s), forces cashout
→ If crash detected (< 1.0), stops
```

### Game Crashed
```
Status: FAILED
Error: "Game crashed"
→ Detected when multiplier < 1.0
→ Does not execute cashout
→ Prevents loss recovery
```

---

## Performance Characteristics

```
Component          | Operation        | Time
───────────────────────────────────────────
Supabase Query     | Poll table       | ~100-200ms
JSON Parsing       | Parse payload    | <1ms
Signal Validation  | Check fields     | <1ms
Confidence Filter  | Compare to threshold | <1ms
Bet Placement      | Click + delays   | 0.8s
Multiplier Read    | OCR read         | 100-200ms
Monitoring Loop    | Per iteration    | 0.1s
Cashout Execution  | Click + delays   | 0.8s
───────────────────────────────────────────
Total per trade    | End-to-end       | 2-60s
Polling cycle      | Full loop        | 5s (default)
```

---

## Monitoring & Logging

### Enable Debug Logging

In `supabase_signal_listener.py`:
```python
self._log(f"...", "DEBUG")  # Add DEBUG messages
```

In `supabase_trading_executor.py`:
```python
self._log(f"...", "DEBUG")  # Add DEBUG messages
```

### Log Output Example

```
[14:23:45] SUPABASE_LISTENER INFO: Starting signal listener (poll interval: 5.0s)
[14:23:50] SUPABASE_LISTENER INFO: Fetching new signals...
[14:23:51] SUPABASE_LISTENER INFO: Signal #1: Signal(Round: 1234, Model: RandomForest, Target: 7.88x, Confidence: 85%)
[14:23:51] SUPABASE_EXECUTOR INFO: Processing signal: Round 1234, Model: RandomForest, Target: 7.88x, Confidence: 85%
[14:23:51] SUPABASE_EXECUTOR INFO: Placing bet for round 1234...
[14:23:52] SUPABASE_EXECUTOR DEBUG: Target multiplier: 7.88x (confidence: 85%)
[14:23:52] SUPABASE_EXECUTOR INFO: Monitoring for multiplier target: 7.88x (max wait: 60s)
[14:23:53] SUPABASE_EXECUTOR DEBUG: Current: 1.15x | Target: 7.88x | Max: 1.15x
[14:23:54] SUPABASE_EXECUTOR DEBUG: Current: 2.30x | Target: 7.88x | Max: 2.30x
...
[14:24:02] SUPABASE_EXECUTOR DEBUG: Current: 7.88x | Target: 7.88x | Max: 7.88x
[14:24:02] SUPABASE_EXECUTOR INFO: Target multiplier reached! (7.88x >= 7.88x)
[14:24:02] SUPABASE_EXECUTOR INFO: Executing cashout at 7.88x
[14:24:03] SUPABASE_EXECUTOR INFO: Cashout successful at 7.88x
[14:24:03] SUPABASE_AUTO_TRADE INFO: Execution completed - Status: cashout_executed, Multiplier: 7.88x
```

---

## Troubleshooting

### Signals Not Being Fetched

**Check:**
1. Supabase URL is correct
2. Supabase key is valid
3. Database connection is active
4. `analytics_round_signals` table exists
5. Rows are being inserted into table

**Debug:**
```python
# Check connection manually
from supabase_client import SupabaseLogger

logger = SupabaseLogger(supabase_url, supabase_key)
response = logger.client.table('analytics_round_signals').select('*').limit(1).execute()
print(response)
```

### Signals Being Skipped

**Check:**
1. Confidence threshold matches your strategy
2. Model name in table matches enum value
3. Confidence percentage format is correct

**Example:**
- Strategy: "moderate" → threshold 60%
- Signal confidence: 45%
- Result: SKIPPED (45% < 60%)

**Increase Trades:**
Change strategy to "aggressive" or lower threshold in code.

### No Multiplier Readings

**Check:**
1. Multiplier region is configured correctly
2. Region is visible on screen
3. Tesseract is installed
4. Region captures multiplier clearly
5. Test with: `python main.py → Test Configuration`

### Clicks Not Working

**Check:**
1. Button coordinates are correct
2. Window is in focus
3. PyAutoGUI failsafe not triggered
4. No other application is using mouse

### Cashout Not Executing

**Check:**
1. Target multiplier is realistic
2. Game hasn't crashed (multiplier < 1.0)
3. Timeout (60s) isn't being exceeded
4. Cashout button coordinates match bet button

---

## Advanced Usage

### Custom Polling Interval

```python
await run_supabase_automated_trading(
    game_config=config,
    supabase_url="...",
    supabase_key="...",
    poll_interval=3.0,  # Check every 3 seconds (faster)
    # or
    poll_interval=10.0  # Check every 10 seconds (slower)
)
```

### Multiple Instances

```python
# Can run multiple systems simultaneously
# Each with different confidence strategies

system1 = SupabaseAutomatedTradingSystem(
    game_config=config,
    supabase_url="...",
    supabase_key="...",
    confidence_strategy="conservative"
)

system2 = SupabaseAutomatedTradingSystem(
    game_config=config,
    supabase_url="...",
    supabase_key="...",
    confidence_strategy="aggressive"
)

# Start both
await asyncio.gather(
    system1.start(),
    system2.start()
)
```

### Listener Callbacks

```python
listener = SupabaseSignalListener(supabase_logger)

def on_signal_received(signal):
    print(f"Signal: {signal.model_name} - {signal.confidence}%")

listener.add_listener(on_signal_received)
```

---

## Safety Precautions

1. **Test First**: Always use `test_mode=True` initially
2. **Monitor Closely**: Watch first few real trades
3. **Start Conservative**: Use "conservative" strategy initially
4. **Gradual Rollout**: Increase trading frequency slowly
5. **Keep Logs**: Save execution records for analysis
6. **Have Failsafe**: Mouse ready at screen corner
7. **Validate Signals**: Check table is receiving correct data
8. **Verify Models**: Confirm model names are in enum

---

## Summary

The Supabase automated trading system provides:

✓ Polling-based signal reception from Supabase
✓ Confidence-based trading decisions
✓ Multi-model support (RandomForest, NeuralNet, XGBoost, Ensemble)
✓ Three confidence strategies (Conservative, Moderate, Aggressive)
✓ Automatic bet placement and cashout
✓ Real-time multiplier monitoring
✓ Comprehensive execution tracking
✓ Detailed statistics and reporting
✓ Test mode for safe development
✓ Production-ready automation

Ready for Supabase integration!
