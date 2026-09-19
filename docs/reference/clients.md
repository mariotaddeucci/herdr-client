# Client API

The sync and async clients intentionally expose the same operation names, parameters
and return models. The async methods must be awaited; `subscribe()` returns an async
subscription object.

Both clients connect to a local Unix socket and close ordinary request connections
after one response. Use a subscription when the server needs to push events over a
long-lived connection.

## Operation map

| Operation | Purpose | Result |
| --- | --- | --- |
| `ping()` | Verify that the socket is reachable | `PongResult` |
| `workspace_list()` | List available workspaces | `WorkspaceListResult` |
| `tab_list()` | List tabs, optionally filtered by workspace | `TabListResult` |
| `pane_list()` | List panes, optionally filtered by workspace | `PaneListResult` |
| `pane_send_text()` | Send literal text to a pane | `OkResult` |
| `pane_send_keys()` | Send named keys to a pane | `OkResult` |
| `pane_send_input()` | Send text and keys together | `OkResult` |
| `pane_read()` | Read pane output | `PaneReadResponse` |
| `pane_wait_for_output()` | Wait for a match in pane output | `OutputMatchedResult` |
| `subscribe()` | Consume pushed events | `Subscription` |
| `request()` | Call any canonical protocol method | Method-specific result |

## Connection configuration

The constructor accepts one explicit connection source:

```python
from herdr_client import HerdrClient

client = HerdrClient(
    socket_path="/tmp/herdr.sock",
    timeout=5.0,
)
```

Use `session="work"` instead of `socket_path` to resolve a named session. If neither
is supplied, the client follows the documented environment and default socket search
order.

## Synchronous client

::: herdr_client.HerdrClient
    options:
      members:
        - __init__
        - request
        - ping
        - workspace_list
        - tab_list
        - pane_list
        - pane_send_text
        - pane_send_keys
        - pane_send_input
        - pane_read
        - pane_wait_for_output
        - subscribe
      inherited_members: false
      show_if_no_docstring: true
      show_signature_annotations: true
      separate_signature: true
      show_source: true

## Asynchronous client

::: herdr_client.AsyncHerdrClient
    options:
      members:
        - __init__
        - request
        - ping
        - workspace_list
        - tab_list
        - pane_list
        - pane_send_text
        - pane_send_keys
        - pane_send_input
        - pane_read
        - pane_wait_for_output
        - subscribe
      inherited_members: false
      show_if_no_docstring: true
      show_signature_annotations: true
      separate_signature: true
      show_source: true

## Choosing a client

Use `HerdrClient` for scripts and blocking applications. Use `AsyncHerdrClient` when
the surrounding application already runs an `asyncio` event loop or needs to monitor
multiple sockets without blocking the loop.
