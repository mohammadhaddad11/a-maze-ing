"""Placement rules for the closed-cell 42 pattern."""

from .config import Config

PATTERN_42 = (
    "1000111",
    "1000001",
    "1110111",
    "0010100",
    "0010111",
)


def pattern_cells(row: int, col: int) -> set[tuple[int, int]]:
    """Return the occupied cells for a pattern at the given position."""
    cells: set[tuple[int, int]] = set()

    for pattern_row, line in enumerate(PATTERN_42):
        for pattern_col, value in enumerate(line):
            if value == "1":
                cells.add((
                    row + pattern_row,
                    col + pattern_col,
                ))

    return cells


def _center_key(position: tuple[int, int], height: int, width: int
                ) -> tuple[float, int, int]:
    """Return the original center-distance and tie-breaking key."""
    row, col = position
    pattern_height = len(PATTERN_42)
    pattern_width = len(PATTERN_42[0])

    center_row = (height - pattern_height) / 2
    center_col = (width - pattern_width) / 2

    distance = abs(row - center_row) + abs(col - center_col)

    return distance, row, col


def find_42_cells(config: Config) -> set[tuple[int, int]]:
    """Choose and reserve a legal centered pattern position."""
    height = config.height
    width = config.width
    pattern_height = len(PATTERN_42)
    pattern_width = len(PATTERN_42[0])
    if height < pattern_height or width < pattern_width:
        print("Error: maze is too small for the 42 pattern; omitted.")
        return set()
    positions = [
        (row, col)
        for row in range(height - pattern_height + 1)
        for col in range(width - pattern_width + 1)
    ]
    positions.sort(key=lambda position: _center_key(position, height, width))
    entry_x, entry_y = config.entry
    exit_x, exit_y = config.exit
    reserved = {(entry_y, entry_x), (exit_y, exit_x)}
    if not config.perfect:
        reserved.update({
            (0, 0), (0, width - 1),
            (height - 1, 0), (height - 1, width - 1),
            (height // 2, width // 2),
        })
    for row, col in positions:
        cells = pattern_cells(row, col)
        if not cells & reserved:
            return cells
    raise ValueError(
        "Cannot place the 42 pattern without covering required cells"
    )
