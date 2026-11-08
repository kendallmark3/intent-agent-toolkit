"""Create .env from .env.example with a freshly generated IAT_JWT_SECRET. Never overwrites."""

from __future__ import annotations

import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main(root: Path = ROOT) -> int:
    target = root / ".env"
    if target.exists():
        print(".env already exists; leaving it unchanged.")
        return 0
    example = (root / ".env.example").read_text(encoding="utf-8")
    marker = "\nIAT_JWT_SECRET=\n"
    if marker not in example:
        print(".env.example has no empty IAT_JWT_SECRET line", file=sys.stderr)
        return 1
    target.write_text(
        example.replace(marker, f"\nIAT_JWT_SECRET={secrets.token_urlsafe(48)}\n"), encoding="utf-8"
    )
    target.chmod(0o600)
    print("Created .env with a new signing secret (git-ignored, mode 600).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
