from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import NoReturn

from .protocol import NOT_IMPLEMENTED_METHODS, SPECIAL_METHODS, _not_implemented

STUB_METHODS = NOT_IMPLEMENTED_METHODS | SPECIAL_METHODS


def _method_name(method: str) -> str:
    return method.replace(".", "_")


def _sync_stub(method: str) -> Callable[..., NoReturn]:
    def stub(_self: object, *_args: object, **_kwargs: object) -> NoReturn:
        _not_implemented(method)

    stub.__name__ = _method_name(method)
    return stub


def _async_stub(method: str) -> Callable[..., Awaitable[NoReturn]]:
    async def stub(_self: object, *_args: object, **_kwargs: object) -> NoReturn:
        _not_implemented(method)

    stub.__name__ = _method_name(method)
    return stub


class SyncMethodStubs:
    """Named sync placeholders for official methods without wrappers."""


class AsyncMethodStubs:
    """Named async placeholders for official methods without wrappers."""


for _method in sorted(STUB_METHODS):
    setattr(SyncMethodStubs, _method_name(_method), _sync_stub(_method))
    setattr(AsyncMethodStubs, _method_name(_method), _async_stub(_method))
