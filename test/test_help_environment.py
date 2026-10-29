"""The environment dash runs in, as the help, README and package state it
(WP-36 section 36-04, ruling M8: documented, no code change).

Each class reads one item's sentences: the tested platform and what has
not been run (plat:PT-5), the Stata 19 floor of the drop-in claim
(plat:PT-2), the complete dependency list (plat:PT-11), the lock's Python
and platform coverage (plat:PT-12), how saving() reads a leading tilde
(plat:PT-6), Chrome as the tested browser (plat:PT-16) and the time and
memory a million rows take (plat:PT-14).  The tested-release sentences
themselves are pinned, unchanged, by
test_version_floor.py::TestTheStataFloor::test_every_stata_declaration_agrees
(DECISIONS A-2); nothing here names a Stata edition.  The measurable
claims are probed in test_wp36_truth.cscript block S04 (Q3604-1..3).
"""

import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_HELP = os.path.join(_ROOT, "dash.sthlp")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _help():
    return _read(_HELP)


def _between(text, start, end):
    i = text.index(start)
    j = text.index(end, i + len(start))
    return text[i:j]


def _flat(text):
    return " ".join(text.split())


def _setup_help():
    return _read(os.path.join(_ROOT, "dash_setup.sthlp"))


def _readme():
    return _read(os.path.join(_ROOT, "README.md"))


def _pkg_description():
    """dash.pkg's ``d`` lines, the ``d `` dropped, as one text."""
    lines = _read(os.path.join(_ROOT, "dash.pkg")).split("\n")
    return "\n".join(ln[2:] for ln in lines if ln.startswith("d "))


def _requirements():
    return _read(os.path.join(_ROOT, "dash_requirements.txt"))


def _differences():
    return _between(_help(), "{marker differences}", "{marker subcommands}")


def _differences_entry(title):
    """The Differences entry whose underlined title is ``title``."""
    diff = _differences()
    i = diff.index("{ul:%s}" % title)
    j = diff.find("{phang2}", i)
    return _flat(diff[i:j if j >= 0 else len(diff)])


def _stata_item():
    return _flat(_between(_help(), "{phang2}{ul:Stata}",
                          "{phang2}{ul:Python 3.11+}"))


def _drop_in_paragraph():
    return _flat(_between(_help(), "{cmd:dash} replaces {cmd:twoway}:",
                          "{marker description}"))


def _readme_requirements():
    return _flat(_between(_readme(), "## Requirements", "## Installation"))


_NOT_RUN = ("It is run from the console; Windows, Linux, Intel macOS and "
            "Stata's graphical interface have not been run")


class TestThePlatform:
    """plat:PT-5: dash has run only on macOS arm64 with StataNow 19.5 from
    the console; the help, dash_setup's help, README and package say what
    has not been run, beside the kept tested-release sentences."""

    def test_the_sentence_everywhere(self):
        places = {
            "dash.sthlp {ul:Stata}": _stata_item(),
            "dash_setup.sthlp": _flat(_between(_setup_help(),
                                               "{pstd}{ul:Stata}",
                                               "{pstd}{ul:Python}")),
            "README.md Requirements": _readme_requirements(),
            "dash.pkg": _flat(_pkg_description()),
        }
        missing = [k for k, v in places.items() if _NOT_RUN not in v]
        assert not missing, missing
        assert ("the code that opens a page there, the Windows file "
                "handling and the test runners (POSIX shell scripts) are "
                "untested") in _stata_item()

    def test_the_drop_in_paragraph(self):
        said = "macOS arm64 with StataNow 19.5, run from the console"
        assert said in _drop_in_paragraph()
        assert ("{help dash##dependencies:Dependencies}"
                in _drop_in_paragraph())
        readme = _flat(_between(_readme(), "`dash` takes the place of",
                                "Beyond the graphs"))
        assert said in readme, readme

    def test_the_differences_entry(self):
        entry = _differences_entry("Tested on one platform.")
        assert ("{cmd:dash} has run only on macOS arm64 with StataNow 19.5 "
                "from the console; see "
                "{help dash##dependencies:Dependencies}.") in entry, entry


class TestTheFloor:
    """plat:PT-2: dash refuses a Stata older than 19, r(9), where twoway
    runs; the claim that dash takes twoway's place is made for Stata 19 and
    later (probe: test_wp36_truth.cscript Q3604-1)."""

    def test_the_claim_is_for_stata_19(self):
        item = _stata_item()
        assert "r(9)" in item, item
        assert item.endswith(
            "The claim that {cmd:dash} takes {cmd:twoway}'s place is made "
            "for Stata 19 and later; {cmd:twoway} itself runs on older "
            "releases."), item
        readme = _flat(_between(_readme(), "`dash` takes the place of",
                                "Beyond the graphs"))
        assert readme.startswith(
            "`dash` takes the place of `twoway` (on Stata 19 and later):"), \
            readme
        assert "Stata 19 or later" in _readme_requirements()

    def test_the_differences_entry(self):
        entry = _differences_entry("Stata 19 or later.")
        assert ("{cmd:dash} refuses an older Stata, {cmd:r(9)}, where "
                "{cmd:twoway} runs; see "
                "{help dash##dependencies:Dependencies}.") in entry, entry


def _deps_intro():
    return _flat(_between(_help(), "{title:Dependencies}",
                          "{phang2}{ul:Stata}")[len("{title:Dependencies}"):])


def _python_item():
    return _flat(_between(_help(), "{phang2}{ul:Python 3.11+}",
                          "{phang2}{ul:Python packages, required}"))


def _packages_item():
    return _flat(_between(_help(), "{phang2}{ul:Python packages, required}",
                          "{phang2}{ul:Python packages, optional}"))


class TestTheDependencies:
    """plat:PT-11: the Dependencies section lists everything dash needs --
    Python 3.11+ (the one Stata runs), bokeh>=3.8,<3.10, numpy>=2.3 and
    pandas>=2.3 -- and says nothing else is needed (Q49, M8)."""

    def test_nothing_else(self):
        intro = _deps_intro()
        assert intro.startswith(
            "{pstd} These are all {cmd:dash} needs: no other program, "
            "package or service. Run {helpb dash_setup} once"), intro
        assert intro.endswith(
            "; a Python you install yourself -- Stata finds it, or uses "
            "the one {cmd:python set exec} names:"), intro
        assert "link yourself" not in intro, intro

    def test_no_upgrade(self):
        item = _packages_item()
        assert item.startswith("{phang2}{ul:Python packages, required} -- "
                               "bokeh>=3.8,<3.10, numpy>=2.3, pandas>=2.3."), \
            item
        assert ("{helpb dash_setup} reports a numpy or pandas older than "
                "its minimum and does not upgrade it.") in item, item
        h = _help()
        order = [h.index(s) for s in ("{phang2}{ul:Stata}",
                                      "{phang2}{ul:Python 3.11+}",
                                      "{phang2}{ul:Python packages, required}",
                                      "{phang2}{ul:Python packages, optional}")]
        assert order == sorted(order), order

    def test_the_python_item_follows_m8(self):
        item = _python_item()
        assert item.startswith(
            "{phang2}{ul:Python 3.11+} -- the one {cmd:python set exec} "
            "names, or, with none set, the one Stata finds; see "
            "{helpb python}."), item
        assert "linked to Stata" not in item, item

    def test_readme_agrees(self):
        assert ("Python 3.11+, bokeh>=3.8,<3.10, numpy>=2.3, pandas>=2.3."
                in _readme_requirements())
        assert ("Requires: Python 3.11+, bokeh>=3.8,<3.10, numpy>=2.3, "
                "pandas>=2.3." in _pkg_description())


def _lock_paragraph():
    return _flat(_between(_setup_help(), "{ul:The hash-pinned lock.}",
                          "\n\n"))


class TestTheLock:
    """plat:PT-12: the hash-pinned lock covers Python 3.11-3.14 on five
    platform tags; Python 3.15 and Windows ARM64 are not covered (probe:
    test_wp36_truth.cscript Q3604-3)."""

    def test_the_coverage(self):
        lock = _lock_paragraph()
        assert ("for Python 3.11, 3.12, 3.13 and 3.14 on five platforms: "
                "macOS arm64 and x86_64, Linux x86_64 and aarch64, and "
                "Windows x86_64 (the {cmd:# pythons:} and "
                "{cmd:# platforms:} lines at the top of "
                "{cmd:dash_requirements.txt})") in lock, lock
        assert ("On another platform or Python there is no wheel to match "
                "and {cmd:pip} stops; this includes Python 3.15 and later "
                "and Windows on ARM64, which the lock does not cover;") \
            in lock, lock

    def test_it_matches_the_lock_header(self):
        lines = _requirements().split("\n")
        assert lines[5] == "# pythons: 3.11 3.12 3.13 3.14", lines[5]
        assert lines[6] == ("# platforms: macos-arm64 macos-x86_64 "
                            "linux-x86_64 linux-aarch64 windows-amd64"), \
            lines[6]


class TestTheTilde:
    """plat:PT-6: saving() expands only a leading ``~/``, from HOME; ``~\\``
    is an ordinary path, relative on Windows (probe: test_wp36_truth.cscript
    Q3604-2)."""

    def test_the_rule(self):
        para = _flat(_between(_help(), "{marker saving_chars}",
                              "{marker nobrowser_global}"))
        assert para.endswith(
            "A {cmd:saving()} path that starts with {cmd:~/} starts in your "
            "home folder, read from the {cmd:HOME} environment variable "
            "({cmd:r(198)} when it is not set); a {cmd:~} anywhere else, and "
            "{cmd:~\\}, is an ordinary character, so on Windows "
            "{cmd:~\\}{it:dir}{cmd:\\}{it:file} is a path relative to the "
            "working directory, not your home folder (Windows has not been "
            "run; see {help dash##dependencies:Dependencies})."), para


class TestTheBrowser:
    """plat:PT-16: dash is tested in Google Chrome; the help, README and
    package no longer say "any browser" or "a modern browser" (A1)."""

    def test_chrome_is_named(self):
        description = _flat(_between(_help(), "{marker description}",
                                     "{marker differences}"))
        assert ("The HTML file works offline -- no server, internet "
                "connection, or special software is required. {cmd:dash} is "
                "tested in Google Chrome; a page that misbehaves in another "
                "browser is outside what {cmd:dash} supports.") \
            in description, description
        item1 = _flat(_between(_differences(), "{phang2}1.", "{phang2}2."))
        assert item1.endswith(
            "The file can be shared, emailed, or opened offline in a "
            "browser; {cmd:dash} is tested in Google Chrome only."), item1
        assert ("that opens offline, without a server or an internet "
                "connection; it is tested in Google Chrome."
                in _flat(_readme()))
        assert ("that opens offline, without a server or an internet "
                "connection; it is tested in Google Chrome."
                in _flat(_pkg_description()))

    def test_no_any_browser(self):
        for name, text in (("dash.sthlp", _help()), ("README.md", _readme()),
                           ("dash.pkg", _pkg_description())):
            flat = _flat(text).lower()
            assert "modern browser" not in flat, name
            assert "any browser" not in flat, name
