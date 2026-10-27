"""Write the subject's maze output format."""

from .config import Config


def write_output(config: Config, maze: list[list[int]], solution: str) -> None:
    """Write maze rows, endpoints, and the BFS solution as UTF-8 text."""
    with open(config.output_file, "w", encoding="utf-8", newline="\n") as file:
        for row in maze:
            file.write("".join(f"{cell:X}" for cell in row) + "\n")
        file.write("\n")
        file.write(f"{config.entry[0]},{config.entry[1]}\n")
        file.write(f"{config.exit[0]},{config.exit[1]}\n")
        file.write(solution + "\n")
