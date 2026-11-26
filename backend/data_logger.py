"""CSV logs for sessions and difficulty decisions.

sessions.csv is one row per completed game.
decisions.csv is one row per controller decision, including the initial choice
and later choices that kept the same difficulty.

Rows are written with the standard-library csv module. The game can then
start without importing pandas, which would load a NumPy DLL.
"""

from __future__ import annotations

import csv
from pathlib import Path

from backend.game_engine import SessionResult


SESSION_COLUMNS = [
    "session_id",
    "experimental_mode",
    "selected_difficulty",
    "initial_difficulty",
    "dominant_difficulty",
    "survival_time",
    "final_score",
    "remaining_health",
    "enemies_defeated",
    "difficulty_changes",
    "reward",
    "timestamp",
    "game_over_reason",
    "seed",
    "ticks",
]

DECISION_COLUMNS = [
    "session_id",
    "experimental_mode",
    "tick",
    "previous_difficulty",
    "selected_difficulty",
    "changed",
    "reason",
    "policy_detail",
    "health_ratio",
    "recent_damage",
    "survival_time",
    "performance",
    "estimated_reward",
    "observed_reward",
    "timestamp",
]

_SESSION_INTS = {"final_score", "enemies_defeated", "difficulty_changes", "seed", "ticks"}
_SESSION_FLOATS = {"survival_time", "remaining_health", "reward"}
_DECISION_INTS = {"tick", "changed"}
_DECISION_FLOATS = {
    "health_ratio",
    "recent_damage",
    "survival_time",
    "performance",
    "estimated_reward",
    "observed_reward",
}


class CsvTable:
    """Rows loaded from one CSV file.

    Supports the column list, ``len``, ``table["column"]``, and
    ``table.iloc[i]`` used by the logger tests. It is not a pandas frame.
    """

    def __init__(self, columns: list[str], rows: list[dict]) -> None:
        self.columns = list(columns)
        self._rows = rows

    def __len__(self) -> int:
        return len(self._rows)

    def __getitem__(self, column: str) -> list:
        return [row[column] for row in self._rows]

    @property
    def iloc(self) -> "_Iloc":
        return _Iloc(self._rows)


class _Iloc:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def __getitem__(self, index: int) -> dict:
        return self._rows[index]


class DataLogger:
    def __init__(self, sessions_path: str | Path, decisions_path: str | Path) -> None:
        self.sessions_path = Path(sessions_path)
        self.decisions_path = Path(decisions_path)
        self.sessions_path.parent.mkdir(parents=True, exist_ok=True)
        self.decisions_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure(self.sessions_path, SESSION_COLUMNS)
        self._ensure(self.decisions_path, DECISION_COLUMNS)

    def reset(self) -> None:
        """Replace both CSV files with headers only."""
        self._write_header(self.sessions_path, SESSION_COLUMNS)
        self._write_header(self.decisions_path, DECISION_COLUMNS)

    def log_session(self, result: SessionResult) -> None:
        session_row = {
            "session_id": result.session_id,
            "experimental_mode": result.experimental_mode,
            "selected_difficulty": result.selected_difficulty,
            "initial_difficulty": result.initial_difficulty,
            "dominant_difficulty": result.dominant_difficulty,
            "survival_time": result.survival_time,
            "final_score": result.final_score,
            "remaining_health": result.remaining_health,
            "enemies_defeated": result.enemies_defeated,
            "difficulty_changes": result.difficulty_changes,
            "reward": result.reward,
            "timestamp": result.timestamp,
            "game_over_reason": result.game_over_reason,
            "seed": result.seed,
            "ticks": result.ticks,
        }
        self._append(self.sessions_path, SESSION_COLUMNS, session_row)
        for decision in result.decisions:
            decision_row = {
                "session_id": result.session_id,
                "experimental_mode": result.experimental_mode,
                "tick": decision.tick,
                "previous_difficulty": decision.previous_difficulty,
                "selected_difficulty": decision.selected_difficulty,
                "changed": int(decision.changed),
                "reason": decision.reason,
                "policy_detail": decision.policy_detail,
                "health_ratio": decision.health_ratio,
                "recent_damage": decision.recent_damage,
                "survival_time": decision.survival_time,
                "performance": decision.performance,
                "estimated_reward": decision.estimated_reward,
                "observed_reward": decision.observed_reward,
                "timestamp": result.timestamp,
            }
            self._append(self.decisions_path, DECISION_COLUMNS, decision_row)

    def load_sessions(self) -> CsvTable:
        return _read_table(self.sessions_path, SESSION_COLUMNS, _SESSION_INTS, _SESSION_FLOATS)

    def load_decisions(self) -> CsvTable:
        return _read_table(self.decisions_path, DECISION_COLUMNS, _DECISION_INTS, _DECISION_FLOATS)

    @staticmethod
    def _ensure(path: Path, columns: list[str]) -> None:
        if not path.exists() or path.stat().st_size == 0:
            DataLogger._write_header(path, columns)

    @staticmethod
    def _write_header(path: Path, columns: list[str]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(columns)

    @staticmethod
    def _append(path: Path, columns: list[str], row: dict) -> None:
        with path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n", extrasaction="ignore")
            writer.writerow({column: _csv_cell(row.get(column, "")) for column in columns})


def _csv_cell(value) -> str:
    """Match the previous logger: missing values are blank, numbers stay precise."""
    if value is None:
        return ""
    if isinstance(value, float):
        return repr(value)
    return str(value)


def _parse_cell(column: str, raw: str, ints: set[str], floats: set[str]):
    if raw == "":
        return None if column in floats else ""
    if column in ints:
        return int(float(raw))
    if column in floats:
        return float(raw)
    return raw


def _read_table(path: Path, fallback_columns: list[str], ints: set[str], floats: set[str]) -> CsvTable:
    if not path.exists() or path.stat().st_size == 0:
        return CsvTable(fallback_columns, [])
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = list(reader.fieldnames or fallback_columns)
        rows = []
        for raw_row in reader:
            rows.append(
                {
                    column: _parse_cell(column, (raw_row.get(column) or "").strip(), ints, floats)
                    for column in columns
                }
            )
    return CsvTable(columns, rows)
