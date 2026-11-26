"""Screen loop. ``run`` is what ``python main.py`` calls."""

from __future__ import annotations

import pygame

from frontend.game_over_screen import GameOverScreen
from frontend.game_screen import GameScreen
from frontend.main_menu import Instructions, MainMenu, ModeSelect
from frontend.results_screen import ResultsScreen
from frontend.settings import (
    ASSETS_PATH,
    DECISIONS_PATH,
    SESSIONS_PATH,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from frontend.sprites import build_ground, build_sprites, save_assets, scaled
from frontend.ui import load_fonts


class App:
    """Holds the window, the shared bandit, and the screen that is active.

    The bandit lives here, not inside one match, because its estimates are
    meant to carry from round to round. Fixed and rule-based controllers
    are created fresh inside each match.
    """

    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.fonts = load_fonts()
        self.sprites = build_sprites()
        self.ground = build_ground(3)
        save_assets(self.sprites, self.ground, ASSETS_PATH)
        self.selection = {"mode": "fixed", "level": "medium"}
        self.bandit = None
        self.last_result = None
        self.log_note = ""
        self.log_sessions = True
        self.sessions_path = SESSIONS_PATH
        self.decisions_path = DECISIONS_PATH
        self.results_return = "menu"
        self.running = True
        self.state = "menu"
        self.screens = {
            "menu": MainMenu(self),
            "mode": ModeSelect(self),
            "instructions": Instructions(self),
            "play": GameScreen(self),
            "game_over": GameOverScreen(self),
            "results": ResultsScreen(self),
        }
        icon = scaled(self.sprites["player"], 2)
        pygame.display.set_icon(icon)
        self.go("menu")

    def go(self, name: str) -> None:
        self.state = name
        self.screens[name].enter()

    def open_results(self, return_to: str) -> None:
        self.results_return = return_to
        self.go("results")

    def loop(self) -> None:
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                self.screens[self.state].handle_event(event)
            if not self.running:
                break
            self.screens[self.state].update(dt)
            self.screens[self.state].draw(self.screen)
            pygame.display.flip()
        pygame.quit()


def run() -> None:
    pygame.init()
    pygame.display.set_caption("Adaptive Survival")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    App(screen).loop()
