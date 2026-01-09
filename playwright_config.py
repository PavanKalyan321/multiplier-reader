"""
Playwright Configuration - Store selectors and browser settings
"""

import json
import os
from typing import Dict, Any, Optional

try:
    from playwright.async_api import Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class PlaywrightConfig:
    """Manage Playwright configuration"""

    DEFAULT_CONFIG = {
        "game_url": "https://demo.aviatrix.bet/?cid=cricazaprod&isDemo=true&lang=en&sessionToken=",
        "selectors": {
            "multiplier": ".game-score .game-score-char",
            "balance": ".header-balance .text-subheading-3",
            "bet_button_1": "[data-testid='button-place-bet-1']",
            "bet_button_2": "[data-testid='button-place-bet-2']",
            "cashout_button_1": "[data-testid='button-cashout-1']",
            "cashout_button_2": "[data-testid='button-cashout-2']",
            "bet_amount_input_1": "[data-testid='bet-input-amount-1'] input",
            "bet_amount_input_2": "[data-testid='bet-input-amount-2'] input",
            "auto_cashout_input_1": "[data-testid='bet-input-cashout-1'] input",
            "auto_cashout_input_2": "[data-testid='bet-input-cashout-2'] input"
        },
        "browser": {
            "headless": False,
            "viewport_width": 1920,
            "viewport_height": 1080,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        },
        "anti_detection": {
            "use_stealth": True,
            "randomize_timing": True,
            "human_like_delays": True,
            "click_delay_min": 50,
            "click_delay_max": 300
        },
        "timeouts": {
            "page_load": 30000,
            "element_wait": 5000,
            "bet_wait": 30000,
            "cashout_wait": 5000
        }
    }

    def __init__(self, config_file: str = "playwright_config.json"):
        """
        Initialize configuration

        Args:
            config_file: Path to configuration JSON file
        """
        self.config_file = config_file
        self.config = self.load()

    def load(self) -> Dict[str, Any]:
        """
        Load configuration from file, or create default if not exists

        Returns:
            Configuration dictionary
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                print(f"[OK] Configuration loaded from {self.config_file}")
                return config
            except Exception as e:
                print(f"[ERROR] Failed to load config: {e}")
                print("[INFO] Using default configuration")
                return self.DEFAULT_CONFIG.copy()
        else:
            print(f"[INFO] Configuration file not found, creating default: {self.config_file}")
            self.save(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()

    def save(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save configuration to file

        Args:
            config: Configuration to save (uses self.config if not provided)

        Returns:
            True if successful, False otherwise
        """
        try:
            to_save = config if config is not None else self.config

            with open(self.config_file, 'w') as f:
                json.dump(to_save, f, indent=2)

            print(f"[OK] Configuration saved to {self.config_file}")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to save config: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key

        Args:
            key: Configuration key (supports dot notation: 'browser.headless')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value if value is not None else default

    def set(self, key: str, value: Any) -> bool:
        """
        Set configuration value by key

        Args:
            key: Configuration key (supports dot notation: 'browser.headless')
            value: Value to set

        Returns:
            True if successful, False otherwise
        """
        try:
            keys = key.split('.')
            config = self.config

            # Navigate to parent of target key
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]

            # Set value
            config[keys[-1]] = value

            print(f"[OK] Set {key} = {value}")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to set config: {e}")
            return False

    def get_selector(self, name: str) -> Optional[str]:
        """
        Get CSS selector by name

        Args:
            name: Selector name (e.g., 'multiplier', 'bet_button_1')

        Returns:
            CSS selector or None if not found
        """
        return self.config.get('selectors', {}).get(name)

    def update_selector(self, name: str, selector: str) -> bool:
        """
        Update CSS selector

        Args:
            name: Selector name
            selector: New CSS selector

        Returns:
            True if successful
        """
        if 'selectors' not in self.config:
            self.config['selectors'] = {}

        self.config['selectors'][name] = selector
        return self.save()

    async def validate_selectors(self, page: 'Page') -> Dict[str, bool]:
        """
        Validate all selectors by checking if elements exist on page

        Args:
            page: Playwright page object

        Returns:
            Dict of selector_name -> is_valid
        """
        results = {}

        for name, selector in self.config.get('selectors', {}).items():
            try:
                elements = await page.locator(selector).all()
                is_valid = len(elements) > 0
                results[name] = is_valid

                status = "[OK]" if is_valid else "[WARN]"
                print(f"{status} Selector '{name}': {is_valid}")

            except Exception as e:
                results[name] = False
                print(f"[ERROR] Selector '{name}' failed: {e}")

        return results

    def get_browser_config(self) -> Dict[str, Any]:
        """Get browser configuration"""
        return self.config.get('browser', {})

    def get_anti_detection_config(self) -> Dict[str, Any]:
        """Get anti-detection configuration"""
        return self.config.get('anti_detection', {})

    def get_timeouts(self) -> Dict[str, int]:
        """Get timeout configuration"""
        return self.config.get('timeouts', {})

    def export_to_dict(self) -> Dict[str, Any]:
        """Export full configuration as dictionary"""
        return self.config.copy()

    def import_from_dict(self, config: Dict[str, Any]) -> bool:
        """
        Import configuration from dictionary

        Args:
            config: Configuration dictionary

        Returns:
            True if successful
        """
        try:
            self.config = config
            return self.save()
        except Exception as e:
            print(f"[ERROR] Failed to import config: {e}")
            return False


# Helper function to create default config file
def create_default_config(filename: str = "playwright_config.json") -> bool:
    """
    Create default configuration file

    Args:
        filename: Configuration filename

    Returns:
        True if successful
    """
    try:
        with open(filename, 'w') as f:
            json.dump(PlaywrightConfig.DEFAULT_CONFIG, f, indent=2)
        print(f"[OK] Default configuration created: {filename}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create default config: {e}")
        return False


# Example usage
if __name__ == "__main__":
    # Create default config
    create_default_config()

    # Load and modify config
    config = PlaywrightConfig()

    print("\nCurrent configuration:")
    print(json.dumps(config.export_to_dict(), indent=2))

    # Update a selector
    config.update_selector('multiplier', '.new-multiplier-selector')

    # Get specific values
    print(f"\nGame URL: {config.get('game_url')}")
    print(f"Headless: {config.get('browser.headless')}")
    print(f"Multiplier selector: {config.get_selector('multiplier')}")
