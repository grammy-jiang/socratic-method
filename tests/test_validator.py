"""Validator tests: the golden fixture must pass, and five targeted mutations must each
be caught by their INTENDED rule (not merely caught by something)."""

import re
from pathlib import Path

import pytest

from socratic_method.validator import validate_idea_brief

GOLDEN = Path(__file__).parent.parent / "evals" / "fixtures" / "tech-talk-series-20260704.md"

MUTATIONS = {
    "refuted-without-colliding-claims": (
        lambda g: g.replace("verdict: sharpened", "verdict: refuted"),
        "'colliding_claims' is a required property",
    ),
    "refuted-nonverbatim-claim": (
        lambda g: g.replace(
            "verdict: sharpened",
            'verdict: refuted\ncolliding_claims: ["weekly, otherwise it loses momentum",'
            ' "THIS QUOTE IS NOT IN THE BODY"]',
        ),
        "not found verbatim in body",
    ),
    "invalid-verdict-enum": (
        lambda g: g.replace("verdict: sharpened", "verdict: maybe"),
        "'maybe' is not one of",
    ),
    "missing-required-header": (
        lambda g: g.replace("## Scope", "## Range"),
        "missing required header '## Scope'",
    ),
    "aporia-with-empty-open-questions": (
        lambda g: re.sub(
            r"open_questions:\n(  - .*\n)+",
            "open_questions: []\n",
            g.replace("verdict: sharpened", "verdict: aporia"),
        ),
        "open_questions: [] should be non-empty",
    ),
}


def test_golden_fixture_is_valid():
    assert validate_idea_brief(GOLDEN) == []


@pytest.mark.parametrize("name", MUTATIONS)
def test_mutation_caught_by_intended_rule(name, tmp_path):
    mutate, expected = MUTATIONS[name]
    p = tmp_path / GOLDEN.name
    p.write_text(mutate(GOLDEN.read_text(encoding="utf-8")), encoding="utf-8")
    errors = validate_idea_brief(p)
    assert any(expected in e for e in errors), f"{name}: intended rule not hit; got {errors}"


def test_filename_slug_mismatch_caught(tmp_path):
    p = tmp_path / "wrong-slug-20260704.md"
    p.write_text(GOLDEN.read_text(encoding="utf-8"), encoding="utf-8")
    errors = validate_idea_brief(p)
    assert any("does not match frontmatter idea" in e for e in errors)


def test_missing_frontmatter_caught(tmp_path):
    p = tmp_path / "x.md"
    p.write_text("# Idea brief: nope\n")
    assert validate_idea_brief(p) == ["No YAML frontmatter block (file must start with ---)"]
