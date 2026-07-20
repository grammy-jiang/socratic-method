"""Autonomous behavioral eval runner for the socratic-method skill.

Run from the repo root (needs the claude CLI): python evals/run_eval.py --dry-run

For each scenario cell it runs a live examiner (headless ``claude -p`` session with the
skill installed in an isolated workdir) against a scripted user-simulator (stateless
one-shot ``claude -p`` calls), then grades the transcript with deterministic graders
(graders.py) and one independent model judge (judge-rubric.md).

Roles are separated on purpose: examiner (generator), simulator (environment), graders
(computational sensors), judge (inferential sensor). The examiner never grades itself.

Usage (from the repo root):
    uv run python evals/run_eval.py --dry-run
    uv run python evals/run_eval.py --cell O1 --cell E2
    uv run python evals/run_eval.py            # full 6-cell matrix

Cost warning: a full matrix run spawns ~30-60 headless claude calls. Reports land in
evals/reports/<timestamp>/ (transcripts, grader + judge verdicts,
summary.md) — keep them: they are the evidence trail and seed future grader tuning.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

EVAL_DIR = Path(__file__).resolve().parent
REPO_ROOT = EVAL_DIR.parent
SKILL_DIR = REPO_ROOT / "src" / "socratic_method" / "assets"
sys.path.insert(0, str(EVAL_DIR))
sys.path.insert(0, str(REPO_ROOT / "src"))

from graders import run_graders  # noqa: E402

EXAMINER_TIMEOUT = 900
SIM_TIMEOUT = 300
JUDGE_TIMEOUT = 600

SIM_PROMPT_TMPL = """{persona}

Conversation so far (you are the "user"; the "examiner" is questioning you):

{dialogue}

The examiner's latest message is the last one above. Reply as the user, in character,
per your briefing. Output ONLY the user's reply text — no quotes, no role labels,
no commentary."""

JUDGE_PROMPT_TMPL = """{rubric}

## Scenario expectation

{judge_focus}

## Transcript

{dialogue}

## Brief written by the examiner (empty if none)

{brief}
"""


def _now_stamp() -> str:
    return _dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def load_scenarios(cells: list[str] | None) -> list[dict]:
    scenarios = []
    for f in sorted((EVAL_DIR / "scenarios").glob("*.yaml")):
        s = yaml.safe_load(f.read_text(encoding="utf-8"))
        s["_file"] = f.name
        if cells is None or s["cell"] in cells:
            scenarios.append(s)
    return scenarios


def _run(cmd: list[str], *, cwd: Path, timeout: int) -> str:
    # subprocess(cwd=...) does NOT update $PWD; a stale PWD pointing at the repo root
    # is how one examiner run wrote its brief outside the sandbox workdir.
    env = {**os.environ, "PWD": str(cwd), "OLDPWD": str(cwd)}
    proc = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed (rc={proc.returncode}): {' '.join(cmd[:4])}...\n"
            f"stderr tail: {proc.stderr[-800:]}"
        )
    return proc.stdout


def _parse_stream_json(stdout: str) -> tuple[str | None, str, bool]:
    """Return (session_id, final_result_text, is_error) from a claude -p stream-json run."""
    session_id, result_text, is_error = None, "", False
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            evt = json.loads(line)
        except json.JSONDecodeError:
            continue
        if evt.get("type") == "system" and evt.get("subtype") == "init":
            session_id = evt.get("session_id") or session_id
        elif evt.get("type") == "result":
            result_text = evt.get("result") or result_text
            session_id = evt.get("session_id") or session_id
            # result events carry is_error, or a subtype like "error_max_turns".
            is_error = bool(evt.get("is_error")) or str(evt.get("subtype") or "").startswith(
                "error"
            )
    return session_id, result_text, is_error


def examiner_call(
    workdir: Path, model: str, prompt: str, session_id: str | None
) -> tuple[str | None, str, bool]:
    cmd = ["claude", "-p"]
    if session_id:
        cmd += ["--resume", session_id]
    cmd += [
        "--model",
        model,
        # Minimal grant instead of --dangerously-skip-permissions: exactly the tool
        # surface the skill declares (plus Skill to invoke it). Also avoids the CLI's
        # root-user refusal of the blanket bypass.
        "--allowedTools",
        "Skill,Read,Write,Edit",
        "--output-format",
        "stream-json",
        "--verbose",
        prompt,
    ]
    return _parse_stream_json(_run(cmd, cwd=workdir, timeout=EXAMINER_TIMEOUT))


def one_shot(model: str, prompt: str, cwd: Path, timeout: int) -> str:
    cmd = ["claude", "-p", "--model", model, prompt]
    return _run(cmd, cwd=cwd, timeout=timeout).strip()


def _dialogue_text(transcript: list[dict]) -> str:
    return "\n\n".join(f"[{m['role']} — turn {m['turn']}]\n{m['text']}" for m in transcript)


def _find_brief(workdir: Path) -> Path | None:
    briefs = (
        sorted((workdir / "notes" / "idea-briefs").glob("*.md"))
        if (workdir / "notes" / "idea-briefs").is_dir()
        else []
    )
    return briefs[-1] if briefs else None


def _find_leaked_brief(run_started: float, scenario: dict) -> Path | None:
    """Detect a brief the examiner wrote OUTSIDE its sandbox (repo-root notes/) — a
    harness leak that must be reported as such, never as 'no brief written'. Correlate a
    candidate to THIS scenario (a token from its invocation must appear in the file), so a
    concurrent, unrelated real-skill brief in notes/ is not mis-attributed to this cell."""
    leak_dir = REPO_ROOT / "notes" / "idea-briefs"
    if not leak_dir.is_dir():
        return None
    fresh = [p for p in leak_dir.glob("*.md") if p.stat().st_mtime >= run_started]
    if not fresh:
        return None
    tokens = {t.lower() for t in re.findall(r"[A-Za-z]{4,}", scenario.get("invocation", ""))}

    def related(p: Path) -> bool:
        try:
            return (
                any(t in p.read_text(encoding="utf-8").lower() for t in tokens) if tokens else True
            )
        except OSError:
            return False

    related_files = [p for p in fresh if related(p)]
    if not related_files:
        return None  # fresh files exist but none match this cell — don't mis-attribute
    return sorted(related_files, key=lambda p: p.stat().st_mtime)[-1]


def run_cell(scenario: dict, args, report_dir: Path) -> dict:
    cell = scenario["cell"]
    cell_dir = report_dir / cell
    workdir = cell_dir / "workdir"
    (workdir / ".claude" / "skills").mkdir(parents=True)
    shutil.copytree(SKILL_DIR, workdir / ".claude" / "skills" / "socratic-method")

    transcript: list[dict] = []
    session_id: str | None = None
    prompt = scenario["invocation"].strip()
    quiet_examiner_turns = 0
    run_started = _dt.datetime.now().timestamp()

    def _persist_transcript() -> None:
        # Persist after every turn so a mid-cell failure (rate limit, timeout) still
        # leaves the dialogue-so-far on disk — the evidence trail this run exists for.
        (cell_dir / "transcript.json").write_text(
            json.dumps(transcript, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    for turn in range(1, int(scenario.get("max_turns", 16)) + 1):
        session_id, examiner_text, examiner_error = examiner_call(
            workdir, args.model, prompt, session_id
        )
        transcript.append({"role": "examiner", "turn": turn, "text": examiner_text})
        _persist_transcript()
        print(f"  [{cell}] examiner turn {turn} ({len(examiner_text)} chars)")

        # A turn that errored, or lost its session so the next --resume would silently
        # start a NEW conversation, breaks the dialogue premise — stop and grade what we
        # have rather than append to a thread the examiner no longer remembers.
        if examiner_error or (turn > 1 and session_id is None):
            transcript[-1]["session_error"] = True
            print(
                f"  [{cell}] WARNING: examiner turn {turn} errored or lost its session — stopping"
            )
            break

        if _find_brief(workdir) is not None:
            break
        if "?" not in re.sub(r"```.*?```", "", examiner_text, flags=re.DOTALL):
            quiet_examiner_turns += 1
            if quiet_examiner_turns >= 2:
                break  # two question-less examiner turns: dialogue has ended without a brief
        else:
            quiet_examiner_turns = 0

        sim_prompt = SIM_PROMPT_TMPL.format(
            persona=scenario["persona"].strip(), dialogue=_dialogue_text(transcript)
        )
        user_text = one_shot(args.sim_model, sim_prompt, cwd=cell_dir, timeout=SIM_TIMEOUT)
        transcript.append({"role": "user", "turn": turn, "text": user_text})
        _persist_transcript()
        prompt = user_text

    brief_path = _find_brief(workdir)
    harness_leak = False
    if brief_path is None:
        leaked = _find_leaked_brief(run_started, scenario)
        if leaked is not None:
            harness_leak = True
            print(f"  [{cell}] HARNESS LEAK: brief written outside sandbox: {leaked}")
            brief_path = Path(shutil.move(str(leaked), cell_dir / "brief-leaked.md"))
    grader_results = run_graders(transcript, brief_path, scenario)

    judge_prompt = JUDGE_PROMPT_TMPL.format(
        rubric=(EVAL_DIR / "judge-rubric.md").read_text(encoding="utf-8"),
        judge_focus=scenario["expected"].get("judge_focus", "").strip(),
        dialogue=_dialogue_text(transcript),
        brief=brief_path.read_text(encoding="utf-8") if brief_path else "(no brief written)",
    )
    judge_raw = one_shot(args.judge_model, judge_prompt, cwd=cell_dir, timeout=JUDGE_TIMEOUT)
    try:
        judge = json.loads(re.sub(r"^```(json)?|```$", "", judge_raw.strip(), flags=re.MULTILINE))
    except json.JSONDecodeError:
        judge = {"parse_error": True, "raw": judge_raw[-2000:]}

    # harness_leak is a deterministic sandbox-boundary defect — it hard-fails the cell.
    # premature_solutioning is a NEW judge-based backstop for the skill's #1 guardrail
    # (the literal-marker grader misses paraphrases). It is kept REPORT-ONLY (surfaced in
    # the result/summary below, not gating `passed`) until a real matrix run confirms it
    # doesn't misfire on O1's legitimate "record as-is" decline. Promote it to a hard gate
    # by adding `and not judge.get("premature_solutioning", True)` here once validated.
    passed = (
        all(g["passed"] for g in grader_results)
        and judge.get("expected_behavior_met", False)
        and not judge.get("fabrication", True)
        and not harness_leak
    )

    _persist_transcript()
    (cell_dir / "graders.json").write_text(
        json.dumps(grader_results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (cell_dir / "judge.json").write_text(
        json.dumps(judge, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    if brief_path:
        shutil.copy2(brief_path, cell_dir / "brief.md")

    return {
        "cell": cell,
        "name": scenario["name"],
        "passed": passed,
        "harness_leak": harness_leak,
        # Report-only (not folded into `passed` yet — see the passed computation above).
        "judge_premature_solutioning": judge.get("premature_solutioning"),
        "graders": {g["grader"]: g["passed"] for g in grader_results},
        "judge_expected_behavior_met": judge.get("expected_behavior_met"),
        "judge_scores": {
            k: judge.get(k)
            for k in ("information_gain", "adaptivity", "type_diversity", "tone", "honest_verdict")
        },
        "turns": len([m for m in transcript if m["role"] == "examiner"]),
        "brief": str(brief_path.name) if brief_path else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cell", action="append", help="run only this cell (repeatable)")
    ap.add_argument("--model", default="sonnet", help="examiner model (default: sonnet)")
    ap.add_argument("--sim-model", default="sonnet", help="user-simulator model")
    ap.add_argument("--judge-model", default="opus", help="judge model (default: opus)")
    ap.add_argument("--dry-run", action="store_true", help="list planned cells, no calls")
    args = ap.parse_args()

    scenarios = load_scenarios(args.cell)
    if not scenarios:
        print(f"No scenarios matched cells={args.cell}")
        return 1

    if args.dry_run:
        for s in scenarios:
            print(
                f"{s['cell']:3} {s['name']:32} mode={s['mode']:7} depth={s['depth']:8} "
                f"graders={s['expected']['graders']}"
            )
        print(f"\nexaminer={args.model} sim={args.sim_model} judge={args.judge_model}")
        return 0

    report_dir = EVAL_DIR / "reports" / _now_stamp()
    report_dir.mkdir(parents=True)
    results = []
    for s in scenarios:
        print(f"[{s['cell']}] {s['name']} ...")
        try:
            results.append(run_cell(s, args, report_dir))
        except (RuntimeError, subprocess.TimeoutExpired) as e:
            results.append({"cell": s["cell"], "name": s["name"], "passed": False, "error": str(e)})
        print(f"[{s['cell']}] {'PASS' if results[-1].get('passed') else 'FAIL'}")

    summary_lines = [
        "# socratic-method eval run",
        "",
        f"examiner={args.model} sim={args.sim_model} judge={args.judge_model}",
        "",
        "| cell | name | result | leak | solu? | graders | judge ebm |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in results:
        graders = ", ".join(f"{k}={'P' if v else 'F'}" for k, v in r.get("graders", {}).items())
        leak = "LEAK" if r.get("harness_leak") else ""
        # Report-only judge signal: flag it for review, but it does not fail the cell yet.
        solu = "SOLU?" if r.get("judge_premature_solutioning") else ""
        summary_lines.append(
            f"| {r['cell']} | {r['name']} | {'PASS' if r.get('passed') else 'FAIL'} "
            f"| {leak} | {solu} | {graders or r.get('error', '')} | "
            f"{r.get('judge_expected_behavior_met')} |"
        )
    (report_dir / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    (report_dir / "summary.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nReports: {report_dir}")
    n_pass = sum(1 for r in results if r.get("passed"))
    print(f"{n_pass}/{len(results)} cells passed")
    return 0 if n_pass == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
