# Console-based menu controller for the Aviator Bot
import os
from datetime import datetime
from config import load_game_config


class MenuController:
    """Console-based menu system for the Aviator Bot"""

    def __init__(self):
        """Initialize the menu controller"""
        self.running = True

    def clear_screen(self):
        """Clear console screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def display_menu(self):
        """Display the main menu"""
        self.clear_screen()

        print("=" * 60)
        print("AVIATOR BOT - MAIN MENU".center(60))
        print("=" * 60)
        print()

        # Check if configuration exists
        config = load_game_config()
        if config and config.is_valid():
            print("[OK] Configuration: READY".ljust(60))
        else:
            print("[!!] Configuration: NOT CONFIGURED".ljust(60))

        print()
        print("-" * 60)
        print()

        print("1. Start Monitoring")
        print("   - Begin monitoring the game and tracking multipliers")
        print()

        print("2. Configure Regions")
        print("   - Set up balance region, multiplier region, and bet button")
        print()

        print("3. Test Configuration")
        print("   - Test current configuration (read balance and multiplier)")
        print()

        print("4. WebSocket Automated Trading")
        print("   - Connect to WebSocket API for automated trading")
        print()

        print("5. Supabase Automated Trading")
        print("   - Connect to Supabase database for automated trading")
        print()

        print("6. Demo Mode")
        print("   - Run automated demo: stake 10, cashout at 1.3x multiplier")
        print()

        print("7. Model Signal Listener")
        print("   - Real-time listener for any AutoML model (PyCaret, XGBoost, CatBoost, etc.)")
        print()

        print("8. Exit")
        print("   - Close the application")
        print()

        print("-" * 60)

    def get_user_choice(self) -> int:
        """Get user menu choice with validation

        Returns:
            int: Menu choice (1-8)
        """
        while True:
            try:
                choice = input("\nEnter your choice (1-8): ").strip()

                if choice not in ['1', '2', '3', '4', '5', '6', '7', '8']:
                    print("Invalid choice. Please enter 1, 2, 3, 4, 5, 6, 7, or 8.")
                    continue

                return int(choice)

            except (ValueError, KeyboardInterrupt):
                print("Invalid input. Please enter a number between 1 and 8.")
                continue

    def run(self) -> str:
        """Run the menu and return selected action

        Returns:
            str: Action to perform ('monitor', 'configure', 'test', 'websocket', 'supabase', 'demo', 'pycaret', or 'exit')
        """
        self.display_menu()
        choice = self.get_user_choice()

        if choice == 1:
            # Validate configuration before starting monitor
            config = load_game_config()
            if not config or not config.is_valid():
                print("\n" + "!" * 60)
                print("Configuration is not complete!".center(60))
                print("!" * 60)
                print("\nPlease configure the regions first (option 2).")
                input("\nPress Enter to return to menu...")
                return self.run()

            return 'monitor'

        elif choice == 2:
            return 'configure'

        elif choice == 3:
            return 'test'

        elif choice == 4:
            return 'websocket'

        elif choice == 5:
            return 'supabase'

        elif choice == 6:
            return 'demo'

        elif choice == 7:
            return 'pycaret'

        elif choice == 8:
            return 'exit'

    def print_section_header(self, title):
        """Print a formatted section header

        Args:
            title: Section title
        """
        print("\n" + "=" * 60)
        print(title.center(60))
        print("=" * 60 + "\n")

    def print_info(self, message):
        """Print an info message with timestamp

        Args:
            message: Message to print
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] INFO: {message}")

    def print_warning(self, message):
        """Print a warning message with timestamp

        Args:
            message: Message to print
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] WARNING: {message}")

    def print_error(self, message):
        """Print an error message with timestamp

        Args:
            message: Message to print
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ERROR: {message}")
