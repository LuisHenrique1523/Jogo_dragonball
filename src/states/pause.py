from __future__ import annotations

import pygame

from .. import settings as cfg
from ..ui import text
from ..ui.widgets import OptionList
from .base import State

RESUME_KEYS = (pygame.K_ESCAPE, pygame.K_p)
PANEL_RECT = pygame.Rect(cfg.SCREEN_WIDTH // 2 - 210, 190, 420, 280)


class PauseState(State):
    def __init__(self, game, play_state):
        super().__init__(game)
        self.play = play_state
        self.session = play_state.session
        self.session.set_boost(False)
        self.options = OptionList(
            [("Continuar", self._resume),
             ("Reiniciar", lambda: self._leave(game.start_new_game)),
             ("Menu principal", lambda: self._leave(game.show_menu))],
            center=(PANEL_RECT.centerx, PANEL_RECT.top + 125), size=36, spacing=48,
            on_move=lambda: game.audio.play("move"))

    def _leave(self, action) -> None:
        self.game.highscore.submit(self.session.score)
        action()

    def _resume(self) -> None:
        self.game.audio.play("select")
        self.game.change_state(self.play)

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in RESUME_KEYS:
                self._resume()
                return
            if event.key == pygame.K_r:
                self._leave(self.game.start_new_game)
                return
            if event.key == pygame.K_m:
                self.game.audio.toggle_mute()
                return
        self.options.handle_event(event)

    def update(self, dt: float) -> None:
        self.options.update(dt)
        self.play.hud.update(dt)

    def draw(self, surface) -> None:
        self.play.draw(surface, paused=True)
        text.overlay(surface.subsurface(cfg.VIEWPORT), cfg.DARK, 150)
        rect = PANEL_RECT
        text.panel(surface, rect)
        title = text.gradient_title("PAUSA", 64)
        surface.blit(title, title.get_rect(center=(rect.centerx, rect.top + 50)))
        self.options.draw(surface)
        sound = "desligado" if self.game.audio.muted else "ligado"
        text.draw(surface, f"ESC continua  |  R reinicia  |  M som ({sound})", 20, cfg.CREAM,
                  midbottom=(rect.centerx, rect.bottom - 14))
