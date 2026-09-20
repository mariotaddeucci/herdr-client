# Client API

The sync and async clients intentionally expose the same operation names, parameters,
return models and protocol envelopes. The async methods must be awaited; both
`subscribe()` methods return a long-lived subscription object.

Both clients connect to a local Unix socket. Ordinary requests use one connection per
response, while subscriptions keep a connection open for server-pushed events.

## Choose a client

| Client | Use it when | Reference |
| --- | --- | --- |
| `HerdrClient` | A script or blocking application owns the call site | [`HerdrClient` constructor](clients/herdr-client.md) |
| `AsyncHerdrClient` | An asyncio application must avoid blocking its event loop | [`AsyncHerdrClient` constructor](clients/async-herdr-client.md) |

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
| `subscribe()` | Consume pushed events | `Subscription` or `AsyncSubscription` |
| `request()` | Call any canonical protocol method | Method-specific result |

## Connection configuration

Both constructors accept `socket_path`, `session` and `timeout`. `socket_path` and
`session` are mutually exclusive; use one or the other:

```python
from herdr_client import HerdrClient

client = HerdrClient(
    socket_path="/tmp/herdr.sock",
    timeout=5.0,
)
```

Use `session="work"` instead of `socket_path` to resolve a named session. If neither
is supplied, the client follows the documented environment and default socket search
order. See the constructor pages for the complete signature and lifecycle details.

## Detailed method pages

The constructor pages below are the entry points for the reference. Each one contains
shortlinks to a separate page for every constructor and method, with the generated
signature and its full docstring:

- [`HerdrClient`](clients/herdr-client.md)
- [`AsyncHerdrClient`](clients/async-herdr-client.md)
