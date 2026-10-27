"""Generate, export and interactively display the configured maze."""

import sys

from mazegen import MazeGenerator, Parser, Config, solver, Renderer
from mazegen.exporter import write_output


def main() -> None:
    """Read the sole config argument and run the six-choice terminal menu."""
    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py config.txt")
        return
    try:
        parser = Parser()
        config: Config | None = parser.read_config(sys.argv[1])
        if config is None:
            return
        maze, solution = generation(config)
        renderer = Renderer(
            maze, solution, show_path=True,
            entry=config.entry, exit=config.exit,
        )
        renderer.render()
        run_menu(config, renderer)

    except (EOFError, KeyboardInterrupt):
        print("\nExiting.")
    except OverflowError:
        print("Error: WIDTH or HEIGHT is too large for this system.")
    except (OSError, ValueError, MemoryError) as error:
        print(f"Error: {error}")


def run_menu(config: Config, rend: Renderer) -> None:
    """Run the six interactive actions while retaining renderer state."""
    while True:
        print(f"Current seed: {config.seed}")
        print(
            """1. Re-generate maze
2. Show/Hide shortest path
3. Change maze wall colors
4. Change solution path color
5. Change 42 pattern color
6. Exit"""
        )
        try:
            choice = int(input("Choice (1-6): "))
        except ValueError:
            print("Please enter a number from 1 to 6.")
            continue
        try:
            match choice:
                case 1:
                    if config.seed is None:
                        raise RuntimeError("Seed is missing")
                    config.seed += 1
                    maze, solution = generation(config)
                    rend.update(maze, solution)
                    rend.render()
                case 2:
                    rend.toggle_path()
                    rend.render()
                case 3:
                    rend.randomize_color()
                    rend.render()
                case 4:
                    rend.rotate_path_color()
                    rend.render()
                case 5:
                    rend.rotate_pattern_color()
                    rend.render()
                case 6:
                    break
                case _:
                    print("Please enter a number from 1 to 6.")
        except OverflowError:
            print("Error: WIDTH or HEIGHT is too large for this system.")
        except (OSError, ValueError, MemoryError) as error:
            print(f"Error: {error}")


def generation(config: Config) -> tuple[list[list[int]], str]:
    """Generate, solve and write the exact subject format; return both values.

    Config endpoints use (x, y). BFS endpoints use (row, column).
    Generation, solving and file errors propagate to main() for reporting.
    """
    generator = MazeGenerator(config)

    maze: list[list[int]] = generator.generate()

    entry_cell = (config.entry[1], config.entry[0])
    exit_cell = (config.exit[1], config.exit[0])
    bfs = solver.BFS(maze, entry_cell, exit_cell)

    solution = bfs.solve()

    write_output(config, maze, solution)

    return maze, solution


if __name__ == "__main__":
    main()
