"""Model-agnostic real-time listener with selective betting based on criteria"""
import asyncio
import time
import json
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from supabase.client import AsyncClient
from multiplier_reader import MultiplierReader
from game_actions import GameActions
from screen_capture import ScreenCapture
from config import RegionConfig
from balance_reader import BalanceReader
import pyautogui
import numpy as np
from PIL import ImageGrab


class RoundRecord:
    """Track information about each round"""

    def __init__(self, round_id: int, signal_id: int):
        self.round_id = round_id
        self.signal_id = signal_id
        self.created_at = datetime.now()
        self.predicted_multiplier = 0.0
        self.confidence = 0.0
        self.range_min = 0.0
        self.range_max = 0.0
        self.bet_qualified = False  # Whether it meets betting criteria
        self.bet_placed = False
        self.cashout_executed = False
        self.final_multiplier = 0.0
        self.status = "signal_received"  # signal_received, bet_qualified, bet_placed, completed, failed
        self.error_message = None

    def __repr__(self):
        return (
            f"Round#{self.round_id} | "
            f"Pred: {self.predicted_multiplier:.2f}x | "
            f"Range: [{self.range_min:.2f}, {self.range_max:.2f}] | "
            f"Qualified: {self.bet_qualified} | "
            f"Status: {self.status}"
        )


class ModelRealtimeListener:
    """Real-time listener with selective betting criteria (model-agnostic)"""

    def __init__(
        self,
        game_actions: GameActions,
        multiplier_reader: MultiplierReader,
        screen_capture: ScreenCapture,
        supabase_url: str,
        supabase_key: str,
        model_name: str = "PyCaret",
        min_predicted_multiplier: float = 1.3,
        min_range_start: float = 1.3,
        safety_margin: float = 0.8,
        base_stake: float = 20.0
    ):
        """Initialize real-time listener

        Args:
            game_actions: GameActions instance for clicking
            multiplier_reader: MultiplierReader instance for monitoring
            screen_capture: ScreenCapture instance for balance reading
            supabase_url: Supabase project URL
            supabase_key: Supabase anon/JWT key
            model_name: Name of model to extract (default: "PyCaret")
            min_predicted_multiplier: Minimum predicted multiplier to bet (default 1.3)
            min_range_start: Minimum range start to bet (default 1.3)
            safety_margin: Cashout at this % of predicted (default 0.8 = 20% buffer)
            base_stake: Base bet amount (default 20)
        """
        self.game_actions = game_actions
        self.multiplier_reader = multiplier_reader
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.model_name = model_name
        self.client: Optional[AsyncClient] = None
        self.channel = None
        self.running = False

        # Betting criteria
        self.min_predicted_multiplier = min_predicted_multiplier
        self.min_range_start = min_range_start
        self.safety_margin = safety_margin
        self.base_stake = base_stake
        self.current_stake = base_stake

        # Balance tracking
        self.balance_reader = BalanceReader(screen_capture)
        self.previous_balance = None
        self.last_balance_check = None

        # Statistics
        self.execution_count = 0
        self.qualified_bets = 0
        self.successful_trades = 0
        self.failed_trades = 0
        self.consecutive_losses = 0

        # Local round tracking array
        self.rounds: List[RoundRecord] = []

    def _log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {self.model_name.upper()}-RT {level}: {message}")

    async def connect(self) -> bool:
        """Connect to Supabase asynchronously

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            from supabase import create_async_client
            self.client = await create_async_client(self.supabase_url, self.supabase_key)
            self._log("Connected to Supabase (async client)", "INFO")
            return True
        except Exception as e:
            self._log(f"Failed to connect to Supabase: {e}", "ERROR")
            return False

    def extract_model_prediction(self, signal_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract model prediction from signal

        Args:
            signal_data: Signal data from database

        Returns:
            Dict with prediction details or None if not found
        """
        try:
            # Parse payload if it's a string
            payload = signal_data
            if isinstance(signal_data.get("payload"), str):
                payload = json.loads(signal_data["payload"])

            # Look for model in modelPredictions.automl
            if "modelPredictions" not in payload or "automl" not in payload["modelPredictions"]:
                return None

            for model in payload["modelPredictions"]["automl"]:
                if model.get("model_name") == self.model_name:
                    return {
                        "model_name": self.model_name,
                        "predicted_multiplier": float(model.get("predicted_multiplier", 0)),
                        "confidence": float(model.get("confidence", 0)),
                        "range": model.get("range", [0, 0]),
                        "strategy": model.get("strategy", "unknown"),
                        "bet": model.get("bet", False),
                        "timestamp": model.get("timestamp")
                    }

            return None

        except Exception as e:
            self._log(f"Error extracting {self.model_name} prediction: {e}", "ERROR")
            return None

    def _display_all_predictions_table(self, signal_data: Dict, selected_model: str) -> None:
        """
        Display all 15 model predictions in a formatted table

        Args:
            signal_data: Complete signal data from analytics_round_signals
            selected_model: Name of the user-selected model to highlight
        """
        try:
            # Extract payload
            payload = signal_data.get("payload", {})
            if isinstance(payload, str):
                payload = json.loads(payload)

            predictions = payload.get("modelPredictions", {}).get("automl", [])

            if not predictions:
                self._log("No predictions found in payload", "WARNING")
                return

            round_id = signal_data.get("round_id", "N/A")
            pattern = signal_data.get("pattern_match_type", "UNKNOWN")

            # Build table
            lines = []

            # Header
            lines.append("=" * 85)
            lines.append(f"{'AZURE AI FOUNDRY - ROUND #' + str(round_id) + ' PREDICTIONS':^85}")
            lines.append("=" * 85)

            # Column headers
            lines.append(f"{'Model':<22} {'Prediction':<12} {'Confidence':<12} {'Range':<18} {'Strategy':<12} {'Bet?':<8}")
            lines.append("-" * 85)

            # Data rows
            total_confidence = 0
            total_prediction = 0
            bet_count = 0

            for pred in predictions:
                model_name = pred.get("model_name", "Unknown")
                predicted_mult = pred.get("predicted_multiplier", 0.0)
                confidence = pred.get("confidence", 0.0)
                range_vals = pred.get("range", [0, 0])
                strategy = pred.get("strategy", "unknown")
                should_bet = pred.get("bet", False)

                # Accumulate statistics
                total_confidence += confidence
                total_prediction += predicted_mult
                if should_bet:
                    bet_count += 1

                # Format range
                range_str = f"[{range_vals[0]:.1f}-{range_vals[1]:.1f}]"

                # Format bet recommendation
                bet_str = "YES" if should_bet else "NO"

                # Highlight selected model
                if model_name == selected_model:
                    line = f"→ {model_name:<20} {predicted_mult:>6.1f}x{'':<5} {confidence*100:>6.1f}%{'':<5} {range_str:<18} {strategy:<12} {bet_str:<8}"
                else:
                    line = f"  {model_name:<20} {predicted_mult:>6.1f}x{'':<5} {confidence*100:>6.1f}%{'':<5} {range_str:<18} {strategy:<12} {bet_str:<8}"

                lines.append(line)

            # Statistics
            lines.append("-" * 85)
            lines.append("ENSEMBLE STATISTICS")

            avg_prediction = total_prediction / len(predictions) if predictions else 0
            avg_confidence = total_confidence / len(predictions) if predictions else 0

            lines.append(f"  Average Prediction: {avg_prediction:.2f}x | Average Confidence: {avg_confidence*100:.1f}% | Consensus: {bet_count}/{len(predictions)}")
            lines.append(f"  Pattern: {pattern}")

            # Selected model summary
            selected_pred = next((p for p in predictions if p.get("model_name") == selected_model), None)
            if selected_pred:
                lines.append("-" * 85)
                pred_mult = selected_pred.get("predicted_multiplier", 0)
                pred_conf = selected_pred.get("confidence", 0)
                pred_bet = selected_pred.get("bet", False)
                status = "QUALIFIED [YES]" if pred_bet else "NOT QUALIFIED [NO]"
                lines.append(f"SELECTED MODEL: {selected_model} => {pred_mult:.1f}x ({pred_conf*100:.0f}% confidence) - {status}")

            lines.append("=" * 85)

            # Print table
            for line in lines:
                print(line)

        except Exception as e:
            self._log(f"Error displaying predictions table: {e}", "ERROR")

    def check_bet_criteria(self, predicted_mult: float, range_min: float, range_max: float) -> tuple:
        """Check if bet meets criteria

        Args:
            predicted_mult: Predicted multiplier from PyCaret
            range_min: Minimum of expected range
            range_max: Maximum of expected range

        Returns:
            Tuple of (should_bet: bool, reason: str)
        """
        # Check predicted multiplier
        if predicted_mult < self.min_predicted_multiplier:
            return False, f"Predicted {predicted_mult:.2f}x < min {self.min_predicted_multiplier:.2f}x"

        # Check range minimum
        if range_min < self.min_range_start:
            return False, f"Range start {range_min:.2f}x < min {self.min_range_start:.2f}x"

        # All criteria met
        return True, f"Predicted {predicted_mult:.2f}x, Range [{range_min:.2f}, {range_max:.2f}] - QUALIFIED"

    def get_button_color(self) -> Tuple[int, int, int]:
        """Get the average color of the bet button area

        Returns:
            Tuple of (R, G, B) values representing the button color
        """
        try:
            # Capture pixel at bet button coordinates
            x, y = self.game_actions.bet_button_point.x, self.game_actions.bet_button_point.y

            # Capture a small region around the button (30x30 pixels)
            screenshot = ImageGrab.grab(bbox=(x - 15, y - 15, x + 15, y + 15))
            pixels = np.array(screenshot)

            # Get average color (convert from RGB to BGR for consistency)
            avg_color = np.mean(pixels, axis=(0, 1))
            return tuple(int(c) for c in avg_color)
        except Exception as e:
            self._log(f"Error getting button color: {e}", "WARNING")
            return (0, 0, 0)

    def check_button_state(self) -> str:
        """Check the state of the bet button by its color

        Returns:
            'green' - Button is GREEN (place bet available, can place bet NOW)
            'blue' - Button is BLUE (multiplier running/round in progress)
            'orange' - Button is GRAY/OTHER (bet already placed, waiting for next round)
            'unknown' - Cannot determine state
        """
        try:
            r, g, b = self.get_button_color()

            # Exact color detection from bet_placement_orchestrator
            # GREEN button: Place bet is available (g > 100 and r < g)
            # Typical green: (85, 170, 38) or similar
            if g > 100 and r < g:
                self._log(f"DEBUG: GREEN detected RGB({r}, {g}, {b}) - Bet can be placed", "DEBUG")
                return 'green'

            # BLUE button: Game in progress (b > 100 and r < b)
            # Typical blue: (45, 107, 253) or similar
            elif b > 100 and r < b:
                self._log(f"DEBUG: BLUE detected RGB({r}, {g}, {b}) - Multiplier running", "DEBUG")
                return 'blue'

            # GRAY/OTHER: Button state changed (placed or disabled)
            # This is when abs(r-g) < 30 and abs(g-b) < 30 OR any other color
            elif abs(r - g) < 30 and abs(g - b) < 30:
                self._log(f"DEBUG: GRAY detected RGB({r}, {g}, {b}) - Bet placed/waiting", "DEBUG")
                return 'orange'

            else:
                self._log(f"DEBUG: OTHER color detected RGB({r}, {g}, {b})", "DEBUG")
                return 'orange'  # Default to orange (not green = not available to place)

        except Exception as e:
            self._log(f"Error checking button state: {e}", "WARNING")
            return 'unknown'

    def wait_for_button_ready(self, max_wait_seconds: int = 30) -> bool:
        """Wait for bet button to be in green state (ready to place bet)

        Args:
            max_wait_seconds: Maximum time to wait for button to be ready

        Returns:
            bool: True if button became green, False if timeout
        """
        start_time = time.time()
        check_interval = 0.5
        last_log = start_time

        while time.time() - start_time < max_wait_seconds:
            state = self.check_button_state()

            if state == 'green':
                self._log("Bet button is GREEN - Ready to place bet!", "INFO")
                return True

            # Log every 2 seconds
            if time.time() - last_log > 2:
                self._log(f"Waiting for button to be green... (current: {state})", "DEBUG")
                last_log = time.time()

            time.sleep(check_interval)

        self._log(f"Timeout waiting for button to be green (waited {max_wait_seconds}s)", "WARNING")
        return False

    def add_round(self, round_id: int, signal_id: int) -> RoundRecord:
        """Add a new round to tracking array

        Args:
            round_id: Round ID
            signal_id: Signal ID

        Returns:
            The new RoundRecord
        """
        record = RoundRecord(round_id, signal_id)
        self.rounds.append(record)
        self._log(f"Added round to tracking: Round#{round_id}", "DEBUG")
        return record

    def get_round(self, round_id: int) -> Optional[RoundRecord]:
        """Get round record by ID

        Args:
            round_id: Round ID to find

        Returns:
            RoundRecord or None if not found
        """
        for record in self.rounds:
            if record.round_id == round_id:
                return record
        return None

    def print_rounds_summary(self):
        """Print summary of all tracked rounds"""
        print("\n" + "="*100)
        print("ROUNDS SUMMARY")
        print("="*100)

        if not self.rounds:
            print("No rounds tracked yet")
            return

        qualified = sum(1 for r in self.rounds if r.bet_qualified)
        executed = sum(1 for r in self.rounds if r.bet_placed)
        succeeded = sum(1 for r in self.rounds if r.status == "completed")

        print(f"\nTotal Rounds: {len(self.rounds)}")
        print(f"Qualified for Bet: {qualified}")
        print(f"Bets Executed: {executed}")
        print(f"Successful: {succeeded}")

        print(f"\nDetailed List:")
        for i, record in enumerate(self.rounds[-10:], 1):  # Show last 10
            print(f"  {i}. {record}")

        print("="*100 + "\n")

    def read_current_balance(self) -> Optional[float]:
        """Read current balance from screen

        Returns:
            float: Current balance or None if unable to read
        """
        try:
            balance = self.balance_reader.read_balance()
            if balance is not None:
                # Validate balance is reasonable
                if balance > 0:
                    self._log(f"Current balance: {balance:.2f}", "INFO")
                    return balance
                else:
                    self._log(f"Balance is non-positive: {balance}", "WARNING")
                    return None
            else:
                self._log("Failed to read balance - OCR could not extract value from region", "WARNING")
                return None
        except Exception as e:
            self._log(f"Error reading balance: {str(e)}", "WARNING")
            return None

    def calculate_balance_change(self, current_balance: Optional[float]) -> Tuple[bool, Optional[float]]:
        """Calculate balance change and determine win/loss

        Args:
            current_balance: Current balance value

        Returns:
            Tuple: (is_win: bool, balance_change: float or None)
        """
        if current_balance is None or self.previous_balance is None:
            return False, None

        change = current_balance - self.previous_balance
        is_win = change > 0

        self._log(
            f"Balance change: {self.previous_balance:.2f} → {current_balance:.2f} (Delta: {change:+.2f}) - {'WIN' if is_win else 'LOSS'}",
            "INFO"
        )

        return is_win, change

    def adjust_stake(self, is_win: bool):
        """Adjust stake for next bet based on win/loss

        Args:
            is_win: True if last bet was a win, False if loss
        """
        old_stake = self.current_stake

        if is_win:
            # Increase stake by 30% on win
            self.current_stake = self.current_stake * 1.3
            self.consecutive_losses = 0
            self._log(
                f"WIN! Stake increased: {old_stake:.2f} → {self.current_stake:.2f} (+30%)",
                "INFO"
            )
        else:
            # Reset to base on loss
            self.current_stake = self.base_stake
            self.consecutive_losses += 1
            self._log(
                f"LOSS! Stake reset to base: {old_stake:.2f} → {self.current_stake:.2f}",
                "INFO"
            )

    def validate_pre_bet_conditions(self) -> Tuple[bool, str]:
        """Validate all conditions before placing a bet (balance check skipped)

        Returns:
            Tuple: (is_valid: bool, reason: str)
        """
        # Check 1: Verify button is GREEN right now (CRITICAL)
        button_state = self.check_button_state()
        if button_state != 'green':
            return False, f"Button is {button_state}, not GREEN - cannot place bet"

        # Check 2: Verify no active multiplier (round not started)
        try:
            current_mult = self.multiplier_reader.read_multiplier()
            if current_mult is not None and current_mult > 1.0:
                return False, f"Multiplier already active at {current_mult:.2f}x - round in progress"
        except Exception as e:
            self._log(f"Warning: Could not check multiplier: {e}", "WARNING")
            pass  # If can't read multiplier, continue

        # Check 3: Verify we haven't processed this round yet (DUPLICATE PREVENTION)
        if hasattr(self, '_current_round_id'):
            round_id = self._current_round_id
            existing_round = next((r for r in self.rounds if r.round_id == round_id and r.bet_placed), None)
            if existing_round:
                return False, f"Bet already placed in round {round_id}"

        # BALANCE CHECK SKIPPED - will attempt to place bet regardless
        self._log(
            f"Pre-bet validation PASSED | Button: {button_state} | Stake: {self.current_stake:.2f}",
            "INFO"
        )
        return True, "All critical conditions valid"

    async def execute_pycaret_signal(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute trading based on PyCaret signal with criteria

        Args:
            signal_data: Signal data from analytics_round_signals

        Returns:
            Execution result
        """
        self.execution_count += 1
        round_id = signal_data.get("round_id")
        signal_id = signal_data.get("id")

        # Add to rounds tracking
        round_record = self.add_round(round_id, signal_id)

        result = {
            "signal_id": signal_id,
            "round_id": round_id,
            "status": "pending",
            "execution_time": datetime.now().strftime("%H:%M:%S"),
            "bet_qualified": False,
            "bet_placed": False,
            "cashout_executed": False,
            "final_multiplier": 0.0,
            "error_message": None
        }

        try:
            # Extract model prediction
            model_pred = self.extract_model_prediction(signal_data)

            # Display all 15 model predictions in table format
            self._display_all_predictions_table(signal_data, self.model_name)

            if not model_pred:
                result["status"] = "failed"
                result["error_message"] = f"{self.model_name} prediction not found in payload"
                round_record.status = "failed"
                round_record.error_message = f"{self.model_name} not found"
                self._log(f"{self.model_name} prediction not found for round {round_id}", "WARNING")
                # Debug: Check what's in signal_data
                self._log(f"DEBUG: signal_data keys: {list(signal_data.keys())}", "DEBUG")
                if "payload" in signal_data and isinstance(signal_data["payload"], str):
                    try:
                        payload_dict = json.loads(signal_data["payload"])
                        if "modelPredictions" in payload_dict:
                            models_found = [m.get("model_name") for m in payload_dict["modelPredictions"].get("automl", [])]
                            self._log(f"DEBUG: Models in payload: {models_found}", "DEBUG")
                    except:
                        pass
                self.failed_trades += 1
                return result

            predicted_mult = model_pred.get("predicted_multiplier", 0)
            confidence = model_pred.get("confidence", 0)
            range_min, range_max = model_pred.get("range", [0, 0])

            # Update round record with prediction data
            round_record.predicted_multiplier = predicted_mult
            round_record.confidence = confidence
            round_record.range_min = range_min
            round_record.range_max = range_max

            # Check betting criteria
            should_bet, criteria_reason = self.check_bet_criteria(predicted_mult, range_min, range_max)

            self._log(
                f"Round {round_id}: {criteria_reason}",
                "INFO"
            )

            if not should_bet:
                result["status"] = "skipped"
                result["error_message"] = criteria_reason
                round_record.status = "signal_received"
                round_record.error_message = criteria_reason
                self._log(f"Round {round_id} does not meet betting criteria - SKIPPING", "INFO")
                return result

            # Criteria met - proceed with betting
            result["bet_qualified"] = True
            round_record.bet_qualified = True
            self.qualified_bets += 1

            cashout_mult = predicted_mult * self.safety_margin

            self._log(
                f"Round {round_id}: QUALIFIED FOR BET | "
                f"Predicted: {predicted_mult:.2f}x | "
                f"Cashout at: {cashout_mult:.2f}x (20% buffer)",
                "INFO"
            )

            # Wait for round to end (if one is active)
            self._log(f"Waiting for current round to end...", "INFO")
            round_ready = self.game_actions.wait_for_round_end(self.multiplier_reader, max_wait_seconds=120)

            if not round_ready:
                result["status"] = "failed"
                result["error_message"] = "Timeout waiting for previous round to end"
                round_record.status = "failed"
                self._log("Timeout waiting for round to end", "ERROR")
                self.failed_trades += 1
                return result

            # COMPREHENSIVE PRE-BET VALIDATION
            # Check all conditions before placing bet
            self._current_round_id = round_id  # Store for validation
            time.sleep(0.5)  # Let UI settle

            is_valid, validation_reason = self.validate_pre_bet_conditions()

            if not is_valid:
                result["status"] = "failed"
                result["error_message"] = f"Pre-bet validation failed: {validation_reason}"
                round_record.status = "failed"
                self._log(f"PRE-BET VALIDATION FAILED: {validation_reason}", "WARNING")
                self.failed_trades += 1
                return result

            # All validations passed - safe to place bet
            self._log(f"ALL PRE-BET CHECKS PASSED - Proceeding with bet placement", "INFO")

            # FINAL BUTTON CHECK - right before click (race condition detection)
            final_button_state = self.check_button_state()
            if final_button_state != 'green':
                result["status"] = "failed"
                result["error_message"] = f"Button changed to {final_button_state} - aborting bet placement"
                round_record.status = "failed"
                self._log(f"ABORT: Button is {final_button_state} at click time (was green moments ago) - race condition detected", "ERROR")
                self.failed_trades += 1
                return result

            # Try to read balance for tracking (not blocking if fails)
            self.previous_balance = self.read_current_balance()
            if self.previous_balance is None:
                self._log(f"Note: Could not read balance before bet", "WARNING")
                self.previous_balance = 0  # Use 0 as placeholder

            # Place bet
            self._log(f"CLICKING BET BUTTON for round {round_id} | Stake: {self.current_stake:.2f}", "INFO")
            bet_success = self.game_actions.click_bet_button()

            if not bet_success:
                result["status"] = "failed"
                result["error_message"] = "Failed to click bet button"
                round_record.status = "failed"
                self._log(f"BET CLICK FAILED - Click action returned False", "ERROR")
                self.failed_trades += 1
                return result

            result["bet_placed"] = True
            round_record.bet_placed = True
            self._log(f"BET PLACED SUCCESSFULLY | Round: {round_id} | Stake: {self.current_stake:.2f}", "INFO")
            time.sleep(1.0)

            # Wait for round to start
            self._log(f"Waiting for round to start...", "INFO")
            round_started = False
            start_wait = time.time()

            while time.time() - start_wait < 10:
                try:
                    mult = self.multiplier_reader.read_multiplier()
                    if mult and mult > 1.0:
                        self._log(f"Round started! Multiplier: {mult:.2f}x", "INFO")
                        round_started = True
                        break
                except:
                    pass
                await asyncio.sleep(0.2)

            if not round_started:
                result["status"] = "failed"
                result["error_message"] = "Round did not start or multiplier not readable"
                round_record.status = "failed"
                self._log("Round failed to start", "ERROR")
                self.failed_trades += 1
                return result

            # Monitor multiplier and execute cashout
            # Use local variables to avoid interference from new signals
            round_cashout_mult = cashout_mult
            round_predicted_mult = predicted_mult
            round_round_id = round_id

            self._log(
                f"[Round {round_round_id}] Monitoring for cashout at {round_cashout_mult:.2f}x (pred: {round_predicted_mult:.2f}x)...",
                "INFO"
            )

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
                            f"[Round {round_round_id}] Current: {current_mult:.2f}x | Target: {round_cashout_mult:.2f}x | Predicted: {round_predicted_mult:.2f}x",
                            "INFO"
                        )
                        last_display = time.time()

                    # Check if we reached cashout multiplier
                    if current_mult >= round_cashout_mult:
                        self._log(
                            f"[Round {round_round_id}] CASHOUT! {current_mult:.2f}x >= {round_cashout_mult:.2f}x",
                            "INFO"
                        )

                        # Click cashout button
                        pyautogui.click(
                            self.game_actions.bet_button_point.x,
                            self.game_actions.bet_button_point.y
                        )
                        result["cashout_executed"] = True
                        result["final_multiplier"] = current_mult
                        round_record.cashout_executed = True
                        round_record.final_multiplier = current_mult

                        time.sleep(2.0)
                        break

                except Exception as e:
                    self._log(f"Error monitoring multiplier: {e}", "ERROR")

                await asyncio.sleep(0.2)

            if not result["cashout_executed"]:
                self._log(f"Cashout not executed (timeout or crashed)", "WARNING")
                result["final_multiplier"] = max_mult
                round_record.final_multiplier = max_mult

            result["status"] = "completed"
            round_record.status = "completed"
            self._log(
                f"Round {round_id} completed - Final multiplier: {result['final_multiplier']:.2f}x",
                "INFO"
            )

            # Track balance change and adjust stake for next bet
            time.sleep(1.0)  # Wait for balance to update
            current_balance = self.read_current_balance()

            if current_balance is not None:
                is_win, balance_change = self.calculate_balance_change(current_balance)

                if balance_change is not None:
                    # Record balance change in result
                    result["balance_before"] = self.previous_balance
                    result["balance_after"] = current_balance
                    result["balance_change"] = balance_change

                    # Adjust stake for next bet
                    self.adjust_stake(is_win)

                    # Update tracking - only count here (not earlier)
                    if is_win:
                        self.successful_trades += 1
                    else:
                        self.failed_trades += 1
                else:
                    # Could not read balance change, mark as failed
                    self._log("Could not determine win/loss from balance", "WARNING")
                    self.failed_trades += 1
            else:
                # Could not read current balance, mark as failed
                self._log("Could not read current balance for tracking", "WARNING")
                self.failed_trades += 1

            return result

        except Exception as e:
            result["status"] = "failed"
            result["error_message"] = str(e)
            round_record.status = "failed"
            round_record.error_message = str(e)
            self._log(f"Execution error: {e}", "ERROR")
            self.failed_trades += 1
            return result

    async def on_signal_received(self, payload: Dict[str, Any]):
        """Handle incoming signal from subscription (non-blocking)

        Args:
            payload: Signal payload from Supabase
        """
        try:
            # Extract the actual data - Supabase sends it in 'data' -> 'record'
            if "data" in payload and "record" in payload["data"]:
                signal_data = payload["data"]["record"]
            elif "new" in payload:
                signal_data = payload["new"]
            else:
                signal_data = payload

            signal_id = signal_data.get("id")
            round_id = signal_data.get("round_id") or signal_data.get("roundId")

            self._log(f"New signal received: Round#{round_id}, Signal ID: {signal_id}", "INFO")

            # Spawn execution as background task (non-blocking)
            # This allows new signals to be received while previous signal is processing
            asyncio.create_task(self._execute_signal_background(signal_data))

        except Exception as e:
            self._log(f"Error processing signal: {e}", "ERROR")

    async def _execute_signal_background(self, signal_data: Dict[str, Any]):
        """Execute signal in background task

        Args:
            signal_data: Signal data from database
        """
        try:
            # Prevent concurrent processing of SAME round
            round_id = signal_data.get("round_id")

            # Check if we're already processing this round
            if any(r.round_id == round_id and r.status in ["signal_received", "bet_qualified"] for r in self.rounds):
                self._log(f"Round {round_id} already being processed", "WARNING")
                return

            # Execute the signal
            result = await self.execute_pycaret_signal(signal_data)
            self._log(
                f"Execution result: {result['status']} | "
                f"Qualified: {result['bet_qualified']} | "
                f"Final: {result['final_multiplier']:.2f}x",
                "INFO"
            )
        except Exception as e:
            self._log(f"Error in background execution: {e}", "ERROR")

    async def listen(self):
        """Start listening to analytics_round_signals table in real-time"""
        if not await self.connect():
            return

        self.running = True
        self._log(
            f"Starting enhanced real-time listener | "
            f"Min Predicted: {self.min_predicted_multiplier:.2f}x | "
            f"Min Range Start: {self.min_range_start:.2f}x | "
            f"Safety Margin: {self.safety_margin*100:.0f}%",
            "INFO"
        )

        try:
            # Create channel for real-time updates
            self.channel = self.client.channel("analytics-round-signals-channel")

            # Subscribe to INSERT events
            self.channel.on_postgres_changes(
                event="INSERT",
                schema="public",
                table="analytics_round_signals",
                callback=lambda payload: asyncio.create_task(self.on_signal_received(payload))
            )

            # Subscribe asynchronously
            await self.channel.subscribe()

            self._log("Subscribed to analytics_round_signals", "INFO")

            # Keep the listener running
            while self.running:
                await asyncio.sleep(1)

        except Exception as e:
            self._log(f"Subscription error: {e}", "ERROR")
        finally:
            await self.stop()

    async def stop(self):
        """Stop the listener and clean up"""
        self.running = False
        if self.channel:
            try:
                await self.channel.unsubscribe()
                self._log("Unsubscribed from channel", "INFO")
            except:
                pass
        self._log("Listener stopped", "INFO")

    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics

        Returns:
            Statistics dictionary
        """
        return {
            "execution_count": self.execution_count,
            "qualified_bets": self.qualified_bets,
            "successful_trades": self.successful_trades,
            "failed_trades": self.failed_trades,
            "total_rounds_tracked": len(self.rounds),
            "qualification_rate": (
                self.qualified_bets / self.execution_count * 100
                if self.execution_count > 0 else 0
            ),
            "success_rate": (
                self.successful_trades / self.qualified_bets * 100
                if self.qualified_bets > 0 else 0
            )
        }
