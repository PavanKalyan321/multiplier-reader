"""
Example implementations using betting_helpers module.
These are reference implementations for common betting scenarios.
"""

from betting_helpers import (
    StakeReader, update_stake, update_stake_with_history,
    update_stake_by_strategy, batch_update_stakes,
    set_stake_verified, place_bet_with_verification,
    cashout_verified, calculate_martingale_stake,
    verify_bet_placed, verify_bet_is_active
)
import time


# ============================================================================
# EXAMPLE 1: Simple Single Position Betting Loop
# ============================================================================

def example_single_position_betting(
    screen_capture, detector, stats,
    stake_coords, bet_button_coords, cashout_coords,
    initial_stake=100, max_stake=1000
):
    """
    Simple betting loop for single position.
    """
    print("\n=== EXAMPLE 1: Single Position Betting ===\n")

    reader = StakeReader()
    current_stake = initial_stake

    for round_num in range(1, 4):  # 3 rounds for demo
        print(f"Round {round_num}")

        # Set stake
        result = update_stake(
            stake_coords, current_stake,
            reader, screen_capture
        )

        if not result['success']:
            print(f"Failed to set stake: {result['message']}")
            break

        print(f"  Stake set to {current_stake}")

        # Place bet
        success, reason = place_bet_with_verification(
            bet_button_coords, detector, stats, current_stake
        )

        if not success:
            print(f"Failed to place bet: {reason}")
            break

        print(f"  Bet placed successfully")

        # Wait for game
        time.sleep(5)

        # Cashout
        cashout_success, outcome = cashout_verified(
            cashout_coords, detector
        )

        print(f"  Cashout: {outcome}")

        # Update stake based on result
        if cashout_success:
            current_stake = initial_stake  # Reset on win
            print(f"  Won! Reset stake to {initial_stake}")
        else:
            current_stake = calculate_martingale_stake(
                current_stake, 2.0, max_stake
            )
            print(f"  Lost. Doubled stake to {current_stake}")

        time.sleep(1)


# ============================================================================
# EXAMPLE 2: Strategy-Based Betting
# ============================================================================

def example_strategy_betting(
    screen_capture, detector, stats,
    stake_coords, bet_button_coords, cashout_coords,
    strategy='martingale', initial_stake=100
):
    """
    Betting using different strategies.
    """
    print("\n=== EXAMPLE 2: Strategy-Based Betting ===\n")

    reader = StakeReader()
    current_stake = initial_stake

    strategies_to_try = ['martingale', 'percentage', 'increment']

    for strategy in strategies_to_try:
        print(f"\n--- Testing {strategy} strategy ---")

        # Define parameters for each strategy
        strategy_params = {
            'martingale': {
                'multiplier': 2.0,
                'max_stake': 1000
            },
            'percentage': {
                'increase_percent': 25,
                'max_stake': 1000
            },
            'increment': {
                'increment_amount': 20,
                'max_stake': 1000
            }
        }

        params = strategy_params[strategy]

        # Update stake using strategy
        result = update_stake_by_strategy(
            stake_coords=stake_coords,
            current_stake=current_stake,
            strategy=strategy,
            params=params,
            stake_reader=reader,
            screen_capture=screen_capture
        )

        if result['success']:
            print(f"Strategy applied: {result['strategy_msg']}")
            print(f"New stake: {result['new_stake']}")
            current_stake = result['new_stake']
        else:
            print(f"Strategy failed: {result['message']}")


# ============================================================================
# EXAMPLE 3: Multi-Position Betting (Dual Browser)
# ============================================================================

def example_multi_position_betting(
    screen_capture, detector, stats,
    position1_coords, position2_coords,
    bet1_coords, bet2_coords,
    cashout1_coords, cashout2_coords,
    initial_stake=100
):
    """
    Betting on two positions simultaneously.
    """
    print("\n=== EXAMPLE 3: Multi-Position Betting ===\n")

    reader = StakeReader()
    stakes = [initial_stake, initial_stake]

    print("Round 1: Setting stakes for both positions")

    # Batch update stakes
    results = batch_update_stakes(
        stake_coords_list=[position1_coords, position2_coords],
        new_stakes=stakes,
        position_labels=['Position 1', 'Position 2']
    )

    for i, result in enumerate(results):
        if result['success']:
            print(f"  {result['position']}: Stake set to {stakes[i]}")
        else:
            print(f"  {result['position']}: Failed - {result['message']}")

    print("\nPlacing bets for both positions")

    # Place bets for both positions
    for i, (bet_coords, stake) in enumerate([(bet1_coords, stakes[0]),
                                              (bet2_coords, stakes[1])]):
        success, reason = place_bet_with_verification(
            bet_coords, detector, stats, stake
        )
        label = f"Position {i+1}"
        if success:
            print(f"  {label}: Bet placed")
        else:
            print(f"  {label}: Failed - {reason}")

    print("\nWaiting for round to complete...")
    time.sleep(5)

    print("Cashing out from both positions")

    # Cashout from both
    for i, coords in enumerate([cashout1_coords, cashout2_coords]):
        success, outcome = cashout_verified(coords, detector)
        label = f"Position {i+1}"
        if success:
            print(f"  {label}: Success - {outcome}")
        else:
            print(f"  {label}: Failed - {outcome}")


# ============================================================================
# EXAMPLE 4: History Tracking for Analysis
# ============================================================================

def example_history_tracking(
    screen_capture, detector, stats,
    stake_coords, bet_button_coords, cashout_coords,
    initial_stake=100, num_rounds=5
):
    """
    Track stake history across multiple rounds.
    """
    print("\n=== EXAMPLE 4: History Tracking ===\n")

    reader = StakeReader()
    current_stake = initial_stake
    wins = 0
    losses = 0

    for round_num in range(1, num_rounds + 1):
        print(f"Round {round_num}: Stake = {current_stake}")

        # Update with history
        result = update_stake_with_history(
            stake_coords, current_stake,
            reader, screen_capture, max_history=50
        )

        # Place and play
        time.sleep(2)

        # Simulate outcome (random for demo)
        import random
        win = random.choice([True, False])

        if win:
            wins += 1
            print(f"  Result: WIN")
            current_stake = initial_stake
            print(f"  Reset to {initial_stake}")
        else:
            losses += 1
            print(f"  Result: LOSS")
            current_stake = calculate_martingale_stake(
                current_stake, 2.0, 1000
            )
            print(f"  Doubled to {current_stake}")

        time.sleep(0.5)

    # Print summary
    print(f"\n--- Summary ---")
    print(f"Rounds: {num_rounds}")
    print(f"Wins: {wins}")
    print(f"Losses: {losses}")
    print(f"Win Rate: {wins/num_rounds*100:.1f}%")
    print(f"History Size: {len(reader.stake_history)}")


# ============================================================================
# EXAMPLE 5: Error Handling & Recovery
# ============================================================================

def example_error_handling(
    screen_capture, detector, stats,
    stake_coords, bet_button_coords, cashout_coords,
    initial_stake=100, max_retries=3
):
    """
    Handle errors and recover gracefully.
    """
    print("\n=== EXAMPLE 5: Error Handling ===\n")

    reader = StakeReader()
    current_stake = initial_stake
    retry_count = 0

    while retry_count < max_retries:
        try:
            print(f"Attempt {retry_count + 1}/{max_retries}")

            # Try to update stake
            result = update_stake(
                stake_coords, current_stake,
                reader, screen_capture
            )

            if not result['success']:
                print(f"  Warning: {result['message']}")
                retry_count += 1
                time.sleep(1)
                continue

            # Try to place bet
            success, reason = place_bet_with_verification(
                bet_button_coords, detector, stats, current_stake
            )

            if not success:
                print(f"  Warning: Bet failed - {reason}")
                retry_count += 1
                time.sleep(1)
                continue

            # If we got here, success
            print(f"  Success! Proceeding with round...")
            break

        except Exception as e:
            print(f"  Error: {e}")
            retry_count += 1
            time.sleep(2)

    if retry_count >= max_retries:
        print(f"Failed after {max_retries} retries. Aborting.")
        return False

    print("Continuing to cashout...")
    cashout_verified(cashout_coords, detector)

    return True


# ============================================================================
# EXAMPLE 6: Verification & Validation
# ============================================================================

def example_verification(
    screen_capture, detector, stats,
    stake_coords, bet_button_coords, cashout_coords,
    initial_stake=100
):
    """
    Verify all operations before proceeding.
    """
    print("\n=== EXAMPLE 6: Verification ===\n")

    reader = StakeReader()

    # Verify stake was read
    print("1. Verifying stake reading...")
    stake_status = reader.get_stake_with_status(screen_capture)
    if stake_status['status'] == 'ERROR':
        print(f"  ERROR: {stake_status['message']}")
        return False
    print(f"  OK: {stake_status['message']}")

    # Set new stake
    print("\n2. Setting new stake...")
    result = update_stake(stake_coords, initial_stake, reader, screen_capture)
    if not result['success']:
        print(f"  ERROR: {result['message']}")
        return False
    if not result['verified']:
        print(f"  WARNING: Not verified - {result['message']}")
    else:
        print(f"  OK: {result['message']}")

    # Verify bet placement possible
    print("\n3. Verifying bet can be placed...")
    is_placed, status = verify_bet_placed(bet_button_coords, detector)
    if is_placed:
        print(f"  WARNING: Bet already placed!")
    else:
        print(f"  OK: Ready to place bet")

    # Place bet
    print("\n4. Placing bet...")
    success, reason = place_bet_with_verification(
        bet_button_coords, detector, stats, initial_stake
    )
    if not success:
        print(f"  ERROR: {reason}")
        return False
    print(f"  OK: Bet placed")

    # Verify active bet
    print("\n5. Verifying active bet...")
    is_active = verify_bet_is_active(cashout_coords, detector)
    if is_active:
        print(f"  OK: Bet is active")
    else:
        print(f"  WARNING: Bet may not be active")

    print("\nAll verifications passed!")
    return True


# ============================================================================
# MAIN - Run examples
# ============================================================================

if __name__ == "__main__":
    """
    Run example functions (commented by default)
    Uncomment the examples you want to run.

    Note: These require proper setup with screen_capture, detector, etc.
    They are for reference/documentation only.
    """

    print("Betting Helpers - Example Implementations")
    print("=" * 60)
    print("\nThese are reference implementations.")
    print("Uncomment example functions in main block to run them.")
    print("\nAvailable examples:")
    print("  1. example_single_position_betting()")
    print("  2. example_strategy_betting()")
    print("  3. example_multi_position_betting()")
    print("  4. example_history_tracking()")
    print("  5. example_error_handling()")
    print("  6. example_verification()")
