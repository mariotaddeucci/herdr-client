from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, NoReturn, cast

if TYPE_CHECKING:
    from collections.abc import Mapping

from .exceptions import HerdrApiError, HerdrClientError
from .types import EventEnvelope, JsonObject, JSONValue, SubscriptionAck

# Kept as an import-compatible alias for callers that used the old internal name.
JsonDict = JsonObject
SCHEMA_PROTOCOL = 22
SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class MethodSchema:
    """Request schema metadata published by the herdr socket API."""

    name: str
    required: tuple[str, ...] = ()
    properties: tuple[str, ...] = ()


def schema(
    name: str,
    required: tuple[str, ...] = (),
    properties: tuple[str, ...] = (),
) -> MethodSchema:
    return MethodSchema(name, required, properties)


METHOD_SCHEMAS: dict[str, MethodSchema] = {
    "ping": schema("PingParams"),
    "server.stop": schema("EmptyParams"),
    "server.reload_config": schema("EmptyParams"),
    "server.agent_manifests": schema("EmptyParams"),
    "server.reload_agent_manifests": schema("EmptyParams"),
    "server.live_handoff": schema(
        "ServerLiveHandoffParams",
        properties=("expected_protocol", "expected_version", "import_exe"),
    ),
    "notification.show": schema(
        "NotificationShowParams",
        required=("title",),
        properties=("body", "position", "sound", "title"),
    ),
    "product_announcement.dismiss": schema(
        "ProductAnnouncementDismissParams",
        required=("version", "id"),
        properties=("id", "version"),
    ),
    "release_notes.dismiss": schema(
        "ReleaseNotesDismissParams",
        required=("version",),
        properties=("version",),
    ),
    "command.invoke": schema(
        "CommandInvokeParams",
        required=("command_id",),
        properties=("command_id", "pane_id", "selection", "tab_id", "workspace_id"),
    ),
    "client.window_title.set": schema(
        "ClientWindowTitleSetParams",
        required=("title",),
        properties=("title",),
    ),
    "client.window_title.clear": schema("EmptyParams"),
    "client_shell.surface.set": schema(
        "ClientShellSurfaceSetParams",
        required=("active",),
        properties=("active",),
    ),
    "session.snapshot": schema("EmptyParams"),
    "workspace.create": schema(
        "WorkspaceCreateParams",
        properties=("cwd", "env", "focus", "label", "source_workspace_id"),
    ),
    "workspace.list": schema("EmptyParams"),
    "workspace.get": schema(
        "WorkspaceTarget", required=("workspace_id",), properties=("workspace_id",)
    ),
    "workspace.focus": schema(
        "WorkspaceTarget", required=("workspace_id",), properties=("workspace_id",)
    ),
    "workspace.rename": schema(
        "WorkspaceRenameParams",
        required=("workspace_id", "label"),
        properties=("label", "workspace_id"),
    ),
    "workspace.move": schema(
        "WorkspaceMoveParams",
        required=("workspace_id", "insert_index"),
        properties=("workspace_id", "insert_index"),
    ),
    "workspace.move_block": schema(
        "WorkspaceMoveBlockParams",
        required=("workspace_ids",),
        properties=("before_workspace_id", "workspace_ids"),
    ),
    "workspace.report_metadata": schema(
        "WorkspaceReportMetadataParams",
        required=("workspace_id", "source", "tokens"),
        properties=("seq", "source", "tokens", "ttl_ms", "workspace_id"),
    ),
    "workspace.close": schema(
        "WorkspaceCloseParams",
        required=("workspace_id",),
        properties=("close_group", "workspace_id"),
    ),
    "worktree.list": schema(
        "WorktreeListParams",
        properties=("cwd", "trust_repository", "workspace_id"),
    ),
    "worktree.create": schema(
        "WorktreeCreateParams",
        properties=(
            "base",
            "branch",
            "cwd",
            "focus",
            "label",
            "path",
            "trust_repository",
            "workspace_id",
        ),
    ),
    "worktree.open": schema(
        "WorktreeOpenParams",
        properties=(
            "branch",
            "cwd",
            "focus",
            "label",
            "path",
            "trust_repository",
            "workspace_id",
        ),
    ),
    "worktree.remove": schema(
        "WorktreeRemoveParams",
        required=("workspace_id",),
        properties=("force", "trust_repository", "workspace_id"),
    ),
    "tab.create": schema(
        "TabCreateParams",
        properties=("cwd", "env", "focus", "label", "workspace_id"),
    ),
    "tab.list": schema("TabListParams", properties=("workspace_id",)),
    "tab.get": schema("TabTarget", required=("tab_id",), properties=("tab_id",)),
    "tab.focus": schema("TabTarget", required=("tab_id",), properties=("tab_id",)),
    "tab.rename": schema(
        "TabRenameParams",
        required=("tab_id", "label"),
        properties=("tab_id", "label"),
    ),
    "tab.move": schema(
        "TabMoveParams",
        required=("tab_id", "insert_index"),
        properties=("tab_id", "insert_index"),
    ),
    "tab.close": schema("TabTarget", required=("tab_id",), properties=("tab_id",)),
    "pane.split": schema(
        "PaneSplitParams",
        required=("direction",),
        properties=(
            "cwd",
            "direction",
            "env",
            "focus",
            "ratio",
            "right_click",
            "target_pane_id",
            "workspace_id",
        ),
    ),
    "pane.swap": schema(
        "PaneSwapParams",
        properties=("direction", "pane_id", "source_pane_id", "target_pane_id"),
    ),
    "pane.move": schema(
        "PaneMoveParams",
        required=("pane_id", "destination"),
        properties=("destination", "focus", "pane_id"),
    ),
    "pane.zoom": schema("PaneZoomParams", properties=("mode", "pane_id")),
    "pane.layout": schema("PaneLayoutParams", properties=("pane_id",)),
    "pane.process_info": schema("PaneProcessInfoParams", properties=("pane_id",)),
    "layout.export": schema("LayoutExportParams", properties=("pane_id", "tab_id")),
    "layout.apply": schema(
        "LayoutApplyParams",
        required=("root",),
        properties=("focus", "root", "tab_id", "tab_label", "workspace_id"),
    ),
    "layout.set_split_ratio": schema(
        "LayoutSetSplitRatioParams",
        required=("path", "ratio"),
        properties=("pane_id", "path", "ratio", "tab_id"),
    ),
    "pane.neighbor": schema(
        "PaneNeighborParams",
        required=("direction",),
        properties=("direction", "pane_id"),
    ),
    "pane.edges": schema("PaneEdgesParams", properties=("pane_id",)),
    "pane.focus_direction": schema(
        "PaneFocusDirectionParams",
        required=("direction",),
        properties=("direction", "pane_id"),
    ),
    "pane.resize": schema(
        "PaneResizeParams",
        required=("direction",),
        properties=("amount", "direction", "pane_id"),
    ),
    "pane.scroll": schema(
        "PaneScrollParams",
        required=("pane_id", "offset_from_bottom"),
        properties=("pane_id", "offset_from_bottom"),
    ),
    "pane.edit_scrollback": schema(
        "PaneTarget", required=("pane_id",), properties=("pane_id",)
    ),
    "pane.selection.read": schema(
        "PaneSelectionReadParams",
        required=("pane_id", "anchor", "cursor"),
        properties=("anchor", "content_revision", "cursor", "pane_id"),
    ),
    "pane.copy_motion": schema(
        "PaneCopyMotionParams",
        required=("pane_id", "cursor", "motion"),
        properties=("content_revision", "cursor", "motion", "pane_id"),
    ),
    "pane.copy_search": schema(
        "PaneCopySearchParams",
        required=("pane_id", "query", "direction", "cursor", "content_revision"),
        properties=(
            "content_revision",
            "cursor",
            "direction",
            "pane_id",
            "previous",
            "query",
        ),
    ),
    "pane.list": schema("PaneListParams", properties=("workspace_id",)),
    "pane.current": schema("PaneCurrentParams", properties=("caller_pane_id",)),
    "pane.get": schema("PaneTarget", required=("pane_id",), properties=("pane_id",)),
    "pane.focus": schema("PaneTarget", required=("pane_id",), properties=("pane_id",)),
    "pane.input.set": schema(
        "PaneInputSetParams",
        required=("pane_id", "right_click"),
        properties=("pane_id", "right_click"),
    ),
    "pane.link.activate": schema(
        "PaneLinkActivateParams",
        required=("pane_id", "viewport_row", "col"),
        properties=(
            "col",
            "content_revision",
            "offset_from_bottom",
            "pane_id",
            "viewport_row",
        ),
    ),
    "pane.link.resolve": schema(
        "PaneLinkActivateParams",
        required=("pane_id", "viewport_row", "col"),
        properties=(
            "col",
            "content_revision",
            "offset_from_bottom",
            "pane_id",
            "viewport_row",
        ),
    ),
    "pane.rename": schema(
        "PaneRenameParams",
        required=("pane_id",),
        properties=("label", "pane_id"),
    ),
    "pane.send_text": schema(
        "PaneSendTextParams",
        required=("pane_id", "text"),
        properties=("pane_id", "text"),
    ),
    "pane.send_keys": schema(
        "PaneSendKeysParams",
        required=("pane_id", "keys"),
        properties=("pane_id", "keys"),
    ),
    "pane.send_input": schema(
        "PaneSendInputParams",
        required=("pane_id",),
        properties=("keys", "pane_id", "text"),
    ),
    "pane.read": schema(
        "PaneReadParams",
        required=("pane_id", "source"),
        properties=("format", "lines", "pane_id", "source", "strip_ansi"),
    ),
    "pane.graphics.info": schema(
        "PaneTarget", required=("pane_id",), properties=("pane_id",)
    ),
    "pane.graphics.set": schema(
        "PaneGraphicsSetParams",
        required=("pane_id", "format", "image_width", "image_height"),
        properties=(
            "data_base64",
            "format",
            "image_height",
            "image_width",
            "layer_id",
            "pane_id",
            "placement",
            "z_index",
        ),
    ),
    "pane.graphics.clear": schema(
        "PaneGraphicsClearParams",
        required=("pane_id",),
        properties=("layer_id", "pane_id"),
    ),
    "pane.report_agent": schema(
        "PaneReportAgentParams",
        required=("pane_id", "source", "agent", "state"),
        properties=(
            "agent",
            "agent_session_id",
            "agent_session_path",
            "message",
            "pane_id",
            "seq",
            "source",
            "state",
        ),
    ),
    "pane.report_agent_session": schema(
        "PaneReportAgentSessionParams",
        required=("pane_id", "source", "agent"),
        properties=(
            "agent",
            "agent_session_id",
            "agent_session_path",
            "pane_id",
            "seq",
            "session_start_source",
            "source",
        ),
    ),
    "pane.report_metadata": schema(
        "PaneReportMetadataParams",
        required=("pane_id", "source"),
        properties=(
            "agent",
            "applies_to_source",
            "clear_display_agent",
            "clear_state_labels",
            "clear_title",
            "display_agent",
            "pane_id",
            "seq",
            "source",
            "state_labels",
            "title",
            "tokens",
            "ttl_ms",
        ),
    ),
    "pane.clear_agent_authority": schema(
        "PaneClearAgentAuthorityParams",
        required=("pane_id",),
        properties=("pane_id", "seq", "source"),
    ),
    "pane.release_agent": schema(
        "PaneReleaseAgentParams",
        required=("pane_id", "source", "agent"),
        properties=("agent", "pane_id", "seq", "source"),
    ),
    "pane.close": schema("PaneTarget", required=("pane_id",), properties=("pane_id",)),
    "pane.wait_for_output": schema(
        "PaneWaitForOutputParams",
        required=("pane_id", "source", "match"),
        properties=("lines", "match", "pane_id", "source", "strip_ansi", "timeout_ms"),
    ),
    "agent.list": schema("EmptyParams"),
    "agent.get": schema("AgentTarget", required=("target",), properties=("target",)),
    "agent.explain": schema(
        "AgentTarget", required=("target",), properties=("target",)
    ),
    "agent.read": schema(
        "AgentReadParams",
        required=("target", "source"),
        properties=("format", "lines", "source", "strip_ansi", "target"),
    ),
    "agent.send_keys": schema(
        "AgentSendKeysParams",
        required=("target", "keys"),
        properties=("target", "keys"),
    ),
    "agent.rename": schema(
        "AgentRenameParams",
        required=("target",),
        properties=("name", "target"),
    ),
    "agent.focus": schema("AgentTarget", required=("target",), properties=("target",)),
    "agent.view.set": schema(
        "AgentViewSetParams",
        required=("source",),
        properties=("filter", "label", "sort", "source"),
    ),
    "agent.view.clear": schema("AgentViewClearParams", properties=("source",)),
    "agent.start": schema(
        "AgentStartParams",
        required=("name", "kind", "pane_id"),
        properties=("args", "kind", "name", "pane_id", "timeout_ms"),
    ),
    "agent.prompt": schema(
        "AgentPromptParams",
        required=("target", "text"),
        properties=("target", "text", "wait"),
    ),
    "agent.wait": schema(
        "AgentWaitParams",
        required=("target",),
        properties=("target", "timeout_ms", "until"),
    ),
    "events.subscribe": schema(
        "EventsSubscribeParams",
        required=("subscriptions",),
        properties=("subscriptions",),
    ),
    "events.wait": schema(
        "EventsWaitParams",
        required=("match_event",),
        properties=("match_event", "timeout_ms"),
    ),
    "integration.install": schema(
        "IntegrationInstallParams", required=("target",), properties=("target",)
    ),
    "integration.uninstall": schema(
        "IntegrationUninstallParams", required=("target",), properties=("target",)
    ),
    "plugin.link": schema(
        "PluginLinkParams", required=("path",), properties=("enabled", "path", "source")
    ),
    "plugin.list": schema("PluginListParams", properties=("plugin_id",)),
    "plugin.unlink": schema(
        "PluginUnlinkParams", required=("plugin_id",), properties=("plugin_id",)
    ),
    "plugin.enable": schema(
        "PluginSetEnabledParams", required=("plugin_id",), properties=("plugin_id",)
    ),
    "plugin.disable": schema(
        "PluginSetEnabledParams", required=("plugin_id",), properties=("plugin_id",)
    ),
    "plugin.action.list": schema("PluginActionListParams", properties=("plugin_id",)),
    "plugin.action.invoke": schema(
        "PluginActionInvokeParams",
        required=("action_id",),
        properties=("action_id", "context", "plugin_id"),
    ),
    "plugin.log.list": schema("PluginLogListParams", properties=("limit", "plugin_id")),
    "plugin.pane.open": schema(
        "PluginPaneOpenParams",
        required=("plugin_id", "entrypoint"),
        properties=(
            "cwd",
            "direction",
            "entrypoint",
            "env",
            "focus",
            "height",
            "placement",
            "plugin_id",
            "target_pane_id",
            "width",
            "workspace_id",
        ),
    ),
    "plugin.pane.focus": schema(
        "PluginPaneFocusParams", required=("pane_id",), properties=("pane_id",)
    ),
    "plugin.pane.close": schema(
        "PluginPaneCloseParams", required=("pane_id",), properties=("pane_id",)
    ),
    "popup.close": schema("EmptyParams"),
    "integration.list": schema("EmptyParams"),
}

CANONICAL_METHODS = frozenset(METHOD_SCHEMAS)
SPECIAL_METHODS = frozenset({"pane.graphics.stream"})

CONVENIENCE_METHODS = frozenset(
    {
        "ping",
        "workspace.list",
        "tab.list",
        "pane.list",
        "pane.send_text",
        "pane.send_keys",
        "pane.send_input",
        "pane.read",
        "pane.wait_for_output",
        "events.subscribe",
    }
)

NOT_IMPLEMENTED_METHODS = CANONICAL_METHODS - CONVENIENCE_METHODS


def new_id() -> str:
    return f"req_{uuid.uuid4().hex}"


def encode_envelope(envelope: Mapping[str, JSONValue]) -> bytes:
    return json.dumps(envelope).encode("utf-8") + b"\n"


def decode_json(line: bytes) -> JSONValue:
    try:
        decoded: object = json.loads(line)
    except json.JSONDecodeError as exc:
        raise HerdrClientError("herdr socket returned invalid JSON") from exc
    return narrow_json(decoded)


def narrow_json(value: object) -> JSONValue:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, list):
        return [narrow_json(item) for item in cast("list[object]", value)]
    if isinstance(value, dict):
        result: JsonObject = {}
        for key, item in cast("dict[object, object]", value).items():
            if not isinstance(key, str):
                raise HerdrClientError("herdr socket returned invalid JSON")
            result[key] = narrow_json(item)
        return result
    raise HerdrClientError("herdr socket returned invalid JSON")


def raise_for_error(response: JsonDict) -> None:
    error = response.get("error")
    if error is None:
        return
    if not isinstance(error, dict):
        raise HerdrClientError("herdr error envelope is invalid")
    try:
        code = error["code"]
        message = error["message"]
    except KeyError as exc:
        raise HerdrClientError("herdr error envelope is missing fields") from exc
    if not isinstance(code, str) or not isinstance(message, str):
        raise HerdrClientError("herdr error envelope is invalid")
    raise HerdrApiError(code, message)


def response_result(response: JsonDict) -> JsonDict:
    raise_for_error(response)
    result = response.get("result")
    if not isinstance(result, dict):
        raise HerdrClientError("herdr response result must be a JSON object")
    result_type = result.get("type")
    if not isinstance(result_type, str):
        raise HerdrClientError("herdr response result is missing its type")
    return result


def subscription_ack(response: JsonDict) -> SubscriptionAck:
    raise_for_error(response)
    if not isinstance(response.get("id"), str):
        raise HerdrClientError("herdr subscription acknowledgement is invalid")
    result = response.get("result")
    if not isinstance(result, dict) or result.get("type") != "subscription_started":
        raise HerdrClientError("herdr subscription acknowledgement is invalid")
    return cast("SubscriptionAck", response)


def event_envelope(value: JSONValue) -> EventEnvelope:
    if not isinstance(value, dict):
        raise HerdrClientError("herdr event must be a JSON object")
    if not isinstance(value.get("event"), str) or not isinstance(
        value.get("data"), dict
    ):
        raise HerdrClientError("herdr event envelope is invalid")
    return cast("EventEnvelope", value)


def not_implemented(method: str) -> NoReturn:
    if method in SPECIAL_METHODS:
        raise NotImplementedError(
            "herdr method 'pane.graphics.stream' uses a dedicated hybrid "
            "JSON/binary framing transport and has no implementation yet."
        )
    schema = METHOD_SCHEMAS[method]
    raise NotImplementedError(
        f"herdr method '{method}' has no convenience implementation; "
        f"schema: {schema.name}. Use request() for the raw method."
    )
