# Client API

The sync and async clients intentionally expose equivalent method names and parameters.
The async methods must be awaited; `subscribe()` returns an async subscription object.

## Synchronous client

::: herdr_client.HerdrClient

## Asynchronous client

::: herdr_client.AsyncHerdrClient

## Choosing a client

Use `HerdrClient` for scripts and blocking applications. Use `AsyncHerdrClient` when
the surrounding application already runs an `asyncio` event loop or needs to monitor
multiple sockets without blocking the loop.
