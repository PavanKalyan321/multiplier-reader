"""Select cashout multiplier (defensive/default/aggressive)"""

import time
from typing import Dict, Any, Tuple


class CashoutDecision:
    """Cashout selection result"""

    def __init__(self, multiplier: float, mode: str, reason: str):
        self.multiplier = multiplier
        self.mode = mode
        self.reason = reason

    def __repr__(self):
        return f"CashoutDecision({self.multiplier:.2f}x, mode={self.mode})"


class CashoutSelector:
    """Select cashout strategy"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.aggressive_used_this_window = False
        self.window_start_time = time.time()

        # Extract cashout multipliers
        cashout_cfg = config.get('cashout', {})
        self.default_mult = cashout_cfg.get('default', {}).get('multiplier', 1.85)
        self.defensive_mult = cashout_cfg.get('defensive', {}).get('multiplier', 1.5)
        self.aggressive_mult = cashout_cfg.get('aggressive', {}).get('multiplier', 2.5)

        # Defensive trigger
        self.defensive_trigger_loss = cashout_cfg.get('defensive', {}).get('trigger_loss', 80)

        # Aggressive conditions
        agg = cashout_cfg.get('aggressive', {})
        self.aggressive_min_profit = agg.get('min_profit', 100)
        self.aggressive_require_regime = agg.get('require_regime', 'LOOSE')
        self.aggressive_window_duration = agg.get('window_duration_min', 15) * 60

    def select_cashout(
        self,
        session_profit: float,
        session_loss: float,
        compound_level: int,
        regime: str
    ) -> CashoutDecision:
        """Select cashout multiplier"""

        # Check if window expired
        if time.time() - self.window_start_time > self.aggressive_window_duration:
            self.aggressive_used_this_window = False
            self.window_start_time = time.time()

        # Defensive mode: Session loss too high
        if session_loss >= self.defensive_trigger_loss:
            return CashoutDecision(
                multiplier=self.defensive_mult,
                mode="defensive",
                reason=f"session_loss={session_loss:.0f} >= {self.defensive_trigger_loss}"
            )

        # Aggressive mode: Favorable conditions
        if (session_profit >= self.aggressive_min_profit and
            compound_level == 0 and
            regime == self.aggressive_require_regime and
            not self.aggressive_used_this_window):
            self.aggressive_used_this_window = True
            return CashoutDecision(
                multiplier=self.aggressive_mult,
                mode="aggressive",
                reason=f"profit={session_profit:.0f}, regime={regime}, compound=0"
            )

        # Regime-based defensive
        if regime == "TIGHT":
            return CashoutDecision(
                multiplier=self.defensive_mult,
                mode="regime_tight",
                reason="regime=TIGHT"
            )

        if regime == "VOLATILE":
            return CashoutDecision(
                multiplier=self.defensive_mult,
                mode="regime_volatile",
                reason="regime=VOLATILE (conservative)"
            )

        # Default mode
        return CashoutDecision(
            multiplier=self.default_mult,
            mode="default",
            reason="standard_conditions"
        )

    def reset_window(self):
        """Reset aggressive window counter"""
        self.aggressive_used_this_window = False
        self.window_start_time = time.time()
