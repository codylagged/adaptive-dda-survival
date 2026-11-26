"""Connect a menu choice to the existing backend controllers.

Nothing in this module reimplements a difficulty rule or a bandit update.
It constructs the same objects the experiment runner uses, then turns on
``manual_control`` so the window can supply movement and attack.
"""

from __future__ import annotations

import secrets
import uuid
from dataclasses import replace

from backend.bandit import EpsilonGreedyBandit
from backend.data_logger import DataLogger
from backend.fixed_difficulty import FixedDifficulty
from backend.game_config import DIFFICULTY_ORDER, GameConfig
from backend.game_engine import GameEngine, SessionResult
from backend.rule_based_dda import RuleBasedDDA
from frontend.settings import INTERACTIVE_LIMIT_SECONDS, MODE_ORDER


def _rule_agent(config: GameConfig) -> RuleBasedDDA:
    """Same arguments as experiments.run_experiments.build_rule_agent.

    That module imports pandas, so the window does not import it.
    """
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


def interactive_config() -> GameConfig:
    """Backend config for a human round.

    Enemy presets, rule thresholds, epsilon, and the reward weights stay
    on the ``GameConfig`` defaults. Only the time limit is longer, so a
    person can see more than one adaptation. The batch runner still builds
    its own ``GameConfig()`` and keeps the 20-second horizon.
    """
    base = GameConfig()
    ticks = int(round(INTERACTIVE_LIMIT_SECONDS / base.seconds_per_tick))
    return replace(base, max_ticks=ticks)


def start_play_session(
    mode: str,
    level: str,
    bandit: EpsilonGreedyBandit | None = None,
    seed: int | None = None,
    session_id: str | None = None,
) -> tuple[GameEngine, EpsilonGreedyBandit | None]:
    """Create a manual session and return the engine plus the bandit to keep.

    The bandit object is reused across rounds because its Q values are the
    memory of the algorithm. A new ``FixedDifficulty`` or ``RuleBasedDDA``
    is created per round, which is also what the batch runner does.
    The returned bandit is the one the caller should store. It is unchanged
    when the mode is not the bandit.
    """
    if mode not in MODE_ORDER:
        raise ValueError(f"Unknown mode '{mode}'. Choose from {MODE_ORDER}.")
    if mode != "bandit" and level not in DIFFICULTY_ORDER:
        raise ValueError(f"Unknown difficulty '{level}'. Choose from {DIFFICULTY_ORDER}.")

    config = interactive_config()
    if mode == "fixed":
        agent = FixedDifficulty(level)
    elif mode == "rule_based":
        # Same constructor arguments as the experiment runner.
        config = replace(config, rule_initial_difficulty=level)
        agent = _rule_agent(config)
        if not isinstance(agent, RuleBasedDDA):
            raise TypeError("build_rule_agent did not return RuleBasedDDA")
    else:
        if bandit is None:
            bandit = EpsilonGreedyBandit(
                epsilon=config.bandit_epsilon,
                check_interval=config.bandit_check_interval,
                seed=secrets.randbits(32) if seed is None else seed,
            )
        agent = bandit

    if seed is None:
        seed = secrets.randbelow(1_000_000_000)
    if session_id is None:
        session_id = f"interactive-{mode}-{uuid.uuid4().hex[:8]}"

    engine = GameEngine(config, agent, seed=seed, session_id=session_id)
    engine.manual_control = True
    return engine, bandit


def log_finished_session(result: SessionResult, sessions_path, decisions_path) -> None:
    """Append one completed ``SessionResult`` using the backend logger.

    Call this only after ``GameEngine.finish()``. An abandoned round has
    no result and must not be written.
    """
    DataLogger(sessions_path, decisions_path).log_session(result)
