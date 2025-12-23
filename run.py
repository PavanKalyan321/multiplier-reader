"""Quick-start script for Multiplier Reader"""
import sys
import os
import subprocess
from config import load_config

def main():
    """Main menu"""
    print("\n" + "="*60)
    print("MULTIPLIER READER - QUICK START")
    print("="*60 + "\n")

    print("Choose an option:")
    print("1. Configure region (GUI selector)")
    print("2. Start monitoring")
    print("3. View last configuration")
    print("4. Setup dependencies")
    print("5. Exit\n")

    choice = input("Enter choice (1-5): ").strip()

    if choice == "1":
        print("\nLaunching GUI selector...")
        subprocess.run([sys.executable, "gui_selector.py"])

    elif choice == "2":
        config = load_config()
        if not config:
            print("\n⚠ No region configured!")
            print("Please run option 1 first to configure the region.\n")
            return main()

        interval = input("Enter update interval in seconds (default 0.5): ").strip()
        if interval:
            try:
                float(interval)
            except ValueError:
                print("Invalid interval. Using default 0.5")
                interval = "0.5"
        else:
            interval = "0.5"

        print(f"\nStarting multiplier reader with {interval}s intervals...")
        subprocess.run([sys.executable, "main.py", interval])

    elif choice == "3":
        config = load_config()
        if config:
            print(f"\nLast configuration:")
            print(f"  Region: ({config.x1}, {config.y1}) to ({config.x2}, {config.y2})")
            print(f"  Size: {config.x2 - config.x1}x{config.y2 - config.y1}")
        else:
            print("\nNo configuration saved yet.")
        input("\nPress Enter to continue...")
        return main()

    elif choice == "4":
        print("\nRunning setup...")
        subprocess.run([sys.executable, "setup.py"])

    elif choice == "5":
        print("\nGoodbye!")
        sys.exit(0)

    else:
        print("\nInvalid choice. Please try again.")
        return main()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)
