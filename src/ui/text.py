from __future__ import annotations

from functools import lru_cache

import pygame

from .. import settings as cfg
from ..graphics.sprites import vertical_gradient

OUTLINE_OFFSETS = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)]


@lru_cache(maxsize=16)
def font(size: int) -> pygame.font.Font:
    return pygame.font.Font(None, size)


@lru_cache(maxsize=512)
def outlined(message: str, size: int, color=cfg.WHITE, outline_color=cfg.DARK, thickness: int = 2) -> pygame.Surface:
    f = font(size)
    inner = f.render(message, True, color)
    outer = f.render(message, True, outline_color)
    w, h = inner.get_width() + thickness * 2, inner.get_height() + thickness * 2
    surface = pygame.Surface((w, h), pygame.SRCALPHA)
    for dx, dy in OUTLINE_OFFSETS:
        surface.blit(outer, (thickness + dx * thickness, thickness + dy * thickness))
    surface.blit(inner, (thickness, thickness))
    return surface


@lru_cache(maxsize=16)
def gradient_title(message: str, size: int, top=cfg.GOLD, bottom=cfg.DEEP_ORANGE, outline_color=(70, 20, 0)) -> pygame.Surface:
    f = font(size)
    mask = f.render(message, True, cfg.WHITE).convert_alpha()
    gradient = vertical_gradient(mask.get_width(), mask.get_height(), top, bottom)
    fill = mask.copy()
    fill.blit(gradient, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    thickness = max(3, size // 18)
    outline = f.render(message, True, outline_color)
    surface = pygame.Surface((mask.get_width() + thickness * 2, mask.get_height() + thickness * 2), pygame.SRCALPHA)
    for dx in range(-thickness, thickness + 1, max(1, thickness // 2)):
        for dy in range(-thickness, thickness + 1, max(1, thickness // 2)):
            surface.blit(outline, (thickness + dx, thickness + dy))
    surface.blit(fill, (thickness, thickness))
    return surface


def reset_cache() -> None:
    for cached in (font, outlined, gradient_title):
        cached.cache_clear()


def draw(surface, message, size, color=cfg.WHITE, **anchor) -> pygame.Rect:
    label = outlined(message, size, color)
    rect = label.get_rect(**anchor)
    surface.blit(label, rect)
    return rect


def panel(surface, rect, alpha: int = 215, border=cfg.ORANGE) -> None:
    rect = pygame.Rect(rect)
    box = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(box, (*cfg.NAVY, alpha), box.get_rect(), border_radius=18)
    pygame.draw.rect(box, (*border, 255), box.get_rect(), 3, border_radius=18)
    pygame.draw.rect(box, (255, 255, 255, 40), box.get_rect().inflate(-10, -10), 1, border_radius=14)
    surface.blit(box, rect)


def overlay(surface, color=(0, 0, 0), alpha: int = 140) -> None:
    shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    shade.fill((*color, alpha))
    surface.blit(shade, (0, 0))
