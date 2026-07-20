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

REQUIRED_HEADERS = (
    "# Idea brief:",
    "## What changed under questioning",
    "## Scope",
    "## Assumptions surfaced",
    "## Contradictions & how resolved",
    "## Open questions (aporia)",
    "## Suggested next step",
)

_FILENAME_RE = re.compile(r"^(?P<slug>[a-z0-9][a-z0-9-]*)-(?P<date>\d{8})\.md$")

# A real brief is a few KB. Cap the read at ~100x that so a pathological input (a giant
# blob, or a deeply nested / alias-expanded YAML "bomb") can't exhaust memory in the CLI
# or in the eval harness, which runs this validator on model-written briefs.
_MAX_BRIEF_BYTES = 1 << 20  # 1 MiB


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
    # Split only on the FIRST "\n---" (the closing fence). Splitting on every
    # occurrence and reassembling silently dropped body lines that begin with
    # "---" — e.g. a Markdown horizontal rule between two quoted claims, exactly
    # where the verdict=refuted verbatim check reads the body.
    parts = text.split("\n---", 1)
    if len(parts) < 2:
        return None, text
    return parts[0].removeprefix("---").strip("\n"), parts[1]


class _NoAliasSafeLoader(yaml.SafeLoader):
    """SafeLoader that refuses YAML anchors/aliases.

    A brief never legitimately needs them, and an alias graph is a denial-of-service vector:
    PyYAML shares references at parse time (so the parse itself stays cheap), but downstream
    ``jsonschema`` error messages embed ``repr(instance)``, which re-materializes every logical
    occurrence of a shared node — a few KB of nested anchors expands exponentially there,
    under any byte cap. Refusing aliases at compose time closes that at the root, with no
    effect on any real brief.
    """

    def compose_node(self, parent, index):
        if self.check_event(yaml.events.AliasEvent):
            event = self.get_event()
            raise yaml.constructor.ConstructorError(
                None,
                None,
                "YAML aliases/anchors are not allowed in an idea brief",
                event.start_mark,
            )
        return super().compose_node(parent, index)


def parse_frontmatter_yaml(raw_fm: str) -> dict | None:
    """Parse a frontmatter YAML block to a mapping, or None if it is not one.

    Raises ``yaml.YAMLError`` on malformed YAML — including a refused anchor/alias (callers
    decide how to report it) — and normalizes a ``date:`` that YAML auto-parsed into a
    ``datetime.date`` back to an ISO string, so the validator and the eval graders parse
    frontmatter one identical way.
    """
    fm = yaml.load(raw_fm, Loader=_NoAliasSafeLoader)  # SafeLoader subclass — safe_load-equivalent
    if not isinstance(fm, dict):
        return None
    if isinstance(fm.get("date"), datetime.date):
        fm["date"] = fm["date"].isoformat()
    return fm


def validate_idea_brief(brief_path: str | Path) -> list[str]:
    """Return list of error strings. Empty list = valid."""
    path = Path(brief_path)
    errors: list[str] = []

    try:
        # Bounded read (read one byte past the cap so an over-limit file is detectable
        # without pulling the whole thing into memory). utf-8-sig transparently strips a
        # leading BOM (a no-op otherwise); a decode failure (UnicodeDecodeError is a
        # ValueError, NOT an OSError) must degrade to the usual Read-error string, not crash.
        with path.open("rb") as fh:
            raw = fh.read(_MAX_BRIEF_BYTES + 1)
        if len(raw) > _MAX_BRIEF_BYTES:
            return [f"Read error: file exceeds {_MAX_BRIEF_BYTES}-byte limit"]
        text = raw.decode("utf-8-sig")
    except (OSError, UnicodeDecodeError) as e:
        return [f"Read error: {e}"]

    raw_fm, body = split_frontmatter(text)
    if raw_fm is None:
        if text.startswith("---"):
            return ["Unterminated YAML frontmatter block (opening --- found, no closing --- found)"]
        return ["No YAML frontmatter block (file must start with ---)"]

    try:
        fm = parse_frontmatter_yaml(raw_fm)
    except yaml.YAMLError as e:
        return [f"Frontmatter YAML parse error: {e}"]
    except RecursionError:
        # Deeply nested YAML (thousands of open brackets) overflows the pure-Python
        # parser's recursion before it builds a value — report, never crash the CLI.
        return ["Frontmatter YAML parse error: structure nested too deeply"]
    except MemoryError:
        # Best-effort: a very wide (non-aliased) structure. Aliases — the classic bomb — are
        # already refused at the loader above; and the OS OOM-killer may fire before CPython's
        # allocator raises, so this bounds the crash mode, not peak memory.
        return ["Frontmatter YAML parse error: structure expands too large"]
    if fm is None:
        return ["Frontmatter is not a mapping"]

    try:
        schema = load_schema()
    except (OSError, json.JSONDecodeError) as e:
        return [f"Schema load error: {e}"]
    validator = jsonschema.Draft202012Validator(schema)
    try:
        schema_errors = sorted(validator.iter_errors(fm), key=lambda e: list(e.path))
    except (RecursionError, MemoryError):
        # Defense-in-depth: the no-alias loader already blocks the known amplification vector
        # (jsonschema error reprs re-materializing an alias DAG); this catches any other
        # pathological structure that overflows the validator instead of crashing the CLI.
        return ["frontmatter: structure too complex to validate"]
    errors.extend(
        f"frontmatter{'.' + '.'.join(str(p) for p in err.path) if err.path else ''}: {err.message}"
        for err in schema_errors
    )

    for header in REQUIRED_HEADERS:
        if not any(line.startswith(header) for line in body.splitlines()):
            errors.append(f"body: missing required header '{header}'")

    if fm.get("verdict") == "refuted":
        # Iterate only a genuine list. A malformed scalar (e.g. `colliding_claims: 5`)
        # is already reported by the schema check above; guarding here keeps this
        # function's "always return, never raise" contract instead of crashing on
        # enumerate() — the exact class of input this validator exists to police.
        claims = fm.get("colliding_claims")
        if isinstance(claims, list):
            for i, claim in enumerate(claims):
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
