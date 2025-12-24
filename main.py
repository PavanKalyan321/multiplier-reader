# Main monitoring loop for multiplier reader
import time
import sys
import json
from datetime import datetime
from config import load_config, get_default_region
from screen_capture import ScreenCapture
from multiplier_reader import MultiplierReader
from game_tracker import GameTracker
from supabase_client import SupabaseLogger
from prediction_engine import PredictionEngine
from analytics_client import AnalyticsClient


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

    def __init__(self, region=None, update_interval=0.5):
        self.region = region or load_config() or get_default_region()
        self.update_interval = update_interval
        self.screen_capture = ScreenCapture(self.region)
        self.multiplier_reader = MultiplierReader(self.screen_capture)
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
        }

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
                'crash_detected': round_data.crash_detected
            })
        return rounds

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
        print("=" * 80)
        print("ROUND ENDED")
        print("=" * 80)
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
            try:
                # Prepare round history for prediction
                rounds_data = self._prepare_rounds_for_prediction()

                # Train prediction engine with historical data
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] INFO: Training prediction models with {len(rounds_data)} rounds...")
                self.prediction_engine.train(rounds_data)

                # Make prediction for next round
                prediction = self.prediction_engine.predict(rounds_data)

                if prediction:
                    self.stats['predictions_generated'] += 1

                    # Calculate volatility and momentum metrics
                    volatility = self.prediction_engine.calculate_volatility(rounds_data)
                    momentum = self.prediction_engine.calculate_momentum(rounds_data)

                    # Get ensemble prediction
                    ensemble_pred = prediction.get('ensemble', {})
                    signal_type = self.analytics_client._get_pattern_type(
                        prediction.get('features', {})
                    )

                    print(f"[{timestamp}] INFO: Prediction complete")
                    print(f"[{timestamp}]   - Signal: {ensemble_pred.get('prediction', 'N/A')} (confidence: {ensemble_pred.get('confidence', 0):.2%})")
                    print(f"[{timestamp}]   - Volatility: {volatility:.3f}, Momentum: {momentum:.3f}")

                    # Insert signal into analytics_round_signals table
                    signal_inserted = self.analytics_client.insert_signal(
                        round_id=round_summary.round_number,
                        round_number=round_summary.round_number,
                        prediction=prediction,
                        volatility=volatility,
                        momentum=momentum,
                        bot_id="multiplier-reader",
                        game_name="aviator"
                    )

                    if signal_inserted:
                        self.stats['signals_saved'] += 1
                        print(f"[{timestamp}] INFO: Signal saved to analytics_round_signals")
                    else:
                        print(f"[{timestamp}] WARNING: Failed to save signal to analytics")

            except Exception as e:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] WARNING: Prediction pipeline error: {e}")

        print()
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] INFO: Waiting for next round...")

    def update_step(self):
        """Single update step"""
        self.stats['total_updates'] += 1

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
            duration = round_summary['duration']
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

            # Build status line with columns
            # Format: [TIME] R:X | CURR: X.XXx | MAX: X.XXx | DUR: X.Xs | TREND: sparkline
            timestamp = datetime.now().strftime("%H:%M:%S")
            status_line = (
                f"{Colors.GRAY}[{timestamp}]{Colors.RESET} "
                f"{Colors.CYAN}R:{round_num+1}{Colors.RESET} | "
                f"{Colors.BOLD}CURR:{Colors.RESET} {color}{current:5.2f}x{Colors.RESET} | "
                f"{Colors.BOLD}MAX:{Colors.RESET} {Colors.MAGENTA}{max_mult:5.2f}x{Colors.RESET} | "
                f"{Colors.BOLD}DUR:{Colors.RESET} {duration:5.1f}s | "
                f"{Colors.BOLD}TREND:{Colors.RESET} {color}{sparkline}{Colors.RESET}"
            )

            # Only print if values changed (compare without colors/timestamp)
            status_key = f"{round_num}|{current:.2f}|{max_mult:.2f}|{duration:.1f}"
            if status_key != self.last_status_msg:
                print(status_line)
                self.last_status_msg = status_key
                self.status_printed = True

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

        print(f"[{datetime.now().strftime('%H:%M:%S')}] STATUS: WAITING for first round...")

        try:
            while self.running:
                self.update_step()
                time.sleep(self.update_interval)
        except KeyboardInterrupt:
            print("\n")
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] WARNING: Stopping multiplier reader...")
            self.print_stats()

if __name__ == "__main__":
    # Check for command line arguments
    interval = 0.5
    if len(sys.argv) > 1:
        try:
            interval = float(sys.argv[1])
        except ValueError:
            print("Usage: python main.py [update_interval_seconds]")
            sys.exit(1)

    app = MultiplierReaderApp(update_interval=interval)
    app.run()
