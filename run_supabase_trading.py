#!/usr/bin/env python3
"""
Quick script to run Supabase Automated Trading with pre-configured credentials.
Starts in TEST MODE for safe testing (no real clicks).
"""
import asyncio
from config import load_game_config
from supabase_automated_trading import run_supabase_automated_trading


async def main():
    """Run Supabase automated trading"""

    # Load configuration
    config = load_game_config()

    if not config or not config.is_valid():
        print("ERROR: Configuration is invalid!")
        return

    print("=" * 60)
    print("SUPABASE AUTOMATED TRADING - TEST MODE")
    print("=" * 60)
    print()
    print("Configuration loaded successfully:")
    print(f"  Balance region: ({config.balance_region.x1}, {config.balance_region.y1}) to ({config.balance_region.x2}, {config.balance_region.y2})")
    print(f"  Multiplier region: ({config.multiplier_region.x1}, {config.multiplier_region.y1}) to ({config.multiplier_region.x2}, {config.multiplier_region.y2})")
    print(f"  Bet button: ({config.bet_button_point.x}, {config.bet_button_point.y})")
    print()
    print("Starting Supabase Automated Trading System...")
    print("MODE: TEST (no real clicks - simulation only)")
    print("STRATEGY: Moderate (60% confidence threshold)")
    print("POLLING: Every 5 seconds")
    print()
    print("Press Ctrl+C to stop the system")
    print("=" * 60)
    print()

    # Run in test mode (no real trades)
    await run_supabase_automated_trading(
        game_config=config,
        supabase_url="https://zofojiubrykbtmstfhzx.supabase.co",
        supabase_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvZm9qaXVicnlrYnRtc3RmaHp4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM4NzU0OTEsImV4cCI6MjA3OTQ1MTQ5MX0.mxwvnhT-ouONWff-gyqw67lKon82nBx2fsbd8meyc8s",
        poll_interval=5.0,
        confidence_strategy="moderate",
        enable_trading=False,  # TEST MODE - no real trades
        test_mode=True
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nSystem stopped by user.")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
