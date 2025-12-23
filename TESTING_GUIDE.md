# Testing & Verification Guide

Complete guide for testing and validating the Multiplier Reader installation and functionality.

## Installation Verification

### Test 1: Python Installation

**Command:**
```bash
python --version
pip --version
```

**Expected Output:**
```
Python 3.8.x or higher
pip 20.x or higher
```

**If fails:** Reinstall Python with "Add to PATH" option

### Test 2: Dependencies Installation

**Command:**
```bash
pip list
```

**Expected packages:**
- opencv-python (4.8.x)
- Pillow (10.x)
- pytesseract (0.3.x)
- numpy (1.24.x)

**If missing:**
```bash
pip install -r requirements.txt
```

### Test 3: Tesseract Installation

**Command:**
```bash
tesseract --version
```

**Expected Output:**
```
tesseract v5.x.x
```

**If fails:**
- Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
- Mac: `brew install tesseract`
- Linux: `sudo apt-get install tesseract-ocr`

### Test 4: Python Module Imports

**Command:**
```bash
python -c "import cv2, PIL, pytesseract, numpy; print('✓ All modules loaded successfully')"
```

**Expected Output:**
```
✓ All modules loaded successfully
```

**If fails:** Run `pip install -r requirements.txt` again

---

## Component Testing

### Test 5: Screen Capture Module

**File:** `test_screen_capture.py`

**Create this test file:**
```python
from screen_capture import ScreenCapture
from config import get_default_region
import time

print("Testing ScreenCapture module...")

# Test 1: Full screen capture
print("1. Testing full screen capture...")
sc = ScreenCapture()
frame = sc.capture_full_screen()
print(f"   ✓ Full screen captured: {frame.shape}")

# Test 2: Region capture
print("2. Testing region capture...")
region = get_default_region()
sc.set_region(region)
frame = sc.capture_region()
print(f"   ✓ Region captured: {frame.shape}")

# Test 3: Image preprocessing
print("3. Testing image preprocessing...")
processed = sc.preprocess_image(frame)
print(f"   ✓ Image preprocessed: {processed.shape}")
print(f"   ✓ Data type: {processed.dtype}")

# Test 4: Change detection
print("4. Testing change detection...")
changed, percentage = sc.detect_changes(processed)
print(f"   ✓ Change detected: {changed}, Percentage: {percentage:.2f}%")

print("\n✓ All ScreenCapture tests passed!")
```

**Run:**
```bash
python test_screen_capture.py
```

**Expected output:**
```
Testing ScreenCapture module...
1. Testing full screen capture...
   ✓ Full screen captured: (1080, 1920, 3)
2. Testing region capture...
   ✓ Region captured: (100, 150, 3)
3. Testing image preprocessing...
   ✓ Image preprocessed: (100, 150)
   ✓ Data type: uint8
4. Testing change detection...
   ✓ Change detected: True, Percentage: 25.50%

✓ All ScreenCapture tests passed!
```

### Test 6: Configuration Module

**File:** `test_config.py`

**Create this test file:**
```python
from config import RegionConfig, save_config, load_config
import os

print("Testing config module...")

# Test 1: Create RegionConfig
print("1. Testing RegionConfig creation...")
region = RegionConfig(x1=100, y1=50, x2=200, y2=150)
print(f"   ✓ Region created: {region}")

# Test 2: Validate region
print("2. Testing region validation...")
assert region.is_valid(), "Region should be valid"
print(f"   ✓ Region is valid")

# Test 3: Save config
print("3. Testing config save...")
save_config(region)
assert os.path.exists("multiplier_config.json"), "Config file should exist"
print(f"   ✓ Config saved to multiplier_config.json")

# Test 4: Load config
print("4. Testing config load...")
loaded = load_config()
assert loaded is not None, "Config should load"
assert loaded.x1 == 100, "Coordinates should match"
print(f"   ✓ Config loaded: {loaded}")

print("\n✓ All config tests passed!")
```

**Run:**
```bash
python test_config.py
```

**Expected output:**
```
Testing config module...
1. Testing RegionConfig creation...
   ✓ Region created: RegionConfig(x1=100, y1=50, x2=200, y2=150)
2. Testing region validation...
   ✓ Region is valid
3. Testing config save...
   ✓ Config saved to multiplier_config.json
4. Testing config load...
   ✓ Config loaded: RegionConfig(x1=100, y1=50, x2=200, y2=150)

✓ All config tests passed!
```

### Test 7: Multiplier Reader Module

**File:** `test_multiplier_reader.py`

**Create this test file:**
```python
from multiplier_reader import MultiplierReader
from screen_capture import ScreenCapture
from config import get_default_region
import cv2
import numpy as np

print("Testing MultiplierReader module...")

# Create a test image with text
print("1. Creating test image with multiplier text...")
test_img = np.ones((100, 200, 3), dtype=np.uint8) * 255

# Add some black text (simulating multiplier)
cv2.putText(test_img, "5.23x", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, 0, 2)
cv2.imwrite("test_multiplier.png", test_img)
print(f"   ✓ Test image created: test_multiplier.png")

# Test 2: Extract multiplier
print("2. Testing multiplier extraction...")
sc = ScreenCapture(get_default_region())
reader = MultiplierReader(sc)
multiplier = reader.extract_multiplier(test_img)
print(f"   ✓ Extracted multiplier: {multiplier}")

# Test 3: Status detection
print("3. Testing status detection...")
status = reader._detect_status(5.23)
print(f"   ✓ Status detected: {status}")

# Test 4: Status message
print("4. Testing status message...")
message = reader._get_status_message(status)
print(f"   ✓ Status message: {message}")

print("\n✓ All MultiplierReader tests passed!")
```

**Run:**
```bash
python test_multiplier_reader.py
```

**Expected output:**
```
Testing MultiplierReader module...
1. Creating test image with multiplier text...
   ✓ Test image created: test_multiplier.png
2. Testing multiplier extraction...
   ✓ Extracted multiplier: 5.23
3. Testing status detection...
   ✓ Status detected: RUNNING
4. Testing status message...
   ✓ Status message: Game running - multiplier increasing

✓ All MultiplierReader tests passed!
```

### Test 8: Game Tracker Module

**File:** `test_game_tracker.py`

**Create this test file:**
```python
from game_tracker import GameTracker
import time

print("Testing GameTracker module...")

tracker = GameTracker()

# Test 1: Game start detection
print("1. Testing game start detection...")
events = tracker.update(1.0, 'STARTING')
assert len(events) > 0 and events[0].event_type == 'GAME_START'
print(f"   ✓ Game start detected")

# Test 2: Multiplier increase detection
print("2. Testing multiplier increase detection...")
events = tracker.update(1.5, 'RUNNING')
assert len(events) > 0 and events[0].event_type == 'MULTIPLIER_INCREASE'
print(f"   ✓ Multiplier increase detected: +0.5")

# Test 3: High multiplier detection
print("3. Testing high multiplier detection...")
tracker.update(5.0, 'RUNNING')
events = tracker.update(10.5, 'HIGH')
assert any(e.event_type == 'HIGH_MULTIPLIER' for e in events)
print(f"   ✓ High multiplier detected")

# Test 4: Crash detection
print("4. Testing crash detection...")
events = tracker.update(0.0, 'CRASHED')
assert len(events) > 0 and events[0].event_type == 'CRASH'
print(f"   ✓ Crash detected")

# Test 5: Round summary
print("5. Testing round summary...")
summary = tracker.get_round_summary()
assert summary['status'] == 'COMPLETED'
assert summary['max_multiplier'] >= 10
print(f"   ✓ Round summary: Max {summary['max_multiplier']}x")

print("\n✓ All GameTracker tests passed!")
```

**Run:**
```bash
python test_game_tracker.py
```

**Expected output:**
```
Testing GameTracker module...
1. Testing game start detection...
   ✓ Game start detected
2. Testing multiplier increase detection...
   ✓ Multiplier increase detected: +0.5
3. Testing high multiplier detection...
   ✓ High multiplier detected
4. Testing crash detection...
   ✓ Crash detected
5. Testing round summary...
   ✓ Round summary: Max 10.5x

✓ All GameTracker tests passed!
```

---

## Integration Testing

### Test 9: GUI Selector

**Steps:**
1. Run: `python gui_selector.py`
2. Verify:
   - [ ] Full screen preview displays
   - [ ] Can select region with mouse
   - [ ] Selection rectangle shows in red
   - [ ] Coordinates update as dragging
   - [ ] "Save Region" button saves config
   - [ ] "Test Region" captures correctly
   - [ ] Config file created (`multiplier_config.json`)

### Test 10: Main Monitoring Loop

**Steps:**
1. Run: `python main.py 2.0` (2 second interval for testing)
2. Play a game round manually
3. Verify:
   - [ ] Initial log shows region and interval
   - [ ] "GAME_START" logs when round begins
   - [ ] Multiplier values update regularly
   - [ ] Status changes (STARTING → RUNNING → HIGH)
   - [ ] "CRASH" logs when game ends
   - [ ] Statistics print on Ctrl+C
   - [ ] No errors or exceptions

### Test 11: Quick Start Menu

**Steps:**
1. Run: `python run.py`
2. Test each menu option:
   - [ ] Option 1: Region selector launches
   - [ ] Option 2: Monitoring starts (with default region)
   - [ ] Option 3: Shows saved config
   - [ ] Option 4: Setup script runs
   - [ ] Option 5: Exits cleanly

---

## Performance Testing

### Test 12: CPU Usage

**Procedure:**
1. Open Task Manager (Windows) or Activity Monitor (Mac)
2. Start monitoring: `python main.py 0.5`
3. Check CPU usage for python process
4. Should be: **2-5%** at idle

**Expected:**
```
python.exe: 2-4% CPU
Memory: 50-100MB
```

### Test 13: OCR Accuracy

**Procedure:**
1. Create test images with different multipliers
2. Run extract on each
3. Compare results

**Test cases:**
```
Input          │ Expected    │ Status
────────────────┼─────────────┼────────
"1.23x"         │ 1.23        │ ✓ PASS
"5.5x"          │ 5.5         │ ✓ PASS
"25x"           │ 25.0        │ ✓ PASS
"100.00x"       │ 100.0       │ ✓ PASS
"1,234.56x"     │ 1234.56     │ ✓ PASS (if supported)
"invalid"       │ None        │ ✓ PASS
```

### Test 14: Response Time

**Procedure:**
1. Note time of game change
2. Note time of log output
3. Measure latency

**Expected: < 1 second latency** (depends on interval)

---

## Troubleshooting Test Procedures

### Issue: Low OCR Accuracy

**Test:**
```bash
python -c "
from screen_capture import ScreenCapture
from config import load_config
from multiplier_reader import MultiplierReader
import cv2

config = load_config()
if config:
    sc = ScreenCapture(config)
    reader = MultiplierReader(sc)

    # Take 10 samples
    for i in range(10):
        mult = reader.read_multiplier()
        print(f'Sample {i+1}: {mult}')
"
```

**If inconsistent:** Region selection needs improvement

### Issue: Screen Capture Fails

**Test:**
```bash
python -c "
from screen_capture import ScreenCapture
sc = ScreenCapture()
frame = sc.capture_full_screen()
print(f'Screen size: {frame.shape}')
cv2.imwrite('test_screen.png', frame)
print('Screenshot saved as test_screen.png')
"
```

**If fails:** Try running as Administrator

### Issue: Module Import Error

**Test:**
```bash
python -c "import cv2; print(cv2.__version__)"
python -c "import PIL; print(PIL.__version__)"
python -c "import pytesseract; print(pytesseract.__version__)"
python -c "import numpy; print(numpy.__version__)"
```

**If any fail:** Reinstall that package

---

## Checklist

### Before Production Use

- [ ] Python 3.8+ installed
- [ ] Tesseract installed and working
- [ ] All dependencies installed (`requirements.txt`)
- [ ] GUI selector works
- [ ] Region can be selected and saved
- [ ] Test region preview looks correct
- [ ] Main monitoring loop runs without errors
- [ ] Multiplier values are being read correctly
- [ ] Events are being detected (with actual game)
- [ ] Statistics are accurate
- [ ] CPU usage acceptable (< 10%)
- [ ] No memory leaks (check after 1 hour)

### Quick Verification Command

```bash
echo "=== Installation Check ===" && \
echo "Python:" && python --version && \
echo "Tesseract:" && tesseract --version && \
echo "Dependencies:" && python -c "import cv2, PIL, pytesseract, numpy; print('✓ All OK')" && \
echo "=== All systems operational ==="
```

---

## Test Results Log

Keep a record of test results:

```
Date: [DATE]
Python Version: [VERSION]
OS: [OS]
Tesseract Version: [VERSION]

Tests:
[ ] Installation verification - PASS/FAIL
[ ] Screen capture test - PASS/FAIL
[ ] Config test - PASS/FAIL
[ ] Multiplier reader test - PASS/FAIL
[ ] Game tracker test - PASS/FAIL
[ ] GUI selector test - PASS/FAIL
[ ] Main monitoring loop test - PASS/FAIL

Performance:
- CPU Usage: [X]%
- Memory Usage: [X]MB
- OCR Accuracy: [X]%

Notes:
[Any issues or observations]
```

---

This comprehensive testing guide ensures your Multiplier Reader is properly installed and functioning correctly before actual use.
