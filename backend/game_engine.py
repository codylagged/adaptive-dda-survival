"""Tick-based survival simulation.

No window and no sprites are required. Call `run()` for a full session, or
`step()` from a future Pygame loop:

    snapshot = engine.render_snapshot()
    # draw snapshot["player"] and snapshot["enemies"]
    engine.set_external_action({"move_x": 1, "move_y": 0, "attack": True})
    engine.step()

The default player is a scripted survivor that stands in the centre and
attacks the nearest enemy in range. Set `manual_control` to hand movement
and attacks to a frontend.

Tick order
----------
1. Optional manual movement.
2. Spawn, if the interval has elapsed and the arena is not full.
3. Enemies step toward the player and stop at attack range.
4. Enemies in range deal damage when their cooldown is ready.
5. The player attacks, if the scripted policy or the external action says so.
6. Defeat, score, and game-over checks.
7. If the controller adapts and this tick is a decision tick, it may switch
   difficulty. The tick that just happened was played at the old difficulty.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
import random
import uuid

from backend.enemy import Enemy
from backend.game_config import (
    DIFFICULTY_PRESETS,
    AgentDecision,
    DifficultyParams,
    GameConfig,
    PerformanceMetrics,
)
from backend.player import Player
from backend.reward_system import RewardObservation, compute_reward


@dataclass
class DecisionRecord:
    tick: int
    previous_difficulty: str
    selected_difficulty: str
    changed: bool
    reason: str
    policy_detail: str
    health_ratio: float
    recent_damage: float
    survival_time: float
    performance: float
    estimated_reward: float | None
    observed_reward: float | None


@dataclass
class SessionResult:
    session_id: str
    experimental_mode: str
    selected_difficulty: str
    initial_difficulty: str
    dominant_difficulty: str
    survival_time: float
    final_score: int
    remaining_health: float
    enemies_defeated: int
    difficulty_changes: int
    reward: float
    timestamp: str
    game_over_reason: str
    seed: int
    ticks: int
    max_health: float
    difficulty_trace: list[str] = field(default_factory=list)
    decisions: list[DecisionRecord] = field(default_factory=list)


class GameEngine:
    def __init__(
        self,
        config: GameConfig,
        agent,
        seed: int = 0,
        session_id: str | None = None,
        presets: dict[str, DifficultyParams] | None = None,
    ) -> None:
        self.config = config
        self.agent = agent
        self.seed = int(seed)
        # Python's random generator, not NumPy. The spawn rule is unchanged:
        # one of the four edges, then a point along the middle of that edge.
        self.rng = random.Random(self.seed)
        self.presets = presets or DIFFICULTY_PRESETS
        self.session_id = session_id or f"{agent.mode_name}-{uuid.uuid4().hex[:12]}"
        self.tick = 0
        self.game_over = False
        self.game_over_reason = ""
        self.manual_control = False
        self.external_action: dict | None = None
        self.player = Player(
            max_health=config.player_max_health,
            attack_damage=config.player_attack_damage,
            attack_range=config.player_attack_range,
            attack_cooldown=config.player_attack_cooldown,
            x=config.width / 2.0,
            y=config.height / 2.0,
        )
        self.enemies: list[Enemy] = []
        self._next_enemy_id = 1
        self.difficulty_changes = 0
        self.difficulty_trace: list[str] = []
        self.decisions: list[DecisionRecord] = []
        self.window_start_tick = 0
        self.window_start_score = 0
        self.window_start_kills = 0
        self._finished = False

        opening = agent.start_session()
        self._require_known_difficulty(opening.difficulty)
        self.difficulty = opening.difficulty
        self.initial_difficulty = opening.difficulty
        self._record_decision(opening, previous=opening.difficulty, observed_reward=None, changed=False)

    def set_external_action(self, action: dict | None) -> None:
        """Store the next manual action. Ignored unless manual_control is True."""
        self.external_action = action

    def run(self) -> SessionResult:
        while not self.game_over:
            self.step()
        return self.finish()

    def step(self) -> bool:
        """Advance one tick. Returns True while the session is still going."""
        if self.game_over:
            return False
        self.tick += 1
        self._apply_manual_movement()
        self._spawn_enemies()
        self._move_enemies()
        self._enemy_attacks()
        self._player_attack()
        self._remove_defeated()
        self._add_survival_score()
        self.player.survival_ticks = self.tick
        self._check_game_over()
        self.difficulty_trace.append(self.difficulty)
        if (
            not self.game_over
            and getattr(self.agent, "adapts", False)
            and self.tick % self.agent.check_interval == 0
        ):
            self._adapt()
        return not self.game_over

    def finish(self) -> SessionResult:
        if not self.game_over:
            raise RuntimeError("finish() requires the session to be over")
        if not self._finished:
            # The reward belongs to the difficulty that was just played,
            # which is the most recent decision, not a new one.
            observed = self._observe_active_difficulty()
            if self.decisions:
                self.decisions[-1].observed_reward = observed
            self._finished = True
        return self._build_result()

    def metrics(self) -> PerformanceMetrics:
        seconds = self.tick * self.config.seconds_per_tick
        performance = self.player.enemies_defeated / seconds if seconds > 0 else 0.0
        return PerformanceMetrics(
            tick=self.tick,
            health_ratio=self.player.health_ratio,
            recent_damage=self.player.recent_damage(self.tick, self.config.recent_damage_window),
            survival_time=seconds,
            performance=performance,
            current_difficulty=self.difficulty,
            remaining_health=self.player.health,
            max_health=self.player.max_health,
            score=float(self.player.score),
            enemies_defeated=self.player.enemies_defeated,
        )

    def render_snapshot(self) -> dict:
        """State a Pygame frontend can draw without importing the simulation."""
        return {
            "tick": self.tick,
            "game_over": self.game_over,
            "game_over_reason": self.game_over_reason,
            "difficulty": self.difficulty,
            "width": self.config.width,
            "height": self.config.height,
            "player": {
                "x": self.player.x,
                "y": self.player.y,
                "health": self.player.health,
                "max_health": self.player.max_health,
                "score": self.player.score,
                "enemies_defeated": self.player.enemies_defeated,
            },
            "enemies": [
                {
                    "id": enemy.id,
                    "x": enemy.x,
                    "y": enemy.y,
                    "health": enemy.health,
                    "max_health": enemy.max_health,
                }
                for enemy in self.enemies
            ],
        }

    def spawn_enemy(self, x: float, y: float, health: float | None = None) -> Enemy:
        """Place an enemy directly. Tests and a future debug overlay use this."""
        params = self._params()
        enemy = Enemy(
            enemy_id=self._next_enemy_id,
            x=x,
            y=y,
            health=params.enemy_health if health is None else health,
            speed=params.enemy_speed,
            damage=params.enemy_damage,
            attack_range=params.enemy_attack_range,
            attack_cooldown=params.enemy_attack_cooldown,
        )
        self._next_enemy_id += 1
        self.enemies.append(enemy)
        return enemy

    def _adapt(self) -> None:
        observed = self._observe_active_difficulty()
        if self.decisions:
            self.decisions[-1].observed_reward = observed
        decision = self.agent.decide(self.metrics())
        self._apply_decision(decision)

    def _observe_active_difficulty(self) -> float:
        lived_ticks = max(self.tick - self.window_start_tick, 0)
        observation = RewardObservation(
            survival_time=lived_ticks * self.config.seconds_per_tick,
            remaining_health=self.player.health,
            max_health=self.player.max_health,
            score=self.player.score - self.window_start_score,
            enemies_defeated=self.player.enemies_defeated - self.window_start_kills,
            died=self.player.health <= 0,
        )
        scheduled = max(getattr(self.agent, "check_interval", 1), 1) * self.config.seconds_per_tick
        reward = compute_reward(observation, self.config.reward, survival_target=scheduled)
        if getattr(self.agent, "learns_from_reward", False):
            self.agent.update(self.difficulty, reward)
        self.window_start_tick = self.tick
        self.window_start_score = self.player.score
        self.window_start_kills = self.player.enemies_defeated
        return reward

    def _apply_decision(self, decision: AgentDecision) -> None:
        self._require_known_difficulty(decision.difficulty)
        previous = self.difficulty
        changed = decision.difficulty != previous
        if changed:
            self.difficulty_changes += 1
            self._set_difficulty(decision.difficulty)
        self._record_decision(decision, previous=previous, observed_reward=None, changed=changed)

    def _record_decision(
        self,
        decision: AgentDecision,
        previous: str,
        observed_reward: float | None,
        changed: bool | None = None,
    ) -> None:
        snapshot = self.metrics()
        self.decisions.append(
            DecisionRecord(
                tick=self.tick,
                previous_difficulty=previous,
                selected_difficulty=decision.difficulty,
                changed=decision.changed if changed is None else changed,
                reason=decision.reason,
                policy_detail=decision.policy_detail,
                health_ratio=snapshot.health_ratio,
                recent_damage=snapshot.recent_damage,
                survival_time=snapshot.survival_time,
                performance=snapshot.performance,
                estimated_reward=decision.estimated_reward,
                observed_reward=observed_reward,
            )
        )

    def _set_difficulty(self, name: str) -> None:
        self.difficulty = name
        params = self._params()
        for enemy in self.enemies:
            enemy.apply_preset_stats(
                speed=params.enemy_speed,
                damage=params.enemy_damage,
                attack_range=params.enemy_attack_range,
                attack_cooldown=params.enemy_attack_cooldown,
            )

    def _params(self) -> DifficultyParams:
        try:
            return self.presets[self.difficulty]
        except KeyError as exc:
            raise KeyError(f"No preset configured for '{self.difficulty}'") from exc

    def _require_known_difficulty(self, name: str) -> None:
        if name not in self.presets:
            raise KeyError(f"No preset configured for '{name}'")

    def _apply_manual_movement(self) -> None:
        if not self.manual_control:
            return
        action = self.external_action or {}
        dx = float(action.get("move_x", 0.0))
        dy = float(action.get("move_y", 0.0))
        self.player.x = min(max(self.player.x + dx * self.config.player_speed, 0.0), self.config.width)
        self.player.y = min(max(self.player.y + dy * self.config.player_speed, 0.0), self.config.height)

    def _spawn_enemies(self) -> None:
        params = self._params()
        if params.spawn_interval < 1:
            return
        if self.tick % params.spawn_interval != 0:
            return
        if len(self.enemies) >= self.config.max_enemies:
            return
        x, y = self._perimeter_point()
        self.spawn_enemy(x, y)

    def _perimeter_point(self) -> tuple[float, float]:
        edge = self.rng.randrange(0, 4)
        along = 0.35 + 0.30 * self.rng.random()
        if edge == 0:
            return along * self.config.width, 0.0
        if edge == 1:
            return self.config.width, along * self.config.height
        if edge == 2:
            return along * self.config.width, self.config.height
        return 0.0, along * self.config.height

    def _move_enemies(self) -> None:
        for enemy in self.enemies:
            enemy.move_toward(self.player.x, self.player.y)

    def _enemy_attacks(self) -> None:
        for enemy in self.enemies:
            in_range = enemy.distance_to(self.player.x, self.player.y) <= enemy.attack_range + 1e-6
            if in_range and enemy.cooldown_left <= 0:
                self.player.take_damage(enemy.damage, self.tick)
                enemy.cooldown_left = enemy.attack_cooldown
            elif enemy.cooldown_left > 0:
                enemy.cooldown_left -= 1

    def _player_attack(self) -> None:
        wants_attack = True
        if self.manual_control:
            wants_attack = bool((self.external_action or {}).get("attack", False))
        if self.player.attack_cooldown_left > 0:
            self.player.attack_cooldown_left -= 1
            return
        if not wants_attack:
            return
        target = self._nearest_enemy_within(self.player.attack_range)
        if target is None:
            return
        target.health -= self.player.attack_damage
        self.player.attack_cooldown_left = self.player.attack_cooldown

    def _nearest_enemy_within(self, reach: float) -> Enemy | None:
        best: Enemy | None = None
        best_distance = reach + 1e-6
        for enemy in self.enemies:
            distance = enemy.distance_to(self.player.x, self.player.y)
            if distance <= best_distance:
                best = enemy
                best_distance = distance
        return best

    def _remove_defeated(self) -> None:
        params = self._params()
        alive: list[Enemy] = []
        for enemy in self.enemies:
            if enemy.health <= 0:
                points = int(round(self.config.kill_score * params.score_multiplier))
                self.player.register_defeat(points)
            else:
                alive.append(enemy)
        self.enemies = alive

    def _add_survival_score(self) -> None:
        interval = self.config.survival_score_interval
        if interval > 0 and self.tick % interval == 0 and self.player.alive:
            self.player.add_score(self.config.survival_score_amount)

    def _check_game_over(self) -> None:
        if self.player.health <= 0:
            self.player.health = 0.0
            self.game_over = True
            self.game_over_reason = "health_depleted"
        elif self.tick >= self.config.max_ticks:
            self.game_over = True
            self.game_over_reason = "time_limit"

    def _build_result(self) -> SessionResult:
        horizon = self.config.max_ticks * self.config.seconds_per_tick
        observation = RewardObservation(
            survival_time=self.tick * self.config.seconds_per_tick,
            remaining_health=self.player.health,
            max_health=self.player.max_health,
            score=float(self.player.score),
            enemies_defeated=self.player.enemies_defeated,
            died=self.player.health <= 0 or self.game_over_reason == "health_depleted",
        )
        reward = compute_reward(observation, self.config.reward, survival_target=horizon)
        trace = self.difficulty_trace or [self.difficulty]
        dominant = Counter(trace).most_common(1)[0][0]
        return SessionResult(
            session_id=self.session_id,
            experimental_mode=self.agent.mode_name,
            selected_difficulty=self.difficulty,
            initial_difficulty=self.initial_difficulty,
            dominant_difficulty=dominant,
            survival_time=self.tick * self.config.seconds_per_tick,
            final_score=self.player.score,
            remaining_health=self.player.health,
            enemies_defeated=self.player.enemies_defeated,
            difficulty_changes=self.difficulty_changes,
            reward=reward,
            timestamp=datetime.now().isoformat(timespec="seconds"),
            game_over_reason=self.game_over_reason,
            seed=self.seed,
            ticks=self.tick,
            max_health=self.player.max_health,
            difficulty_trace=list(self.difficulty_trace),
            decisions=list(self.decisions),
        )
