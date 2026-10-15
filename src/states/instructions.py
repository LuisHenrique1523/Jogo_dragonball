from __future__ import annotations

import pygame

from .. import settings as cfg
from ..ui import text
from ..ui.backdrop import MenuBackdrop
from .base import State

SECTIONS = [
    ("OBJETIVO", [
        "Guie Shenlong pelo céu e reúna as 7 Esferas do Dragão,",
        "da esfera de 1 estrela até a de 7 estrelas, em ordem.",
        "Com as sete reunidas, o dragão é invocado: vitória!",
    ]),
    ("COMO JOGAR", [
        "O mundo é maior que a tela: use o RADAR DO DRAGÃO",
        "(canto inferior direito) para achar a próxima esfera.",
        "Cada esfera faz o dragão crescer e aumenta o nível:",
        "mais velocidade e novas rochas no caminho.",
        "Colete rápido: o bônus de tempo diminui a cada segundo.",
    ]),
    ("DERROTA", [
        "Bater no próprio corpo, em uma rocha ou na barreira",
        "de energia que cerca o mundo encerra a partida.",
    ]),
]

CONTROLS = [
    ("Setas / WASD", "mover o dragão"),
    ("ESPAÇO ou SHIFT (segurar)", "Turbo de Ki: mais velocidade, gasta Ki"),
    ("ESC ou P", "pausar / continuar"),
    ("M", "liga/desliga o som"),
    ("ENTER", "confirmar / pular a animação final"),
    ("R", "reiniciar (pausa e painel final)"),
]


class InstructionsState(State):
    def __init__(self, game, backdrop: MenuBackdrop | None = None):
        super().__init__(game)
        self.backdrop = backdrop or MenuBackdrop()

    def handle_event(self, event) -> None:
        back = (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_BACKSPACE)
        clicked = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
        if (event.type == pygame.KEYDOWN and event.key in back) or clicked:
            self.game.audio.play("select")
            self.game.show_menu(self.backdrop)

    def update(self, dt: float) -> None:
        self.backdrop.update(dt)

    def draw(self, surface) -> None:
        self.backdrop.draw(surface, dim=120)
        text.panel(surface, pygame.Rect(30, 20, cfg.SCREEN_WIDTH - 60, cfg.SCREEN_HEIGHT - 40))
        title = text.gradient_title("INSTRUÇÕES", 64)
        surface.blit(title, title.get_rect(center=(cfg.SCREEN_WIDTH // 2, 62)))

        y = 110
        for heading, lines in SECTIONS:
            text.draw(surface, heading, 28, cfg.GOLD, topleft=(60, y))
            y += 28
            for line in lines:
                text.draw(surface, line, 22, cfg.WHITE, topleft=(70, y))
                y += 22
            y += 12

        x, y = 560, 110
        text.draw(surface, "CONTROLES", 28, cfg.GOLD, topleft=(x, y))
        y += 32
        for key, action in CONTROLS:
            text.draw(surface, key, 22, cfg.KI_BLUE, topleft=(x + 10, y))
            text.draw(surface, action, 20, cfg.WHITE, topleft=(x + 20, y + 20))
            y += 46

        text.draw(surface, "ENTER ou ESC para voltar", 24, cfg.CREAM,
                  midbottom=(cfg.SCREEN_WIDTH // 2, cfg.SCREEN_HEIGHT - 34))
