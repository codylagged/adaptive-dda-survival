"""Window size, colours, and the labels shared by every screen.

Gameplay numbers such as enemy speed and damage are not stored here.
Those live in ``backend.game_config`` so the window cannot drift away
from the experiment.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SESSIONS_PATH = ROOT / "data" / "sessions.csv"
DECISIONS_PATH = ROOT / "data" / "decisions.csv"
ASSETS_PATH = Path(__file__).resolve().parent / "assets"

# One simulation unit is drawn this many pixels across.
# The backend world is 240 by 240 units (see GameConfig).
SCALE = 3
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 830
ARENA_X = 36
ARENA_Y = 56

# A human round is longer than the 20-second experiment default so that
# several controller decisions fit in one play. Presets are not changed.
# 60 seconds / 0.1 seconds per tick = 600 ticks.
INTERACTIVE_LIMIT_SECONDS = 60.0

COLOR_BG = (12, 16, 15)
COLOR_GRID = (22, 30, 28)
COLOR_PANEL = (20, 28, 26)
COLOR_PANEL_BORDER = (62, 80, 74)
COLOR_TEXT = (236, 230, 218)
COLOR_MUTED = (166, 176, 168)
COLOR_ACCENT = (224, 164, 90)
COLOR_BUTTON = (30, 42, 38)
COLOR_BUTTON_HOVER = (48, 66, 58)
COLOR_BUTTON_ON = (62, 50, 30)
COLOR_HEALTH = (118, 186, 122)
COLOR_HEALTH_LOW = (196, 96, 84)
COLOR_HEALTH_BG = (42, 28, 28)
COLOR_EASY = (126, 184, 140)
COLOR_MEDIUM = (224, 164, 90)
COLOR_HARD = (196, 96, 84)

MODE_ORDER = ("fixed", "rule_based", "bandit")
MODE_LABELS = {
    "fixed": "Fixed Difficulty",
    "rule_based": "Rule-Based DDA",
    "bandit": "Epsilon-Greedy Bandit",
}
MODE_SHORT = {
    "fixed": "Fixed",
    "rule_based": "Rule-based",
    "bandit": "Bandit",
}
LEVELS = ("easy", "medium", "hard")


def difficulty_color(name: str) -> tuple[int, int, int]:
    return {
        "easy": COLOR_EASY,
        "medium": COLOR_MEDIUM,
        "hard": COLOR_HARD,
    }.get(name, COLOR_ACCENT)


def describe_selection(selection: dict) -> str:
    """One line for the menu, naming the controller the next round will use."""
    mode = selection.get("mode", "fixed")
    level = selection.get("level", "medium")
    if mode == "bandit":
        return "Epsilon-greedy bandit (the bandit chooses the level)"
    if mode == "rule_based":
        return f"Rule-based DDA, starting at {level}"
    return f"Fixed difficulty, {level}"
