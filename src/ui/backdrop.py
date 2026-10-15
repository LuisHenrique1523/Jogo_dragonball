from __future__ import annotations

import math

import pygame
from pygame import Vector2

from .. import settings as cfg
from ..graphics.background import SkyBackground
from ..graphics.dragon_renderer import DragonRenderer, tangent_angle

DRAGON_SEGMENTS = 22
SEGMENT_DELAY = 0.075


def lissajous(t: float) -> Vector2:
    return Vector2(cfg.SCREEN_WIDTH / 2 + 400 * math.sin(0.55 * t),
                   cfg.SCREEN_HEIGHT / 2 + 40 + 200 * math.sin(1.1 * t + 0.6))


class MenuBackdrop:
    def __init__(self):
        self.sky = SkyBackground((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT))
        self.sky.progress = 0.12
        self.renderer = DragonRenderer()
        self.time = 0.0

    def update(self, dt: float) -> None:
        self.time += dt
        self.renderer.update(dt)

    def draw(self, surface: pygame.Surface, dim: int = 0) -> None:
        self.sky.draw(surface, (self.time * 40, 0), self.time)
        points = [lissajous(self.time - i * SEGMENT_DELAY) for i in range(DRAGON_SEGMENTS)]
        angle = tangent_angle(points[0], points[1])
        self.renderer.draw_path(surface, points, angle, scale=1.15)
        if dim:
            shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            shade.fill((*cfg.DARK, dim))
            surface.blit(shade, (0, 0))
