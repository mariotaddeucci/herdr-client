from __future__ import annotations

import socket
from collections.abc import Iterable, Iterator, Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO, Literal, Self, cast, overload

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
        """Prepare a synchronous subscription without opening the socket.

        Args:
            socket_path: Unix socket path used for the subscription connection.
            timeout: Timeout in seconds for connect, write and read operations.
            subscriptions: Event filters sent to ``events.subscribe`` when the
                context is entered.

        Example:
            ```python
            subscription = Subscription(
                Path("/tmp/herdr.sock"),
                timeout=5.0,
                subscriptions=[{"event": "pane.output"}],
            )
            ```
        """
        self._socket_path = socket_path
        self._timeout = timeout
        self._subscriptions = list(subscriptions)
        self._socket: socket.socket | None = None
        self._file: BinaryIO | None = None
        self._ack: SubscriptionAck | None = None

    @property
    def ack(self) -> SubscriptionAck:
        """Return the server acknowledgement after entering the context.

        Example:
            ```python
            with client.subscribe([{"event": "pane.output"}]) as stream:
                print(stream.ack["result"])
            ```
        """
        if self._ack is None:
            raise RuntimeError("subscription has not been opened")
        return self._ack

    def __enter__(self) -> Self:
        """Open the subscription and return it for a ``with`` block.

        Example:
            ```python
            with client.subscribe([{"event": "pane.output"}]) as stream:
                for event in stream.events():
                    print(event)
            ```
        """
        if self._socket is not None:
            raise RuntimeError("subscription is already open")

        self._socket = connect_socket(self._socket_path, self._timeout)
        try:
            send_envelope(
                self._socket,
                {
                    "id": new_id(),
                    "method": "events.subscribe",
                    "params": {"subscriptions": cast("JSONValue", self._subscriptions)},
                },
            )
            self._file = self._socket.makefile("rb")
            response = read_json_line(self._file)
            self._ack = subscription_ack(response)
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
        """Close the subscription when leaving a ``with`` block."""
        self.close()

    def close(self) -> None:
        """Close the subscription connection, if it is open.

        Example:
            ```python
            stream = client.subscribe([{"event": "pane.output"}])
            with stream:
                print(stream.ack)
            stream.close()
            ```
        """
        file, self._file = self._file, None
        if file is not None:
            file.close()
        connection, self._socket = self._socket, None
        if connection is not None:
            connection.close()

    def events(self) -> Iterator[EventEnvelope]:
        """Yield pushed event payloads until the server closes the socket.

        Raises:
            RuntimeError: If the subscription has not been opened with ``with``.

        Example:
            ```python
            with client.subscribe([{"event": "pane.output"}]) as stream:
                for event in stream.events():
                    print(event["event"])
            ```
        """
        file = self._file
        if file is None or self._socket is None:
            raise RuntimeError("subscription has not been opened")

        while True:
            line = read_line(file)
            if line == b"":
                return
            if line.strip() == b"":
                continue
            yield event_envelope(decode_json(line))


class HerdrClient(SyncMethodStubs):
    """Synchronous client for herdr's newline-delimited Unix socket protocol."""

    def __init__(
        self,
        socket_path: str | Path | None = None,
        timeout: float = 5.0,
        session: str | None = None,
    ) -> None:
        """Create a synchronous client for a Herdr Unix socket.

        Args:
            socket_path: Explicit socket path. When omitted, use Herdr's standard
                socket resolution order.
            timeout: Timeout in seconds for connect, write and read operations.
            session: Named Herdr session to resolve instead of ``socket_path``.

        Raises:
            ValueError: If both ``socket_path`` and ``session`` are provided, or if
                ``timeout`` is not positive.

        Example:
            ```python
            from herdr_client import HerdrClient

            client = HerdrClient(session="work", timeout=5.0)
            print(client.socket_path)
            ```
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

    def request(self, method: str, params: object | None = None) -> ResponseResult:
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
            client.request("workspace.list")
            client.request("pane.read", {"pane_id": "build"})
            ```
        """
        if method not in CANONICAL_METHODS:
            raise HerdrClientError(f"unsupported herdr socket method: {method}")

        connection = connect_socket(self.socket_path, self.timeout)
        try:
            if params is None:
                request_params: Mapping[str, JSONValue] = {}
            elif isinstance(params, Mapping):
                request_params = cast("Mapping[str, JSONValue]", params)
            else:
                raise TypeError("herdr request params must be a mapping")
            send_envelope(
                connection,
                {
                    "id": new_id(),
                    "method": method,
                    "params": request_params,
                },
            )
            with connection.makefile("rb") as file:
                response = read_json_line(file)
            return response_result(response)
        finally:
            connection.close()

    def ping(self) -> PongResult:
        """Check that the Herdr socket is reachable.

        Returns:
            The server's pong result.

        Example:
            ```python
            client = HerdrClient()
            pong = client.ping()
            print(pong["version"])
            ```
        """
        return self.request("ping")

    def workspace_list(self) -> WorkspaceListResult:
        """List workspaces visible to the Herdr session.

        Returns:
            A schema-derived workspace list result.

        Example:
            ```python
            client = HerdrClient()
            result = client.workspace_list()
            for workspace in result["workspaces"]:
                print(workspace["workspace_id"])
            ```
        """
        return self.request("workspace.list")

    def tab_list(self, workspace_id: str | None = None) -> TabListResult:
        """List tabs, optionally limited to one workspace.

        Args:
            workspace_id: Workspace identifier to filter by, or ``None`` for all
                workspaces.

        Returns:
            A schema-derived tab list result.

        Example:
            ```python
            client = HerdrClient()
            result = client.tab_list(workspace_id="main")
            print(result["tabs"])
            ```
        """
        params: TabListParams = {}
        if workspace_id is not None:
            params["workspace_id"] = workspace_id
        return self.request("tab.list", params)

    def pane_list(self, workspace_id: str | None = None) -> PaneListResult:
        """List panes, optionally limited to one workspace.

        Args:
            workspace_id: Workspace identifier to filter by, or ``None`` for all
                workspaces.

        Returns:
            A schema-derived pane list result.

        Example:
            ```python
            client = HerdrClient()
            result = client.pane_list(workspace_id="main")
            print(result["panes"])
            ```
        """
        params: PaneListParams = {}
        if workspace_id is not None:
            params["workspace_id"] = workspace_id
        return self.request("pane.list", params)

    def pane_send_text(self, pane_id: str, text: str) -> OkResult:
        """Send literal text to a pane.

        Args:
            pane_id: Target pane identifier.
            text: Text to write to the pane.

        Returns:
            The server's successful command result.

        Example:
            ```python
            client = HerdrClient()
            client.pane_send_text("build", "printf 'ready\\n'")
            ```
        """
        params: PaneSendTextParams = {"pane_id": pane_id, "text": text}
        return self.request("pane.send_text", params)

    def pane_send_keys(self, pane_id: str, keys: Sequence[str]) -> OkResult:
        """Send named key presses to a pane.

        Args:
            pane_id: Target pane identifier.
            keys: Key names in the order they should be sent.

        Returns:
            The server's successful command result.

        Example:
            ```python
            client = HerdrClient()
            client.pane_send_keys("build", ["Enter"])
            ```
        """
        params: PaneSendKeysParams = {"pane_id": pane_id, "keys": list(keys)}
        return self.request("pane.send_keys", params)

    def pane_send_input(
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

        Example:
            ```python
            client = HerdrClient()
            client.pane_send_input("build", text="printf 'ready\\n'", keys=["Enter"])
            ```
        """
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
        """Read captured output from a pane.

        Args:
            pane_id: Target pane identifier.
            source: Output source, such as ``"recent"`` or ``"visible"``.
            lines: Maximum number of lines to return, or ``None`` for no limit.
            strip_ansi: Remove ANSI escape sequences when true.
            format: Optional response format, ``"text"`` or ``"ansi"``.

        Returns:
            A typed pane read response containing the requested output.

        Example:
            ```python
            client = HerdrClient()
            result = client.pane_read("build", source="recent", lines=20)
            print(result["text"])
            ```
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

        Example:
            ```python
            client = HerdrClient()
            result = client.pane_wait_for_output(
                "build",
                match={"type": "substring", "value": "ready"},
                timeout_ms=5_000,
            )
            print(result["matched"])
            ```
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
        return self.request("pane.wait_for_output", params)

    def subscribe(self, subscriptions: Iterable[EventSubscription]) -> Subscription:
        """Create a context manager for pushed Herdr events.

        Args:
            subscriptions: Event filters to register with the server.

        Returns:
            A subscription context manager. Enter it before iterating over
            ``events()``.

        The ``subscriptions`` iterable contains event filters, for example
        ``{"event": "pane.output"}``.

        Example:
            ```python
            with client.subscribe([{"event": "pane.output"}]) as stream:
                for event in stream.events():
                    print(event)
            ```
        """
        return Subscription(self.socket_path, self.timeout, subscriptions)


def connect_socket(socket_path: Path, timeout_seconds: float) -> socket.socket:
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


def send_envelope(connection: socket.socket, envelope: Mapping[str, JSONValue]) -> None:
    try:
        connection.sendall(encode_envelope(envelope))
    except TimeoutError as exc:
        raise HerdrClientError("timed out writing to herdr socket") from exc
    except OSError as exc:
        raise HerdrClientError("could not write to herdr socket") from exc


def read_json_line(file: BinaryIO) -> JsonDict:
    line = read_line(file)
    if line == b"":
        raise HerdrClientError("herdr socket closed before a response was received")
    response = decode_json(line)
    if not isinstance(response, dict):
        raise HerdrClientError("herdr response must be a JSON object")
    return cast("JsonDict", response)


def read_line(file: BinaryIO) -> bytes:
    try:
        return file.readline()
    except TimeoutError as exc:
        raise HerdrClientError("timed out reading from herdr socket") from exc
    except (ConnectionError, OSError) as exc:
        raise HerdrClientError("could not read from herdr socket") from exc
