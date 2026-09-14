from __future__ import annotations

import base64
import subprocess
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from herdr_client import HerdrApiError, HerdrClient

from .support import (
    LiveWorkspace,
    RequestCase,
    assert_method_inventory,
    assert_result_type,
    assert_workspace_scope,
    read_only_cases,
    required_object,
    required_string,
    safe_command,
)

pytestmark = pytest.mark.integration


def test_ping_and_schema_identity(sync_client: HerdrClient) -> None:
    result = sync_client.ping()

    assert_result_type(result, "pong")
    assert result["protocol"] == 22
    assert isinstance(result["version"], str)


@pytest.mark.parametrize(
    "case",
    read_only_cases(),
    ids=lambda case: f"{case.method}-{case.expected_type}",
)
def test_read_only_request_variants(
    sync_client: HerdrClient,
    live_workspace: LiveWorkspace,
    case: RequestCase,
) -> None:
    try:
        result = sync_client.request(case.method, case.params(live_workspace))
    except HerdrApiError as exc:
        if case.method == "pane.graphics.info" and exc.code == "cell_size_unavailable":
            pytest.skip("headless Herdr session has no host cell size")
        raise

    assert_result_type(result, case.expected_type)


def test_method_inventory_excludes_agents() -> None:
    covered = frozenset(
        {
            "ping",
            "workspace.create",
            "workspace.list",
            "workspace.get",
            "workspace.focus",
            "workspace.rename",
            "workspace.move",
            "workspace.move_block",
            "workspace.report_metadata",
            "workspace.close",
            "worktree.list",
            "worktree.create",
            "worktree.open",
            "worktree.remove",
            "tab.create",
            "tab.list",
            "tab.get",
            "tab.focus",
            "tab.rename",
            "tab.move",
            "tab.close",
            "pane.split",
            "pane.swap",
            "pane.move",
            "pane.zoom",
            "pane.layout",
            "pane.process_info",
            "layout.export",
            "layout.apply",
            "layout.set_split_ratio",
            "pane.neighbor",
            "pane.edges",
            "pane.focus_direction",
            "pane.resize",
            "pane.scroll",
            "pane.selection.read",
            "pane.list",
            "pane.current",
            "pane.get",
            "pane.focus",
            "pane.input.set",
            "pane.link.resolve",
            "pane.rename",
            "pane.send_text",
            "pane.send_keys",
            "pane.send_input",
            "pane.read",
            "pane.graphics.info",
            "pane.graphics.set",
            "pane.graphics.clear",
            "pane.close",
            "pane.wait_for_output",
            "events.subscribe",
            "events.wait",
            "integration.list",
            "plugin.list",
            "plugin.action.list",
            "plugin.log.list",
        }
    )

    assert_method_inventory(covered)


def test_convenience_variants_and_safe_terminal_output(
    sync_client: HerdrClient,
    live_workspace: LiveWorkspace,
) -> None:
    assert_result_type(sync_client.workspace_list(), "workspace_list")
    assert_result_type(sync_client.tab_list(), "tab_list")
    assert_result_type(sync_client.tab_list(live_workspace.workspace_id), "tab_list")
    assert_result_type(sync_client.pane_list(), "pane_list")
    assert_result_type(sync_client.pane_list(live_workspace.workspace_id), "pane_list")

    token = f"herdr_py_{uuid.uuid4().hex}"
    assert_result_type(
        sync_client.pane_send_text(live_workspace.pane_id, safe_command(token)),
        "ok",
    )
    assert_result_type(
        sync_client.pane_send_keys(live_workspace.pane_id, ["Enter"]), "ok"
    )
    matched = sync_client.pane_wait_for_output(
        live_workspace.pane_id,
        {"type": "substring", "value": token},
        source="recent",
        lines=20,
        timeout_ms=3000,
        strip_ansi=True,
    )
    assert_result_type(matched, "output_matched")
    assert token in str(matched.get("matched_line"))

    regex_token = f"herdr_py_{uuid.uuid4().hex}"
    assert_result_type(
        sync_client.pane_send_input(
            live_workspace.pane_id,
            text=safe_command(regex_token),
            keys=["Enter"],
        ),
        "ok",
    )
    regex_match = sync_client.pane_wait_for_output(
        live_workspace.pane_id,
        {"type": "regex", "value": rf"{regex_token}"},
        source="recent_unwrapped",
        lines=None,
        timeout_ms=3000,
        strip_ansi=False,
    )
    assert_result_type(regex_match, "output_matched")
    assert regex_token in str(regex_match.get("matched_line"))

    assert_result_type(sync_client.pane_send_input(live_workspace.pane_id), "ok")
    assert_result_type(
        sync_client.pane_send_input(live_workspace.pane_id, text="true"), "ok"
    )
    assert_result_type(
        sync_client.pane_send_keys(live_workspace.pane_id, ["Enter"]), "ok"
    )
    assert_result_type(
        sync_client.pane_send_input(live_workspace.pane_id, keys=["Enter"]), "ok"
    )

    for source in ("visible", "recent", "recent_unwrapped", "detection"):
        for output_format in ("text", "ansi"):
            result = sync_client.pane_read(
                live_workspace.pane_id,
                source=source,
                lines=None,
                strip_ansi=False,
                format=output_format,
            )
            assert_result_type(result, "pane_read")
            read = required_object(result.get("read"), "read")
            assert read.get("source") == source
            assert read.get("format") == output_format


def test_events_wait_and_subscription(
    sync_client: HerdrClient,
    live_workspace: LiveWorkspace,
) -> None:
    with pytest.raises(HerdrApiError, match="unsupported_event_wait_match"):
        sync_client.request(
            "events.wait",
            {
                "match_event": {
                    "event": "pane_output_changed",
                    "pane_id": live_workspace.pane_id,
                },
                "timeout_ms": 100,
            },
        )

    second_token = f"herdr_py_{uuid.uuid4().hex}"
    subscription_filter = {
        "type": "pane.output_matched",
        "pane_id": live_workspace.pane_id,
        "source": "recent",
        "match": {"type": "substring", "value": second_token},
        "lines": 20,
        "strip_ansi": True,
    }
    with sync_client.subscribe([subscription_filter]) as subscription:
        assert_result_type(subscription.ack["result"], "subscription_started")
        with ThreadPoolExecutor(max_workers=1) as executor:
            event_future = executor.submit(next, subscription.events())
            sync_client.pane_send_input(
                live_workspace.pane_id,
                text=safe_command(second_token),
                keys=["Enter"],
            )
            event = event_future.result(timeout=5)
        assert isinstance(event.get("event"), str)
        assert isinstance(event.get("data"), dict)


def test_graphics_lifecycle_when_host_capabilities_are_available(
    sync_client: HerdrClient,
    live_workspace: LiveWorkspace,
) -> None:
    try:
        set_result = sync_client.request(
            "pane.graphics.set",
            {
                "pane_id": live_workspace.pane_id,
                "format": "rgb",
                "image_width": 1,
                "image_height": 1,
                "data_base64": base64.b64encode(b"\x00\x00\x00").decode("ascii"),
            },
        )
    except HerdrApiError as exc:
        if exc.code in {"cell_size_unavailable", "feature_disabled"}:
            pytest.skip(f"pane graphics unavailable: {exc.code}")
        raise

    assert set_result.get("type") in {"ok", "pane_graphics_frame_ack"}
    clear_result = sync_client.request(
        "pane.graphics.clear", {"pane_id": live_workspace.pane_id}
    )
    assert clear_result.get("type") == "ok"


def test_workspace_tab_and_pane_lifecycle(
    sync_client: HerdrClient,
    live_workspace: LiveWorkspace,
) -> None:
    renamed_workspace = sync_client.request(
        "workspace.rename",
        {"workspace_id": live_workspace.workspace_id, "label": "herdr-py-renamed"},
    )
    assert_result_type(renamed_workspace, "workspace_info")
    assert_result_type(
        sync_client.request(
            "workspace.focus", {"workspace_id": live_workspace.workspace_id}
        ),
        "workspace_info",
    )
    assert_result_type(
        sync_client.request(
            "workspace.report_metadata",
            {
                "workspace_id": live_workspace.workspace_id,
                "source": "herdr-py-integration",
                "tokens": {"test": "integration"},
                "ttl_ms": 100,
            },
        ),
        "ok",
    )

    workspace_list = sync_client.workspace_list()
    workspace_rows = workspace_list.get("workspaces")
    assert isinstance(workspace_rows, list)
    current = next(
        row
        for row in workspace_rows
        if isinstance(row, dict)
        and row.get("workspace_id") == live_workspace.workspace_id
    )
    current_number = current.get("number")
    assert isinstance(current_number, int)
    assert_result_type(
        sync_client.request(
            "workspace.move",
            {
                "workspace_id": live_workspace.workspace_id,
                "insert_index": max(current_number - 1, 0),
            },
        ),
        "workspace_list",
    )
    assert_result_type(
        sync_client.request(
            "workspace.move_block",
            {"workspace_ids": [live_workspace.workspace_id]},
        ),
        "workspace_list",
    )

    created_tab = sync_client.request(
        "tab.create",
        {
            "workspace_id": live_workspace.workspace_id,
            "cwd": str(live_workspace.cwd),
            "focus": False,
            "label": "herdr-py-tab",
        },
    )
    assert_result_type(created_tab, "tab_created")
    tab = required_object(created_tab.get("tab"), "tab")
    tab_id = required_string(tab.get("tab_id"), "tab_id")
    created_root_pane = required_object(created_tab.get("root_pane"), "root_pane")
    tab_pane_id = required_string(created_root_pane.get("pane_id"), "pane_id")
    assert_workspace_scope(live_workspace, created_root_pane.get("cwd"))
    assert created_root_pane.get("agent") is None
    assert created_root_pane.get("agent_session") is None

    assert_result_type(sync_client.request("tab.get", {"tab_id": tab_id}), "tab_info")
    assert_result_type(sync_client.request("tab.focus", {"tab_id": tab_id}), "tab_info")
    assert_result_type(
        sync_client.request(
            "tab.rename", {"tab_id": tab_id, "label": "herdr-py-tab-renamed"}
        ),
        "tab_info",
    )
    assert_result_type(
        sync_client.request("tab.move", {"tab_id": tab_id, "insert_index": 0}),
        "tab_list",
    )

    split = sync_client.request(
        "pane.split",
        {
            "direction": "right",
            "cwd": str(live_workspace.cwd),
            "focus": False,
            "target_pane_id": live_workspace.pane_id,
            "workspace_id": live_workspace.workspace_id,
        },
    )
    assert_result_type(split, "pane_info")
    split_pane = required_object(split.get("pane"), "pane")
    split_pane_id = required_string(split_pane.get("pane_id"), "pane_id")
    assert_workspace_scope(live_workspace, split_pane.get("cwd"))
    assert split_pane.get("agent") is None
    assert split_pane.get("agent_session") is None

    assert_result_type(
        sync_client.request(
            "pane.rename",
            {"pane_id": split_pane_id, "label": "herdr-py-pane"},
        ),
        "pane_info",
    )
    assert_result_type(
        sync_client.request("pane.focus", {"pane_id": split_pane_id}), "pane_info"
    )
    assert_result_type(
        sync_client.request(
            "pane.input.set",
            {"pane_id": split_pane_id, "right_click": "pane"},
        ),
        "ok",
    )
    assert_result_type(
        sync_client.request(
            "pane.scroll",
            {"pane_id": split_pane_id, "offset_from_bottom": 0},
        ),
        "pane_info",
    )
    assert_result_type(
        sync_client.request(
            "pane.resize",
            {"pane_id": split_pane_id, "direction": "right", "amount": 0},
        ),
        "pane_resize",
    )
    assert_result_type(
        sync_client.request(
            "pane.focus_direction",
            {"pane_id": split_pane_id, "direction": "left"},
        ),
        "pane_focus_direction",
    )
    assert_result_type(
        sync_client.request(
            "pane.neighbor",
            {"pane_id": split_pane_id, "direction": "left"},
        ),
        "pane_neighbor",
    )
    assert_result_type(
        sync_client.request(
            "pane.swap",
            {"source_pane_id": live_workspace.pane_id, "target_pane_id": split_pane_id},
        ),
        "pane_swap",
    )
    assert_result_type(
        sync_client.request("pane.zoom", {"pane_id": split_pane_id, "mode": "on"}),
        "pane_zoom",
    )
    assert_result_type(
        sync_client.request("pane.zoom", {"pane_id": split_pane_id, "mode": "off"}),
        "pane_zoom",
    )

    layout_export = sync_client.request(
        "layout.export", {"tab_id": live_workspace.tab_id}
    )
    assert_result_type(layout_export, "layout_export")
    layout = required_object(layout_export.get("layout"), "layout")
    root = layout.get("root")
    assert isinstance(root, dict)
    applied_layout = sync_client.request(
        "layout.apply",
        {
            "root": root,
            "tab_id": tab_id,
            "focus": False,
        },
    )
    assert_result_type(applied_layout, "layout_apply")
    applied_description = required_object(applied_layout.get("layout"), "layout")
    applied_tab_id = required_string(applied_description.get("tab_id"), "tab_id")
    if root.get("type") == "split":
        assert_result_type(
            sync_client.request(
                "layout.set_split_ratio",
                {"tab_id": applied_tab_id, "path": [], "ratio": 0.5},
            ),
            "layout_split_ratio_set",
        )

    moved = sync_client.request(
        "pane.move",
        {
            "pane_id": split_pane_id,
            "destination": {
                "type": "new_tab",
                "workspace_id": live_workspace.workspace_id,
                "label": "herdr-py-moved-pane",
            },
            "focus": False,
        },
    )
    assert_result_type(moved, "pane_move")
    move_result = required_object(moved.get("move_result"), "move_result")
    moved_pane = required_object(move_result.get("pane"), "pane")
    moved_pane_id = required_string(moved_pane.get("pane_id"), "pane_id")
    assert_workspace_scope(live_workspace, moved_pane.get("cwd"))

    assert_result_type(
        sync_client.request("tab.close", {"tab_id": applied_tab_id}), "ok"
    )
    assert_result_type(
        sync_client.request("pane.close", {"pane_id": moved_pane_id}), "ok"
    )
    assert tab_pane_id != live_workspace.pane_id


def test_worktree_lifecycle_in_private_repository(
    sync_client: HerdrClient,
    integration_root: Path,
) -> None:
    repo = integration_root / f"repo-{uuid.uuid4().hex}"
    repo.mkdir()
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "herdr-py@example.invalid"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.name", "herdr-py integration"],
        check=True,
        capture_output=True,
    )
    (repo / "README.txt").write_text("integration fixture\n")
    subprocess.run(["git", "-C", str(repo), "add", "README.txt"], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-m", "initial integration fixture"],
        check=True,
        capture_output=True,
    )

    branch = f"herdr-py-{uuid.uuid4().hex}"
    checkout = integration_root / f"checkout-{uuid.uuid4().hex}"
    created = sync_client.request(
        "worktree.create",
        {
            "base": "HEAD",
            "branch": branch,
            "cwd": str(repo),
            "focus": False,
            "label": "herdr-py-worktree",
            "path": str(checkout),
            "trust_repository": True,
        },
    )
    assert_result_type(created, "worktree_created")
    created_workspace = required_object(created.get("workspace"), "workspace")
    created_workspace_id = required_string(
        created_workspace.get("workspace_id"), "workspace_id"
    )
    worktree = required_object(created.get("worktree"), "worktree")
    assert (
        Path(required_string(worktree.get("path"), "path")).resolve()
        == checkout.resolve()
    )
    assert_result_type(
        sync_client.request(
            "worktree.list",
            {"cwd": str(repo), "trust_repository": True},
        ),
        "worktree_list",
    )

    opened = sync_client.request(
        "worktree.open",
        {
            "cwd": str(repo),
            "focus": False,
            "path": str(checkout),
            "trust_repository": True,
        },
    )
    assert_result_type(opened, "worktree_opened")
    opened_workspace = required_object(opened.get("workspace"), "workspace")
    opened_workspace_id = required_string(
        opened_workspace.get("workspace_id"), "workspace_id"
    )
    try:
        removed = sync_client.request(
            "worktree.remove",
            {"workspace_id": created_workspace_id, "force": False},
        )
        assert_result_type(removed, "worktree_removed")
    finally:
        workspace_list = sync_client.workspace_list()
        workspace_rows = workspace_list.get("workspaces")
        assert isinstance(workspace_rows, list)
        owned_ids = {created_workspace_id, opened_workspace_id}
        remaining_ids: set[str] = set()
        for row in workspace_rows:
            if not isinstance(row, dict):
                continue
            workspace_id = row.get("workspace_id")
            if isinstance(workspace_id, str):
                remaining_ids.add(workspace_id)
            worktree_info = row.get("worktree")
            if not isinstance(worktree_info, dict):
                continue
            repo_root = worktree_info.get("repo_root")
            checkout_path = worktree_info.get("checkout_path")
            if isinstance(workspace_id, str) and (
                repo_root == str(repo)
                or (
                    isinstance(checkout_path, str)
                    and integration_root.resolve()
                    in Path(checkout_path).resolve().parents
                )
            ):
                owned_ids.add(workspace_id)
        for workspace_id in owned_ids & remaining_ids:
            sync_client.request(
                "workspace.close",
                {"workspace_id": workspace_id, "close_group": False},
            )
