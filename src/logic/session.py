from __future__ import annotations

import random
from dataclasses import dataclass, field

from .. import settings as cfg
from .arena import Arena, Rock
from .dragon import Dragon
from .grid import RIGHT, Cell, Direction

COLLECTED = "collected"
LEVEL_UP = "level_up"
DEATH = "death"
VICTORY = "victory"

HIT_SELF = "self"
HIT_ROCK = "rock"
HIT_WALL = "wall"

DEATH_MESSAGES = {
    HIT_SELF: "O dragão se enroscou no próprio corpo!",
    HIT_ROCK: "O dragão colidiu com uma rocha!",
    HIT_WALL: "O dragão atingiu a barreira de energia!",
}


@dataclass
class DragonBall:
    stars: int
    cell: Cell
    spawned_at: float = 0.0


@dataclass
class Event:
    kind: str
    data: dict = field(default_factory=dict)


class Session:
    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()
        self.arena = Arena(cfg.GRID_COLS, cfg.GRID_ROWS)
        start: Cell = (cfg.GRID_COLS // 4, cfg.GRID_ROWS // 2)
        self.dragon = Dragon(start, RIGHT, cfg.START_LENGTH)

        self.collected: list[int] = []
        self.score = 0
        self.elapsed = 0.0
        self.ki = cfg.KI_MAX
        self.boost_requested = False
        self.ki_exhausted = False
        self.outcome: str | None = None
        self.death_reason: str | None = None
        self._step_fraction = 0.0

        self.arena.spawn_rocks(cfg.INITIAL_ROCKS, self.rng, self.dragon.segments,
                               self.dragon.head, self.dragon.planned_directions())
        self.ball: DragonBall | None = self._spawn_ball(1)

    @property
    def level(self) -> int:
        return min(len(self.collected) + 1, cfg.TOTAL_BALLS)

    @property
    def boosting(self) -> bool:
        return self.boost_requested and not self.ki_exhausted

    @property
    def base_speed(self) -> float:
        return cfg.BASE_SPEED + cfg.SPEED_PER_BALL * len(self.collected)

    @property
    def speed(self) -> float:
        return self.base_speed * (cfg.KI_BOOST_MULTIPLIER if self.boosting else 1.0)

    @property
    def step_progress(self) -> float:
        return min(self._step_fraction, 1.0)

    @property
    def progress(self) -> float:
        return len(self.collected) / cfg.TOTAL_BALLS

    def time_bonus(self) -> int:
        if self.ball is None:
            return 0
        waited = self.elapsed - self.ball.spawned_at
        return max(0, int(cfg.TIME_BONUS_MAX - cfg.TIME_BONUS_DECAY * waited))

    def queue_turn(self, direction: Direction) -> bool:
        return self.outcome is None and self.dragon.queue_turn(direction)

    def set_boost(self, active: bool) -> None:
        self.boost_requested = active

    def update(self, dt: float) -> list[Event]:
        if self.outcome:
            return []
        self.elapsed += dt
        self._step_fraction += dt * self.speed
        self._update_ki(dt)
        events: list[Event] = []
        while self._step_fraction >= 1.0 and not self.outcome:
            self._step_fraction -= 1.0
            events.extend(self.tick())
        return events

    def _update_ki(self, dt: float) -> None:
        if self.boosting:
            self.ki = max(0.0, self.ki - cfg.KI_DRAIN * dt)
            self.ki_exhausted = self.ki <= 0
        else:
            self.ki = min(cfg.KI_MAX, self.ki + cfg.KI_REGEN * dt)
            if self.ki >= cfg.KI_MIN_TO_REBOOST:
                self.ki_exhausted = False

    def tick(self) -> list[Event]:
        if self.outcome:
            return []
        target = self.dragon.next_head()
        reason = self.collision_at(target)
        if reason:
            self.outcome = DEATH
            self.death_reason = reason
            self._step_fraction = 1.0
            return [Event(DEATH, {"reason": reason, "cell": target})]

        self.dragon.step()
        if self.ball and target == self.ball.cell:
            return self._collect()
        return []

    def collision_at(self, cell: Cell) -> str | None:
        if not self.arena.in_bounds(cell):
            return HIT_WALL
        if self.arena.is_rock(cell):
            return HIT_ROCK
        if cell in self.dragon.blocking_cells():
            return HIT_SELF
        return None

    def _collect(self) -> list[Event]:
        ball = self.ball
        points = cfg.BALL_BASE_POINTS * ball.stars + self.time_bonus()
        self.score += points
        self.collected.append(ball.stars)
        self.dragon.grow(cfg.GROWTH_PER_BALL)
        self.ki = min(cfg.KI_MAX, self.ki + cfg.KI_REFILL_ON_COLLECT)
        self.ki_exhausted = self.ki_exhausted and self.ki < cfg.KI_MIN_TO_REBOOST
        events = [Event(COLLECTED, {"stars": ball.stars, "cell": ball.cell, "points": points})]

        if len(self.collected) == cfg.TOTAL_BALLS:
            self.score += cfg.VICTORY_BONUS
            self.outcome = VICTORY
            self.ball = None
            events.append(Event(VICTORY, {"bonus": cfg.VICTORY_BONUS}))
            return events

        new_rocks = self._spawn_level_rocks()
        self.ball = self._spawn_ball(ball.stars + 1)
        events.append(Event(LEVEL_UP, {"level": self.level, "rocks": new_rocks}))
        return events

    def _spawn_level_rocks(self) -> list[Rock]:
        return self.arena.spawn_rocks(
            cfg.ROCKS_PER_BALL, self.rng, self.dragon.segments, self.dragon.head,
            self.dragon.planned_directions(), born_at=self.elapsed,
        )

    def _spawn_ball(self, stars: int) -> DragonBall:
        cell = self.arena.find_ball_cell(self.rng, self.dragon.segments, self.dragon.head)
        return DragonBall(stars, cell, spawned_at=self.elapsed)
