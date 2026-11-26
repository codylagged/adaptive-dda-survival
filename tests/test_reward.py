"""Reward formula terms."""

from backend.game_config import RewardWeights
from backend.reward_system import RewardObservation, compute_reward, reward_breakdown


def test_full_health_low_challenge():
    obs = RewardObservation(
        survival_time=20,
        remaining_health=100,
        max_health=100,
        score=50,
        enemies_defeated=4,
        died=False,
    )
    terms = reward_breakdown(obs)
    assert terms["challenge"] < 0.1
    assert terms["death_penalty"] == 0.0


def test_death_penalty_applied():
    obs = RewardObservation(
        survival_time=8,
        remaining_health=0,
        max_health=100,
        score=20,
        enemies_defeated=1,
        died=True,
    )
    total = compute_reward(obs)
    assert total < 0.5
