"""Cross-platform smoke tier: is the skill discoverable, and does it stay manual-only?

``run_eval.py`` is the behavioral matrix, and it is Claude-Code-only by construction —
it drives ``claude -p``, parses Claude's stream-json, and installs into ``.claude/skills``.
That leaves the two *platform contract* properties this package actually claims for Codex
and Copilot untested:

1. **Discovery** — the agent finds ``SKILL.md`` at the directory this installer writes to.
   Breaks when a vendor moves its skills path. Deterministic; cheap to check.
2. **Manual-only** — a prompt that matches the skill's description must NOT auto-invoke it.
   This is the property with the weakest cross-platform support (see the invocation table
   in the README), so it is the one most worth watching.

This tier deliberately does NOT grade questioning behavior — no one-question-per-turn, no
stop-signal, no verdict honesty. Those need a scripted multi-turn simulator and stay in
``run_eval.py``. A green smoke run means "the skill is wired up correctly on this
platform", never "the skill behaves correctly on this platform".

Usage (from the repo root):
    uv run python evals/run_smoke.py --dry-run
    uv run python evals/run_smoke.py --platform codex
    uv run python evals/run_smoke.py                  # every detected platform

Cost: 2 headless calls per platform. Needs the platform's CLI on PATH and authenticated.
Like the rest of evals/, this must never run in CI — real tokens, real model variance.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
REPO_ROOT = EVAL_DIR.parent
SKILL_DIR = REPO_ROOT / "src" / "socratic_method" / "assets"
sys.path.insert(0, str(REPO_ROOT / "src"))

from socratic_method import SKILL_NAME  # noqa: E402
from socratic_method.installer import PLATFORMS  # noqa: E402

PROBE_TIMEOUT = 420

# Probe 1. Invokes the skill the way a user would on this platform, then asks which
# file was actually loaded. Asking "is it in your skill list" does NOT work: manual-only
# skills are deliberately kept out of that list (that is what the policy does on Codex),
# so a list probe reports "not available" for a perfectly good install. Reading back the
# loaded path is also the stronger check — it proves the file at *our* install path is
# the one that ran, not some other copy on the machine.
DISCOVERY_PROMPT_TMPL = """{invoke}

Before asking me anything, and before writing any file, reply with exactly one line of
JSON and nothing else:
{{"loaded": true|false, "path": "<absolute path of the SKILL.md you just loaded>"}}
If no such skill was available, answer with loaded=false and an empty path. Do not guess."""

# Probe 2. Lifted from the skill's own description triggers ("help me think through",
# a fuzzy idea plus "what should I do"). If manual-only holds, the agent answers as
# itself; if it does not, the skill takes over and the sandbox gets a brief.
BAIT_PROMPT = """Help me think through a fuzzy idea: I want to start a weekly tech talk
series at work but I am not sure it is worth it. Poke holes in this — what am I missing
here? Answer in at most three sentences."""

# Phrases that only appear when the skill body is actually driving the reply.
_SKILL_MARKERS = (
    "idea brief",
    "idea-brief-v1",
    "elenchus",
    "aporia",
    "state the idea in one or two sentences",
)


@dataclass(frozen=True)
class Runner:
    """How to drive one platform headlessly, and where it reads project skills."""

    key: str
    cli: str
    argv: tuple[str, ...]  # command template; "{prompt}" is substituted
    invoke: str  # how a user names the skill explicitly on this platform

    def command(self, prompt: str, workdir: Path) -> list[str]:
        return [a.format(prompt=prompt, workdir=workdir) for a in self.argv]


RUNNERS: dict[str, Runner] = {
    "claude": Runner(
        key="claude",
        cli="claude",
        # Same tool grant shape as run_eval.py's examiner, minus Edit: these probes
        # must be able to load a skill and read files, nothing more.
        argv=("claude", "-p", "{prompt}", "--allowedTools", "Skill,Read"),
        invoke=f"/{SKILL_NAME}",
    ),
    "codex": Runner(
        key="codex",
        cli="codex",
        # --skip-git-repo-check keeps the runner honest if the sandbox is ever not a
        # repo; _install() git-inits it, because Codex's documented REPO scopes are
        # relative to a repository root and users run agents inside repos.
        argv=("codex", "exec", "--skip-git-repo-check", "-s", "read-only", "{prompt}"),
        invoke=f"${SKILL_NAME}",
    ),
    "copilot": Runner(
        key="copilot",
        cli="copilot",
        # --allow-all-tools is required for non-interactive mode per `copilot --help`.
        argv=("copilot", "-p", "{prompt}", "--allow-all-tools", "--no-color"),
        invoke=f"Use the /{SKILL_NAME} skill.",
    ),
}


# A run that never reached the model must not be graded. Without this, a spend-limit or
# auth failure makes the manual-only probe "pass" — nothing was invoked because nothing
# ran at all. That is the fabrication mode this whole project exists to prevent.
_CLI_FAILURE_MARKERS = (
    "spend limit",
    "usage limit",
    "rate limit",
    "quota",
    "not logged in",
    "please log in",
    "authentication",
    "unauthorized",
    "invalid api key",
)


def _run(cmd: list[str], cwd: Path) -> tuple[str, bool]:
    """Run one headless probe. Returns (output, reached_the_model)."""
    # subprocess(cwd=...) does not update $PWD; a stale PWD is how an agent ends up
    # writing outside its sandbox (learned the hard way in run_eval.py).
    env = {**os.environ, "PWD": str(cwd), "OLDPWD": str(cwd)}
    proc = subprocess.run(
        cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=PROBE_TIMEOUT
    )
    out = proc.stdout + ("\n" + proc.stderr if proc.stderr else "")
    healthy = (
        proc.returncode == 0
        and bool(out.strip())
        and not any(m in out.casefold() for m in _CLI_FAILURE_MARKERS)
    )
    return out, healthy


def _install(platform_key: str, workdir: Path) -> Path:
    """Copy the *working tree* assets into the platform's project skills directory.

    Copies rather than using installer.install() on purpose: evals must test uncommitted
    edits, matching run_eval.py. The path still comes from the installer's registry, so a
    wrong path here is a real bug, not a test-only divergence.
    """
    target = workdir / PLATFORMS[platform_key].project_dir / SKILL_NAME
    shutil.copytree(SKILL_DIR, target)
    # Codex resolves its REPO skill scopes against a repository root, and every agent
    # is normally launched inside a repo. Make the sandbox one so discovery is not
    # measuring "bare temp directory" instead of "our install path".
    subprocess.run(["git", "init", "-q"], cwd=workdir, check=True, capture_output=True)
    return target


def _briefs(workdir: Path) -> list[Path]:
    return sorted(workdir.glob("notes/idea-briefs/*.md"))


def probe_discovery(runner: Runner, workdir: Path, target: Path) -> dict:
    prompt = DISCOVERY_PROMPT_TMPL.format(invoke=runner.invoke)
    out, healthy = _run(runner.command(prompt, workdir), workdir)
    if not healthy:
        return {"probe": "discovery", "status": "ERROR", "detail": _why(out), "output": out}
    reported = ""
    for line in out.splitlines():
        line = line.strip().strip("`")
        if line.startswith("{") and "loaded" in line:
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if payload.get("loaded"):
                reported = str(payload.get("path", ""))
            break
    # Accept only a path inside this sandbox: a machine-wide install of the same skill
    # would otherwise let a broken project path pass.
    passed = bool(reported) and str(target) in reported
    detail = f"loaded {reported}" if passed else f"expected {target}, agent reported {reported!r}"
    return {
        "probe": "discovery",
        "status": "PASS" if passed else "FAIL",
        "detail": detail,
        "output": out,
    }


def probe_manual_only(runner: Runner, workdir: Path) -> dict:
    before = set(_briefs(workdir))
    out, healthy = _run(runner.command(BAIT_PROMPT, workdir), workdir)
    if not healthy:
        return {"probe": "manual-only", "status": "ERROR", "detail": _why(out), "output": out}
    new_briefs = [p for p in _briefs(workdir) if p not in before]
    markers = [m for m in _SKILL_MARKERS if m in out.casefold()]
    detail = "no skill markers and no brief written"
    if new_briefs:
        detail = f"skill wrote {[p.name for p in new_briefs]} without being asked"
    elif markers:
        detail = f"reply carries skill markers {markers}"
    return {
        "probe": "manual-only",
        "status": "FAIL" if (new_briefs or markers) else "PASS",
        "detail": detail,
        "output": out,
    }


def _why(out: str) -> str:
    """Short reason a probe never reached the model, for the ERROR line."""
    lowered = out.casefold()
    for marker in _CLI_FAILURE_MARKERS:
        if marker in lowered:
            return f"CLI never reached the model ({marker}) — probe not graded"
    return "CLI failed or produced no output — probe not graded"


def smoke(platform_key: str, keep: bool) -> list[dict]:
    runner = RUNNERS[platform_key]
    workdir = Path(tempfile.mkdtemp(prefix=f"smoke-{platform_key}-"))
    try:
        target = _install(platform_key, workdir)
        return [probe_discovery(runner, workdir, target), probe_manual_only(runner, workdir)]
    finally:
        if keep:
            print(f"    workdir kept: {workdir}")
        else:
            shutil.rmtree(workdir, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument(
        "--platform",
        action="append",
        choices=sorted(RUNNERS),
        help="platform to smoke (repeatable; default: every one whose CLI is on PATH)",
    )
    p.add_argument("--dry-run", action="store_true", help="print the plan, call nothing")
    p.add_argument("--keep-workdir", action="store_true", help="do not delete the sandboxes")
    p.add_argument("--show-output", action="store_true", help="print each probe's raw output")
    args = p.parse_args(argv)

    keys = args.platform or [k for k, r in RUNNERS.items() if shutil.which(r.cli)]
    if not keys:
        print("No agent CLI found on PATH. Name one with --platform.")
        return 1

    print(f"smoke tier — discovery + manual-only, {len(keys) * 2} headless calls")
    for key in keys:
        print(f"  {key:8s} {RUNNERS[key].cli} -> {PLATFORMS[key].project_dir}/{SKILL_NAME}")
    if args.dry_run:
        return 0

    tally = {"PASS": 0, "FAIL": 0, "ERROR": 0}
    for key in keys:
        print(f"\n== {key}")
        for result in smoke(key, args.keep_workdir):
            status = result["status"]
            tally[status] += 1
            print(f"  [{status:5s}] {result['probe']:12s} {result['detail']}")
            if args.show_output or status != "PASS":
                body = result["output"].strip()
                print("    ---\n" + "\n".join(f"    {ln}" for ln in body.splitlines()[-25:]))
    print(f"\n{tally['PASS']} passed, {tally['FAIL']} failed, {tally['ERROR']} not graded")
    # ERROR is not a pass. An ungraded probe leaves the platform unverified, and
    # reporting that as success is exactly the fabrication the skill forbids.
    return 1 if tally["FAIL"] or tally["ERROR"] else 0


if __name__ == "__main__":
    sys.exit(main())
