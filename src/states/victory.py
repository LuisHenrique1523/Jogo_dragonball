from __future__ import annotations

import math
import random
from functools import lru_cache

import pygame
from pygame import Vector2

from .. import settings as cfg
from ..graphics import sprites
from ..graphics.dragon_renderer import DragonRenderer, tangent_angle
from ..graphics.effects import EffectsLayer
from ..ui import text
from ..ui.hud import SLOT_RADIUS, slot_center
from .end_screen import EndScreenState

RISE_START = 1.5
CHARGE_START = 3.0
SUMMON_TIME = 5.5
TITLE_TIME = 6.6
PANEL_TIME = 8.5
REVEAL_DURATION = 2.6

CENTER = Vector2(cfg.SCREEN_WIDTH / 2, 340)
GROUND_CENTER = Vector2(cfg.SCREEN_WIDTH / 2, 600)
RING_RADIUS = 110
SUMMON_BALL_RADIUS = 22
GIANT_SEGMENTS = 56
GIANT_SPACING = 0.018
GIANT_SCALE = 2.2
FIREWORK_COLORS = (cfg.GOLD, cfg.ORANGE, cfg.KI_BLUE, cfg.WHITE)


def smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def phase(time: float, start: float, duration: float) -> float:
    return max(0.0, min(1.0, (time - start) / duration))


@lru_cache(maxsize=1)
def light_beam() -> pygame.Surface:
    width, height = 160, cfg.SCREEN_HEIGHT
    beam = pygame.Surface((width, height))
    for x in range(width):
        falloff = (1 - abs(x - width / 2) / (width / 2)) ** 2
        pygame.draw.line(beam, sprites.scale_color((255, 220, 140), falloff), (x, 0), (x, height))
    return beam


def lightning_points(rng: random.Random, start: Vector2, end: Vector2, segments: int = 10):
    direction = end - start
    normal = Vector2(-direction.y, direction.x).normalize()
    points = [start]
    for i in range(1, segments):
        t = i / segments
        points.append(start + direction * t + normal * rng.uniform(-28, 28))
    points.append(end)
    return points


PANEL_RECT = pygame.Rect(cfg.SCREEN_WIDTH // 2 - 260, 305, 520, 250)


class VictoryState(EndScreenState):
    panel_time = PANEL_TIME

    def __init__(self, game, play_state):
        super().__init__(game, play_state, options_y=PANEL_RECT.top + 164)
        self.rng = random.Random()
        self.effects = EffectsLayer()
        self.giant = DragonRenderer()
        self.lightning: list | None = None
        self.lightning_timer = 0.0
        self.flash = 0.0
        self.fired: set[str] = set()

    def _once(self, name: str, at: float) -> bool:
        if self.time >= at and name not in self.fired:
            self.fired.add(name)
            return True
        return False

    def update(self, dt: float) -> None:
        super().update(dt)
        self.effects.update(dt)
        self.giant.update(dt)
        self.flash = max(0.0, self.flash - dt * 1.2)

        if self._once("summon_sound", CHARGE_START):
            self.game.audio.play("summon")
        if self._once("summon", SUMMON_TIME):
            self.flash = 1.0
            self.game.audio.play("victory")
            self.effects.particles.burst(CENTER.x, CENTER.y, 200, cfg.GOLD, speed=(150, 500), life=(0.8, 1.6))

        self._update_lightning(dt)
        if CHARGE_START <= self.time < SUMMON_TIME:
            self._converging_particles()
        if self.time >= SUMMON_TIME and self.rng.random() < dt * 2.5:
            self._firework()

    def _update_lightning(self, dt: float) -> None:
        self.lightning_timer -= dt
        if self.lightning_timer <= 0:
            self.lightning = None
            active = self.time < SUMMON_TIME + 1.5
            if active and self.rng.random() < 0.35:
                x = self.rng.uniform(80, cfg.SCREEN_WIDTH - 80)
                start = Vector2(x, cfg.HUD_HEIGHT)
                end = Vector2(x + self.rng.uniform(-120, 120), self.rng.uniform(260, 420))
                self.lightning = lightning_points(self.rng, start, end)
            self.lightning_timer = self.rng.uniform(0.08, 0.3)

    def _converging_particles(self) -> None:
        angle = self.rng.uniform(0, math.tau)
        start = CENTER + Vector2(math.cos(angle), math.sin(angle)) * 260
        towards = math.atan2(CENTER.y - start.y, CENTER.x - start.x)
        self.effects.particles.burst(start.x, start.y, 3, cfg.GOLD, speed=(220, 300), life=(0.7, 0.9),
                                     angle=towards, spread=0.2, drag=0.2)

    def _firework(self) -> None:
        x = self.rng.uniform(100, cfg.SCREEN_WIDTH - 100)
        y = self.rng.uniform(110, 300)
        color = self.rng.choice(FIREWORK_COLORS)
        self.effects.particles.burst(x, y, 60, color, speed=(60, 260), life=(0.6, 1.3), gravity=90)
        self.effects.shockwave(x, y, color, max_radius=70, duration=0.45)

    def draw(self, surface) -> None:
        glow = 0.4 + 0.4 * math.sin(self.time * 6) if self.time < SUMMON_TIME else 0.0
        self.scene.draw(surface, glow=glow, show_ball=False)
        self.play.hud.draw(surface, self.session, self.game.highscore.best, show_radar=False,
                           show_collected=self.time < RISE_START)

        darkness = 120 * smoothstep(self.time / RISE_START) + 90 * smoothstep(phase(self.time, SUMMON_TIME, 1.0))
        text.overlay(surface, (5, 5, 25), int(darkness))
        self._draw_lightning(surface)
        if CHARGE_START <= self.time:
            self._draw_beam(surface)
        if self.time >= SUMMON_TIME:
            self._draw_giant_dragon(surface)
        if self.time >= RISE_START:
            self._draw_balls(surface)
        self.effects.draw(surface)
        if self.flash > 0:
            text.overlay(surface, cfg.WHITE, int(255 * self.flash))
        if self.time >= TITLE_TIME:
            self._draw_title(surface)
        if self.time >= PANEL_TIME:
            self._draw_panel(surface)

    def _draw_lightning(self, surface) -> None:
        if not self.lightning:
            return
        pygame.draw.lines(surface, (150, 170, 255), False, self.lightning, 7)
        pygame.draw.lines(surface, cfg.WHITE, False, self.lightning, 3)
        text.overlay(surface, (200, 210, 255), 35)

    def _draw_beam(self, surface) -> None:
        strength = smoothstep(phase(self.time, CHARGE_START, SUMMON_TIME - CHARGE_START))
        if self.time >= SUMMON_TIME:
            strength *= 1 - phase(self.time, SUMMON_TIME, 2.0)
        if strength <= 0:
            return
        width = max(2, int(160 * strength))
        beam = pygame.transform.scale(light_beam(), (width, int(CENTER.y)))
        surface.blit(beam, beam.get_rect(midbottom=CENTER), special_flags=pygame.BLEND_RGB_ADD)
        g = sprites.glow(int(60 + 60 * strength), (255, 190, 80))
        surface.blit(g, g.get_rect(center=CENTER), special_flags=pygame.BLEND_RGB_ADD)

    def _ring_layout(self) -> tuple[Vector2, float, float]:
        if self.time < SUMMON_TIME:
            return CENTER, RING_RADIUS, 1.0
        t = smoothstep(phase(self.time, SUMMON_TIME, 1.2))
        return CENTER.lerp(GROUND_CENTER, t), RING_RADIUS + 90 * t, 1.0 - 0.75 * t

    def _ring_angle(self) -> float:
        charge = phase(self.time, CHARGE_START, SUMMON_TIME - CHARGE_START)
        return self.time * 0.6 + charge ** 2 * 9

    def _draw_balls(self, surface) -> None:
        travel = smoothstep(phase(self.time, RISE_START, CHARGE_START - RISE_START))
        center, radius, squash = self._ring_layout()
        base_angle = self._ring_angle()
        for i in range(cfg.TOTAL_BALLS):
            angle = base_angle + i * math.tau / cfg.TOTAL_BALLS
            target = center + Vector2(math.cos(angle) * radius, math.sin(angle) * radius * squash)
            pos = Vector2(slot_center(i)).lerp(target, travel)
            scale = (SLOT_RADIUS + (SUMMON_BALL_RADIUS - SLOT_RADIUS) * travel) / SUMMON_BALL_RADIUS
            pulse = 0.5 + 0.5 * math.sin(self.time * 8 + i)
            halo = sprites.glow(int(SUMMON_BALL_RADIUS * 2.2 * scale + pulse * 8), (200, 110, 0))
            surface.blit(halo, halo.get_rect(center=pos), special_flags=pygame.BLEND_RGB_ADD)
            image = pygame.transform.rotozoom(sprites.dragon_ball(i + 1, SUMMON_BALL_RADIUS), 0, scale)
            surface.blit(image, image.get_rect(center=pos))

    def _giant_path(self, s: float) -> Vector2:
        wobble = self.time * 0.8
        amplitude = 230 * (0.35 + 0.65 * (1 - max(0.0, s)))
        x = cfg.SCREEN_WIDTH / 2 + amplitude * math.sin(s * 2.6 * math.pi + wobble)
        y = 720 - s * 560
        return Vector2(x, y)

    def _draw_giant_dragon(self, surface) -> None:
        reveal = smoothstep(phase(self.time, SUMMON_TIME, REVEAL_DURATION))
        head_s = -0.15 + reveal * 1.15
        points = [self._giant_path(head_s - k * GIANT_SPACING) for k in range(GIANT_SEGMENTS)]
        angle = tangent_angle(points[0], points[1])
        self.giant.draw_path(surface, points, angle, scale=GIANT_SCALE, glow=0.3, shadow=False)
        eye_glow = sprites.glow(22, (200, 20, 20))
        forward = (points[0] - points[1]).normalize() if points[0] != points[1] else Vector2(1, 0)
        side = Vector2(-forward.y, forward.x)
        for sign in (-1, 1):
            eye = points[0] + forward * 4 * GIANT_SCALE + side * sign * 7 * GIANT_SCALE
            surface.blit(eye_glow, eye_glow.get_rect(center=eye), special_flags=pygame.BLEND_RGB_ADD)

    def _draw_title(self, surface) -> None:
        appear = smoothstep(phase(self.time, TITLE_TIME, 0.6))
        title = text.gradient_title("SHENLONG FOI INVOCADO!", 64)
        title = pygame.transform.rotozoom(title, 0, 0.6 + 0.4 * appear)
        title.set_alpha(int(255 * appear))
        surface.blit(title, title.get_rect(center=(cfg.SCREEN_WIDTH // 2, 110)))

    def _draw_panel(self, surface) -> None:
        rect = PANEL_RECT
        text.panel(surface, rect, alpha=200, border=cfg.GOLD)
        cx = rect.centerx
        text.draw(surface, "Seu desejo foi realizado: VITÓRIA!", 32, cfg.GOLD, center=(cx, rect.top + 30))
        minutes, seconds = divmod(int(self.session.elapsed), 60)
        text.draw(surface, f"Pontos: {self.session.score}  (bônus de invocação +{cfg.VICTORY_BONUS})", 24,
                  cfg.WHITE, center=(cx, rect.top + 66))
        text.draw(surface, f"Tempo: {minutes:02d}:{seconds:02d}    Tamanho final: {len(self.session.dragon)}",
                  24, cfg.WHITE, center=(cx, rect.top + 94))
        text.draw(surface, self.record_line(), 24, cfg.GOLD, center=(cx, rect.top + 122))
        self.options.draw(surface)
        text.draw(surface, "ENTER escolhe  |  R reinicia  |  ESC menu", 18, cfg.CREAM, midbottom=(cx, rect.bottom - 6))
