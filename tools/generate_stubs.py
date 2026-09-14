"""Generate static declarations for runtime-installed stub methods."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from herdr_client.stub_methods import STUB_METHODS

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "src/herdr_client/stub_methods.pyi"


def render() -> str:
    names = sorted(method.replace(".", "_") for method in STUB_METHODS)
    lines = [
        "from typing import NoReturn",
        "",
        "STUB_METHODS: frozenset[str]",
        "",
        "",
        "class SyncMethodStubs:",
    ]
    lines.extend(
        f"    def {name}(self, *args: object, **kwargs: object) -> NoReturn: ..."
        for name in names
    )
    lines.extend(["", "", "class AsyncMethodStubs:"])
    lines.extend(
        f"    async def {name}(self, *args: object, **kwargs: object) -> NoReturn: ..."
        for name in names
    )
    return "\n".join(lines) + "\n"


def format_generated(source: str) -> str:
    completed = subprocess.run(  # noqa: S603
        [
            sys.executable,
            "-m",
            "ruff",
            "format",
            "--stdin-filename",
            str(OUTPUT_PATH),
            "-",
        ],
        input=source,
        capture_output=True,
        check=True,
        text=True,
    )
    return completed.stdout


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = format_generated(render())

    if args.check:
        if not OUTPUT_PATH.exists() or OUTPUT_PATH.read_text() != output:
            raise SystemExit(f"generated stubs are stale: {OUTPUT_PATH}")
        return

    OUTPUT_PATH.write_text(output)


if __name__ == "__main__":
    main()
