"""Session and window reward used by logging and by the bandit.

Formula
-------
pressure   = 1 - (remaining_health / max_health)
survival_n = min(survival_time / target_survival, 1)
health_n   = remaining_health / max_health
score_n    = tanh(score / score_scale)
kills_n    = tanh(enemies_defeated / kill_scale)
challenge  = clip(1 - |pressure - target_pressure| / tolerance, 0, 1)

R = w_survival * survival_n
  + w_health   * health_n
  + w_score    * score_n
  + w_kills    * kills_n
  + w_challenge * challenge
  - death_penalty   if the player died, else 0

Why each component is here
--------------------------
Survival time
    A difficulty system that kills the player immediately has failed, and a
    system that ends the session early has given the player less to do.
    The term is capped at the horizon so it cannot grow without limit.

Remaining health
    Ending a session with health left is better than ending it at zero.
    Its weight is deliberately modest. If this term dominated, Easy would
    always win because the player rarely gets hit.

Score
    Score is the in-game record of progress (defeats plus a small time
    bonus). tanh compresses very large scores. Hard uses a higher score
    multiplier, and without the squash that multiplier would favour Hard
    even when the session felt unfair.

Enemy defeats
    Defeats measure whether the player was actually in the fight. tanh
    stops a preset that simply spawns more enemies from increasing this
    term forever.

Difficulty experience (the challenge term)
    This is the piece that keeps the maximum away from a single label.
    Pressure is the fraction of health lost. The term peaks when pressure
    is near the target (default 0.40) and falls when the player is
    untouched or nearly dead. It scores the experience, not the name
    "easy" or "hard". An easy session at full health and a hard session
    that ends at 0 health both score poorly here. A session that costs
    about 40% health scores well, whichever label produced it.

Death penalty
    Health passes through the target pressure on the way to zero. Without
    a penalty, a short death could still collect a high challenge score.
    The penalty is applied only when remaining health is 0.

Window rewards and session rewards use this same function. The engine
passes a different survival target: the decision interval for a bandit
update, and the full horizon for the number written to sessions.csv.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from backend.game_config import RewardWeights


@dataclass(frozen=True)
class RewardObservation:
    survival_time: float
    remaining_health: float
    max_health: float
    score: float
    enemies_defeated: int
    died: bool


def reward_breakdown(
    observation: RewardObservation,
    weights: RewardWeights | None = None,
    survival_target: float | None = None,
) -> dict[str, float]:
    """Return every term and the total. Tests and the report use this."""
    weights = weights or RewardWeights()
    target = weights.target_survival_seconds if survival_target is None else float(survival_target)
    if target <= 0:
        raise ValueError("survival target must be positive")
    if observation.max_health <= 0:
        raise ValueError("max_health must be positive")

    health_n = min(max(observation.remaining_health / observation.max_health, 0.0), 1.0)
    pressure = 1.0 - health_n
    survival_n = min(max(observation.survival_time, 0.0) / target, 1.0)
    score_n = math.tanh(max(observation.score, 0.0) / weights.score_scale)
    kills_n = math.tanh(max(observation.enemies_defeated, 0) / weights.kill_scale)
    challenge = 1.0 - min(abs(pressure - weights.target_pressure) / weights.pressure_tolerance, 1.0)
    challenge = min(max(challenge, 0.0), 1.0)
    penalty = weights.death_penalty if observation.died or observation.remaining_health <= 0 else 0.0

    terms = {
        "survival": weights.survival * survival_n,
        "health": weights.health * health_n,
        "score": weights.score * score_n,
        "kills": weights.kills * kills_n,
        "challenge": weights.challenge * challenge,
        "death_penalty": penalty,
    }
    terms["total"] = (
        terms["survival"]
        + terms["health"]
        + terms["score"]
        + terms["kills"]
        + terms["challenge"]
        - terms["death_penalty"]
    )
    return terms


def compute_reward(
    observation: RewardObservation,
    weights: RewardWeights | None = None,
    survival_target: float | None = None,
) -> float:
    return float(reward_breakdown(observation, weights, survival_target)["total"])
