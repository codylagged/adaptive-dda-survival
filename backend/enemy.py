"""Enemy movement and attack timing.

Enemies walk toward the player and stop at attack range. They do not
render themselves; the engine snapshot exposes position and health.
"""

from __future__ import annotations

import math


class Enemy:
    def __init__(
        self,
        enemy_id: int,
        x: float,
        y: float,
        health: float,
        speed: float,
        damage: float,
        attack_range: float,
        attack_cooldown: int,
    ) -> None:
        if health <= 0:
            raise ValueError("enemy health must be positive")
        self.id = int(enemy_id)
        self.x = float(x)
        self.y = float(y)
        self.health = float(health)
        self.max_health = float(health)
        self.speed = float(speed)
        self.damage = float(damage)
        self.attack_range = float(attack_range)
        self.attack_cooldown = int(attack_cooldown)
        self.cooldown_left = 0

    def distance_to(self, x: float, y: float) -> float:
        return math.hypot(self.x - x, self.y - y)

    def move_toward(self, x: float, y: float) -> float:
        """Step toward (x, y) by at most `speed`, stopping at attack range.

        Returns the distance that remains after the step.
        """
        dx = x - self.x
        dy = y - self.y
        distance = math.hypot(dx, dy)
        if distance == 0.0 or distance <= self.attack_range:
            return distance
        step = min(self.speed, distance - self.attack_range)
        if step <= 0:
            return distance
        self.x += dx / distance * step
        self.y += dy / distance * step
        return distance - step

    def apply_preset_stats(self, speed: float, damage: float, attack_range: float, attack_cooldown: int) -> None:
        """Update live enemies when difficulty changes.

        Current health and the cooldown already counting down are left alone,
        so a difficulty switch does not heal or instantly re-arm an enemy.
        """
        self.speed = float(speed)
        self.damage = float(damage)
        self.attack_range = float(attack_range)
        self.attack_cooldown = int(attack_cooldown)
