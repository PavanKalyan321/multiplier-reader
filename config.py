# Configuration file for multiplier reader
import json
import os
from dataclasses import dataclass, asdict
from typing import Optional

CONFIG_FILE = "multiplier_config.json"
GAME_CONFIG_FILE = "game_config.json"

@dataclass
class RegionConfig:
    """Store region coordinates for multiplier detection"""
    x1: int
    y1: int
    x2: int
    y2: int

    def is_valid(self):
        return self.x1 < self.x2 and self.y1 < self.y2

@dataclass
class PointConfig:
    """Store point coordinates for button clicks"""
    x: int
    y: int

    def is_valid(self):
        return self.x > 0 and self.y > 0

@dataclass
class GameConfig:
    """Unified configuration for all game actions"""
    balance_region: RegionConfig
    multiplier_region: RegionConfig
    bet_button_point: PointConfig

    def is_valid(self):
        """Validate all regions and points"""
        if not self.balance_region.is_valid():
            return False
        if not self.multiplier_region.is_valid():
            return False
        if not self.bet_button_point.is_valid():
            return False
        return True

def load_config():
    """Load configuration from file (legacy multiplier config)"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)
            return RegionConfig(**data)
    return None

def save_config(region: RegionConfig):
    """Save configuration to file (legacy)"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(asdict(region), f, indent=2)
    print(f"Configuration saved to {CONFIG_FILE}")

def get_default_region():
    """Return a default region (left side of screen)"""
    return RegionConfig(x1=0, y1=0, x2=300, y2=100)

def load_game_config() -> Optional[GameConfig]:
    """Load unified game configuration from file"""
    if os.path.exists(GAME_CONFIG_FILE):
        try:
            with open(GAME_CONFIG_FILE, 'r') as f:
                data = json.load(f)
                return GameConfig(
                    balance_region=RegionConfig(**data['balance_region']),
                    multiplier_region=RegionConfig(**data['multiplier_region']),
                    bet_button_point=PointConfig(**data['bet_button_point'])
                )
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"Error loading game config: {e}")
            return None
    return None

def save_game_config(config: GameConfig):
    """Save unified game configuration to file"""
    try:
        data = {
            'balance_region': asdict(config.balance_region),
            'multiplier_region': asdict(config.multiplier_region),
            'bet_button_point': asdict(config.bet_button_point)
        }
        with open(GAME_CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Game configuration saved to {GAME_CONFIG_FILE}")
        return True
    except Exception as e:
        print(f"Error saving game config: {e}")
        return False

def get_default_game_config() -> GameConfig:
    """Return default game configuration"""
    # Try to load existing multiplier config and use it
    existing_mult_config = load_config()
    mult_region = existing_mult_config if existing_mult_config else RegionConfig(x1=117, y1=1014, x2=292, y2=1066)

    return GameConfig(
        balance_region=RegionConfig(x1=0, y1=0, x2=0, y2=0),  # Needs configuration
        multiplier_region=mult_region,
        bet_button_point=PointConfig(x=0, y=0)  # Needs configuration
    )

def migrate_old_config():
    """Migrate old multiplier_config.json to new game_config.json format"""
    if os.path.exists(CONFIG_FILE) and not os.path.exists(GAME_CONFIG_FILE):
        try:
            old_config = load_config()
            if old_config:
                timestamp = __import__('datetime').datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] INFO: Migrating old configuration to new format...")

                new_config = GameConfig(
                    balance_region=RegionConfig(x1=0, y1=0, x2=0, y2=0),
                    multiplier_region=old_config,
                    bet_button_point=PointConfig(x=0, y=0)
                )
                save_game_config(new_config)
                print(f"[{timestamp}] INFO: Configuration migrated successfully. Please configure balance region and bet button.")
        except Exception as e:
            timestamp = __import__('datetime').datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] WARNING: Failed to migrate configuration: {e}")
