# `AsyncSubscription`

Asynchronous context manager for a long-lived Herdr event stream. It is normally
created with [`AsyncHerdrClient.subscribe`](../clients/async-herdr-client/subscribe.md).

## Constructor

::: herdr_client.AsyncSubscription.__init__
    options:
      show_root_heading: false
      show_source: true
      show_signature_annotations: true
      separate_signature: true

## Method shortlinks

| Member | Purpose |
| --- | --- |
| [`ack`](async-subscription/ack.md) | Read the server acknowledgement |
| [`__aenter__`](async-subscription/aenter.md) | Open the async context |
| [`__aexit__`](async-subscription/aexit.md) | Close the async context |
| [`aclose`](async-subscription/aclose.md) | Close the connection explicitly |
| [`events`](async-subscription/events.md) | Iterate asynchronously over events |
