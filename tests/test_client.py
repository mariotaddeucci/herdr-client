from __future__ import annotations

import asyncio
import json
import tempfile
import uuid
from collections.abc import AsyncIterator, Callable
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio

from herdr_client import AsyncHerdrClient, HerdrApiError, HerdrClientError

JsonDict = dict[str, Any]
ResponseFactory = Callable[[JsonDict], JsonDict]
Response = JsonDict | ResponseFactory


class FakeHerdrServer:
    def __init__(self, socket_path: Path) -> None:
        self.socket_path = socket_path
        self.handlers: list[dict[str, Any]] = []
        self.requests: list[JsonDict] = []
        self._server: asyncio.Server | None = None
        self._connections: set[asyncio.Task[None]] = set()

    async def start(self) -> None:
        self._server = await asyncio.start_unix_server(
            self._handle_connection,
            path=str(self.socket_path),
        )

    async def close(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
        for task in self._connections:
            task.cancel()
        if self._connections:
            await asyncio.gather(*self._connections, return_exceptions=True)
        if self.socket_path.exists():
            self.socket_path.unlink()

    async def _handle_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        task = asyncio.current_task()
        if task is not None:
            self._connections.add(task)
        try:
            raw = await reader.readline()
            if not raw:
                return
            request = json.loads(raw)
            self.requests.append(request)
            handler = self.handlers.pop(0)
            await asyncio.sleep(handler.get("delay", 0.0))
            for response in handler.get("responses", []):
                payload = response(request) if callable(response) else response
                writer.write(json.dumps(payload).encode("utf-8") + b"\n")
                await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()
            if task is not None:
                self._connections.discard(task)


@pytest_asyncio.fixture
async def fake_server() -> AsyncIterator[FakeHerdrServer]:
    socket_path = Path(tempfile.gettempdir()) / f"herdr-test-{uuid.uuid4().hex}.sock"
    server = FakeHerdrServer(socket_path)
    await server.start()
    yield server
    await server.close()


async def test_ping_round_trips_over_unix_socket(fake_server: FakeHerdrServer) -> None:
    fake_server.handlers = [
        {
            "responses": [
                lambda request: {
                    "id": request["id"],
                    "result": {"type": "pong", "version": "0.2.0"},
                }
            ]
        }
    ]
    client = AsyncHerdrClient(socket_path=fake_server.socket_path)

    result = await client.ping()

    assert result == {"type": "pong", "version": "0.2.0"}
    assert fake_server.requests[0]["method"] == "ping"
    assert fake_server.requests[0]["params"] == {}


async def test_helpers_preserve_request_parameters(
    fake_server: FakeHerdrServer,
) -> None:
    fake_server.handlers = [
        {"responses": [{"id": "1", "result": {"type": "ok"}}]} for _ in range(5)
    ]
    client = AsyncHerdrClient(socket_path=fake_server.socket_path)

    await client.workspace_list()
    await client.tab_list(workspace_id="w1")
    await client.pane_list()
    await client.pane_read("w1-1", lines=None, strip_ansi=False, format="text")
    await client.pane_wait_for_output(
        "w1-1",
        {"type": "substring", "value": "ready"},
        lines=10,
        timeout_ms=1000,
    )

    assert [request["method"] for request in fake_server.requests] == [
        "workspace.list",
        "tab.list",
        "pane.list",
        "pane.read",
        "pane.wait_for_output",
    ]
    assert fake_server.requests[1]["params"] == {"workspace_id": "w1"}
    assert fake_server.requests[2]["params"] == {}
    assert fake_server.requests[3]["params"] == {
        "pane_id": "w1-1",
        "source": "recent",
        "strip_ansi": False,
        "format": "text",
    }
    assert fake_server.requests[4]["params"] == {
        "pane_id": "w1-1",
        "source": "recent",
        "match": {"type": "substring", "value": "ready"},
        "strip_ansi": True,
        "lines": 10,
        "timeout_ms": 1000,
    }


async def test_pane_send_input_sends_text_and_keys(
    fake_server: FakeHerdrServer,
) -> None:
    fake_server.handlers = [{"responses": [{"id": "1", "result": {"type": "ok"}}]}]
    client = AsyncHerdrClient(socket_path=fake_server.socket_path)

    result = await client.pane_send_input("w123-1", text="status", keys=["Enter"])

    assert result == {"type": "ok"}
    assert fake_server.requests[0]["method"] == "pane.send_input"
    assert fake_server.requests[0]["params"] == {
        "pane_id": "w123-1",
        "text": "status",
        "keys": ["Enter"],
    }


async def test_api_errors_raise_exception(fake_server: FakeHerdrServer) -> None:
    fake_server.handlers = [
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
    client = AsyncHerdrClient(socket_path=fake_server.socket_path)

    with pytest.raises(HerdrApiError) as exc:
        await client.pane_send_text("w123-99", "hello")

    assert exc.value.code == "pane_not_found"
    assert "w123-99" in str(exc.value)


async def test_request_rejects_non_canonical_method(
    fake_server: FakeHerdrServer,
) -> None:
    client = AsyncHerdrClient(socket_path=fake_server.socket_path)

    with pytest.raises(HerdrClientError, match="unsupported herdr socket method"):
        await client.request("pane.targeted_read", {"pane_id": "w123-1"})


async def test_subscription_reads_ack_then_events(
    fake_server: FakeHerdrServer,
) -> None:
    fake_server.handlers = [
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
    client = AsyncHerdrClient(socket_path=fake_server.socket_path)

    async with client.subscribe([{"type": "workspace.created"}]) as subscription:
        events = [event async for event in subscription.events()]

        assert subscription.ack["result"] == {"type": "subscription_started"}

    assert events == [
        {"event": "workspace_created", "data": {"workspace": {"workspace_id": "w1"}}},
        {"event": "workspace_focused", "data": {"workspace_id": "w1"}},
    ]
    assert fake_server.requests[0]["method"] == "events.subscribe"
    assert fake_server.requests[0]["params"] == {
        "subscriptions": [{"type": "workspace.created"}]
    }


async def test_subscription_api_errors_close_the_socket(
    fake_server: FakeHerdrServer,
) -> None:
    fake_server.handlers = [
        {
            "responses": [
                {
                    "id": "1",
                    "error": {"code": "invalid_subscription", "message": "bad filter"},
                }
            ]
        }
    ]
    client = AsyncHerdrClient(socket_path=fake_server.socket_path)
    subscription = client.subscribe([])

    with pytest.raises(HerdrApiError, match="invalid_subscription"):
        await subscription.__aenter__()
    await subscription.aclose()


async def test_socket_closure_before_response_raises_client_error(
    fake_server: FakeHerdrServer,
) -> None:
    fake_server.handlers = [{"responses": []}]
    client = AsyncHerdrClient(socket_path=fake_server.socket_path)

    with pytest.raises(HerdrClientError, match="closed before a response"):
        await client.ping()


async def test_read_timeout_raises_client_error(fake_server: FakeHerdrServer) -> None:
    fake_server.handlers = [
        {
            "delay": 0.1,
            "responses": [{"id": "1", "result": {"type": "pong"}}],
        }
    ]
    client = AsyncHerdrClient(socket_path=fake_server.socket_path, timeout=0.01)

    with pytest.raises(HerdrClientError, match="timed out reading"):
        await client.ping()


async def test_request_cancellation_closes_the_connection(
    fake_server: FakeHerdrServer,
) -> None:
    fake_server.handlers = [
        {
            "delay": 0.1,
            "responses": [{"id": "1", "result": {"type": "pong"}}],
        }
    ]
    client = AsyncHerdrClient(socket_path=fake_server.socket_path, timeout=1.0)
    request = asyncio.create_task(client.ping())

    await asyncio.sleep(0.01)
    request.cancel()

    with pytest.raises(asyncio.CancelledError):
        await request


async def test_subscription_close_is_idempotent(fake_server: FakeHerdrServer) -> None:
    subscription = AsyncHerdrClient(socket_path=fake_server.socket_path).subscribe([])

    await subscription.aclose()
    await subscription.aclose()
