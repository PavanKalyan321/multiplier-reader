"""
Playwright Game Reader - Direct DOM access for game state reading
Reads multiplier, balance, and game status from HTML elements
"""

import asyncio
import re
from typing import Optional, Dict, Any, Callable
from datetime import datetime

try:
    from playwright.async_api import Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class PlaywrightGameReader:
    """Read game state directly from DOM"""

    def __init__(self, page: 'Page', config: Dict[str, Any]):
        """
        Initialize game reader

        Args:
            page: Playwright page object
            config: Configuration with selectors
        """
        self.page = page
        self.config = config
        self.selectors = config.get('selectors', {})
        self.last_multiplier = 0.0
        self.last_balance = 0.0
        self.game_status = 'UNKNOWN'

    async def read_multiplier(self) -> Optional[float]:
        """
        Read current multiplier from DOM
        Uses cashout button win amount if main selector fails

        Returns:
            Multiplier value or None if failed
        """
        try:
            # Method 1: Try main multiplier selector
            selector = self.selectors.get('multiplier', '.game-score .game-score-char')
            elements = await self.page.locator(selector).all()

            if elements and len(elements) > 0:
                # Get text from each element
                chars = []
                for element in elements:
                    text = await element.text_content()
                    if text:
                        chars.append(text.strip())

                # Join characters: ['2', '.', '8', '1', 'x'] -> '2.81x'
                mult_str = ''.join(chars)

                # Parse multiplier: '2.81x' -> 2.81
                mult_str = mult_str.replace('x', '').replace('X', '').strip()

                if mult_str:
                    try:
                        mult = float(mult_str)
                        self.last_multiplier = mult
                        return mult
                    except ValueError:
                        pass

            # Method 2: Extract from cashout button display value
            # The button shows winnings as "multiplier x bet_amount"
            # We need to calculate: winnings / bet_amount = multiplier
            try:
                cashout_selector = self.selectors.get('cashout_button_1', '[data-testid="button-cashout-1"]')

                # Get the bet-win-amount text from cashout button
                win_amount_elements = await self.page.locator(f'{cashout_selector} .bet-win-amount-char').all()

                if win_amount_elements and len(win_amount_elements) > 0:
                    # Extract digits from bet-win-amount-char elements
                    win_chars = []
                    for elem in win_amount_elements:
                        text = await elem.text_content()
                        if text:
                            win_chars.append(text.strip())

                    win_str = ''.join(win_chars)

                    # Parse: "11.30" -> 11.30
                    win_str = win_str.replace('x', '').strip()

                    if win_str and win_str != '':
                        try:
                            # The display shows total winnings, divide by bet amount to get multiplier
                            win_amount = float(win_str)
                            # Assuming default bet is 50
                            bet_amount = 50  # Can be made configurable
                            mult = win_amount / bet_amount

                            if mult > 0:
                                self.last_multiplier = mult
                                return mult
                        except (ValueError, ZeroDivisionError):
                            pass
            except Exception as e:
                pass  # Fallback method failed, continue

            # If both methods fail, return last known multiplier
            return self.last_multiplier if self.last_multiplier > 0 else None

        except Exception as e:
            print(f"[WARN] Failed to read multiplier: {e}")
            return self.last_multiplier if self.last_multiplier > 0 else None

    async def read_balance(self) -> Optional[float]:
        """
        Read current balance from DOM

        Returns:
            Balance value or None if failed
        """
        try:
            selector = self.selectors.get('balance', '.header-balance .text-subheading-3')

            balance_text = await self.page.locator(selector).text_content()

            if not balance_text:
                return None

            balance = self._parse_balance(balance_text)
            self.last_balance = balance
            return balance

        except Exception as e:
            print(f"[ERROR] Failed to read balance: {e}")
            return None

    async def get_game_status(self) -> str:
        """
        Detect game status from button state

        Returns:
            Game status: 'WAITING', 'RUNNING', 'STARTING', 'UNKNOWN'
        """
        try:
            # Try to get status from cashout button first (most reliable during game)
            cashout_selector = self.selectors.get('cashout_button_1', '[data-testid="button-cashout-1"]')

            try:
                cashout_button = await self.page.locator(cashout_selector).text_content()
                if cashout_button and 'cash out' in cashout_button.lower():
                    # If cashout button exists and says "Cash out", game is RUNNING
                    self.game_status = 'RUNNING'
                    return 'RUNNING'
            except:
                pass

            # Fallback: check bet button
            bet_selector = self.selectors.get('bet_button_1', '[data-testid="button-place-bet-1"]')
            button_text = await self.page.locator(bet_selector).text_content()

            if not button_text:
                return self.game_status  # Return last known status

            button_text = button_text.lower()

            if 'place bet' in button_text:
                status = 'WAITING'
            elif 'cash out' in button_text:
                status = 'RUNNING'
            elif 'cancel' in button_text or 'starting' in button_text:
                status = 'STARTING'
            else:
                status = 'UNKNOWN'

            self.game_status = status
            return status

        except Exception as e:
            print(f"[WARN] Failed to get game status: {e}")
            return self.game_status  # Return last known status instead of UNKNOWN

    async def get_multiplier_with_status(self) -> Dict[str, Any]:
        """
        Get multiplier and status in one call

        Returns:
            Dict with multiplier, status, timestamp
        """
        mult = await self.read_multiplier()
        status = await self.get_game_status()

        return {
            'multiplier': mult,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }

    async def wait_for_multiplier_change(self, timeout: float = 30) -> Optional[float]:
        """
        Wait for multiplier to change

        Args:
            timeout: Maximum wait time in seconds

        Returns:
            New multiplier value or None if timeout
        """
        try:
            selector = self.selectors.get('multiplier', '.game-score .game-score-char')
            initial_mult = await self.read_multiplier()

            # Wait for multiplier to change
            start_time = datetime.now()

            while True:
                elapsed = (datetime.now() - start_time).total_seconds()

                if elapsed > timeout:
                    return None

                current_mult = await self.read_multiplier()

                if current_mult and current_mult != initial_mult:
                    return current_mult

                await asyncio.sleep(0.05)  # Poll every 50ms

        except Exception as e:
            print(f"[ERROR] Wait for multiplier change failed: {e}")
            return None

    async def wait_for_round_start(self, timeout: float = 30) -> bool:
        """
        Wait for a new round to start (status changes to RUNNING)

        Args:
            timeout: Maximum wait time in seconds

        Returns:
            True if round started, False if timeout
        """
        try:
            start_time = datetime.now()

            while True:
                elapsed = (datetime.now() - start_time).total_seconds()

                if elapsed > timeout:
                    return False

                status = await self.get_game_status()

                if status == 'RUNNING':
                    return True

                await asyncio.sleep(0.1)

        except Exception as e:
            print(f"[ERROR] Wait for round start failed: {e}")
            return False

    async def wait_for_round_end(self, timeout: float = 60) -> bool:
        """
        Wait for round to end (status changes back to WAITING)

        Args:
            timeout: Maximum wait time in seconds

        Returns:
            True if round ended, False if timeout
        """
        try:
            start_time = datetime.now()

            while True:
                elapsed = (datetime.now() - start_time).total_seconds()

                if elapsed > timeout:
                    return False

                status = await self.get_game_status()

                if status == 'WAITING':
                    await asyncio.sleep(0.5)  # Small delay after status change
                    return True

                await asyncio.sleep(0.1)

        except Exception as e:
            print(f"[ERROR] Wait for round end failed: {e}")
            return False

    async def monitor_multiplier_stream(self, callback: Callable) -> None:
        """
        Monitor multiplier changes and call callback for each update

        Args:
            callback: Async function to call with (multiplier, status) on each update
        """
        try:
            last_mult = None

            while True:
                mult = await self.read_multiplier()
                status = await self.get_game_status()

                if mult != last_mult:
                    await callback(mult, status)
                    last_mult = mult

                await asyncio.sleep(0.05)  # Poll every 50ms

        except Exception as e:
            print(f"[ERROR] Monitor stream error: {e}")

    @staticmethod
    def _parse_balance(balance_text: str) -> float:
        """
        Parse balance from various formats

        Args:
            balance_text: Balance text (e.g., "2,979.7", "1.5k", "500")

        Returns:
            Parsed balance as float
        """
        try:
            # Remove whitespace
            balance_text = balance_text.strip()

            # Handle "k" suffix (1.5k = 1500)
            if 'k' in balance_text.lower():
                balance_text = balance_text.lower().replace('k', '')
                value = float(balance_text)
                return value * 1000

            # Remove commas (2,979.7 -> 2979.7)
            balance_text = balance_text.replace(',', '')

            return float(balance_text)

        except Exception as e:
            print(f"[WARN] Failed to parse balance '{balance_text}': {e}")
            return 0.0

    def get_last_multiplier(self) -> float:
        """Get last read multiplier"""
        return self.last_multiplier

    def get_last_balance(self) -> float:
        """Get last read balance"""
        return self.last_balance

    def get_current_status(self) -> str:
        """Get last detected game status"""
        return self.game_status


# Example usage
if __name__ == "__main__":
    async def test_reader():
        """Test game reader"""
        from playwright_browser import create_browser_manager

        config = {
            'game_url': 'https://example.com/aviator',
            'selectors': {
                'multiplier': '.game-score .game-score-char',
                'balance': '.header-balance .text-subheading-3',
                'bet_button': '[data-testid="button-place-bet-1"]'
            }
        }

        manager = await create_browser_manager(config, headless=False)

        if manager:
            page = manager.get_page()
            reader = PlaywrightGameReader(page, config)

            print("Reading game state...")

            for i in range(10):
                data = await reader.get_multiplier_with_status()
                print(f"[{i}] Multiplier: {data['multiplier']}, Status: {data['status']}")
                await asyncio.sleep(1)

            await manager.close_session()

    asyncio.run(test_reader())
