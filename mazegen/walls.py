"""Shared wall bits and cardinal direction ordering."""

from enum import IntFlag


class Wall(IntFlag):
    """Represent closed walls in an exported maze cell."""

    NORTH = 1
    EAST = 2
    SOUTH = 4
    WEST = 8
    ALL = NORTH | EAST | SOUTH | WEST


DIRECTIONS = (
    (-1, 0, Wall.NORTH, Wall.SOUTH, "N"),
    (0, 1, Wall.EAST, Wall.WEST, "E"),
    (1, 0, Wall.SOUTH, Wall.NORTH, "S"),
    (0, -1, Wall.WEST, Wall.EAST, "W"),
)
