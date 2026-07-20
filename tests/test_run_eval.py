"""Unit tests for the eval harness's pure helpers (no model calls, no claude CLI).

These functions ship the new Round-1 logic (stream-json parsing, leak correlation) and,
like the graders, never run in CI otherwise — so a regression would be invisible.
"""

import json

import run_eval  # importable because conftest.py puts evals/ on sys.path


def _line(**evt):
    return json.dumps(evt)


def test_parse_stream_json_normal_completion():
    stdout = "\n".join(
        [
            _line(type="system", subtype="init", session_id="abc"),
            _line(type="result", subtype="success", result="hello", is_error=False),
        ]
    )
    sid, text, is_error = run_eval._parse_stream_json(stdout)
    assert sid == "abc" and text == "hello" and is_error is False


def test_parse_stream_json_flags_is_error():
    stdout = _line(type="result", subtype="success", result="oops", is_error=True, session_id="s")
    _, text, is_error = run_eval._parse_stream_json(stdout)
    assert is_error is True and text == "oops"


def test_parse_stream_json_flags_error_subtype():
    stdout = _line(type="result", subtype="error_max_turns", result="", session_id="s")
    _, _, is_error = run_eval._parse_stream_json(stdout)
    assert is_error is True


def test_parse_stream_json_missing_session_id_is_none():
    sid, _, _ = run_eval._parse_stream_json(_line(type="result", subtype="success", result="hi"))
    assert sid is None


def test_parse_stream_json_ignores_non_json_noise():
    stdout = "not json\n" + _line(type="result", result="ok", session_id="z") + "\nalso noise"
    sid, text, _ = run_eval._parse_stream_json(stdout)
    assert sid == "z" and text == "ok"


def test_find_leaked_brief_correlates_to_scenario(tmp_path, monkeypatch):
    monkeypatch.setattr(run_eval, "REPO_ROOT", tmp_path)
    leak_dir = tmp_path / "notes" / "idea-briefs"
    leak_dir.mkdir(parents=True)
    related = leak_dir / "newsletter-20260101.md"
    related.write_text("about a weekly newsletter idea", encoding="utf-8")
    scenario = {"invocation": "/socratic-method a weekly newsletter for the team"}
    assert run_eval._find_leaked_brief(0.0, scenario) == related


def test_find_leaked_brief_ignores_unrelated_file(tmp_path, monkeypatch):
    monkeypatch.setattr(run_eval, "REPO_ROOT", tmp_path)
    leak_dir = tmp_path / "notes" / "idea-briefs"
    leak_dir.mkdir(parents=True)
    (leak_dir / "other-20260101.md").write_text("quantum widget fabrication plan", encoding="utf-8")
    scenario = {"invocation": "/socratic-method a weekly newsletter for the team"}
    assert run_eval._find_leaked_brief(0.0, scenario) is None


def test_find_leaked_brief_none_when_dir_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(run_eval, "REPO_ROOT", tmp_path)
    assert run_eval._find_leaked_brief(0.0, {"invocation": "x"}) is None


def test_find_leaked_brief_stopword_only_overlap_is_not_correlated(tmp_path, monkeypatch):
    # A brief that shares only a generic word the invocation happens to contain ("idea")
    # must NOT be tied to this cell — the pre-tightening any-token match false-positived
    # on it. "startup" is the distinctive token, and it is absent from the stray file.
    monkeypatch.setattr(run_eval, "REPO_ROOT", tmp_path)
    leak_dir = tmp_path / "notes" / "idea-briefs"
    leak_dir.mkdir(parents=True)
    (leak_dir / "journal-20260101.md").write_text("random idea journal", encoding="utf-8")
    scenario = {"invocation": "/socratic-method my startup idea --mode stress"}
    assert run_eval._find_leaked_brief(0.0, scenario) is None


def test_find_leaked_brief_skips_non_utf8_file(tmp_path, monkeypatch):
    # A non-UTF-8 file in notes/ must not crash the sweep (UnicodeDecodeError is not an
    # OSError); it simply can't be correlated.
    monkeypatch.setattr(run_eval, "REPO_ROOT", tmp_path)
    leak_dir = tmp_path / "notes" / "idea-briefs"
    leak_dir.mkdir(parents=True)
    (leak_dir / "binary-20260101.md").write_bytes(b"\xff\xfe weekly newsletter")
    scenario = {"invocation": "/socratic-method a weekly newsletter for the team"}
    assert run_eval._find_leaked_brief(0.0, scenario) is None


def test_capture_leaked_brief_copies_and_preserves_original(tmp_path):
    # The leaked brief lives in the user's gitignored notes/; capturing it for the report
    # must COPY (leave the original in place), never move — a coincidental correlation
    # must not delete a real brief the user was writing.
    src = tmp_path / "brief-20260101.md"
    src.write_text("real user brief", encoding="utf-8")
    dest = tmp_path / "report" / "brief-leaked.md"
    dest.parent.mkdir()
    out = run_eval._capture_leaked_brief(src, dest)
    assert out == dest
    assert dest.read_text(encoding="utf-8") == "real user brief"
    assert src.exists() and src.read_text(encoding="utf-8") == "real user brief"
