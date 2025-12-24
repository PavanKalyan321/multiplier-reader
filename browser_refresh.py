"""Browser refresh logic for session management"""

import pyautogui
import time
from datetime import datetime


class BrowserRefresh:
    """Handle periodic browser refresh to prevent session expiration"""

    def __init__(self, refresh_interval_minutes=30):
        """
        Initialize browser refresh handler

        Args:
            refresh_interval_minutes: Interval between refreshes (default 30 minutes)
        """
        self.refresh_interval = refresh_interval_minutes * 60  # Convert to seconds
        self.last_refresh_time = time.time()
        self.refresh_count = 0

    def should_refresh(self):
        """Check if it's time to refresh the browser"""
        elapsed = time.time() - self.last_refresh_time
        return elapsed >= self.refresh_interval

    def refresh_browser(self):
        """
        Refresh the browser using F5 key
        Assumes the browser window is active/focused
        """
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] INFO: Browser refresh starting...")

            # Wait a moment to ensure we're ready
            time.sleep(0.5)

            # Press F5 to refresh
            pyautogui.press('f5')

            # Wait for browser to refresh (adjust based on network speed)
            time.sleep(3)

            # Reset the last refresh time
            self.last_refresh_time = time.time()
            self.refresh_count += 1

            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] INFO: Browser refresh complete (total refreshes: {self.refresh_count})")
            return True

        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] WARNING: Browser refresh failed: {e}")
            return False

    def refresh_browser_keyboard(self):
        """
        Alternative refresh method using Ctrl+R (works better on some browsers)
        """
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] INFO: Browser refresh starting (Ctrl+R)...")

            time.sleep(0.5)

            # Press Ctrl+R to refresh
            pyautogui.hotkey('ctrl', 'r')

            # Wait for browser to refresh
            time.sleep(3)

            self.last_refresh_time = time.time()
            self.refresh_count += 1

            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] INFO: Browser refresh complete (total refreshes: {self.refresh_count})")
            return True

        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] WARNING: Browser refresh failed: {e}")
            return False

    def refresh_browser_hard(self):
        """
        Hard refresh using Ctrl+Shift+R (clears cache and reloads)
        """
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] INFO: Browser hard refresh starting (Ctrl+Shift+R)...")

            time.sleep(0.5)

            # Press Ctrl+Shift+R for hard refresh
            pyautogui.hotkey('ctrl', 'shift', 'r')

            # Wait longer for hard refresh with cache clear
            time.sleep(5)

            self.last_refresh_time = time.time()
            self.refresh_count += 1

            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] INFO: Browser hard refresh complete (total refreshes: {self.refresh_count})")
            return True

        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] WARNING: Browser hard refresh failed: {e}")
            return False

    def get_time_until_refresh(self):
        """Get remaining time until next refresh in seconds"""
        elapsed = time.time() - self.last_refresh_time
        remaining = max(0, self.refresh_interval - elapsed)
        return remaining

    def get_time_until_refresh_minutes(self):
        """Get remaining time until next refresh in minutes"""
        return self.get_time_until_refresh() / 60

    def get_refresh_status(self):
        """Get current refresh status"""
        remaining = self.get_time_until_refresh_minutes()
        return {
            'last_refresh': datetime.fromtimestamp(self.last_refresh_time).isoformat(),
            'next_refresh_in_minutes': round(remaining, 2),
            'total_refreshes': self.refresh_count,
            'refresh_interval_minutes': self.refresh_interval / 60
        }
