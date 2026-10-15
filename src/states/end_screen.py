from __future__ import annotations

import pygame

from .. import settings as cfg
from ..ui.widgets import OptionList
from .base import State

SKIP_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE)
INPUT_GRACE = 0.35


class EndScreenState(State):
    panel_time = 0.0

    def __init__(self, game, play_state, options_y: int):
        super().__init__(game)
        self.play = play_state
        self.session = play_state.session
        self.scene = play_state.scene
        self.session.set_boost(False)
        self.time = 0.0
        self.new_record = game.highscore.submit(self.session.score)
        self.options = OptionList(
            [("Jogar novamente", game.start_new_game), ("Menu principal", game.show_menu)],
            center=(cfg.SCREEN_WIDTH // 2, options_y), size=34, spacing=46,
            on_move=lambda: game.audio.play("move"))

    @property
    def show_panel(self) -> bool:
        return self.time >= self.panel_time

    def handle_event(self, event) -> None:
        key = event.key if event.type == pygame.KEYDOWN else None
        if not self.show_panel:
            if key in SKIP_KEYS:
                self.time = self.panel_time
            return
        if self.time < self.panel_time + INPUT_GRACE:
            return
        if key == pygame.K_r:
            self.game.start_new_game()
        elif key == pygame.K_ESCAPE:
            self.game.show_menu()
        else:
            self.options.handle_event(event)

    def update(self, dt: float) -> None:
        self.time += dt
        self.scene.update(dt)
        self.options.update(dt)

    def record_line(self) -> str:
        return "NOVO RECORDE!" if self.new_record else f"Recorde: {self.game.highscore.best}"
