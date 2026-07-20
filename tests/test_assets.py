"""Invocation policy of the shipped skill: manual-only on every platform.

The policy intentionally lives in two places that must stay in sync:
SKILL.md frontmatter (``disable-model-invocation`` — Claude Code, Copilot) and
the ``agents/openai.yaml`` sidecar (``policy.allow_implicit_invocation`` — Codex,
which ignores the frontmatter key).
"""

from importlib.resources import files
from pathlib import Path

import yaml

from socratic_method.installer import MANAGED_FILES


def _asset(rel: str) -> str:
    return files("socratic_method").joinpath(f"assets/{rel}").read_text(encoding="utf-8")


def test_skill_frontmatter_disables_model_invocation():
    text = _asset("SKILL.md")
    assert text.startswith("---\n")
    frontmatter = yaml.safe_load(text.split("\n---", 1)[0].removeprefix("---\n"))
    assert frontmatter["disable-model-invocation"] is True


def test_codex_sidecar_disables_implicit_invocation():
    sidecar = yaml.safe_load(_asset("agents/openai.yaml"))
    assert sidecar["policy"]["allow_implicit_invocation"] is False


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
