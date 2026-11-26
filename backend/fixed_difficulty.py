"""Fixed difficulty. The chosen level is never changed.

This is the control condition for the comparison. Easy, medium, and hard
are the same three labels the rule system and the bandit can select, but
here the label is a constant.
"""

from __future__ import annotations

from backend.game_config import DIFFICULTY_ORDER, AgentDecision, PerformanceMetrics


class FixedDifficulty:
    mode_name = "fixed"
    adapts = False
    learns_from_reward = False
    check_interval = 10**9

    def __init__(self, level: str) -> None:
        if level not in DIFFICULTY_ORDER:
            raise ValueError(f"Unknown difficulty '{level}'. Choose from {DIFFICULTY_ORDER}.")
        self.level = level
        self.change_count = 0

    def start_session(self) -> AgentDecision:
        return AgentDecision(
            difficulty=self.level,
            reason="fixed_preset",
            policy_detail="fixed",
            estimated_reward=None,
            changed=False,
        )

    def decide(self, metrics: PerformanceMetrics) -> AgentDecision:
        """Ignore health, score, and time. Always return the original level."""
        del metrics
        return AgentDecision(
            difficulty=self.level,
            reason="fixed_difficulty",
            policy_detail="fixed",
            estimated_reward=None,
            changed=False,
        )
