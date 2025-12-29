# Supabase-based automated trading system orchestrator
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any

from supabase_client import SupabaseLogger
from supabase_signal_listener import SupabaseSignalListener
from supabase_trading_executor import SupabaseExecutor, ConfidenceStrategy
from config import GameConfig
from screen_capture import ScreenCapture
from multiplier_reader import MultiplierReader
from game_actions import GameActions


class SupabaseAutomatedTradingSystem:
    """Automated trading system based on Supabase signals with confidence-based execution"""

    def __init__(
        self,
        game_config: GameConfig,
        supabase_url: str,
        supabase_key: str,
        poll_interval: float = 5.0,
        confidence_strategy: str = "moderate",
        enable_trading: bool = True
    ):
        """Initialize Supabase automated trading system

        Args:
            game_config: GameConfig with regions and button points
            supabase_url: Supabase project URL
            supabase_key: Supabase API key
            poll_interval: Polling interval in seconds (default 5s)
            confidence_strategy: Trading strategy ("conservative", "moderate", "aggressive")
            enable_trading: Whether to execute real trades
        """
        self.game_config = game_config
        self.poll_interval = poll_interval
        self.enable_trading = enable_trading
        self.running = False

        # Map strategy string to enum
        strategy_map = {
            "conservative": ConfidenceStrategy.CONSERVATIVE,
            "moderate": ConfidenceStrategy.MODERATE,
            "aggressive": ConfidenceStrategy.AGGRESSIVE
        }
        self.confidence_strategy = strategy_map.get(confidence_strategy, ConfidenceStrategy.MODERATE)

        # Initialize Supabase
        self.supabase_logger = SupabaseLogger(supabase_url, supabase_key)
        self.listener = SupabaseSignalListener(self.supabase_logger)

        # Initialize trading components
        self.screen_capture = ScreenCapture(game_config.multiplier_region)
        self.multiplier_reader = MultiplierReader(self.screen_capture)
        self.game_actions = GameActions(game_config.bet_button_point)

        # Initialize executor
        self.executor = SupabaseExecutor(
            listener=self.listener,
            multiplier_reader=self.multiplier_reader,
            game_actions=self.game_actions,
            confidence_strategy=self.confidence_strategy
        )

        self.listen_task = None
        self.execution_task = None

    def _log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] SUPABASE_AUTO_TRADE {level}: {message}")

    async def start(self) -> bool:
        """Start the automated trading system

        Returns:
            True if started successfully
        """
        self._log("Starting Supabase automated trading system...", "INFO")

        try:
            # Verify components
            if not self.game_config.is_valid():
                self._log("Invalid game configuration", "ERROR")
                return False

            # Start listener task
            self.listen_task = asyncio.create_task(
                self.listener.listen(poll_interval=self.poll_interval)
            )

            # Start execution task
            self.execution_task = asyncio.create_task(self._execution_loop())

            self.running = True
            self._log("System started successfully", "INFO")
            return True

        except Exception as e:
            self._log(f"Failed to start system: {e}", "ERROR")
            return False

    async def stop(self):
        """Stop the automated trading system"""
        self._log("Stopping system...", "INFO")
        self.running = False

        if self.listen_task:
            self.listen_task.cancel()
        if self.execution_task:
            self.execution_task.cancel()

        try:
            if self.listen_task:
                await self.listen_task
        except asyncio.CancelledError:
            pass

        try:
            if self.execution_task:
                await self.execution_task
        except asyncio.CancelledError:
            pass

        self._log("System stopped", "INFO")

    async def _execution_loop(self):
        """Main execution loop - waits for signals and executes"""
        self._log("Execution loop started", "INFO")

        try:
            while self.running:
                try:
                    # Get next signal with timeout
                    signal = await self.listener.get_signal(timeout=30.0)

                    if signal is None:
                        await asyncio.sleep(0.1)
                        continue

                    self._log(f"Processing signal: {signal}", "INFO")

                    if self.enable_trading:
                        # Execute signal
                        record = await self.executor.execute_signal(signal)
                        self._log(
                            f"Execution completed - Status: {record.status}, "
                            f"Multiplier: {record.actual_multiplier_at_cashout:.2f}x",
                            "INFO"
                        )
                    else:
                        self._log(f"Trading disabled - signal received but not executed", "INFO")

                    await asyncio.sleep(0.1)

                except Exception as e:
                    self._log(f"Error in execution loop: {e}", "ERROR")
                    await asyncio.sleep(1.0)

        except asyncio.CancelledError:
            self._log("Execution loop cancelled", "INFO")

    def get_system_status(self) -> Dict[str, Any]:
        """Get complete system status

        Returns:
            Dictionary with full system status
        """
        listener_stats = self.listener.get_stats()
        executor_summary = self.executor.get_execution_summary()
        click_stats = self.game_actions.get_click_stats()

        return {
            'running': self.running,
            'enable_trading': self.enable_trading,
            'confidence_strategy': self.confidence_strategy.value,
            'poll_interval': self.poll_interval,
            'listener': listener_stats,
            'executor': executor_summary,
            'game_actions': click_stats
        }

    def print_system_status(self):
        """Print comprehensive system status"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status = self.get_system_status()

        print(f"\n[{timestamp}] Supabase Automated Trading System Status:")
        print(f"[{timestamp}] Running: {status['running']}")
        print(f"[{timestamp}] Trading Enabled: {status['enable_trading']}")
        print(f"[{timestamp}] Confidence Strategy: {status['confidence_strategy']}")
        print(f"[{timestamp}] Poll Interval: {status['poll_interval']}s")
        print(f"\n[{timestamp}] Listener Status:")
        print(f"[{timestamp}]   Signals received: {status['listener']['signals_received']}")
        print(f"[{timestamp}]   Errors: {status['listener']['errors']}")
        print(f"[{timestamp}]   Queue size: {status['listener']['queue_size']}")
        print(f"\n[{timestamp}] Executor Status:")
        print(f"[{timestamp}]   Total executions: {status['executor']['total_executions']}")
        print(f"[{timestamp}]   Successful: {status['executor']['successful']}")
        print(f"[{timestamp}]   Skipped: {status['executor']['skipped']}")
        print(f"[{timestamp}]   Failed: {status['executor']['failed']}")
        print(f"[{timestamp}]   Success rate: {status['executor']['success_rate']:.1f}%")


async def run_supabase_automated_trading(
    game_config: GameConfig,
    supabase_url: str,
    supabase_key: str,
    poll_interval: float = 5.0,
    confidence_strategy: str = "moderate",
    enable_trading: bool = True,
    test_mode: bool = False
):
    """Run Supabase automated trading system

    Args:
        game_config: GameConfig with regions and button coordinates
        supabase_url: Supabase project URL
        supabase_key: Supabase API key
        poll_interval: Polling interval in seconds
        confidence_strategy: Trading strategy
        enable_trading: Whether to execute actual trades
        test_mode: If True, won't execute trades (safe for testing)
    """
    system = SupabaseAutomatedTradingSystem(
        game_config=game_config,
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        poll_interval=poll_interval,
        confidence_strategy=confidence_strategy,
        enable_trading=enable_trading and not test_mode
    )

    print("\n" + "=" * 60)
    print("SUPABASE AUTOMATED TRADING SYSTEM".center(60))
    print("=" * 60)
    if test_mode:
        print("MODE: TEST (no real trades)".center(60))
    else:
        print("MODE: PRODUCTION (real trades)".center(60))
    print("=" * 60 + "\n")

    try:
        if not await system.start():
            print("Failed to start system")
            return

        print("System running. Press Ctrl+C to stop.\n")

        # Keep system running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n\nShutting down...")
    finally:
        await system.stop()
        system.print_system_status()
