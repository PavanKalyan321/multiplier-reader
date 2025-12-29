"""Enhanced PyCaret real-time listener with selective betting based on criteria"""
import asyncio
import time
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from supabase.client import AsyncClient
from multiplier_reader import MultiplierReader
from game_actions import GameActions
import pyautogui


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


class PyCaretRealtimeEnhanced:
    """Enhanced real-time listener with selective betting criteria"""

    def __init__(
        self,
        game_actions: GameActions,
        multiplier_reader: MultiplierReader,
        supabase_url: str,
        supabase_key: str,
        min_predicted_multiplier: float = 1.3,
        min_range_start: float = 1.3,
        safety_margin: float = 0.8
    ):
        """Initialize enhanced real-time listener

        Args:
            game_actions: GameActions instance for clicking
            multiplier_reader: MultiplierReader instance for monitoring
            supabase_url: Supabase project URL
            supabase_key: Supabase anon/JWT key
            min_predicted_multiplier: Minimum predicted multiplier to bet (default 1.3)
            min_range_start: Minimum range start to bet (default 1.3)
            safety_margin: Cashout at this % of predicted (default 0.8 = 20% buffer)
        """
        self.game_actions = game_actions
        self.multiplier_reader = multiplier_reader
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.client: Optional[AsyncClient] = None
        self.channel = None
        self.running = False

        # Betting criteria
        self.min_predicted_multiplier = min_predicted_multiplier
        self.min_range_start = min_range_start
        self.safety_margin = safety_margin

        # Statistics
        self.execution_count = 0
        self.qualified_bets = 0
        self.successful_trades = 0
        self.failed_trades = 0
        self.processing_signal = False

        # Local round tracking array
        self.rounds: List[RoundRecord] = []

    def _log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] PYCARET-ENH {level}: {message}")

    async def connect(self) -> bool:
        """Connect to Supabase asynchronously

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            from supabase.client import AsyncClient as AsyncSupabaseClient
            self.client = AsyncSupabaseClient(self.supabase_url, self.supabase_key)
            self._log("Connected to Supabase (async client)", "INFO")
            return True
        except Exception as e:
            self._log(f"Failed to connect to Supabase: {e}", "ERROR")
            return False

    def extract_pycaret_prediction(self, signal_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract PyCaret prediction from signal

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

            # Look for PyCaret in modelPredictions.automl
            if "modelPredictions" not in payload or "automl" not in payload["modelPredictions"]:
                return None

            for model in payload["modelPredictions"]["automl"]:
                if model.get("model_name") == "PyCaret":
                    return {
                        "model_name": "PyCaret",
                        "predicted_multiplier": float(model.get("predicted_multiplier", 0)),
                        "confidence": float(model.get("confidence", 0)),
                        "range": model.get("range", [0, 0]),
                        "strategy": model.get("strategy", "unknown"),
                        "bet": model.get("bet", False),
                        "timestamp": model.get("timestamp")
                    }

            return None

        except Exception as e:
            self._log(f"Error extracting PyCaret prediction: {e}", "ERROR")
            return None

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
            # Extract PyCaret prediction
            pycaret = self.extract_pycaret_prediction(signal_data)
            if not pycaret:
                result["status"] = "failed"
                result["error_message"] = "PyCaret prediction not found in payload"
                round_record.status = "failed"
                round_record.error_message = "PyCaret not found"
                self._log(f"PyCaret prediction not found for round {round_id}", "WARNING")
                self.failed_trades += 1
                return result

            predicted_mult = pycaret.get("predicted_multiplier", 0)
            confidence = pycaret.get("confidence", 0)
            range_min, range_max = pycaret.get("range", [0, 0])

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

            # Place bet
            self._log(f"Placing bet for round {round_id}...", "INFO")
            bet_success = self.game_actions.click_bet_button()

            if not bet_success:
                result["status"] = "failed"
                result["error_message"] = "Failed to place bet"
                round_record.status = "failed"
                self._log("Failed to place bet", "ERROR")
                self.failed_trades += 1
                return result

            result["bet_placed"] = True
            round_record.bet_placed = True
            self._log(f"Bet placed successfully for round {round_id}", "INFO")
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
            self._log(
                f"Monitoring for cashout at {cashout_mult:.2f}x (pred: {predicted_mult:.2f}x)...",
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
                            f"Current: {current_mult:.2f}x | "
                            f"Target: {cashout_mult:.2f}x | "
                            f"Predicted: {predicted_mult:.2f}x",
                            "INFO"
                        )
                        last_display = time.time()

                    # Check if we reached cashout multiplier
                    if current_mult >= cashout_mult:
                        self._log(
                            f"CASHOUT! {current_mult:.2f}x >= {cashout_mult:.2f}x",
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
                self._log(f"Cashout not executed (timeout)", "WARNING")
                result["final_multiplier"] = max_mult
                round_record.final_multiplier = max_mult

            result["status"] = "completed"
            round_record.status = "completed"
            self.successful_trades += 1
            self._log(
                f"Round {round_id} completed - Cashout at {result['final_multiplier']:.2f}x",
                "INFO"
            )

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
        """Handle incoming signal from subscription

        Args:
            payload: Signal payload from Supabase
        """
        try:
            # Extract the actual data
            if "new" in payload:
                signal_data = payload["new"]
            else:
                signal_data = payload

            signal_id = signal_data.get("id")
            round_id = signal_data.get("round_id")

            self._log(f"New signal received: Round#{round_id}, Signal ID: {signal_id}", "INFO")

            # Prevent concurrent signal processing
            if self.processing_signal:
                self._log(f"Already processing a signal", "WARNING")
                return

            self.processing_signal = True

            try:
                # Execute the signal
                result = await self.execute_pycaret_signal(signal_data)
                self._log(
                    f"Execution result: {result['status']} | "
                    f"Qualified: {result['bet_qualified']} | "
                    f"Final: {result['final_multiplier']:.2f}x",
                    "INFO"
                )
            finally:
                self.processing_signal = False

        except Exception as e:
            self._log(f"Error processing signal: {e}", "ERROR")
            self.processing_signal = False

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
