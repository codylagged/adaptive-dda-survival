"""End-of-round screen. Every figure is taken from the SessionResult."""

from __future__ import annotations

import pygame

from frontend.settings import COLOR_ACCENT, COLOR_MUTED, COLOR_TEXT, MODE_LABELS, difficulty_color
from frontend.ui import Button, button_at, draw_backdrop, draw_panel, draw_text


def _path(trace: list[str]) -> str:
    if not trace:
        return ""
    collapsed = [trace[0]]
    for level in trace[1:]:
        if level != collapsed[-1]:
            collapsed.append(level)
    return " -> ".join(collapsed)


class GameOverScreen:
    def __init__(self, app) -> None:
        self.app = app
        self.buttons: list[Button] = []

    def enter(self) -> None:
        self.buttons = [
            Button((250, 680, 230, 56), "Play Again", "again"),
            Button((520, 680, 230, 56), "Main Menu", "menu"),
            Button((790, 680, 240, 56), "View Results", "results"),
        ]

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.go("menu")
            return
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        hit = button_at(self.buttons, event.pos)
        if hit is None:
            return
        if hit.key == "again":
            self.app.go("play")
        elif hit.key == "menu":
            self.app.go("menu")
        else:
            self.app.open_results("game_over")

    def update(self, dt: float) -> None:
        del dt

    def draw(self, surface: pygame.Surface) -> None:
        fonts = self.app.fonts
        draw_backdrop(surface)
        result = self.app.last_result
        card = pygame.Rect(180, 70, 920, 580)
        draw_panel(surface, card)
        if result is None:
            draw_text(surface, "No finished round to show.", fonts["heading"], COLOR_TEXT, (220, 120))
        else:
            self._draw_result(surface, fonts, result)
        for button in self.buttons:
            button.draw(surface, fonts["button"])

    def _draw_result(self, surface, fonts, result) -> None:
        if result.game_over_reason == "health_depleted":
            title = "Defeated"
            subtitle = "Health reached 0."
        elif result.game_over_reason == "time_limit":
            title = "Time limit reached"
            subtitle = "You lasted until the round ended."
        else:
            title = "Round over"
            subtitle = result.game_over_reason or "The backend ended the session."
        draw_text(surface, title, fonts["title"], COLOR_TEXT, (220, 100))
        draw_text(surface, subtitle, fonts["body"], COLOR_MUTED, (224, 168))

        mode = MODE_LABELS.get(result.experimental_mode, result.experimental_mode)
        rows = [
            ("Mode", mode),
            ("Final difficulty", result.selected_difficulty),
            ("Started at", result.initial_difficulty),
            ("Score", str(result.final_score)),
            ("Survival time", f"{result.survival_time:.1f} s"),
            ("Remaining health", f"{result.remaining_health:.1f}"),
            ("Enemies defeated", str(result.enemies_defeated)),
            ("Difficulty changes", str(result.difficulty_changes)),
            ("Session reward", f"{result.reward:.3f}"),
        ]
        y = 220
        for label, value in rows:
            draw_text(surface, label, fonts["body"], COLOR_MUTED, (230, y))
            color = difficulty_color(value) if value in ("easy", "medium", "hard") else COLOR_TEXT
            draw_text(surface, value, fonts["body"], color, (520, y))
            y += 36
        path = _path(result.difficulty_trace)
        if path:
            draw_text(surface, "Path  " + path, fonts["small"], COLOR_ACCENT, (230, y + 4))
        note = self.app.log_note or ""
        if note:
            draw_text(surface, note, fonts["tiny"], COLOR_MUTED, (230, 620))
