"""Summarise the CSV logs and draw the comparison bars with Pygame.

The numbers come from sessions.csv and decisions.csv, read with the
standard-library csv module. Modes with no rows are left out. A measured
zero, such as fixed difficulty never changing, is kept.

Pandas and Matplotlib stay in the experiment scripts. This module does
not import them, so opening the statistics screen does not load NumPy.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from backend.data_logger import DECISION_COLUMNS, SESSION_COLUMNS
from frontend.settings import MODE_ORDER, MODE_SHORT


METRIC_COLUMNS = [
    ("Survival (s)", "survival_time"),
    ("Score", "final_score"),
    ("Health", "remaining_health"),
    ("Defeated", "enemies_defeated"),
    ("Changes", "difficulty_changes"),
    ("Reward", "reward"),
]

CHART_METRICS = ["Survival (s)", "Score", "Health", "Defeated", "Changes"]

BAR_COLORS = {
    "Fixed": (143, 180, 176),
    "Rule-based": (224, 164, 90),
    "Bandit": (210, 122, 104),
}


def _empty_report(message: str) -> dict:
    return {
        "message": message,
        "frame": [],
        "interactive_frame": [],
        "decision_lines": [],
        "interactive_lines": [],
        "missing": list(MODE_ORDER),
        "recorded_rows": 0,
        "interactive_rows": 0,
        "error": False,
    }


def _read_csv(path: Path, expected_columns: list[str]) -> list[dict]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return []
        return list(reader)


def _to_float(value, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_report(sessions_path, decisions_path) -> dict:
    """Build the statistics table from the two CSV files.

    Interactive rows (session_id starting with 'interactive-') are kept
    separate so the experiment bars stay comparable to the batch results.
    """
    sessions = _read_csv(Path(sessions_path), SESSION_COLUMNS)
    decisions = _read_csv(Path(decisions_path), DECISION_COLUMNS)
    if not sessions:
        return _empty_report("No sessions recorded yet. Play a round or run the experiments.")

    experiment = [row for row in sessions if not str(row.get("session_id", "")).startswith("interactive-")]
    interactive = [row for row in sessions if str(row.get("session_id", "")).startswith("interactive-")]

    def summarise(rows: list[dict]) -> list[dict]:
        if not rows:
            return []
        by_mode: dict[str, list[dict]] = {}
        for row in rows:
            mode = row.get("experimental_mode", "")
            by_mode.setdefault(mode, []).append(row)
        summary = []
        for mode in MODE_ORDER:
            group = by_mode.get(mode)
            if not group:
                continue
            n = len(group)
            entry = {"Mode": MODE_SHORT.get(mode, mode), "N": n}
            for label, column in METRIC_COLUMNS:
                values = [_to_float(row.get(column)) for row in group]
                entry[label] = sum(values) / n if values else 0.0
            summary.append(entry)
        return summary

    frame = summarise(experiment)
    interactive_frame = summarise(interactive)

    decision_lines = []
    if decisions:
        changes = Counter()
        for row in decisions:
            if str(row.get("changed", "0")) in ("1", "True", "true"):
                mode = row.get("experimental_mode", "")
                changes[mode] += 1
        for mode in MODE_ORDER:
            if changes[mode]:
                decision_lines.append(f"{MODE_SHORT.get(mode, mode)} changed {changes[mode]} times")

    missing = [MODE_SHORT.get(m, m) for m in MODE_ORDER if m not in {r.get("experimental_mode") for r in experiment}]
    return {
        "message": f"{len(experiment)} experiment rows, {len(interactive)} interactive rows.",
        "frame": frame,
        "interactive_frame": interactive_frame,
        "decision_lines": decision_lines,
        "interactive_lines": [],
        "missing": missing,
        "recorded_rows": len(experiment),
        "interactive_rows": len(interactive),
        "error": False,
    }


def frame_as_text(frame: list[dict]) -> str:
    if not frame:
        return ""
    headers = ["Mode", "N"] + [label for label, _ in METRIC_COLUMNS]
    lines = [" ".join(f"{h:>12}" for h in headers)]
    for row in frame:
        cells = [f"{row.get('Mode', ''):>12}", f"{row.get('N', 0):>12}"]
        for label, _ in METRIC_COLUMNS:
            value = row.get(label, 0)
            if isinstance(value, float):
                cells.append(f"{value:>12.2f}")
            else:
                cells.append(f"{value:>12}")
        lines.append(" ".join(cells))
    return "\n".join(lines)


def render_chart_surface(report: dict):
    """Draw a simple bar chart of the experiment summary with Pygame.

    Returns a Surface or None if there is nothing to draw.
    """
    import pygame

    frame = report.get("frame") or []
    if not frame:
        return None

    width, height = 1100, 280
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    surface.fill((0, 0, 0, 0))

    metrics = CHART_METRICS
    modes = [row["Mode"] for row in frame]
    if not modes:
        return None

    # Normalise each metric independently so bars are comparable within a metric.
    values = {}
    for metric in metrics:
        nums = [float(row.get(metric, 0)) for row in frame]
        max_v = max(nums) if nums else 1.0
        if max_v <= 0:
            max_v = 1.0
        values[metric] = nums

    bar_width = 28
    group_gap = 40
    metric_gap = 120
    start_x = 40
    base_y = height - 40
    max_bar_height = 180

    font = pygame.font.SysFont("consolas", 14)
    for mi, metric in enumerate(metrics):
        mx = start_x + mi * metric_gap
        pygame.draw.line(surface, (80, 90, 86), (mx - 10, base_y), (mx + len(modes) * (bar_width + 6) + 10, base_y))
        label = font.render(metric, True, (200, 200, 200))
        surface.blit(label, (mx, base_y + 6))
        for bi, mode in enumerate(modes):
            val = values[metric][bi]
            max_v = max(values[metric]) if values[metric] else 1.0
            h = int((val / max_v) * max_bar_height) if max_v > 0 else 0
            color = BAR_COLORS.get(mode, (160, 160, 160))
            x = mx + bi * (bar_width + 6)
            pygame.draw.rect(surface, color, (x, base_y - h, bar_width, h))
    return surface
