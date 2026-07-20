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

from socratic_method.validator import (
    REQUIRED_HEADERS,
    parse_frontmatter_yaml,
    split_frontmatter,
    validate_idea_brief,
)

_BRIEF_MARKER = "schema: idea-brief-v1"

# A synthesis (Phase 3/4) message: the examiner may print the brief in chat as prose
# rather than embedding the frontmatter, so detect any of the wrap-up signatures.
# Built from _BRIEF_MARKER so the marker string has a single source.
_SYNTHESIS_RE = re.compile(rf"{re.escape(_BRIEF_MARKER)}|notes/idea-briefs/|\*\*Verdict|\bVerdict:")

# Brief-ECHO markers only (the printed brief's own content is starting) — a stricter set
# than _SYNTHESIS_RE, which also matches the bare "Verdict:" prose label that in live
# dialogue routinely PRECEDES the quote-back a same-message refutation is built from.
_BRIEF_ECHO_RE = re.compile(
    "|".join(
        [re.escape(_BRIEF_MARKER), "notes/idea-briefs/", *(re.escape(h) for h in REQUIRED_HEADERS)]
    )
)

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
    raw_fm, _ = split_frontmatter(brief_path.read_text(encoding="utf-8-sig"))
    if raw_fm is None:
        return None
    try:
        return parse_frontmatter_yaml(raw_fm)  # shared with the validator (incl. date-normalize)
    except yaml.YAMLError:
        return None


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
    pre = _pre_synthesis_examiner_msgs(transcript)
    for m in pre:
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
    # Conservative devolution backstop (uncalibrated cutoff): a quick session should GROUP
    # its probes. If it never groups (probe_rounds == 0) yet runs several single-question
    # turns past the first two Phase-1 turns (thesis ask + steelman confirm), it silently
    # ran a standard one-per-turn cadence — which the grouped-round count alone passes.
    single_q = sum(1 for i, msg in enumerate(pre) if i >= 2 and _question_count(msg["text"]) == 1)
    if probe_rounds == 0 and single_q >= 3:
        violations.append(
            f"{single_q} single-question turns, no grouped rounds — "
            "ran one-question-per-turn (standard) cadence, not quick"
        )
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
        # Scan only the pre-synthesis portion. A refuted brief's colliding_claims, printed
        # in the wrap-up message, reproduce the user's words verbatim — scanning the whole
        # message would let surfaced=True fire off the brief alone, with zero live elenchus.
        # Mirror stop_honored's head/tail split.
        # Truncate on brief-ECHO markers only (schema line, output path, or a required
        # brief header) — NOT on a bare "Verdict:" label, which in live dialogue precedes
        # the very quote-back a same-message refutation is built from.
        marker = _BRIEF_ECHO_RE.search(m["text"])
        scan_text = _strip_brief_and_fences(m["text"][: marker.start()] if marker else m["text"])
        hits = {s for s in _quoted_spans(scan_text) if s and s in user_so_far}
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
    fenced block, frontmatter (lowercase `key:` lines), headers, list items, and
    blockquotes — so a trailing 'would you like me to also…?' is caught but the brief's
    own open questions are not. Once a required brief header appears, every later line is
    brief body (open-question prose can be un-fenced narrative)."""
    n = 0
    in_brief_body = False
    for line in _strip_brief_and_fences(tail).splitlines():
        s = line.strip()
        if any(s.startswith(h) for h in REQUIRED_HEADERS):
            in_brief_body = True
        # Lowercase `key:` only — so a natural lead-in like "One more thing:" is not
        # mistaken for a frontmatter key and skipped along with its trailing '?'.
        if in_brief_body or not s or s[0] in "#-*>|" or re.match(r"^[a-z][a-z_]*:\s", s):
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
    # can legitimately claim more than the '?'-count. The flat floor of 6 (uncalibrated
    # stopgap, NOT derived from the 5-session data) keeps an all-imperative session
    # (measured≈0, where the proportional term collapses to 2) from failing an honest
    # higher claim.
    hi = max(measured * 1.5 + 2, 6)
    ok = lo <= claimed <= hi
    return {
        "grader": "session_claims_accurate",
        "passed": ok,
        "detail": (
            f"claimed={claimed}, measured='?'-count={measured}, sane range [{lo:.1f}, {hi:.1f}]"
        ),
    }


_FALSIFICATION_MARKERS = (
    # "what would change your mind / prove it wrong / falsify it" family
    "change your mind",
    "change my mind",
    "wrong call",
    "prove you wrong",
    "prove it wrong",
    "prove this wrong",
    "falsif",  # falsify / falsifiable / falsification
    "disconfirm",
    "what would you have to see",
    "what would have to be true for",
    "what would tell you",
    "what would convince you",
    "how would you know if",
    "what evidence would",
    "what would make this the wrong",
    # stop / kill-condition framing — a disconfirming probe often asks for the failure
    # threshold or kill trigger without ever using the word "wrong" (observed in a live
    # run: "what triggers pulling that switch", "what would count as the experiment
    # failing"). These are canonical falsification phrasings, not scenario-specific.
    "pull the plug",
    "pulling the plug",
    "pull that switch",
    "pulling that switch",
    "trigger pulling",
    "triggers pulling",
    "kill switch",
    "kill criteri",  # kill criteria / kill criterion
    "walk away from this",
    "would you walk away",
    "call it a mistake",
    "call this a mistake",
    "call it quits",
    "when would you stop",
    "when would you kill",
    "when would you pull",
    "when would you abandon",
    "what would make you stop",
    "what would make you pull",
    "what would make you kill",
    "what would make you abandon",
)


def _asks_falsification(text: str) -> bool:
    t = text.lower()
    if any(marker in t for marker in _FALSIFICATION_MARKERS):
        return True
    # "what would count as (it / the experiment) failing / a failure / a mistake" — a
    # threshold-for-being-wrong probe that needn't contain the literal word "wrong".
    # "count as" is rare enough that pairing it with fail/mistake is a reliable signal.
    return "count as" in t and ("fail" in t or "mistake" in t)


def falsification_probe_asked(transcript, brief_path, scenario):
    """`stress` mode mandates at least one falsification/disconfirming probe (SKILL.md:
    'at least one disconfirming probe belongs in every stress pass', scheduled in
    Sequencing). Deterministic sensor that some pre-synthesis examiner message actually
    asked one, recognising both the 'what would prove this wrong' family and the
    'what's the kill/failure threshold' framing. The harder, inferential half — that a
    clean, concrete falsifier is NOT then mislabeled 'faith-based' / unfalsifiable — is
    left to the judge (see the cell's judge_focus), matching the graders/judge split used
    everywhere else here."""
    hits = [
        f"turn {m['turn']}"
        for m in _pre_synthesis_examiner_msgs(transcript)
        if _asks_falsification(m["text"])
    ]
    return {
        "grader": "falsification_probe_asked",
        "passed": bool(hits),
        "detail": (
            f"falsification/disconfirming probe asked ({', '.join(hits)})"
            if hits
            else "no falsification/disconfirming probe found before synthesis"
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
        falsification_probe_asked,
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
