"""CLI smoke tests through main(argv)."""

from pathlib import Path

import pytest

from socratic_method.cli import main

GOLDEN = Path(__file__).parent.parent / "evals" / "fixtures" / "tech-talk-series-20260704.md"


def test_validate_golden_ok(capsys):
    assert main(["validate", str(GOLDEN)]) == 0
    assert "OK" in capsys.readouterr().out


def test_validate_bad_file_fails(tmp_path, capsys):
    p = tmp_path / "bad.md"
    p.write_text("no frontmatter")
    assert main(["validate", str(p)]) == 1
    assert "ERROR" in capsys.readouterr().out


def test_setup_all_dry_run_and_status(tmp_path, capsys):
    assert main(["setup", "all", "--dry-run", "--root", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "would-install" in out
    assert main(["status", "--root", str(tmp_path)]) == 0
    assert "agent claude" in capsys.readouterr().out  # status shows detection


def test_setup_autodetect_installs_only_detected(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        "socratic_method.cli.detect_platforms",
        lambda home: {
            "claude": "claude CLI on PATH (/fake/claude)",
            "codex": None,
            "copilot": None,
        },
    )
    assert main(["setup", "--root", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "detected: claude CLI on PATH" in out
    assert (tmp_path / ".claude/skills/socratic-method/SKILL.md").is_file()
    assert not (tmp_path / ".agents").exists()
    assert not (tmp_path / ".github").exists()


def test_setup_autodetect_none_found(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        "socratic_method.cli.detect_platforms",
        lambda home: {"claude": None, "codex": None, "copilot": None},
    )
    assert main(["setup", "--root", str(tmp_path)]) == 1
    assert "No supported agent detected" in capsys.readouterr().out
    assert not (tmp_path / ".claude").exists()


def test_setup_all_then_uninstall(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    (tmp_path / "home").mkdir()
    assert main(["setup", "claude", "codex", "--root", str(tmp_path)]) == 0
    assert (tmp_path / ".claude/skills/socratic-method/SKILL.md").is_file()
    assert (tmp_path / ".agents/skills/socratic-method/SKILL.md").is_file()
    assert main(["uninstall", "claude", "codex", "--root", str(tmp_path)]) == 0
    assert not (tmp_path / ".claude/skills/socratic-method").exists()


def test_remove_is_the_uninstall_alias(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    (tmp_path / "home").mkdir()
    assert main(["setup", "claude", "--root", str(tmp_path)]) == 0
    assert main(["remove", "claude", "--root", str(tmp_path)]) == 0
    assert not (tmp_path / ".claude/skills/socratic-method").exists()


def test_setup_copy_flag_writes_regular_files(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    (tmp_path / "home").mkdir()
    assert main(["setup", "claude", "--copy", "--root", str(tmp_path)]) == 0
    skill_md = tmp_path / ".claude/skills/socratic-method/SKILL.md"
    assert skill_md.is_file() and not skill_md.is_symlink()


def test_unknown_target_rejected(tmp_path):
    with pytest.raises(SystemExit):
        main(["setup", "cursor", "--root", str(tmp_path)])


def test_setup_blocked_returns_exit_1(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    (tmp_path / "home").mkdir()
    assert main(["setup", "claude", "--root", str(tmp_path)]) == 0
    skill = tmp_path / ".claude/skills/socratic-method/SKILL.md"
    skill.unlink()
    skill.write_text("locally edited")  # now differs from packaged
    assert main(["setup", "claude", "--root", str(tmp_path)]) == 1
    assert "blocked" in capsys.readouterr().out


def test_setup_user_scope_valueerror_returns_exit_1(tmp_path, capsys):
    # Copilot has no user scope: skill_dir raises ValueError, caught into exit 1.
    assert main(["setup", "copilot", "--scope", "user", "--root", str(tmp_path)]) == 1
    assert "error:" in capsys.readouterr().out


def test_remove_no_targets_expands_to_all(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    (tmp_path / "home").mkdir()
    assert main(["setup", "claude", "codex", "--root", str(tmp_path)]) == 0
    assert main(["remove", "--root", str(tmp_path)]) == 0  # no targets → all platforms
    assert not (tmp_path / ".claude/skills/socratic-method").exists()
    assert not (tmp_path / ".agents/skills/socratic-method").exists()


def test_remove_dry_run_previews_without_removing(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    (tmp_path / "home").mkdir()
    assert main(["setup", "claude", "--root", str(tmp_path)]) == 0
    assert main(["remove", "claude", "--dry-run", "--root", str(tmp_path)]) == 0
    assert "would-remove" in capsys.readouterr().out
    assert (tmp_path / ".claude/skills/socratic-method/SKILL.md").exists()
