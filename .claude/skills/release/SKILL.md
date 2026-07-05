---
name: release
description: Cut a socratic-method release to GitHub Releases and PyPI. Use when asked to release, publish, tag a version, or ship vX.Y.Z of this package. Covers both the normal tag-push path and the dispatch fallback for environments whose git proxy cannot push tags (e.g. Claude Code remote sessions).
---

# Release socratic-method

Releases are tag-driven: an annotated tag `vX.Y.Z` on master fires
`.github/workflows/release.yml`, whose three jobs build + verify the distributions,
create the GitHub Release with the wheel and sdist attached, and publish to PyPI via
Trusted Publishing (OIDC; bound to workflow file `release.yml` + environment `pypi`).

## Preconditions

1. Master CI is green.
2. `__version__` in `src/socratic_method/__init__.py` is bumped to X.Y.Z, in the literal
   form `__version__ = "X.Y.Z"` — `tag-release.yml` parses that exact shape with sed.
   This is the ONLY place the version lives (pyproject reads it dynamically).
3. The tag you will create is exactly `v` + `__version__`; both workflows hard-fail on
   mismatch.
4. PyPI uploads are immutable: if a release went out broken, bump the patch version and
   release again — never try to re-upload the same version.

## Path A — normal (environment can push tags)

```bash
git tag -a vX.Y.Z -m "socratic-method X.Y.Z — <one-line summary>"
git push origin vX.Y.Z
```

The tag push triggers the Release workflow; skip to Verify.

## Path B — dispatch fallback (tag pushes rejected, e.g. remote-session git proxy)

Symptom: `git push origin vX.Y.Z` fails with HTTP 403 while branch pushes succeed.

1. Ensure master (with the version bump) is pushed.
2. Dispatch the **Tag release** workflow (`tag-release.yml`) on `master` with input
   `tag: vX.Y.Z`. It verifies the tag matches `__version__`, then creates and pushes the
   annotated tag server-side as github-actions[bot].
3. Wait until the tag exists (`git ls-remote origin refs/tags/vX.Y.Z`).
4. Dispatch the **Release** workflow (`release.yml`) with `ref: vX.Y.Z` — the TAG ref,
   never a branch, or the tag/version check fails (`GITHUB_REF_NAME` must be the tag).

Both dispatches are always required on this path: tags created with the Actions
`GITHUB_TOKEN` do not fire tag-push events.

## Verify (both paths)

1. The Release run: all three jobs (`build`, `github-release`, `pypi`) green.
2. The GitHub Release `vX.Y.Z` exists with BOTH assets attached:
   `socratic_method-X.Y.Z-py3-none-any.whl` and `socratic_method-X.Y.Z.tar.gz`.
3. PyPI shows the new version: `https://pypi.org/pypi/socratic-method/json` lists both
   files under `urls`.
4. Optional end-to-end: `pip install --no-deps --target <tmpdir> socratic-method==X.Y.Z`
   and import it.

Do not report the release done until all of the above are confirmed.
