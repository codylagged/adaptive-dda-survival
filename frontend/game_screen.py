"""The playable match. Input goes in. The backend advances the world.

This screen does not move enemies, apply damage, or choose a difficulty.
``GameEngine.step`` does that, and the drawing uses ``render_snapshot``
plus the preset that belongs to ``engine.difficulty``.
"""

from __future__ import annotations

import pygame

from backend.bandit import EpsilonGreedyBandit
from backend.game_config import DIFFICULTY_PRESETS
from frontend.controls import action_from_keyboard, idle_action
from frontend.session import log_finished_session, start_play_session
from frontend.settings import (
    ARENA_X,
    ARENA_Y,
    COLOR_ACCENT,
    COLOR_HEALTH,
    COLOR_HEALTH_BG,
    COLOR_HEALTH_LOW,
    COLOR_MUTED,
    COLOR_TEXT,
    MODE_LABELS,
    SCALE,
    difficulty_color,
)
from frontend.sprites import scaled
from frontend.ui import Button, draw_backdrop, draw_panel, draw_text, wrap_text


# Short explanations of the reason codes written into decisions.csv.
REASON_TEXT = {
    "fixed_preset": "Opening preset. This mode will keep it.",
    "fixed_difficulty": "FixedDifficulty returned the original level.",
    "initial_difficulty": "Opening level for the rule set.",
    "cooldown": "A change happened recently, so the level is held.",
    "health_below_threshold": "Health is under 30%, so the level steps down.",
    "recent_damage_high": "Recent damage is high and health is under 60%.",
    "strong_performance": "Health, survival time, and kill rate are all high.",
    "stable": "No rule matched, so the level stays.",
    "already_at_minimum": "The rules asked to step down, but the level is already easy.",
    "already_at_maximum": "The rules asked to step up, but the level is already hard.",
    "explore": "Epsilon-greedy drew a level at random.",
    "exploit": "Epsilon-greedy took a level with the best estimate.",
}


def _lerp(start: float, end: float, amount: float) -> float:
    return start + (end - start) * amount


class GameScreen:
    def __init__(self, app) -> None:
        self.app = app
        self.engine = None
        self.action = idle_action()
        self.read_keyboard = True
        self.paused = False
        self.completed = False
        self.accumulator = 0.0
        self.prev_player = (0.0, 0.0)
        self.prev_health = 0.0
        self.prev_enemies: dict[int, tuple[float, float]] = {}
        self.seen_decisions = 0
        self.toast = ""
        self.toast_time = 0.0
        self.hurt = 0.0
        self.swing = 0.0
        self.resume_button = Button((390, 390, 220, 52), "Resume", "resume")
        self.menu_button = Button((640, 390, 240, 52), "Main menu", "menu")

    def enter(self) -> None:
        selection = self.app.selection
        engine, bandit = start_play_session(
            selection["mode"],
            selection["level"],
            bandit=self.app.bandit,
        )
        self.app.bandit = bandit
        self.engine = engine
        self.action = idle_action()
        self.paused = False
        self.completed = False
        self.accumulator = 0.0
        self.toast = ""
        self.toast_time = 0.0
        self.hurt = 0.0
        self.swing = 0.0
        self.seen_decisions = len(engine.decisions)
        self._capture_prev()

    def _capture_prev(self) -> None:
        player = self.engine.player
        self.prev_player = (player.x, player.y)
        self.prev_health = player.health
        self.prev_enemies = {enemy.id: (enemy.x, enemy.y) for enemy in self.engine.enemies}

    def handle_event(self, event) -> None:
        if event.type != pygame.KEYDOWN and event.type != pygame.MOUSEBUTTONDOWN:
            return
        if self.completed or self.engine is None or self.engine.game_over:
            return
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_p, pygame.K_ESCAPE):
            self.paused = not self.paused
            if self.paused:
                self._capture_prev()
                self.accumulator = 0.0
            return
        if not self.paused or event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        if self.resume_button.contains(event.pos):
            self.paused = False
            self.accumulator = 0.0
            self._capture_prev()
        elif self.menu_button.contains(event.pos):
            # The engine is not finished, so this round is not logged.
            self.completed = True
            self.app.log_note = "Left before the round ended. Nothing was written to the CSV."
            self.app.go("menu")

    def update(self, dt: float) -> None:
        self.hurt = max(0.0, self.hurt - dt)
        self.swing = max(0.0, self.swing - dt)
        self.toast_time = max(0.0, self.toast_time - dt)
        if self.engine is None or self.paused or self.completed or self.engine.game_over:
            return
        if self.read_keyboard:
            self.action = action_from_keyboard()
        self.engine.set_external_action(self.action)
        self.accumulator += dt
        while self.accumulator >= self.engine.config.seconds_per_tick and not self.engine.game_over:
            self.accumulator -= self.engine.config.seconds_per_tick
            self._capture_prev()
            self.engine.step()
            self._check_toast()
            if self.engine.game_over:
                self._finish()
                break

    def _check_toast(self) -> None:
        if len(self.engine.decisions) > self.seen_decisions:
            decision = self.engine.decisions[-1]
            self.seen_decisions = len(self.engine.decisions)
            reason = REASON_TEXT.get(decision.reason, decision.reason)
            self.toast = f"{decision.selected_difficulty}: {reason}"
            self.toast_time = 3.5

    def _finish(self) -> None:
        if self.completed:
            return
        self.completed = True
        result = self.engine.finish()
        self.app.last_result = result
        try:
            log_finished_session(result, self.app.sessions_path, self.app.decisions_path)
            self.app.log_note = "Round written to the CSV."
        except Exception as exc:
            self.app.log_note = f"Could not write the CSV: {exc}"
        self.app.go("game_over")

    def draw(self, surface: pygame.Surface) -> None:
        fonts = self.app.fonts
        draw_backdrop(surface)
        if self.engine is None:
            draw_text(surface, "Starting...", fonts["heading"], COLOR_TEXT, (48, 40))
            return
        snapshot = self.engine.render_snapshot()
        self._draw_arena(surface, snapshot)
        self._draw_hud(surface, fonts, snapshot)
        if self.toast_time > 0 and self.toast:
            draw_text(surface, self.toast, fonts["small"], COLOR_ACCENT, (48, 780))
        if self.paused:
            self._draw_pause(surface, fonts)

    def _draw_arena(self, surface, snapshot) -> None:
        arena = pygame.Rect(ARENA_X, ARENA_Y, 240 * SCALE, 240 * SCALE)
        pygame.draw.rect(surface, (16, 22, 20), arena)
        # Player
        px = ARENA_X + int(snapshot["player"]["x"] * SCALE)
        py = ARENA_Y + int(snapshot["player"]["y"] * SCALE)
        pygame.draw.circle(surface, (126, 200, 196), (px, py), 12)
        # Enemies
        for enemy in snapshot["enemies"]:
            ex = ARENA_X + int(enemy["x"] * SCALE)
            ey = ARENA_Y + int(enemy["y"] * SCALE)
            pygame.draw.circle(surface, (176, 72, 68), (ex, ey), 10)
        pygame.draw.rect(surface, (62, 80, 74), arena, width=2)

    def _draw_hud(self, surface, fonts, snapshot) -> None:
        panel = pygame.Rect(800, 56, 440, 700)
        draw_panel(surface, panel)
        mode = MODE_LABELS.get(self.engine.agent.mode_name, self.engine.agent.mode_name)
        draw_text(surface, mode, fonts["heading"], COLOR_TEXT, (panel.x + 20, panel.y + 16))
        draw_text(
            surface,
            f"Difficulty: {snapshot['difficulty']}",
            fonts["body"],
            difficulty_color(snapshot["difficulty"]),
            (panel.x + 20, panel.y + 60),
        )
        health = snapshot["player"]["health"]
        max_health = snapshot["player"]["max_health"]
        draw_text(surface, f"Health {health:.0f} / {max_health:.0f}", fonts["body"], COLOR_TEXT, (panel.x + 20, panel.y + 100))
        bar = pygame.Rect(panel.x + 20, panel.y + 130, 400, 18)
        pygame.draw.rect(surface, COLOR_HEALTH_BG, bar, border_radius=4)
        if max_health > 0:
            filled = int(bar.width * (health / max_health))
            color = COLOR_HEALTH if health / max_health > 0.3 else COLOR_HEALTH_LOW
            pygame.draw.rect(surface, color, (bar.x, bar.y, filled, bar.height), border_radius=4)
        draw_text(surface, f"Score {snapshot['player']['score']}", fonts["body"], COLOR_TEXT, (panel.x + 20, panel.y + 170))
        draw_text(
            surface,
            f"Defeated {snapshot['player']['enemies_defeated']}",
            fonts["body"],
            COLOR_TEXT,
            (panel.x + 20, panel.y + 200),
        )
        draw_text(
            surface,
            f"Tick {snapshot['tick']}",
            fonts["small"],
            COLOR_MUTED,
            (panel.x + 20, panel.y + 240),
        )

    def _draw_pause(self, surface, fonts) -> None:
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        surface.blit(overlay, (0, 0))
        card = pygame.Rect(340, 260, 600, 280)
        draw_panel(surface, card)
        draw_text(surface, "Paused", fonts["heading"], COLOR_TEXT, card.centerx, center=True)
        note = fonts["small"].render("Leaving does not log this round.", True, COLOR_MUTED)
        surface.blit(note, note.get_rect(center=(card.centerx, card.y + 100)))
        self.resume_button.draw(surface, fonts["button"])
        self.menu_button.draw(surface, fonts["button"])
