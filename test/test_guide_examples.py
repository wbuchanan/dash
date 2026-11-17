"""test_guide_examples.py -- scripts/guide_examples.py, which builds the user's
guide examples (make guide), and the examples committed in docs/guide/examples.

Each example is a do-file a reader can copy; the builder runs it in batch
Stata and keeps the page it writes.  The functions are tested with a fake
Stata runner (no Stata here or on CI); the committed examples are checked
against BUILD.md, so a do-file changed after its page was built fails here
until make guide rebuilds the page.
"""
import os
import re
import subprocess
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from scripts import guide_examples as ge  # noqa: E402
from scripts import pages_index as pi  # noqa: E402

#: A stand-in for scripts/stata_slot.sh <dir> <do>: it writes <dir>/run.log
#: ending in "##RC $FAKE_RC" (none when FAKE_RC is empty) and, when
#: FAKE_PAGE names one, a page in <dir>, as an example's saving() would.
_FAKE = """#!/bin/bash
cd "$1"
printf '. display "##RC " _rc\\n' > run.log
[ -n "$FAKE_RC" ] && printf '##RC %s\\n' "$FAKE_RC" >> run.log
[ -n "$FAKE_PAGE" ] && printf '<html>%s</html>' "$FAKE_PAGE" > "$FAKE_PAGE.html"
exit 0
"""


@pytest.fixture
def fake_slot(tmp_path):
    path = tmp_path / "fake_slot.sh"
    path.write_text(_FAKE)
    path.chmod(0o755)
    return (str(path),)


@pytest.fixture
def folder(tmp_path):
    d = tmp_path / "examples"
    d.mkdir()
    for n in ("alpha", "beta-2"):
        (d / (n + ".do")).write_text("* %s\ndash clear\n" % n)
    (d / "notes.txt").write_text("not an example")
    return d


def _git(*args):
    return subprocess.run(["git", "-C", _ROOT, *args], capture_output=True,
                          text=True, check=True).stdout


# ---- the functions ----------------------------------------------------------

def test_names_lists_the_do_files_and_refuses_a_bad_name(folder):
    assert ge.names(str(folder)) == ["alpha", "beta-2"]
    (folder / "Bad_Name.do").write_text("")
    with pytest.raises(ValueError, match="Bad_Name"):
        ge.names(str(folder))


def test_sha256_of_hashes_the_bytes(tmp_path):
    p = tmp_path / "x.do"
    p.write_bytes(b"abc")
    assert ge.sha256_of(str(p)) == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")


def test_wrapper_runs_the_example_under_the_header():
    assert ge.wrapper("/r/dash/", "/r/dash/docs/guide/examples/a.do").split("\n") == [
        "version 19", "set more off", "set linesize 255", 'adopath ++ "/r/dash/"',
        "global dash_nobrowser 1",
        'capture noisily do "/r/dash/docs/guide/examples/a.do"',
        'display "##RC " _rc', ""]
    for bad in ('/r/"q', "/r/`q", "/r/$q"):
        with pytest.raises(ValueError):
            ge.wrapper(bad, "/r/a.do")
        with pytest.raises(ValueError):
            ge.wrapper("/r", bad)


@pytest.mark.parametrize("log, rc", [
    ('. display "##RC " _rc\n##RC 0\n', 0),
    ('. display "##RC " _rc\n##RC 198\n', 198),
    ("##RC 0\n##RC 459\n", 459),
    ('. display "##RC " _rc\nr(601);\n', None),
    ("", None),
])
def test_rc_of_reads_the_wrappers_line(log, rc):
    assert ge.rc_of(log) == rc


def test_build_one_copies_the_page_or_says_why_not(folder, fake_slot, monkeypatch):
    monkeypatch.setenv("FAKE_RC", "0")
    monkeypatch.setenv("FAKE_PAGE", "alpha")
    assert ge.build_one("alpha", str(folder), "/r", fake_slot) is None
    assert (folder / "alpha.html").read_text() == "<html>alpha</html>"

    monkeypatch.setenv("FAKE_RC", "198")
    why = ge.build_one("alpha", str(folder), "/r", fake_slot)
    assert why.startswith("alpha.do ended with rc 198:")

    monkeypatch.setenv("FAKE_RC", "")
    assert ge.build_one("alpha", str(folder), "/r", fake_slot).startswith(
        "alpha.do ended with rc None:")

    monkeypatch.setenv("FAKE_RC", "0")
    monkeypatch.setenv("FAKE_PAGE", "")
    assert ge.build_one("beta-2", str(folder), "/r", fake_slot).startswith(
        "beta-2.do wrote no beta-2.html:")
    assert not (folder / "beta-2.html").exists()


def test_dash_commit_names_head():
    got = ge.dash_commit(_ROOT)
    assert re.fullmatch(r"[0-9a-f]{8}(-dirty)?", got), got
    assert got[:8] == _git("rev-parse", "--short=8", "HEAD").strip()
    dirty = _git("status", "--porcelain", "--", *ge.DASH_FILES).strip()
    assert got.endswith("-dirty") == bool(dirty)


def test_the_record_reads_back_what_it_wrote(folder):
    assert ge.read_record(str(folder)) == {}
    rows = {"beta-2": ("b" * 64, "0123abcd-dirty"), "alpha": ("a" * 64, "0123abcd")}
    ge.write_record(rows, str(folder))
    assert ge.read_record(str(folder)) == rows
    text = (folder / ge.RECORD).read_text()
    assert text.index("| alpha |") < text.index("| beta-2 |")
    (folder / ge.RECORD).write_text(text + "stray\n")
    with pytest.raises(ValueError, match="stray"):
        ge.read_record(str(folder))


def test_main_builds_records_and_reports(folder, fake_slot, monkeypatch, capsys):
    monkeypatch.setattr(ge, "dash_commit", lambda repo: "0123abcd")
    monkeypatch.setenv("FAKE_RC", "0")
    monkeypatch.setenv("FAKE_PAGE", "alpha")
    assert ge.main(["--only", "alpha"], str(folder), "/r", fake_slot) == 0
    assert ge.read_record(str(folder)) == {
        "alpha": (ge.sha256_of(str(folder / "alpha.do")), "0123abcd")}

    # A failure keeps the other rows and is reported; a gone example's row goes.
    ge.write_record({"alpha": ("a" * 64, "1"), "gone": ("c" * 64, "1")}, str(folder))
    monkeypatch.setenv("FAKE_RC", "111")
    assert ge.main(["--only", "beta-2"], str(folder), "/r", fake_slot) == 1
    assert ge.read_record(str(folder)) == {"alpha": ("a" * 64, "1")}
    assert "beta-2.do ended with rc 111" in capsys.readouterr().err

    assert ge.main(["--only", "nope"], str(folder), "/r", fake_slot) == 2


# ---- the committed examples -------------------------------------------------

def test_every_example_page_is_built_from_its_do_file():
    """A do-file changed after its page was built fails here: run make guide.
    Every page is committed and built from committed dash."""
    every = ge.names()
    assert every, "docs/guide/examples holds no example"
    record = ge.read_record()
    assert sorted(record) == every
    tracked = set(_git("ls-files", "docs/guide/examples").split())
    for n in every:
        for ext in (".do", ".html"):
            assert "docs/guide/examples/%s%s" % (n, ext) in tracked, n + ext
        sha, commit = record[n]
        assert sha == ge.sha256_of(os.path.join(ge.EXAMPLES, n + ".do")), (
            "%s.do changed since its page was built: run make guide" % n)
        assert not commit.endswith("-dirty"), n


def test_the_guide_builds_and_shows_every_example_once():
    """guide.md is the page the next deploy publishes (pages_index --guide):
    it builds, draws each example exactly once, and every link and frame on
    it points at a section of the page, a file in docs/guide, the site's
    other pages or an absolute address."""
    folder = os.path.join(_ROOT, "docs", "guide")
    with open(os.path.join(folder, "guide.md"), encoding="utf-8") as fh:
        md = fh.read()
    examples = pi.read_examples(ge.EXAMPLES)
    assert sorted(examples) == ge.names()
    used = re.findall(r"^@example ([a-z0-9-]+) \d+$", md, re.M)
    assert sorted(used) == sorted(examples), used
    page = pi.guide_page(md, examples)
    for url in re.findall(r'(?:href|src)="([^"]+)"', page):
        if url.startswith("#"):
            assert 'id="%s"' % url[1:] in page, url
        elif url.startswith("examples/"):
            assert os.path.exists(os.path.join(folder, url)), url
        else:
            assert (url in ("./", "../", "../gallery/")
                    or url.startswith(("https://", "mailto:"))), url
    assert "docs/guide/guide.md" in set(_git("ls-files", "docs/guide").split())


def test_make_guide_builds_the_examples_outside_every_gate():
    with open(os.path.join(_ROOT, "Makefile"), encoding="utf-8") as fh:
        mk = fh.read()
    rules = {m.group(1): (m.group(2), m.group(3)) for m in re.finditer(
        r"^([A-Za-z][\w-]*):([^\n=]*)\n((?:\t[^\n]*\n)*)", mk, re.M)}
    assert re.search(r"^\.PHONY:.*\bguide\b", mk, re.M)
    assert rules["guide"][1] == "\t$(PYTHON) scripts/guide_examples.py\n"
    assert "make guide" in rules["help"][1]
    for gate in ("check", "test", "test-dev", "test-all", "cert", "gate", "release"):
        assert not re.search(r"\bguide\b", rules[gate][0]), gate


def test_every_example_is_a_do_file_a_reader_can_run():
    """It says what it shows on its first line and writes <name>.html."""
    for n in ge.names():
        with open(os.path.join(ge.EXAMPLES, n + ".do"), encoding="utf-8") as fh:
            text = fh.read()
        assert text.startswith("* "), n
        assert len(re.findall(r"\bsaving\(%s\.html, replace\)" % re.escape(n),
                              text)) == 1, n
        assert "dash_nobrowser" not in text and "adopath" not in text, n
