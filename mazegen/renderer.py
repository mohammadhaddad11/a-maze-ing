"""Apply display colors and overlays to a Unicode maze canvas."""

from os import get_terminal_size
import random
import sys

from .canvas import CELL_HEIGHT, CELL_WIDTH, build_canvas, cell_position
from .walls import Wall


class Renderer:
    """Draw maze walls with endpoint and optional path overlays."""

    def __init__(
        self, maze: list[list[int]], solution: str = "",
        show_path: bool = False, entry: tuple[int, int] = (0, 0),
        exit: tuple[int, int] | None = None, wall_color: int = 37,
        path_color: int = 46, pattern_color: int = 47,
    ) -> None:
        """Store maze, N/E/S/W solution, endpoints, and display state."""
        self._maze = maze
        self._solution = solution
        self._show_path = show_path
        self._entry = entry
        self._exit = exit if exit is not None else (
            len(maze[0]) - 1, len(maze) - 1,
        )
        self._wall_color = wall_color
        self._path_color = path_color
        self._pattern_color = pattern_color

    def update(self, maze: list[list[int]], solution: str) -> None:
        """Replace the maze and solution while preserving display settings."""
        self._maze = maze
        self._solution = solution

    def toggle_path(self) -> None:
        """Toggle visibility without changing the maze or its solution."""
        self._show_path = not self._show_path

    def randomize_color(self) -> None:
        """Choose a different ANSI wall color without changing geometry."""
        self._wall_color = random.choice(
            [color for color in range(31, 38) if color != self._wall_color]
        )

    def rotate_path_color(self) -> None:
        """Rotate the solution background without changing the path."""
        self._path_color = 41 + (self._path_color - 40) % 7

    def rotate_pattern_color(self) -> None:
        """Rotate closed-cell interior color without changing walls."""
        self._pattern_color = 41 + (self._pattern_color - 40) % 7

    def _check_terminal_size(self) -> None:
        """Require a terminal large enough for the original maze and menu."""
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            raise ValueError("An interactive terminal is required for display")
        terminal = get_terminal_size(sys.stdout.fileno())

        required_cols = max(
            len(self._maze[0]) * CELL_WIDTH + 1,
            len("4. Change solution path color"),
            len("Choice (1-6): "),
        ) + 1
        # Extra rows leave room for the border, seed, menu, and prompt.
        required_rows = len(self._maze) * CELL_HEIGHT + 11

        if (terminal.columns < required_cols
                or terminal.lines < required_rows):
            raise ValueError(
                f"Maze requires {required_cols} columns × "
                f"{required_rows} rows, "
                f"but the terminal has "
                f"{terminal.columns} columns × {terminal.lines} rows. "
                "Zoom out or enlarge the terminal."
            )

    def _style_canvas(self, canvas: list[list[str]]) -> list[str]:
        """Apply pattern, path, and endpoint overlays to canvas interiors."""
        styles: dict[tuple[int, int], int] = {}
        height = len(self._maze)
        width = len(self._maze[0])
        for row in range(height):
            for col in range(width):
                if self._maze[row][col] == int(Wall.ALL):
                    y, x = cell_position(row, col)
                    for offset in (0, 1):
                        styles[(y, x + offset)] = self._pattern_color

        if self._show_path:
            row, col = self._entry[1], self._entry[0]
            steps = {"N": (-1, 0), "E": (0, 1),
                     "S": (1, 0), "W": (0, -1)}
            y, x = cell_position(row, col)
            styles[(y, x)] = self._path_color
            styles[(y, x + 1)] = self._path_color
            for direction in self._solution:
                dr, dc = steps[direction]
                y, x = cell_position(row, col)
                if dr:
                    passage = [(y + dr, x), (y + dr, x + 1)]
                else:
                    passage = [(y, x + 2 if dc > 0 else x - 1)]
                for passage_row, passage_col in passage:
                    canvas[passage_row][passage_col] = " "
                    styles[(passage_row, passage_col)] = self._path_color
                row += dr
                col += dc
                y, x = cell_position(row, col)
                styles[(y, x)] = self._path_color
                styles[(y, x + 1)] = self._path_color

        for (x, y), marker, color in (
            (self._entry, "E", 45), (self._exit, "X", 41),
        ):
            screen_row, screen_col = cell_position(y, x)
            canvas[screen_row][screen_col] = (
                f"\x1b[{color};97m{marker}\x1b[0;{self._wall_color}m"
            )
            canvas[screen_row][screen_col + 1] = " "
            styles.pop((screen_row, screen_col), None)
            styles.pop((screen_row, screen_col + 1), None)

        lines = []
        for row, cells in enumerate(canvas):
            line = []
            for col, value in enumerate(cells):
                style_color = styles.get((row, col))
                if style_color is None:
                    line.append(value)
                else:
                    line.append(
                        f"\x1b[{style_color}m{value}"
                        f"\x1b[0;{self._wall_color}m"
                    )
            lines.append("".join(line))
        return lines

    def render(self) -> None:
        """Redraw the maze canvas and its required overlays."""
        self._check_terminal_size()
        try:
            canvas = build_canvas(self._maze)
            print(end="\x1b[2J\x1b[H")
            print(end=f"\x1b[{self._wall_color}m")
            print(end="\n".join(self._style_canvas(canvas)) + "\n")
        finally:
            print(end="\x1b[0m", flush=True)
