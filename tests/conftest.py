from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="run tests that connect to a live Herdr socket",
    )
    parser.addoption(
        "--run-agent-integration",
        action="store_true",
        default=False,
        help="run tests that start a local OpenCode agent through Herdr",
    )


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    run_integration = config.getoption("--run-integration")
    run_agent_integration = config.getoption("--run-agent-integration")
    for item in items:
        if "integration" in item.keywords and not run_integration:
            item.add_marker(
                pytest.mark.skip(
                    reason="pass --run-integration to run live Herdr tests"
                )
            )
        elif "agent_integration" in item.keywords and not run_agent_integration:
            item.add_marker(
                pytest.mark.skip(
                    reason="pass --run-agent-integration to start a local agent"
                )
            )
