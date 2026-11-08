# Adding an Agent — the IAT Template Path

The supplier-readiness agent is the reference. A new agent (for example *customer onboarding* or
*credit card application review*) follows the same seven steps and gets authentication, tool
governance, bounded memory, execution evidence, the web console, regression, smoke tests and CI
with no extra wiring.

Start each new agent with an intent: copy `templates/feature-template.md`, state the outcome,
decisions, evidence and boundaries, then run `bash hooks/pre-implement.sh`.

## 1. Data access as a read-only tool — `src/iat/tools/<name>.py`

Agents never read data directly. Define a `Tool` with Pydantic input and output models:

```python
class ApplicantLookupInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    applicant_reference: str = Field(
        min_length=1, max_length=100, pattern=r"^[A-Za-z0-9][A-Za-z0-9 .'\-]*$"
    )


class ApplicantLookupTool(Tool[ApplicantLookupInput, ApplicantLookupOutput]):
    name: ClassVar[str] = "applicant_lookup"
    description: ClassVar[str] = "Return the evidence on file for one applicant. Read-only."
    read_only: ClassVar[bool] = True
    input_model: ClassVar[type[BaseModel]] = ApplicantLookupInput
    output_model: ClassVar[type[BaseModel]] = ApplicantLookupOutput
```

Register it in `create_app` (`ToolRegistry([...])`). Write tools need a separate intent: they
change the risk profile.

## 2. Output contract — `src/iat/schemas/<name>.py`

A frozen Pydantic model with a closed decision enum, the evidence used, the evidence missing, an
explanation and `execution_id`. The runner validates every result against it.

## 3. Decision rules — `src/iat/agents/<name>/rules.py`

Rules that do not need judgement are ordinary code. Keep the supplier pattern:
- unknown or unparseable evidence is **missing**, never satisfied;
- a failed check outranks missing evidence;
- the decision is computed before any explanation.

## 4. Workflow — `src/iat/agents/<name>/graph.py`

A LangGraph `StateGraph` compiled once. Call tools only through the gateway the runner provides:

```python
def lookup(state, config):
    tools = config["configurable"]["tools"]  # AgentToolGateway, bound by the runner
    result = tools.invoke("applicant_lookup", {"applicant_reference": state["reference"]})
    return {"lookup": result.model_dump(mode="json")}
```

Fail closed: a denied, invalid or failed tool call must lead to the "insufficient evidence"
decision, never to approval. If a model is added later, keep it out of the decision node (see
`Narrator`).

## 5. Regression cases — `src/iat/agents/<name>/regression_cases.json`

Declare the expected decision for representative inputs. A dotted key compares a list attribute
regardless of order:

```json
{"cases": [
  {"name": "approved-applicant", "message": "Can applicant Dana Reyes be approved?",
   "expect": {"decision": "APPROVED", "missing_evidence.check": []}}
]}
```

Cover: a clear approval, each failure kind, missing evidence, an unknown subject, and no subject
named. These cases run in the console, `POST /v1/agents/<key>/regression`, `make demo`-style
scripts, `scripts/smoke.py`, and the CI container job.

## 6. Registration — `src/iat/agents/registry.py`

```python
AgentDefinition(
    key="credit-card-review",
    description="…",
    allowed_tools=frozenset({"applicant_lookup"}),   # the ONLY source of tool permission
    graph=build_graph(),
    output_key="assessment",
    output_model=CreditCardAssessment,
    examples=("Can applicant Dana Reyes be approved?", …),
    regression_cases=load_cases(Path(__file__).with_name("regression_cases.json")),
)
```

At startup the `ToolPolicy` is built from `allowed_tools`; granting an unregistered tool fails
startup. The console lists the agent, shows its workflow and examples, and runs its regression
cases automatically.

## 7. Tests — `tests/test_<name>.py`

At minimum: each decision path, missing evidence not invented, the agent cannot call a tool outside
its registration, and the regression endpoint passing. Then run:

```bash
make check      # lint, strict types, security scans, tests, intent gate
make run        # then open http://127.0.0.1:8000/ui/ with a token from `make token`
make smoke      # against the running service
```

## Synthetic data rule

Use synthetic data until an intent introduces real data with its own controls (classification,
retention, access logging). Credit and identity data in particular need that intent first.
