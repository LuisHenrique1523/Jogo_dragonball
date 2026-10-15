from __future__ import annotations

import math

import pygame
from pygame import Vector2

from .. import settings as cfg
from ..logic import session as rules
from ..ui import text
from . import sprites
from .background import SkyBackground
from .camera import Camera
from .dragon_renderer import DragonRenderer, cell_center, interpolated_points
from .effects import EffectsLayer

BALL_RADIUS = 13
ROCK_GROW_TIME = 0.6
BANNER_TIME = 2.4


def ease_out_back(t: float) -> float:
    c = 1.70158
    t -= 1
    return 1 + (c + 1) * t ** 3 + c * t ** 2


class Banner:
    def __init__(self, title: str, subtitle: str):
        self.title = title
        self.subtitle = subtitle
        self.age = 0.0

    @property
    def done(self) -> bool:
        return self.age >= BANNER_TIME

    def draw(self, surface: pygame.Surface) -> None:
        t = self.age / BANNER_TIME
        alpha = int(255 * min(1.0, self.age * 5, (1 - t) * 5))
        zoom = 1.0 + max(0.0, 0.25 - self.age) * 2.4
        title = pygame.transform.rotozoom(text.gradient_title(self.title, 64), 0, zoom)
        title.set_alpha(alpha)
        cx = surface.get_width() // 2
        surface.blit(title, title.get_rect(center=(cx, 150)))
        subtitle = text.outlined(self.subtitle, 28).copy()
        subtitle.set_alpha(alpha)
        surface.blit(subtitle, subtitle.get_rect(center=(cx, 200)))


def _grid_overlay() -> pygame.Surface:
    surface = pygame.Surface((cfg.WORLD_WIDTH, cfg.WORLD_HEIGHT), pygame.SRCALPHA)
    for x in range(0, cfg.WORLD_WIDTH + 1, cfg.CELL):
        for y in range(0, cfg.WORLD_HEIGHT + 1, cfg.CELL):
            pygame.draw.circle(surface, (255, 255, 255, 45), (x, y), 1)
    return surface


class GameScene:
    def __init__(self, session: rules.Session):
        self.session = session
        view_size = (cfg.VIEWPORT[2], cfg.VIEWPORT[3])
        self.camera = Camera(view_size, (cfg.WORLD_WIDTH, cfg.WORLD_HEIGHT))
        self.sky = SkyBackground(view_size)
        self.dragon_renderer = DragonRenderer()
        self.effects = EffectsLayer()
        self.grid = _grid_overlay()
        self.time = 0.0
        self.flash = 0.0
        self.banner: Banner | None = None
        self.camera.snap_to(cell_center(session.dragon.head))

    def handle_events(self, events: list[rules.Event]) -> None:
        for event in events:
            if event.kind == rules.COLLECTED:
                self._collect_effect(event.data)
            elif event.kind == rules.LEVEL_UP:
                self.banner = Banner(f"NÍVEL {event.data['level']}",
                                     "Mais velocidade... e novas rochas surgiram!")
                for rock in event.data["rocks"]:
                    center = Vector2(rock.x + rock.w / 2, rock.y + rock.h / 2) * cfg.CELL
                    self.effects.particles.burst(center.x, center.y, 25, (160, 120, 80), speed=(40, 140),
                                                 life=(0.4, 0.8), size=(3, 6), drag=3)
            elif event.kind == rules.DEATH:
                self.camera.shake(12, 0.5)
                self.flash = 0.5

    def _collect_effect(self, data: dict) -> None:
        pos = cell_center(data["cell"])
        self.effects.particles.burst(pos.x, pos.y, 70, cfg.ORANGE, speed=(80, 320), life=(0.4, 1.0))
        self.effects.particles.burst(pos.x, pos.y, 30, cfg.GOLD, speed=(30, 140), life=(0.6, 1.2), size=(4, 8))
        self.effects.shockwave(pos.x, pos.y, cfg.GOLD, max_radius=110)
        self.effects.shockwave(pos.x, pos.y, cfg.WHITE, max_radius=60, duration=0.35)
        self.effects.floating_text(pos.x, pos.y - 20, f"+{data['points']}", cfg.GOLD)
        self.camera.shake(5, 0.2)
        self.flash = 0.3

    def head_position(self) -> Vector2:
        return interpolated_points(self.session.dragon, self.session.step_progress)[0]

    def update(self, dt: float) -> None:
        self.time += dt
        self.sky.set_progress(self.session.progress, dt)
        self.dragon_renderer.update(dt)
        self.effects.update(dt)
        self.camera.follow(self.head_position(), dt)
        self.camera.update(dt)
        self.flash = max(0.0, self.flash - dt * 1.5)
        if self.banner:
            self.banner.age += dt
            if self.banner.done:
                self.banner = None
        if self.session.boosting:
            self._emit_ki_aura()

    def _emit_ki_aura(self) -> None:
        points = interpolated_points(self.session.dragon, self.session.step_progress)
        for p in points[::3]:
            self.effects.particles.burst(p.x, p.y, 1, cfg.KI_BLUE, speed=(20, 60), life=(0.3, 0.6),
                                         size=(3, 5), gravity=-80)

    def viewport(self, surface: pygame.Surface) -> pygame.Surface:
        return surface.subsurface(cfg.VIEWPORT)

    def draw(self, surface: pygame.Surface, glow: float = 0.0, hidden: int = 0, show_ball: bool = True) -> None:
        view = self.viewport(surface)
        offset = self.camera.offset
        self.sky.draw(view, offset, self.time)
        view.blit(self.grid, (-offset[0], -offset[1]))
        self._draw_barrier(view, offset)
        self._draw_rocks(view, offset)
        if show_ball and self.session.ball:
            self._draw_ball(view, offset)
        if self.session.boosting:
            glow, glow_color = max(glow, 0.6), cfg.KI_BLUE
        else:
            glow_color = cfg.GOLD
        self.dragon_renderer.draw_dragon(view, self.session.dragon, self.session.step_progress, offset,
                                         glow, hidden, glow_color)
        self.effects.draw(view, offset)
        if self.flash > 0:
            text.overlay(view, cfg.WHITE, int(180 * self.flash))
        if self.banner:
            self.banner.draw(view)

    def _draw_barrier(self, view, offset) -> None:
        pulse = 0.6 + 0.4 * math.sin(self.time * 4)
        rect = pygame.Rect(-offset[0], -offset[1], cfg.WORLD_WIDTH, cfg.WORLD_HEIGHT).inflate(-4, -4)
        pygame.draw.rect(view, sprites.scale_color(cfg.ORANGE, pulse), rect, 6, border_radius=8)
        pygame.draw.rect(view, sprites.scale_color(cfg.GOLD, pulse), rect.inflate(-10, -10), 2, border_radius=6)

    def _draw_rocks(self, view, offset) -> None:
        for rock in self.session.arena.rocks:
            image = sprites.rock(rock.w, rock.h, rock.variant)
            age = self.session.elapsed - rock.born_at
            if age < ROCK_GROW_TIME:
                image = pygame.transform.rotozoom(image, 0, max(0.05, ease_out_back(age / ROCK_GROW_TIME)))
            center = (rock.x * cfg.CELL + rock.w * cfg.CELL / 2 - offset[0],
                      rock.y * cfg.CELL + rock.h * cfg.CELL / 2 - offset[1])
            shadow = sprites.shadow_ellipse(*image.get_size())
            view.blit(shadow, shadow.get_rect(center=(center[0] + 8, center[1] + 10)))
            view.blit(image, image.get_rect(center=center))

    def _draw_ball(self, view, offset) -> None:
        ball = self.session.ball
        pos = cell_center(ball.cell) - Vector2(offset)
        pos.y += math.sin(self.time * 3) * 3
        pulse = 0.5 + 0.5 * math.sin(self.time * 5)
        halo = sprites.glow(int(30 + 8 * pulse), cfg.ORANGE)
        view.blit(halo, halo.get_rect(center=pos), special_flags=pygame.BLEND_RGB_ADD)
        age = self.session.elapsed - ball.spawned_at
        image = sprites.dragon_ball(ball.stars, BALL_RADIUS)
        if age < 0.5:
            image = pygame.transform.rotozoom(image, 0, max(0.05, ease_out_back(age / 0.5)))
        view.blit(image, image.get_rect(center=pos))
