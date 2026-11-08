# Security
See [docs/SECURITY.md](../docs/SECURITY.md). Fail closed: no secret → no startup; identity only from verified JWT `sub`;
conversations owner-scoped (foreign ids return 404); tools denied unless registered and allowlisted for the agent.
