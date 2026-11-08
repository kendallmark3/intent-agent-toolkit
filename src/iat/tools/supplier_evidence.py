"""Read-only tool: look up the onboarding evidence on file for a supplier."""

from __future__ import annotations

from typing import Any, ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field

from iat.services.supplier_repository import SupplierRepository
from iat.tools.base import Tool


class SupplierEvidenceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supplier_reference: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9 &.,'\-]*$",
        description="Supplier id (e.g. SUP-001), name, or alias.",
    )


class SupplierEvidenceOutput(BaseModel):
    match: Literal["found", "not_found", "ambiguous"]
    supplier_id: str | None = None
    supplier_name: str | None = None
    candidates: list[str] = Field(default_factory=list)
    evidence: dict[str, dict[str, Any]] = Field(default_factory=dict)


class SupplierEvidenceLookupTool(Tool[SupplierEvidenceInput, SupplierEvidenceOutput]):
    name: ClassVar[str] = "supplier_evidence_lookup"
    description: ClassVar[str] = (
        "Return the onboarding evidence records on file for one supplier. Read-only."
    )
    read_only: ClassVar[bool] = True
    input_model: ClassVar[type[BaseModel]] = SupplierEvidenceInput
    output_model: ClassVar[type[BaseModel]] = SupplierEvidenceOutput

    def __init__(self, repository: SupplierRepository) -> None:
        self._repository = repository

    def run(self, args: SupplierEvidenceInput) -> SupplierEvidenceOutput:
        matches = self._repository.find(args.supplier_reference)
        if not matches:
            return SupplierEvidenceOutput(match="not_found")
        if len(matches) > 1:
            return SupplierEvidenceOutput(
                match="ambiguous", candidates=sorted(m.supplier_id for m in matches)
            )
        record = matches[0]
        return SupplierEvidenceOutput(
            match="found",
            supplier_id=record.supplier_id,
            supplier_name=record.name,
            evidence={k: dict(v) for k, v in record.evidence.items()},
        )
