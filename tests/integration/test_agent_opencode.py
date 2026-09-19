from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import Mapping
from contextlib import suppress

import pytest

from herdr_client import (
    AsyncHerdrClient,
    HerdrClient,
    HerdrClientError,
)

from .support import (
    OPENCODE_TEST_MODEL,
    LiveWorkspace,
    assert_result_type,
    required_object,
)

pytestmark = [pytest.mark.integration, pytest.mark.agent_integration]


def _assert_agent(
    result: Mapping[str, object],
    workspace: LiveWorkspace,
    name: str,
) -> Mapping[str, object]:
    agent = required_object(result.get("agent"), "agent")
    assert agent.get("agent") == "opencode"
    assert agent.get("name") == name
    assert agent.get("pane_id") == workspace.pane_id
    assert agent.get("workspace_id") == workspace.workspace_id
    assert agent.get("tab_id") == workspace.tab_id
    assert agent.get("agent_status") in {
        "idle",
        "working",
        "blocked",
        "done",
        "unknown",
    }
    return agent


def _assert_agent_list(
    result: Mapping[str, object],
    workspace: LiveWorkspace,
    name: str,
) -> None:
    assert_result_type(result, "agent_list")
    agents = result.get("agents")
    assert isinstance(agents, list)
    assert any(
        isinstance(agent, Mapping)
        and agent.get("name") == name
        and agent.get("pane_id") == workspace.pane_id
        for agent in agents
    )


def _assert_agent_read(
    result: Mapping[str, object],
    workspace: LiveWorkspace,
    expected_text: str | None = None,
) -> None:
    assert_result_type(result, "pane_read")
    read = required_object(result.get("read"), "read")
    assert read.get("pane_id") == workspace.pane_id
    text = read.get("text")
    assert isinstance(text, str)
    if expected_text is not None:
        assert expected_text in text


def _shell_is_ready(result: Mapping[str, object]) -> bool:
    assert_result_type(result, "pane_process_info")
    process_info = required_object(result.get("process_info"), "process_info")
    shell_pid = process_info.get("shell_pid")
    foreground_group_id = process_info.get("foreground_process_group_id")
    foreground_processes = process_info.get("foreground_processes")
    if not isinstance(shell_pid, int) or foreground_group_id != shell_pid:
        return False
    if not isinstance(foreground_processes, list) or len(foreground_processes) != 1:
        return False
    foreground = foreground_processes[0]
    return isinstance(foreground, Mapping) and foreground.get("pid") == shell_pid


def _wait_for_shell_sync(client: HerdrClient, workspace: LiveWorkspace) -> None:
    deadline = time.monotonic() + 5.0
    while True:
        result = client.request("pane.process_info", {"pane_id": workspace.pane_id})
        if _shell_is_ready(result):
            return
        if time.monotonic() >= deadline:
            pytest.fail("Herdr pane did not reach a stable shell foreground")
        time.sleep(0.05)


async def _wait_for_shell_async(
    client: AsyncHerdrClient,
    workspace: LiveWorkspace,
) -> None:
    deadline = time.monotonic() + 5.0
    while True:
        result = await client.request(
            "pane.process_info", {"pane_id": workspace.pane_id}
        )
        if _shell_is_ready(result):
            return
        if time.monotonic() >= deadline:
            pytest.fail("Herdr pane did not reach a stable shell foreground")
        await asyncio.sleep(0.05)


def _start_params(
    workspace: LiveWorkspace,
    name: str,
    model: str,
) -> dict[str, object]:
    return {
        "name": name,
        "kind": "opencode",
        "pane_id": workspace.pane_id,
        "args": ["--model", model],
        "timeout_ms": 30_000,
    }


def _stop_sync_agent(client: HerdrClient, name: str) -> None:
    with suppress(HerdrClientError):
        client.request("agent.send_keys", {"target": name, "keys": ["ctrl+c"]})


async def _stop_async_agent(client: AsyncHerdrClient, name: str) -> None:
    with suppress(HerdrClientError):
        await client.request("agent.send_keys", {"target": name, "keys": ["ctrl+c"]})


def test_opencode_agent_lifecycle(
    agent_client: HerdrClient,
    live_workspace: LiveWorkspace,
    opencode_test_model: str,
) -> None:
    name = f"herdr-py-opencode-{uuid.uuid4().hex[:12]}"
    started = True
    try:
        _wait_for_shell_sync(agent_client, live_workspace)
        result = agent_client.request(
            "agent.start", _start_params(live_workspace, name, opencode_test_model)
        )
        assert_result_type(result, "agent_started")
        started_agent = required_object(result.get("agent"), "agent")
        assert started_agent.get("name") == name
        assert started_agent.get("pane_id") == live_workspace.pane_id
        argv = result.get("argv")
        assert isinstance(argv, list)
        assert opencode_test_model == OPENCODE_TEST_MODEL
        assert opencode_test_model in argv

        agent = _assert_agent(
            agent_client.request(
                "agent.wait",
                {
                    "target": live_workspace.pane_id,
                    "until": ["idle", "done"],
                    "timeout_ms": 120_000,
                },
            ),
            live_workspace,
            name,
        )
        _assert_agent_list(agent_client.request("agent.list", {}), live_workspace, name)
        _assert_agent(
            agent_client.request("agent.get", {"target": name}),
            live_workspace,
            name,
        )
        _assert_agent_read(
            agent_client.request(
                "agent.read",
                {
                    "target": name,
                    "source": "recent_unwrapped",
                    "lines": 80,
                    "strip_ansi": True,
                },
            ),
            live_workspace,
        )

        prompt = (
            "Reply with exactly HERDR_OPENCODE_TEST_OK. "
            "Do not use tools or modify files."
        )
        prompted = agent_client.request(
            "agent.prompt",
            {
                "target": name,
                "text": prompt,
                "wait": {"until": ["idle", "done"], "timeout_ms": 120_000},
            },
        )
        assert_result_type(prompted, "agent_prompted")
        _assert_agent(prompted, live_workspace, name)

        waited = agent_client.request(
            "agent.wait",
            {
                "target": name,
                "until": ["idle", "done"],
                "timeout_ms": 120_000,
            },
        )
        _assert_agent(waited, live_workspace, name)
        assert agent.get("pane_id") == live_workspace.pane_id
        _assert_agent_read(
            agent_client.request(
                "agent.read",
                {
                    "target": name,
                    "source": "recent_unwrapped",
                    "lines": 120,
                    "strip_ansi": True,
                },
            ),
            live_workspace,
            "HERDR_OPENCODE_TEST_OK",
        )
    finally:
        if started:
            _stop_sync_agent(agent_client, name)


@pytest.mark.asyncio
async def test_opencode_agent_lifecycle_async(
    async_agent_client: AsyncHerdrClient,
    live_workspace: LiveWorkspace,
    opencode_test_model: str,
) -> None:
    name = f"herdr-py-opencode-{uuid.uuid4().hex[:12]}"
    started = True
    try:
        await _wait_for_shell_async(async_agent_client, live_workspace)
        result = await async_agent_client.request(
            "agent.start",
            _start_params(live_workspace, name, opencode_test_model),
        )
        assert_result_type(result, "agent_started")
        started_agent = required_object(result.get("agent"), "agent")
        assert started_agent.get("name") == name
        assert started_agent.get("pane_id") == live_workspace.pane_id
        argv = result.get("argv")
        assert isinstance(argv, list)
        assert opencode_test_model == OPENCODE_TEST_MODEL
        assert opencode_test_model in argv

        agent = _assert_agent(
            await async_agent_client.request(
                "agent.wait",
                {
                    "target": live_workspace.pane_id,
                    "until": ["idle", "done"],
                    "timeout_ms": 120_000,
                },
            ),
            live_workspace,
            name,
        )
        _assert_agent_list(
            await async_agent_client.request("agent.list", {}),
            live_workspace,
            name,
        )
        _assert_agent(
            await async_agent_client.request("agent.get", {"target": name}),
            live_workspace,
            name,
        )
        _assert_agent_read(
            await async_agent_client.request(
                "agent.read",
                {
                    "target": name,
                    "source": "recent_unwrapped",
                    "lines": 80,
                    "strip_ansi": True,
                },
            ),
            live_workspace,
        )

        prompt = (
            "Reply with exactly HERDR_OPENCODE_TEST_OK. "
            "Do not use tools or modify files."
        )
        prompted = await async_agent_client.request(
            "agent.prompt",
            {
                "target": name,
                "text": prompt,
                "wait": {"until": ["idle", "done"], "timeout_ms": 120_000},
            },
        )
        assert_result_type(prompted, "agent_prompted")
        _assert_agent(prompted, live_workspace, name)

        waited = await async_agent_client.request(
            "agent.wait",
            {
                "target": name,
                "until": ["idle", "done"],
                "timeout_ms": 120_000,
            },
        )
        _assert_agent(waited, live_workspace, name)
        assert agent.get("pane_id") == live_workspace.pane_id
        _assert_agent_read(
            await async_agent_client.request(
                "agent.read",
                {
                    "target": name,
                    "source": "recent_unwrapped",
                    "lines": 120,
                    "strip_ansi": True,
                },
            ),
            live_workspace,
            "HERDR_OPENCODE_TEST_OK",
        )
    finally:
        if started:
            await _stop_async_agent(async_agent_client, name)
