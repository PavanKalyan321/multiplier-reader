# WebSocket listener for receiving trading signals from API
import asyncio
import websockets
import json
from datetime import datetime
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class SignalAction(Enum):
    """Action types from API signal"""
    PLACE_BET = "place_bet"
    CASHOUT = "cashout"
    HOLD = "hold"
    CANCEL = "cancel"


@dataclass
class TradingSignal:
    """Data structure for API trading signal"""
    timestamp: str
    expected_range: str
    expected_multiplier: float
    bet: bool
    round_id: str
    action: SignalAction = SignalAction.HOLD
    confidence: float = 0.0
    additional_data: Dict[str, Any] = field(default_factory=dict)

    def is_valid(self) -> bool:
        """Validate signal data"""
        if not self.timestamp or not self.round_id:
            return False
        if self.expected_multiplier <= 0:
            return False
        return True

    def __str__(self) -> str:
        """String representation"""
        return (
            f"Signal(Round: {self.round_id}, "
            f"Multiplier: {self.expected_multiplier}x, "
            f"Bet: {self.bet}, "
            f"Action: {self.action.value})"
        )


class WebSocketListener:
    """WebSocket listener for receiving trading signals"""

    def __init__(self, uri: str = "ws://localhost:8765"):
        """Initialize WebSocket listener

        Args:
            uri: WebSocket URI to connect to (default: localhost:8765)
        """
        self.uri = uri
        self.connected = False
        self.websocket = None
        self.signal_queue = asyncio.Queue()
        self.last_signal: Optional[TradingSignal] = None
        self.signal_count = 0
        self.error_count = 0
        self.listeners = []  # Callbacks for new signals

    def add_listener(self, callback: Callable[[TradingSignal], None]):
        """Add a callback to be called when new signal arrives

        Args:
            callback: Function to call with TradingSignal
        """
        self.listeners.append(callback)

    def _log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def _parse_signal(self, data: Dict[str, Any]) -> Optional[TradingSignal]:
        """Parse raw API data into TradingSignal

        Args:
            data: Raw signal data from API

        Returns:
            TradingSignal or None if invalid
        """
        try:
            # Extract required fields
            timestamp = data.get('timestamp', '')
            expected_range = data.get('expectedRange', '')
            expected_multiplier = float(data.get('expectedMultiplier', 0))
            bet = data.get('bet', False)
            round_id = data.get('roundId', '')

            # Create signal
            signal = TradingSignal(
                timestamp=timestamp,
                expected_range=expected_range,
                expected_multiplier=expected_multiplier,
                bet=bet,
                round_id=round_id,
                additional_data=data  # Store original data
            )

            # Determine action
            if bet:
                signal.action = SignalAction.PLACE_BET
            else:
                signal.action = SignalAction.HOLD

            # Extract confidence if available
            if 'confidence' in data:
                signal.confidence = float(data.get('confidence', 0.0))

            return signal if signal.is_valid() else None

        except (ValueError, TypeError, KeyError) as e:
            self._log(f"Error parsing signal: {e}", "WARNING")
            return None

    async def connect(self):
        """Connect to WebSocket server"""
        try:
            self._log(f"Connecting to {self.uri}...")
            self.websocket = await websockets.connect(self.uri)
            self.connected = True
            self._log(f"Connected successfully", "INFO")
            return True
        except Exception as e:
            self._log(f"Connection failed: {e}", "ERROR")
            self.connected = False
            self.error_count += 1
            return False

    async def disconnect(self):
        """Disconnect from WebSocket server"""
        try:
            if self.websocket:
                await self.websocket.close()
                self.connected = False
                self._log("Disconnected", "INFO")
        except Exception as e:
            self._log(f"Error disconnecting: {e}", "WARNING")

    async def listen(self):
        """Listen for incoming signals (blocking)

        This should be run in a separate async task
        """
        if not self.connected:
            if not await self.connect():
                return

        try:
            while self.connected:
                try:
                    # Receive message
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=30)

                    # Parse JSON
                    data = json.loads(message)
                    self._log(f"Received signal: {data}", "DEBUG")

                    # Parse into TradingSignal
                    signal = self._parse_signal(data)

                    if signal:
                        self.last_signal = signal
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
                    else:
                        self._log("Invalid signal received", "WARNING")

                except asyncio.TimeoutError:
                    # No message received - continue waiting
                    continue
                except json.JSONDecodeError as e:
                    self._log(f"JSON parse error: {e}", "WARNING")
                    self.error_count += 1
                except Exception as e:
                    self._log(f"Error receiving message: {e}", "WARNING")
                    self.error_count += 1

        except Exception as e:
            self._log(f"Listen error: {e}", "ERROR")
            self.connected = False

    async def get_signal(self, timeout: Optional[float] = None) -> Optional[TradingSignal]:
        """Get next signal from queue (non-blocking with optional timeout)

        Args:
            timeout: Timeout in seconds, None for no timeout

        Returns:
            TradingSignal or None if timeout
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
            'connected': self.connected,
            'signals_received': self.signal_count,
            'errors': self.error_count,
            'last_signal': str(self.last_signal) if self.last_signal else None,
            'queue_size': self.signal_queue.qsize()
        }

    def print_stats(self):
        """Print statistics"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        stats = self.get_stats()

        print(f"\n[{timestamp}] WebSocket Listener Statistics:")
        print(f"[{timestamp}] Connected: {stats['connected']}")
        print(f"[{timestamp}] Signals received: {stats['signals_received']}")
        print(f"[{timestamp}] Errors: {stats['errors']}")
        print(f"[{timestamp}] Queue size: {stats['queue_size']}")
        if stats['last_signal']:
            print(f"[{timestamp}] Last signal: {stats['last_signal']}")
