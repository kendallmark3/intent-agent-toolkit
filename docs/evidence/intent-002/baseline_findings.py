# Evidence script (INTENT-002). Run: PYTHONPATH=<checkout of 8ecc05d>/src python baseline_findings.py
"""Demonstrate INTENT-001 findings A, B, C on the baseline commit (run with PYTHONPATH=<baseline>/src)."""
import hashlib
from typing import ClassVar

from pydantic import BaseModel

from iat.security.identity import Identity
from iat.services.conversations import InMemoryConversationRepository
from iat.tools.base import Tool
from iat.tools.registry import ExecutionRecorder, ToolExecutor, ToolRegistry


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


# A: an agent registered for the lookup tool passes its own wider allowlist.
r = ToolExecutor(ToolRegistry([Delete()])).invoke(
    agent="supplier-readiness", allowed_tools=frozenset({"delete_supplier"}),
    tool_name="delete_supplier", args={}, recorder=ExecutionRecorder())
print("A baseline: agent-supplied allowlist ->", r.status.value)

# B: logged identifier is recomputable from a guessed user name.
logged = Identity("alice").subject_hash
print("B baseline: sha256('alice')[:16] == logged ->", hashlib.sha256(b"alice").hexdigest()[:16] == logged)

# C: no bound on conversations.
repo = InMemoryConversationRepository()
for _ in range(20000):
    repo.create(Identity("flood"), "supplier-readiness")
print("C baseline: stored conversations after 20000 creates ->", len(repo._items))
