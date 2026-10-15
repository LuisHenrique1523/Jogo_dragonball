from __future__ import annotations

import math

import pygame

from .. import settings as cfg
from ..graphics import sprites
from ..ui import text
from ..ui.backdrop import MenuBackdrop
from ..ui.widgets import OptionList
from .base import State


class MenuState(State):
    def __init__(self, game, backdrop: MenuBackdrop | None = None):
        super().__init__(game)
        self.backdrop = backdrop or MenuBackdrop()
        self.options = OptionList(
            [("Jogar", game.start_new_game),
             ("Instruções", lambda: game.show_instructions(self.backdrop)),
             ("Sair", game.quit)],
            center=(cfg.SCREEN_WIDTH // 2, 400), on_move=lambda: game.audio.play("move"))

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.quit()
            return
        self.options.handle_event(event)

    def update(self, dt: float) -> None:
        self.backdrop.update(dt)
        self.options.update(dt)

    def draw(self, surface) -> None:
        self.backdrop.draw(surface, dim=70)
        t = self.backdrop.time
        title = text.gradient_title("SHENLONG", 120)
        title = pygame.transform.rotozoom(title, 0, 1 + 0.02 * math.sin(t * 2))
        surface.blit(title, title.get_rect(center=(cfg.SCREEN_WIDTH // 2, 120)))
        text.draw(surface, "A Busca das Sete Esferas", 40, cfg.CREAM, center=(cfg.SCREEN_WIDTH // 2, 190))
        self._draw_ball_arc(surface, t)
        text.panel(surface, pygame.Rect(cfg.SCREEN_WIDTH // 2 - 200, 360, 400, 160), alpha=170)
        self.options.draw(surface)
        text.draw(surface, f"Recorde: {self.game.highscore.best}", 24, cfg.GOLD,
                  bottomleft=(16, cfg.SCREEN_HEIGHT - 12))
        text.draw(surface, "Projeto acadêmico de Computação Gráfica  |  Setas e ENTER", 20, (220, 225, 240),
                  bottomright=(cfg.SCREEN_WIDTH - 16, cfg.SCREEN_HEIGHT - 12))

    def _draw_ball_arc(self, surface, t: float) -> None:
        for i in range(cfg.TOTAL_BALLS):
            angle = math.radians(200 + i * 140 / 6)
            x = cfg.SCREEN_WIDTH // 2 + math.cos(angle) * 300
            y = 330 + math.sin(angle) * 70 + math.sin(t * 3 + i) * 5
            halo = sprites.glow(30, (140, 80, 0))
            surface.blit(halo, halo.get_rect(center=(x, y)), special_flags=pygame.BLEND_RGB_ADD)
            ball = sprites.dragon_ball(i + 1, 20)
            surface.blit(ball, ball.get_rect(center=(x, y)))
