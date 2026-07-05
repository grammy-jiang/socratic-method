"""Install/inspect/remove the socratic-method skill for coding-agent platforms.

Design rules (inherited from the skill's own eval-hardened history):

- **Idempotent.** Every managed file is compared by content before writing;
  an identical install is reported "up to date", never rewritten.
- **Never clobber local edits silently.** A file that differs from the packaged
  version requires ``force=True`` to overwrite.
- **Verify before claiming.** After writing, every file is read back from disk and
  compared to the packaged content; "installed" is only reported when the read-back
  matches. A claimed install with no verified file is the failure mode this skill
  exists to prevent.

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
    note: str = ""


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
        note="reads a repo's .claude/skills too — a project Claude install covers it",
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
    if not dst.is_file():
        return "missing"
    return (
        "up-to-date" if _digest(dst.read_bytes()) == _digest(packaged_content(rel)) else "differs"
    )


def install_state(target: Path) -> str:
    """Whole-install state: 'not-installed' | 'up-to-date' | 'partial-or-modified'."""
    states = {rel: file_state(target, rel) for rel in MANAGED_FILES}
    if all(s == "missing" for s in states.values()):
        return "not-installed"
    if all(s == "up-to-date" for s in states.values()):
        return "up-to-date"
    return "partial-or-modified"


@dataclass
class Action:
    platform: str
    scope: str
    target: Path
    # 'installed' | 'up-to-date' | 'skipped' | 'would-install' | 'blocked' |
    # 'removed' | 'not-installed'
    outcome: str
    detail: str = ""


def install(
    platform_key: str,
    scope: str,
    root: Path,
    home: Path,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> Action:
    platform = PLATFORMS[platform_key]
    target = skill_dir(platform, scope, root, home)

    # Copilot dedupe: a project-scope Claude install in the same root already covers it.
    if platform_key == "copilot" and scope == "project" and not force:
        claude_target = skill_dir(PLATFORMS["claude"], "project", root, home)
        if install_state(claude_target) == "up-to-date":
            return Action(
                platform_key,
                scope,
                target,
                "skipped",
                f"Copilot reads .claude/skills — already covered by {claude_target} "
                "(use --force to install to .github/skills anyway)",
            )

    state = install_state(target)
    if state == "up-to-date":
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
        return Action(platform_key, scope, target, "would-install", f"{len(MANAGED_FILES)} files")

    for rel in MANAGED_FILES:
        dst = target / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(packaged_content(rel))

    # Verify before claiming: read back every file from disk.
    unverified = [rel for rel in MANAGED_FILES if file_state(target, rel) != "up-to-date"]
    if unverified:
        return Action(
            platform_key,
            scope,
            target,
            "blocked",
            f"post-write verification FAILED for: {', '.join(unverified)}",
        )
    return Action(
        platform_key,
        scope,
        target,
        "installed",
        f"{len(MANAGED_FILES)} files written and read back",
    )


def uninstall(
    platform_key: str, scope: str, root: Path, home: Path, *, dry_run: bool = False
) -> Action:
    platform = PLATFORMS[platform_key]
    target = skill_dir(platform, scope, root, home)
    if install_state(target) == "not-installed":
        return Action(platform_key, scope, target, "not-installed")
    if dry_run:
        return Action(platform_key, scope, target, "would-install", "would remove managed files")
    for rel in MANAGED_FILES:
        (target / rel).unlink(missing_ok=True)
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
            out.append(Action(key, scope, target, install_state(target)))
    return out
