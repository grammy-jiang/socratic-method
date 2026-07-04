"""Validate an idea brief produced by the socratic-method skill.

Structural: YAML frontmatter validated against the packaged
``idea-brief-v1.schema.json``. Cross-field rules the schema cannot express:

- ``verdict: refuted`` — each ``colliding_claims`` entry must appear verbatim in the
  markdown body (the skill may only refute out of the user's own quoted mouth);
- required body headers from the skill's Phase 4 template must all be present;
- the filename slug (when the file follows ``<idea-slug>-YYYYMMDD.md``) must agree
  with the frontmatter ``idea`` field.

API: ``validate_idea_brief(path) -> list[str]`` (empty list = valid).
CLI: ``socratic-method validate <brief.md>``.
"""

from __future__ import annotations

import datetime
import json
import re
from importlib.resources import files
from pathlib import Path

import jsonschema
import yaml

_REQUIRED_HEADERS = (
    "# Idea brief:",
    "## What changed under questioning",
    "## Scope",
    "## Assumptions surfaced",
    "## Contradictions & how resolved",
    "## Open questions (aporia)",
    "## Suggested next step",
)

_FILENAME_RE = re.compile(r"^(?P<slug>[a-z0-9][a-z0-9-]*)-(?P<date>\d{8})\.md$")


def load_schema() -> dict:
    """Load the packaged idea-brief-v1 JSON schema."""
    raw = (
        files("socratic_method")
        .joinpath("assets/idea-brief-v1.schema.json")
        .read_text(encoding="utf-8")
    )
    return json.loads(raw)


def split_frontmatter(text: str) -> tuple[str | None, str]:
    """Return (frontmatter_yaml, body), or (None, text) when no frontmatter block."""
    if not text.startswith("---"):
        return None, text
    parts = text.split("\n---", 2)
    if len(parts) < 2:
        return None, text
    return parts[0].removeprefix("---").strip("\n"), parts[1] + (parts[2] if len(parts) > 2 else "")


def validate_idea_brief(brief_path: str | Path) -> list[str]:
    """Return list of error strings. Empty list = valid."""
    path = Path(brief_path)
    errors: list[str] = []

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        return [f"Read error: {e}"]

    raw_fm, body = split_frontmatter(text)
    if raw_fm is None:
        return ["No YAML frontmatter block (file must start with ---)"]

    try:
        fm = yaml.safe_load(raw_fm)
    except yaml.YAMLError as e:
        return [f"Frontmatter YAML parse error: {e}"]
    if not isinstance(fm, dict):
        return ["Frontmatter is not a mapping"]

    # YAML parses an unquoted 2026-07-04 as datetime.date; normalize before schema check.
    if isinstance(fm.get("date"), datetime.date):
        fm["date"] = fm["date"].isoformat()

    try:
        schema = load_schema()
    except (OSError, json.JSONDecodeError) as e:
        return [f"Schema load error: {e}"]
    validator = jsonschema.Draft202012Validator(schema)
    errors.extend(
        f"frontmatter{'.' + '.'.join(str(p) for p in err.path) if err.path else ''}: {err.message}"
        for err in sorted(validator.iter_errors(fm), key=lambda e: list(e.path))
    )

    for header in _REQUIRED_HEADERS:
        if not any(line.startswith(header) for line in body.splitlines()):
            errors.append(f"body: missing required header '{header}'")

    if fm.get("verdict") == "refuted":
        for i, claim in enumerate(fm.get("colliding_claims") or []):
            if isinstance(claim, str) and claim not in body:
                errors.append(
                    f"colliding_claims[{i}]: not found verbatim in body — "
                    "refutation must quote the colliding answers exactly"
                )

    m = _FILENAME_RE.match(path.name)
    if m and isinstance(fm.get("idea"), str) and m.group("slug") != fm["idea"]:
        errors.append(
            f"filename slug '{m.group('slug')}' does not match frontmatter idea '{fm['idea']}'"
        )

    return errors
