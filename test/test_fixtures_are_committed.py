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

A fixture git holds and nothing reads is the other way to lie: a file that
looks like ground truth and checks nothing (GAPS.md L8, ROADMAP TR-25.4).
Measured 24sep2026: the nine files of test/fixtures/scheme_visual/ were named
by no test file or certification script, while the message below called
every fixture "read by the test suite"; and fifteen .do files in test/,
March 2026 diagnostics with no assertion in them, were named by nothing at
all.  Two guards keep both from coming back.  They read the test files and
certification scripts in test/ (every .py, .cscript and .do there) rather
than asking git, so they run on any copy:

* every file under test/fixtures is named by one of them -- by its file
  name, or, for a file a test loads from a subdirectory under a computed
  name (test_statistical_truth.py reads data/<name>.csv for each dataset
  its record lists), by that directory as a fixtures path together with
  the file's stem;
* every .do file under test/ is named by another of them --
  run_all_cscripts.do by test_cscript_hygiene.py, cert_helpers.do by the
  scripts that run it, fixtures/twoway_corpus.do by
  test_option_surface.cscript.

This file names fixtures only to guard them, so it is not one of the files
that can name them.
"""
import os
import re
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


def test_the_scan_found_the_fixtures(tracked):
    """Guards the guard: an empty list would pass every check below, and so
    would a partial one -- a file the scan misses is never checked."""
    found = _fixture_files()
    # Measured 24sep2026: git tracks 32 files under test/fixtures, 13 of
    # them in data/ and scheme_visual/.  The floor this replaced, 8, passed
    # a scan that never left the top directory (19 files), and then no file
    # below it was asked about.  Every file git holds there must be one the
    # scan found; the parametrized test below asks the converse.  Outside a
    # git working tree `tracked' skips this, as it skips every check it
    # guards.
    prefix = os.path.join("test", "fixtures", "")
    under = {f for f in tracked if f.startswith(prefix)}
    assert under, "git tracks no file under test/fixtures"
    missed = sorted(under - set(found))
    assert not missed, (
        f"the scan found {len(found)} files under test/fixtures and missed "
        f"{len(missed)} that git tracks there, so the checks below never "
        f"see them: {missed}"
    )
    assert any(f.endswith("stat_truth.json") for f in found)


@pytest.mark.parametrize("rel", _fixture_files())
def test_every_fixture_is_tracked_by_git(rel, tracked):
    assert os.path.normpath(rel) in tracked, (
        f"{rel} is a test fixture -- test_every_fixture_is_named_by_a_test "
        f"holds that a test file or certification script names it -- and "
        f"git does not track it, so a clone does not have it. Add it with "
        f"`git add -f' -- .git/info/exclude carries a `*.json' rule that "
        f"silently drops it otherwise."
    )


# ---------------------------------------------------------------------------
# Nothing under test/ that nothing names
# ---------------------------------------------------------------------------

#: The kinds of file in test/ that can name a fixture or a do-file: the test
#: modules and their helpers, the certification scripts, the do-files.
_READER_EXTENSIONS = (".py", ".cscript", ".do")


@pytest.fixture(scope="module")
def readers():
    """{file name: text} of every test file and certification script in
    test/, this file excepted."""
    me = os.path.abspath(__file__)
    out = {}
    for f in sorted(os.listdir(_HERE)):
        path = os.path.join(_HERE, f)
        if (not f.endswith(_READER_EXTENSIONS) or not os.path.isfile(path)
                or os.path.abspath(path) == me):
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            out[f] = fh.read()
    return out


def _names(text, name):
    """Whether *text* names *name* as a whole token: "truth.json" is not
    named by "stat_truth.json", nor "sp500" by "sp5000"."""
    return re.search(r"(?<![\w.-])" + re.escape(name) + r"(?![\w-])",
                     text) is not None


def _names_dir(text, directory):
    """Whether *text* names test/fixtures/<directory> as a path: `"fixtures",
    "data"' in an os.path.join, or `fixtures/data' in a string.  A bare
    "data" is a JSON key in half the suite and names nothing."""
    return re.search(r"fixtures(?:[\"']\s*,\s*[\"']|/)"
                     + re.escape(directory) + r"(?![\w.-])", text) is not None


def _named_by(sub, readers):
    """The readers that name the fixture at *sub*, a path relative to
    test/fixtures: by its file name, or by its directory and its stem.  A
    file deeper than one directory must be named by its file name."""
    parts = sub.split(os.sep)
    hits = [f for f, t in readers.items() if _names(t, parts[-1])]
    if not hits and len(parts) == 2:
        stem = os.path.splitext(parts[-1])[0]
        hits = [f for f, t in readers.items()
                if _names_dir(t, parts[0]) and _names(t, stem)]
    return hits


def _do_files():
    out = []
    for root, _dirs, files in os.walk(_HERE):
        for f in files:
            if f.endswith(".do"):
                out.append(os.path.relpath(os.path.join(root, f), _REPO))
    return sorted(out)


def test_the_readers_are_found(readers):
    """Guards the two guards below: a scan that read nothing would find
    every file unnamed, and one that read this file would find every
    fixture named."""
    names = set(readers)
    cscripts = {f for f in os.listdir(_HERE) if f.endswith(".cscript")}
    # Measured 24sep2026: 63 certification scripts, all of them read.
    assert len(cscripts) >= 63 and cscripts <= names, sorted(cscripts - names)
    assert {"conftest.py", "cert_helpers.do", "run_all_cscripts.do",
            "test_statistical_truth.py", "test_scheme_visual_truth.py"} <= names
    assert os.path.basename(__file__) not in names


def test_the_readers_name_what_they_load(readers):
    """The two ways a fixture is named, each on a file that loads it that
    way, and each refusing what only looks like it."""
    assert _named_by("stat_truth.json", readers)
    assert "test_scheme_visual_truth.py" in _named_by(
        os.path.join("scheme_visual", "truth.json"), readers)
    # data/nlsw88.csv appears nowhere by its file name: it is loaded as
    # os.path.join(_DATA_DIR, f"{name}.csv").
    assert not [f for f, t in readers.items() if _names(t, "nlsw88.csv")]
    assert "test_statistical_truth.py" in _named_by(
        os.path.join("data", "nlsw88.csv"), readers)
    assert not _named_by(os.path.join("data", "nlsw88x.csv"), readers)
    assert not _named_by("no_such_fixture.json", readers)
    assert not _names('"stat_truth.json"', "truth.json")
    assert _names('os.path.join(_DIR, "truth.json")', "truth.json")
    assert _names_dir('os.path.join(_HERE, "fixtures", "data")', "data")
    assert _names_dir('"test/fixtures/data/auto.csv"', "data")
    assert not _names_dir('{"data": [1, 2]}', "data")
    assert not _names_dir('os.path.join(_HERE, "fixtures", "database")',
                          "data")


@pytest.mark.parametrize("rel", _fixture_files())
def test_every_fixture_is_named_by_a_test(rel, readers):
    sub = os.path.relpath(os.path.join(_REPO, rel), _FIXTURES)
    assert _named_by(sub, readers), (
        f"{rel} is named by no test file or certification script in test/, "
        f"so nothing reads it: wire it to a test or delete it (GAPS.md L8). "
        f"A file in a subdirectory may instead be named by that directory, "
        f"as a fixtures path, and its stem."
    )


def test_the_do_file_scan_found_the_scripts():
    # Measured 24sep2026, after the fifteen dead diagnostics were deleted:
    # these three are every .do file under test/.
    found = {os.path.basename(p) for p in _do_files()}
    assert {"cert_helpers.do", "run_all_cscripts.do",
            "twoway_corpus.do"} <= found, sorted(found)


@pytest.mark.parametrize("rel", _do_files())
def test_every_do_file_is_named_by_another_script_or_test(rel, readers):
    base = os.path.basename(rel)
    hits = [f for f, t in readers.items() if f != base and _names(t, base)]
    assert hits, (
        f"{rel} is named by no other test file or certification script in "
        f"test/: run_all_cscripts.do does not run it and no script or test "
        f"calls it, so it tests nothing (GAPS.md L8).  Wire it in or delete "
        f"it."
    )
