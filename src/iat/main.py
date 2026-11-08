"""Local entry point: ``uv run iat-serve``."""

from __future__ import annotations

import os

import uvicorn


def run() -> None:
    uvicorn.run(
        "iat.api.app:create_app",
        factory=True,
        host=os.environ.get("IAT_HOST", "127.0.0.1"),
        port=int(os.environ.get("IAT_PORT", "8000")),
        log_level="warning",
    )


if __name__ == "__main__":
    run()
