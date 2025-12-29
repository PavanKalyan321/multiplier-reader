# Supabase Automated Trading - Quick Start

## 5-Minute Setup

### 1. Verify Configuration (1 min)
```bash
python main.py
# Choose "3. Test Configuration"
# Verify balance and multiplier readings work
```

### 2. Create Supabase Table (2 min)

Run this SQL in Supabase SQL Editor:

```sql
CREATE TABLE public.analytics_round_signals (
  id BIGSERIAL PRIMARY KEY,
  round_id BIGINT NOT NULL,
  multiplier NUMERIC NOT NULL,
  model_name TEXT NOT NULL,
  model_output JSONB,
  confidence NUMERIC,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  payload TEXT
);

-- Optional: Create index for faster queries
CREATE INDEX idx_analytics_round_signals_id
ON public.analytics_round_signals(id);
```

### 3. Get Your Credentials (1 min)

In Supabase Dashboard:
- Settings → API
- Copy: **Project URL** (e.g., `https://your-project.supabase.co`)
- Copy: **anon public key** (API Key)

### 4. Create Test File (`run_supabase.py`)

```python
import asyncio
from config import load_game_config
from supabase_automated_trading import run_supabase_automated_trading

async def main():
    config = load_game_config()

    print("\n" + "="*60)
    print("SUPABASE AUTOMATED TRADING - TEST MODE".center(60))
    print("="*60 + "\n")

    await run_supabase_automated_trading(
        game_config=config,
        supabase_url="https://your-project.supabase.co",  # Your URL
        supabase_key="your-anon-key",                      # Your API Key
        poll_interval=5.0,
        confidence_strategy="moderate",
        enable_trading=False,  # TEST MODE - no real trades
        test_mode=True
    )

if __name__ == "__main__":
    asyncio.run(main())
```

### 5. Insert Test Data

In Supabase SQL Editor:

```sql
-- Insert a test signal
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

### 6. Run Test

```bash
python run_supabase.py
```

Watch for:
```
[14:23:45] SUPABASE_AUTO_TRADE INFO: System started successfully
[14:23:50] SUPABASE_LISTENER INFO: Signal #1: Signal(Round: 1001, Model: RandomForest, Target: 7.50x, Confidence: 85%)
[14:23:51] SUPABASE_EXECUTOR INFO: Processing signal...
```

---

## What's Happening

1. System polls Supabase every 5 seconds
2. Finds new rows in `analytics_round_signals`
3. Extracts signal data and payload JSON
4. Checks if confidence meets threshold (60% for moderate)
5. If yes → Places bet → Monitors multiplier → Executes cashout
6. If no → Skips signal and logs it

---

## Signal Anatomy

### Table Data
```
round_id:     1001
multiplier:   7.50         ← Target for cashout
model_name:   RandomForest
confidence:   85           ← Confidence percentage
```

### Payload JSON
```json
{
  "modelName": "RandomForest",    ← Model identifier
  "expectedOutput": 7.50,          ← Expected range
  "confidence": "85%",             ← Confidence with %
  "range": "6.30-9.46"             ← Min-max range
}
```

### Confidence Strategies

| Strategy | Threshold | Use Case |
|----------|-----------|----------|
| Conservative | 80% | Only high-confidence signals |
| Moderate | 60% | Balanced (default) |
| Aggressive | 40% | More frequent trades |

---

## Confidence Examples

### Signal 1: High Confidence
```
confidence: 90%
multiplier: 8.00

Moderate strategy (60% threshold)
→ EXECUTES (90% >= 60%)
→ Places bet
→ Monitors 8.00x multiplier
→ Cashout executed
```

### Signal 2: Low Confidence
```
confidence: 45%
multiplier: 5.50

Moderate strategy (60% threshold)
→ SKIPPED (45% < 60%)
→ Not executed
→ Logged as skipped
→ Listening continues
```

---

## Adding Signals to Database

### Manual Insert
```sql
INSERT INTO public.analytics_round_signals
(round_id, multiplier, model_name, confidence, payload)
VALUES (
  1002,
  6.75,
  'XGBoost',
  72,
  '{"modelName": "XGBoost", "expectedOutput": 6.75, "confidence": "72%", "range": "5.00-8.50"}'
);
```

### Batch Insert
```sql
INSERT INTO public.analytics_round_signals
(round_id, multiplier, model_name, confidence, payload)
VALUES
(1003, 7.50, 'RandomForest', 85, '{"modelName": "RandomForest", "expectedOutput": 7.50, "confidence": "85%", "range": "6.30-9.46"}'),
(1004, 6.00, 'NeuralNet', 78, '{"modelName": "NeuralNet", "expectedOutput": 6.00, "confidence": "78%", "range": "5.00-7.50"}'),
(1005, 5.50, 'XGBoost', 65, '{"modelName": "XGBoost", "expectedOutput": 5.50, "confidence": "65%", "range": "4.50-6.50"}');
```

---

## Monitoring Execution

### Check System Status
```python
system = SupabaseAutomatedTradingSystem(...)
await system.start()
# ... after some signals ...
system.print_system_status()
```

### Output Example
```
[14:24:15] Supabase Automated Trading System Status:
[14:24:15] Running: True
[14:24:15] Trading Enabled: False (test_mode)
[14:24:15] Confidence Strategy: moderate

[14:24:15] Listener Status:
[14:24:15]   Signals received: 3
[14:24:15]   Errors: 0
[14:24:15]   Queue size: 0

[14:24:15] Executor Status:
[14:24:15]   Total executions: 3
[14:24:15]   Successful: 2
[14:24:15]   Skipped: 0
[14:24:15]   Failed: 1
[14:24:15]   Success rate: 66.7%
```

---

## Production Setup

### Update run_supabase.py
```python
await run_supabase_automated_trading(
    game_config=config,
    supabase_url="https://your-project.supabase.co",
    supabase_key="your-anon-key",
    poll_interval=5.0,
    confidence_strategy="moderate",
    enable_trading=True,      # REAL TRADING!
    test_mode=False
)
```

### Choose Strategy
```python
# Conservative - high confidence only
confidence_strategy="conservative"

# Moderate - balanced (default)
confidence_strategy="moderate"

# Aggressive - more frequent
confidence_strategy="aggressive"
```

---

## Supported Models

Current:
- RandomForest
- NeuralNet
- XGBoost
- Ensemble
- Custom

Using model in insert:
```sql
INSERT INTO public.analytics_round_signals
(round_id, multiplier, model_name, confidence, payload)
VALUES (
  1006,
  7.25,
  'Ensemble',  ← Model name here
  82,
  '{"modelName": "Ensemble", "expectedOutput": 7.25, "confidence": "82%", "range": "6.00-8.50"}'
);
```

---

## Troubleshooting

### No Signals Detected
1. Check table exists: `SELECT COUNT(*) FROM analytics_round_signals;`
2. Check URL and API key are correct
3. Check poll interval is set to reasonable value (5-10s)
4. Check logs for connection errors

### All Signals Skipped
1. Check confidence values in table (vs threshold)
2. Check confidence_strategy setting
3. Example: If strategy="moderate" (60%), signals with <60% confidence will skip

### Clicks Not Working
1. Run `python main.py → Test Configuration` first
2. Verify button coordinates are correct
3. Try test_mode=True first (no clicking)

### Multiplier Not Reading
1. Run `python main.py → Test Configuration`
2. Verify multiplier region is configured
3. Check region is visible on screen

---

## File Overview

| File | Purpose |
|------|---------|
| `supabase_signal_listener.py` | Polls Supabase table |
| `supabase_trading_executor.py` | Executes trades with confidence logic |
| `supabase_automated_trading.py` | Orchestrates system |
| `supabase_client.py` | Supabase connection (existing) |
| `config.py` | Game configuration (existing) |
| `game_actions.py` | Click automation (existing) |
| `multiplier_reader.py` | Multiplier OCR (existing) |

---

## Safety Checklist

Before going live:

- [ ] Configuration verified (Test Configuration passes)
- [ ] Test mode works (signals detected)
- [ ] Signals are inserted correctly
- [ ] Confidence strategy is set appropriately
- [ ] Model names match table values
- [ ] Multiplier readings are accurate
- [ ] Clicks are working (bet and cashout)
- [ ] First few trades monitored closely

---

## Example Workflow

### Session 1: Setup & Test
1. Run `python main.py` → Configure Regions
2. Set balance, multiplier, button regions
3. Run test_mode=True with sample data
4. Verify signals are processed
5. Check execution logs

### Session 2: Live Trading
1. Change `enable_trading=True` in script
2. Start with conservative strategy
3. Monitor first 5-10 trades closely
4. Watch execution logs for errors
5. Gradually increase signal frequency

### Session 3: Optimization
1. Review success rate and statistics
2. Adjust confidence strategy if needed
3. Fine-tune polling interval
4. Add more signals to table
5. Monitor performance

---

## Key Differences from WebSocket

| Feature | WebSocket | Supabase |
|---------|-----------|----------|
| Signal Source | External API | Your database |
| Delivery | Immediate | Polled every 5s |
| Control | API controls signals | You insert rows |
| Testing | Use test server | Use SQL inserts |
| Confidence | Not used | Used for filtering |
| Models | Single | Multiple models |
| Scalability | Limited | Easy to scale |

---

## Next Steps

1. ✓ Create Supabase table
2. ✓ Get credentials
3. ✓ Insert test signal
4. ✓ Run test_mode=True
5. ✓ Verify signals are processed
6. ✓ Change to enable_trading=True
7. ✓ Monitor live trades
8. ✓ Adjust strategy as needed

---

## Support

Check logs for:
- `[SUPABASE_LISTENER INFO]` - Signal reception
- `[SUPABASE_EXECUTOR INFO]` - Trade execution
- `[SUPABASE_AUTO_TRADE INFO]` - System events

Enable DEBUG level for more details:
- Change `INFO` to `DEBUG` in log calls
- See detailed step-by-step execution
