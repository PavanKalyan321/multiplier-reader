@echo off
echo Adding Tesseract to Windows PATH...
setx PATH "%PATH%;C:\Program Files\Tesseract-OCR"
echo.
echo Tesseract has been added to your system PATH.
echo Please close this terminal and open a new one for changes to take effect.
echo Then run: python.exe main.py
pause
