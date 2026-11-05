"""dash.sthlp's Resource limits, Faceting with by() and Marker Label
Options, claim by claim (ROADMAP WP-23, AC-23.1), in both render modes.

Every claim the help makes about twoway was measured against twoway itself
(StataNow 19.5 MP, the console binary, ``set graphics off``, each picture
exported to SVG and its ``<text>`` and ``<circle>`` elements read); the
live measurements are test_help_claims_5.cscript's HC5 cases.  What they
found, and what this file holds dash to:

1. Where a label sits around its point.  twoway puts a label beyond the
   marker in the clock direction, the edge or corner of the text nearest
   the point on that direction: at 12 its bottom centre, at 6 its top
   centre, at 3 its left middle, at 9 its right middle, at 1 and 2 its
   bottom-left corner, at 4 and 5 its top-left, at 7 and 8 its top-right,
   at 10 and 11 its bottom-right, and at 0 the label is centred on the
   point.  dash anchored every label at its bottom-left corner, so
   mlabposition(9) started 4 pixels left of the point and ran back across
   it, mlabposition(6) sat on the point, and 12 and 0 hung up and to the
   right -- where the help said 9 = left, 6 = below and 12 = above.
2. mlabgap().  twoway widens the gap along the clock direction -- measured,
   mlabgap(10) moves a 9 o'clock label 324 of the graph's 3,240 units
   further LEFT and changes nothing at 0.  dash added the gap to both
   offsets whatever the position: mlabgap(10) at 9 o'clock moved the label
   right, over its point, and up; mlabgap(0) still moved it one pixel.
3. A clock position twoway does not recognise -- 13, 2.5, 03, 3.0, -1,
   abc -- is noted ("named style 13 not found in class clockdir, default
   attributes used") and the label drawn at 12 o'clock, under s2color,
   s2mono, s1mono, stcolor and economist alike.  dash drew it at 3 and
   said "using 3 (right)"; 03 it drew at 3 without a word.
4. by() panel titles.  twoway titles a panel with the value's label, else
   with the value as Stata writes a number (3, .25, 1234567) whatever its
   display format -- measured, %9.2f and %12.0fc change nothing.  dash
   wrote an unlabelled value as a Python float, 3.0, in both modes, so the
   help's own example "Domestic / 3" was drawn "Domestic / 3.0"; and the
   saved page applied a %f display format BEFORE the value labels, so a
   labelled variable with a %9.2f format lost its labels ("3.00" where the
   label is "Three") while the served app kept them.
5. Dates.  The saved page writes a date variable's marker labels and panel
   titles as dates; the served app wrote the Stata numbers under them
   (14612.0), read a value label attached to a date variable, and applied
   an mlabformat() to one without the note the saved page gives.
6. The large-data note, documented "above 1,000,000 values", came at
   1,000,000.

The served app copies GlyphMapper and the shared helpers by source, so each
drawing check below renders the same spec through DashRenderer (the saved
page) and through ServerAppBuilder and make_document (the served app).
"""
import itertools
import json
import math
import os
import re
import sys
import tempfile
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import BoxSelectTool, ColumnDataSource, GridPlot, LabelSet
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from by_panel_probe import by_grid, chrome_texts, panel_label  # noqa: E402
from conftest import load_app  # noqa: E402

_SEQ = itertools.count()
_TMP = tempfile.mkdtemp(prefix="dash_help_claims_5_")
_HELP = os.path.join(_HERE, "..", "dash.sthlp")


# ===========================================================================
# Inputs as dash.ado writes them, rendered both ways
# ===========================================================================

from conftest import render_models  # noqa: E402
from conftest import drawn_renderers  # noqa: E402


def _auto():
    """Twelve cars: auto's first rows, with rep78 missing twice."""
    return pd.DataFrame({
        "mpg": [22.0, 17.0, 22.0, 20.0, 15.0, 18.0, 26.0, 20.0, 16.0, 19.0,
                14.0, 14.0],
        "weight": [2930.0, 3350.0, 2640.0, 3250.0, 4080.0, 3670.0, 2230.0,
                   3280.0, 3880.0, 3400.0, 4330.0, 3900.0],
        "price": [4099.0, 4749.0, 3799.0, 4816.0, 7827.0, 5788.0, 4453.0,
                  5189.0, 10372.0, 4082.0, 11385.0, 14500.0],
        "foreign": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                    1.0],
        "rep78": [3.0, 3.0, np.nan, 3.0, 4.0, 3.0, np.nan, 3.0, 3.0, 3.0,
                  4.0, 5.0],
        "make": ["AMC Concord", "AMC Pacer", "AMC Spirit", "Buick Century",
                 "Buick Electra", "Buick LeSabre", "Buick Opel",
                 "Buick Regal", "Buick Riviera", "Buick Skylark",
                 "Cad. Deville", "Cad. Eldorado"],
    })


_ORIGIN = {"0": "Domestic", "1": "Foreign"}


def _payload(df, value_labels=None, label_names=None):
    """The data file as jsonio writes it: one object per observation, a
    missing value as the string "null", the value labels keyed by the
    VARIABLE's name (measured: ``jsonio out ... metaprint(vallabs
    labelnames)`` writes ``{"em": {"1": "ONE"}}`` for a variable em carrying
    the label set eml), strings marked in variableIsString."""
    names = list(df.columns)
    rows = []
    for _, r in df.iterrows():
        row = {}
        for c in names:
            v = r[c]
            if isinstance(v, str):
                row[c] = v
            elif v is None or (isinstance(v, float) and math.isnan(v)):
                row[c] = "null"
            else:
                row[c] = float(v)
        rows.append(row)
    is_str = {c: bool(pd.api.types.is_string_dtype(df[c])
                      and not pd.api.types.is_numeric_dtype(df[c]))
              for c in names}
    return {"values": rows, "variableNames": names,
            "variableLabels": {c: "" for c in names},
            "valueLabels": dict(value_labels or {}),
            "valueLabelNames": dict(label_names or {}),
            "variableIsString": is_str,
            "numberOfRecords": len(rows), "numberOfVariables": len(names)}


def _spec(graphs, build=None, kpis=None):
    """A master spec: ``graphs`` is ``[(name, plots, graph_options)]``."""
    gs = []
    for name, plots, go in graphs:
        g = {"name": name}
        g.update(go or {})
        gs.append({"name": name, "graph_options": g, "options": dict(g),
                   "plots": plots, "if_expr": "", "in_expr": ""})
    bo = {"layout": "auto", "link": "", "filter": "", "theme": "",
          "scheme": "", "session_scheme": "", "title": "", "subtitle": "",
          "registry": " ".join([g[0] for g in graphs]
                               + [k["name"] for k in (kpis or [])]),
          "tabs": "", "filter_position": "top", "level": "95",
          "formats": {}}
    bo.update(build or {})
    return {"graphs": gs, "kpis": list(kpis or []), "build_options": bo}


def _scatter(**options):
    return {"type": "scatter", "yvar": "mpg", "xvar": "weight",
            "options": dict(options)}


def _write(spec, payload):
    tag = next(_SEQ)
    sp = os.path.join(_TMP, f"spec_{tag}.json")
    dp = os.path.join(_TMP, f"data_{tag}.json")
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    with open(dp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)
    return tag, sp, dp


def _both(spec, payload):
    """``(saved renderer, served document, saved notes, served notes)``.

    The served notes are the build's and the session's together: a note a
    served app raises at build time is the one the Stata user sees."""
    _, sp, dp = _write(spec, payload)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r = dr.DashRenderer(sp, dp)
        render_models(r)
    # A ResourceWarning is the garbage collector closing a file some
    # earlier test in this worker leaked; it is no note of dash's.
    saved = sorted({str(w.message) for w in caught
                    if not issubclass(w.category, ResourceWarning)})
    tag, sp, dp = _write(spec, payload)
    ap = os.path.join(_TMP, f"app_{tag}.py")
    with warnings.catch_warnings(record=True) as built:
        warnings.simplefilter("always")
        dr.ServerAppBuilder(sp, dp).build(ap)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mod = load_app(ap, f"_hc5_{tag}", draw=False)
    with warnings.catch_warnings(record=True) as session:
        warnings.simplefilter("always")
        doc = Document()
        mod.make_document(doc)
    served = sorted({str(w.message) for w in list(built) + list(session)
                     if not issubclass(w.category, ResourceWarning)})
    return r, doc, saved, served


def _walk(doc):
    """Every model reachable from the document's roots, in layout order."""
    out, seen = [], set()

    def visit(m):
        if isinstance(m, (list, tuple)):
            for x in m:
                if x is not None and not isinstance(x, (int, float, str)):
                    visit(x)
            return
        if m is None or id(m) in seen:
            return
        seen.add(id(m))
        out.append(m)
        for attr in ("children", "tabs", "child"):
            k = getattr(m, attr, None)
            if k is not None:
                visit(k)

    for root in doc.roots:
        visit(root)
    return out


def _served_figures(doc):
    return [m for m in _walk(doc) if type(m).__name__ == "figure"]


def _labelsets(fig):
    return [x for x in (list(fig.center) + list(fig.above) + list(fig.below)
                        + list(fig.left) + list(fig.right))
            if isinstance(x, LabelSet)]


def _field(spec):
    if isinstance(spec, str):
        return spec
    if isinstance(spec, dict):
        return spec.get("field")
    return getattr(spec, "field", None)


def _drawn(value):
    """The text BokehJS draws for one value: it writes `${value}`, so a
    float 22.0 is drawn "22"."""
    if isinstance(value, float):
        if math.isnan(value):
            return "NaN"
        if value.is_integer() and abs(value) < 1e21:
            return str(int(value))
        return repr(value)
    return str(value)


def _texts(ls):
    return [_drawn(v) for v in ls.source.data[_field(ls.text)]]


def _one_labelset(fig):
    sets = _labelsets(fig)
    assert len(sets) == 1, sets
    return sets[0]


def _pair_figures(r, doc):
    """(saved figure, served figure) of a one-graph, unfaceted spec."""
    saved = list(r.figures.values())
    served = _served_figures(doc)
    assert len(saved) == 1 and len(served) == 1, (list(r.figures), served)
    return saved[0], served[0]


def _grid_panels(root):
    """The panels of the one by() grid under *root*, as ``[(row, col,
    label)]`` sorted by place.  Flipped (WP-30 P1.15a): read the title,
    which held the label, and took every grid child for a panel; twoway
    keeps the graph's title on every panel and draws the label as a row
    of its own, and the grid now holds the overall text's chrome cells."""
    panels, _head, _foot = by_grid(root)
    return [(row, col, panel_label(fig)) for row, col, fig in panels]


def _saved_panels(r):
    return _grid_panels(r._last_layout_root)


def _served_panels(doc):
    (root,) = [x for x in doc.roots
               if any(isinstance(m, GridPlot) for m in x.references())]
    return _grid_panels(root)


def _help_section(start_marker, end_marker):
    with open(_HELP, encoding="utf-8") as fh:
        text = fh.read()
    sec = text[text.index(start_marker):text.index(end_marker)]
    # SMCL wraps its lines; the words are what a reader reads.
    return " ".join(sec.split())


# ===========================================================================
# 1. Where a label sits: twoway's anchor at each clock position
# ===========================================================================

#: The corner or edge of the text on the clock direction, measured from
#: twoway's SVG (text-anchor start/middle/end; the baseline against the
#: marker centre): Bokeh's text_align and text_baseline for each position.
_ANCHOR = {
    0: ("center", "middle"),
    1: ("left", "bottom"), 2: ("left", "bottom"),
    3: ("left", "middle"),
    4: ("left", "top"), 5: ("left", "top"),
    6: ("center", "top"),
    7: ("right", "top"), 8: ("right", "top"),
    9: ("right", "middle"),
    10: ("right", "bottom"), 11: ("right", "bottom"),
    12: ("center", "bottom"),
}


# WP-30 P1.12a: twoway's label offset, as measured in Evidence E5, is
# (marker radius + gap) along the clock's unit vector.  Under s2color the
# default marker is symbolsize medium, 1.52778 rs (1 rs = 2.88 pt, 1 pt =
# 4/3 px), so its radius is half that; the default gap is gsize label_gap,
# 2 pt; one Stata size unit (rs) is 2.88 pt = 3.84 px.
_R = 1.52778 * 2.88 * (4 / 3) / 2      # 2.93334 px
_GAP = 2 * (4 / 3)                     # 2.66667 px
_U = 2.88 * (4 / 3)                    # 3.84 px per Stata unit
_DEF = _R + _GAP                       # 5.6 px


def _direction(p):
    """The clock direction of position *p* as signs (x, y), y up."""
    if p == 0:
        return (0, 0)
    ang = math.radians(90 - 30 * p)
    sx = 0 if abs(math.cos(ang)) < 1e-9 else (1 if math.cos(ang) > 0 else -1)
    sy = 0 if abs(math.sin(ang)) < 1e-9 else (1 if math.sin(ang) > 0 else -1)
    return (sx, sy)


def _sign(v):
    return 0 if v == 0 else (1 if v > 0 else -1)


def _labelled(**options):
    """Both modes' label set for a scatter labelled by make."""
    opts = {"mlabel": "make"}
    opts.update(options)
    r, doc, saved, served = _both(_spec([("g1", [_scatter(**opts)], {})]),
                                  _payload(_auto()))
    a, b = _pair_figures(r, doc)
    return _one_labelset(a), _one_labelset(b), saved, served


class TestTheClockPositionPlacesTheLabelAsTwowayDoes:
    """HC5-04 measured twoway's placement; this holds both modes to it."""

    @pytest.mark.parametrize("p", list(range(13)))
    def test_the_label_is_anchored_where_twoway_anchors_it(self, p):
        for ls in _labelled(mlabposition=str(p))[:2]:
            assert (ls.text_align, ls.text_baseline) == _ANCHOR[p], (
                f"mlabposition({p}) anchored the text at "
                f"{ls.text_align}/{ls.text_baseline}; twoway anchors it "
                f"at {_ANCHOR[p]}")
            assert (_sign(ls.x_offset), _sign(ls.y_offset)) == \
                _direction(p), (p, ls.x_offset, ls.y_offset)

    def test_the_default_is_three_oclock(self):
        for ls in _labelled()[:2]:
            assert (ls.text_align, ls.text_baseline) == _ANCHOR[3]
            # WP-30 P1.12a (Evidence E5, twoway measured): radius 2.93334
            # + default gap 2pt (2.66667 px) at 3 o'clock, not 4 px.
            assert ls.x_offset == pytest.approx(_DEF)
            assert ls.y_offset == 0

    # WP-30 P1.12a (Evidence E5, twoway measured): the offset is
    # (radius + gap) along the clock's unit vector, the gap in Stata units:
    # mlabgap(10) is 10 x 3.84 px, so 2.93334 + 38.4 px from the centre.
    @pytest.mark.parametrize("p,want", [
        (3, (_R + 38.4, 0)), (9, (-(_R + 38.4), 0)),
        (12, (0, _R + 38.4)), (6, (0, -(_R + 38.4))),
        (0, (0, 0)),
        (1, ((_R + 38.4) / 2, (_R + 38.4) * math.sqrt(3) / 2)),
        (2, ((_R + 38.4) * math.sqrt(3) / 2, (_R + 38.4) / 2)),
        (7, (-(_R + 38.4) / 2, -(_R + 38.4) * math.sqrt(3) / 2)),
    ])
    def test_mlabgap_widens_the_gap_along_the_clock_direction(self, p, want):
        """HC5-05: twoway's mlabgap(10) moves a 9 o'clock label further
        left and does nothing at 0.  The gap is in Stata's size units."""
        for ls in _labelled(mlabposition=str(p), mlabgap="10")[:2]:
            assert ls.x_offset == pytest.approx(want[0]), (p, ls.x_offset)
            assert ls.y_offset == pytest.approx(want[1]), (p, ls.y_offset)

    # WP-30 P1.12a (Evidence E5, twoway measured): the gap is Stata units
    # (3.84 px each) added to the marker radius 2.93334 px; small and tiny
    # are gsize 2.777 and 1.3888 units.
    @pytest.mark.parametrize("gap,want", [
        ("0", _R), ("-2", _R - 2 * _U), ("2.5", _R + 2.5 * _U),
        ("small", _R + 2.777 * _U), ("tiny", _R + 1.3888 * _U),
    ])
    def test_mlabgap_is_in_statas_units(self, gap, want):
        """A zero gap leaves the label at the marker's edge, a negative one
        moves it toward the point (twoway accepts mlabgap(-5): measured, the
        label crosses the marker), a fraction is kept, and a size keyword is
        read from Stata's gsize ladder."""
        a, b, saved, served = _labelled(mlabgap=gap)
        assert not [m for m in saved + served if "mlabgap" in m], saved
        for ls in (a, b):
            assert (ls.x_offset, ls.y_offset) == (
                pytest.approx(want, rel=1e-4), 0)

    @pytest.mark.parametrize("raw", ["13", "2.5", "03", "3.0", "-1", "abc"])
    def test_a_position_twoway_does_not_recognise_is_drawn_at_twelve(
            self, raw):
        """HC5-03: twoway notes each and draws the label at 12 o'clock."""
        a, b, saved, served = _labelled(mlabposition=raw)
        want = [f"dash: mlabposition({raw}) is not a recognised clock "
                f"position; using 12 (above)."]
        assert [m for m in saved if "mlabposition" in m] == want, saved
        assert [m for m in served if "mlabposition" in m] == want, served
        for ls in (a, b):
            assert (ls.text_align, ls.text_baseline) == _ANCHOR[12]
            # WP-30 P1.12a (Evidence E5, twoway measured): 12 o'clock is
            # radius + default gap, 2.93334 + 2.66667 px, straight up.
            assert ls.x_offset == 0
            assert ls.y_offset == pytest.approx(_DEF)

    def test_every_label_of_a_two_ended_type_is_placed_alike(self):
        """rcapsym labels both ends, each with the same anchor."""
        plot = {"type": "rcapsym", "yvar1": "mpg", "yvar2": "price",
                "xvar": "weight",
                "options": {"mlabel": "make", "mlabposition": "9"}}
        r, doc, _, _ = _both(_spec([("g1", [plot], {})]), _payload(_auto()))
        for fig in _pair_figures(r, doc):
            sets = _labelsets(fig)
            assert len(sets) == 2
            for ls in sets:
                assert (ls.text_align, ls.text_baseline) == _ANCHOR[9]
                # WP-30 P1.12a (Evidence E5, twoway measured): 9 o'clock is
                # -(radius + default gap), -(2.93334 + 2.66667) px.
                assert ls.x_offset == pytest.approx(-_DEF)
                assert ls.y_offset == 0

    def test_an_immediate_label_takes_its_own_clock_position(self):
        """scatteri's per-point clock positions go through the same
        placement: 6 is anchored at the text's top centre."""
        plot = {"type": "scatteri", "values": [[20.0, 3000.0, "A", 6],
                                               [30.0, 4000.0, "B", 9]],
                "options": {}}
        r, doc, _, _ = _both(_spec([("g1", [plot], {})]), _payload(_auto()))
        for fig in _pair_figures(r, doc):
            got = sorted((ls.text_align, ls.text_baseline)
                         for ls in _labelsets(fig))
            assert got == sorted([_ANCHOR[6], _ANCHOR[9]]), got


class TestTheClockHelpers:
    """GlyphMapper's placement table and gap reader, on their own."""

    def test_the_table_covers_the_thirteen_positions(self):
        table = dr.GlyphMapper._MLABEL_CLOCK
        assert sorted(table) == list(range(13))
        for p, (base, unit, anchor) in table.items():
            assert anchor == _ANCHOR[p], p
            assert (_sign(base[0]), _sign(base[1])) == _direction(p), p
            assert math.hypot(*unit) == pytest.approx(0 if p == 0 else 1)

    # WP-30 P1.12a (Evidence E5, twoway measured): the reader returns
    # signed px at 3.84 px per Stata unit; small is gsize 2.777 units and
    # *2 is twice the 2pt default gap.  HUGE is not a gsize name (case).
    @pytest.mark.parametrize("raw,want", [
        ("10", 10 * 3.84), (" 3 ", 3 * 3.84), ("-4", -4 * 3.84),
        ("0", 0.0), (".5", 0.5 * 3.84), ("1e2", 100 * 3.84),
        ("small", 2.777 * 3.84), ("*2", 2 * 2 * (4 / 3)),
    ])
    def test_the_gap_reader(self, raw, want):
        assert dr.GlyphMapper._mlabel_gap_px(raw) == pytest.approx(want)

    @pytest.mark.parametrize("raw", [
        # WP-30 P1.12a (Evidence E5): *2 is now read (above); HUGE is
        # refused, as Stata's size names are lower case.
        "abc", "", "inf", "-inf", "nan", "1e400", "HUGE", "\u0665", "5px",
        "1" * 400,
    ])
    def test_the_gap_reader_refuses_what_is_not_a_gap(self, raw):
        with pytest.raises(ValueError):
            dr.GlyphMapper._mlabel_gap_px(raw)


# ===========================================================================
# 2. by(): panel titles, Total, missing, arrangement, sub-options, link()
# ===========================================================================

def _by(by, df=None, value_labels=None, label_names=None, formats=None,
        build=None, graph_opts=None):
    go = {"by": by}
    go.update(graph_opts or {})
    b = {"formats": dict(formats or {})}
    b.update(build or {})
    return _both(_spec([("g1", [_scatter()], go)], build=b),
                 _payload(df if df is not None else _auto(),
                          value_labels, label_names))


class TestThePanelTitles:
    """HC5-07 measured twoway's titles; the help promises value labels and
    composite titles such as "Domestic, 3".  Flipped (WP-30 P1.15a):
    "Domestic / 3" was wrong because twoway joins labels ", "."""

    def test_an_unlabelled_value_is_written_as_stata_writes_it(self):
        r, doc, _, _ = _by("rep78")
        for panels in (_saved_panels(r), _served_panels(doc)):
            assert [t for _, _, t in panels] == ["3", "4", "5"], panels

    def test_the_helps_composite_example(self):
        r, doc, _, _ = _by("foreign rep78",
                           value_labels={"foreign": dict(_ORIGIN)},
                           label_names={"foreign": "origin"})
        want = ["Domestic, 3", "Domestic, 4", "Foreign, 3",
                "Foreign, 4", "Foreign, 5"]
        for panels in (_saved_panels(r), _served_panels(doc)):
            assert [t for _, _, t in panels] == want, panels

    def test_value_labels_are_used_whatever_the_display_format(self):
        """A %9.2f by() variable with a label on 3: twoway titles its
        panels 3 -> "Three", 4 -> "4"; the saved page drew "3.00"."""
        r, doc, _, _ = _by("rep78",
                           value_labels={"rep78": {"3": "Three"}},
                           label_names={"rep78": "rl"},
                           formats={"rep78": "%9.2f"})
        for panels in (_saved_panels(r), _served_panels(doc)):
            assert [t for _, _, t in panels] == ["Three", "4", "5"], panels

    def test_a_display_format_plays_no_part(self):
        """twoway: by(big) with %12.0fc is titled 1234567, not 1,234,567."""
        df = _auto()
        df["big"] = [1234567.0 + (i % 2) for i in range(len(df))]
        r, doc, _, _ = _by("big", df=df, formats={"big": "%12.0fc"})
        for panels in (_saved_panels(r), _served_panels(doc)):
            assert [t for _, _, t in panels] == ["1234567", "1234568"]

    def test_a_fraction_is_written_without_its_leading_zero(self):
        df = _auto()
        df["h"] = [(-0.25, 0.25, 0.75)[i % 3] for i in range(len(df))]
        r, doc, _, _ = _by("h", df=df)
        for panels in (_saved_panels(r), _served_panels(doc)):
            assert [t for _, _, t in panels] == ["-.25", ".25", ".75"]

    def test_a_string_is_its_own_title(self):
        df = _auto()
        df["s"] = ["alpha" if i % 2 else "beta" for i in range(len(df))]
        r, doc, _, _ = _by("s", df=df)
        for panels in (_saved_panels(r), _served_panels(doc)):
            assert [t for _, _, t in panels] == ["alpha", "beta"]

    def test_a_date_is_titled_alike_in_both_modes(self):
        df = _auto()
        df["d"] = [14610.0 + (i % 3) for i in range(len(df))]
        r, doc, _, _ = _by("d", df=df, formats={"d": "%td"})
        saved = [t for _, _, t in _saved_panels(r)]
        served = [t for _, _, t in _served_panels(doc)]
        # Flipped (WP-41 BY-16): 01jan2000 .. was wrong because twoway
        # writes the number (by_label_truth.json D01: 14610, 14611).
        assert saved == served == ["14610", "14611", "14612"], \
            (saved, served)

    def test_the_graphs_title_leads_each_panels(self):
        """Flipped (WP-30 P1.15a): "Cars — Domestic" was wrong because
        twoway keeps title() on every panel and draws the label as a row
        under it (probe p14)."""
        r, doc, _, _ = _by("foreign",
                           value_labels={"foreign": dict(_ORIGIN)},
                           label_names={"foreign": "origin"},
                           graph_opts={"title": "Cars"})
        saved = [f for _, _, f in by_grid(r._last_layout_root)[0]]
        served = _served_figures(doc)
        for figs in (saved, served):
            assert [f.title.text for f in figs] == ["Cars", "Cars"]
            assert [panel_label(f) for f in figs] == ["Domestic", "Foreign"]


class TestTheFacetLabelHelper:
    """``_dash_facet_label`` on its own: the one rule both modes run."""

    _L = {"foreign": {"0": "Domestic", "1": "Foreign"}}
    _N = {"foreign": "origin"}

    @pytest.mark.parametrize("key,want", [
        (3.0, "3"), (0.25, ".25"), (-0.25, "-.25"), (1234567.0, "1234567"),
        (2.5e-12, "2.50000000000e-12"), (np.float64(4.0), "4"),
        # Flipped (WP-30 P1.15a): "Missing" was wrong because twoway
        # writes "(missing)".
        (float("nan"), "(missing)"),
    ])
    def test_one_unlabelled_variable(self, key, want):
        assert dr._dash_facet_label(["rep78"], key) == want

    def test_a_labelled_value_and_an_unlabelled_one(self):
        assert dr._dash_facet_label(["foreign"], 1.0, self._N, self._L) \
            == "Foreign"
        assert dr._dash_facet_label(["foreign"], 2.0, self._N, self._L) \
            == "2"

    def test_two_variables_are_joined(self):
        # Flipped (WP-30 P1.15a): " / " was wrong because twoway joins ", ".
        assert dr._dash_facet_label(["foreign", "rep78"], (0.0, 3.0),
                                    self._N, self._L) == "Domestic, 3"

    def test_the_label_wins_over_a_display_format(self):
        assert dr._dash_facet_label(
            ["r"], 3.0, {"r": "rl"}, {"rl": {"3": "Three"}},
            numeric_formats={"r": "%9.2f"}) == "Three"
        assert dr._dash_facet_label(
            ["r"], 4.0, {"r": "rl"}, {"rl": {"3": "Three"}},
            numeric_formats={"r": "%9.2f"}) == "4"

    def test_a_date_goes_through_the_formatter(self):
        # Flipped (WP-41 BY-16): 01jan2000 was wrong because twoway writes
        # the number (by_label_truth.json D01); subtitleformat(var) still
        # writes the date through the formatter (D02).
        got = dr._dash_facet_label(["d"], 14610.0, date_vars={"d": "td"},
                                   date_formatter=dr._dash_stata_date_text)
        assert got == "14610"
        got = dr._dash_facet_label(["d"], pd.Timestamp("2000-01-01"),
                                   date_vars={"d": "td"},
                                   date_formatter=dr._dash_stata_date_text)
        assert got == "14610"
        got = dr._dash_facet_label(["d"], pd.Timestamp("2000-01-01"),
                                   date_vars={"d": "td"},
                                   date_formatter=dr._dash_stata_date_text,
                                   formats={"d": "%td"},
                                   subtitle_format="var")
        # GAPS2 E3/G6, WP-28 S12: Stata's %td text (was "01 Jan 2000").
        assert got == "01jan2000"

    def test_a_long_number_is_bounded_as_stata_bounds_it(self):
        for v in (1e308, -1e308, 5e-324, 123456789012345678901234567890.0):
            assert len(dr._dash_facet_label(["x"], v)) <= 18, v


class TestTheStataDateText:
    """``_dash_stata_date_text``: a date from either representation."""

    # GAPS2 E3/G6, WP-28 S12: Stata's display text in the full format
    # (was one fixed picture per kind: "01 Jan 2000", "Jan 2000").
    @pytest.mark.parametrize("value,kind,want", [
        (14610.0, "td", "01jan2000"), (14610, "td", "01jan2000"),
        (480.0, "tm", "2000m1"), (2000.0, "ty", "2000"),
        (pd.Timestamp("2000-01-01"), "td", "01jan2000"),
        (np.datetime64("2000-01-01"), "td", "01jan2000"),
        (1262304000000.0, "tc", "01jan2000 00:00:00"),
    ])
    def test_each(self, value, kind, want):
        assert dr._dash_stata_date_text(value, kind) == want
        assert dr._dash_stata_date_text(value, "%" + kind) == want
        if isinstance(value, (int, float)):
            assert want == dr._dash_fmt_text(float(value), "%" + kind)

    @pytest.mark.parametrize("value", [float("nan"), None, pd.NaT])
    def test_missing_is_a_dot(self, value):
        assert dr._dash_stata_date_text(value, "td") == "."

    def test_a_date_past_the_calendar_is_written_as_a_number(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # GAPS2 E3/G6, WP-28 S12: a number past the calendar is
            # written as _dash_fmt_text writes it (was ".").
            assert dr._dash_stata_date_text(1e12, "td") == \
                dr._dash_fmt_text(1e12, "%td")


class TestTheTotalAndMissingPanels:
    """HC5-06 measured twoway: without missing, the Total panel draws the
    observations of every group (auto: 69 of 74, rep78 missing on 5); with
    missing, every observation and a panel of the missing ones."""

    @staticmethod
    def _points(fig):
        n = 0
        for rr in drawn_renderers(fig):
            if type(rr.glyph).__name__ != "Scatter":
                continue
            filt = getattr(rr.view, "filter", None)
            if type(filt).__name__ == "BooleanFilter" and \
                    filt.booleans is not None:
                n += sum(1 for b in filt.booleans if b)
            elif type(filt).__name__ == "IndexFilter" and \
                    filt.indices is not None:
                n += len(filt.indices)
            else:
                x = rr.glyph.x
                col = rr.data_source.data[_field(x)]
                n += sum(1 for v in col if v == v)
        return n

    def _counts(self, r, doc):
        # Flipped (WP-30 P1.15a): keyed on the title, which held the label;
        # the label is its own row now.
        saved = {panel_label(f): self._points(f) for f in r.figures.values()}
        served = {panel_label(f): self._points(f)
                  for f in _served_figures(doc)}
        return saved, served

    def test_total_without_missing_is_the_groups_together(self):
        r, doc, _, _ = _by("rep78, total")
        for got in self._counts(r, doc):
            assert got == {"3": 7, "4": 2, "5": 1, "Total": 10}, got

    def test_total_with_missing_is_every_observation(self):
        r, doc, _, _ = _by("rep78, missing total")
        for got in self._counts(r, doc):
            # Flipped (WP-30 P1.15a): twoway writes "(missing)".
            assert got == {"3": 7, "4": 2, "5": 1, "(missing)": 2,
                           "Total": 12}, got

    def test_the_total_panel_is_one_more_than_the_group_limit(self):
        """$dash_max_by_groups counts groups: with total, one panel more."""
        df = _auto()
        df["g"] = [float(i) for i in range(len(df))]
        r, doc, saved, served = _by("g, total", df=df,
                                    build={"limits": {"by_groups": 4}})
        # Flipped (WP-30 P1.15a): the panels are named by their label row.
        for titles in ([panel_label(f) for f in r.figures.values()],
                       [panel_label(f) for f in _served_figures(doc)]):
            assert sorted(titles) == sorted(["0", "1", "2", "3", "Total"])
        for notes in (saved, served):
            assert [m for m in notes if "has 12 groups, more than the 4"
                    in m], notes


class TestThePanelArrangement:
    """ceil(sqrt(panels)) columns by default -- five panels in rows of 3
    and 2 -- in the grid, in a tab and in a layout(bs) cell, in both
    modes; cols(#) wins."""

    @staticmethod
    def _spy(namespace):
        """``(rows, spy)``: *rows* fills, as each grid is laid out, with the
        panels per row of every grid gridplot() made.  Flipped (WP-30
        P1.15b): the by() grid is made from one row and its children then
        placed in twoway's cells (_dash_by_positions), so the rows are read
        from the grid's children, not from gridplot()'s argument."""
        grids = []
        real = namespace.gridplot if not isinstance(namespace, dict) \
            else namespace["gridplot"]

        class _Rows(list):
            def __contains__(self, want):
                for g in grids:
                    per = {}
                    for c in g.children:
                        if type(c[0]).__name__ == "figure":
                            per[int(c[1])] = per.get(int(c[1]), 0) + 1
                    if [per[r] for r in sorted(per)] == want:
                        return True
                return False

        def spy(children, *a, **k):
            g = real(children, *a, **k)
            grids.append(g)
            return g
        return _Rows(), spy

    @pytest.mark.parametrize("build", [
        {"layout": "auto"}, {"layout": "auto", "tabs": "A: g1"},
        {"layout": "bs"},
    ], ids=["grid", "tab", "bs-cell"])
    @pytest.mark.parametrize("by,want", [
        ("g", [3, 2]), ("g, cols(2)", [2, 2, 1]), ("g, cols(1)", [1] * 5),
    ])
    def test_both_modes(self, monkeypatch, build, by, want):
        df = _auto()
        df["g"] = [float(i % 5) for i in range(len(df))]
        spec = _spec([("g1", [_scatter()], {"by": by})], build=build)
        rows, spy = self._spy(dr)
        monkeypatch.setattr(dr, "gridplot", spy)
        _, sp, dp = _write(spec, _payload(df))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.DashRenderer(sp, dp).render()
        assert want in rows, (build, by, rows)
        monkeypatch.undo()
        tag, sp, dp = _write(spec, _payload(df))
        ap = os.path.join(_TMP, f"app_arr_{tag}.py")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(ap)
            from test_adversarial_matrix import _load_app, _session
            with open(ap, encoding="utf-8") as fh:
                ns = _load_app(fh.read(), f"arr_{tag}")
            srows, sspy = self._spy(ns)
            ns["gridplot"] = sspy
            _session(ns)
        assert want in srows, (build, by, srows)


class TestTheOneLineFormHonoursCols:
    """WP-27: ``dash scatter mpg weight, by(foreign, cols(1)) saving(f)``
    put its panels at (0,0) and (0,1), as plain by(foreign) does, where the
    same graph registered and built puts them at (0,0) and (1,0) (measured
    24sep2026 by WP-24).  The one-line graph has no name, and the grid read
    a graph's options by name, so it found none and fell back to
    ceil(sqrt(n)) columns.  The options are now read by the key the layout
    places the graph under -- its name, or '' for the one-line graph."""

    @staticmethod
    def _immediate(by):
        """The spec ``_dash_render_immediate`` writes: one graph, no name,
        no registry, layout "1 1"."""
        return {"graphs": [{"plots": [_scatter()],
                            "graph_options": {"by": by, "saving": "f.html"},
                            "if_expr": "", "in_expr": ""}],
                "build_options": {"layout": "1 1", "theme": "",
                                  "session_scheme": "", "level": "95",
                                  "formats": {}}}

    @pytest.mark.parametrize("by,want", [
        ("foreign, cols(1)", [(0, 0), (1, 0)]),
        ("foreign, cols(2)", [(0, 0), (0, 1)]),
        ("foreign", [(0, 0), (0, 1)]),
    ])
    def test_the_saved_page(self, by, want):
        _, sp, dp = _write(self._immediate(by), _payload(_auto()))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = dr.DashRenderer(sp, dp)
            render_models(r)
        assert [(row, col) for row, col, _ in _saved_panels(r)] == want

    def test_the_options_are_found_by_the_layout_key(self):
        named = {"name": "g1", "graph_options": {"name": "g1", "by": "a"}}
        unnamed = {"graph_options": {"by": "b"}}
        top = {"name": "g3", "graph_options": {"by": "c"}}
        gs = [named, unnamed, top]
        assert dr._dash_graph_options_of(gs, "g1") == {"name": "g1",
                                                       "by": "a"}
        assert dr._dash_graph_options_of(gs, "") == {"by": "b"}
        assert dr._dash_graph_options_of(gs, "g3") == {"by": "c"}
        assert dr._dash_graph_options_of(gs, "nope") == {}
        # Malformed entries are skipped, never raised on.
        assert dr._dash_graph_options_of(
            [None, {"graph_options": None}, "x"], "") == {}


class TestTheSubOptionsDashDoesNotImplement:
    """subtitleformat() and the shrink words are accepted, named in one
    note -- the ones dash implements never -- and ignored, in both modes.
    Flipped (WP-30 P1.15b): rows(), holes() and compact were the examples;
    they are drawn now, as twoway draws them (by_grid_truth.json).
    Flipped (WP-31 D10): subtitleformat() is drawn now
    (by_remainder_truth.json stf_*), so overallshrink is the example."""

    def test_named_and_ignored(self):
        # Flipped (WP-31 D10b): shrink and overallshrink are drawn; the
        # bystyles econ and stata7 are the example.
        # Flipped (WP-41 BY-7): bgcolor() is taken in silence now;
        # spacers(ring(2)) is the sub-option still named, here and below.
        r, doc, saved, served = _by("foreign, style(econ) spacers(ring(2)) "
                                    "cols(2) total missing")
        # Flipped (WP-31 D10c): style(econ) is drawn as its options
        # (bystyle_truth.json), silently; spacers(ring(2)) is the sub-option
        # still ignored.
        want = ["dash: by() sub-option(s) not implemented and ignored: "
                "spacers(ring(2))"]
        assert [m for m in saved if "sub-option" in m] == want, saved
        assert [m for m in served if "sub-option" in m] == want, served
        # cols(2), total and missing were honoured: two groups and the
        # Total panel, in two columns.
        for panels in (_saved_panels(r), _served_panels(doc)):
            assert [(row, col) for row, col, _ in panels] == [
                (0, 0), (0, 1), (1, 0)], panels

    def test_a_served_build_names_them_when_the_app_is_built(self):
        """`dash build, server' writes the app and returns: a note the app
        gives only when a session opens reaches the terminal it is run in,
        never the Stata log.  HC5-08 measured it missing from the log; the
        build names them now, once, and a session does not again."""
        spec = _spec([("g1", [_scatter()],
                       {"by": "foreign, style(econ) spacers(ring(2))"})])
        tag, sp, dp = _write(spec, _payload(_auto()))
        ap = os.path.join(_TMP, f"app_sub_{tag}.py")
        with warnings.catch_warnings(record=True) as built:
            warnings.simplefilter("always")
            dr.ServerAppBuilder(sp, dp).build(ap)
        from test_adversarial_matrix import _load_app
        with open(ap, encoding="utf-8") as fh:
            ns = _load_app(fh.read(), f"sub_{tag}")
        with warnings.catch_warnings(record=True) as session:
            warnings.simplefilter("always")
            ns["make_document"](Document())
        # Flipped (WP-31 D10c): style(econ) is drawn as its options,
        # silently; spacers(ring(2)) is still ignored.
        for want in ("dash: by() sub-option(s) not implemented and ignored: "
                     "spacers(ring(2))",):
            assert [str(w.message) for w in built].count(want) == 1, \
                [str(w.message) for w in built]
            assert want not in [str(w.message) for w in session]


class TestTheSubOptionSplitterReadsStataQuotes:
    """``_dash_by_tokens`` read a single quote as a quote, so an apostrophe
    inside a sub-option took every sub-option after it into its token:
    ``by(foreign, title(Bob's cars) cols(2))`` lost cols(2), and an
    unimplemented sub-option after one was dropped without a word (legend()
    and the other options that split their sub-options here alike).  Stata
    has no single-quoted string: a string is "..." or the compound
    `"..."', which nests."""

    @pytest.mark.parametrize("raw,want", [
        ("title(Bob's cars) cols(2)", ["title(Bob's cars)", "cols(2)"]),
        ('title("Bob\'s cars") cols(2)', ['title("Bob\'s cars")', "cols(2)"]),
        ("label(1 `\"A \"B\" C\"') cols(2)",
         ["label(1 `\"A \"B\" C\"')", "cols(2)"]),
        ("label(1 `\"x `\"y\"' z\"') span",
         ["label(1 `\"x `\"y\"' z\"')", "span"]),
        ('title("a (b") cols(2)', ['title("a (b")', "cols(2)"]),
        ("rows(2) holes(1 3) compact", ["rows(2)", "holes(1 3)", "compact"]),
        ("it's", ["it's"]),
    ])
    def test_the_tokens(self, raw, want):
        assert dr._dash_by_tokens(raw) == want

    def test_by_keeps_its_cols_after_an_apostrophe(self):
        # Flipped (WP-30 P1.15a): title() was named as unsupported; by()'s
        # title() is drawn now, as twoway draws it.
        assert dr._dash_parse_by("foreign, title(Bob's cars) cols(2)",
                                 warn=False) == (
            "foreign", 2, False, False, [])

    def test_legend_names_what_follows_an_apostrophe(self):
        # Flipped (WP-31 D4): span is taken in silence now (a side-panel
        # legend spans its side), so the word after the apostrophe is
        # stack, which twoway's legend_g draws and Bokeh cannot.
        # Flipped (WP-43 LT-21): stacked is drawn now (CSS on the Legend),
        # so the word after the apostrophe is symplacement(), still named.
        # Flipped (WP-43 LT-21): symplacement() is drawn (test_legend_keys.py::TestSymplacement), so the word is orientation().
        assert dr._dash_legend_unsupported(
            "label(1 Bob's) orientation(vertical)") == [
                "orientation(vertical)"]

    def test_in_both_modes(self):
        """Flipped (WP-30 P1.15a): title(Bob's cars) was named as not
        implemented; twoway draws by()'s title once over the panels."""
        r, doc, saved, served = _by("foreign, title(Bob's cars) cols(1)")
        assert [m for m in saved if "sub-option" in m] == [], saved
        assert [m for m in served if "sub-option" in m] == [], served
        (served_root,) = [x for x in doc.roots
                          if any(isinstance(m, GridPlot)
                                 for m in x.references())]
        for root in (r._last_layout_root, served_root):
            assert chrome_texts(by_grid(root)[1]) == ["Bob's cars"]
        for panels in (_saved_panels(r), _served_panels(doc)):
            assert [(row, col) for row, col, _ in panels] == [(0, 0),
                                                              (1, 0)]

    def test_a_megabyte_of_quotes_is_split_at_once(self):
        """Adversarial (rule 18): unbalanced quotes and parentheses are read
        in one pass and cannot run away."""
        import time
        for raw in ("(" + "`\"" * 200_000, "'" * 400_000,
                    '"' * 400_000 + " cols(2)", "(" * 400_000):
            t0 = time.monotonic()
            dr._dash_by_tokens(raw)
            assert time.monotonic() - t0 < 2.0


class TestAFacetedGraphInALinkGroup:
    """by() with link(): every panel draws its markers as a view over the one
    source the other linked graph draws, dims what is not selected, and
    carries a box select -- the mechanism by which a selection in one panel
    shows in all of them.  In both modes that holds for the markers of
    scatter, connected and dot layers, and the help says so and no more:
    measured, a line, bar, spike, area, fit or paired-coordinate layer
    draws from a source of its own in both modes; rspike and the markers of
    rconnected share the group's source in both modes too (WP-28 E14: a
    served range layer used to build a private source every time); rbar
    draws its own rows in both modes (WP-27)."""

    @pytest.mark.parametrize("ptype", ["scatter", "connected", "dot"])
    def test_the_markers_follow_the_selection_in_both_modes(self, ptype):
        plot = {"type": ptype, "yvar": "mpg", "xvar": "weight",
                "options": {}}
        spec = _spec([("g1", [plot], {"by": "foreign"}),
                      ("g2", [{"type": "scatter", "yvar": "price",
                               "xvar": "weight", "options": {}}], {})],
                     build={"link": "g1 g2"})
        r, doc, _, _ = _both(spec, _payload(_auto()))
        saved = list(r.figures.values())
        served = _served_figures(doc)
        for figs in (saved, served):
            assert len(figs) == 3
            # dot's rows of dots draw from a source of their own, the
            # rows its marker draws (WP-31 B5b); the markers share one.
            markers = [rr for f in figs for rr in drawn_renderers(f)
                       if type(rr.glyph).__name__ == "Scatter"
                       and "dash_dots" not in (rr.tags or [])]
            assert len({id(rr.data_source) for rr in markers}) == 1, (
                "the panels and g2 draw two sources")
            # What is not selected is dimmed.  (The saved page dims to
            # dash's _NONSELECTION_ALPHA, 0.15; the served app leaves
            # Bokeh's own 0.1 -- a difference of degree, reported apart.)
            for rr in markers:
                assert rr.nonselection_glyph is not None
                assert rr.nonselection_glyph.fill_alpha <= \
                    dr._NONSELECTION_ALPHA
            for f in figs:
                assert any(isinstance(t, BoxSelectTool) for t in f.tools)
            panel_views = [rr.view for f in figs[:2] for rr in drawn_renderers(f)
                           if type(rr.glyph).__name__ == "Scatter"
                           and "dash_dots" not in (rr.tags or [])]
            # One marker renderer a panel, two panels (measured 24sep2026,
            # every type here, both modes): `panel_views and' passed a
            # panel that drew no markers at all.
            assert len(panel_views) == 2, [
                [type(rr.glyph).__name__ for rr in drawn_renderers(f)]
                for f in figs[:2]]
            assert panel_views and all(
                type(v.filter).__name__ in ("BooleanFilter", "IndexFilter")
                for v in panel_views), [type(v.filter).__name__
                                         for v in panel_views]

    @pytest.mark.parametrize("ptype", ["bar", "lfit", "rcap", "rscatter"])
    def test_a_layer_with_a_source_of_its_own_does_not(self, ptype):
        """What the help leaves out: in both modes these layers draw from a
        source of their own, which a selection on the group's does not
        reach."""
        if ptype in ("rcap", "rscatter"):
            plot = {"type": ptype, "yvar1": "mpg", "yvar2": "price",
                    "xvar": "weight", "options": {}}
        else:
            plot = {"type": ptype, "yvar": "mpg", "xvar": "weight",
                    "options": {}}
        spec = _spec([("g1", [plot], {"by": "foreign"}),
                      ("g2", [_scatter()], {})], build={"link": "g1 g2"})
        r, doc, _, _ = _both(spec, _payload(_auto()))
        for figs in (list(r.figures.values()), _served_figures(doc)):
            shared = [rr.data_source for rr in drawn_renderers(figs[-1])
                      if type(rr.glyph).__name__ == "Scatter"][0]
            layer = [rr for f in figs[:-1] for rr in drawn_renderers(f)
                     if not str(getattr(rr, "name", "") or "")
                     .startswith("__dash")]
            assert layer and all(rr.data_source is not shared
                                 for rr in layer), ptype


def _drawn_labels(fig):
    """Every label the browser draws, as sorted ``(x, y, text)``: BokehJS
    skips a row whose position is not finite or whose text is null."""
    out = []
    for ls in _labelsets(fig):
        d = ls.source.data
        for x, y, t in zip(d[_field(ls.x)], d[_field(ls.y)],
                           d[_field(ls.text)]):
            if t is None:
                continue
            try:
                fx, fy = float(x), float(y)
            except (TypeError, ValueError):
                continue
            if math.isfinite(fx) and math.isfinite(fy):
                out.append((round(fx, 6), round(fy, 6), _drawn(t)))
    return sorted(out)


def _marker_points(fig):
    pts = set()
    for rr in drawn_renderers(fig):
        g = rr.glyph
        if type(g).__name__ != "Scatter":
            continue
        d = rr.data_source.data
        for x, y in zip(d[_field(g.x)], d[_field(g.y)]):
            fx, fy = float(x), float(y)
            if math.isfinite(fx) and math.isfinite(fy):
                pts.add((round(fx, 6), round(fy, 6)))
    return pts


def _drawn_ends(fig):
    """``{kind: set of (x, y)}``: every end a paired-coordinate layer draws,
    by what draws it -- "Scatter" for markers, "Segment" for a segment's two
    ends, "Arrow" for an arrow annotation's two ends.

    _marker_points reads Scatter renderers only, and pcarrow and pcbarrow
    draw none: a Segment and one Arrow annotation per observation, whose
    ends are literal numbers, not columns (measured 24sep2026).  A segment
    or an arrow counts only when all four of its coordinates are finite,
    since only then does BokehJS draw it."""
    from bokeh.models import Arrow

    def rows(values, data):
        """The rows four coordinates give: a number is every row's, a
        field is a column of *data*."""
        cols = [data[_field(v)] if not isinstance(v, (int, float)) else None
                for v in values]
        n = max([len(c) for c in cols if c is not None] or [1])
        return [[v if c is None else c[i] for v, c in zip(values, cols)]
                for i in range(n)]

    def ends(row):
        e = [float(v) for v in row]
        if not all(math.isfinite(v) for v in e):
            return []
        e = [round(v, 6) for v in e]
        return [(e[0], e[1]), (e[2], e[3])]

    out = {}
    for rr in drawn_renderers(fig):
        g, d = rr.glyph, rr.data_source.data
        kind = type(g).__name__
        if kind == "Scatter":
            for row in rows([g.x, g.y, g.x, g.y], d):
                out.setdefault(kind, set()).update(ends(row)[:1])
        elif kind == "Segment":
            for row in rows([g.x0, g.y0, g.x1, g.y1], d):
                out.setdefault(kind, set()).update(ends(row))
    for a in fig.center:
        if isinstance(a, Arrow):
            data = a.source.data if a.source is not None else {}
            for row in rows([a.x_start, a.y_start, a.x_end, a.y_end], data):
                out.setdefault("Arrow", set()).update(ends(row))
    # WP-31 C1: the heads are drawn by the page's script from the rows of
    # the shaft's source it reads; "Arrow" is that script's rows.
    from bokeh.models import CustomJS
    for m in fig.references():
        if isinstance(m, CustomJS) and m.name == "dash_arrow_head":
            a = m.args
            for row in rows([{"field": a["x1"]}, {"field": a["y1"]},
                             {"field": a["x2"]}, {"field": a["y2"]}],
                            a["src"].data):
                out.setdefault("Arrow", set()).update(ends(row))
    return out


class TestEachEndOfARangeIsLabelledOnItsOwn:
    """"an end that is missing is left unlabelled on its own": the other end
    is still marked and labelled, as twoway draws it (HC5-12 measures it:
    rscatter with observation 1's high end missing labels its low end).
    The served app dropped the whole observation -- both markers and both
    labels -- when either end was missing, while the saved page kept the
    end that is there."""

    @pytest.mark.parametrize("ptype", ["rcapsym", "rconnected", "rscatter"])
    def test_in_both_modes(self, ptype):
        df = _auto()
        df.loc[0, "price"] = np.nan          # AMC Concord: no high end
        df.loc[1, "mpg"] = np.nan            # AMC Pacer: no low end
        plot = {"type": ptype, "yvar1": "mpg", "yvar2": "price",
                "xvar": "weight", "options": {"mlabel": "make"}}
        r, doc, _, _ = _both(_spec([("g1", [plot], {})]), _payload(df))
        for fig in _pair_figures(r, doc):
            drawn = _drawn_labels(fig)
            assert len(drawn) == 2 * len(df) - 2, (ptype, len(drawn))
            assert [d for d in drawn if d[2] == "AMC Concord"] == [
                (2930.0, 22.0, "AMC Concord")], ptype
            assert [d for d in drawn if d[2] == "AMC Pacer"] == [
                (3350.0, 4749.0, "AMC Pacer")], ptype
            pts = _marker_points(fig)
            assert (2930.0, 22.0) in pts and (3350.0, 4749.0) in pts, ptype

    @pytest.mark.parametrize("ptype", ["rarea", "rbar", "rspike", "rcap",
                                       "rline"])
    def test_the_other_range_types_draw_alike_in_both_modes(self, ptype):
        """The rows a served range layer keeps are the saved page's: an
        observation with one end missing draws nothing a range needs two
        ends for, in either mode, and nothing is lost that was drawn."""
        df = _auto()
        df.loc[0, "price"] = np.nan
        df.loc[1, "mpg"] = np.nan
        plot = {"type": ptype, "yvar1": "mpg", "yvar2": "price",
                "xvar": "weight", "options": {}}
        r, doc, saved, served = _both(_spec([("g1", [plot], {})]),
                                      _payload(df))
        assert saved == served, (saved, served)
        a, b = _pair_figures(r, doc)

        def rows(fig):
            out = []
            for rr in drawn_renderers(fig):
                d = rr.data_source.data
                out.append((type(rr.glyph).__name__,
                            len(next(iter(d.values()))) if d else 0))
            return out
        assert rows(a) == rows(b), (rows(a), rows(b))


class TestAPairedCoordinateObservationWithAMissingPoint:
    """"A paired-coordinate observation with a missing coordinate is not
    drawn at all, marker or label" -- in both modes, on all four labelling
    paired-coordinate types (HC5-11 measures what twoway draws instead)."""

    @pytest.mark.parametrize("ptype", ["pcscatter", "pccapsym", "pcarrow",
                                       "pcbarrow"])
    def test_in_both_modes(self, ptype):
        df = _auto()
        df["w2"] = df["weight"] + 100.0
        df.loc[0, "price"] = np.nan          # AMC Concord: no second point
        plot = {"type": ptype, "y1var": "mpg", "x1var": "weight",
                "y2var": "price", "x2var": "w2",
                "options": {"mlabel": "make"}}
        r, doc, _, _ = _both(_spec([("g1", [plot], {})]), _payload(df))
        for fig in _pair_figures(r, doc):
            drawn = _drawn_labels(fig)
            assert len(drawn) == len(df) - 1, (ptype, len(drawn))
            assert "AMC Concord" not in [d[2] for d in drawn], ptype
            assert (2930.0, 22.0) not in _marker_points(fig), ptype
            # The check above reads markers, and pcarrow and pcbarrow draw
            # none, so for them it held over an empty set and the AMC's
            # segment and arrow were never looked at.  Every end each glyph
            # draws is read instead: the kinds each type draws (measured
            # 24sep2026), the other eleven cars' ends -- both ends of each,
            # and the second car's first point as the control that the
            # reading sees that glyph -- and never the AMC's first point.
            ends = _drawn_ends(fig)
            assert set(ends) == self._DRAWS[ptype], (ptype, sorted(ends))
            for kind, pts in ends.items():
                assert (3350.0, 17.0) in pts, (ptype, kind)
                assert (2930.0, 22.0) not in pts, (ptype, kind)
                assert len(pts) == 2 * (len(df) - 1), (ptype, kind, len(pts))

    #: What each type draws its ends with.
    _DRAWS = {"pcscatter": {"Scatter"}, "pccapsym": {"Segment", "Scatter"},
              "pcarrow": {"Segment", "Arrow"}, "pcbarrow": {"Segment", "Arrow"}}


# ===========================================================================
# 3. What a label says, for a date variable, in both modes
# ===========================================================================

def _dated(**options):
    df = _auto()
    df["d"] = [14612.0 + i for i in range(len(df))]
    opts = dict(options)
    r, doc, saved, served = _both(
        _spec([("g1", [_scatter(**opts)], {})],
              build={"formats": {"d": "%td"}}),
        _payload(df, {"d": {"14612": "LABELLED"}}, {"d": "dl"}))
    a, b = _pair_figures(r, doc)
    return _one_labelset(a), _one_labelset(b), saved, served


class TestADateVariablesLabels:
    def test_are_its_dates_in_both_modes(self):
        a, b, _, _ = _dated(mlabel="d")
        assert _texts(a) == _texts(b), (_texts(a), _texts(b))
        # GAPS2 E3/G6, WP-28 S12: Stata's %td text (was "03 Jan 2000").
        assert _texts(a)[:3] == ["03jan2000", "04jan2000", "05jan2000"]

    def test_a_value_label_on_it_is_not_read_in_either_mode(self):
        a, b, _, _ = _dated(mlabel="d")
        assert "LABELLED" not in _texts(a) + _texts(b)

    def test_mlabformat_is_named_and_the_dates_kept_in_both_modes(self):
        a, b, saved, served = _dated(mlabel="d", mlabformat="%9.2f")
        want = ["dash: mlabformat(%9.2f) is not applied to the date "
                "variable d; its labels are drawn as dates."]
        assert [m for m in saved if "mlabformat" in m] == want, saved
        assert [m for m in served if "mlabformat" in m] == want, served
        assert _texts(a) == _texts(b)
        # GAPS2 E3/G6, WP-28 S12: Stata's %td text (was "03 Jan 2000").
        assert _texts(b)[0] == "03jan2000"

    def test_a_missing_date_is_a_dot_in_both_modes(self):
        df = _auto()
        df["d"] = [np.nan if i == 1 else 14612.0 + i
                   for i in range(len(df))]
        r, doc, _, _ = _both(
            _spec([("g1", [_scatter(mlabel="d")], {})],
                  build={"formats": {"d": "%td"}}),
            _payload(df))
        a, b = _pair_figures(r, doc)
        for ls in (_one_labelset(a), _one_labelset(b)):
            assert _texts(ls)[1] == ".", _texts(ls)


# ===========================================================================
# 4. The other label claims, pinned in both modes
# ===========================================================================

class TestTheOtherLabelOptions:
    def test_mlabsize_takes_a_keyword_or_a_number(self):
        # WP-30 P1.12a (Evidence E5, twoway measured): label sizes are
        # CSS points from Stata's gsize ladder: small 2.777 units = 7.998pt
        # (8pt), large 4.8611 units = 14pt, 12 units = 12 x 2.88 = 34.56pt.
        for raw, pt in (("small", "8pt"), ("large", "14pt"),
                        ("12", "34.56pt")):
            a, b, saved, served = _labelled(mlabsize=raw)
            assert not [m for m in saved + served if "mlabsize" in m]
            for ls in (a, b):
                assert ls.text_font_size == pt, (raw, ls)

    def test_mlabcolor_colours_the_text(self):
        a, b, _, _ = _labelled(mlabcolor="navy")
        for ls in (a, b):
            assert str(ls.text_color).lower() == \
                dr.OptionTranslator.translate_mcolor("navy").lower()

    def test_mlabformat_of_the_helps_example(self):
        """mlabformat(%9.1fc) labels 4099 as 4,099.0 (twoway, HC5)."""
        a, b, _, _ = _labelled(mlabel="price", mlabformat="%9.1fc")
        for ls in (a, b):
            assert _texts(ls)[0] == "4,099.0"


# ===========================================================================
# 5. Resource limits
# ===========================================================================

class TestTheLargeDataNote:
    """"Above 1,000,000 values dash notes the size the file will be.\""""

    def _notes(self, rows, cols):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            dr._report_dataset_shape(rows, cols, "dashboard")
        return [str(x.message) for x in w]

    def test_not_at_a_million(self):
        assert self._notes(500_000, 2) == []
        assert self._notes(1_000_000, 1) == []

    def test_above_a_million(self):
        notes = self._notes(1_000_001, 1)
        assert len(notes) == 1 and "roughly 24 MB" in notes[0], notes


def _normal_pairs(n, seed):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({"y": rng.normal(size=n), "x": rng.normal(size=n)})


def _pairs_payload(df):
    """jsonio's own layout for two numeric columns, written directly (the
    generic builder is too slow for tens of thousands of rows)."""
    return {"values": [{"y": float(a), "x": float(b)}
                       for a, b in zip(df["y"], df["x"])],
            "variableNames": ["y", "x"],
            "variableLabels": {"y": "", "x": ""},
            "valueLabels": {}, "valueLabelNames": {},
            "variableIsString": {"y": False, "x": False}}


def _pairs_spec():
    return _spec([("g1", [{"type": "scatter", "yvar": "y", "xvar": "x",
                           "options": {}}], {})])


class TestTheSizeTheNoteGives:
    """"at about 24 bytes a value, which is what a saved page takes; a
    served app's file carries the values as text and takes up to about
    twice that."  Measured on 1,200,000 values: a saved page 23.7 bytes a
    value, a served app 45.4 on random doubles and 27.2 on whole numbers.
    Each file's cost of one more value is its growth between two sizes,
    so the page's fixed part (BokehJS, the app's code) does not count."""

    @staticmethod
    def _saved_size(n, seed):
        _, sp, dp = _write(_pairs_spec(), _pairs_payload(_normal_pairs(
            n, seed)))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return len(dr.DashRenderer(sp, dp).render().encode("utf-8"))

    @staticmethod
    def _served_size(n, seed):
        tag, sp, dp = _write(_pairs_spec(), _pairs_payload(_normal_pairs(
            n, seed)))
        ap = os.path.join(_TMP, f"app_size_{tag}.py")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(ap)
        return os.path.getsize(ap)

    def test_a_saved_page(self):
        per = (self._saved_size(40_000, 1) - self._saved_size(20_000, 1)) \
            / (2 * 20_000)
        assert 16 <= per <= 32, per
        assert dr._HTML_BYTES_PER_CELL == 24

    def test_a_served_app_takes_up_to_about_twice_that(self):
        per = (self._served_size(40_000, 2) - self._served_size(20_000, 2)) \
            / (2 * 20_000)
        assert dr._HTML_BYTES_PER_CELL < per <= 2.2 * dr._HTML_BYTES_PER_CELL, \
            per


class TestTheByGroupsGlobalOfTheHelpsExample:
    """``global dash_max_by_groups 250`` lets one by() graph draw 250
    panels: the renderer takes 250 from the spec and keeps 250 groups."""

    def test_two_hundred_and_fifty(self):
        lim = dr._dash_limits({"limits": {"by_groups": 250}})["by_groups"]
        assert lim == 250
        df = pd.DataFrame({"g": [float(i) for i in range(300)],
                           "y": [1.0] * 300})
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            got = dr._dash_by_groups(df, ["g"], False, lim, "g1")
        assert len(got) == 250 and got[0][0] == 0.0 and got[-1][0] == 249.0


# ===========================================================================
# 6. The help says what the code does
# ===========================================================================

class TestTheHelpSaysSo:
    """Each corrected sentence, as the help now words it; each fails
    against the text as it was at 4ede074."""

    def _labels(self):
        return _help_section("{marker marker_labels}",
                             "{marker smoother_options}")

    def _facets(self):
        return _help_section("{marker faceting}", "{marker marker_labels}")

    def _limits(self):
        return _help_section("{marker limits}", "{marker examples}")

    def test_mlg_is_documented_as_dashs_own_synonym(self):
        """TR-23.3: twoway refuses mlg(), "option mlg() not allowed",
        r(198), and so does dash (HC5-01).

        Flipped (WP-35 DT-15): mlabgap()'s entry naming mlg() as dash's
        synonym was wrong; dash refuses it as twoway does (P4-7)."""
        sec = self._labels()
        entry = sec[sec.index("{cmdab:mlabg:ap("):]
        entry = entry[:entry.index("{p_end}")]
        assert "mlg()" not in entry, entry

    def test_the_clock_positions_are_described_as_drawn(self):
        sec = self._labels()
        assert "drawn at 12, where {cmd:twoway}" in sec
        assert "3 used" not in sec

    def test_the_gap_is_along_the_clock_direction(self):
        sec = self._labels()
        assert "in the direction of the clock position" in sec

    def test_the_total_panel_is_described_as_twoway_draws_it(self):
        sec = self._facets()
        assert "showing all data" not in sec
        assert "with a missing {cmd:by()} value only with {cmd:missing}" \
            in sec

    def test_the_link_claim_names_the_layers_it_holds_for(self):
        sec = self._facets()
        assert ("in the markers of {cmd:scatter}, {cmd:connected} and "
                "{cmd:dot} layers, which draw from that source") in sec

    def test_the_panel_title_rule_is_stated(self):
        sec = self._facets()
        assert "whatever its display format" in sec
        # Flipped (WP-30 P1.15a): "Domestic / 3" was wrong because twoway
        # joins the labels of several by() variables ", ".
        assert '"Domestic, 3"' in sec

    def test_the_by_group_limit_counts_groups(self):
        for sec in (self._facets(), self._limits()):
            assert "one more" in sec, sec[:300]

    def test_the_memory_figure_is_the_measured_one(self):
        sec = self._limits()
        assert "about 2 GB of memory" in sec
        assert "2.1 GB" not in sec

    def test_the_limits_are_claimed_for_the_listed_quantities_only(self):
        sec = self._limits()
        assert "Every input that decides how much" not in sec

    def test_the_size_note_says_whose_size_it_is(self):
        sec = self._limits()
        assert "which is what a saved page takes" in sec
        assert "up to about twice that" in sec


# ===========================================================================
# 7. "Live Bokeh Server (blocking -- Ctrl+C to stop)"
# ===========================================================================

def _free_port():
    import socket
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.mark.serve
class TestServingBlocksUntilInterrupted:
    """``dash serve`` runs ``dash_render.py --launch`` in Stata's own Python
    and waits on it (dash.ado's _dash_serve, through runpy), so Stata is
    blocked while the server runs; Ctrl+C is a SIGINT to the foreground
    process group, and it stops the server.  The launch is driven here as a
    subprocess, with --no-browser: nothing opens a browser."""

    def test_the_launch_waits_and_ctrl_c_stops_it(self, tmp_path):
        import signal
        import subprocess
        import time
        import urllib.request

        _, sp, dp = _write(_spec([("g1", [_scatter()], {})]),
                           _payload(_auto()))
        app = str(tmp_path / "served_app.py")
        port = _free_port()
        health = f"http://127.0.0.1:{port}/health"
        log = open(tmp_path / "launch.log", "w")
        proc = subprocess.Popen(
            [sys.executable, os.path.join(_HERE, "..", "dash_render.py"),
             "--spec", sp, "--data", dp, "--output", app, "--mode", "server",
             "--launch", "--port", str(port), "--no-browser"],
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            up = False
            deadline = time.monotonic() + 120
            while time.monotonic() < deadline and proc.poll() is None:
                try:
                    with urllib.request.urlopen(health, timeout=2) as resp:
                        up = resp.status == 200
                except OSError:
                    time.sleep(0.5)
                    continue
                if up:
                    break
            assert up, (tmp_path / "launch.log").read_text()[-2000:]
            time.sleep(1.0)
            assert proc.poll() is None, (
                "the launch returned while its server was running")
            os.killpg(proc.pid, signal.SIGINT)
            proc.wait(timeout=60)
        finally:
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
            log.close()
        with pytest.raises(OSError):
            urllib.request.urlopen(health, timeout=2)


# ===========================================================================
# 8. Adversarial cases (CLAUDE.md rule 18) for the inputs this file's fixes
#    read: mlabposition(), mlabgap(), a by() variable's values and labels,
#    and a date value
# ===========================================================================

class TestAdversarialLabelPlacement:
    # ---- bypass: a spelling that is not twoway's --------------------------
    @pytest.mark.parametrize("raw", ["\u0663", "\uff13", "+3", "3.", "0x3",
                                     "3\n9", "3 9", "1_2"])
    def test_a_position_in_another_spelling_is_not_a_position(self, raw):
        """Arabic-Indic and full-width digits, a sign, a trailing point, hex,
        two numbers: none is one of the thirteen names twoway takes, so each
        is named and drawn at 12, as twoway draws what it does not know."""
        a, b, saved, served = _labelled(mlabposition=raw)
        for notes in (saved, served):
            hits = [m for m in notes if m.startswith("dash: mlabposition(")]
            assert len(hits) == 1 and hits[0].endswith(
                "using 12 (above)."), notes
        for ls in (a, b):
            assert (ls.text_align, ls.text_baseline) == _ANCHOR[12]

    @pytest.mark.parametrize("raw", ["\u0665", "1_000", "0x10", "infinity",
                                     "5e", "--5", "5,0"])
    def test_a_gap_in_another_spelling_is_not_a_gap(self, raw):
        """float() reads other scripts' digits, underscores and "infinity";
        Stata reads none of them.  Each is named and drawn at medium."""
        a, b, saved, served = _labelled(mlabgap=raw)
        for notes in (saved, served):
            assert [m for m in notes if m == f"dash: mlabgap({raw}) is not "
                    "a recognised size; using medium."], notes
        for ls in (a, b):
            # WP-30 P1.12a (Evidence E5, twoway measured; P1.12.2): an
            # unknown gap draws medium, gsize 3.8194 units = 14.667 px,
            # beyond the radius 2.93334 px.
            assert ls.x_offset == pytest.approx(_R + 3.8194 * _U, rel=1e-4)
            assert ls.y_offset == 0

    # ---- injection: markup in a value is named as text, never drawn --------
    def test_markup_in_either_option_is_named_as_text(self):
        bad = "<img src=x onerror=alert(1)>"
        _, sp, dp = _write(_spec([("g1", [_scatter(
            mlabel="make", mlabposition=bad, mlabgap=bad)], {})]),
            _payload(_auto()))
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            page = dr.DashRenderer(sp, dp).render()
        notes = [str(x.message) for x in w]
        assert [m for m in notes if bad in m and "mlabposition" in m], notes
        assert [m for m in notes if bad in m and "mlabgap" in m], notes
        assert "onerror=alert" not in page

    # ---- exhaustion: a megabyte value is judged at once ---------------------
    def test_a_megabyte_value_is_judged_at_once(self):
        import time
        huge = "9" * 10 ** 6
        t0 = time.monotonic()
        with pytest.raises(ValueError):
            dr.GlyphMapper._mlabel_gap_px(huge)
        assert huge not in dr.GlyphMapper._MLABEL_CLOCK_NAMES
        _a, _b, saved, served = _labelled(mlabposition=huge, mlabgap=huge)
        assert time.monotonic() - t0 < 30
        for notes in (saved, served):
            assert notes and max(len(m) for m in notes) < 300, notes

    # ---- the by() titles: a key in another spelling, a huge label set ------
    def test_a_title_label_keyed_by_another_spelling_is_not_matched(self):
        labels = {"rl": {"03": "X", "3.0": "Y", " 3": "Z", "\u0663": "W"}}
        assert dr._dash_facet_label(["r"], 3.0, {"r": "rl"}, labels) == "3"

    def test_markup_in_a_title_label_is_carried_as_text(self):
        bad = "</script><script>alert(1)</script>"
        assert dr._dash_facet_label(["r"], 1.0, {"r": "rl"},
                                    {"rl": {"1": bad}}) == bad

    def test_a_huge_label_set_titles_at_once(self):
        import time
        big = {str(i): "L%d" % i for i in range(200_000)}
        t0 = time.monotonic()
        got = [dr._dash_facet_label(["r"], float(i), {"r": "big"},
                                    {"big": big}) for i in range(1000)]
        assert time.monotonic() - t0 < 2.0
        assert got[999] == "L999"

    @pytest.mark.parametrize("value", [1e308, -1e308, float("inf"),
                                       float("-inf"), 2 ** 80])
    def test_a_date_no_calendar_holds_is_written_as_stata_does(self, value):
        # GAPS2 E3/G6, WP-28 S12, measured in StataMP 19: an infinity and
        # -1e308 are ".", 1e308 (past Stata's largest double) is ".z_", a
        # finite number past the calendar is a number (was "." for all);
        # never a crash.
        got = dr._dash_stata_date_text(value, "td")
        assert got == dr._dash_fmt_text(float(value), "%td")
        want = {1e308: ".z_", -1e308: ".", float("inf"): ".",
                float("-inf"): "."}
        if value in want:
            assert got == want[value], (value, got)
        else:
            assert got[0].isdigit() and "e+" in got, got
