from __future__ import annotations

import json
import re
from pathlib import Path
from typing import cast, get_args

import pytest

from herdr_client import AsyncHerdrClient, HerdrClient, HerdrClientError
from herdr_client.generated_types import RequestMethod
from herdr_client.protocol import (
    CANONICAL_METHODS,
    CONVENIENCE_METHODS,
    METHOD_SCHEMAS,
    NOT_IMPLEMENTED_METHODS,
    SCHEMA_PROTOCOL,
    SCHEMA_VERSION,
    SPECIAL_METHODS,
    response_result,
)
from herdr_client.schema import (
    OFFICIAL_SCHEMA_PROTOCOL,
    OFFICIAL_SCHEMA_SHA256,
    OFFICIAL_SCHEMA_URL,
    OFFICIAL_SCHEMA_VERSION,
)
from herdr_client.stub_methods import STUB_METHODS

EXPECTED_METHOD_COUNT = 103
EXPECTED_NOT_IMPLEMENTED_COUNT = 93
EXPECTED_CONVENIENCE_COUNT = 10
EXPECTED_SCHEMA_PROTOCOL = 22
EXPECTED_SCHEMA_VERSION = 1
EXPECTED_SHA256_LENGTH = 64


def test_method_registry_matches_the_official_schema_surface() -> None:
    assert SCHEMA_PROTOCOL == EXPECTED_SCHEMA_PROTOCOL
    assert SCHEMA_VERSION == EXPECTED_SCHEMA_VERSION
    assert len(METHOD_SCHEMAS) == EXPECTED_METHOD_COUNT
    assert CANONICAL_METHODS == frozenset(METHOD_SCHEMAS)
    assert len(NOT_IMPLEMENTED_METHODS) == EXPECTED_NOT_IMPLEMENTED_COUNT
    assert "agent.send" not in CANONICAL_METHODS
    assert "agent.send_keys" in CANONICAL_METHODS
    assert "pane.graphics.stream" not in CANONICAL_METHODS
    assert SPECIAL_METHODS == {"pane.graphics.stream"}
    assert len(CONVENIENCE_METHODS) == EXPECTED_CONVENIENCE_COUNT


def test_schema_metadata_contains_required_and_optional_fields() -> None:
    pane_read = METHOD_SCHEMAS["pane.read"]
    assert pane_read.name == "PaneReadParams"
    assert pane_read.required == ("pane_id", "source")
    assert "format" in pane_read.properties

    plugin_open = METHOD_SCHEMAS["plugin.pane.open"]
    assert plugin_open.required == ("plugin_id", "entrypoint")
    assert "placement" in plugin_open.properties


def test_official_schema_identity_is_pinned() -> None:
    assert OFFICIAL_SCHEMA_PROTOCOL == SCHEMA_PROTOCOL
    assert OFFICIAL_SCHEMA_VERSION == SCHEMA_VERSION
    assert len(OFFICIAL_SCHEMA_SHA256) == EXPECTED_SHA256_LENGTH
    assert re.search(r"/[0-9a-f]{40}/", OFFICIAL_SCHEMA_URL) is not None

    schema_path = Path(__file__).parents[1] / "schema/herdr-api.schema.json"
    schema = cast(dict[str, object], json.loads(schema_path.read_text()))
    schemas = schema.get("schemas")
    assert isinstance(schemas, dict)
    request_schema = schemas.get("request")
    assert isinstance(request_schema, dict)
    request_variants = request_schema.get("oneOf")
    assert isinstance(request_variants, list)
    assert len(request_variants) == len(METHOD_SCHEMAS)
    assert len(get_args(RequestMethod.__value__)) == len(METHOD_SCHEMAS)


def test_static_stub_declarations_match_runtime_stub_methods() -> None:
    pyi_path = Path(__file__).parents[1] / "src/herdr_client/stub_methods.pyi"
    declarations = set(
        re.findall(r"^\s+(?:async )?def ([a-z0-9_]+)\(", pyi_path.read_text(), re.M)
    )
    runtime_names = {method.replace(".", "_") for method in STUB_METHODS}

    assert declarations == runtime_names


@pytest.mark.parametrize(
    "method",
    sorted(NOT_IMPLEMENTED_METHODS | SPECIAL_METHODS),
)
def test_sync_stub_raises_not_implemented(method: str, tmp_path: Path) -> None:
    client = HerdrClient(socket_path=tmp_path / "not-used-herdr.sock")

    with pytest.raises(NotImplementedError, match=method.replace(".", r"\.")):
        getattr(client, method.replace(".", "_"))()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method",
    sorted(NOT_IMPLEMENTED_METHODS | SPECIAL_METHODS),
)
async def test_async_stub_raises_not_implemented(method: str, tmp_path: Path) -> None:
    client = AsyncHerdrClient(socket_path=tmp_path / "not-used-herdr.sock")

    with pytest.raises(NotImplementedError, match=method.replace(".", r"\.")):
        await getattr(client, method.replace(".", "_"))()


def test_unknown_method_is_still_a_client_error(tmp_path: Path) -> None:
    client = HerdrClient(socket_path=tmp_path / "not-used-herdr.sock")

    with pytest.raises(HerdrClientError, match="unsupported herdr socket method"):
        assert client.request("not.a.real.method") is not None


def test_response_result_requires_a_result_discriminator() -> None:
    with pytest.raises(HerdrClientError, match="missing its type"):
        assert response_result({"id": "req_1", "result": {}}) is not None
