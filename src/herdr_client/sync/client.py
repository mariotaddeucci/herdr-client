from __future__ import annotations

import socket
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path
from typing import Any, BinaryIO

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
from ..stub_methods import SyncMethodStubs
from ..transport import resolve_socket_path


class Subscription:
    """Context manager for a long-lived herdr event subscription."""

    def __init__(
        self,
        socket_path: Path,
        timeout: float,
        subscriptions: Iterable[JsonDict],
    ) -> None:
        self._socket_path = socket_path
        self._timeout = timeout
        self._subscriptions = list(subscriptions)
        self._socket: socket.socket | None = None
        self._file: BinaryIO | None = None
        self._ack: JsonDict | None = None

    @property
    def ack(self) -> JsonDict:
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
                    "params": {"subscriptions": self._subscriptions},
                },
            )
            self._file = self._socket.makefile("rb")
            response = _read_json_line(self._file)
            _raise_for_error(response)
            self._ack = response
            return self
        except BaseException:
            self.close()
            raise

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: Any,
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

    def events(self) -> Iterator[JsonDict]:
        """Yield pushed event payloads until the server closes the socket."""
        file = self._file
        if file is None or self._socket is None:
            raise RuntimeError("subscription has not been opened")

        while True:
            line = _readline(file)
            if line == b"":
                return
            if not line.strip():
                continue
            event = _decode_json(line)
            if not isinstance(event, dict):
                raise HerdrClientError("herdr event must be a JSON object")
            yield event


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

    def request(self, method: str, params: JsonDict | None = None) -> JsonDict:
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
                    "params": params or {},
                },
            )
            with connection.makefile("rb") as file:
                response = _read_json_line(file)
            return _response_result(response)
        finally:
            connection.close()

    def ping(self) -> JsonDict:
        return self.request("ping")

    def workspace_list(self) -> JsonDict:
        return self.request("workspace.list")

    def tab_list(self, workspace_id: str | None = None) -> JsonDict:
        params = {"workspace_id": workspace_id} if workspace_id is not None else {}
        return self.request("tab.list", params)

    def pane_list(self, workspace_id: str | None = None) -> JsonDict:
        params = {"workspace_id": workspace_id} if workspace_id is not None else {}
        return self.request("pane.list", params)

    def pane_send_text(self, pane_id: str, text: str) -> JsonDict:
        return self.request("pane.send_text", {"pane_id": pane_id, "text": text})

    def pane_send_keys(self, pane_id: str, keys: Sequence[str]) -> JsonDict:
        return self.request("pane.send_keys", {"pane_id": pane_id, "keys": list(keys)})

    def pane_send_input(
        self,
        pane_id: str,
        text: str = "",
        keys: Sequence[str] | None = None,
    ) -> JsonDict:
        return self.request(
            "pane.send_input",
            {"pane_id": pane_id, "text": text, "keys": list(keys or [])},
        )

    def pane_read(
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
        return self.request("pane.read", params)

    def pane_wait_for_output(
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
        return self.request("pane.wait_for_output", params)

    def subscribe(self, subscriptions: Iterable[JsonDict]) -> Subscription:
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


def _send_envelope(connection: socket.socket, envelope: JsonDict) -> None:
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
    return response


def _readline(file: BinaryIO) -> bytes:
    try:
        return file.readline()
    except TimeoutError as exc:
        raise HerdrClientError("timed out reading from herdr socket") from exc
    except (ConnectionError, OSError) as exc:
        raise HerdrClientError("could not read from herdr socket") from exc
