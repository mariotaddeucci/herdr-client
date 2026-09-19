# Errors and timeouts

## Client-side errors

`HerdrClientError` is raised when the client cannot complete a request. Common causes
include:

- No socket exists at any configured path.
- The socket cannot be opened.
- The connection times out.
- The server closes the socket before sending a response.
- A response is not valid JSON or has an invalid envelope.
- A method name is not in the canonical protocol registry.

## API errors

`HerdrApiError` is raised when Herdr returns an error envelope. It exposes `code` and
`message` for structured handling:

```python
from herdr_client import HerdrApiError, HerdrClient

try:
    HerdrClient().request("some.method")
except HerdrApiError as exc:
    print(exc.code)
    print(exc.message)
```

## Handle missing sockets

```python
from herdr_client import HerdrClient, HerdrClientError

try:
    HerdrClient(session="missing").ping()
except (FileNotFoundError, HerdrClientError) as exc:
    print(f"Herdr is unavailable: {exc}")
```

Socket path resolution raises `FileNotFoundError` when no candidate exists. Transport
and protocol failures use `HerdrClientError`.

## Timeout behavior

Set a larger client timeout for slow commands or remote workloads:

```python
client = HerdrClient(timeout=30.0)
```

The timeout is expressed in seconds. `pane_wait_for_output()` has a separate
`timeout_ms` parameter that controls how long the Herdr operation waits for output.
