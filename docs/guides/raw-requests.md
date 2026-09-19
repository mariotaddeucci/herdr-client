# Raw requests

The convenience methods cover the most common operations, but the client can send any
canonical JSON method from the pinned Herdr schema through `request()`.

## Call a canonical method

The method name uses the Herdr protocol name, not the Python convenience name.

=== "Sync"

    ```python
    from herdr_client import HerdrClient

    client = HerdrClient()
    result = client.request(
        "workspace.list",
        {},
    )
    print(result)
    ```

=== "Async"

    ```python
    import asyncio

    from herdr_client import AsyncHerdrClient


    async def main() -> None:
        client = AsyncHerdrClient()
        result = await client.request(
            "workspace.list",
            {},
        )
        print(result)


    asyncio.run(main())
    ```

The `params` argument must be a mapping. Omit it or pass `None` for methods with empty
parameters.

## Typed overloads

Literal method names have precise overloads in type checkers:

```python
from herdr_client import HerdrClient, PongResult

result: PongResult = HerdrClient().request("ping")
```

Dynamic method names use the generic JSON object fallback:

```python
method = "workspace.list"
result = HerdrClient().request(method)
```

## Validate method availability

The package exposes protocol metadata for tooling and discovery:

```python
from herdr_client import CANONICAL_METHODS, METHOD_SCHEMAS

print(len(CANONICAL_METHODS))
print(METHOD_SCHEMAS["pane.read"])
```

Unknown method names raise `HerdrClientError` before a socket connection is opened.
