from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


def config_dir() -> Path:
    return Path.home() / ".config" / "herdr"


def session_socket_path(session: str) -> Path:
    if session == "":
        raise ValueError("session must not be empty")
    return config_dir() / "sessions" / session / "herdr.sock"


def DEFAULT_SOCKET_CANDIDATES(session: str | None = None) -> list[Path]:
    """Return socket candidates in herdr's documented precedence order."""
    if session is not None:
        return [session_socket_path(session)]

    explicit = os.environ.get("HERDR_SOCKET_PATH")
    if explicit is not None and explicit != "":
        return [Path(explicit)]

    env_session = os.environ.get("HERDR_SESSION")
    if env_session is not None and env_session != "":
        return [session_socket_path(env_session)]

    return [config_dir() / "herdr.sock"]


def resolve_socket_path(
    candidates: Iterable[Path] | None = None,
    session: str | None = None,
) -> Path:
    """Resolve the first existing socket path from the candidate list."""
    resolved_candidates = (
        list(candidates)
        if candidates is not None
        else DEFAULT_SOCKET_CANDIDATES(session)
    )
    for candidate in resolved_candidates:
        if candidate.exists():
            return candidate
    searched = ", ".join(str(candidate) for candidate in resolved_candidates)
    raise FileNotFoundError(f"No herdr socket found; checked: {searched}")
