from __future__ import annotations

import math
import random

FOLLOW_SHARPNESS = 6.0


class Camera:
    def __init__(self, view_size: tuple[int, int], world_size: tuple[int, int]):
        self.view_w, self.view_h = view_size
        self.world_w, self.world_h = world_size
        self.x = 0.0
        self.y = 0.0
        self._shake_time = 0.0
        self._shake_strength = 0.0
        self._shake_offset = (0.0, 0.0)

    def _clamped_target(self, target: tuple[float, float]) -> tuple[float, float]:
        x = min(max(target[0] - self.view_w / 2, 0), self.world_w - self.view_w)
        y = min(max(target[1] - self.view_h / 2, 0), self.world_h - self.view_h)
        return x, y

    def snap_to(self, target: tuple[float, float]) -> None:
        self.x, self.y = self._clamped_target(target)

    def follow(self, target: tuple[float, float], dt: float) -> None:
        tx, ty = self._clamped_target(target)
        blend = 1 - math.exp(-FOLLOW_SHARPNESS * dt)
        self.x += (tx - self.x) * blend
        self.y += (ty - self.y) * blend

    def shake(self, strength: float, duration: float) -> None:
        self._shake_strength = max(self._shake_strength, strength)
        self._shake_time = max(self._shake_time, duration)

    def update(self, dt: float) -> None:
        if self._shake_time > 0:
            self._shake_time -= dt
            s = self._shake_strength
            self._shake_offset = (random.uniform(-s, s), random.uniform(-s, s))
            self._shake_strength *= math.exp(-6 * dt)
        else:
            self._shake_offset = (0.0, 0.0)

    @property
    def offset(self) -> tuple[int, int]:
        return round(self.x + self._shake_offset[0]), round(self.y + self._shake_offset[1])
