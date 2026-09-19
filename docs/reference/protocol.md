# Protocol coverage

The client follows the official Herdr JSON schema pinned in the repository.

| Metadata | Current value |
| --- | --- |
| Protocol | `22` |
| Schema version | `1` |
| Canonical JSON methods | `103` |
| Convenience wrappers | `10` |
| Runtime dependencies | `0` |

## Convenience wrappers

The implemented wrappers are:

- `ping`
- `workspace_list`
- `tab_list`
- `pane_list`
- `pane_send_text`
- `pane_send_keys`
- `pane_send_input`
- `pane_read`
- `pane_wait_for_output`
- `subscribe`

## Canonical methods without wrappers

The sync and async clients expose named stubs for the other canonical methods. These
stubs raise `NotImplementedError` and identify the method and schema. Use `request()`
when a canonical method does not have a convenience wrapper yet.

This distinction prevents a generated method name from implying that its high-level
behavior has already been implemented.

## Hybrid graphics transport

`pane.graphics.stream` is not a canonical JSON-only operation. It uses an initial JSON
request followed by JSON headers and raw bytes, so it remains separate from `request()`
and is currently not implemented by this client.

## Inspect metadata

```python
from herdr_client import (
    CANONICAL_METHODS,
    METHOD_SCHEMAS,
    SCHEMA_PROTOCOL,
    SCHEMA_VERSION,
)

print(SCHEMA_PROTOCOL, SCHEMA_VERSION)
print("pane.read" in CANONICAL_METHODS)
print(METHOD_SCHEMAS["pane.read"])
```
