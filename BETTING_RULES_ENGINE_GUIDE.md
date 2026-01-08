# Betting Rules Engine - Quick Start Guide

## What's New

Your betting system now has a **comprehensive rule-based engine** that works alongside Azure AI Foundry predictions. Instead of simple +30% win/reset loss stakes, you now have:

### ✅ What You Get

1. **Regime Detection** - Automatically detects TIGHT/NORMAL/LOOSE/VOLATILE game states
2. **Smart Stake Management** - Win ×1.4, Loss ÷1.4 (max 3 compound steps)
3. **Adaptive Cashout** - 1.85x default, 1.5x defensive (when losing), 2.5x aggressive (in favorable conditions)
4. **Entry Filters** - Skip bets when previous round ≥10x, any of last 3 ≥20x, etc.
5. **Cooldown System** - Skip rounds after high multipliers, consecutive losses, max compounding
6. **Session Management** - Auto-stop at 200 profit, 200 loss, or 30-minute time limit
7. **Hot-Reload Config** - Edit JSON rules mid-session without restarting

## Configuration File

**Location**: `betting_rules_config.json`

### How to Customize

Edit these sections based on your 4000+ rounds of analysis:

#### 1. Session Goals
```json
"session": {
  "duration_minutes": 30,      // Stop after 30 min
  "profit_target": 200,        // Stop after +200 profit
  "max_loss": 200              // Stop after -200 loss
}
```

#### 2. Capital Management
```json
"capital": {
  "start_bet": 15,             // Base stake
  "max_bet": 40                // Never exceed this
}
```

#### 3. Stake Compounding
```json
"stake_compounding": {
  "win_multiplier": 1.4,       // On win: stake × 1.4
  "loss_divisor": 1.4,         // On loss: stake ÷ 1.4
  "max_steps": 3,              // Max 3 compound steps
  "reset_on_high_mult": 10     // Reset if round ≥10x
}
```

#### 4. Cashout Modes
```json
"cashout": {
  "default": 1.85,             // Normal cashout
  "defensive": 1.5,            // When session_loss ≥80
  "aggressive": 2.5            // When profit ≥100 AND regime=LOOSE
}
```

#### 5. Entry Filters
```json
"entry_filters": {
  "do_not_bet_if": {
    "previous_round_gte": 10,  // Skip if last round ≥10x
    "last_3_any_gte": 20       // Skip if any of last 3 ≥20x
  }
}
```

#### 6. Regime Thresholds
```json
"regime_thresholds": {
  "TIGHT": {
    "median_max": 2.0,         // Median multiplier < 2.0x
    "pct_below_1_5x_min": 40   // >40% of rounds < 1.5x
  },
  "LOOSE": {
    "median_min": 2.5          // Median multiplier > 2.5x
  },
  "VOLATILE": {
    "median_min": 3.0,         // Median > 3.0x
    "high_tail_freq_min": 15   // >15% rounds ≥10x
  }
}
```

## How It Works

### Betting Flow (with rules engine)

```
Signal Received
  ↓
Regime Detected: [TIGHT/NORMAL/LOOSE/VOLATILE]
  ↓
Entry Filters: [Check previous round, last 3 rounds, cooldown]
  ↓
Calculate Stake: [win ×1.4, loss ÷1.4, max 3 steps]
  ↓
Select Cashout: [1.5x/1.85x/2.5x based on conditions]
  ↓
Place Bet
  ↓
Monitor & Cashout
  ↓
Process Result: [Update session stats, check stop conditions]
  ↓
Session Stop? [Profit ≥200, Loss ≥200, Time ≥30min]
```

### Rule Engine Modules

1. **config_loader.py** - Loads and hot-reloads JSON
2. **regime_detector.py** - Detects TIGHT/NORMAL/LOOSE/VOLATILE
3. **entry_filter.py** - Evaluates do_not_bet_if / bet_only_if
4. **stake_manager.py** - Manages ×1.4/÷1.4 compounding
5. **cashout_selector.py** - Selects 1.5x/1.85x/2.5x
6. **cooldown_manager.py** - Enforces skip conditions
7. **session_tracker.py** - Tracks profit/loss/time limits
8. **historical_data.py** - In-memory cache of recent rounds

## Testing with Demo Account

### Step 1: Start the Bot
```bash
python main.py
```

### Step 2: Select Option 7 (Model Signal Listener)
```
Select an option: 7
Which model would you like to use? 1 (PyCaret)
```

### Step 3: Watch the Rules Engine in Action
```
[14:23:45] RULES-ENGINE INFO: Current regime: NORMAL (median=2.2x, conf=85%)
[14:23:45] RULES-ENGINE INFO: Entry evaluation: APPROVED
[14:23:45] RULES-ENGINE INFO: Stake decision: 21.00 (compound_level=1)
[14:23:45] RULES-ENGINE INFO: Cashout: default mode → 1.85x
[14:23:47] RULES-ENGINE INFO: Round 4398: WIN | Mult: 2.10x | P&L: +31.5 | Profit: 65 | Loss: 0
```

### Step 4: Check Session Summary
When session stops:
```
[14:53:45] RULES-ENGINE WARNING: SESSION STOP: Profit target reached: 201 >= 200
[14:53:45] RULES-ENGINE INFO: Session summary: {
  'duration_min': '30.0',
  'total_profit': '201',
  'total_loss': '0',
  'net_pnl': '+201',
  'rounds_played': 15,
  'wins': 12,
  'losses': 3,
  'win_rate': '80.0%'
}
```

## What the Rules Engine Logs

Every decision is logged with timestamp:

```
[HH:MM:SS] RULES-ENGINE INFO: Current regime: NORMAL (median=2.3x, conf=85%)
[HH:MM:SS] RULES-ENGINE INFO: Entry evaluation: APPROVED
[HH:MM:SS] RULES-ENGINE INFO: Entry filters: All filters passed
[HH:MM:SS] RULES-ENGINE INFO: Stake decision: 21.00 (compound_level=1, reason=win → level=1)
[HH:MM:SS] RULES-ENGINE INFO: Cashout: default mode → 1.85x (standard_conditions)
[HH:MM:SS] RULES-ENGINE INFO: Round 4398: WIN | Mult: 2.10x | P&L: +31.5 | Profit: 65 | Loss: 0
```

## Making Changes Mid-Session

You can edit `betting_rules_config.json` while the bot is running:

```json
// Example: Change default cashout from 1.85x to 1.75x
"default": {
  "multiplier": 1.75    // Changed from 1.85
}
```

The system will detect the file change and reload within 10 seconds without restarting.

## Troubleshooting

### "Rules engine disabled"
- Check that `betting_rules_config.json` exists in the bot directory
- Ensure the JSON is valid (no syntax errors)

### "Cooldown active"
- Expected after high multipliers (≥10x) or consecutive losses
- The system will resume betting after the cooldown period

### "Entry filters failed"
- Last round multiplier out of range (check do_not_bet_if conditions)
- Compound level too high (max 3 steps)
- Check the detailed reason in the logs

### Regime shows "VOLATILE"
- Indicates highly unpredictable game state
- Betting may be skipped (set "allow_volatile": true to override)

## Key Settings for Your Demo

Based on your configuration:

| Setting | Value | Meaning |
|---------|-------|---------|
| Session Duration | 30 min | Stop after 30 minutes |
| Profit Target | 200 | Stop after winning 200 |
| Max Loss | 200 | Stop after losing 200 |
| Start Bet | 15 | Initial stake |
| Max Bet | 40 | Never bet more than 40 |
| Win Multiplier | 1.4 | Increase stake by 40% on win |
| Loss Divisor | 1.4 | Decrease stake by 40% on loss |
| Default Cashout | 1.85x | Standard cashout target |
| Defensive Cashout | 1.5x | When session loss ≥80 |
| Aggressive Cashout | 2.5x | When regime=LOOSE AND profit≥100 |

## Next Steps

1. **Test**: Run the demo with your account and observe the rules engine decisions
2. **Tune**: Edit regime thresholds based on actual game patterns
3. **Optimize**: Adjust cashout multipliers based on win rates
4. **Monitor**: Watch the logs to understand decision-making

Enjoy your new intelligent betting system! 🚀
