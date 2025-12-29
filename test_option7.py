#!/usr/bin/env python3
"""
Test Option 7: Model Signal Listener from main menu
"""
import asyncio
from config import load_game_config
from screen_capture import ScreenCapture
from multiplier_reader import MultiplierReader
from game_actions import GameActions
from model_realtime_listener import ModelRealtimeListener


async def test_option7():
    """Simulate running option 7 from main menu"""

    print("\n" + "=" * 60)
    print("Testing Option 7: Model Signal Listener")
    print("=" * 60 + "\n")

    # Load configuration
    config = load_game_config()
    if not config or not config.is_valid():
        print("ERROR: Configuration is invalid!")
        return

    print("[OK] Configuration loaded")

    # Initialize components
    screen_capture = ScreenCapture(config.multiplier_region)
    multiplier_reader = MultiplierReader(screen_capture)
    game_actions = GameActions(config.bet_button_point)

    print("[OK] Components initialized")

    # Supabase credentials (pre-configured)
    supabase_url = "https://zofojiubrykbtmstfhzx.supabase.co"
    supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvZm9qaXVicnlrYnRtc3RmaHp4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM4NzU0OTEsImV4cCI6MjA3OTQ1MTQ5MX0.mxwvnhT-ouONWff-gyqw67lKon82nBx2fsbd8meyc8s"

    # Create listener with default settings
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

    print("\n" + "=" * 60)
    print("Starting PyCaret Real-Time Listener")
    print("=" * 60)
    print("Model:             PyCaret")
    print("Min Predicted:     1.3x")
    print("Min Range Start:   1.3x")
    print("Safety Margin:     80% (cashout at 0.8)")
    print("Listening for analytics_round_signals table updates...")
    print("Press Ctrl+C to stop\n")

    try:
        # Run listener with 30-second timeout for testing
        await asyncio.wait_for(listener.listen(), timeout=30)
    except asyncio.TimeoutError:
        print("\nTest timeout (30 seconds) - stopping listener")
    except KeyboardInterrupt:
        print("\nListener stopped by user")
    finally:
        # Show statistics
        stats = listener.get_stats()
        print("\n" + "=" * 60)
        print("Listener Statistics")
        print("=" * 60)
        print(f"Total Executions:      {stats['execution_count']}")
        print(f"Qualified Bets:        {stats['qualified_bets']}")
        print(f"Successful Trades:     {stats['successful_trades']}")
        print(f"Failed Trades:         {stats['failed_trades']}")
        print(f"Qualification Rate:    {stats['qualification_rate']:.1f}%")
        print(f"Success Rate:          {stats['success_rate']:.1f}%")
        print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(test_option7())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
