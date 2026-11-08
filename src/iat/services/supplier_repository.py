"""Read-only access to synthetic supplier records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict


class SupplierRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    supplier_id: str
    name: str
    aliases: tuple[str, ...] = ()
    evidence: dict[str, dict[str, Any]]


class SupplierRepository:
    def __init__(self, records: list[SupplierRecord]) -> None:
        self._records = records

    @classmethod
    def from_json(cls, path: Path) -> SupplierRepository:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls([SupplierRecord.model_validate(r) for r in raw["suppliers"]])

    def __len__(self) -> int:
        return len(self._records)

    def find(self, reference: str) -> list[SupplierRecord]:
        """Match by exact id, exact name/alias, then name prefix (case-insensitive)."""
        ref = reference.strip().casefold()
        exact = [
            r
            for r in self._records
            if ref in {r.supplier_id.casefold(), r.name.casefold()}
            or ref in {a.casefold() for a in r.aliases}
        ]
        if exact:
            return exact
        return [r for r in self._records if r.name.casefold().startswith(ref)]
