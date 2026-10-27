*This project was created as part of the 42 curriculum by mhaddad and domansou.*

# A-Maze-ing

A configurable maze generator, shortest-path solver, and interactive terminal viewer written in Python. The generation logic is also packaged as the reusable `mazegen` library.

## Description

The application reads a configuration file, constructs a connected maze, computes a shortest path, exports hexadecimal wall data, and renders the maze in a Unicode terminal.

- **Perfect mode:** generates a spanning tree with exactly one path between ordinary cells.
- **Non-perfect mode:** adds passages to form loops while enforcing layout constraints.
- **Reproducible generation:** an explicit fixed seed produces the same layout for the same settings.
- **Interactive display:** toggle the path, regenerate the maze, and change colors.

## Instructions

Requirements: Python **3.10+**, [uv](https://docs.astral.sh/uv/), Make, and a terminal supporting Unicode and ANSI controls. Pydantic v2 is the runtime dependency installed by `make install`.

```sh
git clone git@github.com:mohammadhaddad11/a-maze-ing.git
cd a-maze-ing
make install
make run
```

`make run` uses `config.txt`. To use another file, replace `my-config.txt` below with the path to an existing configuration file:

```sh
uv run python a_maze_ing.py my-config.txt
```

`make debug` starts the Python debugger; `make lint` and `make lint-strict` run the configured checks.

### Configuration

```ini
WIDTH=10
HEIGHT=10
ENTRY=0,0
EXIT=9,9
OUTPUT_FILE=maze.txt
PERFECT=False
SEED=3
```

| Key | Meaning |
| --- | --- |
| `WIDTH`, `HEIGHT` | Positive maze dimensions in cells |
| `ENTRY`, `EXIT` | Different, in-bounds `x,y` positions, written without parentheses |
| `OUTPUT_FILE` | Nonempty destination for encoded output |
| `PERFECT` | Required generation mode; prefer `True` or `False` |
| `SEED` | Optional integer seed; the parser generates one when omitted |

The parser rejects missing required or unknown keys, duplicate assignments, malformed coordinates, and invalid endpoints. It accepts blank lines and whole-line comments, but not inline comments. Keys are case-insensitive. Coordinate strings must contain two digit-only components without spaces around the comma. Pydantic accepts some coerced integer/boolean values, and explicit negative seeds are allowed.

### Interactive controls

1. Regenerate the maze
2. Show or hide the shortest path
3. Change wall color
4. Change solution color
5. Change the reserved `42` pattern color
6. Exit

`E` marks the entrance and `X` the exit. The supplied 10×10 configuration needs a terminal of at least **32 columns × 31 rows**.

## Architecture

```text
config.txt
   │
   ▼
Parser / Config ──▶ MazeGenerator ──▶ BFS solver
                          │               │
                          └──────┬────────┘
                                 ├──▶ Hex exporter
                                 └──▶ Terminal renderer
```

| Component | Responsibility |
| --- | --- |
| `config.py`, `parser.py` | Settings and validation |
| `maze_generator.py`, `union_find.py` | Spanning tree and additional passages |
| `walls.py`, `pattern.py` | Cell walls and reserved `42` cells |
| `solver.py` | BFS and shortest path |
| `canvas.py`, `symbols.py`, `renderer.py` | Unicode geometry and display |
| `exporter.py` | Hexadecimal wall data and route export |

These components are modules inside `mazegen/`; `a_maze_ing.py` orchestrates generation, export, and the menu.

### Maze representation

Each cell stores four wall bits; a set bit means the wall is **closed**.

| Direction | Bit |
| --- | --- |
| North | `1` |
| East | `2` |
| South | `4` |
| West | `8` |

The hexadecimal value `F` represents a cell with every wall closed. Neighboring cells must agree on shared walls. Configuration coordinates use `(x,y)`; grid and solver internals use row/column order.

## Algorithms

**Randomized Kruskal:** enumerate candidate edges, shuffle with a seeded generator, and use Union-Find (path compression and union by size) to open walls between disconnected components. The resulting perfect maze is connected and acyclic over ordinary cells.

**Braiding:** non-perfect mode opens additional legal walls to create at least two independent cycles and at most two dead ends, while avoiding fully open 3×3 areas. Corners and the center must have at least two open sides. The generator makes at most 30 attempts and raises an error if it cannot satisfy the constraints; impossible loop capacity is rejected earlier.

**Breadth-first search:** use a queue and parent links to reconstruct an `N/E/S/W` route. In an unweighted grid, BFS finds a shortest path in `O(V + E)` time.

Grids smaller than the five-row, seven-column `42` motif omit it with a message. Larger grids must admit a placement that avoids required cells; otherwise generation raises an error rather than silently omitting the pattern.

## Output and Packaging

The exporter writes one row of uppercase hexadecimal wall values per maze row, then a blank line, entry coordinates, exit coordinates, and the solution route. Lines use LF endings. An actual plain-text maze example is available at [`docs/maze-example.txt`](docs/maze-example.txt).

The reusable `mazegen` package is defined in `pyproject.toml` and can be built with:

```sh
uv build
```

The wheel contains the reusable Python modules and license, not the root interactive application or a built-in command-line entry point.

## Verification and Limitations

The earlier portfolio checks included linting, 24 grid/export configurations, seed repeatability, wall consistency, connectivity, BFS route replay, invalid configuration handling, terminal interaction, and installing a freshly built wheel. Those are historical verification results, not a claim that the full suite was rerun for this documentation-only refresh.

The application needs a sufficiently large terminal for the viewer. Export occurs before terminal validation, so a non-interactive run can write a file and then display an error. Some command-line failures print a message without a nonzero exit status.

## Contributors and License

**mhaddad** and **domansou** are credited in the existing project materials. Original responsibility notes attribute generator/renderer/parser work and final cleanup to mhaddad; solver/license/Makefile/packaging metadata to domansou; and application integration to both. See [`LICENSE.md`](LICENSE.md) for the unchanged MIT copyright and permission notice.

## Resources

- [Maze generation algorithms](https://en.wikipedia.org/wiki/Maze_generation_algorithm)
- [Disjoint-set data structure](https://en.wikipedia.org/wiki/Disjoint-set_data_structure)
- [Python deque](https://docs.python.org/3/library/collections.html#collections.deque)
- [Pydantic validators](https://docs.pydantic.dev/latest/concepts/validators/)
- [uv build backend](https://docs.astral.sh/uv/concepts/build-backend/)

## AI Usage

The project documentation records AI assistance with learning, review/refactoring, parser/renderer edge cases, integration review, and testing ideas. An AI assistant also helped organize documentation and execute verification during the earlier portfolio publication. This refresh uses AI-assisted README review only; the implementation, contributor credits, and license remain unchanged.
