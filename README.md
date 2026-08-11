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

- **Meant to be invoked by hand, never auto-triggered** (`/socratic-method …` in Claude
  Code and Copilot, `$socratic-method` in Codex); it costs zero context tokens until
  invoked. If it seems inactive, that is by design — invoke it explicitly rather than
  rephrasing the prompt to bait it. **How that is enforced differs per platform, and it
  is not airtight on Copilot** — see
  [How manual-only is enforced](#how-manual-only-is-enforced-per-platform) before relying
  on it.
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
| GitHub Copilot | `copilot` CLI on PATH; else `~/.copilot/` config directory; else `gh-copilot` extension; else a `github.copilot*` extension under `~/.vscode`, `~/.vscode-insiders`, `~/.vscode-server`, `~/.vscode-oss` or `~/.vscodium` |

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
| GitHub Copilot | `<root>/.github/skills/socratic-method/` | `~/.copilot/skills/socratic-method/` |

Copilot is the one platform that reads *other* agents' directories, so installing it on top
of another install would register the skill twice with the same agent. The installer skips
in that case and names the covering install in its output; `--force` installs anyway:

| Scope | Copilot also reads | So it is skipped when installed for |
|---|---|---|
| project | `.claude/skills/`, `.agents/skills/` | Claude Code **or** Codex |
| user | `~/.agents/skills/` | Codex only |

`~/.claude/skills/` is deliberately *not* treated as covering Copilot at user scope: VS Code
lists it, but GitHub's Copilot CLI and cloud-agent docs do not, and skipping there would
leave a Copilot CLI user with no skill at all. Paths and coverage live in one data-driven
registry (`installer.py`) — if a platform moves its skills directory, the fix is one line.

## Use the skill

The skill is **manual-invocation-only**: it should never auto-trigger on phrasing, and it
costs zero context tokens until you call it. Invoke it explicitly:

```text
/socratic-method <idea> [--mode stress|develop] [--depth quick|standard|deep]   # Claude Code
Use the /socratic-method skill to <idea>, --mode stress --depth deep            # GitHub Copilot
$socratic-method <idea> --mode stress --depth deep                              # Codex ($ mention)
```

`--mode` and `--depth` are **not** parsed by any CLI — no agent has a flag parser for skill
arguments. They are conventions the model reads out of your prompt text, so any phrasing
that names them works. Copilot CLI also has `/skills list|info|reload` and a terminal-side
`copilot skill` subcommand; Codex has a `/skills` picker.

The session ends with the brief saved to `notes/idea-briefs/<slug>-YYYYMMDD.md`. A full
worked session — steelman restatement, contradiction-surfacing by verbatim quotation, a
refutation-vs-aporia contrast, and the resulting `idea-brief-v1` file — is in
[references/example-session.md](src/socratic_method/assets/references/example-session.md).

### How manual-only is enforced, per platform

Support is **not uniform**, and one platform has no mechanism at all. Verified
2026-08-11 against the sources linked below:

| Platform | Mechanism | Status |
|---|---|---|
| Claude Code | `disable-model-invocation: true` | Documented — [origin of the field](https://code.claude.com/docs/en/skills) |
| VS Code (Copilot) | `disable-model-invocation` + `user-invocable: true` | Supported per the [cross-agent survey](https://gist.github.com/zeke/0f654737ec01b20e9bf85d3cc0bc1c14); absent from [VS Code's own docs](https://code.visualstudio.com/docs/agent-customization/agent-skills) |
| Copilot CLI | `disable-model-invocation` | **Broken — the skill is unreachable.** Measured on CLI 1.0.79: the key removes the skill from the model entirely, so even an explicit `/socratic-method` returns `Skill not found`, while `copilot skill list` still shows it. [GitHub's docs](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills) never document the key. Tracked in [#18](https://github.com/grammy-jiang/socratic-method/issues/18); delete the line from your installed copy to use the skill there |
| Copilot cloud agent | none | **Known gap.** [The docs](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills) describe no user-only mechanism, so it may still pick the skill autonomously |
| OpenAI Codex | `agents/openai.yaml` → `policy.allow_implicit_invocation: false` | Documented — [Codex skills](https://developers.openai.com/codex/skills); "explicit `$skill` invocation still works" |

`disable-model-invocation` is not part of the [agentskills.io](https://agentskills.io) open
spec (which defines `name`, `description`, and optionally `license`, `compatibility`,
`metadata`, `allowed-tools`). It is a client extension several agents converged on — which
is why the guarantee has to be stated per platform rather than claimed once.

Note also that `allowed-tools` is a *restriction* on Claude Code but a **pre-approval**
list on Copilot, where listed tools skip the confirmation prompt. The shipped value is
`AskUserQuestion, Read, Write`; a test in the package repository pins that it can never
grow a shell/bash-family tool.

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

**This matrix measures Claude Code only** — it drives `claude -p`, parses Claude's
stream-json, and installs into `.claude/skills`. Treat a green matrix as evidence about
Claude Code, never as evidence about Codex or Copilot.

### Cross-platform smoke tier (`evals/run_smoke.py`)

The cheap complement: two probes per platform, checking the *contract* rather than the
behavior — (1) an explicit invocation loads `SKILL.md` from the directory this installer
writes to, and (2) a prompt matching the skill's description does **not** auto-invoke it.

```bash
python evals/run_smoke.py --dry-run           # list the plan, no calls
python evals/run_smoke.py --platform codex    # one platform (repeatable)
python evals/run_smoke.py --model claude=sonnet   # override one platform's model
python evals/run_smoke.py                     # every platform whose CLI is on PATH
```

Needs each platform's CLI authenticated; 2 headless calls per platform. Probe outcomes:

| | |
|---|---|
| `PASS` / `FAIL` | the probe ran and the contract held / did not |
| `ERROR` | the CLI never reached the model (spend limit, auth) — **not** a pass; the platform is simply unverified, and calling that success is the fabrication mode this project exists to prevent |
| `XFAIL` | a measured, upstream-reported breakage listed in `KNOWN_BREAKAGE` — does not fail the run |
| `XPASS` | a known breakage that now passes — **does** fail the run, because the docs describing it have gone stale and must be removed |

Today one entry is expected-broken: Copilot CLI discovery, tracked in
[#18](https://github.com/grammy-jiang/socratic-method/issues/18) and
[github/copilot-cli#4438](https://github.com/github/copilot-cli/issues/4438). Like the rest
of `evals/`, this must never run in CI.

It does **not** grade questioning behavior — no turn discipline, no stop signal, no verdict
honesty. Those need a scripted multi-turn simulator and stay in `run_eval.py`.

## Contributing

Development setup, the test/lint loop, and the PyPI release process live in
[CONTRIBUTING.md](CONTRIBUTING.md). Start with [CLAUDE.md](CLAUDE.md) (the authoritative
agent guide) before any non-trivial change.

## License

MIT
