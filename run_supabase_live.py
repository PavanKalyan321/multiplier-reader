#!/usr/bin/env python3
"""
Live Supabase Automated Trading with REAL CLICKS
Executes bets based on XGBoost model signals with bet flag = true
Cashout at expectedOutput target multiplier
"""
import asyncio
from config import load_game_config
from supabase_automated_trading import run_supabase_automated_trading


async def main():
    config = load_game_config()

    if not config or not config.is_valid():
        print("ERROR: Configuration is invalid!")
        print("Run 'python main.py' and select option 2 to configure regions")
        return

    print("=" * 60)
    print("SUPABASE AUTOMATED TRADING - LIVE MODE")
    print("=" * 60)
    print()
    print("WARNING: REAL CLICKS ENABLED")
    print("This will place REAL bets and execute REAL cashouts!")
    print()
    print("Configuration:")
    print(f"  Bet button: ({config.bet_button_point.x}, {config.bet_button_point.y})")
    print(f"  Multiplier region: ({config.multiplier_region.x1}, {config.multiplier_region.y1}) to ({config.multiplier_region.x2}, {config.multiplier_region.y2})")
    print()
    print("Signal filtering:")
    print("  Model: XGBoost only")
    print("  Trigger: bet flag = true")
    print("  Target: expectedOutput from XGBoost model")
    print()
    print("Press Ctrl+C to stop the system")
    print("=" * 60)
    print()

    # Confirm before starting
    confirm = input("Type 'START' to begin live trading: ").strip()
    if confirm != 'START':
        print("Cancelled.")
        return

    print("\nStarting live trading...")
    print()

    # Run with REAL CLICKS enabled
    await run_supabase_automated_trading(
        game_config=config,
        supabase_url="https://zofojiubrykbtmstfhzx.supabase.co",
        supabase_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvZm9qaXVicnlrYnRtc3RmaHp4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM4NzU0OTEsImV4cCI6MjA3OTQ1MTQ5MX0.mxwvnhT-ouONWff-gyqw67lKon82nBx2fsbd8meyc8s",
        poll_interval=5.0,
        confidence_strategy="moderate",
        enable_trading=True,   # REAL CLICKS
        test_mode=False        # NOT a test
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
