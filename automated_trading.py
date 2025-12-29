# Automated trading system - integrates WebSocket listener with signal executor
import asyncio
from datetime import datetime
from typing import Optional
import json

from websocket_listener import WebSocketListener, TradingSignal
from signal_executor import SignalExecutor
from game_actions import GameActions
from multiplier_reader import MultiplierReader
from screen_capture import ScreenCapture
from config import GameConfig


class AutomatedTradingSystem:
    """Complete automated trading system with WebSocket signals"""

    def __init__(
        self,
        game_config: GameConfig,
        websocket_uri: str = "ws://localhost:8765",
        enable_trading: bool = True
    ):
        """Initialize automated trading system

        Args:
            game_config: GameConfig with all regions and coordinates
            websocket_uri: WebSocket server URI
            enable_trading: Whether to actually execute trades (False for testing)
        """
        self.game_config = game_config
        self.websocket_uri = websocket_uri
        self.enable_trading = enable_trading

        # Initialize components
        self.screen_capture = ScreenCapture(game_config.multiplier_region)
        self.multiplier_reader = MultiplierReader(self.screen_capture)
        self.game_actions = GameActions(game_config.bet_button_point)
        self.websocket_listener = WebSocketListener(websocket_uri)
        self.signal_executor = SignalExecutor(self.game_actions, self.multiplier_reader)

        # State
        self.running = False
        self.execution_task = None
        self.listen_task = None

        self._log(f"Automated Trading System initialized (trading: {enable_trading})", "INFO")

    def _log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] AUTO_TRADE {level}: {message}")

    async def start(self):
        """Start the automated trading system"""
        self._log("Starting automated trading system", "INFO")
        self.running = True

        try:
            # Connect WebSocket
            if not await self.websocket_listener.connect():
                self._log("Failed to connect to WebSocket", "ERROR")
                self.running = False
                return False

            # Start listening for signals
            self.listen_task = asyncio.create_task(self.websocket_listener.listen())

            # Start signal execution loop
            self.execution_task = asyncio.create_task(self._execution_loop())

            self._log("Automated trading system started successfully", "INFO")
            return True

        except Exception as e:
            self._log(f"Failed to start: {e}", "ERROR")
            self.running = False
            return False

    async def stop(self):
        """Stop the automated trading system"""
        self._log("Stopping automated trading system", "INFO")
        self.running = False

        # Cancel tasks
        if self.listen_task:
            self.listen_task.cancel()
        if self.execution_task:
            self.execution_task.cancel()

        # Disconnect WebSocket
        await self.websocket_listener.disconnect()

        self._log("Automated trading system stopped", "INFO")

    async def _execution_loop(self):
        """Main execution loop - processes signals and executes trades"""
        self._log("Signal execution loop started", "INFO")

        try:
            while self.running:
                try:
                    # Wait for signal (timeout 30 seconds)
                    signal = await self.websocket_listener.get_signal(timeout=30)

                    if signal:
                        self._log(f"Processing signal: {signal}", "INFO")

                        if self.enable_trading:
                            # Execute the signal
                            record = await self.signal_executor.execute_signal(signal)
                            self._log(f"Signal execution completed: {record}", "INFO")
                        else:
                            # Testing mode - just log
                            self._log(f"[TEST MODE] Would execute: {signal}", "INFO")

                except asyncio.TimeoutError:
                    # No signal received - continue waiting
                    pass
                except Exception as e:
                    self._log(f"Error in execution loop: {e}", "ERROR")
                    await asyncio.sleep(1)

        except asyncio.CancelledError:
            self._log("Execution loop cancelled", "INFO")
        except Exception as e:
            self._log(f"Execution loop error: {e}", "ERROR")

    async def process_test_signals(self, num_rounds: int = 5):
        """Process test signals for every round (for testing)

        This simulates API signals for testing automation

        Args:
            num_rounds: Number of test rounds to process
        """
        self._log(f"Processing {num_rounds} test signals", "INFO")

        for i in range(num_rounds):
            try:
                # Create test signal
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                signal = TradingSignal(
                    timestamp=timestamp,
                    expected_range=f"1.0-5.0",
                    expected_multiplier=1.5 + (i * 0.1),  # Vary multiplier
                    bet=True,  # Always bet
                    round_id=f"test_round_{i+1}",
                    additional_data={
                        'test': True,
                        'iteration': i + 1
                    }
                )

                self._log(f"Test signal {i+1}/{num_rounds}: {signal}", "INFO")

                if self.enable_trading:
                    record = await self.signal_executor.execute_signal(signal)
                    self._log(f"Test execution {i+1} completed: {record}", "INFO")
                else:
                    self._log(f"[TEST MODE] Would execute signal {i+1}: {signal}", "INFO")

                # Wait between test signals
                await asyncio.sleep(5)

            except Exception as e:
                self._log(f"Error processing test signal {i+1}: {e}", "ERROR")

    def get_system_status(self) -> dict:
        """Get complete system status"""
        return {
            'running': self.running,
            'enable_trading': self.enable_trading,
            'websocket': self.websocket_listener.get_stats(),
            'executor': self.signal_executor.get_execution_summary(),
            'game_actions': self.game_actions.get_click_stats()
        }

    def print_system_status(self):
        """Print system status"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status = self.get_system_status()

        print(f"\n[{timestamp}] Automated Trading System Status:")
        print(f"[{timestamp}] Running: {status['running']}")
        print(f"[{timestamp}] Trading Enabled: {status['enable_trading']}")

        print(f"\n[{timestamp}] WebSocket Status:")
        ws_stats = status['websocket']
        print(f"[{timestamp}]   Connected: {ws_stats['connected']}")
        print(f"[{timestamp}]   Signals received: {ws_stats['signals_received']}")
        print(f"[{timestamp}]   Errors: {ws_stats['errors']}")

        print(f"\n[{timestamp}] Execution Status:")
        exec_stats = status['executor']
        print(f"[{timestamp}]   Total executions: {exec_stats['total_executions']}")
        print(f"[{timestamp}]   Successful: {exec_stats['successful']}")
        print(f"[{timestamp}]   Failed: {exec_stats['failed']}")
        print(f"[{timestamp}]   Success rate: {exec_stats['success_rate']:.1f}%")

        print(f"\n[{timestamp}] Click Statistics:")
        click_stats = status['game_actions']
        print(f"[{timestamp}]   Total clicks: {click_stats['total_clicks']}")
        print(f"[{timestamp}]   Successful: {click_stats['successful_clicks']}")
        print(f"[{timestamp}]   Failed: {click_stats['failed_clicks']}")


async def run_automated_trading(
    game_config: GameConfig,
    websocket_uri: str = "ws://localhost:8765",
    test_mode: bool = False,
    num_test_rounds: int = 5
):
    """Run automated trading system

    Args:
        game_config: GameConfig with regions and coordinates
        websocket_uri: WebSocket server URI
        test_mode: Whether to run in test mode (no actual trades)
        num_test_rounds: Number of test rounds for test mode
    """
    system = AutomatedTradingSystem(
        game_config=game_config,
        websocket_uri=websocket_uri,
        enable_trading=not test_mode
    )

    try:
        # Start the system
        if not await system.start():
            return

        if test_mode:
            # Process test signals
            await system.process_test_signals(num_test_rounds)
        else:
            # Run indefinitely until interrupted
            print("\nAutomated trading system running. Press Ctrl+C to stop.")
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\nShutdown requested...")

        # Print final status
        system.print_system_status()

    except Exception as e:
        print(f"\nError: {e}")
    finally:
        await system.stop()


if __name__ == "__main__":
    # Example usage
    from config import load_game_config

    async def main():
        config = load_game_config()
        if not config or not config.is_valid():
            print("Error: No valid game configuration found")
            return

        # Run in test mode for demonstration
        await run_automated_trading(
            game_config=config,
            websocket_uri="ws://localhost:8765",
            test_mode=True,
            num_test_rounds=3
        )

    asyncio.run(main())
