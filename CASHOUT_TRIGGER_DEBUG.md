# Cashout Trigger - Debug Guide

## What Was Fixed

Fixed the cashout trigger logic with proper state management:

### Changes Made

1. **Simplified Cashout Condition**
```python
# OLD: (Too strict)
if (bet_placed and not cashout_attempted and
    multiplier_visible and multiplier >= cashout_target_multiplier):

# NEW: (Simpler, more reliable)
if (bet_placed and
    not cashout_attempted and
    multiplier is not None and
    multiplier >= cashout_target_multiplier):
```

2. **Reset `cashout_attempted` on Success**
```python
if cashout_result.get('success'):
    bet_placed = False
    cashout_attempted = False  # ← IMPORTANT: Reset for next round
    # ... record profit
```

3. **Reset State on Crash**
```python
if round_crashed:
    bet_placed = False
    cashout_attempted = False  # Reset
    round_started = False      # Reset
    # ... record loss
```

4. **Added Debug Indicator**
```python
# In the status line, shows "READY" when cashout can be triggered
cashout_ready = "READY" if (bet_placed and multiplier is not None
                             and multiplier >= cashout_target_multiplier) else ""
log(f"...Status... | {cashout_ready}")
```

## How Cashout Trigger Works

### Conditions Required

```python
if (bet_placed and                          # 1. Bet must be placed
    not cashout_attempted and               # 2. Haven't tried to cashout yet
    multiplier is not None and              # 3. Multiplier must be visible
    multiplier >= cashout_target_multiplier):  # 4. Must reach target (1.2x)

    # CASHOUT TRIGGERED
    [Execute cashout]
```

### Example Flow

```
TIME    | Multiplier | bet_placed | cashout_attempted | Action
--------|-----------|-----------|-------------------|--------
1       | INVISIBLE | False     | False             | -
2       | INVISIBLE | False     | False             | Place bet
3       | INVISIBLE | True      | False             | -
4       | INVISIBLE | True      | False             | -
5       | 1.01x     | True      | False             | Round started
6       | 1.05x     | True      | False             | -
7       | 1.10x     | True      | False             | -
8       | 1.15x     | True      | False             | -
9       | 1.21x ✓   | True      | False             | ← TRIGGER!
10      | 1.21x     | True      | True              | Execute cashout
11      | 1.21x     | True      | True              | Success
12      | 1.21x     | False     | False             | Reset for next
```

## What to Look For in Output

### Cashout About to Trigger
```
[19:30:46.723] Mult:      1.21x | Bal:  1000.00 | Status: RUNNING  | Bet: YES  | READY
```

When you see `| READY` it means the cashout condition is met and should trigger next cycle.

### Cashout Triggered
```
[INFO] Cashout triggered! Multiplier: 1.21x, Target: 1.2x, Status: RUNNING
```

### Successful Cashout
```
[✅ CASHOUT SUCCESS!] Multiplier: 1.21x | Profit: 60.50 | Balance: 1060.50
```

### Fallback Cashout
```
[⚠️  WARN] Validation failed, trying fallback click...
[✅ CASHOUT SUCCESS (fallback)!] Multiplier: 1.21x | Profit: 60.50
```

### Failed Cashout
```
[❌ CASHOUT FAILED!] Could not click cashout button!
[ERROR] Cashout click failed at 1.21x
```

## Troubleshooting

### Problem: Cashout Not Triggering

**Check 1: Is `READY` showing in output?**
```
Mult:      1.21x | Bet: YES  | READY  ← Should see READY
```

If NO `READY`:
- Multiplier might not be reaching 1.2x
- Bet might not be placed
- Multiplier reading might be wrong

**Check 2: Is bet actually placed?**
```
[OK] Bet 1 PLACED! Amount: 50
```

If not seeing this:
- Wait for WAITING status
- Check if bet button selector is correct
- Look for bet placement error messages

**Check 3: Is multiplier readable?**
```
Mult:      1.21x  ← Should show number, not INVISIBLE
```

If showing INVISIBLE when multiplier should be visible:
- Multiplier selector might be wrong
- Game might be having issues
- Check browser console for errors

### Problem: Cashout Triggers but Doesn't Execute

**Check for validation errors:**
```
[INFO] Cashout triggered!
[⚠️  WARN] Validation failed, trying fallback click...
[CASHOUT] SUCCESS! Button clicked
```

If validation fails but fallback works - that's fine, it still cashes out.

**If both fail:**
```
[❌ CASHOUT FAILED!] Could not click cashout button!
```

This means:
- Cashout button not found
- Button not clickable
- Wrong selector

Check selector in `playwright_config.py`:
```python
"cashout_button_1": "[data-testid='button-cashout-1']"
```

### Problem: Cashout Triggers but Immediately Shows as Lost

**Check if crash detection is false-triggering:**
```
[💥 ROUND CRASHED] Multiplier: 1.21x → INVISIBLE
```

If multiplier disappears right after cashout:
- Game rounds normally after cashout
- This is expected behavior
- Check statistics - if "Successful Cashouts" increases, cashout worked

## Debug Output Guide

### Line Breakdown
```
[19:30:46.723] Mult: 1.21x | Bal: 1060.50 | Status: RUNNING | Bet: YES | READY
│              │    │       │ │            │ │               │ │       │ │
│              │    │       │ │            │ │               │ │       │ └─ CASHOUT CONDITION MET
│              │    │       │ │            │ │               │ │       └─ Bet placed
│              │    │       │ │            │ │               │ └─ Game status
│              │    │       │ │            │ └─ Current balance
│              │    │       │ └─ Multiplier value
│              │    └─ Multiplier display
│              └─ Timestamp
└─ Log line
```

## Quick Test

To verify cashout triggering works:

1. **Run bot:** `python start_playwright_bot.py`
2. **Watch status line:** Look for `READY` indicator
3. **When multiplier hits 1.2x+:** Should see `READY`
4. **Next 100ms cycle:** Should see `[INFO] Cashout triggered!`
5. **Then:** Should see either success or fallback message
6. **Result:** Profit recorded, stats updated, ready for next bet

## State Reset Checklist

✅ After successful cashout:
- `bet_placed = False` (ready to place new bet)
- `cashout_attempted = False` (ready to cashout next time)

✅ After crash:
- `bet_placed = False` (reset)
- `cashout_attempted = False` (reset)
- `round_started = False` (reset)

✅ After failed cashout:
- `bet_placed = False` (reset)
- `cashout_attempted = False` (ready for next round)

## Example: Working Session

```
[19:30:45.123] Mult:    INVISIBLE | Bal:  1000.00 | Status:  WAITING  | Bet: NO  |

[INFO] Placing bet with validation...
[OK] Bet 1 PLACED! Amount: 50

[19:30:46.223] Mult:    INVISIBLE | Bal:  1000.00 | Status: RUNNING  | Bet: YES |

[🎮 ROUND STARTED] Multiplier visible: 1.02x

[19:30:46.323] Mult:      1.02x | Bal:  1000.00 | Status: RUNNING  | Bet: YES |
[19:30:46.423] Mult:      1.08x | Bal:  1000.00 | Status: RUNNING  | Bet: YES |
[19:30:46.523] Mult:      1.15x | Bal:  1000.00 | Status: RUNNING  | Bet: YES |
[19:30:46.623] Mult:      1.21x | Bal:  1000.00 | Status: RUNNING  | Bet: YES | READY ✓

[INFO] Cashout triggered! Multiplier: 1.21x, Target: 1.2x
[INFO] STEP 1: Reading initial balance...
[INFO] STEP 2: Clicking cashout button...
[CASHOUT] SUCCESS! Button clicked
[INFO] STEP 3: Verifying cashout completed...
[INFO] STEP 4: Verifying balance change...
✅ Cashout validation successful
[✅ CASHOUT SUCCESS!] Multiplier: 1.21x | Profit: 60.50 | Balance: 1060.50

[INFO] Placing bet with validation...
[OK] Bet 2 PLACED! Amount: 50

[🎮 ROUND STARTED] Multiplier visible: 1.03x

...continues...
```

## Summary

The cashout trigger now:

✅ **Checks all conditions** - bet placed, not attempted, multiplier visible, reaches target
✅ **Resets state properly** - After success/fail/crash
✅ **Shows debug info** - `READY` indicator in status line
✅ **Has fallback** - Tries validation, then direct click
✅ **Logs everything** - See exactly what's happening

**Run the bot and look for `READY` indicator!**
