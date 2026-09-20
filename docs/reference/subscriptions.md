# Subscription API

Subscriptions keep a Unix socket open and yield server-pushed event envelopes. They
are normally created through a client's `subscribe()` method rather than instantiated
directly.

| Subscription | Lifecycle | Reference |
| --- | --- | --- |
| `Subscription` | Synchronous context manager and iterator | [`Subscription` constructor](subscriptions/subscription.md) |
| `AsyncSubscription` | Asynchronous context manager and async iterator | [`AsyncSubscription` constructor](subscriptions/async-subscription.md) |

Both objects expose an acknowledgement, a context-manager lifecycle and an event
iterator. The sync object uses `close()` and `events()`; the async object uses
`aclose()` and the async generator returned by `events()`.

Each constructor page contains shortlinks to a separate page for every lifecycle
method, including the context-manager hooks.
