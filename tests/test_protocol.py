from __future__ import annotations

from pathlib import Path

import pytest

from herdr_client import AsyncHerdrClient, HerdrClient, HerdrClientError
from herdr_client.protocol import (
    CANONICAL_METHODS,
    CONVENIENCE_METHODS,
    METHOD_SCHEMAS,
    NOT_IMPLEMENTED_METHODS,
    SCHEMA_PROTOCOL,
    SCHEMA_VERSION,
    SPECIAL_METHODS,
)


def test_method_registry_matches_the_official_schema_surface() -> None:
    assert SCHEMA_PROTOCOL == 22
    assert SCHEMA_VERSION == 1
    assert len(METHOD_SCHEMAS) == 103
    assert CANONICAL_METHODS == frozenset(METHOD_SCHEMAS)
    assert len(NOT_IMPLEMENTED_METHODS) == 93
    assert "agent.send" not in CANONICAL_METHODS
    assert "agent.send_keys" in CANONICAL_METHODS
    assert "pane.graphics.stream" not in CANONICAL_METHODS
    assert SPECIAL_METHODS == {"pane.graphics.stream"}
    assert len(CONVENIENCE_METHODS) == 10


def test_schema_metadata_contains_required_and_optional_fields() -> None:
    pane_read = METHOD_SCHEMAS["pane.read"]
    assert pane_read.name == "PaneReadParams"
    assert pane_read.required == ("pane_id", "source")
    assert "format" in pane_read.properties

    plugin_open = METHOD_SCHEMAS["plugin.pane.open"]
    assert plugin_open.required == ("plugin_id", "entrypoint")
    assert "placement" in plugin_open.properties


@pytest.mark.parametrize(
    "method",
    sorted(NOT_IMPLEMENTED_METHODS | SPECIAL_METHODS),
)
def test_sync_stub_raises_not_implemented(method: str) -> None:
    client = HerdrClient(socket_path=Path("/tmp/not-used-herdr.sock"))

    with pytest.raises(NotImplementedError, match=method.replace(".", r"\.")):
        getattr(client, method.replace(".", "_"))()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method",
    sorted(NOT_IMPLEMENTED_METHODS | SPECIAL_METHODS),
)
async def test_async_stub_raises_not_implemented(method: str) -> None:
    client = AsyncHerdrClient(socket_path=Path("/tmp/not-used-herdr.sock"))

    with pytest.raises(NotImplementedError, match=method.replace(".", r"\.")):
        await getattr(client, method.replace(".", "_"))()


def test_unknown_method_is_still_a_client_error() -> None:
    client = HerdrClient(socket_path=Path("/tmp/not-used-herdr.sock"))

    with pytest.raises(HerdrClientError, match="unsupported herdr socket method"):
        client.request("not.a.real.method")
