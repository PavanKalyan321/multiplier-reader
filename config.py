# Configuration file for multiplier reader
import json
import os
from dataclasses import dataclass, asdict

CONFIG_FILE = "multiplier_config.json"

@dataclass
class RegionConfig:
    """Store region coordinates for multiplier detection"""
    x1: int
    y1: int
    x2: int
    y2: int

    def is_valid(self):
        return self.x1 < self.x2 and self.y1 < self.y2

def load_config():
    """Load configuration from file"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)
            return RegionConfig(**data)
    return None

def save_config(region: RegionConfig):
    """Save configuration to file"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(asdict(region), f, indent=2)
    print(f"Configuration saved to {CONFIG_FILE}")

def get_default_region():
    """Return a default region (left side of screen)"""
    return RegionConfig(x1=0, y1=0, x2=300, y2=100)
