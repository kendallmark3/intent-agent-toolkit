// Intent Agent Toolkit console. Plain JS, no dependencies.
// Security: every value from the API is rendered with textContent (never innerHTML). The token is
// held in sessionStorage for this tab only and is never written into evidence downloads.
"use strict";

const state = {
  token: "",
  agents: [],
  agent: null,
  conversationId: null,
  version: null,
  history: [],
  lastRegression: null,
};

const $ = (id) => document.getElementById(id);

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k === "text") node.textContent = v;
    else node.setAttribute(k, v);
  }
  for (const child of children) node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  return node;
}

function setMessage(id, text, kind = "") {
  const node = $(id);
  node.textContent = text;
  node.className = "message" + (kind ? " " + kind : "");
}

function store(key, value) {
  try {
    if (value) sessionStorage.setItem(key, value);
    else sessionStorage.removeItem(key);
  } catch (_) { /* storage unavailable: keep in memory only */ }
}

function load(key) {
  try { return sessionStorage.getItem(key) || ""; } catch (_) { return ""; }
}

async function api(method, path, body) {
  const headers = { "Content-Type": "application/json" };
  if (state.token) headers.Authorization = "Bearer " + state.token;
  const response = await fetch(path, { method, headers, body: body ? JSON.stringify(body) : undefined });
  let data = null;
  try { data = await response.json(); } catch (_) { data = null; }
  if (!response.ok) {
    const error = (data && data.error) || {};
    const err = new Error(error.message || "Request failed (" + response.status + ")");
    err.status = response.status;
    err.code = error.code;
    err.requestId = error.request_id || response.headers.get("X-Request-ID");
    err.executionId = error.execution_id;
    throw err;
  }
  return data;
}

function describeError(err) {
  if (err.status === 401) return "Not signed in or token expired. Generate a new token with `make token`.";
  if (err.status === 403) return "Signed in, but the token lacks the required scope (" + err.message + ").";
  const ids = [err.requestId && "request " + err.requestId, err.executionId && "execution " + err.executionId].filter(Boolean);
  return err.message + (ids.length ? " — " + ids.join(", ") : "");
}

// ---------------------------------------------------------------- health

async function checkHealth() {
  const box = $("health");
  try {
    const health = await api("GET", "/health/ready");
    state.version = health.version;
    box.className = "status ok";
    $("health-text").textContent = "Service ready · v" + health.version;
  } catch (err) {
    box.className = "status bad";
    $("health-text").textContent = "Service not ready";
  }
}

// ---------------------------------------------------------------- access

async function connect() {
  const token = $("token").value.trim();
  if (!token) { setMessage("access-msg", "Paste a token first.", "error"); return; }
  state.token = token;
  try {
    state.agents = await api("GET", "/v1/agents");
    store("iat-token", token);
    $("who").textContent = "Signed in · " + state.agents.length + " agent" + (state.agents.length === 1 ? "" : "s");
    setMessage("access-msg", "Connected.", "ok");
    renderAgents();
    for (const id of ["run", "regression"]) $(id).hidden = false;
  } catch (err) {
    state.token = "";
    store("iat-token", "");
    setMessage("access-msg", describeError(err), "error");
  }
}

function disconnect() {
  state.token = "";
  state.conversationId = null;
  store("iat-token", "");
  $("token").value = "";
  $("who").textContent = "Not signed in";
  setMessage("access-msg", "Token cleared from this tab.");
  for (const id of ["run", "result", "regression"]) $(id).hidden = true;
}

// ---------------------------------------------------------------- agents

function renderAgents() {
  const select = $("agent");
  select.replaceChildren(...state.agents.map((a) => el("option", { value: a.key, text: a.key })));
  selectAgent(state.agents[0] && state.agents[0].key);
}

function selectAgent(key) {
  state.agent = state.agents.find((a) => a.key === key) || null;
  state.conversationId = null;
  $("continue").checked = false;
  $("conv-id").textContent = "";
  if (!state.agent) return;
  $("agent-desc").textContent = state.agent.description;
  renderWorkflow($("workflow-plan"), state.agent.workflow, null);
  $("examples").replaceChildren(
    ...state.agent.examples.map((text) => {
      const chip = el("button", { class: "chip", type: "button", text });
      chip.addEventListener("click", () => { $("message").value = text; updateCount(); $("message").focus(); });
      return chip;
    })
  );
  $("run-regression").disabled = !state.agent.regression_cases;
  $("reg-summary").textContent = state.agent.regression_cases ? state.agent.regression_cases + " cases" : "no cases";
  $("reg-summary").className = "badge";
}

function renderWorkflow(container, nodes, steps) {
  const ran = new Map((steps || []).map((s) => [s.node, s.duration_ms]));
  const parts = [];
  nodes.forEach((name, i) => {
    if (i) parts.push(el("span", { class: "arrow", text: "→" }));
    let cls = "node";
    if (steps) cls += ran.has(name) ? " ran" : " skipped";
    const node = el("div", { class: cls }, name);
    if (steps) node.append(el("span", { class: "t", text: ran.has(name) ? ran.get(name).toFixed(2) + " ms" : "skipped" }));
    parts.push(node);
  });
  container.replaceChildren(...parts);
}

// ---------------------------------------------------------------- invoke

function updateCount() {
  const n = $("message").value.length;
  $("char-count").textContent = n + " character" + (n === 1 ? "" : "s");
}

async function invoke() {
  const message = $("message").value.trim();
  if (!message) { setMessage("run-msg", "Enter a question.", "error"); return; }
  const body = { message };
  if ($("continue").checked && state.conversationId) body.conversation_id = state.conversationId;
  $("invoke").disabled = true;
  setMessage("run-msg", "Running " + state.agent.key + "…");
  const started = performance.now();
  try {
    const result = await api("POST", "/v1/agents/" + encodeURIComponent(state.agent.key) + "/invoke", body);
    const roundTrip = performance.now() - started;
    state.conversationId = result.conversation_id;
    $("conv-id").textContent = result.conversation_id.slice(0, 8) + "…";
    setMessage("run-msg", "Completed in " + roundTrip.toFixed(0) + " ms (server " + result.execution.duration_ms.toFixed(1) + " ms).", "ok");
    renderResult(result);
    addHistory(message, result);
  } catch (err) {
    setMessage("run-msg", describeError(err), "error");
  } finally {
    $("invoke").disabled = false;
  }
}

function fact(dl, label, value) {
  dl.append(el("dt", { text: label }), el("dd", { class: "mono", text: value == null ? "—" : String(value) }));
}

function renderResult(result) {
  const out = result.output;
  const exec = result.execution;
  $("result").hidden = false;

  const badge = $("decision");
  badge.textContent = (out.decision || exec.status).replaceAll("_", " ");
  badge.className = "badge " + (out.decision || "");
  $("explanation").textContent = out.explanation || "";

  const facts = $("facts");
  facts.replaceChildren();
  fact(facts, "Supplier", out.supplier_id ? out.supplier_id + " · " + out.supplier_name : null);
  fact(facts, "Evaluated as of", out.as_of);
  fact(facts, "Conversation", result.conversation_id);

  renderWorkflow($("workflow-run"), state.agent.workflow, exec.steps);

  const supporting = $("supporting").tBodies[0];
  supporting.replaceChildren(
    ...(out.supporting_evidence || []).map((e) =>
      el("tr", {}, el("td", { text: e.check }), el("td", {}, el("span", { class: "badge " + (e.outcome === "SATISFIED" ? "pass" : "fail"), text: e.outcome })), el("td", { text: e.detail }), el("td", { class: "mono", text: e.source }))
    )
  );
  if (!supporting.rows.length) supporting.append(el("tr", {}, el("td", { colspan: "4", class: "muted", text: "None found." })));

  const missing = $("missing");
  const items = (out.missing_evidence || []).map((m) => el("li", {}, el("strong", { text: m.check }), " — ", m.reason));
  missing.replaceChildren(...(items.length ? items : [el("li", { class: "none", text: "Nothing missing." })]));

  const ex = $("execution");
  ex.replaceChildren();
  fact(ex, "Status", exec.status);
  fact(ex, "Execution id", exec.execution_id);
  fact(ex, "Request id", exec.request_id);
  fact(ex, "Agent", exec.agent);
  fact(ex, "Caller pseudonym", exec.subject_hash);
  fact(ex, "Server duration", exec.duration_ms.toFixed(2) + " ms");
  fact(ex, "Steps", exec.steps.map((s) => s.node).join(" → "));

  const tools = $("tools").tBodies[0];
  tools.replaceChildren(
    ...exec.tools_invoked.map((t) =>
      el("tr", {}, el("td", { text: t.tool }), el("td", {}, el("span", { class: "badge " + (t.status === "OK" ? "pass" : "fail"), text: t.status })), el("td", { text: t.duration_ms.toFixed(3) }), el("td", { class: "mono", text: t.error_class || "—" }))
    )
  );
  if (!tools.rows.length) tools.append(el("tr", {}, el("td", { colspan: "4", class: "muted", text: "No tools were called on this path." })));

  $("raw").textContent = JSON.stringify(result, null, 2);
}

function addHistory(message, result) {
  state.history.unshift({
    at: new Date().toISOString(),
    agent: state.agent.key,
    message,
    decision: result.output.decision,
    execution: result.execution,
    conversation_id: result.conversation_id,
  });
  $("history").hidden = false;
  $("history-count").textContent = state.history.length + " run" + (state.history.length === 1 ? "" : "s");
  $("history-table").tBodies[0].replaceChildren(
    ...state.history.map((h) =>
      el("tr", {}, el("td", { class: "mono", text: h.at.slice(11, 19) }), el("td", { text: h.message }), el("td", {}, el("span", { class: "badge " + h.decision, text: h.decision.replaceAll("_", " ") })), el("td", { text: h.execution.steps.map((s) => s.node).join(" → ") }), el("td", { class: "mono", text: h.execution.execution_id.slice(0, 12) + "…" }))
    )
  );
  $("download").disabled = false;
}

// ---------------------------------------------------------------- regression

function short(value) {
  return Object.entries(value).map(([k, v]) => k + "=" + (Array.isArray(v) ? "[" + v.join(", ") + "]" : v)).join("\n");
}

async function runRegression() {
  $("run-regression").disabled = true;
  setMessage("reg-msg", "Running " + state.agent.regression_cases + " cases against the live service…");
  try {
    const report = await api("POST", "/v1/agents/" + encodeURIComponent(state.agent.key) + "/regression");
    state.lastRegression = report;
    const ok = report.failed === 0;
    $("reg-summary").textContent = report.passed + " / " + report.total + " passed";
    $("reg-summary").className = "badge " + (ok ? "pass" : "fail");
    setMessage("reg-msg", ok ? "All cases passed. Request " + report.request_id + "." : report.failed + " case(s) failed.", ok ? "ok" : "error");
    const table = $("reg-table");
    table.hidden = false;
    table.tBodies[0].replaceChildren(
      ...report.cases.map((c) =>
        el("tr", {}, el("td", {}, el("span", { class: "badge " + (c.passed ? "pass" : "fail"), text: c.passed ? "PASS" : "FAIL" })), el("td", { text: c.name }), el("td", { text: c.message }), el("td", { class: "mono", text: short(c.expected) }), el("td", { class: "mono", text: c.error ? "error: " + c.error : short(c.actual) }), el("td", { class: "mono", text: c.execution_id ? c.execution_id.slice(0, 8) + "…" : "—" }), el("td", { class: "mono", text: c.duration_ms.toFixed(1) }))
      )
    );
    $("download").disabled = false;
  } catch (err) {
    setMessage("reg-msg", describeError(err), "error");
  } finally {
    $("run-regression").disabled = false;
  }
}

function downloadEvidence() {
  const evidence = {
    kind: "iat-console-evidence",
    generated_at: new Date().toISOString(),
    service_version: state.version,
    origin: location.origin,
    agent: state.agent && state.agent.key,
    regression: state.lastRegression,
    runs: state.history,
  };
  const blob = new Blob([JSON.stringify(evidence, null, 2)], { type: "application/json" });
  const link = el("a", { href: URL.createObjectURL(blob), download: "iat-evidence-" + evidence.generated_at.replace(/[:.]/g, "-") + ".json" });
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(link.href);
}

// ---------------------------------------------------------------- wire up

document.addEventListener("DOMContentLoaded", () => {
  $("connect").addEventListener("click", connect);
  $("disconnect").addEventListener("click", disconnect);
  $("token").addEventListener("keydown", (e) => { if (e.key === "Enter") connect(); });
  $("agent").addEventListener("change", (e) => selectAgent(e.target.value));
  $("message").addEventListener("input", updateCount);
  $("message").addEventListener("keydown", (e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) invoke(); });
  $("invoke").addEventListener("click", invoke);
  $("run-regression").addEventListener("click", runRegression);
  $("download").addEventListener("click", downloadEvidence);
  $("continue").addEventListener("change", (e) => { if (e.target.checked && !state.conversationId) setMessage("run-msg", "Run once first; the next run will continue that conversation."); });
  checkHealth();
  const saved = load("iat-token");
  if (saved) { $("token").value = saved; connect(); }
});
