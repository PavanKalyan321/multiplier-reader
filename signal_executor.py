# Automated signal executor - processes trading signals and executes actions
import asyncio
import time
from datetime import datetime
from typing import Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from websocket_listener import TradingSignal, SignalAction
from game_actions import GameActions
from multiplier_reader import MultiplierReader


class ExecutionStatus(Enum):
    """Status of signal execution"""
    PENDING = "pending"
    WAITING_FOR_ROUND = "waiting_for_round"
    PLACED_BET = "placed_bet"
    MONITORING = "monitoring"
    CASHOUT_EXECUTED = "cashout_executed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionRecord:
    """Record of signal execution"""
    signal: TradingSignal
    status: ExecutionStatus = ExecutionStatus.PENDING
    bet_placed_at: Optional[str] = None
    bet_result: bool = False
    cashout_executed_at: Optional[str] = None
    cashout_result: bool = False
    max_multiplier_reached: float = 0.0
    actual_multiplier_at_cashout: float = 0.0
    error_message: str = ""
    details: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return (
            f"Execution(Signal: {self.signal.round_id}, "
            f"Status: {self.status.value}, "
            f"Bet: {self.bet_result}, "
            f"Cashout: {self.cashout_result})"
        )


class SignalExecutor:
    """Execute trading signals automatically"""

    def __init__(self, game_actions: GameActions, multiplier_reader: MultiplierReader):
        """Initialize signal executor

        Args:
            game_actions: GameActions instance for clicking
            multiplier_reader: MultiplierReader instance for monitoring
        """
        self.game_actions = game_actions
        self.multiplier_reader = multiplier_reader
        self.execution_records = []
        self.current_execution: Optional[ExecutionRecord] = None
        self.active_rounds = {}  # Track active round executions by round_id
        self.execution_count = 0
        self.success_count = 0

    def _log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] EXECUTOR {level}: {message}")

    async def execute_signal(self, signal: TradingSignal) -> ExecutionRecord:
        """Execute a trading signal

        Args:
            signal: TradingSignal to execute

        Returns:
            ExecutionRecord with execution details
        """
        self._log(f"Executing signal: {signal}", "INFO")

        record = ExecutionRecord(signal=signal)
        self.execution_count += 1

        try:
            # Validate signal
            if not signal.is_valid():
                record.status = ExecutionStatus.FAILED
                record.error_message = "Invalid signal data"
                self._log(f"Invalid signal: {signal}", "WARNING")
                return record

            # Check if bet should be placed
            if signal.action == SignalAction.PLACE_BET and signal.bet:
                record.status = ExecutionStatus.WAITING_FOR_ROUND
                self._log(f"Waiting for round {signal.round_id} to start", "INFO")

                # Place bet
                self._log(f"Placing bet for round {signal.round_id}", "INFO")
                bet_success = self.game_actions.click_bet_button()

                if bet_success:
                    record.status = ExecutionStatus.PLACED_BET
                    record.bet_placed_at = datetime.now().strftime("%H:%M:%S")
                    record.bet_result = True
                    self._log(f"Bet placed successfully at {record.bet_placed_at}", "INFO")

                    # Start monitoring for cashout
                    record.status = ExecutionStatus.MONITORING
                    await self._monitor_and_cashout(signal, record)
                else:
                    record.status = ExecutionStatus.FAILED
                    record.error_message = "Failed to place bet"
                    self._log("Failed to place bet", "ERROR")

            elif signal.action == SignalAction.HOLD:
                record.status = ExecutionStatus.PENDING
                self._log(f"Signal action is HOLD - no action taken", "INFO")

            elif signal.action == SignalAction.CANCEL:
                record.status = ExecutionStatus.CANCELLED
                self._log(f"Signal action is CANCEL - execution cancelled", "INFO")

            # Record execution
            self.execution_records.append(record)
            self.current_execution = record

            if record.status in [ExecutionStatus.CASHOUT_EXECUTED, ExecutionStatus.PLACED_BET]:
                self.success_count += 1

            return record

        except Exception as e:
            record.status = ExecutionStatus.FAILED
            record.error_message = str(e)
            self._log(f"Execution error: {e}", "ERROR")
            self.execution_records.append(record)
            return record

    async def _monitor_and_cashout(self, signal: TradingSignal, record: ExecutionRecord):
        """Monitor multiplier and execute cashout

        Args:
            signal: Original signal
            record: Execution record to update
        """
        try:
            target_multiplier = signal.expected_multiplier
            max_wait_time = 60  # Maximum seconds to wait before forced cashout
            start_time = time.time()

            self._log(
                f"Monitoring for multiplier target: {target_multiplier}x (max wait: {max_wait_time}s)",
                "INFO"
            )

            while time.time() - start_time < max_wait_time:
                try:
                    # Read current multiplier
                    current_mult = self.multiplier_reader.read_multiplier()

                    if current_mult is not None:
                        record.max_multiplier_reached = max(
                            record.max_multiplier_reached,
                            current_mult
                        )

                        self._log(
                            f"Current: {current_mult:.2f}x | Target: {target_multiplier}x | "
                            f"Max: {record.max_multiplier_reached:.2f}x",
                            "DEBUG"
                        )

                        # Check if target reached or exceeded
                        if current_mult >= target_multiplier:
                            self._log(
                                f"Target multiplier reached! ({current_mult:.2f}x >= {target_multiplier}x)",
                                "INFO"
                            )
                            await self._execute_cashout(signal, record, current_mult)
                            return

                        # Check for crash (multiplier goes to 0)
                        if current_mult < 1:
                            self._log(f"Game crashed before target! Multiplier: {current_mult:.2f}x", "WARNING")
                            record.status = ExecutionStatus.FAILED
                            record.error_message = "Game crashed before cashout"
                            record.actual_multiplier_at_cashout = current_mult
                            return

                    # Small delay before next read
                    await asyncio.sleep(0.1)

                except Exception as e:
                    self._log(f"Error monitoring multiplier: {e}", "WARNING")
                    await asyncio.sleep(0.5)

            # Timeout - force cashout at current multiplier
            self._log(f"Monitor timeout after {max_wait_time}s - forcing cashout", "WARNING")
            current_mult = self.multiplier_reader.read_multiplier() or 0
            await self._execute_cashout(signal, record, current_mult)

        except Exception as e:
            record.status = ExecutionStatus.FAILED
            record.error_message = f"Monitoring error: {e}"
            self._log(f"Monitoring failed: {e}", "ERROR")

    async def _execute_cashout(self, signal: TradingSignal, record: ExecutionRecord, multiplier: float):
        """Execute cashout action

        Args:
            signal: Original signal
            record: Execution record to update
            multiplier: Multiplier at cashout time
        """
        try:
            self._log(f"Executing cashout at {multiplier:.2f}x", "INFO")

            cashout_success = self.game_actions.click_cashout_button()

            if cashout_success:
                record.status = ExecutionStatus.CASHOUT_EXECUTED
                record.cashout_executed_at = datetime.now().strftime("%H:%M:%S")
                record.cashout_result = True
                record.actual_multiplier_at_cashout = multiplier
                self._log(f"Cashout successful at {multiplier:.2f}x", "INFO")
            else:
                record.status = ExecutionStatus.FAILED
                record.error_message = "Failed to execute cashout click"
                self._log("Cashout click failed", "ERROR")

        except Exception as e:
            record.status = ExecutionStatus.FAILED
            record.error_message = f"Cashout error: {e}"
            self._log(f"Cashout error: {e}", "ERROR")

    def get_execution_summary(self) -> dict:
        """Get execution summary statistics"""
        total = len(self.execution_records)
        successful = sum(1 for r in self.execution_records if r.status == ExecutionStatus.CASHOUT_EXECUTED)
        failed = sum(1 for r in self.execution_records if r.status == ExecutionStatus.FAILED)
        pending = sum(1 for r in self.execution_records if r.status == ExecutionStatus.PENDING)

        total_pnl = sum(
            (r.actual_multiplier_at_cashout - 1.0) * 100 if r.cashout_result else -100
            for r in self.execution_records
        )

        return {
            'total_executions': total,
            'successful': successful,
            'failed': failed,
            'pending': pending,
            'success_rate': (successful / total * 100) if total > 0 else 0,
            'total_pnl': total_pnl,
            'records': self.execution_records
        }

    def print_execution_summary(self):
        """Print execution summary"""
        summary = self.get_execution_summary()
        timestamp = datetime.now().strftime("%H:%M:%S")

        print(f"\n[{timestamp}] Signal Execution Summary:")
        print(f"[{timestamp}] Total executions: {summary['total_executions']}")
        print(f"[{timestamp}] Successful: {summary['successful']}")
        print(f"[{timestamp}] Failed: {summary['failed']}")
        print(f"[{timestamp}] Pending: {summary['pending']}")
        print(f"[{timestamp}] Success rate: {summary['success_rate']:.1f}%")
        print(f"[{timestamp}] Total PnL: {summary['total_pnl']:.2f}")

        if self.execution_records:
            print(f"\n[{timestamp}] Recent Executions:")
            for record in self.execution_records[-5:]:
                print(
                    f"[{timestamp}] {record.signal.round_id}: "
                    f"{record.status.value} | "
                    f"Bet: {record.bet_result} | "
                    f"Cashout: {record.actual_multiplier_at_cashout:.2f}x"
                )
