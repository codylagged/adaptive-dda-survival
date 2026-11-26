"""Tests for the epsilon-greedy bandit."""

from backend.bandit import EpsilonGreedyBandit


def test_sample_average_update():
    bandit = EpsilonGreedyBandit(epsilon=0.0, seed=0)
    assert bandit.estimates["medium"] == 0.0
    first = bandit.update("medium", 1.0)
    assert abs(first - 1.0) < 1e-9
    second = bandit.update("medium", 0.0)
    assert abs(second - 0.5) < 1e-9
    assert bandit.counts["medium"] == 2
    assert bandit.estimates["easy"] == 0.0


def test_exploit_when_epsilon_zero():
    bandit = EpsilonGreedyBandit(epsilon=0.0, seed=1)
    bandit.estimates["easy"] = 0.1
    bandit.estimates["medium"] = 0.4
    bandit.estimates["hard"] = 0.9
    action, kind = bandit.select_action()
    assert action == "hard"
    assert kind == "exploit"


def test_explore_when_epsilon_one():
    bandit = EpsilonGreedyBandit(epsilon=1.0, seed=2)
    draws = [bandit.select_action()[0] for _ in range(60)]
    assert set(draws) == {"easy", "medium", "hard"}
    assert bandit.exploitation_count == 0
