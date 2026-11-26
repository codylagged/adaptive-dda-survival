"""Epsilon-greedy multi-armed bandit for difficulty selection.

This is the standard sample-average bandit from Sutton and Barto, kept
separate from the survival simulation so it can be tested on its own.

Components
----------
Actions
    The arms are the difficulty labels: easy, medium, hard. Choosing an
    arm means "use this difficulty until the next decision".

Epsilon
    With probability epsilon the agent explores: it draws an arm uniformly
    at random. With probability 1 - epsilon it exploits: it picks an arm
    with the largest estimated reward. Ties are broken uniformly at random
    so a 0-0-0 start does not permanently prefer the first label.

Q(a)
    The estimated value of arm a. It starts at 0. After each observed
    reward it is updated in place. No table of past rewards is stored.

N(a)
    How many times arm a has been updated. The engine updates an arm once
    for every time it was selected, so N(a) is the selection count of a.

Update
    Q(a) <- Q(a) + (R - Q(a)) / N(a)
    N(a) is incremented first, so the first observation sets Q(a) = R.

The game calls `select_action` when it needs a difficulty and `update`
when that difficulty has produced a reward. The bandit does not know
about health or enemies.
"""

from __future__ import annotations

import random

from backend.game_config import DIFFICULTY_ORDER


class EpsilonGreedyBandit:
    mode_name = "bandit"
    adapts = True
    learns_from_reward = True

    def __init__(
        self,
        epsilon: float = 0.10,
        check_interval: int = 40,
        actions: tuple[str, ...] = DIFFICULTY_ORDER,
        seed: int | None = 0,
        rng=None,
        initial_value: float = 0.0,
    ) -> None:
        if not 0.0 <= float(epsilon) <= 1.0:
            raise ValueError("epsilon must be between 0 and 1")
        if check_interval < 1:
            raise ValueError("check_interval must be at least 1")
        if len(actions) < 1:
            raise ValueError("at least one action is required")
        self.epsilon = float(epsilon)
        self.check_interval = int(check_interval)
        self.actions = tuple(actions)
        self.rng = rng if rng is not None else random.Random(None if seed is None else int(seed))
        self.estimates = {action: float(initial_value) for action in self.actions}
        self.counts = {action: 0 for action in self.actions}
        self.selection_counts = {action: 0 for action in self.actions}
        self.exploration_count = 0
        self.exploitation_count = 0
        self.last_action: str | None = None
        self.last_selection_kind: str | None = None
        self.change_count = 0
        self._last_difficulty: str | None = None

    def start_session(self):
        from backend.game_config import AgentDecision

        action, kind = self.select_action()
        self._last_difficulty = action
        return AgentDecision(
            difficulty=action,
            reason=kind,
            policy_detail=self.policy_detail(kind),
            estimated_reward=self.estimates[action],
            changed=False,
        )

    def select_action(self) -> tuple[str, str]:
        """Return (action, 'explore' or 'exploit')."""
        if float(self.rng.random()) < self.epsilon:
            action = self._as_action(self.rng.choice(list(self.actions)))
            kind = "explore"
            self.exploration_count += 1
        else:
            action = self._greedy_action()
            kind = "exploit"
            self.exploitation_count += 1
        self.selection_counts[action] += 1
        self.last_action = action
        self.last_selection_kind = kind
        return action, kind

    def update(self, action: str, reward: float) -> float:
        """Incremental sample-average update. Returns the new Q(action)."""
        if action not in self.estimates:
            raise KeyError(f"Unknown action '{action}'")
        self.counts[action] += 1
        samples = self.counts[action]
        previous = self.estimates[action]
        updated = previous + (float(reward) - previous) / samples
        self.estimates[action] = updated
        return updated

    def decide(self, metrics) -> "AgentDecision":
        from backend.game_config import AgentDecision

        action, kind = self.select_action()
        changed = self._last_difficulty is not None and action != self._last_difficulty
        if changed:
            self.change_count += 1
        self._last_difficulty = action
        return AgentDecision(
            difficulty=action,
            reason=kind,
            policy_detail=self.policy_detail(kind),
            estimated_reward=self.estimates[action],
            changed=changed,
        )

    def policy_detail(self, kind: str) -> str:
        values = ", ".join(f"{name}={self.estimates[name]:.3f}" for name in self.actions)
        return f"{kind}; Q[{values}]"

    def _greedy_action(self) -> str:
        best_value = max(self.estimates[action] for action in self.actions)
        tied = [action for action in self.actions if self.estimates[action] == best_value]
        if len(tied) == 1:
            return tied[0]
        return self._as_action(self.rng.choice(tied))

    @staticmethod
    def _as_action(value) -> str:
        return str(value)
