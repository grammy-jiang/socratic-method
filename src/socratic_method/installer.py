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

Platform skill directories (data-driven so corrections are one-line; grounded in the
platform research of the agent-skills-advisor corpus — see README for caveats):

- Claude Code: ``.claude/skills/`` (project) and ``~/.claude/skills/`` (user).
- OpenAI Codex: ``.agents/skills/`` (project) and ``~/.agents/skills/`` (user) —
  Codex scans the open Agent Skills directory, not ``.claude/skills``.
- GitHub Copilot: ``.github/skills/`` (project). Copilot also reads a repo's
  ``.claude/skills/``, so a project-scope Claude install already covers Copilot;
  the installer detects that and skips to avoid a double-triggering duplicate.
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
        user_dir=None,
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
    elif (home / ".local/share/gh/extensions/gh-copilot").is_dir():
        evidence["copilot"] = "gh-copilot extension installed"
    elif vsix := sorted((home / ".vscode" / "extensions").glob("github.copilot*")):
        evidence["copilot"] = f"VS Code extension {vsix[-1].name}"
    else:
        evidence["copilot"] = None

    return evidence


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
    if scope == "project":
        base = root / platform.project_dir
    elif scope == "user":
        if platform.user_dir is None:
            raise ValueError(
                f"{platform.label} has no documented user-scope skills directory; "
                "use --scope project"
            )
        base = home / platform.user_dir
    else:
        raise ValueError(f"unknown scope '{scope}'")
    return base / SKILL_NAME


def file_state(target: Path, rel: str) -> str:
    """One managed file's state: 'missing' | 'up-to-date' | 'differs'."""
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
    return "up-to-date" if _digest(current) == _digest(packaged_content(rel)) else "differs"


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


def _copilot_covered_by_claude(root: Path, home: Path) -> Path | None:
    """The Claude project-scope target that already covers a project-scope Copilot install
    (Copilot reads .claude/skills), or None. One source for both install()'s dedupe and
    status()'s report, so the write side and the read side never disagree."""
    claude_target = skill_dir(PLATFORMS["claude"], "project", root, home)
    return claude_target if install_state(claude_target) == "up-to-date" else None


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
) -> Action:
    platform = _resolve_platform(platform_key)
    target = skill_dir(platform, scope, root, home)
    state = install_state(target)

    # Copilot dedupe: a project-scope Claude install in the same root already covers it —
    # but ONLY when Copilot itself is absent (no install, no dangling leftovers). An
    # already-installed or locally-modified Copilot must report its own state
    # (up-to-date / blocked), matching status(), not be masked as "skipped".
    if (
        platform_key == "copilot"
        and scope == "project"
        and not force
        and state == "not-installed"
        and not has_leftovers(target)
    ):
        covered_by = _copilot_covered_by_claude(root, home)
        if covered_by is not None:
            return Action(
                platform_key,
                scope,
                target,
                "skipped",
                f"Copilot reads .claude/skills — already covered by {covered_by} "
                "(use --force to install to .github/skills anyway)",
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
        return Action(
            platform_key, scope, target, "would-install", f"{len(MANAGED_FILES)} files ({mode})"
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
            dst.write_bytes(packaged_content(rel))
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
    return Action(
        platform_key,
        scope,
        target,
        "installed",
        f"{' + '.join(parts)}, read back and verified",
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
            # Reflect install()'s Copilot dedupe: a not-installed project Copilot (with no
            # dangling leftovers) that a Claude install already covers is "skipped", not
            # "not-installed" — so status (read side) agrees with what setup would report.
            if (
                key == "copilot"
                and scope == "project"
                and state == "not-installed"
                and not has_leftovers(target)
            ):
                covered_by = _copilot_covered_by_claude(root, home)
                if covered_by is not None:
                    out.append(Action(key, scope, target, "skipped", f"covered by {covered_by}"))
                    continue
            out.append(Action(key, scope, target, state))
    return out
