# Quick Installation Guide

## TL;DR - Just Want to Install?

### Windows Users

**Pick ONE option below:**

### Option 1: Batch File (Recommended - Easiest)

```bash
SETUP.bat
```

1. Extract bot folder
2. Double-click `SETUP.bat`
3. Wait for completion
4. Press Enter

**That's it!** All dependencies installed.

---

### Option 2: PowerShell Script

```powershell
.\SETUP.ps1
```

1. Right-click PowerShell, select "Run as administrator"
2. Run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
3. Type `Y` and press Enter
4. Run: `.\SETUP.ps1`
5. Wait for completion

**Done!** All dependencies installed.

---

### Option 3: Manual Install

```bash
pip install -r requirements.txt
```

Simple one-liner to install everything manually.

---

## Verify Installation

After setup, test that everything works:

```bash
python test_model_listener.py
```

Should show:
```
[OK] Configuration loaded successfully
[OK] Game components initialized
[OK] ModelRealtimeListener created successfully
[OK] Successfully connected to Supabase!
[OK] ALL TESTS PASSED - READY TO USE
```

---

## Next Steps

Once installed:

1. **Configure regions:**
   ```bash
   python main.py
   # Select option 2
   ```

2. **Test configuration:**
   ```bash
   python main.py
   # Select option 3
   ```

3. **Start trading:**
   ```bash
   python main.py
   # Select option 7
   ```

---

## Help & Troubleshooting

- **Installation issues?** → See `SETUP_GUIDE.md`
- **How to use the bot?** → See `QUICK_START_OPTION7.md`
- **Technical details?** → See `BUTTON_COLOR_VALIDATION.md`

---

## What Gets Installed

All required packages from `requirements.txt`:
- opencv-python (image processing)
- Pillow (image manipulation)
- pytesseract (OCR)
- numpy (math)
- supabase (real-time database)
- scikit-learn (ML tools)
- pandas (data processing)
- joblib (serialization)
- pyautogui (automation)

---

## Estimated Time

- **Windows setup script:** 5-10 minutes
- **Manual installation:** 10-15 minutes

(Depends on internet speed)

---

## Requirements

- Windows 7 or higher
- Python 3.8+ (installed with add to PATH)
- Internet connection
- 500MB+ free disk space

---

## Still Having Issues?

1. Make sure Python is installed: `python --version`
2. Make sure pip works: `pip --version`
3. Try upgrading pip: `python -m pip install --upgrade pip`
4. Run with: `pip install --no-cache-dir -r requirements.txt`

See `SETUP_GUIDE.md` for detailed troubleshooting.

---

**Ready to go?** Run `SETUP.bat` and wait 5-10 minutes!
