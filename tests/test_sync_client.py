from __future__ import annotations

import json
import socket
import tempfile
import threading
import time
import uuid
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest

from herdr_client import (
    AsyncHerdrClient,
    HerdrApiError,
    HerdrClient,
    HerdrClientError,
    Subscription,
)
from herdr_client.async_client import AsyncHerdrClient as AsyncSubpackageClient
from herdr_client.client import AsyncHerdrClient as LegacyAsyncClient
from herdr_client.sync import HerdrClient as SyncSubpackageClient

JsonDict = dict[str, Any]
ResponseFactory = Callable[[JsonDict], JsonDict]
Response = JsonDict | ResponseFactory


class FakeSyncHerdrServer:
    def __init__(self) -> None:
        self.socket_path = (
            Path(tempfile.gettempdir()) / f"herdr-sync-test-{uuid.uuid4().hex}.sock"
        )
        self.handlers: list[dict[str, Any]] = []
        self.requests: list[JsonDict] = []
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._ready = threading.Event()
        self._stop = threading.Event()
        self._error: BaseException | None = None

    def start(self) -> None:
        self._thread.start()
        assert self._ready.wait(timeout=2), "server did not start"

    def close(self) -> None:
        self._stop.set()
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.connect(str(self.socket_path))
        except OSError:
            pass
        self._thread.join(timeout=2)
        if self.socket_path.exists():
            self.socket_path.unlink()
        if self._error is not None:
            raise self._error

    def _serve(self) -> None:
        if self.socket_path.exists():
            self.socket_path.unlink()
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(str(self.socket_path))
        server.listen()
        server.settimeout(0.1)
        self._ready.set()
        try:
            while not self._stop.is_set():
                try:
                    connection, _ = server.accept()
                except TimeoutError:
                    continue
                with connection:
                    raw = self._recv_line(connection)
                    if not raw:
                        continue
                    request = json.loads(raw)
                    self.requests.append(request)
                    handler = (
                        self.handlers.pop(0) if self.handlers else {"responses": []}
                    )
                    time.sleep(handler.get("delay", 0.0))
                    for response in handler.get("responses", []):
                        payload = response(request) if callable(response) else response
                        try:
                            connection.sendall(json.dumps(payload).encode() + b"\n")
                        except OSError:
                            break
        except BaseException as exc:  # noqa: BLE001  # surfaced in close()
            self._error = exc
        finally:
            server.close()

    @staticmethod
    def _recv_line(connection: socket.socket) -> str:
        chunks: list[bytes] = []
        while True:
            chunk = connection.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
            if b"\n" in chunk:
                break
        data = b"".join(chunks)
        return data.splitlines()[0].decode() if data else ""


@pytest.fixture
def sync_server() -> Iterator[FakeSyncHerdrServer]:
    server = FakeSyncHerdrServer()
    server.start()
    yield server
    server.close()


def test_public_imports_expose_both_clients() -> None:
    assert HerdrClient is SyncSubpackageClient
    assert AsyncHerdrClient is AsyncSubpackageClient
    assert LegacyAsyncClient is AsyncHerdrClient
    assert Subscription.__name__ == "Subscription"


def test_ping_round_trips_over_unix_socket(sync_server: FakeSyncHerdrServer) -> None:
    sync_server.handlers = [
        {
            "responses": [
                lambda request: {
                    "id": request["id"],
                    "result": {"type": "pong", "version": "0.2.0"},
                }
            ]
        }
    ]
    client = HerdrClient(socket_path=sync_server.socket_path)

    result = client.ping()

    assert result == {"type": "pong", "version": "0.2.0"}
    assert sync_server.requests[0]["method"] == "ping"
    assert sync_server.requests[0]["params"] == {}


def test_helpers_preserve_request_parameters(sync_server: FakeSyncHerdrServer) -> None:
    sync_server.handlers = [
        {"responses": [{"id": "1", "result": {"type": "ok"}}]} for _ in range(5)
    ]
    client = HerdrClient(socket_path=sync_server.socket_path)

    client.workspace_list()
    client.tab_list(workspace_id="w1")
    client.pane_list()
    client.pane_read("w1-1", lines=None, strip_ansi=False, format="text")
    client.pane_wait_for_output(
        "w1-1",
        {"type": "substring", "value": "ready"},
        lines=10,
        timeout_ms=1000,
    )

    assert [request["method"] for request in sync_server.requests] == [
        "workspace.list",
        "tab.list",
        "pane.list",
        "pane.read",
        "pane.wait_for_output",
    ]
    assert sync_server.requests[1]["params"] == {"workspace_id": "w1"}
    assert sync_server.requests[2]["params"] == {}
    assert sync_server.requests[3]["params"] == {
        "pane_id": "w1-1",
        "source": "recent",
        "strip_ansi": False,
        "format": "text",
    }
    assert sync_server.requests[4]["params"] == {
        "pane_id": "w1-1",
        "source": "recent",
        "match": {"type": "substring", "value": "ready"},
        "strip_ansi": True,
        "lines": 10,
        "timeout_ms": 1000,
    }


def test_pane_send_input_sends_text_and_keys(sync_server: FakeSyncHerdrServer) -> None:
    sync_server.handlers = [{"responses": [{"id": "1", "result": {"type": "ok"}}]}]
    client = HerdrClient(socket_path=sync_server.socket_path)

    result = client.pane_send_input("w123-1", text="status", keys=["Enter"])

    assert result == {"type": "ok"}
    assert sync_server.requests[0]["method"] == "pane.send_input"
    assert sync_server.requests[0]["params"] == {
        "pane_id": "w123-1",
        "text": "status",
        "keys": ["Enter"],
    }


def test_api_errors_raise_exception(sync_server: FakeSyncHerdrServer) -> None:
    sync_server.handlers = [
        {
            "responses": [
                lambda request: {
                    "id": request["id"],
                    "error": {
                        "code": "pane_not_found",
                        "message": "pane w123-99 not found",
                    },
                }
            ]
        }
    ]
    client = HerdrClient(socket_path=sync_server.socket_path)

    with pytest.raises(HerdrApiError) as exc:
        client.pane_send_text("w123-99", "hello")

    assert exc.value.code == "pane_not_found"
    assert "w123-99" in str(exc.value)


def test_request_rejects_non_canonical_method(sync_server: FakeSyncHerdrServer) -> None:
    client = HerdrClient(socket_path=sync_server.socket_path)

    with pytest.raises(HerdrClientError, match="unsupported herdr socket method"):
        client.request("pane.targeted_read", {"pane_id": "w123-1"})


def test_subscription_reads_ack_then_events(sync_server: FakeSyncHerdrServer) -> None:
    sync_server.handlers = [
        {
            "responses": [
                {"id": "1", "result": {"type": "subscription_started"}},
                {
                    "event": "workspace_created",
                    "data": {"workspace": {"workspace_id": "w1"}},
                },
                {"event": "workspace_focused", "data": {"workspace_id": "w1"}},
            ]
        }
    ]
    client = HerdrClient(socket_path=sync_server.socket_path)

    with client.subscribe([{"type": "workspace.created"}]) as subscription:
        events = list(subscription.events())
        assert subscription.ack["result"] == {"type": "subscription_started"}

    assert events == [
        {"event": "workspace_created", "data": {"workspace": {"workspace_id": "w1"}}},
        {"event": "workspace_focused", "data": {"workspace_id": "w1"}},
    ]
    assert sync_server.requests[0]["method"] == "events.subscribe"
    assert sync_server.requests[0]["params"] == {
        "subscriptions": [{"type": "workspace.created"}]
    }


def test_subscription_api_errors_close_the_socket(
    sync_server: FakeSyncHerdrServer,
) -> None:
    sync_server.handlers = [
        {
            "responses": [
                {
                    "id": "1",
                    "error": {"code": "invalid_subscription", "message": "bad filter"},
                }
            ]
        }
    ]
    client = HerdrClient(socket_path=sync_server.socket_path)
    subscription = client.subscribe([])

    with pytest.raises(HerdrApiError, match="invalid_subscription"):
        subscription.__enter__()
    subscription.close()


def test_socket_closure_before_response_raises_client_error(
    sync_server: FakeSyncHerdrServer,
) -> None:
    sync_server.handlers = [{"responses": []}]
    client = HerdrClient(socket_path=sync_server.socket_path)

    with pytest.raises(HerdrClientError, match="closed before a response"):
        client.ping()


def test_read_timeout_raises_client_error(sync_server: FakeSyncHerdrServer) -> None:
    sync_server.handlers = [
        {
            "delay": 0.1,
            "responses": [{"id": "1", "result": {"type": "pong"}}],
        }
    ]
    client = HerdrClient(socket_path=sync_server.socket_path, timeout=0.01)

    with pytest.raises(HerdrClientError, match="timed out reading"):
        client.ping()


def test_subscription_close_is_idempotent(sync_server: FakeSyncHerdrServer) -> None:
    subscription = HerdrClient(socket_path=sync_server.socket_path).subscribe([])

    subscription.close()
    subscription.close()
