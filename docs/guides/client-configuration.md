# Client configuration

## Constructor

Both clients accept the same constructor arguments:

```python
Client(socket_path=None, timeout=5.0, session=None)
```

`socket_path` and `session` are mutually exclusive. `timeout` must be greater than
zero and applies to socket connection, reads and writes.

=== "Sync"

    ```python
    from pathlib import Path

    from herdr_client import HerdrClient

    client = HerdrClient(
        socket_path=Path("/run/user/1000/herdr.sock"),
        timeout=10.0,
    )
    ```

=== "Async"

    ```python
    from pathlib import Path

    from herdr_client import AsyncHerdrClient

    client = AsyncHerdrClient(
        socket_path=Path("/run/user/1000/herdr.sock"),
        timeout=10.0,
    )
    ```

## Socket resolution order

When no explicit path is supplied, the client checks:

1. The `session` constructor argument.
2. `HERDR_SOCKET_PATH`.
3. `HERDR_SESSION`.
4. `$HOME/.config/herdr/herdr.sock`.

Named sessions use:

```text
$HOME/.config/herdr/sessions/<name>/herdr.sock
```

Examples:

```bash
export HERDR_SOCKET_PATH="$HOME/.config/herdr/herdr.sock"
export HERDR_SESSION=docs
```

An explicit `socket_path` takes precedence over environment variables. A named session
passed to the constructor takes precedence over the environment as well.

## Multiple sessions

Use the constructor when a process needs to communicate with a named session:

=== "Sync"

    ```python
    from herdr_client import HerdrClient

    client = HerdrClient(session="docs")
    print(client.ping())
    ```

=== "Async"

    ```python
    import asyncio

    from herdr_client import AsyncHerdrClient


    async def main() -> None:
        client = AsyncHerdrClient(session="docs")
        print(await client.ping())


    asyncio.run(main())
    ```
