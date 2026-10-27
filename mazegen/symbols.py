"""Unicode wall glyphs and the directions of their connections."""

from enum import IntFlag

VERTICAL = "┃"
HORIZONTAL = "━"


class Junction(IntFlag):
    """Readable connection bits for a wall junction."""

    UP = 1
    RIGHT = 2
    DOWN = 4
    LEFT = 8


JUNCTION_GLYPHS: dict[Junction, str] = {
    Junction(0): " ",
    Junction.UP: "╹",
    Junction.RIGHT: "╺",
    Junction.DOWN: "╻",
    Junction.LEFT: "╸",
    Junction.UP | Junction.RIGHT: "┗",
    Junction.UP | Junction.DOWN: "┃",
    Junction.UP | Junction.LEFT: "┛",
    Junction.RIGHT | Junction.DOWN: "┏",
    Junction.RIGHT | Junction.LEFT: "━",
    Junction.DOWN | Junction.LEFT: "┓",
    Junction.UP | Junction.RIGHT | Junction.DOWN: "┣",
    Junction.UP | Junction.RIGHT | Junction.LEFT: "┻",
    Junction.UP | Junction.DOWN | Junction.LEFT: "┫",
    Junction.RIGHT | Junction.DOWN | Junction.LEFT: "┳",
    Junction.UP | Junction.RIGHT | Junction.DOWN | Junction.LEFT:
        "╋",
}
