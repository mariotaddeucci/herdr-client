# Types

The package exports schema-derived `TypedDict` models from `herdr_client` and
`herdr_client.types`. They remain regular dictionaries at runtime.

## Common result types

| Type | Use |
| --- | --- |
| `PongResult` | Result returned by `ping()` |
| `WorkspaceListResult` | Result returned by `workspace_list()` |
| `TabListResult` | Result returned by `tab_list()` |
| `PaneListResult` | Result returned by `pane_list()` |
| `PaneReadResponse` | Result returned by `pane_read()` |
| `OutputMatchedResult` | Result returned by `pane_wait_for_output()` |
| `OkResult` | Successful command result |
| `SubscriptionAck` | Acknowledgement returned when a subscription starts |

## Common parameter types

| Type | Use |
| --- | --- |
| `PaneReadParams` | Parameters for pane reads |
| `PaneSendTextParams` | Parameters for text input |
| `PaneSendKeysParams` | Parameters for key input |
| `PaneSendInputParams` | Combined text and key input |
| `PaneWaitForOutputParams` | Output matching and wait options |
| `EventSubscription` | Subscription filter definition |
| `ReadSource` | `visible`, `recent`, `recent_unwrapped` or `detection` |
| `ReadFormat` | `text` or `ansi` |
| `OutputMatch` | Schema-defined output match object |

## JSON types

`JSONValue` describes recursive JSON values and `JsonObject` describes a mutable JSON
object. The generic `request()` fallback returns `JsonObject`.

## Type checking example

```python
from herdr_client import HerdrClient, PaneReadResponse

result: PaneReadResponse = HerdrClient().pane_read("pane-id")
text: str = result["text"]
```

For the complete generated model surface, inspect `herdr_client.generated_types` and
the aliases re-exported by `herdr_client.types`.
