<div class="hero" markdown>

# herdr-client

Sync and async Python clients for the [herdr](https://github.com/herdrdev/herdr)
Unix socket API.

[Get started](getting-started/installation.md){ .md-button .md-button--primary }
[API reference](reference/clients.md){ .md-button }

</div>

`herdr-client` gives Python applications a typed interface for inspecting and
controlling Herdr workspaces, tabs and panes. It uses the local Unix socket and has
no runtime dependencies.

<div class="feature-grid" markdown>

<div class="feature-card" markdown>

**Sync and async**

Use blocking methods or native `asyncio` methods with the same API surface.

</div>

<div class="feature-card" markdown>

**Typed results**

Responses are ordinary dictionaries with `TypedDict` models and editor-friendly types.

</div>

<div class="feature-card" markdown>

**Local by default**

Connect to a Herdr Unix socket with explicit paths, named sessions or environment variables.

</div>

</div>

## Install

=== "pip"

    ```bash
    python -m pip install herdr-client
    ```

=== "uv"

    ```bash
    uv add herdr-client
    ```

## First request

Both clients expose the same operations. Choose a tab and keep that choice across
the rest of the site.

=== "Sync"

    ```python
    from herdr_client import HerdrClient

    client = HerdrClient()
    print(client.ping())
    ```

=== "Async"

    ```python
    import asyncio

    from herdr_client import AsyncHerdrClient


    async def main() -> None:
        client = AsyncHerdrClient()
        print(await client.ping())


    asyncio.run(main())
    ```

## What is included

- Convenience methods for ping, workspace, tab and pane operations.
- Event subscriptions with sync iterators and async generators.
- Raw access to every canonical JSON method in the Herdr protocol.
- Typed request and response models generated from the official schema.
- Clear client-side and server-side exception types.

The package currently targets Python 3.13 or newer and protocol 22.
