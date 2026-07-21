# socratic-method

[![CI](https://github.com/grammy-jiang/socratic-method/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/grammy-jiang/socratic-method/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/socratic-method)](https://pypi.org/project/socratic-method/)
[![Python](https://img.shields.io/pypi/pyversions/socratic-method)](https://pypi.org/project/socratic-method/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
![Agent skill](https://img.shields.io/badge/agent%20skill-Claude%20Code%20%7C%20Codex%20%7C%20Copilot-8A2BE2)
![Invocation](https://img.shields.io/badge/invocation-manual--only-orange)

A **Socratic questioning skill for coding agents** — Claude Code, OpenAI Codex, and
GitHub Copilot — packaged with a one-command installer and a deterministic artifact
validator.

Invoke the skill before real work starts (writing software, drafting a plan or document,
making a decision) and the agent becomes a disciplined questioner: it steelmans your idea,
interrogates it one question at a time (classic elenchus — six Socratic question types,
counterexamples, contradiction-surfacing by quoting your own words), and ends with an
honest verdict — **sharpened**, **aporia** (a genuinely unresolved hole, treated as a
finding), **refuted** (only ever out of your own mouth), or **accepted-as-is** (an
already-precise idea recorded without questioning). The result is written down as
a machine-validatable **idea brief** (`idea-brief-v1`), a point-in-time snapshot the next
step can pick up: its open questions seed a research agenda, its unvalidated assumptions a
validation checklist.

The skill was authored and hardened in
[subagent-factory](https://github.com/grammy-jiang/subagent-factory): seven rounds of
grounded review plus a seven-cell adversarial behavioral eval (examiner vs. scripted user
simulator, deterministic graders + independent judge), which caught and fixed real
behavior gaps static review missed. The eval harness ships in this repo under `evals/`.

## Why use it

A before/after (abridged) — a fuzzy engineering idea, tightened in one pass:

> **You:** "We should add a caching layer to speed up the API."
> **Skill:** "Speed up which calls, and what's slow about them today — the database, a
> downstream service, or serialization? Measured how?"
> **You:** "…honestly I haven't profiled it. It just feels slow."
> **Skill → `verdict: aporia`:** the load-bearing question isn't *which cache* but *where the
> latency actually is.* The brief's next step: profile the hot path before designing anything
> — a cache on the wrong layer would add complexity and hide the real cost.

**Why not just type "poke holes in this" into any chat?** For a quick gut-check, do exactly
that. What this packages is what an ad-hoc prompt tends to drop under pressure: a forced
one-question-at-a-time cadence at standard depth (so you can't skim past the hard one), refutation drawn *only*
from your own quoted words (never the agent's opinion), and a durable, schema-validated brief
the next step can pick up — instead of a scrollback you'll lose.

## For AI agents

This README is written for you too. The 30-second version:

```bash
pipx install socratic-method  # from PyPI; pip works too but pipx isolates the CLI
socratic-method setup         # auto-detects Claude Code / Codex / Copilot; exits 1 if none detected
socratic-method status        # verify what landed where before claiming success
```

Special properties to know before acting:

- **Manual-invocation only** (`/socratic-method …` in Claude Code and Copilot,
  `$socratic-method` in Codex), and it costs zero context tokens until invoked. This is
  enforced where the platform supports it — Claude Code, Codex, and Copilot's VS Code/CLI
  surfaces. **One known gap:** GitHub's *cloud* Copilot coding agent documents no user-only
  mechanism, so it may still pick the skill on its own. On the enforced surfaces, if it
  seems inactive that is by design — invoke it explicitly rather than rephrasing to bait it.
- **Output contract:** a session must end with a brief at
  `notes/idea-briefs/<slug>-YYYYMMDD.md` that passes
  `socratic-method validate <file>` (exit 0 = valid; exit 1 prints `ERROR:` lines).
- **Installer semantics:** `setup` symlinks the skill from the installed package by
  default (`--copy` for real copies); it is idempotent and refuses to overwrite a
  locally modified install without `--force`. `remove` (alias `uninstall`) reverts
  what setup did — careful: with no targets it removes the skill for ALL platforms,
  including locally modified copies.
- **Never hand-edit an installed copy** (e.g. `.claude/skills/socratic-method/`). A
  default install is a *symlink*, so an edit writes straight through to the packaged
  asset — corrupting the source for every install while the install still reports
  `up-to-date`; a `--copy` install instead flips to `partial-or-modified` and blocks
  future `setup` runs. Either way, edit the canonical source at
  `src/socratic_method/assets/` in this repo, never the installed path.
- Working on this repository itself? Read [CLAUDE.md](CLAUDE.md) (authoritative agent
  guide) or [AGENTS.md](AGENTS.md) (summary) first: the idea-brief format is enforced
  in lockstep across six files, and the shipped `SKILL.md` must never be reformatted.

## Install

```bash
pipx install socratic-method    # recommended
# or run it one-off without installing anything:
uvx socratic-method --help
# or plain pip, into whatever environment is currently active:
pip install socratic-method
```

Prefer [pipx](https://pipx.pypa.io/): `socratic-method` is a command-line tool, not a
library you import, and pipx installs it into its own isolated virtualenv with just the
`socratic-method` command on your PATH — its dependencies can never conflict with a
project's, and `pipx upgrade socratic-method` upgrades it cleanly. All of the commands
above install the released package from [PyPI](https://pypi.org/project/socratic-method/);
the same wheel and sdist are attached to each
[GitHub Release](https://github.com/grammy-jiang/socratic-method/releases).

## Set up the skill for your agents

```bash
# auto-detect which agents are installed on this machine and configure those
socratic-method setup

# or name platforms explicitly / force all three
socratic-method setup claude codex
socratic-method setup all

# install into your user home instead of the current project
socratic-method setup claude --scope user

# see what would happen first / check current state / revert
socratic-method setup --dry-run
socratic-method status
socratic-method remove claude        # alias: uninstall
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

`setup` creates **symlinks** to the packaged assets by default, so upgrading the package
(`pipx upgrade socratic-method`) updates every install automatically and nothing is
duplicated on disk. Use `--copy` for real file copies instead — e.g. when you commit the
skill directory into a repo (a symlink into your local environment is useless to
collaborators), when you want to customize the installed copy (editing *through* a
symlink would edit the packaged version for every install), or on filesystems without
symlink support (where the installer falls back to copies automatically). Switch an
existing install between modes with `setup --force [--copy]`. `remove` reverts whatever
`setup` created — links or copies, dangling links included.

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

The skill is **manual-invocation-only**: it never auto-triggers on phrasing, and it costs
zero context tokens until you call it. Invoke it explicitly:

```text
/socratic-method <idea> [--mode stress|develop] [--depth quick|standard|deep]   # Claude Code, Copilot
$socratic-method <idea> ...                                                     # Codex ($ mention)
```

The session ends with the brief saved to `notes/idea-briefs/<slug>-YYYYMMDD.md`. A full
worked session — steelman restatement, contradiction-surfacing by verbatim quotation, a
refutation-vs-aporia contrast, and the resulting `idea-brief-v1` file — is in
[references/example-session.md](src/socratic_method/assets/references/example-session.md).

This is enforced by `disable-model-invocation: true` in the skill frontmatter (Claude
Code; Copilot VS Code agent mode and CLI) and by the `agents/openai.yaml` sidecar with
`policy.allow_implicit_invocation: false` (Codex ignores the frontmatter key). One known
gap: GitHub's cloud coding agent documents no user-only mechanism, so it may still pick
the skill autonomously.

## Validate a brief

```bash
socratic-method validate notes/idea-briefs/my-idea-20260704.md
```

Checks the YAML frontmatter against the packaged `idea-brief-v1` JSON schema plus the
cross-field rules a schema can't express (e.g. `verdict: refuted` requires the two
colliding claims verbatim in the body; `verdict: aporia` requires open questions).

## Behavioral eval harness (`evals/`)

The seven-cell regression matrix that hardened the skill: normal cells (planted
contradiction → refuted; genuine unknowns → aporia; quick-depth cadence; a concrete-falsifier
stress pass), edge cells (mid-session stop; disputed restatement), and an out-of-scope cell
(fully specified plan → decline). Each cell runs a live examiner against a scripted user simulator, then grades
the transcript with deterministic graders and an independent model judge.

```bash
python evals/run_eval.py --dry-run     # list cells, no calls
python evals/run_eval.py --cell O1     # one cell
python evals/run_eval.py               # full matrix — spawns ~30-60 headless `claude` calls
```

Requires the `claude` CLI and real tokens; run cells individually while iterating. A cell
passes only when **all** deterministic graders pass AND the judge confirms the expected
behavior with no fabrication and no premature solutioning, AND the brief stayed inside its
sandbox (no harness leak).

## Contributing

Development setup, the test/lint loop, and the PyPI release process live in
[CONTRIBUTING.md](CONTRIBUTING.md). Start with [CLAUDE.md](CLAUDE.md) (the authoritative
agent guide) before any non-trivial change.

## License

MIT
