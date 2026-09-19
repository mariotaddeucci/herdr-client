# Subscription API

Subscriptions keep a Unix socket open and yield server-pushed event envelopes.

## Synchronous subscription

::: herdr_client.Subscription
    options:
      members:
        - __init__
        - ack
        - __enter__
        - __exit__
        - close
        - events
      inherited_members: false
      show_if_no_docstring: true
      show_signature_annotations: true
      separate_signature: true
      show_source: true

## Asynchronous subscription

::: herdr_client.AsyncSubscription
    options:
      members:
        - __init__
        - ack
        - __aenter__
        - __aexit__
        - aclose
        - events
      inherited_members: false
      show_if_no_docstring: true
      show_signature_annotations: true
      separate_signature: true
      show_source: true

Both objects expose an acknowledgement, a context manager lifecycle and an event
iterator. The sync object uses `close()` and `events()`. The async object uses
`aclose()` and the async generator returned by `events()`.
