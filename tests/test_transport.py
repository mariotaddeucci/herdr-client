from __future__ import annotations

from pathlib import Path

import pytest

from herdr_client.transport import DEFAULT_SOCKET_CANDIDATES, resolve_socket_path


@pytest.fixture(autouse=True)
def clear_socket_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ("HERDR_SOCKET_PATH", "HERDR_SESSION"):
        monkeypatch.delenv(key, raising=False)


def test_default_socket_candidates_use_documented_default() -> None:
    candidates = DEFAULT_SOCKET_CANDIDATES()

    assert candidates == [Path.home() / ".config" / "herdr" / "herdr.sock"]


def test_resolve_socket_path_prefers_explicit_env_override(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    explicit = tmp_path / "explicit.sock"
    explicit.touch()
    monkeypatch.setenv("HERDR_SOCKET_PATH", str(explicit))

    resolved = resolve_socket_path()

    assert resolved == explicit


def test_resolve_socket_path_uses_env_session(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("HERDR_SESSION", "demo")
    session_socket = tmp_path / ".config" / "herdr" / "sessions" / "demo" / "herdr.sock"
    session_socket.parent.mkdir(parents=True)
    session_socket.touch()

    resolved = resolve_socket_path()

    assert resolved == session_socket


def test_resolve_socket_path_prefers_session_argument(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    explicit = tmp_path / "explicit.sock"
    explicit.touch()
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("HERDR_SOCKET_PATH", str(explicit))
    session_socket = tmp_path / ".config" / "herdr" / "sessions" / "demo" / "herdr.sock"
    session_socket.parent.mkdir(parents=True)
    session_socket.touch()

    resolved = resolve_socket_path(session="demo")

    assert resolved == session_socket


def test_resolve_socket_path_raises_when_no_candidate_exists(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        assert (
            resolve_socket_path(
                candidates=[tmp_path / "missing-a.sock", tmp_path / "missing-b.sock"]
            )
            is not None
        )


def test_empty_session_is_rejected() -> None:
    with pytest.raises(ValueError, match="session must not be empty"):
        assert DEFAULT_SOCKET_CANDIDATES(session="") is not None
