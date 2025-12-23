"""Setup script for Multiplier Reader"""
import subprocess
import sys
import os
import platform

def install_dependencies():
    """Install Python dependencies"""
    print("Installing Python dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("✓ Python dependencies installed")

def install_tesseract():
    """Install Tesseract OCR"""
    system = platform.system()

    if system == "Windows":
        print("\nTesseract installation for Windows:")
        print("1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki")
        print("2. Run the installer (default location: C:\\Program Files\\Tesseract-OCR)")
        print("3. Add Tesseract to your environment or update the path in screen_capture.py")
        print("\nAfter installation, update multiplier_reader.py with your Tesseract path:")
        print('   pytesseract.pytesseract.pytesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"')

    elif system == "Darwin":  # macOS
        print("\nTesseract installation for macOS:")
        print("Run: brew install tesseract")

    elif system == "Linux":
        print("\nTesseract installation for Linux:")
        print("Run: sudo apt-get install tesseract-ocr")

def main():
    """Main setup function"""
    print("=" * 60)
    print("MULTIPLIER READER - SETUP")
    print("=" * 60)

    # Install Python dependencies
    try:
        install_dependencies()
    except Exception as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False

    # Show Tesseract installation instructions
    install_tesseract()

    print("\n" + "=" * 60)
    print("SETUP COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Install Tesseract OCR (see instructions above)")
    print("2. Run the region selector to configure: python gui_selector.py")
    print("3. Start monitoring: python main.py")
    print("\nFor help: python main.py --help")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
