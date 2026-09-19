# Workspaces and panes

Herdr organizes terminal state into workspaces, tabs and panes. The client exposes
read and input operations for these resources.

## List resources

=== "Sync"

    ```python
    from herdr_client import HerdrClient

    client = HerdrClient()
    workspaces = client.workspace_list()
    tabs = client.tab_list()
    panes = client.pane_list()

    print(workspaces)
    print(tabs)
    print(panes)
    ```

=== "Async"

    ```python
    import asyncio

    from herdr_client import AsyncHerdrClient


    async def main() -> None:
        client = AsyncHerdrClient()
        workspaces = await client.workspace_list()
        tabs = await client.tab_list()
        panes = await client.pane_list()

        print(workspaces)
        print(tabs)
        print(panes)


    asyncio.run(main())
    ```

Pass `workspace_id` to `tab_list()` or `pane_list()` to limit the result:

```python
panes = client.pane_list(workspace_id="workspace-id")
```

## Send text

`pane_send_text()` sends text as a complete input operation. Use
`pane_send_keys()` when the input is represented by key names.

=== "Sync"

    ```python
    from herdr_client import HerdrClient

    client = HerdrClient()
    client.pane_send_text("pane-id", "echo hello")
    client.pane_send_keys("pane-id", ["Enter"])
    ```

=== "Async"

    ```python
    import asyncio

    from herdr_client import AsyncHerdrClient


    async def main() -> None:
        client = AsyncHerdrClient()
        await client.pane_send_text("pane-id", "echo hello")
        await client.pane_send_keys("pane-id", ["Enter"])


    asyncio.run(main())
    ```

`pane_send_input()` combines both operations:

```python
client.pane_send_input("pane-id", text="echo hello", keys=["Enter"])
```
