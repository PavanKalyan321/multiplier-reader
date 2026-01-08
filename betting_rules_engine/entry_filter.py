"""Evaluate entry filters (do_not_bet_if, bet_only_if)"""

from typing import Dict, Any, List, Tuple, Optional


class FilterResult:
    """Result of filter evaluation"""

    def __init__(self, should_bet: bool, reason: str, filters_failed: List[str]):
        self.should_bet = should_bet
        self.reason = reason
        self.filters_failed = filters_failed

    def __repr__(self):
        status = "ALLOW" if self.should_bet else "DENY"
        return f"FilterResult({status}: {self.reason})"


class EntryFilter:
    """Evaluate entry filters"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def evaluate(
        self,
        previous_round_mult: Optional[float],
        last_3_rounds_mults: List[float],
        cooldown_active: bool,
        compound_level: int,
        regime: str
    ) -> FilterResult:
        """Evaluate all entry filters"""

        filters_failed = []

        do_not_bet = self.config.get('do_not_bet_if', {})
        bet_only = self.config.get('bet_only_if', {})

        # Rule 1: Previous round >= threshold
        prev_threshold = do_not_bet.get('previous_round_gte', 10)
        if previous_round_mult is not None and previous_round_mult >= prev_threshold:
            filters_failed.append(f"previous_round={previous_round_mult:.1f}x >= {prev_threshold}x")

        # Rule 2: Any of last 3 >= threshold
        last_3_threshold = do_not_bet.get('last_3_any_gte', 20)
        if any(m >= last_3_threshold for m in last_3_rounds_mults):
            filters_failed.append(f"last_3_rounds contains {last_3_threshold}x+")

        # Rule 3: Compound level too high
        compound_max = do_not_bet.get('compound_level_gte', 4)
        if compound_level >= compound_max:
            filters_failed.append(f"compound_level={compound_level} >= {compound_max}")

        # Rule 4: Cooldown active
        if cooldown_active:
            filters_failed.append("cooldown_active=true")

        # Rule 5: Regime check (VOLATILE not allowed)
        allow_volatile = bet_only.get('allow_volatile', False)
        if regime == "VOLATILE" and not allow_volatile:
            filters_failed.append("regime=VOLATILE (not allowed)")

        # Rule 6: Previous round in range
        bet_range = bet_only.get('previous_round_between', [1.4, 6.0])
        if previous_round_mult is not None:
            if not (bet_range[0] <= previous_round_mult <= bet_range[1]):
                filters_failed.append(
                    f"previous_round={previous_round_mult:.1f}x not in range {bet_range}"
                )

        should_bet = len(filters_failed) == 0
        reason = " | ".join(filters_failed) if filters_failed else "All filters passed"

        return FilterResult(
            should_bet=should_bet,
            reason=reason,
            filters_failed=filters_failed
        )
