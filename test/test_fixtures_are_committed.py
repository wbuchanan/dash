"""A fixture the suite reads but git does not hold makes the suite lie.

`.git/info/exclude` in this working copy lists `*.json` under "Common ASCII
dataset extensions" -- a sensible local rule for a Stata repository, and the
reason seven of the nine truth fixtures were added with `git add -f`. The two
most recent were added without it, so they exist on this machine and in no
clone.

Measured, clean `git archive HEAD` export against the working tree:

    clean checkout   2934 passed, 116 skipped
    working tree     3056 passed,  33 skipped

174 tests do not run on a clone, and the suite still exits 0, because each of
them skips politely when its fixture is missing. Those 174 are the
Stata-ground-truth checks -- whether dash's KPI statistics and its colour
table match Stata's -- which is the claim the package is built on.

This test asks git, not the filesystem, so a fixture that exists only here
fails.
"""
import os
import subprocess
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, ".."))
_FIXTURES = os.path.join(_HERE, "fixtures")


def _git(*args):
    return subprocess.run(["git", "-C", _REPO, *args],
                          capture_output=True, text=True)


@pytest.fixture(scope="module")
def tracked():
    p = _git("ls-files")
    if p.returncode != 0:
        pytest.skip("not a git working tree")
    return {os.path.normpath(line) for line in p.stdout.splitlines()}


def _fixture_files():
    out = []
    for root, _dirs, files in os.walk(_FIXTURES):
        for f in files:
            if f.startswith(".") or f.endswith(".pyc"):
                continue
            full = os.path.join(root, f)
            out.append(os.path.relpath(full, _REPO))
    return sorted(out)


def test_the_scan_found_the_fixtures():
    """Guards the guard: an empty list would pass every check below."""
    found = _fixture_files()
    assert len(found) >= 8, (
        f"only {len(found)} files found under test/fixtures; the checks "
        f"below would be vacuous"
    )
    assert any(f.endswith("stat_truth.json") for f in found)


@pytest.mark.parametrize("rel", _fixture_files())
def test_every_fixture_is_tracked_by_git(rel, tracked):
    assert os.path.normpath(rel) in tracked, (
        f"{rel} is read by the test suite and is not in the repository, so "
        f"on a clone the tests that need it skip and the suite still reports "
        f"success. Add it with `git add -f' -- .git/info/exclude carries a "
        f"`*.json' rule that silently drops it otherwise."
    )
