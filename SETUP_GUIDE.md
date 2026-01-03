# Aviator Bot - Complete Setup Guide for New System

## Overview

This guide walks you through setting up the Aviator Bot on a brand new Windows computer. The setup process is fully automated and takes 5-10 minutes.

## Prerequisites

Before starting, ensure you have:
- Windows 7 or higher
- Internet connection
- Administrator access (for some installations)
- At least 500MB free disk space
- A web browser for Supabase configuration

## Quick Start (Recommended)

### Option 1: Batch File (Easiest)

1. **Download/Extract the Bot**
   - Extract the bot folder to your desired location
   - Example: `C:\Users\YourName\Desktop\bot`

2. **Run Setup Script**
   - Open Command Prompt (cmd.exe)
   - Navigate to bot folder: `cd path\to\bot`
   - Run: `SETUP.bat`
   - Wait for all packages to install
   - Press Enter when done

3. **Done!** All dependencies are installed

### Option 2: PowerShell (Advanced)

1. **Open PowerShell as Administrator**
   - Right-click PowerShell, select "Run as administrator"

2. **Enable Script Execution** (first time only)
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
   - Type `Y` and press Enter

3. **Run Setup Script**
   ```powershell
   cd path\to\bot
   .\SETUP.ps1
   ```

4. **Done!** All dependencies are installed

### Option 3: Manual Setup

If scripts don't work, install manually:

```bash
# Install Python packages
pip install opencv-python>=4.8.0
pip install Pillow>=10.1.0
pip install pytesseract>=0.3.10
pip install numpy>=1.26.0
pip install supabase>=2.0.0
pip install scikit-learn>=1.3.0
pip install pandas>=2.0.0
pip install joblib>=1.3.0
pip install pyautogui>=0.9.53
```

## Step-by-Step Manual Installation

### Step 1: Install Python

1. **Download Python**
   - Go to: https://www.python.org/downloads/
   - Download Python 3.10 or higher (latest stable version)

2. **Install Python**
   - Run the installer
   - **IMPORTANT:** Check "Add Python to PATH"
   - Click "Install Now"
   - Wait for installation to complete

3. **Verify Installation**
   - Open Command Prompt
   - Type: `python --version`
   - Should show: `Python 3.x.x`

### Step 2: Verify pip

1. **Check pip**
   - Open Command Prompt
   - Type: `pip --version`
   - Should show version information

2. **Upgrade pip** (optional but recommended)
   ```bash
   python -m pip install --upgrade pip
   ```

### Step 3: Install Dependencies

1. **Navigate to bot folder**
   ```bash
   cd C:\path\to\bot
   ```

2. **Install all packages at once**
   ```bash
   pip install -r requirements.txt
   ```

3. **Wait for installation**
   - This may take 5-10 minutes
   - You'll see packages being downloaded and installed
   - Don't close the window

### Step 4: Install Tesseract (Optional)

Tesseract improves number recognition from screen. It's optional but recommended.

1. **Download**
   - Go to: https://github.com/UB-Mannheim/tesseract/wiki
   - Click "Download" for Windows
   - Look for: `tesseract-ocr-w64-setup-v5.x.x.exe`

2. **Install**
   - Run the installer
   - Use default path: `C:\Program Files\Tesseract-OCR`
   - Click "Install"

3. **Verify**
   - Open new Command Prompt
   - Type: `tesseract --version`
   - Should show version information

## Verify Everything Works

### Test 1: Python Packages

```bash
python -c "import cv2, PIL, supabase, numpy; print('All packages installed!')"
```

Expected output: `All packages installed!`

### Test 2: Supabase Connection

```bash
python test_model_listener.py
```

Expected output:
```
[1/4] Loading game configuration...
[OK] Configuration loaded successfully
[2/4] Initializing game components...
[OK] Game components initialized
[3/4] Creating ModelRealtimeListener...
[OK] ModelRealtimeListener created successfully
[4/4] Testing Supabase connection...
[OK] Successfully connected to Supabase!
[OK] ALL TESTS PASSED - READY TO USE
```

### Test 3: Run Main Application

```bash
python main.py
```

Expected output:
```
AVIATOR BOT - MAIN MENU
[OK] Configuration: READY
1. Start Monitoring
2. Configure Regions
3. Test Configuration
...
```

## Troubleshooting

### Problem: "Python is not recognized"

**Solution:**
1. Reinstall Python
2. **MAKE SURE TO CHECK "Add Python to PATH"**
3. Restart Command Prompt after installation

### Problem: "pip is not recognized"

**Solution:**
```bash
python -m pip --version
python -m pip install --upgrade pip
```

### Problem: "Permission Denied" or "Access Denied"

**Solution:**
1. Open Command Prompt as Administrator
2. Right-click cmd.exe, select "Run as administrator"
3. Run commands again

### Problem: "No module named 'cv2'" or other import errors

**Solution:**
```bash
pip install --upgrade --force-reinstall -r requirements.txt
```

### Problem: Installation takes forever or hangs

**Solution:**
1. Press Ctrl+C to cancel
2. Try with specific package:
   ```bash
   pip install opencv-python --no-cache-dir
   ```
3. Or try with older version:
   ```bash
   pip install opencv-python==4.8.0
   ```

### Problem: Tesseract "command not found"

**Solution:**
1. Make sure Tesseract is installed to: `C:\Program Files\Tesseract-OCR`
2. Add to PATH:
   - Open System Properties (Win+Pause)
   - Click "Advanced system settings"
   - Click "Environment Variables"
   - Under "System variables", click "New"
   - Variable name: `TESSERACT_PATH`
   - Variable value: `C:\Program Files\Tesseract-OCR`
   - Click OK

## System Requirements

### Minimum
- Windows 7 or higher
- 4GB RAM
- 500MB disk space
- Dual-core processor
- 1 Mbps internet connection

### Recommended
- Windows 10 or higher
- 8GB RAM
- 1GB disk space
- Quad-core processor
- 10 Mbps internet connection

## What Gets Installed

### Core Packages

| Package | Version | Purpose |
|---------|---------|---------|
| opencv-python | 4.8.0+ | Computer vision, image processing |
| Pillow | 10.1.0+ | Image handling |
| pytesseract | 0.3.10+ | OCR (recognize numbers from screen) |
| numpy | 1.26.0+ | Numerical computing |
| supabase | 2.0.0+ | Real-time database access |
| scikit-learn | 1.3.0+ | Machine learning utilities |
| pandas | 2.0.0+ | Data processing |
| joblib | 1.3.0+ | Data serialization |
| pyautogui | 0.9.53+ | Mouse and keyboard automation |

### External Tools (Optional)

| Tool | Purpose |
|------|---------|
| Tesseract OCR | Better number recognition from screen |

## Post-Installation Setup

After installation completes, you need to configure the bot:

### Step 1: Configure Game Regions

```bash
python main.py
# Select option 2: Configure Regions
# Follow on-screen instructions to set:
# - Balance region (where balance is displayed)
# - Multiplier region (where multiplier is shown)
# - Bet button position (where to click to place bet)
```

### Step 2: Test Configuration

```bash
python main.py
# Select option 3: Test Configuration
# Verify regions are correct
```

### Step 3: Configure Supabase (if not already done)

The bot uses Supabase for real-time signal subscriptions. Credentials should be pre-configured.

To verify or change:
1. Open `main.py`
2. Look for Supabase URL and key in pycaret_trading function
3. Update if needed

### Step 4: Start Trading!

```bash
python main.py
# Select option 7: Model Signal Listener
# Watch real-time signals and automatic trading
```

## Quick Commands Reference

```bash
# Start main application
python main.py

# Run test suite
python test_option7.py
python test_model_listener.py

# Install specific package
pip install package-name

# Upgrade specific package
pip install --upgrade package-name

# List installed packages
pip list

# Check Python version
python --version

# Check pip version
pip --version
```

## File Structure

After setup, your folder should look like:

```
bot/
├── main.py                          # Main application
├── model_realtime_listener.py       # Real-time listener
├── game_actions.py                  # Game automation
├── config.py                        # Configuration
├── requirements.txt                 # Python dependencies
├── SETUP.bat                        # Setup script (batch)
├── SETUP.ps1                        # Setup script (PowerShell)
├── SETUP_GUIDE.md                   # This file
├── QUICK_START_OPTION7.md           # Usage guide
├── BUTTON_COLOR_VALIDATION.md       # Button validation docs
├── test_option7.py                  # Test script
├── test_model_listener.py           # Test script
└── [other files...]
```

## Getting Help

If you encounter issues:

1. **Check the error message** - It usually tells you what's wrong
2. **Look in Troubleshooting section above**
3. **Check documentation files:**
   - QUICK_START_OPTION7.md
   - BUTTON_COLOR_VALIDATION.md
   - PAYLOAD_EXTRACTION_FIXED.md
4. **Run test scripts:**
   ```bash
   python test_model_listener.py
   python test_option7.py
   ```

## Next Steps

Once setup is complete:

1. Configure regions (Option 2)
2. Test configuration (Option 3)
3. Start using the listener (Option 7)
4. Monitor real-time signals and trading

## Uninstall/Clean Up

To remove everything and start fresh:

```bash
# Uninstall all packages
pip uninstall -r requirements.txt -y

# Clear pip cache
pip cache purge

# Delete the bot folder entirely
rmdir /s /q "C:\path\to\bot"
```

## Support

For additional help:
- Review documentation files in the bot folder
- Check git history: `git log --oneline`
- View detailed logs during execution

---

**Setup Guide Version:** 1.0
**Last Updated:** 2025-12-30
**Compatible With:** Windows 7+, Python 3.8+
