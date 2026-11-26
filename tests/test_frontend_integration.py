"""The window must drive the real controllers, and the charts must use the CSV.

Algorithm checks below do not need a finished frame. The last test draws
each screen once. SDL is set to a dummy driver before pygame is imported
so the draw test does not open a desktop window.
"""

from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import csv
from collections import defaultdict

import pygame
import pytest

from backend.bandit import EpsilonGreedyBandit
from backend.data_logger import DataLogger
from backend.fixed_difficulty import FixedDifficulty
from backend.game_config import DIFFICULTY_PRESETS
from backend.rule_based_dda import RuleBasedDDA
from frontend.app import App
from frontend.charts import build_report, render_chart_surface
from frontend.controls import action_from_directions
from frontend.session import start_play_session
from frontend.settings import DECISIONS_PATH, MODE_SHORT, SESSIONS_PATH, WINDOW_HEIGHT, WINDOW_WIDTH


def _stand(engine, ticks: int) -> None:
    action = action_from_directions(False, False, False, False, False)
    for _ in range(ticks):
        engine.set_external_action(action)
        if not engine.step():
            break


def test_diagonal_input_is_not_faster_than_a_straight_step():
    action = action_from_directions(left=True, right=False, up=True, down=False, attack=True)
    assert action["attack"] is True
    assert action["move_x"] == pytest.approx(-0.70710678, abs=1e-6)
    assert action["move_y"] == pytest.approx(-0.70710678, abs=1e-6)
    straight = action_from_directions(False, True, False, False, False)
    assert straight["move_x"] == 1.0
    assert straight["move_y"] == 0.0


def test_manual_movement_uses_the_engine_speed():
    engine, _bandit = start_play_session("fixed", "easy", seed=1, session_id="test-move")
    assert engine.manual_control is True
    assert isinstance(engine.agent, FixedDifficulty)
    start = engine.player.x
    engine.set_external_action(action_from_directions(False, True, False, False, False))
    engine.step()
    assert engine.player.x == pytest.approx(start + engine.config.player_speed)


def test_fixed_difficulty_stays_on_the_preset():
    engine, _bandit = start_play_session("fixed", "medium", seed=2, session_id="test-fixed")
    _stand(engine, 30)
    preset = DIFFICULTY_PRESETS["medium"]
    assert engine.difficulty == "medium"
    assert engine.difficulty_changes == 0
    assert engine.enemies
    assert all(enemy.speed == preset.enemy_speed for enemy in engine.enemies)
    assert all(enemy.damage == preset.enemy_damage for enemy in engine.enemies)


def test_spawn_interval_changes_how_many_enemies_are_alive():
    easy, _bandit = start_play_session("fixed", "easy", seed=4, session_id="test-easy-count")
    hard, _bandit = start_play_session("fixed", "hard", seed=4, session_id="test-hard-count")
    _stand(easy, 30)
    _stand(hard, 30)
    assert not easy.game_over
    assert not hard.game_over
    assert len(hard.enemies) > len(easy.enemies)


def test_rule_based_controller_steps_down_and_updates_live_enemies():
    engine, _bandit = start_play_session("rule_based", "medium", seed=5, session_id="test-rules")
    assert isinstance(engine.agent, RuleBasedDDA)
    assert engine.agent.mode_name == "rule_based"
    engine.player.health = 20
    _stand(engine, 28)
    assert engine.difficulty == "easy"
    assert engine.difficulty_changes == 1
    assert engine.decisions[-1].reason == "health_below_threshold"
    easy = DIFFICULTY_PRESETS["easy"]
    medium = DIFFICULTY_PRESETS["medium"]
    healths = sorted(enemy.max_health for enemy in engine.enemies)
    assert healths == [easy.enemy_health, medium.enemy_health]
    assert all(enemy.speed == easy.enemy_speed for enemy in engine.enemies)
    assert all(enemy.damage == easy.enemy_damage for enemy in engine.enemies)


def test_bandit_update_uses_the_backend_object_and_the_preset_speed():
    bandit = EpsilonGreedyBandit(epsilon=0.0, check_interval=40, seed=3)
    engine, kept = start_play_session(
        "bandit",
        "medium",
        bandit=bandit,
        seed=6,
        session_id="test-bandit",
    )
    assert kept is bandit
    assert engine.agent is bandit
    opening = engine.difficulty
    # Keep the player alive so the decision tick is reached even on hard.
    engine.player.health = 10_000
    _stand(engine, 40)
    assert bandit.counts[opening] == 1
    assert engine.difficulty in DIFFICULTY_PRESETS
    preset = DIFFICULTY_PRESETS[engine.difficulty]
    assert engine.enemies
    assert all(enemy.speed == preset.enemy_speed for enemy in engine.enemies)


def test_finished_round_is_appended_with_the_backend_columns(tmp_path):
    engine, _bandit = start_play_session("fixed", "hard", seed=7, session_id="interactive-fixed-test")
    engine.player.health = 1
    engine.spawn_enemy(engine.player.x, engine.player.y)
    engine.set_external_action(action_from_directions(False, False, False, False, False))
    assert engine.step() is False
    result = engine.finish()
    sessions = tmp_path / "sessions.csv"
    decisions = tmp_path / "decisions.csv"
    from frontend.session import log_finished_session

    log_finished_session(result, sessions, decisions)
    loaded = DataLogger(sessions, decisions).load_sessions()
    assert list(loaded["session_id"]) == ["interactive-fixed-test"]
    assert loaded.iloc[0]["experimental_mode"] == "fixed"
    assert float(loaded.iloc[0]["remaining_health"]) == 0
    assert loaded.iloc[0]["game_over_reason"] == "health_depleted"


def test_empty_log_says_more_sessions_are_required(tmp_path):
    logger = DataLogger(tmp_path / "sessions.csv", tmp_path / "decisions.csv")
    report = build_report(logger.sessions_path, logger.decisions_path)
    assert report["frame"] == []
    assert report["recorded_rows"] == 0
    assert "more sessions are required" in report["message"].lower()


def test_a_partial_log_does_not_invent_the_missing_modes(tmp_path):
    sessions = tmp_path / "sessions.csv"
    decisions = tmp_path / "decisions.csv"
    logger = DataLogger(sessions, decisions)
    engine, _bandit = start_play_session("fixed", "easy", seed=8, session_id="fixed-only")
    logger.log_session(engine.run())
    report = build_report(sessions, decisions)
    assert [row["Mode"] for row in report["frame"]] == ["Fixed"]
    assert "more sessions are required" in report["message"].lower()
    assert "Rule-based" in report["message"]
    assert "Bandit" in report["message"]


def test_real_log_means_match_the_csv():
    with SESSIONS_PATH.open(newline="", encoding="utf-8") as handle:
        sessions = list(csv.DictReader(handle))
    report = build_report(SESSIONS_PATH, DECISIONS_PATH)
    recorded = [row for row in sessions if not str(row["session_id"]).startswith("interactive-")]
    assert report["recorded_rows"] == len(recorded)
    groups: dict[str, list] = defaultdict(list)
    for row in recorded:
        groups[row["experimental_mode"]].append(row)
    for mode, group in groups.items():
        summary = next(item for item in report["frame"] if item["Mode"] == MODE_SHORT[mode])
        assert int(summary["n"]) == len(group)
        survival = sum(float(item["survival_time"]) for item in group) / len(group)
        changes = sum(float(item["difficulty_changes"]) for item in group) / len(group)
        assert float(summary["Survival (s)"]) == pytest.approx(survival, abs=0.01)
        assert float(summary["Changes"]) == pytest.approx(changes, abs=0.01)


def test_screens_draw_and_a_logged_round_reaches_game_over(tmp_path):
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    app = App(screen)
    app.sessions_path = tmp_path / "sessions.csv"
    app.decisions_path = tmp_path / "decisions.csv"
    app.selection = {"mode": "fixed", "level": "hard"}

    for name in ("menu", "mode", "instructions"):
        app.go(name)
        app.screens[name].draw(screen)

    app.go("play")
    game = app.screens["play"]
    game.read_keyboard = False
    game.action = action_from_directions(False, False, False, False, False)
    game.engine.player.health = 1
    game.engine.spawn_enemy(game.engine.player.x, game.engine.player.y)
    game.update(0.1)
    assert app.state == "game_over"
    assert app.last_result.remaining_health == 0
    loaded = DataLogger(app.sessions_path, app.decisions_path).load_sessions()
    assert len(loaded) == 1
    assert str(loaded.iloc[0]["session_id"]).startswith("interactive-")

    app.screens["game_over"].draw(screen)
    game.paused = True
    game.completed = False
    game.engine.game_over = False
    game.draw(screen)

    app.go("results")
    app.screens["results"].draw(screen)
    real_report = build_report(SESSIONS_PATH, DECISIONS_PATH)
    real_chart = render_chart_surface(real_report)
    assert real_chart is not None
    assert real_chart.get_width() > 0
    app.screens["results"].report = real_report
    app.screens["results"].chart = real_chart
    app.screens["results"].draw(screen)

    empty = DataLogger(tmp_path / "empty_sessions.csv", tmp_path / "empty_decisions.csv")
    app.screens["results"].enter(empty.sessions_path, empty.decisions_path)
    assert "more sessions are required" in app.screens["results"].report["message"].lower()
    assert app.screens["results"].chart is None
    app.screens["results"].draw(screen)
    pygame.quit()
