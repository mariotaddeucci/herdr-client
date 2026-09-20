# `Subscription`

Synchronous context manager for a long-lived Herdr event stream. It is normally
created with [`HerdrClient.subscribe`](../clients/herdr-client/subscribe.md).

## Constructor

::: herdr_client.Subscription.__init__
    options:
      show_root_heading: false
      show_source: true
      show_signature_annotations: true
      separate_signature: true

## Method shortlinks

| Member | Purpose |
| --- | --- |
| [`ack`](subscription/ack.md) | Read the server acknowledgement |
| [`__enter__`](subscription/enter.md) | Open the subscription context |
| [`__exit__`](subscription/exit.md) | Close the context |
| [`close`](subscription/close.md) | Close the connection explicitly |
| [`events`](subscription/events.md) | Iterate over pushed event envelopes |
