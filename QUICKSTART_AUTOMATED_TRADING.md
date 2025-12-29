# Quick Start - Automated Trading System

## 5-Minute Setup

### 1. Verify Configuration (1 min)
```bash
python main.py
# Choose "3. Test Configuration"
# Verify balance and multiplier readings work
```

### 2. Start Test Server (Terminal 1)
```bash
python websocket_test_server.py --mode interactive
```

### 3. Start Trader in Test Mode (Terminal 2)

Create file `run_test.py`:
```python
import asyncio
from config import load_game_config
from automated_trading import run_automated_trading

async def main():
    config = load_game_config()
    print("\n" + "="*60)
    print("AUTOMATED TRADING - TEST MODE".center(60))
    print("="*60 + "\n")

    await run_automated_trading(
        game_config=config,
        websocket_uri="ws://localhost:8765",
        test_mode=True,  # Safe - no real trades
        num_test_rounds=3
    )

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python run_test.py
```

### 4. Send Test Signals (Terminal 1)
```
> send 3
```

### 5. Watch Execution (Terminal 2)
```
[14:23:45] AUTO_TRADE INFO: Processing signal...
[14:23:46] EXECUTOR INFO: Placing bet...
[14:23:47] EXECUTOR INFO: Monitoring for multiplier target: 1.5x
[14:23:48] EXECUTOR DEBUG: Current: 1.15x | Target: 1.5x
[14:23:49] EXECUTOR DEBUG: Current: 1.50x | Target: 1.5x
[14:23:49] EXECUTOR INFO: Target multiplier reached!
[14:23:49] EXECUTOR INFO: Cashout successful at 1.50x
```

---

## Production Setup

### Connect to Your API

Replace WebSocket URI:
```python
await run_automated_trading(
    game_config=config,
    websocket_uri="ws://your_api_server:port",
    test_mode=False  # Real trading!
)
```

---

## Signal Format

Your API sends:
```json
{
  "timestamp": "2025-12-29T14:23:45.123456",
  "expectedRange": "1.0-3.0",
  "expectedMultiplier": "1.5",
  "bet": true,
  "roundId": "round_123456"
}
```

---

## What Happens Automatically

For each signal:

1. **[0s]** Receive signal
2. **[0.5s]** Wait (safety delay)
3. **[0.5s]** Click bet button
4. **[0.3s]** Wait (post-delay)
5. **[1+s]** Monitor multiplier every 0.1s
6. **[N.Ns]** Click cashout when target reached
7. **[+0.3s]** Record statistics

Total: 1-60 seconds per signal

---

## System Status

Check how many trades were executed:
```python
system = AutomatedTradingSystem(config)
await system.start()
# ... after some trading ...
system.print_system_status()
```

Output:
```
[14:24:15] Automated Trading System Status:
[14:24:15] Running: True
[14:24:15] Trading Enabled: True
[14:24:15] WebSocket Status:
[14:24:15]   Connected: True
[14:24:15]   Signals received: 3
[14:24:15]   Errors: 0
[14:24:15] Execution Status:
[14:24:15]   Total executions: 3
[14:24:15]   Successful: 3
[14:24:15]   Failed: 0
[14:24:15]   Success rate: 100.0%
```

---

## Troubleshooting

### WebSocket Connection Failed
```
Check:
1. Test server is running: python websocket_test_server.py
2. Port is correct: ws://localhost:8765
3. No firewall blocking
```

### Signals Not Executing
```
Check:
1. Bet button coordinates are correct
2. Window is in focus
3. Check logs for errors
```

### Wrong Multiplier Read
```
Check:
1. Multiplier region is configured correctly
2. Region is visible on screen
3. Test with: python main.py → Test Configuration
```

---

## Files Overview

| File | Purpose |
|------|---------|
| `websocket_listener.py` | Receives signals from API |
| `signal_executor.py` | Executes bets and cashouts |
| `automated_trading.py` | Main system |
| `websocket_test_server.py` | Test server for development |
| `game_actions.py` | Click automation |
| `multiplier_reader.py` | Multiplier OCR |
| `config.py` | Configuration management |

---

## Enable Debug Logging

For more detailed logs, modify these files:

In `websocket_listener.py`:
```python
self._log(f"...", "DEBUG")  # Add DEBUG level logs
```

In `signal_executor.py`:
```python
self._log(f"...", "DEBUG")  # Add DEBUG level logs
```

---

## Performance Metrics

- **Bet placement**: 0.8s
- **Multiplier reading**: 100-200ms
- **Monitoring loop**: 0.1s per iteration
- **Cashout execution**: 0.8s

Total per round: 1-60 seconds (depends on target multiplier)

---

## Safety Checks

Before going live:

- [ ] Configuration verified (Test Configuration passes)
- [ ] Test signals process correctly
- [ ] Bets are placed at right times
- [ ] Multiplier readings are accurate
- [ ] Cashouts execute at target
- [ ] Statistics track correctly

---

## Next: Connect to Real API

1. Get WebSocket URI from API provider
2. Verify signal format matches
3. Update WebSocket URI in code
4. Change `test_mode=False`
5. Monitor first few trades closely

---

## Full Example - Production Ready

```python
import asyncio
from config import load_game_config
from automated_trading import AutomatedTradingSystem

async def main():
    # Load configuration
    config = load_game_config()
    if not config or not config.is_valid():
        print("Error: Invalid configuration")
        return

    # Create system
    system = AutomatedTradingSystem(
        game_config=config,
        websocket_uri="ws://your_api_server:8765",  # Your API
        enable_trading=True  # Real trades
    )

    try:
        # Start
        if not await system.start():
            return

        print("\nAutomated Trading Running")
        print("Press Ctrl+C to stop\n")

        # Run until interrupted
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\nShutdown...")

    finally:
        # Stop and print status
        await system.stop()
        system.print_system_status()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## That's It!

Your automated trading system is ready to:
- ✓ Receive signals via WebSocket
- ✓ Place bets automatically
- ✓ Monitor multipliers
- ✓ Execute cashouts
- ✓ Track statistics
- ✓ Process every round

Just connect your API!
