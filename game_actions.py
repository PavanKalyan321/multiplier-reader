# Game action automation using PyAutoGUI
import pyautogui
import time
from datetime import datetime
from config import PointConfig
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from multiplier_reader import MultiplierReader


class GameActions:
    """Handle game actions like placing bets and cashing out"""

    def __init__(self, bet_button_point: PointConfig):
        """Initialize with button coordinates

        Args:
            bet_button_point: PointConfig with x, y coordinates for bet/cashout button
        """
        self.bet_button_point = bet_button_point
        self.click_stats = {
            'total_clicks': 0,
            'successful_clicks': 0,
            'failed_clicks': 0,
            'last_click_time': None,
            'last_click_type': None
        }

    def safe_click(self, x, y, click_type='click') -> bool:
        """Safely click at specified coordinates with error handling and delays

        Args:
            x: X coordinate
            y: Y coordinate
            click_type: Type of click action (bet, cashout, etc.)

        Returns:
            bool: True if click succeeded, False otherwise
        """
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")

            # Safety delay before click
            time.sleep(0.5)

            print(f"[{timestamp}] INFO: {click_type.upper()} - Clicking at ({x}, {y})")

            # Perform the click
            pyautogui.click(x, y)

            # Safety delay after click
            time.sleep(0.3)

            # Update statistics
            self.click_stats['total_clicks'] += 1
            self.click_stats['successful_clicks'] += 1
            self.click_stats['last_click_time'] = datetime.now()
            self.click_stats['last_click_type'] = click_type

            return True

        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] WARNING: {click_type.upper()} FAILED - Error: {e}")

            # Update statistics
            self.click_stats['total_clicks'] += 1
            self.click_stats['failed_clicks'] += 1

            return False

    def wait_for_round_end(self, multiplier_reader: "MultiplierReader", max_wait_seconds: float = 120) -> bool:
        """Wait for current round to end before placing a bet

        Args:
            multiplier_reader: MultiplierReader instance to check multiplier
            max_wait_seconds: Maximum time to wait (default 2 minutes)

        Returns:
            bool: True if round ended or no active round, False if timeout
        """
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")

            # Check if a round is currently active
            current_mult = multiplier_reader.read_multiplier()
            if current_mult is None or current_mult <= 1.0:
                print(f"[{timestamp}] INFO: No active round. Ready to place bet.")
                return True

            print(f"[{timestamp}] INFO: Round is active at {current_mult:.2f}x. Waiting for it to end...")

            # Wait for round to end (multiplier <= 1.0 or becomes None)
            start_time = time.time()
            last_display = start_time

            while time.time() - start_time < max_wait_seconds:
                try:
                    mult = multiplier_reader.read_multiplier()
                    if mult is None or mult <= 1.0:
                        print(f"[{timestamp}] INFO: Previous round ended. Ready to place new bet.")
                        return True

                    # Display status every 1 second
                    if time.time() - last_display >= 1.0:
                        elapsed = time.time() - start_time
                        print(f"[{timestamp}] INFO: Waiting... Current: {mult:.2f}x (Elapsed: {elapsed:.1f}s)")
                        last_display = time.time()
                except:
                    pass

                time.sleep(0.2)

            print(f"[{timestamp}] WARNING: Timeout waiting for round to end (waited {max_wait_seconds}s)")
            return False

        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] ERROR: Failed to wait for round end: {e}")
            return False

    def click_bet_button(self) -> bool:
        """Click the bet button at configured coordinates

        Returns:
            bool: True if click succeeded, False otherwise
        """
        if not self.bet_button_point.is_valid():
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] ERROR: Invalid bet button coordinates")
            return False

        return self.safe_click(
            self.bet_button_point.x,
            self.bet_button_point.y,
            click_type='place_bet'
        )

    def click_cashout_button(self) -> bool:
        """Click the cashout button (same coordinates as bet button)

        Returns:
            bool: True if click succeeded, False otherwise
        """
        if not self.bet_button_point.is_valid():
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] ERROR: Invalid cashout button coordinates")
            return False

        return self.safe_click(
            self.bet_button_point.x,
            self.bet_button_point.y,
            click_type='cashout'
        )

    def get_click_stats(self) -> dict:
        """Get click statistics

        Returns:
            dict: Statistics about clicks performed
        """
        return {
            **self.click_stats,
            'success_rate': (
                self.click_stats['successful_clicks'] / self.click_stats['total_clicks'] * 100
                if self.click_stats['total_clicks'] > 0
                else 0
            )
        }

    def print_click_stats(self):
        """Print click statistics to console"""
        stats = self.get_click_stats()
        timestamp = datetime.now().strftime("%H:%M:%S")

        print(f"\n[{timestamp}] INFO: Click Statistics")
        print(f"[{timestamp}] INFO: Total clicks: {stats['total_clicks']}")
        print(f"[{timestamp}] INFO: Successful: {stats['successful_clicks']}")
        print(f"[{timestamp}] INFO: Failed: {stats['failed_clicks']}")
        print(f"[{timestamp}] INFO: Success rate: {stats['success_rate']:.1f}%")

        if stats['last_click_time']:
            print(f"[{timestamp}] INFO: Last click: {stats['last_click_type']} at {stats['last_click_time'].strftime('%H:%M:%S')}")
