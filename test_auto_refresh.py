"""Test script for auto-refresh functionality"""
import time
from config import load_config, get_default_region
from auto_refresh import AutoRefresher


def test_auto_refresh():
    """Test the auto-refresh functionality with a short interval"""
    print("=" * 80)
    print("AUTO-REFRESH TEST")
    print("=" * 80)
    print()

    # Load region
    region = load_config() or get_default_region()
    print(f"Region: ({region.x1}, {region.y1}) to ({region.x2}, {region.y2})")
    print(f"Top-right corner: ({region.x2}, {region.y1})")
    print()

    # Create auto-refresher with 30-second interval for testing
    print("Creating auto-refresher with 30-second interval (for testing)...")
    refresher = AutoRefresher(region, refresh_interval=30)

    # Test 1: Immediate manual refresh
    print("\nTest 1: Manual refresh (immediate)")
    print("Moving mouse and sending Ctrl+R in 3 seconds...")
    time.sleep(3)
    result = refresher.perform_refresh()
    print(f"Result: {'SUCCESS' if result else 'FAILED'}")

    # Test 2: Background auto-refresh
    print("\nTest 2: Auto-refresh background thread")
    print("Starting auto-refresher...")
    refresher.start()

    print("Waiting 35 seconds to test auto-refresh (should refresh at 30s mark)...")
    for i in range(35):
        remaining = refresher.get_time_until_next_refresh()
        print(f"\rTime until next refresh: {remaining:.1f}s", end='', flush=True)
        time.sleep(1)

    print("\n\nStopping auto-refresher...")
    refresher.stop()

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_auto_refresh()
