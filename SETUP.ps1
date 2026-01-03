# ============================================================================
# Aviator Bot - PowerShell Setup Script for Windows
# ============================================================================
# Run this script to install all dependencies on a fresh Windows system
#
# To run this script:
#   1. Open PowerShell as Administrator
#   2. Run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#   3. Run: .\SETUP.ps1
# ============================================================================

Write-Host "`n" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host "AVIATOR BOT - COMPLETE SETUP" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host "`n"

# Color helper function
function Write-Status {
    param([string]$Message, [string]$Status)

    if ($Status -eq "OK") {
        Write-Host "[OK] $Message" -ForegroundColor Green
    } elseif ($Status -eq "ERROR") {
        Write-Host "[ERROR] $Message" -ForegroundColor Red
    } elseif ($Status -eq "WARNING") {
        Write-Host "[WARNING] $Message" -ForegroundColor Yellow
    } else {
        Write-Host $Message -ForegroundColor Cyan
    }
}

# Step 1: Check Python
Write-Status "Checking Python installation..." ""
try {
    $pythonVersion = python --version 2>&1
    Write-Host $pythonVersion -ForegroundColor White
    Write-Status "Python is installed" "OK"
} catch {
    Write-Status "Python is not installed or not in PATH" "ERROR"
    Write-Host "`nPlease download and install Python from:" -ForegroundColor Yellow
    Write-Host "  https://www.python.org/downloads/" -ForegroundColor White
    Write-Host "`nIMPORTANT: Check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    Write-Host "`nAfter installing Python, run this script again." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# Step 2: Check pip
Write-Status "Checking pip installation..." ""
try {
    $pipVersion = pip --version 2>&1
    Write-Host $pipVersion -ForegroundColor White
    Write-Status "pip is installed" "OK"
} catch {
    Write-Status "pip is not installed" "ERROR"
    Write-Status "Attempting to install pip..." ""
    python -m ensurepip --upgrade
    if ($LASTEXITCODE -ne 0) {
        Write-Status "Failed to install pip" "ERROR"
        Read-Host "Press Enter to exit"
        exit 1
    }
}
Write-Host ""

# Step 3: Upgrade pip
Write-Status "Upgrading pip to latest version..." ""
python -m pip install --upgrade pip --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Status "pip is up to date" "OK"
} else {
    Write-Status "pip upgrade failed (continuing anyway)" "WARNING"
}
Write-Host ""

# Step 4: Install requirements
Write-Status "Installing Python packages..." ""
Write-Host "`nRequired packages:" -ForegroundColor Cyan
Write-Host "  - opencv-python (computer vision)" -ForegroundColor White
Write-Host "  - Pillow (image processing)" -ForegroundColor White
Write-Host "  - pytesseract (OCR for number recognition)" -ForegroundColor White
Write-Host "  - numpy (numerical computing)" -ForegroundColor White
Write-Host "  - supabase (database and real-time subscriptions)" -ForegroundColor White
Write-Host "  - scikit-learn (machine learning utilities)" -ForegroundColor White
Write-Host "  - pandas (data processing)" -ForegroundColor White
Write-Host "  - joblib (data persistence)" -ForegroundColor White
Write-Host "  - pyautogui (mouse/keyboard automation)" -ForegroundColor White
Write-Host ""

pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Status "Failed to install Python packages" "ERROR"
    Write-Host "`nTroubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Check internet connection" -ForegroundColor White
    Write-Host "  2. Run PowerShell as Administrator" -ForegroundColor White
    Write-Host "  3. Check if firewall is blocking pip" -ForegroundColor White
    Write-Host "  4. Try: pip install --upgrade --force-reinstall -r requirements.txt" -ForegroundColor White
    Read-Host "`nPress Enter to exit"
    exit 1
}

Write-Status "All Python packages installed successfully" "OK"
Write-Host ""

# Step 5: Check Tesseract (optional)
Write-Status "Checking Tesseract OCR..." ""
try {
    $tesseractVersion = tesseract --version 2>&1 | Select-Object -First 1
    Write-Host $tesseractVersion -ForegroundColor White
    Write-Status "Tesseract is installed" "OK"
} catch {
    Write-Status "Tesseract OCR is not installed" "WARNING"
    Write-Host "`nTesseract is optional but recommended for better number recognition" -ForegroundColor Yellow
    Write-Host "`nTo install Tesseract:" -ForegroundColor Yellow
    Write-Host "  1. Download: https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor White
    Write-Host "  2. Install to: C:\Program Files\Tesseract-OCR" -ForegroundColor White
    Write-Host "  3. Add to PATH if not done automatically" -ForegroundColor White
    Write-Host "`nYou can skip this for now and install later if needed." -ForegroundColor Yellow
}
Write-Host ""

# Setup complete
Write-Host "`n" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host "SETUP COMPLETE!" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host "`n"

Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Configure regions (run: python main.py -> Option 2)" -ForegroundColor White
Write-Host "  2. Test configuration (run: python main.py -> Option 3)" -ForegroundColor White
Write-Host "  3. Start trading (run: python main.py -> Option 7)" -ForegroundColor White
Write-Host ""

Write-Host "Documentation:" -ForegroundColor Cyan
Write-Host "  - QUICK_START_OPTION7.md - How to use the listener" -ForegroundColor White
Write-Host "  - BUTTON_COLOR_VALIDATION.md - Button validation details" -ForegroundColor White
Write-Host "  - PAYLOAD_EXTRACTION_FIXED.md - Technical details" -ForegroundColor White
Write-Host ""

Write-Host "============================================================================" -ForegroundColor Green
Write-Host "`n"

Read-Host "Press Enter to exit"
