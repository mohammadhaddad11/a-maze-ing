"""Generate connected perfect or braided mazes using four wall bits."""

import random

from .config import Config
from .pattern import find_42_cells
from .walls import DIRECTIONS, Wall


class MazeGenerator:
    """Generate a perfect or braided maze from a validated configuration."""

    MAX_ATTEMPTS = 30
    MIN_LOOPS = 2
    MAX_DEAD_ENDS = 2

    def __init__(self, config: Config) -> None:
        """Store configuration and initialise generation state."""
        self._config = config
        self._height = config.height
        self._width = config.width
        self._rng = random.Random(config.seed)
        self._maze: list[list[int]] = []
        self._blocked: set[tuple[int, int]] = set()
        self._cells: list[tuple[int, int]] = []
        self._edges: list[tuple[tuple[int, int], tuple[int, int]]] = []
        self._cycles = 0

    def generate(self) -> list[list[int]]:
        """Generate and validate a maze, retrying unsuccessful layouts."""
        self._blocked = find_42_cells(self._config)
        for _ in range(self.MAX_ATTEMPTS):
            self._reset()
            # A connected graph has E - V + 1 edges beyond a spanning tree:
            # this is its capacity for independent cycles.
            if (not self._config.perfect
                    and len(self._edges) - len(self._cells) + 1
                    < self.MIN_LOOPS):
                raise ValueError(
                    "Maze graph cannot support the required number of loops"
                )
            self._dfs()
            if not self._valid_maze():
                continue
            if self._config.perfect:
                return self._maze
            self._braid()
            self._add_loops()
            if self._playable() and self._valid_maze():
                return self._maze
        raise ValueError(
            "Could not build a board with two loops and at most two "
            f"dead ends after {self.MAX_ATTEMPTS} attempts. Try another seed "
            "or a larger size."
        )

    def _reset(self) -> None:
        """Reset walls and collect the unblocked cells and possible edges."""
        self._maze = [
            [int(Wall.ALL)] * self._width for _ in range(self._height)
        ]
        cells = [
            (row, col)
            for row in range(self._height)
            for col in range(self._width)
            if (row, col) not in self._blocked
        ]
        self._cells = cells
        self._edges = []
        for cell in cells:
            row, col = cell
            right = (row, col + 1)
            down = (row + 1, col)
            if col + 1 < self._width and right not in self._blocked:
                self._edges.append((cell, right))
            if row + 1 < self._height and down not in self._blocked:
                self._edges.append((cell, down))
        self._cycles = 0

    def _walls(
        self, a: tuple[int, int], b: tuple[int, int]
    ) -> tuple[Wall, Wall]:
        """Return the two wall bits separating adjacent cells."""
        offset = (b[0] - a[0], b[1] - a[1])
        for dr, dc, wall, opposite, _ in DIRECTIONS:
            if offset == (dr, dc):
                return wall, opposite
        raise ValueError("Can only connect orthogonally adjacent cells")

    def _open_wall(self, a: tuple[int, int], b: tuple[int, int]) -> None:
        """Clear both sides of a shared wall between ordinary cells."""
        wall, opposite = self._walls(a, b)
        self._maze[a[0]][a[1]] &= ~int(wall)
        self._maze[b[0]][b[1]] &= ~int(opposite)

    def _dfs(self) -> None:
        """Build a spanning tree with randomized iterative DFS."""
        if not self._cells:
            return

        visited = {self._cells[0]}
        stack = [self._cells[0]]
        while stack:
            row, col = stack[-1]
            neighbors = []
            for dr, dc, _, _, _ in DIRECTIONS:
                neighbor = (row + dr, col + dc)
                if (0 <= neighbor[0] < self._height
                        and 0 <= neighbor[1] < self._width
                        and neighbor not in self._blocked
                        and neighbor not in visited):
                    neighbors.append(neighbor)
            if not neighbors:
                stack.pop()
                continue
            neighbor = self._rng.choice(neighbors)
            self._open_wall((row, col), neighbor)
            visited.add(neighbor)
            stack.append(neighbor)

        if len(visited) != len(self._cells):
            raise ValueError(
                "The 42 pattern separates the walkable area into "
                "disconnected regions"
            )

    def _open_count(self, cell: tuple[int, int]) -> int:
        """Return the number of open sides for a cell."""
        value = self._maze[cell[0]][cell[1]]
        return sum(not (value & wall) for _, _, wall, _, _ in DIRECTIONS)

    def _open_square(self, row: int, col: int) -> bool:
        """Check the twelve internal shared walls of one 3-by-3 block."""
        horizontal = all(
            not (self._maze[r][c] & Wall.EAST)
            for r in range(row, row + 3)
            for c in range(col, col + 2)
        )
        vertical = all(
            not (self._maze[r][c] & Wall.SOUTH)
            for r in range(row, row + 2)
            for c in range(col, col + 3)
        )
        return horizontal and vertical

    def _makes_square(
        self, a: tuple[int, int], b: tuple[int, int]
    ) -> bool:
        """Inspect only 3-by-3 blocks containing the changed shared wall."""
        # A newly open 3x3 region must contain both cells of this wall;
        # every other region has unchanged walls.
        first_row = max(0, max(a[0], b[0]) - 2)
        last_row = min(min(a[0], b[0]), self._height - 3)
        first_col = max(0, max(a[1], b[1]) - 2)
        last_col = min(min(a[1], b[1]), self._width - 3)
        return any(
            self._open_square(row, col)
            for row in range(first_row, last_row + 1)
            for col in range(first_col, last_col + 1)
        )

    def _try_loop(self, a: tuple[int, int], b: tuple[int, int]) -> bool:
        """Add a loop unless it opens a fully open 3-by-3 area."""
        wall, _ = self._walls(a, b)
        old_a = self._maze[a[0]][a[1]]
        old_b = self._maze[b[0]][b[1]]
        if not (old_a & wall):
            return False
        self._open_wall(a, b)
        if self._makes_square(a, b):
            self._maze[a[0]][a[1]] = old_a
            self._maze[b[0]][b[1]] = old_b
            return False
        self._cycles += 1
        return True

    def _braid(self) -> None:
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
            # Stable sorting prefers dead ends without losing the shuffled
            # order among candidates with the same priority.
            candidates.sort(key=lambda other: self._open_count(other) != 1)
            for neighbor in candidates:
                if self._try_loop(cell, neighbor):
                    break

    def _add_loops(self) -> None:
        """Ensure at least two independent cycles, if legal openings exist."""
        for a, b in self._edges:
            if self._cycles >= self.MIN_LOOPS:
                return
            self._try_loop(a, b)

    def _playable(self) -> bool:
        """Apply the subject's minimum loops and tolerated dead-end count."""
        dead_ends = sum(
            self._open_count(cell) == 1 for cell in self._cells
        )
        if self._cycles < self.MIN_LOOPS or dead_ends > self.MAX_DEAD_ENDS:
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

    def _valid_maze(self) -> bool:
        """Check wall agreement, borders, and blocked cells."""
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
