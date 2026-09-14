"""Fetch and verify the pinned Herdr JSON Schema.

This is a development tool only. The client has no runtime dependency on the
schema or on this module.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

from herdr_client.schema import OFFICIAL_SCHEMA_SHA256, OFFICIAL_SCHEMA_URL

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema" / "herdr-api.schema.json"


def fetch() -> bytes:
    parsed_url = urlparse(OFFICIAL_SCHEMA_URL)
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise RuntimeError("official schema URL must use HTTPS")
    with urlopen(OFFICIAL_SCHEMA_URL, timeout=30) as response:  # noqa: S310
        payload = response.read()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != OFFICIAL_SCHEMA_SHA256:
        raise RuntimeError(
            "official schema checksum changed: "
            f"expected {OFFICIAL_SCHEMA_SHA256}, got {digest}"
        )
    return payload


def normalized(payload: bytes) -> bytes:
    document = json.loads(payload)
    return (json.dumps(document, indent=2) + "\n").encode()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the checked-in schema without changing it",
    )
    args = parser.parse_args()

    payload = normalized(fetch())
    if args.check:
        if not SCHEMA_PATH.exists() or SCHEMA_PATH.read_bytes() != payload:
            raise SystemExit(f"schema is stale or missing: {SCHEMA_PATH}")
        return

    SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCHEMA_PATH.write_bytes(payload)


if __name__ == "__main__":
    main()
