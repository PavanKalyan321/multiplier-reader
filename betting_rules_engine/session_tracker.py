"""Track session metrics and evaluate stop conditions"""

from datetime import datetime
from typing import Dict, Any, Optional, Tuple


class SessionMetrics:
    """Session statistics"""

    def __init__(self):
        self.start_time = datetime.now()
        self.total_profit = 0.0
        self.total_loss = 0.0
        self.net_pnl = 0.0
        self.rounds_played = 0
        self.rounds_won = 0
        self.rounds_lost = 0
        self.current_window = 0  # 0 or 1 for two 15-min windows
        self.max_stake_used = 0.0


class StopDecision:
    """Session stop evaluation"""

    def __init__(self, should_stop: bool, reason: str, category: str = ""):
        self.should_stop = should_stop
        self.reason = reason
        self.category = category  # profit_target, loss_limit, time_limit, early_abort

    def __repr__(self):
        return f"StopDecision(stop={self.should_stop}, {self.category})"


class SessionTracker:
    """Track session and evaluate stop conditions"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics = SessionMetrics()
        self.aggressive_failures = 0
        self.high_mults_in_last_5 = []

        # Stop conditions
        stop_cfg = config.get('stop_conditions', {})
        self.profit_target = stop_cfg.get('profit_target', 200)
        self.max_loss = stop_cfg.get('max_loss', 200)
        self.duration_minutes = stop_cfg.get('duration_minutes', 30)

        # Early abort
        early_cfg = stop_cfg.get('early_abort', {})
        self.early_abort_loss = early_cfg.get('loss_in_first_window', 120)
        self.early_abort_agg_failures = early_cfg.get('aggressive_failures', 2)

    def update_metrics(self, result: str, pnl: float, cashout_mode: str):
        """Update metrics after each round"""
        self.metrics.rounds_played += 1

        if pnl > 0:
            self.metrics.total_profit += pnl
            self.metrics.rounds_won += 1
        else:
            self.metrics.total_loss += abs(pnl)
            self.metrics.rounds_lost += 1

        self.metrics.net_pnl = self.metrics.total_profit - self.metrics.total_loss

        # Track aggressive failures
        if cashout_mode == "aggressive" and pnl < 0:
            self.aggressive_failures += 1

        # Update window
        elapsed_min = (datetime.now() - self.metrics.start_time).total_seconds() / 60
        self.metrics.current_window = 0 if elapsed_min < 15 else 1

    def track_high_mult(self, multiplier: float):
        """Track high multipliers for early abort"""
        if multiplier >= 10:
            self.high_mults_in_last_5.append(multiplier)
            if len(self.high_mults_in_last_5) > 5:
                self.high_mults_in_last_5.pop(0)

    def track_max_stake(self, stake: float):
        """Track maximum stake used"""
        if stake > self.metrics.max_stake_used:
            self.metrics.max_stake_used = stake

    def should_stop(self) -> StopDecision:
        """Evaluate all stop conditions"""

        # Profit target reached
        if self.metrics.total_profit >= self.profit_target:
            return StopDecision(
                should_stop=True,
                reason=f"Profit target reached: {self.metrics.total_profit:.0f} >= {self.profit_target}",
                category="profit_target"
            )

        # Max loss reached
        if self.metrics.total_loss >= self.max_loss:
            return StopDecision(
                should_stop=True,
                reason=f"Max loss reached: {self.metrics.total_loss:.0f} >= {self.max_loss}",
                category="loss_limit"
            )

        # Time limit exceeded
        elapsed_min = (datetime.now() - self.metrics.start_time).total_seconds() / 60
        if elapsed_min >= self.duration_minutes:
            return StopDecision(
                should_stop=True,
                reason=f"Time limit: {elapsed_min:.0f}min >= {self.duration_minutes}min",
                category="time_limit"
            )

        # Early abort conditions (first 15 min only)
        if self.metrics.current_window == 0:
            if self.metrics.total_loss >= self.early_abort_loss:
                return StopDecision(
                    should_stop=True,
                    reason=f"Early abort: loss={self.metrics.total_loss:.0f} in first 15min",
                    category="early_abort"
                )

            if self.aggressive_failures >= self.early_abort_agg_failures:
                return StopDecision(
                    should_stop=True,
                    reason=f"Early abort: {self.aggressive_failures} aggressive failures",
                    category="early_abort"
                )

            if len(self.high_mults_in_last_5) >= 2:
                return StopDecision(
                    should_stop=True,
                    reason=f"Early abort: 2+ high mults in last 5 rounds",
                    category="early_abort"
                )

        return StopDecision(should_stop=False, reason="", category="")

    def get_summary(self) -> Dict[str, Any]:
        """Get session summary"""
        elapsed = (datetime.now() - self.metrics.start_time).total_seconds() / 60
        win_rate = (self.metrics.rounds_won / self.metrics.rounds_played * 100) if self.metrics.rounds_played > 0 else 0

        return {
            "duration_min": f"{elapsed:.1f}",
            "total_profit": f"{self.metrics.total_profit:.0f}",
            "total_loss": f"{self.metrics.total_loss:.0f}",
            "net_pnl": f"{self.metrics.net_pnl:.0f}",
            "rounds_played": self.metrics.rounds_played,
            "wins": self.metrics.rounds_won,
            "losses": self.metrics.rounds_lost,
            "win_rate": f"{win_rate:.1f}%",
            "max_stake": f"{self.metrics.max_stake_used:.0f}"
        }

    def reset(self):
        """Reset session tracker"""
        self.metrics = SessionMetrics()
        self.aggressive_failures = 0
        self.high_mults_in_last_5 = []
