# Main monitoring loop for multiplier reader
import time
import sys
import json
from datetime import datetime
from config import load_config, get_default_region
from screen_capture import ScreenCapture
from multiplier_reader import MultiplierReader
from game_tracker import GameTracker

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
        self.stats = {
            'total_updates': 0,
            'successful_reads': 0,
            'failed_reads': 0,
            'crashes_detected': 0,
            'max_multiplier_ever': 0,
            'start_time': datetime.now(),
        }

    def log_event(self, event):
        """Log only critical game events (not every multiplier change)"""
        if event.event_type == 'CRASH':
            max_mult = event.details.get('max_multiplier', 'N/A')
            duration = event.details.get('round_duration', 0)
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{timestamp}] EVENT: [CRASH] Reached {max_mult}x in {duration:.2f}s")
            self.stats['crashes_detected'] += 1
        elif event.event_type == 'GAME_START':
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] ROUND: [START] ROUND {self.game_tracker.round_number + 1} STARTED")
            self.is_round_running = True
        elif event.event_type == 'HIGH_MULTIPLIER':
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] EVENT: [HIGH] MULTIPLIER: {event.multiplier:.2f}x")
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
        """Log a completed round with formatted table"""
        print("\n")
        print("=" * 80)
        print("ROUND ENDED")
        print("=" * 80)
        print()

        # Log the complete round history table
        history_table = self.game_tracker.format_round_history_table(limit=None)
        print(history_table)

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
        """Print current status only when it changes"""
        if round_summary['status'] == 'RUNNING' and 'current_multiplier' in round_summary:
            duration = round_summary['duration']
            max_mult = round_summary['max_multiplier']
            current = round_summary['current_multiplier']
            round_num = self.game_tracker.round_number

            # Status without timestamp for comparison (only compare actual values, not time)
            status_without_time = f"Multiplier: {current:.2f}x | Max: {max_mult:.2f}x | Time: {duration:.1f}s | Round: {round_num}"

            # Only print if values changed
            if status_without_time != self.last_status_msg:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] STATUS: {status_without_time}")
                self.last_status_msg = status_without_time
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
