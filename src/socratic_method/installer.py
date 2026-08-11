"""Install/inspect/remove the socratic-method skill for coding-agent platforms.

Design rules (inherited from the skill's own eval-hardened history):

- **Symlink by default.** ``install`` creates soft links to the packaged assets, so
  upgrading the package updates every install automatically. ``copy=True`` (CLI
  ``--copy``) writes real file copies instead, and any target where a symlink cannot
  be created (no durable asset path, or an OS that forbids symlinks) silently falls
  back to a copy of the same content.
- **Idempotent.** Every managed file is compared by content before writing;
  an identical install is reported "up to date", never rewritten.
- **Never clobber local edits silently.** A file that differs from the packaged
  version requires ``force=True`` to overwrite.
- **Verify before claiming.** After writing, every file is read back from disk
  (through the link, for symlinks) and compared to the packaged content;
  "installed" is only reported when the read-back matches. A claimed install with
  no verified file is the failure mode this skill exists to prevent.

Platform skill directories (data-driven so corrections are one-line; each claim below is
traceable to the vendor doc cited at the end of this docstring, not to prior research):

- Claude Code: ``.claude/skills/`` (project) and ``~/.claude/skills/`` (user).
- OpenAI Codex: ``.agents/skills/`` (project) and ``~/.agents/skills/`` (user) —
  Codex scans the open Agent Skills directory, not ``.claude/skills``.
- GitHub Copilot: ``.github/skills/`` (project) and ``~/.copilot/skills/`` (user).
  Copilot reads *three* project directories (``.github/skills``, ``.claude/skills``,
  ``.agents/skills``) and two personal ones (``~/.copilot/skills``,
  ``~/.agents/skills``), so a Claude *or* Codex install can already cover it; see
  ``Platform.covered_by_*`` and ``covering_install``.

Sources, verified 2026-08-11: developers.openai.com/codex/skills,
docs.github.com Copilot CLI + cloud-agent "add skills", and
code.visualstudio.com/docs/agent-customization/agent-skills.
"""

from __future__ import annotations

import contextlib
import hashlib
import os
import shutil
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from . import SKILL_NAME

# Relative paths (within the skill directory) of every file this installer manages.
MANAGED_FILES = (
    "SKILL.md",
    "references/example-session.md",
    "idea-brief-v1.schema.json",
    "agents/openai.yaml",  # Codex invocation policy; inert on other platforms
)


@dataclass(frozen=True)
class Platform:
    key: str
    label: str
    project_dir: str  # relative to --root
    user_dir: str | None  # relative to ~; None = no user scope documented
    # Other platform keys whose install directory this platform also reads, per
    # scope. An up-to-date install for any of them already covers this one, so
    # installing again would register the skill twice with the same agent.
    # Kept per-scope because coverage is not symmetric: every Copilot surface
    # reads a repo's .claude/skills, but GitHub's own CLI and cloud-agent docs
    # list only ~/.copilot/skills and ~/.agents/skills for personal skills.
    covered_by_project: tuple[str, ...] = ()
    covered_by_user: tuple[str, ...] = ()

    def dir_for(self, scope: str) -> str | None:
        """Skills directory for a scope, relative to --root or ~. None = no such scope."""
        if scope == "project":
            return self.project_dir
        if scope == "user":
            return self.user_dir
        raise ValueError(f"unknown scope '{scope}'")

    def covered_by(self, scope: str) -> tuple[str, ...]:
        return self.covered_by_project if scope == "project" else self.covered_by_user


PLATFORMS: dict[str, Platform] = {
    "claude": Platform(
        key="claude",
        label="Claude Code",
        project_dir=".claude/skills",
        user_dir=".claude/skills",
    ),
    "codex": Platform(
        key="codex",
        label="OpenAI Codex",
        project_dir=".agents/skills",
        user_dir=".agents/skills",
    ),
    "copilot": Platform(
        key="copilot",
        label="GitHub Copilot",
        project_dir=".github/skills",
        user_dir=".copilot/skills",
        # Project skills: .github/skills, .claude/skills, .agents/skills.
        # Personal skills: ~/.copilot/skills, ~/.agents/skills. VS Code also lists
        # ~/.claude/skills, but the Copilot CLI and cloud-agent docs do not — so
        # claude does NOT cover copilot at user scope, or a Copilot CLI user would
        # silently end up with no skill at all.
        covered_by_project=("claude", "codex"),
        covered_by_user=("codex",),
    ),
}


def detect_platforms(home: Path, path_env: str | None = None) -> dict[str, str | None]:
    """Detect which agents are installed on this machine.

    Returns ``{platform_key: evidence_or_None}`` — evidence is the concrete signal
    found (a CLI on PATH, a config directory, an editor extension), so every claimed
    detection is verifiable. ``path_env`` overrides the PATH searched (for tests).
    """

    def which(cmd: str) -> str | None:
        return shutil.which(cmd, path=path_env)

    evidence: dict[str, str | None] = {}

    if exe := which("claude"):
        evidence["claude"] = f"claude CLI on PATH ({exe})"
    elif (home / ".claude").is_dir():
        evidence["claude"] = f"config directory {home / '.claude'}"
    else:
        evidence["claude"] = None

    if exe := which("codex"):
        evidence["codex"] = f"codex CLI on PATH ({exe})"
    elif (home / ".codex").is_dir():
        evidence["codex"] = f"config directory {home / '.codex'}"
    else:
        evidence["codex"] = None

    if exe := which("copilot"):
        evidence["copilot"] = f"copilot CLI on PATH ({exe})"
    elif (home / ".copilot").is_dir():
        evidence["copilot"] = f"config directory {home / '.copilot'}"
    elif (home / ".local/share/gh/extensions/gh-copilot").is_dir():
        evidence["copilot"] = "gh-copilot extension installed"
    elif vsix := _copilot_extension(home):
        evidence["copilot"] = f"editor extension {vsix.parent.parent.name}/{vsix.name}"
    else:
        evidence["copilot"] = None

    return evidence


# Extension roots of the VS Code family, in the order they are reported. Stable
# release first; Insiders, the remote/server install and VSCodium follow, since a
# machine with only one of those still has Copilot available.
_VSCODE_EXTENSION_DIRS = (
    ".vscode/extensions",
    ".vscode-insiders/extensions",
    ".vscode-server/extensions",
    ".vscode-oss/extensions",
    ".vscodium/extensions",
)


def _copilot_extension(home: Path) -> Path | None:
    """Newest installed ``github.copilot*`` extension across the VS Code family."""
    for rel in _VSCODE_EXTENSION_DIRS:
        try:
            found = sorted((home / rel).glob("github.copilot*"))
        except OSError:
            continue  # unreadable dir: absence of evidence, not a reason to crash setup
        if found:
            return found[-1]
    return None


def packaged_content(rel: str) -> bytes:
    return files("socratic_method").joinpath(f"assets/{rel}").read_bytes()


def asset_path(rel: str) -> Path | None:
    """Durable filesystem path of a packaged asset, or None if there isn't one.

    Symlinks need a real, stable file to point at. A normal wheel/editable install
    provides one; an importer that only exposes assets virtually (e.g. a zipapp)
    does not — returning None there makes ``install`` fall back to copying.
    """
    traversable = files("socratic_method").joinpath(f"assets/{rel}")
    try:
        path = Path(os.fspath(traversable))  # type: ignore[arg-type]
    except TypeError:
        return None
    return path if path.is_file() else None


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def skill_dir(platform: Platform, scope: str, root: Path, home: Path) -> Path:
    """Resolve the target skill directory for a platform+scope."""
    rel = platform.dir_for(scope)  # raises on an unknown scope
    if rel is None:
        raise ValueError(
            f"{platform.label} has no documented user-scope skills directory; use --scope project"
        )
    return (root if scope == "project" else home) / rel / SKILL_NAME


_MANUAL_ONLY_KEY = "disable-model-invocation"

_WORKAROUND_BANNER = """\
# COPILOT CLI WORKAROUND INSTALL — this copy is NOT the packaged skill.
# `disable-model-invocation` has been removed, because GitHub Copilot CLI drops skills
# that carry it entirely: even an explicit /socratic-method returned "Skill not found"
# while `copilot skill list` still showed the skill. Reported as
# github/copilot-cli#4438; Claude Code, VS Code Copilot and Codex are unaffected.
# The cost of this workaround: on THIS install the model may auto-invoke the skill.
# Reinstall without --copilot-cli-workaround once the upstream bug is fixed.
"""


def cli_workaround_content(rel: str) -> bytes:
    """Packaged content with the manual-only key removed, for the Copilot CLI workaround.

    GitHub Copilot CLI 1.0.79 drops a skill carrying ``disable-model-invocation``
    entirely — even an explicit ``/socratic-method`` returns ``Skill not found``, while
    ``copilot skill list`` still shows it. That contradicts GitHub's own bundled docs
    (``disable-model-invocation: true`` => slash command yes, auto-load no) and its own
    SDK 1.0.39, which resolves explicit invocations against the *unfiltered* skill list.
    It is a regression, reported as github/copilot-cli#4438, and it affects the CLI only —
    Claude Code, VS Code Copilot and Codex all behave correctly.

    Removing the key restores reachability at the cost of the guarantee: on that install
    the model may auto-invoke the skill. Hence opt-in, never a default.
    """
    content = packaged_content(rel)
    if rel != "SKILL.md":
        return content
    text = content.decode("utf-8")
    head, fence, body = text.partition("\n---\n")  # frontmatter only; never touch the body
    lines = head.splitlines()
    key = next(
        (i for i, ln in enumerate(lines) if ln.startswith(f"{_MANUAL_ONLY_KEY}:")),
        None,
    )
    if key is None:  # key already absent — nothing to work around
        return content
    # Take the contiguous comment block directly above the key with it. Those comments
    # exist to explain that key; leaving prose describing a key the file no longer has
    # is its own kind of lie. Structural rather than keyword-matched, so rewording the
    # comments cannot silently orphan half of them.
    start = key
    while start > 0 and lines[start - 1].lstrip().startswith("#"):
        start -= 1
    kept = lines[:start] + _WORKAROUND_BANNER.splitlines() + lines[key + 1 :]
    return ("\n".join(kept) + fence + body).encode("utf-8")


def file_state(target: Path, rel: str) -> str:
    """One managed file's state: 'missing' | 'up-to-date' | 'differs'.

    A file matching the CLI-workaround variant counts as up-to-date: it is a supported
    install shape, not a local edit, so `status` must not cry "modified" at it and the
    next `setup` must not need --force.
    """
    dst = target / rel
    try:
        if not dst.is_file():
            return "missing"
        current = dst.read_bytes()
    except OSError:
        # is_file() and read_bytes() both propagate a PermissionError (e.g. an unreadable
        # parent dir). Treat that as differing so status() can report it and install()
        # routes through --force — never an uncaught OSError that crashes every caller.
        return "differs"
    digest = _digest(current)
    if digest == _digest(packaged_content(rel)):
        return "up-to-date"
    return "up-to-date" if digest == _digest(cli_workaround_content(rel)) else "differs"


def install_state(target: Path) -> str:
    """Whole-install state: 'not-installed' | 'up-to-date' | 'partial-or-modified'."""
    states = {rel: file_state(target, rel) for rel in MANAGED_FILES}
    if all(s == "missing" for s in states.values()):
        return "not-installed"
    if all(s == "up-to-date" for s in states.values()):
        return "up-to-date"
    return "partial-or-modified"


def has_leftovers(target: Path) -> bool:
    """Any managed path present as a symlink (including a dangling one, which reads as
    'missing' to file_state) — i.e. is there anything on disk for uninstall to sweep,
    independent of whether it is a valid content install."""
    try:
        return any((target / rel).is_symlink() for rel in MANAGED_FILES)
    except OSError:
        # Can't tell (e.g. an unreadable parent dir): assume cleanup may be needed;
        # uninstall()'s own unlink guard surfaces any real failure as "blocked".
        return True


def covering_install(
    platform: Platform, scope: str, root: Path, home: Path
) -> tuple[Platform, Path] | None:
    """The first up-to-date install by another platform that already covers this one.

    Returns ``(covering_platform, its_target)``, or None when nothing covers it. One
    source for both install()'s dedupe and status()'s report, so the write side and the
    read side never disagree. Coverage itself is data on ``Platform`` (``covered_by_*``).
    """
    for key in platform.covered_by(scope):
        other = PLATFORMS[key]
        if other.dir_for(scope) is None:  # no such scope for the covering platform
            continue
        other_target = skill_dir(other, scope, root, home)
        if install_state(other_target) == "up-to-date":
            return other, other_target
    return None


def _resolve_platform(platform_key: str) -> Platform:
    """Look up a platform, raising ValueError (the module's convention for a bad argument,
    which cli.py catches) instead of a raw KeyError for an unknown key."""
    try:
        return PLATFORMS[platform_key]
    except KeyError:
        raise ValueError(
            f"unknown platform '{platform_key}' (choose from {', '.join(PLATFORMS)})"
        ) from None


# Every value Action.outcome can take — the single source of truth cli.py renders from.
OUTCOMES = (
    "installed",
    "up-to-date",
    "skipped",
    "would-install",
    "would-remove",
    "blocked",
    "removed",
    "not-installed",
    "partial-or-modified",
)


@dataclass
class Action:
    platform: str
    scope: str
    target: Path
    outcome: str  # one of OUTCOMES
    detail: str = ""

    def __post_init__(self) -> None:
        # OUTCOMES is the single source of truth; catch a new/renamed outcome that forgot
        # to update it (which would otherwise render as "?" in cli with no test failing).
        assert self.outcome in OUTCOMES, f"outcome {self.outcome!r} not in OUTCOMES"


def install(
    platform_key: str,
    scope: str,
    root: Path,
    home: Path,
    *,
    force: bool = False,
    dry_run: bool = False,
    copy: bool = False,
    cli_workaround: bool = False,
) -> Action:
    platform = _resolve_platform(platform_key)
    target = skill_dir(platform, scope, root, home)
    state = install_state(target)
    # The workaround rewrites SKILL.md, so it cannot be a symlink to the packaged asset —
    # writing through one would strip the key from the package itself, for every install.
    copy = copy or cli_workaround

    # Dedupe: another platform's install in the same scope may sit in a directory this
    # platform also reads, in which case installing again registers the skill twice with
    # the same agent. Name the platform that actually covered it — the printed detail has
    # to stay verifiable, not a bare claim. Applies ONLY when this platform is itself
    # absent (no install, no dangling leftovers): an already-installed or locally-modified
    # target must report its own state (up-to-date / blocked), matching status(), not be
    # masked as "skipped".
    if (
        not force
        and state == "not-installed"
        and not has_leftovers(target)
        and (covering := covering_install(platform, scope, root, home))
    ):
        other, other_target = covering
        return Action(
            platform_key,
            scope,
            target,
            "skipped",
            f"{platform.label} also reads {other.dir_for(scope)} — already covered by "
            f"{other_target} (use --force to install to {target} anyway)",
        )

    if state == "up-to-date" and not force:
        # force still rewrites an up-to-date install: it is the way to switch an
        # install between symlink and copy mode (same content, different mechanism).
        return Action(
            platform_key, scope, target, "up-to-date", "all files match the packaged version"
        )
    if state == "partial-or-modified" and not force:
        differing = [rel for rel in MANAGED_FILES if file_state(target, rel) == "differs"]
        return Action(
            platform_key,
            scope,
            target,
            "blocked",
            f"existing install differs from packaged version "
            f"({', '.join(differing) or 'partial'}); re-run with --force to overwrite",
        )
    if dry_run:
        mode = "copies" if copy else "symlinks"
        note = ", disable-model-invocation stripped" if cli_workaround else ""
        return Action(
            platform_key,
            scope,
            target,
            "would-install",
            f"{len(MANAGED_FILES)} files ({mode}){note}",
        )

    linked, copied = [], []
    for rel in MANAGED_FILES:
        dst = target / rel
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            # Remove any existing file OR stale/dangling symlink first — writing through
            # a pre-existing link would modify the package's own asset, never the install.
            dst.unlink(missing_ok=True)
            src = None if copy else asset_path(rel)
            if src is not None:
                try:
                    dst.symlink_to(src)
                    linked.append(rel)
                    continue
                except OSError:  # e.g. a filesystem/OS that forbids symlinks
                    pass
            dst.write_bytes(
                cli_workaround_content(rel) if cli_workaround else packaged_content(rel)
            )
            copied.append(rel)
        except OSError as e:
            # A path occupied by an incompatible node (a directory where a file must go,
            # a file where references/ must go) must degrade to a reported failure, not a
            # bare traceback mid-loop. Name what was already written so "blocked" is not
            # misread as "nothing happened".
            written = linked + copied
            done = f" ({len(written)} already written: {', '.join(written)})" if written else ""
            return Action(
                platform_key, scope, target, "blocked", f"write failed for {rel}: {e}{done}"
            )

    # Verify before claiming: read back every file (through the link) from disk.
    unverified = [rel for rel in MANAGED_FILES if file_state(target, rel) != "up-to-date"]
    if unverified:
        return Action(
            platform_key,
            scope,
            target,
            "blocked",
            f"post-write verification FAILED for: {', '.join(unverified)}",
        )
    parts = []
    if linked:
        parts.append(f"{len(linked)} symlinked")
    if copied:
        parts.append(f"{len(copied)} copied")
    note = (
        " — disable-model-invocation STRIPPED for the Copilot CLI bug (#4438): the skill "
        "is reachable there again, but the model may now auto-invoke it"
        if cli_workaround
        else ""
    )
    return Action(
        platform_key,
        scope,
        target,
        "installed",
        f"{' + '.join(parts)}, read back and verified{note}",
    )


def uninstall(
    platform_key: str, scope: str, root: Path, home: Path, *, dry_run: bool = False
) -> Action:
    """Revert an install (CLI: ``remove``, with ``uninstall`` kept as an alias)."""
    platform = _resolve_platform(platform_key)
    target = skill_dir(platform, scope, root, home)
    # Dangling symlinks read as 'missing' to install_state; still clean them up.
    if install_state(target) == "not-installed" and not has_leftovers(target):
        return Action(platform_key, scope, target, "not-installed")
    if dry_run:
        return Action(platform_key, scope, target, "would-remove", "would remove managed files")
    for rel in MANAGED_FILES:
        try:
            (target / rel).unlink(missing_ok=True)
        except OSError as e:
            # Mirror install()'s guard: a permission error on one platform must not abort
            # the others when `remove` (no targets) expands to all of them.
            return Action(platform_key, scope, target, "blocked", f"remove failed for {rel}: {e}")
    # Remove now-empty directories we own, innermost first.
    for d in sorted({(target / rel).parent for rel in MANAGED_FILES} | {target}, reverse=True):
        with contextlib.suppress(OSError):  # not empty — user files present; leave them
            d.rmdir()
    return Action(platform_key, scope, target, "removed")


def status(root: Path, home: Path) -> list[Action]:
    out = []
    for key, platform in PLATFORMS.items():
        for scope in ("project", "user"):
            if scope == "user" and platform.user_dir is None:
                continue
            target = skill_dir(platform, scope, root, home)
            state = install_state(target)
            # Reflect install()'s dedupe: a not-installed target (with no dangling
            # leftovers) that another platform's install already covers is "skipped", not
            # "not-installed" — so status (read side) agrees with what setup would report.
            if (
                state == "not-installed"
                and not has_leftovers(target)
                and (covering := covering_install(platform, scope, root, home))
            ):
                out.append(Action(key, scope, target, "skipped", f"covered by {covering[1]}"))
                continue
            out.append(Action(key, scope, target, state))
    return out
