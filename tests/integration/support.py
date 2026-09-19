from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from herdr_client import CANONICAL_METHODS, SPECIAL_METHODS, JSONValue

OPENCODE_TEST_MODEL = "opencode/big-pickle"


@dataclass(frozen=True, slots=True)
class LiveWorkspace:
    workspace_id: str
    tab_id: str
    pane_id: str
    cwd: Path


type ParamsFactory = Callable[[LiveWorkspace], Mapping[str, JSONValue]]


@dataclass(frozen=True, slots=True)
class RequestCase:
    method: str
    expected_type: str
    params: ParamsFactory


def required_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise AssertionError(f"expected non-empty string field {field!r}: {value!r}")
    return value


def required_object(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise AssertionError(f"expected object field {field!r}: {value!r}")
    return value


def assert_result_type(result: Mapping[str, object], expected: str) -> None:
    actual = result.get("type")
    assert actual == expected, (
        f"expected result type {expected!r}, got {actual!r}: {result!r}"
    )


def assert_workspace_scope(workspace: LiveWorkspace, value: object) -> None:
    path = Path(required_string(value, "cwd")).resolve()
    root = workspace.cwd.resolve()
    assert path == root or root in path.parents, (path, root)


def safe_command(token: str) -> str:
    """Return a shell command that only writes a deterministic stdout line."""
    assert token.replace("_", "").isalnum()
    return f"printf '%s\\n' {token}"


def read_only_cases() -> tuple[RequestCase, ...]:
    return (
        RequestCase(
            "workspace.get",
            "workspace_info",
            lambda workspace: {"workspace_id": workspace.workspace_id},
        ),
        RequestCase("tab.list", "tab_list", lambda _workspace: {}),
        RequestCase(
            "tab.list",
            "tab_list",
            lambda workspace: {"workspace_id": workspace.workspace_id},
        ),
        RequestCase(
            "tab.get",
            "tab_info",
            lambda workspace: {"tab_id": workspace.tab_id},
        ),
        RequestCase("pane.list", "pane_list", lambda _workspace: {}),
        RequestCase(
            "pane.list",
            "pane_list",
            lambda workspace: {"workspace_id": workspace.workspace_id},
        ),
        RequestCase(
            "pane.get",
            "pane_info",
            lambda workspace: {"pane_id": workspace.pane_id},
        ),
        RequestCase("pane.current", "pane_current", lambda _workspace: {}),
        RequestCase(
            "pane.current",
            "pane_current",
            lambda workspace: {"caller_pane_id": workspace.pane_id},
        ),
        RequestCase("pane.process_info", "pane_process_info", lambda _workspace: {}),
        RequestCase(
            "pane.process_info",
            "pane_process_info",
            lambda workspace: {"pane_id": workspace.pane_id},
        ),
        RequestCase("pane.layout", "pane_layout", lambda _workspace: {}),
        RequestCase(
            "pane.layout",
            "pane_layout",
            lambda workspace: {"pane_id": workspace.pane_id},
        ),
        RequestCase("layout.export", "layout_export", lambda _workspace: {}),
        RequestCase(
            "layout.export",
            "layout_export",
            lambda workspace: {"tab_id": workspace.tab_id},
        ),
        RequestCase(
            "layout.export",
            "layout_export",
            lambda workspace: {"pane_id": workspace.pane_id},
        ),
        RequestCase(
            "pane.neighbor",
            "pane_neighbor",
            lambda workspace: {"pane_id": workspace.pane_id, "direction": "left"},
        ),
        RequestCase(
            "pane.edges",
            "pane_edges",
            lambda workspace: {"pane_id": workspace.pane_id},
        ),
        RequestCase(
            "pane.graphics.info",
            "pane_graphics_info",
            lambda workspace: {"pane_id": workspace.pane_id},
        ),
        RequestCase(
            "pane.selection.read",
            "pane_selection",
            lambda workspace: {
                "pane_id": workspace.pane_id,
                "anchor": {"row": 0, "col": 0},
                "cursor": {"row": 0, "col": 1},
            },
        ),
        RequestCase("worktree.list", "worktree_list", lambda _workspace: {}),
        RequestCase(
            "integration.list",
            "integration_list",
            lambda _workspace: {},
        ),
        RequestCase("plugin.list", "plugin_list", lambda _workspace: {}),
        RequestCase(
            "plugin.action.list",
            "plugin_action_list",
            lambda _workspace: {},
        ),
        RequestCase("plugin.log.list", "plugin_log_list", lambda _workspace: {}),
    )


AGENT_METHODS = frozenset(
    {
        "server.agent_manifests",
        "server.reload_agent_manifests",
        "agent.list",
        "agent.get",
        "agent.explain",
        "agent.read",
        "agent.send_keys",
        "agent.rename",
        "agent.focus",
        "agent.view.set",
        "agent.view.clear",
        "agent.start",
        "agent.prompt",
        "agent.wait",
        "pane.report_agent",
        "pane.report_agent_session",
        "pane.report_metadata",
        "pane.clear_agent_authority",
        "pane.release_agent",
    }
)

GLOBAL_SIDE_EFFECT_METHODS = frozenset(
    {
        "server.stop",
        "server.reload_config",
        "server.live_handoff",
        "notification.show",
        "product_announcement.dismiss",
        "release_notes.dismiss",
        "command.invoke",
        "client.window_title.set",
        "client.window_title.clear",
        "client_shell.surface.set",
        "session.snapshot",
        "pane.edit_scrollback",
        "pane.copy_motion",
        "pane.copy_search",
        "pane.link.activate",
        "integration.install",
        "integration.uninstall",
        "plugin.link",
        "plugin.unlink",
        "plugin.enable",
        "plugin.disable",
        "plugin.action.invoke",
        "plugin.pane.open",
        "plugin.pane.focus",
        "plugin.pane.close",
        "popup.close",
    }
)

SPECIAL_SIDE_EFFECT_METHODS = frozenset(SPECIAL_METHODS)


def assert_method_inventory(covered: frozenset[str]) -> None:
    excluded = AGENT_METHODS | GLOBAL_SIDE_EFFECT_METHODS | SPECIAL_SIDE_EFFECT_METHODS
    assert covered.isdisjoint(excluded)
    assert covered | excluded == CANONICAL_METHODS | SPECIAL_METHODS
    assert covered & AGENT_METHODS == frozenset()
