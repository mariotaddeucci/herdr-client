"""Typed models exposed by the public Herdr client API.

Wire models come from the pinned JSON Schema generator. The few hand-written
envelopes below describe transport shapes that are intentionally extensible.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import NotRequired, TypedDict

from . import generated_types

AgentSessionInfo = generated_types.EventAgentSessionInfo
AgentStatus = generated_types.EventAgentStatus
EventsSubscribeParams = generated_types.RequestEventsSubscribeParams
OutputMatch = generated_types.RequestOutputMatch
PaneListParams = generated_types.RequestPaneListParams
PaneReadParams = generated_types.RequestPaneReadParams
PaneSendInputParams = generated_types.RequestPaneSendInputParams
PaneSendKeysParams = generated_types.RequestPaneSendKeysParams
PaneSendTextParams = generated_types.RequestPaneSendTextParams
PaneWaitForOutputParams = generated_types.RequestPaneWaitForOutputParams
ReadFormat = generated_types.RequestReadFormat
ReadSource = generated_types.RequestReadSource
EventSubscription = generated_types.RequestSubscription
TabListParams = generated_types.RequestTabListParams
ResponseEventData = generated_types.ResponseEventData
PaneInfo = generated_types.ResponsePaneInfo
PaneReadResult = generated_types.ResponsePaneReadResult
GeneratedResponseResult = generated_types.ResponseResponseResult
OkResult = generated_types.ResponseResultOk
OutputMatchedResult = generated_types.ResponseResultOutputMatched
PaneListResult = generated_types.ResponseResultPaneList
PaneReadResponse = generated_types.ResponseResultPaneRead
PongResult = generated_types.ResponseResultPong
SubscriptionStartedResult = generated_types.ResponseResultSubscriptionStarted
TabListResult = generated_types.ResponseResultTabList
WorkspaceListResult = generated_types.ResponseResultWorkspaceList
ServerCapabilities = generated_types.ResponseServerCapabilities
TabInfo = generated_types.ResponseTabInfo
WorkspaceInfo = generated_types.ResponseWorkspaceInfo
WorkspaceWorktreeInfo = generated_types.ResponseWorkspaceWorktreeInfo

type JSONScalar = bool | int | float | str | None
type JSONValue = JSONScalar | list[JSONValue] | Mapping[str, JSONValue]
type JsonObject = dict[str, JSONValue]

__all__ = [
    "AgentSessionInfo",
    "AgentStatus",
    "ErrorEnvelope",
    "ErrorObject",
    "EventEnvelope",
    "EventSubscription",
    "EventsSubscribeParams",
    "JSONValue",
    "JsonObject",
    "OkResult",
    "OutputMatch",
    "OutputMatchedResult",
    "PaneInfo",
    "PaneListParams",
    "PaneListResult",
    "PaneReadParams",
    "PaneReadResponse",
    "PaneReadResult",
    "PaneSendInputParams",
    "PaneSendKeysParams",
    "PaneSendTextParams",
    "PaneWaitForOutputParams",
    "PingParams",
    "PongResult",
    "ReadFormat",
    "ReadSource",
    "RequestEnvelope",
    "ResponseEnvelope",
    "ResponseResult",
    "ServerCapabilities",
    "SubscriptionAck",
    "SubscriptionStartedResult",
    "SuccessEnvelope",
    "TabInfo",
    "TabListParams",
    "TabListResult",
    "WorkspaceInfo",
    "WorkspaceListResult",
    "WorkspaceWorktreeInfo",
]


class ErrorObject(TypedDict):
    code: str
    message: str
    data: NotRequired[JSONValue]


class RequestEnvelope(TypedDict):
    id: str
    method: str
    params: JsonObject


class SuccessEnvelope(TypedDict):
    id: str
    result: JsonObject


class ErrorEnvelope(TypedDict):
    id: str
    error: ErrorObject


type ResponseEnvelope = SuccessEnvelope | ErrorEnvelope


class EventEnvelope(TypedDict):
    """An event envelope with typed known data and forward-compatible extras."""

    event: str
    data: ResponseEventData | JsonObject


class PingParams(TypedDict):
    pass


class SubscriptionAck(TypedDict):
    id: str
    result: SubscriptionStartedResult


type ResponseResult = GeneratedResponseResult | JsonObject
