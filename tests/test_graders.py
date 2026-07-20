"""Unit tests for the pure, deterministic eval graders (no model calls).

The eval harness (``run_eval.py``) is never wired into CI, so without these the grader
logic only ever runs during a paid, non-deterministic full eval — a regression in a
bound/marker/regex would be indistinguishable from ordinary model variance.
"""

from pathlib import Path

from graders import (  # noqa: E402  (path set up in conftest.py)
    brief_valid,
    no_premature_solutioning,
    refutation_mechanics,
    run_graders,
    stop_honored,
    turn_discipline,
)

GOLDEN = Path(__file__).parent.parent / "evals" / "fixtures" / "tech-talk-series-20260704.md"


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
