from __future__ import annotations

import random
from dataclasses import dataclass

from ..settings import BALL_MIN_DISTANCE, FORWARD_LANE_LENGTH, SAFE_SPAWN_DISTANCE
from .grid import Cell, Direction, add, chebyshev

ROCK_SHAPES = ((1, 1), (2, 1), (1, 2), (2, 2), (3, 2), (2, 3))
MAX_PLACEMENT_ATTEMPTS = 300


@dataclass
class Rock:
    x: int
    y: int
    w: int
    h: int
    born_at: float = -100.0
    variant: int = 0

    def cells(self) -> list[Cell]:
        return [(self.x + i, self.y + j) for i in range(self.w) for j in range(self.h)]


class Arena:
    def __init__(self, cols: int, rows: int):
        self.cols = cols
        self.rows = rows
        self.rocks: list[Rock] = []
        self._blocked: set[Cell] = set()

    def in_bounds(self, cell: Cell) -> bool:
        return 0 <= cell[0] < self.cols and 0 <= cell[1] < self.rows

    def is_rock(self, cell: Cell) -> bool:
        return cell in self._blocked

    def add_rock(self, rock: Rock) -> None:
        self.rocks.append(rock)
        self._blocked.update(rock.cells())

    def free_cells(self, occupied: set[Cell], margin: int = 0) -> list[Cell]:
        return [
            (x, y)
            for x in range(margin, self.cols - margin)
            for y in range(margin, self.rows - margin)
            if (x, y) not in self._blocked and (x, y) not in occupied
        ]

    def spawn_rocks(
        self,
        count: int,
        rng: random.Random,
        dragon_cells: list[Cell],
        head: Cell,
        directions: list[Direction],
        born_at: float = -100.0,
    ) -> list[Rock]:
        forbidden = set(dragon_cells)
        for direction in directions:
            forbidden |= self._forward_lane(head, direction)
        created = []
        for _ in range(count):
            rock = self._try_place_rock(rng, forbidden, head)
            if rock is None:
                break
            rock.born_at = born_at
            self.add_rock(rock)
            created.append(rock)
        return created

    def _forward_lane(self, head: Cell, direction: Direction) -> set[Cell]:
        lane = set()
        cell = head
        for _ in range(FORWARD_LANE_LENGTH):
            cell = add(cell, direction)
            for side in (-1, 0, 1):
                lane.add((cell[0] + side * abs(direction[1]), cell[1] + side * abs(direction[0])))
        return lane

    def _try_place_rock(self, rng: random.Random, forbidden: set[Cell], head: Cell) -> Rock | None:
        for _ in range(MAX_PLACEMENT_ATTEMPTS):
            w, h = rng.choice(ROCK_SHAPES)
            x = rng.randint(1, self.cols - 1 - w)
            y = rng.randint(1, self.rows - 1 - h)
            rock = Rock(x, y, w, h, variant=rng.randrange(1000))
            cells = rock.cells()
            if any(c in forbidden or chebyshev(c, head) < SAFE_SPAWN_DISTANCE for c in cells):
                continue
            if any(self._touches_rock(c) for c in cells):
                continue
            return rock
        return None

    def _touches_rock(self, cell: Cell) -> bool:
        x, y = cell
        return any((x + dx, y + dy) in self._blocked for dx in (-1, 0, 1) for dy in (-1, 0, 1))

    def find_ball_cell(self, rng: random.Random, dragon_cells: list[Cell], head: Cell) -> Cell:
        occupied = set(dragon_cells)
        candidates = self.free_cells(occupied, margin=1)
        far = [c for c in candidates if chebyshev(c, head) >= BALL_MIN_DISTANCE]
        return rng.choice(far or candidates)

