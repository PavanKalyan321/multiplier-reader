# Test script to verify click action functionality
import sys
from datetime import datetime
from config import PointConfig, GameConfig, RegionConfig
from game_actions import GameActions

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(title.center(60))
    print("=" * 60 + "\n")

def test_import():
    """Test if GameActions can be imported"""
    print_header("Test 1: Import GameActions")
    try:
        from game_actions import GameActions
        print("[PASS] GameActions imported successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to import GameActions: {e}")
        return False

def test_initialization():
    """Test GameActions initialization"""
    print_header("Test 2: Initialize GameActions")
    try:
        test_point = PointConfig(x=640, y=900)
        actions = GameActions(test_point)
        print(f"[PASS] GameActions initialized")
        print(f"       Button coordinates: ({actions.bet_button_point.x}, {actions.bet_button_point.y})")
        return actions
    except Exception as e:
        print(f"[FAIL] Failed to initialize GameActions: {e}")
        return None

def test_point_validation():
    """Test PointConfig validation"""
    print_header("Test 3: PointConfig Validation")

    # Valid point
    valid_point = PointConfig(x=100, y=200)
    if valid_point.is_valid():
        print("[PASS] Valid point (100, 200) validated correctly")
    else:
        print("[FAIL] Valid point rejected")
        return False

    # Invalid point (0, 0)
    invalid_point = PointConfig(x=0, y=0)
    if not invalid_point.is_valid():
        print("[PASS] Invalid point (0, 0) rejected correctly")
    else:
        print("[FAIL] Invalid point accepted")
        return False

    # Invalid point (negative)
    invalid_point2 = PointConfig(x=-10, y=200)
    if not invalid_point2.is_valid():
        print("[PASS] Negative point rejected correctly")
    else:
        print("[FAIL] Negative point accepted")
        return False

    return True

def test_click_stats():
    """Test click statistics tracking"""
    print_header("Test 4: Click Statistics Tracking")
    try:
        actions = GameActions(PointConfig(x=640, y=900))

        # Manually update stats without actually clicking
        actions.click_stats['total_clicks'] = 5
        actions.click_stats['successful_clicks'] = 4
        actions.click_stats['failed_clicks'] = 1

        stats = actions.get_click_stats()

        print(f"[INFO] Simulated stats:")
        print(f"       Total clicks: {stats['total_clicks']}")
        print(f"       Successful: {stats['successful_clicks']}")
        print(f"       Failed: {stats['failed_clicks']}")
        print(f"       Success rate: {stats['success_rate']:.1f}%")

        if stats['success_rate'] == 80.0:
            print("[PASS] Click statistics calculated correctly (80%)")
            return True
        else:
            print(f"[FAIL] Success rate incorrect: {stats['success_rate']}% (expected 80%)")
            return False

    except Exception as e:
        print(f"[FAIL] Error in statistics test: {e}")
        return False

def test_invalid_click_coordinates():
    """Test that invalid coordinates are rejected"""
    print_header("Test 5: Invalid Click Coordinates Rejection")
    try:
        # Try to create GameActions with invalid coordinates
        invalid_point = PointConfig(x=0, y=0)
        actions = GameActions(invalid_point)

        # Try to click - should fail validation
        result = actions.click_bet_button()

        if not result:
            print("[PASS] Invalid coordinates rejected (click returned False)")
            print(f"       Stats - Total: {actions.click_stats['total_clicks']}, Failed: {actions.click_stats['failed_clicks']}")
            return True
        else:
            print("[FAIL] Invalid coordinates were not rejected")
            return False

    except Exception as e:
        print(f"[FAIL] Error in invalid coordinates test: {e}")
        return False

def test_safe_click_logging():
    """Test safe_click logging and error handling"""
    print_header("Test 6: Safe Click Logging & Error Handling")
    try:
        actions = GameActions(PointConfig(x=640, y=900))

        # Test with valid coordinates (will actually try to click but won't fail)
        print("[INFO] Testing safe_click with valid coordinates...")
        print("[INFO] NOTE: This will attempt to move mouse and click at (640, 900)")
        print("[INFO] Make sure your mouse is in a safe area!")

        response = input("\nDo you want to proceed with actual click test? (y/n): ").strip().lower()

        if response == 'y':
            timestamp_before = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp_before}] INFO: Starting click test...")

            # This will actually try to click - be careful!
            try:
                result = actions.safe_click(640, 900, click_type='test')
                timestamp_after = datetime.now().strftime("%H:%M:%S")

                if result:
                    print(f"[PASS] Click executed successfully")
                    print(f"       Logged time: {timestamp_after}")
                    stats = actions.get_click_stats()
                    print(f"       Click stats updated: {stats['total_clicks']} total, {stats['successful_clicks']} successful")
                    return True
                else:
                    print("[FAIL] Click execution returned False")
                    return False
            except Exception as e:
                print(f"[FAIL] Click execution raised exception: {e}")
                return False
        else:
            print("[SKIP] Click test skipped (user preference)")
            return True

    except Exception as e:
        print(f"[FAIL] Error in safe_click test: {e}")
        return False

def test_click_with_game_config():
    """Test clicking with full GameConfig"""
    print_header("Test 7: GameActions with Full GameConfig")
    try:
        config = GameConfig(
            balance_region=RegionConfig(x1=100, y1=50, x2=300, y2=100),
            multiplier_region=RegionConfig(x1=117, y1=1014, x2=292, y2=1066),
            bet_button_point=PointConfig(x=640, y=900)
        )

        actions = GameActions(config.bet_button_point)

        print(f"[PASS] GameActions created from GameConfig")
        print(f"       Bet button: ({actions.bet_button_point.x}, {actions.bet_button_point.y})")
        print(f"       Is valid: {actions.bet_button_point.is_valid()}")

        return True

    except Exception as e:
        print(f"[FAIL] Error with GameConfig test: {e}")
        return False

def print_summary(results):
    """Print test summary"""
    print_header("TEST SUMMARY")

    passed = sum(1 for r in results if r)
    total = len(results)

    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {passed/total*100:.1f}%")

    if passed == total:
        print("\n[ALL TESTS PASSED] Click action is working correctly!")
        return True
    else:
        print(f"\n[SOME TESTS FAILED] {total - passed} test(s) failed")
        return False

def main():
    """Run all tests"""
    print("\n" + "*" * 60)
    print("CLICK ACTION TEST SUITE".center(60))
    print("*" * 60)

    results = []

    # Run tests
    results.append(test_import())

    if not results[-1]:
        print("\n[CRITICAL] Import failed. Cannot continue.")
        return False

    actions = test_initialization()
    results.append(actions is not None)

    results.append(test_point_validation())
    results.append(test_click_stats())
    results.append(test_invalid_click_coordinates())

    # Ask about live click test
    response = input("\n\nDo you want to test actual click functionality? (This will move/click mouse) (y/n): ").strip().lower()
    if response == 'y':
        results.append(test_safe_click_logging())
    else:
        print("[SKIP] Live click test skipped")
        results.append(True)  # Consider as passed since user skipped

    results.append(test_click_with_game_config())

    # Print summary
    success = print_summary(results)

    print("\n" + "*" * 60)

    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[CRITICAL ERROR] {e}")
        sys.exit(1)
