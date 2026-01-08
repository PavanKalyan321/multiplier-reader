"""Manage historical round data with in-memory cache"""

from collections import deque
from datetime import datetime
from typing import List, Optional, Dict, Any


class RoundData:
    """Single round record"""

    def __init__(self, round_id: int, multiplier: float, timestamp: Optional[datetime] = None):
        self.round_id = round_id
        self.multiplier = multiplier
        self.timestamp = timestamp or datetime.now()
        self.bet_placed = False
        self.compound_level = 0

    def __repr__(self):
        return f"RoundData(id={self.round_id}, mult={self.multiplier:.2f}x)"


class HistoricalDataCache:
    """In-memory cache for recent rounds"""

    def __init__(self, maxlen: int = 10):
        self.recent_rounds: deque = deque(maxlen=maxlen)
        self.maxlen = maxlen

    def add_round(self, round_data: RoundData):
        """Add completed round to cache"""
        self.recent_rounds.append(round_data)

    def get_previous_round(self) -> Optional[RoundData]:
        """Get last completed round"""
        if len(self.recent_rounds) > 0:
            return self.recent_rounds[-1]
        return None

    def get_last_n_rounds(self, n: int) -> List[RoundData]:
        """Get last N rounds from cache"""
        return list(self.recent_rounds)[-n:] if n > 0 else []

    def get_multipliers(self, n: int = None) -> List[float]:
        """Get list of last N multipliers"""
        rounds = self.get_last_n_rounds(n) if n else list(self.recent_rounds)
        return [r.multiplier for r in rounds]

    def clear(self):
        """Clear all cached rounds"""
        self.recent_rounds.clear()

    def __repr__(self):
        return f"HistoricalDataCache({len(self.recent_rounds)} rounds cached)"
