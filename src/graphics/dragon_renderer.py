from __future__ import annotations

import math

import pygame
from pygame import Vector2

from .. import settings as cfg
from ..logic.dragon import Dragon
from ..logic.grid import direction_angle
from . import sprites

NECK_DIAMETER = 30
TAIL_DIAMETER = 14
UNDULATION_AMPLITUDE = 3.0
HEAD_FPS = 10
SHADOW_OFFSET = Vector2(7, 9)


def cell_center(cell) -> Vector2:
    return Vector2(cell[0] * cfg.CELL + cfg.CELL / 2, cell[1] * cfg.CELL + cfg.CELL / 2)


def lerp_angle(a: float, b: float, t: float) -> float:
    diff = (b - a + 180) % 360 - 180
    return a + diff * t


def interpolated_points(dragon: Dragon, alpha: float) -> list[Vector2]:
    previous = dragon.previous_segments
    points = []
    for i, cell in enumerate(dragon.segments):
        start = cell_center(previous[i] if i < len(previous) else cell)
        points.append(start.lerp(cell_center(cell), alpha))
    return points


def head_angle(dragon: Dragon, alpha: float) -> float:
    return lerp_angle(direction_angle(dragon.previous_direction), direction_angle(dragon.direction), alpha)


def tangent_angle(a: Vector2, b: Vector2) -> float:
    d = a - b
    return math.degrees(math.atan2(-d.y, d.x)) if d.length_squared() > 1e-6 else 0.0


class DragonRenderer:
    def __init__(self):
        self.time = 0.0

    def update(self, dt: float) -> None:
        self.time += dt

    def draw_dragon(self, surface, dragon: Dragon, alpha: float, offset=(0, 0), glow: float = 0.0,
                    hidden: int = 0, glow_color=cfg.GOLD) -> None:
        points = [p - Vector2(offset) for p in interpolated_points(dragon, alpha)]
        self.draw_path(surface, self._undulate(points), head_angle(dragon, alpha), glow=glow, hidden=hidden,
                       glow_color=glow_color)

    def _undulate(self, points: list[Vector2]) -> list[Vector2]:
        result = [points[0]]
        for i in range(1, len(points)):
            tangent = points[i - 1] - points[i]
            if tangent.length_squared() < 1e-6:
                result.append(points[i])
                continue
            normal = Vector2(-tangent.y, tangent.x).normalize()
            ramp = min(1.0, i / 3)
            wave = math.sin(self.time * 8 - i * 0.7) * UNDULATION_AMPLITUDE * ramp
            result.append(points[i] + normal * wave)
        return result

    def draw_path(self, surface, points: list[Vector2], angle: float, scale: float = 1.0,
                  glow: float = 0.0, hidden: int = 0, shadow: bool = True, glow_color=cfg.GOLD) -> None:
        if not points:
            return
        count = len(points)
        sizes = [self._diameter(i, count) * scale for i in range(count)]
        bodies = self._body_discs(points, sizes)
        visible = [(pos, size) for pos, size, index in bodies if index >= hidden]

        if shadow:
            for pos, size in visible:
                disc = sprites.shadow_disc(max(2, int(size)))
                surface.blit(disc, disc.get_rect(center=pos + SHADOW_OFFSET * scale))
        if glow > 0:
            color = sprites.scale_color(glow_color, round(glow, 1))
            for pos, size in visible[::2]:
                g = sprites.glow(int(size * 1.1), color)
                surface.blit(g, g.get_rect(center=pos), special_flags=pygame.BLEND_RGB_ADD)

        self._draw_claws(surface, points, sizes, hidden)
        if count > 1 and count - 1 >= hidden:
            self._draw_tail(surface, points, scale)
        for pos, size in reversed(visible):
            disc = sprites.body_segment(max(2, int(size)))
            surface.blit(disc, disc.get_rect(center=pos))
        if hidden == 0:
            frame = sprites.head_frames()[int(self.time * HEAD_FPS) % sprites.HEAD_FRAMES]
            head = pygame.transform.rotozoom(frame, angle, scale)
            surface.blit(head, head.get_rect(center=points[0]))

    @staticmethod
    def _diameter(index: int, count: int) -> float:
        if count <= 2:
            return NECK_DIAMETER
        t = (index - 1) / (count - 2) if index > 0 else 0.0
        return NECK_DIAMETER + (TAIL_DIAMETER - NECK_DIAMETER) * t

    @staticmethod
    def _body_discs(points, sizes):
        discs = []
        for i in range(1, len(points)):
            discs.append((points[i], sizes[i], i))
            joint = points[i - 1].lerp(points[i], 0.5)
            discs.append((joint, (sizes[i - 1] + sizes[i]) / 2 * 0.92, i))
        return discs

    @staticmethod
    def _draw_tail(surface, points, scale):
        tip = points[-1]
        reference = next((p for p in reversed(points[:-1]) if (tip - p).length_squared() > 1), None)
        if reference is None:
            return
        direction = (tip - reference).normalize()
        tail = pygame.transform.rotozoom(sprites.tail_tip(), tangent_angle(tip, reference), scale)
        surface.blit(tail, tail.get_rect(center=tip + direction * 10 * scale))

    def _draw_claws(self, surface, points, sizes, hidden):
        count = len(points)
        if count < 5:
            return
        for index in sorted({2, int(count * 0.6)}):
            if index < hidden or index >= count:
                continue
            base_angle = tangent_angle(points[index - 1], points[index])
            sway = math.sin(self.time * 6 + index) * 15
            for side in (-1, 1):
                angle = base_angle + side * (75 + sway * side)
                image = pygame.transform.rotozoom(sprites.claw(), angle, sizes[index] / NECK_DIAMETER)
                direction = Vector2(1, 0).rotate(-angle)
                surface.blit(image, image.get_rect(center=points[index] + direction * sizes[index] * 0.55))
