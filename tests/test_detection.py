"""Agent auto-detection: each signal produces evidence; absence produces None."""

import stat
from pathlib import Path

from socratic_method.installer import detect_platforms


def _fake_exe(bindir: Path, name: str) -> None:
    exe = bindir / name
    exe.write_text("#!/bin/sh\n")
    exe.chmod(exe.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def test_nothing_detected_in_empty_env(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    empty_bin = tmp_path / "bin"
    empty_bin.mkdir()
    d = detect_platforms(home, path_env=str(empty_bin))
    assert d == {"claude": None, "codex": None, "copilot": None}


def test_cli_on_path_detected(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    bindir = tmp_path / "bin"
    bindir.mkdir()
    for cmd in ("claude", "codex", "copilot"):
        _fake_exe(bindir, cmd)
    d = detect_platforms(home, path_env=str(bindir))
    assert "claude CLI on PATH" in d["claude"]
    assert "codex CLI on PATH" in d["codex"]
    assert "copilot CLI on PATH" in d["copilot"]


def test_config_dirs_detected_without_cli(tmp_path):
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    (home / ".codex").mkdir()
    empty_bin = tmp_path / "bin"
    empty_bin.mkdir()
    d = detect_platforms(home, path_env=str(empty_bin))
    assert "config directory" in d["claude"]
    assert "config directory" in d["codex"]
    assert d["copilot"] is None


def test_copilot_editor_extensions_detected(tmp_path):
    empty_bin = tmp_path / "bin"
    empty_bin.mkdir()

    home_gh = tmp_path / "home-gh"
    (home_gh / ".local/share/gh/extensions/gh-copilot").mkdir(parents=True)
    assert "gh-copilot extension" in detect_platforms(home_gh, path_env=str(empty_bin))["copilot"]

    home_vsc = tmp_path / "home-vsc"
    (home_vsc / ".vscode/extensions/github.copilot-1.250.0").mkdir(parents=True)
    d = detect_platforms(home_vsc, path_env=str(empty_bin))
    assert "VS Code extension github.copilot-1.250.0" in d["copilot"]
