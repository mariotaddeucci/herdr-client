from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterable, Mapping, Sequence
from contextlib import suppress
from pathlib import Path
from types import TracebackType
from typing import Literal, cast, overload

from ..exceptions import HerdrClientError
from ..protocol import (
    CANONICAL_METHODS,
    JsonDict,
    _decode_json,
    _encode_envelope,
    _event_envelope,
    _new_id,
    _response_result,
    _subscription_ack,
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


async def _close_writer(writer: asyncio.StreamWriter) -> None:
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

    async def __aenter__(self) -> AsyncSubscription:
        if self._writer is not None:
            raise RuntimeError("subscription is already open")

        self._reader, self._writer = await _connect(self._socket_path, self._timeout)
        try:
            await _send_envelope(
                self._writer,
                self._timeout,
                {
                    "id": _new_id(),
                    "method": "events.subscribe",
                    "params": {"subscriptions": cast(JSONValue, self._subscriptions)},
                },
            )
            response = await _read_json_line(self._reader, self._timeout)
            self._ack = _subscription_ack(response)
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
            await _close_writer(writer)

    async def events(self) -> AsyncIterator[EventEnvelope]:
        """Yield pushed event payloads until the server closes the socket."""
        reader = self._reader
        if reader is None or self._writer is None:
            raise RuntimeError("subscription has not been opened")

        while True:
            line = await _readline(reader, self._timeout)
            if line == b"":
                return
            if line.strip() == b"":
                continue
            yield _event_envelope(_decode_json(line))


class AsyncHerdrClient(AsyncMethodStubs):
    """Async client for herdr's newline-delimited Unix socket protocol."""

    def __init__(
        self,
        socket_path: str | Path | None = None,
        timeout: float = 5.0,
        session: str | None = None,
    ) -> None:
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
        self, method: str, params: Mapping[str, object] | None = None
    ) -> ResponseResult:
        """Call a canonical herdr socket method and return its result."""
        if method not in CANONICAL_METHODS:
            raise HerdrClientError(f"unsupported herdr socket method: {method}")

        reader, writer = await _connect(self.socket_path, self.timeout)
        try:
            await _send_envelope(
                writer,
                self.timeout,
                {
                    "id": _new_id(),
                    "method": method,
                    "params": cast(
                        Mapping[str, JSONValue],
                        params if params is not None else {},
                    ),
                },
            )
            response = await _read_json_line(reader, self.timeout)
            return _response_result(response)
        finally:
            await _close_writer(writer)

    async def ping(self) -> PongResult:
        return await self.request("ping")

    async def workspace_list(self) -> WorkspaceListResult:
        return await self.request("workspace.list")

    async def tab_list(self, workspace_id: str | None = None) -> TabListResult:
        params: TabListParams = {}
        if workspace_id is not None:
            params["workspace_id"] = workspace_id
        return await self.request("tab.list", params)

    async def pane_list(self, workspace_id: str | None = None) -> PaneListResult:
        params: PaneListParams = {}
        if workspace_id is not None:
            params["workspace_id"] = workspace_id
        return await self.request("pane.list", params)

    async def pane_send_text(self, pane_id: str, text: str) -> OkResult:
        params: PaneSendTextParams = {"pane_id": pane_id, "text": text}
        return await self.request("pane.send_text", params)

    async def pane_send_keys(self, pane_id: str, keys: Sequence[str]) -> OkResult:
        params: PaneSendKeysParams = {"pane_id": pane_id, "keys": list(keys)}
        return await self.request("pane.send_keys", params)

    async def pane_send_input(
        self,
        pane_id: str,
        text: str = "",
        keys: Sequence[str] | None = None,
    ) -> OkResult:
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
        """Create an async context manager for pushed herdr events."""
        return AsyncSubscription(self.socket_path, self.timeout, subscriptions)


async def _connect(
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


async def _send_envelope(
    writer: asyncio.StreamWriter,
    timeout_seconds: float,
    envelope: Mapping[str, JSONValue],
) -> None:
    try:
        writer.write(_encode_envelope(envelope))
        async with asyncio.timeout(timeout_seconds):
            await writer.drain()
    except TimeoutError as exc:
        raise HerdrClientError("timed out writing to herdr socket") from exc
    except OSError as exc:
        raise HerdrClientError("could not write to herdr socket") from exc


async def _read_json_line(
    reader: asyncio.StreamReader, timeout_seconds: float
) -> JsonDict:
    line = await _readline(reader, timeout_seconds)
    if line == b"":
        raise HerdrClientError("herdr socket closed before a response was received")
    response = _decode_json(line)
    if not isinstance(response, dict):
        raise HerdrClientError("herdr response must be a JSON object")
    return cast(JsonDict, response)


async def _readline(reader: asyncio.StreamReader, timeout_seconds: float) -> bytes:
    try:
        async with asyncio.timeout(timeout_seconds):
            return await reader.readline()
    except TimeoutError as exc:
        raise HerdrClientError("timed out reading from herdr socket") from exc
    except (ConnectionError, OSError, asyncio.IncompleteReadError) as exc:
        raise HerdrClientError("could not read from herdr socket") from exc
