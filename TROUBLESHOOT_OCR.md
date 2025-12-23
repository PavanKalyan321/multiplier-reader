# Troubleshooting Guide - OCR Not Reading Multiplier

## Issue
The application says "Waiting for next round" and doesn't detect the multiplier value.

## Root Cause
The selected region doesn't properly cover the multiplier text, OR the region is empty when the screenshot is taken.

## Solution Steps

### Step 1: Check Your Region Selection

The region coordinates shown are: `(117, 1009) to (309, 1064)`

This should cover the area where the multiplier is displayed on your screen.

**To verify:**
1. Look at `test_region_raw.png` in your bot folder
2. This image should show the multiplier text clearly
3. If it shows a blank area, the region is wrong

### Step 2: Reconfigure the Region

If the region is wrong:

```bash
python gui_selector.py
```

When the GUI opens:
1. **Click and drag** to select the multiplier area
2. Make sure the selected box includes the ENTIRE multiplier text (e.g., "25.50x")
3. Click "Save Region"
4. Click "Test Region" to verify

**Important Tips:**
- Select slightly LARGER than needed (add padding)
- The multiplier text should be clearly visible in the preview
- Don't include other UI elements that move

### Step 3: Verify Tesseract is Working

Run the diagnostic test:

```bash
python test_capture.py
```

This will:
1. Check your configuration
2. Capture your screen region
3. Try to read it with Tesseract
4. Show results

**Look for:**
- `test_region_raw.png` - Should show multiplier text
- `test_region_processed.png` - Should show binary version
- Console output should show extracted numbers

### Step 4: Common Issues & Fixes

#### Issue: "Empty region" or blank image
**Cause:** Region doesn't cover the multiplier
**Fix:** Reconfigure with `python gui_selector.py`

#### Issue: "Text not recognized"
**Cause:** Tesseract can't read the font/size
**Fix:**
- Adjust region slightly larger
- Make sure text is clear (not too small)
- Try higher game zoom level

#### Issue: "Wrong multiplier values"
**Cause:** Region includes other numbers or text
**Fix:** Make region SMALLER to include only the multiplier

#### Issue: Tesseract path error
**Cause:** Tesseract not installed in standard location
**Fix:**
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to: `C:\Program Files\Tesseract-OCR\`
3. Or edit this line in `multiplier_reader.py`:
   ```python
   tesseract_path = r"YOUR\CUSTOM\PATH\tesseract.exe"
   ```

### Step 5: Debug Information

To get more detailed debugging:

1. Check captured images:
   ```bash
   python test_capture.py
   ```

2. Look at `test_region_raw.png`:
   - Should show the multiplier text clearly
   - If blank or wrong area, fix region selection

3. Look at `test_region_processed.png`:
   - Shows the binary version Tesseract sees
   - Should show clear black text on white

### Step 6: Test with Live Game

Once configuration looks good:

```bash
python main.py
```

While the game is running:
1. Start a round
2. Watch for multiplier updates
3. You should see ONE line updating with current multiplier

If you still see "Waiting for next round...":
- Reconfigure the region
- Make sure game window is visible
- Try larger/adjusted region bounds

## Quick Checklist

- [ ] Region selection covers the multiplier text
- [ ] `test_region_raw.png` shows multiplier clearly
- [ ] Tesseract is installed at `C:\Program Files\Tesseract-OCR\`
- [ ] Game window is visible and running
- [ ] Multiplier text is large enough to read

## Getting Help

If you're still having issues:

1. **Take a screenshot of your game**
2. **Note the multiplier location** (e.g., top-right, bottom-left)
3. **Run:** `python gui_selector.py`
4. **Select that area carefully** with some padding
5. **Save and test**
6. **Run:** `python test_capture.py`
7. **Check the test images** to see if text is visible

## Success Indicators

When working correctly, you'll see:

```
[13:16:18] ROUND: 🟢 ROUND 1 STARTED
[13:16:20] STATUS: Multiplier: 1.62x | Max: 1.62x | Time: 2.1s | Status: RUNNING | Round: 1
[13:16:21] STATUS: Multiplier: 2.35x | Max: 2.35x | Time: 3.0s | Status: RUNNING | Round: 1
```

Not just "Waiting for next round..."

---

**The most common cause:** Region doesn't properly cover the multiplier text.
**The fix:** Reconfigure with `python gui_selector.py` and select a larger area.
