"""Unit tests for the pure, deterministic eval graders (no model calls).

The eval harness (``run_eval.py``) is never wired into CI, so without these the grader
logic only ever runs during a paid, non-deterministic full eval — a regression in a
bound/marker/regex would be indistinguishable from ordinary model variance.
"""

import re

from conftest import GOLDEN  # also puts evals/ on sys.path for the graders import below
from graders import (
    aporia_open_questions,
    brief_valid,
    dispute_loop_honored,
    no_premature_solutioning,
    quick_cadence,
    refutation_mechanics,
    run_graders,
    scope_check_fired,
    session_claims_accurate,
    stop_honored,
    turn_discipline,
)


def _t(role, turn, text):
    return {"role": role, "turn": turn, "text": text}


def test_turn_discipline_flags_three_bundled_questions():
    transcript = [_t("examiner", 1, "Who is it for? What do they do? Why now?")]
    assert turn_discipline(transcript, None, {})["passed"] is False


def test_turn_discipline_allows_two_questions_in_one_turn():
    transcript = [_t("examiner", 1, "What goes wrong? Is it A or B?")]
    assert turn_discipline(transcript, None, {})["passed"] is True


def test_no_premature_solutioning_flags_advice_marker():
    transcript = [_t("examiner", 1, "I'd suggest using a message queue here.")]
    assert no_premature_solutioning(transcript, None, {})["passed"] is False


def test_brief_valid_passes_golden_fails_missing():
    assert brief_valid([], GOLDEN, {})["passed"] is True
    assert brief_valid([], None, {})["passed"] is False


def test_refutation_mechanics_accepts_blockquote_quoting():
    # Regression: the quote regex used to match only double quotes, false-failing a
    # correct collision surfaced with Markdown blockquotes. brief_path -> a sharpened
    # brief so the verdict branch defers to the judge and only the mechanics are checked.
    transcript = [
        _t("examiner", 1, "What's the cadence?"),
        _t("user", 1, "It absolutely must ship every single week without any exception."),
        _t("examiner", 2, "And capacity?"),
        _t("user", 2, "We only have three engineers and they are already fully booked."),
        _t(
            "examiner",
            3,
            "Two of your answers seem to collide:\n"
            "> It absolutely must ship every single week without any exception\n"
            "> We only have three engineers and they are already fully booked\n"
            "Which one gives?",
        ),
    ]
    assert refutation_mechanics(transcript, GOLDEN, {})["passed"] is True


def test_refutation_mechanics_accepts_single_quote_quoting():
    transcript = [
        _t("user", 1, "It absolutely must ship every single week without any exception."),
        _t("user", 2, "We only have three engineers and they are already fully booked."),
        _t(
            "examiner",
            3,
            "You said 'It absolutely must ship every single week without any exception' "
            "but also 'We only have three engineers and they are already fully booked'.",
        ),
    ]
    assert refutation_mechanics(transcript, GOLDEN, {})["passed"] is True


def test_stop_honored_passes_a_clean_wrapup():
    transcript = [
        _t("examiner", 1, "What's the core idea?"),
        _t("user", 1, "A weekly newsletter."),
        _t("user", 2, "ok that's enough"),
        _t(
            "examiner",
            2,
            "Verdict: sharpened. Brief saved to notes/idea-briefs/x-20260101.md.\n"
            "```\nschema: idea-brief-v1\n## Open questions (aporia)\n- who is it for?\n```",
        ),
    ]
    assert stop_honored(transcript, None, {})["passed"] is True


def test_stop_honored_catches_trailing_question_in_wrapup():
    # Regression: a whole synthesis message used to be exempt, hiding a smuggled probe.
    transcript = [
        _t("examiner", 1, "What's the core idea?"),
        _t("user", 1, "A weekly newsletter."),
        _t("user", 2, "ok that's enough, wrap up"),
        _t(
            "examiner",
            2,
            "Verdict: sharpened.\nBrief saved to notes/idea-briefs/x-20260101.md.\n"
            "Out of curiosity, would you like me to also note the tooling risk?",
        ),
    ]
    assert stop_honored(transcript, None, {})["passed"] is False


def test_stop_honored_catches_post_stop_probe():
    transcript = [
        _t("user", 1, "that's enough"),
        _t("examiner", 1, "Just one more thing: what is your budget?"),
    ]
    assert stop_honored(transcript, None, {})["passed"] is False


def test_run_graders_reports_unknown_grader():
    results = run_graders([], None, {"expected": {"graders": ["does_not_exist"]}})
    assert results == [{"grader": "does_not_exist", "passed": False, "detail": "unknown grader"}]


def test_no_premature_solutioning_passes_clean_questioning():
    transcript = [_t("examiner", 1, "What problem does this solve, and for whom?")]
    assert no_premature_solutioning(transcript, None, {})["passed"] is True


def test_stop_honored_fails_when_stop_never_sent():
    transcript = [_t("examiner", 1, "What's the goal?"), _t("user", 1, "A newsletter.")]
    r = stop_honored(transcript, None, {})
    assert r["passed"] is False
    assert r["detail"] == "stop message never sent"


def test_brief_valid_fails_on_invalid_content(tmp_path):
    bad = tmp_path / "x-20260101.md"
    bad.write_text("not a valid brief", encoding="utf-8")
    r = brief_valid([], bad, {})
    assert r["passed"] is False and "No YAML frontmatter" in r["detail"]


def test_quick_cadence_flags_checklist_line():
    transcript = [_t("examiner", 1, "A few things:\n- what's the audience?\n- what's the budget?")]
    r = quick_cadence(transcript, None, {"expected_max_question_rounds": 2})
    assert r["passed"] is False
    assert "checklist-style question line" in r["detail"]


def test_quick_cadence_flags_one_question_per_turn_devolution():
    # Regression: a quick session that never groups but runs turn-by-turn used to pass.
    transcript = [
        _t("examiner", 1, "State the idea?"),
        _t("examiner", 2, "Is that right?"),
        _t("examiner", 3, "Who is it for?"),
        _t("examiner", 4, "What do they do now?"),
        _t("examiner", 5, "Why now?"),
    ]
    r = quick_cadence(transcript, None, {"expected_max_question_rounds": 2})
    assert r["passed"] is False
    assert "one-question-per-turn" in r["detail"]


def test_quick_cadence_passes_two_grouped_rounds():
    transcript = [
        _t("examiner", 1, "State the idea?"),
        _t("examiner", 2, "So it's X — right?"),
        _t("examiner", 3, "Who is it for? What do they do today?"),
        _t("examiner", 4, "What breaks if it works? Who loses?"),
    ]
    assert quick_cadence(transcript, None, {"expected_max_question_rounds": 2})["passed"] is True


def test_aporia_open_questions_pass_and_fail(tmp_path):
    base = GOLDEN.read_text(encoding="utf-8").replace("verdict: sharpened", "verdict: aporia")
    ok = tmp_path / "a-20260101.md"
    ok.write_text(base, encoding="utf-8")  # golden already carries two open_questions
    assert aporia_open_questions([], ok, {})["passed"] is True
    bad = tmp_path / "b-20260101.md"
    bad.write_text(
        re.sub(r"open_questions:\n(  - .*\n)+", 'open_questions:\n  - "only one"\n', base),
        encoding="utf-8",
    )
    assert aporia_open_questions([], bad, {})["passed"] is False


def test_scope_check_fired_hard_cap_beats_politeness():
    # A decline marker cannot compensate for actually running an elenchus (4 questions).
    transcript = [_t("examiner", 1, "This is already specified, but who? what? when? why?")]
    assert scope_check_fired(transcript, None, {"expected_max_questions": 2})["passed"] is False


def test_scope_check_fired_passes_on_clean_decline():
    transcript = [
        _t("examiner", 1, "This looks already specified — want me to record it as a brief as-is?")
    ]
    assert scope_check_fired(transcript, None, {"expected_max_questions": 2})["passed"] is True


def test_dispute_loop_honored_pass_and_fail():
    ok = [
        _t("examiner", 1, "So the core is X — right?"),
        _t("user", 1, "not quite, it's more about Y"),
        _t("examiner", 2, "Got it — so the core is Y. Did I capture that right?"),
    ]
    assert dispute_loop_honored(ok, None, {})["passed"] is True
    bad = [
        _t("examiner", 1, "So the core is X — right?"),
        _t("user", 1, "not quite, it's more about Y"),
        _t("examiner", 2, "OK. So who is the audience?"),
    ]
    r = dispute_loop_honored(bad, None, {})
    assert r["passed"] is False
    assert "unconfirmed thesis" in r["detail"]


def test_session_claims_accurate_pass_and_fail():
    six_q = [_t("examiner", i, "why?") for i in range(1, 7)]  # measured '?'-count = 6
    assert session_claims_accurate(six_q, GOLDEN, {})["passed"] is True  # golden claims 9
    # Empty transcript: measured 0, hi floor 6; golden's claimed 9 is out of range.
    assert session_claims_accurate([], GOLDEN, {})["passed"] is False


_U1 = "It absolutely must ship every single week without any exception."
_U2 = "We only have three engineers and they are already fully booked."


def _refuted_brief(path, claim2):
    path.write_text(
        f"---\nschema: idea-brief-v1\nverdict: refuted\n"
        f'colliding_claims:\n  - "{_U1}"\n  - "{claim2}"\n---\nbody\n',
        encoding="utf-8",
    )
    return path


def test_refutation_mechanics_refuted_from_user_words(tmp_path):
    transcript = [
        _t("user", 1, _U1),
        _t("user", 2, _U2),
        _t("examiner", 3, f'You said "{_U1}" but also "{_U2}" — which one gives?'),
    ]
    good = _refuted_brief(tmp_path / "r-20260101.md", _U2)
    assert refutation_mechanics(transcript, good, {})["passed"] is True
    bad = _refuted_brief(tmp_path / "r2-20260101.md", "the user never said this at all")
    r = refutation_mechanics(transcript, bad, {})
    assert r["passed"] is False
    assert "not verbatim from user" in r["detail"]


def test_refutation_mechanics_ignores_brief_only_quotes(tmp_path):
    # Regression: the surfaced check must NOT be satisfiable by the printed brief's own
    # colliding_claims when the examiner never quoted the collision during the dialogue.
    transcript = [
        _t("user", 1, _U1),
        _t("user", 2, _U2),
        _t(
            "examiner",
            3,
            f'Verdict: refuted. Brief at notes/idea-briefs/x.md quotes "{_U1}", "{_U2}".',
        ),
    ]
    good = _refuted_brief(tmp_path / "r-20260101.md", _U2)
    assert refutation_mechanics(transcript, good, {})["passed"] is False


def test_refutation_mechanics_accepts_verdict_label_before_quotes(tmp_path):
    # Regression: truncating on _SYNTHESIS_RE dropped quotes that follow a bare "Verdict:"
    # label in the same message — the natural same-message refutation must be recognised.
    transcript = [
        _t("user", 1, _U1),
        _t("user", 2, _U2),
        _t("examiner", 3, f'Verdict: refuted. You said "{_U1}" but also "{_U2}".'),
    ]
    good = _refuted_brief(tmp_path / "r-20260101.md", _U2)
    assert refutation_mechanics(transcript, good, {})["passed"] is True


def test_stop_honored_passes_unfenced_brief_with_open_question():
    # in_brief_body: the brief's own (un-fenced) open question must not count as a probe.
    transcript = [
        _t("user", 1, "that's enough"),
        _t(
            "examiner",
            1,
            "Verdict: aporia.\n# Idea brief: x\n## Open questions (aporia)\nwho is it for?",
        ),
    ]
    assert stop_honored(transcript, None, {})["passed"] is True


def test_stop_honored_flags_question_before_unfenced_brief_body():
    # A genuine trailing question that PRECEDES the un-fenced brief body is still caught.
    transcript = [
        _t("user", 1, "that's enough"),
        _t(
            "examiner",
            1,
            "Verdict: sharpened. One more — should I also flag the tooling risk?\n"
            "# Idea brief: x\n## Open questions (aporia)\nwho is it for?",
        ),
    ]
    assert stop_honored(transcript, None, {})["passed"] is False
