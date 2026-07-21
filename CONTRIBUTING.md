# Contributing to socratic-method

Working on this repository? Read [CLAUDE.md](CLAUDE.md) first — or [AGENTS.md](AGENTS.md)
for the short version — before any non-trivial change: the idea-brief format is enforced in
lockstep across several files, and the shipped `SKILL.md` must never be reformatted.

## Development

```bash
uv sync                      # or: pip install -e . && pip install pytest
uv run pytest -q             # validator negatives, installer + detection behavior, CLI smoke
uv run pre-commit install    # install the git hook: one tool per file type — ruff (py), syntax checks (yaml/json/toml), actionlint
uvx pre-commit run --all-files --show-diff-on-failure   # the exact lint sweep CI runs; do this before pushing
```

CI (`.github/workflows/ci.yml`) runs three parallel jobs: the pre-commit lint sweep, the
test suite on Python 3.11–3.14, and a build job that builds the sdist/wheel, checks
metadata, and smoke-tests the CLI installed from the built wheel.

## Releasing to PyPI

Publishing uses **PyPI Trusted Publishing** (OIDC) — no API token lives in the repo.
One-time setup on pypi.org: *Account → Publishing → Add a new pending publisher* with
project `socratic-method`, owner `grammy-jiang`, repository `socratic-method`, workflow
`release.yml`, environment `pypi`. Then, to release:

1. Bump `__version__` in `src/socratic_method/__init__.py`.
2. Push an annotated tag `vX.Y.Z` on master (must match `__version__` — the workflow
   verifies): `git tag -a vX.Y.Z -m "..." && git push origin vX.Y.Z`.
3. `release.yml` builds and checks the distributions, publishes to PyPI via Trusted
   Publishing, then creates the GitHub Release with the wheel and sdist attached. PyPI
   deliberately goes **first** and gates the Release — PyPI is immutable, so a failed
   publish never leaves a half-released state. The package then appears at
   `pypi.org/project/socratic-method/`, after which `pip install socratic-method` works.

From an environment that cannot push tags (e.g. a Claude Code remote session, whose git
proxy rejects `refs/tags` pushes): dispatch the **Tag release** workflow to create the
annotated tag server-side, then dispatch **Release** with `ref` set to the new tag —
tags created with the Actions `GITHUB_TOKEN` do not fire tag-push events on their own.

Maintenance rule inherited from the skill's history: a behavioral failure is not fixed
until something durable changes — a grader, a scenario, or a rail in `SKILL.md` — never a
prose spot-fix alone.
