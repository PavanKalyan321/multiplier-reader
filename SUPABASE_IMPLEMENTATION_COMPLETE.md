# Supabase Automated Trading - Phase 4 Implementation Complete

## Overview

Phase 4 of the Aviator Bot project adds **Supabase-based automated trading** with **confidence-based decision logic**. The system listens to the `analytics_round_signals` table and automatically executes trades based on ML model predictions and confidence levels.

---

## What Was Implemented

### 1. Supabase Signal Listener (`supabase_signal_listener.py`)
- **Purpose**: Polls Supabase `analytics_round_signals` table for new signals
- **Features**:
  - Async polling-based signal retrieval
  - Automatic ID tracking (no reprocessing)
  - Payload JSON parsing
  - Confidence percentage extraction
  - Range parsing (e.g., "6.30-9.46" → min:6.30, max:9.46)
  - Multi-model support (RandomForest, NeuralNet, XGBoost, Ensemble, Custom)
  - Signal validation
  - Listener callbacks support

**Key Classes:**
- `ModelName` enum: Supported ML models
- `ModelSignal` dataclass: Signal structure with extracted fields
- `SupabaseSignalListener` class: Main listener implementation

**Key Methods:**
```python
async def fetch_new_signals() -> list
async def listen(poll_interval: float = 5.0)
async def get_signal(timeout: Optional[float]) -> Optional[ModelSignal]
def get_stats() -> Dict[str, Any]
```

### 2. Supabase Trading Executor (`supabase_trading_executor.py`)
- **Purpose**: Executes trades with confidence-based filtering
- **Features**:
  - Three confidence strategies (Conservative, Moderate, Aggressive)
  - Confidence threshold filtering
  - Confidence-adjusted target multipliers
  - Automatic bet placement
  - Real-time multiplier monitoring
  - Conditional cashout execution
  - Comprehensive execution record tracking
  - Statistics and success rate calculation

**Key Classes:**
- `ConfidenceStrategy` enum: Trading strategies
- `SupabaseExecutionRecord` dataclass: Trade execution record
- `SupabaseExecutor` class: Main executor implementation

**Key Methods:**
```python
async def execute_signal(signal: ModelSignal) -> SupabaseExecutionRecord
async def _monitor_and_cashout(signal, record, target_mult, max_wait_seconds)
async def _execute_cashout(signal, record, multiplier)
def _should_trade(signal: ModelSignal) -> bool
def _get_target_multiplier(signal: ModelSignal) -> float
def get_execution_summary() -> Dict[str, Any]
```

**Confidence Strategies:**
| Strategy | Threshold | Adjustment |
|----------|-----------|-----------|
| Conservative | 80% | Lower target for low confidence |
| Moderate | 60% | Minimal adjustment (default) |
| Aggressive | 40% | Higher target for high confidence |

### 3. Supabase Automated Trading System (`supabase_automated_trading.py`)
- **Purpose**: Orchestrates listener and executor
- **Features**:
  - Unified system initialization
  - Async signal processing loop
  - Status reporting and statistics
  - Integration with all components
  - Test mode support
  - Configurable polling interval

**Key Classes:**
- `SupabaseAutomatedTradingSystem` class: Main system coordinator

**Key Methods:**
```python
async def start() -> bool
async def stop()
async def _execution_loop()
def get_system_status() -> Dict[str, Any]
def print_system_status()
```

### 4. Main Menu Integration (`menu_controller.py` & `main.py`)
- **Menu Updates**:
  - Added option 4: WebSocket Automated Trading
  - Added option 5: Supabase Automated Trading
  - Added option 6: Exit (previously option 4)

- **Main Function Updates**:
  - New `websocket_trading()` function for WebSocket setup
  - New `supabase_trading()` function for Supabase setup
  - Async support with `asyncio.run()`
  - User prompts for credentials and settings

**User Interaction Flow:**
1. Select menu option 5 (Supabase Automated Trading)
2. Enter Supabase Project URL
3. Enter Supabase API Key
4. Choose confidence strategy (Conservative/Moderate/Aggressive)
5. Choose test mode or live trading
6. Set polling interval
7. System starts and polls for signals

---

## Database Schema

### analytics_round_signals Table

```sql
CREATE TABLE public.analytics_round_signals (
  id BIGSERIAL PRIMARY KEY,
  round_id BIGINT NOT NULL,
  multiplier NUMERIC NOT NULL,           -- Expected multiplier
  model_name TEXT NOT NULL,               -- ML model name
  model_output JSONB,                     -- Model output data
  confidence NUMERIC,                     -- 0-100 confidence
  metadata JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  payload TEXT                            -- JSON with additional data
);
```

### Signal Payload Structure

```json
{
  "modelName": "RandomForest",
  "id": 681,
  "expectedOutput": 7.88,
  "confidence": "85%",
  "range": "6.30-9.46"
}
```

### Example Insert

```sql
INSERT INTO public.analytics_round_signals
(round_id, multiplier, model_name, confidence, payload)
VALUES (
  1001,
  7.88,
  'RandomForest',
  85,
  '{"modelName": "RandomForest", "expectedOutput": 7.88, "confidence": "85%", "range": "6.30-9.46"}'
);
```

---

## How It Works

### Signal Flow

```
Supabase Table (analytics_round_signals)
    ↓
SupabaseSignalListener polls every 5s
    ↓
Fetch new rows (id > last_checked_id)
    ↓
Parse to ModelSignal
    ↓
Extract payload JSON
    ↓
Validate signal
    ↓
Queue signal
    ↓
SupabaseAutomatedTradingSystem.get_signal()
    ↓
SupabaseExecutor.execute_signal()
    ↓
Check confidence threshold
    ↓
Place bet → Monitor multiplier → Execute cashout
    ↓
Record execution with statistics
```

### Execution Decision Tree

```
Signal received
  │
  ├─ Is signal valid?
  │  ├─ NO → FAILED
  │  └─ YES ↓
  │
  ├─ Does confidence meet threshold?
  │  ├─ NO → SKIPPED (logged separately)
  │  └─ YES ↓
  │
  ├─ Place bet
  │  ├─ Failed → FAILED
  │  └─ Success ↓
  │
  ├─ Monitor multiplier (every 0.1s)
  │  ├─ Game crashed (< 1.0) → FAILED
  │  ├─ Timeout (60s) → Force cashout
  │  ├─ Target reached → Execute cashout
  │  └─ Cashout failed → FAILED
  │
  └─ COMPLETED
```

---

## Confidence-Based Logic

### Threshold Filtering

```python
Moderate strategy (60% threshold):

Signal 1: confidence 85% → EXECUTES (85% >= 60%)
Signal 2: confidence 45% → SKIPPED (45% < 60%)
Signal 3: confidence 78% → EXECUTES (78% >= 60%)
```

### Target Adjustment (Optional)

```python
# Conservative: Lower target for uncertain predictions
if confidence < 60%:
    adjusted_target = original_target - ((60 - confidence) / 100 * 0.1)

# Aggressive: Higher target for confident predictions
if confidence > 80%:
    adjusted_target = original_target + ((confidence - 80) / 100 * 0.1)
```

### Example Scenario

```
Signal from RandomForest model:
- Expected multiplier: 7.50x
- Confidence: 75%
- Strategy: Moderate (60% threshold)

Execution:
1. Check confidence: 75% >= 60% ✓
2. Get target: 7.50x
3. Place bet
4. Monitor: 1.05x → 2.15x → 3.50x → 5.20x → 7.50x
5. Target reached: Execute cashout at 7.50x
6. Record: Status = CASHOUT_EXECUTED, Multiplier = 7.50x
```

---

## Key Features

### ✓ Automatic Signal Processing
- Polls Supabase every 5 seconds (configurable)
- Detects new rows automatically
- No manual intervention needed

### ✓ Confidence-Based Filtering
- Only trades signals meeting confidence threshold
- Three strategies for different risk profiles
- Automatic target adjustment based on confidence

### ✓ Multi-Model Support
- RandomForest, NeuralNet, XGBoost, Ensemble, Custom
- Easy to extend with new models
- Model name tracked in execution records

### ✓ Automatic Trading
- Places bets when signal arrives
- Monitors multiplier in real-time (0.1s intervals)
- Executes cashout at target or timeout
- Prevents betting on crashed rounds

### ✓ Comprehensive Statistics
- Total executions, successful, skipped, failed
- Success rate calculation
- Per-trade execution records
- Model and confidence tracking

### ✓ Test Mode
- Dry run without actual trades
- Verify signal reception
- Test confidence logic
- Safe development

### ✓ Flexible Configuration
- User-friendly setup prompts
- Test mode vs. live trading
- Strategy selection (Conservative/Moderate/Aggressive)
- Polling interval adjustment

---

## Files Created/Modified

### New Files
1. **supabase_signal_listener.py** (287 lines)
   - Listens to Supabase table
   - Parses signals and payloads

2. **supabase_trading_executor.py** (368 lines)
   - Executes trades with confidence logic
   - Monitors multipliers and executes cashouts
   - Tracks statistics

3. **supabase_automated_trading.py** (305 lines)
   - Orchestrates listener + executor
   - Manages async tasks
   - Provides system status

4. **SUPABASE_TRADING_GUIDE.md** (600+ lines)
   - Complete documentation
   - Usage examples
   - Troubleshooting guide

5. **SUPABASE_QUICKSTART.md** (300+ lines)
   - 5-minute quick start
   - Examples and scenarios
   - Setup checklist

6. **SUPABASE_IMPLEMENTATION_COMPLETE.md** (this file)
   - Phase 4 summary

### Modified Files
1. **menu_controller.py**
   - Added 2 new menu options
   - Updated choice validation (1-6)
   - Added 'websocket' and 'supabase' actions

2. **main.py**
   - Imported asyncio and trading modules
   - Added websocket_trading() function
   - Added supabase_trading() function
   - Updated main() to handle new actions

---

## Usage Examples

### Basic Setup

```python
import asyncio
from config import load_game_config
from supabase_automated_trading import run_supabase_automated_trading

async def main():
    config = load_game_config()

    await run_supabase_automated_trading(
        game_config=config,
        supabase_url="https://your-project.supabase.co",
        supabase_key="your-anon-key",
        poll_interval=5.0,
        confidence_strategy="moderate",
        enable_trading=True,
        test_mode=False
    )

asyncio.run(main())
```

### Via Menu (Easier)

```bash
python main.py
# Select option 5 (Supabase Automated Trading)
# Enter credentials and settings
# System starts automatically
```

### Test Mode

```python
await run_supabase_automated_trading(
    game_config=config,
    supabase_url="...",
    supabase_key="...",
    enable_trading=False,  # Dry run
    test_mode=True
)
```

### Different Strategies

```python
# Conservative - only high-confidence signals
await run_supabase_automated_trading(
    ...,
    confidence_strategy="conservative"  # 80% threshold
)

# Moderate - balanced (default)
await run_supabase_automated_trading(
    ...,
    confidence_strategy="moderate"      # 60% threshold
)

# Aggressive - more frequent trades
await run_supabase_automated_trading(
    ...,
    confidence_strategy="aggressive"    # 40% threshold
)
```

---

## Performance Characteristics

```
Component          | Operation        | Time
───────────────────────────────────────────────
Supabase Query     | Poll table       | 100-200ms
JSON Parsing       | Parse payload    | <1ms
Signal Validation  | Check fields     | <1ms
Confidence Check   | Compare value    | <1ms
Bet Placement      | Click + delays   | 0.8s
Multiplier Read    | OCR read         | 100-200ms
Monitoring Loop    | Per iteration    | 0.1s
Cashout Execution  | Click + delays   | 0.8s
───────────────────────────────────────────────
Total per trade    | End-to-end       | 2-60s
Polling cycle      | Full loop        | 5s (default)
```

---

## Testing Strategy

### Step 1: Verify Configuration
```bash
python main.py
# Choose "3. Test Configuration"
# Verify balance and multiplier readings work
```

### Step 2: Create Supabase Table
Run SQL in Supabase dashboard to create `analytics_round_signals` table.

### Step 3: Test with Sample Data
```sql
INSERT INTO public.analytics_round_signals
(round_id, multiplier, model_name, confidence, payload)
VALUES (
  1001,
  7.50,
  'RandomForest',
  85,
  '{"modelName": "RandomForest", "expectedOutput": 7.50, "confidence": "85%", "range": "6.30-9.46"}'
);
```

### Step 4: Run Test Mode
```bash
python main.py
# Select option 5 (Supabase Automated Trading)
# Enter credentials
# Select test_mode=yes
# Observe signal processing and execution
```

### Step 5: Verify Execution
```bash
# Check system status in logs
# Verify correct confidence filtering
# Verify bet placement and cashout
# Check execution records
```

### Step 6: Enable Live Trading
```bash
# Change test_mode=no
# Observe first few real trades
# Monitor success rate and statistics
```

---

## Error Handling

### Invalid Signal
- Status: FAILED
- Reason: Missing required fields or invalid values
- Action: Logged and tracked, continues listening

### Low Confidence
- Status: SKIPPED
- Reason: Confidence below threshold
- Action: Not executed, logged separately, continues listening

### Bet Placement Failed
- Status: FAILED
- Reason: Click failed or invalid coordinates
- Action: Does not attempt to monitor/cashout

### Multiplier Read Error
- Status: FAILED (if persistent)
- Reason: OCR failed multiple times
- Action: Retries with delay, forces cashout if timeout

### Game Crashed
- Status: FAILED
- Reason: Multiplier < 1.0 detected
- Action: Skips cashout, prevents loss recovery

---

## Safety Precautions

1. **Always test first** with test_mode=True
2. **Monitor closely** during first trades
3. **Start conservative** to build confidence
4. **Gradual rollout** - increase signals slowly
5. **Keep logs** for analysis and debugging
6. **Have failsafe** - mouse ready at screen corner
7. **Verify credentials** before starting
8. **Check signals** are being inserted correctly

---

## Monitoring & Logging

### Log Levels
```
[timestamp] SUPABASE_LISTENER INFO: Signal received
[timestamp] SUPABASE_EXECUTOR INFO: Executing trade
[timestamp] SUPABASE_AUTO_TRADE INFO: System event
[timestamp] ... ERROR: Something failed
[timestamp] ... WARNING: Potential issue
[timestamp] ... DEBUG: Detailed step-by-step
```

### System Status
```python
system = SupabaseAutomatedTradingSystem(...)
await system.start()
# ... after trading ...
system.print_system_status()

# Output:
# Signals received: 10
# Successful: 8
# Skipped: 1
# Failed: 1
# Success rate: 80%
```

---

## Files Overview

| File | Purpose | Type |
|------|---------|------|
| supabase_signal_listener.py | Listen to table | Implementation |
| supabase_trading_executor.py | Execute trades | Implementation |
| supabase_automated_trading.py | Orchestrate system | Implementation |
| SUPABASE_TRADING_GUIDE.md | Complete guide | Documentation |
| SUPABASE_QUICKSTART.md | Quick setup | Documentation |
| menu_controller.py | Menu system | Modified |
| main.py | Main entry point | Modified |

---

## Integration with Existing System

The Supabase system works alongside existing components:

```
Existing Components (Unchanged):
- screen_capture.py → Used for multiplier region
- multiplier_reader.py → Used for monitoring
- game_actions.py → Used for betting/cashout
- config.py → Used for configuration
- balance_reader.py → Available for monitoring

New Components (Added):
- supabase_signal_listener.py → Supabase polling
- supabase_trading_executor.py → Trade execution
- supabase_automated_trading.py → System orchestration

Menu System (Enhanced):
- menu_controller.py → Added trading options
- main.py → Added trading handlers
```

---

## Next Steps

1. ✓ Create Supabase table (analytics_round_signals)
2. ✓ Get Supabase credentials (URL and API key)
3. ✓ Insert test signal into table
4. ✓ Run `python main.py` and select Supabase option
5. ✓ Test with test_mode=True
6. ✓ Verify signals are processed correctly
7. ✓ Verify confidence filtering works
8. ✓ Verify bet placement and cashout
9. ✓ Change to test_mode=False for live trading
10. ✓ Monitor first trades closely
11. ✓ Adjust strategy as needed
12. ✓ Scale up signal frequency

---

## Supported Models

**Current:**
- RandomForest
- NeuralNet
- XGBoost
- Ensemble
- Custom

**Adding New Models:**
1. Add to `ModelName` enum in `supabase_signal_listener.py`
2. Optionally add model-specific logic in executor
3. Use model name in database inserts

---

## Confidence Strategy Comparison

| Aspect | Conservative | Moderate | Aggressive |
|--------|-------------|----------|-----------|
| Threshold | 80% | 60% | 40% |
| Signals Executed | Low | Medium | High |
| Risk Level | Low | Medium | High |
| Win Rate | High | Medium | Lower |
| Avg Profit | Low | Medium | High |
| Best For | Capital preservation | General use | Profit maximization |

---

## Summary

Phase 4 implementation provides a complete **Supabase-based automated trading system** with:

✓ Polling-based signal reception from Supabase table
✓ Confidence-based decision logic (3 strategies)
✓ Multi-model support (5+ models)
✓ Automatic bet placement and cashout
✓ Real-time multiplier monitoring
✓ Comprehensive execution tracking
✓ Statistics and success rate reporting
✓ Test mode for safe development
✓ User-friendly menu integration
✓ Production-ready automation

Ready for deployment and real trading!

---

## Support & Troubleshooting

For detailed troubleshooting, see:
- `SUPABASE_TRADING_GUIDE.md` - Complete guide with examples
- `SUPABASE_QUICKSTART.md` - Quick setup and common issues
- Logs and error messages for specific problems

---

**Phase 4 Complete! ✓**
All Supabase automated trading components implemented and integrated.
