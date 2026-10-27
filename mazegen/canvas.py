"""Turn maze wall bits into a Unicode character grid."""

from .symbols import HORIZONTAL, JUNCTION_GLYPHS, VERTICAL, Junction
from .walls import Wall

CELL_HEIGHT = 2
CELL_WIDTH = 3


def cell_position(row: int, col: int) -> tuple[int, int]:
    """Return the screen position of the first interior character of a cell."""
    return 1 + row * CELL_HEIGHT, 1 + col * CELL_WIDTH


def resolve_junctions(
    canvas: list[list[str]], height: int, width: int
) -> None:
    """Select junctions from their four drawn neighboring segments."""
    for row in range(height + 1):
        for col in range(width + 1):
            y, x = row * CELL_HEIGHT, col * CELL_WIDTH
            connections = Junction(0)
            if y > 0 and canvas[y - 1][x] == VERTICAL:
                connections |= Junction.UP
            if x + 1 < len(canvas[0]) and canvas[y][x + 1] == HORIZONTAL:
                connections |= Junction.RIGHT
            if y + 1 < len(canvas) and canvas[y + 1][x] == VERTICAL:
                connections |= Junction.DOWN
            if x > 0 and canvas[y][x - 1] == HORIZONTAL:
                connections |= Junction.LEFT
            canvas[y][x] = JUNCTION_GLYPHS[connections]


def build_canvas(maze: list[list[int]]) -> list[list[str]]:
    """Draw each cell's closed walls, then resolve all intersections."""
    height = len(maze)
    width = len(maze[0])
    rows, cols = height * CELL_HEIGHT + 1, width * CELL_WIDTH + 1
    canvas = [[" " for _ in range(cols)] for _ in range(rows)]

    for row in range(height):
        for col in range(width):
            value = maze[row][col]
            y, x = cell_position(row, col)
            if value & Wall.NORTH:
                canvas[y - 1][x] = HORIZONTAL
                canvas[y - 1][x + 1] = HORIZONTAL
            if value & Wall.EAST:
                canvas[y][x + 2] = VERTICAL
            if value & Wall.SOUTH:
                canvas[y + 1][x] = HORIZONTAL
                canvas[y + 1][x + 1] = HORIZONTAL
            if value & Wall.WEST:
                canvas[y][x - 1] = VERTICAL

    resolve_junctions(canvas, height, width)
    return canvas
