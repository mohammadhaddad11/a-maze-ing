from random import randint

from .config import Config


class Parser:
    """Read and validate a maze configuration file."""

    def _get_key_value(self, line: str) -> tuple[str, str]:
        """Return the normalized key and value from one configuration line."""
        parts = line.strip().split("=")

        if len(parts) != 2:
            raise ValueError("expected one KEY=VALUE pair")

        key = parts[0].strip().lower()
        value = parts[1].strip()

        return key, value

    def read_config(self, config_file: str) -> Config | None:
        """Read a configuration file and return its validated settings."""
        try:
            values: dict[str, str] = {}

            with open(config_file, "r", encoding="utf-8") as file:
                for number, line in enumerate(file, 1):
                    if not line.strip() or line.lstrip().startswith("#"):
                        continue

                    try:
                        key, value = self._get_key_value(line)

                        if key in values:
                            raise ValueError(f"duplicate key: {key}")

                        values[key] = value

                    except ValueError as error:
                        raise ValueError(f"line {number}: {error}") from error

            config: Config = Config.model_validate(values)

            if config.seed is None:
                config.seed = randint(1, 1000000)
                print(f"Generated seed: {config.seed}")

            return config

        except (OSError, ValueError) as error:
            print(f"Error: {config_file}: {error}")
            return None
