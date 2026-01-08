"""Main orchestrator for betting rules engine"""

import os
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

from .config_loader import ConfigLoader
from .regime_detector import RegimeDetector
from .entry_filter import EntryFilter
from .cooldown_manager import CooldownManager
from .stake_manager import StakeManager
from .cashout_selector import CashoutSelector
from .session_tracker import SessionTracker
from .historical_data import HistoricalDataCache, RoundData


class BettingRulesEngine:
    """Main orchestrator for all rule modules"""

    def __init__(self, config_path: str):
        """Initialize rules engine"""

        self.config_loader = ConfigLoader(config_path)
        self.config = self.config_loader.config

        # Initialize modules
        self.historical_cache = HistoricalDataCache(maxlen=10)
        self.regime_detector = RegimeDetector(self.config.regime_thresholds)
        self.entry_filter = EntryFilter(self.config.entry_filters)
        self.cooldown_manager = CooldownManager(self.config.cooldowns)
        self.stake_manager = StakeManager(self.config.capital)
        self.cashout_selector = CashoutSelector(self.config.cashout)
        self.session_tracker = SessionTracker(self.config.stop_conditions)

        # State tracking
        self.last_round_result = None
        self.consecutive_losses = 0
        self.current_regime = "NORMAL"
        self.enabled = True

        self._log("Betting rules engine initialized", "INFO")

    def check_config_reload(self):
        """Hot-reload config if file changed"""
        if self.config_loader.should_reload():
            try:
                self.config = self.config_loader.reload_if_changed()
                self._log("Config reloaded successfully", "INFO")
            except Exception as e:
                self._log(f"Config reload failed: {e}", "ERROR")

    def evaluate_entry(self, predicted_mult: float, ai_confidence: float) -> Tuple[bool, str]:
        """INJECTION POINT #1: Evaluate if should enter this trade"""

        if not self.enabled:
            return True, "Rules engine disabled"

        self.check_config_reload()

        # Detect current regime
        mults = self.historical_cache.get_multipliers()
        if mults:
            regime_result = self.regime_detector.detect_regime(mults)
            self.current_regime = regime_result.regime
            self._log(
                f"Current regime: {self.current_regime} (median={regime_result.features.median:.2f}x, "
                f"conf={regime_result.confidence:.0%})",
                "INFO"
            )

        # Check cooldown
        cooldown_active = self.cooldown_manager.is_active()
        if cooldown_active:
            status = self.cooldown_manager.get_status()
            return False, f"Cooldown: {status['reason']} ({status['rounds_remaining']} rounds)"

        # Get last 3 rounds
        last_3 = self.historical_cache.get_last_n_rounds(3)
        last_3_mults = [r.multiplier for r in last_3]

        prev_round = self.historical_cache.get_previous_round()
        prev_mult = prev_round.multiplier if prev_round else None

        # Evaluate entry filters
        filter_result = self.entry_filter.evaluate(
            previous_round_mult=prev_mult,
            last_3_rounds_mults=last_3_mults,
            cooldown_active=cooldown_active,
            compound_level=self.stake_manager.compound_level,
            regime=self.current_regime
        )

        if not filter_result.should_bet:
            return False, f"Entry filters: {filter_result.reason}"

        self._log("Entry evaluation: APPROVED", "INFO")
        return True, "Entry approved"

    def calculate_stake_for_bet(self) -> Tuple[float, int]:
        """INJECTION POINT #4: Calculate stake amount"""

        prev_round = self.historical_cache.get_previous_round()
        last_mult = prev_round.multiplier if prev_round else 0

        stake_decision = self.stake_manager.calculate_stake(
            last_result=self.last_round_result or "skip",
            last_round_mult=last_mult,
            consecutive_losses=self.consecutive_losses,
            regime=self.current_regime
        )

        self._log(
            f"Stake decision: {stake_decision.stake:.2f} "
            f"(compound_level={stake_decision.compound_level}, reason={stake_decision.reason})",
            "INFO"
        )

        self.session_tracker.track_max_stake(stake_decision.stake)
        return stake_decision.stake, stake_decision.compound_level

    def calculate_cashout_target(self, predicted_mult: float) -> Tuple[float, str]:
        """INJECTION POINT #3: Calculate cashout multiplier"""

        cashout_decision = self.cashout_selector.select_cashout(
            session_profit=self.session_tracker.metrics.total_profit,
            session_loss=self.session_tracker.metrics.total_loss,
            compound_level=self.stake_manager.compound_level,
            regime=self.current_regime
        )

        self._log(
            f"Cashout: {cashout_decision.mode} mode → {cashout_decision.multiplier:.2f}x "
            f"({cashout_decision.reason})",
            "INFO"
        )

        return cashout_decision.multiplier, cashout_decision.mode

    def process_round_result(
        self,
        round_id: int,
        final_mult: float,
        pnl: float,
        cashout_mode: str
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """INJECTION POINT #5: Process completed round"""

        # Determine win/loss
        result = "win" if pnl > 0 else "loss"

        # Update session tracker
        self.session_tracker.update_metrics(result, pnl, cashout_mode)
        self.session_tracker.track_high_mult(final_mult)

        # Update consecutive losses
        if result == "loss":
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0

        self.last_round_result = result

        # Add to historical cache
        round_data = RoundData(
            round_id=round_id,
            multiplier=final_mult
        )
        round_data.compound_level = self.stake_manager.compound_level
        self.historical_cache.add_round(round_data)

        # Check/apply cooldowns
        self.cooldown_manager.check_and_activate(
            last_round_mult=final_mult,
            last_stake=self.stake_manager.current_stake,
            compound_level=self.stake_manager.compound_level,
            consecutive_losses=self.consecutive_losses
        )

        # Always decrement cooldown
        self.cooldown_manager.decrement()

        # Log round result
        self._log(
            f"Round {round_id}: {result.upper()} | Mult: {final_mult:.2f}x | "
            f"P&L: {pnl:+.0f} | Profit: {self.session_tracker.metrics.total_profit:.0f} | "
            f"Loss: {self.session_tracker.metrics.total_loss:.0f}",
            "INFO"
        )

        # Check stop conditions
        stop_decision = self.session_tracker.should_stop()
        if stop_decision.should_stop:
            self._log(f"SESSION STOP: {stop_decision.reason}", "WARNING")
            summary = self.session_tracker.get_summary()
            self._log(f"Session summary: {summary}", "INFO")
            return True, stop_decision

        return False, None

    def reset_session(self):
        """Reset session tracker for new session"""
        self.session_tracker.reset()
        self.consecutive_losses = 0
        self.last_round_result = None
        self.cashout_selector.reset_window()
        self._log("Session reset", "INFO")

    def get_status(self) -> Dict[str, Any]:
        """Get current engine status"""
        return {
            "enabled": self.enabled,
            "regime": self.current_regime,
            "stake": f"{self.stake_manager.current_stake:.2f}",
            "compound_level": self.stake_manager.compound_level,
            "cooldown_active": self.cooldown_manager.is_active(),
            "session_profit": f"{self.session_tracker.metrics.total_profit:.0f}",
            "session_loss": f"{self.session_tracker.metrics.total_loss:.0f}",
            "rounds_played": self.session_tracker.metrics.rounds_played,
            "consecutive_losses": self.consecutive_losses
        }

    def _log(self, message: str, level: str = "INFO"):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] RULES-ENGINE {level}: {message}")
