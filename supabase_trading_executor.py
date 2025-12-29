# Supabase-based trading executor with confidence-based decision logic
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from supabase_signal_listener import SupabaseSignalListener, ModelSignal, ModelName


class ConfidenceStrategy(Enum):
    """Trading strategies based on model confidence"""
    CONSERVATIVE = "conservative"  # Only trade if confidence > 80%
    MODERATE = "moderate"          # Trade if confidence > 60%
    AGGRESSIVE = "aggressive"      # Trade if confidence > 40%


@dataclass
class SupabaseExecutionRecord:
    """Record of execution from Supabase signal"""
    signal: ModelSignal
    status: str                        # pending, placed_bet, monitoring, cashout_executed, failed
    model_name: str                    # e.g., "RandomForest"
    confidence: float                  # 0-100
    expected_multiplier: float         # From signal
    expected_output: float             # From payload
    range_min: float
    range_max: float
    bet_placed_at: Optional[str] = None
    bet_result: bool = False
    cashout_executed_at: Optional[str] = None
    cashout_result: bool = False
    actual_multiplier_at_cashout: float = 0.0
    max_multiplier_reached: float = 0.0
    error_message: str = ""
    trades_today: int = 0              # Statistics
    win_rate: float = 0.0
    total_profit: float = 0.0


class SupabaseExecutor:
    """Execute trades based on Supabase signals and confidence"""

    def __init__(
        self,
        listener: SupabaseSignalListener,
        multiplier_reader,  # MultiplierReader instance
        game_actions,       # GameActions instance
        confidence_threshold: float = 60.0,
        confidence_strategy: ConfidenceStrategy = ConfidenceStrategy.MODERATE
    ):
        """Initialize Supabase executor

        Args:
            listener: SupabaseSignalListener instance
            multiplier_reader: MultiplierReader for monitoring
            game_actions: GameActions for clicking
            confidence_threshold: Minimum confidence to trade (0-100)
            confidence_strategy: Trading strategy based on confidence
        """
        self.listener = listener
        self.multiplier_reader = multiplier_reader
        self.game_actions = game_actions
        self.confidence_threshold = confidence_threshold
        self.confidence_strategy = confidence_strategy

        self.execution_records: list[SupabaseExecutionRecord] = []
        self.total_executions = 0
        self.successful_trades = 0
        self.failed_trades = 0

        # Strategy-specific thresholds
        self.strategy_thresholds = {
            ConfidenceStrategy.CONSERVATIVE: 80.0,
            ConfidenceStrategy.MODERATE: 60.0,
            ConfidenceStrategy.AGGRESSIVE: 40.0
        }

    def _log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] SUPABASE_EXECUTOR {level}: {message}")

    def _should_trade(self, signal: ModelSignal) -> bool:
        """Determine if signal should be traded (check bet flag)

        Args:
            signal: ModelSignal to evaluate

        Returns:
            True if bet flag is set to True
        """
        if not signal.bet:
            self._log(
                f"Signal bet flag is False - SKIPPING",
                "DEBUG"
            )
            return False

        return True

    def _get_target_multiplier(self, signal: ModelSignal) -> float:
        """Get target multiplier from expected_output

        Args:
            signal: ModelSignal with expected_output

        Returns:
            Target multiplier for cashout
        """
        target = signal.expected_output

        self._log(
            f"Target multiplier: {target:.2f}x (from XGBoost expectedOutput)",
            "INFO"
        )

        return target

    async def execute_signal(self, signal: ModelSignal) -> SupabaseExecutionRecord:
        """Execute trade based on Supabase signal

        Args:
            signal: ModelSignal to execute

        Returns:
            SupabaseExecutionRecord with execution details
        """
        record = SupabaseExecutionRecord(
            signal=signal,
            status="pending",
            model_name=signal.model_name,
            confidence=signal.confidence_pct,
            expected_multiplier=signal.multiplier,
            expected_output=signal.expected_output,
            range_min=signal.range_min,
            range_max=signal.range_max
        )

        self.total_executions += 1

        # Validate signal
        if not signal.is_valid():
            record.status = "failed"
            record.error_message = "Invalid signal data"
            self._log(f"Invalid signal: {signal.is_valid()}", "WARNING")
            self.failed_trades += 1
            self.execution_records.append(record)
            return record

        # Check confidence threshold
        if not self._should_trade(signal):
            record.status = "skipped"
            record.error_message = f"Confidence {signal.confidence_pct}% below threshold"
            self._log(f"Signal skipped: {record.error_message}", "INFO")
            self.execution_records.append(record)
            return record

        self._log(
            f"Executing signal: Round {signal.round_id}, Model: {signal.model_name}, "
            f"Target: {signal.expected_output}x, Confidence: {signal.confidence_pct}%",
            "INFO"
        )

        try:
            # Wait for current round to end before placing bet
            record.status = "waiting_for_round"
            self._log(f"Waiting for current round to end before placing bet for round {signal.round_id}...", "INFO")

            round_ready = self.game_actions.wait_for_round_end(self.multiplier_reader, max_wait_seconds=120)

            if not round_ready:
                record.status = "failed"
                record.error_message = "Timeout waiting for previous round to end"
                self._log("Timeout waiting for previous round to end", "WARNING")
                self.failed_trades += 1
                self.execution_records.append(record)
                return record

            # Place bet
            record.status = "placing_bet"
            self._log(f"Placing bet for round {signal.round_id}...", "INFO")

            bet_result = self.game_actions.click_bet_button()
            record.bet_placed_at = datetime.now().strftime("%H:%M:%S")
            record.bet_result = bet_result

            if not bet_result:
                record.status = "failed"
                record.error_message = "Bet placement failed"
                self._log("Bet placement failed", "WARNING")
                self.failed_trades += 1
                self.execution_records.append(record)
                return record

            self._log("Bet placed successfully", "INFO")
            record.status = "placed_bet"

            # Get target multiplier (adjusted by confidence if needed)
            target_mult = self._get_target_multiplier(signal)

            # Monitor multiplier and cashout
            record.status = "monitoring"
            await self._monitor_and_cashout(signal, record, target_mult)

            # Record execution
            record.status = "completed"
            self.successful_trades += 1
            self._log(
                f"Trade completed: Cashout at {record.actual_multiplier_at_cashout:.2f}x "
                f"(target: {target_mult:.2f}x)",
                "INFO"
            )

        except Exception as e:
            record.status = "failed"
            record.error_message = str(e)
            self.failed_trades += 1
            self._log(f"Execution error: {e}", "ERROR")

        self.execution_records.append(record)
        return record

    async def _monitor_and_cashout(
        self,
        signal: ModelSignal,
        record: SupabaseExecutionRecord,
        target_mult: float,
        max_wait_seconds: float = 60.0
    ):
        """Monitor multiplier and execute cashout

        Args:
            signal: Original signal
            record: Execution record to update
            target_mult: Target multiplier for cashout
            max_wait_seconds: Maximum time to wait before forcing cashout
        """
        start_time = datetime.now()
        max_multiplier = 0.0

        self._log(
            f"Monitoring for multiplier target: {target_mult:.2f}x (max wait: {max_wait_seconds}s)",
            "INFO"
        )

        while True:
            # Check timeout
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > max_wait_seconds:
                self._log(f"Timeout reached ({max_wait_seconds}s), forcing cashout", "WARNING")
                break

            # Read current multiplier
            try:
                current_mult = self.multiplier_reader.read_multiplier()

                if current_mult is None:
                    await asyncio.sleep(0.1)
                    continue

                max_multiplier = max(max_multiplier, current_mult)
                record.max_multiplier_reached = max_multiplier

                self._log(
                    f"Current: {current_mult:.2f}x | Target: {target_mult:.2f}x | "
                    f"Max: {max_multiplier:.2f}x",
                    "DEBUG"
                )

                # Check crash
                if current_mult < 1.0:
                    self._log("Game crashed before target - skipping cashout", "WARNING")
                    record.error_message = "Game crashed"
                    return

                # Check if target reached
                if current_mult >= target_mult:
                    self._log(
                        f"Target multiplier reached! ({current_mult:.2f}x >= {target_mult:.2f}x)",
                        "INFO"
                    )
                    break

            except Exception as e:
                self._log(f"Error reading multiplier: {e}", "WARNING")
                await asyncio.sleep(0.1)
                continue

            await asyncio.sleep(0.1)

        # Execute cashout
        await self._execute_cashout(signal, record, max_multiplier)

    async def _execute_cashout(
        self,
        signal: ModelSignal,
        record: SupabaseExecutionRecord,
        multiplier: float
    ):
        """Execute cashout

        Args:
            signal: Original signal
            record: Execution record to update
            multiplier: Current multiplier
        """
        self._log(f"Executing cashout at {multiplier:.2f}x", "INFO")

        cashout_result = self.game_actions.click_cashout_button()
        record.cashout_executed_at = datetime.now().strftime("%H:%M:%S")
        record.cashout_result = cashout_result
        record.actual_multiplier_at_cashout = multiplier

        if not cashout_result:
            record.error_message = "Cashout click failed"
            self._log("Cashout click failed", "WARNING")
            record.status = "failed"
        else:
            self._log(f"Cashout successful at {multiplier:.2f}x", "INFO")
            record.status = "cashout_executed"

    def get_execution_summary(self) -> Dict[str, Any]:
        """Get execution statistics

        Returns:
            Dictionary with execution summary
        """
        successful = len([r for r in self.execution_records if r.status == "cashout_executed"])
        skipped = len([r for r in self.execution_records if r.status == "skipped"])
        failed = len([r for r in self.execution_records if r.status == "failed"])

        success_rate = (successful / self.total_executions * 100) if self.total_executions > 0 else 0

        return {
            'total_executions': self.total_executions,
            'successful': successful,
            'skipped': skipped,
            'failed': failed,
            'success_rate': success_rate,
            'records': self.execution_records
        }

    def print_execution_summary(self):
        """Print execution statistics"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        summary = self.get_execution_summary()

        print(f"\n[{timestamp}] Supabase Trading Execution Summary:")
        print(f"[{timestamp}] Total executions: {summary['total_executions']}")
        print(f"[{timestamp}] Successful: {summary['successful']}")
        print(f"[{timestamp}] Skipped: {summary['skipped']}")
        print(f"[{timestamp}] Failed: {summary['failed']}")
        print(f"[{timestamp}] Success rate: {summary['success_rate']:.1f}%")
        print(f"[{timestamp}] Strategy: {self.confidence_strategy.value}")
        print(f"[{timestamp}] Confidence threshold: {self.strategy_thresholds[self.confidence_strategy]}%")
