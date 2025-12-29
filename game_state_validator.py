"""
Game State Validator Module - Pre-Bet Validation Checks

Handles:
1. Game state validation (not crashed, not busy)
2. Multiplier reader status verification
3. Stake setting verification
4. Balance readability check
5. Complete pre-bet check orchestration
"""

import time
from datetime import datetime
from typing import Dict, Tuple, Optional, Any


class GameStateValidator:
    """Validates game is ready for betting"""

    def __init__(self, game_tracker: Any, multiplier_reader: Any,
                 balance_reader: Optional[Any] = None):
        """
        Initialize game state validator

        Args:
            game_tracker: GameTracker instance for crash detection
            multiplier_reader: MultiplierReader instance
            balance_reader: BalanceReader instance (optional)
        """
        self.game_tracker = game_tracker
        self.multiplier_reader = multiplier_reader
        self.balance_reader = balance_reader

    def validate_game_not_crashed(self) -> Tuple[bool, str]:
        """
        Check if game is in crashed state

        Returns:
            Tuple of (is_ok: bool, reason: str)
        """
        try:
            # Check game tracker state
            if hasattr(self.game_tracker, 'is_crashed'):
                if self.game_tracker.is_crashed():
                    return False, "game_crashed"

            if hasattr(self.game_tracker, 'is_waiting_next_flight'):
                if self.game_tracker.is_waiting_next_flight():
                    return True, "awaiting_next_flight"

            return True, "game_ok"

        except Exception as e:
            return False, f"error_checking_state: {str(e)}"

    def verify_multiplier_reader_status(self, num_attempts: int = 3,
                                       timeout: float = 2.0) -> Tuple[bool, Dict]:
        """
        Verify multiplier reader is functional

        Tests by attempting multiple reads. At least 2 of 3 must succeed.

        Args:
            num_attempts: Number of read attempts
            timeout: Timeout per attempt

        Returns:
            Tuple of (is_ok: bool, status_dict)
        """
        successful_reads = 0
        values_read = []
        errors = []

        for attempt in range(num_attempts):
            try:
                # Attempt to read multiplier
                start_time = time.time()
                mult = self.multiplier_reader.read_multiplier()
                elapsed = time.time() - start_time

                if mult is not None and elapsed < timeout:
                    successful_reads += 1
                    values_read.append(mult)
                else:
                    errors.append(f"attempt_{attempt+1}: invalid_or_timeout")

            except Exception as e:
                errors.append(f"attempt_{attempt+1}: {str(e)}")

            time.sleep(0.1)

        # Pass if at least 2 of 3 succeeded
        reader_ok = successful_reads >= (num_attempts - 1)

        status_dict = {
            'functional': reader_ok,
            'successful_reads': successful_reads,
            'total_attempts': num_attempts,
            'values_read': values_read,
            'errors': errors,
            'confidence': successful_reads / num_attempts if num_attempts > 0 else 0.0
        }

        return reader_ok, status_dict

    def validate_balance_readable(self, timeout: float = 2.0) -> Tuple[bool, Optional[float]]:
        """
        Verify balance can be read

        Args:
            timeout: Timeout for read

        Returns:
            Tuple of (is_readable: bool, balance_value)
        """
        if not self.balance_reader:
            return False, None

        try:
            start_time = time.time()
            balance = self.balance_reader.read_balance()
            elapsed = time.time() - start_time

            if balance is not None and elapsed < timeout and balance > 0:
                return True, balance
            else:
                return False, balance

        except Exception as e:
            return False, None

    def validate_no_active_bet(self) -> Tuple[bool, str]:
        """
        Check if there's an active bet pending

        Returns:
            Tuple of (is_clear: bool, reason: str)
        """
        try:
            # Check game tracker for active bet state
            if hasattr(self.game_tracker, 'has_active_bet'):
                if self.game_tracker.has_active_bet():
                    return False, "active_bet_pending"

            return True, "no_active_bet"

        except Exception as e:
            return False, f"error_checking_bet: {str(e)}"


class StakeVerifier:
    """Verifies stake is properly set"""

    def __init__(self, stake_reader: Any):
        """
        Initialize stake verifier

        Args:
            stake_reader: StakeReader instance
        """
        self.stake_reader = stake_reader

    def verify_stake_set(self, expected_stake: float,
                        timeout: float = 2.0,
                        tolerance: float = 0.5) -> Tuple[bool, Dict]:
        """
        Verify stake is set to expected value

        Args:
            expected_stake: Expected stake amount
            timeout: Timeout for read
            tolerance: Percentage tolerance (default 0.5%)

        Returns:
            Tuple of (is_correct: bool, verification_dict)
        """
        try:
            start_time = time.time()
            actual_stake = self.stake_reader.read_stake()
            elapsed = time.time() - start_time

            if actual_stake is None or elapsed > timeout:
                return False, {
                    'expected': expected_stake,
                    'actual': actual_stake,
                    'error': 'timeout_or_unreadable'
                }

            # Check within tolerance
            difference = abs(actual_stake - expected_stake)
            max_tolerance = expected_stake * (tolerance / 100)

            is_correct = difference <= max_tolerance

            verification_dict = {
                'expected': expected_stake,
                'actual': actual_stake,
                'difference': difference,
                'tolerance': tolerance,
                'is_correct': is_correct,
                'elapsed': elapsed
            }

            return is_correct, verification_dict

        except Exception as e:
            return False, {
                'error': str(e),
                'expected': expected_stake,
                'actual': None
            }


class PreBetCheckOrchestrator:
    """Orchestrates all pre-bet validation checks"""

    def __init__(self, game_state_validator: GameStateValidator,
                 stake_verifier: StakeVerifier):
        """Initialize orchestrator"""
        self.game_state = game_state_validator
        self.stake_verifier = stake_verifier

    def run_all_checks(self, expected_stake: float,
                      allow_balance_unreadable: bool = True) -> Dict:
        """
        Execute all pre-bet validation checks

        Args:
            expected_stake: Expected stake amount to verify
            allow_balance_unreadable: If True, continue even if balance can't be read

        Returns:
            Dict with comprehensive validation results
        """
        checks_passed = True
        reasons = []

        # Check 1: Game not crashed
        game_ok, reason = self.game_state.validate_game_not_crashed()
        if not game_ok:
            checks_passed = False
            reasons.append(f"game_state: {reason}")

        # Check 2: Multiplier reader functional
        reader_ok, reader_status = self.game_state.verify_multiplier_reader_status()
        if not reader_ok:
            checks_passed = False
            reasons.append(f"multiplier_reader: {reader_status['successful_reads']}/{reader_status['total_attempts']} success")

        # Check 3: Balance readable
        balance_ok, balance_value = self.game_state.validate_balance_readable()
        if not balance_ok and not allow_balance_unreadable:
            checks_passed = False
            reasons.append("balance_not_readable")

        # Check 4: No active bet
        no_active_bet, reason = self.game_state.validate_no_active_bet()
        if not no_active_bet:
            checks_passed = False
            reasons.append(f"active_bet: {reason}")

        # Check 5: Stake verified
        stake_ok, stake_status = self.stake_verifier.verify_stake_set(expected_stake)
        if not stake_ok:
            checks_passed = False
            reasons.append(f"stake_verification: {stake_status.get('error', 'mismatch')}")

        validation_result = {
            'all_passed': checks_passed,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'checks': {
                'game_state': {
                    'passed': game_ok,
                    'status': reason
                },
                'multiplier_reader': {
                    'passed': reader_ok,
                    'details': reader_status
                },
                'balance_readable': {
                    'passed': balance_ok,
                    'balance': balance_value,
                    'allowed_to_fail': allow_balance_unreadable
                },
                'no_active_bet': {
                    'passed': no_active_bet,
                    'status': reason if not no_active_bet else "clear"
                },
                'stake_verified': {
                    'passed': stake_ok,
                    'details': stake_status
                }
            },
            'failures': reasons,
            'proceed_to_bet': checks_passed
        }

        return validation_result

    def should_proceed_to_bet(self, validation_result: Dict) -> bool:
        """
        Decision gate for bet placement

        Args:
            validation_result: Result from run_all_checks()

        Returns:
            bool indicating whether to proceed
        """
        return validation_result.get('all_passed', False)
