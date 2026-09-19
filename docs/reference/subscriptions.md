# Subscription API

Subscriptions keep a Unix socket open and yield server-pushed event envelopes.

## Synchronous subscription

::: herdr_client.Subscription

## Asynchronous subscription

::: herdr_client.AsyncSubscription

Both objects expose an acknowledgement, a context manager lifecycle and an event
iterator. The sync object uses `close()` and `events()`. The async object uses
`aclose()` and the async generator returned by `events()`.
