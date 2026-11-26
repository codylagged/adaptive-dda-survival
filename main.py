"""Entry point for the adaptive difficulty survival project.

`python main.py` opens the Pygame window.
`python main.py --console` runs the scripted demo that appends three rows to
the CSV.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running from the project root without installing the package.
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def run_console() -> None:
    from backend.bandit import EpsilonGreedyBandit
    from backend.fixed_difficulty import FixedDifficulty
    from backend.game_config import GameConfig
    from backend.game_engine import GameEngine
    from backend.rule_based_dda import RuleBasedDDA
    from backend.data_logger import DataLogger

    config = GameConfig()
    logger = DataLogger(ROOT / "data" / "sessions.csv", ROOT / "data" / "decisions.csv")

    agents = [
        FixedDifficulty("easy"),
        RuleBasedDDA(),
        EpsilonGreedyBandit(),
    ]
    for agent in agents:
        engine = GameEngine(config, agent, seed=42)
        result = engine.run()
        logger.log_session(result)
        print(
            f"{result.session_id}: {result.experimental_mode} "
            f"survived {result.survival_time:.1f}s score={result.final_score} "
            f"reward={result.reward:.3f} reason={result.game_over_reason}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Adaptive DDA survival game")
    parser.add_argument(
        "--console",
        action="store_true",
        help="Run the scripted three-session demo instead of the window.",
    )
    args = parser.parse_args()
    if args.console:
        run_console()
        return
    from frontend.app import run

    run()


if __name__ == "__main__":
    main()
