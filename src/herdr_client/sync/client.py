from __future__ import annotations

import socket
from collections.abc import Iterable, Iterator, Mapping, Sequence
from pathlib import Path
from types import TracebackType
from typing import BinaryIO, Literal, cast, overload

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
from ..stub_methods import SyncMethodStubs
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


class Subscription:
    """Context manager for a long-lived herdr event subscription."""

    def __init__(
        self,
        socket_path: Path,
        timeout: float,
        subscriptions: Iterable[EventSubscription],
    ) -> None:
        self._socket_path = socket_path
        self._timeout = timeout
        self._subscriptions = list(subscriptions)
        self._socket: socket.socket | None = None
        self._file: BinaryIO | None = None
        self._ack: SubscriptionAck | None = None

    @property
    def ack(self) -> SubscriptionAck:
        """Return the server acknowledgement after entering the context."""
        if self._ack is None:
            raise RuntimeError("subscription has not been opened")
        return self._ack

    def __enter__(self) -> Subscription:
        if self._socket is not None:
            raise RuntimeError("subscription is already open")

        self._socket = _connect(self._socket_path, self._timeout)
        try:
            _send_envelope(
                self._socket,
                {
                    "id": _new_id(),
                    "method": "events.subscribe",
                    "params": {"subscriptions": cast(JSONValue, self._subscriptions)},
                },
            )
            self._file = self._socket.makefile("rb")
            response = _read_json_line(self._file)
            self._ack = _subscription_ack(response)
            return self
        except BaseException:
            self.close()
            raise

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        """Close the subscription connection, if it is open."""
        file, self._file = self._file, None
        if file is not None:
            file.close()
        connection, self._socket = self._socket, None
        if connection is not None:
            connection.close()

    def events(self) -> Iterator[EventEnvelope]:
        """Yield pushed event payloads until the server closes the socket."""
        file = self._file
        if file is None or self._socket is None:
            raise RuntimeError("subscription has not been opened")

        while True:
            line = _readline(file)
            if line == b"":
                return
            if line.strip() == b"":
                continue
            yield _event_envelope(_decode_json(line))


class HerdrClient(SyncMethodStubs):
    """Synchronous client for herdr's newline-delimited Unix socket protocol."""

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
    def request(
        self, method: Literal["ping"], params: PingParams | None = None
    ) -> PongResult: ...

    @overload
    def request(
        self, method: Literal["workspace.list"], params: None = None
    ) -> WorkspaceListResult: ...

    @overload
    def request(
        self, method: Literal["tab.list"], params: TabListParams | None = None
    ) -> TabListResult: ...

    @overload
    def request(
        self, method: Literal["pane.list"], params: PaneListParams | None = None
    ) -> PaneListResult: ...

    @overload
    def request(
        self,
        method: Literal["pane.send_text"],
        params: PaneSendTextParams | None = None,
    ) -> OkResult: ...

    @overload
    def request(
        self,
        method: Literal["pane.send_keys"],
        params: PaneSendKeysParams | None = None,
    ) -> OkResult: ...

    @overload
    def request(
        self,
        method: Literal["pane.send_input"],
        params: PaneSendInputParams | None = None,
    ) -> OkResult: ...

    @overload
    def request(
        self,
        method: Literal["pane.read"],
        params: PaneReadParams | None = None,
    ) -> PaneReadResponse: ...

    @overload
    def request(
        self,
        method: Literal["pane.wait_for_output"],
        params: PaneWaitForOutputParams | None = None,
    ) -> OutputMatchedResult: ...

    @overload
    def request(
        self,
        method: Literal["events.subscribe"],
        params: EventsSubscribeParams | None = None,
    ) -> SubscriptionStartedResult: ...

    @overload
    def request(
        self, method: str, params: Mapping[str, JSONValue] | None = None
    ) -> JsonDict: ...

    def request(
        self, method: str, params: Mapping[str, object] | None = None
    ) -> ResponseResult:
        """Call a canonical herdr socket method and return its result."""
        if method not in CANONICAL_METHODS:
            raise HerdrClientError(f"unsupported herdr socket method: {method}")

        connection = _connect(self.socket_path, self.timeout)
        try:
            _send_envelope(
                connection,
                {
                    "id": _new_id(),
                    "method": method,
                    "params": cast(
                        Mapping[str, JSONValue],
                        params if params is not None else {},
                    ),
                },
            )
            with connection.makefile("rb") as file:
                response = _read_json_line(file)
            return _response_result(response)
        finally:
            connection.close()

    def ping(self) -> PongResult:
        return self.request("ping")

    def workspace_list(self) -> WorkspaceListResult:
        return self.request("workspace.list")

    def tab_list(self, workspace_id: str | None = None) -> TabListResult:
        params: TabListParams = {}
        if workspace_id is not None:
            params["workspace_id"] = workspace_id
        return self.request("tab.list", params)

    def pane_list(self, workspace_id: str | None = None) -> PaneListResult:
        params: PaneListParams = {}
        if workspace_id is not None:
            params["workspace_id"] = workspace_id
        return self.request("pane.list", params)

    def pane_send_text(self, pane_id: str, text: str) -> OkResult:
        params: PaneSendTextParams = {"pane_id": pane_id, "text": text}
        return self.request("pane.send_text", params)

    def pane_send_keys(self, pane_id: str, keys: Sequence[str]) -> OkResult:
        params: PaneSendKeysParams = {"pane_id": pane_id, "keys": list(keys)}
        return self.request("pane.send_keys", params)

    def pane_send_input(
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
        return self.request("pane.send_input", params)

    def pane_read(
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
        return self.request("pane.read", params)

    def pane_wait_for_output(
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
        return self.request("pane.wait_for_output", params)

    def subscribe(self, subscriptions: Iterable[EventSubscription]) -> Subscription:
        """Create a context manager for pushed herdr events."""
        return Subscription(self.socket_path, self.timeout, subscriptions)


def _connect(socket_path: Path, timeout_seconds: float) -> socket.socket:
    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    connection.settimeout(timeout_seconds)
    try:
        connection.connect(str(socket_path))
    except TimeoutError as exc:
        connection.close()
        raise HerdrClientError(
            f"timed out connecting to herdr socket: {socket_path}"
        ) from exc
    except OSError as exc:
        connection.close()
        raise HerdrClientError(
            f"could not connect to herdr socket: {socket_path}"
        ) from exc
    return connection


def _send_envelope(
    connection: socket.socket, envelope: Mapping[str, JSONValue]
) -> None:
    try:
        connection.sendall(_encode_envelope(envelope))
    except TimeoutError as exc:
        raise HerdrClientError("timed out writing to herdr socket") from exc
    except OSError as exc:
        raise HerdrClientError("could not write to herdr socket") from exc


def _read_json_line(file: BinaryIO) -> JsonDict:
    line = _readline(file)
    if line == b"":
        raise HerdrClientError("herdr socket closed before a response was received")
    response = _decode_json(line)
    if not isinstance(response, dict):
        raise HerdrClientError("herdr response must be a JSON object")
    return cast(JsonDict, response)


def _readline(file: BinaryIO) -> bytes:
    try:
        return file.readline()
    except TimeoutError as exc:
        raise HerdrClientError("timed out reading from herdr socket") from exc
    except (ConnectionError, OSError) as exc:
        raise HerdrClientError("could not read from herdr socket") from exc
