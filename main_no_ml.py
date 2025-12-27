# Main monitoring loop WITHOUT ML predictions (for testing rounds only)
# Use this temporarily to test AviatorRound table fixes

import time
import sys
import json
from datetime import datetime
from config import load_config, get_default_region
from screen_capture import ScreenCapture
from multiplier_reader import MultiplierReader
from game_tracker import GameTracker
from supabase_client import SupabaseLogger


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
    """Main application for monitoring game multiplier - NO ML VERSION"""

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
        self.multiplier_history = []
        self.max_history = 10

        # Initialize Supabase logger
        self.supabase = SupabaseLogger(
            url='https://zofojiubrykbtmstfhzx.supabase.co',
            key='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvZm9qaXVicnlrYnRtc3RmaHp4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM4NzU0OTEsImV4cCI6MjA3OTQ1MTQ5MX0.mxwvnhT-ouONWff-gyqw67lKon82nBx2fsbd8meyc8s'
        )

        print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Running in TEST MODE - ML Predictions disabled")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Testing AviatorRound table only")

        self.stats = {
            'total_updates': 0,
            'successful_reads': 0,
            'failed_reads': 0,
            'crashes_detected': 0,
            'max_multiplier_ever': 0,
            'start_time': datetime.now(),
            'supabase_inserts': 0,
            'supabase_failures': 0,
        }

    def generate_sparkline(self, values, width=10):
        """Generate ASCII sparkline from values"""
        if not values or len(values) < 2:
            return ' ' * min(width, len(values) if values else 1)

        # Normalize values to 0-7 range for block chars
        min_val = min(values)
        max_val = max(values)
        if max_val == min_val:
            return '▄' * len(values)

        blocks = '▁▂▃▄▅▆▇█'
        result = []
        for val in values[-width:]:
            normalized = (val - min_val) / (max_val - min_val)
            block_idx = min(int(normalized * (len(blocks) - 1)), len(blocks) - 1)
            result.append(blocks[block_idx])

        return ''.join(result)

    def log_event(self, event):
        """Log game event to console"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        if event.event_type == 'CRASH':
            color = Colors.get_multiplier_color(event.multiplier)
            sparkline = self.generate_sparkline(self.multiplier_history)
            print(f"\n{Colors.GRAY}[{timestamp}]{Colors.RESET} {Colors.RED}{Colors.BOLD}[CRASH]{Colors.RESET} at {color}{event.multiplier:.2f}x{Colors.RESET} {Colors.GRAY}[{sparkline}]{Colors.RESET}")
            self.stats['crashes_detected'] += 1
        elif event.event_type == 'GAME_START':
            round_num = self.game_tracker.round_number + 1
            print(f"{Colors.GRAY}[{timestamp}]{Colors.RESET} {Colors.GREEN}{Colors.BOLD}[START]{Colors.RESET} ROUND {round_num} STARTED")
            self.is_round_running = True
            self.multiplier_history = []
        elif event.event_type == 'HIGH_MULTIPLIER':
            print(f"{Colors.GRAY}[{timestamp}]{Colors.RESET} {Colors.MAGENTA}{Colors.BOLD}[HIGH]{Colors.RESET} MULTIPLIER: {Colors.MAGENTA}{event.multiplier:.2f}x{Colors.RESET}")

    def check_and_log_round_completion(self):
        """Check if a new round was completed and log it"""
        current_round_count = len(self.game_tracker.round_history)
        if current_round_count > self.previous_round_count:
            new_round = self.game_tracker.round_history[-1]
            self.log_round_completion(new_round)
            self.previous_round_count = current_round_count
            self.is_round_running = False

    def log_round_completion(self, round_summary):
        """Log a completed round and save to Supabase"""
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

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] INFO: Attempting to save round to Supabase...")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] DEBUG: Round #{round_summary.round_number}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] DEBUG: Multiplier: {round_summary.max_multiplier:.2f}x")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] DEBUG: Timestamp: {round_end_time.isoformat()}")

        success = self.supabase.insert_round(
            round_number=round_summary.round_number,
            multiplier=round_summary.max_multiplier,
            timestamp=round_end_time
        )

        # Update stats
        if success:
            self.stats['supabase_inserts'] += 1
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ SUCCESS: Round saved to Supabase")
        else:
            self.stats['supabase_failures'] += 1
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ FAILED: Could not save to Supabase")

        print()
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] INFO: Waiting for next round...")

    def update_step(self):
        """Single update step"""
        self.stats['total_updates'] += 1

        result = self.multiplier_reader.get_multiplier_with_status()

        if result['multiplier'] is None:
            self.stats['failed_reads'] += 1
            return

        self.stats['successful_reads'] += 1
        multiplier = result['multiplier']
        status = result['status']

        # Track max multiplier
        if multiplier > self.stats['max_multiplier_ever']:
            self.stats['max_multiplier_ever'] = multiplier

        # Track multiplier history for sparkline
        if self.is_round_running and multiplier > 1.0:
            if not self.multiplier_history or multiplier != self.multiplier_history[-1]:
                self.multiplier_history.append(multiplier)
                if len(self.multiplier_history) > self.max_history:
                    self.multiplier_history.pop(0)

        # Process with game tracker
        events = self.game_tracker.process_multiplier(multiplier, status)

        # Log any new events
        for event in events:
            self.log_event(event)

        # Check for round completion
        self.check_and_log_round_completion()

        # Print status line
        self.print_status_line(multiplier, status)

    def print_status_line(self, multiplier, status):
        """Print live status line"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = Colors.get_multiplier_color(multiplier)

        if not self.game_tracker.state.is_running:
            status_msg = f"\r[{timestamp}] STATUS: WAITING for first round..."
            status_key = "WAITING"
        else:
            sparkline = self.generate_sparkline(self.multiplier_history, width=10)
            duration = self.game_tracker.state.round_duration

            status_msg = (
                f"\r[{timestamp}] "
                f"{color}{multiplier:.2f}x{Colors.RESET} | "
                f"Max: {color}{self.game_tracker.state.max_multiplier:.2f}x{Colors.RESET} | "
                f"Duration: {duration:.1f}s | "
                f"{Colors.GRAY}[{sparkline}]{Colors.RESET}"
            )
            status_key = f"{multiplier:.2f}"

        if status_key != self.last_status_msg:
            print(status_msg, end='', flush=True)
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
            print()
            print(f"[{timestamp}] INFO: Supabase inserts: {self.stats['supabase_inserts']}")
            print(f"[{timestamp}] INFO: Supabase failures: {self.stats['supabase_failures']}")

            if self.stats['supabase_inserts'] > 0:
                print(f"[{timestamp}] ✅ AviatorRound table is working correctly!")
            else:
                print(f"[{timestamp}] ❌ AviatorRound table needs fixing - check SQL scripts")

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
        print("MULTIPLIER READER - TEST MODE (NO ML)")
        print("=" * 80)
        print()

        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] INFO: Started")
        print(f"[{timestamp}] INFO: Region: ({self.region.x1}, {self.region.y1}) to ({self.region.x2}, {self.region.y2})")
        print(f"[{timestamp}] INFO: Update interval: {self.update_interval}s")
        print(f"[{timestamp}] INFO: Press Ctrl+C to stop")
        print()

        try:
            while self.running:
                self.update_step()
                time.sleep(self.update_interval)

        except KeyboardInterrupt:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n\n[{timestamp}] WARNING: Stopping multiplier reader...")

        finally:
            self.print_stats()


def main():
    update_interval = 0.5
    if len(sys.argv) > 1:
        try:
            update_interval = float(sys.argv[1])
        except ValueError:
            print(f"Invalid interval: {sys.argv[1]}, using default 0.5s")

    app = MultiplierReaderApp(update_interval=update_interval)
    app.run()


if __name__ == '__main__':
    main()
