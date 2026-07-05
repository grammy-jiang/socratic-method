"""socratic-method command-line interface.

Subcommands:
    setup     install/refresh the skill for Claude Code, Codex, and/or Copilot
              (symlinks by default; --copy for real file copies)
    status    show what is installed where, and whether it matches this package
    remove    revert what setup did (alias: uninstall)
    validate  check an idea brief against the idea-brief-v1 format
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .installer import PLATFORMS, detect_platforms, install, status, uninstall
from .validator import validate_idea_brief

_TARGET_CHOICES = [*PLATFORMS.keys(), "all"]


def _targets(raw: list[str]) -> list[str]:
    bad = [t for t in raw if t not in _TARGET_CHOICES]
    if bad:
        raise SystemExit(
            f"unknown target(s): {', '.join(bad)} (choose from {', '.join(_TARGET_CHOICES)})"
        )
    return list(PLATFORMS) if (not raw or "all" in raw) else list(dict.fromkeys(raw))


def _print_action(a) -> None:
    mark = {
        "installed": "+",
        "up-to-date": "=",
        "skipped": "~",
        "would-install": ">",
        "blocked": "!",
        "removed": "-",
        "not-installed": " ",
        "partial-or-modified": "!",
    }.get(a.outcome, "?")
    line = f" [{mark}] {a.platform:8s} {a.scope:8s} {a.outcome:20s} {a.target}"
    print(line)
    if a.detail:
        print(f"      {a.detail}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="socratic-method",
        description="Socratic questioning skill for coding agents — installer and brief validator.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_setup = sub.add_parser("setup", help="install/refresh the skill for one or more platforms")
    p_setup.add_argument(
        "targets",
        nargs="*",
        metavar="TARGET",
        help=f"platforms to set up: {', '.join(_TARGET_CHOICES)} "
        "(default: auto-detect installed agents)",
    )
    p_setup.add_argument(
        "--scope",
        choices=["project", "user"],
        default="project",
        help="install into the current project (default) or the user home",
    )
    p_setup.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="project root for --scope project (default: cwd)",
    )
    p_setup.add_argument(
        "--force",
        action="store_true",
        help="overwrite an existing install that differs from this package",
    )
    p_setup.add_argument(
        "--copy",
        action="store_true",
        help="write file copies instead of symlinks (e.g. when committing the skill "
        "directory to a repo, or on filesystems without symlink support)",
    )
    p_setup.add_argument("--dry-run", action="store_true", help="print the plan, write nothing")

    p_status = sub.add_parser("status", help="show install state for every platform and scope")
    p_status.add_argument("--root", type=Path, default=Path.cwd())

    p_un = sub.add_parser(
        "remove",
        aliases=["uninstall"],
        help="revert what setup did: remove the managed skill links/files",
    )
    p_un.add_argument("targets", nargs="*", metavar="TARGET")
    p_un.add_argument("--scope", choices=["project", "user"], default="project")
    p_un.add_argument("--root", type=Path, default=Path.cwd())
    p_un.add_argument("--dry-run", action="store_true")

    p_val = sub.add_parser("validate", help="validate an idea-brief-v1 file")
    p_val.add_argument("brief", type=Path, help="path to the brief markdown file")

    args = parser.parse_args(argv)
    home = Path.home()

    if args.command == "validate":
        errors = validate_idea_brief(args.brief)
        for e in errors:
            print(f"ERROR: {e}")
        if not errors:
            print(f"OK: {args.brief} is a valid idea-brief-v1")
        return 0 if not errors else 1

    if args.command == "status":
        print(f"socratic-method {__version__} — install status (project root: {args.root})")
        detected = detect_platforms(home)
        for key, ev in detected.items():
            print(f"  agent {key:8s} {'detected: ' + ev if ev else 'not detected'}")
        for a in status(args.root, home):
            _print_action(a)
        return 0

    if args.command == "setup" and not args.targets:
        # Auto-detect which agents are installed; configure only those.
        detected = detect_platforms(home)
        for key, ev in detected.items():
            print(f"  agent {key:8s} {'detected: ' + ev if ev else 'not detected'}")
        keys = [k for k, ev in detected.items() if ev]
        if not keys:
            print(
                "No supported agent detected on this machine. Name targets explicitly, "
                "e.g. `socratic-method setup claude` or `socratic-method setup all`."
            )
            return 1
    else:
        keys = _targets(args.targets)

    rc = 0
    for key in keys:
        try:
            if args.command == "setup":
                a = install(
                    key,
                    args.scope,
                    args.root,
                    home,
                    force=args.force,
                    dry_run=args.dry_run,
                    copy=args.copy,
                )
            else:
                a = uninstall(key, args.scope, args.root, home, dry_run=args.dry_run)
        except ValueError as e:
            print(f" [!] {key:8s} {args.scope:8s} error: {e}")
            rc = 1
            continue
        _print_action(a)
        if a.outcome == "blocked":
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
