"""Auto-refresh module to periodically refresh the multiplier display"""
import time
import threading
import pyautogui
from datetime import datetime


class AutoRefresher:
    """Handles automatic refreshing of the multiplier display"""

    def __init__(self, region, refresh_interval=900):
        """
        Initialize auto-refresher

        Args:
            region: Region object with x1, y1, x2, y2 coordinates
            refresh_interval: Time in seconds between refreshes (default: 900 = 15 minutes)
        """
        self.region = region
        self.refresh_interval = refresh_interval
        self.running = False
        self.thread = None
        self.last_refresh_time = time.time()

    def get_top_right_corner(self):
        """Get the top-right corner coordinates of the region"""
        # Top-right corner is at (x2, y1)
        return (self.region.x2, self.region.y1)

    def perform_refresh(self):
        """Move mouse to top-right corner, click to focus, and send F5"""
        try:
            # Get top-right corner coordinates
            x, y = self.get_top_right_corner()

            # Move mouse to top-right corner
            pyautogui.moveTo(x, y, duration=0.5)

            # Small pause
            time.sleep(0.2)

            # Click to give focus to the window
            pyautogui.click()

            # Small pause after click to ensure focus is set
            time.sleep(0.3)

            # Send F5 (standard refresh key)
            pyautogui.press('f5')

            # Log the refresh action
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{timestamp}] AUTO-REFRESH: Moved to ({x}, {y}), clicked, and pressed F5")

            # Update last refresh time
            self.last_refresh_time = time.time()

            return True

        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{timestamp}] AUTO-REFRESH ERROR: {e}")
            return False

    def _refresh_loop(self):
        """Background thread loop that performs periodic refreshes"""
        while self.running:
            try:
                # Wait for the refresh interval
                time.sleep(1)  # Check every second

                # Check if it's time to refresh
                elapsed = time.time() - self.last_refresh_time
                if elapsed >= self.refresh_interval:
                    self.perform_refresh()

            except Exception as e:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"\n[{timestamp}] AUTO-REFRESH THREAD ERROR: {e}")
                time.sleep(1)

    def start(self):
        """Start the auto-refresh background thread"""
        if self.running:
            print("[AUTO-REFRESH] Already running")
            return

        self.running = True
        self.last_refresh_time = time.time()
        self.thread = threading.Thread(target=self._refresh_loop, daemon=True)
        self.thread.start()

        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] AUTO-REFRESH: Started (interval: {self.refresh_interval}s = {self.refresh_interval/60:.1f} minutes)")
        print(f"[{timestamp}] AUTO-REFRESH: Target region top-right corner: {self.get_top_right_corner()}")

    def stop(self):
        """Stop the auto-refresh background thread"""
        if not self.running:
            return

        self.running = False
        if self.thread:
            self.thread.join(timeout=2)

        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] AUTO-REFRESH: Stopped")

    def get_time_until_next_refresh(self):
        """Get seconds until next refresh"""
        elapsed = time.time() - self.last_refresh_time
        remaining = max(0, self.refresh_interval - elapsed)
        return remaining
