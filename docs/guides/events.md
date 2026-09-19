# Events

Use `subscribe()` when the application needs to receive server-pushed events. The
subscription object is a context manager in the sync client and an async context
manager in the async client.

## Subscribe to events

=== "Sync"

    ```python
    from herdr_client import HerdrClient

    with HerdrClient().subscribe([{"type": "workspace.created"}]) as subscription:
        print("subscription:", subscription.ack)
        for event in subscription.events():
            print(event)
    ```

=== "Async"

    ```python
    import asyncio

    from herdr_client import AsyncHerdrClient


    async def main() -> None:
        async with AsyncHerdrClient().subscribe(
            [{"type": "workspace.created"}]
        ) as subscription:
            print("subscription:", subscription.ack)
            async for event in subscription.events():
                print(event)


    asyncio.run(main())
    ```

The acknowledgement is available through `subscription.ack` after entering the
context. Calling `close()` or `aclose()` is safe and idempotent.

## Event envelopes

Each event has this general shape:

```python
{
    "event": "workspace.created",
    "data": {
        "type": "workspace_created",
        "workspace": {...},
    },
}
```

Known event data is typed where the schema defines it. Unknown fields remain available
because event envelopes are intentionally forward-compatible.

## Lifecycle recommendations

- Always use the context manager to close the socket on normal and exceptional exits.
- Keep event processing inside the iterator loop short.
- Create a separate subscription when independent consumers need different filters.
- Treat the server closing the socket as the end of the event stream.
