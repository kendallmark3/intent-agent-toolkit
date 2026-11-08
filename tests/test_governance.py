"""INTENT-002 finding D: agent listing scope, local intent gate, and project intent."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from iat.security.identity import SCOPE_INVOKE, SCOPE_READ_CONVERSATIONS
from tests.conftest import TokenFactory

ROOT = Path(__file__).resolve().parent.parent


def test_listing_agents_requires_invoke_scope(client: TestClient, make_token: TokenFactory) -> None:
    read_only = make_token("alice", scopes=SCOPE_READ_CONVERSATIONS)
    invoker = make_token("alice", scopes=SCOPE_INVOKE)
    denied = client.get("/v1/agents", headers={"Authorization": f"Bearer {read_only}"})
    allowed = client.get("/v1/agents", headers={"Authorization": f"Bearer {invoker}"})
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "FORBIDDEN"
    assert allowed.status_code == 200


def _hook_command() -> str:
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text())
    (entry,) = settings["hooks"]["PreToolUse"]
    assert {"Edit", "Write"} <= set(entry["matcher"].split("|"))
    (hook,) = entry["hooks"]
    assert hook["type"] == "command"
    return str(hook["command"])


def _run_hook(project: Path, target: str) -> int:
    payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": target}})
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project)}
    bash = shutil.which("bash")
    assert bash is not None
    result = subprocess.run(  # noqa: S603 - fixed command from the repo's own settings file
        [bash, "-c", _hook_command()], input=payload, env=env, capture_output=True, text=True
    )
    return result.returncode


def test_project_hook_is_wired_for_local_sessions() -> None:
    command = _hook_command()
    assert "$CLAUDE_PROJECT_DIR/hooks/pre-implement-hook.sh" in command
    assert "CLAUDE_PLUGIN_ROOT" not in command
    assert (ROOT / "hooks" / "pre-implement-hook.sh").is_file()


def test_hook_allows_code_edits_with_current_intent() -> None:
    assert _run_hook(ROOT, str(ROOT / "src" / "iat" / "main.py")) == 0


def test_hook_blocks_code_edits_when_intent_is_blank(tmp_path: Path) -> None:
    shutil.copytree(ROOT / "hooks", tmp_path / "hooks")
    shutil.copytree(ROOT / ".claude", tmp_path / ".claude")
    (tmp_path / "intent").mkdir()
    shutil.copy(
        ROOT / "templates" / "feature-template.md", tmp_path / "intent" / "current-feature.md"
    )
    assert _run_hook(tmp_path, str(tmp_path / "src" / "app.py")) == 2
    # Markdown is never blocked, so the intent itself can always be written.
    assert _run_hook(tmp_path, str(tmp_path / "intent" / "current-feature.md")) == 0


def test_plugin_only_hook_config_is_gone() -> None:
    assert not (ROOT / "hooks" / "hooks.json").exists()


@pytest.mark.parametrize("section", ["Purpose:", "Business outcomes:", "Constraints:"])
def test_project_intent_sections_are_filled(section: str) -> None:
    text = (ROOT / "intent" / "project-intent.md").read_text()
    after = text.split(section, 1)[1].split("\n\n", 1)[0].strip()
    assert after, f"{section} is empty"
