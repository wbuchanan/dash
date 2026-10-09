"""
test_by_text.py -- by() panel labels and overall text (WP-30 P1.15a,
section 28).

The defect: dash appended each panel's label to the graph's title
(``T — Domestic``), joined the labels of several variables " / ", titled a
missing panel "Missing", drew a string by() value ``""`` as an untitled
panel (and counted it in Total), drew a graph-level subtitle() as a row
beside the label, and named by()'s title(), subtitle(), note() and
caption() as ignored, with no ``Graphs by`` note -- in both modes.

twoway's rule (bygraph_g.class; StataNow 19.5): the label is the panel's
subtitle(), given before the user's options, so the graph's subtitle()
merges with it and title() stays on every panel; labels are joined ", ",
a missing value -- a string ``""`` included (``markout ..., strok``) --
reads ``(missing)``; by()'s own text and the default note ``Graphs by
<list>`` are drawn once over the panels.

The design (D-28a, D-28b): the label is a ``Title`` named
``dash_by_label`` in each panel's ``above``; the overall text lives in two
chrome cells, bare ``Plot`` models ``dash_by_head`` and ``dash_by_foot``
spanning the panel grid, carried by the first panel as
``_dash_by_chrome``.  The truth is ``test/fixtures/by_text_truth.json``,
measured by ``scripts/extract_by_text_truth.do``; its ``data`` block is the
data file every case here draws.
"""
import itertools
import json
import logging
import os
import sys
import tempfile
import time
import types
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from by_panel_probe import (by_grid, chrome_texts, panel_label,  # noqa: E402
                            panel_label_title)
from conftest import load_app  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "by_text_truth.json")
_MODES = ("saved", "served")
_SEQ = itertools.count()
_TMP = tempfile.mkdtemp(prefix="dash_by_text_")
_TRUTH = None


from conftest import render_models  # noqa: E402


def _truth():
    global _TRUTH
    if _TRUTH is None:
        with open(_FIXTURE, encoding="utf-8") as fh:
            _TRUTH = json.load(fh)
    return _TRUTH


def _spec(go, if_expr="", scheme="", filt=""):
    go = dict(go)
    go["name"] = "g1"
    g = {"name": "g1", "graph_options": go, "options": dict(go),
         "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                    "options": {}}],
         "if_expr": if_expr, "in_expr": ""}
    return {"graphs": [g], "kpis": [],
            "build_options": {
                "layout": "auto", "link": "", "filter": filt, "theme": "",
                "scheme": scheme, "session_scheme": "", "title": "",
                "subtitle": "", "registry": "g1", "tabs": "",
                "filter_position": "top", "level": "95", "formats": {}}}


def _probe_spec(probe):
    """The dash spec of one fixture probe: `twoway scatter mpg weight
    <if>, <options>', its title/subtitle/note/caption/by as graph options
    and its scheme as the build's."""
    go, scheme = {}, ""
    for tok in dr._dash_by_tokens(probe["options"]):
        name, _, arg = tok.partition("(")
        arg = arg[:-1]
        if name == "scheme":
            scheme = arg
        else:
            go[name] = arg
    return _spec(go, probe["if"].replace("if ", "", 1), scheme)


def _write(spec):
    tag = next(_SEQ)
    sp = os.path.join(_TMP, "spec_%d.json" % tag)
    dp = os.path.join(_TMP, "data_%d.json" % tag)
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(_truth()["data"], fh)
    return tag, sp, dp


def _draw(mode, spec):
    """Namespace(panels=[fig], head, foot, notes, root) as *mode* draws
    *spec*; panels in grid order."""
    tag, sp, dp = _write(spec)
    dr._dash_reset_notes()
    if mode == "saved":
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            r = dr.DashRenderer(sp, dp)
            render_models(r)
        roots, notes = [r._last_layout_root], [str(w.message) for w in caught]
        extra = r
    else:
        from bokeh.document import Document
        ap = os.path.join(_TMP, "app_%d.py" % tag)
        with warnings.catch_warnings(record=True) as built:
            warnings.simplefilter("always")
            dr.ServerAppBuilder(sp, dp).build(ap)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mod = load_app(ap, "_bt_app_%d" % tag)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            doc = Document()
            mod.make_document(doc)
        roots = list(doc.roots)
        notes = [str(w.message) for w in built + caught]
        extra = doc
    panels, head, foot = [], None, None
    gridded = [r for r in roots if _has_panel_grid(r)]
    if gridded:
        p, head, foot = by_grid(gridded[0])
        panels = [f for _, _, f in p]
    return types.SimpleNamespace(panels=panels, head=head, foot=foot,
                                 notes=notes, roots=roots, extra=extra)


def _has_panel_grid(root):
    """True when *root* holds a GridPlot of figures (a by() grid)."""
    from bokeh.models import GridPlot
    return any(isinstance(m, GridPlot)
               and any(type(c[0]).__name__ == "figure" for c in m.children)
               for m in root.references())


def _rows(fig):
    for r in fig.renderers:
        if type(r).__name__ == "GlyphRenderer":
            data = r.data_source.data
            return len(next(iter(data.values()))) if data else 0
    return None


def _panel_boxes(fig):
    """The panel's own note and caption rows (every Title or in-band
    Label but its label)."""
    out = [m.text for m in list(fig.above) + list(fig.below)
           if type(m).__name__ == "Title" and m.name != "dash_by_label"]
    out += [m.text for m in fig.center if type(m).__name__ == "Label"]
    return sorted(t for t in out if t)


def _ok_probes():
    return sorted(k for k, p in _truth()["probes"].items() if p["rc"] == 0)


# ---------------------------------------------------------------------------
# The fixture
# ---------------------------------------------------------------------------
class TestTheFixture:
    def test_meta_and_probes(self):
        """test/fixtures/by_text_truth.json, by scripts/extract_by_text_truth.do."""
        t = _truth()
        assert {"stata_version", "born_date", "dash_commit",
                "extracted"} <= set(t["_meta"])
        assert len(t["probes"]) == 39
        assert t["probes"]["bp32"]["rc"] == 198
        assert t["probes"]["bp35"]["rc"] == 198


@pytest.mark.parametrize("mode", _MODES)
class TestPanelsMatchTwoway:
    def test_panels(self, mode):
        """Every probe twoway draws: the panel count, each panel's label,
        title, note, caption and rows equal twoway's, in panel order."""
        bad = []
        for pid in _ok_probes():
            p = _truth()["probes"][pid]
            r = _draw(mode, _probe_spec(p))
            got = [("\n".join([panel_label(f)] if panel_label(f) else []),
                    str(f.title.text or ""), _panel_boxes(f), _rows(f))
                   for f in r.panels]
            want = [("\n".join(q["sub"]), q["title"],
                     sorted(t for t in (q["note"], q["caption"]) if t),
                     q["n"]) for q in p["panels"]]
            if got != want:
                bad.append((pid, got, want))
        assert not bad, "\n".join("%s: dash %r, twoway %r" % b for b in bad)


@pytest.mark.parametrize("mode", _MODES)
class TestOverallTextMatchesTwoway:
    def test_texts(self, mode):
        """Every probe twoway draws: the head and foot cells hold twoway's
        overall title, subtitle, note (its lines joined) and caption, the
        note at size(large)'s size where by(, note()) asks for it."""
        bad = []
        for pid in _ok_probes():
            p = _truth()["probes"][pid]
            o = p["overall"]
            r = _draw(mode, _probe_spec(p))
            got = sorted(sum((chrome_texts(c) for c in (r.head, r.foot)
                              if c is not None), []))
            want = sorted(t for t in (o["title"], o["subtitle"],
                                      "\n".join(o["note"]), o["caption"]) if t)
            if got != want:
                bad.append((pid, got, want))
            if "size(large)" in p["options"]:
                rows = [m for c in (r.head, r.foot) if c is not None
                        for m in list(c.above) + list(c.below)
                        if type(m).__name__ == "Title"
                        and m.text == "\n".join(o["note"])]
                big = dr._textbox_size({"size": "large"}, None)
                if [m.text_font_size for m in rows] != [big]:
                    bad.append((pid, "note size",
                                [m.text_font_size for m in rows], big))
        assert not bad, "\n".join("%s: dash %r, twoway %r" % b[:3]
                                  for b in bad)


@pytest.mark.parametrize("mode", _MODES)
class TestPlacementMatchesTwoway:
    def test_sides_and_alignment(self, mode):
        """Every probe twoway draws: each panel label's alignment and each
        overall text's side (above or below the panels) and alignment are
        those of twoway's SVG (start left, middle center, end right)."""
        # An SVG text with no text-anchor is anchored at its start.
        align_of = {"start": "left", "middle": "center", "end": "right",
                    None: "left"}
        bad = []
        for pid in _ok_probes():
            p = _truth()["probes"][pid]
            svg = p["svg"]
            r = _draw(mode, _probe_spec(p))
            labels = [q["sub"][0] for q in p["panels"] if q["sub"]]
            lab_y = [t["y"] for t in svg if t["text"] in labels]
            # The fixture keeps no numeric text: a numeric label is not
            # in its SVG list, and the first label that is decides.
            t = next((t for t in svg if t["text"] in labels), None)
            # bp07's subtitle(, ring(0) pos(1)) moves the label inside
            # the plot region, which dash names and does not draw (P2.4).
            if t is not None and r.panels and pid != "bp07":
                f = next(f for f in r.panels
                         if panel_label(f).split("\n")[0] == t["text"])
                got = panel_label_title(f).align
                if got != align_of[t["anchor"]]:
                    bad.append((pid, t["text"], got, t["anchor"]))
            for cell, side in ((r.head, "above"), (r.foot, "below")):
                if cell is None:
                    continue
                models = [cell.title] + list(cell.above) + list(cell.below) \
                    + list(cell.center)
                for m in models:
                    text = str(getattr(m, "text", "") or "")
                    if not text or type(m).__name__ not in ("Title", "Label"):
                        continue
                    first = text.split("\n")[0]
                    t = next((t for t in svg if t["text"] == first), None)
                    if t is None:
                        bad.append((pid, first, "not in the SVG", ""))
                        continue
                    want_side = ("above" if lab_y and t["y"] < min(lab_y)
                                 else "below")
                    got_align = getattr(m, "align", None) or \
                        str(m.anchor).split("_")[-1]
                    if side != want_side or got_align != align_of[t["anchor"]]:
                        bad.append((pid, first, (side, got_align),
                                    (want_side, t["anchor"])))
        assert not bad, "\n".join("%s %r: dash %r, twoway %r" % b
                                  for b in bad)


# ---------------------------------------------------------------------------
# Regression tests beyond the fixture's rows
# ---------------------------------------------------------------------------
class TestAStringMissingPanel:
    def test_the_build_time_count_leaves_it_out(self):
        """The served build counts by(s) as 2 groups (D, F): the "" group
        is not a panel, so a limit of 2 says nothing."""
        spec = _spec({"by": "s"})
        _tag, sp, dp = _write(spec)
        dr._dash_reset_notes()
        b = dr.ServerAppBuilder(sp, dp)
        b.limits = dict(b.limits, by_groups=2)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            b._plan_by_groups()
        assert not [w for w in caught if "groups" in str(w.message)], \
            [str(w.message) for w in caught]


@pytest.mark.parametrize("mode", _MODES)
class TestThePanelLabelIsItsOwnRow:
    def test_the_label_row_is_centred_and_not_bold(self, mode):
        """title("T") by(foreign): each panel keeps title T and draws its
        label as an unbolded row in fig.above; no text holds the em dash
        the old join wrote."""
        r = _draw(mode, _spec({"title": '"T"', "by": "foreign"}))
        assert [f.title.text for f in r.panels] == ["T", "T"]
        for f in r.panels:
            t = panel_label_title(f)
            assert t in f.above and t.text_font_style == "normal"
        texts = [m.text for root in r.roots for m in root.references()
                 if type(m).__name__ == "Title"]
        assert not [t for t in texts if "—" in str(t)]


@pytest.mark.parametrize("mode", _MODES)
class TestTheOverallText:
    def test_text_sub_options_are_not_named_but_capitals_are(self, mode):
        """by()'s title/subtitle/note/caption raise no by() sub-option
        note; TITLE("Xq"), which twoway refuses, is still named and never
        drawn (until by()'s refusals land)."""
        r = _draw(mode, _spec({"by": 'foreign, ti("X") sub("S") note("N") '
                                     'cap("C") TITLE("Xq")'}))
        named = [n for n in r.notes if "by() sub-option" in n]
        assert len(named) == 1 and 'TITLE("Xq")' in named[0]
        assert 'ti("X")' not in named[0] and 'note("N")' not in named[0]
        texts = sum((chrome_texts(c) for c in (r.head, r.foot) if c), [])
        assert "Xq" not in texts and sorted(texts) == ["C", "N", "S", "X"]

    def test_a_subtitle_sub_option_is_named_once(self, mode):
        """subtitle(, ring(0) pos(1) nobexpand) keeps the labels and names
        what dash cannot draw once for the graph, not once per panel."""
        r = _draw(mode, _spec({"subtitle": ", ring(0) pos(1) nobexpand",
                               "by": "foreign"}))
        assert [panel_label(f) for f in r.panels] == ["Domestic", "Foreign"]
        named = [n for n in r.notes if "ring(0)" in n]
        assert len(named) == 1, r.notes


@pytest.mark.parametrize("mode", _MODES)
class TestTheGrid:
    def test_cells_and_the_save_tool(self, mode):
        """The head cell spans row 0, the foot the row after the panels,
        both over every column; the grid keeps one SaveTool."""
        from bokeh.models import GridPlot, SaveTool
        r = _draw(mode, _spec({"by": 'foreign, title("X")'}))
        (grid,) = [m for root in r.roots for m in root.references()
                   if isinstance(m, GridPlot)
                   and any(c[0] is r.head for c in m.children)]
        kids = {getattr(c[0], "name", None): tuple(c[1:])
                for c in grid.children}
        # Flipped (WP-30 P1.15c): the axis titles are drawn once, the y
        # title in a column of its own left of the panels and the x title
        # in a row under them (twoway's l1title and b1title, probe p01), so
        # the head and foot span four columns (the stacked view's
        # one-pixel ruler takes the last) and the foot is one row lower.
        assert kids["dash_by_head"] == (0, 0, 1, 4)
        assert kids["dash_by_ytitle"] == (1, 0, 1, 1)
        assert kids["dash_by_xtitle"] == (2, 1, 1, 2)
        assert kids["dash_by_ruler"] == (1, 3, 1, 1)
        assert kids["dash_by_foot"] == (3, 0, 1, 4)
        assert type(r.head).__name__ == "Plot"
        saves = [t for t in grid.toolbar.tools if isinstance(t, SaveTool)]
        assert len(saves) == 1

    def test_no_missing_renderers_warning(self, mode, caplog):
        """A chrome cell carries an invisible Span: no W-1000 is logged."""
        from bokeh.embed import file_html
        from bokeh.resources import INLINE
        r = _draw(mode, _spec({"by": 'foreign, title("X")'}))
        with caplog.at_level(logging.WARNING, logger="bokeh.core.validation"):
            file_html(r.roots[0], INLINE, "t")
        assert "W-1000" not in caplog.text


@pytest.mark.parametrize("mode", _MODES)
class TestAfterAFilterMove:
    def test_the_text_is_unchanged(self, mode):
        """After a served filter move every label and chrome text is the
        same; on the saved page no callback carries a label or a cell."""
        spec = _spec({"title": '"T"', "by": 'foreign, title("X")'},
                     filt="rep78")
        r = _draw(mode, spec)
        before = ([panel_label(f) for f in r.panels],
                  chrome_texts(r.head), chrome_texts(r.foot))
        if mode == "served":
            from test_mode_parity import _fire, _widgets_of
            (w,) = [x for x in _widgets_of(r.extra)
                    if type(x).__name__ == "Select"]
            _fire(w, w.options[1][0])
            assert ([panel_label(f) for f in r.panels],
                    chrome_texts(r.head), chrome_texts(r.foot)) == before
        else:
            from bokeh.models import CustomJS
            held = {id(panel_label_title(f)) for f in r.panels} | \
                {id(r.head), id(r.foot)}
            for cb in [m for m in r.roots[0].references()
                       if isinstance(m, CustomJS)]:
                assert "dash_by_" not in cb.code
                for v in dict(cb.args).values():
                    vals = v if isinstance(v, (list, tuple)) else [v]
                    assert not {id(x) for x in vals} & held


# ---------------------------------------------------------------------------
# Unit tests (one per new function)
# ---------------------------------------------------------------------------
class TestTheMissingRule:
    def test_values(self):
        """_dash_by_value_missing: "" and every NA are missing; blanks,
        numbers, text and non-scalars are not; it never raises."""
        f = dr._dash_by_value_missing
        assert [f(v) for v in ("", None, float("nan"), pd.NaT, np.nan)] \
            == [True] * 5
        assert [f(v) for v in (" ", 0, "D", [1])] == [False] * 4

    def test_frames(self):
        """_dash_by_nonmissing drops a NaN row and a "" row, keeps " ",
        gives an all-missing frame zero rows, and is fast."""
        df = pd.DataFrame({"a": [1.0, np.nan, 2.0, 3.0],
                           "s": ["x", "y", "", " "]})
        assert list(dr._dash_by_nonmissing(df, ["a", "s"]).index) == [0, 3]
        e = pd.DataFrame({"e": ["", ""]})
        out = dr._dash_by_nonmissing(e, ["e", "nothere"])
        assert len(out) == 0 and list(out.columns) == ["e"]
        big = pd.DataFrame({"s": ["a", ""] * 100000})
        t0 = time.perf_counter()
        assert len(dr._dash_by_nonmissing(big, ["s"])) == 100000
        assert time.perf_counter() - t0 < 1.0


class TestTheTextOptions:
    def test_keys(self):
        """_dash_by_text_key: twoway's lower-case spellings only."""
        f = dr._dash_by_text_key
        assert [f(t) for t in ('ti("X")', 'sub("S")', 'note("N")',
                               'cap("C")')] == \
            ["title", "subtitle", "note", "caption"]
        assert [f(t) for t in ('no("N")', 'TITLE("X")', "title",
                               't("X")')] == [None] * 4

    def test_merge(self):
        """_dash_by_text_options merges repeats as twoway does (a07, a08,
        a13) and keeps quoted text whole."""
        f = dr._dash_by_text_options
        assert f('foreign, note("A") note("B")')["note"] == '"B"'
        assert f('foreign, note("A") note(, size(large))')["note"] == \
            '"A", size(large)'
        assert f('foreign, title("X") title("Y")')["title"] == '"Y"'
        assert f('foreign, note("")')["note"] == '""'
        assert f('foreign, title(`"a "b" c"\')')["title"] == '`"a "b" c"\''
        assert f("foreign, title(Bob's cars) cols(2)")["title"] == \
            "Bob's cars"
        assert f("foreign") == {"title": "", "subtitle": "", "note": "",
                                "caption": ""}

    def test_a_megabyte_is_read_at_once(self):
        t0 = time.perf_counter()
        dr._dash_by_text_options("foreign, " + 'title("x") ' * 90000)
        assert time.perf_counter() - t0 < 2.0


class TestTheNoteList:
    def test_lists(self):
        """_dash_by_note_list: twoway's SetByList."""
        lab = {"foreign": "Car origin", "rep78": "Repair record 1978",
               "headroom": "Headroom (in.)", "u": "", "fb": "   "}
        f = dr._dash_by_note_list
        assert f([], lab) == ""
        assert f(["foreign"], lab) == "Car origin"
        assert f(["u"], lab) == "u"
        assert f(["fb"], lab) == "   "
        assert f(["foreign", "rep78"], lab) == \
            "Car origin and Repair record 1978"
        assert f(["foreign", "rep78", "headroom"], lab) == \
            "foreign, Repair record 1978, and Headroom (in.)"


class TestThePanelLabel:
    def test_unit(self):
        """_dash_by_panel_label: none for removed text; size() and color()
        style it; without a scheme 13px #444444; named dash_by_label."""
        from bokeh.plotting import figure
        fig = figure()
        assert dr._dash_by_panel_label(fig, "D", {"subtitle": '""'}) is None
        assert not fig.above
        t = dr._dash_by_panel_label(fig, "D", {})
        assert (t.name, t.text, t.text_font_size, t.text_color, t.align) == \
            ("dash_by_label", "D", "13px", "#444444", "center")
        t = dr._dash_by_panel_label(
            fig, "D", {"subtitle": ", size(large) color(red)"})
        assert t.text_color == dr._textbox_color({"color": "red"}, None)
        assert t.text_font_size == dr._textbox_size({"size": "large"},
                                                    "13px")


class TestTheChromeCells:
    def test_a_cell_draws_no_frame_and_no_warning(self, caplog):
        """_dash_by_text_cell: a bare Plot with no axis, grid or tool, one
        invisible Span, the scheme's graph-region colour, no W-1000."""
        from bokeh.embed import file_html
        from bokeh.resources import INLINE
        sch = dr.SchemeParser("stcolor")
        cell = dr._dash_by_text_cell(sch, "dash_by_head")
        assert type(cell).__name__ == "Plot"
        assert not cell.renderers and cell.toolbar_location is None
        assert not cell.toolbar.tools
        assert not [m for m in cell.left + cell.below
                    if "Axis" in type(m).__name__]
        (span,) = cell.center
        assert type(span).__name__ == "Span" and span.visible is False
        assert cell.background_fill_color == sch.background_color
        with caplog.at_level(logging.WARNING, logger="bokeh.core.validation"):
            file_html(cell, INLINE, "t")
        assert "W-1000" not in caplog.text

    def test_head_and_foot(self):
        """_dash_by_chrome: p11 splits head/foot; note("") alone draws
        nothing; economist's note goes to the head."""
        lab = {"foreign": "Car origin"}
        c = dr._dash_by_chrome(
            {"by": 'foreign, title("X") subtitle("S") note("N") '
                   'caption("C")'}, ["foreign"], lab, dr.SchemeParser("stcolor"))
        assert chrome_texts(c["head"]) == ["X", "S"]
        assert chrome_texts(c["foot"]) == ["N", "C"]
        assert dr._dash_by_chrome({"by": 'foreign, note("")'}, ["foreign"],
                                  lab) == {"head": None, "foot": None}
        e = dr._dash_by_chrome({"by": "foreign"}, ["foreign"], lab,
                               dr.SchemeParser("economist"))
        assert e["foot"] is None
        assert chrome_texts(e["head"]) == ["Graphs by Car origin"]

    def test_frame_grid_positions(self):
        """_dash_by_frame_grid: head only, foot only, both, neither, an
        empty grid; 3- and 5-tuples kept."""
        a, b, h, f = object(), object(), object(), object()

        def grid(kids):
            return types.SimpleNamespace(children=list(kids))
        kids = [(a, 0, 0), (b, 0, 1, 1, 1)]
        assert dr._dash_by_frame_grid(grid(kids), None, 2).children == kids
        assert dr._dash_by_frame_grid(
            grid(kids), {"head": h, "foot": f}, 2).children == \
            [(h, 0, 0, 1, 2), (a, 1, 0), (b, 1, 1, 1, 1), (f, 2, 0, 1, 2)]
        assert dr._dash_by_frame_grid(
            grid(kids), {"head": h, "foot": None}, 2).children == \
            [(h, 0, 0, 1, 2), (a, 1, 0), (b, 1, 1, 1, 1)]
        assert dr._dash_by_frame_grid(
            grid(kids), {"head": None, "foot": f}, 2).children == \
            kids + [(f, 1, 0, 1, 2)]
        assert dr._dash_by_frame_grid(grid([]), {"head": h, "foot": None},
                                      2).children == [(h, 0, 0, 1, 2)]

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_pass_sees_the_cells(self, mode):
        """_dash_by_chrome_figures names g1__by__head/foot, and in both
        modes a TeX pair in by(, title()) reaches the head inert."""
        from bokeh.plotting import figure
        p = figure()
        p._dash_by_chrome = {"head": "H", "foot": None}
        assert dr._dash_by_chrome_figures(
            {"g1__by__0": p, "g2": figure()},
            {"g1": [("g1__by__0", "D")]}) == {"g1__by__head": "H"}
        r = _draw(mode, _spec({"by": r'foreign, title("\(t\)")'}))
        assert r.head.title.text != r"\(t\)"
        assert getattr(r.head.title, dr._DASH_GRAPH_TEXT_DONE, False)
