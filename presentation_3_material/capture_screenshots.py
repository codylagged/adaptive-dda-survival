"""Render the real screens and save them for the presentation.

The pixels come from the same draw methods the window uses. Completed
rounds in this script set ``log_sessions`` off so the experiment CSV is
not changed.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from frontend.app import App
from frontend.settings import WINDOW_HEIGHT, WINDOW_WIDTH


OUT = Path(__file__).resolve().parent / "screenshots"


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    app = App(screen)
    app.log_sessions = False
    OUT.mkdir(parents=True, exist_ok=True)

    def save(name: str) -> None:
        pygame.image.save(screen, str(OUT / name))
        print("saved", name)

    app.go("menu")
    app.screens["menu"].draw(screen)
    pygame.display.flip()
    save("01_main_menu.png")

    app.go("instructions")
    app.screens["instructions"].draw(screen)
    pygame.display.flip()
    save("02_instructions.png")

    app.go("mode")
    app.screens["mode"].draw(screen)
    pygame.display.flip()
    save("03_mode_select.png")

    print("Screenshots written to", OUT)
    pygame.quit()


if __name__ == "__main__":
    main()
