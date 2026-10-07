"""Marker labels and marker outlines drawn as twoway draws them, in both modes.

Three defects, measured 23sep2026 against twoway itself (StataNow 19.5 MP,
the console binary, ``set graphics off``, each picture exported to SVG and
its ``<text>`` and ``<circle>`` elements read), and against both dash render
modes at ad13a0f:

1. **The l-options restyled the markers.**  ``GlyphMapper._apply_marker_opts``
   read ``lcolor()``, ``lwidth()`` and ``lalpha()`` onto the marker outline.
   twoway's line options never reach a marker: on scatter, connected, dot,
   dropline, rscatter, rcapsym, rconnected, pcscatter, pccapsym and scatteri,
   ``lcolor(red)``, ``lcolor(red%50)`` and ``lwidth(vthick)`` each leave every
   ``<circle>`` exactly as the picture drawn without them, while
   ``mlcolor(red)`` turns the outline ``stroke:#FF0000`` and
   ``mlwidth(vthick)`` widens it from 9.72 to 45.36.  (``lalpha()`` is not a
   twoway option -- twoway refuses it, "option lalpha() not allowed" -- and
   dash.sthlp documents it as "opacity of the lines".)  dash drew the outline
   red, thick or faded on every one of those types but pccapsym, which WP-22
   had already filtered.

2. **mlabel() was drawn where twoway draws none, and missed where it draws
   them.**  ``twoway <type> ..., mlabel(zl)`` with ten observations labelled
   ZQLAB1..ZQLAB10, the range and paired-coordinate ends placed in opposite
   halves of the plot region so the SVG says which end a label sits at:

   ==========================  ========================  ====================
   plot type                   twoway                    dash before
   ==========================  ========================  ====================
   scatter connected bar       10, at each point         10
   dot dropline
   rcapsym rconnected          20: BOTH ends             rcapsym y2 only;
   rscatter                                              rconnected each end
                                                         twice; rscatter none
   pcscatter pccapsym          10, at (y1, x1)           pccapsym (y1, x1);
   pcarrow pcbarrow            (headlabel: at (y2, x2))  the other three none
   line spike area rarea rbar  none, rc 0, no note       labelled (y2 on the
   rspike rcap rline tsline                              range types)
   tsrline
   lfit qfit lowess lpoly      none, rc 0, no note       none
   fpfit lfitci qfitci lpolyci
   fpfitci histogram kdensity
   function pcspike
   mspline mband               r(103) "too many          none, rc 0
                               variables specified"
   ==========================  ========================  ====================

   twoway refuses ``mlabel(nosuchvar)`` with r(111) on every type but
   histogram and function, which ignore the option entirely (rc 0) -- where
   dash.ado refused it.

3. **A value-labelled variable was labelled with its codes.**
   ``scatter mpg weight, mlabel(foreign)`` draws "Domestic"/"Foreign"; dash
   drew 0/1.  twoway's rule, read from yxview.class and series.class and
   measured: a labelled value draws its label; an unlabelled value of a
   labelled variable draws the NUMBER, whatever the display format (with
   ``%9.2f`` a 2 is "2", not "2.00"; a ``%td`` 21917 is "21917"), written as
   Stata expands a number into a macro -- %18.0g: 0.5 is ".5", 2.5e-12 is
   "2.50000000000e-12"; and a missing value draws "." (twoway writes an
   extended missing value's own label or name, .a to .z, which the data dash
   receives cannot tell from "." -- jsonio writes every one as "null").
   A missing value of an unlabelled numeric variable is "." too, in any
   format (``%td`` and ``%9.2f`` measured); dash drew "NaN" or nothing.

The served app copies ``GlyphMapper`` by source, so every drawing check runs
in both render modes and asserts they agree.
"""
import html
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
from bokeh.models import ColumnDataSource, LabelSet
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import make_data_json, load_app  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402
from test_abbreviations import _program_body  # noqa: E402

_DF = pd.DataFrame({
    "mpg": [22.0, 17.0, 25.0, 30.0, 21.0, 19.0, 14.0, 28.0, 16.0, 23.0],
    "weight": [2930.0, 3350.0, 2200.0, 1800.0, 3000.0, 3100.0, 4080.0,
               2010.0, 3600.0, 2650.0],
    "price": [4099.0, 4749.0, 3799.0, 4816.0, 5788.0, 4453.0, 5189.0,
              10372.0, 4082.0, 11385.0],
    "foreign": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
    "rep": [3.0, 4.0, 3.0, 5.0, 4.0, 3.0, 5.0, 4.0, 3.0, 4.0],
    "gap": [1.5, np.nan, 2.25, 3.0, np.nan, 4.5, 5.0, 6.75, 7.0, 8.0],
    "make": ["AMC Concord", "AMC Pacer", "AMC Spirit", "Buick Century",
             "Buick Electra", "Buick LeSabre", "Buick Opel", "Buick Regal",
             "Buick Riviera", "Buick Skylark"],
})
_ORIGIN = {"0": "Domestic", "1": "Foreign"}
_SEQ = itertools.count()
_TMP = tempfile.mkdtemp(prefix="dash_marker_label_parity_")


def _write(spec, df, value_labels, label_names):
    tag = next(_SEQ)
    sp = os.path.join(_TMP, f"spec_{tag}.json")
    dp = os.path.join(_TMP, f"data_{tag}.json")
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    data = make_data_json(df, value_labels, label_names)
    # Real jsonio marks a string variable; the served app coerces an
    # unmarked column to NaN.  (pandas 3 infers a `str' dtype, not object.)
    for key in ("variableIsString", "variableTypeIsString"):
        for col in df.columns:
            if pd.api.types.is_string_dtype(df[col]):
                data["StataJSON"][key][col] = True
    with open(dp, "w") as fh:
        json.dump(data, fh)
    return tag, sp, dp


def _both(plots, df=_DF, value_labels=None, label_names=None, formats=None,
          go=None, served=True):
    """(saved figure, served figure, saved warnings, served warnings).

    By default ``foreign`` carries the label set ``origin`` keyed by the
    label set's name; real jsonio keys valueLabels by the VARIABLE's name,
    which ``value_labels=`` can say instead.  ``served=False`` renders the
    saved page alone: the served figure and warnings are then None.
    """
    if value_labels is None:
        value_labels = {"origin": dict(_ORIGIN)}
    if label_names is None:
        label_names = {"foreign": "origin"}
    spec = tp._spec(plots, {"formats": dict(formats or {})}, go)
    _, sp, dp = _write(spec, df, value_labels, label_names)
    dr._dash_reset_notes()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r = dr.DashRenderer(sp, dp)
        r.render()
    std_w = sorted(str(w.message) for w in caught)
    if not served:
        return list(r.figures.values())[0], None, std_w, None

    tag, sp, dp = _write(spec, df, value_labels, label_names)
    ap = os.path.join(_TMP, f"app_{tag}.py")
    with warnings.catch_warnings(record=True) as built:
        warnings.simplefilter("always")
        dr.ServerAppBuilder(sp, dp).build(ap)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mod = load_app(ap, f"_mlp_{tag}")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        doc = Document()
        mod.make_document(doc)
    srv_w = sorted(str(w.message) for w in list(built) + list(caught))
    std = list(r.figures.values())[0]
    srv = [m for m in tp._walk_models(doc)
           if type(m).__name__ == "figure"][0]
    return std, srv, std_w, srv_w


def _labelsets(fig):
    return [x for x in (list(fig.center) + list(fig.above) + list(fig.below)
                        + list(fig.left) + list(fig.right))
            if isinstance(x, LabelSet)]


def _field(spec):
    if isinstance(spec, str):
        return spec
    if isinstance(spec, dict):
        return spec.get("field")
    # A document read back from a page's JSON holds a Field object.
    return getattr(spec, "field", None)


def _drawn_labels(fig):
    """Every label the browser draws, as sorted ``(x, y, text)`` triples.

    BokehJS's LabelSetView skips a row whose screen position is not finite
    or whose text is null (``if (!isFinite(sx_i + sy_i + angle_i) ||
    text_i == null) continue``), and writes the rest as ``${text}``.
    """
    out = []
    for ls in _labelsets(fig):
        data = ls.source.data
        xs, ys = data[_field(ls.x)], data[_field(ls.y)]
        texts = data[_field(ls.text)]
        for x, y, t in zip(xs, ys, texts):
            if t is None:
                continue
            try:
                fx, fy = float(x), float(y)
            except (TypeError, ValueError):
                continue
            if not (math.isfinite(fx) and math.isfinite(fy)):
                continue
            out.append((round(fx, 6), round(fy, 6), tp._drawn_text(t)))
    return sorted(out)


def _expected(ptype, textcol, df=_DF):
    """The labels twoway draws for ``plot_for(ptype, {"mlabel": textcol})``
    on *df*, from the measured placement of each plot-type family."""
    def text(v):
        return tp._drawn_text(v)
    rows = []
    for _, r in df.iterrows():
        if ptype in _AT_POINT:
            pts = [(r["weight"], r["mpg"])]
        elif ptype in _BOTH_ENDS:
            pts = [(r["weight"], r["mpg"]), (r["weight"], r["price"])]
        elif ptype in _FIRST_POINT:
            pts = [(r["weight"], r["mpg"])]
        else:
            pts = []
        for x, y in pts:
            rows.append((round(float(x), 6), round(float(y), 6),
                         text(r[textcol])))
    return sorted(rows)


def _hex(name):
    return dr.OptionTranslator.parse_color_alpha(name)[0].lower()


# ===========================================================================
# The measured partition of twoway's plot types
# ===========================================================================

#: Labels at each observation's point.
_AT_POINT = ("scatter", "connected", "bar", "dot", "dropline")
#: Labels at BOTH ends of each range: "the same marker label would be used
#: to label both ends" (twoway_rcapsym.sthlp, _rscatter, _rconnected), and
#: measured 20 labels for 10 observations, ten in each half.
_BOTH_ENDS = ("rcapsym", "rconnected", "rscatter")
#: Labels at the first point, (y1var, x1var) -- "By default, the labels are
#: placed at the tail of the arrow" (twoway_pcarrow.sthlp); measured ten
#: labels, all at the first point, on all four.
_FIRST_POINT = ("pcscatter", "pccapsym", "pcarrow", "pcbarrow")
#: twoway accepts mlabel() and draws no label, without a note.
_NO_LABEL = ("line", "spike", "area", "lfit", "qfit", "lowess", "lpoly",
             "fpfit", "lfitci", "qfitci", "lpolyci", "fpfitci", "rarea",
             "rbar", "rspike", "rcap", "rline", "pcspike", "histogram",
             "kdensity", "function", "tsline", "tsrline")
#: twoway refuses mlabel() (r(103)); dash.ado refuses it too, and a spec
#: written by hand draws none.
_REFUSED = ("mspline", "mband")
#: The immediate types take their labels from the command line; their
#: labels are drawn by their own branches (not this file's subject).
_IMMEDIATE = ("scatteri", "pci", "pcarrowi")

#: The types that draw markers, for the l-option checks.  pccapsym draws
#: markers too, and already kept its line options off them (WP-22,
#: test_pccapsym_pcarrowi.py certifies it).
_MARKER_TYPES = ("scatter", "connected", "dot", "dropline", "rscatter",
                 "rcapsym", "rconnected", "pcscatter", "scatteri")


def test_the_partition_covers_every_plot_type_once():
    """A plot type added to dash must be measured and placed here."""
    groups = (_AT_POINT, _BOTH_ENDS, _FIRST_POINT, _NO_LABEL, _REFUSED,
              _IMMEDIATE)
    flat = [t for g in groups for t in g]
    assert len(flat) == len(set(flat)), "a type is in two groups"
    assert set(flat) == set(dr._dash_plot_type_names())
    # and the drawing below must now match it -- a guard that fails on the
    # code as it was, where rscatter drew no label at all
    std, srv, _, _ = _both([plot_for("rscatter", {"mlabel": "make"})])
    assert _drawn_labels(std) == _expected("rscatter", "make")


# ===========================================================================
# 1. The l-options never reach a marker
# ===========================================================================

def _markers(fig):
    return [(g.line_color, float(g.line_width), round(float(g.line_alpha), 4),
             g.fill_color, round(float(g.fill_alpha), 4))
            for g in (r.glyph for r in fig.renderers)
            if type(g).__name__ == "Scatter"]


class TestTheApplierLeavesTheOutlineToTheMarkerOptions:
    """``_apply_marker_opts`` on one glyph."""

    @staticmethod
    def _glyph(options):
        gm = dr.GlyphMapper(scheme=dr.SchemeParser("s2color"))
        fig = figure()
        src = ColumnDataSource({"x": [1.0, 2.0], "y": [3.0, 4.0]})
        r = fig.scatter(x="x", y="y", source=src, fill_color="#1a476f",
                        line_color="#1a476f", line_width=1.0,
                        line_alpha=1.0, fill_alpha=1.0)
        gm._apply_marker_opts(r, dict(options))
        return r.glyph

    @pytest.mark.parametrize("options", [
        {"lcolor": "red"}, {"lcolor": "red%50"}, {"lwidth": "vthick"},
        {"lalpha": "30"}, {"lcolor": "none"},
        {"lcolor": "red", "lwidth": "vthick", "lalpha": "30"},
    ], ids=["lcolor", "lcolor%", "lwidth", "lalpha", "lcolor(none)", "all"])
    def test_the_line_options_are_not_read(self, options):
        g = self._glyph(options)
        assert (g.line_color, g.line_width, g.line_alpha, g.fill_color,
                g.fill_alpha) == ("#1a476f", 1.0, 1.0, "#1a476f", 1.0), (
            options, g.line_color, g.line_width, g.line_alpha)

    def test_mlcolor_and_mlwidth_are_the_outlines_own(self):
        """mlcolor()/mlwidth() draw the outline; an lwidth() or lalpha()
        beside mlcolor() leaves the width and opacity where they were."""
        g = self._glyph({"mlcolor": "red", "lwidth": "vthick",
                         "lalpha": "30"})
        assert g.line_color.lower() == _hex("red")
        assert (g.line_width, g.line_alpha) == (1.0, 1.0)
        g = self._glyph({"mlwidth": "vthick", "lcolor": "green"})
        assert g.line_width == pytest.approx(
            dr.OptionTranslator.translate_lwidth("vthick"))
        assert g.line_color == "#1a476f"


#: The marker types whose served half the line-option sweep keeps (WP-30
#: test performance E): point, line, range, spike, pc and immediate.  The
#: saved half keeps all nine; the served app draws markers through the same
#: GlyphMapper text, and test_mode_parity's corpus compares every type.
_LINE_OPTION_SERVED = ("scatter", "connected", "rcapsym", "dropline",
                       "pcscatter", "scatteri")


@pytest.mark.parametrize("ptype", _MARKER_TYPES)
@pytest.mark.parametrize("options", [
    {"lcolor": "red"}, {"lwidth": "vthick"}, {"lcolor": "red%50"},
    {"lalpha": "30"},
], ids=["lcolor", "lwidth", "lcolor%", "lalpha"])
def test_the_line_options_leave_every_marker_alone(ptype, options):
    """The markers are the ones drawn with no option: saved for every
    marker type, served as well for ``_LINE_OPTION_SERVED``."""
    served = ptype in _LINE_OPTION_SERVED
    b_std, b_srv, _, _ = _both([plot_for(ptype)], served=served)
    std, srv, std_w, srv_w = _both([plot_for(ptype, options)], served=served)
    pairs = [(b_std, std)]
    if served:
        assert std_w == srv_w
        pairs.append((b_srv, srv))
    for base, fig in pairs:
        assert _markers(base), ptype
        assert _markers(fig) == _markers(base), (ptype, options)


def test_the_line_option_sweep_serves_a_type_of_each_family():
    """Guards the pruning: every served representative is a marker type."""
    assert set(_LINE_OPTION_SERVED) < set(_MARKER_TYPES)
    assert len(_LINE_OPTION_SERVED) == 6


@pytest.mark.parametrize("ptype,kind", [
    ("connected", "Line"), ("rconnected", "Line"), ("dropline", "Segment"),
    ("rcapsym", "Segment"),
])
def test_the_lines_still_take_the_line_options(ptype, kind):
    """twoway: lcolor() and lwidth() style the connecting line, the drop and
    the spike -- the markers keep the scheme's outline."""
    b_std, b_srv, _, _ = _both([plot_for(ptype)])
    std, srv, _, _ = _both([plot_for(ptype, {"lcolor": "red",
                                             "lwidth": "vthick"})])
    for base, fig in ((b_std, std), (b_srv, srv)):
        lines = [r.glyph for r in fig.renderers
                 if type(r.glyph).__name__ == kind]
        assert lines and all(g.line_color.lower() == _hex("red")
                             for g in lines), (ptype, kind)
        assert _markers(fig) == _markers(base), ptype


# ===========================================================================
# 2. Where mlabel() draws, per plot type
# ===========================================================================

def test_no_label_on_any_type_twoway_leaves_unlabelled():
    """rc 0 and no note in twoway (mspline and mband it refuses, and so does
    dash.ado; a spec that carries one anyway draws nothing).  One sweep, so
    the types dash already left alone are held there too."""
    bad = []
    for ptype in _NO_LABEL + _REFUSED:
        std, srv, std_w, srv_w = _both([plot_for(ptype, {"mlabel": "make"})])
        if std_w != srv_w or [w for w in std_w if "mlabel" in w]:
            bad.append((ptype, "notes", std_w, srv_w))
        if _labelsets(std) or _labelsets(srv):
            bad.append((ptype, "labels", len(_labelsets(std)),
                        len(_labelsets(srv))))
    assert not bad, bad


def test_a_hand_written_second_name_is_as_silent_as_twoway():
    """``line y x, mlabel(zl t)``: rc 0, nothing drawn, nothing said."""
    bad = []
    for ptype in _NO_LABEL:
        std, srv, std_w, srv_w = _both([plot_for(ptype,
                                                 {"mlabel": "make foreign"})])
        if [w for w in std_w + srv_w if "mlabel" in w]:
            bad.append((ptype, std_w))
        if _labelsets(std) or _labelsets(srv):
            bad.append((ptype, "labels"))
    assert not bad, bad


def test_labels_are_drawn_where_twoway_draws_them():
    """Every labelling type, one sweep: each label at the point twoway puts
    it, once, in both modes."""
    bad = []
    for ptype in _AT_POINT + _BOTH_ENDS + _FIRST_POINT:
        std, srv, std_w, srv_w = _both([plot_for(ptype, {"mlabel": "make"})])
        want = _expected(ptype, "make")
        if std_w != srv_w:
            bad.append((ptype, "notes", std_w, srv_w))
        if _drawn_labels(std) != want:
            bad.append((ptype, "saved", len(_drawn_labels(std)), len(want)))
        if _drawn_labels(srv) != want:
            bad.append((ptype, "served", len(_drawn_labels(srv)), len(want)))
    assert not bad, bad


@pytest.mark.parametrize("ptype", _BOTH_ENDS)
def test_each_end_is_labelled_exactly_once(ptype):
    """rconnected drew each end twice -- map_line and map_scatter both
    labelled -- which reads as doubled, bolder text."""
    std, srv, _, _ = _both([plot_for(ptype, {"mlabel": "make"})])
    for fig in (std, srv):
        drawn = _drawn_labels(fig)
        assert len(drawn) == 2 * len(_DF) == len(set(drawn)), ptype


@pytest.mark.parametrize("ptype", ("pcscatter", "pcarrow", "pcbarrow"))
def test_the_second_point_carries_no_label(ptype):
    std, srv, _, _ = _both([plot_for(ptype, {"mlabel": "make"})])
    ends = {(round(float(x), 6), round(float(y), 6))
            for x, y in zip(_DF["foreign"], _DF["price"])}
    for fig in (std, srv):
        drawn = _drawn_labels(fig)
        assert drawn and not [d for d in drawn if (d[0], d[1]) in ends]


@pytest.mark.parametrize("ptype", _BOTH_ENDS + ("pcscatter", "pcarrow",
                                                 "pcbarrow"))
def test_the_label_options_reach_every_label(ptype):
    """mlabangle(), mlabcolor() and mlabposition() style both ends alike."""
    opts = {"mlabel": "make", "mlabangle": "45", "mlabcolor": "red",
            "mlabposition": "9"}
    std, srv, std_w, srv_w = _both([plot_for(ptype, opts)])
    assert std_w == srv_w
    for fig in (std, srv):
        sets = _labelsets(fig)
        assert sets and _drawn_labels(fig) == _expected(ptype, "make")
        for ls in sets:
            assert float(ls.angle) == pytest.approx(math.radians(45))
            assert str(ls.text_color).lower() == _hex("red")
            assert (ls.x_offset, ls.y_offset) == (-4, 0)


def test_an_out_of_range_angle_on_an_arrow_is_reported_and_drawn_flat():
    """Measured: on pcarrow and pcbarrow twoway prints "textangle must be
    between -360.000 and 360.000" for mlabangle(400), returns rc 0 and
    draws the arrows without their labels.  dash.ado passes it (twoway's
    rc is 0), and the renderer names it and draws the labels horizontal,
    as dash.sthlp says."""
    for ptype in ("pcarrow", "pcbarrow"):
        std, srv, std_w, srv_w = _both([plot_for(ptype, {
            "mlabel": "make", "mlabangle": "400"})])
        want = ["dash: mlabangle(400) is not a recognised angle; using "
                "horizontal."]
        assert [w for w in std_w if "mlabangle" in w] == want, std_w
        assert [w for w in srv_w if "mlabangle" in w] == want, srv_w
        for fig in (std, srv):
            assert _drawn_labels(fig) == _expected(ptype, "make")
            assert all(float(ls.angle) == 0.0 for ls in _labelsets(fig))


def test_a_per_plot_qualifier_labels_only_the_qualified_ends():
    """rscatter and pcscatter draw their labels from the rows their markers
    come from, so a qualified layer labels only the qualified rows."""
    for ptype in ("rscatter", "pcscatter", "pcarrow"):
        std, srv, _, _ = _both([plot_for(ptype, {"mlabel": "make"},
                                         if_expr="foreign==1")])
        sub = _DF[_DF["foreign"] == 1]
        want = _expected(ptype, "make", df=sub)
        assert _drawn_labels(std) == want, ptype
        assert _drawn_labels(srv) == want, ptype


def _marker_points(fig):
    pts = set()
    for r in fig.renderers:
        g = r.glyph
        if type(g).__name__ != "Scatter":
            continue
        d = r.data_source.data
        for x, y in zip(d[_field(g.x)], d[_field(g.y)]):
            fx, fy = float(x), float(y)
            if math.isfinite(fx) and math.isfinite(fy):
                pts.add((round(fx, 6), round(fy, 6)))
    return pts


def test_each_end_of_a_range_is_labelled_on_its_own():
    """Measured (m6): with hi missing on observation 1 and lo missing on
    observation 2, rcapsym, rconnected and rscatter label observation 1 at
    its low end only and observation 2 at its high end only -- 18 labels,
    as the saved dashboard draws them.  (The served app's range source
    drops an observation with either end missing, markers and all -- a
    divergence of the markers reported separately; there, as everywhere,
    no label is drawn without its marker.)"""
    df = _DF.copy()
    df.loc[0, "price"] = np.nan
    df.loc[1, "mpg"] = np.nan
    for ptype in _BOTH_ENDS:
        std, srv, _, _ = _both([plot_for(ptype, {"mlabel": "make"})], df=df)
        drawn = _drawn_labels(std)
        assert len(drawn) == 2 * len(df) - 2, (ptype, len(drawn))
        assert [d for d in drawn if d[2] == "AMC Concord"] == [
            (2930.0, 22.0, "AMC Concord")], ptype
        assert [d for d in drawn if d[2] == "AMC Pacer"] == [
            (3350.0, 4749.0, "AMC Pacer")], ptype
        for fig in (std, srv):
            pts = _marker_points(fig)
            assert _drawn_labels(fig) and all(
                (x, y) in pts for x, y, _ in _drawn_labels(fig)), ptype


def test_a_paired_coordinate_label_goes_with_its_observation():
    """dash draws a paired-coordinate observation only when all four of its
    coordinates are present, and its label with it -- never a label with no
    point under it.  (twoway draws the first point, and its label, when only
    the second point is missing: measured, nine labels for ten observations
    with one second point and one first point missing.  The help says so.)"""
    df = _DF.copy()
    df.loc[0, "price"] = np.nan
    for ptype in ("pcscatter", "pcarrow", "pcbarrow"):
        std, srv, _, _ = _both([plot_for(ptype, {"mlabel": "make"})], df=df)
        for fig in (std, srv):
            drawn = _drawn_labels(fig)
            assert len(drawn) == len(df) - 1, (ptype, len(drawn))
            assert "AMC Concord" not in [d[2] for d in drawn], ptype


def test_a_missing_label_variable_is_named_on_the_new_types():
    """A spec written by hand that names a variable the data lacks is named
    once, as on scatter (dash.ado refuses it from a command)."""
    for ptype in ("rscatter", "pcscatter", "pcarrow", "pcbarrow"):
        std, srv, std_w, srv_w = _both([plot_for(ptype,
                                                 {"mlabel": "nosuchvar"})])
        want = ["dash: mlabel(nosuchvar): the variable is not in the data; "
                "drawing no labels."]
        assert [w for w in std_w if "mlabel" in w] == want, (ptype, std_w)
        assert [w for w in srv_w if "mlabel" in w] == want, (ptype, srv_w)
        assert _labelsets(std) == [] and _labelsets(srv) == []


def test_a_label_variable_named_x_or_y_does_not_move_the_labels():
    """rscatter and pcscatter stack their points in columns named x and y;
    a label variable of that name must not take their place."""
    df = _DF.copy()
    df["x"] = [f"L{i}" for i in range(len(df))]
    df["y"] = [f"M{i}" for i in range(len(df))]
    for ptype in ("rscatter", "pcscatter"):
        for lab in ("x", "y"):
            std, srv, _, _ = _both([plot_for(ptype, {"mlabel": lab})], df=df)
            assert _drawn_labels(std) == _expected(ptype, lab, df=df), (
                ptype, lab)
            assert _drawn_labels(srv) == _expected(ptype, lab, df=df)


# ===========================================================================
# 3. The text of a numeric label
# ===========================================================================

class TestTheNumberStataWrites:
    """``GlyphMapper._mlabel_number_text``: Stata's own writing of a number
    it expands into a macro (%18.0g), which is what twoway draws for an
    unlabelled value of a value-labelled variable.  Each expectation is a
    measured twoway label."""

    @pytest.mark.parametrize("value,text", [
        (1.0, "1"), (1234567.0, "1234567"), (123456789.0, "123456789"),
        (-3.25, "-3.25"), (0.00001, ".00001"), (12345.678, "12345.678"),
        (1e15, "1000000000000000"), (2.5e-12, "2.50000000000e-12"),
        (100000.0, "100000"), (0.1, ".1"), (0.5, ".5"),
        (float(np.float32(0.1)), ".1000000014901161"),
        (0.0, "0"), (-0.5, "-.5"), (21917.0, "21917"),
    ])
    def test_measured(self, value, text):
        assert dr.GlyphMapper._mlabel_number_text(value) == text

    @pytest.mark.parametrize("value", [float("nan"), None])
    def test_missing_is_a_dot(self, value):
        assert dr.GlyphMapper._mlabel_number_text(value) == "."


class TestTheValueLabelText:
    """``GlyphMapper._mlabel_value_text`` -- one value of a labelled
    variable, as twoway draws it."""

    _L = {"0": "Domestic", "1": "Foreign", "-2": "Minus two"}

    @pytest.mark.parametrize("value,text", [
        (0.0, "Domestic"), (1.0, "Foreign"), (-2.0, "Minus two"),
        (np.float64(1.0), "Foreign"), (2.0, "2"), (0.5, ".5"),
        (float("nan"), "."), (None, "."),
    ])
    def test_each_value(self, value, text):
        assert dr.GlyphMapper._mlabel_value_text(value, self._L) == text

    def test_a_label_is_drawn_whole(self):
        """Measured: an 80-character value label is drawn in full."""
        assert dr.GlyphMapper._mlabel_value_text(
            0.0, {"0": "x" * 80}) == "x" * 80


class TestTheMissingTest:
    """``GlyphMapper._mlabel_missing``."""

    @pytest.mark.parametrize("value,missing", [
        (None, True), (float("nan"), True), (np.float64("nan"), True),
        (pd.NaT, True), (np.datetime64("NaT"), True), (0.0, False),
        (-1.5, False), ("", False), ("x", False),
        (pd.Timestamp("2020-01-01"), False),
    ])
    def test_each(self, value, missing):
        assert dr.GlyphMapper._mlabel_missing(value) is missing


class TestTheColumnReader:
    """``GlyphMapper._mlabel_column_kind``: text or not, and which values
    are missing, read in one pass."""

    def test_numbers(self):
        is_text, miss = dr.GlyphMapper._mlabel_column_kind(
            [1.0, float("nan"), 3.0])
        assert is_text is False and list(miss) == [False, True, False]

    def test_integers_and_an_empty_column(self):
        assert list(dr.GlyphMapper._mlabel_column_kind([1, 2])[1]) == [
            False, False]
        is_text, miss = dr.GlyphMapper._mlabel_column_kind([])
        assert is_text is False and len(miss) == 0

    def test_strings(self):
        is_text, miss = dr.GlyphMapper._mlabel_column_kind(["a", ""])
        # One flag per row, as for every other kind: `not miss.any()' alone
        # was true of a zero-length mask too.
        assert is_text is True and list(miss) == [False, False]
        assert dr.GlyphMapper._mlabel_column_kind(
            pd.Series(["a", "b"]))[0] is True

    def test_numbers_beside_none(self):
        is_text, miss = dr.GlyphMapper._mlabel_column_kind([1.0, None, 2.0])
        assert is_text is False and list(miss) == [False, True, False]

    def test_dates(self):
        col = np.array(["2020-01-01", "NaT"], dtype="datetime64[ns]")
        assert list(dr.GlyphMapper._mlabel_column_kind(col)[1]) == [
            False, True]
        stamps = [pd.Timestamp("2020-01-01"), pd.NaT]
        is_text, miss = dr.GlyphMapper._mlabel_column_kind(stamps)
        assert is_text is False and list(miss) == [False, True]


class TestThePairedCoordinateRows:
    """``GlyphMapper._pc_clean_with_label``: the rows a pcarrow or pcbarrow
    layer draws, with its label column."""

    @staticmethod
    def _src():
        return ColumnDataSource({
            "y1": [1.0, 2.0, np.nan, 4.0], "x1": [1.0, 2.0, 3.0, 4.0],
            "y2": [5.0, 6.0, 7.0, 8.0], "x2": [5.0, 6.0, 7.0, 8.0],
            "lab": ["a", None, "c", "d"]})

    def test_the_label_rides_along_and_a_coordinate_drops_a_row(self):
        gm = dr.GlyphMapper(scheme=dr.SchemeParser("s2color"))
        clean = gm._pc_clean_with_label(self._src(), "y1", "x1", "y2", "x2",
                                        {"mlabel": "lab"})
        labs = list(clean["lab"])
        # the row with no label is kept (pandas holds its label as NaN)
        assert labs[0] == "a" and pd.isna(labs[1]) and labs[2] == "d"
        assert list(clean["y1"]) == [1.0, 2.0, 4.0]

    def test_no_label_column_without_mlabel_or_without_the_variable(self):
        gm = dr.GlyphMapper(scheme=dr.SchemeParser("s2color"))
        for opts in ({}, {"mlabel": "nosuchvar"}):
            clean = gm._pc_clean_with_label(self._src(), "y1", "x1", "y2",
                                            "x2", opts)
            assert list(clean.columns) == ["y1", "x1", "y2", "x2"]

    def test_the_view_masks_before_a_row_is_dropped(self):
        from bokeh.models import BooleanFilter, CDSView
        gm = dr.GlyphMapper(scheme=dr.SchemeParser("s2color"))
        view = CDSView(filter=BooleanFilter(booleans=[False, True, True,
                                                      True]))
        clean = gm._pc_clean_with_label(self._src(), "y1", "x1", "y2", "x2",
                                        {"mlabel": "lab"}, view)
        labs = list(clean["lab"])
        assert len(labs) == 2 and pd.isna(labs[0]) and labs[1] == "d"

    def test_a_repeated_coordinate_is_one_column(self):
        gm = dr.GlyphMapper(scheme=dr.SchemeParser("s2color"))
        clean = gm._pc_clean_with_label(self._src(), "y1", "x1", "y1", "x1",
                                        {"mlabel": "lab"})
        assert list(clean.columns) == ["y1", "x1", "lab"]


class TestTheLabelSetLookup:
    """``GlyphMapper._mlabel_value_labels``: the label set by its name, or
    keyed by the variable's own name, as real jsonio writes valueLabels."""

    def test_by_label_set_name(self):
        gm = dr.GlyphMapper(scheme=dr.SchemeParser("s2color"))
        gm.value_labels = {"origin": dict(_ORIGIN)}
        gm.value_label_names = {"foreign": "origin"}
        assert gm._mlabel_value_labels("foreign") == _ORIGIN

    def test_keyed_by_variable_as_jsonio_writes_it(self):
        gm = dr.GlyphMapper(scheme=dr.SchemeParser("s2color"))
        gm.value_labels = {"foreign": dict(_ORIGIN)}
        gm.value_label_names = {"foreign": "origin"}
        assert gm._mlabel_value_labels("foreign") == _ORIGIN

    def test_an_unlabelled_variable_has_none(self):
        gm = dr.GlyphMapper(scheme=dr.SchemeParser("s2color"))
        gm.value_labels = {"origin": dict(_ORIGIN)}
        gm.value_label_names = {"foreign": "origin"}
        assert gm._mlabel_value_labels("rep") == {}


def _texts_of(fig):
    return [d[2] for d in _drawn_labels(fig)]


@pytest.mark.parametrize("ptype", _AT_POINT + _BOTH_ENDS + _FIRST_POINT)
def test_a_value_labelled_variable_draws_its_labels(ptype):
    std, srv, std_w, srv_w = _both([plot_for(ptype, {"mlabel": "foreign"})])
    assert std_w == srv_w
    want = sorted(t for _, _, t in _expected(ptype, "foreign"))
    want = sorted({"0": "Domestic", "1": "Foreign"}[t] for t in want)
    for fig in (std, srv):
        assert sorted(_texts_of(fig)) == want, ptype


def test_jsonio_keys_the_labels_by_variable():
    """valueLabels {"foreign": {...}}, valueLabelNames {"foreign": "origin"}:
    what jsonio out ... metaprint(vallabs labelnames) writes."""
    std, srv, _, _ = _both([plot_for("scatter", {"mlabel": "foreign"})],
                           value_labels={"foreign": dict(_ORIGIN)})
    for fig in (std, srv):
        assert set(_texts_of(fig)) == {"Domestic", "Foreign"}


def test_an_unlabelled_value_is_its_number_whatever_the_format():
    """Measured: label define part 0 "Zero" 1 "One", format %9.2f -- 2 and 3
    are drawn "2" and "3", not "2.00"."""
    std, srv, _, _ = _both([plot_for("scatter", {"mlabel": "rep"})],
                           value_labels={"quality": {"3": "Fair"}},
                           label_names={"rep": "quality"},
                           formats={"rep": "%9.2f"})
    want = sorted({3.0: "Fair", 4.0: "4", 5.0: "5"}[v] for v in _DF["rep"])
    for fig in (std, srv):
        assert sorted(_texts_of(fig)) == want


def test_mlabformat_does_not_touch_a_value_label():
    std, srv, std_w, srv_w = _both([plot_for("scatter", {
        "mlabel": "foreign", "mlabformat": "%9.2f"})])
    assert not std_w and not srv_w, (std_w, srv_w)
    for fig in (std, srv):
        assert set(_texts_of(fig)) == {"Domestic", "Foreign"}


@pytest.mark.parametrize("fmt,present", [
    (None, ["1.5", "2.25", "3", "4.5", "5", "6.75", "7", "8"]),
    ("%9.2f", ["1.50", "2.25", "3.00", "4.50", "5.00", "6.75", "7.00",
               "8.00"]),
], ids=["no format", "%9.2f"])
def test_a_missing_numeric_label_is_a_dot(fmt, present):
    """Measured: "." whatever the format; dash drew NaN, or nothing."""
    std, srv, _, _ = _both([plot_for("scatter", {"mlabel": "gap"})],
                           formats={"gap": fmt} if fmt else None)
    for fig in (std, srv):
        assert sorted(_texts_of(fig)) == sorted(present + [".", "."])


def test_a_missing_value_labelled_value_is_a_dot():
    df = _DF.copy()
    df.loc[[2, 5], "foreign"] = np.nan
    std, srv, _, _ = _both([plot_for("scatter", {"mlabel": "foreign"})],
                           df=df)
    for fig in (std, srv):
        texts = _texts_of(fig)
        assert texts.count(".") == 2 and "NaN" not in texts, texts


def _served_after_filter(ptype, df, label, value):
    """The served figure's labels, drawn, after the dropdown on foreign is
    moved to *value* -- and each LabelSet's text field, which must still be
    a column of its source after the filter's redraw."""
    from bokeh.models import Select
    spec = tp._spec([plot_for(ptype, {"mlabel": label})],
                    {"filter": "foreign, type(dropdown)"})
    tag, sp, dp = _write(spec, df, {"origin": dict(_ORIGIN)},
                         {"foreign": "origin"})
    ap = os.path.join(_TMP, f"app_f{tag}.py")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(ap)
        mod = load_app(ap, f"_mlpf_{tag}")
        doc = Document()
        mod.make_document(doc)
        w = [m for m in doc.select({"type": Select})][0]
        old = w.value
        w.value = value
        for cb in w._callbacks.get("value", []):
            cb("value", old, value)
    fig = [m for m in tp._walk_models(doc)
           if type(m).__name__ == "figure"][0]
    fields = [(_field(ls.text), list(ls.source.data)) for ls in
              _labelsets(fig)]
    return fig, fields


@pytest.mark.parametrize("ptype", ["rscatter", "pcscatter", "dropline"])
def test_a_served_filter_keeps_the_label_column(ptype):
    """The text column a LabelSet draws is named by the variable alone,
    never by whether the rows hold a missing value: a served filter redraws
    rscatter's, pcscatter's and dropline's sources through the mapper, and
    a column that exists only while a missing label is in view would leave
    the live LabelSet naming a column its source no longer has."""
    df = _DF.copy()
    df["gap"] = [np.nan, 2.0, 3.0, 4.0, np.nan, 6.0, 7.0, 8.0, 9.0, 10.0]
    fig, fields = _served_after_filter(ptype, df, "gap", "1.0")
    assert fields, ptype
    for field, cols in fields:
        assert field in cols, (ptype, field, cols)
    want = _expected(ptype, "gap", df=df[df["foreign"] == 1])
    assert _drawn_labels(fig) == want, ptype


def test_mlabformat_writes_a_missing_value_as_a_dot():
    std, srv, _, _ = _both([plot_for("scatter", {"mlabel": "gap",
                                                 "mlabformat": "%9.1f"})])
    for fig in (std, srv):
        texts = _texts_of(fig)
        assert texts.count(".") == 2 and "" not in texts, texts


# ===========================================================================
# 4. dash.ado: what twoway refuses and ignores, per plot type
# ===========================================================================

_ADO = os.path.join(_HERE, "..", "dash.ado")


def _fold_body():
    with open(_ADO, encoding="utf-8") as fh:
        return _program_body(fh.read(), "_dash_fold_mlab") or ""


def test_dash_ado_refuses_mlabel_where_twoway_refuses_it():
    """mspline and mband read the label variable as a third plotted
    variable: "too many variables specified", r(103)."""
    body = _fold_body()
    m = re.search(r'local mlab_refused\s+"([^"]+)"', body)
    assert m and sorted(m.group(1).split()) == sorted(_REFUSED), body[:200]
    assert "exit 103" in body


def test_dash_ado_ignores_mlabel_where_twoway_never_reads_it():
    """histogram and function accept mlabel(nosuchvar) with rc 0."""
    m = re.search(r'local mlab_unread\s+"([^"]+)"', _fold_body())
    assert m and sorted(m.group(1).split()) == ["function", "histogram"]


def test_the_fold_runs_before_the_value_rules():
    """So mlabel(nosuchvar) is never refused on a type twoway ignores it on,
    and r(111) still comes first where the variable does not exist."""
    with open(_ADO, encoding="utf-8") as fh:
        src = fh.read()
    body = _program_body(src, "_dash_fold_bw")
    assert '_dash_fold_mlab "`ptype\'"' in body


# ===========================================================================
# 5. Adversarial cases (CLAUDE.md rule 18) -- the value labels are data
# ===========================================================================

class TestAdversarialMarkerLabels:
    # ---- bypass: a key that is not Stata's spelling of the code ----------
    def test_a_label_keyed_by_another_spelling_is_not_matched(self):
        """Stata keys a label by the integer code; "01", "1.0" or " 1" is
        not 1, and must not become one through a lenient parse."""
        for key in ("01", "1.0", " 1", "\u0661"):
            assert dr.GlyphMapper._mlabel_value_text(1.0, {key: "X"}) == "1"

    # ---- injection: markup and code in a value label ----------------------
    def test_markup_in_a_value_label_is_carried_as_text(self):
        """A LabelSet is canvas text: the label is drawn as written and
        never reaches the page as markup."""
        bad = "</script><script>alert(1)</script>"
        hostile = {"origin": {"0": bad, "1": "Foreign"}}
        std, srv, _, _ = _both([plot_for("scatter", {"mlabel": "foreign"})],
                               value_labels=hostile)
        for fig in (std, srv):
            assert bad in _texts_of(fig)
        # The page is written from the SAME hostile labels.  It was
        # test_mode_parity's page, whose data labels foreign
        # Domestic/Foreign, so the payload never entered it and the absence
        # check below could not fail (measured 24sep2026).
        spec = tp._spec([plot_for("scatter", {"mlabel": "foreign"})])
        _, sp, dp = _write(spec, _DF, hostile, {"foreign": "origin"})
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            page = dr.DashRenderer(sp, dp).render()
        assert bad not in page and "<script>alert(1)" not in page
        # ...and it is IN the page, as text: the embedded document (which
        # Bokeh HTML-escapes, so only its decoded form holds the raw text)
        # draws it, or the absence above is of a label that was dropped.
        blocks = re.findall(r'<script type="application/json" id="[^"]+">'
                            r'\s*(.*?)\s*</script>', page, re.S)
        docs = [d for b in blocks
                for d in json.loads(html.unescape(b)).values()]
        assert len(docs) == 1, f"{len(docs)} embedded documents"
        figs = [m for m in tp._walk_models(Document.from_json(docs[0]))
                if type(m).__name__ == "figure"]
        assert figs and bad in _texts_of(figs[0])

    # ---- exhaustion: a label set or a label built to cost ------------------
    def test_a_huge_label_set_is_read_at_once(self):
        import time
        big = {str(i): "L%d" % i for i in range(200_000)}
        gm = dr.GlyphMapper(scheme=dr.SchemeParser("s2color"))
        gm.value_labels = {"big": big}
        gm.value_label_names = {"v": "big"}
        fig = figure()
        src = ColumnDataSource({"x": [1.0] * 2000, "y": [2.0] * 2000,
                                "v": [float(i) for i in range(2000)]})
        t0 = time.monotonic()
        gm._apply_mlabel_opts(fig, src, {"mlabel": "v"}, "x", "y")
        assert time.monotonic() - t0 < 2.0
        # G1 (WP-28): the marker-label column is named under the __dash prefix.
        assert src.data[dr._DASH_MLABEL_PREFIX + "v"][1999] == "L1999"

    def test_a_number_stata_would_write_long_is_bounded(self):
        """The widest text a number becomes is Stata's own: 18 characters."""
        for v in (1e308, -1e308, 5e-324, -1.2345678901234567e-300,
                  123456789012345678901234567890.0):
            assert len(dr.GlyphMapper._mlabel_number_text(v)) <= 18, v
