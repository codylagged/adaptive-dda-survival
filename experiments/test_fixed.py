"""Quick check that fixed difficulty stays constant."""

from backend.fixed_difficulty import FixedDifficulty
from backend.game_config import GameConfig
from backend.game_engine import GameEngine


def main() -> None:
    config = GameConfig()
    for level in ("easy", "medium", "hard"):
        engine = GameEngine(config, FixedDifficulty(level), seed=1)
        result = engine.run()
        print(
            f"{level:6}  survived={result.survival_time:5.1f}s  "
            f"score={result.final_score:4}  reward={result.reward:.3f}  "
            f"changes={result.difficulty_changes}"
        )


if __name__ == "__main__":
    main()
