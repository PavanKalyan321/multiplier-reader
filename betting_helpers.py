"""Helper functions for betting operations and verification."""

import math
import time
import numpy as np
import cv2
import pyautogui
import colorsys
import re
import pytesseract
import os
from statistics import median
from datetime import datetime

# Configure Tesseract path if it exists in common Windows location
tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(tesseract_path):
    pytesseract.pytesseract.pytesseract_cmd = tesseract_path


# ============================================================================
# STAKE READER & UPDATE FUNCTIONS
# ============================================================================

class StakeReader:
    """Read and track stake values from game screen"""

    def __init__(self, stake_region=None):
        """
        Initialize StakeReader.

        Args:
            stake_region: Dict with 'x1', 'y1', 'x2', 'y2' for stake display region
        """
        self.stake_region = stake_region
        self.last_stake = None
        self.stake_history = []

    def extract_stake(self, image):
        """
        Extract stake value from image using OCR.

        Args:
            image: Image to extract stake from

        Returns:
            float: Stake value or None if extraction fails
        """
        try:
            # Preprocess the image
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            processed = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]

            # Use pytesseract to extract text
            text = pytesseract.image_to_string(processed, config='--psm 6')

            # Clean the text
            text = text.replace(' ', '').replace(',', '').replace('$', '')

            # Look for patterns with 'k' suffix
            k_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*k', re.IGNORECASE)
            k_matches = k_pattern.findall(text)

            if k_matches:
                try:
                    value = float(k_matches[0])
                    stake = value * 1000
                    return stake
                except ValueError:
                    pass

            # Look for regular numbers
            numbers = re.findall(r'\d{1,}(?:\.\d+)?', text)

            if numbers:
                try:
                    for num_str in numbers:
                        num = float(num_str)
                        if num >= 1:
                            return num
                except ValueError:
                    pass

            return None

        except Exception as e:
            print(f"ERROR: Failed to extract stake: {e}")
            return None

    def read_stake(self, screen_capture=None):
        """
        Capture stake region and read stake value.

        Args:
            screen_capture: ScreenCapture instance (optional)

        Returns:
            float: Current stake value or None
        """
        try:
            if self.stake_region and screen_capture:
                # Capture from region
                frame = screen_capture.capture_region()
            else:
                # Fallback: capture full screen (not recommended)
                frame = np.array(pyautogui.screenshot())

            stake = self.extract_stake(frame)
            self.last_stake = stake

            if stake:
                self.stake_history.append({
                    'timestamp': datetime.now(),
                    'stake': stake
                })

            return stake

        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] WARNING: Error reading stake: {e}")
            return None

    def get_stake_with_status(self, screen_capture=None):
        """
        Read stake and return with status information.

        Args:
            screen_capture: ScreenCapture instance (optional)

        Returns:
            dict: Stake info with status
        """
        stake = self.read_stake(screen_capture)

        if stake is None:
            return {
                'stake': None,
                'status': 'ERROR',
                'message': 'Could not read stake'
            }

        status = self._detect_status(stake)

        return {
            'stake': stake,
            'status': status,
            'message': self._get_status_message(status, stake)
        }

    def _detect_status(self, stake):
        """Detect stake status"""
        if stake <= 0:
            return 'INVALID'
        elif stake < 10:
            return 'VERY_LOW'
        elif stake < 100:
            return 'LOW'
        elif stake < 500:
            return 'NORMAL'
        else:
            return 'HIGH'

    def _get_status_message(self, status, stake=None):
        """Get human-readable status message"""
        messages = {
            'INVALID': 'Invalid stake value',
            'VERY_LOW': 'Very low stake',
            'LOW': 'Low stake',
            'NORMAL': 'Normal stake',
            'HIGH': 'High stake',
            'ERROR': 'Could not read stake'
        }
        message = messages.get(status, 'Unknown status')
        if stake is not None and status != 'ERROR':
            message += f' ({stake:.2f})'
        return message


# ============================================================================
# VERIFICATION FUNCTIONS
# ============================================================================

def verify_bet_placed(bet_button_coords, detector=None):
    """
    Verify bet was actually placed by checking button state.

    Args:
        bet_button_coords: Tuple (x, y) of bet button coordinates
        detector: GameStateDetector instance (optional, for OCR)

    Returns:
        Tuple (bool, str): (is_placed, button_text/status)
    """
    try:
        x, y = bet_button_coords
        region = (x - 60, y - 25, 120, 50)

        screenshot = pyautogui.screenshot(region=region)
        img = np.array(screenshot)
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        # Check button color
        avg_color = np.mean(img, axis=(0, 1))
        is_green = avg_color[1] > 100 and avg_color[0] < avg_color[1]

        # Try OCR if detector available
        if detector and hasattr(detector, 'pytesseract'):
            try:
                text = detector.pytesseract.image_to_string(gray).strip().upper()

                if 'PLACE' in text or 'BET' in text:
                    return False, text

                if 'CANCEL' in text or 'CASH' in text:
                    return True, text
            except:
                pass

        return not is_green, "COLOR_CHECK"

    except Exception as e:
        return False, f"ERROR: {e}"


def verify_bet_is_active(cashout_coords, detector):
    """
    Check if bet is currently active.

    Args:
        cashout_coords: Tuple (x, y) of cashout button coordinates
        detector: GameStateDetector instance

    Returns:
        bool: True if bet is active, False otherwise
    """
    try:
        print("  🔍 Verifying active bet...")
        # Check if in awaiting state
        if detector.is_awaiting_next_flight():
            return False

        x, y = cashout_coords
        region = (x - 50, y - 20, 100, 40)
        screenshot = pyautogui.screenshot(region=region)
        img = np.array(screenshot)
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        # Try OCR
        if hasattr(detector, 'pytesseract'):
            text = detector.pytesseract.image_to_string(gray).strip().upper()
            return 'CASH' in text or 'CANCEL' in text

        return True
    except:
        return False


# ============================================================================
# STAKE MANAGEMENT FUNCTIONS
# ============================================================================

def set_stake_verified(stake_coords, amount):
    """
    Set stake amount and verify it changed.

    Args:
        stake_coords: Tuple (x, y) of stake input coordinates
        amount: Stake amount to set

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        pyautogui.click(stake_coords)
        time.sleep(0.15)
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        pyautogui.press('backspace')
        time.sleep(0.1)
        pyautogui.typewrite(str(amount), interval=0.05)
        time.sleep(0.2)
        return True
    except Exception as e:
        print(f"Error setting stake: {e}")
        return False


def increase_stake(current_stake, increase_percent, max_stake, stats):
    """
    Increase stake by percentage.

    Args:
        current_stake: Current stake amount
        increase_percent: Percentage to increase
        max_stake: Maximum allowed stake
        stats: Stats dictionary to update

    Returns:
        int: New stake amount
    """
    old_stake = current_stake
    new_stake = current_stake * (1 + increase_percent / 100)

    if new_stake > max_stake:
        new_stake = max_stake

    new_stake = int(new_stake)

    if new_stake > stats.get("max_stake_reached", 0):
        stats["max_stake_reached"] = new_stake

    if new_stake != old_stake:
        print(f"  📈 Stake: {old_stake} → {new_stake}")

    return new_stake


def reset_stake(initial_stake, stats):
    """
    Reset stake to initial value.

    Args:
        initial_stake: Initial stake amount
        stats: Stats dictionary to update

    Returns:
        int: Reset stake amount
    """
    stats["current_streak"] = 0
    print(f"  📉 Stake reset to: {initial_stake}")
    return initial_stake


def calculate_martingale_stake(current_stake, multiplier, max_stake):
    """
    Calculate next stake using Martingale strategy (double on loss).

    Args:
        current_stake: Current stake amount
        multiplier: Multiplier for next stake (typically 2.0 for doubling)
        max_stake: Maximum allowed stake

    Returns:
        int: New stake amount (capped at max_stake)
    """
    new_stake = int(current_stake * multiplier)
    return min(new_stake, max_stake)


def calculate_percentage_stake(balance, percentage):
    """
    Calculate stake as a percentage of balance.

    Args:
        balance: Current balance
        percentage: Percentage of balance to stake (e.g., 5 for 5%)

    Returns:
        int: Stake amount
    """
    return int(balance * (percentage / 100))


def calculate_fixed_increment_stake(base_stake, increment_steps, max_stake):
    """
    Calculate stake by adding fixed increments (after each loss).

    Args:
        base_stake: Initial base stake
        increment_steps: Number of loss increments to apply
        max_stake: Maximum allowed stake

    Returns:
        int: New stake amount
    """
    new_stake = base_stake + (base_stake * increment_steps)
    return min(new_stake, max_stake)


# ============================================================================
# BET PLACEMENT FUNCTIONS
# ============================================================================

def place_bet_with_verification(bet_button_coords, detector, stats, current_stake):
    """
    Place bet with verification.

    Args:
        bet_button_coords: Tuple (x, y) of bet button coordinates
        detector: GameStateDetector instance
        stats: Stats dictionary to update
        current_stake: Current stake amount

    Returns:
        Tuple (bool, str): (success, reason)
    """
    try:
        pyautogui.click(bet_button_coords)
        time.sleep(0.4)

        # Verify it placed
        for attempt in range(3):
            is_placed, button_text = verify_bet_placed(bet_button_coords, detector)

            if is_placed:
                stats["rounds_played"] = stats.get("rounds_played", 0) + 1
                stats["ml_bets_placed"] = stats.get("ml_bets_placed", 0) + 1
                stats["total_bet"] = stats.get("total_bet", 0) + current_stake
                print(f"  ✅ Bet confirmed (Stake: {current_stake})")
                return True, "SUCCESS"

            if attempt < 2:
                print(f"  ⚠️ Retry {attempt+1}/3...")
                pyautogui.click(bet_button_coords)
                time.sleep(0.3)

        print(f"  ❌ Bet verification failed")
        return False, "FAILED_VERIFICATION"

    except Exception as e:
        return False, f"ERROR: {e}"


def estimate_multiplier(elapsed_time):
    """
    Estimate multiplier based on elapsed time.

    Args:
        elapsed_time: Time elapsed in seconds

    Returns:
        float: Estimated multiplier value
    """
    multiplier = math.exp(0.15 * elapsed_time)
    return round(multiplier, 2)


# ============================================================================
# CASHOUT VERIFICATION (Advanced Color Tracking)
# ============================================================================

def cashout_verified(cashout_coords, detector,
                     duration=4.0, interval=0.2,
                     sample_radius=3, rgb_tol=65, hue_tol_deg=15, low_v_acceptance=0.5):
    """
    Live color tracker + smart cashout verification.
    Observes color changes in 0.2s intervals to deduce what happened.

    Args:
        cashout_coords: (x, y) button center
        detector: GameStateDetector instance
        duration: how long (seconds) to track colors after clicking
        interval: sampling gap between frames (seconds)
        sample_radius: sampling radius around the coord
        rgb_tol, hue_tol_deg, low_v_acceptance: color match tuning

    Returns:
        (bool, str): success flag, outcome reason
    """
    try:
        x, y = int(cashout_coords[0]), int(cashout_coords[1])

        TARGETS = {
            "GREEN": (85, 170, 38),
            "BLUE": (45, 107, 253),
            "ORANGE": (242, 96, 44)
        }

        def rgb_distance(c1, c2):
            return ((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2 + (c1[2]-c2[2])**2) ** 0.5

        def rgb_to_hsv_deg(rgb):
            r, g, b = rgb
            h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
            return h * 360.0, s, v

        def hue_diff_deg(h1, h2):
            diff = abs(h1 - h2) % 360
            return min(diff, 360 - diff)

        # --- Step 1: initial click if button is green ---
        img = pyautogui.screenshot()
        start_color = img.getpixel((x, y))
        r, g, b = start_color
        d_green = rgb_distance(start_color, TARGETS["GREEN"])

        if d_green <= rgb_tol:
            pyautogui.click(cashout_coords)
            print("🟢 Cashout clicked (button was green).")
        else:
            print("⚠️ Cashout button not green at start, skipping click.")

        # --- Step 2: observe color changes for a few seconds ---
        observed = []
        start_time = time.time()
        while time.time() - start_time < duration:
            img = pyautogui.screenshot()
            pixels = []
            for dx in range(-sample_radius, sample_radius + 1):
                for dy in range(-sample_radius, sample_radius + 1):
                    sx, sy = x + dx, y + dy
                    if 0 <= sx < img.width and 0 <= sy < img.height:
                        pixels.append(img.getpixel((sx, sy)))
            if pixels:
                r = int(median([p[0] for p in pixels]))
                g = int(median([p[1] for p in pixels]))
                b = int(median([p[2] for p in pixels]))
                color = (r, g, b)
            else:
                color = img.getpixel((x, y))

            color_h, _, color_v = rgb_to_hsv_deg(color)
            best_match, best_dist = None, float('inf')

            for name, ref in TARGETS.items():
                ref_h, _, ref_v = rgb_to_hsv_deg(ref)
                dist = rgb_distance(color, ref)
                hue_diff = hue_diff_deg(color_h, ref_h)
                if dist < best_dist or (hue_diff < hue_tol_deg and color_v < low_v_acceptance):
                    best_match, best_dist = name, dist

            observed.append(best_match)
            time.sleep(interval)

        # --- Step 3: interpret what happened based on observed sequence ---
        if not observed:
            return False, "NO_COLOR_DATA"

        joined = "→".join([c for c in observed if c])
        last = observed[-1]

        if "GREEN" in observed and "BLUE" in observed:
            return True, f"CASHOUT_SUCCESS (Green→Blue transition)"
        elif "GREEN" in observed and "ORANGE" in observed:
            return True, f"ROUND_ENDED_BET_AGAIN (Green→Orange)"
        elif "BLUE" in observed and "ORANGE" in observed:
            return False, f"ROUND_ENDED_BET_AVAILABLE (Blue→Orange)"
        elif all(c == "GREEN" for c in observed if c):
            return True, f"CASHOUT_HELD_GREEN (stable)"
        elif all(c == "BLUE" for c in observed if c):
            return False, f"ROUND_ENDED_NO_BET (Blue stable)"
        elif all(c == "ORANGE" for c in observed if c):
            return False, f"WAITING_NEXT_ROUND (Orange stable)"
        elif detector.is_awaiting_next_flight():
            return True, "DETECTED_NEXT_FLIGHT"
        else:
            return False, f"UNSURE|Sequence={joined}"

    except Exception as e:
        return False, f"ERROR: {e}"


# ============================================================================
# MULTI-POSITION SUPPORT FUNCTIONS
# ============================================================================

def set_stake_verified_pos(stake_coords, amount, position=1):
    """
    Set stake amount for a specific position.

    Args:
        stake_coords: Tuple (x, y) of stake input coordinates
        amount: Stake amount to set
        position: Position number (1 or 2) for logging

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        pyautogui.click(stake_coords)
        time.sleep(0.15)
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        pyautogui.press('backspace')
        time.sleep(0.1)
        pyautogui.typewrite(str(amount), interval=0.05)
        time.sleep(0.2)
        print(f"  💰 Position {position} stake set to: {amount}")
        return True
    except Exception as e:
        print(f"  ❌ Error setting Position {position} stake: {e}")
        return False


def place_bet_with_verification_pos(bet_button_coords, detector, stats, current_stake, position=1):
    """
    Place bet with verification for a specific position.

    Args:
        bet_button_coords: Tuple (x, y) of bet button coordinates
        detector: GameStateDetector instance
        stats: Stats dictionary to update
        current_stake: Current stake amount
        position: Position number (1 or 2)

    Returns:
        Tuple (bool, str): (success, reason)
    """
    try:
        pyautogui.click(bet_button_coords)
        time.sleep(0.4)

        # Verify it placed
        for attempt in range(3):
            is_placed, button_text = verify_bet_placed(bet_button_coords, detector)

            if is_placed:
                stats[f"position{position}_bets_placed"] = stats.get(f"position{position}_bets_placed", 0) + 1
                stats[f"position{position}_total_bet"] = stats.get(f"position{position}_total_bet", 0) + current_stake
                print(f"  ✅ Position {position} bet confirmed ({current_stake} stake)")
                return True, "SUCCESS"

            if attempt < 2:
                print(f"  ⚠️ Position {position} Retry {attempt+1}/3...")
                pyautogui.click(bet_button_coords)
                time.sleep(0.3)

        print(f"  ❌ Position {position} bet verification failed")
        return False, "FAILED_VERIFICATION"

    except Exception as e:
        return False, f"ERROR: {e}"


def cashout_verified_pos(cashout_coords, detector, position=1,
                         duration=4.0, interval=0.2,
                         sample_radius=3, rgb_tol=65, hue_tol_deg=15, low_v_acceptance=0.5):
    """
    Cashout with verification for a specific position.

    Args:
        cashout_coords: (x, y) button center
        detector: GameStateDetector instance
        position: Position number (1 or 2)
        duration: how long (seconds) to track colors after clicking
        interval: sampling gap between frames (seconds)
        sample_radius: sampling radius around the coord
        rgb_tol, hue_tol_deg, low_v_acceptance: color match tuning

    Returns:
        (bool, str): success flag, outcome reason
    """
    try:
        x, y = int(cashout_coords[0]), int(cashout_coords[1])

        TARGETS = {
            "GREEN": (85, 170, 38),
            "BLUE": (45, 107, 253),
            "ORANGE": (242, 96, 44)
        }

        def rgb_distance(c1, c2):
            return ((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2 + (c1[2]-c2[2])**2) ** 0.5

        def rgb_to_hsv_deg(rgb):
            r, g, b = rgb
            h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
            return h * 360.0, s, v

        def hue_diff_deg(h1, h2):
            diff = abs(h1 - h2) % 360
            return min(diff, 360 - diff)

        # Check button color and click if green
        img = pyautogui.screenshot()
        start_color = img.getpixel((x, y))
        r, g, b = start_color
        d_green = rgb_distance(start_color, TARGETS["GREEN"])

        if d_green <= rgb_tol:
            pyautogui.click(cashout_coords)
            print(f"🟢 Position {position} cashout clicked (button was green).")
        else:
            print(f"⚠️ Position {position} cashout button not green at start, skipping click.")

        # Observe color changes
        observed = []
        start_time = time.time()
        while time.time() - start_time < duration:
            img = pyautogui.screenshot()
            pixels = []
            for dx in range(-sample_radius, sample_radius + 1):
                for dy in range(-sample_radius, sample_radius + 1):
                    sx, sy = x + dx, y + dy
                    if 0 <= sx < img.width and 0 <= sy < img.height:
                        pixels.append(img.getpixel((sx, sy)))
            if pixels:
                r = int(median([p[0] for p in pixels]))
                g = int(median([p[1] for p in pixels]))
                b = int(median([p[2] for p in pixels]))
                color = (r, g, b)
            else:
                color = img.getpixel((x, y))

            color_h, _, color_v = rgb_to_hsv_deg(color)
            best_match, best_dist = None, float('inf')

            for name, ref in TARGETS.items():
                ref_h, _, ref_v = rgb_to_hsv_deg(ref)
                dist = rgb_distance(color, ref)
                hue_diff = hue_diff_deg(color_h, ref_h)
                if dist < best_dist or (hue_diff < hue_tol_deg and color_v < low_v_acceptance):
                    best_match, best_dist = name, dist

            observed.append(best_match)
            time.sleep(interval)

        # Interpret sequence
        if not observed:
            return False, "NO_COLOR_DATA"

        joined = "→".join([c for c in observed if c])
        last = observed[-1]

        if "GREEN" in observed and "BLUE" in observed:
            return True, f"CASHOUT_SUCCESS (Green→Blue transition)"
        elif "GREEN" in observed and "ORANGE" in observed:
            return False, f"CASHOUT_CRASHED (Green→Orange)"
        elif last == "BLUE" or (observed.count("BLUE") > observed.count("GREEN") // 2):
            return True, "DETECTED_NEXT_FLIGHT"
        else:
            return False, f"UNSURE|Sequence={joined}"

    except Exception as e:
        return False, f"ERROR: {e}"


# ============================================================================
# STAKE UPDATE FUNCTIONS
# ============================================================================

def update_stake(stake_coords, new_stake, stake_reader=None, screen_capture=None):
    """
    Update stake value and verify change.

    Args:
        stake_coords: Tuple (x, y) of stake input field
        new_stake: New stake amount to set
        stake_reader: StakeReader instance (optional, for verification)
        screen_capture: ScreenCapture instance (optional, for reading)

    Returns:
        dict: Update status with verification result
    """
    try:
        timestamp = datetime.now().strftime("%H:%M:%S")
        old_stake = stake_reader.last_stake if stake_reader else None

        # Click and set new stake
        success = set_stake_verified(stake_coords, new_stake)

        if not success:
            return {
                'success': False,
                'timestamp': timestamp,
                'old_stake': old_stake,
                'new_stake': new_stake,
                'verified': False,
                'message': 'Failed to set stake value'
            }

        # Optional: verify stake was actually changed
        time.sleep(0.3)
        verified_stake = None

        if stake_reader and screen_capture:
            verified_stake = stake_reader.read_stake(screen_capture)

            if verified_stake and abs(verified_stake - new_stake) < 1:
                print(f"[{timestamp}] ✅ Stake updated: {old_stake} → {new_stake}")
                return {
                    'success': True,
                    'timestamp': timestamp,
                    'old_stake': old_stake,
                    'new_stake': new_stake,
                    'verified_stake': verified_stake,
                    'verified': True,
                    'message': f'Stake successfully updated to {new_stake}'
                }
            else:
                print(f"[{timestamp}] ⚠️ Stake change not verified. Expected: {new_stake}, Got: {verified_stake}")
                return {
                    'success': True,
                    'timestamp': timestamp,
                    'old_stake': old_stake,
                    'new_stake': new_stake,
                    'verified_stake': verified_stake,
                    'verified': False,
                    'message': f'Stake set but verification showed {verified_stake}'
                }
        else:
            print(f"[{timestamp}] ✅ Stake command sent: {old_stake} → {new_stake}")
            return {
                'success': True,
                'timestamp': timestamp,
                'old_stake': old_stake,
                'new_stake': new_stake,
                'verified': False,
                'message': f'Stake set to {new_stake} (no verification available)'
            }

    except Exception as e:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ❌ Error updating stake: {e}")
        return {
            'success': False,
            'timestamp': timestamp,
            'error': str(e),
            'message': f'Error: {e}'
        }


def update_stake_with_history(stake_coords, new_stake, stake_reader=None,
                              screen_capture=None, max_history=50):
    """
    Update stake and maintain history for analysis.

    Args:
        stake_coords: Tuple (x, y) of stake input field
        new_stake: New stake amount to set
        stake_reader: StakeReader instance (for history tracking)
        screen_capture: ScreenCapture instance (for verification)
        max_history: Maximum history entries to keep

    Returns:
        dict: Update result with historical context
    """
    result = update_stake(stake_coords, new_stake, stake_reader, screen_capture)

    if stake_reader:
        # Add to history
        stake_reader.stake_history.append({
            'timestamp': datetime.now(),
            'stake': new_stake,
            'update_result': result
        })

        # Keep history size manageable
        if len(stake_reader.stake_history) > max_history:
            stake_reader.stake_history = stake_reader.stake_history[-max_history:]

        result['history_size'] = len(stake_reader.stake_history)

    return result


def update_stake_by_strategy(stake_coords, current_stake, strategy, params,
                             stake_reader=None, screen_capture=None):
    """
    Update stake based on betting strategy.

    Args:
        stake_coords: Tuple (x, y) of stake input field
        current_stake: Current stake amount
        strategy: Strategy type ('martingale', 'percentage', 'increment', 'fixed', 'reset')
        params: Dict with strategy parameters
        stake_reader: StakeReader instance (optional)
        screen_capture: ScreenCapture instance (optional)

    Returns:
        dict: Update result with strategy info
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    new_stake = current_stake

    try:
        if strategy == 'martingale':
            # Double on loss
            multiplier = params.get('multiplier', 2.0)
            max_stake = params.get('max_stake', 1000)
            new_stake = calculate_martingale_stake(current_stake, multiplier, max_stake)
            strategy_msg = f'Martingale (×{multiplier})'

        elif strategy == 'percentage':
            # Increase by percentage
            increase_percent = params.get('increase_percent', 10)
            max_stake = params.get('max_stake', 1000)
            new_stake = int(current_stake * (1 + increase_percent / 100))
            new_stake = min(new_stake, max_stake)
            strategy_msg = f'Percentage (+{increase_percent}%)'

        elif strategy == 'increment':
            # Fixed increment
            increment_amount = params.get('increment_amount', 10)
            max_stake = params.get('max_stake', 1000)
            new_stake = current_stake + increment_amount
            new_stake = min(new_stake, max_stake)
            strategy_msg = f'Increment (+{increment_amount})'

        elif strategy == 'fixed':
            # Fixed stake (from params or stats)
            new_stake = params.get('fixed_stake', current_stake)
            strategy_msg = f'Fixed ({new_stake})'

        elif strategy == 'reset':
            # Reset to initial
            new_stake = params.get('initial_stake', current_stake)
            strategy_msg = f'Reset to initial ({new_stake})'

        else:
            return {
                'success': False,
                'timestamp': timestamp,
                'strategy': strategy,
                'message': f'Unknown strategy: {strategy}'
            }

        # Apply the update
        result = update_stake(stake_coords, new_stake, stake_reader, screen_capture)
        result['strategy'] = strategy
        result['strategy_msg'] = strategy_msg

        print(f"[{timestamp}] 📊 Strategy: {strategy_msg} | {current_stake} → {new_stake}")

        return result

    except Exception as e:
        print(f"[{timestamp}] ❌ Error applying strategy '{strategy}': {e}")
        return {
            'success': False,
            'timestamp': timestamp,
            'strategy': strategy,
            'error': str(e),
            'message': f'Strategy error: {e}'
        }


def batch_update_stakes(stake_coords_list, new_stakes, position_labels=None):
    """
    Update stakes for multiple positions simultaneously.

    Args:
        stake_coords_list: List of (x, y) tuples for each position
        new_stakes: List of stake amounts for each position
        position_labels: Optional labels for positions (e.g., ['Position 1', 'Position 2'])

    Returns:
        list: Update results for each position
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    results = []

    if len(stake_coords_list) != len(new_stakes):
        print(f"[{timestamp}] ❌ Mismatch: {len(stake_coords_list)} coords, {len(new_stakes)} stakes")
        return []

    for i, (coords, stake) in enumerate(zip(stake_coords_list, new_stakes)):
        label = position_labels[i] if position_labels and i < len(position_labels) else f"Position {i+1}"

        try:
            result = update_stake(coords, stake)
            result['position'] = label
            results.append(result)

            print(f"[{timestamp}] 💰 {label}: {stake}")

        except Exception as e:
            results.append({
                'success': False,
                'position': label,
                'error': str(e),
                'timestamp': timestamp
            })
            print(f"[{timestamp}] ❌ {label}: Error - {e}")

    return results


# ============================================================================
# DEMO MODE FUNCTIONS
# ============================================================================

def demo_mode_real_multiplier(
    stake_coords, bet_button_coords, cashout_coords,
    detector, stats, multiplier_reader=None,
    demo_stake=10, target_multiplier=1.3,
    screen_capture=None
):
    """
    Demo mode with REAL multiplier monitoring from screen.
    Reads actual multiplier values instead of estimating.

    Args:
        stake_coords: Tuple (x, y) of stake input field
        bet_button_coords: Tuple (x, y) of bet/place button
        cashout_coords: Tuple (x, y) of cashout button
        detector: GameStateDetector instance
        stats: Stats dictionary to track
        multiplier_reader: MultiplierReader instance (REQUIRED for real multiplier)
        demo_stake: Stake amount for demo (default 10)
        target_multiplier: Target multiplier to cashout at (default 1.3)
        screen_capture: ScreenCapture instance (optional)

    Returns:
        dict: Demo result with all steps executed
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    result = {
        'timestamp': timestamp,
        'demo_stake': demo_stake,
        'target_multiplier': target_multiplier,
        'steps': [],
        'use_real_multiplier': True
    }

    try:
        print("\n" + "=" * 60)
        print(f"[{timestamp}] DEMO MODE STARTED (REAL MULTIPLIER)")
        print("=" * 60)
        print(f"Target: Stake {demo_stake} | Cashout at {target_multiplier}x\n")

        # Step 1: Set Stake
        print(f"[{timestamp}] STEP 1: Setting stake to {demo_stake}...")
        stake_result = set_stake_verified(stake_coords, demo_stake)

        if not stake_result:
            print(f"[{timestamp}] Failed to set stake")
            result['steps'].append({
                'step': 'set_stake',
                'success': False,
                'message': 'Failed to set stake'
            })
            result['success'] = False
            return result

        time.sleep(0.5)
        print(f"[{timestamp}] Stake set to {demo_stake}")
        result['steps'].append({
            'step': 'set_stake',
            'success': True,
            'stake': demo_stake
        })

        # Step 2: Place Bet
        print(f"[{timestamp}] STEP 2: Placing bet...")
        success, reason = place_bet_with_verification(
            bet_button_coords, detector, stats, demo_stake
        )

        if not success:
            print(f"[{timestamp}] Failed to place bet: {reason}")
            result['steps'].append({
                'step': 'place_bet',
                'success': False,
                'message': f'Failed: {reason}'
            })
            result['success'] = False
            return result

        print(f"[{timestamp}] Bet placed successfully")
        result['steps'].append({
            'step': 'place_bet',
            'success': True,
            'reason': reason
        })

        # Step 3: Monitor for REAL Multiplier
        print(f"\n[{timestamp}] STEP 3: Monitoring REAL multiplier from screen...")
        print(f"Waiting for multiplier to reach {target_multiplier}x...")

        if not multiplier_reader:
            print(f"[{timestamp}] WARNING: No multiplier_reader provided, using estimation")
            result['use_real_multiplier'] = False
            # Fallback to estimation
            multiplier_reached = False
            final_multiplier = 0
            start_time = time.time()

            while time.time() - start_time < 60:
                elapsed = time.time() - start_time
                estimated_mult = estimate_multiplier(elapsed)

                if estimated_mult >= target_multiplier and not multiplier_reached:
                    multiplier_reached = True
                    final_multiplier = estimated_mult
                    print(f"[{timestamp}] Target {target_multiplier}x reached! (Current: {estimated_mult:.2f}x)")
                    break

                if int(elapsed) % 1 == 0:
                    print(f"  {elapsed:.1f}s | Multiplier: {estimated_mult:.2f}x (ESTIMATED)")

                time.sleep(0.5)
        else:
            # Read REAL multiplier from screen
            multiplier_reached = False
            final_multiplier = 0
            start_time = time.time()
            last_display = 0

            while time.time() - start_time < 60:
                elapsed = time.time() - start_time

                # Read real multiplier from screen
                try:
                    real_mult = multiplier_reader.read_multiplier()

                    if real_mult is None:
                        # Multiplier not visible (game crashed or round ended)
                        if multiplier_reached:
                            print(f"[{timestamp}] Round ended or game state changed")
                            break
                        else:
                            # Keep waiting
                            real_mult = 0

                    # Display every 1 second
                    if elapsed - last_display >= 1.0:
                        if real_mult > 0:
                            print(f"  {elapsed:.1f}s | Multiplier: {real_mult:.2f}x (REAL)")
                        else:
                            print(f"  {elapsed:.1f}s | Waiting for multiplier...")
                        last_display = elapsed

                    # Check if target reached
                    if real_mult >= target_multiplier and not multiplier_reached:
                        multiplier_reached = True
                        final_multiplier = real_mult
                        print(f"[{timestamp}] Target {target_multiplier}x reached! (Current: {real_mult:.2f}x)")
                        break

                except Exception as e:
                    print(f"[{timestamp}] Error reading multiplier: {e}")

                time.sleep(0.2)

        if not multiplier_reached:
            print(f"[{timestamp}] Timeout: Target multiplier not reached in 60s")
            result['steps'].append({
                'step': 'monitor_multiplier',
                'success': False,
                'message': 'Timeout waiting for multiplier'
            })
            # Still proceed with cashout at current multiplier
            final_multiplier = final_multiplier if final_multiplier > 0 else 1.0

        result['steps'].append({
            'step': 'monitor_multiplier',
            'success': multiplier_reached,
            'target': target_multiplier,
            'final_multiplier': final_multiplier,
            'elapsed_seconds': elapsed
        })

        # Step 4: Cashout
        print(f"\n[{timestamp}] STEP 4: Cashing out at {final_multiplier:.2f}x...")
        cashout_success, outcome = cashout_verified(
            cashout_coords, detector,
            duration=4.0, interval=0.2
        )

        if cashout_success:
            print(f"[{timestamp}] Cashout successful!")
            print(f"Outcome: {outcome}")
        else:
            print(f"[{timestamp}] Cashout result: {outcome}")

        result['steps'].append({
            'step': 'cashout',
            'success': cashout_success,
            'outcome': outcome,
            'final_multiplier': final_multiplier
        })

        # Calculate winnings
        winnings = demo_stake * final_multiplier
        profit = winnings - demo_stake

        print(f"\n" + "=" * 60)
        print(f"[{timestamp}] DEMO MODE COMPLETED")
        print("=" * 60)
        print(f"Stake:        {demo_stake}")
        print(f"Multiplier:   {final_multiplier:.2f}x (REAL)")
        print(f"Winnings:     {winnings:.2f}")
        print(f"Profit:       {profit:.2f}")
        print(f"Status:       {'WON' if cashout_success else 'UNCERTAIN'}")
        print("=" * 60 + "\n")

        result.update({
            'success': True,
            'stake': demo_stake,
            'final_multiplier': final_multiplier,
            'winnings': winnings,
            'profit': profit,
            'cashout_success': cashout_success
        })

        return result

    except Exception as e:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] Demo mode error: {e}")
        result.update({
            'success': False,
            'error': str(e),
            'message': f'Demo mode failed: {e}'
        })
        return result


def demo_mode_simple_bet(
    stake_coords, bet_button_coords, cashout_coords,
    detector, stats,
    demo_stake=10, target_multiplier=1.3,
    screen_capture=None
):
    """
    Simple demo mode: Set stake to 10, place bet, cashout at 1.3x multiplier.

    Args:
        stake_coords: Tuple (x, y) of stake input field
        bet_button_coords: Tuple (x, y) of bet/place button
        cashout_coords: Tuple (x, y) of cashout button
        detector: GameStateDetector instance
        stats: Stats dictionary to track
        demo_stake: Stake amount for demo (default 10)
        target_multiplier: Target multiplier to cashout at (default 1.3)
        screen_capture: ScreenCapture instance (optional)

    Returns:
        dict: Demo result with all steps executed
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    result = {
        'timestamp': timestamp,
        'demo_stake': demo_stake,
        'target_multiplier': target_multiplier,
        'steps': []
    }

    try:
        print("\n" + "=" * 60)
        print(f"[{timestamp}] DEMO MODE STARTED")
        print("=" * 60)
        print(f"Target: Stake {demo_stake} | Cashout at {target_multiplier}x\n")

        # Step 1: Set Stake
        print(f"[{timestamp}] STEP 1: Setting stake to {demo_stake}...")
        stake_result = set_stake_verified(stake_coords, demo_stake)

        if not stake_result:
            print(f"[{timestamp}] ❌ Failed to set stake")
            result['steps'].append({
                'step': 'set_stake',
                'success': False,
                'message': 'Failed to set stake'
            })
            result['success'] = False
            return result

        time.sleep(0.5)
        print(f"[{timestamp}] ✅ Stake set to {demo_stake}")
        result['steps'].append({
            'step': 'set_stake',
            'success': True,
            'stake': demo_stake
        })

        # Step 2: Place Bet
        print(f"[{timestamp}] STEP 2: Placing bet...")
        success, reason = place_bet_with_verification(
            bet_button_coords, detector, stats, demo_stake
        )

        if not success:
            print(f"[{timestamp}] ❌ Failed to place bet: {reason}")
            result['steps'].append({
                'step': 'place_bet',
                'success': False,
                'message': f'Failed: {reason}'
            })
            result['success'] = False
            return result

        print(f"[{timestamp}] ✅ Bet placed successfully")
        result['steps'].append({
            'step': 'place_bet',
            'success': True,
            'reason': reason
        })

        # Step 3: Monitor for Target Multiplier
        print(f"\n[{timestamp}] STEP 3: Monitoring multiplier...")
        print(f"Waiting for multiplier to reach {target_multiplier}x...")

        start_time = time.time()
        multiplier_reached = False
        final_multiplier = 0

        # Monitor for up to 60 seconds (typical round duration)
        while time.time() - start_time < 60:
            # Check current multiplier (estimated from elapsed time)
            elapsed = time.time() - start_time
            estimated_mult = estimate_multiplier(elapsed)

            if estimated_mult >= target_multiplier and not multiplier_reached:
                multiplier_reached = True
                final_multiplier = estimated_mult
                print(f"[{timestamp}] Target {target_multiplier}x reached! (Current: {estimated_mult:.2f}x)")
                break

            # Show progress every 0.5 seconds
            if int(elapsed) % 1 == 0:
                print(f"  {elapsed:.1f}s | Multiplier: {estimated_mult:.2f}x")

            time.sleep(0.5)

        if not multiplier_reached:
            print(f"[{timestamp}] ⚠️  Timeout: Target multiplier not reached in 60s")
            result['steps'].append({
                'step': 'monitor_multiplier',
                'success': False,
                'message': 'Timeout waiting for multiplier'
            })
            # Still proceed with cashout
            final_multiplier = estimated_mult

        result['steps'].append({
            'step': 'monitor_multiplier',
            'success': multiplier_reached,
            'target': target_multiplier,
            'final_multiplier': final_multiplier,
            'elapsed_seconds': elapsed
        })

        # Step 4: Cashout
        print(f"\n[{timestamp}] STEP 4: Cashing out at {final_multiplier:.2f}x...")
        cashout_success, outcome = cashout_verified(
            cashout_coords, detector,
            duration=4.0, interval=0.2
        )

        if cashout_success:
            print(f"[{timestamp}] ✅ Cashout successful!")
            print(f"Outcome: {outcome}")
        else:
            print(f"[{timestamp}] ⚠️  Cashout result: {outcome}")

        result['steps'].append({
            'step': 'cashout',
            'success': cashout_success,
            'outcome': outcome,
            'final_multiplier': final_multiplier
        })

        # Calculate winnings
        winnings = demo_stake * final_multiplier
        profit = winnings - demo_stake

        print(f"\n" + "=" * 60)
        print(f"[{timestamp}] DEMO MODE COMPLETED")
        print("=" * 60)
        print(f"Stake:        {demo_stake}")
        print(f"Multiplier:   {final_multiplier:.2f}x")
        print(f"Winnings:     {winnings:.2f}")
        print(f"Profit:       {profit:.2f}")
        print(f"Status:       {'WON' if cashout_success else 'UNCERTAIN'}")
        print("=" * 60 + "\n")

        result.update({
            'success': True,
            'stake': demo_stake,
            'final_multiplier': final_multiplier,
            'winnings': winnings,
            'profit': profit,
            'cashout_success': cashout_success
        })

        return result

    except Exception as e:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ❌ Demo mode error: {e}")
        result.update({
            'success': False,
            'error': str(e),
            'message': f'Demo mode failed: {e}'
        })
        return result


def demo_mode_interactive(
    stake_coords, bet_button_coords, cashout_coords,
    detector, stats,
    screen_capture=None
):
    """
    Interactive demo mode: User enters stake and multiplier.

    Args:
        stake_coords: Tuple (x, y) of stake input field
        bet_button_coords: Tuple (x, y) of bet/place button
        cashout_coords: Tuple (x, y) of cashout button
        detector: GameStateDetector instance
        stats: Stats dictionary to track
        screen_capture: ScreenCapture instance (optional)

    Returns:
        dict: Demo result
    """
    print("\n" + "=" * 60)
    print("INTERACTIVE DEMO MODE")
    print("=" * 60)

    # Get user inputs
    try:
        stake_input = input("Enter stake amount (default 10): ").strip()
        demo_stake = int(stake_input) if stake_input else 10

        mult_input = input("Enter target multiplier (default 1.3): ").strip()
        target_mult = float(mult_input) if mult_input else 1.3

    except ValueError:
        print("Invalid input. Using defaults: stake=10, multiplier=1.3")
        demo_stake = 10
        target_mult = 1.3

    print(f"\nConfiguration: Stake={demo_stake}, Target={target_mult}x\n")

    # Run the demo
    return demo_mode_simple_bet(
        stake_coords, bet_button_coords, cashout_coords,
        detector, stats,
        demo_stake=demo_stake,
        target_multiplier=target_mult,
        screen_capture=screen_capture
    )


def demo_mode_multi_round(
    stake_coords, bet_button_coords, cashout_coords,
    detector, stats,
    num_rounds=3, demo_stake=10, target_multiplier=1.3,
    screen_capture=None
):
    """
    Multi-round demo: Run multiple rounds with same parameters.

    Args:
        stake_coords: Tuple (x, y) of stake input field
        bet_button_coords: Tuple (x, y) of bet/place button
        cashout_coords: Tuple (x, y) of cashout button
        detector: GameStateDetector instance
        stats: Stats dictionary to track
        num_rounds: Number of rounds to play (default 3)
        demo_stake: Stake amount for each round (default 10)
        target_multiplier: Target multiplier (default 1.3)
        screen_capture: ScreenCapture instance (optional)

    Returns:
        dict: Summary of all rounds
    """
    timestamp = datetime.now().strftime("%H:%M:%S")

    print("\n" + "=" * 60)
    print(f"[{timestamp}] MULTI-ROUND DEMO MODE")
    print("=" * 60)
    print(f"Rounds: {num_rounds}")
    print(f"Stake: {demo_stake}")
    print(f"Target: {target_multiplier}x")
    print("=" * 60 + "\n")

    all_results = {
        'timestamp': timestamp,
        'num_rounds': num_rounds,
        'stake': demo_stake,
        'target_multiplier': target_multiplier,
        'rounds': []
    }

    total_winnings = 0
    total_profit = 0
    wins = 0
    losses = 0

    for round_num in range(1, num_rounds + 1):
        print(f"\n{'='*60}")
        print(f"ROUND {round_num}/{num_rounds}")
        print(f"{'='*60}\n")

        result = demo_mode_simple_bet(
            stake_coords, bet_button_coords, cashout_coords,
            detector, stats,
            demo_stake=demo_stake,
            target_multiplier=target_multiplier,
            screen_capture=screen_capture
        )

        all_results['rounds'].append(result)

        if result['success'] and result.get('cashout_success'):
            wins += 1
            total_winnings += result.get('winnings', 0)
            total_profit += result.get('profit', 0)
        else:
            losses += 1

        # Wait between rounds
        if round_num < num_rounds:
            print(f"\nWaiting before next round...")
            time.sleep(2)

    # Summary
    print(f"\n{'='*60}")
    print(f"DEMO MODE SUMMARY - {num_rounds} ROUNDS")
    print(f"{'='*60}")
    print(f"Total Rounds:   {num_rounds}")
    print(f"Wins:           {wins}")
    print(f"Losses:         {losses}")
    print(f"Win Rate:       {wins/num_rounds*100:.1f}%")
    print(f"Total Bet:      {demo_stake * num_rounds}")
    print(f"Total Winnings: {total_winnings:.2f}")
    print(f"Total Profit:   {total_profit:.2f}")
    print(f"{'='*60}\n")

    all_results.update({
        'summary': {
            'wins': wins,
            'losses': losses,
            'win_rate': wins/num_rounds*100,
            'total_bet': demo_stake * num_rounds,
            'total_winnings': total_winnings,
            'total_profit': total_profit
        }
    })

    return all_results


def demo_mode_continuous(
    stake_coords, bet_button_coords, cashout_coords,
    detector, stats, multiplier_reader=None,
    demo_stake=10, target_multiplier=1.3,
    num_rounds=3, screen_capture=None
):
    """
    Continuous demo mode with REAL multiplier monitoring and AUTO-CASHOUT.
    Runs multiple rounds automatically, reading REAL multiplier and clicking cashout button.

    Args:
        stake_coords: Tuple (x, y) of stake input field
        bet_button_coords: Tuple (x, y) of bet/place button
        cashout_coords: Tuple (x, y) of cashout button
        detector: GameStateDetector instance
        stats: Stats dictionary to track
        multiplier_reader: MultiplierReader instance (REQUIRED for real multiplier)
        demo_stake: Stake amount per round (default 10)
        target_multiplier: Target multiplier to cashout at (default 1.3)
        num_rounds: Number of rounds to run (default 3)
        screen_capture: ScreenCapture instance (optional)

    Returns:
        dict: Summary of all rounds with auto-cashout results
    """
    timestamp = datetime.now().strftime("%H:%M:%S")

    print("\n" + "=" * 60)
    print(f"[{timestamp}] CONTINUOUS DEMO MODE (AUTO-CASHOUT)")
    print("=" * 60)
    print(f"Rounds: {num_rounds}")
    print(f"Stake: {demo_stake}")
    print(f"Target: {target_multiplier}x")
    print(f"Mode: REAL Multiplier with AUTO-CLICK Cashout")
    print("=" * 60 + "\n")

    all_results = {
        'timestamp': timestamp,
        'num_rounds': num_rounds,
        'stake': demo_stake,
        'target_multiplier': target_multiplier,
        'mode': 'continuous_auto_cashout',
        'rounds': []
    }

    total_winnings = 0
    total_profit = 0
    wins = 0
    losses = 0

    for round_num in range(1, num_rounds + 1):
        print(f"\n{'='*60}")
        print(f"ROUND {round_num}/{num_rounds}")
        print(f"{'='*60}\n")

        round_start = datetime.now().strftime("%H:%M:%S")

        try:
            # Step 1: Wait for current round to end (if one is active)
            print(f"[{round_start}] STEP 1: Checking if a round is currently active...")

            if not multiplier_reader:
                print(f"[{round_start}] WARNING: No multiplier_reader")
                losses += 1
                continue

            # Check if multiplier > 1.0 (round is active)
            current_mult = multiplier_reader.read_multiplier()
            if current_mult and current_mult > 1.0:
                print(f"[{round_start}] Round is active at {current_mult:.2f}x. Waiting for it to end...")

                # Wait for round to end (multiplier <= 1.0 or becomes None)
                wait_start = time.time()
                while time.time() - wait_start < 120:  # Max 2 minutes wait
                    try:
                        mult = multiplier_reader.read_multiplier()
                        if mult is None or mult <= 1.0:
                            print(f"[{round_start}] Previous round ended. Ready to place new bet.")
                            break
                    except:
                        pass
                    time.sleep(0.5)
            else:
                print(f"[{round_start}] No active round. Ready to place bet.")

            time.sleep(0.5)

            # Step 2: Set Stake
            print(f"[{round_start}] STEP 2: Setting stake to {demo_stake}...")
            stake_result = set_stake_verified(stake_coords, demo_stake)

            if not stake_result:
                print(f"[{round_start}] Failed to set stake, skipping round")
                all_results['rounds'].append({
                    'round': round_num,
                    'success': False,
                    'error': 'Failed to set stake'
                })
                losses += 1
                continue

            time.sleep(0.5)
            print(f"[{round_start}] Stake set to {demo_stake}")

            # Step 3: Place Bet
            print(f"[{round_start}] STEP 3: Placing bet...")
            success, reason = place_bet_with_verification(
                bet_button_coords, detector, stats, demo_stake
            )

            if not success:
                print(f"[{round_start}] Failed to place bet: {reason}")
                all_results['rounds'].append({
                    'round': round_num,
                    'success': False,
                    'error': f'Failed to place bet: {reason}'
                })
                losses += 1
                continue

            print(f"[{round_start}] Bet placed successfully")
            time.sleep(1.0)

            # Step 4: Wait for round to start (multiplier > 1.0)
            print(f"\n[{round_start}] STEP 4: Waiting for round to start...")

            round_started = False
            start_wait_time = time.time()
            while time.time() - start_wait_time < 10:  # Wait max 10 seconds for round to start
                try:
                    real_mult = multiplier_reader.read_multiplier()
                    if real_mult and real_mult > 1.0:
                        print(f"[{round_start}] Round started! Multiplier: {real_mult:.2f}x")
                        round_started = True
                        break
                except:
                    pass
                time.sleep(0.2)

            if not round_started:
                print(f"[{round_start}] Round failed to start or multiplier not readable")
                all_results['rounds'].append({
                    'round': round_num,
                    'success': False,
                    'error': 'Round did not start'
                })
                losses += 1
                continue

            # Step 5: Monitor for REAL Multiplier and AUTO-CASHOUT
            print(f"\n[{round_start}] STEP 5: Monitoring REAL multiplier...")
            print(f"Waiting for multiplier to reach {target_multiplier}x, then AUTO-CLICK cashout...\n")

            multiplier_reached = False
            final_multiplier = 0
            cashout_clicked = False
            start_time = time.time()
            last_display = 0

            # Monitor for up to 60 seconds
            while time.time() - start_time < 60:
                elapsed = time.time() - start_time

                try:
                    # Read REAL multiplier from screen
                    real_mult = multiplier_reader.read_multiplier()

                    if real_mult is None:
                        # Multiplier not visible
                        if multiplier_reached:
                            break
                        else:
                            real_mult = 0

                    # Display every 1 second
                    if elapsed - last_display >= 1.0:
                        if real_mult > 0:
                            print(f"  {elapsed:.1f}s | Multiplier: {real_mult:.2f}x (REAL)")
                        else:
                            print(f"  {elapsed:.1f}s | Waiting for multiplier...")
                        last_display = elapsed

                    # AUTO-CLICK CASHOUT when target is reached
                    if real_mult >= target_multiplier and not cashout_clicked:
                        multiplier_reached = True
                        final_multiplier = real_mult
                        print(f"\n[{round_start}] TARGET REACHED: {real_mult:.2f}x >= {target_multiplier}x")
                        print(f"[{round_start}] AUTO-CLICKING CASHOUT BUTTON...")

                        # ACTUALLY CLICK THE CASHOUT BUTTON
                        pyautogui.click(cashout_coords[0], cashout_coords[1])
                        cashout_clicked = True

                        print(f"[{round_start}] Cashout button clicked!")
                        time.sleep(1.0)
                        break

                except Exception as e:
                    print(f"[{round_start}] Error reading multiplier: {e}")

                time.sleep(0.2)  # Check every 0.2 seconds

            # Verify cashout success
            if cashout_clicked:
                print(f"\n[{round_start}] STEP 6: Verifying cashout...")
                # Wait for cashout verification
                time.sleep(2.0)

                # Calculate winnings
                winnings = demo_stake * final_multiplier
                profit = winnings - demo_stake

                print(f"\n[{round_start}] Round {round_num} COMPLETED")
                print(f"[{round_start}] Cashout at: {final_multiplier:.2f}x")
                print(f"[{round_start}] Profit: {profit:.2f}")

                all_results['rounds'].append({
                    'round': round_num,
                    'success': True,
                    'stake': demo_stake,
                    'final_multiplier': final_multiplier,
                    'winnings': winnings,
                    'profit': profit,
                    'cashout_success': True,
                    'auto_clicked': True
                })

                wins += 1
                total_winnings += winnings
                total_profit += profit
            else:
                print(f"\n[{round_start}] Round {round_num} FAILED - Target not reached or auto-click failed")
                all_results['rounds'].append({
                    'round': round_num,
                    'success': False,
                    'error': 'Target multiplier not reached or auto-click failed'
                })
                losses += 1

        except Exception as e:
            print(f"[{round_start}] Round {round_num} ERROR: {e}")
            all_results['rounds'].append({
                'round': round_num,
                'success': False,
                'error': str(e)
            })
            losses += 1

        # Wait between rounds (except after last round)
        if round_num < num_rounds:
            print(f"\nWaiting 3 seconds before next round...")
            time.sleep(3)

    # Summary
    print(f"\n{'='*60}")
    print(f"[{timestamp}] CONTINUOUS DEMO COMPLETED - {num_rounds} ROUNDS")
    print(f"{'='*60}")
    print(f"Total Rounds:   {num_rounds}")
    print(f"Wins (Cashed):  {wins}")
    print(f"Losses (Failed): {losses}")
    if num_rounds > 0:
        print(f"Win Rate:       {wins/num_rounds*100:.1f}%")
    print(f"Total Bet:      {demo_stake * num_rounds}")
    print(f"Total Winnings: {total_winnings:.2f}")
    print(f"Total Profit:   {total_profit:.2f}")
    print(f"{'='*60}\n")

    all_results.update({
        'summary': {
            'wins': wins,
            'losses': losses,
            'win_rate': wins/num_rounds*100 if num_rounds > 0 else 0,
            'total_bet': demo_stake * num_rounds,
            'total_winnings': total_winnings,
            'total_profit': total_profit,
            'auto_cashout_mode': True
        }
    })

    return all_results
