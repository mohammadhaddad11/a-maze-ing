*This activity has been created as part of the 42 curriculum by mhaddad, yalsaleh.*

# A-Maze-ing

## Description

A-Maze-ing is a Python project that generates a maze from a configuration file,
finds a shortest path, exports hexadecimal wall data, and displays the result in
an interactive Unicode terminal. The goal is to practise algorithms, modular
programming, and building a reusable Python package.

The generator uses randomized iterative depth-first search (DFS) with an
explicit stack and optional braiding. Both
modes keep ordinary cells connected, shared walls coherent, external borders
closed, and avoid fully open 3×3 areas. Fully closed cells form a visible “42”
when an eligible placement exists; physically undersized mazes report that the
pattern was omitted, while fitting mazes must have a legal placement.

## Instructions

Use Python 3.10 or later, [uv](https://docs.astral.sh/uv/), Make, and a Unix-like
terminal supporting Unicode, ANSI colors, and cursor movement. Pydantic is the
runtime dependency. Run these commands from the project root; Python source
does not need a separate compilation step:

```sh
make install
. .venv/bin/activate
python3 a_maze_ing.py config.txt
```

`make install` runs `uv sync` to prepare the environment and development tools.
The program accepts exactly one argument: a configuration filename, which can
be different from `config.txt`. You can also run it with:

```sh
make run
# Or use a different configuration file:
# Replace config.txt below with that filename.
uv run python a_maze_ing.py config.txt
```

`make run` uses the supplied `config.txt`; `make debug` runs it through `pdb`.
The terminal must have at least `max(3 * WIDTH + 2, 30)` columns and
`2 * HEIGHT + 11` rows, including room for the menu. The supplied 40×20 grid
needs 122 columns and 51 rows. Enlarge the terminal or zoom out if needed.
A successful non-interactive run exports the maze, then reports that display
requires a terminal. Relative file paths use the current working directory.

### Configuration format

Use one `KEY=VALUE` pair per line, in any order. Blank lines and comment lines
starting with `#` (also after indentation) are ignored. Comments occupy their
own line. Keys are case-insensitive and surrounding key/value whitespace is
ignored. Duplicate or unknown keys, missing required keys, and invalid values
are reported as errors.

| Key | Required | Recommended format |
| --- | --- | --- |
| `WIDTH` | Yes | Positive integer number of columns |
| `HEIGHT` | Yes | Positive integer number of rows |
| `ENTRY` | Yes | Nonnegative integers `x,y`, inside the grid |
| `EXIT` | Yes | Nonnegative integers `x,y`, inside the grid; different from entry |
| `OUTPUT_FILE` | Yes | Nonempty output filename/path |
| `PERFECT` | Yes | `True` or `False`, case-insensitive |
| `SEED` | No | Nonnegative integer; generated from 1 through 1,000,000 when omitted |

For clarity, write numbers as decimal digits without signs, use `True`/`False`
for booleans, and write coordinates without spaces around the comma.
These recommendations are not all strict validation rules: Pydantic also
accepts signed integer strings such as `+2`, seeds may be negative, and boolean
strings such as `yes`/`no` or `1`/`0` are accepted case-insensitively. Width and
height must still be positive. Coordinate strings are checked separately and
must contain two digit-only components separated by a comma.

The supplied `config.txt` contains:

```text
WIDTH=40
HEIGHT=20
ENTRY=0,0
EXIT=19,14
OUTPUT_FILE=maze.txt
PERFECT=False
```

`PERFECT` must be provided explicitly; the supplied configuration selects
`False` and omits `SEED`. The parser therefore generates an integer from 1
through 1,000,000 at startup. An explicit seed with the same other parameters
reproduces the maze. Regeneration increments the current seed.

### Menu and display

1. Re-generate maze
2. Show/Hide shortest path
3. Change maze wall colors
4. Change solution path color
5. Change 42 pattern color
6. Exit

Enter a number at `Choice (1-6): ` and press Enter. `E` marks the entry and `X`
the exit. The shortest path is initially shown in cyan; the 42 interiors are
initially white. Option 3 randomly selects a different wall color; options 4
and 5 cycle the path and pattern colors. Hiding the path keeps both endpoints
visible. Regeneration rewrites the output file and retains visibility and all
three color settings. EOF and Ctrl-C exit cleanly.

The canvas builds Unicode walls and junctions from wall bits, using three
columns and two rows per cell. The renderer overlays endpoints, the path, and
the 42 pattern, then prints the colored canvas using ANSI colors. Color changes
affect the display, not the maze or exported data.

### Output format

`OUTPUT_FILE` is overwritten with:

1. Exactly `HEIGHT` rows, each containing `WIDTH` uppercase hexadecimal digits
   (`0`–`F`), one digit per cell, ordered left to right and top to bottom.
2. One empty line.
3. Entry coordinates as `x,y`.
4. Exit coordinates as `x,y`.
5. The shortest path as a string containing only `N`, `E`, `S`, and `W`.

Every line, including the last, ends with `\n`. There are no spaces, labels, or
ANSI color codes in the output. Each digit encodes closed walls:

| Bit | Value | Direction |
| --- | --- | --- |
| 0 | 1 | North |
| 1 | 2 | East |
| 2 | 4 | South |
| 3 | 8 | West |

A set bit means closed; an unset bit means open. For example, `3` closes north
and east, and `F` closes all four walls. Configuration and footer coordinates
use `(x,y)`; maze arrays and BFS coordinates use `(row,column)`.

## Algorithms and technical choices

We chose **randomized iterative DFS** because it is direct to explain and
naturally produces a spanning tree without a separate component data
structure. The generator starts from the first ordinary cell, keeps a stack
and visited set, chooses a random unvisited neighbor, opens the shared wall,
and backtracks when no unvisited neighbor remains. The configured seed drives
the neighbor choices.

- **Perfect mode (`PERFECT=True`):** the ordinary cells form a spanning tree,
  with no loops and exactly one path between any two ordinary cells.
- **Non-perfect mode (`PERFECT=False`):** braiding opens extra passages at dead
  ends, then a loop pass ensures at least two independent cycles. A board is
  accepted only with at most two dead ends; the four corners and centre remain
  reachable ordinary cells. Openings that create a fully open 3×3 area are
  rejected. Generation tries at most 30 layouts before reporting failure.

The 42 placement protects entry and exit, and also the corners and centre in
non-perfect mode. The complete pattern is centered as closely as possible;
valid positions are tried from closest to farthest with deterministic
row-and-column tie-breaking. A physically undersized grid omits the pattern,
but a fitting grid with no legal placement raises an error. Grids without room
for two loops cannot be used in non-perfect mode.

**Breadth-first search (BFS)** explores open passages using a queue, records
parent links, and reconstructs an `N/E/S/W` route. Since each step has equal
cost, the returned route is shortest in either mode.

## Reusing mazegen

`mazegen/` is the reusable package, exporting `Config`, `Parser`,
`MazeGenerator`, `solver`, `Renderer`, and `Wall`. Its `__init__.py` includes API
documentation. `LICENSE.md` uses the MIT license, allowing reuse and
distribution under its terms. The modules have these roles:

| Module | Responsibility |
| --- | --- |
| `config.py`, `parser.py` | Pydantic value validation; reading `KEY=VALUE` files |
| `walls.py`, `pattern.py` | Wall bits; 42 placement |
| `maze_generator.py`, `solver.py` | Randomized DFS and braiding; BFS shortest path |
| `symbols.py`, `canvas.py`, `renderer.py` | Unicode glyphs; wall geometry and junctions; colored display and overlays |
| `exporter.py` | Exact subject output file format |

Generation can be used without the interactive application and does not write
files or launch a display:

```python
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
generator = MazeGenerator(config)
maze = generator.generate()  # list[list[int]], indexed as maze[row][column]
entry_cell = (config.entry[1], config.entry[0])
exit_cell = (config.exit[1], config.exit[0])
solution = solver.BFS(maze, entry_cell, exit_cell).solve()
print(maze[0][0], solution)
```

Change the size, endpoints, mode, and seed in the named `Config` fields to pass
custom parameters. `generate()` returns the maze as a row-major `list[list[int]]`
of wall-bit values; `BFS.solve()` returns a shortest direction string.
Invalid/impossible generator parameters or an unreachable BFS exit raise
`ValueError`. `Parser().read_config("config.txt")` can read a configuration,
returning `None` after reporting a parsing/file error. `Config` is defined in
`mazegen.config` and validates values independently of file parsing. To write
the same subject output format from another application, call
`mazegen.exporter.write_output(config, maze, solution)`.

### Build and install the distributable

The package uses the `uv_build` backend configured in `pyproject.toml`. To build
a wheel from the current sources at the project root:

```sh
make install
uv run python -m build --wheel --outdir .
```

The distributable is `mazegen-0.1.0-py3-none-any.whl`. To install that root-level
wheel into a separate environment, run from the project root:

```sh
python3 -m venv /tmp/mazegen-check
/tmp/mazegen-check/bin/python -m pip install ./mazegen-0.1.0-py3-none-any.whl
```

Use that environment's Python to run the example from outside the source
directory when checking the installed package.

## Verification and maintenance

```sh
make lint
make clean
```

`lint` executes `flake8 .` and the required command:

```sh
mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
```

`make lint-strict` additionally provides the optional `mypy . --strict` check.
`make clean` removes Python and mypy caches. Internal regression checks are
development-only and are not part of the submission or reusable package.
The subject's `maze_analyzer.py`, supplied in `a_maze_ing-analyzer.tgz`, was used to
check wall coherence, connectivity, and generation-mode verdicts.

## Team and project management

### Original responsibilities

- **yalsaleh:** `maze_generator.py`, `renderer.py`, and `parser.py`.
- **mhaddad:** `solver.py`, `LICENSE.md`, `Makefile`, and `pyproject.toml`.
  mhaddad performed the final refactoring and code cleanup during integration.
- **Both:** shared work on `a_maze_ing.py`, which connects the components.



### Planning and evolution

We first divided the work into parsing, generation, solving, rendering, and
application integration, and made each component work independently. During
integration and subject review, configuration handling, output generation,
terminal interactions, packaging, and edge cases needed more work. Our plan
then shifted to testing the modules together and fixing compliance issues.
mhaddad carried out the final refactoring and code cleanup without replacing
the original algorithms.

### What worked well and what could improve

Separate modules let us work in parallel and made debugging easier. Testing
components independently helped us locate integration problems. Sharing the
wall-bit representation also kept generation, solving, rendering, and output
generation consistent.

If we restarted, we would define module interfaces earlier, especially between
the renderer, solver, and main application. We would also test subject edge
cases and packaging sooner, using an early checklist based on the PDF to
reduce late compliance work.

### Tools used

Python, uv, Make, Git,  pdb, flake8, mypy, Python unittest/project test
scripts, the Python build frontend, `maze_analyzer.py`, and ChatGPT/AI tools for explanations and review.

## Resources

- [Python deque and BFS queue support](https://docs.python.org/3/library/collections.html#collections.deque)
- [Maze generation algorithms](https://en.wikipedia.org/wiki/Maze_generation_algorithm)
- [Depth-first search](https://en.wikipedia.org/wiki/Depth-first_search)
- [PEP 257: docstring conventions](https://peps.python.org/pep-0257/)
- [uv build backend](https://docs.astral.sh/uv/concepts/build-backend/)

### AI use

We used AI as a support tool for understanding programming and terminal-rendering
concepts, reviewing edge cases, and reviewing/refactoring code. It helped check
parser and renderer edge cases, review integration between the generator,
solver, renderer, and main application, and suggest small refactoring/compliance
improvements and testing scenarios based on the subject.

The team developed the original generator, solver, parser, renderer, and project
structure. AI mainly helped with explanations, review, testing ideas, and
identifying edge cases.
