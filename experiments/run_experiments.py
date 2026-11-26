"""Batch runner used by the experiment scripts and the presentation logs.

The numbers printed here are computed from the simulation. They are not
hand-written. Re-run this module to reproduce them.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import replace
from pathlib import Path

import pandas as pd

from backend.bandit import EpsilonGreedyBandit
from backend.data_logger import DataLogger
from backend.fixed_difficulty import FixedDifficulty
from backend.game_config import GameConfig
from backend.game_engine import GameEngine, SessionResult
from backend.rule_based_dda import RuleBasedDDA


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def build_rule_agent(config: GameConfig) -> RuleBasedDDA:
    return RuleBasedDDA(
        initial=config.rule_initial_difficulty,
        check_interval=config.rule_check_interval,
        min_ticks_between_changes=config.rule_min_ticks_between_changes,
        low_health=config.rule_low_health,
        high_health=config.rule_high_health,
        recent_damage_limit=config.rule_recent_damage_limit,
        recent_damage_health_ceiling=config.rule_recent_damage_health_ceiling,
        good_performance=config.rule_good_performance,
        min_survival_before_increase=config.rule_min_survival_before_increase,
    )


def run_session(agent, config: GameConfig, seed: int, session_id: str | None = None) -> SessionResult:
    engine = GameEngine(config, agent, seed=seed, session_id=session_id)
    return engine.run()


def run_fixed_block(config: GameConfig, sessions: int, logger: DataLogger) -> list[SessionResult]:
    results = []
    for level in ("easy", "medium", "hard"):
        for index in range(sessions):
            agent = FixedDifficulty(level)
            result = run_session(agent, config, seed=1000 + index)
            logger.log_session(result)
            results.append(result)
    return results


def run_rule_block(config: GameConfig, sessions: int, logger: DataLogger) -> list[SessionResult]:
    results = []
    for index in range(sessions):
        agent = build_rule_agent(config)
        result = run_session(agent, config, seed=2000 + index)
        logger.log_session(result)
        results.append(result)
    return results


def run_bandit_block(config: GameConfig, sessions: int, logger: DataLogger) -> list[SessionResult]:
    # One bandit object is reused so the estimates accumulate across sessions.
    bandit = EpsilonGreedyBandit(
        epsilon=config.bandit_epsilon,
        check_interval=config.bandit_check_interval,
        seed=0,
    )
    results = []
    for index in range(sessions):
        result = run_session(bandit, config, seed=3000 + index)
        logger.log_session(result)
        results.append(result)
    return results


def summarise(results: list[SessionResult]) -> dict:
    if not results:
        return {}
    by_mode: dict[str, list[SessionResult]] = {}
    for result in results:
        by_mode.setdefault(result.experimental_mode, []).append(result)
    summary = {}
    for mode, group in by_mode.items():
        n = len(group)
        summary[mode] = {
            "n": n,
            "survival_time": sum(r.survival_time for r in group) / n,
            "final_score": sum(r.final_score for r in group) / n,
            "remaining_health": sum(r.remaining_health for r in group) / n,
            "enemies_defeated": sum(r.enemies_defeated for r in group) / n,
            "difficulty_changes": sum(r.difficulty_changes for r in group) / n,
            "reward": sum(r.reward for r in group) / n,
        }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the fixed / rule / bandit comparison")
    parser.add_argument("--sessions", type=int, default=24, help="Sessions per mode")
    parser.add_argument("--fresh", action="store_true", help="Replace the CSV files")
    args = parser.parse_args()

    config = GameConfig()
    data_dir = PROJECT_ROOT / "data"
    sessions_path = data_dir / "sessions.csv"
    decisions_path = data_dir / "decisions.csv"
    logger = DataLogger(sessions_path, decisions_path)
    if args.fresh:
        logger.reset()

    print(f"Running {args.sessions} sessions per mode")
    fixed = run_fixed_block(config, args.sessions, logger)
    rules = run_rule_block(config, args.sessions, logger)
    bandit = run_bandit_block(config, args.sessions, logger)
    all_results = fixed + rules + bandit

    summary = summarise(all_results)
    summary_path = data_dir / "experiment_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print()
    print("Summary written to", summary_path)
    for mode, stats in summary.items():
        print(
            f"  {mode:12}  n={stats['n']:3}  "
            f"survival={stats['survival_time']:5.1f}s  "
            f"score={stats['final_score']:6.1f}  "
            f"reward={stats['reward']:.3f}"
        )


if __name__ == "__main__":
    main()
