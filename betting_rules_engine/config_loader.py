"""Load and manage JSON betting rules configuration"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional


class BettingConfig:
    """Configuration object for betting rules"""

    def __init__(self, config_dict: Dict[str, Any]):
        self.session = config_dict.get('session', {})
        self.capital = config_dict.get('capital', {})
        self.stake_compounding = config_dict.get('stake_compounding', {})
        self.cashout = config_dict.get('cashout', {})
        self.entry_filters = config_dict.get('entry_filters', {})
        self.cooldowns = config_dict.get('cooldowns', {})
        self.regime_model = config_dict.get('regime_model', {})
        self.regime_thresholds = config_dict.get('regime_thresholds', {})
        self.stop_conditions = config_dict.get('stop_conditions', {})
        self.logging = config_dict.get('logging', {})
        self.raw = config_dict


class ConfigLoader:
    """Load and monitor JSON configuration file"""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.last_modified = 0
        self.config: Optional[BettingConfig] = None
        self.load_config()

    def load_config(self) -> BettingConfig:
        """Load and validate JSON configuration"""
        try:
            if not os.path.exists(self.config_path):
                # Create default config if doesn't exist
                self._create_default_config()

            with open(self.config_path, 'r') as f:
                config_dict = json.load(f)

            self.config = BettingConfig(config_dict)
            self.last_modified = os.path.getmtime(self.config_path)

            print(f"[CONFIG] Loaded betting rules config from {self.config_path}")
            return self.config

        except json.JSONDecodeError as e:
            print(f"[CONFIG ERROR] Invalid JSON in {self.config_path}: {e}")
            self.config = BettingConfig({})
            return self.config
        except Exception as e:
            print(f"[CONFIG ERROR] Failed to load config: {e}")
            self.config = BettingConfig({})
            return self.config

    def should_reload(self) -> bool:
        """Check if file was modified since last load"""
        try:
            if os.path.exists(self.config_path):
                current_mtime = os.path.getmtime(self.config_path)
                return current_mtime > self.last_modified
        except Exception:
            pass
        return False

    def reload_if_changed(self) -> BettingConfig:
        """Hot-reload config if file changed"""
        if self.should_reload():
            print(f"[CONFIG] Config file changed, reloading...")
            return self.load_config()
        return self.config

    def _create_default_config(self):
        """Create default configuration file"""
        default_config = {
            "session": {
                "duration_minutes": 30,
                "profit_target": 200,
                "max_loss": 200
            },
            "capital": {
                "min_balance": 1000,
                "preferred_balance": 1200,
                "start_bet": 15,
                "max_bet": 40
            },
            "stake_compounding": {
                "enabled": True,
                "win_multiplier": 1.4,
                "loss_divisor": 1.4,
                "max_steps": 3,
                "reset_on_high_mult": 10
            },
            "cashout": {
                "mode": "fixed",
                "default": {"multiplier": 1.85},
                "defensive": {"multiplier": 1.5, "trigger_loss": 80},
                "aggressive": {"multiplier": 2.5, "min_profit": 100, "require_regime": "LOOSE"}
            },
            "entry_filters": {
                "do_not_bet_if": {
                    "previous_round_gte": 10,
                    "last_3_any_gte": 20,
                    "compound_level_gte": 4
                },
                "bet_only_if": {
                    "previous_round_between": [1.4, 6.0]
                }
            },
            "cooldowns": {
                "after_high_mult": {"threshold": 10, "skip_rounds": 2, "reset_stake": True},
                "after_consecutive_losses": {"count": 2, "stake_min": 25, "skip_rounds": 2},
                "after_max_compound": {"skip_rounds": 1}
            },
            "regime_model": {
                "enabled": True,
                "evaluation_window_rounds": 60,
                "cache_duration_seconds": 180
            },
            "regime_thresholds": {
                "TIGHT": {"median_max": 2.0, "pct_below_1_5x_min": 40},
                "NORMAL": {"median_range": [2.0, 2.8]},
                "LOOSE": {"median_min": 2.5},
                "VOLATILE": {"median_min": 3.0, "high_tail_freq_min": 15}
            },
            "stop_conditions": {
                "profit_target": 200,
                "max_loss": 200,
                "duration_minutes": 30,
                "early_abort": {
                    "enabled": True,
                    "loss_in_first_window": 120,
                    "aggressive_failures": 2
                }
            },
            "logging": {
                "log_to_console": True,
                "log_to_db": False,
                "log_level": "INFO"
            }
        }

        try:
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            print(f"[CONFIG] Created default config at {self.config_path}")
        except Exception as e:
            print(f"[CONFIG ERROR] Failed to create default config: {e}")
