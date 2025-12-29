"""
Betting Orchestrator - Master Orchestrator for Complete Betting Flow

Coordinates all phases:
1. Signal validation
2. Pre-bet checks
3. Bet placement
4. Game monitoring
5. Cashout execution
6. Post-cashout processing
"""

import time
from datetime import datetime
from typing import Dict, Optional, Any, List

from signal_validator import SignalValidationOrchestrator
from game_state_validator import PreBetCheckOrchestrator
from bet_placement_orchestrator import BetPlacementOrchestrator
from game_monitoring_orchestrator import GameMonitoringOrchestrator
from cashout_orchestrator import CashoutOrchestrator
from post_cashout_handler import PostCashoutHandler


class BettingOrchestrator:
    """Master orchestrator for complete betting cycle"""

    def __init__(self, config: Dict, dependencies: Dict):
        """
        Initialize betting orchestrator

        Args:
            config: Configuration dict with thresholds and parameters
            dependencies: Dict with all required components:
                - 'signal_validator': SignalValidationOrchestrator
                - 'game_state_validator': PreBetCheckOrchestrator
                - 'bet_placement': BetPlacementOrchestrator
                - 'game_monitoring': GameMonitoringOrchestrator
                - 'cashout': CashoutOrchestrator
                - 'post_cashout': PostCashoutHandler
                - 'stats_tracker': Statistics object
        """
        self.config = config
        self.signal_validator = dependencies.get('signal_validator')
        self.game_state_validator = dependencies.get('game_state_validator')
        self.bet_placement = dependencies.get('bet_placement')
        self.game_monitoring = dependencies.get('game_monitoring')
        self.cashout = dependencies.get('cashout')
        self.post_cashout = dependencies.get('post_cashout')
        self.stats_tracker = dependencies.get('stats_tracker', {})

        self.round_history = []
        self.current_stake = config.get('initial_stake', 100)
        self.consecutive_losses = 0

    def execute_complete_betting_cycle(self,
                                      game_history: List[float],
                                      target_multiplier: float = 1.3,
                                      position: int = 1) -> Dict:
        """
        Execute complete betting cycle from signal to post-cashout

        Phases:
        1. Signal generation and validation
        2. Pre-bet checks
        3. Bet placement
        4. Game monitoring
        5. Cashout execution
        6. Post-cashout processing

        Args:
            game_history: List of recent multiplier values
            target_multiplier: Target multiplier for cashout
            position: Position 1 or 2

        Returns:
            Dict with cycle result
        """
        cycle_start = datetime.now()
        print(f"\n{'='*60}")
        print(f"STARTING BETTING CYCLE - Position {position} | Target: {target_multiplier}x")
        print(f"{'='*60}")

        # PHASE 1: Signal Validation
        print("\n[PHASE 1] Signal Validation")
        print("-" * 60)

        signal_result = self.signal_validator.validate_and_decide(
            game_history,
            strategy=self.config.get('signal_strategy', 'moderate')
        )

        position_info = signal_result.get(f'position_{position}', {})

        if not position_info.get('should_bet'):
            print(f"Signal rejected: {position_info.get('reason')}")
            return {
                'success': False,
                'error': f"signal_rejected: {position_info.get('reason')}",
                'cycle_type': 'signal_rejected'
            }

        print(f"Signal accepted: {position_info.get('signal')} @ {position_info.get('confidence'):.2%} confidence")

        # PHASE 2: Pre-Bet Checks
        print("\n[PHASE 2] Pre-Bet Validation")
        print("-" * 60)

        pre_bet_result = self.game_state_validator.run_all_checks(
            self.current_stake,
            allow_balance_unreadable=self.config.get('allow_balance_unreadable', True)
        )

        if not self.game_state_validator.should_proceed_to_bet(pre_bet_result):
            failures = ', '.join(pre_bet_result.get('failures', []))
            print(f"Pre-bet checks failed: {failures}")
            return {
                'success': False,
                'error': f"pre_bet_failed: {failures}",
                'cycle_type': 'pre_bet_failed'
            }

        print(f"All pre-bet checks passed")

        # PHASE 3: Bet Placement
        print("\n[PHASE 3] Bet Placement")
        print("-" * 60)

        bet_result = self.bet_placement.execute_bet_placement(
            stake=self.current_stake,
            position=position
        )

        if not bet_result.get('success'):
            print(f"Bet placement failed: {bet_result.get('error')}")
            return {
                'success': False,
                'error': f"bet_placement_failed: {bet_result.get('error')}",
                'cycle_type': 'bet_failed'
            }

        print(f"Bet placed successfully at stake {self.current_stake}")

        # PHASE 4: Game Monitoring
        print("\n[PHASE 4] Game Monitoring")
        print("-" * 60)

        monitoring_result = self.game_monitoring.execute_monitoring_phase(
            target_multiplier=target_multiplier
        )

        if not monitoring_result.get('success'):
            print(f"Game monitoring failed: {monitoring_result.get('error')}")
            return {
                'success': False,
                'error': f"monitoring_failed: {monitoring_result.get('error')}",
                'cycle_type': 'monitoring_failed'
            }

        if monitoring_result.get('crash_detected'):
            print(f"Game crashed at {monitoring_result.get('crash_point'):.2f}x (target: {target_multiplier}x)")

        # PHASE 5: Cashout Execution
        print("\n[PHASE 5] Cashout Execution")
        print("-" * 60)

        cashout_result = self.cashout.execute_cashout(
            final_multiplier=monitoring_result.get('final_multiplier', 0)
        )

        # PHASE 6: Post-Cashout Processing
        print("\n[PHASE 6] Post-Cashout Processing")
        print("-" * 60)

        round_summary = self.post_cashout.handle_post_cashout(
            cashout_result=cashout_result,
            monitoring_result=monitoring_result,
            bet_result=bet_result,
            signal_info=position_info,
            current_stake=self.current_stake,
            position=position
        )

        # Update state for next round
        self.current_stake = round_summary.get('new_stake', self.current_stake)

        if round_summary.get('outcome') == 'WIN':
            self.consecutive_losses = 0
            print(f"WIN: +{round_summary.get('profit'):.2f} | New stake: {self.current_stake:.2f}")
        elif round_summary.get('outcome') == 'LOSS':
            self.consecutive_losses += 1
            print(f"LOSS: -{self.current_stake:.2f} | New stake: {self.current_stake:.2f}")
        else:
            print(f"UNCERTAIN: P/L {round_summary.get('profit'):+.2f}")

        # Store in history
        self.round_history.append(round_summary)

        # Return complete result
        cycle_duration = (datetime.now() - cycle_start).total_seconds()

        complete_result = {
            'success': True,
            'cycle_type': 'complete',
            'position': position,
            'outcome': round_summary.get('outcome'),
            'final_multiplier': round_summary.get('final_multiplier'),
            'profit': round_summary.get('profit'),
            'duration': cycle_duration,
            'round_summary': round_summary,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        print(f"\n[CYCLE COMPLETE] Duration: {cycle_duration:.1f}s")
        print("=" * 60)

        return complete_result

    def execute_multi_position_cycle(self,
                                    game_history: List[float],
                                    position_1_target: float = 1.3,
                                    position_2_target: float = 1.5) -> Dict:
        """
        Execute betting cycle for both positions sequentially

        Tries Position 1 first, then Position 2 if Position 1 is rejected

        Args:
            game_history: List of recent multipliers
            position_1_target: Target for position 1
            position_2_target: Target for position 2

        Returns:
            Dict with combined result
        """
        print(f"\n{'='*60}")
        print("MULTI-POSITION CYCLE")
        print(f"{'='*60}")

        results = {
            'position_1': None,
            'position_2': None,
            'executed_position': None,
            'outcome': None
        }

        # Try Position 1
        print("\nAttempting Position 1...")
        pos1_result = self.execute_complete_betting_cycle(
            game_history=game_history,
            target_multiplier=position_1_target,
            position=1
        )

        results['position_1'] = pos1_result

        if pos1_result.get('success'):
            results['executed_position'] = 1
            results['outcome'] = pos1_result.get('outcome')
            return results

        # Position 1 failed, try Position 2
        print("\nPosition 1 not available, attempting Position 2...")
        pos2_result = self.execute_complete_betting_cycle(
            game_history=game_history,
            target_multiplier=position_2_target,
            position=2
        )

        results['position_2'] = pos2_result

        if pos2_result.get('success'):
            results['executed_position'] = 2
            results['outcome'] = pos2_result.get('outcome')
            return results

        # Both positions failed
        results['executed_position'] = None
        results['outcome'] = 'SKIPPED'

        return results

    def get_stats_summary(self) -> Dict:
        """Get statistics summary of all rounds executed"""
        if not self.round_history:
            return {'rounds_completed': 0}

        wins = sum(1 for r in self.round_history if r.get('outcome') == 'WIN')
        losses = sum(1 for r in self.round_history if r.get('outcome') == 'LOSS')
        total_profit = sum(r.get('profit', 0) for r in self.round_history)
        total_winnings = sum(r.get('winnings', 0) for r in self.round_history)

        return {
            'rounds_completed': len(self.round_history),
            'wins': wins,
            'losses': losses,
            'win_rate': (wins / len(self.round_history) * 100) if self.round_history else 0,
            'total_profit': total_profit,
            'total_winnings': total_winnings,
            'current_stake': self.current_stake,
            'consecutive_losses': self.consecutive_losses
        }

    def reset(self) -> None:
        """Reset orchestrator for new session"""
        self.round_history = []
        self.current_stake = self.config.get('initial_stake', 100)
        self.consecutive_losses = 0

    def should_continue(self) -> bool:
        """Determine if should continue with next cycle"""
        max_consecutive_losses = self.config.get('max_consecutive_losses', 5)

        if self.consecutive_losses >= max_consecutive_losses:
            print(f"Max consecutive losses ({max_consecutive_losses}) reached, stopping")
            return False

        if self.current_stake > self.config.get('max_stake', 10000):
            print(f"Stake exceeded maximum, stopping")
            return False

        return True
