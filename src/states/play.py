from __future__ import annotations

import random

import pygame

from ..graphics.scene import GameScene
from ..logic import session as rules
from ..logic.grid import DOWN, LEFT, RIGHT, UP
from ..ui.hud import Hud
from .base import State
from .defeat import DefeatState
from .pause import PauseState
from .victory import VictoryState

KEY_DIRECTIONS = {
    pygame.K_UP: UP, pygame.K_w: UP,
    pygame.K_DOWN: DOWN, pygame.K_s: DOWN,
    pygame.K_LEFT: LEFT, pygame.K_a: LEFT,
    pygame.K_RIGHT: RIGHT, pygame.K_d: RIGHT,
}
BOOST_KEYS = (pygame.K_SPACE, pygame.K_LSHIFT, pygame.K_RSHIFT)
PAUSE_KEYS = (pygame.K_ESCAPE, pygame.K_p)

EVENT_SOUNDS = {rules.COLLECTED: "collect", rules.LEVEL_UP: "level_up", rules.DEATH: "death"}


class PlayState(State):
    def __init__(self, game, seed: int | None = None):
        super().__init__(game)
        self.session = rules.Session(random.Random(seed))
        self.scene = GameScene(self.session)
        self.hud = Hud()

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in KEY_DIRECTIONS:
                self.session.queue_turn(KEY_DIRECTIONS[event.key])
            elif event.key in PAUSE_KEYS:
                self.game.audio.play("select")
                self.game.change_state(PauseState(self.game, self))
            elif event.key == pygame.K_m:
                self.game.audio.toggle_mute()
        elif event.type == pygame.WINDOWFOCUSLOST:
            self.game.change_state(PauseState(self.game, self))

    def update(self, dt: float) -> None:
        pressed = pygame.key.get_pressed()
        self.session.set_boost(any(pressed[k] for k in BOOST_KEYS))
        events = self.session.update(dt)
        self._react(events)
        self.scene.update(dt)
        self.hud.update(dt)

        if self.session.outcome == rules.VICTORY:
            self.game.change_state(VictoryState(self.game, self))
        elif self.session.outcome == rules.DEATH:
            self.game.change_state(DefeatState(self.game, self))

    def _react(self, events: list[rules.Event]) -> None:
        self.scene.handle_events(events)
        for event in events:
            if event.kind in EVENT_SOUNDS:
                self.game.audio.play(EVENT_SOUNDS[event.kind])
            if event.kind == rules.COLLECTED:
                self.hud.notify_collect(event.data["stars"])

    def draw(self, surface, paused: bool = False) -> None:
        self.scene.draw(surface)
        self.hud.draw(surface, self.session, self.game.highscore.best, paused=paused)
