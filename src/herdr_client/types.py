"""Typed models for the public herdr socket API.

The models intentionally use dictionaries and ``TypedDict`` rather than
runtime validation objects so callers keep normal JSON/dict ergonomics.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal, NotRequired, Required, TypedDict

type JSONScalar = bool | int | float | str | None
type JSONValue = JSONScalar | list[JSONValue] | Mapping[str, JSONValue]
type JsonObject = dict[str, JSONValue]

ReadSource = Literal["visible", "recent", "recent_unwrapped", "detection"]
ReadFormat = Literal["text", "ansi"]
AgentStatus = Literal["idle", "working", "blocked", "done", "unknown"]


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


class ServerCapabilities(TypedDict, total=False):
    live_handoff: Required[bool]
    detached_server_daemon: NotRequired[bool]
    endpoint_protocol_generation: NotRequired[int | None]
    health_check: NotRequired[bool]
    surface_interest: NotRequired[bool]


class AgentSessionInfo(TypedDict):
    source: str
    agent: str
    kind: Literal["id", "path"]
    value: str


class WorkspaceWorktreeInfo(TypedDict):
    repo_key: str
    repo_name: str
    repo_root: str
    checkout_path: str
    is_linked_worktree: bool


class WorkspaceInfo(TypedDict, total=False):
    workspace_id: Required[str]
    number: Required[int]
    label: Required[str]
    focused: Required[bool]
    pane_count: Required[int]
    tab_count: Required[int]
    active_tab_id: Required[str]
    agent_status: Required[AgentStatus]
    tokens: NotRequired[dict[str, str]]
    worktree: NotRequired[WorkspaceWorktreeInfo | None]


class TabInfo(TypedDict, total=False):
    tab_id: Required[str]
    workspace_id: Required[str]
    number: Required[int]
    label: Required[str]
    focused: Required[bool]
    pane_count: Required[int]
    agent_status: Required[AgentStatus]


class PaneInfo(TypedDict, total=False):
    pane_id: Required[str]
    terminal_id: Required[str]
    workspace_id: Required[str]
    tab_id: Required[str]
    focused: Required[bool]
    agent_status: Required[AgentStatus]
    revision: Required[int]
    agent: NotRequired[str | None]
    agent_session: NotRequired[AgentSessionInfo | None]
    cwd: NotRequired[str | None]
    display_agent: NotRequired[str | None]
    foreground_cwd: NotRequired[str | None]
    label: NotRequired[str | None]
    scroll: NotRequired[JsonObject | None]
    state_labels: NotRequired[dict[str, str]]
    terminal_title: NotRequired[str | None]
    terminal_title_stripped: NotRequired[str | None]
    title: NotRequired[str | None]
    tokens: NotRequired[dict[str, str]]


class PaneReadResult(TypedDict):
    pane_id: str
    workspace_id: str
    tab_id: str
    source: ReadSource
    format: ReadFormat
    text: str
    revision: int
    truncated: bool


class OutputSubstringMatch(TypedDict):
    type: Literal["substring"]
    value: str


class OutputRegexMatch(TypedDict):
    type: Literal["regex"]
    value: str


type OutputMatch = OutputSubstringMatch | OutputRegexMatch

SubscriptionType = Literal[
    "workspace.created",
    "workspace.updated",
    "workspace.metadata_updated",
    "workspace.renamed",
    "workspace.moved",
    "workspace.reordered",
    "workspace.closed",
    "workspace.focused",
    "worktree.created",
    "worktree.opened",
    "worktree.removed",
    "tab.created",
    "tab.closed",
    "tab.focused",
    "tab.renamed",
    "tab.moved",
    "pane.created",
    "pane.closed",
    "pane.updated",
    "pane.focused",
    "pane.moved",
    "pane.exited",
    "pane.agent_detected",
    "pane.output_matched",
    "pane.agent_status_changed",
    "pane.scroll_changed",
    "layout.updated",
]


class EventSubscription(TypedDict, total=False):
    type: Required[SubscriptionType]
    pane_id: NotRequired[str]
    source: NotRequired[ReadSource]
    match: NotRequired[OutputMatch]
    lines: NotRequired[int | None]
    strip_ansi: NotRequired[bool]
    agent_status: NotRequired[AgentStatus | None]


class EventEnvelope(TypedDict):
    event: str
    data: JsonObject


class PingParams(TypedDict):
    pass


class TabListParams(TypedDict, total=False):
    workspace_id: str | None


class PaneListParams(TypedDict, total=False):
    workspace_id: str | None


class PaneSendTextParams(TypedDict):
    pane_id: str
    text: str


class PaneSendKeysParams(TypedDict):
    pane_id: str
    keys: list[str]


class PaneSendInputParams(TypedDict, total=False):
    pane_id: Required[str]
    text: NotRequired[str]
    keys: NotRequired[list[str]]


class PaneReadParams(TypedDict, total=False):
    pane_id: Required[str]
    source: Required[ReadSource]
    lines: NotRequired[int | None]
    strip_ansi: NotRequired[bool]
    format: NotRequired[ReadFormat]


class PaneWaitForOutputParams(TypedDict, total=False):
    pane_id: Required[str]
    source: Required[ReadSource]
    match: Required[OutputMatch]
    lines: NotRequired[int | None]
    timeout_ms: NotRequired[int | None]
    strip_ansi: NotRequired[bool]


class EventsSubscribeParams(TypedDict):
    subscriptions: list[EventSubscription]


class PongResult(TypedDict, total=False):
    type: Required[Literal["pong"]]
    version: Required[str]
    protocol: Required[int]
    capabilities: NotRequired[ServerCapabilities | None]


class WorkspaceListResult(TypedDict):
    type: Literal["workspace_list"]
    workspaces: list[WorkspaceInfo]


class TabListResult(TypedDict):
    type: Literal["tab_list"]
    tabs: list[TabInfo]


class PaneListResult(TypedDict):
    type: Literal["pane_list"]
    panes: list[PaneInfo]


class OkResult(TypedDict):
    type: Literal["ok"]


class PaneReadResponse(TypedDict):
    type: Literal["pane_read"]
    read: PaneReadResult


class OutputMatchedResult(TypedDict, total=False):
    type: Required[Literal["output_matched"]]
    pane_id: Required[str]
    revision: Required[int]
    read: Required[PaneReadResult]
    matched_line: NotRequired[str | None]


class SubscriptionStartedResult(TypedDict):
    type: Literal["subscription_started"]


class SubscriptionAck(TypedDict):
    id: str
    result: SubscriptionStartedResult


type ResponseResult = (
    JsonObject
    | PongResult
    | WorkspaceListResult
    | TabListResult
    | PaneListResult
    | OkResult
    | PaneReadResponse
    | OutputMatchedResult
    | SubscriptionStartedResult
)
