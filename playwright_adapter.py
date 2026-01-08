"""
Playwright Adapter - Drop-in replacements for OCR-based modules
Provides backward-compatible API for existing code
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

try:
    from playwright.async_api import Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from playwright_game_reader import PlaywrightGameReader
from playwright_game_actions import PlaywrightGameActions


class PlaywrightMultiplierReader:
    """
    Drop-in replacement for multiplier_reader.py
    Uses Playwright instead of OCR
    """

    def __init__(self, page: 'Page', config: Dict[str, Any]):
        """
        Initialize multiplier reader

        Args:
            page: Playwright page object
            config: Configuration dict
        """
        self.reader = PlaywrightGameReader(page, config)
        self.page = page
        self.config = config

    async def read_multiplier(self) -> Optional[float]:
        """
        Read current multiplier

        Returns:
            Multiplier value or None
        """
        return await self.reader.read_multiplier()

    async def get_multiplier_with_status(self) -> Dict[str, Any]:
        """
        Get multiplier with game status

        Returns:
            Dict with multiplier, status, timestamp
        """
        return await self.reader.get_multiplier_with_status()

    def get_last_multiplier(self) -> float:
        """Get last read multiplier"""
        return self.reader.get_last_multiplier()

    def get_status(self) -> str:
        """Get current game status"""
        return self.reader.get_current_status()

    # Compatibility methods for old API
    def capture_and_read(self) -> Optional[Dict[str, Any]]:
        """Legacy method - not async"""
        raise NotImplementedError("Use async method get_multiplier_with_status() instead")


class PlaywrightBalanceReader:
    """
    Drop-in replacement for balance_reader.py
    Uses Playwright instead of OCR
    """

    def __init__(self, page: 'Page', config: Dict[str, Any]):
        """
        Initialize balance reader

        Args:
            page: Playwright page object
            config: Configuration dict
        """
        self.reader = PlaywrightGameReader(page, config)
        self.page = page
        self.config = config

    async def read_balance(self) -> Optional[float]:
        """
        Read current balance

        Returns:
            Balance value or None
        """
        return await self.reader.read_balance()

    async def get_balance_with_status(self) -> Dict[str, Any]:
        """
        Get balance with status

        Returns:
            Dict with balance, status, timestamp
        """
        balance = await self.read_balance()
        status = 'NORMAL'

        if balance is None:
            status = 'ERROR'
        elif balance == 0:
            status = 'ZERO'
        elif balance < 10:
            status = 'VERY_LOW'
        elif balance < 50:
            status = 'LOW'
        elif balance > 1000:
            status = 'HIGH'

        return {
            'balance': balance,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }

    def get_last_balance(self) -> float:
        """Get last read balance"""
        return self.reader.get_last_balance()

    # Compatibility methods
    def capture_and_read(self) -> Optional[float]:
        """Legacy method - not async"""
        raise NotImplementedError("Use async method read_balance() instead")


class PlaywrightGameActionsAdapter:
    """
    Drop-in replacement for game_actions.py
    Uses Playwright instead of PyAutoGUI
    """

    def __init__(self, page: 'Page', config: Dict[str, Any]):
        """
        Initialize game actions

        Args:
            page: Playwright page object
            config: Configuration dict
        """
        self.actions = PlaywrightGameActions(page, config)
        self.page = page
        self.config = config

    async def click_bet_button(self, panel: int = 1) -> bool:
        """
        Click bet button

        Args:
            panel: Bet panel (1 or 2)

        Returns:
            True if successful
        """
        return await self.actions.click_bet_button(panel)

    async def click_cashout_button(self, panel: int = 1) -> bool:
        """
        Click cashout button

        Args:
            panel: Bet panel (1 or 2)

        Returns:
            True if successful
        """
        return await self.actions.click_cashout_button(panel)

    async def wait_for_round_end(self, timeout: float = 60) -> bool:
        """
        Wait for round to end

        Args:
            timeout: Maximum wait time in seconds

        Returns:
            True if round ended
        """
        return await self.actions.wait_for_bet_button_available(timeout=timeout)

    async def is_bet_button_ready(self) -> bool:
        """Check if bet button is clickable"""
        return await self.actions.is_button_clickable(1)

    async def get_button_state(self) -> Optional[str]:
        """Get button text"""
        return await self.actions.get_button_state(1)

    # Compatibility methods
    def safe_click(self, x: int, y: int) -> bool:
        """Legacy coordinate-based click - not supported"""
        raise NotImplementedError("Use async method click_bet_button() instead")


class PlaywrightGameController:
    """
    Complete game controller combining reader + actions
    Coordinates between multiplier reading and betting
    """

    def __init__(self, page: 'Page', config: Dict[str, Any]):
        """
        Initialize game controller

        Args:
            page: Playwright page object
            config: Configuration dict
        """
        self.page = page
        self.config = config
        self.reader = PlaywrightGameReader(page, config)
        self.actions = PlaywrightGameActions(page, config)
        self.current_round_id = 0
        self.session_stats = {
            'rounds_played': 0,
            'total_profit': 0,
            'total_loss': 0,
            'wins': 0,
            'losses': 0,
        }

    async def place_bet(self, amount: float, panel: int = 1) -> bool:
        """
        Place a bet

        Args:
            amount: Amount to bet
            panel: Bet panel

        Returns:
            True if successful
        """
        # Set amount
        success = await self.actions.set_bet_amount(amount, panel)
        if not success:
            return False

        # Click bet button
        return await self.actions.click_bet_button(panel)

    async def monitor_round(self) -> Dict[str, Any]:
        """
        Monitor a round from start to finish

        Returns:
            Dict with round data (multiplier, status, etc.)
        """
        # Wait for round to start
        started = await self.actions.wait_for_cashout_button_available(timeout=30)

        if not started:
            return {'error': 'Round did not start'}

        # Monitor multiplier until round ends
        multiplier = 0.0

        while True:
            current_mult = await self.reader.read_multiplier()

            if current_mult:
                multiplier = current_mult

            # Check if round ended
            status = await self.reader.get_game_status()

            if status == 'WAITING':
                break

            await asyncio.sleep(0.05)

        return {
            'round_id': self.current_round_id,
            'multiplier': multiplier,
            'completed': True,
            'timestamp': datetime.now().isoformat()
        }

    async def cashout(self, panel: int = 1) -> bool:
        """
        Execute cashout

        Args:
            panel: Bet panel

        Returns:
            True if successful
        """
        return await self.actions.click_cashout_button(panel)

    async def wait_for_next_round(self, timeout: float = 60) -> bool:
        """
        Wait for next round to become available

        Args:
            timeout: Maximum wait time

        Returns:
            True if ready
        """
        return await self.actions.wait_for_bet_button_available(timeout=timeout)

    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        return self.session_stats.copy()

    def update_session_stats(self, profit: float, loss: float, won: bool):
        """Update session statistics"""
        self.session_stats['rounds_played'] += 1
        self.session_stats['total_profit'] += profit
        self.session_stats['total_loss'] += loss

        if won:
            self.session_stats['wins'] += 1
        else:
            self.session_stats['losses'] += 1

    def reset_session_stats(self):
        """Reset session statistics"""
        self.session_stats = {
            'rounds_played': 0,
            'total_profit': 0,
            'total_loss': 0,
            'wins': 0,
            'losses': 0,
        }


# Example usage
if __name__ == "__main__":
    async def test_adapters():
        """Test adapters"""
        from playwright_browser import create_browser_manager

        config = {
            'game_url': 'https://example.com/aviator',
            'selectors': {
                'multiplier': '.game-score .game-score-char',
                'balance': '.header-balance .text-subheading-3',
                'bet_button_1': '[data-testid="button-place-bet-1"]'
            }
        }

        manager = await create_browser_manager(config, headless=False)

        if manager:
            page = manager.get_page()

            # Test adapters
            multiplier_reader = PlaywrightMultiplierReader(page, config)
            balance_reader = PlaywrightBalanceReader(page, config)
            actions_adapter = PlaywrightGameActionsAdapter(page, config)

            print("Testing adapters...")

            # Read multiplier
            mult = await multiplier_reader.read_multiplier()
            print(f"Multiplier: {mult}")

            # Read balance
            balance = await balance_reader.read_balance()
            print(f"Balance: {balance}")

            # Check button state
            state = await actions_adapter.get_button_state()
            print(f"Button state: {state}")

            await manager.close_session()

    asyncio.run(test_adapters())
