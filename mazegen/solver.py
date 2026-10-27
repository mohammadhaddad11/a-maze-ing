"""Find a shortest maze route using the original breadth-first search."""

from collections import deque

from .walls import DIRECTIONS


class BFS:
    """Solve a wall-bit grid using (row, column) endpoint coordinates."""

    def __init__(
            self,
            maze: list[list[int]],
            entry: tuple[int, int],
            exit: tuple[int, int],) -> None:
        """Store the maze and the endpoints to be connected."""
        self.maze = maze
        self.entry = entry
        self.exit = exit

    def solve(self) -> str:
        """Return shortest N/E/S/W directions or raise if no route exists."""
        queue = deque([self.entry])
        visited = {self.entry}
        parent: dict[tuple[int, int], tuple[tuple[int, int], str]] = {}

        while queue:
            current = queue.popleft()
            if current == self.exit:
                break
            for cell, direction in self._neighbors(current):
                if cell not in visited:
                    visited.add(cell)
                    parent[cell] = current, direction
                    queue.append(cell)

        if self.exit not in visited:
            raise ValueError("No path found from entry to exit")

        path: list[str] = []
        current = self.exit

        while current != self.entry:
            current, direction = parent[current]
            path.append(direction)

        path.reverse()

        return ''.join(path)

    def _neighbors(
        self, cell: tuple[int, int]
    ) -> list[tuple[tuple[int, int], str]]:
        """Return in-bounds neighbors reachable through an open wall."""
        row, col = cell
        value = self.maze[row][col]

        height = len(self.maze)
        width = len(self.maze[0])

        neighbors: list[tuple[tuple[int, int], str]] = []

        for dr, dc, wall, _, direction in DIRECTIONS:
            neighbor_row = row + dr
            neighbor_col = col + dc
            if (0 <= neighbor_row < height
                    and 0 <= neighbor_col < width
                    and not value & wall):
                neighbors.append(((neighbor_row, neighbor_col), direction))

        return neighbors
