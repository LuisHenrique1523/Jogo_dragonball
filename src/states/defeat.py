from __future__ import annotations

import pygame

from .. import settings as cfg
from ..graphics.dragon_renderer import interpolated_points
from ..logic.session import DEATH_MESSAGES
from ..ui import text
from .end_screen import EndScreenState

EXPLODE_START = 0.45
EXPLODE_INTERVAL = 0.05
PANEL_DELAY = 0.7
PANEL_RECT = pygame.Rect(cfg.SCREEN_WIDTH // 2 - 280, 180, 560, 360)


class DefeatState(EndScreenState):
    def __init__(self, game, play_state):
        super().__init__(game, play_state, options_y=PANEL_RECT.top + 235)
        self.exploded = 0
        self.points = interpolated_points(self.session.dragon, self.session.step_progress)
        self.panel_time = EXPLODE_START + len(self.points) * EXPLODE_INTERVAL + PANEL_DELAY

    def update(self, dt: float) -> None:
        super().update(dt)
        target = min(len(self.points), max(0, int((self.time - EXPLODE_START) / EXPLODE_INTERVAL) + 1))
        while self.exploded < target:
            self._explode(self.exploded)
            self.exploded += 1

    def _explode(self, index: int) -> None:
        p = self.points[index]
        particles = self.scene.effects.particles
        particles.burst(p.x, p.y, 18, cfg.DRAGON_GREEN, speed=(60, 220), life=(0.5, 1.1), gravity=160)
        particles.burst(p.x, p.y, 6, cfg.GOLD, speed=(30, 120), life=(0.4, 0.8))
        if index == 0:
            self.scene.effects.shockwave(p.x, p.y, cfg.DANGER_RED, max_radius=140, duration=0.6)

    def draw(self, surface) -> None:
        self.scene.draw(surface, hidden=self.exploded)
        self.play.hud.draw(surface, self.session, self.game.highscore.best, show_radar=False)
        redness = min(1.0, self.time / 1.2)
        text.overlay(surface.subsurface(cfg.VIEWPORT), (60, 0, 10), int(120 * redness))
        if self.show_panel:
            self._draw_panel(surface)

    def _draw_panel(self, surface) -> None:
        rect = PANEL_RECT
        text.panel(surface, rect, border=cfg.DANGER_RED)
        title = text.gradient_title("DERROTA", 72, top=(255, 120, 90), bottom=(170, 10, 10))
        surface.blit(title, title.get_rect(center=(rect.centerx, rect.top + 50)))
        cx = rect.centerx
        text.draw(surface, DEATH_MESSAGES[self.session.death_reason], 26, cfg.CREAM, center=(cx, rect.top + 105))
        text.draw(surface, f"Pontos: {self.session.score}    Esferas: {len(self.session.collected)}/7",
                  30, cfg.WHITE, center=(cx, rect.top + 145))
        text.draw(surface, self.record_line(), 26, cfg.GOLD, center=(cx, rect.top + 180))
        self.options.draw(surface)
        text.draw(surface, "ENTER escolhe  |  R reinicia  |  ESC menu", 20, cfg.CREAM,
                  midbottom=(cx, rect.bottom - 12))
