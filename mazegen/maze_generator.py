"""Generate connected perfect or braided mazes using four wall bits."""

import random

from .config import Config
from .pattern import find_42_cells
from .union_find import DisjointSet
from .walls import DIRECTIONS, Wall


class MazeGenerator:
    """Generate a perfect or braided maze from a validated configuration."""

    def __init__(self, config: Config) -> None:
        """Store configuration and initialise generation state."""
        self._config = config
        self._height = config.height
        self._width = config.width
        self._rng = random.Random(config.seed)
        self._maze: list[list[int]] = []
        self._blocked: set[tuple[int, int]] = set()
        self._sets = DisjointSet([])
        self._cells: dict[tuple[int, int], None] = {}
        self._edges: list[tuple[tuple[int, int], tuple[int, int]]] = []
        self._cycles = 0

    def generate(self) -> list[list[int]]:
        """Generate and validate a maze, retrying unsuccessful layouts."""
        self._blocked = find_42_cells(self._config)
        for _ in range(30):
            self._reset()
            if (not self._config.perfect and len(self._edges)
                    - len(self._cells) + 1 < 2):
                raise ValueError(
                    "Maze graph cannot support the required number of loops")
            self._kruskal()
            if not self._is_valid():
                continue
            if self._config.perfect:
                return self._maze
            self._prune()

            for a, b in self._edges:
                if self._cycles >= 2:
                    break
                self._try_loop(a, b)

            if self._is_qualified() and self._is_valid():
                return self._maze
        raise ValueError(
            "Could not build a board with two loops and at most two "
            "dead ends after 30 attempts. Try another seed "
            "or a larger size.")

    def _reset(self) -> None:
        """Reset walls and Union-Find, retaining the chosen pattern."""
        self._maze = [
            [Wall.ALL] * self._width for _ in range(self._height)
        ]
        cells = [
            (row, col)
            for row in range(self._height)
            for col in range(self._width)
            if (row, col) not in self._blocked
        ]
        self._cells = dict.fromkeys(cells)
        self._sets = DisjointSet(cells)
        self._edges = []
        for cell in cells:
            row, col = cell
            right = (row, col + 1)
            down = (row + 1, col)
            if right in self._cells:
                self._edges.append((cell, right))
            if down in self._cells:
                self._edges.append((cell, down))
        self._cycles = 0

    def _kruskal(self) -> None:
        """Build a spanning tree with Randomized Kruskal."""
        self._rng.shuffle(self._edges)
        for a, b in self._edges:
            if self._sets.union(a, b):
                self._open_wall(a, b)

    def _open_wall(self, a: tuple[int, int], b: tuple[int, int]) -> None:
        """Clear both sides of a shared wall between ordinary cells."""
        wall, opposite = self._wall_pair(a, b)
        self._maze[a[0]][a[1]] &= ~int(wall)
        self._maze[b[0]][b[1]] &= ~int(opposite)

    def _wall_pair(
        self, a: tuple[int, int], b: tuple[int, int]
    ) -> tuple[Wall, Wall]:
        """Return the two wall bits separating adjacent cells."""
        offset = (b[0] - a[0], b[1] - a[1])
        for dr, dc, wall, opposite, _ in DIRECTIONS:
            if offset == (dr, dc):
                return wall, opposite
        raise ValueError("Can only connect orthogonally adjacent cells")

    def _is_valid(self) -> bool:
        """Check connectivity, wall agreement, borders, and blocked cells."""
        roots = {self._sets.find(cell) for cell in self._cells}
        if self._cells and len(roots) != 1:
            return False
        for row in range(self._height):
            for col in range(self._width):
                value = self._maze[row][col]
                if (row, col) in self._blocked and value != int(Wall.ALL):
                    return False
                if row == 0 and not value & Wall.NORTH:
                    return False
                if col == 0 and not value & Wall.WEST:
                    return False
                if row == self._height - 1 and not value & Wall.SOUTH:
                    return False
                if col == self._width - 1 and not value & Wall.EAST:
                    return False
                if col + 1 < self._width:
                    right = self._maze[row][col + 1]
                    if bool(value & Wall.EAST) != bool(right & Wall.WEST):
                        return False
                if row + 1 < self._height:
                    below = self._maze[row + 1][col]
                    if bool(value & Wall.SOUTH) != bool(below & Wall.NORTH):
                        return False
        return True

    def _prune(self) -> None:
        """Try to give every dead end a second exit without large rooms."""
        dead_ends = [
            cell for cell in self._cells if self._open_count(cell) == 1
        ]
        self._rng.shuffle(dead_ends)
        for cell in dead_ends:
            if self._open_count(cell) != 1:
                continue
            row, col = cell
            candidates = []
            for dr, dc, wall, _, _ in DIRECTIONS:
                neighbor = (row + dr, col + dc)
                if (neighbor in self._cells
                        and self._maze[row][col] & wall):
                    candidates.append(neighbor)
            self._rng.shuffle(candidates)
            candidates.sort(key=lambda other: self._open_count(other) != 1)
            for neighbor in candidates:
                if self._try_loop(cell, neighbor):
                    break

    def _open_count(self, cell: tuple[int, int]) -> int:
        """Return the number of open sides for a cell."""
        value = self._maze[cell[0]][cell[1]]
        return sum(not (value & wall) for _, _, wall, _, _ in DIRECTIONS)

    def _try_loop(self, a: tuple[int, int], b: tuple[int, int]) -> bool:
        """Add a loop unless it opens a fully open 3-by-3 area."""
        wall, _ = self._wall_pair(a, b)
        old_a = self._maze[a[0]][a[1]]
        old_b = self._maze[b[0]][b[1]]
        if not (old_a & wall):
            return False
        self._open_wall(a, b)
        if self._is_3x3_open(a, b):
            self._maze[a[0]][a[1]] = old_a
            self._maze[b[0]][b[1]] = old_b
            return False
        self._cycles += 1
        return True

    def _is_3x3_open(self, a: tuple[int, int], b: tuple[int, int]) -> bool:
        """Check if the changed wall creates a fully open 3x3 area."""
        def is_open(row, col):
            """ check if there is 3x3"""
            for r in range(row, row + 3):
                for c in range(col, col + 3):
                    walls = self._maze[r][c]

                    if c < col + 2 and walls & Wall.EAST:
                        return False

                    if r < row + 2 and walls & Wall.SOUTH:
                        return False
            return True

        for row in range(a[0] - 2, a[0] + 1):
            for col in range(a[1] - 2, a[1] + 1):

                if not (0 <= row <= self._height - 3):
                    continue

                if not (0 <= col <= self._width - 3):
                    continue

                if not (row <= b[0] < row + 3):
                    continue

                if not (col <= b[1] < col + 3):
                    continue

                if is_open(row, col):
                    return True

        return False

    def _is_qualified(self) -> bool:
        """Apply the minimum loops and tolerated dead-end count."""
        dead_ends = sum(
            self._open_count(cell) == 1 for cell in self._cells
        )
        if self._cycles < 2 or dead_ends > 2:
            return False
        required = {
            (0, 0), (0, self._width - 1),
            (self._height - 1, 0),
            (self._height - 1, self._width - 1),
            (self._height // 2, self._width // 2),
        }
        return all(
            cell in self._cells and self._open_count(cell) >= 2
            for cell in required
        )
