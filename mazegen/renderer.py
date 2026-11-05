"""Apply display colors and overlays to a Unicode maze canvas."""

from os import get_terminal_size
import sys

from .canvas import CELL_HEIGHT, CELL_WIDTH, build_canvas, cell_position
from .walls import Wall


class Renderer:
    """Draw maze walls with endpoint and optional path overlays."""

    def __init__(
        self,
        maze: list[list[int]],
        entry: tuple[int, int],
        exit: tuple[int, int],
        solution: str = "",
        show_path: bool = False,
        wall_color: int = 39,
        path_color: int = 46,
        pattern_color: int = 7,
    ) -> None:
        """Store maze, N/E/S/W solution, endpoints, and display state."""
        self._maze = maze
        self._solution = solution
        self._show_path = show_path
        self._entry = entry
        self._exit = exit
        self._wall_color = wall_color
        self._path_color = path_color
        self._pattern_color = pattern_color

    def render(self) -> None:
        """Redraw the maze canvas and its required overlays."""
        self._check_terminal_size()

        try:
            canvas = build_canvas(self._maze)

            print("\x1b[2J\x1b[H", end="")
            print(f"\x1b[{self._wall_color}m", end="")
            print("\n".join(self._style_canvas(canvas)))

        finally:
            print("\x1b[0m", end="", flush=True)

    def _check_terminal_size(self) -> None:
        """Require a terminal large enough for the original maze and menu."""
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            raise ValueError("An interactive terminal is required for display")
        terminal = get_terminal_size(sys.stdout.fileno())

        required_cols = len(self._maze[0]) * CELL_WIDTH + 2
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

        self._color_pattern(styles)

        if self._show_path:
            self._color_path(styles)

        self._mark_endpoints(canvas, styles)

        return self._to_ansi(canvas, styles)

    def _color_pattern(self, styles: dict[tuple[int, int], int]) -> None:
        """Color the interiors of fully blocked cells."""
        height = len(self._maze)
        width = len(self._maze[0])
        for row in range(height):
            for col in range(width):
                if self._maze[row][col] == int(Wall.ALL):
                    y, x = cell_position(row, col)
                    self._color_span(styles, y, x, self._pattern_color)

    def _color_span(
        self,
        styles: dict[tuple[int, int], int],
        y: int,
        x: int,
        color: int,
    ) -> None:
        """Color a horizontal span across a cell interior."""
        for offset in range(CELL_WIDTH - 1):
            styles[(y, x + offset)] = color

    def _color_path(
        self, styles: dict[tuple[int, int], int],
    ) -> None:
        """Color the solution cells and passages."""
        row, col = self._entry[1], self._entry[0]
        steps = {"N": (-1, 0), "E": (0, 1),
                 "S": (1, 0), "W": (0, -1)}
        for direction in self._solution:
            dr, dc = steps[direction]
            y, x = cell_position(row, col)
            if dr:
                self._color_span(styles, y + dr, x, self._path_color)
            else:
                passage_col = x + CELL_WIDTH - 1 if dc > 0 else x - 1
                styles[(y, passage_col)] = self._path_color
            row += dr
            col += dc
            y, x = cell_position(row, col)
            self._color_span(styles, y, x, self._path_color)

    def _mark_endpoints(
        self, canvas: list[list[str]], styles: dict[tuple[int, int], int],
    ) -> None:
        """Draw entry and exit markers with full-cell backgrounds."""
        for (x, y), marker, color in (
            (self._entry, "E", 45),
            (self._exit, "X", 41),
        ):
            screen_row, screen_col = cell_position(y, x)

            self._color_span(styles, screen_row, screen_col, color)

            middle = screen_col + (CELL_WIDTH - 1) // 2
            canvas[screen_row][middle] = f"\x1b[97m{marker}"

    def _to_ansi(
        self, canvas: list[list[str]], styles: dict[tuple[int, int], int],
    ) -> list[str]:
        """Convert the styled canvas to ANSI-colored output lines."""
        lines = []
        for row, cells in enumerate(canvas):
            line = []
            for col, value in enumerate(cells):
                style_color = styles.get((row, col))
                if style_color is None:
                    line.append(value)
                elif style_color == 7:
                    line.append(
                        f"\x1b[0;{style_color}m{value}"
                        f"\x1b[0;{self._wall_color}m"
                    )
                else:
                    line.append(
                        f"\x1b[{style_color}m{value}"
                        f"\x1b[0;{self._wall_color}m"
                    )
            lines.append("".join(line))
        return lines

    def update(self, maze: list[list[int]], solution: str) -> None:
        """Replace the maze and solution while preserving display settings."""
        self._maze = maze
        self._solution = solution

    def toggle_path(self) -> None:
        """Toggle visibility without changing the maze or its solution."""
        self._show_path = not self._show_path

    def rotate_wall_color(self) -> None:
        """Choose a different ANSI wall color without changing geometry."""
        self._wall_color = 31 + (self._wall_color - 30) % 7

    def rotate_path_color(self) -> None:
        """Rotate the solution background without changing the path."""
        self._path_color = 41 + (self._path_color - 40) % 7

    def rotate_pattern_color(self) -> None:
        """Rotate closed-cell interior color without changing walls."""
        self._pattern_color = 41 + (self._pattern_color - 40) % 7
