"""Supplier Readiness reference agent, expressed as a LangGraph ``StateGraph``.

Graph shape (pattern credit: the explicit node / conditional-edge style of
ai-agents-masterclass ``7-langgraph-agent``, kept minimal):

    identify ──(reference found)──▶ lookup ──▶ assess ──▶ explain ──▶ END
        └────────(no reference)──────────────▶ assess

The graph is compiled once. Per-execution dependencies (a tool gateway bound to this agent by the
runner, and the evaluation date) arrive through ``RunnableConfig["configurable"]`` so the same
compiled graph is safe to share across concurrent requests and is independent of HTTP.

``ALLOWED_TOOLS`` is this agent's *registration request*. It is read once by the agent registry at
startup; the graph never passes it at call time, so changing it at runtime grants nothing.
"""

from __future__ import annotations

import datetime as dt
import re
from typing import Any, Literal, TypedDict, cast

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from iat.agents.supplier_readiness.narrator import Narrator
from iat.agents.supplier_readiness.rules import evaluate_evidence
from iat.schemas.assessment import Decision, EvidenceItem, MissingEvidence, SupplierAssessment
from iat.tools.registry import AgentToolGateway
from iat.tools.supplier_evidence import SupplierEvidenceLookupTool

AGENT_KEY = "supplier-readiness"
ALLOWED_TOOLS = frozenset({SupplierEvidenceLookupTool.name})

_SUPPLIER_ID_RE = re.compile(r"\bSUP-\d{3,}\b", re.IGNORECASE)
_SUPPLIER_NAME_RE = re.compile(r"(?i:\bsupplier)\s+([A-Z0-9][\w&.'\-]*(?:\s+[A-Z0-9][\w&.'\-]*)*)")


class SupplierState(TypedDict, total=False):
    message: str
    supplier_reference: str | None
    lookup: dict[str, Any] | None
    supplier_id: str | None
    supplier_name: str | None
    decision: Decision
    supporting: list[EvidenceItem]
    missing: list[MissingEvidence]
    assessment: SupplierAssessment


def extract_supplier_reference(message: str) -> str | None:
    """Deterministically pull a supplier id or capitalised name from the question."""
    if match := _SUPPLIER_ID_RE.search(message):
        return match.group(0).upper()
    if match := _SUPPLIER_NAME_RE.search(message):
        return match.group(1).rstrip(".,'") or None
    return None


def _cfg(config: RunnableConfig) -> dict[str, Any]:
    return config.get("configurable", {})


def build_graph(narrator: Narrator) -> CompiledStateGraph[Any, Any, Any, Any]:
    def identify(state: SupplierState) -> SupplierState:
        return {"supplier_reference": extract_supplier_reference(state["message"])}

    def route(state: SupplierState) -> Literal["lookup", "assess"]:
        return "lookup" if state.get("supplier_reference") else "assess"

    def lookup(state: SupplierState, config: RunnableConfig) -> SupplierState:
        tools = cast(AgentToolGateway, _cfg(config)["tools"])
        result = tools.invoke(
            SupplierEvidenceLookupTool.name, {"supplier_reference": state["supplier_reference"]}
        )
        return {"lookup": result.model_dump(mode="json")}

    def assess(state: SupplierState, config: RunnableConfig) -> SupplierState:
        as_of = cast(dt.date, _cfg(config)["as_of"])
        reference = state.get("supplier_reference")
        lookup_result = state.get("lookup")

        def insufficient(check: str, reason: str) -> SupplierState:
            return {
                "supplier_id": None,
                "supplier_name": None,
                "decision": Decision.INSUFFICIENT_EVIDENCE,
                "supporting": [],
                "missing": [MissingEvidence(check=check, reason=reason)],
            }

        if not reference:
            return insufficient(
                "supplier_identity", "No supplier id or name could be identified in the request"
            )
        if lookup_result is None or lookup_result["status"] != "OK":
            status = lookup_result["status"] if lookup_result else "NOT_RUN"
            return insufficient(
                "supplier_evidence", f"Supplier evidence lookup unavailable (status {status})"
            )
        output = lookup_result["output"]
        if output["match"] == "not_found":
            return insufficient("supplier_record", f"No supplier record found for '{reference}'")
        if output["match"] == "ambiguous":
            return insufficient(
                "supplier_identity",
                f"'{reference}' matches multiple suppliers: {', '.join(output['candidates'])}",
            )
        rules = evaluate_evidence(output["evidence"], as_of)
        return {
            "supplier_id": output["supplier_id"],
            "supplier_name": output["supplier_name"],
            "decision": rules.decision,
            "supporting": rules.supporting,
            "missing": rules.missing,
        }

    def explain(state: SupplierState, config: RunnableConfig) -> SupplierState:
        cfg = _cfg(config)
        assessment = SupplierAssessment(
            supplier_id=state.get("supplier_id"),
            supplier_name=state.get("supplier_name"),
            decision=state["decision"],
            supporting_evidence=state["supporting"],
            missing_evidence=state["missing"],
            explanation=narrator.explain(
                state.get("supplier_name"), state["decision"], state["supporting"], state["missing"]
            ),
            execution_id=str(cfg["execution_id"]),
            as_of=cast(dt.date, cfg["as_of"]).isoformat(),
        )
        return {"assessment": assessment}

    graph = StateGraph(SupplierState)
    graph.add_node("identify", identify)
    graph.add_node("lookup", lookup)
    graph.add_node("assess", assess)
    graph.add_node("explain", explain)
    graph.set_entry_point("identify")
    graph.add_conditional_edges("identify", route, {"lookup": "lookup", "assess": "assess"})
    graph.add_edge("lookup", "assess")
    graph.add_edge("assess", "explain")
    graph.add_edge("explain", END)
    return graph.compile()
