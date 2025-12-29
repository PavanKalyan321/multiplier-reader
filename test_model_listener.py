#!/usr/bin/env python3
"""
Quick test script for ModelRealtimeListener
Tests connection to Supabase and basic functionality
"""
import asyncio
from config import load_game_config
from screen_capture import ScreenCapture
from multiplier_reader import MultiplierReader
from game_actions import GameActions
from model_realtime_listener import ModelRealtimeListener


async def main():
    """Test ModelRealtimeListener setup and connection"""

    print("=" * 60)
    print("MODEL REALTIME LISTENER - SETUP TEST")
    print("=" * 60)
    print()

    # Load game configuration
    print("[1/4] Loading game configuration...")
    config = load_game_config()
    if not config or not config.is_valid():
        print("ERROR: Game configuration is invalid!")
        print("Please run: python main.py -> Option 2 (Configure Regions)")
        return
    print("[OK] Configuration loaded successfully")
    print(f"  Balance region: ({config.balance_region.x1}, {config.balance_region.y1}) to ({config.balance_region.x2}, {config.balance_region.y2})")
    print(f"  Multiplier region: ({config.multiplier_region.x1}, {config.multiplier_region.y1}) to ({config.multiplier_region.x2}, {config.multiplier_region.y2})")
    print(f"  Bet button: ({config.bet_button_point.x}, {config.bet_button_point.y})")
    print()

    # Initialize components
    print("[2/4] Initializing game components...")
    try:
        screen_capture = ScreenCapture(config.multiplier_region)
        multiplier_reader = MultiplierReader(screen_capture)
        game_actions = GameActions(config.bet_button_point)
        print("[OK] Game components initialized")
    except Exception as e:
        print(f"ERROR: Failed to initialize components: {e}")
        return
    print()

    # Supabase credentials
    supabase_url = "https://zofojiubrykbtmstfhzx.supabase.co"
    supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvZm9qaXVicnlrYnRtc3RmaHp4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM4NzU0OTEsImV4cCI6MjA3OTQ1MTQ5MX0.mxwvnhT-ouONWff-gyqw67lKon82nBx2fsbd8meyc8s"

    # Create listener
    print("[3/4] Creating ModelRealtimeListener...")
    try:
        listener = ModelRealtimeListener(
            game_actions=game_actions,
            multiplier_reader=multiplier_reader,
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            model_name="PyCaret",
            min_predicted_multiplier=1.3,
            min_range_start=1.3,
            safety_margin=0.8
        )
        print("[OK] ModelRealtimeListener created successfully")
    except Exception as e:
        print(f"ERROR: Failed to create listener: {e}")
        return
    print()

    # Test Supabase connection
    print("[4/4] Testing Supabase connection...")
    try:
        connected = await listener.connect()
        if connected:
            print("[OK] Successfully connected to Supabase!")
            print(f"  URL: {supabase_url}")
            print(f"  Listening to: analytics_round_signals table")
        else:
            print("[FAIL] Failed to connect to Supabase")
            return
    except Exception as e:
        print(f"ERROR: Connection test failed: {e}")
        return
    print()

    # Test configuration summary
    print("=" * 60)
    print("LISTENER CONFIGURATION")
    print("=" * 60)
    print(f"Model Name:           PyCaret")
    print(f"Min Predicted:        1.3x")
    print(f"Min Range Start:      1.3x")
    print(f"Safety Margin:        80% (cashout at 0.8)")
    print()

    print("=" * 60)
    print("[OK] ALL TESTS PASSED - READY TO USE")
    print("=" * 60)
    print()
    print("You can now run:")
    print("  1. From menu: Select option 7 (Model Signal Listener)")
    print("  2. Or run: python main.py -> option 7")
    print()

    # Clean up
    if listener.running:
        await listener.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user.")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
