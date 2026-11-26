"""Pixel characters drawn in code, then saved under frontend/assets.

They are display-only. Position, health, and speed still come from the
backend snapshot and the difficulty presets.
"""

from __future__ import annotations

from pathlib import Path

import pygame


def _surface(rows: list[str], palette: dict[str, tuple]) -> pygame.Surface:
    height = len(rows)
    width = len(rows[0])
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, mark in enumerate(row):
            color = palette.get(mark)
            if color is not None:
                surface.set_at((x, y), color)
    return surface


def build_sprites() -> dict[str, pygame.Surface]:
    """Return unscaled sprites. Callers scale them by an integer factor."""
    player = _surface(
        [
            "................",
            "......hhhh......",
            ".....hhhhhh.....",
            "....hhhsshhh....",
            "....hhsssshh....",
            "....hhhhhhhh....",
            ".....hhbbhh.....",
            "....bbbbbbbb....",
            "...bbbbbbbbbb...",
            "...bbbbbbbbbb...",
            "....bbbbbbbb....",
            ".....bb..bb.....",
            ".....bb..bb.....",
            ".....bb..bb.....",
            "....bbb..bbb....",
            "................",
        ],
        {
            "h": (28, 92, 96),
            "s": (214, 176, 140),
            "b": (126, 200, 196),
        },
    )
    enemy = _surface(
        [
            "................",
            ".....rrrrr......",
            "...rrrrrrrrr....",
            "..rrwrrrrrwrr...",
            "..rrwkrrrwkrr...",
            "..rrrrrrrrrrr...",
            "...rrrrrrrrr....",
            "..rrrrrrrrrrr...",
            "..rr.rrrr.rr....",
            "..rr.rrrr.rr....",
            "...rr.rr.rr.....",
            "....r....r......",
            "....r....r......",
            "...rr....rr.....",
            "................",
            "................",
        ],
        {
            "r": (176, 72, 68),
            "w": (236, 224, 210),
            "k": (32, 24, 24),
        },
    )
    return {"player": player, "enemy": enemy}


def build_ground(scale: int) -> pygame.Surface:
    """A dark tiled floor for the 240 by 240 world. Tiles are cosmetic."""
    world = 240
    surface = pygame.Surface((world * scale, world * scale))
    surface.fill((16, 22, 20))
    tile = 16
    for gy in range(0, world, tile):
        for gx in range(0, world, tile):
            # Both axes have to change the shade. A multiple of the tile
            # size would otherwise cancel out and leave vertical stripes.
            shade = 28 + ((gx * 13 + gy * 7) % 5) * 3
            color = (shade, shade + 5, shade + 3)
            inset = max(1, scale // 2)
            pygame.draw.rect(
                surface,
                color,
                (
                    gx * scale + inset,
                    gy * scale + inset,
                    tile * scale - inset * 2,
                    tile * scale - inset * 2,
                ),
            )
    stone = (52, 62, 56)
    for index in range(14):
        sx = (23 + index * 41) % (world - 10)
        sy = (19 + index * 29) % (world - 10)
        pygame.draw.circle(surface, stone, (int(sx * scale), int(sy * scale)), max(2, scale))
    return surface


def scaled(sprite: pygame.Surface, factor: int) -> pygame.Surface:
    width = sprite.get_width() * factor
    height = sprite.get_height() * factor
    return pygame.transform.scale(sprite, (width, height))


def save_assets(sprites: dict[str, pygame.Surface], ground: pygame.Surface, folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for name, sprite in sprites.items():
        pygame.image.save(scaled(sprite, 4), str(folder / f"{name}.png"))
    pygame.image.save(ground, str(folder / "ground.png"))
