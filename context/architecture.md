# Architecture
See [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md). Layers: `api` (HTTP) → `services/runner` (transport-independent execution)
→ `agents` (LangGraph graphs) → `tools` (governed executor) → `services` (data access).
