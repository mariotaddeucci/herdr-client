# `AsyncHerdrClient`

Asynchronous client for the herdr Unix socket API.

The constructor page is the shortlink hub for the complete asynchronous client
reference. Await every operation and use the subscription pages for streaming events.

## Constructor

::: herdr_client.AsyncHerdrClient.__init__
    options:
      show_root_heading: false
      show_source: true
      show_signature_annotations: true
      separate_signature: true

## Method shortlinks

| Method | Purpose |
| --- | --- |
| [`request`](async-herdr-client/request.md) | Send a raw or canonical protocol request |
| [`ping`](async-herdr-client/ping.md) | Check that the server is reachable |
| [`workspace_list`](async-herdr-client/workspace-list.md) | List workspaces |
| [`tab_list`](async-herdr-client/tab-list.md) | List tabs, optionally by workspace |
| [`pane_list`](async-herdr-client/pane-list.md) | List panes, optionally by workspace |
| [`pane_send_text`](async-herdr-client/pane-send-text.md) | Send literal text to a pane |
| [`pane_send_keys`](async-herdr-client/pane-send-keys.md) | Send named keys to a pane |
| [`pane_send_input`](async-herdr-client/pane-send-input.md) | Send text and keys in one operation |
| [`pane_read`](async-herdr-client/pane-read.md) | Read pane output |
| [`pane_wait_for_output`](async-herdr-client/pane-wait-for-output.md) | Wait for matching output |
| [`subscribe`](async-herdr-client/subscribe.md) | Open a server-event subscription |
