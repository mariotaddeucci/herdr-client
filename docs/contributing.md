# Contributing

## Set up the repository

```bash
git clone https://github.com/mariotaddeucci/herdr-client.git
cd herdr-client
uv sync --all-groups
```

## Run checks

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run pyrefly check
uv run mkdocs build --strict
```

The default test command includes coverage and requires at least 90 percent coverage.
Integration tests are opt-in and require a configured live Herdr socket.

## Generated protocol files

The request and response models are generated from the pinned official schema. Do not
hand-edit generated files. Use the repository tools and then run their check modes:

```bash
PYTHONPATH=src uv run python tools/fetch_schema.py --check
PYTHONPATH=src uv run python tools/generate_models.py --check
PYTHONPATH=src uv run python tools/generate_stubs.py --check
```

## Documentation rules

- Keep public documentation in English.
- Use the same `Sync` and `Async` tab labels so tabs stay linked across pages.
- Prefer examples that work with the public API and do not depend on private modules.
- Keep protocol limitations explicit when a method is a named stub.
- Run `uv run mkdocs build --strict` before opening a pull request.
