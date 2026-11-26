"""Rule-based dynamic difficulty adjustment.

The policy is a small ordered list of rules, not a learned model. Thresholds
are constructor arguments so an experiment can change them without editing
the conditions.

Evaluation order
----------------
1. If the last change was too recent, keep the current difficulty.
2. If health is below `low_health` (default 30%), step down one level.
3. If recent damage is high and health is not comfortable, step down one level.
4. If health is high, survival is long enough, and kill-rate is high, step up.
5. Otherwise keep the current difficulty.

The level never jumps from easy to hard in one decision. It moves at most
one step along easy -> medium -> hard.
"""

from __future__ import annotations

from backend.game_config import DIFFICULTY_ORDER, AgentDecision, PerformanceMetrics


class RuleBasedDDA:
    mode_name = "rule_based"
    adapts = True
    learns_from_reward = False

    def __init__(
        self,
        initial: str = "medium",
        check_interval: int = 20,
        min_ticks_between_changes: int = 40,
        low_health: float = 0.30,
        high_health: float = 0.70,
        recent_damage_limit: float = 18.0,
        recent_damage_health_ceiling: float = 0.60,
        good_performance: float = 0.20,
        min_survival_before_increase: float = 4.0,
    ) -> None:
        if initial not in DIFFICULTY_ORDER:
            raise ValueError(f"Unknown difficulty '{initial}'. Choose from {DIFFICULTY_ORDER}.")
        if check_interval < 1:
            raise ValueError("check_interval must be at least 1")
        if min_ticks_between_changes < 1:
            raise ValueError("min_ticks_between_changes must be at least 1")
        self.initial = initial
        self.check_interval = int(check_interval)
        self.min_ticks_between_changes = int(min_ticks_between_changes)
        self.low_health = float(low_health)
        self.high_health = float(high_health)
        self.recent_damage_limit = float(recent_damage_limit)
        self.recent_damage_health_ceiling = float(recent_damage_health_ceiling)
        self.good_performance = float(good_performance)
        self.min_survival_before_increase = float(min_survival_before_increase)
        self.current = initial
        self.last_change_tick = -self.min_ticks_between_changes
        self.change_count = 0

    def start_session(self) -> AgentDecision:
        self.current = self.initial
        # The opening preset is not a "change", so the first review is allowed
        # to react immediately if the player is already in trouble.
        self.last_change_tick = -self.min_ticks_between_changes
        self.change_count = 0
        return AgentDecision(
            difficulty=self.current,
            reason="initial_difficulty",
            policy_detail="rule_based",
            estimated_reward=None,
            changed=False,
        )

    def evaluate(
        self,
        current: str,
        health_ratio: float,
        recent_damage: float,
        survival_time: float,
        performance: float,
        ticks_since_change: int,
    ) -> AgentDecision:
        """Pure rule evaluation. Does not modify controller state."""
        if current not in DIFFICULTY_ORDER:
            raise ValueError(f"Unknown difficulty '{current}'")

        if ticks_since_change < self.min_ticks_between_changes:
            return self._stay(current, "cooldown")

        if health_ratio < self.low_health:
            return self._shift(current, -1, "health_below_threshold")

        if (
            recent_damage >= self.recent_damage_limit
            and health_ratio < self.recent_damage_health_ceiling
        ):
            return self._shift(current, -1, "recent_damage_high")

        if (
            health_ratio >= self.high_health
            and performance >= self.good_performance
            and survival_time >= self.min_survival_before_increase
        ):
            return self._shift(current, +1, "strong_performance")

        return self._stay(current, "stable")

    def decide(self, metrics: PerformanceMetrics) -> AgentDecision:
        ticks_since_change = metrics.tick - self.last_change_tick
        decision = self.evaluate(
            current=self.current,
            health_ratio=metrics.health_ratio,
            recent_damage=metrics.recent_damage,
            survival_time=metrics.survival_time,
            performance=metrics.performance,
            ticks_since_change=ticks_since_change,
        )
        if decision.changed:
            self.current = decision.difficulty
            self.last_change_tick = metrics.tick
            self.change_count += 1
        return decision

    def _stay(self, current: str, reason: str) -> AgentDecision:
        return AgentDecision(
            difficulty=current,
            reason=reason,
            policy_detail="rule_based",
            estimated_reward=None,
            changed=False,
        )

    def _shift(self, current: str, delta: int, reason: str) -> AgentDecision:
        index = DIFFICULTY_ORDER.index(current)
        new_index = min(max(index + delta, 0), len(DIFFICULTY_ORDER) - 1)
        new_level = DIFFICULTY_ORDER[new_index]
        if new_level == current:
            bound = "already_at_minimum" if delta < 0 else "already_at_maximum"
            return self._stay(current, bound)
        return AgentDecision(
            difficulty=new_level,
            reason=reason,
            policy_detail="rule_based",
            estimated_reward=None,
            changed=True,
        )
