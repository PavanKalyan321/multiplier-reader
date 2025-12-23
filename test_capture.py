# Test script to diagnose capture and OCR issues
import cv2
from config import load_config
from screen_capture import ScreenCapture
from multiplier_reader import MultiplierReader
import os

print("=" * 80)
print("MULTIPLIER READER - DIAGNOSTIC TEST")
print("=" * 80)

# Test 1: Load configuration
print("\n[1] Loading configuration...")
config = load_config()
if config:
    print(f"    Region loaded: ({config.x1}, {config.y1}) to ({config.x2}, {config.y2})")
else:
    print("    ERROR: No configuration found!")
    print("    Please run: python gui_selector.py")
    exit(1)

# Test 2: Capture screen
print("\n[2] Capturing screen...")
sc = ScreenCapture(config)
frame = sc.capture_full_screen()
print(f"    Full screen captured: {frame.shape}")

# Test 3: Capture region
print("\n[3] Capturing region...")
region_frame = sc.capture_region()
print(f"    Region captured: {region_frame.shape}")

# Save raw region
cv2.imwrite("test_region_raw.png", region_frame)
print(f"    Saved: test_region_raw.png")

# Test 4: Preprocess image
print("\n[4] Preprocessing image...")
processed = sc.preprocess_image(region_frame)
print(f"    Processed image: {processed.shape}")

cv2.imwrite("test_region_processed.png", processed)
print(f"    Saved: test_region_processed.png")

# Test 5: OCR
print("\n[5] Testing OCR...")
reader = MultiplierReader(sc)
multiplier = reader.extract_multiplier(region_frame)
print(f"    Raw capture OCR result: {multiplier}")

# Test with preprocessed image
processed_mult = reader.extract_multiplier(processed)
print(f"    Processed image OCR result: {processed_mult}")

# Test 6: Multiplier with status
print("\n[6] Testing full multiplier reader...")
result = reader.get_multiplier_with_status()
print(f"    Result: {result}")

# Test 7: Manual Tesseract test
print("\n[7] Testing Tesseract directly...")
try:
    import pytesseract
    text = pytesseract.image_to_string(region_frame)
    print(f"    Raw text from region:\n    {repr(text)}")
except Exception as e:
    print(f"    ERROR: {e}")

print("\n" + "=" * 80)
print("DIAGNOSTIC TEST COMPLETE")
print("=" * 80)
print("\nIf you see multiplier values, the setup is working!")
print("If not, check:")
print("  1. Region covers the multiplier text")
print("  2. Game is open and running")
print("  3. Tesseract is installed correctly")
print("=" * 80)
