*This project was created as part of the 42 curriculum by mhaddad and domansou.*

# A-Maze-ing

A-Maze-ing turns a configuration file into a maze that can be generated,
solved, exported, and explored in a terminal. The same generation and solving
components are available as the reusable Python package `mazegen`, so another
program can use the maze grid without opening the interactive viewer.

The implementation combines randomized Kruskal generation, Union-Find component
tracking, optional passage braiding, BFS shortest-path solving, and a Unicode
renderer. Its central design decision is to share one four-bit wall
representation across generation, solving, output, and display.

## Build and run

Requirements: Python **3.10+**, [uv](https://docs.astral.sh/uv/), Make, and a
Unix-like terminal with Unicode and ANSI support. Pydantic v2 is the runtime
dependency; `make install` also installs development tools.

```sh
git clone git@github.com:mohammadhaddad11/a-maze-ing.git
cd a-maze-ing
make install
make run
```

`make install` runs `uv sync`; `make run` uses the supplied `config.txt`.
To supply a different existing file, run `uv run python a_maze_ing.py` followed
by its path. `make debug` starts the same application through pdb.

The default 10×10 maze needs at least **32 columns × 31 rows** for the viewer
and menu. For other sizes, the renderer requires `max(3 × WIDTH + 2, 30)`
columns and `2 × HEIGHT + 11` rows. Both stdin and stdout must be terminals.

## A real generated layout

This is the uncolored wall canvas produced by the supplied 10×10, non-perfect,
seed-3 configuration. It is also stored in
[`docs/maze-example.txt`](docs/maze-example.txt):

```text
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃              ┃              ┃
┃  ┏━━━━━╸  ╻  ╹     ╻  ╺━━╸  ┃
┃  ┃        ┃        ┃        ┃
┃  ┃  ┏━━┓  ┗━━━━━┳━━╋━━┳━━┓  ┃
┃  ┃  ┃  ┃        ┃  ┃  ┃  ┃  ┃
┃  ┃  ┣━━┫     ╻  ┗━━┻━━╋━━┫  ┃
┃  ┃  ┃  ┃     ┃        ┃  ┃  ┃
┃  ╹  ┣━━╋━━┳━━┫  ┏━━┳━━╋━━┫  ┃
┃     ┃  ┃  ┃  ┃  ┃  ┃  ┃  ┃  ┃
┃  ╺━━┻━━┻━━╋━━┫  ┣━━╋━━┻━━┛  ┃
┃           ┃  ┃  ┃  ┃        ┃
┃  ╺━━┓     ┣━━┫  ┣━━╋━━┳━━┓  ┃
┃     ┃     ┃  ┃  ┃  ┃  ┃  ┃  ┃
┃  ╻  ┗━━┳━━┻━━┫  ┗━━┻━━┻━━┫  ┃
┃  ┃     ┃     ┃           ┃  ┃
┃  ┗━━╸  ╹     ╹  ╻  ╺━━┓  ╹  ┃
┃                 ┃     ┃     ┃
┃     ╻     ╻  ╺━━┻━━╸  ┗━━╸  ┃
┃     ┃     ┃                 ┃
┗━━━━━┻━━━━━┻━━━━━━━━━━━━━━━━━┛
```

The live renderer adds colored closed-cell interiors for the `42` motif,
entry `E`, exit `X`, and an initially visible solution path. The plain canvas
shows geometry only; it does not pretend to capture the ANSI overlays.

## Architecture and execution flow

```text
configuration file
       │
       ▼
Parser → Config validation
       │
       ▼
MazeGenerator ── pattern placement + Union-Find
       │
       ▼
wall-bit grid → BFS → N/E/S/W route
       │                   │
       └─────────┬─────────┘
                 ├── exporter → hexadecimal file
                 └── renderer → canvas, styles, interactive menu
```

[`a_maze_ing.py`](a_maze_ing.py) is the application layer. `main()` reads one
configuration filename, `generation(config)` generates/solves/exports, then a
`Renderer` displays the result and `run_menu` handles interaction. Generation
errors propagate to the application for reporting rather than being hidden
inside the output writer.

| Component | Responsibility |
| --- | --- |
| [`parser.py`](mazegen/parser.py), [`config.py`](mazegen/config.py) | Read settings and validate their types/relationships |
| [`walls.py`](mazegen/walls.py) | Wall bits, direction offsets, opposite walls, solver letters |
| [`pattern.py`](mazegen/pattern.py) | Select cells reserved for the closed-wall `42` motif |
| [`maze_generator.py`](mazegen/maze_generator.py) | Build/validate a tree, then optional loops |
| [`union_find.py`](mazegen/union_find.py) | Track connected components during Kruskal generation |
| [`solver.py`](mazegen/solver.py) | Find and reconstruct a shortest route |
| [`exporter.py`](mazegen/exporter.py) | Serialize grid, endpoints, and route |
| [`canvas.py`](mazegen/canvas.py), [`symbols.py`](mazegen/symbols.py) | Convert walls to segments and junction glyphs |
| [`renderer.py`](mazegen/renderer.py) | Apply colors/overlays and enforce terminal requirements |

## Configuration: text parsing and model validation

The supplied [`config.txt`](config.txt) contains:

```ini
WIDTH=10
HEIGHT=10
ENTRY=0,0
EXIT=9,9
OUTPUT_FILE=maze.txt
PERFECT=False
SEED=3
```

All keys except `SEED` are required. Width/height must be positive; endpoints
must be distinct and inside the grid; the output filename must be nonempty.
Coordinates use **x first, y second**. Relative input/output paths are resolved
from the working directory.

`Parser.read_config` ignores blank lines and whole-line `#` comments, splits
each setting on `=`, trims surrounding whitespace, and lowercases its key.
It rejects extra `=` signs and duplicate keys, including differently cased
duplicates. Inline comments are not a supported grammar feature.

The resulting dictionary goes through Pydantic `Config`, which forbids unknown
keys. A before-validator turns digit-only `x,y` strings into tuples; an after-
validator checks bounds and endpoint distinctness. Write coordinate values
without parentheses or spaces around the comma.

This is not strict parsing of every scalar: Pydantic accepts some integer and
boolean coercions, and an explicit seed may be negative. Prefer decimal
dimensions and `True`/`False` for readability. With no seed, the parser chooses
one from 1 to 1,000,000 and prints it. Parsing failures print an error and return
`None` rather than a partially valid configuration.

## Internal representation: closed walls as bits

Each row-major grid cell is an integer whose four low bits describe closed walls:

| Direction | Decimal bit | Hex bit |
| --- | ---: | --- |
| North | 1 | `1` |
| East | 2 | `2` |
| South | 4 | `4` |
| West | 8 | `8` |

`F` (`15`) means all walls closed. Testing `cell & Wall.EAST` asks whether the
east wall is present. Opening it clears that bit, rather than setting an
“open” flag. The neighbor's opposite wall must also be cleared:

```text
left:  F & ~EAST = D     right: F & ~WEST = 7
          same shared passage, recorded in both cells
```

The shared direction tuple includes row/column offsets and opposite bits so
generation and solving use the same convention. Configuration/renderer endpoints
are `(x,y)`, but generator cells and `BFS` endpoints are `(row,column)`.
The application swaps coordinates explicitly when constructing the solver.

## Generation, step by step

### 1. Reserve the `42` cells

The motif is defined by a five-row, seven-column occupancy pattern:

```text
1000111
1000001
1110111
0010100
0010111
```

Only `1` positions are blocked; `0` positions remain ordinary maze cells.
Candidate placements are ordered by Manhattan distance from the center, with
row/column tie-breaks. The first placement avoiding entry and exit is chosen.
Non-perfect mode also protects the four corners and center.

A grid physically smaller than the motif omits it with a message. A sufficiently
large grid that has no legal placement raises an error instead of silently
dropping the pattern. Placement avoids required cells; graph connectivity is
validated afterward, so valid dimensions alone do not guarantee generation.

### 2. Initialize the graph

`_reset` fills the grid with `F`, creates the list of ordinary cells, and
enumerates candidate edges to right/down neighbors. Considering those two
directions avoids listing every undirected edge twice. Blocked cells never
become passage endpoints and remain fully closed.

`DisjointSet` creates one component per ordinary cell. Its parent dictionary
tracks component roots; its size dictionary supports balanced merging.

### 3. Build a spanning tree with randomized Kruskal

The generator shuffles edges with its own `random.Random(seed)`. For each edge:

1. Find each endpoint's component root.
2. If roots match, skip the edge: opening it would create a cycle.
3. Otherwise join the smaller component under the larger one and open the
   shared wall on both cells.

`find` compresses parent paths, shortening future lookups. When ordinary cells
form a connected candidate graph, the selected passages connect them without
cycles. `_valid_maze` checks the component result, reciprocal walls, closed
external borders, and intact blocked cells before returning perfect mode.

For **V ordinary cells**, a connected perfect maze has V−1 undirected passages
and one path between any pair. Reserved cells are excluded from that statement.

### 4. Add legal passages for non-perfect mode

`_braid` visits shuffled dead ends, preferring openings toward other dead ends.
`_try_loop` opens a candidate wall, checks affected 3×3 blocks, and rolls back
if it would create a fully open area. `_add_loops` then opens more candidates
if the minimum cycle count has not been reached.

Non-perfect acceptance requires at least **two independent cycles**, at most
**two dead ends**, and degree at least two at corners and the center. Extra
passages make multiple routes possible while BFS still identifies a shortest
one. This is more restrictive than merely deleting a random wall from a tree.

Generation can retry up to 30 times. An edge-capacity check rejects graphs that
cannot support two cycles before doing futile braiding. The same blocked motif
is retained between attempts; retries reshuffle generation, not pattern placement.

### Cost and repeatability

Union-Find makes component operations efficient, but the complete generator
also performs list-membership checks, pattern searches, validation, and possible
retries. It should not be advertised as uniformly linear-time. A fixed explicit
seed/settings reproduce the observed layout; repeated calls on one generator
advance its RNG, so create a new instance for a fresh same-seed reproduction.

## Solving: BFS and route reconstruction

`BFS.solve()` starts at the entry with a `deque`, visited set, and parent map.
It examines reachable neighbors in fixed north/east/south/west order. A neighbor
must be in bounds and have no blocking wall in the current cell.

When discovering a cell, the solver records its parent and direction letter.
After reaching the exit, it follows parent links backward, reverses the collected
letters, and returns one shortest `N/E/S/W` string. If the exit was never reached,
it raises `ValueError`.

BFS is O(V+E) for this unweighted grid, with O(V) auxiliary storage. In a braided
maze several equally short routes may exist; direction order resolves the
search consistently. The solver does not independently repair an incoherent
external grid; generation is responsible for those invariants.

## Export format, with an actual small example

`write_output` overwrites its UTF-8 destination using LF line endings. It writes
HEIGHT rows of WIDTH uppercase hex digits, a blank line, entry, exit, and route,
each followed by newline.

A generated **2×2 perfect maze, seed 3**, entry `(0,0)` and exit `(1,1)`, exports:

```text
D3
D6

0,0
1,1
ES
```

The grid is too small for the motif, so the generator separately prints its
omission message; that message is not written into the export. `ES` means move
east from the entry, then south to the exit. The outer border remains closed:
entry/exit are cell markers, not holes cut in the external wall.

## Terminal geometry and interaction

`build_canvas` maps each cell to three character columns and two rows. It draws
wall segments, then resolves every intersection by inspecting neighboring
segments and looking up the corresponding Unicode junction glyph. The screen
coordinates are different from both configuration and solver coordinates.

`Renderer` overlays reserved-cell backgrounds, the optional solution path,
and endpoint markers. Colors/path visibility are display state, not changes
to the generated wall grid. `render()` clears/redraws and resets ANSI styling.

The menu can regenerate, toggle the route, change wall color, cycle path/pattern
backgrounds, or exit. Regeneration increments the seed, generates/exports a new
grid, and updates the existing renderer while keeping its display settings.
EOF and Ctrl-C are handled at application level.

Export occurs **before terminal validation**. A noninteractive run can therefore
write a file and then report a display error. Several CLI error paths print a
message and return without a nonzero process status, so status zero alone is
not proof of successful display or generation.

## Reusable API and packaging

The package exports `Config`, `MazeGenerator`, `Parser`, `Renderer`, `Wall`, and
the `solver` module. A caller can generate/solve without a terminal or file write:

```sh
uv run python - <<'PY'
from mazegen import Config, MazeGenerator, solver

config = Config(width=20, height=15, entry=(0, 0), exit=(19, 14),
                output_file="maze.txt", perfect=True, seed=3)
maze = MazeGenerator(config).generate()
entry = (config.entry[1], config.entry[0])
exit_cell = (config.exit[1], config.exit[0])
route = solver.BFS(maze, entry, exit_cell).solve()
print(len(maze), len(maze[0]))
print(len(route), set(route) <= set("NESW"))
PY
```

`output_file` is required configuration even in this example, but no file is
written until the caller invokes `mazegen.exporter.write_output` or uses the
application's `generation()` function. The first printed dimensions are
`15 20`: rows first, then columns.

```sh
uv build
```

[`pyproject.toml`](pyproject.toml) uses `uv_build` to produce a source distribution
and `mazegen-0.1.0-py3-none-any.whl` under `dist/`. Install the wheel into another
environment with `python -m pip install dist/mazegen-0.1.0-py3-none-any.whl`.
It contains the reusable modules and MIT license, not the root interactive
application/configuration or an installed console entry point. Test imports
outside the checkout when checking the installed package, to avoid accidentally
importing the source directory instead.

## Verification and boundaries

`make lint` and `make lint-strict` passed. Representative checks covered twelve
perfect/non-perfect dimension/seed combinations, seed repeatability, reciprocal
walls, connectivity, cycle/dead-end conditions, shortest-route lengths, exports,
and the generated visual above. The reusable package was built successfully.

These checks do not promise that every syntactically valid size can satisfy
pattern and non-perfect constraints. Large dimensions also incur significant
memory/work and can be rejected or fail. The project demonstrates graph
algorithms, invariant-based design, coordinate conversion, serialization,
terminal rendering, and reusable packaging through one shared data model.

## Contributors and license

The project credits **mhaddad** and **domansou**. Existing responsibility notes
attribute generator/renderer/parser work and final cleanup to mhaddad;
solver/license/Makefile/packaging metadata to domansou; and application integration
to both. Copyright (c) 2026 domansou and mhaddad.

The [MIT license](LICENSE.md) applies; preserve its copyright and permission
notice when distributing the software or reusable package.

## Resources

- [Maze generation algorithms](https://en.wikipedia.org/wiki/Maze_generation_algorithm)
- [Disjoint-set data structure](https://en.wikipedia.org/wiki/Disjoint-set_data_structure)
- [Python deque](https://docs.python.org/3/library/collections.html#collections.deque)
- [Pydantic validators](https://docs.pydantic.dev/latest/concepts/validators/)
- [uv build backend](https://docs.astral.sh/uv/concepts/build-backend/)

## AI Usage

The existing disclosure records AI support for explanations, review/refactoring,
parser/renderer edge cases, integration review, and testing ideas. AI assisted
this documentation and checking its examples. The original team attribution
and license remain authoritative; the algorithms described are implemented in
the project source.
