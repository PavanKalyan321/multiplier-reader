# Cashout Target Fix - 1.2x Multiplier

## Issue Fixed

The bot was displaying an undefined variable `profit_at_cashout` when placing bets, causing errors in the output logs.

## What Was Changed

### Fixed Line 153 in `start_playwright_bot.py`

**BEFORE:**
```python
print(f"[OK] Bet {round_count} PLACED! Amount: {bet_amount} | Target: {cashout_target_multiplier}x (Profit: {profit_at_cashout})")
```

**AFTER:**
```python
expected_profit = bet_amount * cashout_target_multiplier
print(f"[OK] Bet {round_count} PLACED! Amount: {bet_amount} | Target: {cashout_target_multiplier}x (Profit: {expected_profit:.2f})")
```

## Clarification

### Cashout Target Multiplier = 1.2x

The `cashout_target_multiplier` on line 55 is **1.2**, which means:

- **Game Multiplier:** The value shown in the game (1.05x, 1.1x, 1.2x, 1.5x, etc.)
- **Target:** Cash out when game reaches **1.2x or higher**
- **Profit Calculation:** `profit = bet_amount × multiplier`
  - At 1.2x: profit = 50 × 1.2 = 60
  - At 1.3x: profit = 50 × 1.3 = 65
  - At 1.5x: profit = 50 × 1.5 = 75

## How Cashout Trigger Works

```python
if (bet_placed and
    not cashout_attempted and
    multiplier is not None and
    multiplier >= cashout_target_multiplier):  # >= 1.2

    # Execute cashout
    print(f"[INFO] Cashout triggered! Multiplier: {multiplier}x, Target: {cashout_target_multiplier}x")
```

## Example Output

### Bet Placement
```
[OK] Bet 1 PLACED! Amount: 50 | Target: 1.2x (Profit: 60.00)
```

### Cashout Trigger (when multiplier reaches 1.2x)
```
[INFO] Cashout triggered! Multiplier: 1.2x, Target: 1.2x, Status: RUNNING
[✅ CASHOUT SUCCESS!] Multiplier: 1.20x | Profit: 60.00 | Balance: 1060.00
```

## Changing Cashout Target

To change when the bot cashes out, edit **line 55**:

```python
cashout_target_multiplier = 1.2  # Change this value
```

### Examples

- `1.1` = Low risk, cash out at 1.1x (profit = 50 × 1.1 = 55)
- `1.2` = Balanced, cash out at 1.2x (profit = 50 × 1.2 = 60)  ← **Current**
- `1.5` = Higher risk, cash out at 1.5x (profit = 50 × 1.5 = 75)
- `2.0` = High risk, cash out at 2.0x (profit = 50 × 2.0 = 100)

## Testing the Fix

Run the bot:
```bash
python start_playwright_bot.py
```

Watch for proper output:
```
[OK] Bet 1 PLACED! Amount: 50 | Target: 1.2x (Profit: 60.00)
[INFO] Cashout triggered! Multiplier: 1.20x, Target: 1.2x
[✅ CASHOUT SUCCESS!] Multiplier: 1.20x | Profit: 60.00 | Balance: 1060.00
```

## Summary

✅ Fixed undefined variable error
✅ Cashout target correctly set to 1.2x multiplier
✅ Profit calculation is now accurate
✅ Bot ready to run

No further changes needed - the bot will now properly cash out at 1.2x game multiplier!
