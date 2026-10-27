"""Validate maze settings independently of the configuration file format."""

from pydantic import (
    BaseModel, ConfigDict, Field, field_validator, model_validator,
)


class Config(BaseModel):
    """Validate the maze dimensions, endpoints, output, and seed."""

    model_config = ConfigDict(extra="forbid")

    width: int = Field(gt=0)
    height: int = Field(gt=0)
    entry: tuple[int, int]
    exit: tuple[int, int]
    output_file: str = Field(min_length=1)
    perfect: bool
    seed: int | None = None

    @field_validator("entry", "exit", mode="before")
    @classmethod
    def parse_coordinates(cls, value: object) -> object:
        """Parse an endpoint written as an ``x,y`` string."""
        if not isinstance(value, str):
            return value

        parts = value.split(",")
        if len(parts) != 2:
            raise ValueError("coordinates must be x,y")

        x, y = parts
        if not x.isdigit() or not y.isdigit():
            raise ValueError("coordinates must contain integers")
        return int(x), int(y)

    @model_validator(mode="after")
    def validate_endpoints(self) -> "Config":
        """Validate endpoint relationships and configured bounds."""
        if self.entry == self.exit:
            raise ValueError("ENTRY and EXIT must be different")
        for x, y in (self.entry, self.exit):
            if not (0 <= x < self.width and 0 <= y < self.height):
                raise ValueError("ENTRY and EXIT must be inside the maze")
        return self
