from __future__ import annotations

import math
from typing import Callable

import pygame

from .. import settings as cfg
from ..graphics import sprites
from . import text

UP_KEYS = (pygame.K_UP, pygame.K_w)
DOWN_KEYS = (pygame.K_DOWN, pygame.K_s)
CONFIRM_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER)


class OptionList:
    def __init__(self, options: list[tuple[str, Callable[[], None]]], center: tuple[int, int],
                 spacing: int = 52, size: int = 40, on_move: Callable[[], None] | None = None):
        self.options = options
        self.center = center
        self.spacing = spacing
        self.size = size
        self.index = 0
        self.on_move = on_move
        self.time = 0.0

    def _rect(self, i: int) -> pygame.Rect:
        cx, cy = self.center
        rect = pygame.Rect(0, 0, 320, self.spacing - 6)
        rect.center = (cx, cy + i * self.spacing)
        return rect

    def _move(self, delta: int) -> None:
        self.index = (self.index + delta) % len(self.options)
        if self.on_move:
            self.on_move()

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key in UP_KEYS:
                self._move(-1)
            elif event.key in DOWN_KEYS:
                self._move(1)
            elif event.key in CONFIRM_KEYS:
                self.options[self.index][1]()
            else:
                return False
            return True
        if event.type == pygame.MOUSEMOTION:
            for i in range(len(self.options)):
                if self._rect(i).collidepoint(event.pos) and i != self.index:
                    self.index = i
                    if self.on_move:
                        self.on_move()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, (_, action) in enumerate(self.options):
                if self._rect(i).collidepoint(event.pos):
                    self.index = i
                    action()
                    return True
        return False

    def update(self, dt: float) -> None:
        self.time += dt

    def draw(self, surface: pygame.Surface) -> None:
        for i, (label, _) in enumerate(self.options):
            rect = self._rect(i)
            selected = i == self.index
            color = cfg.GOLD if selected else (210, 215, 235)
            label_rect = text.draw(surface, label, self.size + (4 if selected else 0), color, center=rect.center)
            if selected:
                ball = pygame.transform.rotozoom(sprites.dragon_ball(4, 12), self.time * 120, 1.0)
                bob = math.sin(self.time * 6) * 4
                surface.blit(ball, ball.get_rect(center=(label_rect.left - 26 + bob, rect.centery)))
                surface.blit(ball, ball.get_rect(center=(label_rect.right + 26 - bob, rect.centery)))
