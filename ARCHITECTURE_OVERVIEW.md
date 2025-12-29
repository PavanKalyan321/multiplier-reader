# Automated Trading System - Architecture Overview

## System Components

```
┌────────────────────────────────────────────────────────────────┐
│                    YOUR API SERVER                              │
│  (Sends trading signals via WebSocket)                         │
└────────────────┬─────────────────────────────────────────────┘
                 │ WebSocket JSON Signal
                 │ {timestamp, expectedRange, expectedMultiplier, bet, roundId}
                 ↓
┌────────────────────────────────────────────────────────────────┐
│              WEBSOCKET LISTENER                                 │
│  websocket_listener.py                                         │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  TradingSignal (dataclass)                                     │
│  └─ timestamp, expected_range, expected_multiplier, bet, etc   │
│                                                                 │
│  WebSocketListener (class)                                     │
│  ├─ connect() - Connect to API server                         │
│  ├─ listen() - Wait for signals                               │
│  ├─ _parse_signal() - Convert JSON to TradingSignal           │
│  └─ get_signal() - Retrieve from queue                        │
│                                                                 │
└────────────────┬─────────────────────────────────────────────┘
                 │ TradingSignal
                 ↓
┌────────────────────────────────────────────────────────────────┐
│              SIGNAL EXECUTOR                                    │
│  signal_executor.py                                            │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ExecutionRecord (dataclass)                                   │
│  └─ status, bet_result, cashout_result, multiplier, etc        │
│                                                                 │
│  SignalExecutor (class)                                        │
│  ├─ execute_signal(signal) - Main execution                    │
│  ├─ _monitor_and_cashout() - Monitor multiplier               │
│  └─ get_execution_summary() - Statistics                       │
│                                                                 │
│  Execution Flow:                                               │
│  Signal → Place Bet → Monitor Multiplier → Cashout → Record   │
│                                                                 │
└────────────────┬─────────────────────────────────────────────┘
                 │ Execution Record + Stats
                 ↓
┌────────────────────────────────────────────────────────────────┐
│              AUTOMATED TRADING SYSTEM                           │
│  automated_trading.py                                          │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  AutomatedTradingSystem (class)                               │
│  ├─ start() - Initialize WebSocket + Executor                │
│  ├─ _execution_loop() - Main processing loop                  │
│  ├─ process_test_signals() - Generate test signals            │
│  └─ get_system_status() - Report status                       │
│                                                                 │
│  Integration:                                                  │
│  ├─ WebSocketListener - Receives signals                      │
│  ├─ SignalExecutor - Executes trades                          │
│  ├─ GameActions - Clicks (bet/cashout)                        │
│  └─ MultiplierReader - Reads multiplier                       │
│                                                                 │
└────────────────┬─────────────────────────────────────────────┘
                 │ System Status + Statistics
                 ↓
        ┌────────────────────┐
        │  USER / MONITORING │
        │  System Status,    │
        │  Execution Logs,   │
        │  Statistics        │
        └────────────────────┘


┌────────────────────────────────────────────────────────────────┐
│              SUPPORTING COMPONENTS                              │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  GameActions (game_actions.py)                                │
│  ├─ click_bet_button() - Place bet                            │
│  └─ click_cashout_button() - Execute cashout                  │
│                                                                 │
│  MultiplierReader (multiplier_reader.py)                      │
│  └─ read_multiplier() - Get current multiplier via OCR        │
│                                                                 │
│  ScreenCapture (screen_capture.py)                            │
│  └─ capture_region() - Screenshot for OCR                     │
│                                                                 │
│  Configuration (config.py)                                    │
│  ├─ load_game_config() - Load settings                        │
│  └─ save_game_config() - Save settings                        │
│                                                                 │
│  WebSocket Test Server (websocket_test_server.py)             │
│  ├─ Interactive Mode - Manual signal sending                  │
│  └─ Test Mode - Automatic test signal generation              │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Signal Arrival to Execution

```
1. API sends JSON signal
   └─→ {"timestamp": "...", "expectedMultiplier": "1.5", "bet": true, ...}

2. WebSocket Listener receives
   └─→ Parses JSON → Creates TradingSignal → Validates → Queues

3. Automated Trading System retrieves
   └─→ Gets signal from queue

4. Signal Executor processes
   ├─→ Check if bet=true
   ├─→ Place bet (GameActions.click_bet_button)
   ├─→ Monitor multiplier (MultiplierReader.read_multiplier)
   │   ├─→ Read every 0.1s
   │   ├─→ Compare with target
   │   └─→ Check for crash (< 1.0)
   └─→ Cashout (GameActions.click_cashout_button)
       └─→ When target reached OR 60s timeout

5. Execution Record created
   ├─→ Status: CASHOUT_EXECUTED
   ├─→ Bet result: success/failure
   ├─→ Actual multiplier: 1.50x
   └─→ Statistics: success_rate, PnL, etc

6. System reports
   └─→ Logs, statistics, status available
```

---

## Component Responsibilities

### WebSocket Listener
**Responsibility:** Signal Reception
- Connects to WebSocket server
- Receives JSON messages
- Validates signal format
- Converts to TradingSignal objects
- Queues for processing
- Error handling & retry

### Signal Executor
**Responsibility:** Trade Execution
- Places bets via GameActions
- Monitors multiplier via MultiplierReader
- Executes cashout at target
- Handles timeouts
- Records execution details
- Calculates statistics

### Automated Trading System
**Responsibility:** Orchestration
- Initializes all components
- Manages async event loop
- Coordinates listener + executor
- Processes signals sequentially
- Provides system interface
- Reports status/statistics

### Supporting Components
- **GameActions** - Automates clicks
- **MultiplierReader** - OCR multiplier reading
- **ScreenCapture** - Screen region capture
- **Config** - Manages configuration

---

## Execution States

```
Signal Execution States:

PENDING (Start)
    ↓
    ├─→ Invalid Signal? → FAILED (end)
    │
WAITING_FOR_ROUND
    ↓
    ├─→ Bet Click Failed? → FAILED (end)
    │
PLACED_BET
    ↓
    ├─→ Game Crashed (< 1.0)? → FAILED (end)
    │
MONITORING
    ├─→ Target reached? → Continue
    │
    ├─→ 60s timeout? → Force cashout
    │
    └─→ Cashout succeeded? → CASHOUT_EXECUTED (end, SUCCESS)
        └─→ Cashout failed? → FAILED (end)
```

---

## Async Architecture

```
Main Event Loop (asyncio)
│
├─── Task: WebSocket Listen
│    ├─ connect()
│    └─ listen() [Blocking]
│        └─ Receives messages continuously
│        └─ Queues TradingSignal objects
│
├─── Task: Signal Execution
│    ├─ get_signal() [Waits for signal]
│    ├─ execute_signal() [Async]
│    │   ├─ Place bet
│    │   ├─ Monitor multiplier
│    │   └─ Execute cashout
│    └─ Record execution
│
└─── Main Loop
     └─ Keeps tasks running indefinitely
```

---

## Signal Processing Pipeline

```
Queue of Signals
    │
    ↓ (Get next signal with timeout)

Validate Signal
    │
    ├─ Has required fields?
    ├─ bet_button_point valid?
    └─ multiplier > 0?

    ↓ (Yes)

Execute Signal
    │
    ├─ bet=true?
    │   │
    │   ├─ Yes → Place Bet
    │   │       ├─ Click bet button
    │   │       ├─ Wait 0.8s total
    │   │       └─ Continue to Monitor
    │   │
    │   └─ No → Skip (status: PENDING)
    │
    └─ Monitor Multiplier
        │
        ├─ Read multiplier every 0.1s
        ├─ Track max value
        ├─ Check crash (< 1.0)
        │
        └─ Exit condition?
            │
            ├─ Target reached? → Cashout at target
            ├─ 60s timeout? → Cashout at current
            ├─ Crash detected? → Skip cashout
            │
            └─ Execute Cashout
                ├─ Click cashout button
                └─ Record results

Record Execution
    │
    └─ Save status, multipliers, times, etc
```

---

## Configuration Flow

```
User runs application
    ↓
Load game_config.json
    ├─ Balance region
    ├─ Multiplier region
    └─ Bet button point

Create Components
    ├─ ScreenCapture (multiplier region)
    ├─ MultiplierReader
    ├─ GameActions (button point)
    └─ WebSocketListener

Create System
    └─ AutomatedTradingSystem

Start System
    ├─ Connect WebSocket
    ├─ Start listening task
    ├─ Start execution task
    └─ Ready for signals
```

---

## Error Handling

```
Invalid Signal Format
    └─ Log error
    └─ Skip signal
    └─ Continue listening

WebSocket Connection Failed
    ├─ Retry connection
    ├─ Exponential backoff
    └─ Log errors

Bet Click Failed
    └─ Record as failed
    └─ Skip monitoring
    └─ Continue to next signal

Multiplier Read Failed
    ├─ Retry read
    ├─ Continue monitoring
    └─ If timeout, force cashout

Cashout Click Failed
    └─ Record as failed
    └─ Log error
    └─ Continue to next signal
```

---

## Performance Characteristics

```
Component          | Operation      | Time
─────────────────────────────────────────
WebSocket          | Connect        | 100-500ms
                   | Receive        | <1ms
                   | Parse JSON     | <1ms

Signal Executor    | Place bet      | 0.8s (0.5+click+0.3)
                   | Read mult      | 100-200ms
                   | Cashout        | 0.8s (0.5+click+0.3)

MultiplierReader   | OCR read       | 100-200ms
                   | Preprocess     | 50-100ms

Total per round    | Fast path      | 2-3s (bet+cashout+reads)
                   | Slow path      | 60s (timeout)
                   | Average        | 5-20s
```

---

## Scalability

### Current Capabilities
- Single sequential signal processing
- One trade per round
- Per-signal tracking

### Limitations
- Can't process multiple signals in parallel
- No multi-account support
- Single game instance

### Future Extensions
- Process multiple signals simultaneously
- Multiple game accounts
- Signal prioritization
- Advanced filtering/conditions

---

## Integration Points

```
Your API Server
    ↓ (WebSocket JSON)

WebSocketListener
    ├─ Can handle custom JSON formats (modify _parse_signal)
    └─ Supports custom signal fields

SignalExecutor
    ├─ Can add custom conditions
    ├─ Can add new action types
    └─ Can integrate with other systems

GameActions
    ├─ Already uses PyAutoGUI
    ├─ Can add new click types
    └─ Can support different button placements

System
    ├─ Async-compatible with other systems
    ├─ Signal hooks/callbacks available
    └─ Extensible statistics
```

---

## Testing Architecture

```
Test Server (websocket_test_server.py)
    │
    ├─ Interactive Mode
    │   └─ Manual signal control
    │   └─ Send custom signals
    │   └─ Monitor client connections
    │
    └─ Test Mode
        └─ Auto-generate signals
        └─ Incrementing multipliers
        └─ Simulated rounds
        └─ Continuous streaming

Automated Trading System
    │
    └─ Test Mode (test_mode=True)
        ├─ Connect to test server
        ├─ Receive test signals
        ├─ Process without executing trades
        ├─ Track execution records
        └─ Report statistics
```

---

## Summary

The automated trading system provides:

1. **Signal Reception** via WebSocket
2. **Async Processing** with event loop
3. **Automatic Execution** (bet + cashout)
4. **Real-time Monitoring** of multipliers
5. **Comprehensive Tracking** of executions
6. **Error Handling** at all levels
7. **Test Mode** for safe development
8. **Extensible Architecture** for integration

All components work together to create a complete automated trading pipeline that responds to API signals and executes trades automatically, for every round!
