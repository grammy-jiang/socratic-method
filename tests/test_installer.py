"""Installer behavior: idempotence, no-silent-clobber, verify-after-write, the Copilot
dedupe, uninstall cleanliness, and user-scope resolution."""

import pytest

from socratic_method.installer import (
    MANAGED_FILES,
    PLATFORMS,
    asset_path,
    file_state,
    has_leftovers,
    install,
    install_state,
    packaged_content,
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
    # Replace the symlink with a locally modified real file (writing through the
    # link would edit the packaged asset itself, which is exactly what install()
    # must never do — see test_force_reinstall_never_writes_through_links).
    (target / "SKILL.md").unlink()
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


def test_install_creates_symlinks_to_packaged_assets(roots):
    root, home = roots
    a = install("claude", "project", root, home)
    assert a.outcome == "installed"
    assert "symlinked" in a.detail
    target = skill_dir(PLATFORMS["claude"], "project", root, home)
    for rel in MANAGED_FILES:
        dst = target / rel
        assert dst.is_symlink()
        assert dst.resolve() == asset_path(rel).resolve()


def test_copy_mode_writes_regular_files(roots):
    root, home = roots
    a = install("claude", "project", root, home, copy=True)
    assert a.outcome == "installed"
    assert "copied" in a.detail and "symlinked" not in a.detail
    target = skill_dir(PLATFORMS["claude"], "project", root, home)
    for rel in MANAGED_FILES:
        assert (target / rel).is_file() and not (target / rel).is_symlink()
    assert install_state(target) == "up-to-date"


def test_force_reinstall_never_writes_through_links(roots):
    # --force over an existing symlinked install must replace the links, not
    # write through them into the package's own assets.
    root, home = roots
    install("claude", "project", root, home)
    packaged_before = packaged_content("SKILL.md")
    a = install("claude", "project", root, home, force=True, copy=True)
    assert a.outcome == "installed"
    assert packaged_content("SKILL.md") == packaged_before
    target = skill_dir(PLATFORMS["claude"], "project", root, home)
    assert not (target / "SKILL.md").is_symlink()


def test_uninstall_cleans_dangling_symlinks(roots):
    root, home = roots
    install("claude", "project", root, home)
    target = skill_dir(PLATFORMS["claude"], "project", root, home)
    for rel in MANAGED_FILES:  # simulate the package vanishing (e.g. pipx uninstall)
        (target / rel).unlink()
        (target / rel).symlink_to(root / "gone" / rel)
    assert uninstall("claude", "project", root, home).outcome == "removed"
    assert not target.exists()


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


def test_uninstall_dry_run_previews_and_writes_nothing(roots):
    root, home = roots
    install("claude", "project", root, home)
    target = skill_dir(PLATFORMS["claude"], "project", root, home)
    a = uninstall("claude", "project", root, home, dry_run=True)
    assert a.outcome == "would-remove"  # not "would-install" (regression)
    for rel in MANAGED_FILES:
        assert (target / rel).exists()  # preview removed nothing


def test_uninstall_removes_locally_modified_file(roots):
    # remove is deliberately force-free: it cleans up even a locally-edited managed file.
    root, home = roots
    install("claude", "project", root, home)
    target = skill_dir(PLATFORMS["claude"], "project", root, home)
    (target / "SKILL.md").unlink()
    (target / "SKILL.md").write_text("locally edited")
    assert uninstall("claude", "project", root, home).outcome == "removed"
    assert not (target / "SKILL.md").exists()


def test_install_post_write_verification_failure_blocks(roots, monkeypatch):
    # The readback-and-compare step is "the failure mode this skill exists to prevent".
    # Key the fake on real filesystem state (nothing yet -> missing, so install proceeds;
    # written files -> differs, so verification fails) rather than a call counter, so the
    # test stays valid if install() ever changes how many times it calls file_state.
    root, home = roots

    def fake_file_state(target, rel):
        return "differs" if (target / rel).exists() else "missing"

    monkeypatch.setattr("socratic_method.installer.file_state", fake_file_state)
    a = install("claude", "project", root, home)
    assert a.outcome == "blocked"
    assert "post-write verification FAILED" in a.detail


def test_install_falls_back_to_copy_when_asset_path_missing(roots, monkeypatch):
    # No durable asset path (e.g. a zipapp import) must fall back to copying, not fail.
    root, home = roots
    monkeypatch.setattr("socratic_method.installer.asset_path", lambda rel: None)
    a = install("claude", "project", root, home)
    assert a.outcome == "installed" and "copied" in a.detail
    target = skill_dir(PLATFORMS["claude"], "project", root, home)
    for rel in MANAGED_FILES:
        assert (target / rel).is_file() and not (target / rel).is_symlink()


def test_install_falls_back_to_copy_on_symlink_oserror(roots, monkeypatch):
    # A filesystem/OS that refuses symlinks must fall back to copying.
    root, home = roots

    def boom(self, target, target_is_directory=False):
        raise OSError("symlinks unsupported")

    monkeypatch.setattr("pathlib.Path.symlink_to", boom)
    a = install("claude", "project", root, home)
    assert a.outcome == "installed" and "copied" in a.detail
    target = skill_dir(PLATFORMS["claude"], "project", root, home)
    assert not (target / "SKILL.md").is_symlink()


def test_install_blocked_when_path_occupied_by_incompatible_node(roots):
    # A regular file where the references/ subdir must go makes mkdir raise OSError;
    # install must degrade to a reported "blocked", not crash mid-loop.
    root, home = roots
    target = skill_dir(PLATFORMS["claude"], "project", root, home)
    target.mkdir(parents=True)
    (target / "references").write_text("not a directory")
    a = install("claude", "project", root, home)
    assert a.outcome == "blocked"
    assert "write failed for references/example-session.md" in a.detail


def test_copilot_installs_when_claude_only_partial(roots):
    # Dedupe fires only when the claude install is fully up-to-date; a partial one
    # must not suppress the copilot install.
    root, home = roots
    install("claude", "project", root, home)
    claude_target = skill_dir(PLATFORMS["claude"], "project", root, home)
    (claude_target / "SKILL.md").unlink()
    (claude_target / "SKILL.md").write_text("modified")
    a = install("copilot", "project", root, home)
    assert a.outcome == "installed"
    assert ".github/skills" in str(a.target)


def test_status_reports_copilot_covered_by_claude(roots):
    # status() must agree with install()'s dedupe: covered Copilot is "skipped", not
    # "not-installed" (the read side and the write side must not contradict each other).
    root, home = roots
    install("claude", "project", root, home)
    by_key = {(a.platform, a.scope): a for a in status(root, home)}
    covered = by_key[("copilot", "project")]
    assert covered.outcome == "skipped"
    assert "covered by" in covered.detail


def test_uninstall_blocked_on_unlink_oserror(roots, monkeypatch):
    # A permission error during remove must degrade to a blocked Action (so `remove` with
    # no targets does not abort the remaining platforms), mirroring install()'s guard.
    root, home = roots
    install("claude", "project", root, home)

    def boom(self, missing_ok=False):
        raise PermissionError("read-only mount")

    monkeypatch.setattr("pathlib.Path.unlink", boom)
    a = uninstall("claude", "project", root, home)
    assert a.outcome == "blocked"
    assert "remove failed for" in a.detail


def test_file_state_unreadable_file_reads_as_differs(roots, monkeypatch):
    # An existing-but-unreadable managed file must not crash file_state (and thus status).
    root, home = roots
    install("claude", "project", root, home, copy=True)
    target = skill_dir(PLATFORMS["claude"], "project", root, home)

    def boom(self):
        raise PermissionError("no read")

    monkeypatch.setattr("pathlib.Path.read_bytes", boom)
    assert file_state(target, "SKILL.md") == "differs"


def test_unknown_platform_raises_valueerror(roots):
    # install/uninstall are public API; an unknown key must raise ValueError (cli.py's
    # caught type), not a raw KeyError.
    root, home = roots
    with pytest.raises(ValueError, match="unknown platform"):
        install("cursor", "project", root, home)
    with pytest.raises(ValueError, match="unknown platform"):
        uninstall("cursor", "project", root, home)


def test_copilot_installed_reports_up_to_date_not_skipped(roots):
    # Regression: the dedupe used to fire before checking Copilot's OWN state, masking an
    # already-installed Copilot as "skipped" (disagreeing with status()'s "up-to-date").
    # copy=True so has_leftovers() is False — the `state` conjunct is what's under test
    # here (with symlinks, has_leftovers alone would gate the branch and hide the fix).
    root, home = roots
    install("copilot", "project", root, home, copy=True)  # real files, not symlinks
    install("claude", "project", root, home)  # claude now also covers it
    assert install("copilot", "project", root, home).outcome == "up-to-date"


def test_copilot_modified_reports_blocked_not_skipped(roots):
    root, home = roots
    install("copilot", "project", root, home, copy=True)  # real files (isolate `state`)
    install("claude", "project", root, home)
    cop = skill_dir(PLATFORMS["copilot"], "project", root, home)
    (cop / "SKILL.md").unlink()
    (cop / "SKILL.md").write_text("locally edited")
    assert install("copilot", "project", root, home).outcome == "blocked"


def test_copilot_dangling_leftovers_installs_not_skipped(roots):
    # The OTHER dedupe conjunct: not-installed but with a dangling symlink → has_leftovers
    # is True, so the dedupe must NOT fire; install proceeds and clears the stale link.
    root, home = roots
    install("claude", "project", root, home)  # claude would otherwise cover copilot
    cop = skill_dir(PLATFORMS["copilot"], "project", root, home)
    cop.mkdir(parents=True)
    (cop / "SKILL.md").symlink_to(root / "gone" / "SKILL.md")  # dangling
    assert install("copilot", "project", root, home).outcome == "installed"


def test_has_leftovers_true_on_oserror(roots, monkeypatch):
    # An unreadable parent dir (is_symlink raises PermissionError) must not crash uninstall;
    # has_leftovers conservatively returns True so the unlink guard can surface the failure.
    root, home = roots
    target = skill_dir(PLATFORMS["claude"], "project", root, home)

    def boom(self):
        raise PermissionError("unreadable parent")

    monkeypatch.setattr("pathlib.Path.is_symlink", boom)
    assert has_leftovers(target) is True
