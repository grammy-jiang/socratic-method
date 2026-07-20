"""Deterministic graders for socratic-method eval transcripts.

Each grader takes ``(transcript, brief_path, scenario)`` and returns a dict:
``{"grader": name, "passed": bool, "detail": str}``.

Transcript format: list of ``{"role": "examiner"|"user", "turn": int, "text": str}``.

These are the *computational* sensors (cheap, unambiguous); the Opus judge covers the
inferential dimensions (question quality, adaptivity, tone). Design rule from issue
#51: the out-of-scope grader failed by being too lenient once — graders here prefer
hard counts over marker-sniffing wherever possible.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from socratic_method.validator import split_frontmatter, validate_idea_brief

_BRIEF_MARKER = "schema: idea-brief-v1"

# A synthesis (Phase 3/4) message: the examiner may print the brief in chat as prose
# rather than embedding the frontmatter, so detect any of the wrap-up signatures.
# Built from _BRIEF_MARKER so the marker string has a single source.
_SYNTHESIS_RE = re.compile(rf"{re.escape(_BRIEF_MARKER)}|notes/idea-briefs/|\*\*Verdict|\bVerdict:")

_SOLUTIONING_MARKERS = (
    "i'd suggest",
    "i suggest",
    "i recommend",
    "my recommendation",
    "you should ",
    "you could use",
    "have you considered using",
    "the solution is",
    "my advice",
)

_DECLINE_MARKERS = (
    "not for",
    "already specified",
    "already precisely",
    "doesn't need questioning",
    "does not need questioning",
    "record it as a brief",
    "record the plan as a brief",
    "record this as a brief",
    "as-is",
    "one specific aspect",
    "decline",
    "won't run the full",
    "no need to interrogate",
    "no elenchus",
    "without questioning",
)

_CONFIRMATION_MARKERS = re.compile(
    r"(is that (the |your |it|right|correct|accurate|exactly)|did i (get|capture|state)"
    r"|right\?|correct\?|accurate\?|exactly( it| right)?\?|that's it\?|confirm)",
    re.IGNORECASE,
)


def _strip_brief_and_fences(text: str) -> str:
    """Remove code fences and any embedded brief so '?' counting sees only dialogue."""
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    return text


def _question_count(text: str) -> int:
    return _strip_brief_and_fences(text).count("?")


def _examiner_msgs(transcript: list[dict]) -> list[dict]:
    return [m for m in transcript if m["role"] == "examiner"]


def _pre_synthesis_examiner_msgs(transcript: list[dict]) -> list[dict]:
    """Examiner messages before (and excluding) the verdict/brief wrap-up."""
    out = []
    for m in _examiner_msgs(transcript):
        if _SYNTHESIS_RE.search(m["text"]):
            break
        out.append(m)
    return out


def _load_frontmatter(brief_path: Path | None) -> dict | None:
    if brief_path is None or not brief_path.is_file():
        return None
    raw_fm, _ = split_frontmatter(brief_path.read_text(encoding="utf-8"))
    if raw_fm is None:
        return None
    try:
        fm = yaml.safe_load(raw_fm)
    except yaml.YAMLError:
        return None
    return fm if isinstance(fm, dict) else None


def turn_discipline(transcript, brief_path, scenario):
    """standard/deep: one probe per turn. Real single-probe turns often carry two '?'
    ("what goes wrong — is it A, B, or C?" / a restatement-confirm plus the probe), so
    the deterministic cap is 2 '?' per message; 3+ is unambiguous bundling. The judge's
    information_gain/adaptivity dimensions cover the semantic one-variable check."""
    violations = [
        f"turn {m['turn']}: {_question_count(m['text'])} questions"
        for m in _pre_synthesis_examiner_msgs(transcript)
        if _question_count(m["text"]) >= 3
    ]
    return {
        "grader": "turn_discipline",
        "passed": not violations,
        "detail": "; ".join(violations) or "no bundled turns (3+ questions) before synthesis",
    }


def quick_cadence(transcript, brief_path, scenario):
    """quick: grouped probe rounds (messages with 2+ questions) bounded by
    expected_max_question_rounds; single-question turns (thesis ask, steelman confirm)
    are Phase 1, not probe rounds. Max 3 questions per round; no bulleted/numbered
    question lists — a quick-mode group must read as connected prose."""
    violations = []
    probe_rounds = 0
    for m in _pre_synthesis_examiner_msgs(transcript):
        q = _question_count(m["text"])
        if q >= 2:
            probe_rounds += 1
        if q > 3:
            violations.append(f"turn {m['turn']}: {q} questions in one round")
        for line in _strip_brief_and_fences(m["text"]).splitlines():
            if re.match(r"^\s*([-*]|\d+[.)])\s", line) and "?" in line:
                violations.append(f"turn {m['turn']}: checklist-style question line")
                break
    max_rounds = int(scenario.get("expected_max_question_rounds", 2))
    if probe_rounds > max_rounds:
        violations.append(f"{probe_rounds} grouped probe rounds (max {max_rounds})")
    return {
        "grader": "quick_cadence",
        "passed": not violations,
        "detail": "; ".join(violations)
        or f"{probe_rounds} grouped-prose probe rounds, no checklists",
    }


def no_premature_solutioning(transcript, brief_path, scenario):
    """No advice/solution markers in any examiner message before the brief."""
    violations = []
    for m in _pre_synthesis_examiner_msgs(transcript):
        low = m["text"].lower()
        for marker in _SOLUTIONING_MARKERS:
            if marker in low:
                violations.append(f"turn {m['turn']}: '{marker.strip()}'")
    return {
        "grader": "no_premature_solutioning",
        "passed": not violations,
        "detail": "; ".join(violations) or "no solutioning before Phase 4",
    }


def brief_valid(transcript, brief_path, scenario):
    """The brief file exists and passes validate_idea_brief (schema + body rules)."""
    if brief_path is None or not Path(brief_path).is_file():
        return {"grader": "brief_valid", "passed": False, "detail": "no brief file written"}
    errors = validate_idea_brief(brief_path)
    return {
        "grader": "brief_valid",
        "passed": not errors,
        "detail": "; ".join(errors) or "idea-brief-v1 valid",
    }


_QUOTED_SPAN_RE = re.compile(
    r'[""]([^""]{15,300})[""]'  # curly double quotes
    r'|"([^"]{15,300})"'  # straight double quotes
    r"|(?<![A-Za-z0-9])'([^']{15,300})'"  # straight single quotes (not an apostrophe)
)


def _normalize_quote(text: str) -> str:
    """Strip markdown emphasis and collapse whitespace so an examiner quote with added
    **bold** still matches the user's plain words."""
    return re.sub(r"\s+", " ", text.replace("*", "").replace("_", "")).strip().lower()


def _quoted_spans(text: str) -> list[str]:
    """Normalized quoted spans in an examiner message: inline curly/straight double and
    straight single quotes, plus Markdown blockquote lines — the rubric asks the examiner
    to 'quote both back', which a model may render as > blockquotes, not inline quotes."""
    spans = []
    for groups in _QUOTED_SPAN_RE.findall(text):
        span = next((g for g in groups if g), "")
        if span:
            spans.append(_normalize_quote(span))
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith(">"):
            quoted = _normalize_quote(stripped.lstrip(">").strip())
            if len(quoted) >= 15:
                spans.append(quoted)
    return spans


def refutation_mechanics(transcript, brief_path, scenario):
    """The deterministic core of a contradiction cell, verdict-agnostic (with a live
    LLM user-simulator the terminal verdict is variance-prone — the sim may concede —
    so the honest final label is the judge's call; the *mechanics* are checkable):

    1. Some examiner message surfaces a collision by quoting the user: at least two
       distinct quoted spans (>=15 chars) in one message, each found verbatim in
       earlier user messages.
    2. If the brief's verdict IS refuted, every colliding_claims entry must appear
       verbatim in a USER message (refute out of the user's own mouth, or not at all).
    """
    user_so_far = ""
    surfaced = False
    for m in transcript:
        if m["role"] == "user":
            user_so_far += "\n" + _normalize_quote(m["text"])
            continue
        spans = _quoted_spans(m["text"])
        hits = {s for s in spans if s and s in user_so_far}
        if len(hits) >= 2:
            surfaced = True
            break
    if not surfaced:
        return {
            "grader": "refutation_mechanics",
            "passed": False,
            "detail": "no examiner message quotes two verbatim user statements side by side",
        }

    fm = _load_frontmatter(Path(brief_path) if brief_path else None)
    if fm is None:
        return {"grader": "refutation_mechanics", "passed": False, "detail": "no parseable brief"}
    if fm.get("verdict") == "refuted":
        user_text = "\n".join(m["text"] for m in transcript if m["role"] == "user")
        missing = [
            c
            for c in (fm.get("colliding_claims") or [])
            if isinstance(c, str) and c not in user_text
        ]
        if missing:
            return {
                "grader": "refutation_mechanics",
                "passed": False,
                "detail": f"refuted, but colliding claims not verbatim from user: {missing}",
            }
        return {
            "grader": "refutation_mechanics",
            "passed": True,
            "detail": "collision surfaced verbatim; refuted from the user's own words",
        }
    return {
        "grader": "refutation_mechanics",
        "passed": True,
        "detail": f"collision surfaced verbatim; verdict '{fm.get('verdict')}' left to judge",
    }


def aporia_open_questions(transcript, brief_path, scenario):
    """verdict=aporia with at least two open questions (the scenario plants two unknowns)."""
    fm = _load_frontmatter(Path(brief_path) if brief_path else None)
    if fm is None:
        return {"grader": "aporia_open_questions", "passed": False, "detail": "no parseable brief"}
    ok = fm.get("verdict") == "aporia" and len(fm.get("open_questions") or []) >= 2
    return {
        "grader": "aporia_open_questions",
        "passed": ok,
        "detail": (
            f"verdict={fm.get('verdict')}, open_questions={len(fm.get('open_questions') or [])}"
        ),
    }


def _tail_dialogue_questions(tail: str) -> int:
    """Conversational questions in a wrap-up segment, ignoring the brief itself — its
    frontmatter (`key:` lines), headers, list items, blockquotes, and any fenced block —
    so a trailing 'would you like me to also…?' is caught but the brief's own open
    questions are not."""
    n = 0
    for line in _strip_brief_and_fences(tail).splitlines():
        s = line.strip()
        if not s or s[0] in "#-*>|" or re.match(r"^[A-Za-z_][\w -]*:", s):
            continue
        n += s.count("?")
    return n


def stop_honored(transcript, brief_path, scenario):
    """After the user's stop message, no examiner message asks another question. The
    wrap-up message is not exempted wholesale — only its synthesis segment is — so a
    question smuggled into the verdict/brief turn (before or after the brief) is caught."""
    stop_idx = None
    for i, m in enumerate(transcript):
        if m["role"] == "user" and (
            "that's enough" in m["text"].lower() or "wrap up" in m["text"].lower()
        ):
            stop_idx = i
            break
    if stop_idx is None:
        return {"grader": "stop_honored", "passed": False, "detail": "stop message never sent"}
    violations = []
    for m in transcript[stop_idx + 1 :]:
        if m["role"] != "examiner":
            continue
        match = _SYNTHESIS_RE.search(m["text"])
        if match:
            # Count questions before the synthesis marker (dialogue) plus conversational
            # questions after it, but never the brief's own content.
            q = _question_count(m["text"][: match.start()]) + _tail_dialogue_questions(
                m["text"][match.start() :]
            )
        else:
            q = _question_count(m["text"])
        if q > 0:
            violations.append(f"turn {m['turn']}: asked {q} question(s) after stop")
    return {
        "grader": "stop_honored",
        "passed": not violations,
        "detail": "; ".join(violations) or "stop honored instantly",
    }


def dispute_loop_honored(transcript, brief_path, scenario):
    """After the user rejects the restatement, the very next examiner message must be a
    corrected restatement seeking explicit confirmation (exactly one confirmation-style
    question), not a Phase 2 probe."""
    dispute_idx = None
    for i, m in enumerate(transcript):
        if m["role"] == "user" and "not quite" in m["text"].lower():
            dispute_idx = i
            break
    if dispute_idx is None:
        return {"grader": "dispute_loop_honored", "passed": False, "detail": "dispute never raised"}
    nxt = next((m for m in transcript[dispute_idx + 1 :] if m["role"] == "examiner"), None)
    if nxt is None:
        return {"grader": "dispute_loop_honored", "passed": False, "detail": "no examiner reply"}
    q = _question_count(nxt["text"])
    confirming = bool(_CONFIRMATION_MARKERS.search(nxt["text"]))
    ok = q == 1 and confirming
    return {
        "grader": "dispute_loop_honored",
        "passed": ok,
        "detail": (
            "corrected restatement re-confirmed before probing"
            if ok
            else f"next examiner turn after dispute: {q} question(s), "
            f"confirmation-seeking={confirming} — probing on an unconfirmed thesis"
        ),
    }


def scope_check_fired(transcript, brief_path, scenario):
    """Out-of-scope cell (tightened G7): HARD CAP on total examiner questions
    (expected_max_questions, default 2), plus one of the skill's two legitimate
    stand-down outcomes: an explicit decline/redirect, or the idea recorded as a
    brief as-is (brief written without an elenchus — detected by the same hard
    count, not by phrasing). Question count is the teeth — politeness cannot
    compensate for an elenchus, and phrasing variance cannot fail a real decline."""
    max_q = int(scenario.get("expected_max_questions", 2))
    total_q = sum(_question_count(m["text"]) for m in _examiner_msgs(transcript))
    declined = any(
        marker in m["text"].lower()
        for m in _examiner_msgs(transcript)
        for marker in _DECLINE_MARKERS
    )
    brief_as_is = brief_path is not None and Path(brief_path).is_file()
    ok = total_q <= max_q and (declined or brief_as_is)
    return {
        "grader": "scope_check_fired",
        "passed": ok,
        "detail": (
            f"total examiner questions={total_q} (cap {max_q}), "
            f"decline/redirect stated={declined}, brief recorded as-is={brief_as_is}"
        ),
    }


def session_claims_accurate(transcript, brief_path, scenario):
    """Audit-loop check on the brief's self-reported questions_asked. The skill counts
    semantic Phase 2 probes; this measures '?' occurrences in pre-synthesis examiner
    messages — a noisy superset (elaboration/confirmation '?'s) that can also undercount
    (imperative probes carry no '?'). So: sanity BOUNDS, not equality — catch gross
    fabrication in either direction, tolerate counting semantics. Calibrated on five
    honest recorded sessions (claimed/measured ratio 0.50-0.82). types_used accuracy is
    semantic and stays judge territory."""
    fm = _load_frontmatter(Path(brief_path) if brief_path else None)
    if fm is None:
        return {
            "grader": "session_claims_accurate",
            "passed": False,
            "detail": "no parseable brief",
        }
    claimed = fm.get("questions_asked")
    if not isinstance(claimed, int):
        return {
            "grader": "session_claims_accurate",
            "passed": True,
            "detail": "questions_asked not set (optional field)",
        }
    measured = sum(_question_count(m["text"]) for m in _pre_synthesis_examiner_msgs(transcript))
    # measured <= 2 can be a lone steelman-confirm '?': claiming zero probes is honest.
    lo = 0 if measured <= 2 else measured / 3
    # Upper bound is proportional, not flat: imperative probes ("walk me through...")
    # are real Phase 2 probes carrying no '?', so an imperative-heavy honest session
    # can legitimately claim more than the '?'-count.
    hi = measured * 1.5 + 2
    ok = lo <= claimed <= hi
    return {
        "grader": "session_claims_accurate",
        "passed": ok,
        "detail": (
            f"claimed={claimed}, measured='?'-count={measured}, sane range [{lo:.1f}, {hi:.1f}]"
        ),
    }


GRADERS = {
    fn.__name__: fn
    for fn in (
        turn_discipline,
        quick_cadence,
        no_premature_solutioning,
        brief_valid,
        refutation_mechanics,
        aporia_open_questions,
        stop_honored,
        dispute_loop_honored,
        scope_check_fired,
        session_claims_accurate,
    )
}


def run_graders(transcript, brief_path, scenario) -> list[dict]:
    """Run the graders named in scenario['expected']['graders']; unknown names fail loudly."""
    results = []
    for name in scenario.get("expected", {}).get("graders", []):
        fn = GRADERS.get(name)
        if fn is None:
            results.append({"grader": name, "passed": False, "detail": "unknown grader"})
        else:
            results.append(fn(transcript, brief_path, scenario))
    return results
