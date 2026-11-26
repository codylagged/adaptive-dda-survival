"""Window size, colours, and file paths used by the frontend."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
ASSETS_PATH = Path(__file__).resolve().parent / "assets"

SESSIONS_PATH = DATA_DIR / "sessions.csv"
DECISIONS_PATH = DATA_DIR / "decisions.csv"

WINDOW_WIDTH = 960
WINDOW_HEIGHT = 640

# Colours
BG = (18, 20, 28)
PANEL = (32, 36, 48)
ACCENT = (86, 156, 214)
TEXT = (230, 232, 236)
MUTED = (160, 164, 176)
GOOD = (120, 200, 120)
WARN = (230, 180, 80)
BAD = (220, 100, 100)
