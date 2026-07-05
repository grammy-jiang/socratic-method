# AGENTS.md

Guide for AI coding agents working on this repository (Codex, Copilot, and others).

**The authoritative, detailed agent guide is [CLAUDE.md](CLAUDE.md) — read it before any
non-trivial change.** The essentials:

- `src/socratic_method/assets/SKILL.md` is the shipped product. Editing it invalidates
  every existing install's content hash and is instantly picked up by the eval harness.
  Never let a formatter touch it.
- The idea-brief format is enforced in lockstep across the JSON schema, the SKILL.md
  brief template, `validator.py`, the golden fixture in `evals/fixtures/`, the graders,
  and the mutation tests — change all of them together or none.
- Dev loop: `uv sync`, `uv run pytest -q`,
  `uvx pre-commit run --all-files --show-diff-on-failure`. All committed files need LF
  endings, no trailing whitespace, one final newline.
- The version lives only in `src/socratic_method/__init__.py` as
  `__version__ = "X.Y.Z"`; release tags are `v` + that string. Releases are tag-driven
  via `.github/workflows/release.yml`.
- Do not run the full eval matrix (`python evals/run_eval.py`) casually — it spawns
  ~30-60 live `claude` calls. Use `--dry-run` or `--cell`. Never add evals to CI.
- A behavioral failure is fixed by a durable change (grader, scenario, or SKILL.md
  rail), never a prose spot-fix alone.
