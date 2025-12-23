# Enhanced Visual Display - Terminal Output

## Overview

The multiplier reader now displays rich, color-coded terminal output with ASCII sparkline trends. All information fits on a single line per status update, with no emoji or special character dependencies.

## Visual Output Format

```
[14:15:03] R:1 | CURR:  1.50x | MAX: 35.96x | DUR:   0.0s | TREND: _
[14:15:04] R:1 | CURR:  5.50x | MAX: 35.96x | DUR:   0.7s | TREND: _-
[14:15:05] R:1 | CURR: 11.22x | MAX: 35.96x | DUR:   1.5s | TREND: _-^
[14:15:06] R:1 | CURR: 20.79x | MAX: 35.96x | DUR:   2.2s | TREND: _-=^*
[14:15:19] R:1 | CURR: 35.96x | MAX: 35.96x | DUR:  15.5s | TREND: __.-=^^*#@

[14:15:19] [CRASH] Reached 35.96x in 15.46s

[14:15:25] [START] ROUND 2 STARTED
[14:15:25] R:2 | CURR:  1.03x | MAX:  3.23x | DUR:   0.0s | TREND: _
```

## Output Components

### Timestamp
- **Format**: `[HH:MM:SS]`
- **Color**: Gray
- **Purpose**: Shows when the status was recorded

### Round Number
- **Format**: `R:1`, `R:2`, etc.
- **Color**: Cyan
- **Purpose**: Identifies which round is currently running

### Current Multiplier
- **Format**: `CURR:  X.XXx`
- **Color**: Dynamic (based on value)
- **Purpose**: Shows current game multiplier
- **Alignment**: Padded to 5 characters for consistent columns

### Max Multiplier
- **Format**: `MAX: XX.XXx`
- **Color**: Magenta (always)
- **Purpose**: Shows highest multiplier reached in current round

### Duration
- **Format**: `DUR:   X.Xs`
- **Color**: White
- **Purpose**: Shows how long the current round has been running

### Trend Sparkline
- **Format**: `TREND: _-=^*#@`
- **Color**: Matches current multiplier color
- **Purpose**: Visual trend showing multiplier progression
- **Max Points**: Last 10 values

## Color Scheme

The multiplier value determines its display color:

| Multiplier Range | Color | Meaning |
|---|---|---|
| 1.00x - 2.99x | Green | Low (safe range) |
| 3.00x - 6.99x | Yellow | Medium (accumulating) |
| 7.00x - 9.99x | Red | High (risky) |
| 10.00x+ | Magenta | Very High (maximum risk) |

## Sparkline Explanation

The sparkline shows multiplier progression using ASCII characters that represent different heights:

```
_ = Lowest values in the range
. = Slightly higher
- = Medium
= = Higher
^ = Even higher
* = High
# = Very high
@ = Highest values
```

**Example**: `_-=^*#@` shows the multiplier steadily increasing from low to high.

## Event Colors

### Game Start Event
```
[14:15:03] [START] ROUND 1 STARTED
```
- **Color**: Green
- **Indicator**: `[START]`

### Crash Event
```
[14:15:19] [CRASH] Reached 35.96x in 15.46s
```
- **Color**: Red
- **Indicator**: `[CRASH]`
- **Max Multiplier**: Shown in magenta
- **Duration**: Time the round lasted

### High Multiplier Event
```
[14:15:03] [HIGH] MULTIPLIER: 10.50x
```
- **Color**: Magenta
- **Indicator**: `[HIGH]`
- **Triggered**: When multiplier >= 10.0x

## Terminal Compatibility

The enhanced display uses **ANSI color codes** which are supported by:

### Windows
- ✅ Windows Terminal (recommended)
- ✅ Windows PowerShell (with ANSI enabled)
- ✅ Windows 10+ Command Prompt (limited)
- ✅ ConEmu
- ✅ Git Bash

### macOS & Linux
- ✅ All standard terminals
- ✅ iTerm2
- ✅ GNOME Terminal
- ✅ xterm

### Troubleshooting Colors

**If colors don't appear:**

1. **Windows Command Prompt**: Switch to Windows Terminal or PowerShell
2. **PowerShell**: Colors should work by default in PowerShell 7+
3. **Other terminals**: Check that ANSI color support is enabled

## Example Session Output

```
================================================================================
MULTIPLIER READER
================================================================================

[14:15:03] INFO: Started
[14:15:03] INFO: Region: (117, 1014) to (292, 1066)
[14:15:03] INFO: Update interval: 0.5s
[14:15:03] INFO: Press Ctrl+C to stop

[14:15:03] STATUS: WAITING for first round...
[14:15:03] [START] ROUND 1 STARTED
[14:15:03] R:1 | CURR:  11.22x | MAX: 11.22x | DUR:   0.0s | TREND: _
[14:15:04] R:1 | CURR:  11.89x | MAX: 11.89x | DUR:   0.7s | TREND: _@
[14:15:05] R:1 | CURR:  12.61x | MAX: 12.61x | DUR:   1.5s | TREND: _=@
[14:15:06] R:1 | CURR:  13.37x | MAX: 13.37x | DUR:   2.2s | TREND: _-^@
[14:15:07] R:1 | CURR:  15.27x | MAX: 15.27x | DUR:   3.7s | TREND: _.-=*@
[14:15:08] R:1 | CURR:  17.16x | MAX: 17.16x | DUR:   4.4s | TREND: __=^*@
[14:15:10] R:1 | CURR:  20.79x | MAX: 20.79x | DUR:   7.4s | TREND: __..-=^^*@
[14:15:12] R:1 | CURR:  23.36x | MAX: 23.36x | DUR:   8.8s | TREND: __..-=^*#@
[14:15:14] R:1 | CURR:  27.83x | MAX: 27.83x | DUR:  11.0s | TREND: __..-=^*#@
[14:15:16] R:1 | CURR:  31.80x | MAX: 31.80x | DUR:  12.5s | TREND: __..-=^^*@
[14:15:18] R:1 | CURR:  35.96x | MAX: 35.96x | DUR:  14.7s | TREND: __.--=^*@@

[14:15:19] [CRASH] Reached 35.96x in 15.46s

================================================================================
ROUND ENDED
================================================================================

Round   Start Time  End Time    Duration    Max Mult    Crash At    Status    Events
----------------------------------------------------------------------------------------------------
1       14:15:03    14:15:19    15.46s      35.96x      35.96x      CRASHED   21

[14:15:19] INFO: Waiting for next round...
[14:15:25] [START] ROUND 2 STARTED
[14:15:25] R:2 | CURR:   1.03x | MAX:   1.03x | DUR:   0.0s | TREND: _
[14:15:26] R:2 | CURR:   1.09x | MAX:   1.09x | DUR:   0.7s | TREND: _@
[14:15:27] R:2 | CURR:   1.16x | MAX:   1.16x | DUR:   1.5s | TREND: _=@
```

## Benefits

✅ **Visual Appeal** - Color-coded output makes information easy to scan
✅ **Trend Visualization** - Sparkline shows multiplier movement at a glance
✅ **Compact Display** - All information on a single line per update
✅ **Terminal Compatible** - Works in Windows Terminal, PowerShell, Linux, macOS
✅ **No Special Characters** - Uses only ASCII, no emoji or Unicode issues
✅ **Professional Appearance** - Dashboard-like organized columns
✅ **Easy to Read** - Aligned columns with clear separators

## Implementation Details

### File: main.py

**Colors Class**
- Defines ANSI color codes for terminal output
- Provides `get_multiplier_color()` method for dynamic color selection

**Sparkline Generation**
- `generate_sparkline()` method creates ASCII trend visualization
- Tracks last 10 multiplier values
- Normalizes values to 0-7 range for 8-character block set
- Automatically scales with value range

**Status Display**
- `print_status()` generates colored, formatted status line
- Only prints when values change (not every tick)
- Maintains compact column alignment
- Includes timestamp, round number, current/max multiplier, duration, and trend

**Event Logging**
- `log_event()` colors all game events
- Green for GAME_START
- Magenta for HIGH_MULTIPLIER
- Red for CRASH

## Customization

To modify colors, edit the `Colors` class in `main.py`:

```python
class Colors:
    GREEN = '\033[92m'   # Change green color code
    YELLOW = '\033[93m'  # Change yellow color code
    RED = '\033[91m'     # Change red color code
    MAGENTA = '\033[95m' # Change magenta color code
```

ANSI color codes:
- `\033[90m` = Dark Gray
- `\033[91m` = Red
- `\033[92m` = Green
- `\033[93m` = Yellow
- `\033[94m` = Blue
- `\033[95m` = Magenta
- `\033[96m` = Cyan
- `\033[97m` = White

## Commit Information

```
abe4241 Add enhanced visual display with colors and sparkline trends
```

To revert to previous version:
```bash
git checkout HEAD~1
```

## Running the Application

```bash
python main.py
```

The enhanced visual display will automatically activate. No configuration needed!

---

**Last Updated**: 2025-12-23
**Status**: ✅ Production Ready
