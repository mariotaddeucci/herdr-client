"""Sync and async Python clients for the herdr Unix socket API."""

from .async_client import AsyncHerdrClient, AsyncSubscription
from .exceptions import HerdrApiError, HerdrClientError
from .protocol import (
    CANONICAL_METHODS,
    CONVENIENCE_METHODS,
    METHOD_SCHEMAS,
    NOT_IMPLEMENTED_METHODS,
    SCHEMA_PROTOCOL,
    SCHEMA_VERSION,
    SPECIAL_METHODS,
)
from .sync import HerdrClient, Subscription
from .transport import DEFAULT_SOCKET_CANDIDATES, resolve_socket_path

__all__ = [
    "CANONICAL_METHODS",
    "CONVENIENCE_METHODS",
    "DEFAULT_SOCKET_CANDIDATES",
    "METHOD_SCHEMAS",
    "NOT_IMPLEMENTED_METHODS",
    "SCHEMA_PROTOCOL",
    "SCHEMA_VERSION",
    "SPECIAL_METHODS",
    "AsyncHerdrClient",
    "AsyncSubscription",
    "HerdrApiError",
    "HerdrClient",
    "HerdrClientError",
    "Subscription",
    "resolve_socket_path",
]
