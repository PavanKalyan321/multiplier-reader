# Multiplier detection using OCR
import pytesseract
import cv2
import re
import os
import sys
import subprocess
from screen_capture import ScreenCapture
from config import RegionConfig

# Configure Tesseract path for Windows
# Set the path directly - pytesseract will handle it
if sys.platform == 'win32':
    # Windows paths
    possible_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]

    for path in possible_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.pytesseract_cmd = path
            print(f"[DEBUG] Tesseract configured at: {path}")

            # Monkey-patch pytesseract's run_tesseract to use shell=True on Windows
            # This fixes subprocess issues with paths containing spaces
            _original_run_and_get_output = pytesseract.pytesseract.run_and_get_output

            def patched_run_and_get_output(cmd, *args, **kwargs):
                """Patched version that uses shell=True on Windows"""
                # Modify the subprocess call to use shell=True
                import subprocess as sp
                original_run = sp.run

                def run_with_shell(*run_args, **run_kwargs):
                    run_kwargs['shell'] = True
                    return original_run(*run_args, **run_kwargs)

                sp.run = run_with_shell
                try:
                    result = _original_run_and_get_output(cmd, *args, **kwargs)
                finally:
                    sp.run = original_run
                return result

            pytesseract.pytesseract.run_and_get_output = patched_run_and_get_output
            break
else:
    # Unix-like systems - should be in PATH
    pytesseract.pytesseract.pytesseract_cmd = 'tesseract'

class MultiplierReader:
    """Read multiplier values from game screen"""

    def __init__(self, screen_capture: ScreenCapture):
        self.screen_capture = screen_capture
        self.last_multiplier = None

    def extract_multiplier(self, image):
        """Extract multiplier value from image using OCR"""
        # Preprocess the image
        processed = self.screen_capture.preprocess_image(image)

        # Use custom OCR function for Windows compatibility
        if sys.platform == 'win32':
            text = self._run_tesseract_windows(processed)
        else:
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

    def _run_tesseract_windows(self, image):
        """Run Tesseract directly on Windows using subprocess with shell=True"""
        import tempfile
        import subprocess

        # Save image to temp file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name
            cv2.imwrite(tmp_path, image)

        try:
            # Run tesseract with shell=True to handle paths with spaces
            tesseract_cmd = pytesseract.pytesseract.pytesseract_cmd
            result = subprocess.run(
                [tesseract_cmd, tmp_path, 'stdout', '--psm', '6'],
                capture_output=True,
                text=True,
                shell=True
            )

            if result.returncode == 0:
                return result.stdout
            else:
                raise Exception(f"Tesseract failed: {result.stderr}")
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except:
                pass

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
