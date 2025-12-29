# Auto-Refresh Feature Guide

## Overview

The auto-refresh feature automatically moves the mouse pointer to the top-right corner of the multiplier read region, clicks to focus the window, and presses F5 to refresh every 15 minutes. This helps keep the multiplier display fresh and prevents stale data.

## How It Works

1. **Background Thread**: The auto-refresher runs in a separate background thread that doesn't interfere with the main multiplier reading loop.

2. **Periodic Execution**: Every 15 minutes (900 seconds by default), the refresher:
   - Moves the mouse to the top-right corner of the configured region
   - Waits briefly (0.2 seconds)
   - Clicks to give focus to the browser/application window
   - Waits (0.3 seconds) to ensure focus is set
   - Presses F5 (standard refresh key)
   - Logs the action to the console

3. **Configurable Interval**: You can customize the refresh interval when starting the application.

## Usage

### Default Behavior (15 minutes)

Simply run the main application as usual:

```bash
python main.py
```

The auto-refresh will start automatically with a 15-minute interval.

### Custom Refresh Interval

To change the refresh interval, you'll need to modify the code slightly. For example, to set a 10-minute interval:

```python
app = MultiplierReaderApp(update_interval=0.5, auto_refresh_interval=600)  # 600 seconds = 10 minutes
```

### Testing the Auto-Refresh

A test script is provided to verify the functionality:

```bash
python test_auto_refresh.py
```

This test script uses a 30-second interval for quick testing and demonstrates:
- Manual refresh trigger
- Background auto-refresh thread
- Time-until-next-refresh display

## Configuration

### Region Configuration

The auto-refresh uses the same region configuration as the multiplier reader. The top-right corner is calculated as:
- X-coordinate: `region.x2` (right edge)
- Y-coordinate: `region.y1` (top edge)

Make sure your region is properly configured using:

```bash
python configure_region.py
```

### Refresh Interval

Default: 900 seconds (15 minutes)

You can modify this in the `MultiplierReaderApp` initialization:

```python
self.auto_refresher = AutoRefresher(self.region, refresh_interval=900)
```

Common intervals:
- 5 minutes: 300 seconds
- 10 minutes: 600 seconds
- 15 minutes: 900 seconds (default)
- 30 minutes: 1800 seconds
- 1 hour: 3600 seconds

## Technical Details

### Dependencies

The auto-refresh feature requires the `pyautogui` library:

```bash
pip install pyautogui
```

This is automatically included in `requirements.txt`.

### Implementation Files

1. **auto_refresh.py**: Core module containing the `AutoRefresher` class
2. **main.py**: Integrated auto-refresh into the main application
3. **test_auto_refresh.py**: Test script for verification

### AutoRefresher Class

Key methods:
- `start()`: Starts the background refresh thread
- `stop()`: Stops the background thread gracefully
- `perform_refresh()`: Manually triggers a refresh
- `get_time_until_next_refresh()`: Returns seconds until next auto-refresh

## Troubleshooting

### Mouse Doesn't Move

- Verify the region is correctly configured
- Check that pyautogui is installed: `pip list | grep pyautogui`
- Ensure your system allows programmatic mouse control

### F5 Doesn't Refresh

- Ensure the window has focus by checking if the click is working
- Some applications may not respond to simulated keyboard input
- Try the test script to verify keyboard simulation works: `python test_auto_refresh.py`
- The browser/application window must be visible (not minimized) for F5 to work
- Check if there are any pop-ups or dialogs blocking the refresh

### Performance Impact

The auto-refresh runs in a background thread with minimal overhead:
- Sleep interval: 1 second check cycle
- Mouse movement: 0.5 seconds duration
- Total refresh action: ~0.7 seconds every 15 minutes

## Logs

Auto-refresh actions are logged to the console:

```
[12:34:56] AUTO-REFRESH: Started (interval: 900s = 15.0 minutes)
[12:34:56] AUTO-REFRESH: Target region top-right corner: (363, 1000)
...
[12:49:56] AUTO-REFRESH: Moved to (363, 1000), clicked, and pressed F5
```

## Disabling Auto-Refresh

To disable the auto-refresh feature:

1. Comment out the start/stop calls in `main.py`:

```python
# self.auto_refresher.start()
# ...
# self.auto_refresher.stop()
```

Or set an extremely long interval (e.g., 24 hours):

```python
self.auto_refresher = AutoRefresher(self.region, refresh_interval=86400)
```
