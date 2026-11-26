"""Fixed difficulty never changes."""

from backend.fixed_difficulty import FixedDifficulty
from backend.game_config import GameConfig, PerformanceMetrics
from backend.game_engine import GameEngine


def test_fixed_stays_constant():
    agent = FixedDifficulty("medium")
    metrics = PerformanceMetrics(
        tick=50,
        health_ratio=0.1,
        recent_damage=40,
        survival_time=5,
        performance=0.0,
        current_difficulty="medium",
        remaining_health=10,
        max_health=100,
        score=0,
        enemies_defeated=0,
    )
    decision = agent.decide(metrics)
    assert decision.difficulty == "medium"
    assert decision.changed is False


def test_engine_keeps_fixed_level():
    config = GameConfig()
    engine = GameEngine(config, FixedDifficulty("hard"), seed=3)
    result = engine.run()
    assert result.difficulty_changes == 0
    assert result.selected_difficulty == "hard"
