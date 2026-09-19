# Concepts

## Distribution name versus import name

Install the distribution as:

```bash
python -m pip install herdr-client
```

Import it as:

```python
import herdr_client
```

This follows normal Python packaging conventions: the PyPI name uses a hyphen while
the import package uses an underscore.

## One API, two transports

`HerdrClient` uses a blocking Unix socket connection. `AsyncHerdrClient` uses
`asyncio` streams. The public method names, parameters, return models and exceptions
are intentionally equivalent.

## Short-lived versus long-lived calls

Regular methods open a connection, send one newline-delimited JSON request, read one
response and close the connection. Subscriptions keep a connection open so the server
can push events until the context is closed.

## Typed dictionaries remain dictionaries

Return values are normal Python dictionaries. The package adds static type information
without forcing a validation or model-conversion layer on callers.

```python
from herdr_client import HerdrClient, PongResult

result: PongResult = HerdrClient().ping()
print(result["version"])
```
