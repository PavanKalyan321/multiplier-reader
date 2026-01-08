"""Pure rules-based trader - bets and cashouts based ONLY on rules, no AI predictions"""

import asyncio
import time
import json
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

from supabase.client import AsyncClient
from multiplier_reader import MultiplierReader
from game_actions import GameActions
from screen_capture import ScreenCapture
from balance_reader import BalanceReader
from betting_rules_engine import BettingRulesEngine
import pyautogui


class RulesBasedTrader:
    """Purely rules-driven trader with no AI dependency"""

    def __init__(
        self,
        game_actions: GameActions,
        multiplier_reader: MultiplierReader,
        screen_capture: ScreenCapture,
        supabase_url: str,
        supabase_key: str
    ):
        """Initialize rules-based trader

        Args:
            game_actions: GameActions instance
            multiplier_reader: MultiplierReader instance
            screen_capture: ScreenCapture instance for balance reading
            supabase_url: Supabase URL
            supabase_key: Supabase key
        """
        self.game_actions = game_actions
        self.multiplier_reader = multiplier_reader
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.client: Optional[AsyncClient] = None
        self.running = False

        # Balance tracking
        self.balance_reader = BalanceReader(screen_capture)
        self.previous_balance = None

        # Initialize rules engine
        import os
        config_path = os.path.join(os.path.dirname(__file__), "betting_rules_config.json")
        self.rules_engine = BettingRulesEngine(config_path)

        # Statistics
        self.total_rounds = 0
        self.total_wins = 0
        self.total_losses = 0
        self.total_profit = 0.0
        self.total_loss = 0.0

        self._log("Rules-based trader initialized (NO AI - RULES ONLY)", "INFO")

    def _log(self, message: str, level: str = "INFO"):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] RULES-TRADER {level}: {message}")

    async def connect(self) -> bool:
        """Connect to Supabase"""
        try:
            from supabase import create_async_client
            self.client = await create_async_client(self.supabase_url, self.supabase_key)
            self._log("Connected to Supabase", "INFO")
            return True
        except Exception as e:
            self._log(f"Failed to connect to Supabase: {e}", "ERROR")
            return False

    async def place_bet_and_monitor(self) -> Dict[str, Any]:
        """Place a bet based ONLY on rules and monitor until cashout"""

        self.total_rounds += 1
        round_num = self.total_rounds

        result = {
            "round": round_num,
            "bet_placed": False,
            "cashout_executed": False,
            "final_multiplier": 0.0,
            "pnl": 0.0,
            "status": "pending"
        }

        try:
            # STEP 1: Evaluate entry based on RULES ONLY
            self._log(f"Round {round_num}: Evaluating entry...", "INFO")

            # Dummy AI values - we don't use them, just for entry evaluation structure
            dummy_predicted_mult = 2.0
            dummy_confidence = 0.8

            entry_approved, entry_reason = self.rules_engine.evaluate_entry(
                dummy_predicted_mult,
                dummy_confidence
            )

            if not entry_approved:
                self._log(f"Round {round_num}: SKIPPED - {entry_reason}", "INFO")
                result["status"] = "skipped"
                result["reason"] = entry_reason
                return result

            self._log(f"Round {round_num}: Entry APPROVED", "INFO")

            # STEP 2: Calculate stake based on RULES
            stake_amount, compound_level = self.rules_engine.calculate_stake_for_bet()
            self._log(f"Round {round_num}: Calculated stake: {stake_amount:.2f} (compound_level={compound_level})", "INFO")

            # STEP 3: Calculate cashout based on RULES (no prediction needed!)
            # We use dummy prediction since cashout selector just uses regime
            cashout_mult, cashout_mode = self.rules_engine.calculate_cashout_target(2.0)
            self._log(f"Round {round_num}: Cashout target: {cashout_mult:.2f}x ({cashout_mode} mode)", "INFO")

            # STEP 4: Verify conditions before betting
            self._log(f"Round {round_num}: Waiting for current round to end...", "INFO")
            round_ready = self.game_actions.wait_for_round_end(self.multiplier_reader, max_wait_seconds=120)

            if not round_ready:
                self._log(f"Round {round_num}: Timeout waiting for round end", "ERROR")
                result["status"] = "failed"
                return result

            # Validate button state
            from game_actions import GameActions as GA
            button_state = self.game_actions.check_button_state() if hasattr(self.game_actions, 'check_button_state') else 'green'

            if button_state != 'green':
                self._log(f"Round {round_num}: Button is {button_state}, not green - ABORT", "WARNING")
                result["status"] = "failed"
                return result

            # Read balance before bet
            time.sleep(0.5)
            try:
                self.previous_balance = self.balance_reader.read_balance()
                if self.previous_balance:
                    self._log(f"Round {round_num}: Balance before: {self.previous_balance:.0f}", "INFO")
            except:
                self.previous_balance = 0

            # STEP 5: Place bet
            self._log(f"Round {round_num}: PLACING BET - Stake: {stake_amount:.2f}", "INFO")
            bet_success = self.game_actions.click_bet_button()

            if not bet_success:
                self._log(f"Round {round_num}: Bet click failed", "ERROR")
                result["status"] = "failed"
                return result

            result["bet_placed"] = True
            self._log(f"Round {round_num}: BET PLACED SUCCESSFULLY", "INFO")
            time.sleep(1.0)

            # Wait for round to start
            self._log(f"Round {round_num}: Waiting for round to start...", "INFO")
            round_started = False
            start_wait = time.time()

            while time.time() - start_wait < 10:
                try:
                    mult = self.multiplier_reader.read_multiplier()
                    if mult and mult > 1.0:
                        self._log(f"Round {round_num}: Round started! Multiplier: {mult:.2f}x", "INFO")
                        round_started = True
                        break
                except:
                    pass
                await asyncio.sleep(0.2)

            if not round_started:
                self._log(f"Round {round_num}: Round failed to start", "ERROR")
                result["status"] = "failed"
                return result

            # STEP 6: Monitor and cashout
            self._log(f"Round {round_num}: Monitoring for cashout at {cashout_mult:.2f}x...", "INFO")

            start_time = time.time()
            last_display = start_time
            max_mult = 0

            while time.time() - start_time < 60:
                try:
                    current_mult = self.multiplier_reader.read_multiplier()

                    if current_mult is None:
                        await asyncio.sleep(0.2)
                        continue

                    max_mult = max(max_mult, current_mult)

                    # Display every 1 second
                    elapsed = time.time() - start_time
                    if elapsed - (last_display - start_time) >= 1.0:
                        self._log(
                            f"Round {round_num}: Current: {current_mult:.2f}x | Target: {cashout_mult:.2f}x",
                            "INFO"
                        )
                        last_display = time.time()

                    # Check if we reached cashout multiplier
                    if current_mult >= cashout_mult:
                        self._log(
                            f"Round {round_num}: CASHOUT! {current_mult:.2f}x >= {cashout_mult:.2f}x",
                            "INFO"
                        )

                        # Click cashout button
                        pyautogui.click(
                            self.game_actions.bet_button_point.x,
                            self.game_actions.bet_button_point.y
                        )
                        result["cashout_executed"] = True
                        result["final_multiplier"] = current_mult

                        time.sleep(2.0)
                        break

                except Exception as e:
                    self._log(f"Round {round_num}: Error monitoring multiplier: {e}", "ERROR")

                await asyncio.sleep(0.2)

            if not result["cashout_executed"]:
                self._log(f"Round {round_num}: Cashout not executed (timeout)", "WARNING")
                result["final_multiplier"] = max_mult

            # STEP 7: Calculate P&L
            result["status"] = "completed"
            time.sleep(1.0)
            current_balance = self.balance_reader.read_balance()

            if current_balance and self.previous_balance:
                result["pnl"] = current_balance - self.previous_balance
                is_win = result["pnl"] > 0

                self._log(
                    f"Round {round_num}: {'WIN' if is_win else 'LOSS'} - "
                    f"Multiplier: {result['final_multiplier']:.2f}x | "
                    f"P&L: {result['pnl']:+.0f}",
                    "INFO"
                )

                # STEP 8: Process result with rules engine
                should_stop, stop_decision = self.rules_engine.process_round_result(
                    round_id=round_num,
                    final_mult=result["final_multiplier"],
                    pnl=result["pnl"],
                    cashout_mode=cashout_mode
                )

                # Update stats
                if is_win:
                    self.total_wins += 1
                    self.total_profit += result["pnl"]
                else:
                    self.total_losses += 1
                    self.total_loss += abs(result["pnl"])

                # Check session stop
                if should_stop:
                    self._log(f"SESSION STOP: {stop_decision.reason}", "WARNING")
                    self.running = False
                    result["session_stop"] = True

            else:
                self._log(f"Round {round_num}: Could not read balance", "WARNING")

            return result

        except Exception as e:
            self._log(f"Round {round_num}: Exception: {e}", "ERROR")
            result["status"] = "failed"
            import traceback
            traceback.print_exc()
            return result

    async def run(self):
        """Main trading loop"""
        if not await self.connect():
            self._log("Failed to connect - exiting", "ERROR")
            return

        self.running = True

        try:
            while self.running:
                result = await self.place_bet_and_monitor()

                if not self.running or result.get("session_stop"):
                    break

                await asyncio.sleep(0.5)

        except KeyboardInterrupt:
            self._log("Trader stopped by user", "INFO")
        finally:
            self._print_session_summary()

    def _print_session_summary(self):
        """Print session summary"""
        print("\n" + "=" * 70)
        print("RULES-BASED TRADING SESSION SUMMARY".center(70))
        print("=" * 70)
        print(f"Total Rounds:          {self.total_rounds}")
        print(f"Total Wins:            {self.total_wins}")
        print(f"Total Losses:          {self.total_losses}")
        print(f"Win Rate:              {(self.total_wins/self.total_rounds*100) if self.total_rounds > 0 else 0:.1f}%")
        print(f"Total Profit:          {self.total_profit:+.0f}")
        print(f"Total Loss:            {self.total_loss:+.0f}")
        print(f"Net P&L:               {(self.total_profit - self.total_loss):+.0f}")
        print("=" * 70)

    async def stop(self):
        """Stop the trader"""
        self.running = False
