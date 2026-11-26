"""CSV logger columns and append behaviour."""

from pathlib import Path

from backend.data_logger import DataLogger, SESSION_COLUMNS
from backend.fixed_difficulty import FixedDifficulty
from backend.game_config import GameConfig
from backend.game_engine import GameEngine


def test_logger_creates_headers(tmp_path: Path):
    sessions = tmp_path / "sessions.csv"
    decisions = tmp_path / "decisions.csv"
    logger = DataLogger(sessions, decisions)
    table = logger.load_sessions()
    assert list(table.columns) == SESSION_COLUMNS
    assert len(table) == 0


def test_log_session_appends_row(tmp_path: Path):
    sessions = tmp_path / "sessions.csv"
    decisions = tmp_path / "decisions.csv"
    logger = DataLogger(sessions, decisions)
    engine = GameEngine(GameConfig(), FixedDifficulty("easy"), seed=7)
    result = engine.run()
    logger.log_session(result)
    table = logger.load_sessions()
    assert len(table) == 1
    assert table["session_id"][0] == result.session_id
