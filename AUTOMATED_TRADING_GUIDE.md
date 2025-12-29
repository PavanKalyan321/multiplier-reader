# Automated Trading System - Complete Guide

## Overview

The automated trading system integrates WebSocket signal reception with automatic trade execution. The system:

1. **Receives signals** from API via WebSocket
2. **Validates signals** according to format and requirements
3. **Places bets** automatically when signal indicates
4. **Monitors multiplier** in real-time
5. **Executes cashout** at target multiplier or on timeout
6. **Tracks statistics** for all executed trades

---

## Architecture

### Components

#### 1. WebSocket Listener (`websocket_listener.py`)
Receives and parses trading signals from API.

**Signal Format:**
```json
{
  "timestamp": "2025-12-29T14:23:45.123456",
  "expectedRange": "1.0-3.0",
  "expectedMultiplier": "1.5",
  "bet": true,
  "roundId": "round_12345"
}
```

**Features:**
- Async WebSocket connection
- Automatic reconnection
- Signal validation
- Queue-based message handling
- Listener callback support

#### 2. Signal Executor (`signal_executor.py`)
Executes trading actions based on signals.

**Features:**
- Automatic bet placement
- Real-time multiplier monitoring
- Conditional cashout (at target or timeout)
- Execution record tracking
- Performance statistics

#### 3. Automated Trading System (`automated_trading.py`)
Orchestrates WebSocket listener and executor.

**Features:**
- Unified system initialization
- Async signal processing loop
- Test mode support
- System status reporting
- Integration with all components

#### 4. WebSocket Test Server (`websocket_test_server.py`)
Simulates API for testing purposes.

**Modes:**
- Interactive mode (manual signal sending)
- Test mode (automatic test signal generation)

---

## Usage

### 1. Interactive Mode (Manual Testing)

**Terminal 1 - Start Test Server:**
```bash
python websocket_test_server.py --mode interactive --host localhost --port 8765
```

**Server Commands:**
- `send 5` - Send 5 test signals
- `clients` - Show connected clients
- `quit` - Exit

**Terminal 2 - Start Automated Trader:**
```python
import asyncio
from config import load_game_config
from automated_trading import run_automated_trading

async def main():
    config = load_game_config()
    await run_automated_trading(
        game_config=config,
        websocket_uri="ws://localhost:8765",
        test_mode=True,  # Don't execute actual trades
        num_test_rounds=5
    )

asyncio.run(main())
```

### 2. Test Mode (Automated)

Run complete test automatically:

```bash
# Terminal 1 - Start test server with automatic signals
python websocket_test_server.py --mode test --signals 5 --interval 10

# Terminal 2 - Start automated trader
python automated_trading.py
```

### 3. Production Mode (Real Trading)

```python
import asyncio
from config import load_game_config
from automated_trading import run_automated_trading

async def main():
    config = load_game_config()
    await run_automated_trading(
        game_config=config,
        websocket_uri="ws://your_api_server:port",
        test_mode=False,  # Actually execute trades
        num_test_rounds=0  # Use indefinite mode
    )

asyncio.run(main())
```

---

## Signal Processing Flow

```
API sends signal via WebSocket
         ↓
WebSocket Listener receives JSON
         ↓
Parse into TradingSignal
         ↓
Validate (round_id, multiplier > 0, etc.)
         ↓
Add to queue
         ↓
Signal Executor receives signal
         ↓
IF bet == true:
  Place bet (click_bet_button)
         ↓
  Monitor multiplier in real-time
         ↓
  IF current >= target:
    Execute cashout at target
  IF timeout reached:
    Force cashout at current
  IF crash detected (< 1):
    Skip cashout
         ↓
Record execution (stats, multiplier, etc.)
```

---

## Signal Format Details

### Required Fields

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| `timestamp` | string | "2025-12-29T14:23:45" | ISO format timestamp |
| `expectedRange` | string | "1.0-3.0" | Visual information |
| `expectedMultiplier` | float/string | "1.5" | Target for cashout |
| `bet` | boolean | true | Whether to place bet |
| `roundId` | string | "round_12345" | Unique identifier |

### Optional Fields

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| `confidence` | float | 0.85 | Prediction confidence |
| `action` | string | "place_bet" | Explicit action (inferred from `bet` if not present) |

---

## Execution Record Structure

```python
ExecutionRecord:
  signal: TradingSignal                    # Original signal
  status: ExecutionStatus                  # Current execution status
  bet_placed_at: "HH:MM:SS"               # When bet was placed
  bet_result: bool                         # True if bet click succeeded
  cashout_executed_at: "HH:MM:SS"         # When cashout was executed
  cashout_result: bool                     # True if cashout click succeeded
  max_multiplier_reached: float            # Highest multiplier during round
  actual_multiplier_at_cashout: float     # Multiplier when cashout executed
  error_message: str                       # Error description if failed
```

### Execution Status

- `PENDING` - Awaiting processing
- `WAITING_FOR_ROUND` - Signal received, waiting for round start
- `PLACED_BET` - Bet placed successfully
- `MONITORING` - Monitoring multiplier for target
- `CASHOUT_EXECUTED` - Cashout successfully executed
- `FAILED` - Execution failed
- `CANCELLED` - Signal indicated cancel

---

## Statistics & Reporting

### Execution Summary

```python
{
    'total_executions': int,           # Total signals processed
    'successful': int,                 # Successfully cashed out
    'failed': int,                     # Failed executions
    'pending': int,                    # Awaiting completion
    'success_rate': float,             # Percentage successful
    'total_pnl': float,                # Estimated profit/loss
    'records': [ExecutionRecord]       # All execution records
}
```

### System Status

```python
{
    'running': bool,
    'enable_trading': bool,
    'websocket': {...},                # WebSocket stats
    'executor': {...},                 # Execution stats
    'game_actions': {...}              # Click stats
}
```

---

## Testing Workflow

### Step 1: Verify Configuration
```bash
python main.py
# Choose "Test Configuration" to verify regions and button
```

### Step 2: Run Interactive Test
```bash
# Terminal 1
python websocket_test_server.py --mode interactive

# Terminal 2
import asyncio
from config import load_game_config
from automated_trading import run_automated_trading

config = load_game_config()
asyncio.run(run_automated_trading(config, test_mode=True, num_test_rounds=3))

# In Terminal 1, type: send 3
```

### Step 3: Monitor Execution
- Watch Terminal 2 for:
  - Bet placement
  - Multiplier monitoring
  - Cashout execution
  - Statistics

### Step 4: Review Results
```python
system = AutomatedTradingSystem(config)
await system.start()
# ... after trading ...
system.print_system_status()
```

---

## Error Handling

### Invalid Signal
```
[timestamp] WARNING: Invalid signal data
→ Status: FAILED
→ Records execution with error message
→ Continues listening for next signal
```

### Bet Placement Failed
```
[timestamp] ERROR: Failed to place bet
→ Status: FAILED
→ Does not attempt to monitor/cashout
→ Returns execution record with error
```

### Multiplier Read Failed
```
[timestamp] WARNING: Error reading multiplier
→ Retries with small delay
→ Continues monitoring
→ If timeout reached, forces cashout
```

### Crash Detected
```
[timestamp] WARNING: Game crashed before target
→ Status: FAILED
→ Does not execute cashout
→ Records crash multiplier
```

---

## Performance Considerations

### Timing
- **Bet Placement**: 0.8s (0.5s pre-delay + click + 0.3s post-delay)
- **Multiplier Read**: ~100-200ms (OCR dependent)
- **Monitoring Loop**: 0.1s per iteration
- **Total Signal Processing**: 1-60s depending on target multiplier

### Resource Usage
- Memory: ~10-20MB base + execution records
- CPU: Low (mostly I/O waiting)
- Network: Minimal (JSON messages)

### Limitations
- Single round execution only
- Sequential signal processing
- No parallel trading

---

## Configuration Example

### game_config.json
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

---

## Troubleshooting

### WebSocket Connection Failed
```
Check:
- Server is running
- URI is correct (host:port)
- Firewall allows connection
```

### Signals Not Received
```
Check:
- Server is sending signals
- Client is connected (check "Connected: True")
- Signal format is valid JSON
```

### Clicks Not Working
```
Check:
- Button coordinates are correct
- Window is in focus
- PyAutoGUI failsafe not triggered (move mouse from corner)
```

### Wrong Multiplier Read
```
Check:
- Multiplier region is properly configured
- Region is visible and clear
- Tesseract is installed and working
```

### Cashout Not Executing
```
Check:
- Target multiplier is realistic
- Timeout (60s) isn't being exceeded
- Game hasn't crashed
- Click coordinates are correct
```

---

## API Integration Guide

### Connecting Real API

Replace WebSocket URI:
```python
await run_automated_trading(
    game_config=config,
    websocket_uri="ws://your_api_server:8765",  # Your API server
    test_mode=False  # Enable real trading
)
```

### Signal Format Compatibility

If your API uses different field names:
1. Modify `_parse_signal()` in `WebSocketListener`
2. Map your fields to expected format
3. Test with mock signals first

Example mapping:
```python
def _parse_signal(self, data):
    # Your API uses different names
    return TradingSignal(
        timestamp=data.get('time', ''),  # Your field name
        expected_range=data.get('range', ''),
        expected_multiplier=float(data.get('target_mult', 0)),
        bet=data.get('should_bet', False),
        round_id=data.get('gameId', '')
    )
```

---

## Monitoring & Logging

### Enable Debug Logging
Modify log level in components:
```python
# In websocket_listener.py
self._log(message, "DEBUG")  # More verbose output
```

### Save Execution Records
```python
import json

summary = system.signal_executor.get_execution_summary()
with open('execution_log.json', 'w') as f:
    json.dump({
        'records': [
            {
                'round_id': r.signal.round_id,
                'status': r.status.value,
                'bet_result': r.bet_result,
                'cashout_result': r.cashout_result,
                'multiplier': r.actual_multiplier_at_cashout
            }
            for r in summary['records']
        ]
    }, f, indent=2)
```

---

## Safety Precautions

1. **Test First**: Always test with `test_mode=True`
2. **Monitor Closely**: Watch first few real trades
3. **Start Small**: Test with realistic but conservative multipliers
4. **Failsafe Ready**: Have mouse ready at screen corner
5. **Logging**: Keep logs of all executions for analysis
6. **Gradual Rollout**: Increase number of signals slowly

---

## Summary

The automated trading system provides a complete framework for:
- ✓ Receiving trading signals via WebSocket
- ✓ Validating signal integrity
- ✓ Automatically placing bets
- ✓ Real-time multiplier monitoring
- ✓ Conditional cashout execution
- ✓ Comprehensive statistics and tracking
- ✓ Test mode for safe development
- ✓ Production-ready automation

Ready for integration with your API server!
