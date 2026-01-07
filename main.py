# Main monitoring loop for multiplier reader
import time
import sys
import json
import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from config import load_config, get_default_region, load_game_config, GameConfig, migrate_old_config
from screen_capture import ScreenCapture
from multiplier_reader import MultiplierReader
from balance_reader import BalanceReader
from game_actions import GameActions
from game_tracker import GameTracker
from supabase_client import SupabaseLogger
from prediction_engine import PredictionEngine
from analytics_client import AnalyticsClient
from azure_foundry_client import AzureFoundryClient
from browser_refresh import BrowserRefresh
from auto_refresher import AutoRefresher
from menu_controller import MenuController
from unified_region_selector import run_unified_gui
from automated_trading import run_automated_trading
from supabase_automated_trading import run_supabase_automated_trading
from betting_helpers import demo_mode_simple_bet, demo_mode_real_multiplier, demo_mode_continuous
from pycaret_signal_listener import PyCaretSignalListener
from model_realtime_listener import ModelRealtimeListener


class Colors:
    """ANSI color codes for terminal"""
    RESET = '\033[0m'
    BOLD = '\033[1m'

    # Status colors
    GREEN = '\033[92m'   # Low multiplier (1x-3x)
    YELLOW = '\033[93m'  # Medium (3x-7x)
    RED = '\033[91m'     # High (7x-10x)
    MAGENTA = '\033[95m' # Very high (10x+)

    # Info colors
    CYAN = '\033[96m'
    GRAY = '\033[90m'
    WHITE = '\033[97m'

    @staticmethod
    def get_multiplier_color(mult):
        """Get color based on multiplier value"""
        if mult >= 10:
            return Colors.MAGENTA
        elif mult >= 7:
            return Colors.RED
        elif mult >= 3:
            return Colors.YELLOW
        else:
            return Colors.GREEN


class MultiplierReaderApp:
    """Main application for monitoring game multiplier"""

    def __init__(self, region=None, config=None, update_interval=0.5):
        # Handle both legacy region parameter and new GameConfig parameter
        if config:
            self.config = config
            self.region = config.multiplier_region
        else:
            self.region = region or load_config() or get_default_region()
            self.config = None

        self.update_interval = update_interval
        self.screen_capture = ScreenCapture(self.region)
        self.multiplier_reader = MultiplierReader(self.screen_capture)

        # Initialize new components if GameConfig is provided
        if self.config:
            self.balance_screen_capture = ScreenCapture(self.config.balance_region)
            self.balance_reader = BalanceReader(self.balance_screen_capture)
            self.game_actions = GameActions(self.config.bet_button_point)
        else:
            self.balance_reader = None
            self.game_actions = None

        self.game_tracker = GameTracker()
        self.running = False
        self.previous_round_count = 0
        self.is_round_running = False
        self.last_status_msg = ""
        self.status_printed = False
        self.multiplier_history = []  # Track last N multipliers for sparkline
        self.max_history = 10  # Keep last 10 values

        # Initialize Supabase logger
        self.supabase = SupabaseLogger(
            url='https://zofojiubrykbtmstfhzx.supabase.co',
            key='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvZm9qaXVicnlrYnRtc3RmaHp4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM4NzU0OTEsImV4cCI6MjA3OTQ1MTQ5MX0.mxwvnhT-ouONWff-gyqw67lKon82nBx2fsbd8meyc8s'
        )

        # Initialize prediction engine and analytics client
        self.prediction_engine = PredictionEngine()
        self.analytics_client = AnalyticsClient(self.supabase.client if self.supabase.enabled else None)

        # Initialize Azure AI Foundry client
        self.azure_foundry_client = AzureFoundryClient(
            endpoint_url=os.getenv('AZURE_FOUNDRY_ENDPOINT'),
            api_key=os.getenv('AZURE_FOUNDRY_API_KEY')
        )

        # Initialize browser refresh manager (refresh every 30 minutes)
        self.browser_refresh = BrowserRefresh(refresh_interval_minutes=30)

        # Initialize auto-refresher (refresh every 15 minutes)
        self.auto_refresher = AutoRefresher(self.region, refresh_interval=900)  # 900 seconds = 15 minutes

        self.stats = {
            'total_updates': 0,
            'successful_reads': 0,
            'failed_reads': 0,
            'crashes_detected': 0,
            'max_multiplier_ever': 0,
            'start_time': datetime.now(),
            'supabase_inserts': 0,      # Track successful inserts
            'supabase_failures': 0,      # Track failed inserts
            'predictions_generated': 0,  # Track predictions made
            'signals_saved': 0,          # Track signals saved to analytics
            'browser_refreshes': 0,      # Track browser refreshes
            'azure_predictions': 0,      # Track Azure predictions
            'azure_failures': 0,         # Track Azure failures
            'fallback_predictions': 0,   # Track fallback predictions
        }

    def _check_and_refresh_browser(self):
        """Check if browser needs refresh and perform it"""
        if self.browser_refresh.should_refresh():
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{timestamp}] INFO: Browser refresh interval reached. Refreshing to prevent session expiration...")

            # Try standard refresh first (F5)
            success = self.browser_refresh.refresh_browser()

            if success:
                self.stats['browser_refreshes'] += 1
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] INFO: Browser refresh successful - Session extended")
            else:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] WARNING: Browser refresh may have failed - Check browser window")

    def _prepare_rounds_for_prediction(self):
        """Convert game_tracker round history to format expected by prediction engine"""
        if not self.game_tracker.round_history:
            return []

        rounds = []
        for round_data in self.game_tracker.round_history:
            rounds.append({
                'multiplier': round_data.max_multiplier,
                'timestamp': datetime.fromtimestamp(round_data.end_time).isoformat(),
                'duration': round_data.duration,
                'crash_at': round_data.crash_multiplier
            })
        return rounds

    def _trigger_azure_prediction(self, round_summary):
        """
        Request prediction from Azure AI Foundry with fallback to local prediction

        Args:
            round_summary: Round summary data from game_tracker
        """
        timestamp = datetime.now().strftime("%H:%M:%S")

        try:
            # Request from Azure AI Foundry
            result = self.azure_foundry_client.request_prediction(
                round_id=round_summary.round_number,
                round_number=round_summary.round_number
            )

            if result.get('status') == 'success':
                self.stats['azure_predictions'] += 1
                self.stats['signals_saved'] += 1
                print(f"[{timestamp}] SUCCESS: Azure AI Foundry prediction completed")
            else:
                raise Exception(f"Azure error: {result.get('error', 'Unknown error')}")

        except Exception as e:
            # Fallback to local prediction
            self.stats['azure_failures'] += 1
            print(f"[{timestamp}] WARNING: Azure unavailable, using local fallback")
            print(f"[{timestamp}]   Error: {str(e)}")

            try:
                # Prepare round history for prediction
                rounds_data = self._prepare_rounds_for_prediction()

                # Train prediction engine with historical data
                print(f"[{timestamp}] INFO: Training local prediction models with {len(rounds_data)} rounds...")
                self.prediction_engine.train(rounds_data)

                # Make prediction for next round
                prediction = self.prediction_engine.predict(rounds_data)

                if prediction:
                    self.stats['predictions_generated'] += 1
                    self.stats['fallback_predictions'] += 1

                    # Calculate volatility and momentum metrics
                    volatility = self.prediction_engine.calculate_volatility(rounds_data)
                    momentum = self.prediction_engine.calculate_momentum(rounds_data)

                    # Get ensemble prediction
                    ensemble_pred = prediction.get('ensemble', {})
                    signal_type = self.analytics_client._get_pattern_type(
                        prediction.get('features', {})
                    )

                    print(f"[{timestamp}] INFO: Local prediction complete (fallback)")
                    print(f"[{timestamp}]   - Signal: {ensemble_pred.get('prediction', 'N/A')} (confidence: {ensemble_pred.get('confidence', 0):.2%})")
                    print(f"[{timestamp}]   - Volatility: {volatility:.3f}, Momentum: {momentum:.3f}")

                    # Insert signal into analytics_round_signals table
                    signal_inserted = self.analytics_client.insert_signal(
                        round_id=round_summary.round_number,
                        round_number=round_summary.round_number,
                        prediction=prediction,
                        volatility=volatility,
                        momentum=momentum,
                        bot_id="multiplier-reader-fallback",
                        game_name="aviator"
                    )

                    if signal_inserted:
                        self.stats['signals_saved'] += 1
                        print(f"[{timestamp}] INFO: Fallback signal saved to analytics_round_signals")
                    else:
                        print(f"[{timestamp}] WARNING: Failed to save fallback signal")

            except Exception as fallback_error:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] ERROR: Fallback prediction also failed: {fallback_error}")

    def generate_sparkline(self, values, width=10):
        """Generate ASCII sparkline from values"""
        if not values or len(values) < 2:
            return ' ' * min(width, len(values) if values else 1)

        # Normalize values to 0-7 range for block chars
        min_val = min(values)
        max_val = max(values)

        if max_val == min_val:
            return '-' * min(len(values), width)

        # Use ASCII characters that work in most terminals
        blocks = ['_', '.', '-', '=', '^', '*', '#', '@']

        result = []
        for val in values[-width:]:
            normalized = int(((val - min_val) / (max_val - min_val)) * 7)
            result.append(blocks[normalized])

        return ''.join(result)

    def log_event(self, event):
        """Log events with color coding"""
        if event.event_type == 'CRASH':
            max_mult = event.details.get('max_multiplier', 'N/A')
            duration = event.details.get('round_duration', 0)
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n{Colors.GRAY}[{timestamp}]{Colors.RESET} {Colors.RED}{Colors.BOLD}[CRASH]{Colors.RESET} Reached {Colors.MAGENTA}{max_mult}x{Colors.RESET} in {duration:.2f}s")
            self.stats['crashes_detected'] += 1
        elif event.event_type == 'GAME_START':
            timestamp = datetime.now().strftime("%H:%M:%S")
            round_num = self.game_tracker.round_number + 1
            print(f"{Colors.GRAY}[{timestamp}]{Colors.RESET} {Colors.GREEN}{Colors.BOLD}[START]{Colors.RESET} ROUND {round_num} STARTED")
            self.is_round_running = True
            self.multiplier_history = []  # Reset sparkline on new round
        elif event.event_type == 'HIGH_MULTIPLIER':
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"{Colors.GRAY}[{timestamp}]{Colors.RESET} {Colors.MAGENTA}{Colors.BOLD}[HIGH]{Colors.RESET} MULTIPLIER: {Colors.MAGENTA}{event.multiplier:.2f}x{Colors.RESET}")
        # NOTE: MULTIPLIER_INCREASE events are NOT logged to avoid clutter - shown only in status line

    def check_and_log_round_completion(self):
        """Check if a new round was completed and log it"""
        current_round_count = len(self.game_tracker.round_history)
        if current_round_count > self.previous_round_count:
            # A new round was just completed
            new_round = self.game_tracker.round_history[-1]
            self.log_round_completion(new_round)
            self.previous_round_count = current_round_count
            self.is_round_running = False

    def log_round_completion(self, round_summary):
        """Log a completed round with formatted table and save to Supabase"""
        print("\n")
        print("ROUND ENDED")
        print()

        # Log the complete round history table
        history_table = self.game_tracker.format_round_history_table(limit=None)
        print(history_table)

        # Insert round data into Supabase
        round_end_time = datetime.fromtimestamp(round_summary.end_time)
        success = self.supabase.insert_round(
            round_number=round_summary.round_number,
            multiplier=round_summary.max_multiplier,  # Use max_multiplier as final multiplier
            timestamp=round_end_time
        )

        # Update stats
        if success:
            self.stats['supabase_inserts'] += 1
        else:
            self.stats['supabase_failures'] += 1

        # Trigger prediction pipeline if we have enough historical data
        if len(self.game_tracker.round_history) >= 5:
            self._trigger_azure_prediction(round_summary)

        print()
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] INFO: Waiting for next round...")

    def update_step(self):
        """Single update step"""
        self.stats['total_updates'] += 1

        # Check if browser refresh is needed
        self._check_and_refresh_browser()

        result = self.multiplier_reader.get_multiplier_with_status()

        if result['multiplier'] is None:
            self.stats['failed_reads'] += 1
            # Pass None to game_tracker to trigger crash detection
            events = self.game_tracker.update(None, 'UNKNOWN')

            # Log crash event if generated
            for event in events:
                self.log_event(event)

            # Check if round was just completed
            self.check_and_log_round_completion()
            return

        self.stats['successful_reads'] += 1
        multiplier = result['multiplier']
        status = result['status']

        # Update tracker and get events
        events = self.game_tracker.update(multiplier, status)

        # Log events
        for event in events:
            self.log_event(event)

        # Check if round was just completed (after crash event)
        self.check_and_log_round_completion()

        # Update stats
        if multiplier > self.stats['max_multiplier_ever']:
            self.stats['max_multiplier_ever'] = multiplier

        # Print current state
        round_summary = self.game_tracker.get_round_summary()
        self.print_status(multiplier, status, round_summary)

    def print_status(self, multiplier, status, round_summary):
        """Print enhanced status with colors and sparkline"""
        if round_summary['status'] == 'RUNNING' and 'current_multiplier' in round_summary:
            max_mult = round_summary['max_multiplier']
            current = round_summary['current_multiplier']
            round_num = self.game_tracker.round_number

            # Track multiplier history for sparkline
            self.multiplier_history.append(current)
            if len(self.multiplier_history) > self.max_history:
                self.multiplier_history.pop(0)

            # Generate sparkline
            sparkline = self.generate_sparkline(self.multiplier_history)

            # Get color based on multiplier
            color = Colors.get_multiplier_color(current)

            # Build status line with dynamic multiplier (updates on same line)
            # Format: [TIME] R:X | CURR: X.XXx MAX: X.XXx | TREND: sparkline
            timestamp = datetime.now().strftime("%H:%M:%S")
            status_line = (
                f"\r{Colors.GRAY}[{timestamp}]{Colors.RESET} "
                f"{Colors.CYAN}R:{round_num+1}{Colors.RESET} | "
                f"{Colors.BOLD}CURR:{Colors.RESET} {color}{current:5.2f}x{Colors.RESET} "
                f"{Colors.BOLD}MAX:{Colors.RESET} {Colors.MAGENTA}{max_mult:5.2f}x{Colors.RESET} | "
                f"{Colors.BOLD}TREND:{Colors.RESET} {color}{sparkline}{Colors.RESET}"
            )

            # Print every update without newline (carriage return updates same line)
            # status_key tracks when to log a new line (only on max_mult or round change)
            status_key = f"{round_num}|{max_mult:.2f}"

            # Always print multiplier updates on same line
            print(status_line, end='', flush=True)

            # Only create new line when max multiplier or round changes
            if status_key != self.last_status_msg:
                print()  # New line when max changes
                self.last_status_msg = status_key
                self.status_printed = True

    def read_current_balance(self):
        """Read current balance value

        Returns:
            float: Balance amount or None if failed
        """
        if not self.balance_reader:
            return None

        return self.balance_reader.read_balance()

    def place_bet(self) -> bool:
        """Place a bet by clicking the bet button

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.game_actions:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] ERROR: Game actions not configured")
            return False

        return self.game_actions.click_bet_button()

    def cashout(self) -> bool:
        """Cashout by clicking the cashout button

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.game_actions:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] ERROR: Game actions not configured")
            return False

        return self.game_actions.click_cashout_button()

    def print_stats(self):
        """Print statistics"""
        elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
        success_rate = (self.stats['successful_reads'] / self.stats['total_updates'] * 100) if self.stats['total_updates'] > 0 else 0

        print("\n")
        print("=" * 80)
        print("FINAL STATISTICS")
        print("=" * 80)
        print()

        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] INFO: Elapsed time: {elapsed:.1f}s")
        print(f"[{timestamp}] INFO: Total updates: {self.stats['total_updates']}")
        print(f"[{timestamp}] INFO: Successful reads: {self.stats['successful_reads']}")
        print(f"[{timestamp}] INFO: Failed reads: {self.stats['failed_reads']}")
        print(f"[{timestamp}] INFO: Success rate: {success_rate:.1f}%")
        print(f"[{timestamp}] INFO: Crashes detected: {self.stats['crashes_detected']}")
        print(f"[{timestamp}] INFO: Max multiplier ever: {self.stats['max_multiplier_ever']:.2f}x")

        # Show Supabase statistics
        if self.supabase.enabled:
            print(f"[{timestamp}] INFO: Supabase inserts: {self.stats['supabase_inserts']}")
            print(f"[{timestamp}] INFO: Supabase failures: {self.stats['supabase_failures']}")

        # Show prediction statistics
        print(f"[{timestamp}] INFO: Predictions generated: {self.stats['predictions_generated']}")
        print(f"[{timestamp}] INFO: Signals saved: {self.stats['signals_saved']}")

        # Show browser refresh statistics
        print(f"[{timestamp}] INFO: Browser refreshes: {self.stats['browser_refreshes']}")

        # Show click statistics
        if self.game_actions:
            print()
            self.game_actions.print_click_stats()

        print()

        # Print round history
        if self.game_tracker.round_history:
            history_table = self.game_tracker.format_round_history_table(limit=None)
            print(history_table)
        else:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] WARNING: No completed rounds yet.")

        print()

    def run(self):
        """Main run loop"""
        self.running = True
        print("=" * 80)
        print("MULTIPLIER READER")
        print("=" * 80)
        print()

        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] INFO: Started")
        print(f"[{timestamp}] INFO: Region: ({self.region.x1}, {self.region.y1}) to ({self.region.x2}, {self.region.y2})")
        print(f"[{timestamp}] INFO: Update interval: {self.update_interval}s")
        print(f"[{timestamp}] INFO: Press Ctrl+C to stop")
        print()

        # Start auto-refresher
        self.auto_refresher.start()

        print(f"[{datetime.now().strftime('%H:%M:%S')}] STATUS: WAITING for first round...")

        try:
            while self.running:
                self.update_step()
                time.sleep(self.update_interval)
        except KeyboardInterrupt:
            print("\n")
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] WARNING: Stopping multiplier reader...")
            # Stop auto-refresher
            self.auto_refresher.stop()
            self.print_stats()

def test_configuration():
    """Test current configuration by reading balance and multiplier"""
    timestamp = datetime.now().strftime("%H:%M:%S")

    config = load_game_config()
    if not config or not config.is_valid():
        print("\n" + "!" * 60)
        print("Configuration is not complete!".center(60))
        print("!" * 60)
        print("\nPlease configure the regions first.")
        input("\nPress Enter to continue...")
        return

    print("\n" + "=" * 60)
    print("TESTING CONFIGURATION".center(60))
    print("=" * 60 + "\n")

    # Create temporary app for testing
    app = MultiplierReaderApp(config=config)

    print(f"[{timestamp}] INFO: Testing balance reader...")
    balance = app.read_current_balance()
    if balance is not None:
        print(f"[{timestamp}] SUCCESS: Balance read: {balance:.2f}")
    else:
        print(f"[{timestamp}] WARNING: Could not read balance")

    print(f"\n[{timestamp}] INFO: Testing multiplier reader...")
    result = app.multiplier_reader.get_multiplier_with_status()
    if result['multiplier'] is not None:
        print(f"[{timestamp}] SUCCESS: Multiplier read: {result['multiplier']:.2f}x")
    else:
        print(f"[{timestamp}] WARNING: Could not read multiplier")

    print(f"\n[{timestamp}] INFO: Bet button coordinates: ({config.bet_button_point.x}, {config.bet_button_point.y})")
    print(f"[{timestamp}] INFO: (Button test: NOT clicking to avoid accidental bets)")

    print("\n" + "=" * 60)
    input("Press Enter to continue...")


def websocket_trading():
    """Start WebSocket-based automated trading"""
    config = load_game_config()
    if not config or not config.is_valid():
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] ERROR: Invalid configuration")
        input("\nPress Enter to continue...")
        return

    print("\n" + "=" * 60)
    print("WebSocket Automated Trading Setup".center(60))
    print("=" * 60 + "\n")

    # Get WebSocket URI from user
    uri = input("Enter WebSocket URI (default: ws://localhost:8765): ").strip()
    if not uri:
        uri = "ws://localhost:8765"

    # Ask for test mode
    test_input = input("Run in test mode? (y/n, default: y): ").strip().lower()
    test_mode = test_input != 'n'

    print("\nStarting WebSocket automated trading...")
    print(f"URI: {uri}")
    print(f"Test Mode: {test_mode}\n")

    try:
        asyncio.run(run_automated_trading(
            game_config=config,
            websocket_uri=uri,
            test_mode=test_mode,
            num_test_rounds=5 if test_mode else 0
        ))
    except KeyboardInterrupt:
        print("\n\nWebSocket trading stopped.")
    except Exception as e:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] ERROR: {e}")
    finally:
        input("\nPress Enter to return to menu...")


def supabase_trading():
    """Start Supabase-based automated trading"""
    config = load_game_config()
    if not config or not config.is_valid():
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] ERROR: Invalid configuration")
        input("\nPress Enter to continue...")
        return

    print("\n" + "=" * 60)
    print("Supabase Automated Trading Setup".center(60))
    print("=" * 60 + "\n")

    # Get Supabase credentials from user
    supabase_url = input("Enter Supabase Project URL: ").strip()
    if not supabase_url:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] ERROR: Supabase URL is required")
        input("\nPress Enter to continue...")
        return

    supabase_key = input("Enter Supabase API Key: ").strip()
    if not supabase_key:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] ERROR: Supabase API Key is required")
        input("\nPress Enter to continue...")
        return

    # Ask for confidence strategy
    print("\nConfidence Strategies:")
    print("1. Conservative (only >80% confidence)")
    print("2. Moderate (only >60% confidence) - default")
    print("3. Aggressive (only >40% confidence)")
    strategy_choice = input("Select strategy (1-3, default: 2): ").strip()

    strategy_map = {"1": "conservative", "2": "moderate", "3": "aggressive"}
    strategy = strategy_map.get(strategy_choice, "moderate")

    # Ask for test mode
    test_input = input("Run in test mode? (y/n, default: y): ").strip().lower()
    test_mode = test_input != 'n'

    # Ask for polling interval
    poll_interval_input = input("Enter polling interval in seconds (default: 5): ").strip()
    try:
        poll_interval = float(poll_interval_input) if poll_interval_input else 5.0
    except ValueError:
        poll_interval = 5.0

    print("\nStarting Supabase automated trading...")
    print(f"URL: {supabase_url}")
    print(f"Strategy: {strategy}")
    print(f"Test Mode: {test_mode}")
    print(f"Poll Interval: {poll_interval}s\n")

    try:
        asyncio.run(run_supabase_automated_trading(
            game_config=config,
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            poll_interval=poll_interval,
            confidence_strategy=strategy,
            enable_trading=not test_mode,
            test_mode=test_mode
        ))
    except KeyboardInterrupt:
        print("\n\nSupabase trading stopped.")
    except Exception as e:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] ERROR: {e}")
    finally:
        input("\nPress Enter to return to menu...")


def demo_mode():
    """Run continuous demo mode betting with REAL multiplier monitoring and AUTO-CASHOUT"""
    try:
        config = load_game_config()

        if not config or not config.is_valid():
            print("\n" + "!" * 60)
            print("Configuration is not complete!".center(60))
            print("!" * 60)
            print("\nPlease configure the regions first (option 2).")
            input("\nPress Enter to return to menu...")
            return

        print("\n" + "=" * 60)
        print("CONTINUOUS DEMO MODE - AUTO-CASHOUT".center(60))
        print("=" * 60)
        print("\nContinuous demo mode will:")
        print("  1. Run multiple rounds automatically")
        print("  2. Set stake to 10 per round")
        print("  3. Place bets and monitor REAL multiplier")
        print("  4. AUTO-CLICK cashout when multiplier reaches 1.3x")
        print("  5. Display results and summary")
        print()

        # Get number of rounds from user
        try:
            rounds_input = input("Enter number of rounds (default 3): ").strip()
            num_rounds = int(rounds_input) if rounds_input else 3
            if num_rounds < 1:
                num_rounds = 3
        except ValueError:
            num_rounds = 3

        # Initialize stats
        stats = {
            'rounds_played': 0,
            'ml_bets_placed': 0,
            'total_bet': 0
        }

        # Initialize multiplier reader to read REAL multiplier values
        screen_capture = ScreenCapture(config.multiplier_region)
        multiplier_reader = MultiplierReader(screen_capture)

        print(f"\nInitializing continuous demo with {num_rounds} rounds...")
        print()

        # Run continuous demo mode with AUTO-CASHOUT
        result = demo_mode_continuous(
            stake_coords=(config.bet_button_point.x, config.bet_button_point.y - 100),
            bet_button_coords=(config.bet_button_point.x, config.bet_button_point.y),
            cashout_coords=(config.bet_button_point.x, config.bet_button_point.y),
            detector=None,
            stats=stats,
            multiplier_reader=multiplier_reader,
            demo_stake=10,
            target_multiplier=1.3,
            num_rounds=num_rounds
        )

        print("\n" + "=" * 60)
        print("CONTINUOUS DEMO SUMMARY".center(60))
        print("=" * 60)
        summary = result.get('summary', {})
        print(f"Total Rounds:       {result['num_rounds']}")
        print(f"Successful Cashouts: {summary.get('wins', 0)}")
        print(f"Failed Rounds:      {summary.get('losses', 0)}")
        print(f"Win Rate:           {summary.get('win_rate', 0):.1f}%")
        print(f"Total Bet:          {summary.get('total_bet', 0)}")
        print(f"Total Winnings:     {summary.get('total_winnings', 0):.2f}")
        print(f"Total Profit:       {summary.get('total_profit', 0):.2f}")
        print(f"Mode:               Continuous AUTO-CASHOUT")
        print("=" * 60)
        input("\nPress Enter to return to menu...")

    except KeyboardInterrupt:
        print("\n\nDemo mode stopped by user.")
    except Exception as e:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nPress Enter to return to menu...")


def pycaret_trading():
    """Start real-time model listener for analytics_round_signals (model-agnostic)"""
    try:
        config = load_game_config()

        if not config or not config.is_valid():
            print("\n" + "!" * 60)
            print("Configuration is not complete!".center(60))
            print("!" * 60)
            print("\nPlease configure the regions first (option 2).")
            input("\nPress Enter to return to menu...")
            return

        print("\n" + "=" * 60)
        print("Real-Time Model Signal Listener".center(60))
        print("=" * 60)

        # Display available models
        available_models = [
            "PyCaret", "H2O_AutoML", "AutoSklearn", "LSTM_Model", "AutoGluon",
            "RandomForest_AutoML", "CatBoost", "LightGBM_AutoML", "XGBoost_AutoML",
            "MLP_NeuralNet", "TPOT_Genetic", "AutoKeras", "AutoPyTorch", "MLBox",
            "TransmogrifAI", "Google_AutoML"
        ]

        print("\nAvailable Models:")
        for i, model in enumerate(available_models, 1):
            print(f"  {i}. {model}")

        # Get model selection from user
        while True:
            model_input = input("\nEnter model name or number (default: PyCaret): ").strip()
            if not model_input:
                model_name = "PyCaret"
                break
            elif model_input.isdigit() and 1 <= int(model_input) <= len(available_models):
                model_name = available_models[int(model_input) - 1]
                break
            elif model_input in available_models:
                model_name = model_input
                break
            else:
                print("Invalid model. Please enter a valid model name or number.")

        # Get betting criteria from user
        min_predicted_input = input("Enter min predicted multiplier (default: 1.3): ").strip()
        try:
            min_predicted = float(min_predicted_input) if min_predicted_input else 1.3
        except ValueError:
            min_predicted = 1.3

        min_range_input = input("Enter min range start (default: 1.3): ").strip()
        try:
            min_range = float(min_range_input) if min_range_input else 1.3
        except ValueError:
            min_range = 1.3

        safety_margin_input = input("Enter safety margin (0.0-1.0, default: 0.8): ").strip()
        try:
            safety_margin = float(safety_margin_input) if safety_margin_input else 0.8
            safety_margin = max(0.0, min(1.0, safety_margin))  # Clamp to 0.0-1.0
        except ValueError:
            safety_margin = 0.8

        print(f"\n" + "=" * 60)
        print(f"Starting {model_name} Real-Time Listener")
        print("=" * 60)
        print(f"Model:             {model_name}")
        print(f"Min Predicted:      {min_predicted}x")
        print(f"Min Range Start:   {min_range}x")
        print(f"Safety Margin:     {safety_margin * 100:.0f}% (cashout at {safety_margin})")
        print(f"Listening for analytics_round_signals table updates...")
        print(f"Press Ctrl+C to stop\n")

        # Use saved Supabase credentials
        supabase_url = "https://zofojiubrykbtmstfhzx.supabase.co"
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvZm9qaXVicnlrYnRtc3RmaHp4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM4NzU0OTEsImV4cCI6MjA3OTQ1MTQ5MX0.mxwvnhT-ouONWff-gyqw67lKon82nBx2fsbd8meyc8s"

        print("\nUsing configured Supabase credentials")

        # Initialize components
        screen_capture = ScreenCapture(config.multiplier_region)
        multiplier_reader = MultiplierReader(screen_capture)
        game_actions = GameActions(config.bet_button_point)

        # Create and start real-time listener
        listener = ModelRealtimeListener(
            game_actions=game_actions,
            multiplier_reader=multiplier_reader,
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            model_name=model_name,
            min_predicted_multiplier=min_predicted,
            min_range_start=min_range,
            safety_margin=safety_margin
        )

        # Run listener
        asyncio.run(listener.listen())

    except KeyboardInterrupt:
        print("\n\nListener stopped by user.")
        if 'listener' in locals():
            listener.stop()
            stats = listener.get_stats()
            print("\n" + "=" * 60)
            print("Listener Statistics".center(60))
            print("=" * 60)
            print(f"Total Executions:      {stats['execution_count']}")
            print(f"Qualified Bets:        {stats['qualified_bets']}")
            print(f"Successful Trades:     {stats['successful_trades']}")
            print(f"Failed Trades:         {stats['failed_trades']}")
            print(f"Qualification Rate:    {stats['qualification_rate']:.1f}%")
            print(f"Success Rate:          {stats['success_rate']:.1f}%")
            print("=" * 60)
    except Exception as e:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nPress Enter to return to menu...")


def main():
    """Main entry point with menu system"""
    # Migrate old config if needed
    migrate_old_config()

    menu = MenuController()

    while True:
        action = menu.run()

        if action == 'configure':
            run_unified_gui()

        elif action == 'monitor':
            config = load_game_config()
            if not config or not config.is_valid():
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"\n[{timestamp}] ERROR: Invalid configuration")
                input("\nPress Enter to continue...")
                continue

            # Check for command line arguments for interval
            interval = 0.5
            if len(sys.argv) > 1:
                try:
                    interval = float(sys.argv[1])
                except ValueError:
                    print("Usage: python main.py [update_interval_seconds]")
                    continue

            app = MultiplierReaderApp(config=config, update_interval=interval)
            app.run()

        elif action == 'test':
            test_configuration()

        elif action == 'websocket':
            websocket_trading()

        elif action == 'supabase':
            supabase_trading()

        elif action == 'demo':
            demo_mode()

        elif action == 'pycaret':
            pycaret_trading()

        elif action == 'exit':
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{timestamp}] INFO: Exiting Aviator Bot. Goodbye!")
            break


if __name__ == "__main__":
    main()
