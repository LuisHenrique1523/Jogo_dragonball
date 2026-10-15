from __future__ import annotations

import math
from functools import lru_cache

import pygame
from pygame import Vector2

from .. import settings as cfg
from ..graphics import sprites
from ..logic.grid import direction_angle
from ..logic.session import Session
from . import text

SLOT_SPACING = 40
SLOT_RADIUS = 14
SLOT_FLASH_TIME = 0.7

RADAR_RADIUS = 60
RADAR_RANGE = 20
RADAR_CENTER = (cfg.SCREEN_WIDTH - RADAR_RADIUS - 22, cfg.SCREEN_HEIGHT - RADAR_RADIUS - 22)


def slot_center(index: int) -> tuple[int, int]:
    return cfg.SCREEN_WIDTH // 2 + (index - 3) * SLOT_SPACING, cfg.HUD_HEIGHT // 2


@lru_cache(maxsize=1)
def _bar_background() -> pygame.Surface:
    bar = sprites.vertical_gradient(cfg.SCREEN_WIDTH, cfg.HUD_HEIGHT, (40, 35, 95), (14, 16, 45)).copy()
    pygame.draw.line(bar, cfg.ORANGE, (0, cfg.HUD_HEIGHT - 3), (cfg.SCREEN_WIDTH, cfg.HUD_HEIGHT - 3), 3)
    return bar


@lru_cache(maxsize=1)
def _radar_face() -> pygame.Surface:
    size = RADAR_RADIUS * 2
    face = pygame.Surface((size, size), pygame.SRCALPHA)
    for r in range(RADAR_RADIUS, 0, -1):
        pygame.draw.circle(face, sprites.lerp_color((90, 200, 110), (20, 80, 40), r / RADAR_RADIUS),
                           (RADAR_RADIUS, RADAR_RADIUS), r)
    for k in range(0, size, 15):
        pygame.draw.line(face, (140, 230, 150), (k, 0), (k, size), 1)
        pygame.draw.line(face, (140, 230, 150), (0, k), (size, k), 1)
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255), (RADAR_RADIUS, RADAR_RADIUS), RADAR_RADIUS)
    face.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    case = pygame.Surface((size + 24, size + 34), pygame.SRCALPHA)
    c = (RADAR_RADIUS + 12, RADAR_RADIUS + 22)
    pygame.draw.rect(case, (60, 60, 70), (c[0] - 9, 2, 18, 14), border_radius=4)
    pygame.draw.rect(case, (200, 200, 210), (c[0] - 7, 4, 14, 10), border_radius=3)
    pygame.draw.circle(case, (60, 60, 70), c, RADAR_RADIUS + 11)
    pygame.draw.circle(case, (210, 215, 225), c, RADAR_RADIUS + 9)
    pygame.draw.circle(case, (150, 155, 170), c, RADAR_RADIUS + 3)
    case.blit(face, face.get_rect(center=c))
    return case


class Hud:
    def __init__(self):
        self.time = 0.0
        self._flash: dict[int, float] = {}

    def notify_collect(self, stars: int) -> None:
        self._flash[stars - 1] = SLOT_FLASH_TIME

    def update(self, dt: float) -> None:
        self.time += dt
        self._flash = {i: t - dt for i, t in self._flash.items() if t - dt > 0}

    def draw(self, surface: pygame.Surface, session: Session, best: int, paused: bool = False,
             show_radar: bool = True, show_collected: bool = True) -> None:
        surface.blit(_bar_background(), (0, 0))
        self._draw_score(surface, session.score, best)
        collected = session.collected if show_collected else []
        self.draw_balls(surface, collected, None if session.ball is None else session.ball.stars)
        self._draw_status(surface, session, paused)
        if show_radar:
            self._draw_radar(surface, session)

    def _draw_score(self, surface, score: int, best: int) -> None:
        text.draw(surface, "PONTOS", 20, cfg.GOLD, topleft=(16, 8))
        text.draw(surface, f"{score:06d}", 34, cfg.WHITE, topleft=(16, 26))
        text.draw(surface, "RECORDE", 20, cfg.GOLD, topleft=(150, 8))
        text.draw(surface, f"{max(best, score):06d}", 34, (200, 200, 220), topleft=(150, 26))

    def draw_balls(self, surface, collected: list[int], target: int | None) -> None:
        for index in range(cfg.TOTAL_BALLS):
            stars = index + 1
            center = slot_center(index)
            if stars in collected:
                halo = sprites.glow(24, (120, 70, 0))
                surface.blit(halo, halo.get_rect(center=center), special_flags=pygame.BLEND_RGB_ADD)
                image = sprites.dragon_ball(stars, SLOT_RADIUS)
                flash = self._flash.get(index, 0.0)
                if flash > 0:
                    image = pygame.transform.rotozoom(image, 0, 1 + 0.8 * flash / SLOT_FLASH_TIME)
            else:
                image = sprites.dragon_ball_inactive(stars, SLOT_RADIUS)
            surface.blit(image, image.get_rect(center=center))
            if stars == target:
                pulse = 0.5 + 0.5 * math.sin(self.time * 6)
                pygame.draw.circle(surface, sprites.scale_color(cfg.ORANGE, 0.5 + pulse * 0.5), center,
                                   SLOT_RADIUS + 3 + int(pulse * 2), 2)

    def _draw_status(self, surface, session: Session, paused: bool) -> None:
        x = 730
        if paused:
            if int(self.time * 2) % 2 == 0:
                text.draw(surface, "II  PAUSADO", 26, cfg.GOLD, topleft=(x, 10))
        else:
            text.draw(surface, f"NÍVEL {session.level}", 26, cfg.WHITE, topleft=(x, 10))
            text.draw(surface, f"VEL {session.speed:4.1f}", 22, (190, 200, 230), topleft=(x + 110, 13))
        text.draw(surface, "KI", 22, cfg.KI_BLUE, topleft=(x, 38))
        bar = pygame.Rect(x + 30, 40, 180, 12)
        pygame.draw.rect(surface, (10, 10, 30), bar, border_radius=6)
        fill = bar.copy()
        fill.width = int(bar.width * session.ki / cfg.KI_MAX)
        if fill.width > 0:
            color = cfg.WHITE if session.boosting and int(self.time * 12) % 2 else cfg.KI_BLUE
            pygame.draw.rect(surface, color, fill, border_radius=6)
        pygame.draw.rect(surface, (200, 220, 255), bar, 1, border_radius=6)

    def _draw_radar(self, surface, session: Session) -> None:
        case = _radar_face()
        center = Vector2(RADAR_CENTER)
        surface.blit(case, case.get_rect(center=(center.x, center.y - 5)))

        sweep = Vector2(RADAR_RADIUS - 4, 0).rotate(self.time * 140)
        pygame.draw.line(surface, (200, 255, 200), center, center + sweep, 2)

        angle = -direction_angle(session.dragon.direction)
        triangle = [center + Vector2(8, 0).rotate(angle), center + Vector2(-5, 5).rotate(angle),
                    center + Vector2(-5, -5).rotate(angle)]
        pygame.draw.polygon(surface, cfg.WHITE, triangle)

        if session.ball is None:
            return
        head = Vector2(session.dragon.head)
        relative = (Vector2(session.ball.cell) - head) * (RADAR_RADIUS * 0.85 / RADAR_RANGE)
        out_of_range = relative.length() > RADAR_RADIUS - 8
        if out_of_range:
            relative.scale_to_length(RADAR_RADIUS - 8)
        blink = int(self.time * (6 if out_of_range else 3)) % 2 == 0
        if blink or not out_of_range:
            blip = center + relative
            halo = sprites.glow(12, (200, 120, 0))
            surface.blit(halo, halo.get_rect(center=blip), special_flags=pygame.BLEND_RGB_ADD)
            pygame.draw.circle(surface, cfg.GOLD if blink else cfg.ORANGE, blip, 5)
            pygame.draw.circle(surface, (120, 40, 0), blip, 5, 1)
