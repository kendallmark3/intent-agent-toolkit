# Security
See [docs/SECURITY.md](../docs/SECURITY.md). Fail closed: no secret → no startup; identity only from verified JWT `sub`;
conversations owner-scoped (foreign ids return 404); tools denied unless the agent's registration grants them (policy frozen at startup; agents get a
runner-bound gateway); caller ids logged as keyed HMAC pseudonyms; conversations bounded.
