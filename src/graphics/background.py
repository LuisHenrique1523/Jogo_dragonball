from __future__ import annotations

import random

import pygame

from . import sprites

SKY_PALETTES = [
    ((70, 150, 235), (175, 220, 255)),
    ((90, 110, 200), (255, 190, 140)),
    ((70, 50, 130), (250, 120, 80)),
    ((15, 15, 50), (60, 50, 110)),
]
PALETTE_STEPS = 32
CLOUD_LAYERS = (
    (0.25, 150, 7, 150),
    (0.55, 230, 5, 205),
)


def sky_colors(progress: float):
    position = max(0.0, min(1.0, progress)) * (len(SKY_PALETTES) - 1)
    index = min(int(position), len(SKY_PALETTES) - 2)
    t = position - index
    (top_a, bottom_a), (top_b, bottom_b) = SKY_PALETTES[index], SKY_PALETTES[index + 1]
    return sprites.lerp_color(top_a, top_b, t), sprites.lerp_color(bottom_a, bottom_b, t)


class SkyBackground:
    def __init__(self, size: tuple[int, int], seed: int = 7):
        self.width, self.height = size
        rng = random.Random(seed)
        self.wrap = self.width + 400
        self.layers = []
        for factor, cloud_width, count, alpha in CLOUD_LAYERS:
            clouds = [(rng.uniform(0, self.wrap), rng.uniform(0, self.height + 200),
                       sprites.cloud(cloud_width + rng.randint(-40, 40), rng.randrange(999), alpha))
                      for _ in range(count)]
            self.layers.append((factor, clouds))
        self.stars = [(rng.uniform(0, self.wrap), rng.uniform(0, self.height), rng.choice((1, 1, 2)))
                      for _ in range(90)]
        self.progress = 0.0
        self._tinted: dict = {}

    def set_progress(self, progress: float, dt: float) -> None:
        self.progress += (progress - self.progress) * min(1.0, dt * 1.5)

    def _step(self) -> float:
        return round(self.progress * PALETTE_STEPS) / PALETTE_STEPS

    def _gradient(self) -> pygame.Surface:
        top, bottom = sky_colors(self._step())
        return sprites.vertical_gradient(self.width, self.height, top, bottom)

    def _cloud_image(self, image: pygame.Surface) -> pygame.Surface:
        step = self._step()
        key = (id(image), step)
        if key not in self._tinted:
            tinted = image.copy()
            tinted.fill(sprites.lerp_color((255, 255, 255), (110, 100, 165), step), special_flags=pygame.BLEND_RGB_MULT)
            self._tinted[key] = tinted
        return self._tinted[key]

    def draw(self, surface: pygame.Surface, camera_offset=(0, 0), time: float = 0.0) -> None:
        surface.blit(self._gradient(), (0, 0))
        ox, oy = camera_offset

        star_alpha = max(0.0, (self.progress - 0.45) / 0.55)
        if star_alpha > 0:
            twinkle_base = int(200 * star_alpha)
            for i, (x, y, r) in enumerate(self.stars):
                sx = (x - ox * 0.08) % self.wrap - 200
                sy = (y - oy * 0.08) % self.height
                bright = twinkle_base * (0.6 + 0.4 * abs(((time * 0.7 + i * 0.37) % 2) - 1))
                c = int(bright)
                pygame.draw.circle(surface, (c, c, min(255, c + 30)), (sx, sy), r)

        for factor, clouds in self.layers:
            for x, y, image in clouds:
                sx = (x - ox * factor + time * 12 * factor) % self.wrap - 200
                sy = (y - oy * factor) % (self.height + 200) - 120
                surface.blit(self._cloud_image(image), (sx, sy))
