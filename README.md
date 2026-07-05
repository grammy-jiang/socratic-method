# socratic-method

A **Socratic questioning skill for coding agents** — Claude Code, OpenAI Codex, and
GitHub Copilot — packaged with a one-command installer and a deterministic artifact
validator.

Invoke the skill before real work starts (writing software, drafting a plan or document,
making a decision) and the agent becomes a disciplined questioner: it steelmans your idea,
interrogates it one question at a time (classic elenchus — six Socratic question types,
counterexamples, contradiction-surfacing by quoting your own words), and ends with an
honest verdict — **sharpened**, **aporia** (a genuinely unresolved hole, treated as a
finding), or **refuted** (only ever out of your own mouth). The result is written down as
a machine-validatable **idea brief** (`idea-brief-v1`) that downstream work can consume:
open questions become a research agenda, unvalidated assumptions become a validation
worklist.

The skill was authored and hardened in
[subagent-factory](https://github.com/grammy-jiang/subagent-factory): seven rounds of
grounded review plus a six-cell adversarial behavioral eval (examiner vs. scripted user
simulator, deterministic graders + independent judge), which caught and fixed real
behavior gaps static review missed. The eval harness ships in this repo under `evals/`.

## Install

```bash
pip install git+https://github.com/grammy-jiang/socratic-method
# or, without installing:
uvx --from git+https://github.com/grammy-jiang/socratic-method socratic-method --help
```

## Set up the skill for your agents

```bash
# auto-detect which agents are installed on this machine and configure those
socratic-method setup

# or name platforms explicitly / force all three
socratic-method setup claude codex
socratic-method setup all

# install into your user home instead of the current project
socratic-method setup claude --scope user

# see what would happen first / check current state / remove
socratic-method setup --dry-run
socratic-method status
socratic-method uninstall claude
```

With no targets, `setup` **auto-detects** installed agents and configures only those,
printing the concrete evidence for each detection (never a bare claim):

| Agent | Detection signals, in order |
|---|---|
| Claude Code | `claude` CLI on PATH; else `~/.claude/` config directory |
| OpenAI Codex | `codex` CLI on PATH; else `~/.codex/` config directory |
| GitHub Copilot | `copilot` CLI on PATH; else `gh-copilot` extension; else a `github.copilot*` VS Code extension |

If nothing is detected, `setup` installs nothing and tells you how to name targets
explicitly. `setup all` bypasses detection.

`setup` is **idempotent** (content-hash comparison; an identical install reports
"up to date"), refuses to overwrite locally modified files without `--force`, and after
every write **reads the files back from disk before reporting success** — the skill's own
"verify before claiming" rule, applied to its installer.

### Where the skill lands

| Platform | `--scope project` (default) | `--scope user` |
|---|---|---|
| Claude Code | `<root>/.claude/skills/socratic-method/` | `~/.claude/skills/socratic-method/` |
| OpenAI Codex | `<root>/.agents/skills/socratic-method/` | `~/.agents/skills/socratic-method/` |
| GitHub Copilot | `<root>/.github/skills/socratic-method/` | — |

Copilot also reads a repo's `.claude/skills/`, so if the Claude project install is already
present, the Copilot step reports "already covered" and skips (a duplicate would trigger
twice); `--force` installs to `.github/skills/` anyway. Paths live in one data-driven
registry (`installer.py`) — if a platform moves its skills directory, the fix is one line.

## Use the skill

In any agent with the skill installed:

> stress-test this plan: …
> help me think through …
> poke holes in this idea: …

Or invoke directly: `/socratic-method <idea> [--mode stress|develop] [--depth quick|standard|deep]`.
The session ends with the brief saved to `notes/idea-briefs/<slug>-YYYYMMDD.md`.

## Validate a brief

```bash
socratic-method validate notes/idea-briefs/my-idea-20260704.md
```

Checks the YAML frontmatter against the packaged `idea-brief-v1` JSON schema plus the
cross-field rules a schema can't express (e.g. `verdict: refuted` requires the two
colliding claims verbatim in the body; `verdict: aporia` requires open questions).

## Behavioral eval harness (`evals/`)

The six-cell regression matrix that hardened the skill: normal cells (planted
contradiction → refuted; genuine unknowns → aporia; quick-depth cadence), edge cells
(mid-session stop; disputed restatement), and an out-of-scope cell (fully specified plan →
decline). Each cell runs a live examiner against a scripted user simulator, then grades
the transcript with deterministic graders and an independent model judge.

```bash
python evals/run_eval.py --dry-run     # list cells, no calls
python evals/run_eval.py --cell O1     # one cell
python evals/run_eval.py               # full matrix — spawns ~30-60 headless `claude` calls
```

Requires the `claude` CLI and real tokens; run cells individually while iterating. A cell
passes only when **all** deterministic graders pass AND the judge confirms the expected
behavior with no fabrication.

## Development

```bash
uv sync                      # or: pip install -e . && pip install pytest
uv run pytest                # validator negatives, installer + detection behavior, CLI smoke
uv run pre-commit install    # one tool per file type: ruff (py), syntax checks (yaml/json/toml), actionlint
```

CI (`.github/workflows/ci.yml`) runs the test suite on Python 3.11–3.13, builds the
sdist/wheel, checks metadata, and smoke-tests the CLI installed from the built wheel.

## Releasing to PyPI

Publishing uses **PyPI Trusted Publishing** (OIDC) — no API token lives in the repo.
One-time setup on pypi.org: *Account → Publishing → Add a new pending publisher* with
project `socratic-method`, owner `grammy-jiang`, repository `socratic-method`, workflow
`release.yml`, environment `pypi`. Then, to release:

1. Bump `__version__` in `src/socratic_method/__init__.py`.
2. Push an annotated tag `vX.Y.Z` on master (must match `__version__` — the workflow
   verifies): `git tag -a vX.Y.Z -m "..." && git push origin vX.Y.Z`.
3. `release.yml` builds and checks the distributions, creates the GitHub Release with
   the wheel and sdist attached, and publishes to PyPI; the package appears at
   `pypi.org/project/socratic-method/`, after which `pip install socratic-method` works.

From an environment that cannot push tags (e.g. a Claude Code remote session, whose git
proxy rejects `refs/tags` pushes): dispatch the **Tag release** workflow to create the
annotated tag server-side, then dispatch **Release** with `ref` set to the new tag —
tags created with the Actions `GITHUB_TOKEN` do not fire tag-push events on their own.

Maintenance rule inherited from the skill's history: a behavioral failure is not fixed
until something durable changes — a grader, a scenario, or a rail in `SKILL.md` — never a
prose spot-fix alone.

## License

MIT
