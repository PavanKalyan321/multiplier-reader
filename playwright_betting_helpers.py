"""
Playwright Betting Helpers - Validation functions for Playwright-based betting operations
Adapted from betting_helpers.py with DOM-based verification instead of OCR/coordinates
"""

import asyncio
import re
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

try:
    from playwright.async_api import Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class PlaywrightBettingValidator:
    """Validate betting operations using Playwright DOM access"""

    def __init__(self, page: 'Page', config: Dict[str, Any]):
        """
        Initialize validator

        Args:
            page: Playwright page object
            config: Configuration with selectors
        """
        self.page = page
        self.config = config
        self.selectors = config.get('selectors', {})
        self.validation_history = []

    async def verify_bet_placed(self, panel: int = 1) -> Tuple[bool, str]:
        """
        Verify bet was actually placed by checking button state.

        Args:
            panel: Bet panel number (1 or 2)

        Returns:
            Tuple (bool, str): (is_placed, button_text/status)
        """
        try:
            selector = self.selectors.get(f'bet_button_{panel}',
                f'[data-testid="button-place-bet-{panel}"]')

            button_text = await self.page.locator(selector).text_content()

            if not button_text:
                return False, "NO_TEXT"

            button_text = button_text.lower()

            # If button shows "place bet", bet is NOT placed
            if 'place bet' in button_text:
                return False, button_text

            # If button shows "cancel" or "cash out", bet IS placed
            if 'cancel' in button_text or 'cash' in button_text:
                return True, button_text

            return False, button_text

        except Exception as e:
            return False, f"ERROR: {e}"

    async def verify_bet_is_active(self, panel: int = 1) -> bool:
        """
        Check if bet is currently active.

        Args:
            panel: Bet panel number (1 or 2)

        Returns:
            bool: True if bet is active, False otherwise
        """
        try:
            print(f"  🔍 Verifying active bet (panel {panel})...")

            # Check if cashout button is visible (indicates active bet)
            cashout_selector = self.selectors.get(f'cashout_button_{panel}',
                f'[data-testid="button-cashout-{panel}"]')

            cashout_text = await self.page.locator(cashout_selector).text_content()

            if cashout_text and 'cash' in cashout_text.lower():
                return True

            # Fallback: check bet button state
            bet_is_placed, _ = await self.verify_bet_placed(panel)
            return bet_is_placed

        except Exception as e:
            print(f"  ❌ Error verifying active bet: {e}")
            return False

    async def place_bet_with_verification(self, panel: int = 1, retries: int = 3) -> Tuple[bool, str]:
        """
        Place bet with verification.

        Args:
            panel: Bet panel number (1 or 2)
            retries: Number of retries if verification fails

        Returns:
            Tuple (bool, str): (success, reason)
        """
        try:
            from playwright_game_actions import PlaywrightGameActions

            actions = PlaywrightGameActions(self.page, self.config)

            # Try to click bet button multiple times with verification
            for attempt in range(retries):
                print(f"  [Attempt {attempt + 1}/{retries}] Placing bet...")

                # Click the button
                click_success = await actions.click_bet_button(panel=panel, retries=1)

                if not click_success:
                    print(f"  ⚠️ Click attempt {attempt + 1} failed")
                    await asyncio.sleep(0.3)
                    continue

                # Wait for button state to change
                await asyncio.sleep(0.4)

                # Verify it placed
                is_placed, button_text = await self.verify_bet_placed(panel)

                if is_placed:
                    print(f"  ✅ Bet confirmed (Panel {panel})")
                    self.validation_history.append({
                        'timestamp': datetime.now(),
                        'action': 'place_bet',
                        'panel': panel,
                        'success': True,
                        'button_text': button_text
                    })
                    return True, "SUCCESS"

                if attempt < retries - 1:
                    print(f"  ⚠️ Retry {attempt + 1}/{retries}...")
                    await asyncio.sleep(0.2)

            print(f"  ❌ Bet verification failed after {retries} attempts")
            return False, "FAILED_VERIFICATION"

        except Exception as e:
            return False, f"ERROR: {e}"

    async def verify_balance_changed(self, initial_balance: float, panel: int = 1) -> Tuple[bool, float, str]:
        """
        Verify that balance changed after cashout.

        Args:
            initial_balance: Balance before cashout
            panel: Bet panel number

        Returns:
            Tuple (bool, float, str): (changed, new_balance, reason)
        """
        try:
            from playwright_game_reader import PlaywrightGameReader

            reader = PlaywrightGameReader(self.page, self.config)

            # Wait a bit for balance to update
            await asyncio.sleep(0.5)

            # Read new balance
            new_balance = await reader.read_balance()

            if new_balance is None:
                return False, initial_balance, "COULD_NOT_READ_BALANCE"

            # Check if balance increased (profit) or decreased (loss)
            balance_diff = new_balance - initial_balance

            if balance_diff > 0:
                self.validation_history.append({
                    'timestamp': datetime.now(),
                    'action': 'verify_balance',
                    'initial': initial_balance,
                    'final': new_balance,
                    'difference': balance_diff,
                    'success': True
                })
                return True, new_balance, f"PROFIT ({balance_diff:.2f})"

            elif balance_diff < 0:
                return True, new_balance, f"LOSS ({balance_diff:.2f})"

            else:
                return False, new_balance, "NO_CHANGE"

        except Exception as e:
            return False, initial_balance, f"ERROR: {e}"

    async def verify_cashout_completed(self, panel: int = 1) -> Tuple[bool, str]:
        """
        Verify that cashout was completed by checking button state.

        Args:
            panel: Bet panel number

        Returns:
            Tuple (bool, str): (success, reason)
        """
        try:
            # After cashout, bet button should show "place bet" again
            is_placed, button_text = await self.verify_bet_placed(panel)

            if not is_placed:
                # Button shows "place bet", meaning bet was closed/cashed out
                self.validation_history.append({
                    'timestamp': datetime.now(),
                    'action': 'cashout_verified',
                    'panel': panel,
                    'success': True,
                    'button_text': button_text
                })
                return True, "BET_CLOSED"

            else:
                # Bet is still active
                return False, "BET_STILL_ACTIVE"

        except Exception as e:
            return False, f"ERROR: {e}"

    async def set_bet_amount_verified(self, amount: float, panel: int = 1) -> Tuple[bool, float]:
        """
        Set bet amount and verify it was set.

        Args:
            amount: Amount to set
            panel: Bet panel number

        Returns:
            Tuple (bool, float): (success, verified_amount)
        """
        try:
            from playwright_game_actions import PlaywrightGameActions

            actions = PlaywrightGameActions(self.page, self.config)

            # Set the amount
            success = await actions.set_bet_amount(amount, panel=panel)

            if not success:
                return False, 0.0

            # Wait for input to process
            await asyncio.sleep(0.3)

            # Read back the value to verify
            selector = self.selectors.get(f'bet_amount_input_{panel}',
                f'[data-testid="bet-input-amount-{panel}"] input')

            input_value = await self.page.locator(selector).input_value()

            if input_value:
                try:
                    verified_amount = float(input_value)

                    # Allow small variance due to formatting
                    if abs(verified_amount - amount) < 1.0:
                        self.validation_history.append({
                            'timestamp': datetime.now(),
                            'action': 'set_amount',
                            'requested': amount,
                            'verified': verified_amount,
                            'success': True
                        })
                        return True, verified_amount

                except ValueError:
                    pass

            return False, 0.0

        except Exception as e:
            print(f"  ❌ Error setting bet amount: {e}")
            return False, 0.0

    async def get_current_multiplier(self) -> Optional[float]:
        """
        Get current game multiplier.

        Returns:
            float: Current multiplier or None if not available
        """
        try:
            from playwright_game_reader import PlaywrightGameReader

            reader = PlaywrightGameReader(self.page, self.config)
            return await reader.read_multiplier()

        except Exception as e:
            print(f"  ❌ Error reading multiplier: {e}")
            return None

    async def get_current_balance(self) -> Optional[float]:
        """
        Get current balance.

        Returns:
            float: Current balance or None if not available
        """
        try:
            from playwright_game_reader import PlaywrightGameReader

            reader = PlaywrightGameReader(self.page, self.config)
            return await reader.read_balance()

        except Exception as e:
            print(f"  ❌ Error reading balance: {e}")
            return None

    async def get_game_status(self) -> str:
        """
        Get current game status.

        Returns:
            str: Game status ('WAITING', 'RUNNING', 'STARTING', 'UNKNOWN')
        """
        try:
            from playwright_game_reader import PlaywrightGameReader

            reader = PlaywrightGameReader(self.page, self.config)
            return await reader.get_game_status()

        except Exception as e:
            print(f"  ❌ Error getting status: {e}")
            return "UNKNOWN"

    async def validate_bet_placement_flow(self, amount: float, panel: int = 1) -> Dict[str, Any]:
        """
        Complete validation flow for betting: set amount, place bet, verify.

        Args:
            amount: Bet amount
            panel: Bet panel number

        Returns:
            Dict with validation results
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        result = {
            'timestamp': timestamp,
            'panel': panel,
            'amount': amount,
            'steps': [],
            'success': False
        }

        try:
            print(f"\n[{timestamp}] Starting bet placement validation (Panel {panel})...")

            # Step 1: Set bet amount
            print(f"[{timestamp}] STEP 1: Setting bet amount to {amount}...")
            amount_success, verified_amount = await self.set_bet_amount_verified(amount, panel)

            result['steps'].append({
                'step': 'set_amount',
                'success': amount_success,
                'requested': amount,
                'verified': verified_amount
            })

            if not amount_success:
                print(f"[{timestamp}] ❌ Failed to set bet amount")
                return result

            print(f"[{timestamp}] ✅ Bet amount set to {verified_amount}")

            # Step 2: Place bet
            print(f"[{timestamp}] STEP 2: Placing bet...")
            bet_success, reason = await self.place_bet_with_verification(panel, retries=3)

            result['steps'].append({
                'step': 'place_bet',
                'success': bet_success,
                'reason': reason
            })

            if not bet_success:
                print(f"[{timestamp}] ❌ Failed to place bet: {reason}")
                return result

            print(f"[{timestamp}] ✅ Bet placed successfully")

            # Step 3: Verify bet is active
            print(f"[{timestamp}] STEP 3: Verifying bet is active...")
            is_active = await self.verify_bet_is_active(panel)

            result['steps'].append({
                'step': 'verify_active',
                'success': is_active
            })

            if is_active:
                print(f"[{timestamp}] ✅ Bet is active")
                result['success'] = True
            else:
                print(f"[{timestamp}] ⚠️ Could not verify bet is active")

            return result

        except Exception as e:
            print(f"[{timestamp}] ❌ Validation flow error: {e}")
            result['error'] = str(e)
            return result

    async def validate_cashout_flow(self, panel: int = 1) -> Dict[str, Any]:
        """
        Complete validation flow for cashout: click, verify, check balance.

        Args:
            panel: Bet panel number

        Returns:
            Dict with validation results
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        result = {
            'timestamp': timestamp,
            'panel': panel,
            'steps': [],
            'success': False
        }

        try:
            print(f"\n[{timestamp}] Starting cashout validation (Panel {panel})...")

            # Step 1: Get initial balance
            print(f"[{timestamp}] STEP 1: Reading initial balance...")
            initial_balance = await self.get_current_balance()

            if initial_balance is None:
                print(f"[{timestamp}] ❌ Could not read balance")
                return result

            result['steps'].append({
                'step': 'read_balance',
                'success': True,
                'balance': initial_balance
            })

            print(f"[{timestamp}] Initial balance: {initial_balance:.2f}")

            # Step 2: Click cashout
            print(f"[{timestamp}] STEP 2: Clicking cashout button...")
            from playwright_game_actions import PlaywrightGameActions

            actions = PlaywrightGameActions(self.page, self.config)
            click_success = await actions.click_cashout_button(panel=panel, retries=1)

            result['steps'].append({
                'step': 'click_cashout',
                'success': click_success
            })

            if not click_success:
                print(f"[{timestamp}] ❌ Failed to click cashout")
                return result

            print(f"[{timestamp}] ✅ Cashout button clicked")

            # Step 3: Verify cashout completed
            print(f"[{timestamp}] STEP 3: Verifying cashout completed...")
            cashout_completed, completion_reason = await self.verify_cashout_completed(panel)

            result['steps'].append({
                'step': 'verify_cashout',
                'success': cashout_completed,
                'reason': completion_reason
            })

            print(f"[{timestamp}] Cashout verification: {completion_reason}")

            # Step 4: Verify balance changed
            print(f"[{timestamp}] STEP 4: Verifying balance change...")
            balance_changed, new_balance, balance_reason = await self.verify_balance_changed(
                initial_balance, panel
            )

            result['steps'].append({
                'step': 'verify_balance',
                'success': balance_changed,
                'initial': initial_balance,
                'final': new_balance,
                'reason': balance_reason
            })

            print(f"[{timestamp}] Balance change: {initial_balance:.2f} → {new_balance:.2f} ({balance_reason})")

            # Overall success
            if click_success and cashout_completed:
                result['success'] = True
                print(f"[{timestamp}] ✅ Cashout validation successful")
            else:
                print(f"[{timestamp}] ⚠️ Cashout validation incomplete")

            result['final_balance'] = new_balance

            return result

        except Exception as e:
            print(f"[{timestamp}] ❌ Cashout flow error: {e}")
            result['error'] = str(e)
            return result

    def get_validation_history(self) -> list:
        """Get all validation history"""
        return self.validation_history.copy()

    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of validation operations"""
        successful = len([v for v in self.validation_history if v.get('success')])
        failed = len(self.validation_history) - successful

        return {
            'total_validations': len(self.validation_history),
            'successful': successful,
            'failed': failed,
            'success_rate': successful / max(1, len(self.validation_history)) * 100,
            'operations': {}
        }

    def reset_history(self):
        """Reset validation history"""
        self.validation_history = []


# Example usage
if __name__ == "__main__":
    async def test_validators():
        """Test validation functions"""
        from playwright_browser import create_browser_manager
        from playwright_config import PlaywrightConfig

        config = PlaywrightConfig().load()
        manager = await create_browser_manager(config, headless=False)

        if manager:
            page = manager.get_page()
            validator = PlaywrightBettingValidator(page, config)

            print("Testing validators...")

            # Test balance reading
            balance = await validator.get_current_balance()
            print(f"Current balance: {balance}")

            # Test status reading
            status = await validator.get_game_status()
            print(f"Game status: {status}")

            # Test multiplier reading
            mult = await validator.get_current_multiplier()
            print(f"Current multiplier: {mult}")

            # Get validation summary
            summary = validator.get_validation_summary()
            print(f"Validation summary: {summary}")

            await manager.close_session()

    asyncio.run(test_validators())
