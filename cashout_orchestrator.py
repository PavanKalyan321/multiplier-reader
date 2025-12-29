"""
Cashout Orchestrator - Cashout Execution & Color Tracking

Handles:
1. Color-based button state detection
2. Automatic clicking when appropriate
3. Color transition tracking for 4 seconds
4. Outcome interpretation
5. Result determination
"""

import time
import pyautogui
import numpy as np
from datetime import datetime
from typing import Dict, Tuple, Optional, List, Any
from statistics import median


class ColorMatcher:
    """Matches observed colors to target states"""

    # RGB target values for button states
    COLOR_TARGETS = {
        'GREEN': (85, 170, 38),      # Cashout available
        'BLUE': (45, 107, 253),      # Game in progress
        'ORANGE': (242, 96, 44)      # Game ended
    }

    def __init__(self, rgb_tolerance: float = 65, hue_tolerance_deg: float = 15):
        """
        Initialize color matcher

        Args:
            rgb_tolerance: RGB Euclidean distance tolerance
            hue_tolerance_deg: HSV hue tolerance in degrees
        """
        self.rgb_tol = rgb_tolerance
        self.hue_tol_deg = hue_tolerance_deg

    def rgb_distance(self, color1: Tuple[int, int, int],
                    color2: Tuple[int, int, int]) -> float:
        """
        Calculate Euclidean distance in RGB space

        Args:
            color1: RGB tuple
            color2: RGB tuple

        Returns:
            float distance
        """
        r1, g1, b1 = color1[0], color1[1], color1[2]
        r2, g2, b2 = color2[0], color2[1], color2[2]

        distance = np.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)
        return distance

    def rgb_to_hsv(self, rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
        """
        Convert RGB to HSV

        Args:
            rgb: RGB tuple (0-255)

        Returns:
            Tuple of (hue_deg: 0-360, saturation: 0-100, value: 0-100)
        """
        r, g, b = rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0

        max_c = max(r, g, b)
        min_c = min(r, g, b)
        delta = max_c - min_c

        # Hue
        if delta == 0:
            hue = 0
        elif max_c == r:
            hue = 60 * (((g - b) / delta) % 6)
        elif max_c == g:
            hue = 60 * ((b - r) / delta + 2)
        else:
            hue = 60 * ((r - g) / delta + 4)

        # Saturation
        saturation = 0 if max_c == 0 else (delta / max_c) * 100

        # Value
        value = max_c * 100

        return hue, saturation, value

    def match_color(self, observed_rgb: Tuple[int, int, int]) -> Tuple[str, float, float]:
        """
        Match observed color to target colors

        Uses RGB distance as primary method, HSV hue as fallback

        Args:
            observed_rgb: Observed RGB color

        Returns:
            Tuple of (color_name, distance, confidence)
        """
        best_match = 'UNKNOWN'
        best_distance = float('inf')
        best_confidence = 0.0

        obs_hue, obs_sat, obs_val = self.rgb_to_hsv(observed_rgb)

        for target_name, target_rgb in self.COLOR_TARGETS.items():
            target_hue, target_sat, target_val = self.rgb_to_hsv(target_rgb)

            # Calculate RGB distance
            rgb_dist = self.rgb_distance(observed_rgb, target_rgb)

            # Calculate hue difference
            hue_diff = abs(obs_hue - target_hue)
            if hue_diff > 180:
                hue_diff = 360 - hue_diff

            # Match by RGB distance primarily
            if rgb_dist < best_distance:
                best_match = target_name
                best_distance = rgb_dist
                best_confidence = 1.0 - (rgb_dist / 255.0)

            # Match by hue if value is low (dark colors)
            if obs_val < 50 and hue_diff < self.hue_tol_deg:
                if hue_diff < self.hue_tol_deg:
                    # Hue match even better
                    hue_confidence = 1.0 - (hue_diff / self.hue_tol_deg)
                    if hue_confidence > best_confidence:
                        best_match = target_name
                        best_confidence = hue_confidence

        # Confidence: inverse of distance
        if best_distance <= self.rgb_tol:
            confidence_score = 1.0
        else:
            confidence_score = max(0.0, 1.0 - (best_distance / 255.0))

        return best_match, best_distance, confidence_score

    def sample_pixels(self, coords: Tuple[float, float],
                     sample_radius: int = 3) -> Optional[Tuple[int, int, int]]:
        """
        Get median color from pixel region (7x7 area)

        Args:
            coords: (x, y) center coordinates
            sample_radius: Radius around center (default 3 = 7x7 area)

        Returns:
            RGB median tuple or None if failed
        """
        try:
            x, y = int(coords[0]), int(coords[1])
            pixels = []

            screenshot = pyautogui.screenshot()

            # Sample 7x7 pixel area
            for dx in range(-sample_radius, sample_radius + 1):
                for dy in range(-sample_radius, sample_radius + 1):
                    sx, sy = x + dx, y + dy

                    if 0 <= sx < screenshot.width and 0 <= sy < screenshot.height:
                        pixel = screenshot.getpixel((sx, sy))
                        if len(pixel) >= 3:
                            pixels.append(pixel[:3])

            if not pixels:
                return None

            # Calculate median color
            r_values = [p[0] for p in pixels]
            g_values = [p[1] for p in pixels]
            b_values = [p[2] for p in pixels]

            median_color = (int(median(r_values)),
                           int(median(g_values)),
                           int(median(b_values)))

            return median_color

        except Exception as e:
            print(f"Error sampling pixels: {e}")
            return None


class CashoutExecutor:
    """Executes cashout with color tracking"""

    def __init__(self, cashout_coords: Tuple[float, float],
                 screen_capture: Optional[Any] = None):
        """
        Initialize cashout executor

        Args:
            cashout_coords: (x, y) coordinates of cashout button
            screen_capture: ScreenCapture instance (optional)
        """
        self.cashout_coords = cashout_coords
        self.screen_capture = screen_capture
        self.color_matcher = ColorMatcher()

    def click_if_green(self) -> Tuple[bool, str]:
        """
        Click cashout button only if it's currently green

        Returns:
            Tuple of (clicked: bool, initial_color: str)
        """
        try:
            initial_color_rgb = self.color_matcher.sample_pixels(self.cashout_coords)

            if initial_color_rgb is None:
                return False, 'unknown'

            # Match color
            color_name, distance, confidence = self.color_matcher.match_color(initial_color_rgb)

            # Only click if green (and reasonably confident)
            if color_name == 'GREEN' and distance <= self.color_matcher.rgb_tol:
                pyautogui.click(int(self.cashout_coords[0]),
                              int(self.cashout_coords[1]))
                return True, color_name

            return False, color_name

        except Exception as e:
            print(f"Error clicking if green: {e}")
            return False, 'error'

    def track_color_transitions(self, duration: float = 4.0,
                               interval: float = 0.2,
                               sample_radius: int = 3) -> List[str]:
        """
        Monitor button color for specified duration

        Samples every `interval` seconds and tracks color transitions

        Args:
            duration: Total observation time (default 4.0 seconds)
            interval: Sample interval in seconds (default 0.2 = 5 samples/sec)
            sample_radius: Pixel sample radius (default 3 = 7x7 area)

        Returns:
            List of color names observed in sequence
        """
        color_sequence = []
        start_time = time.time()
        last_sample = 0

        while time.time() - start_time < duration:
            elapsed = time.time() - start_time

            # Sample at specified interval
            if elapsed - last_sample >= interval:
                # Get pixel color
                pixel_color = self.color_matcher.sample_pixels(
                    self.cashout_coords,
                    sample_radius
                )

                if pixel_color:
                    color_name, distance, confidence = self.color_matcher.match_color(pixel_color)

                    if confidence > 0.5:  # Only record if confident match
                        color_sequence.append(color_name)
                    else:
                        color_sequence.append('UNCLEAR')

                last_sample = elapsed

            time.sleep(0.01)  # Small sleep to avoid busy loop

        return color_sequence

    def interpret_outcome(self, color_sequence: List[str]) -> str:
        """
        Determine outcome from color transition sequence

        Interpretation rules:
        - GREEN→BLUE = WIN (clicked successfully, game continued)
        - GREEN→ORANGE = WIN (clicked, game ended)
        - All GREEN = WIN (held cashout button)
        - BLUE→ORANGE = CRASH (game ended, we didn't cashout)
        - All BLUE = CRASH (game running, no state change)
        - All ORANGE = CRASH (game ended before cashout)
        - Mixed unclear = UNCERTAIN

        Args:
            color_sequence: List of observed colors

        Returns:
            Interpretation string
        """
        if not color_sequence:
            return 'NO_DATA'

        # Create string representation
        color_str = '→'.join([c for c in color_sequence if c])

        # Check for sequences
        has_green = 'GREEN' in color_sequence
        has_blue = 'BLUE' in color_sequence
        has_orange = 'ORANGE' in color_sequence
        has_unclear = 'UNCLEAR' in color_sequence

        # Win cases
        if has_green and has_blue and not has_orange:
            return 'CASHOUT_SUCCESS'  # GREEN→BLUE = clicked, game continued

        if has_green and has_orange and not has_blue:
            return 'ROUND_ENDED_BET_AGAIN'  # GREEN→ORANGE = game ended at our target

        if all(c == 'GREEN' for c in color_sequence if c):
            return 'CASHOUT_HELD_GREEN'  # Button stayed green

        # Loss cases
        if has_blue and has_orange and not has_green:
            return 'ROUND_ENDED_BET_AVAILABLE'  # BLUE→ORANGE = crash before cashout

        if all(c == 'BLUE' for c in color_sequence if c):
            return 'ROUND_ENDED_NO_BET'  # Game running entire time = crash

        if all(c == 'ORANGE' for c in color_sequence if c):
            return 'WAITING_NEXT_ROUND'  # Game ended = crash

        # Unclear cases
        if has_unclear and not has_blue and not has_orange:
            return 'BUTTON_UNCLEAR'

        return 'UNCERTAIN'


class CashoutOrchestrator:
    """Orchestrates cashout execution and outcome determination"""

    def __init__(self, executor: CashoutExecutor):
        """Initialize orchestrator"""
        self.executor = executor

    def execute_cashout(self, final_multiplier: float) -> Dict:
        """
        Execute complete cashout workflow

        Includes:
        1. Check initial button color
        2. Click if green
        3. Track color transitions for 4 seconds
        4. Interpret outcome

        Args:
            final_multiplier: Final multiplier value achieved

        Returns:
            Dict with cashout results
        """
        print(f"Executing cashout at {final_multiplier:.2f}x...")

        # Phase 1: Check initial button state and click if appropriate
        clicked, initial_color = self.executor.click_if_green()

        if clicked:
            print(f"Cashout button clicked (was {initial_color})")
        else:
            print(f"Cashout button not clicked (was {initial_color})")

        time.sleep(0.5)  # Brief pause after click

        # Phase 2: Track color transitions for 4 seconds
        print("Tracking button state for 4 seconds...")
        color_sequence = self.executor.track_color_transitions(
            duration=4.0,
            interval=0.2,
            sample_radius=3
        )

        # Phase 3: Interpret outcome
        interpretation = self.executor.interpret_outcome(color_sequence)

        # Determine success
        success = interpretation in [
            'CASHOUT_SUCCESS',
            'ROUND_ENDED_BET_AGAIN',
            'CASHOUT_HELD_GREEN'
        ]

        cashout_result = {
            'success': success,
            'final_multiplier': final_multiplier,
            'clicked': clicked,
            'initial_button_color': initial_color,
            'color_sequence': color_sequence,
            'color_sequence_str': '→'.join([c for c in color_sequence if c]),
            'interpretation': interpretation,
            'outcome': 'WIN' if success else 'LOSS',
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        return cashout_result
