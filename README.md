*This project was created as part of the 42 curriculum by mhaddad and domansou.*

# A-Maze-ing

## Description

A configurable maze generator, shortest-path solver, hexadecimal exporter, and
interactive Unicode terminal application. Its reusable `mazegen` Python package
separates validation, generation, solving, wall geometry, and display.

The local implementation uses **randomized Kruskal with Union-Find**, optional
braiding, and breadth-first search. It does not inherit algorithms from the
reference portfolios used to organize this documentation.

## Instructions

Requirements: Python **3.10+**, [uv](https://docs.astral.sh/uv/), Make, and a
Unix-like terminal supporting Unicode and ANSI controls. Pydantic v2 is the
runtime dependency; the development environment includes flake8, mypy, and build.

```sh
git clone git@github.com:mohammadhaddad11/a-maze-ing.git
cd a-maze-ing
make install
make run
```

`make install` runs `uv sync`; `make run` uses the supplied configuration.
For another file, use `uv run python a_maze_ing.py your-config.txt`.
`make debug` starts the application through pdb. `make clean` removes caches;
it does not remove the environment or all generated output.

The display requires at least `max(3 * WIDTH + 2, 30)` columns and
`2 * HEIGHT + 11` rows. The supplied **10×10** configuration needs **32×31**.
Generation/export happen before terminal validation: a non-TTY run may write
output and then print a display error. Most CLI errors are printed without
setting a nonzero exit status; automation should not equate status zero with
successful interactive display.

### Configuration

The actual [`config.txt`](config.txt) is:

```text
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
| `WIDTH`, `HEIGHT` | Positive grid dimensions |
| `ENTRY`, `EXIT` | Distinct in-bounds `x,y` coordinates |
| `OUTPUT_FILE` | Nonempty output path, relative to the working directory unless absolute |
| `PERFECT` | Required generation mode; prefer `True` or `False` |
| `SEED` | Optional integer; omitted seeds are generated from 1 through 1,000,000 |

The parser accepts one `KEY=VALUE` pair per line, ignores blank lines and whole
comment lines, normalizes key case, and trims surrounding whitespace. Duplicate
keys, unknown keys, missing required fields, and invalid endpoints are rejected.
Inline comments are not parsed. Coordinate strings must contain two digit-only
components without spaces around the comma. Pydantic also accepts some coerced
integer/boolean forms, and explicit negative seeds are allowed.

### Menu

1. Regenerate, incrementing the seed.
2. Show/hide the shortest path.
3. Change wall colors.
4. Change solution background color.
5. Change reserved-pattern background color.
6. Exit.

`E` and `X` mark entry and exit. Regeneration preserves display settings.
EOF and Ctrl-C are caught by the application.

## Technical Implementation

```text
configuration → Parser / Config → MazeGenerator → BFS → hexadecimal export
                                      │            │
                                      └── Renderer ←┘
                                           │
                                     canvas + symbols
```

| Module | Responsibility |
| --- | --- |
| `config.py`, `parser.py` | Typed settings and configuration-file validation |
| `walls.py` | Shared direction/wall-bit definitions |
| `pattern.py` | Legal placement of reserved “42” cells |
| `maze_generator.py`, `union_find.py` | Kruskal spanning tree, braiding, constraints, disjoint sets |
| `solver.py` | BFS route reconstruction |
| `canvas.py`, `symbols.py` | Wall geometry and Unicode junction glyphs |
| `renderer.py` | Colors, endpoints, optional route overlay, terminal checks |
| `exporter.py` | UTF-8 grid/endpoints/route serialization |
| `a_maze_ing.py` | Generation/export orchestration and menu |

### Internal representation

The row-major grid stores four wall bits per cell. A set bit means closed:

```text
          N = 1
      W=8 [cell] E=2
          S = 4
```

`F` closes all four walls. Adjacent cells must agree on their shared wall and
external borders remain closed. Configuration/rendering endpoints use **(x,y)**;
the generator and BFS use **(row,column)**. The application converts explicitly.

## Algorithms and Data Structures

### Generation

1. Reserve the occupied cells of a five-row, seven-column “42” pattern.
2. Initialize ordinary cells with all walls closed.
3. Enumerate right/down candidate edges, shuffle using a local seeded RNG,
   and join disjoint components, opening both sides of each selected wall.
4. Validate connectivity, shared walls, borders, and blocked cells.
5. In non-perfect mode, braid dead ends and open additional legal edges.

Union-Find uses path compression and union by size. Perfect mode produces a
connected spanning tree over ordinary cells, so paths are unique. Non-perfect
mode requires at least two independent cycles, at most two dead ends, and
corners/center with at least two open sides. Openings that create a fully open
3×3 area are rolled back. Generation retries at most 30 times and can reject
settings that cannot satisfy these constraints.

Pattern candidates are considered near the center first. Endpoints are
protected; non-perfect mode also protects corners and center. Physically small
boards omit the pattern with a message. A board large enough for the pattern
but without a legal placement raises an error. Connectivity is checked after
placement rather than assumed.

Although disjoint-set operations are near-constant amortized time, the generator
also uses list-membership checks while building and braiding the grid. Those
scans and possible retries preclude a blanket linear-time claim.

### Solving

BFS uses `collections.deque`, a visited set, and parent links. It explores
north/east/south/west neighbors in fixed order and reconstructs an `N/E/S/W`
direction string. For an unweighted grid it returns a shortest route in
O(V+E) time with O(V) auxiliary memory. An unreachable exit raises `ValueError`.

### Rendering and output

The canvas allocates three character columns and two rows per cell, draws wall
segments, and resolves junctions. The renderer applies ANSI styles to reserved
cells, route passages, and endpoints without changing the wall grid.

The exporter overwrites its destination with LF-terminated UTF-8 text:

```text
<HEIGHT rows, each WIDTH uppercase hexadecimal wall digits>

<entry x,y>
<exit x,y>
<N/E/S/W shortest route>
```

[`docs/maze-example.txt`](docs/maze-example.txt) is genuine uncolored canvas
geometry generated from the supplied 10×10, non-perfect, seed-3 configuration.
The interactive renderer adds endpoint, pattern, and path styling.

## Reusable Python Packaging

`pyproject.toml` builds package **`mazegen`**, version `0.1.0`, using `uv_build`.
The package exports `Config`, `MazeGenerator`, `Parser`, `Renderer`, `Wall`, and
the solver module. It does not define an installed application command.

```sh
uv build
```

This creates a source distribution and wheel in `dist/`. Install the wheel into
another environment with `python -m pip install dist/mazegen-0.1.0-py3-none-any.whl`.
The wheel contains the reusable modules and license, not the root application
or configuration file. No stale prebuilt wheel is tracked in the repository.

```python
from mazegen import Config, MazeGenerator, solver

config = Config(width=10, height=10, entry=(0, 0), exit=(9, 9),
                output_file="maze.txt", perfect=True, seed=3)
maze = MazeGenerator(config).generate()
route = solver.BFS(maze, (0, 0), (9, 9)).solve()
print(route)
```

This API example generates and solves in memory. Call
`mazegen.exporter.write_output(config, maze, route)` explicitly to export.

## Verification

Verified on Fedora with Python 3.14.8 and Pydantic 2.14.1, 2026-10-27:

- `make install`, `make lint`, and `make lint-strict` passed for the 13 source files.
- 24 grid/export cases passed: dimensions 10×10, 20×15, and 30×20; seeds 0, 1,
  3, and 42; both generation modes. Each was regenerated for seed repeatability.
- Independent graph checks covered wall reciprocity, closed boundaries,
  connectivity, perfect-mode edge count, non-perfect cycle/dead-end constraints,
  required cell degrees, 3×3 restrictions, and shortest-route replay.
- Seven malformed configurations were rejected, including duplicate/unknown
  keys, invalid dimensions/endpoints, missing mode, and malformed assignment.
- A real pseudo-terminal exercised path/color controls, regeneration, and exit.
  Non-TTY export followed by the printed display error was separately verified.
- `uv build` passed. A newly built wheel installed into a fresh environment and
  generated/solved a maze outside the source tree.

The earlier README mentioned subject-provided analyzer/regression tools that
are not included. They were not run in this publication session; the checks
above are the verification performed here, not an official evaluation result.

## Contributors and License

The current local documentation and unchanged [MIT license](LICENSE.md) credit
**mhaddad and domansou**. Existing responsibility notes attribute original
generator/renderer/parser work and final cleanup to mhaddad;
solver/license/Makefile/packaging metadata to domansou; and application
integration to both. Preserve these notices when redistributing the package.

## Resources

- [Maze generation](https://en.wikipedia.org/wiki/Maze_generation_algorithm).
- [Disjoint-set data structure](https://en.wikipedia.org/wiki/Disjoint-set_data_structure).
- [Python deque](https://docs.python.org/3/library/collections.html#collections.deque).
- [Pydantic validators](https://docs.pydantic.dev/latest/concepts/validators/).
- [uv build backend](https://docs.astral.sh/uv/concepts/build-backend/).
- Documentation presentation informed by [oweidat05/a_maze_ing](https://github.com/oweidat05/a_maze_ing), [AhmadNajiKam/A_maze_ing](https://github.com/AhmadNajiKam/A_maze_ing), and [BilalOrabi/A_maze_ing](https://github.com/BilalOrabi/A_maze_ing). Their source, algorithms, and technical claims were not copied.

## AI Usage

The existing local README records AI support for explanations, review/refactoring,
parser/renderer edge cases, integration review, and testing ideas. During this
publication an AI assistant inspected the source, revised documentation, and
ran graph, parser, terminal, lint, and packaging checks. The supplied application
and package implementations were preserved; the existing team/license credits
remain authoritative.
