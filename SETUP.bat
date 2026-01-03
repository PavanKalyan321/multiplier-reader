@echo off
REM ============================================================================
REM Aviator Bot - Complete Setup Script for Windows
REM ============================================================================
REM This script installs all dependencies and sets up the project
REM Run this on a fresh Windows system to get everything working
REM ============================================================================

setlocal enabledelayedexpansion
color 0A

echo.
echo ============================================================================
echo AVIATOR BOT - COMPLETE SETUP
echo ============================================================================
echo.

REM Check if Python is installed
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please download and install Python from:
    echo   https://www.python.org/downloads/
    echo.
    echo IMPORTANT: During installation, check "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

python --version
echo [OK] Python is installed
echo.

REM Check if pip is installed
echo [2/5] Checking pip installation...
pip --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: pip is not installed
    echo.
    echo Trying to upgrade pip...
    python -m ensurepip --upgrade
    if errorlevel 1 (
        echo ERROR: Failed to install pip
        pause
        exit /b 1
    )
)

pip --version
echo [OK] pip is installed
echo.

REM Upgrade pip to latest version
echo [3/5] Upgrading pip to latest version...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo WARNING: pip upgrade failed, continuing anyway...
)
echo [OK] pip is up to date
echo.

REM Install requirements
echo [4/5] Installing Python packages...
echo.
echo Required packages:
echo   - opencv-python (computer vision)
echo   - Pillow (image processing)
echo   - pytesseract (OCR for number recognition)
echo   - numpy (numerical computing)
echo   - supabase (database and real-time subscriptions)
echo   - scikit-learn (machine learning utilities)
echo   - pandas (data processing)
echo   - joblib (data persistence)
echo   - pyautogui (mouse/keyboard automation)
echo.

pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install Python packages
    echo.
    echo Troubleshooting:
    echo   1. Make sure you have internet connection
    echo   2. Try running Command Prompt as Administrator
    echo   3. Check if your firewall is blocking pip
    echo.
    pause
    exit /b 1
)

echo [OK] All Python packages installed successfully
echo.

REM Check if Tesseract is installed (optional but recommended)
echo [5/5] Checking Tesseract OCR...
tesseract --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNING: Tesseract OCR is not installed
    echo.
    echo Tesseract is optional but recommended for better number recognition
    echo.
    echo To install Tesseract:
    echo   1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
    echo   2. Install to default location: C:\Program Files\Tesseract-OCR
    echo   3. Add to PATH if not done automatically
    echo.
    echo You can skip this for now and install later if needed.
    echo.
) else (
    tesseract --version
    echo [OK] Tesseract is installed
    echo.
)

echo.
echo ============================================================================
echo SETUP COMPLETE!
echo ============================================================================
echo.
echo Next steps:
echo   1. Configure regions (run: python main.py -> Option 2)
echo   2. Test configuration (run: python main.py -> Option 3)
echo   3. Start trading (run: python main.py -> Option 7)
echo.
echo Documentation:
echo   - QUICK_START_OPTION7.md - How to use the listener
echo   - BUTTON_COLOR_VALIDATION.md - Button validation details
echo   - PAYLOAD_EXTRACTION_FIXED.md - Technical details
echo.
echo ============================================================================
echo.

pause
