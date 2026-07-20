# CLAUDE.md — agent guide for socratic-method

Pip-installable package `socratic-method`: a Socratic questioning skill for coding agents
(Claude Code, OpenAI Codex, GitHub Copilot) plus an installer CLI, a deterministic
idea-brief validator, and a behavioral eval harness. The skill was authored and hardened
in [subagent-factory](https://github.com/grammy-jiang/subagent-factory) but **lives
standalone here** — none of that repo's machinery (provenance ledgers, CHANGELOG-per-bump,
`tools/subagent_factory/`, `.claude/agents/generated/`) applies in this repo. The brief
validator here is `src/socratic_method/validator.py`.

**Core maintenance rule** (inherited from the skill's history): a behavioral failure is
not fixed until something durable changes — a grader, a scenario, or a rail in
`SKILL.md` — never a prose spot-fix alone.

## Layout

```text
src/socratic_method/           the package: cli.py, installer.py, validator.py
src/socratic_method/assets/    THE PRODUCT: SKILL.md, example-session, idea-brief schema
evals/                         6-cell behavioral eval harness (run_eval.py, graders, rubric)
evals/fixtures/                golden valid brief (load-bearing for tests + CI smoke)
tests/                         pytest suite (validator mutations, installer, detection, CLI, asset invocation-policy, eval graders)
.claude/skills/                maintainer skills for developing THIS repo (e.g. /release)
notes/                         gitignored; where the skill writes real briefs
```

`SKILL_NAME` and `__version__` live in `src/socratic_method/__init__.py`. Platform install
paths are data-driven in `installer.py`'s `PLATFORMS` dict; the managed files are
`MANAGED_FILES` = SKILL.md, references/example-session.md, idea-brief-v1.schema.json,
agents/openai.yaml.

The skill is **manual-invocation-only** by policy, encoded in two places that must stay
in sync (pinned by `tests/test_assets.py`): `disable-model-invocation: true` in SKILL.md
frontmatter (honored by Claude Code and by Copilot in VS Code agent mode + CLI; ignored
by Codex) and `agents/openai.yaml` with `policy.allow_implicit_invocation: false` (the
Codex equivalent; other platforms never read it). Known gap: the Copilot cloud coding
agent documents no user-only mechanism and may still auto-invoke.

## Dev loop

```bash
uv sync                                          # installs dev group (pytest, pre-commit)
uv run pytest -q                                 # what CI runs
uvx pre-commit run --all-files --show-diff-on-failure   # exact CI lint job; run before pushing
uv build && uvx twine check dist/*               # what the release build job runs
```

- Python floor is 3.11, kept in sync across four places: `requires-python`, the trove
  classifiers, the CI test matrix, and `[tool.ruff] target-version`.
- `uv.lock` is gitignored on purpose — do not commit a lockfile.
- Tests require a full repo checkout: the golden fixture path is defined once as
  `GOLDEN` in `tests/conftest.py` (which also puts `evals/` on `sys.path` so the pure
  eval graders can be unit-tested) and imported by test_validator/test_cli/test_graders.
- Pre-commit gates EVERY file you add, markdown included: LF endings, no trailing
  whitespace, exactly one final newline. One tool per file type is policy — never add a
  markdown formatter (it would reflow the shipped `SKILL.md`) or a second Python linter.
- Validator mutation tests pin exact error wording (including jsonschema's message text) —
  rewording a validator error string breaks `tests/test_validator.py`.

## The shipped skill asset (handle with care)

`src/socratic_method/assets/SKILL.md` is the deliverable users install. Editing it:

- changes the packaged sha256: copy-mode installs everywhere flip to
  `partial-or-modified` and their next `setup` returns `blocked` (exit 1) until
  `--force`, while symlinked installs (the default) see the edit immediately and
  keep reporting `up-to-date`;
- is immediately picked up by evals — `run_eval.py` copies the *working tree* assets into
  each cell's sandbox, so evals always test uncommitted edits;
- must never be reformatted by tooling (see pre-commit policy above).

Never commit an installed copy of the product skill into this repo's own
`.claude/skills/socratic-method/` — the canonical source is `assets/`; an installed copy
here would silently drift. This repo's `.claude/skills/` is for maintainer skills only.

CLI behavior worth remembering: `setup` symlinks the packaged assets by default
(`--copy` writes real copies; symlink failure auto-falls-back to a copy; `--force`
also switches an existing install between modes). `setup` with no targets auto-detects
and exits 1 if nothing is detected, but `remove` (canonical name; `uninstall` is the
alias) with no targets expands to ALL platforms — and removes managed files even if
locally modified, plus dangling symlinks. Copilot has no user scope (`user_dir=None`),
and project-scope Copilot is skipped when `.claude/skills/` already covers the repo
(Copilot reads that path too). Never write through an installed symlink in code or
tests — it edits the packaged asset itself (`install()` unlinks before writing for
exactly this reason; `tests/test_installer.py` pins it).

## Changing the idea-brief format = lockstep edit

`idea-brief-v1` is enforced in several places that must move together. Touch one, touch
all:

1. `src/socratic_method/assets/idea-brief-v1.schema.json` (frontmatter contract;
   `additionalProperties: false`, so new keys REQUIRE a schema change first)
2. `src/socratic_method/assets/SKILL.md` Phase 4 brief template
3. `src/socratic_method/validator.py` `REQUIRED_HEADERS` (body headers, matched by
   `startswith`; also imported by `evals/graders.py`)
4. `evals/fixtures/tech-talk-series-20260704.md` (golden fixture; referenced via
   `tests/conftest.py`'s `GOLDEN` constant from test_validator/test_cli/test_graders AND
   by literal path in the CI smoke step; also embedded verbatim in
   `references/example-session.md`, pinned by `test_assets.py`; its filename slug must
   equal its frontmatter `idea`)
5. `evals/graders.py` (brief markers and frontmatter-dependent graders)
6. `tests/test_validator.py` expected error substrings

A format change that breaks compatibility means a new `idea-brief-v2` schema file, not a
silent edit of v1 (the version lives in the `schema` const and the filename).

## Eval harness (`evals/`)

```bash
python evals/run_eval.py --dry-run      # list cells, zero model calls
python evals/run_eval.py --cell O1      # one cell (repeatable flag)
python evals/run_eval.py                # full matrix — ~30-60 headless `claude` calls
```

- Requires an authenticated `claude` CLI; model choice is flags-only
  (`--model`/`--sim-model`/`--judge-model`, defaults sonnet/sonnet/opus). No env vars.
- A cell passes only when all deterministic graders pass AND the judge reports
  `expected_behavior_met: true`, `fabrication: false`, and `premature_solutioning: false`,
  AND no harness sandbox leak was detected.
- **Never wire evals into CI** — real tokens plus LLM variance; CI runs lint, pytest, CLI
  smoke, and build only.
- Grader thresholds are calibrated, not arbitrary (e.g. `turn_discipline` fires at 3+ `?`;
  `session_claims_accurate` enforces deliberately loose bounds derived from a 0.50–0.82
  claimed/measured ratio observed on honest sessions) — do not "tighten" them to equality
  checks.
- Grader triggers and persona scripts are phrase-coupled: `stop_honored` keys on
  "that's enough"/"wrap up", `dispute_loop_honored` on "not quite". Edit a persona line
  and its grader together.
- The examiner tool grant is deliberately `--allowedTools Skill,Read,Write,Edit` — close
  to, but not identical to, SKILL.md's `allowed-tools` (which names AskUserQuestion, not
  Edit). Widening it changes what the eval measures.
- Adding a cell: drop a YAML into `evals/scenarios/` with `cell`, `name`, `mode`, `depth`,
  `invocation`, `persona`, `expected: {verdict, graders, judge_focus}`; optional
  `max_turns` (default 16) and the `expected_*` knobs are TOP-LEVEL keys, not nested under
  `expected:`. Every grader named must exist in `graders.GRADERS`.
- Reports: `evals/reports/<ts>/**/workdir/` is gitignored; the transcripts, grader/judge
  JSON, and summaries are committable on purpose — they are the evidence trail.
- Leak sweep footgun: when a cell ends with no brief inside its sandbox, a fresh
  `notes/idea-briefs/*.md` at repo root correlated to the cell is **copied** (never moved —
  the original stays in your `notes/`) into the report dir as `brief-leaked.md`, which is
  gitignored so a private brief can't be committed by accident.

## Versioning and releases

The version string lives ONLY in `src/socratic_method/__init__.py`, in the literal form
`__version__ = "X.Y.Z"` (double quotes, single spaces — `tag-release.yml` parses that
exact shape with sed). `pyproject.toml` uses `dynamic = ["version"]`; never add a static
`version =` there. A release tag is exactly `v` + that string; both release workflows
hard-fail on mismatch.

Normal release: bump `__version__`, then push an annotated tag from an environment that
can push tags — `git tag -a vX.Y.Z -m "..." && git push origin vX.Y.Z`. `release.yml`
builds, publishes to PyPI via Trusted Publishing, then attaches the wheel+sdist to a
GitHub Release — PyPI goes **first** and gates the Release (it is immutable, so a failed
publish must not leave a half-released state). Publishing is bound to workflow file
`release.yml` + environment `pypi` — renaming either breaks it until the PyPI publisher
config is updated.

From a Claude Code remote session the git proxy rejects `refs/tags` pushes — use the
dispatch fallback (details in `.claude/skills/release/SKILL.md`, invoke `/release`):
dispatch **Tag release** with the tag input, then dispatch **Release** with `ref` set to
the new tag. Two dispatches are always required (GITHUB_TOKEN-created tags never fire
tag-push events), and Release must be dispatched from the TAG ref, not a branch, or the
version check fails. PyPI uploads are immutable — a botched release means bumping the
patch version, not re-uploading.
