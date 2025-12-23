# Multiplier Reader with Supabase

A Python-based real-time multiplier detection tool for games with multiplier mechanics. It captures the game screen, reads the multiplier value using OCR, tracks game events, and automatically saves round data to Supabase.

## Features

- **Real-time Multiplier Detection**: Reads multiplier values from screen using OCR
- **Game Event Tracking**: Detects game starts, multiplier increases, crashes, and high multipliers
- **Automatic Data Storage**: Saves completed rounds to Supabase database
- **GUI Region Selector**: Easy-to-use interface to select the multiplier region on screen
- **Color-coded Output**: Terminal output with ANSI colors and ASCII sparklines
- **Statistics Tracking**: Keeps track of crashes, max multipliers, and Supabase insertions
- **Graceful Offline Mode**: Works even if Supabase is unavailable

## Project Structure

```
bot/
├── main.py                 # Main monitoring loop with Supabase integration
├── gui_selector.py        # GUI for region selection
├── config.py              # Region configuration management
├── screen_capture.py      # Screen capture and image processing
├── multiplier_reader.py   # OCR and multiplier extraction
├── game_tracker.py        # Game state and event tracking
├── supabase_client.py     # Supabase database client
├── test_capture.py        # OCR testing utility
├── multiplier_config.json # Saved region configuration
├── requirements.txt       # Python dependencies
├── SUPABASE_WORKING.md    # Supabase integration guide
└── README.md              # This file
```

## Installation

### 1. Clone/Download the Repository

```bash
cd /path/to/bot
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Tesseract OCR

**Windows:**
- Download installer: https://github.com/UB-Mannheim/tesseract/wiki
- Install (default: `C:\Program Files\Tesseract-OCR`)
- Update path in `multiplier_reader.py`:
  ```python
  pytesseract.pytesseract.pytesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
  ```

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

## Usage

### Step 1: Configure Region

Run the GUI selector to select the multiplier region:

```bash
python gui_selector.py
```

- Click and drag to select the region containing the multiplier
- Click "Save Region" to save configuration
- The configuration is saved to `multiplier_config.json`

**Tips:**
- Select a region that includes the entire multiplier display (1.23x, 5.50x, etc.)
- Avoid including other UI elements in the selection
- Use "Test Region" to preview the captured area

### Step 2: Start Monitoring

Run the main monitoring application:

```bash
python main.py [update_interval]
```

**Examples:**
```bash
python main.py              # Default: 0.5 second intervals
python main.py 0.2          # Faster: 0.2 second intervals
python main.py 1.0          # Slower: 1.0 second intervals
```

### Output

The application will display:
- Real-time multiplier values
- Game events (starts, increases, crashes)
- Current round statistics
- Overall statistics when stopped (Ctrl+C)

**Example Output:**
```
[2024-01-15 14:23:45.123] Multiplier Reader started
[2024-01-15 14:23:45.234] Region: (150, 50) to (300, 120)
[2024-01-15 14:23:45.345] Update interval: 0.5s

[2024-01-15 14:23:46.123] 🟢 GAME_START: New round initiated
   Current: 1.00x | Max: 1.00x | Duration: 0.23s | Status: STARTING
[2024-01-15 14:23:46.456] 📈 MULTIPLIER_INCREASE: 1.50x (+0.50)
   Current: 1.50x | Max: 1.50x | Duration: 0.56s | Status: RUNNING
[2024-01-15 14:23:47.123] ⚡ HIGH_MULTIPLIER: Reached 10.00x
   Current: 10.00x | Max: 10.00x | Duration: 1.23s | Status: HIGH
[2024-01-15 14:23:48.456] 🔴 CRASH: Reached 25.50x in 3.12s
```

## Configuration

Configuration is stored in `multiplier_config.json`:

```json
{
  "x1": 150,
  "y1": 50,
  "x2": 300,
  "y2": 120
}
```

To load a saved configuration:
1. Run `gui_selector.py`
2. Click "Load Last Config"
3. Adjust if needed and save

## Game Status Detection

The system detects the following statuses:

| Status | Multiplier Range | Meaning |
|--------|------------------|---------|
| CRASHED | ≤ 0.5x | Game crashed/burst |
| STARTING | = 1.0x | Game round starting |
| RUNNING | 1.0x - 10x | Game in progress |
| HIGH | ≥ 10x | High multiplier reached |

## Events Tracked

- **GAME_START**: New round begins
- **MULTIPLIER_INCREASE**: Multiplier increases
- **HIGH_MULTIPLIER**: Reaches configured threshold (default: 10x)
- **CRASH**: Game crashes/ends
- **ERROR**: Read failure

## Advanced Configuration

### Adjust Detection Sensitivity

Edit `game_tracker.py`:

```python
# Change crash threshold (default: 0.5)
tracker = GameTracker(crash_threshold=0.3)

# Change high multiplier threshold (default: 10)
tracker.high_multiplier_threshold = 5
```

### Adjust Update Frequency

```bash
# Very fast: every 0.1 seconds (may cause lag)
python main.py 0.1

# Balanced: every 0.5 seconds (default)
python main.py 0.5

# Relaxed: every 1.0 second
python main.py 1.0
```

## Troubleshooting

### OCR Not Working

**Issue**: "Could not read multiplier" errors

**Solutions:**
1. Check Tesseract is installed and path is correct
2. Verify region selection includes the multiplier clearly
3. Run `gui_selector.py` and use "Test Region" to verify capture

### Region Selection Issues

**Issue**: Selected region not being captured correctly

**Solutions:**
1. Run `gui_selector.py` again
2. Make sure region has good contrast
3. Include sufficient padding around the multiplier text

### Low Success Rate

**Issue**: Many failed reads

**Solutions:**
1. Adjust update interval (slower = more stable)
2. Improve region selection (clearer text area)
3. Check for window scaling or display issues

## Performance

- CPU Usage: Low (mostly waiting for screen capture)
- Memory Usage: ~50-100MB
- Network: None

## Limitations

- OCR accuracy depends on font clarity and contrast
- Works best with 1920x1080 or higher resolution
- Requires game window to be visible (can be minimized but not covered)

## Supabase Integration

Round data is automatically saved to Supabase when rounds complete:

- **Data Saved**: roundId, multiplier, timestamp
- **Automatic**: No configuration needed
- **Graceful Degradation**: Works offline, saves when connection recovers

See [SUPABASE_WORKING.md](SUPABASE_WORKING.md) for configuration details.

## Future Improvements

- [ ] RLS policies for better security
- [ ] Real-time dashboard with live data
- [ ] Export to CSV/JSON
- [ ] Detailed analytics per session
- [ ] Sound/notification alerts

## License

Open source for educational use.

## Support

For issues:
1. Check troubleshooting section above
2. Verify Tesseract installation
3. See [SUPABASE_WORKING.md](SUPABASE_WORKING.md) for Supabase issues
4. Review configuration in `multiplier_config.json`
