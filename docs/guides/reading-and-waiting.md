# Reading and waiting

## Read pane output

`pane_read()` returns a typed response containing the pane ID, source, revision, format
and text.

=== "Sync"

    ```python
    from herdr_client import HerdrClient

    result = HerdrClient().pane_read(
        "pane-id",
        source="recent",
        lines=80,
        strip_ansi=True,
        format="text",
    )
    print(result["text"])
    ```

=== "Async"

    ```python
    import asyncio

    from herdr_client import AsyncHerdrClient


    async def main() -> None:
        result = await AsyncHerdrClient().pane_read(
            "pane-id",
            source="recent",
            lines=80,
            strip_ansi=True,
            format="text",
        )
        print(result["text"])


    asyncio.run(main())
    ```

Supported read sources are `visible`, `recent`, `recent_unwrapped` and `detection`.
The supported formats are `text` and `ansi`.

## Wait for output

`pane_wait_for_output()` waits until an output match is found or the requested timeout
expires. The match object is defined by the Herdr schema. For a substring match:

=== "Sync"

    ```python
    from herdr_client import HerdrClient

    result = HerdrClient().pane_wait_for_output(
        "pane-id",
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
        result = await AsyncHerdrClient().pane_wait_for_output(
            "pane-id",
            match={"type": "substring", "value": "ready"},
            timeout_ms=5_000,
        )
        print(result)


    asyncio.run(main())
    ```

Use `lines`, `source` and `strip_ansi` to control the searched output window.
