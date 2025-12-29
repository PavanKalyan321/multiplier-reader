# Supabase real-time signal listener for analytics_round_signals table
import asyncio
import json
from datetime import datetime
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from supabase_client import SupabaseLogger


class ModelName(Enum):
    """Supported ML models"""
    RANDOM_FOREST = "RandomForest"
    NEURAL_NET = "NeuralNet"
    XGBOOST = "XGBoost"
    ENSEMBLE = "Ensemble"
    CUSTOM = "Custom"


@dataclass
class ModelSignal:
    """Data structure for ML model trading signal"""
    round_id: int
    multiplier: float  # Expected multiplier
    model_name: str
    confidence: float  # 0-100 or 0-1
    model_output: Dict[str, Any]
    payload: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None

    # Extracted from payload
    expected_output: float = 0.0
    confidence_pct: float = 0.0
    range_min: float = 0.0
    range_max: float = 0.0

    def is_valid(self) -> bool:
        """Validate signal data"""
        if not self.model_name or self.round_id <= 0:
            return False
        if self.multiplier <= 0:
            return False
        if not (0 <= self.confidence <= 100):
            return False
        return True

    def __str__(self) -> str:
        """String representation"""
        return (
            f"Signal(Round: {self.round_id}, "
            f"Model: {self.model_name}, "
            f"Target: {self.multiplier}x, "
            f"Confidence: {self.confidence}%)"
        )


class SupabaseSignalListener:
    """Listen to Supabase analytics_round_signals table for new signals"""

    def __init__(self, supabase_client: SupabaseLogger):
        """Initialize Supabase signal listener

        Args:
            supabase_client: SupabaseLogger instance with authenticated client
        """
        self.supabase = supabase_client
        self.client = supabase_client.client
        self.signal_queue = asyncio.Queue()
        self.last_signal: Optional[ModelSignal] = None
        self.signal_count = 0
        self.error_count = 0
        self.listeners = []  # Callbacks for new signals
        self.last_checked_id = 0  # Track last processed signal

    def add_listener(self, callback: Callable[[ModelSignal], None]):
        """Add a callback to be called when new signal arrives

        Args:
            callback: Function to call with ModelSignal
        """
        self.listeners.append(callback)

    def _log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] SUPABASE_LISTENER {level}: {message}")

    def _parse_payload(self, payload_str: str) -> Dict[str, Any]:
        """Parse JSON payload string

        Args:
            payload_str: JSON string payload

        Returns:
            Parsed dictionary or empty dict
        """
        try:
            if isinstance(payload_str, str):
                return json.loads(payload_str)
            elif isinstance(payload_str, dict):
                return payload_str
            return {}
        except (json.JSONDecodeError, TypeError):
            self._log(f"Error parsing payload: {payload_str}", "WARNING")
            return {}

    def _parse_signal(self, row: Dict[str, Any]) -> Optional[ModelSignal]:
        """Parse database row into ModelSignal

        Args:
            row: Database row from analytics_round_signals

        Returns:
            ModelSignal or None if invalid
        """
        try:
            round_id = row.get('round_id', 0)
            multiplier = float(row.get('multiplier', 0))
            model_name = row.get('model_name', '')
            confidence = float(row.get('confidence', 0))
            model_output = row.get('model_output', {})
            payload_str = row.get('payload')
            created_at = row.get('created_at')

            # Parse payload if it's a string
            payload = self._parse_payload(payload_str) if payload_str else {}

            # Create signal
            signal = ModelSignal(
                round_id=round_id,
                multiplier=multiplier,
                model_name=model_name,
                confidence=confidence,
                model_output=model_output,
                payload=payload,
                created_at=created_at
            )

            # Extract payload fields
            if payload:
                signal.expected_output = float(payload.get('expectedOutput', 0))

                # Parse confidence (handle both "10%" and 0.1 formats)
                conf_str = payload.get('confidence', '0%')
                if isinstance(conf_str, str):
                    conf_str = conf_str.rstrip('%')
                    try:
                        signal.confidence_pct = float(conf_str)
                    except ValueError:
                        signal.confidence_pct = confidence
                else:
                    signal.confidence_pct = float(conf_str) * 100 if conf_str < 1 else conf_str

                # Parse range
                range_str = payload.get('range', '0-0')
                if '-' in range_str:
                    try:
                        min_str, max_str = range_str.split('-')
                        signal.range_min = float(min_str.strip())
                        signal.range_max = float(max_str.strip())
                    except ValueError:
                        pass

            return signal if signal.is_valid() else None

        except (ValueError, TypeError, KeyError) as e:
            self._log(f"Error parsing signal: {e}", "WARNING")
            return None

    async def fetch_new_signals(self) -> list:
        """Fetch new signals from Supabase that haven't been processed

        Returns:
            List of ModelSignal objects
        """
        try:
            # Query for new signals since last checked
            response = self.client.table('analytics_round_signals') \
                .select('*') \
                .gt('id', self.last_checked_id) \
                .order('id', desc=False) \
                .execute()

            if not response.data:
                return []

            signals = []
            for row in response.data:
                signal = self._parse_signal(row)
                if signal:
                    signals.append(signal)
                    self.last_checked_id = max(self.last_checked_id, row.get('id', 0))
                    self.signal_count += 1

                    self._log(f"Signal #{self.signal_count}: {signal}", "INFO")

                    # Add to queue
                    await self.signal_queue.put(signal)

                    # Call listeners
                    for listener in self.listeners:
                        try:
                            listener(signal)
                        except Exception as e:
                            self._log(f"Listener error: {e}", "WARNING")

            return signals

        except Exception as e:
            self._log(f"Error fetching signals: {e}", "ERROR")
            self.error_count += 1
            return []

    async def listen(self, poll_interval: float = 5.0):
        """Listen for new signals by polling (blocking)

        Args:
            poll_interval: Polling interval in seconds

        This should be run in a separate async task
        """
        self._log(f"Starting signal listener (poll interval: {poll_interval}s)", "INFO")

        try:
            while True:
                try:
                    # Fetch new signals
                    new_signals = await self.fetch_new_signals()

                    if new_signals:
                        self._log(f"Fetched {len(new_signals)} new signal(s)", "INFO")

                    # Wait before next poll
                    await asyncio.sleep(poll_interval)

                except Exception as e:
                    self._log(f"Error in listen loop: {e}", "WARNING")
                    self.error_count += 1
                    await asyncio.sleep(poll_interval)

        except asyncio.CancelledError:
            self._log("Listener cancelled", "INFO")
        except Exception as e:
            self._log(f"Listener error: {e}", "ERROR")

    async def get_signal(self, timeout: Optional[float] = None) -> Optional[ModelSignal]:
        """Get next signal from queue (non-blocking with optional timeout)

        Args:
            timeout: Timeout in seconds, None for no timeout

        Returns:
            ModelSignal or None if timeout
        """
        try:
            if timeout:
                signal = await asyncio.wait_for(self.signal_queue.get(), timeout=timeout)
            else:
                signal = await self.signal_queue.get()
            return signal
        except asyncio.TimeoutError:
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Get listener statistics"""
        return {
            'signals_received': self.signal_count,
            'errors': self.error_count,
            'last_signal': str(self.last_signal) if self.last_signal else None,
            'queue_size': self.signal_queue.qsize(),
            'last_checked_id': self.last_checked_id
        }

    def print_stats(self):
        """Print statistics"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        stats = self.get_stats()

        print(f"\n[{timestamp}] Supabase Signal Listener Statistics:")
        print(f"[{timestamp}] Signals received: {stats['signals_received']}")
        print(f"[{timestamp}] Errors: {stats['errors']}")
        print(f"[{timestamp}] Queue size: {stats['queue_size']}")
        print(f"[{timestamp}] Last checked ID: {stats['last_checked_id']}")
        if stats['last_signal']:
            print(f"[{timestamp}] Last signal: {stats['last_signal']}")
