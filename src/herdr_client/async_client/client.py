from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterable, Mapping, Sequence
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Self, cast, overload

if TYPE_CHECKING:
    from types import TracebackType

from ..exceptions import HerdrClientError
from ..protocol import (
    CANONICAL_METHODS,
    JsonDict,
    decode_json,
    encode_envelope,
    event_envelope,
    new_id,
    response_result,
    subscription_ack,
)
from ..stub_methods import AsyncMethodStubs
from ..transport import resolve_socket_path
from ..types import (
    EventEnvelope,
    EventsSubscribeParams,
    EventSubscription,
    JSONValue,
    OkResult,
    OutputMatch,
    OutputMatchedResult,
    PaneListParams,
    PaneListResult,
    PaneReadParams,
    PaneReadResponse,
    PaneSendInputParams,
    PaneSendKeysParams,
    PaneSendTextParams,
    PaneWaitForOutputParams,
    PingParams,
    PongResult,
    ReadFormat,
    ReadSource,
    ResponseResult,
    SubscriptionAck,
    SubscriptionStartedResult,
    TabListParams,
    TabListResult,
    WorkspaceListResult,
)


async def close_writer(writer: asyncio.StreamWriter) -> None:
    writer.close()
    with suppress(ConnectionError, OSError):
        await writer.wait_closed()


class AsyncSubscription:
    """Async context manager for a long-lived herdr event subscription."""

    def __init__(
        self,
        socket_path: Path,
        timeout: float,
        subscriptions: Iterable[EventSubscription],
    ) -> None:
        self._socket_path = socket_path
        self._timeout = timeout
        self._subscriptions = list(subscriptions)
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._ack: SubscriptionAck | None = None

    @property
    def ack(self) -> SubscriptionAck:
        """Return the server acknowledgement after entering the context."""
        if self._ack is None:
            raise RuntimeError("subscription has not been opened")
        return self._ack

    async def __aenter__(self) -> Self:
        if self._writer is not None:
            raise RuntimeError("subscription is already open")

        self._reader, self._writer = await connect_socket(
            self._socket_path, self._timeout
        )
        try:
            await send_envelope(
                self._writer,
                self._timeout,
                {
                    "id": new_id(),
                    "method": "events.subscribe",
                    "params": {"subscriptions": cast("JSONValue", self._subscriptions)},
                },
            )
            response = await read_json_line(self._reader, self._timeout)
            self._ack = subscription_ack(response)
            return self
        except BaseException:
            await self.aclose()
            raise

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close the subscription connection, if it is open."""
        writer, self._writer = self._writer, None
        self._reader = None
        if writer is not None:
            await close_writer(writer)

    async def events(self) -> AsyncIterator[EventEnvelope]:
        """Yield pushed event payloads until the server closes the socket."""
        reader = self._reader
        if reader is None or self._writer is None:
            raise RuntimeError("subscription has not been opened")

        while True:
            line = await read_line(reader, self._timeout)
            if line == b"":
                return
            if line.strip() == b"":
                continue
            yield event_envelope(decode_json(line))


class AsyncHerdrClient(AsyncMethodStubs):
    """Async client for herdr's newline-delimited Unix socket protocol."""

    def __init__(
        self,
        socket_path: str | Path | None = None,
        timeout: float = 5.0,
        session: str | None = None,
    ) -> None:
        """Create an asynchronous client for a Herdr Unix socket.

        Args:
            socket_path: Explicit socket path. When omitted, use Herdr's standard
                socket resolution order.
            timeout: Timeout in seconds for connect, write and read operations.
            session: Named Herdr session to resolve instead of ``socket_path``.

        Raises:
            ValueError: If both ``socket_path`` and ``session`` are provided, or if
                ``timeout`` is not positive.
        """
        if socket_path is not None and session is not None:
            raise ValueError("socket_path and session are mutually exclusive")
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")
        self.socket_path = (
            Path(socket_path)
            if socket_path is not None
            else resolve_socket_path(session=session)
        )
        self.timeout = timeout

    @overload
    async def request(
        self, method: Literal["ping"], params: PingParams | None = None
    ) -> PongResult: ...

    @overload
    async def request(
        self, method: Literal["workspace.list"], params: None = None
    ) -> WorkspaceListResult: ...

    @overload
    async def request(
        self, method: Literal["tab.list"], params: TabListParams | None = None
    ) -> TabListResult: ...

    @overload
    async def request(
        self, method: Literal["pane.list"], params: PaneListParams | None = None
    ) -> PaneListResult: ...

    @overload
    async def request(
        self,
        method: Literal["pane.send_text"],
        params: PaneSendTextParams | None = None,
    ) -> OkResult: ...

    @overload
    async def request(
        self,
        method: Literal["pane.send_keys"],
        params: PaneSendKeysParams | None = None,
    ) -> OkResult: ...

    @overload
    async def request(
        self,
        method: Literal["pane.send_input"],
        params: PaneSendInputParams | None = None,
    ) -> OkResult: ...

    @overload
    async def request(
        self,
        method: Literal["pane.read"],
        params: PaneReadParams | None = None,
    ) -> PaneReadResponse: ...

    @overload
    async def request(
        self,
        method: Literal["pane.wait_for_output"],
        params: PaneWaitForOutputParams | None = None,
    ) -> OutputMatchedResult: ...

    @overload
    async def request(
        self,
        method: Literal["events.subscribe"],
        params: EventsSubscribeParams | None = None,
    ) -> SubscriptionStartedResult: ...

    @overload
    async def request(
        self, method: str, params: Mapping[str, JSONValue] | None = None
    ) -> JsonDict: ...

    async def request(
        self, method: str, params: object | None = None
    ) -> ResponseResult:
        """Call a canonical Herdr socket method and return its result.

        Use the convenience methods when one exists. This low-level operation is
        useful for canonical protocol methods that do not yet have a wrapper.

        Args:
            method: Canonical JSON method name, such as ``"pane.read"``.
            params: JSON object containing method parameters, or ``None`` for an
                empty parameter object.

        Returns:
            The validated result object returned by Herdr.

        Raises:
            HerdrClientError: If the method is unsupported or the socket exchange
                fails.
            TypeError: If ``params`` is not a mapping.
            HerdrApiError: If Herdr returns an error envelope.

        Example:
            ```python
            await client.request("workspace.list")
            await client.request("pane.read", {"pane_id": "build"})
            ```
        """
        if method not in CANONICAL_METHODS:
            raise HerdrClientError(f"unsupported herdr socket method: {method}")

        reader, writer = await connect_socket(self.socket_path, self.timeout)
        try:
            if params is None:
                request_params: Mapping[str, JSONValue] = {}
            elif isinstance(params, Mapping):
                request_params = cast("Mapping[str, JSONValue]", params)
            else:
                raise TypeError("herdr request params must be a mapping")
            await send_envelope(
                writer,
                self.timeout,
                {
                    "id": new_id(),
                    "method": method,
                    "params": request_params,
                },
            )
            response = await read_json_line(reader, self.timeout)
            return response_result(response)
        finally:
            await close_writer(writer)

    async def ping(self) -> PongResult:
        """Check that the Herdr socket is reachable.

        Returns:
            The server's pong result.
        """
        return await self.request("ping")

    async def workspace_list(self) -> WorkspaceListResult:
        """List workspaces visible to the Herdr session.

        Returns:
            A schema-derived workspace list result.
        """
        return await self.request("workspace.list")

    async def tab_list(self, workspace_id: str | None = None) -> TabListResult:
        """List tabs, optionally limited to one workspace.

        Args:
            workspace_id: Workspace identifier to filter by, or ``None`` for all
                workspaces.

        Returns:
            A schema-derived tab list result.
        """
        params: TabListParams = {}
        if workspace_id is not None:
            params["workspace_id"] = workspace_id
        return await self.request("tab.list", params)

    async def pane_list(self, workspace_id: str | None = None) -> PaneListResult:
        """List panes, optionally limited to one workspace.

        Args:
            workspace_id: Workspace identifier to filter by, or ``None`` for all
                workspaces.

        Returns:
            A schema-derived pane list result.
        """
        params: PaneListParams = {}
        if workspace_id is not None:
            params["workspace_id"] = workspace_id
        return await self.request("pane.list", params)

    async def pane_send_text(self, pane_id: str, text: str) -> OkResult:
        """Send literal text to a pane.

        Args:
            pane_id: Target pane identifier.
            text: Text to write to the pane.

        Returns:
            The server's successful command result.
        """
        params: PaneSendTextParams = {"pane_id": pane_id, "text": text}
        return await self.request("pane.send_text", params)

    async def pane_send_keys(self, pane_id: str, keys: Sequence[str]) -> OkResult:
        """Send named key presses to a pane.

        Args:
            pane_id: Target pane identifier.
            keys: Key names in the order they should be sent.

        Returns:
            The server's successful command result.
        """
        params: PaneSendKeysParams = {"pane_id": pane_id, "keys": list(keys)}
        return await self.request("pane.send_keys", params)

    async def pane_send_input(
        self,
        pane_id: str,
        text: str = "",
        keys: Sequence[str] | None = None,
    ) -> OkResult:
        """Send text and key presses in one pane input operation.

        Args:
            pane_id: Target pane identifier.
            text: Literal text to write before sending keys.
            keys: Optional key names in the order they should be sent.

        Returns:
            The server's successful command result.
        """
        params: PaneSendInputParams = {
            "pane_id": pane_id,
            "text": text,
            "keys": list(keys) if keys is not None else [],
        }
        return await self.request("pane.send_input", params)

    async def pane_read(
        self,
        pane_id: str,
        source: ReadSource = "recent",
        lines: int | None = 80,
        strip_ansi: bool = True,
        format: ReadFormat | None = None,
    ) -> PaneReadResponse:
        """Read captured output from a pane.

        Args:
            pane_id: Target pane identifier.
            source: Output source, such as ``"recent"`` or ``"visible"``.
            lines: Maximum number of lines to return, or ``None`` for no limit.
            strip_ansi: Remove ANSI escape sequences when true.
            format: Optional response format, ``"text"`` or ``"ansi"``.

        Returns:
            A typed pane read response containing the requested output.
        """
        params: PaneReadParams = {
            "pane_id": pane_id,
            "source": source,
            "strip_ansi": strip_ansi,
        }
        if lines is not None:
            params["lines"] = lines
        if format is not None:
            params["format"] = format
        return await self.request("pane.read", params)

    async def pane_wait_for_output(
        self,
        pane_id: str,
        match: OutputMatch,
        source: ReadSource = "recent",
        lines: int | None = None,
        timeout_ms: int | None = None,
        strip_ansi: bool = True,
    ) -> OutputMatchedResult:
        """Wait until pane output satisfies a match expression.

        Args:
            pane_id: Target pane identifier.
            match: Schema-defined text or pattern match object.
            source: Output source to inspect.
            lines: Optional maximum number of lines to inspect.
            timeout_ms: Server-side wait timeout in milliseconds.
            strip_ansi: Remove ANSI escape sequences before matching.

        Returns:
            The matched output and match metadata.
        """
        params: PaneWaitForOutputParams = {
            "pane_id": pane_id,
            "source": source,
            "match": match,
            "strip_ansi": strip_ansi,
        }
        if lines is not None:
            params["lines"] = lines
        if timeout_ms is not None:
            params["timeout_ms"] = timeout_ms
        return await self.request("pane.wait_for_output", params)

    def subscribe(
        self, subscriptions: Iterable[EventSubscription]
    ) -> AsyncSubscription:
        """Create an async context manager for pushed Herdr events.

        Args:
            subscriptions: Event filters to register with the server.

        Returns:
            An async subscription context manager. Enter it before iterating over
            ``events()``.

        Example:
            ```python
            async with client.subscribe([{"event": "pane.output"}]) as stream:
                async for event in stream.events():
                    print(event)
            ```
        """
        return AsyncSubscription(self.socket_path, self.timeout, subscriptions)


async def connect_socket(
    socket_path: Path,
    timeout_seconds: float,
) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    try:
        async with asyncio.timeout(timeout_seconds):
            return await asyncio.open_unix_connection(str(socket_path))
    except TimeoutError as exc:
        raise HerdrClientError(
            f"timed out connecting to herdr socket: {socket_path}"
        ) from exc
    except OSError as exc:
        raise HerdrClientError(
            f"could not connect to herdr socket: {socket_path}"
        ) from exc


async def send_envelope(
    writer: asyncio.StreamWriter,
    timeout_seconds: float,
    envelope: Mapping[str, JSONValue],
) -> None:
    try:
        writer.write(encode_envelope(envelope))
        async with asyncio.timeout(timeout_seconds):
            await writer.drain()
    except TimeoutError as exc:
        raise HerdrClientError("timed out writing to herdr socket") from exc
    except OSError as exc:
        raise HerdrClientError("could not write to herdr socket") from exc


async def read_json_line(
    reader: asyncio.StreamReader, timeout_seconds: float
) -> JsonDict:
    line = await read_line(reader, timeout_seconds)
    if line == b"":
        raise HerdrClientError("herdr socket closed before a response was received")
    response = decode_json(line)
    if not isinstance(response, dict):
        raise HerdrClientError("herdr response must be a JSON object")
    return cast("JsonDict", response)


async def read_line(reader: asyncio.StreamReader, timeout_seconds: float) -> bytes:
    try:
        async with asyncio.timeout(timeout_seconds):
            return await reader.readline()
    except TimeoutError as exc:
        raise HerdrClientError("timed out reading from herdr socket") from exc
    except (ConnectionError, OSError, asyncio.IncompleteReadError) as exc:
        raise HerdrClientError("could not read from herdr socket") from exc
