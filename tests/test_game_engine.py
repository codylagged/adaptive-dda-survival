"""Engine time limit, damage, and manual control."""

from backend.fixed_difficulty import FixedDifficulty
from backend.game_config import GameConfig
from backend.game_engine import GameEngine


def test_time_limit_ends_session():
    config = GameConfig()
    engine = GameEngine(config, FixedDifficulty("easy"), seed=1)
    result = engine.run()
    assert result.game_over_reason in ("time_limit", "health_depleted")
    assert result.ticks > 0


def test_manual_control_moves_player():
    config = GameConfig()
    engine = GameEngine(config, FixedDifficulty("easy"), seed=1)
    engine.manual_control = True
    start_x = engine.player.x
    engine.set_external_action({"move_x": 1.0, "move_y": 0.0, "attack": False})
    engine.step()
    assert engine.player.x > start_x
