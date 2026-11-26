"""Keyboard mapping for one simulation tick.

The backend expects ``move_x``, ``move_y``, and ``attack``. It multiplies
each axis by ``player_speed`` and does not normalise the vector, so a
diagonal key press would otherwise be faster than a straight one. The
normalisation below keeps that from happening without editing the engine.
"""

from __future__ import annotations


def action_from_directions(
    left: bool,
    right: bool,
    up: bool,
    down: bool,
    attack: bool,
) -> dict:
    """Build the action dict ``GameEngine.set_external_action`` stores.

    Up decreases y because the window draws world y downward.
    """
    move_x = float(bool(right)) - float(bool(left))
    move_y = float(bool(down)) - float(bool(up))
    length_sq = move_x * move_x + move_y * move_y
    if length_sq > 1.0:
        length = length_sq ** 0.5
        move_x /= length
        move_y /= length
    return {"move_x": move_x, "move_y": move_y, "attack": bool(attack)}


def idle_action() -> dict:
    return {"move_x": 0.0, "move_y": 0.0, "attack": False}


def action_from_keyboard() -> dict:
    """Read WASD, the arrow keys, and Space. Called once per frame."""
    import pygame

    keys = pygame.key.get_pressed()
    return action_from_directions(
        left=keys[pygame.K_a] or keys[pygame.K_LEFT],
        right=keys[pygame.K_d] or keys[pygame.K_RIGHT],
        up=keys[pygame.K_w] or keys[pygame.K_UP],
        down=keys[pygame.K_s] or keys[pygame.K_DOWN],
        attack=keys[pygame.K_SPACE],
    )
