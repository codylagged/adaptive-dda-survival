"""Shared configuration, difficulty presets, and decision records.

A future Pygame frontend should read these presets instead of hard-coding
speeds or damage. Changing a number here changes every mode in the same way.
"""

from __future__ import annotations

from dataclasses import dataclass


DIFFICULTY_ORDER = ("easy", "medium", "hard")


@dataclass(frozen=True)
class DifficultyParams:
    """Combat parameters controlled by the active difficulty label.

    enemy_speed: pixels moved toward the player each tick.
    spawn_interval: ticks between spawn attempts.
    enemy_damage: health removed on each successful enemy hit.
    """

    name: str
    enemy_speed: float
    spawn_interval: int
    enemy_damage: float
    enemy_health: float
    enemy_attack_range: float
    enemy_attack_cooldown: int
    score_multiplier: float


# Calibrated for the stationary scripted survivor in game_engine.py.
# Easy enemies are slow and weak. Hard enemies are faster, tougher, and hit harder.
# The gap is intentional so a fixed-difficulty comparison has something to measure.
DIFFICULTY_PRESETS: dict[str, DifficultyParams] = {
    "easy": DifficultyParams(
        name="easy",
        enemy_speed=1.9,
        spawn_interval=28,
        enemy_damage=4.0,
        enemy_health=18.0,
        enemy_attack_range=22.0,
        enemy_attack_cooldown=16,
        score_multiplier=1.0,
    ),
    "medium": DifficultyParams(
        name="medium",
        enemy_speed=2.6,
        spawn_interval=18,
        enemy_damage=8.0,
        enemy_health=30.0,
        enemy_attack_range=24.0,
        enemy_attack_cooldown=11,
        score_multiplier=1.5,
    ),
    "hard": DifficultyParams(
        name="hard",
        enemy_speed=3.6,
        spawn_interval=11,
        enemy_damage=13.0,
        enemy_health=44.0,
        enemy_attack_range=26.0,
        enemy_attack_cooldown=7,
        score_multiplier=2.0,
    ),
}


@dataclass(frozen=True)
class RewardWeights:
    """Coefficients for reward_system.compute_reward.

    Positive weights sum to 1. The death penalty is subtracted separately.
    See reward_system.py for why each term exists.
    """

    survival: float = 0.25
    health: float = 0.15
    score: float = 0.20
    kills: float = 0.15
    challenge: float = 0.25
    target_survival_seconds: float = 20.0
    score_scale: float = 80.0
    kill_scale: float = 8.0
    target_pressure: float = 0.40
    pressure_tolerance: float = 0.50
    death_penalty: float = 0.20


@dataclass(frozen=True)
class GameConfig:
    """World, player, and default controller settings."""

    width: float = 240.0
    height: float = 240.0
    seconds_per_tick: float = 0.1
    max_ticks: int = 200
    max_enemies: int = 6
    recent_damage_window: int = 30

    player_max_health: float = 100.0
    player_attack_damage: float = 8.0
    player_attack_range: float = 30.0
    player_attack_cooldown: int = 5
    player_speed: float = 8.0

    kill_score: int = 10
    survival_score_interval: int = 10
    survival_score_amount: int = 1

    reward: RewardWeights = RewardWeights()

    rule_check_interval: int = 20
    rule_min_ticks_between_changes: int = 40
    rule_low_health: float = 0.30
    rule_high_health: float = 0.70
    rule_recent_damage_limit: float = 18.0
    rule_recent_damage_health_ceiling: float = 0.60
    rule_good_performance: float = 0.20
    rule_min_survival_before_increase: float = 4.0
    rule_initial_difficulty: str = "medium"

    bandit_epsilon: float = 0.10
    bandit_check_interval: int = 40

    def __post_init__(self) -> None:
        if self.max_ticks < 1:
            raise ValueError("max_ticks must be at least 1")
        if self.seconds_per_tick <= 0:
            raise ValueError("seconds_per_tick must be positive")
        if not 0.0 <= self.bandit_epsilon <= 1.0:
            raise ValueError("bandit_epsilon must be between 0 and 1")


@dataclass
class PerformanceMetrics:
    """Snapshot the controllers read. The engine fills this every decision."""

    tick: int
    health_ratio: float
    recent_damage: float
    survival_time: float
    performance: float
    current_difficulty: str
    remaining_health: float
    max_health: float
    score: float
    enemies_defeated: int


@dataclass
class AgentDecision:
    """One difficulty choice made by a controller."""

    difficulty: str
    reason: str
    policy_detail: str
    estimated_reward: float | None = None
    changed: bool = False
