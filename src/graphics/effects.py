from __future__ import annotations

import math
import random
from dataclasses import dataclass

import pygame

from . import sprites
from ..ui import text

MAX_PARTICLES = 1500


@dataclass(slots=True)
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    size: float
    color: tuple
    gravity: float = 0.0
    drag: float = 1.5


class ParticleSystem:
    def __init__(self):
        self.particles: list[Particle] = []

    def burst(self, x, y, count, color, speed=(60, 220), life=(0.4, 1.0), size=(3, 6),
              gravity=0.0, angle=0.0, spread=math.tau, drag=1.5):
        for _ in range(count):
            if len(self.particles) >= MAX_PARTICLES:
                return
            a = angle + random.uniform(-spread / 2, spread / 2)
            v = random.uniform(*speed)
            lifetime = random.uniform(*life)
            self.particles.append(Particle(
                x, y, math.cos(a) * v, math.sin(a) * v, lifetime, lifetime,
                random.uniform(*size), color, gravity, drag))

    def update(self, dt: float) -> None:
        alive = []
        for p in self.particles:
            p.life -= dt
            if p.life <= 0:
                continue
            damping = math.exp(-p.drag * dt)
            p.vx *= damping
            p.vy = p.vy * damping + p.gravity * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            alive.append(p)
        self.particles = alive

    def draw(self, surface: pygame.Surface, offset=(0, 0)) -> None:
        ox, oy = offset
        for p in self.particles:
            radius = max(1, int(p.size * (p.life / p.max_life) * 2))
            g = sprites.glow(radius, p.color)
            surface.blit(g, (p.x - ox - radius, p.y - oy - radius), special_flags=pygame.BLEND_RGB_ADD)


@dataclass(slots=True)
class Shockwave:
    x: float
    y: float
    color: tuple
    max_radius: float = 90
    duration: float = 0.5
    age: float = 0.0

    def draw(self, surface, offset):
        t = self.age / self.duration
        eased = 1 - (1 - t) ** 3
        radius = int(4 + eased * self.max_radius)
        width = max(1, int(8 * (1 - t)))
        ring = pygame.Surface((radius * 2 + 2, radius * 2 + 2))
        pygame.draw.circle(ring, sprites.scale_color(self.color, 1 - t), (radius + 1, radius + 1), radius, width)
        surface.blit(ring, (self.x - offset[0] - radius - 1, self.y - offset[1] - radius - 1),
                     special_flags=pygame.BLEND_RGB_ADD)


@dataclass(slots=True)
class FloatingText:
    x: float
    y: float
    message: str
    color: tuple
    size: int = 28
    duration: float = 1.1
    age: float = 0.0

    def draw(self, surface, offset):
        t = self.age / self.duration
        label = text.outlined(self.message, self.size, self.color).copy()
        label.set_alpha(int(255 * (1 - t ** 2)))
        rect = label.get_rect(center=(self.x - offset[0], self.y - offset[1] - 50 * t))
        surface.blit(label, rect)


class EffectsLayer:
    def __init__(self):
        self.particles = ParticleSystem()
        self.timed: list = []

    def shockwave(self, x, y, color, max_radius=90, duration=0.5):
        self.timed.append(Shockwave(x, y, color, max_radius, duration))

    def floating_text(self, x, y, message, color, size=28):
        self.timed.append(FloatingText(x, y, message, color, size))

    def update(self, dt: float) -> None:
        self.particles.update(dt)
        for effect in self.timed:
            effect.age += dt
        self.timed = [e for e in self.timed if e.age < e.duration]

    def draw(self, surface: pygame.Surface, offset=(0, 0)) -> None:
        for effect in self.timed:
            if isinstance(effect, Shockwave):
                effect.draw(surface, offset)
        self.particles.draw(surface, offset)
        for effect in self.timed:
            if isinstance(effect, FloatingText):
                effect.draw(surface, offset)
