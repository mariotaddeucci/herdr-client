from __future__ import annotations

import os
import stat
import uuid
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
import pytest_asyncio

from herdr_client import AsyncHerdrClient, HerdrClient

from .support import (
    LiveWorkspace,
    assert_result_type,
    assert_workspace_scope,
    required_object,
    required_string,
)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="run tests that connect to a live Herdr socket",
    )


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    if config.getoption("--run-integration"):
        return
    skip = pytest.mark.skip(reason="pass --run-integration to run live Herdr tests")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def integration_socket(request: pytest.FixtureRequest) -> Path:
    raw_path = os.environ.get("HERDR_INTEGRATION_SOCKET")
    if not raw_path:
        if request.config.getoption("--run-integration"):
            pytest.fail("--run-integration requires HERDR_INTEGRATION_SOCKET")
        pytest.skip("HERDR_INTEGRATION_SOCKET is not configured")
    socket_path = Path(raw_path).expanduser()
    if not socket_path.exists():
        pytest.fail(f"Herdr integration socket does not exist: {socket_path}")
    if not stat.S_ISSOCK(socket_path.stat().st_mode):
        pytest.fail(f"Herdr integration path is not a Unix socket: {socket_path}")
    return socket_path


@pytest.fixture(scope="session")
def integration_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("herdr-integration")


@pytest.fixture(scope="session")
def sync_client(integration_socket: Path) -> HerdrClient:
    return HerdrClient(socket_path=integration_socket, timeout=5.0)


@pytest_asyncio.fixture(scope="session")
async def async_client(integration_socket: Path) -> AsyncHerdrClient:
    return AsyncHerdrClient(socket_path=integration_socket, timeout=5.0)


def _workspace_from_created(
    result: dict[str, object],
    cwd: Path,
) -> LiveWorkspace:
    assert_result_type(result, "workspace_created")
    workspace = required_object(result.get("workspace"), "workspace")
    tab = required_object(result.get("tab"), "tab")
    root_pane = required_object(result.get("root_pane"), "root_pane")
    workspace_id = required_string(workspace.get("workspace_id"), "workspace_id")
    tab_id = required_string(tab.get("tab_id"), "tab_id")
    pane_id = required_string(root_pane.get("pane_id"), "pane_id")
    assert root_pane.get("agent") is None
    assert root_pane.get("agent_session") is None
    assert_workspace_scope(
        LiveWorkspace(workspace_id, tab_id, pane_id, cwd), root_pane.get("cwd")
    )
    return LiveWorkspace(workspace_id, tab_id, pane_id, cwd)


@pytest.fixture
def live_workspace(
    sync_client: HerdrClient,
    integration_root: Path,
) -> Iterator[LiveWorkspace]:
    cwd = integration_root / f"workspace-{uuid.uuid4().hex}"
    cwd.mkdir()
    workspace_id: str | None = None
    try:
        result = sync_client.request(
            "workspace.create",
            {"cwd": str(cwd), "focus": False, "label": "herdr-py-integration"},
        )
        created_workspace = result.get("workspace")
        if isinstance(created_workspace, dict):
            candidate_id = created_workspace.get("workspace_id")
            if isinstance(candidate_id, str):
                workspace_id = candidate_id
        workspace = _workspace_from_created(result, cwd)
        yield workspace
    finally:
        if workspace_id is not None:
            closed = sync_client.request(
                "workspace.close",
                {"workspace_id": workspace_id, "close_group": False},
            )
            assert_result_type(closed, "ok")


@pytest_asyncio.fixture
async def async_live_workspace(
    async_client: AsyncHerdrClient,
    integration_root: Path,
) -> AsyncIterator[LiveWorkspace]:
    cwd = integration_root / f"workspace-{uuid.uuid4().hex}"
    cwd.mkdir()
    workspace_id: str | None = None
    try:
        result = await async_client.request(
            "workspace.create",
            {"cwd": str(cwd), "focus": False, "label": "herdr-py-integration"},
        )
        created_workspace = result.get("workspace")
        if isinstance(created_workspace, dict):
            candidate_id = created_workspace.get("workspace_id")
            if isinstance(candidate_id, str):
                workspace_id = candidate_id
        workspace = _workspace_from_created(result, cwd)
        yield workspace
    finally:
        if workspace_id is not None:
            closed = await async_client.request(
                "workspace.close",
                {"workspace_id": workspace_id, "close_group": False},
            )
            assert_result_type(closed, "ok")
