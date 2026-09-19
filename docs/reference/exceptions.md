# Exceptions

## `HerdrClientError`

Base exception for client-side transport and protocol failures.

```python
from herdr_client import HerdrClientError
```

## `HerdrApiError`

Raised when Herdr responds with an error envelope. It inherits from
`HerdrClientError` and exposes:

| Attribute | Meaning |
| --- | --- |
| `code` | Herdr error code |
| `message` | Human-readable error message |

```python
from herdr_client import HerdrApiError

try:
    ...
except HerdrApiError as exc:
    print(exc.code, exc.message)
```

::: herdr_client.exceptions.HerdrClientError

::: herdr_client.exceptions.HerdrApiError
