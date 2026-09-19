from __future__ import annotations

from typing import TYPE_CHECKING, NoReturn

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

from .protocol import NOT_IMPLEMENTED_METHODS, SPECIAL_METHODS, not_implemented

STUB_METHODS = NOT_IMPLEMENTED_METHODS | SPECIAL_METHODS


def method_name(method: str) -> str:
    return method.replace(".", "_")


def sync_stub(method: str) -> Callable[..., NoReturn]:
    def stub(instance: object, *arguments: object, **keywords: object) -> NoReturn:
        del instance, arguments, keywords
        not_implemented(method)

    stub.__name__ = method_name(method)
    return stub


def async_stub(method: str) -> Callable[..., Awaitable[NoReturn]]:
    async def stub(
        instance: object, *arguments: object, **keywords: object
    ) -> NoReturn:
        del instance, arguments, keywords
        not_implemented(method)

    stub.__name__ = method_name(method)
    return stub


class SyncMethodStubs:
    """Named sync placeholders for official methods without wrappers."""


class AsyncMethodStubs:
    """Named async placeholders for official methods without wrappers."""


for method in sorted(STUB_METHODS):
    setattr(SyncMethodStubs, method_name(method), sync_stub(method))
    setattr(AsyncMethodStubs, method_name(method), async_stub(method))
