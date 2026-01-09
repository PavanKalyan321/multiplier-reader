#!/usr/bin/env python3
"""
Playwright Bot - Auto Bet 50 & Cashout at 55 (with Validation)
"""

import asyncio
import sys
from datetime import datetime
from playwright_browser import create_browser_manager
from playwright_game_reader import PlaywrightGameReader
from playwright_game_actions import PlaywrightGameActions
from playwright_config import PlaywrightConfig
from playwright_betting_helpers import PlaywrightBettingValidator


def log(msg):
    """Print with timestamp on single line"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {msg}", end="\r", flush=True)


async def main():
    print("\n" + "="*70)
    print("PLAYWRIGHT BOT - AUTO BET 50 & CASHOUT AT 55")
    print("="*70 + "\n")

    # Load configuration
    config = PlaywrightConfig().load()
    log("[1/3] Config loaded...")

    # Initialize browser
    await asyncio.sleep(0.5)
    log("[2/3] Initializing browser (450x600)...")
    manager = await create_browser_manager(config, headless=False)

    if not manager:
        print("\n[ERROR] Failed to initialize browser")
        return False

    page = manager.get_page()
    await asyncio.sleep(0.5)
    log("[3/3] Game modules ready...")

    # Create reader, actions, and validator
    reader = PlaywrightGameReader(page, config)
    actions = PlaywrightGameActions(page, config)
    validator = PlaywrightBettingValidator(page, config)

    await asyncio.sleep(0.5)
    print("\n[OK] Ready! Starting game automation...\n")

    # Game State Variables
    bet_placed = False
    bet_amount = 50
    cashout_target_multiplier = 1.2  # Cashout when game multiplier reaches 1.2x
    round_count = 0
    last_multiplier = 0.0
    cashout_attempted = False
    last_balance = 0.0

    # Round/Crash Detection
    round_started = False  # Track when multiplier becomes visible (> 1.0)
    round_crashed = False  # Track when multiplier disappears or returns to 1.0
    multiplier_visible = False  # Track if multiplier is currently visible

    stats = {
        'rounds_played': 0,
        'bets_placed': 0,
        'successful_cashouts': 0,
        'crashed_rounds': 0,  # Rounds where game crashed
        'lost_bets': 0,  # Bets not cashed out
        'total_profit': 0.0,
        'start_time': datetime.now(),
        'session_duration': 0
    }

    try:
        while True:
            # Read game state with fast polling (100ms for responsive cashout)
            try:
                multiplier = await reader.read_multiplier()
                balance = await reader.read_balance()
                status = await reader.get_game_status()
            except Exception as e:
                log(f"[ERROR] Reading game state: {e}")
                await asyncio.sleep(0.1)
                continue

            # Safety checks for None values
            if balance is None:
                balance = 0.0
            if status is None:
                status = "UNKNOWN"

            # ========================================================================
            # CRASH DETECTION LOGIC
            # ========================================================================
            # Track if multiplier is visible (> 1.0 means game is running)
            prev_multiplier_visible = multiplier_visible
            multiplier_visible = (multiplier is not None and multiplier > 1.0)

            # Detect round start: multiplier becomes visible (1.0 -> 1.x)
            if multiplier_visible and not prev_multiplier_visible:
                round_started = True
                round_crashed = False
                print()
                print(f"[🎮 ROUND STARTED] Multiplier visible: {multiplier:.2f}x")

            # Detect crash: multiplier disappears (becomes None/0) or returns to 1.0
            if bet_placed and (multiplier is None or (last_multiplier > 1.0 and multiplier is not None and multiplier <= 1.0)):
                if not round_crashed:  # Only log once per crash
                    round_crashed = True
                    print()
                    print(f"[💥 ROUND CRASHED] Multiplier: {last_multiplier:.2f}x → {multiplier if multiplier else 'INVISIBLE'}")
                    print(f"[LOSS] Bet was not cashed out!")

                    bet_placed = False
                    cashout_attempted = False  # Reset for next round
                    round_started = False
                    stats['crashed_rounds'] += 1
                    stats['lost_bets'] += 1
                    await asyncio.sleep(0.3)

            # Single line log (updates frequently)
            mult_str = f"{multiplier:.2f}x" if multiplier_visible else "INVISIBLE"
            cashout_ready = "READY" if (bet_placed and multiplier is not None and multiplier >= cashout_target_multiplier) else ""
            log(f"Mult: {mult_str:>10} | Bal: {balance:>8.2f} | Status: {status:>8} | Bet: {'YES' if bet_placed else 'NO'} | {cashout_ready}")

            # ========================================================================
            # BET PLACEMENT LOGIC
            # ========================================================================

            # Logic: Place bet when status is WAITING and no bet placed
            if not bet_placed and status == "WAITING":
                print()  # New line for bet placement

                # Use validation flow for bet placement
                print(f"[INFO] Placing bet with validation...")
                bet_result = await validator.validate_bet_placement_flow(bet_amount, panel=1)

                if bet_result.get('success'):
                    bet_placed = True
                    cashout_attempted = False
                    round_count += 1
                    last_multiplier = 1.0
                    stats['rounds_played'] += 1
                    stats['bets_placed'] += 1

                    # Get current balance for tracking
                    last_balance = await validator.get_current_balance() or last_balance

                    expected_profit = bet_amount * cashout_target_multiplier
                    print(f"[OK] Bet {round_count} PLACED! Amount: {bet_amount} | Target: {cashout_target_multiplier}x (Profit: {expected_profit:.2f})")
                    await asyncio.sleep(0.2)
                else:
                    # Bet placement failed
                    error = bet_result.get('steps', [{}])[-1].get('reason', 'UNKNOWN')
                    log(f"[ERROR] Bet placement failed: {error}")
                    await asyncio.sleep(0.1)

            # Logic: Cashout when multiplier reaches target
            # IMPORTANT: Check all conditions are met
            if (bet_placed and
                not cashout_attempted and
                multiplier is not None and
                multiplier >= cashout_target_multiplier):
                print()  # New line for cashout
                cashout_attempted = True
                print(f"[INFO] Cashout triggered! Multiplier: {multiplier:.2f}x, Target: {cashout_target_multiplier}x")

                # Direct click - simple and reliable
                result = await actions.click_cashout_button(panel=1, retries=3)

                if result:
                    bet_placed = False
                    cashout_attempted = False  # Reset for next round
                    actual_profit = multiplier * bet_amount
                    stats['successful_cashouts'] += 1
                    stats['total_profit'] += actual_profit

                    print(f"[✅ CASHOUT SUCCESS!] Multiplier: {multiplier:.2f}x | Profit: {actual_profit:.2f}")
                    log(f"[OK] CASHED OUT at {multiplier:.2f}x! Profit: {actual_profit:.2f}")
                    await asyncio.sleep(0.2)
                else:
                    print(f"[❌ CASHOUT FAILED!] Could not click cashout button!")
                    log(f"[ERROR] Cashout click failed at {multiplier:.2f}x")
                    stats['lost_bets'] += 1
                    bet_placed = False  # Reset bet state anyway
                    cashout_attempted = False  # Reset for next round

            # Update tracking variables
            last_multiplier = multiplier

            # Fast polling - 100ms for responsive cashout
            await asyncio.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Stopping bot...")
        if bet_placed:
            log("[ACTION] Cashing out before exit...")
            await actions.click_cashout_button(panel=1)
            await asyncio.sleep(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Calculate session duration
        stats['session_duration'] = (datetime.now() - stats['start_time']).total_seconds()

        # Print session statistics
        print("\n" + "="*70)
        print("📊 SESSION STATISTICS")
        print("="*70)

        hours = int(stats['session_duration'] // 3600)
        minutes = int((stats['session_duration'] % 3600) // 60)
        seconds = int(stats['session_duration'] % 60)

        print(f"Session Duration:         {hours}h {minutes}m {seconds}s")
        print(f"Rounds Played:            {stats['rounds_played']}")
        print(f"Bets Placed:              {stats['bets_placed']}")
        print(f"✅ Successful Cashouts:   {stats['successful_cashouts']}")
        print(f"💥 Crashed Rounds:        {stats['crashed_rounds']}")
        print(f"❌ Lost Bets:             {stats['lost_bets']}")
        print(f"\n💰 Total Profit:          {stats['total_profit']:.2f}")

        if stats['successful_cashouts'] > 0:
            print(f"📈 Avg Profit/Cashout:    {stats['total_profit'] / stats['successful_cashouts']:.2f}")
            print(f"📊 Success Rate:          {(stats['successful_cashouts'] / stats['bets_placed'] * 100):.1f}%")

        print("="*70 + "\n")

        print("[INFO] Closing browser...")
        await manager.close_session()
        print("[OK] Done!")

    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"[FATAL] {e}")
        sys.exit(1)
