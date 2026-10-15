from __future__ import annotations

import math

Cell = tuple[int, int]
Direction = tuple[int, int]

UP: Direction = (0, -1)
DOWN: Direction = (0, 1)
LEFT: Direction = (-1, 0)
RIGHT: Direction = (1, 0)
DIRECTIONS = (UP, DOWN, LEFT, RIGHT)


def add(cell: Cell, direction: Direction) -> Cell:
    return cell[0] + direction[0], cell[1] + direction[1]


def opposite(direction: Direction) -> Direction:
    return -direction[0], -direction[1]


def chebyshev(a: Cell, b: Cell) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def direction_angle(direction: Direction) -> float:
    return math.degrees(math.atan2(-direction[1], direction[0]))
