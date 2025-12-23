# Windows Setup Guide

Complete step-by-step guide for setting up Multiplier Reader on Windows.

## Prerequisites

- Windows 10 or later
- Python 3.8+ installed
  - Download from: https://www.python.org/downloads/
  - When installing, **check "Add Python to PATH"**

## Installation Steps

### Step 1: Verify Python Installation

Open Command Prompt and run:

```cmd
python --version
pip --version
```

Should show Python 3.8 or higher.

### Step 2: Navigate to Bot Folder

```cmd
cd C:\Users\[YourUsername]\OneDrive\Desktop\bot
```

Replace `[YourUsername]` with your actual Windows username.

### Step 3: Install Python Dependencies

```cmd
pip install -r requirements.txt
```

This installs:
- opencv-python (screen capture)
- Pillow (image processing)
- pytesseract (OCR interface)
- numpy (numerical operations)

Wait for it to complete (1-2 minutes).

### Step 4: Install Tesseract OCR

This is the most important step for text recognition.

#### Download

1. Go to: https://github.com/UB-Mannheim/tesseract/wiki
2. Under "Downloads", click the latest `.exe` file
   - Look for: `tesseract-ocr-w64-setup-v5.x.x.exe`
3. Save to your Downloads folder

#### Install

1. Run the downloaded `.exe` file
2. Click "Install"
3. **Important**: Keep the default path: `C:\Program Files\Tesseract-OCR`
4. Choose "Full Installation" (includes language packs)
5. Click "Finish"

#### Verify Installation

Open Command Prompt and run:

```cmd
tesseract --version
```

Should display Tesseract version info.

## Quick Start

### Method 1: Using Menu (Recommended)

```cmd
python run.py
```

A menu will appear:
- Press `1` to configure region
- Press `2` to start monitoring

### Method 2: Direct Commands

#### Configure Region

```cmd
python gui_selector.py
```

- A window will open showing your screen
- Click and drag to select the multiplier area
- Click "Save Region"

#### Start Monitoring

```cmd
python main.py
```

You'll see real-time multiplier readings.

Press `Ctrl+C` to stop.

## Windows-Specific Issues

### Issue: "Python not found"

**Solution**: Python not in PATH

1. Reinstall Python from https://www.python.org/downloads/
2. **Make sure to check "Add Python to PATH" during installation**
3. Restart Command Prompt after installation
4. Try `python --version` again

### Issue: "Tesseract not found"

**Solution 1**: Tesseract not installed

1. Download and install from: https://github.com/UB-Mannheim/tesseract/wiki
2. Use default path: `C:\Program Files\Tesseract-OCR`
3. Restart Command Prompt
4. Try `tesseract --version` again

**Solution 2**: Using non-standard Tesseract path

If you installed to a different location:

1. Open `multiplier_reader.py` in a text editor
2. Find the line: `pytesseract.pytesseract.pytesseract_cmd = r"..."`
3. Add/modify it with your path:
   ```python
   import pytesseract
   pytesseract.pytesseract.pytesseract_cmd = r"C:\Your\Custom\Path\tesseract.exe"
   ```
4. Save the file

### Issue: "No module named 'cv2'"

**Solution**: Dependencies not installed

```cmd
pip install opencv-python Pillow pytesseract numpy
```

### Issue: Screen capture not working

**Solution**: Permission issue or display settings

1. Run Command Prompt as Administrator
2. Try again
3. Ensure game is on primary monitor
4. Check Windows display scaling (set to 100%)

## Performance Tuning

### Slower Updates (More Stable)

```cmd
python main.py 1.0
```

### Faster Updates (More Responsive)

```cmd
python main.py 0.2
```

### Recommended Settings

For most games:
```cmd
python main.py 0.5
```

## Firewall/Antivirus

If you get blocked:

1. Windows Defender: Allow the script through
   - Settings → Firewall → Allow an app through firewall
2. Third-party antivirus: Add exception for Python

The tool doesn't use network, so it's safe.

## Creating a Desktop Shortcut

To run from desktop without command line:

1. Right-click desktop → New → Shortcut
2. Paste this path:
   ```
   C:\Users\[YourUsername]\AppData\Local\Programs\Python\Python310\python.exe run.py
   ```
   (Replace Python310 with your version)
3. Change "Location" to your bot folder
4. Name it "Multiplier Reader"
5. Click Finish

## Full File Structure

After installation, you should have:

```
C:\Users\[YourUsername]\OneDrive\Desktop\bot\
├── main.py
├── gui_selector.py
├── config.py
├── screen_capture.py
├── multiplier_reader.py
├── game_tracker.py
├── run.py
├── setup.py
├── requirements.txt
├── README.md
├── QUICKSTART.md
├── WINDOWS_SETUP.md
└── multiplier_config.json (created after setup)
```

## Testing Installation

Run this command to test everything:

```cmd
python -c "import cv2, PIL, pytesseract, numpy; print('All dependencies OK!')"
```

If successful, you'll see: "All dependencies OK!"

If error, run:
```cmd
pip install -r requirements.txt
```

## Next Steps

1. ✅ Install Python (with PATH)
2. ✅ Install dependencies: `pip install -r requirements.txt`
3. ✅ Install Tesseract OCR
4. ✅ Verify: `tesseract --version`
5. ✅ Configure region: `python run.py` → Option 1
6. ✅ Start monitoring: `python run.py` → Option 2

## Support

If you encounter issues:

1. **Python not found**: Reinstall with "Add to PATH"
2. **Tesseract not found**: Install from https://github.com/UB-Mannheim/tesseract/wiki
3. **Module errors**: Run `pip install -r requirements.txt` again
4. **Screen capture fails**: Run Command Prompt as Administrator

For detailed help, see README.md
