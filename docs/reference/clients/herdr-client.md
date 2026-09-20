# `HerdrClient`

Synchronous client for the herdr Unix socket API.

The constructor page is the shortlink hub for the complete synchronous client
reference. Use the individual pages when you need one operation's exact signature,
parameters, return model, exceptions and examples.

## Constructor

::: herdr_client.HerdrClient.__init__
    options:
      show_root_heading: false
      show_source: true
      show_signature_annotations: true
      separate_signature: true

## Method shortlinks

| Method | Purpose |
| --- | --- |
| [`request`](herdr-client/request.md) | Send a raw or canonical protocol request |
| [`ping`](herdr-client/ping.md) | Check that the server is reachable |
| [`workspace_list`](herdr-client/workspace-list.md) | List workspaces |
| [`tab_list`](herdr-client/tab-list.md) | List tabs, optionally by workspace |
| [`pane_list`](herdr-client/pane-list.md) | List panes, optionally by workspace |
| [`pane_send_text`](herdr-client/pane-send-text.md) | Send literal text to a pane |
| [`pane_send_keys`](herdr-client/pane-send-keys.md) | Send named keys to a pane |
| [`pane_send_input`](herdr-client/pane-send-input.md) | Send text and keys in one operation |
| [`pane_read`](herdr-client/pane-read.md) | Read pane output |
| [`pane_wait_for_output`](herdr-client/pane-wait-for-output.md) | Wait for matching output |
| [`subscribe`](herdr-client/subscribe.md) | Open a server-event subscription |
