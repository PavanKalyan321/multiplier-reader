# Balance detection using OCR
import pytesseract
import cv2
import re
import os
from screen_capture import ScreenCapture
from config import RegionConfig
from datetime import datetime

# Configure Tesseract path if it exists in common Windows location
tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(tesseract_path):
    pytesseract.pytesseract.pytesseract_cmd = tesseract_path

class BalanceReader:
    """Read balance values from game screen"""

    def __init__(self, screen_capture: ScreenCapture):
        self.screen_capture = screen_capture
        self.last_balance = None

    def extract_balance(self, image):
        """Extract balance value from image using OCR

        Handles formats like:
        - 1234 (3+ digits)
        - 1.5k (with k suffix)
        - 500.25 (with decimals)
        """
        # Preprocess the image
        processed = self.screen_capture.preprocess_image(image)

        # Use pytesseract to extract text
        text = pytesseract.image_to_string(processed, config='--psm 6')

        timestamp = datetime.now().strftime("%H:%M:%S")

        # Clean the text - remove spaces and common OCR errors
        text = text.replace(' ', '').replace(',', '').replace('$', '')

        # Look for patterns with 'k' suffix (e.g., "1.5k", "2k", "10k")
        k_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*k', re.IGNORECASE)
        k_matches = k_pattern.findall(text)

        if k_matches:
            try:
                # Take first match with 'k' suffix
                value = float(k_matches[0])
                balance = value * 1000  # Convert k to actual value
                return balance
            except ValueError:
                pass

        # Look for regular numbers (3+ digits for balance, not smaller values)
        # Pattern: look for numbers with 3+ digits or decimal values > 10
        numbers = re.findall(r'\d{3,}(?:\.\d+)?|\d{1,2}\.\d+', text)

        if numbers:
            try:
                # Filter for reasonable balance values (> 10)
                for num_str in numbers:
                    num = float(num_str)
                    if num > 10:  # Balance should be at least > 10
                        return num
            except ValueError:
                pass

        return None

    def read_balance(self):
        """Capture region and read balance"""
        try:
            frame = self.screen_capture.capture_region()
            balance = self.extract_balance(frame)
            self.last_balance = balance
            return balance
        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] WARNING: Error reading balance: {e}")
            return None

    def get_balance_with_status(self):
        """Read balance and return with status info"""
        balance = self.read_balance()

        if balance is None:
            return {
                'balance': None,
                'status': 'ERROR',
                'message': 'Could not read balance'
            }

        # Detect status based on balance value
        status = self._detect_status(balance)

        return {
            'balance': balance,
            'status': status,
            'message': self._get_status_message(status, balance)
        }

    def _detect_status(self, balance):
        """Detect balance status"""
        if balance <= 0:
            return 'ZERO'
        elif balance < 100:
            return 'VERY_LOW'
        elif balance < 500:
            return 'LOW'
        elif balance < 2000:
            return 'NORMAL'
        else:
            return 'HIGH'

    def _get_status_message(self, status, balance=None):
        """Get human-readable status message"""
        messages = {
            'ZERO': 'No balance - game over',
            'VERY_LOW': 'Very low balance',
            'LOW': 'Low balance',
            'NORMAL': 'Normal balance',
            'HIGH': 'High balance',
            'ERROR': 'Could not read balance'
        }
        message = messages.get(status, 'Unknown status')
        if balance is not None and status != 'ERROR':
            message += f' ({balance:.2f})'
        return message
