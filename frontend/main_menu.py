"""Main menu, mode selection, and the instructions screen."""

from __future__ import annotations

import pygame

from frontend.settings import (
    COLOR_ACCENT,
    COLOR_MUTED,
    COLOR_TEXT,
    LEVELS,
    MODE_LABELS,
    WINDOW_WIDTH,
    describe_selection,
    difficulty_color,
)
from frontend.sprites import build_ground, scaled
from frontend.ui import Button, button_at, draw_backdrop, draw_panel, draw_text, wrap_text


INSTRUCTIONS = """
How to play
Move with W, A, S, D or the arrow keys. Hold Space to strike the nearest enemy inside your reach. P or Esc pauses the round. From the pause menu you can resume, or leave. Leaving does not write an unfinished round to the log.

The arena is the backend world of 240 by 240 units, drawn larger. Each tick is 0.1 seconds. Enemy speed, spawn interval, health, damage, and attack timing all come from the presets in backend/game_config.py. This window does not keep a second copy of those numbers.

Fixed difficulty
You pick easy, medium, or hard. FixedDifficulty returns that same label on every decision, so the preset never changes.

Rule-based dynamic difficulty adjustment
You pick a starting level. Every 20 ticks the rules look at health, recent damage, survival time, and kill rate. Low health or a damage spike steps the difficulty down one level. High health plus a good kill rate steps it up. A cooldown blocks another change for 40 ticks.

Epsilon-greedy bandit
The bandit has three arms: easy, medium, and hard. With probability 0.10 it explores by drawing an arm at random. Otherwise it picks the arm with the highest estimated reward. After each spell of difficulty it updates that estimate with the observed reward. The same bandit object is kept across rounds in this window so the estimates accumulate.

Results
Finished rounds are appended to data/sessions.csv. The statistics screen reads that file and keeps rows that start with interactive- separate from the batch experiment bars.
"""


class MainMenu:
    def __init__(self, app) -> None:
        self.app = app
        self.buttons: list[Button] = []

    def enter(self) -> None:
        self.buttons = [
            Button((440, 360, 400, 64), "Play", "play"),
            Button((440, 444, 400, 64), "Instructions", "instructions"),
            Button((440, 528, 400, 64), "Statistics", "results"),
            Button((440, 612, 400, 64), "Quit", "quit"),
        ]

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.running = False
            return
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        hit = button_at(self.buttons, event.pos)
        if hit is None:
            return
        if hit.key == "play":
            self.app.go("mode")
        elif hit.key == "instructions":
            self.app.go("instructions")
        elif hit.key == "results":
            self.app.open_results("menu")
        elif hit.key == "quit":
            self.app.running = False

    def update(self, dt: float) -> None:
        del dt

    def draw(self, surface: pygame.Surface) -> None:
        fonts = self.app.fonts
        draw_backdrop(surface)
        draw_text(surface, "Adaptive Survival", fonts["title"], COLOR_TEXT, (WINDOW_WIDTH // 2, 140), center=True)
        draw_text(
            surface,
            "Fixed, rule-based, and bandit difficulty in one arena",
            fonts["body"],
            COLOR_MUTED,
            (WINDOW_WIDTH // 2, 200),
            center=True,
        )
        selection = describe_selection(self.app.selection)
        draw_text(surface, selection, fonts["small"], COLOR_ACCENT, (WINDOW_WIDTH // 2, 280), center=True)
        for button in self.buttons:
            button.draw(surface, fonts["button"])


class ModeSelect:
    def __init__(self, app) -> None:
        self.app = app
        self.buttons: list[Button] = []

    def enter(self) -> None:
        self.buttons = [
            Button((180, 220, 280, 56), "Fixed", "fixed"),
            Button((500, 220, 280, 56), "Rule-based", "rule_based"),
            Button((820, 220, 280, 56), "Bandit", "bandit"),
            Button((180, 420, 200, 48), "Easy", "easy"),
            Button((420, 420, 200, 48), "Medium", "medium"),
            Button((660, 420, 200, 48), "Hard", "hard"),
            Button((180, 560, 280, 56), "Start", "start"),
            Button((500, 560, 280, 56), "Back", "back"),
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
        if hit.key in ("fixed", "rule_based", "bandit"):
            self.app.selection["mode"] = hit.key
        elif hit.key in LEVELS:
            self.app.selection["level"] = hit.key
        elif hit.key == "start":
            self.app.go("play")
        elif hit.key == "back":
            self.app.go("menu")

    def update(self, dt: float) -> None:
        del dt

    def draw(self, surface: pygame.Surface) -> None:
        fonts = self.app.fonts
        draw_backdrop(surface)
        draw_text(surface, "Choose a mode", fonts["heading"], COLOR_TEXT, (180, 80))
        draw_text(
            surface,
            "The bandit keeps its estimates across rounds. Fixed and rule-based start fresh.",
            fonts["small"],
            COLOR_MUTED,
            (180, 130),
        )
        mode = self.app.selection.get("mode", "fixed")
        level = self.app.selection.get("level", "medium")
        for button in self.buttons:
            active = (
                (button.key == mode)
                or (button.key == level and mode != "bandit")
            )
            button.draw(surface, fonts["button"], active=active)
        draw_text(
            surface,
            describe_selection(self.app.selection),
            fonts["body"],
            difficulty_color(level) if mode != "bandit" else COLOR_ACCENT,
            (180, 500),
        )


class Instructions:
    def __init__(self, app) -> None:
        self.app = app
        self.back = Button((48, 740, 200, 50), "Back", "back")

    def enter(self) -> None:
        pass

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.go("menu")
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back.contains(event.pos):
                self.app.go("menu")

    def update(self, dt: float) -> None:
        del dt

    def draw(self, surface: pygame.Surface) -> None:
        fonts = self.app.fonts
        draw_backdrop(surface)
        draw_text(surface, "Instructions", fonts["heading"], COLOR_TEXT, (48, 24))
        panel = pygame.Rect(36, 80, 1208, 640)
        draw_panel(surface, panel)
        y = panel.y + 20
        for line in wrap_text(INSTRUCTIONS.strip(), fonts["body"], panel.width - 48):
            draw_text(surface, line, fonts["body"], COLOR_TEXT, (panel.x + 24, y))
            y += 28
        self.back.draw(surface, fonts["button"])
