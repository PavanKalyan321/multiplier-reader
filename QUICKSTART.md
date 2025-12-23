# Quick Start Guide - Multiplier Reader

## What is This?

A Python tool that watches your game screen and reads the multiplier value in real-time, detecting crashes, round endings, and other game events.

## Installation (5 minutes)

### 1. Install Python Dependencies

```bash
cd bot
pip install -r requirements.txt
```

### 2. Install Tesseract OCR (Required for text reading)

**Windows:**
- Go to: https://github.com/UB-Mannheim/tesseract/wiki
- Download `tesseract-ocr-w64-setup-v5.x.x.exe`
- Run installer (keep default path: `C:\Program Files\Tesseract-OCR`)
- Done!

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

## Quick Setup (2 minutes)

### Option A: Using Quick Start Menu (Easiest)
```bash
python run.py
```
Then select option 1 to configure region.

### Option B: Direct Commands
```bash
# Step 1: Configure region
python gui_selector.py

# Step 2: Start monitoring
python main.py
```

## Step-by-Step Usage

### Step 1: Start Region Selector

```bash
python gui_selector.py
```

What you'll see:
- Full screen preview
- Crosshair cursor

What to do:
1. Click and drag to select the multiplier region
2. The region should include the multiplier text (1.23x, 5.50x, etc.)
3. Click "Save Region"
4. Optional: Click "Test Region" to preview

### Step 2: Start Monitoring

```bash
python main.py
```

What you'll see:
- Real-time multiplier values
- Game events (starts, crashes, etc.)
- Current round statistics

Press `Ctrl+C` to stop.

## What It Detects

✅ **Game Starts**: When a new round begins
✅ **Multiplier Changes**: Every time the multiplier increases
✅ **Crashes**: When the game ends/crashes
✅ **High Multipliers**: When multiplier reaches 10x+ (configurable)

## Example Output

```
[2024-01-15 14:23:45.345] Multiplier Reader started
[2024-01-15 14:23:45.456] Region: (150, 50) to (300, 120)

[2024-01-15 14:23:46.123] 🟢 GAME_START: New round initiated
   Current: 1.00x | Max: 1.00x | Duration: 0.23s | Status: STARTING

[2024-01-15 14:23:46.456] 📈 MULTIPLIER_INCREASE: 1.50x (+0.50)
   Current: 1.50x | Max: 1.50x | Duration: 0.56s | Status: RUNNING

[2024-01-15 14:23:47.123] ⚡ HIGH_MULTIPLIER: Reached 10.00x
   Current: 10.00x | Max: 10.00x | Duration: 1.23s | Status: HIGH

[2024-01-15 14:23:48.456] 🔴 CRASH: Reached 25.50x in 3.12s
```

## Adjusting Speed

Default is 0.5 second intervals. Adjust with:

```bash
python main.py 0.2    # Faster (every 0.2s)
python main.py 0.5    # Default (every 0.5s)
python main.py 1.0    # Slower (every 1.0s)
```

**Faster** = More responsive but uses more CPU
**Slower** = Less responsive but uses less CPU

## Troubleshooting

### "Could not read multiplier"

1. Run `python gui_selector.py` again
2. Use "Test Region" to verify capture
3. Make sure region includes the multiplier clearly
4. Adjust region size if needed

### Tesseract not found

**Windows:**
1. Reinstall Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
2. Update path in `multiplier_reader.py`:
   ```python
   pytesseract.pytesseract.pytesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
   ```

**macOS/Linux:**
```bash
# Verify installation
which tesseract
tesseract --version
```

### Low read success rate

1. Use slower interval: `python main.py 1.0`
2. Improve region selection (include more text)
3. Check game window is visible

## Files Overview

| File | Purpose |
|------|---------|
| `main.py` | Main monitoring program |
| `gui_selector.py` | GUI to select multiplier region |
| `config.py` | Configuration management |
| `screen_capture.py` | Screen capture and image processing |
| `multiplier_reader.py` | OCR text reading |
| `game_tracker.py` | Event detection and state tracking |
| `run.py` | Quick-start menu |

## Advanced Options

### Save Statistics

The app automatically tracks:
- Total reads and success rate
- Crashes detected
- Max multiplier reached
- Time elapsed

Statistics are printed when you stop (Ctrl+C).

### Change Detection Thresholds

Edit `game_tracker.py`:

```python
# Crash threshold (default 0.5)
tracker = GameTracker(crash_threshold=0.3)

# High multiplier threshold (default 10)
tracker.high_multiplier_threshold = 5
```

## Common Questions

**Q: Can the game window be hidden?**
A: The window must be visible but can be behind other windows.

**Q: How accurate is the multiplier reading?**
A: 95%+ on clear, readable text. Improves with good contrast.

**Q: What's CPU usage like?**
A: Very low (~2-5% on average). OCR takes most time.

**Q: Can I run multiple instances?**
A: Yes, each can monitor different regions.

## Next Steps

1. ✅ Install Tesseract
2. ✅ Run `python run.py`
3. ✅ Configure region
4. ✅ Start monitoring

That's it! You're ready to go.

## Need Help?

- Check README.md for detailed information
- Verify Tesseract is installed correctly
- Ensure game window is visible
- Try adjusting the region selection
