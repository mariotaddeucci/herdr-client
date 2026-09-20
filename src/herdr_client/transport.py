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
    """Return socket candidates in Herdr's documented precedence order.

    Args:
        session: Optional named Herdr session. When supplied, only that session's
            socket path is returned.

    Returns:
        Candidate paths ordered by precedence. Without ``session``, the result uses
        ``HERDR_SOCKET_PATH``, then ``HERDR_SESSION``, then the default socket.

    Example:
        ```python
        from herdr_client import DEFAULT_SOCKET_CANDIDATES

        candidates = DEFAULT_SOCKET_CANDIDATES(session="work")
        print(candidates[0])
        ```
    """
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
    """Resolve the first existing socket path from the candidate list.

    Args:
        candidates: Optional paths to check in order. When omitted, use Herdr's
            standard environment and default socket resolution order.
        session: Optional named session used to build the candidate path when
            ``candidates`` is omitted.

    Returns:
        The first existing Unix socket path.

    Raises:
        FileNotFoundError: If none of the candidate paths exists.

    Example:
        ```python
        from herdr_client import resolve_socket_path

        socket_path = resolve_socket_path(session="work")
        print(socket_path)
        ```
    """
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
