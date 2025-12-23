# Screen capture and image processing module
import cv2
import numpy as np
from PIL import ImageGrab
from config import RegionConfig
import time

class ScreenCapture:
    """Handle screen capture and image processing"""

    def __init__(self, region: RegionConfig = None):
        self.region = region
        self.last_frame = None

    def set_region(self, region: RegionConfig):
        """Set the region for capture"""
        self.region = region

    def capture_full_screen(self):
        """Capture the full screen"""
        screen = ImageGrab.grab()
        return cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)

    def capture_region(self):
        """Capture only the region of interest"""
        if self.region is None:
            raise ValueError("Region not set. Use set_region() first.")

        frame = self.capture_full_screen()
        x1, y1, x2, y2 = self.region.x1, self.region.y1, self.region.x2, self.region.y2
        return frame[y1:y2, x1:x2]

    def preprocess_image(self, image):
        """Preprocess image for OCR"""
        # Convert to grayscale (handle both color and grayscale images)
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Threshold to binary
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Denoise
        denoised = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))

        return denoised

    def detect_changes(self, new_frame):
        """Detect significant changes between frames"""
        if self.last_frame is None:
            self.last_frame = new_frame
            return True, 0

        # Calculate frame difference
        diff = cv2.absdiff(self.last_frame, new_frame)
        change_percentage = (np.count_nonzero(diff) / diff.size) * 100

        self.last_frame = new_frame

        # Consider it a significant change if >5% of pixels changed
        return change_percentage > 5, change_percentage

    def save_debug_frame(self, image, filename):
        """Save frame for debugging"""
        cv2.imwrite(filename, image)
        print(f"Debug frame saved: {filename}")
