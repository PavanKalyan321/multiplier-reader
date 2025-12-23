# Track game state and events
import time
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum

class GameEvent(Enum):
    """Game event types"""
    GAME_START = "GAME_START"
    MULTIPLIER_INCREASE = "MULTIPLIER_INCREASE"
    CRASH = "CRASH"
    ROUND_END = "ROUND_END"
    HIGH_MULTIPLIER = "HIGH_MULTIPLIER"
    ERROR = "ERROR"

@dataclass
class GameState:
    """Current game state"""
    multiplier: Optional[float] = None
    status: str = "IDLE"
    is_running: bool = False
    max_multiplier: float = 0
    crashed: bool = False
    round_start_time: Optional[float] = None
    round_duration: float = 0

@dataclass
class GameEvent:
    """Represent a game event"""
    event_type: str
    timestamp: float
    multiplier: Optional[float]
    status: str
    details: dict = field(default_factory=dict)

@dataclass
class RoundSummary:
    """Summary of a completed round"""
    round_number: int
    start_time: float
    end_time: float
    duration: float
    max_multiplier: float
    crash_multiplier: float
    status: str
    events_count: int

    def to_dict(self):
        """Convert to dictionary for display"""
        from datetime import datetime
        start_dt = datetime.fromtimestamp(self.start_time).strftime("%H:%M:%S")
        end_dt = datetime.fromtimestamp(self.end_time).strftime("%H:%M:%S")

        return {
            'round': self.round_number,
            'start': start_dt,
            'end': end_dt,
            'duration': f"{self.duration:.2f}s",
            'max_mult': f"{self.max_multiplier:.2f}x",
            'crash_at': f"{self.crash_multiplier:.2f}x",
            'status': self.status,
            'events': self.events_count
        }

class GameTracker:
    """Track game state and detect events"""

    def __init__(self, crash_threshold=0.5):
        self.state = GameState()
        self.previous_multiplier = None
        self.previous_status = None
        self.events: List[GameEvent] = []
        self.crash_threshold = crash_threshold
        self.high_multiplier_threshold = 10
        self.round_events = []
        self.round_history: List[RoundSummary] = []
        self.round_number = 0
        self.last_crash_multiplier = 0

    def update(self, multiplier, status):
        """Update game state with new multiplier reading"""
        timestamp = time.time()
        events = []

        # Round start detection - either from multiplier == 1 (normal start) or from any RUNNING status (mid-round entry)
        if not self.state.is_running:
            if (multiplier == 1 and status == 'STARTING') or (status in ['RUNNING', 'HIGH'] and multiplier > 1):
                self.state.is_running = True
                self.state.round_start_time = timestamp
                self.state.crashed = False
                self.state.max_multiplier = multiplier  # Could be > 1 if we start monitoring mid-round
                self.round_events = []

                event = GameEvent(
                    event_type='GAME_START',
                    timestamp=timestamp,
                    multiplier=multiplier,
                    status=status,
                    details={'round_start_time': timestamp}
                )
                events.append(event)

        # Multiplier increase detection
        if multiplier and self.previous_multiplier:
            if multiplier > self.previous_multiplier:
                delta = multiplier - self.previous_multiplier

                event = GameEvent(
                    event_type='MULTIPLIER_INCREASE',
                    timestamp=timestamp,
                    multiplier=multiplier,
                    status=status,
                    details={'delta': delta, 'previous': self.previous_multiplier}
                )
                events.append(event)

                self.state.max_multiplier = max(self.state.max_multiplier, multiplier)

        # High multiplier detection
        if multiplier and multiplier >= self.high_multiplier_threshold:
            if not hasattr(self, 'high_multiplier_reached') or not self.high_multiplier_reached:
                event = GameEvent(
                    event_type='HIGH_MULTIPLIER',
                    timestamp=timestamp,
                    multiplier=multiplier,
                    status=status,
                    details={'threshold': self.high_multiplier_threshold}
                )
                events.append(event)
                self.high_multiplier_reached = True
                print(f"[HIGH_MULTIPLIER] Reached {multiplier}x")

        # Crash detection
        if multiplier is not None and multiplier <= self.crash_threshold and self.state.is_running:
            self.state.is_running = False
            self.state.crashed = True
            round_duration = timestamp - self.state.round_start_time if self.state.round_start_time else 0
            self.last_crash_multiplier = multiplier

            event = GameEvent(
                event_type='CRASH',
                timestamp=timestamp,
                multiplier=multiplier,
                status=status,
                details={
                    'max_multiplier': self.state.max_multiplier,
                    'round_duration': round_duration,
                    'round_end_time': timestamp
                }
            )
            events.append(event)
            self.high_multiplier_reached = False
            print(f"[CRASH] Game crashed at {self.state.max_multiplier}x. Duration: {round_duration:.2f}s")

            # Save round to history
            self.round_number += 1
            round_summary = RoundSummary(
                round_number=self.round_number,
                start_time=self.state.round_start_time,
                end_time=timestamp,
                duration=round_duration,
                max_multiplier=self.state.max_multiplier,
                crash_multiplier=multiplier,
                status='CRASHED',
                events_count=len(self.round_events)
            )
            self.round_history.append(round_summary)

        # Update state
        self.state.multiplier = multiplier
        self.state.status = status
        self.previous_multiplier = multiplier
        self.previous_status = status

        # Store events
        for event in events:
            self.events.append(event)
            self.round_events.append(event)

        return events

    def get_round_summary(self):
        """Get summary of current/last round"""
        if self.state.crashed or not self.state.is_running:
            return {
                'status': 'COMPLETED',
                'max_multiplier': self.state.max_multiplier,
                'duration': time.time() - self.state.round_start_time if self.state.round_start_time else 0,
                'events_count': len(self.round_events)
            }
        else:
            return {
                'status': 'RUNNING',
                'current_multiplier': self.state.multiplier,
                'max_multiplier': self.state.max_multiplier,
                'duration': time.time() - self.state.round_start_time if self.state.round_start_time else 0
            }

    def get_event_history(self, limit=10):
        """Get last N events"""
        return self.events[-limit:]

    def get_round_history(self, limit=None):
        """Get round history (all or last N rounds)"""
        if limit is None:
            return self.round_history
        return self.round_history[-limit:]

    def get_round_statistics(self):
        """Get statistics for all completed rounds"""
        if not self.round_history:
            return None

        total_rounds = len(self.round_history)
        max_mult_overall = max(r.max_multiplier for r in self.round_history)
        avg_max_mult = sum(r.max_multiplier for r in self.round_history) / total_rounds
        avg_duration = sum(r.duration for r in self.round_history) / total_rounds
        crashed_rounds = sum(1 for r in self.round_history if r.status == 'CRASHED')

        return {
            'total_rounds': total_rounds,
            'max_multiplier_ever': max_mult_overall,
            'avg_max_multiplier': avg_max_mult,
            'avg_duration': avg_duration,
            'crashed_rounds': crashed_rounds,
            'success_rate': (crashed_rounds / total_rounds * 100) if total_rounds > 0 else 0
        }

    def format_round_history_table(self, limit=10):
        """Format round history as a readable table"""
        rounds = self.get_round_history(limit)
        if not rounds:
            return "No round history yet"

        lines = []
        lines.append("\n" + "="*100)
        lines.append("ROUND HISTORY")
        lines.append("="*100)
        lines.append(f"{'Round':<8}{'Start Time':<12}{'End Time':<12}{'Duration':<12}{'Max Mult':<12}{'Crash At':<12}{'Status':<10}{'Events':<8}")
        lines.append("-"*100)

        for round_data in rounds:
            d = round_data.to_dict()
            lines.append(f"{d['round']:<8}{d['start']:<12}{d['end']:<12}{d['duration']:<12}{d['max_mult']:<12}{d['crash_at']:<12}{d['status']:<10}{d['events']:<8}")

        lines.append("="*100)

        # Add statistics if available
        stats = self.get_round_statistics()
        if stats:
            lines.append(f"\nStatistics (All {stats['total_rounds']} rounds):")
            lines.append(f"  Max Multiplier Ever: {stats['max_multiplier_ever']:.2f}x")
            lines.append(f"  Average Max Multiplier: {stats['avg_max_multiplier']:.2f}x")
            lines.append(f"  Average Duration: {stats['avg_duration']:.2f}s")
            lines.append(f"  Total Crashes: {stats['crashed_rounds']}")
            lines.append(f"  Crash Rate: {stats['success_rate']:.1f}%")
            lines.append("="*100)

        return "\n".join(lines)
