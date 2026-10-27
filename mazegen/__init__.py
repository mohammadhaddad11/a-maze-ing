"""Reuse maze generation, parsing, rendering, and BFS solving.

Example::

    from mazegen import Config, MazeGenerator, solver

    config = Config(
        width=20,
        height=15,
        entry=(0, 0),
        exit=(19, 14),
        output_file="maze.txt",
        perfect=True,
        seed=3,
    )
    maze = MazeGenerator(config).generate()
    entry = (config.entry[1], config.entry[0])
    exit = (config.exit[1], config.exit[0])
    solution = solver.BFS(maze, entry, exit).solve()
"""

from . import solver
from .config import Config
from .maze_generator import MazeGenerator
from .parser import Parser
from .renderer import Renderer
from .walls import Wall

__all__ = [
    "MazeGenerator", "Config", "Parser", "Renderer", "Wall", "solver",
]
