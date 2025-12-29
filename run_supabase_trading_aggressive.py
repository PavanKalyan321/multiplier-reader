#!/usr/bin/env python3
"""
Run Supabase trading with AGGRESSIVE strategy (40% threshold)
This will execute signals with 0.1%+ confidence
"""
import asyncio
from config import load_game_config
from supabase_automated_trading import run_supabase_automated_trading


async def main():
    config = load_game_config()

    if not config or not config.is_valid():
        print("ERROR: Configuration is invalid!")
        return

    print("=" * 60)
    print("SUPABASE AUTOMATED TRADING - AGGRESSIVE MODE")
    print("=" * 60)
    print()
    print("Configuration loaded successfully")
    print()
    print("Starting with AGGRESSIVE strategy...")
    print("MODE: TEST (no real clicks - simulation only)")
    print("STRATEGY: Aggressive (40% confidence threshold)")
    print("RESULT: All signals with 40%+ confidence will execute")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    # Run with AGGRESSIVE strategy (40% threshold)
    await run_supabase_automated_trading(
        game_config=config,
        supabase_url="https://zofojiubrykbtmstfhzx.supabase.co",
        supabase_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvZm9qaXVicnlrYnRtc3RmaHp4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM4NzU0OTEsImV4cCI6MjA3OTQ1MTQ5MX0.mxwvnhT-ouONWff-gyqw67lKon82nBx2fsbd8meyc8s",
        poll_interval=5.0,
        confidence_strategy="aggressive",  # 40% threshold
        enable_trading=False,  # TEST MODE
        test_mode=True
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nSystem stopped.")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
