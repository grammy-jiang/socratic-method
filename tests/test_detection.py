"""Agent auto-detection: each signal produces evidence; absence produces None."""

import stat
from pathlib import Path

import pytest

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


def test_cli_on_path_wins_over_config_dir(tmp_path):
    # Precedence: a CLI on PATH must be reported over a config directory for the same agent.
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)  # config dir present...
    bindir = tmp_path / "bin"
    bindir.mkdir()
    _fake_exe(bindir, "claude")  # ...AND the CLI on PATH
    d = detect_platforms(home, path_env=str(bindir))
    assert "CLI on PATH" in d["claude"]
    assert "config directory" not in d["claude"]


def test_copilot_config_dir_detected(tmp_path):
    # ~/.copilot is where Copilot keeps personal skills, so its presence is a
    # first-class signal — same rank as ~/.claude and ~/.codex.
    home = tmp_path / "home"
    (home / ".copilot").mkdir(parents=True)
    empty_bin = tmp_path / "bin"
    empty_bin.mkdir()
    d = detect_platforms(home, path_env=str(empty_bin))
    assert "config directory" in d["copilot"]
    assert str(home / ".copilot") in d["copilot"]


def test_copilot_editor_extensions_detected(tmp_path):
    empty_bin = tmp_path / "bin"
    empty_bin.mkdir()

    home_gh = tmp_path / "home-gh"
    (home_gh / ".local/share/gh/extensions/gh-copilot").mkdir(parents=True)
    assert "gh-copilot extension" in detect_platforms(home_gh, path_env=str(empty_bin))["copilot"]

    home_vsc = tmp_path / "home-vsc"
    (home_vsc / ".vscode/extensions/github.copilot-1.250.0").mkdir(parents=True)
    d = detect_platforms(home_vsc, path_env=str(empty_bin))
    assert "editor extension .vscode/github.copilot-1.250.0" in d["copilot"]


@pytest.mark.parametrize("rel", [".vscode-insiders", ".vscode-server", ".vscode-oss", ".vscodium"])
def test_copilot_detected_in_vscode_variants(tmp_path, rel):
    # A machine with only Insiders, a remote/server install, or VSCodium still has
    # Copilot; detecting only ~/.vscode reported "not detected" and installed nothing.
    empty_bin = tmp_path / "bin"
    empty_bin.mkdir()
    home = tmp_path / rel.lstrip(".")
    (home / rel / "extensions/github.copilot-chat-2.0.1").mkdir(parents=True)
    d = detect_platforms(home, path_env=str(empty_bin))
    assert f"editor extension {rel}/github.copilot-chat-2.0.1" == d["copilot"]
