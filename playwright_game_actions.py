"""
Playwright Game Actions - Betting and cashout operations
Click bet/cashout buttons and manage game interactions
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

try:
    from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class PlaywrightGameActions:
    """Manage game interactions: betting, cashout, etc."""

    def __init__(self, page: 'Page', config: Dict[str, Any]):
        """
        Initialize game actions

        Args:
            page: Playwright page object
            config: Configuration with selectors
        """
        self.page = page
        self.config = config
        self.selectors = config.get('selectors', {})
        self.last_bet_panel = 1
        self.click_count = 0
        self.failed_clicks = 0

    async def click_bet_button(self, panel: int = 1, retries: int = 3) -> bool:
        """
        Click the bet button

        Args:
            panel: Bet panel number (1 or 2)
            retries: Number of retries if click fails

        Returns:
            True if successful, False otherwise
        """
        for attempt in range(retries):
            try:
                selector = self.selectors.get(f'bet_button_{panel}',
                    f'[data-testid="button-place-bet-{panel}"]')

                # Wait for button to be visible
                await self.page.wait_for_selector(selector, state='visible', timeout=5000)

                # Verify button shows "Place bet"
                button_text = await self.page.locator(selector).text_content()

                if not button_text or 'place bet' not in button_text.lower():
                    print(f"[WARN] Bet button text not 'Place bet': {button_text}")
                    await asyncio.sleep(0.5)
                    continue

                # Click with human-like delay
                await asyncio.sleep(0.1)  # 100ms delay
                await self.page.locator(selector).click()

                await asyncio.sleep(0.2)  # 200ms wait after click

                self.last_bet_panel = panel
                self.click_count += 1

                print(f"[OK] Bet button clicked (panel {panel}, attempt {attempt + 1})")
                return True

            except PlaywrightTimeoutError:
                print(f"[WARN] Bet button not found (attempt {attempt + 1}/{retries})")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"[ERROR] Bet click failed (attempt {attempt + 1}/{retries}): {e}")
                await asyncio.sleep(0.5)

        self.failed_clicks += 1
        print(f"[ERROR] Failed to click bet button after {retries} retries")
        return False

    async def click_cashout_button(self, panel: int = 1, retries: int = 3) -> bool:
        """
        Click the cashout button (same as bet button but different state)

        Args:
            panel: Bet panel number (1 or 2)
            retries: Number of retries if click fails

        Returns:
            True if successful, False otherwise
        """
        for attempt in range(retries):
            try:
                selector = self.selectors.get(f'bet_button_{panel}',
                    f'[data-testid="button-place-bet-{panel}"]')

                # Wait for button to be visible
                await self.page.wait_for_selector(selector, state='visible', timeout=1000)

                # Verify button shows "Cash out"
                button_text = await self.page.locator(selector).text_content()

                if not button_text or 'cash out' not in button_text.lower():
                    print(f"[WARN] Cashout button not ready: {button_text}")
                    await asyncio.sleep(0.2)
                    continue

                # Click with human-like delay
                await asyncio.sleep(0.05)  # 50ms delay
                await self.page.locator(selector).click()

                await asyncio.sleep(0.2)  # 200ms wait after click

                self.click_count += 1

                print(f"[OK] Cashout button clicked (panel {panel})")
                return True

            except PlaywrightTimeoutError:
                print(f"[WARN] Cashout button not ready (attempt {attempt + 1}/{retries})")
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"[ERROR] Cashout click failed (attempt {attempt + 1}/{retries}): {e}")
                await asyncio.sleep(0.1)

        self.failed_clicks += 1
        print(f"[ERROR] Failed to click cashout button after {retries} retries")
        return False

    async def wait_for_bet_button_available(self, panel: int = 1, timeout: float = 30) -> bool:
        """
        Wait for bet button to become available (status = WAITING)

        Args:
            panel: Bet panel number (1 or 2)
            timeout: Maximum wait time in seconds

        Returns:
            True if button available, False if timeout
        """
        try:
            selector = self.selectors.get(f'bet_button_{panel}',
                f'[data-testid="button-place-bet-{panel}"]')

            await self.page.wait_for_function(
                f"""() => {{
                    const btn = document.querySelector('{selector}');
                    return btn && btn.textContent.toLowerCase().includes('place bet');
                }}""",
                timeout=int(timeout * 1000)
            )

            print(f"[OK] Bet button is available (panel {panel})")
            return True

        except PlaywrightTimeoutError:
            print(f"[WARN] Timeout waiting for bet button (panel {panel})")
            return False
        except Exception as e:
            print(f"[ERROR] Error waiting for bet button: {e}")
            return False

    async def wait_for_cashout_button_available(self, panel: int = 1, timeout: float = 30) -> bool:
        """
        Wait for cashout button to become available (status = RUNNING)

        Args:
            panel: Bet panel number (1 or 2)
            timeout: Maximum wait time in seconds

        Returns:
            True if button available, False if timeout
        """
        try:
            selector = self.selectors.get(f'bet_button_{panel}',
                f'[data-testid="button-place-bet-{panel}"]')

            await self.page.wait_for_function(
                f"""() => {{
                    const btn = document.querySelector('{selector}');
                    return btn && btn.textContent.toLowerCase().includes('cash out');
                }}""",
                timeout=int(timeout * 1000)
            )

            print(f"[OK] Cashout button is available (panel {panel})")
            return True

        except PlaywrightTimeoutError:
            print(f"[WARN] Timeout waiting for cashout button (panel {panel})")
            return False
        except Exception as e:
            print(f"[ERROR] Error waiting for cashout button: {e}")
            return False

    async def is_button_clickable(self, panel: int = 1) -> bool:
        """
        Check if bet button is currently clickable

        Args:
            panel: Bet panel number (1 or 2)

        Returns:
            True if clickable, False otherwise
        """
        try:
            selector = self.selectors.get(f'bet_button_{panel}',
                f'[data-testid="button-place-bet-{panel}"]')

            button = self.page.locator(selector)
            is_visible = await button.is_visible()
            is_enabled = await button.is_enabled()

            return is_visible and is_enabled

        except Exception as e:
            print(f"[ERROR] Error checking button state: {e}")
            return False

    async def get_button_state(self, panel: int = 1) -> Optional[str]:
        """
        Get current button state/text

        Args:
            panel: Bet panel number (1 or 2)

        Returns:
            Button text or None if error
        """
        try:
            selector = self.selectors.get(f'bet_button_{panel}',
                f'[data-testid="button-place-bet-{panel}"]')

            text = await self.page.locator(selector).text_content()
            return text.strip() if text else None

        except Exception as e:
            print(f"[ERROR] Error getting button state: {e}")
            return None

    async def set_bet_amount(self, amount: float, panel: int = 1) -> bool:
        """
        Set bet amount in the input field

        Args:
            amount: Amount to bet
            panel: Bet panel number (1 or 2)

        Returns:
            True if successful, False otherwise
        """
        try:
            selector = self.selectors.get(f'bet_amount_input_{panel}',
                f'[data-testid="bet-input-amount-{panel}"] input')

            input_field = self.page.locator(selector)

            # Clear existing value
            await input_field.clear()
            await asyncio.sleep(0.1)

            # Type new amount
            await input_field.type(str(amount), delay=50)  # Human-like typing
            await asyncio.sleep(0.2)

            print(f"[OK] Set bet amount to {amount} (panel {panel})")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to set bet amount: {e}")
            return False

    def get_click_statistics(self) -> Dict[str, int]:
        """Get click statistics"""
        return {
            'total_clicks': self.click_count,
            'failed_clicks': self.failed_clicks,
            'success_rate': (self.click_count - self.failed_clicks) / max(1, self.click_count)
        }

    def reset_statistics(self):
        """Reset click statistics"""
        self.click_count = 0
        self.failed_clicks = 0


# Example usage
if __name__ == "__main__":
    async def test_actions():
        """Test game actions"""
        from playwright_browser import create_browser_manager

        config = {
            'game_url': 'https://example.com/aviator',
            'selectors': {
                'bet_button_1': '[data-testid="button-place-bet-1"]',
                'cashout_button_1': '[data-testid="button-place-bet-1"]',
            }
        }

        manager = await create_browser_manager(config, headless=False)

        if manager:
            page = manager.get_page()
            actions = PlaywrightGameActions(page, config)

            print("Testing game actions...")

            # Check button state
            state = await actions.get_button_state(1)
            print(f"Button state: {state}")

            # Wait for bet button
            available = await actions.wait_for_bet_button_available(1, timeout=10)
            print(f"Bet button available: {available}")

            await manager.close_session()

    asyncio.run(test_actions())
