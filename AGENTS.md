# Agent Guide

## Project Shape

- This is a Python 3.13+ library managed with `uv`; run `uv sync` before development. Runtime dependencies must remain empty and `uv.lock` is tracked.
- Source uses `src/herdr_client`. Public exports are in `src/herdr_client/__init__.py`; `sync/` and `async_client/` contain the implementations. Keep the legacy `herdr_client.client` async shim importable.
- The clients use newline-delimited JSON over a local Unix socket. The current registry in `protocol.py` has 103 canonical JSON methods, 10 convenience wrappers, and named `NotImplementedError` stubs for the rest. `pane.graphics.stream` is separate hybrid JSON/binary transport and is not canonical.

## Commands

- Install the locked environment with `uv sync`.
- Run all tests with `uv run pytest`; run a focused test with `uv run pytest tests/test_sync_client.py::test_ping_round_trips_over_unix_socket` or a file such as `uv run pytest tests/test_protocol.py`.
- Run checks with `uv run ruff check .`, `uv run ruff format --check .`, and `uv run pyrefly check`; build with `uv build`.
- Pytest discovers `tests/`, adds `src` to `PYTHONPATH`, enforces strict markers, and uses `pytest-asyncio` auto mode. Tool configuration is in `pyproject.toml`.

## Typing Rules

- The public API must remain simple to use while being strongly typed: model JSON requests, responses, envelopes, and events with `TypedDict`, `Literal`, and recursive JSON aliases. Do not use dataclasses or external validation libraries for wire objects; callers must retain normal dict access.
- Keep `request()` dynamically usable, but add typed `Literal`/`@overload` signatures with a generic fallback for dynamic method names. Do not rely on methods installed with `setattr` for static discoverability; expose dynamic names through generated `.pyi` declarations or equivalent `TYPE_CHECKING` declarations.
- Do not leak `Any` through public signatures. Isolate `json.loads()` and other untyped boundaries, narrow untrusted values explicitly, and validate response shapes before exposing them as typed results.
- Use `Protocol` for structural client interfaces, mocks, and dependency injection. A `Protocol` does not replace static declarations for the concrete dynamically populated clients.
- Keep sync and async APIs equivalent in method names, parameters, envelopes, return models, exceptions, and defaults. Any convenience-operation change requires both implementations, shared types, and both test suites.
- Treat the official Herdr JSON Schema as the source for generated request/response types. Pin the schema to the supported protocol version; do not infer complete types from field names or hand-edit generated files. Reference: https://herdr.dev/docs/socket-api/
- Preserve dict compatibility, unknown response fields, existing method names, socket resolution behavior, error behavior, and the legacy import unless a breaking change is explicit.

## Protocol And Tests

- When changing a canonical method, update `METHOD_SCHEMAS`, `CONVENIENCE_METHODS`/stub sets, typed models or generated artifacts, and sync/async coverage together. Preserve the official schema metadata and registry counts unless the protocol itself changed.
- Socket resolution is ordered as constructor `session`, `HERDR_SOCKET_PATH`, `HERDR_SESSION`, then `$HOME/.config/herdr/herdr.sock`; named sessions use `$HOME/.config/herdr/sessions/<name>/herdr.sock`.
- Tests use temporary fake Unix-socket servers in `tests/test_client.py` and `tests/test_sync_client.py`; registry behavior is in `tests/test_protocol.py` and resolution is in `tests/test_transport.py`. Do not require a live Herdr server.
- Typing changes must keep `py.typed` and generated `.pyi` artifacts included in the wheel when those artifacts are introduced; verify with `uv build`.

## References

- Python typing specification: https://typing.python.org/en/latest/spec/
- Protocols: https://typing.python.org/en/latest/spec/protocol.html
- TypedDict: https://typing.python.org/en/latest/spec/typeddict.html
- Overloads and callables: https://typing.python.org/en/latest/spec/overload.html
- Type distribution and `py.typed`: https://typing.python.org/en/latest/spec/distributing.html
- Pyrefly configuration and strictness: https://pyrefly.org/en/docs/configuration/
