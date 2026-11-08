# Repository Rules
Read intent/current-feature.md first, including any deltas appended to it. Full text of the active intent: intent/INTENT-001.md.
Run hooks/pre-implement.sh before implementing.
Build the smallest useful delta, then let the human observe it and decide: continue or stop.
Always write tests. `make check` must pass (ruff, mypy --strict, bandit, pytest, intent gate).
Respect architecture: api → services/runner → agents → tools → services. Agents never read data directly; they call tools.
Never weaken security for a demo: no auth bypass, no caller-supplied user ids, no secrets or message content in logs.
