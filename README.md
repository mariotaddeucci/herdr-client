# herdr-client

Sync and async Python clients for the [herdr](https://github.com/herdrdev/herdr)
Unix socket API. The package implements the canonical newline-delimited JSON
protocol with no runtime dependencies.

[![PyPI](https://img.shields.io/pypi/v/herdr-client)](https://pypi.org/project/herdr-client/)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-16c79a)](https://mariotaddeucci.github.io/herdr-client/)

## Documentation

Read the complete documentation at
<https://mariotaddeucci.github.io/herdr-client/>.

It includes installation, configuration, Sync and Async examples, subscriptions,
typed results, raw requests, errors and the generated API reference.

## Installation

```bash
python -m pip install herdr-client
```

Or with `uv`:

```bash
uv add herdr-client
```

Requirements:

- Python 3.13 or newer.
- A running Herdr instance with an accessible Unix socket.

## Quick example

Synchronous:

```python
from herdr_client import HerdrClient

client = HerdrClient()
print(client.ping())
print(client.workspace_list())
```

Asynchronous:

```python
import asyncio

from herdr_client import AsyncHerdrClient


async def main() -> None:
    client = AsyncHerdrClient()
    print(await client.ping())
    print(await client.workspace_list())


asyncio.run(main())
```

The package name is `herdr-client`; the import package is `herdr_client`.

## Public API

Both clients expose the same operation names:

- `request(method, params)`
- `ping()`
- `workspace_list()`
- `tab_list(workspace_id=None)`
- `pane_list(workspace_id=None)`
- `pane_send_text(pane_id, text)`
- `pane_send_keys(pane_id, keys)`
- `pane_send_input(pane_id, text="", keys=None)`
- `pane_read(pane_id, source="recent", lines=80, strip_ansi=True, format=None)`
- `pane_wait_for_output(...)`
- `subscribe(subscriptions)`

Return values are ordinary dictionaries with schema-derived `TypedDict` types. The
package includes `py.typed` for static type checkers.

## Socket resolution

Without an explicit `socket_path`, clients use this order:

1. `session="name"` in the constructor.
2. `HERDR_SOCKET_PATH`.
3. `HERDR_SESSION=name`.
4. `$HOME/.config/herdr/herdr.sock`.

Named sessions use `$HOME/.config/herdr/sessions/<name>/herdr.sock`.

```python
from pathlib import Path

from herdr_client import AsyncHerdrClient, HerdrClient

sync_client = HerdrClient(socket_path=Path("/run/user/1000/herdr.sock"))
async_client = AsyncHerdrClient(session="docs")
```

## Protocol coverage

The registry follows protocol 22 and contains 103 canonical JSON methods. Ten methods
have convenience wrappers: `ping`, `workspace_list`, `tab_list`, `pane_list`,
`pane_send_text`, `pane_send_keys`, `pane_send_input`, `pane_read`,
`pane_wait_for_output` and `subscribe`.

The remaining canonical methods have named stubs that raise `NotImplementedError`. Use
`request()` for a canonical method without a convenience wrapper. The hybrid
`pane.graphics.stream` transport is not implemented.

## Development

```bash
git clone https://github.com/mariotaddeucci/herdr-client.git
cd herdr-client
uv sync --all-groups
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run pyrefly check
uv run mkdocs build --strict
```

The default test command requires at least 90 percent coverage. Live integration tests
are opt-in and require an explicitly configured Herdr socket.

## Publishing

Package releases are triggered by version tags after PyPI Trusted Publishing is
configured:

```bash
git tag v0.2.0
git push origin v0.2.0
```

Documentation deploys to GitHub Pages from `main`.

## License

Apache License 2.0.
