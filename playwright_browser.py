"""
Playwright Browser Manager - Browser initialization and session management
Handles browser launch, login flow, session persistence, and anti-detection
"""

import os
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
    from playwright_stealth import stealth
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class PlaywrightBrowserManager:
    """Manages Playwright browser instance with anti-detection measures"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize browser manager

        Args:
            config: Configuration dict with browser settings
        """
        self.config = config
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.auth_state_file = "auth_state.json"
        self.is_connected = False

    async def initialize(self, headless: bool = False) -> Optional[Page]:
        """
        Initialize and launch browser

        Args:
            headless: Whether to run in headless mode

        Returns:
            Playwright page object or None if failed
        """
        if not PLAYWRIGHT_AVAILABLE:
            print("[ERROR] Playwright not installed. Run: pip install playwright playwright-stealth")
            return None

        try:
            print("[INFO] Initializing Playwright browser...")

            # Start Playwright
            self.playwright = await async_playwright().start()

            # Launch browser with anti-detection settings
            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-first-run',
                    '--no-default-browser-check',
                ]
            )

            # Browser context with anti-detection
            context_kwargs = {
                'user_agent': self.config.get('user_agent',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                    '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'),
                'viewport': {
                    'width': self.config.get('viewport_width', 1920),
                    'height': self.config.get('viewport_height', 1080)
                },
                'locale': 'en-US',
                'timezone_id': 'America/New_York',
                'permissions': ['geolocation'],
            }

            # Restore session if exists
            if os.path.exists(self.auth_state_file):
                print("[INFO] Restoring saved session...")
                context_kwargs['storage_state'] = self.auth_state_file

            self.context = await self.browser.new_context(**context_kwargs)

            # Create page
            self.page = await self.context.new_page()

            # Apply stealth mode to avoid detection
            await stealth(self.page)

            # Set reasonable timeout
            self.page.set_default_timeout(30000)  # 30 seconds

            self.is_connected = True
            print("[OK] Browser initialized successfully")

            return self.page

        except Exception as e:
            print(f"[ERROR] Failed to initialize browser: {e}")
            await self.cleanup()
            return None

    async def navigate_to_game(self, game_url: str) -> bool:
        """
        Navigate to game URL

        Args:
            game_url: URL of the game

        Returns:
            True if successful, False otherwise
        """
        if not self.page:
            print("[ERROR] Browser not initialized")
            return False

        try:
            print(f"[INFO] Navigating to {game_url}...")
            await self.page.goto(game_url, wait_until='networkidle')
            await asyncio.sleep(2)  # Wait for page to load fully
            print("[OK] Successfully navigated to game")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to navigate: {e}")
            self.is_connected = False
            return False

    async def save_session_state(self) -> bool:
        """
        Save browser session (cookies, localStorage) for later restoration

        Returns:
            True if successful, False otherwise
        """
        if not self.context:
            print("[ERROR] No browser context to save")
            return False

        try:
            storage_state = await self.context.storage_state()
            with open(self.auth_state_file, 'w') as f:
                json.dump(storage_state, f, indent=2)
            print(f"[OK] Session saved to {self.auth_state_file}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save session: {e}")
            return False

    async def close_session(self) -> bool:
        """
        Save session and close browser

        Returns:
            True if successful
        """
        try:
            # Save session before closing
            await self.save_session_state()

            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()

            self.is_connected = False
            print("[OK] Browser closed successfully")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to close browser: {e}")
            return False

    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            self.is_connected = False
        except Exception as e:
            print(f"[WARN] Cleanup error: {e}")

    async def reconnect(self) -> bool:
        """
        Reconnect to browser if connection lost

        Returns:
            True if reconnected, False otherwise
        """
        try:
            print("[INFO] Attempting to reconnect...")
            await self.cleanup()
            await asyncio.sleep(1)

            game_url = self.config.get('game_url')
            if not game_url:
                print("[ERROR] No game URL configured")
                return False

            page = await self.initialize(headless=self.config.get('headless', False))
            if page:
                return await self.navigate_to_game(game_url)
            return False
        except Exception as e:
            print(f"[ERROR] Reconnection failed: {e}")
            return False

    async def check_connection(self) -> bool:
        """
        Check if browser is still connected

        Returns:
            True if connected and responsive, False otherwise
        """
        if not self.page or not self.is_connected:
            return False

        try:
            # Simple check: evaluate JavaScript
            result = await self.page.evaluate('1+1')
            return result == 2
        except Exception:
            self.is_connected = False
            return False

    async def refresh_page(self) -> bool:
        """
        Refresh the game page

        Returns:
            True if successful, False otherwise
        """
        if not self.page:
            print("[ERROR] No page to refresh")
            return False

        try:
            await self.page.reload(wait_until='networkidle')
            await asyncio.sleep(1)
            print("[OK] Page refreshed successfully")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to refresh page: {e}")
            self.is_connected = False
            return False

    def get_page(self) -> Optional[Page]:
        """Get current page object"""
        return self.page


async def create_browser_manager(config: Dict[str, Any], headless: bool = False) -> Optional[PlaywrightBrowserManager]:
    """
    Helper function to create and initialize browser manager

    Args:
        config: Browser configuration
        headless: Whether to run headless

    Returns:
        Initialized PlaywrightBrowserManager or None
    """
    manager = PlaywrightBrowserManager(config)
    page = await manager.initialize(headless=headless)

    if not page:
        return None

    game_url = config.get('game_url')
    if game_url and not await manager.navigate_to_game(game_url):
        await manager.cleanup()
        return None

    return manager


# Example usage
if __name__ == "__main__":
    async def test_browser():
        """Test browser initialization"""
        config = {
            'game_url': 'https://example.com/aviator',
            'viewport_width': 1920,
            'viewport_height': 1080,
            'headless': False,
        }

        manager = await create_browser_manager(config, headless=False)

        if manager:
            print("Browser is running. Press Ctrl+C to exit...")
            try:
                await asyncio.sleep(10)
            except KeyboardInterrupt:
                print("Closing...")

            await manager.close_session()

    asyncio.run(test_browser())
