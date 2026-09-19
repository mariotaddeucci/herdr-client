from __future__ import annotations

from typing import TYPE_CHECKING, assert_type

if TYPE_CHECKING:
    from collections.abc import Mapping

from herdr_client import (
    AsyncClientProtocol,
    AsyncHerdrClient,
    AsyncSubscriptionProtocol,
    HerdrClient,
    JsonObject,
    JSONValue,
    PaneReadParams,
    PaneReadResponse,
    PongResult,
    SubscriptionProtocol,
    SyncClientProtocol,
    TabListResult,
)


def sync_contract(client: HerdrClient, interface: SyncClientProtocol) -> None:
    assert_type(client.ping(), PongResult)
    assert_type(client.tab_list(), TabListResult)
    assert_type(interface.request("dynamic.method"), JsonObject)
    assert_type(client.request("ping"), PongResult)
    assert_type(
        interface.subscribe([{"type": "workspace.created"}]), SubscriptionProtocol
    )

    params: PaneReadParams = {"pane_id": "pane-1", "source": "recent"}
    assert_type(client.request("pane.read", params), PaneReadResponse)


async def async_contract(
    client: AsyncHerdrClient, interface: AsyncClientProtocol
) -> None:
    assert_type(await client.ping(), PongResult)
    assert_type(await client.tab_list(), TabListResult)
    assert_type(await interface.request("dynamic.method"), JsonObject)
    assert_type(await client.request("ping"), PongResult)
    assert_type(
        interface.subscribe([{"type": "workspace.created"}]),
        AsyncSubscriptionProtocol,
    )


def dynamic_request(
    client: SyncClientProtocol, method: str, params: Mapping[str, JSONValue]
) -> JsonObject:
    # Dynamic method names intentionally use the generic JSON object result.
    return client.request(method, params)
