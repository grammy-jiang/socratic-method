"""Installer behavior: idempotence, no-silent-clobber, verify-after-write, the Copilot
dedupe, uninstall cleanliness, and user-scope resolution."""

import pytest

from socratic_method.installer import (
    MANAGED_FILES,
    PLATFORMS,
    install,
    install_state,
    skill_dir,
    status,
    uninstall,
)


@pytest.fixture
def roots(tmp_path):
    root = tmp_path / "project"
    home = tmp_path / "home"
    root.mkdir()
    home.mkdir()
    return root, home


def test_install_then_up_to_date(roots):
    root, home = roots
    a = install("claude", "project", root, home)
    assert a.outcome == "installed"
    target = skill_dir(PLATFORMS["claude"], "project", root, home)
    for rel in MANAGED_FILES:
        assert (target / rel).is_file()
    assert install("claude", "project", root, home).outcome == "up-to-date"


def test_modified_install_blocked_without_force(roots):
    root, home = roots
    install("claude", "project", root, home)
    target = skill_dir(PLATFORMS["claude"], "project", root, home)
    (target / "SKILL.md").write_text("locally edited")
    a = install("claude", "project", root, home)
    assert a.outcome == "blocked"
    assert "SKILL.md" in a.detail
    assert install("claude", "project", root, home, force=True).outcome == "installed"


def test_dry_run_writes_nothing(roots):
    root, home = roots
    a = install("codex", "project", root, home, dry_run=True)
    assert a.outcome == "would-install"
    assert install_state(skill_dir(PLATFORMS["codex"], "project", root, home)) == "not-installed"


def test_copilot_dedupes_against_project_claude(roots):
    root, home = roots
    install("claude", "project", root, home)
    a = install("copilot", "project", root, home)
    assert a.outcome == "skipped"
    assert "already covered" in a.detail
    # force installs to .github/skills anyway
    assert install("copilot", "project", root, home, force=True).outcome == "installed"


def test_copilot_installs_when_no_claude(roots):
    root, home = roots
    a = install("copilot", "project", root, home)
    assert a.outcome == "installed"
    assert ".github/skills" in str(a.target)


def test_copilot_has_no_user_scope(roots):
    root, home = roots
    with pytest.raises(ValueError, match="no documented user-scope"):
        install("copilot", "user", root, home)


def test_user_scope_targets_home(roots):
    root, home = roots
    a = install("codex", "user", root, home)
    assert a.outcome == "installed"
    assert str(a.target).startswith(str(home))
    assert ".agents/skills" in str(a.target)


def test_uninstall_removes_managed_files_and_empty_dirs(roots):
    root, home = roots
    install("claude", "project", root, home)
    target = skill_dir(PLATFORMS["claude"], "project", root, home)
    assert uninstall("claude", "project", root, home).outcome == "removed"
    assert not target.exists()
    assert uninstall("claude", "project", root, home).outcome == "not-installed"


def test_uninstall_preserves_user_files(roots):
    root, home = roots
    install("claude", "project", root, home)
    target = skill_dir(PLATFORMS["claude"], "project", root, home)
    keeper = target / "my-notes.md"
    keeper.write_text("mine")
    uninstall("claude", "project", root, home)
    assert keeper.exists()  # user file and its dir survive


def test_status_covers_all_platform_scopes(roots):
    root, home = roots
    install("claude", "project", root, home)
    entries = status(root, home)
    keys = {(a.platform, a.scope) for a in entries}
    assert ("claude", "project") in keys and ("codex", "user") in keys
    assert ("copilot", "user") not in keys
    by_key = {(a.platform, a.scope): a.outcome for a in entries}
    assert by_key[("claude", "project")] == "up-to-date"
    assert by_key[("codex", "project")] == "not-installed"
