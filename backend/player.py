"""Player state: health, score, survival, and recent damage.

The class does not draw anything. A Pygame frontend can read `x`, `y`,
`health`, and `score` from the engine snapshot.
"""

from __future__ import annotations


class Player:
    def __init__(
        self,
        max_health: float,
        attack_damage: float,
        attack_range: float,
        attack_cooldown: int,
        x: float,
        y: float,
    ) -> None:
        if max_health <= 0:
            raise ValueError("max_health must be positive")
        self.max_health = float(max_health)
        self.health = float(max_health)
        self.attack_damage = float(attack_damage)
        self.attack_range = float(attack_range)
        self.attack_cooldown = int(attack_cooldown)
        self.attack_cooldown_left = 0
        self.x = float(x)
        self.y = float(y)
        self.score = 0
        self.enemies_defeated = 0
        self.survival_ticks = 0
        self._damage_events: list[tuple[int, float]] = []

    @property
    def health_ratio(self) -> float:
        if self.max_health <= 0:
            return 0.0
        return self.health / self.max_health

    @property
    def alive(self) -> bool:
        return self.health > 0

    def take_damage(self, amount: float, tick: int) -> float:
        """Apply damage and record it. Health never drops below zero.

        Returns the amount actually applied (so overkill is visible in tests).
        """
        amount = max(0.0, float(amount))
        applied = min(self.health, amount)
        self.health -= applied
        if applied > 0:
            self._damage_events.append((int(tick), applied))
        return applied

    def recent_damage(self, tick: int, window: int) -> float:
        """Sum of damage taken in (tick - window, tick]."""
        if window < 0:
            raise ValueError("window must be non-negative")
        lower = int(tick) - int(window)
        return float(sum(amount for event_tick, amount in self._damage_events if lower < event_tick <= tick))

    def add_score(self, points: int) -> None:
        self.score += int(points)
        if self.score < 0:
            self.score = 0

    def register_defeat(self, points: int) -> None:
        self.enemies_defeated += 1
        self.add_score(points)
