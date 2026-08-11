"""Cross-platform contract of the shipped skill asset.

Two things are pinned here because they are stated in more than one place and
mean different things per platform:

- Invocation policy — manual-only everywhere. It lives in SKILL.md frontmatter
  (``disable-model-invocation`` — Claude Code, VS Code Copilot) and in the
  ``agents/openai.yaml`` sidecar (``policy.allow_implicit_invocation`` — Codex,
  which ignores the frontmatter key).
- ``allowed-tools`` — a restriction on Claude Code but a *pre-approval* list on
  GitHub Copilot, where listed tools skip the confirmation prompt. The value is
  safe today; the durable rail is that it can never grow a command-execution tool.
"""

from importlib.resources import files
from pathlib import Path

import pytest
import yaml

from socratic_method.installer import MANAGED_FILES


def _asset(rel: str) -> str:
    return files("socratic_method").joinpath(f"assets/{rel}").read_text(encoding="utf-8")


def _frontmatter() -> dict:
    text = _asset("SKILL.md")
    assert text.startswith("---\n")
    return yaml.safe_load(text.split("\n---", 1)[0].removeprefix("---\n"))


def test_skill_frontmatter_disables_model_invocation():
    assert _frontmatter()["disable-model-invocation"] is True


def test_skill_frontmatter_stays_user_invocable():
    # VS Code Copilot pairs disable-model-invocation with user-invocable (default
    # true). Stating it explicitly keeps the 2x2 on "on-demand only" rather than
    # relying on a default; flipping it to false would disable the skill outright.
    assert _frontmatter()["user-invocable"] is True


# Names any of the three platforms could resolve to running a command. Copilot's
# own docs warn that pre-approving these lets a prompt injection execute anything.
_COMMAND_EXECUTION_TOOLS = frozenset(
    {"shell", "bash", "sh", "zsh", "powershell", "pwsh", "terminal", "run", "execute"}
)


def test_allowed_tools_never_pre_approves_command_execution():
    raw = _frontmatter().get("allowed-tools", "")
    listed = raw if isinstance(raw, list) else raw.split(",")
    names = {t.strip().casefold() for t in listed if t.strip()}
    offenders = names & _COMMAND_EXECUTION_TOOLS
    assert not offenders, (
        f"allowed-tools pre-approves command execution on GitHub Copilot: {sorted(offenders)}"
    )


@pytest.mark.parametrize("tool", ["Read", "Write"])
def test_allowed_tools_keeps_the_tools_the_skill_actually_needs(tool):
    # Phase 4 writes the brief and reads it back; losing either would break the
    # read-back-before-claiming-saved rail on Claude Code, where the list restricts.
    assert tool in _frontmatter()["allowed-tools"]


def test_codex_sidecar_disables_implicit_invocation():
    sidecar = yaml.safe_load(_asset("agents/openai.yaml"))
    assert sidecar["policy"]["allow_implicit_invocation"] is False


def test_codex_sidecar_carries_a_human_facing_interface():
    # With implicit invocation off, the /skills picker is the only way a Codex user
    # finds this skill, so it must not fall back to the model-facing description.
    interface = yaml.safe_load(_asset("agents/openai.yaml"))["interface"]
    assert interface["display_name"]
    assert interface["default_prompt"]
    short, long = interface["short_description"], _frontmatter()["description"]
    assert len(short) < len(long) / 3, "short_description is not meaningfully shorter"


def test_codex_sidecar_is_a_managed_file():
    # The sidecar must ship with every install, or Codex installs lose the policy.
    assert "agents/openai.yaml" in MANAGED_FILES


def test_example_session_embeds_golden_fixture():
    # SKILL.md tells the model to consult example-session.md before writing its first
    # brief; its worked deliverable duplicates the golden eval fixture verbatim. The two
    # are hand-maintained separately, so pin them together to catch silent drift.
    example = _asset("references/example-session.md")
    fixture = (
        Path(__file__).parent.parent / "evals" / "fixtures" / "tech-talk-series-20260704.md"
    ).read_text(encoding="utf-8")
    assert fixture.strip() in example
