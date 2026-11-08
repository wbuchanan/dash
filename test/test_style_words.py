"""
test_style_words.py -- style words read per class as twoway reads them
(WP-45 section 45-02: ST-1 with ST-2, ST-3, ST-4, ST-5, ST-6, ST-11).

twoway reads each style word through its class's ``_unabbrev`` program
(ado/base/<c>/<class>.class): a lower-case abbreviation of a ``syntax``
option name, at least its capitals long, plus the class's own exact words.
test/fixtures/style_words_truth.json (scripts/extract_style_words_truth.do)
draws every prefix of every option name at every site of six classes and
compares the SVG with the canonical style's drawing; a word twoway does
not take is noted ("named style <w> not found in class <cls>, default
attributes used").

* TestTheReaders: dash_render.py's ``_dash_style_word`` gives the
  fixture's canonical for every row (the Mata twin, dash_parse.mata's
  ``_dash_style_word``, is pinned row by row by cscript Q4502-3), and 43-02's
  ``_dash_compass_dir`` reads through the same table.
* TestTheSites: the Python sites -- title position(), legend position()
  and ring(), mlabposition(), mlabangle(), msangle(), title and ytitle
  orientation(), legend bplacement() -- draw a taken abbreviation as its
  full spelling, in both modes.  connect(), text() and aspectratio() are
  read by dash.ado (cscript Q4502-1, Q4502-2).
* TestTheNotes: no note for a spelling twoway takes, twoway's note for
  one it does not; justification()'s class horizontal note (ST-11).
* TestTheRings: a title's ring keeps 43-05's full-word grammar; only
  legend() reads gridringstyle's abbreviations (D-45-02.c).
"""
import json
import math
import os
import sys
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402

MODES = ("saved", "served")
_FIXTURE = os.path.join(_HERE, "fixtures", "style_words_truth.json")

with open(_FIXTURE, encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)
ROWS = TRUTH["rows"]

#: The classes _dash_style_word reads (horizontal is justification()'s,
#: noted by _dash_textbox_style, not a reader's table).
_CLASSES = ("compass2dir", "tb_orientstyle", "clockdir", "gridringstyle",
            "anglestyle", "connectstyle")


def _reader_rows():
    """One row per (class, word): the readers do not depend on the site."""
    seen, out = set(), []
    for r in ROWS:
        if r["class"] not in _CLASSES or (r["class"], r["word"]) in seen:
            continue
        seen.add((r["class"], r["word"]))
        out.append(pytest.param(r, id="%s-%s" % (r["class"], r["word"])))
    return out


def _drawn(r):
    """What twoway drew at the row's site: the canonical (with no note),
    "" for a word it noted; the title ring rows are refusals (TestTheRings)."""
    if r["canonical"]:
        assert r["same_as_canonical"] == 1 and r["note"] == "", r
        return r["canonical"]
    assert r["note"] and "not found in class " + r["class"] in r["note"], r
    return ""


class TestTheFixture:
    def test_meta_and_drawings(self):
        m = TRUTH["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted",
                  "source"):
            assert m.get(k), k
        assert m["source"] == "scripts/extract_style_words_truth.do"
        # The canonical drawings of one site differ, so a row's equality
        # with its canonical's drawing says something.
        by_site = {}
        for key, h in TRUTH["drawings"].items():
            cls, site, can = key.split("|")
            assert h, key
            by_site.setdefault((cls, site), []).append(h)
        for (cls, site), hs in by_site.items():
            if cls == "gridringstyle" and site == "title":
                continue
            # aspectratio(1)'s square plot region has no room to move north,
            # south or center apart (4 distinct of 9); text() moves all 9.
            if (cls, site) == ("compass2dir", "aspect"):
                assert len(set(hs)) >= 4, (cls, site)
                continue
            assert len(set(hs)) == len(hs), (cls, site)

    def test_every_row_agrees_with_the_class_rule(self):
        for r in ROWS:
            if r["class"] == "gridringstyle" and r["site"] == "title":
                continue
            assert r["rc"] == 0, r
            _drawn(r)


class TestTheReaders:
    @pytest.mark.parametrize("row", _reader_rows())
    def test_python_reader(self, row):
        """_dash_style_word(cls, w) is the canonical twoway drew for every
        row, "" for every word twoway noted."""
        sites = [r for r in ROWS if r["class"] == row["class"]
                 and r["word"] == row["word"]
                 and not (r["class"] == "gridringstyle"
                          and r["site"] == "title")]
        want = {_drawn(r) for r in sites}
        assert len(want) == 1, sites
        assert dr._dash_style_word(row["class"], row["word"]) == want.pop()

    def test_compass_dir_reads_the_table(self):
        """43-02's _dash_compass_dir answers by the full name of
        compass2dir's canonical, for every compass row (one table)."""
        for r in ROWS:
            if r["class"] != "compass2dir":
                continue
            can = _drawn(r)
            assert dr._dash_compass_dir(r["word"]) == (
                dr._DASH_COMPASS_FULL[can] if can else None), r["word"]

    def test_unknown_classes_and_blank_words(self):
        assert dr._dash_style_word("nosuchclass", "n") == ""
        for cls in _CLASSES:
            for w in (None, "", "  ", "a b", "t\tb"):
                assert dr._dash_style_word(cls, w) == ""
        assert dr._dash_style_word("clockdir", " 6 ") == "6"
        assert dr._dash_style_word("anglestyle", "vertical") == "90"

    def test_the_mata_twin_holds_the_same_names(self):
        """dash_parse.mata's _dash_style_word lists each class's option
        names, minimums and canonicals in the Python table's order."""
        import re
        with open(os.path.join(_HERE, "..", "dash_parse.mata"),
                  encoding="utf-8") as fh:
            src = fh.read()
        body = src[src.index("string scalar _dash_style_word("):]
        body = body[:body.index("\n}\n")]
        for cls, names in dr._DASH_STYLE_NAMES.items():
            part = body[body.index('cls == "%s"' % cls):]
            part = part[:part.index("}")]
            got = re.findall(r'"([a-z]+)", "([0-9])", "([a-z0-9]+)"', part)
            assert [(a, int(b), c) for a, b, c in got] == list(names), cls


# ---- the Python sites ------------------------------------------------------

def _figs(mode, go, plots=None):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        figs, _c = tp._figures_in(mode, tp._spec(
            plots or [tp._sc()], {"scheme": "s2color"}, go))
    assert len(figs) == 1, len(figs)
    return figs[0], [str(w.message) for w in caught] + list(_c or [])


def _val(v):
    if isinstance(v, float):
        return round(v, 9)
    if isinstance(v, (int, str, type(None), bool)):
        return v
    if hasattr(v, "properties_with_values"):
        # A model (a Node, a transform): its own values, not its id.
        return (type(v).__name__, tuple(sorted(
            (k, _val(x)) for k, x in v.properties_with_values(
                include_defaults=False).items())))
    return str(v)


def _sig(fig):
    """Where and how the figure draws its annotations: per panel, each
    model's type, text, angle, location, offsets, alignment and its axis
    label's orientation."""
    out = []
    for side in ("center", "above", "below", "left", "right"):
        for m in getattr(fig, side):
            t = type(m).__name__
            if t in ("BoxAnnotation", "Span"):
                continue
            row = [side, t]
            for p in ("text", "angle", "location", "x_offset", "y_offset",
                      "text_align", "align", "axis_label",
                      "axis_label_orientation", "orientation", "x", "y",
                      "x_units", "y_units", "anchor"):
                if p in m.properties():
                    row.append((p, _val(getattr(m, p))))
            out.append(tuple(row))
    for r in fig.renderers:
        g = getattr(r, "glyph", None)
        if type(g).__name__ != "Text":
            continue
        out.append(("glyph", "Text") + tuple(
            (p, _val(getattr(g, p))) for p in (
                "angle", "x_offset", "y_offset", "text_align",
                "text_baseline")))
    return out


_LEG = [tp._sc(), tp.plot_for("scatter", yvar="price")]
_ML = {"mlabel": "foreign"}

#: (id, graph options with the word, the same with the canonical spelling,
#: plots, the options with no style word -- the default, which must differ).
_SITES = [
    ("title-position-bottom", {"title": '"TT", position(bottom)'},
     {"title": '"TT", position(6)'}, None, {"title": '"TT"'}),
    ("title-position-b", {"title": '"TT", position(b)'},
     {"title": '"TT", position(6)'}, None, {"title": '"TT"'}),
    ("title-position-l", {"title": '"TT", position(l)'},
     {"title": '"TT", position(9)'}, None, {"title": '"TT"'}),
    ("legend-position-top-ring-inside",
     {"legend": "position(top) ring(inside)"},
     {"legend": "position(12) ring(0)"}, _LEG, {}),
    ("legend-position-top", {"legend": "position(top)"},
     {"legend": "position(12)"}, _LEG, {}),
    ("legend-ring-in", {"legend": "ring(in) position(1)"},
     {"legend": "ring(0) position(1)"}, _LEG, {"legend": "position(1)"}),
    ("legend-bplacement-nor", {"legend": "ring(0) bplacement(nor)"},
     {"legend": "ring(0) bplacement(north)"}, _LEG, {"legend": "ring(0)"}),
    ("title-orientation-vertic", {"title": '"TT", orientation(vertic)'},
     {"title": '"TT", orientation(vertical)'}, None, {"title": '"TT"'}),
    ("ytitle-orientation-vertic", {"ytitle": '"YY", orientation(vertic)'},
     {"ytitle": '"YY", orientation(vertical)'}, None, {"ytitle": '"YY"'}),
    ("ytitle-orientation-rhori", {"ytitle": '"YY", orientation(rhori)'},
     {"ytitle": '"YY", orientation(rhorizontal)'}, None, {"ytitle": '"YY"'}),
]

_PLOT_SITES = [
    ("mlabposition-left", dict(_ML, mlabposition="left"),
     dict(_ML, mlabposition="9"), dict(_ML)),
    ("mlabposition-t", dict(_ML, mlabposition="t"),
     dict(_ML, mlabposition="12"), dict(_ML)),
    ("mlabangle-v", dict(_ML, mlabangle="v"), dict(_ML, mlabangle="90"),
     dict(_ML)),
    ("mlabangle-rh", dict(_ML, mlabangle="rh"), dict(_ML, mlabangle="180"),
     dict(_ML)),
]


class TestTheSites:
    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("case,word,canon,plots,base",
                             [pytest.param(*c, id=c[0]) for c in _SITES])
    def test_case(self, case, word, canon, plots, base, mode):
        """The abbreviation draws what its full spelling draws, which is
        not the default, with no note."""
        fw, ww = _figs(mode, word, plots)
        fc, _wc = _figs(mode, canon, plots)
        fb, _wb = _figs(mode, base, plots)
        assert _sig(fw) == _sig(fc), case
        assert _sig(fc) != _sig(fb), case
        assert not [w for w in ww if "not found in class" in w
                    or "clock position" in w or "compass" in w], ww

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("case,word,canon,base",
                             [pytest.param(*c, id=c[0]) for c in _PLOT_SITES])
    def test_plot_case(self, case, word, canon, base, mode):
        fw, ww = _figs(mode, {}, [tp._sc(**word)])
        fc, _wc = _figs(mode, {}, [tp._sc(**canon)])
        fb, _wb = _figs(mode, {}, [tp._sc(**base)])
        assert _sig(fw) == _sig(fc), case
        assert _sig(fc) != _sig(fb), case
        assert not [w for w in ww if "clock position" in w
                    or "angle" in w], ww

    def test_msangle_reads_the_abbreviation(self):
        """msangle() and the axis angle() read through the same
        anglestyle reader."""
        assert dr._dash_anglestyle_degrees("rv") == 270.0
        assert dr._dash_anglestyle_degrees("ver") == 90.0
        assert dr._dash_anglestyle_degrees("r") is None
        assert dr._dash_anglestyle_degrees("Vertical") is None
        assert dr._parse_axis_angle("angle(rv)") == pytest.approx(
            math.radians(270))


# ---- the notes ---------------------------------------------------------------

def _noted(caught, word):
    return [w for w in caught if "(%s)" % word in w
            or "style %s not" % word in w]


#: (class, site) -> how to build it: graph options or plot options with @.
_NOTE_SITES = {
    ("clockdir", "mlabpos"): ("plot", dict(_ML, mlabposition="@")),
    ("tb_orientstyle", "ytitle"): ("graph", {"ytitle": '"YY", orientation(@)'}),
    ("anglestyle", "mlabangle"): ("plot", dict(_ML, mlabangle="@")),
    ("horizontal", "title"): ("graph", {"title": '"T", justification(@)'}),
}


def _note_rows():
    out = []
    for r in ROWS:
        how = _NOTE_SITES.get((r["class"], r["site"]))
        if how is None:
            continue
        # Each option's shortest abbreviation and every word twoway notes.
        short = r["canonical"] == "" or (
            len(r["word"]) <= 2 and r["word"].islower())
        if short:
            out.append(pytest.param(r, id="%s-%s-%s" % (
                r["class"], r["site"], r["word"])))
    return out


class TestTheNotes:
    @pytest.mark.parametrize("row", _note_rows())
    def test_row(self, row):
        """dash notes the word exactly when twoway does, in twoway's
        words where the note is a named-style one."""
        kind, tmpl = _NOTE_SITES[(row["class"], row["site"])]
        sub = {k: v.replace("@", row["word"]) for k, v in tmpl.items()}
        dr._DASH_NOTED.clear()
        if kind == "plot":
            _f, caught = _figs("saved", {}, [tp._sc(**sub)])
        else:
            _f, caught = _figs("saved", sub)
        got = _noted(caught, row["word"])
        if row["note"]:
            assert got, caught
            if row["class"] in ("horizontal", "tb_orientstyle"):
                assert any("named style %s not found in class %s, default "
                           "attributes used" % (row["word"], row["class"])
                           in w for w in got), got
        else:
            assert not got, got


# ---- the rings -----------------------------------------------------------------

class TestTheRings:
    def test_title_and_legend_grammar(self):
        """A title's ring keeps 43-05's grammar; legend() reads
        gridringstyle's abbreviations (D-45-02.c)."""
        assert dr._dash_ring_value("7.5") == 7.5
        assert dr._dash_ring_value("in") is None
        assert dr._dash_ring_value("in", legend=True) == 0.0
        assert dr._dash_ring_value("out", legend=True) == 1.0
        assert dr._dash_ring_value("7.5", legend=True) == 7.5
        assert dr._dash_ring_value("Inside", legend=True) is None
        assert dr._dash_legend_ring("i") == 0.0

    def test_the_title_rows_are_twoways_refusals(self):
        """title("TT", ring(<abbreviation>)) is refused by twoway with no
        note (43-05's refusal stands); an unknown word after its two
        notes."""
        for r in ROWS:
            if not (r["class"] == "gridringstyle" and r["site"] == "title"):
                continue
            if r["word"] in ("inside", "outside"):
                assert r["rc"] == 0 and r["note"] == "", r
                continue
            assert r["rc"] == 198, r
            assert r["lines"][-1] == "option ring() incorrectly specified", r
            assert bool(r["note"]) == (r["canonical"] == ""), r
