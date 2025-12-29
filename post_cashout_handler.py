"""
Post-Cashout Handler - Outcome Processing & Stakes Management

Handles:
1. Balance verification
2. Outcome determination (WIN/LOSS/UNCERTAIN)
3. Stake adjustment based on outcome
4. Statistics updates
5. History logging
"""

from datetime import datetime
from typing import Dict, Tuple, Optional, Any


class OutcomeProcessor:
    """Processes round outcomes"""

    def process_outcome(self, cashout_result: Dict,
                       monitoring_result: Dict) -> str:
        """
        Determine final outcome from cashout and monitoring data

        Logic:
        - If cashout_success → WIN
        - If crash_detected → LOSS
        - Otherwise → UNCERTAIN

        Args:
            cashout_result: Result from cashout execution
            monitoring_result: Result from game monitoring

        Returns:
            Outcome string: 'WIN', 'LOSS', or 'UNCERTAIN'
        """
        # If cashout was successful
        if cashout_result.get('success'):
            return 'WIN'

        # If crash was detected during monitoring
        if monitoring_result.get('crash_detected'):
            return 'LOSS'

        # If game monitoring timed out or had other issues
        if not monitoring_result.get('success'):
            return 'LOSS'

        # Default to uncertain if unclear
        return 'UNCERTAIN'

    def calculate_winnings(self, stake: float,
                          final_multiplier: float) -> Tuple[float, float]:
        """
        Calculate winnings and profit

        Args:
            stake: Original stake amount
            final_multiplier: Final multiplier achieved

        Returns:
            Tuple of (winnings: float, profit: float)
        """
        winnings = stake * final_multiplier
        profit = winnings - stake

        return winnings, profit


class BalanceVerifier:
    """Verifies balance changes after rounds"""

    def __init__(self, balance_reader: Optional[Any] = None,
                 snapshot_tolerance: float = 5.0):
        """
        Initialize balance verifier

        Args:
            balance_reader: BalanceReader instance
            snapshot_tolerance: Tolerance for balance verification
        """
        self.balance_reader = balance_reader
        self.snapshot_tolerance = snapshot_tolerance
        self.pre_round_balance = None
        self.post_round_balance = None

    def take_pre_round_snapshot(self) -> Optional[float]:
        """Take balance snapshot before round"""
        if not self.balance_reader:
            return None

        try:
            self.pre_round_balance = self.balance_reader.read_balance()
            return self.pre_round_balance
        except Exception as e:
            print(f"Error reading pre-round balance: {e}")
            return None

    def verify_balance_changed(self, outcome: str) -> Tuple[bool, Optional[float], str]:
        """
        Verify balance changed according to outcome

        Args:
            outcome: Outcome from OutcomeProcessor ('WIN', 'LOSS', 'UNCERTAIN')

        Returns:
            Tuple of (verified: bool, balance_change: float, reason: str)
        """
        if not self.balance_reader:
            return False, None, "no_balance_reader"

        try:
            self.post_round_balance = self.balance_reader.read_balance()

            if self.pre_round_balance is None or self.post_round_balance is None:
                return False, None, "unreadable_balance"

            balance_change = self.post_round_balance - self.pre_round_balance

            # Verification logic
            if outcome == 'WIN':
                # Balance should increase
                if balance_change > 0:
                    return True, balance_change, "verified_win"
                else:
                    return False, balance_change, f"expected_win_but_balance_decreased_{balance_change}"

            elif outcome == 'LOSS':
                # Balance should decrease
                if balance_change < 0:
                    return True, balance_change, "verified_loss"
                else:
                    return False, balance_change, f"expected_loss_but_balance_increased_{balance_change}"

            else:  # UNCERTAIN
                # Balance may or may not change
                return True, balance_change, "uncertain_outcome_verified"

        except Exception as e:
            return False, None, f"error_verifying_balance: {str(e)}"


class StakeManager:
    """Manages stake adjustments based on outcomes"""

    def __init__(self, initial_stake: float,
                 max_stake: float,
                 increase_percent: float = 20.0):
        """
        Initialize stake manager

        Args:
            initial_stake: Initial stake amount
            max_stake: Maximum allowed stake
            increase_percent: Percentage to increase on win (default 20%)
        """
        self.initial_stake = initial_stake
        self.max_stake = max_stake
        self.increase_percent = increase_percent

    def adjust_stake(self, outcome: str,
                    current_stake: float) -> float:
        """
        Adjust stake based on round outcome

        Logic:
        - WIN: Increase by increase_percent (capped at max_stake)
        - LOSS: Reset to initial_stake
        - UNCERTAIN: No change

        Args:
            outcome: Outcome string ('WIN', 'LOSS', 'UNCERTAIN')
            current_stake: Current stake amount

        Returns:
            New stake amount
        """
        if outcome == 'WIN':
            # Increase stake by percentage
            new_stake = current_stake * (1.0 + self.increase_percent / 100.0)
            # Cap at maximum
            return min(new_stake, self.max_stake)

        elif outcome == 'LOSS':
            # Reset to initial stake
            return self.initial_stake

        else:  # UNCERTAIN or other
            # Keep current stake
            return current_stake


class PostCashoutHandler:
    """Orchestrates post-cashout processing"""

    def __init__(self, outcome_processor: OutcomeProcessor,
                 balance_verifier: BalanceVerifier,
                 stake_manager: StakeManager,
                 stats_tracker: Optional[Any] = None,
                 history_logger: Optional[Any] = None):
        """
        Initialize post-cashout handler

        Args:
            outcome_processor: OutcomeProcessor instance
            balance_verifier: BalanceVerifier instance
            stake_manager: StakeManager instance
            stats_tracker: Statistics tracking object (optional)
            history_logger: History logging object (optional)
        """
        self.outcome_processor = outcome_processor
        self.balance_verifier = balance_verifier
        self.stake_manager = stake_manager
        self.stats_tracker = stats_tracker
        self.history_logger = history_logger

    def handle_post_cashout(self, cashout_result: Dict,
                           monitoring_result: Dict,
                           bet_result: Dict,
                           signal_info: Dict,
                           current_stake: float,
                           position: int = 1) -> Dict:
        """
        Complete post-cashout processing workflow

        Includes:
        1. Determine outcome
        2. Verify balance changed
        3. Calculate winnings
        4. Adjust stake
        5. Update statistics
        6. Log to history

        Args:
            cashout_result: Result from cashout execution
            monitoring_result: Result from game monitoring
            bet_result: Result from bet placement
            signal_info: Signal information from prediction
            current_stake: Current stake amount
            position: Position 1 or 2

        Returns:
            Dict with complete round summary
        """
        # Phase 1: Determine outcome
        outcome = self.outcome_processor.process_outcome(
            cashout_result,
            monitoring_result
        )

        # Phase 2: Calculate winnings
        final_multiplier = cashout_result.get('final_multiplier',
                                              monitoring_result.get('final_multiplier', 0))
        winnings, profit = self.outcome_processor.calculate_winnings(
            current_stake,
            final_multiplier
        )

        # Phase 3: Verify balance (optional, non-blocking)
        balance_verified, balance_change, balance_reason = self.balance_verifier.verify_balance_changed(outcome)

        # Phase 4: Adjust stake
        new_stake = self.stake_manager.adjust_stake(outcome, current_stake)

        # Phase 5: Update statistics
        if self.stats_tracker:
            self._update_statistics(outcome, profit, winnings, new_stake)

        # Phase 6: Log to history
        round_summary = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'position': position,
            'signal': signal_info.get('prediction', 'UNKNOWN'),
            'signal_confidence': signal_info.get('confidence', 0),
            'stake': current_stake,
            'final_multiplier': final_multiplier,
            'winnings': winnings,
            'profit': profit,
            'outcome': outcome,
            'balance_verified': balance_verified,
            'balance_change': balance_change,
            'new_stake': new_stake,
            'cashout_details': {
                'clicked': cashout_result.get('clicked'),
                'interpretation': cashout_result.get('interpretation'),
                'color_sequence': cashout_result.get('color_sequence_str')
            },
            'monitoring_details': {
                'target_reached': monitoring_result.get('target_reached'),
                'crash_detected': monitoring_result.get('crash_detected'),
                'max_multiplier': monitoring_result.get('max_multiplier'),
                'samples_collected': monitoring_result.get('samples_collected')
            }
        }

        if self.history_logger:
            try:
                self.history_logger.log_round(round_summary)
            except Exception as e:
                print(f"Warning: Failed to log round to history: {e}")

        return round_summary

    def _update_statistics(self, outcome: str,
                          profit: float,
                          winnings: float,
                          new_stake: float) -> None:
        """Update statistics tracker"""
        try:
            if isinstance(self.stats_tracker, dict):
                # Dict-based stats
                if outcome == 'WIN':
                    self.stats_tracker['wins'] = self.stats_tracker.get('wins', 0) + 1
                elif outcome == 'LOSS':
                    self.stats_tracker['losses'] = self.stats_tracker.get('losses', 0) + 1
                else:
                    self.stats_tracker['uncertain'] = self.stats_tracker.get('uncertain', 0) + 1

                self.stats_tracker['total_profit'] = self.stats_tracker.get('total_profit', 0) + profit
                self.stats_tracker['total_winnings'] = self.stats_tracker.get('total_winnings', 0) + winnings

            else:
                # Object-based stats with methods
                if hasattr(self.stats_tracker, 'record_round'):
                    self.stats_tracker.record_round({
                        'outcome': outcome,
                        'profit': profit,
                        'winnings': winnings,
                        'new_stake': new_stake
                    })

        except Exception as e:
            print(f"Warning: Failed to update statistics: {e}")
