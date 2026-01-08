"""Manage stake with compounding logic"""

from typing import Dict, Any, Tuple


class StakeDecision:
    """Stake calculation result"""

    def __init__(self, stake: float, compound_level: int, reason: str):
        self.stake = stake
        self.compound_level = compound_level
        self.reason = reason

    def __repr__(self):
        return f"StakeDecision(stake={self.stake:.2f}, level={self.compound_level}, reason='{self.reason}')"


class StakeManager:
    """Manage stake with compounding"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.current_stake = config.get('start_bet', 15)
        self.base_stake = config.get('start_bet', 15)
        self.max_stake = config.get('max_bet', 40)
        self.compound_level = 0

        # Compounding settings
        compound_cfg = config.get('stake_compounding', {})
        self.win_multiplier = compound_cfg.get('win_multiplier', 1.4)
        self.loss_divisor = compound_cfg.get('loss_divisor', 1.4)
        self.max_compound_steps = compound_cfg.get('max_steps', 3)
        self.reset_on_high_mult = compound_cfg.get('reset_on_high_mult', 10)

    def calculate_stake(
        self,
        last_result: str,  # "win" / "loss" / "skip"
        last_round_mult: float,
        consecutive_losses: int,
        regime: str
    ) -> StakeDecision:
        """Calculate stake for next bet"""

        # Check reset conditions first
        should_reset = self._should_reset(last_result, last_round_mult, consecutive_losses, regime)

        if should_reset:
            self.current_stake = self.base_stake
            self.compound_level = 0
            return StakeDecision(
                stake=self.current_stake,
                compound_level=0,
                reason="Reset triggered"
            )

        # Apply compounding
        if last_result == "win":
            if self.compound_level < self.max_compound_steps:
                self.current_stake = min(self.current_stake * self.win_multiplier, self.max_stake)
                self.compound_level += 1
        elif last_result == "loss":
            self.current_stake = max(self.current_stake / self.loss_divisor, self.base_stake)
            if self.compound_level > 0:
                self.compound_level -= 1

        return StakeDecision(
            stake=self.current_stake,
            compound_level=self.compound_level,
            reason=f"{last_result} → level={self.compound_level}"
        )

    def _should_reset(self, last_result: str, last_mult: float, consec_losses: int, regime: str) -> bool:
        """Check reset conditions"""

        # Reset on max compound reached
        if self.compound_level >= self.max_compound_steps:
            return True

        # Reset on high multiplier
        if last_mult >= self.reset_on_high_mult:
            return True

        # Reset on multiple losses at high stake
        if consec_losses >= 2 and self.current_stake >= 25:
            return True

        # Reset in TIGHT regime (disable compounding)
        if regime == "TIGHT":
            return True

        return False

    def set_stake(self, stake: float):
        """Manually set current stake"""
        self.current_stake = max(self.base_stake, min(stake, self.max_stake))

    def reset(self):
        """Reset to base stake"""
        self.current_stake = self.base_stake
        self.compound_level = 0

    def get_status(self) -> Dict[str, Any]:
        """Get current stake status"""
        return {
            "current_stake": self.current_stake,
            "base_stake": self.base_stake,
            "compound_level": self.compound_level,
            "max_compound_steps": self.max_compound_steps
        }
