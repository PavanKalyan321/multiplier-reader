# Multiplier detection using OCR
import pytesseract
import cv2
import re
import os
from screen_capture import ScreenCapture
from config import RegionConfig

# Configure Tesseract path if it exists in common Windows location
tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(tesseract_path):
    pytesseract.pytesseract.pytesseract_cmd = tesseract_path

class MultiplierReader:
    """Read multiplier values from game screen"""

    def __init__(self, screen_capture: ScreenCapture):
        self.screen_capture = screen_capture
        self.last_multiplier = None

    def extract_multiplier(self, image):
        """Extract multiplier value from image using OCR"""
        # Preprocess the image
        processed = self.screen_capture.preprocess_image(image)

        # Use pytesseract to extract text
        text = pytesseract.image_to_string(processed, config='--psm 6')

        # Extract numbers from text
        numbers = re.findall(r'\d+\.?\d*', text)

        if numbers:
            try:
                multiplier = float(numbers[0])
                return multiplier
            except ValueError:
                return None

        return None

    def read_multiplier(self):
        """Capture region and read multiplier"""
        try:
            frame = self.screen_capture.capture_region()
            multiplier = self.extract_multiplier(frame)
            self.last_multiplier = multiplier
            return multiplier
        except Exception as e:
            print(f"Error reading multiplier: {e}")
            return None

    def get_multiplier_with_status(self):
        """Read multiplier and return with status info"""
        multiplier = self.read_multiplier()

        if multiplier is None:
            return {
                'multiplier': None,
                'status': 'ERROR',
                'message': 'Could not read multiplier'
            }

        # Detect status based on multiplier value
        status = self._detect_status(multiplier)

        return {
            'multiplier': multiplier,
            'status': status,
            'message': self._get_status_message(status)
        }

    def _detect_status(self, multiplier):
        """Detect game status based on multiplier value"""
        if multiplier == 0 or multiplier < 1:
            return 'CRASHED'
        elif multiplier == 1:
            return 'STARTING'
        elif multiplier > 1 and multiplier < 10:
            return 'RUNNING'
        elif multiplier >= 10:
            return 'HIGH'
        return 'UNKNOWN'

    def _get_status_message(self, status):
        """Get human-readable status message"""
        messages = {
            'CRASHED': 'Game crashed/burst - multiplier 0',
            'STARTING': 'Game starting - multiplier 1x',
            'RUNNING': 'Game running - multiplier increasing',
            'HIGH': 'High multiplier reached',
            'UNKNOWN': 'Unknown status'
        }
        return messages.get(status, 'Unknown status')
