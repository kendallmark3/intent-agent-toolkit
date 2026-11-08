# Business Rules
Supplier readiness (synthetic): five required checks — tax registration, sanctions screening, insurance certificate
(not expired on the assessment date), bank account verification, code of conduct.
- Any failed check → NOT_READY.
- Otherwise any missing or unrecognized evidence → INSUFFICIENT_EVIDENCE.
- Otherwise → READY. Missing evidence is never assumed. Rules live in `src/iat/agents/supplier_readiness/rules.py`.
