"""Validator tests: the golden fixture must pass, and five targeted mutations must each
be caught by their INTENDED rule (not merely caught by something)."""

import re

import pytest
from conftest import GOLDEN

from socratic_method.validator import (
    _MAX_BRIEF_BYTES,
    split_frontmatter,
    validate_idea_brief,
)

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


def test_colliding_claims_non_list_is_reported_not_raised(tmp_path):
    # Regression: `verdict: refuted` with a scalar colliding_claims (`colliding_claims: 5`)
    # used to raise TypeError from enumerate(); it must return the schema error instead.
    p = tmp_path / GOLDEN.name
    p.write_text(
        GOLDEN.read_text(encoding="utf-8").replace(
            "verdict: sharpened", "verdict: refuted\ncolliding_claims: 5"
        ),
        encoding="utf-8",
    )
    errors = validate_idea_brief(p)  # must return, never raise
    assert any("colliding_claims" in e and "array" in e for e in errors)


def test_body_divider_line_is_preserved():
    # Regression: split_frontmatter used to eat body lines beginning with "---".
    fm, body = split_frontmatter("---\na: 1\n---\nbefore\n---\nafter\n")
    assert fm == "a: 1"
    assert "\n---\n" in body and "before" in body and "after" in body


def test_non_utf8_file_returns_read_error(tmp_path):
    # A non-UTF-8 file must degrade to a Read error, not crash the CLI.
    p = tmp_path / "utf16-20260704.md"
    p.write_bytes(GOLDEN.read_text(encoding="utf-8").encode("utf-16"))
    errors = validate_idea_brief(p)
    assert len(errors) == 1 and errors[0].startswith("Read error:")


def test_bom_prefixed_file_is_still_valid(tmp_path):
    # A leading UTF-8 BOM must not be mistaken for missing frontmatter.
    p = tmp_path / GOLDEN.name
    p.write_bytes(GOLDEN.read_text(encoding="utf-8").encode("utf-8-sig"))
    assert validate_idea_brief(p) == []


def test_missing_file_returns_read_error(tmp_path):
    errors = validate_idea_brief(tmp_path / "does-not-exist.md")
    assert len(errors) == 1 and errors[0].startswith("Read error:")


def test_malformed_yaml_frontmatter_reported(tmp_path):
    p = tmp_path / "x-20260704.md"
    p.write_text("---\nfoo: 'unterminated\n---\n# body\n", encoding="utf-8")
    assert any(e.startswith("Frontmatter YAML parse error:") for e in validate_idea_brief(p))


def test_non_mapping_frontmatter_reported(tmp_path):
    p = tmp_path / "x-20260704.md"
    p.write_text("---\n- a\n- b\n---\n# body\n", encoding="utf-8")
    assert validate_idea_brief(p) == ["Frontmatter is not a mapping"]


def test_unterminated_frontmatter_reported(tmp_path):
    # Opens with --- but has no closing fence: distinct message from "no frontmatter".
    p = tmp_path / "x-20260704.md"
    p.write_text("---\nschema: idea-brief-v1\n", encoding="utf-8")
    assert validate_idea_brief(p) == [
        "Unterminated YAML frontmatter block (opening --- found, no closing --- found)"
    ]


def test_oversize_file_returns_read_error(tmp_path):
    # A pathological over-cap brief must be rejected by the size guard, never read whole
    # into memory (defends the CLI and the eval harness against a giant blob).
    p = tmp_path / "huge-20260704.md"
    p.write_bytes(b"-" * (_MAX_BRIEF_BYTES + 1))
    assert validate_idea_brief(p) == [f"Read error: file exceeds {_MAX_BRIEF_BYTES}-byte limit"]


def test_deeply_nested_yaml_reported_not_raised(tmp_path):
    # Deeply nested flow YAML overflows the pure-Python parser's recursion; it must degrade
    # to an error string, never let a RecursionError escape the validator.
    depth = 20000
    p = tmp_path / "nested-20260704.md"
    p.write_text("---\na: " + "[" * depth + "]" * depth + "\n---\n# body\n", encoding="utf-8")
    errors = validate_idea_brief(p)  # must return, never raise
    assert any("nested too deeply" in e for e in errors), errors


def test_title_header_prefix_is_intentional(tmp_path):
    # The "# Idea brief:" header is matched by prefix on purpose (the title carries a
    # free-text name suffix). Changing the suffix must still validate — this pins WHY
    # the header check uses startswith rather than exact equality.
    p = tmp_path / GOLDEN.name
    p.write_text(
        GOLDEN.read_text(encoding="utf-8").replace(
            "# Idea brief: internal tech-talk series", "# Idea brief: something entirely different"
        ),
        encoding="utf-8",
    )
    assert validate_idea_brief(p) == []
