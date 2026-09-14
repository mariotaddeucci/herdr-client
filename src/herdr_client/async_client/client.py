from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterable, Sequence
from pathlib import Path
from typing import Any

from ..exceptions import HerdrClientError
from ..protocol import (
    CANONICAL_METHODS,
    JsonDict,
    _decode_json,
    _encode_envelope,
    _new_id,
    _raise_for_error,
    _response_result,
)
from ..stub_methods import AsyncMethodStubs
from ..transport import resolve_socket_path


async def _close_writer(writer: asyncio.StreamWriter) -> None:
    writer.close()
    try:
        await writer.wait_closed()
    except (ConnectionError, OSError):
        pass


class AsyncSubscription:
    """Async context manager for a long-lived herdr event subscription."""

    def __init__(
        self,
        socket_path: Path,
        timeout: float,
        subscriptions: Iterable[JsonDict],
    ) -> None:
        self._socket_path = socket_path
        self._timeout = timeout
        self._subscriptions = list(subscriptions)
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._ack: JsonDict | None = None

    @property
    def ack(self) -> JsonDict:
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
                    "params": {"subscriptions": self._subscriptions},
                },
            )
            response = await _read_json_line(self._reader, self._timeout)
            _raise_for_error(response)
            self._ack = response
            return self
        except BaseException:
            await self.aclose()
            raise

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: Any,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close the subscription connection, if it is open."""
        writer, self._writer = self._writer, None
        self._reader = None
        if writer is not None:
            await _close_writer(writer)

    async def events(self) -> AsyncIterator[JsonDict]:
        """Yield pushed event payloads until the server closes the socket."""
        reader = self._reader
        if reader is None or self._writer is None:
            raise RuntimeError("subscription has not been opened")

        while True:
            line = await _readline(reader, self._timeout)
            if line == b"":
                return
            if not line.strip():
                continue
            event = _decode_json(line)
            if not isinstance(event, dict):
                raise HerdrClientError("herdr event must be a JSON object")
            yield event


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

    async def request(self, method: str, params: JsonDict | None = None) -> JsonDict:
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
                    "params": params or {},
                },
            )
            response = await _read_json_line(reader, self.timeout)
            return _response_result(response)
        finally:
            await _close_writer(writer)

    async def ping(self) -> JsonDict:
        return await self.request("ping")

    async def workspace_list(self) -> JsonDict:
        return await self.request("workspace.list")

    async def tab_list(self, workspace_id: str | None = None) -> JsonDict:
        params = {"workspace_id": workspace_id} if workspace_id is not None else {}
        return await self.request("tab.list", params)

    async def pane_list(self, workspace_id: str | None = None) -> JsonDict:
        params = {"workspace_id": workspace_id} if workspace_id is not None else {}
        return await self.request("pane.list", params)

    async def pane_send_text(self, pane_id: str, text: str) -> JsonDict:
        return await self.request("pane.send_text", {"pane_id": pane_id, "text": text})

    async def pane_send_keys(self, pane_id: str, keys: Sequence[str]) -> JsonDict:
        return await self.request(
            "pane.send_keys", {"pane_id": pane_id, "keys": list(keys)}
        )

    async def pane_send_input(
        self,
        pane_id: str,
        text: str = "",
        keys: Sequence[str] | None = None,
    ) -> JsonDict:
        return await self.request(
            "pane.send_input",
            {"pane_id": pane_id, "text": text, "keys": list(keys or [])},
        )

    async def pane_read(
        self,
        pane_id: str,
        source: str = "recent",
        lines: int | None = 80,
        strip_ansi: bool = True,
        format: str | None = None,
    ) -> JsonDict:
        params: JsonDict = {
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
        match: JsonDict,
        source: str = "recent",
        lines: int | None = None,
        timeout_ms: int | None = None,
        strip_ansi: bool = True,
    ) -> JsonDict:
        params: JsonDict = {
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

    def subscribe(self, subscriptions: Iterable[JsonDict]) -> AsyncSubscription:
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
    envelope: JsonDict,
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
    return response


async def _readline(reader: asyncio.StreamReader, timeout_seconds: float) -> bytes:
    try:
        async with asyncio.timeout(timeout_seconds):
            return await reader.readline()
    except TimeoutError as exc:
        raise HerdrClientError("timed out reading from herdr socket") from exc
    except (ConnectionError, OSError, asyncio.IncompleteReadError) as exc:
        raise HerdrClientError("could not read from herdr socket") from exc
