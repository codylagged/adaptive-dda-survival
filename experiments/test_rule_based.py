"""Show the rule table, then run a few live rule-based sessions.

Usage:

    python -m experiments.test_rule_based
"""

from __future__ import annotations

from dataclasses import replace

from backend.game_config import GameConfig
from backend.rule_based_dda import RuleBasedDDA
from experiments.run_experiments import build_rule_agent, run_session


CASES = [
    ("low health on hard", dict(current="hard", health_ratio=0.20, recent_damage=5, survival_time=8, performance=0.1, ticks_since_change=50), "medium"),
    ("low health on medium", dict(current="medium", health_ratio=0.20, recent_damage=5, survival_time=8, performance=0.1, ticks_since_change=50), "easy"),
    ("damage spike", dict(current="medium", health_ratio=0.50, recent_damage=30, survival_time=6, performance=0.1, ticks_since_change=50), "easy"),
    ("strong performance", dict(current="easy", health_ratio=0.90, recent_damage=0, survival_time=8, performance=0.5, ticks_since_change=50), "medium"),
    ("cooldown", dict(current="hard", health_ratio=0.10, recent_damage=40, survival_time=8, performance=0.0, ticks_since_change=10), "hard"),
    ("middle of the road", dict(current="medium", health_ratio=0.55, recent_damage=2, survival_time=6, performance=0.05, ticks_since_change=80), "medium"),
]


def main() -> None:
    agent = RuleBasedDDA()
    print("Rule evaluation on constructed player states")
    print(f"low health < {agent.low_health:.0%}, high health >= {agent.high_health:.0%}, cooldown {agent.min_ticks_between_changes} ticks")
    for name, kwargs, expected in CASES:
        decision = agent.evaluate(**kwargs)
        mark = "ok" if decision.difficulty == expected else "FAIL"
        print(f"  {mark}  {name}: {kwargs['current']} -> {decision.difficulty} (expected {expected})")

    print()
    print("Live sessions")
    config = GameConfig()
    for seed in range(3):
        result = run_session(build_rule_agent(config), config, seed=seed)
        print(
            f"  seed {seed}  survived={result.survival_time:5.1f}s  "
            f"score={result.final_score:4}  changes={result.difficulty_changes}  "
            f"reward={result.reward:.3f}"
        )


if __name__ == "__main__":
    main()
