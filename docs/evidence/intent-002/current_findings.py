# Evidence script (INTENT-002). Run from repo root: uv run python docs/evidence/intent-002/current_findings.py
"""Same scenarios as baseline_findings.py, against the INTENT-002 code."""
import hashlib
from typing import ClassVar

from pydantic import BaseModel, SecretStr

from iat.agents.registry import AgentRegistry, default_agents
from iat.security.identity import Identity
from iat.security.pseudonym import SubjectPseudonymizer, derive_key
from iat.services.conversations import InMemoryConversationRepository
from iat.tools.base import Tool
from iat.tools.registry import ExecutionRecorder, ToolExecutor, ToolPolicy, ToolRegistry


class _E(BaseModel):
    pass


class Delete(Tool[_E, _E]):
    name: ClassVar[str] = "delete_supplier"
    description: ClassVar[str] = "write"
    read_only: ClassVar[bool] = False
    input_model: ClassVar[type[BaseModel]] = _E
    output_model: ClassVar[type[BaseModel]] = _E

    def run(self, args: _E) -> _E:
        return _E()


# A: grants come from registration; the gateway has no way to pass an allowlist.
from iat.core.config import DEFAULT_DATA_PATH
from iat.services.supplier_repository import SupplierRepository
from iat.tools.supplier_evidence import SupplierEvidenceLookupTool
tools = ToolRegistry([SupplierEvidenceLookupTool(SupplierRepository.from_json(DEFAULT_DATA_PATH)), Delete()])
gw = ToolExecutor(tools, ToolPolicy(AgentRegistry(default_agents()).tool_grants(), tools)).bind(
    "supplier-readiness", ExecutionRecorder())
print("A current: registered agent calls delete_supplier ->", gw.invoke("delete_supplier", {}).status.value)
try:
    gw.invoke("delete_supplier", {}, allowed_tools={"delete_supplier"})
except TypeError:
    print("A current: passing allowed_tools -> TypeError (no such parameter)")

# B
p = SubjectPseudonymizer(derive_key(SecretStr("s" * 48), None))
print("B current: sha256('alice')[:16] == logged ->", hashlib.sha256(b"alice").hexdigest()[:16] == p("alice"))

# C
repo = InMemoryConversationRepository()
for _ in range(20000):
    repo.create(Identity("flood"), "supplier-readiness")
print("C current: stored conversations after 20000 creates ->", len(repo), "| evictions", dict(repo.evictions))
