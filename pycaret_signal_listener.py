"""PyCaret signal listener - Listens to analytics_round_signals and executes PyCaret predictions"""
import asyncio
import time
from datetime import datetime
from typing import Optional, Dict, Any
from supabase_client import SupabaseLogger
from multiplier_reader import MultiplierReader
from game_actions import GameActions
import pyautogui


class PyCaretSignalListener:
    """Listen to analytics_round_signals and execute PyCaret model predictions"""

    def __init__(self, game_actions: GameActions, multiplier_reader: MultiplierReader):
        """Initialize listener

        Args:
            game_actions: GameActions instance for clicking
            multiplier_reader: MultiplierReader instance for monitoring
        """
        self.game_actions = game_actions
        self.multiplier_reader = multiplier_reader
        self.supabase = SupabaseLogger(
            url='https://zofojiubrykbtmstfhzx.supabase.co',
            key='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvZm9qaXVicnlrYnRtc3RmaHp4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM4NzU0OTEsImV4cCI6MjA3OTQ1MTQ5MX0.mxwvnhT-ouONWff-gyqw67lKon82nBx2fsbd8meyc8s'
        )
        self.last_processed_id = None
        self.running = False
        self.execution_count = 0
        self.successful_trades = 0
        self.failed_trades = 0

    def _log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] PYCARET {level}: {message}")

    def extract_pycaret_prediction(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract PyCaret prediction from analytics_round_signals payload

        Args:
            payload: Full signal payload from database

        Returns:
            Dict with prediction details or None if not found
        """
        try:
            # Look for PyCaret in modelPredictions.automl
            if "modelPredictions" not in payload or "automl" not in payload["modelPredictions"]:
                return None

            for model in payload["modelPredictions"]["automl"]:
                if model.get("model_name") == "PyCaret":
                    return {
                        "model_name": "PyCaret",
                        "predicted_multiplier": model.get("predicted_multiplier"),
                        "confidence": model.get("confidence"),
                        "range": model.get("range"),
                        "strategy": model.get("strategy"),
                        "bet": model.get("bet", False),
                        "timestamp": model.get("timestamp")
                    }

            return None

        except Exception as e:
            self._log(f"Error extracting PyCaret prediction: {e}", "ERROR")
            return None

    def calculate_cashout_multiplier(self, predicted_multiplier: float, safety_margin: float = 0.8) -> float:
        """Calculate cashout multiplier with safety margin

        Args:
            predicted_multiplier: Predicted multiplier from PyCaret
            safety_margin: Safety margin (default 0.8 = 80% = cashout 20% earlier)

        Returns:
            Cashout multiplier
        """
        return predicted_multiplier * safety_margin

    async def execute_pycaret_signal(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute trading based on PyCaret signal

        Args:
            signal_data: Signal data from analytics_round_signals

        Returns:
            Execution result
        """
        self.execution_count += 1
        round_id = signal_data.get("roundId")

        result = {
            "round_id": round_id,
            "status": "pending",
            "execution_time": datetime.now().strftime("%H:%M:%S"),
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
                self._log(f"PyCaret prediction not found for round {round_id}", "WARNING")
                self.failed_trades += 1
                return result

            if not pycaret.get("bet"):
                result["status"] = "skipped"
                result["error_message"] = "PyCaret did not recommend a bet"
                self._log(f"PyCaret skip signal for round {round_id}", "INFO")
                return result

            predicted_mult = pycaret.get("predicted_multiplier", 0)
            confidence = pycaret.get("confidence", 0)
            cashout_mult = self.calculate_cashout_multiplier(predicted_mult)

            self._log(
                f"Round {round_id}: PyCaret predicts {predicted_mult:.2f}x "
                f"(confidence: {confidence:.0%}), cashout at {cashout_mult:.2f}x",
                "INFO"
            )

            # Wait for round to end (if one is active)
            self._log(f"Waiting for current round to end...", "INFO")
            round_ready = self.game_actions.wait_for_round_end(self.multiplier_reader, max_wait_seconds=120)

            if not round_ready:
                result["status"] = "failed"
                result["error_message"] = "Timeout waiting for previous round to end"
                self._log("Timeout waiting for round to end", "ERROR")
                self.failed_trades += 1
                return result

            # Place bet
            self._log(f"Placing bet for round {round_id}...", "INFO")
            bet_success = self.game_actions.click_bet_button()

            if not bet_success:
                result["status"] = "failed"
                result["error_message"] = "Failed to place bet"
                self._log("Failed to place bet", "ERROR")
                self.failed_trades += 1
                return result

            result["bet_placed"] = True
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
                self._log("Round failed to start", "ERROR")
                self.failed_trades += 1
                return result

            # Monitor multiplier and execute cashout
            self._log(
                f"Monitoring multiplier for target: {cashout_mult:.2f}x "
                f"(predicted: {predicted_mult:.2f}x)",
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
                            f"Target reached! {current_mult:.2f}x >= {cashout_mult:.2f}x, "
                            f"executing cashout...",
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
                    self._log(f"Error monitoring multiplier: {e}", "ERROR")

                await asyncio.sleep(0.2)

            if not result["cashout_executed"]:
                self._log(f"Cashout not executed (timeout or crash)", "WARNING")
                result["final_multiplier"] = max_mult

            result["status"] = "completed"
            self.successful_trades += 1
            self._log(
                f"Round {round_id} completed - Cashout at {result['final_multiplier']:.2f}x "
                f"(target was {cashout_mult:.2f}x)",
                "INFO"
            )

            return result

        except Exception as e:
            result["status"] = "failed"
            result["error_message"] = str(e)
            self._log(f"Execution error: {e}", "ERROR")
            self.failed_trades += 1
            return result

    async def listen(self, poll_interval: float = 2.0, max_retries: int = 3):
        """Listen to analytics_round_signals table for new entries

        Args:
            poll_interval: Time in seconds between database polls
            max_retries: Maximum retries for extraction and execution
        """
        self.running = True
        self._log(f"Starting listener (poll interval: {poll_interval}s, max retries: {max_retries})", "INFO")

        while self.running:
            try:
                # Query the latest signals
                response = self.supabase.client.table("analytics_round_signals").select(
                    "*"
                ).order("id", desc=True).limit(1).execute()

                if response.data:
                    latest_signal = response.data[0]
                    signal_id = latest_signal.get("id")
                    round_id = latest_signal.get("roundId")

                    # Process only if it's a new signal
                    if self.last_processed_id is None or signal_id > self.last_processed_id:
                        self._log(f"New signal detected: Round {round_id}, ID: {signal_id}", "INFO")
                        self.last_processed_id = signal_id

                        # Try to extract and execute PyCaret signal with retries
                        execution_success = False
                        for attempt in range(1, max_retries + 1):
                            try:
                                # Extract PyCaret prediction
                                pycaret = self.extract_pycaret_prediction(latest_signal)

                                if pycaret:
                                    self._log(
                                        f"PyCaret extracted (Attempt {attempt}/{max_retries}): "
                                        f"Prediction: {pycaret.get('predicted_multiplier'):.2f}x, "
                                        f"Confidence: {pycaret.get('confidence'):.0%}, "
                                        f"Bet: {pycaret.get('bet')}",
                                        "INFO"
                                    )

                                    # Execute the signal
                                    result = await self.execute_pycaret_signal(latest_signal)
                                    self._log(
                                        f"Execution result for Round {round_id}: {result['status']} "
                                        f"(Final: {result['final_multiplier']:.2f}x)",
                                        "INFO"
                                    )
                                    execution_success = True
                                    break
                                else:
                                    self._log(
                                        f"PyCaret not found in signal (Attempt {attempt}/{max_retries})",
                                        "WARNING"
                                    )

                            except Exception as e:
                                self._log(
                                    f"Extraction/Execution error on attempt {attempt}/{max_retries}: {e}",
                                    "WARNING"
                                )

                            # Wait before retry
                            if attempt < max_retries:
                                await asyncio.sleep(1.0)

                        if not execution_success:
                            self._log(
                                f"Failed to execute signal for Round {round_id} after {max_retries} attempts",
                                "ERROR"
                            )

                # Wait before next poll
                await asyncio.sleep(poll_interval)

            except Exception as e:
                self._log(f"Listen error: {e}", "ERROR")
                await asyncio.sleep(poll_interval)

    def stop(self):
        """Stop the listener"""
        self.running = False
        self._log("Listener stopped", "INFO")

    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics

        Returns:
            Statistics dictionary
        """
        return {
            "execution_count": self.execution_count,
            "successful_trades": self.successful_trades,
            "failed_trades": self.failed_trades,
            "success_rate": (
                self.successful_trades / self.execution_count * 100
                if self.execution_count > 0 else 0
            )
        }
