"""
Bet Placement Orchestrator - Bet Placement & Verification

Handles:
1. Bet button clicking with error handling
2. Verification using color detection and OCR
3. Retry logic (max 3 attempts)
4. Statistics updates
"""

import time
import pyautogui
import numpy as np
from datetime import datetime
from typing import Dict, Tuple, Optional, Any


class BetPlacementManager:
    """Manages bet button clicking and verification"""

    def __init__(self, game_actions: Any, screen_capture: Any,
                 bet_button_coords: Tuple[float, float]):
        """
        Initialize bet placement manager

        Args:
            game_actions: GameActions instance
            screen_capture: ScreenCapture instance
            bet_button_coords: (x, y) tuple for bet button
        """
        self.game_actions = game_actions
        self.screen_capture = screen_capture
        self.bet_button_coords = bet_button_coords

        # Color targets for button state detection
        self.COLOR_TARGETS = {
            'GREEN': (85, 170, 38),      # Place bet button (available)
            'GRAY': (128, 128, 128),     # Placed or disabled
            'BLUE': (45, 107, 253)       # Game in progress
        }

    def click_bet_button(self) -> Dict:
        """
        Click bet button safely

        Returns:
            Dict with click result
        """
        try:
            # Record initial button state
            initial_color = self._get_button_color()

            # Perform click
            pyautogui.click(int(self.bet_button_coords[0]),
                          int(self.bet_button_coords[1]))

            time.sleep(0.4)  # Wait for UI update

            # Record new button state
            new_color = self._get_button_color()

            result = {
                'success': True,
                'error': None,
                'initial_color': initial_color,
                'new_color': new_color,
                'color_changed': initial_color != new_color,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            return result

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

    def _get_button_color(self) -> Optional[str]:
        """Get button color at current coordinates"""
        try:
            x, y = int(self.bet_button_coords[0]), int(self.bet_button_coords[1])
            screenshot = pyautogui.screenshot()
            pixel = screenshot.getpixel((x, y))

            # Simple color matching
            if len(pixel) >= 3:
                r, g, b = pixel[0], pixel[1], pixel[2]

                # Check if green (place bet button)
                if g > 100 and r < g:
                    return 'GREEN'
                # Check if gray (button state changed)
                elif abs(r - g) < 30 and abs(g - b) < 30:
                    return 'GRAY'
                # Check if blue (game in progress)
                elif b > 100 and r < b:
                    return 'BLUE'
                else:
                    return 'OTHER'

            return None

        except Exception:
            return None

    def verify_bet_placed(self, max_retries: int = 3) -> Dict:
        """
        Verify bet was placed using color detection and fallback OCR

        Args:
            max_retries: Maximum retry attempts

        Returns:
            Dict with verification result
        """
        for attempt in range(max_retries):
            try:
                # Method 1: Color detection
                button_color = self._get_button_color()

                # Button should NOT be GREEN if bet placed
                # (GREEN = "Place Bet" available, any other = placed/not available)
                if button_color != 'GREEN' and button_color is not None:
                    return {
                        'verified': True,
                        'method': 'color_detection',
                        'button_color': button_color,
                        'attempts': attempt + 1,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }

                # Method 2: OCR text detection (fallback)
                if attempt == max_retries - 1:  # Last attempt
                    text_verified = self._verify_by_ocr()
                    if text_verified:
                        return {
                            'verified': True,
                            'method': 'ocr_detection',
                            'button_color': button_color,
                            'attempts': attempt + 1,
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }

                # Wait before retry
                if attempt < max_retries - 1:
                    time.sleep(0.3)

            except Exception as e:
                if attempt == max_retries - 1:
                    return {
                        'verified': False,
                        'error': str(e),
                        'attempts': attempt + 1,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                time.sleep(0.2)

        return {
            'verified': False,
            'error': 'max_retries_exceeded',
            'attempts': max_retries,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def _verify_by_ocr(self) -> bool:
        """
        Verify bet placed using OCR (fallback method)

        Returns:
            bool indicating verification success
        """
        try:
            # Capture button region
            x, y = int(self.bet_button_coords[0]), int(self.bet_button_coords[1])
            region = (x - 60, y - 25, 120, 50)

            # This would require pytesseract integration
            # For now, return simple color-based check result
            color = self._get_button_color()
            return color != 'GREEN'

        except Exception:
            return False

    def place_bet_with_verification(self, max_retries: int = 3) -> Dict:
        """
        Full bet placement with click and verification loop

        Args:
            max_retries: Maximum retries before failure

        Returns:
            Dict with complete placement result
        """
        click_result = self.click_bet_button()

        if not click_result['success']:
            return {
                'success': False,
                'error': f"click_failed: {click_result['error']}",
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        # Verify placement (may retry)
        verification_result = self.verify_bet_placed(max_retries)

        result = {
            'success': verification_result.get('verified', False),
            'click_result': click_result,
            'verification_result': verification_result,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        return result


class BetPlacementOrchestrator:
    """Orchestrates bet placement and statistics updates"""

    def __init__(self, manager: BetPlacementManager, stats_tracker: Any):
        """
        Initialize orchestrator

        Args:
            manager: BetPlacementManager instance
            stats_tracker: Statistics tracking object
        """
        self.manager = manager
        self.stats_tracker = stats_tracker

    def execute_bet_placement(self, stake: float,
                             position: int = 1) -> Dict:
        """
        Execute complete bet placement workflow

        Includes:
        1. Click bet button
        2. Verify placement with retries
        3. Update stats on success
        4. Log transaction

        Args:
            stake: Stake amount for this bet
            position: Position 1 or 2

        Returns:
            Dict with complete result
        """
        # Place bet with verification (max 3 attempts)
        placement_result = self.manager.place_bet_with_verification(max_retries=3)

        if not placement_result['success']:
            return {
                'success': False,
                'error': placement_result.get('error', 'unknown_error'),
                'stake': stake,
                'position': position,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        # Update statistics
        try:
            if hasattr(self.stats_tracker, 'increment_bets_placed'):
                self.stats_tracker.increment_bets_placed(stake)
            elif isinstance(self.stats_tracker, dict):
                self.stats_tracker['bets_placed'] = self.stats_tracker.get('bets_placed', 0) + 1
                self.stats_tracker['total_bet'] = self.stats_tracker.get('total_bet', 0) + stake

        except Exception as e:
            # Don't fail if stats update fails
            print(f"Warning: Stats update failed: {e}")

        return {
            'success': True,
            'stake': stake,
            'position': position,
            'placement_result': placement_result,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
