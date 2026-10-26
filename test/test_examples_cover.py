"""test_examples_cover.py -- every plot type dash draws has an example.

GAPS3 J3 (WP-31 section 57): "10 of 40 plot types unused (bar, scatteri,
pci, pcarrowi, pccapsym, pcbarrow, pcscatter, tsline, tsrline, fpfit); no
example uses `dash serve`, weights or `csv`; feature_tour.do's header names
serve/pci it does not contain and says 'thirty-eight plot types';
test_examples_run.cscript:13-16 claims the examples exercise every plot
type; no coverage test."

Measured at 6370ca4 with
``grep -ohE '\\((scatter|line|bar|...)' examples/*.do`` (no bar, scatteri,
pci, pcarrowi, pccapsym, pcbarrow, pcscatter, tsline, tsrline or fpfit) and
``grep -c 'dash serve\\|\\[aw\\|\\[fw\\|, csv\\|csv ' examples/*.do`` (0 for
every file).

The drawn types are read from the code, not from a list here: dash.ado's
"Supported: ..." refusal text (the message for an unknown plot type), so
a type a later change adds is required automatically.  (WP-35 PD-10: no
word is refused by name any more, so nothing is taken off that list.)

dash replaces twoway: no example may write ``dash twoway ...``, which dash
refuses r(198) as twoway refuses ``twoway twoway``.
"""

import glob
import os
import re

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")


def _read(rel):
    with open(os.path.join(_ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def _supported():
    """The plot-type names in dash.ado's "Supported: ..." refusal text."""
    src = _read("dash.ado")
    m = re.search(r'"Supported: ((?:[^"]*"\s*_n\s*///\s*"|[^"])*)"', src)
    if not m:
        return []
    text = re.sub(r'"\s*_n\s*///\s*"', " ", m.group(1))
    return text.split()


def _undrawn():
    """The words a by-name helper of dash_parse.mata refuses (WP-31 B2):
    none since WP-35 PD-10, which removed the helper."""
    src = _read("dash_parse.mata")
    m = re.search(
        r"string scalar _dash_undrawn_" r"plottype\(.*?\n\}", src, re.S)
    if not m:
        return []
    names = []
    for line in m.group(0).splitlines():
        if re.search(r"\b(?:anyof|inlist)\(|==", line):
            names += re.findall(r'"([a-z]+)"', line)
    return names


def _drawn_types():
    undrawn = set(_undrawn())
    return [t for t in _supported() if t not in undrawn]


def _examples_text():
    out = []
    for p in sorted(glob.glob(os.path.join(_ROOT, "examples", "*.do"))):
        with open(p, encoding="utf-8") as fh:
            out.append(fh.read())
    return "\n".join(out)


def _code_lines(text):
    """The non-comment lines (a do-file's * and // comments dropped)."""
    keep = []
    for line in text.splitlines():
        s = line.lstrip()
        if s.startswith("*") or s.startswith("//"):
            continue
        keep.append(line)
    return keep


def _commands(text):
    """Each command joined across its /// continuations, // comments cut."""
    joined = re.sub(r"///[^\n]*\n", " ", "\n".join(_code_lines(text)))
    cmds = [re.split(r"\s//", c)[0].strip() for c in joined.splitlines()]
    return [c for c in cmds if c]


_TEXT = _examples_text()
_CODE = "\n".join(_commands(_TEXT))


class TestTheParsersFoundSomething:

    def test_the_supported_list_was_found(self):
        assert len(_supported()) >= 40, _supported()

    def test_the_undrawn_list_was_found(self):
        # Flipped (WP-35 PD-10): one word was refused by name; that was
        # wrong (M1), and the helper is gone, so no word is read and every
        # type of the Supported: list needs an example.
        assert _undrawn() == []
        assert len(_drawn_types()) == len(_supported())


class TestEveryDrawnTypeHasAnExample:

    @pytest.mark.parametrize("t", _drawn_types())
    def test_each_type(self, t):
        pat = r"\bdash \(?%s\b|\(%s\b" % (t, t)
        assert re.search(pat, _CODE), "no example draws %s" % t


class TestTheFeaturesHaveExamples:

    def test_serve(self):
        cmds = _commands(_TEXT)
        hit = [c for c in cmds
               if re.match(r"dash serve\b", c)
               or (re.match(r"dash build\b", c)
                   and re.search(r"[, ]server\b", c))]
        assert hit, "no example serves or builds a server app"

    def test_weight(self):
        assert re.search(r"\[(?:aw|fw|pw|iw)\s*=", _CODE), \
            "no example uses a weight"

    def test_csv(self):
        cmds = _commands(_TEXT)
        hit = [c for c in cmds
               if re.match(r"dash build\b", c) and re.search(r"\bcsv\b", c)]
        assert hit, "no example builds with csv"

    def test_no_example_uses_a_twoway_prefix(self):
        bad = re.findall(r"\bdash\s+(?:graph\s+)?tw(?:o|ow|owa|oway)?\b",
                         _CODE)
        assert not bad, bad


class TestTheHeadersAreTrue:

    def test_feature_tour_header(self):
        src = _read("examples/feature_tour.do")
        assert "thirty-eight" not in src
        assert "plot_types_tour.do" in src

    def test_examples_run_header(self):
        src = _read("test/test_examples_run.cscript")
        assert "fourteen" in src
        assert re.search(r"assert `nfiles' == %d\b"
                         % len(glob.glob(os.path.join(
                             _ROOT, "examples", "*.do"))), src)
