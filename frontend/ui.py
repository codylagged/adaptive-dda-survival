"""Small drawing helpers shared by the menu, the match, and the results."""

from __future__ import annotations

import pygame

from frontend.settings import (
    COLOR_BG,
    COLOR_BUTTON,
    COLOR_BUTTON_HOVER,
    COLOR_BUTTON_ON,
    COLOR_GRID,
    COLOR_PANEL,
    COLOR_PANEL_BORDER,
    COLOR_TEXT,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)


def load_fonts() -> dict[str, pygame.font.Font]:
    return {
        "title": pygame.font.SysFont("segoeui", 52, bold=True),
        "heading": pygame.font.SysFont("segoeui", 30, bold=True),
        "button": pygame.font.SysFont("segoeui", 22, bold=True),
        "body": pygame.font.SysFont("segoeui", 20),
        "small": pygame.font.SysFont("segoeui", 17),
        "tiny": pygame.font.SysFont("segoeui", 15),
        "number": pygame.font.SysFont("consolas", 18),
        "number_small": pygame.font.SysFont("consolas", 15),
    }


def draw_backdrop(surface: pygame.Surface) -> None:
    surface.fill(COLOR_BG)
    for x in range(0, WINDOW_WIDTH, 48):
        pygame.draw.line(surface, COLOR_GRID, (x, 0), (x, WINDOW_HEIGHT))
    for y in range(0, WINDOW_HEIGHT, 48):
        pygame.draw.line(surface, COLOR_GRID, (0, y), (WINDOW_WIDTH, y))


def draw_panel(surface: pygame.Surface, rect: pygame.Rect, fill=COLOR_PANEL, border=COLOR_PANEL_BORDER) -> None:
    pygame.draw.rect(surface, fill, rect, border_radius=12)
    pygame.draw.rect(surface, border, rect, width=2, border_radius=12)


def wrap_text(text: str, font: pygame.font.Font, width: int) -> list[str]:
    """Wrap a paragraph on word boundaries. Newlines start a new paragraph."""
    lines: list[str] = []
    for paragraph in text.split("\n"):
        if paragraph == "":
            lines.append("")
            continue
        current = ""
        for word in paragraph.split():
            trial = word if not current else f"{current} {word}"
            if font.size(trial)[0] <= width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
    return lines


def draw_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color,
    pos,
    center: bool = False,
) -> pygame.Rect:
    image = font.render(text, True, color)
    rect = image.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    surface.blit(image, rect)
    return rect


class Button:
    def __init__(self, rect, label: str, key: str) -> None:
        self.rect = pygame.Rect(rect)
        self.label = label
        self.key = key

    def contains(self, pos) -> bool:
        return self.rect.collidepoint(pos)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, active: bool = False) -> None:
        hover = self.contains(pygame.mouse.get_pos())
        if active:
            fill = COLOR_BUTTON_ON
        elif hover:
            fill = COLOR_BUTTON_HOVER
        else:
            fill = COLOR_BUTTON
        pygame.draw.rect(surface, fill, self.rect, border_radius=8)
        border = (224, 164, 90) if active or hover else (78, 98, 90)
        pygame.draw.rect(surface, border, self.rect, width=2, border_radius=8)
        draw_text(surface, self.label, font, COLOR_TEXT, self.rect.center, center=True)


def button_at(buttons: list[Button], pos) -> Button | None:
    for button in buttons:
        if button.contains(pos):
            return button
    return None
