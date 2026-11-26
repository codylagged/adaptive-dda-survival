"""Statistics screen. The table and bars are computed from the CSV files."""

from __future__ import annotations

import pygame

from frontend.charts import build_report, frame_as_text, render_chart_surface
from frontend.settings import COLOR_ACCENT, COLOR_MUTED, COLOR_TEXT
from frontend.ui import Button, draw_backdrop, draw_panel, draw_text, wrap_text


class ResultsScreen:
    def __init__(self, app) -> None:
        self.app = app
        self.report = None
        self.chart = None
        self.back = Button((48, 764, 200, 50), "Back", "back")

    def enter(self, sessions_path=None, decisions_path=None) -> None:
        sessions = self.app.sessions_path if sessions_path is None else sessions_path
        decisions = self.app.decisions_path if decisions_path is None else decisions_path
        self.report = build_report(sessions, decisions)
        self.chart = render_chart_surface(self.report)

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._back()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back.contains(event.pos):
                self._back()

    def _back(self) -> None:
        target = self.app.results_return or "menu"
        if target == "game_over" and self.app.last_result is None:
            target = "menu"
        self.app.go(target)

    def update(self, dt: float) -> None:
        del dt

    def draw(self, surface: pygame.Surface) -> None:
        fonts = self.app.fonts
        draw_backdrop(surface)
        draw_text(surface, "Statistics", fonts["heading"], COLOR_TEXT, (48, 18))
        draw_text(
            surface,
            "Read from data/sessions.csv and data/decisions.csv",
            fonts["tiny"],
            COLOR_MUTED,
            (230, 32),
        )
        report = self.report or {}
        message = report.get("message", "No report was built.")
        y = 64
        for line in wrap_text(message, fonts["small"], 1180)[:3]:
            draw_text(surface, line, fonts["small"], COLOR_TEXT, (48, y))
            y += 22

        panel = pygame.Rect(36, y + 8, 1208, max(220, 740 - (y + 8)))
        draw_panel(surface, panel)
        inner_y = panel.y + 16
        frame = report.get("frame")
        text = frame_as_text(frame) if frame is not None else ""
        if text:
            for line in text.splitlines():
                color = COLOR_ACCENT if line.startswith("Mode") else COLOR_TEXT
                draw_text(surface, line, fonts["number_small"], color, (panel.x + 20, inner_y))
                inner_y += 20
        else:
            draw_text(surface, "No experiment rows to tabulate.", fonts["body"], COLOR_MUTED, (panel.x + 20, inner_y))
            inner_y += 28

        interactive = report.get("interactive_frame")
        interactive_text = frame_as_text(interactive) if interactive is not None else ""
        if interactive_text:
            inner_y += 8
            count = report.get("interactive_rows", 0)
            draw_text(
                surface,
                f"Played in this window ({count}). Not included in the bars above the fold.",
                fonts["tiny"],
                COLOR_ACCENT,
                (panel.x + 20, inner_y),
            )
            inner_y += 20
            for line in interactive_text.splitlines():
                draw_text(surface, line, fonts["number_small"], COLOR_TEXT, (panel.x + 20, inner_y))
                inner_y += 18

        if self.chart is not None:
            chart = self.chart
            # Fit the chart under the table without covering the back button.
            max_height = panel.bottom - inner_y - 78
            if chart.get_height() > max_height > 40:
                scale = max_height / chart.get_height()
                chart = pygame.transform.smoothscale(
                    chart,
                    (int(chart.get_width() * scale), int(max_height)),
                )
            surface.blit(chart, (panel.x + 16, inner_y + 6))
            inner_y += chart.get_height() + 8

        lines = list(report.get("decision_lines") or [])
        extra = report.get("interactive_lines") or []
        if extra and report.get("interactive_rows"):
            lines.extend(extra)
        # Keep the decision summary on one short line if the chart already filled the card.
        if lines and inner_y < panel.bottom - 28:
            summary = "  ".join(lines[:2])
            for line in wrap_text(summary, fonts["tiny"], panel.width - 40)[:2]:
                draw_text(surface, line, fonts["tiny"], COLOR_MUTED, (panel.x + 20, min(inner_y, panel.bottom - 24)))
                inner_y += 16

        self.back.draw(surface, fonts["button"])
