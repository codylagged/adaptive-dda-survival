"""Rule-based controller steps difficulty up or down, and not too often."""

from backend.rule_based_dda import RuleBasedDDA


def _controller() -> RuleBasedDDA:
    return RuleBasedDDA(
        initial="medium",
        check_interval=5,
        min_ticks_between_changes=40,
        low_health=0.30,
        high_health=0.70,
        recent_damage_limit=18,
        recent_damage_health_ceiling=0.60,
        good_performance=0.20,
        min_survival_before_increase=4.0,
    )


def test_health_below_30_percent_steps_down_one_level():
    decision = _controller().evaluate(
        current="hard",
        health_ratio=0.29,
        recent_damage=0,
        survival_time=10,
        performance=1,
        ticks_since_change=40,
    )
    assert decision.changed is True
    assert decision.difficulty == "medium"
    assert decision.reason == "health_below_threshold"


def test_strong_performance_steps_up():
    decision = _controller().evaluate(
        current="easy",
        health_ratio=0.90,
        recent_damage=0,
        survival_time=8,
        performance=0.5,
        ticks_since_change=50,
    )
    assert decision.changed is True
    assert decision.difficulty == "medium"


def test_cooldown_blocks_change():
    decision = _controller().evaluate(
        current="hard",
        health_ratio=0.10,
        recent_damage=40,
        survival_time=8,
        performance=0.0,
        ticks_since_change=10,
    )
    assert decision.changed is False
    assert decision.difficulty == "hard"
