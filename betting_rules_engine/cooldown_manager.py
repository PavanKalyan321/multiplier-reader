"""Manage cooldown conditions (skip rounds)"""

from datetime import datetime
from typing import Dict, Any, Optional


class CooldownState:
    """Current cooldown status"""

    def __init__(self):
        self.active = False
        self.rounds_remaining = 0
        self.reason = ""
        self.started_at = datetime.now()

    def __repr__(self):
        return f"CooldownState(active={self.active}, remaining={self.rounds_remaining})"


class CooldownManager:
    """Manage cooldown conditions"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.state = CooldownState()

    def check_and_activate(
        self,
        last_round_mult: float,
        last_stake: float,
        compound_level: int,
        consecutive_losses: int
    ):
        """Check if cooldown should be activated"""

        after_high = self.config.get('after_high_mult', {})
        after_losses = self.config.get('after_consecutive_losses', {})
        after_compound = self.config.get('after_max_compound', {})

        # Rule 1: After high multiplier
        high_threshold = after_high.get('threshold', 10)
        if last_round_mult >= high_threshold:
            skip_rounds = after_high.get('skip_rounds', 2)
            self._activate_cooldown(skip_rounds, f"High mult {last_round_mult:.1f}x >= {high_threshold}x")
            return

        # Rule 2: After consecutive losses at high stake
        loss_count = after_losses.get('count', 2)
        stake_min = after_losses.get('stake_min', 25)
        if consecutive_losses >= loss_count and last_stake >= stake_min:
            skip_rounds = after_losses.get('skip_rounds', 2)
            self._activate_cooldown(skip_rounds, f"{consecutive_losses} losses at stake {last_stake:.0f}")
            return

        # Rule 3: After max compound reached
        max_steps = after_compound.get('max_steps', 3)
        if compound_level >= max_steps:
            skip_rounds = after_compound.get('skip_rounds', 1)
            self._activate_cooldown(skip_rounds, f"Max compound {compound_level} reached")
            return

    def _activate_cooldown(self, rounds: int, reason: str):
        """Activate cooldown for N rounds"""
        self.state.active = True
        self.state.rounds_remaining = rounds
        self.state.reason = reason
        self.state.started_at = datetime.now()

    def decrement(self):
        """Reduce cooldown by 1 round"""
        if self.state.active:
            self.state.rounds_remaining -= 1
            if self.state.rounds_remaining <= 0:
                self.state.active = False
                self.state.reason = ""

    def is_active(self) -> bool:
        """Check if cooldown is currently active"""
        return self.state.active

    def get_status(self) -> Dict[str, Any]:
        """Get cooldown status"""
        return {
            "active": self.state.active,
            "rounds_remaining": self.state.rounds_remaining,
            "reason": self.state.reason
        }

    def reset(self):
        """Reset cooldown"""
        self.state.active = False
        self.state.rounds_remaining = 0
        self.state.reason = ""
