# Quickstart

The examples below assume that Herdr is running and that its default socket can be
found. If your server uses a named session or a custom path, see
[Client configuration](../guides/client-configuration.md).

## Inspect a workspace

=== "Sync"

    ```python
    from herdr_client import HerdrClient

    client = HerdrClient()
    pong = client.ping()
    workspaces = client.workspace_list()

    print(f"Herdr {pong['version']}")
    for workspace in workspaces["workspaces"]:
        print(workspace["workspace_id"], workspace["label"])
    ```

=== "Async"

    ```python
    import asyncio

    from herdr_client import AsyncHerdrClient


    async def main() -> None:
        client = AsyncHerdrClient()
        pong = await client.ping()
        workspaces = await client.workspace_list()

        print(f"Herdr {pong['version']}")
        for workspace in workspaces["workspaces"]:
            print(workspace["workspace_id"], workspace["label"])


    asyncio.run(main())
    ```

## Send input and read output

The pane convenience methods accept the pane ID returned by `pane_list()` or other
Herdr operations.

=== "Sync"

    ```python
    from herdr_client import HerdrClient

    client = HerdrClient()
    pane_id = "pane-id-from-herdr"

    client.pane_send_input(pane_id, text="printf 'ready\\n'", keys=["Enter"])
    result = client.pane_wait_for_output(
        pane_id,
        match={"type": "substring", "value": "ready"},
        timeout_ms=5_000,
    )
    print(result)
    ```

=== "Async"

    ```python
    import asyncio

    from herdr_client import AsyncHerdrClient


    async def main() -> None:
        client = AsyncHerdrClient()
        pane_id = "pane-id-from-herdr"

        await client.pane_send_input(
            pane_id,
            text="printf 'ready\\n'",
            keys=["Enter"],
        )
        result = await client.pane_wait_for_output(
            pane_id,
            match={"type": "substring", "value": "ready"},
            timeout_ms=5_000,
        )
        print(result)


    asyncio.run(main())
    ```

## Next steps

- Configure the socket explicitly when running outside the default session.
- Use [workspaces and panes](../guides/workspaces-and-panes.md) to navigate Herdr.
- Use [events](../guides/events.md) for long-lived monitoring.
- Use [raw requests](../guides/raw-requests.md) for canonical methods without wrappers.
