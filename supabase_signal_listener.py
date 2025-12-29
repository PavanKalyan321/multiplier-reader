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
    model_name: str                     # e.g., "XGBoost"
    confidence: float                   # 0-100
    expected_output: float              # Target multiplier from model
    bet: bool                           # Should execute bet
    confidence_pct: float               # Parsed confidence as percentage
    range_min: float                    # Min expected range
    range_max: float                    # Max expected range
    actual_multiplier: Optional[float] = None  # Actual game multiplier
    payload: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None

    # Legacy fields for compatibility
    multiplier: float = 0.0

    def is_valid(self) -> bool:
        """Validate signal data"""
        if not self.model_name or self.round_id <= 0:
            return False
        if self.expected_output <= 0:
            return False
        if not (0 <= self.confidence_pct <= 100):
            return False
        return True

    def __str__(self) -> str:
        """String representation"""
        return (
            f"Signal(Round: {self.round_id}, "
            f"Model: {self.model_name}, "
            f"Target: {self.expected_output}x, "
            f"Confidence: {self.confidence_pct}%, "
            f"Bet: {self.bet})"
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
        """Parse database row into ModelSignal (supporting new payload format with models array)

        Args:
            row: Database row from analytics_round_signals

        Returns:
            ModelSignal for XGBoost model or None if not found/invalid
        """
        try:
            round_id = row.get('round_id', 0)
            actual_multiplier = row.get('actualMultiplier')
            payload_str = row.get('payload')
            created_at = row.get('created_at')

            # Parse payload
            payload = self._parse_payload(payload_str) if payload_str else {}

            # Look for XGBoost model in the models array
            models = payload.get('models', [])
            xgboost_model = None
            for model in models:
                if model.get('modelName') == 'XGBoost':
                    xgboost_model = model
                    break

            if not xgboost_model:
                self._log(f"XGBoost model not found in payload for round {round_id}", "DEBUG")
                return None

            # Extract XGBoost model data
            model_name = xgboost_model.get('modelName', 'XGBoost')
            expected_output = float(xgboost_model.get('expectedOutput', 0))
            confidence_str = xgboost_model.get('confidence', '0%')
            range_str = xgboost_model.get('range', '0-0')
            bet = xgboost_model.get('bet', False)

            # Parse confidence (handle "50%" format)
            if isinstance(confidence_str, str):
                confidence_str = confidence_str.rstrip('%')
                try:
                    confidence_pct = float(confidence_str)
                except ValueError:
                    confidence_pct = 0.0
            else:
                confidence_pct = float(confidence_str)

            # Parse range (e.g., "563.04-844.55")
            range_min, range_max = 0.0, 0.0
            if '-' in range_str:
                try:
                    min_str, max_str = range_str.split('-')
                    range_min = float(min_str.strip())
                    range_max = float(max_str.strip())
                except ValueError:
                    pass

            # Create signal
            signal = ModelSignal(
                round_id=round_id,
                model_name=model_name,
                confidence=confidence_pct,
                expected_output=expected_output,
                bet=bet,
                confidence_pct=confidence_pct,
                range_min=range_min,
                range_max=range_max,
                actual_multiplier=actual_multiplier,
                payload=payload,
                created_at=created_at
            )

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
