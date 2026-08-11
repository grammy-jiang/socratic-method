"""Unit tests for the cross-platform smoke tier's pure logic (no model calls, no CLIs).

``run_smoke.py`` decides what counts as evidence about a platform, so its grading rules
carry the same risk the graders do: a silent regression turns "unverified" into "verified"
and nobody notices. Everything below runs offline — the probes themselves are the only
part that spends tokens, and they are never exercised here.
"""

from pathlib import Path

import pytest
import run_smoke  # importable because conftest.py puts evals/ on sys.path

from socratic_method import SKILL_NAME
from socratic_method.installer import PLATFORMS

WORKDIR = Path("/tmp/does-not-need-to-exist")


# --- command construction ---------------------------------------------------------


def test_every_runner_matches_a_known_platform():
    # The runner is what proves the installer's path is the one a real agent reads;
    # a runner for a platform the installer does not know would prove nothing.
    assert set(run_smoke.RUNNERS) == set(PLATFORMS)


def test_claude_command_pins_a_model_and_carries_the_prompt():
    # Left to the account default, the probe can die on a spend limit and report ERROR
    # for a perfectly healthy skill — measuring billing instead of the contract.
    cmd = run_smoke.RUNNERS["claude"].command("PROMPT", WORKDIR)
    assert cmd[0] == "claude"
    assert "PROMPT" in cmd
    assert cmd[-2:] == ["--model", "sonnet"]


def test_model_override_wins_over_the_default():
    cmd = run_smoke.RUNNERS["claude"].command("PROMPT", WORKDIR, "opus")
    assert cmd[-2:] == ["--model", "opus"]
    assert cmd.count("--model") == 1  # override replaces the default, never appends


def test_runner_without_a_default_model_passes_no_flag():
    cmd = run_smoke.RUNNERS["copilot"].command("PROMPT", WORKDIR)
    assert "--model" not in cmd


def test_codex_uses_its_own_model_flag():
    # One flag spelling does not fit three vendors; codex takes -m, not --model.
    cmd = run_smoke.RUNNERS["codex"].command("PROMPT", WORKDIR, "gpt-5.6")
    assert cmd[-2:] == ["-m", "gpt-5.6"]
    assert "--model" not in cmd


def test_each_runner_invokes_the_skill_by_its_real_name():
    for key, runner in run_smoke.RUNNERS.items():
        assert SKILL_NAME in runner.invoke, key


# Per-vendor flag that excludes the operator's own user configuration. Without it the
# tier measures the developer's machine — a terseness hook in ~/.claude/settings.json
# reshaped an examiner's questions badly enough to fail a calibrated grader.
_ISOLATION_FLAG = {
    "claude": "--setting-sources",
    "codex": "--ignore-user-config",
    "copilot": "--no-custom-instructions",
}


@pytest.mark.parametrize(("key", "flag"), sorted(_ISOLATION_FLAG.items()))
def test_every_runner_excludes_user_config(key, flag):
    assert flag in run_smoke.RUNNERS[key].command("PROMPT", WORKDIR)


def test_claude_isolation_drops_user_scope_only():
    cmd = run_smoke.RUNNERS["claude"].command("PROMPT", WORKDIR)
    sources = cmd[cmd.index("--setting-sources") + 1]
    assert "user" not in sources.split(",")  # user is where hooks and output styles live


# --- --model parsing --------------------------------------------------------------


def test_parse_model_overrides_reads_platform_pairs():
    assert run_smoke.parse_model_overrides(["claude=sonnet", "codex=gpt-5.6"]) == {
        "claude": "sonnet",
        "codex": "gpt-5.6",
    }


def test_parse_model_overrides_defaults_to_empty():
    assert run_smoke.parse_model_overrides(None) == {}


@pytest.mark.parametrize("bad", ["sonnet", "bogus=x", "claude="])
def test_parse_model_overrides_rejects_malformed_input(bad):
    # Crash early: a typo'd platform must not silently run the whole matrix on defaults.
    with pytest.raises(SystemExit, match="PLATFORM=NAME"):
        run_smoke.parse_model_overrides([bad])


# --- health gating ----------------------------------------------------------------


@pytest.mark.parametrize("marker", ["spend limit", "not logged in", "Unauthorized"])
def test_failure_markers_are_recognized_case_insensitively(marker):
    assert "not graded" in run_smoke._why(f"Error: you have hit your {marker} today")


def test_why_falls_back_when_no_marker_matches():
    assert "no output" in run_smoke._why("")


# --- known-breakage bookkeeping ---------------------------------------------------


def test_known_breakage_keys_name_real_platforms_and_probes():
    probes = {"discovery", "manual-only"}
    for platform, probe in run_smoke.KNOWN_BREAKAGE:
        assert platform in run_smoke.RUNNERS
        assert probe in probes


def test_known_breakage_reasons_link_upstream():
    # "Known" has to mean reported, not merely tolerated — otherwise the XFAIL is a
    # place to park a bug forever.
    for reason in run_smoke.KNOWN_BREAKAGE.values():
        assert "#" in reason, reason
