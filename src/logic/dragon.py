from __future__ import annotations

from .grid import Cell, Direction, add, opposite

MAX_QUEUED_TURNS = 2


class Dragon:
    def __init__(self, head: Cell, direction: Direction, length: int):
        dx, dy = direction
        self.segments: list[Cell] = [(head[0] - dx * i, head[1] - dy * i) for i in range(length)]
        self.previous_segments: list[Cell] = list(self.segments)
        self.direction: Direction = direction
        self.previous_direction: Direction = direction
        self.pending_growth = 0
        self._turn_queue: list[Direction] = []

    @property
    def head(self) -> Cell:
        return self.segments[0]

    def __len__(self) -> int:
        return len(self.segments)

    def queue_turn(self, direction: Direction) -> bool:
        last = self._turn_queue[-1] if self._turn_queue else self.direction
        if direction in (last, opposite(last)) or len(self._turn_queue) >= MAX_QUEUED_TURNS:
            return False
        self._turn_queue.append(direction)
        return True

    def planned_directions(self) -> list[Direction]:
        return [self.direction, *self._turn_queue]

    def next_direction(self) -> Direction:
        return self._turn_queue[0] if self._turn_queue else self.direction

    def next_head(self) -> Cell:
        return add(self.head, self.next_direction())

    def blocking_cells(self) -> set[Cell]:
        body = self.segments if self.pending_growth > 0 else self.segments[:-1]
        return set(body)

    def step(self) -> None:
        self.previous_segments = list(self.segments)
        self.previous_direction = self.direction
        if self._turn_queue:
            self.direction = self._turn_queue.pop(0)
        self.segments.insert(0, add(self.head, self.direction))
        if self.pending_growth > 0:
            self.pending_growth -= 1
        else:
            self.segments.pop()

    def grow(self, amount: int) -> None:
        self.pending_growth += amount
