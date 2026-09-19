# Python API reference

The reference documents the public `herdr_client` surface: synchronous and
asynchronous clients, long-lived event subscriptions, schema-derived result types and
protocol metadata.

Use the client pages when you need an operation signature. Use the types page when you
need to understand the dictionary returned by an operation.

<div class="grid cards" markdown>

-   :material-sync: **Clients**

    Create a sync or async client, inspect workspaces and panes, send input, read
    output and wait for matches.

    [:octicons-arrow-right-24: Open the client API](clients.md)

-   :material-access-point: **Subscriptions**

    Keep a Unix socket open and consume pushed event envelopes with a context manager.

    [:octicons-arrow-right-24: Open the subscription API](subscriptions.md)

-   :material-code-json: **Types**

    Browse typed request parameters, response dictionaries, event envelopes and JSON
    aliases.

    [:octicons-arrow-right-24: Browse the types](types.md)

-   :material-alert-outline: **Exceptions**

    Handle transport failures and error envelopes without losing Herdr's error code or
    message.

    [:octicons-arrow-right-24: Browse exceptions](exceptions.md)

-   :material-database-search: **Protocol coverage**

    See the pinned schema version, canonical method coverage and convenience wrappers.

    [:octicons-arrow-right-24: Inspect protocol coverage](protocol.md)

</div>

## Design guarantees

| Guarantee | Meaning |
| --- | --- |
| Sync/async parity | Both clients expose the same operation names, parameters and result models. |
| Dictionary compatibility | Wire results remain ordinary dictionaries at runtime. |
| Typed boundaries | Public signatures use `TypedDict`, `Literal` and recursive JSON aliases. |
| Local transport | Requests use newline-delimited JSON over a Unix socket. |
| Forward compatibility | Unknown response fields are retained instead of discarded. |

## Typical flow

```python
from herdr_client import HerdrClient

client = HerdrClient()
workspaces = client.workspace_list()
panes = client.pane_list(workspaces["workspaces"][0]["id"])
output = client.pane_read(panes["panes"][0]["id"])
```

For a first request and socket resolution rules, start with the
[getting started guide](../getting-started/quickstart.md).
