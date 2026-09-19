"""Structural interfaces for dependency injection and test doubles."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterable, Iterator, Mapping, Sequence
    from pathlib import Path
    from types import TracebackType

    from .types import (
        EventEnvelope,
        EventSubscription,
        JsonObject,
        JSONValue,
        OkResult,
        OutputMatch,
        OutputMatchedResult,
        PaneListResult,
        PaneReadResponse,
        PongResult,
        ReadFormat,
        ReadSource,
        SubscriptionAck,
        TabListResult,
        WorkspaceListResult,
    )


class SubscriptionProtocol(Protocol):
    @property
    def ack(self) -> SubscriptionAck: ...

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    def close(self) -> None: ...

    def events(self) -> Iterator[EventEnvelope]: ...


class AsyncSubscriptionProtocol(Protocol):
    @property
    def ack(self) -> SubscriptionAck: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    async def aclose(self) -> None: ...

    def events(self) -> AsyncIterator[EventEnvelope]: ...


class SyncClientProtocol(Protocol):
    socket_path: Path
    timeout: float

    def request(
        self, method: str, params: Mapping[str, JSONValue] | None = None
    ) -> JsonObject: ...

    def ping(self) -> PongResult: ...

    def workspace_list(self) -> WorkspaceListResult: ...

    def tab_list(self, workspace_id: str | None = None) -> TabListResult: ...

    def pane_list(self, workspace_id: str | None = None) -> PaneListResult: ...

    def pane_send_text(self, pane_id: str, text: str) -> OkResult: ...

    def pane_send_keys(self, pane_id: str, keys: Sequence[str]) -> OkResult: ...

    def pane_send_input(
        self,
        pane_id: str,
        text: str = "",
        keys: Sequence[str] | None = None,
    ) -> OkResult: ...

    def pane_read(
        self,
        pane_id: str,
        source: ReadSource = "recent",
        lines: int | None = 80,
        strip_ansi: bool = True,
        format: ReadFormat | None = None,
    ) -> PaneReadResponse: ...

    def pane_wait_for_output(
        self,
        pane_id: str,
        match: OutputMatch,
        source: ReadSource = "recent",
        lines: int | None = None,
        timeout_ms: int | None = None,
        strip_ansi: bool = True,
    ) -> OutputMatchedResult: ...

    def subscribe(
        self, subscriptions: Iterable[EventSubscription]
    ) -> SubscriptionProtocol: ...


class AsyncClientProtocol(Protocol):
    socket_path: Path
    timeout: float

    async def request(
        self, method: str, params: Mapping[str, JSONValue] | None = None
    ) -> JsonObject: ...

    async def ping(self) -> PongResult: ...

    async def workspace_list(self) -> WorkspaceListResult: ...

    async def tab_list(self, workspace_id: str | None = None) -> TabListResult: ...

    async def pane_list(self, workspace_id: str | None = None) -> PaneListResult: ...

    async def pane_send_text(self, pane_id: str, text: str) -> OkResult: ...

    async def pane_send_keys(self, pane_id: str, keys: Sequence[str]) -> OkResult: ...

    async def pane_send_input(
        self,
        pane_id: str,
        text: str = "",
        keys: Sequence[str] | None = None,
    ) -> OkResult: ...

    async def pane_read(
        self,
        pane_id: str,
        source: ReadSource = "recent",
        lines: int | None = 80,
        strip_ansi: bool = True,
        format: ReadFormat | None = None,
    ) -> PaneReadResponse: ...

    async def pane_wait_for_output(
        self,
        pane_id: str,
        match: OutputMatch,
        source: ReadSource = "recent",
        lines: int | None = None,
        timeout_ms: int | None = None,
        strip_ansi: bool = True,
    ) -> OutputMatchedResult: ...

    def subscribe(
        self, subscriptions: Iterable[EventSubscription]
    ) -> AsyncSubscriptionProtocol: ...
