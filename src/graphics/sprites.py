from __future__ import annotations

import math
import random
from functools import lru_cache

import pygame

from .. import settings as cfg


def lerp_color(a, b, t: float):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def scale_color(color, factor: float):
    return tuple(max(0, min(255, int(c * factor))) for c in color[:3])


def star_points(cx: float, cy: float, outer: float, inner_ratio: float = 0.45, rotation: float = -90):
    points = []
    for i in range(10):
        radius = outer if i % 2 == 0 else outer * inner_ratio
        angle = math.radians(rotation + i * 36)
        points.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
    return points


@lru_cache(maxsize=1024)
def glow(radius: int, color: tuple) -> pygame.Surface:
    radius = max(1, radius)
    surface = pygame.Surface((radius * 2, radius * 2))
    for r in range(radius, 0, -1):
        intensity = (1 - r / radius) ** 2
        pygame.draw.circle(surface, scale_color(color, intensity), (radius, radius), r)
    return surface


@lru_cache(maxsize=64)
def vertical_gradient(width: int, height: int, top: tuple, bottom: tuple) -> pygame.Surface:
    column = pygame.Surface((1, height))
    for y in range(height):
        column.set_at((0, y), lerp_color(top, bottom, y / max(1, height - 1)))
    return pygame.transform.scale(column, (width, height))


STAR_LAYOUTS = {
    1: [(0, 0)],
    2: [(-0.45, -0.3), (0.45, 0.3)],
    3: [(0, -0.5), (-0.5, 0.4), (0.5, 0.4)],
    4: [(-0.45, -0.45), (0.45, -0.45), (-0.45, 0.45), (0.45, 0.45)],
    5: [(0, 0), (-0.55, -0.55), (0.55, -0.55), (-0.55, 0.55), (0.55, 0.55)],
    6: [(-0.45, -0.6), (0.45, -0.6), (-0.7, 0), (0.7, 0), (-0.45, 0.6), (0.45, 0.6)],
    7: [(0, 0), (0, -0.68), (0, 0.68), (-0.62, -0.34), (0.62, -0.34), (-0.62, 0.34), (0.62, 0.34)],
}
STAR_SIZE = {1: 0.42, 2: 0.3, 3: 0.27, 4: 0.24, 5: 0.21, 6: 0.2, 7: 0.18}


@lru_cache(maxsize=64)
def dragon_ball(stars: int, radius: int) -> pygame.Surface:
    size = radius * 2 + 2
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    center = pygame.Vector2(radius + 1, radius + 1)
    highlight = center + pygame.Vector2(-radius * 0.35, -radius * 0.35)
    edge, core = (205, 85, 0), (255, 200, 90)
    for r in range(radius, 0, -1):
        t = r / radius
        c = highlight.lerp(center, t)
        pygame.draw.circle(surface, lerp_color(core, edge, t ** 1.4), c, r)
    pygame.draw.circle(surface, (150, 60, 0), center, radius, max(1, radius // 10))

    star_radius = radius * STAR_SIZE[stars]
    for nx, ny in STAR_LAYOUTS[stars]:
        sx, sy = center.x + nx * radius * 0.62, center.y + ny * radius * 0.62
        pygame.draw.polygon(surface, cfg.STAR_RED, star_points(sx, sy, star_radius))

    shine = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.ellipse(shine, (255, 255, 255, 150),
                        (highlight.x - radius * 0.35, highlight.y - radius * 0.22, radius * 0.6, radius * 0.38))
    surface.blit(shine, (0, 0))
    return surface


@lru_cache(maxsize=16)
def dragon_ball_inactive(stars: int, radius: int) -> pygame.Surface:
    surface = pygame.transform.grayscale(dragon_ball(stars, radius))
    surface.set_alpha(110)
    return surface


HEAD_CANVAS = 84
HEAD_FRAMES = 8


def _whisker(surface, base, side: int, phase: float, length: float):
    points = []
    for i in range(12):
        t = i / 11
        x = base[0] - t * length
        y = base[1] + side * (4 + t * 14) + math.sin(phase + t * 5) * 4 * t
        points.append((x, y))
    pygame.draw.lines(surface, (255, 250, 230), False, points, 2)


def _antler(surface, base, side: int):
    color, dark = (240, 225, 180), (170, 140, 90)
    tip = (base[0] - 22, base[1] + side * 20)
    branch_from = (base[0] - 10, base[1] + side * 9)
    branch_tip = (base[0] - 6, base[1] + side * 22)
    for start, end in ((base, tip), (branch_from, branch_tip)):
        pygame.draw.line(surface, dark, start, end, 6)
        pygame.draw.line(surface, color, start, end, 4)


def _draw_head(phase: float) -> pygame.Surface:
    s = pygame.Surface((HEAD_CANVAS, HEAD_CANVAS), pygame.SRCALPHA)
    c = HEAD_CANVAS // 2
    for side in (-1, 1):
        spikes = [(c - 6, c), (c - 22, c + side * 6), (c - 14, c + side * 10),
                  (c - 26, c + side * 16), (c - 8, c + side * 14)]
        pygame.draw.polygon(s, cfg.DRAGON_DARK, spikes)
    for side in (-1, 1):
        _antler(s, (c - 4, c + side * 8), side)
    pygame.draw.ellipse(s, cfg.DRAGON_DARK, (c - 16, c - 15, 32, 30))
    pygame.draw.ellipse(s, cfg.DRAGON_GREEN, (c - 14, c - 13, 28, 26))
    pygame.draw.ellipse(s, cfg.DRAGON_DARK, (c + 2, c - 10, 28, 20))
    pygame.draw.ellipse(s, cfg.DRAGON_GREEN, (c + 3, c - 9, 26, 18))
    pygame.draw.ellipse(s, cfg.DRAGON_LIGHT, (c - 8, c - 4, 32, 8))
    for side in (-1, 1):
        pygame.draw.line(s, cfg.DRAGON_DARK, (c - 2, c + side * 11), (c + 10, c + side * 7), 3)
        pygame.draw.circle(s, (90, 0, 0), (c + 4, c + side * 7), 4)
        pygame.draw.circle(s, cfg.EYE_RED, (c + 4, c + side * 7), 3)
        pygame.draw.circle(s, (255, 200, 200), (c + 5, c + side * 6), 1)
        pygame.draw.circle(s, (20, 60, 25), (c + 26, c + side * 4), 2)
    for side in (-1, 1):
        _whisker(s, (c + 22, c + side * 7), side, phase + (0 if side < 0 else math.pi * 0.5), 34)
    return s


@lru_cache(maxsize=1)
def head_frames() -> tuple[pygame.Surface, ...]:
    return tuple(_draw_head(2 * math.pi * i / HEAD_FRAMES) for i in range(HEAD_FRAMES))


BODY_BASE = 48


@lru_cache(maxsize=1)
def _body_base() -> pygame.Surface:
    s = pygame.Surface((BODY_BASE, BODY_BASE), pygame.SRCALPHA)
    r = BODY_BASE // 2
    center = pygame.Vector2(r, r)
    light = center + pygame.Vector2(-r * 0.3, -r * 0.3)
    for i in range(r, 0, -1):
        t = i / r
        pygame.draw.circle(s, lerp_color(cfg.DRAGON_LIGHT, cfg.DRAGON_GREEN, t ** 0.8), light.lerp(center, t), i)
    pygame.draw.circle(s, cfg.DRAGON_DARK, center, r, 3)
    for k in range(8):
        angle = k * math.pi / 4
        px, py = r + math.cos(angle) * r * 0.58, r + math.sin(angle) * r * 0.58
        pygame.draw.arc(s, cfg.DRAGON_DARK, (px - 6, py - 6, 12, 12), angle + math.pi * 0.2, angle + math.pi * 1.8, 2)
    pygame.draw.circle(s, (230, 190, 90), center, r * 0.28)
    pygame.draw.circle(s, (160, 120, 40), center, r * 0.28, 2)
    return s


@lru_cache(maxsize=128)
def body_segment(diameter: int) -> pygame.Surface:
    return pygame.transform.smoothscale(_body_base(), (diameter, diameter))


@lru_cache(maxsize=1)
def tail_tip() -> pygame.Surface:
    s = pygame.Surface((44, 30), pygame.SRCALPHA)
    pygame.draw.polygon(s, cfg.DRAGON_DARK, [(0, 15), (26, 5), (26, 25)])
    pygame.draw.polygon(s, cfg.DRAGON_GREEN, [(2, 15), (24, 8), (24, 22)])
    for dy in (-7, 0, 7):
        pygame.draw.line(s, cfg.CREAM, (22, 15), (42, 15 + dy), 3)
    return s


@lru_cache(maxsize=1)
def claw() -> pygame.Surface:
    s = pygame.Surface((26, 18), pygame.SRCALPHA)
    pygame.draw.line(s, cfg.DRAGON_DARK, (0, 9), (14, 9), 6)
    pygame.draw.line(s, cfg.DRAGON_GREEN, (0, 9), (14, 9), 4)
    for dy in (-5, 0, 5):
        pygame.draw.line(s, (240, 225, 180), (13, 9), (24, 9 + dy), 2)
    return s


@lru_cache(maxsize=256)
def shadow_ellipse(width: int, height: int) -> pygame.Surface:
    s = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (0, 0, 30, 60), (0, 0, width, height))
    return s


def shadow_disc(diameter: int) -> pygame.Surface:
    return shadow_ellipse(diameter, diameter)


@lru_cache(maxsize=128)
def rock(w: int, h: int, variant: int) -> pygame.Surface:
    rng = random.Random(variant)
    pad = 6
    width, height = w * cfg.CELL + pad * 2, h * cfg.CELL + pad * 2
    s = pygame.Surface((width, height), pygame.SRCALPHA)

    def jagged(inset: int, jitter: int):
        pts = []
        cx, cy = width / 2, height / 2
        rx, ry = width / 2 - inset, height / 2 - inset
        for i in range(18):
            a = 2 * math.pi * i / 18
            px = cx + rx * math.copysign(abs(math.cos(a)) ** 0.5, math.cos(a))
            py = cy + ry * math.copysign(abs(math.sin(a)) ** 0.5, math.sin(a))
            pts.append((px + rng.randint(-jitter, jitter), py + rng.randint(-jitter, jitter)))
        return pts

    pygame.draw.polygon(s, (70, 45, 35), jagged(1, 2))
    pygame.draw.polygon(s, (135, 95, 65), jagged(4, 2))
    pygame.draw.polygon(s, (175, 135, 90), jagged(9, 2))
    grass = jagged(13, 3)
    pygame.draw.polygon(s, (95, 165, 70), grass)
    for _ in range(3 + w * h):
        x = rng.randint(pad + 6, width - pad - 6)
        y = rng.randint(pad + 6, height - pad - 6)
        pygame.draw.line(s, (90, 60, 40), (x, y), (x + rng.randint(-8, 8), y + rng.randint(-8, 8)), 2)
    for _ in range(2 * w * h):
        x = rng.randint(pad + 10, width - pad - 10)
        y = rng.randint(pad + 10, height - pad - 10)
        pygame.draw.circle(s, (130, 200, 90), (x, y), 2)
    return s


@lru_cache(maxsize=32)
def cloud(width: int, seed: int, alpha: int = 210) -> pygame.Surface:
    rng = random.Random(seed)
    height = width // 2
    s = pygame.Surface((width, height), pygame.SRCALPHA)
    puffs = [(rng.uniform(0.2, 0.8) * width, rng.uniform(0.45, 0.65) * height, rng.uniform(0.18, 0.3) * width)
             for _ in range(6)]
    for x, y, r in puffs:
        pygame.draw.circle(s, (200, 210, 235, alpha), (x, y + r * 0.15), r)
    for x, y, r in puffs:
        pygame.draw.circle(s, (255, 255, 255, alpha), (x, y - r * 0.05), r * 0.9)
    return s
