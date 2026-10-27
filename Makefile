install:
	uv sync

run:
	uv run python a_maze_ing.py config.txt

debug:
	uv run python -m pdb a_maze_ing.py config.txt

lint:
	uv run flake8 .
	uv run mypy . \
		--warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	uv run flake8 .
	uv run mypy . --strict

clean:
	rm -rf __pycache__ .mypy_cache
	rm -rf */__pycache__ */.mypy_cache
.PHONY: clean install run debug lint lint-strict
