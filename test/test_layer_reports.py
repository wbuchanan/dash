"""test_layer_reports.py -- what dash says about a layer it cannot draw,
in both render modes (BUGS.md, S3 batch).

* "A dataset with no observations is reported as missing the variables it
  has": the data file of an empty dataset names its variables and holds no
  records, and both loaders built a frame with no columns from no records,
  so every layer said "variable(s) [...] not found in data source" and Bokeh
  logged MISSING_RENDERERS.  twoway draws a scatter's empty region in
  silence (measured 24sep2026, `sysuse auto', `keep if 0', `twoway scatter
  mpg weight': rc 0, nothing printed).  The frame now has the variables as
  its columns; the layer draws nothing, in silence, as twoway's does.
* "A range layer with no second y variable is reported as a plot type with
  no glyph mapper": the saved page fell through the range table to "no
  glyph mapper for plot type 'rscatter'" -- the mapper exists -- and the
  served app said nothing about why.  twoway refuses a range plot that
  names too few variables; dash, which cannot refuse a hand-written spec at
  render time, says what is missing in both modes.
"""
import json
import os
import sys
import warnings

import numpy as np
import pytest
from bokeh.document import Document

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import make_spec  # noqa: E402
from test_adversarial_matrix import _load_app  # noqa: E402


from conftest import render_models  # noqa: E402


def _payload(varnames, values):
    return {"StataJSON": {
        "variableNames": list(varnames),
        "variableLabels": {v: v for v in varnames},
        "valueLabels": {}, "valueLabelNames": {},
        "variableIsString": {v: False for v in varnames},
        "values": list(values),
    }}


def _write(tmp_path, spec, payload):
    sp = os.path.join(str(tmp_path), "spec.json")
    dp = os.path.join(str(tmp_path), "data.json")
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    with open(dp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)
    return sp, dp


def _dash_notes(caught):
    return [str(c.message) for c in caught
            if str(c.message).startswith("dash")]


def _saved(tmp_path, spec, payload):
    """(renderer, dash's notes) for the saved page."""
    sp, dp = _write(tmp_path, spec, payload)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r = dr.DashRenderer(sp, dp)
        render_models(r)
    return r, _dash_notes(caught)


def _served(tmp_path, spec, payload, tag):
    """(document, dash's notes while the served app draws a session, the
    served loader's frame)."""
    sp, dp = _write(tmp_path, spec, payload)
    op = os.path.join(str(tmp_path), "app.py")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(op)
    with open(op, encoding="utf-8") as fh:
        ns = _load_app(fh.read(), tag)
    doc = Document()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        ns["make_document"](doc)
    _spec, df, _meta = ns["_load_spec_and_data"]()
    return doc, _dash_notes(caught), df


def _served_figures(doc):
    from bokeh.plotting import figure as _f
    return [m for m in doc.select({"type": type(_f())})]


# ----------------------------------------------------------------------
# An empty dataset
# ----------------------------------------------------------------------

_SCATTER = {"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}


class TestAnEmptyDatasetKeepsItsVariables:
    """Both loaders give the frame of a dataset with no observations the
    variables it has, and a scatter over it draws nothing in silence, as
    twoway's does."""

    def test_the_saved_frame_has_the_variables_as_columns(self, tmp_path):
        r, _notes = _saved(tmp_path, make_spec([dict(_SCATTER)]),
                           _payload(["mpg", "weight"], []))
        assert list(r.df.columns) == ["mpg", "weight"]
        assert len(r.df) == 0

    def test_the_saved_scatter_is_silent_and_keeps_its_renderer(
            self, tmp_path):
        r, notes = _saved(tmp_path, make_spec([dict(_SCATTER)]),
                          _payload(["mpg", "weight"], []))
        assert not [n for n in notes if "not found in data source" in n], notes
        # twoway scatter on no observations: rc 0, nothing printed.
        assert notes == [], notes
        rends = r.figures["g1"].renderers
        # A figure with no renderer is Bokeh's MISSING_RENDERERS.
        assert rends, "the empty scatter left the figure with no renderer"
        assert all(max((len(v) for v in x.data_source.data.values()),
                       default=0) == 0 for x in rends)

    def test_the_served_frame_has_the_variables_as_columns(self, tmp_path):
        _doc, _notes, df = _served(tmp_path, make_spec([dict(_SCATTER)]),
                                   _payload(["mpg", "weight"], []), "ed1")
        assert list(df.columns) == ["mpg", "weight"]
        assert len(df) == 0

    def test_the_served_scatter_is_silent(self, tmp_path):
        doc, notes, _df = _served(tmp_path, make_spec([dict(_SCATTER)]),
                                  _payload(["mpg", "weight"], []), "ed2")
        assert not [n for n in notes if "not found in data source" in n], notes
        assert notes == [], notes
        figs = _served_figures(doc)
        assert figs and all(f.renderers for f in figs)

    def test_a_list_shaped_empty_payload_is_read_the_same(self, tmp_path):
        """An empty ``values`` with the names given: the saved loader takes
        the names from ``variableNames`` whatever the records' shape."""
        payload = _payload(["mpg", "weight"], [])
        payload["StataJSON"].pop("variableIsString")
        r, notes = _saved(tmp_path, make_spec([dict(_SCATTER)]), payload)
        assert list(r.df.columns) == ["mpg", "weight"]
        assert notes == [], notes

    def test_a_payload_with_records_is_unchanged(self, tmp_path):
        """The columns come from the records when there are records, as
        before: a record's variable absent from ``variableNames`` stays."""
        payload = _payload(["mpg"], [{"mpg": 1.0, "weight": 2.0},
                                     {"mpg": 3.0, "weight": 4.0}])
        r, notes = _saved(tmp_path, make_spec([dict(_SCATTER)]), payload)
        assert list(r.df.columns) == ["mpg", "weight"]
        assert notes == [], notes

    def test_hostile_variable_names_do_not_become_columns(self, tmp_path):
        """Adversarial: ``variableNames`` is data.  A name that is not a
        string, or twenty thousand names, does not stop the loader or
        become a column that outlives it unchecked."""
        names = ["mpg", "weight", 7, None, {"a": 1}] + ["v%d" % i
                                                       for i in range(20000)]
        payload = _payload(["mpg", "weight"], [])
        payload["StataJSON"]["variableNames"] = names
        import time
        t0 = time.perf_counter()
        r, _notes = _saved(tmp_path, make_spec([dict(_SCATTER)]), payload)
        assert time.perf_counter() - t0 < 60.0
        assert "mpg" in r.df.columns and "weight" in r.df.columns
        assert all(isinstance(c, str) for c in r.df.columns)


# ----------------------------------------------------------------------
# A range layer with no second y variable
# ----------------------------------------------------------------------

_ROWS = [{"lo": float(i), "hi": float(i) + 2.0, "x": float(i)}
         for i in range(6)]
_NO_Y2 = "names no second y variable"


class TestARangeLayerWithNoSecondY:
    """A range layer that names no second y variable says so, in both
    modes, and never that its plot type has no glyph mapper."""

    @pytest.mark.parametrize("ptype", ["rscatter", "rarea", "rcap"])
    def test_the_saved_page_names_the_missing_variable(self, tmp_path, ptype):
        spec = make_spec([{"type": ptype, "yvar1": "lo", "xvar": "x",
                           "options": {}}])
        _r, notes = _saved(tmp_path, spec, _payload(["lo", "hi", "x"], _ROWS))
        assert not [n for n in notes if "no glyph mapper" in n], notes
        hit = [n for n in notes if _NO_Y2 in n]
        assert len(hit) == 1, notes
        assert ptype in hit[0]

    @pytest.mark.parametrize("ptype", ["rscatter", "rarea", "rcap"])
    def test_the_served_app_names_the_missing_variable(self, tmp_path, ptype):
        spec = make_spec([{"type": ptype, "yvar1": "lo", "xvar": "x",
                           "options": {}}])
        _doc, notes, _df = _served(tmp_path, spec,
                                   _payload(["lo", "hi", "x"], _ROWS),
                                   "r2_" + ptype)
        assert not [n for n in notes if "no glyph mapper" in n], notes
        hit = [n for n in notes if _NO_Y2 in n]
        assert len(hit) == 1, notes
        assert ptype in hit[0]

    def test_both_modes_word_it_the_same(self, tmp_path):
        spec = make_spec([{"type": "rcap", "yvar1": "lo", "xvar": "x",
                           "options": {}}])
        _r, saved = _saved(tmp_path, spec, _payload(["lo", "hi", "x"], _ROWS))
        _d, served, _df = _served(tmp_path, spec,
                                  _payload(["lo", "hi", "x"], _ROWS), "r3")
        assert [n for n in saved if _NO_Y2 in n] == \
            [n for n in served if _NO_Y2 in n]

    def test_a_range_layer_with_both_y_still_draws(self, tmp_path):
        spec = make_spec([{"type": "rcap", "yvar1": "lo", "yvar2": "hi",
                           "xvar": "x", "options": {}}])
        r, notes = _saved(tmp_path, spec, _payload(["lo", "hi", "x"], _ROWS))
        assert notes == [], notes
        assert any(max((len(v) for v in x.data_source.data.values()),
                       default=0) == 6 for x in r.figures["g1"].renderers)

    def test_an_unknown_type_still_says_no_glyph_mapper(self):
        """The note is for a range type; a type with no mapper keeps its
        own."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            stub = type("M", (), {"__getattr__":
                                  lambda self, n: (lambda *a, **k: None)})()
            got = dr._dash_add_glyph(stub, None, None, "nosuchplot", "", "",
                                     {})
        assert got is None
        assert any("no glyph mapper" in str(c.message) for c in caught)

    def test_a_hostile_type_name_is_not_echoed_raw(self):
        """Adversarial: the type is shown by repr(), so markup or a newline
        in a hand-written spec is quoted, not interpreted."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr._dash_note_no_second_y("r<script>\nscatter")
        msg = str(caught[0].message)
        assert "\n" not in msg and "'r<script>\\nscatter'" in msg


# ----------------------------------------------------------------------
# A fit with too few observations to fit: twoway's note, in both modes
# ----------------------------------------------------------------------
#
# BUGS.md, S3 batch: "On a dataset with no observations, dash draws an
# empty histogram where twoway refuses it, and says nothing for lfit where
# twoway notes it could not fit".  Measured 24sep2026 with the console
# binary: on no observations, or a sample its if/in empties, twoway lfit,
# qfit, lfitci and qfitci draw nothing, rc 0, with "(note:  regress could
# not fit model)"; on one observation qfit and qfitci give the same note,
# rc 0, and fpfit and fpfitci "(note:  fracpoly could not fit model)", rc
# 0, as they do when missing values empty their sample.  (What twoway
# refuses -- lfit on one observation, fpfit on none its if and in select,
# lpoly, kdensity, mspline, mband and histogram -- dash.ado refuses at
# registration: test_parser.cscript P1A-80.)  dash drew each in silence,
# or said "drew nothing from 1 observations".

_REG = "(note:  regress could not fit model)"
_FP = "(note:  fracpoly could not fit model)"


def _fit(ptype, **kw):
    d = {"type": ptype, "yvar": "mpg", "xvar": "weight", "options": {}}
    d.update(kw)
    return d


def _rows(n, y_missing=False):
    return [{"mpg": (None if y_missing else 20.0 + (i * 7) % 5),
             "weight": 2000.0 + 150 * i} for i in range(n)]


class TestAFitWithNothingToFitGivesTwowaysNote:
    """The fit layers twoway draws empty with a note carry that note, word
    for word, in both modes, once per layer, and not also dash's own
    "drew nothing"."""

    @pytest.mark.parametrize("ptype", ["lfit", "qfit", "lfitci", "qfitci"])
    def test_saved_no_observations(self, tmp_path, ptype):
        _r, notes = _saved(tmp_path, make_spec([_fit(ptype)]),
                           _payload(["mpg", "weight"], []))
        assert [n for n in notes if _REG in n] == [
            f"dash: graph 'g1' plot 1 ({ptype}): {_REG}"], notes
        assert not [n for n in notes if "drew nothing" in n], notes

    @pytest.mark.parametrize("ptype", ["lfit", "qfit", "lfitci", "qfitci"])
    def test_served_no_observations(self, tmp_path, ptype):
        _d, notes, _df = _served(tmp_path, make_spec([_fit(ptype)]),
                                 _payload(["mpg", "weight"], []),
                                 "fit0_" + ptype)
        assert [n for n in notes if _REG in n] == [
            f"dash: graph 'g1' plot 1 ({ptype}): {_REG}"], notes
        assert not [n for n in notes if "drew nothing" in n], notes

    @pytest.mark.parametrize("ptype,note", [("qfit", _REG), ("qfitci", _REG),
                                            ("fpfit", _FP), ("fpfitci", _FP)])
    def test_one_observation(self, tmp_path, ptype, note):
        spec = make_spec([_fit(ptype)])
        _r, saved = _saved(tmp_path, spec, _payload(["mpg", "weight"],
                                                    _rows(1)))
        _d, served, _df = _served(tmp_path, spec,
                                  _payload(["mpg", "weight"], _rows(1)),
                                  "fit1_" + ptype)
        for notes in (saved, served):
            assert [n for n in notes if note in n] == [
                f"dash: graph 'g1' plot 1 ({ptype}): {note}"], notes
            assert not [n for n in notes if "drew nothing" in n], notes

    def test_fpfit_emptied_by_missing_values(self, tmp_path):
        """twoway fpfit on a y missing everywhere: the note, rc 0."""
        _r, notes = _saved(tmp_path, make_spec([_fit("fpfit")]),
                           _payload(["mpg", "weight"],
                                    _rows(5, y_missing=True)))
        assert [n for n in notes if _FP in n] == [
            f"dash: graph 'g1' plot 1 (fpfit): {_FP}"], notes
        assert not [n for n in notes if "drew nothing" in n], notes

    def test_a_layer_its_own_if_empties(self, tmp_path):
        """(scatter mpg weight) (lfit mpg weight if mpg < 0): the layer's
        own qualifier leaves no row; the note names that layer."""
        spec = make_spec([
            {"type": "scatter", "yvar": "mpg", "xvar": "weight",
             "options": {}},
            _fit("lfit", if_expr="mpg < 0")])
        payload = _payload(["mpg", "weight"], _rows(6))
        _r, saved = _saved(tmp_path, spec, payload)
        _d, served, _df = _served(tmp_path, spec, payload, "fitif")
        want = [f"dash: graph 'g1' plot 2 (lfit): {_REG}"]
        assert [n for n in saved if _REG in n] == want, saved
        assert [n for n in served if _REG in n] == want, served

    def test_each_empty_fit_layer_is_noted_once(self, tmp_path):
        spec = make_spec([_fit("lfit"), _fit("qfitci")])
        _r, notes = _saved(tmp_path, spec, _payload(["mpg", "weight"], []))
        assert [n for n in notes if _REG in n] == [
            f"dash: graph 'g1' plot 1 (lfit): {_REG}",
            f"dash: graph 'g1' plot 2 (qfitci): {_REG}"], notes

    def test_a_fit_it_can_draw_is_silent(self, tmp_path):
        for ptype in ("lfit", "fpfit"):
            _r, notes = _saved(tmp_path, make_spec([_fit(ptype)]),
                               _payload(["mpg", "weight"], _rows(6)))
            assert notes == [], (ptype, notes)

    def test_a_scatter_on_no_observations_stays_silent(self, tmp_path):
        _r, notes = _saved(tmp_path, make_spec([dict(_SCATTER)]),
                           _payload(["mpg", "weight"], []))
        assert notes == [], notes

    def test_the_mark_is_not_in_the_page(self, tmp_path):
        """The note is dash's own bookkeeping: nothing of it is written
        into the document the page carries."""
        from bokeh.embed import json_item
        r, _notes = _saved(tmp_path, make_spec([_fit("lfit")]),
                           _payload(["mpg", "weight"], []))
        assert "_dash_unfit" not in json.dumps(json_item(r.figures["g1"]))

    def test_a_hostile_graph_name_is_quoted(self, tmp_path):
        """Adversarial: the graph's name comes from the spec; it is shown
        by repr(), so a newline or markup in it is quoted, never
        interpreted, as the "drew nothing" report shows it."""
        spec = make_spec([_fit("lfit")], graph_name="g<b>\nx")
        _r, notes = _saved(tmp_path, spec, _payload(["mpg", "weight"], []))
        hit = [n for n in notes if _REG in n]
        assert hit == [f"dash: graph 'g<b>\\nx' plot 1 (lfit): {_REG}"], notes

    def test_mark_unfit_marks_each_renderer_it_is_given(self):
        """GlyphMapper._mark_unfit: a renderer or a list of them, each
        marked with the estimator and handed back; any other word is not a
        mark, so no text of a spec's can reach the note through it."""
        from bokeh.plotting import figure
        f = figure()
        a, b = f.line(x=[], y=[]), f.varea(x=[], y1=[], y2=[])
        assert dr.GlyphMapper._mark_unfit(a, "regress") is a
        assert a._dash_unfit == "regress"
        pair = [a, b]
        assert dr.GlyphMapper._mark_unfit(pair, "fracpoly") is pair
        assert a._dash_unfit == b._dash_unfit == "fracpoly"
        c = f.line(x=[], y=[])
        dr.GlyphMapper._mark_unfit(c, "<b>\nregress")
        assert not hasattr(c, "_dash_unfit")

    def test_the_note_reads_the_mark_whatever_the_rows(self):
        """_dash_note_empty_layer gives twoway's note for a marked layer
        even with no rows -- twoway notes lfit on no observations -- and
        leaves an unmarked layer on no rows silent, as before."""
        from bokeh.plotting import figure
        f = figure()
        r = dr.GlyphMapper._mark_unfit(f.line(x=[], y=[]), "regress")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr._dash_note_empty_layer("", 3, "qfit", 0, [r])
            dr._dash_note_empty_layer("", 4, "scatter", 0,
                                      [f.line(x=[], y=[])])
        assert [str(c.message) for c in caught] == [
            f"dash: plot 3 (qfit): {_REG}"]

    def test_many_empty_fit_layers_are_bounded(self, tmp_path):
        """Resource exhaustion: forty empty fit layers give forty notes,
        one each, in bounded time."""
        import time
        spec = make_spec([_fit("lfit") for _ in range(40)])
        t0 = time.perf_counter()
        _r, notes = _saved(tmp_path, spec, _payload(["mpg", "weight"], []))
        assert time.perf_counter() - t0 < 120.0
        assert len([n for n in notes if _REG in n]) == 40


# ----------------------------------------------------------------------
# A fit or smoother on two or three observations, and on one: what twoway
# draws, in both modes (BUGS.md, S3 batch)
# ----------------------------------------------------------------------
#
# "qfit, lfitci and qfitci on two observations draw nothing and say so,
# where twoway draws the fit" and "lowess, mspline and mband on one
# observation give dash's "drew nothing" note, where twoway draws in
# silence".  Measured 24sep2026 with the console binary, reading each
# plotted serset (serset use) after `twoway <type> y x, n(5) nodraw':
#
#   x = 1 3, y = 2 5          regress y x x^2 omits x ("note: x omitted
#     because of collinearity"): qfit and qfitci draw 2, 2.46875, 3.125,
#     3.96875, 5 at x = 1, 1.5, 2, 2.5, 3; qfitci's and lfitci's band are
#     missing (df 0) and lfitci's line is 2, 2.75, 3.5, 4.25, 5.  rc 0, no
#     note.
#   x = -1 2, y = 3 1         x^2 omitted: qfit is the line, 3 2.5 2 1.5 1.
#   Which of x and x^2 regress omits when x takes two values a and b,
#     measured on 22 samples: x when |a + b| > 1 -- the centred x^2 is
#     (a + b) times the centred x -- and x^2 otherwise, ties included
#     (x = -5 6 omits x^2, x = -5 6.2 omits x).
#   x = 1 1 3, y = 2 4 5      x omitted: qfitci 3, 3.3125, 3.75, 4.3125, 5,
#     band -9.706204 .. 15.7062, -7.76992 .. 14.39492, -6.66502 ..
#     14.16502, -8.262742 .. 16.88774, -12.96929 .. 22.96929.
#   qfit, n(3)                twoway_qfit_parse.class reads n(3) as its
#     own default and draws 100 points (qfitci, n(3) draws 3).
#   one observation           lowess draws a missing smooth; mspline and
#     mband a serset of the one point, (2, 1); rc 0, nothing printed.
#   x constant (5 5 5), y 2 4 6   mspline and mband: the one point (4, 5).
#   two or three observations lowess and lpoly draw a missing smooth, and
#     lpolyci a missing band, rc 0, nothing printed.
#
# dash drew qfit, lfitci and qfitci on two observations as nothing with
# "drew nothing from 2 observations", drew qfit and qfitci on an x with two
# values as the line (x^2 omitted), and noted each silent smoother above.

_NOTHING = "drew nothing"


def _xy_rows(xs, ys):
    return [{"y": float(b), "x": float(a)} for a, b in zip(xs, ys)]


def _layer(ptype, **opts):
    return {"type": ptype, "yvar": "y",
            "xvar": "" if ptype in ("kdensity", "histogram") else "x",
            "options": {k: str(v) for k, v in opts.items()}}


def _sub(tmp_path, name):
    p = tmp_path / name
    p.mkdir(exist_ok=True)
    return p


def _drawn_saved(r):
    return [dict((k, list(v)) for k, v in rr.data_source.data.items())
            for f in r.figures.values() for rr in f.renderers]


def _drawn_served(doc):
    out = []
    for f in _served_figures(doc):
        out.extend(dict((k, list(v)) for k, v in rr.data_source.data.items())
                   for rr in f.renderers)
    return out


def _both(tmp_path, spec, rows, tag, varnames=("y", "x")):
    """[(drawn, notes) of the saved page, (drawn, notes) of the served
    app]."""
    payload = _payload(list(varnames), rows)
    r, saved = _saved(_sub(tmp_path, "saved"), spec, payload)
    doc, served, _df = _served(_sub(tmp_path, "served"), spec, payload, tag)
    return [(_drawn_saved(r), saved), (_drawn_served(doc), served)]


def _col(drawn, key):
    """The first non-empty column *key* a layer drew."""
    cols = [d[key] for d in drawn if key in d and len(d[key])]
    assert cols, (key, drawn)
    return [None if v is None else float(v) for v in cols[0]]


def _close(got, want, tol=1e-5):
    import math
    assert len(got) == len(want), (got, want)
    for g, w in zip(got, want):
        if w is None:
            assert g is None or math.isnan(g), (got, want)
        else:
            assert g is not None and abs(g - w) <= tol * max(1.0, abs(w)), \
                (got, want)


class TestAFitOnTwoObservationsIsDrawnAsTwowayDraws:
    """qfit, lfitci and qfitci on two observations draw twoway's fit, the
    band missing, in silence; on an x with two values the fit is of the
    term twoway's regress keeps."""

    @pytest.mark.parametrize("ptype,key,want", [
        ("qfit", "y", [2.0, 2.46875, 3.125, 3.96875, 5.0]),
        ("qfitci", "y_fit", [2.0, 2.46875, 3.125, 3.96875, 5.0]),
        ("lfitci", "y_fit", [2.0, 2.75, 3.5, 4.25, 5.0]),
    ])
    def test_two_observations(self, tmp_path, ptype, key, want):
        spec = make_spec([_layer(ptype, n=5)])
        for drawn, notes in _both(tmp_path, spec, _xy_rows([1, 3], [2, 5]),
                                  "two_" + ptype):
            _close(_col(drawn, key), want)
            xk = "x" if key == "y" else "x_fit"
            _close(_col(drawn, xk), [1.0, 1.5, 2.0, 2.5, 3.0])
            if ptype != "qfit":
                _close(_col(drawn, "y_lower"), [None] * 5)
                _close(_col(drawn, "y_upper"), [None] * 5)
            assert notes == [], notes

    def test_two_values_whose_sum_is_small_fit_the_line(self, tmp_path):
        spec = make_spec([_layer("qfit", n=5)])
        for drawn, notes in _both(tmp_path, spec, _xy_rows([-1, 2], [3, 1]),
                                  "two_neg"):
            _close(_col(drawn, "y"), [3.0, 2.5, 2.0, 1.5, 1.0])
            assert notes == [], notes

    @pytest.mark.parametrize("xs,ys,want", [
        ([1000, 3000], [10, 20], [10, 11.5625, 13.75, 16.5625, 20]),
        ([2, 5], [1, 4], [1, 1.508929, 2.178571, 3.008929, 4]),
        ([0, 1], [1, 2], [1, 1.25, 1.5, 1.75, 2]),
        ([-2, 2], [1, 5], [1, 2, 3, 4, 5]),
    ])
    def test_which_term_regress_omits(self, tmp_path, xs, ys, want):
        spec = make_spec([_layer("qfitci", n=5)])
        for drawn, notes in _both(tmp_path, spec, _xy_rows(xs, ys),
                                  "omit%d_%d" % (abs(xs[0]), xs[1])):
            _close(_col(drawn, "y_fit"), want)
            assert notes == [], notes

    @pytest.mark.parametrize("xs,ys,fit,lo,hi", [
        ([1, 1, 3], [2, 4, 5],
         [3, 3.3125, 3.75, 4.3125, 5],
         [-9.706204, -7.76992, -6.66502, -8.262742, -12.96929],
         [15.7062, 14.39492, 14.16502, 16.88774, 22.96929]),
        ([1, 3, 3], [2, 4, 5],
         [2, 2.390625, 2.9375, 3.640625, 4.5],
         [-6.984643, -5.254885, -3.162388, -1.547927, -1.853102],
         [10.98464, 10.03613, 9.037388, 8.829178, 10.8531]),
    ])
    def test_three_observations_on_two_values(self, tmp_path, xs, ys, fit,
                                              lo, hi):
        spec = make_spec([_layer("qfitci", n=5)])
        for drawn, notes in _both(tmp_path, spec, _xy_rows(xs, ys),
                                  "three%d" % xs[1]):
            _close(_col(drawn, "y_fit"), fit)
            _close(_col(drawn, "y_lower"), lo)
            _close(_col(drawn, "y_upper"), hi)
            assert notes == [], notes

    def test_lfitci_on_three_values_is_unchanged(self, tmp_path):
        """The control: three distinct values, lfitci's band has df 1."""
        spec = make_spec([_layer("lfitci", n=3)])
        for drawn, notes in _both(tmp_path, spec,
                                  _xy_rows([1, 3, 4], [2, 5, 3]), "ctl3"):
            _close(_col(drawn, "y_fit"), [2.5, 3.25, 4.0])
            _close(_col(drawn, "y_lower"), [-20.40644, -10.59627, -16.09027])
            assert notes == [], notes

    def test_qfit_reads_n3_as_its_default(self, tmp_path):
        """twoway_qfit_parse.class: `if .points == 3, .points = 100'."""
        spec = make_spec([_layer("qfit", n=3)])
        for drawn, _notes in _both(_sub(tmp_path, "q"), spec,
                                   _xy_rows([1, 3, 4], [2, 5, 3]), "q3"):
            ys = _col(drawn, "y")
            assert len(ys) == 100
            _close([ys[0], ys[1], ys[33], ys[-1]],
                   [2.0, 2.11509, 4.666667, 3.0])
        spec = make_spec([_layer("qfitci", n=3)])
        for drawn, _notes in _both(_sub(tmp_path, "qci"), spec,
                                   _xy_rows([1, 3, 4], [2, 5, 3]), "qci3"):
            _close(_col(drawn, "y_fit"), [2.0, 5.125, 3.0])

    @pytest.mark.parametrize("ptype", ["qfit", "qfitci"])
    def test_one_observation_keeps_twoways_note(self, tmp_path, ptype):
        """The boundary below: one observation is still regress's note."""
        spec = make_spec([_layer(ptype)])
        for _drawn, notes in _both(tmp_path, spec, _xy_rows([1], [2]),
                                   "one_" + ptype):
            assert notes == [
                f"dash: graph 'g1' plot 1 ({ptype}): {_REG}"], notes

    def test_qfit_design_keeps_twoways_term(self):
        """_qfit_design on an x with two values: the term regress keeps,
        by twoway's rule, and a design nothing collinear can hide."""
        import numpy as np
        X, Xg = dr._qfit_design(np.array([1.0, 3.0]),
                                np.array([1.0, 2.0, 3.0]))
        fit = dr._dash_wls(X, np.array([2.0, 5.0]))
        np.testing.assert_allclose(Xg @ fit["beta"], [2.0, 3.125, 5.0])
        X, Xg = dr._qfit_design(np.array([-1.0, 2.0]),
                                np.array([-1.0, 0.5, 2.0]))
        fit = dr._dash_wls(X, np.array([3.0, 1.0]))
        np.testing.assert_allclose(Xg @ fit["beta"], [3.0, 2.0, 1.0])
        # Three or more values: the full quadratic, as before.
        X, _Xg = dr._qfit_design(np.array([1.0, 3.0, 4.0]),
                                 np.array([1.0]))
        assert X.shape == (3, 3)

    def test_a_huge_two_valued_x_is_bounded(self, tmp_path):
        """Resource exhaustion and overflow: 200,000 observations on two
        values of x near 1e150, whose squares overflow, in bounded time;
        nothing infinite is drawn."""
        import math
        import time
        rows = [{"y": float(i % 7), "x": 1e150 if i % 2 else 3e150}
                for i in range(200000)]
        spec = make_spec([_layer("qfitci", n=5)])
        t0 = time.perf_counter()
        r, _notes = _saved(tmp_path, spec, _payload(["y", "x"], rows))
        assert time.perf_counter() - t0 < 120.0
        for d in _drawn_saved(r):
            for v in d.get("y_fit", []):
                assert v is None or not math.isinf(float(v))


class TestASmootherTwowayDrawsInSilenceIsSilent:
    """lowess, mspline and mband on one observation, lowess and lpoly on
    two or three, and mspline and mband on a constant x draw what twoway
    draws and say nothing."""

    @pytest.mark.parametrize("ptype", ["lowess", "mspline", "mband"])
    def test_one_observation(self, tmp_path, ptype):
        spec = make_spec([_layer(ptype)])
        for drawn, notes in _both(tmp_path, spec, _xy_rows([1], [2]),
                                  "one_" + ptype):
            assert notes == [], notes
            if ptype != "lowess":
                xk, yk = (("x_sp", "y_sp") if ptype == "mspline"
                          else ("x_mb", "y_mb"))
                assert _col(drawn, xk) == [1.0]
                assert _col(drawn, yk) == [2.0]

    @pytest.mark.parametrize("ptype,xk,yk", [("mspline", "x_sp", "y_sp"),
                                             ("mband", "x_mb", "y_mb")])
    def test_a_constant_x_is_its_one_cross_median(self, tmp_path, ptype, xk,
                                                  yk):
        spec = make_spec([_layer(ptype)])
        for drawn, notes in _both(tmp_path, spec,
                                  _xy_rows([5, 5, 5], [2, 4, 6]),
                                  "const_" + ptype):
            assert _col(drawn, xk) == [5.0]
            assert _col(drawn, yk) == [4.0]
            assert notes == [], notes

    @pytest.mark.parametrize("ptype", ["lowess", "lpoly", "lpolyci"])
    @pytest.mark.parametrize("n", [2, 3])
    def test_two_or_three_observations(self, tmp_path, ptype, n):
        spec = make_spec([_layer(ptype)])
        rows = _xy_rows([1, 3, 4][:n], [2, 5, 3][:n])
        for _drawn, notes in _both(tmp_path, spec, rows,
                                   "few%d_%s" % (n, ptype)):
            assert notes == [], notes

    @pytest.mark.parametrize("ptype", ["lpoly", "lpolyci"])
    def test_lpoly_whose_smooth_is_missing_everywhere(self, tmp_path, ptype):
        """y = 20 + mod(7(i-1), 5), x = 2000 + 150(i-1), i = 1..8: twoway
        lpoly's and lpolyci's smooth is missing at every grid point
        (measured), and neither says anything."""
        rows = _xy_rows([2000 + 150 * i for i in range(8)],
                        [20 + (7 * i) % 5 for i in range(8)])
        spec = make_spec([_layer(ptype)])
        for _drawn, notes in _both(tmp_path, spec, rows, "miss_" + ptype):
            assert notes == [], notes

    def test_a_constant_x_lowess_is_silent_too(self, tmp_path):
        """A constant x: twoway's smooth is missing on every row, drawn in
        silence (test_pipeline_integration.py EC-04; measured 19oct2026).

        Flipped: WP-32 -- dash kept its note here (BUGS.md "An all-missing
        scatter, a constant-x lowess and a constant kdensity keep dash's
        "drew nothing" note")."""
        spec = make_spec([_layer("lowess")])
        _r, notes = _saved(tmp_path, spec,
                           _payload(["y", "x"], _xy_rows([5] * 6, range(6))))
        assert not [n for n in notes if _NOTHING in n], notes

    def test_mark_silent_marks_each_renderer(self):
        from bokeh.plotting import figure
        f = figure()
        a, b = f.line(x=[], y=[]), f.varea(x=[], y1=[], y2=[])
        assert dr.GlyphMapper._mark_silent(a) is a
        pair = [a, b]
        assert dr.GlyphMapper._mark_silent(pair) is pair
        assert a._dash_silent is True and b._dash_silent is True
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr._dash_note_empty_layer("g1", 1, "lowess", 50, [a])
            dr._dash_note_empty_layer("g1", 2, "lowess", 50,
                                      [f.line(x=[], y=[])])
        assert [str(c.message) for c in caught] == [
            "dash: graph 'g1' plot 2 (lowess) drew nothing from 50 "
            "observations."]

    def test_the_silent_mark_is_not_in_the_page(self, tmp_path):
        from bokeh.embed import json_item
        r, _notes = _saved(tmp_path, make_spec([_layer("lowess")]),
                           _payload(["y", "x"], _xy_rows([1], [2])))
        assert "_dash_silent" not in json.dumps(json_item(r.figures["g1"]))


# ----------------------------------------------------------------------
# A by() graph's empty and one-observation panels (BUGS.md, S3 batch)
# ----------------------------------------------------------------------
#
# "A by() graph's empty panels are not answered as twoway answers each
# panel".  Measured 24sep2026 with the console binary on auto:
#   twoway draws a by() graph panel by panel, plot by plot, and leaves out
#   a panel a plot cannot be drawn in (bygraph_g.class RunGraph); counted
#   with .Graph.n after `twoway ..., by(foreign) nodraw'.
#   a panel the plot draws nothing in, there for another plot --
#   (scatter mpg weight) (<type> mpg weight if foreign==0), by(foreign):
#   lfit, qfit, lfitci, qfitci "(note:  regress could not fit model)", two
#   panels; lowess, kdensity, histogram nothing, two panels; lpoly and
#   lpolyci nothing, ONE panel -- the empty one is left out (fpfit,
#   fpfitci, mspline and mband are refused, r(198), by dash.ado:
#   test_parser.cscript P1A-83).
#   a panel of one observation: lfit and lfitci the note and then
#   "insufficient observations", and the panel left out; lpoly, lpolyci
#   and kdensity the panel left out, in silence; qfit, qfitci, fpfit,
#   fpfitci the note, two panels; lowess, mspline, mband, histogram
#   nothing, two panels.  rc 0 throughout.
# dash drew every panel, said "drew nothing from N observations" for each
# silent one, and gave lfit's note without "insufficient observations".

_BY_TYPES = ["lfit", "qfit", "lfitci", "qfitci", "fpfit", "fpfitci",
             "lowess", "lpoly", "lpolyci", "mspline", "mband", "kdensity",
             "histogram"]
_BY_NOTE = {"lfit": _REG, "qfit": _REG, "lfitci": _REG, "qfitci": _REG,
            "fpfit": _FP, "fpfitci": _FP}
#: The panels twoway draws: with an empty panel, with a panel of one.
_BY_PANELS_EMPTY = {"lpoly": 1, "lpolyci": 1}
_BY_PANELS_ONE = {"lfit": 1, "lfitci": 1, "lpoly": 1, "lpolyci": 1,
                  "kdensity": 1}


def _by_rows(k):
    r = [{"y": 20.0 + (i * 7) % 5, "x": 2000.0 + 150 * i, "g": 0.0}
         for i in range(8)]
    r += [{"y": 30.0 + i, "x": 1800.0 + 100 * i, "g": 1.0} for i in range(k)]
    return r


def _by_spec(plots):
    spec = make_spec(plots)
    spec["graphs"][0]["graph_options"]["by"] = "g"
    return spec


def _by_both(tmp_path, spec, rows, tag, varnames=("y", "x", "g")):
    """[(panels, notes) of the saved page, (panels, notes) served]."""
    payload = _payload(list(varnames), rows)
    r, saved = _saved(_sub(tmp_path, "saved"), spec, payload)
    doc, served, _df = _served(_sub(tmp_path, "served"), spec, payload, tag)
    return [(len(r.figures), saved), (len(_served_figures(doc)), served)]


class TestAByPanelIsAnsweredAsTwowayAnswersIt:

    @pytest.mark.parametrize("ptype", ["lfit", "qfit", "lfitci", "qfitci",
                                       "lowess", "lpoly", "lpolyci",
                                       "kdensity", "histogram"])
    def test_a_panel_the_plot_draws_nothing_in(self, tmp_path, ptype):
        lay = _layer(ptype)
        lay["if_expr"] = "g == 0"
        spec = _by_spec([{"type": "scatter", "yvar": "y", "xvar": "x",
                          "options": {}}, lay])
        for panels, notes in _by_both(tmp_path, spec, _by_rows(2),
                                      "by0_" + ptype):
            assert panels == _BY_PANELS_EMPTY.get(ptype, 2), (ptype, panels)
            want = _BY_NOTE.get(ptype)
            if want:
                assert len(notes) == 1 and notes[0].endswith(
                    f"plot 2 ({ptype}): {want}"), notes
            else:
                assert notes == [], notes

    @pytest.mark.parametrize("ptype", _BY_TYPES)
    def test_a_panel_of_one_observation(self, tmp_path, ptype):
        spec = _by_spec([_layer(ptype)])
        for panels, notes in _by_both(tmp_path, spec, _by_rows(1),
                                      "by1_" + ptype):
            assert panels == _BY_PANELS_ONE.get(ptype, 2), (ptype, panels)
            want = _BY_NOTE.get(ptype)
            if not want:
                assert notes == [], notes
                continue
            got = [n.split(f"plot 1 ({ptype}): ", 1)[-1] for n in notes]
            if ptype in ("lfit", "lfitci"):
                assert got == [want, "insufficient observations"], notes
            else:
                assert got == [want], notes

    @pytest.mark.parametrize("ptype", ["qfit", "lfitci", "qfitci", "lpoly",
                                       "lfit", "kdensity"])
    def test_a_panel_of_two_observations_is_drawn(self, tmp_path, ptype):
        spec = _by_spec([_layer(ptype)])
        for panels, notes in _by_both(tmp_path, spec, _by_rows(2),
                                      "by2_" + ptype):
            assert panels == 2
            assert notes == [], notes

    def test_the_first_plot_that_cannot_draw_decides(self, tmp_path):
        """(lpoly if g==0) (lfit if g==0 | one==1): the empty lpoly leaves
        the second panel out before lfit's one observation is counted, so
        no note is given for it (twoway: P1A-83 "lpoly first")."""
        rows = _by_rows(3)
        for r in rows:
            r["one"] = 0.0
        rows[-1]["one"] = 1.0
        lp = _layer("lpoly")
        lp["if_expr"] = "g == 0"
        lf = _layer("lfit")
        lf["if_expr"] = "g == 0 | one == 1"
        spec = _by_spec([lp, lf])
        for panels, notes in _by_both(tmp_path, spec, rows, "byfirst",
                                      ("y", "x", "g", "one")):
            assert panels == 1
            assert notes == [], notes

    def test_a_weight_not_above_zero_leaves_the_row_out(self, tmp_path):
        rows = _by_rows(3)
        for r in rows:
            r["w"] = 0.0 if r["g"] == 1.0 else 1.0
        rows[-1]["w"] = 2.0
        lay = _layer("lpoly", weight="aweight", wexp="w")
        spec = _by_spec([{"type": "scatter", "yvar": "y", "xvar": "x",
                          "options": {}}, lay])
        for panels, _notes in _by_both(tmp_path, spec, rows, "byw",
                                       ("y", "x", "g", "w")):
            assert panels == 1

    def test_every_panel_left_out_draws_one_empty_panel_and_says_so(
            self, tmp_path):
        """dash.ado refuses it, "nothing to graph", r(198); a spec that
        reaches the renderer keeps the page and names it."""
        rows = [{"y": 1.0, "x": 1.0, "g": 0.0},
                {"y": 2.0, "x": 2.0, "g": 1.0}]
        spec = _by_spec([_layer("lpoly")])
        for panels, notes in _by_both(tmp_path, spec, rows, "byall"):
            assert panels == 1
            assert "dash: graph 'g1': nothing to graph." in notes, notes

    def test_panel_dropped_reads_the_qualifier_column(self):
        """_dash_by_panel_dropped on its own: a plot's qualifier column
        (the path of every spec dash.ado writes), an ``in`` range counted
        over the whole data, and a plot type that never leaves a panel
        out."""
        import pandas as pd
        frame = pd.DataFrame({"y": [1.0, 2.0, 3.0, 4.0],
                              "x": [1.0, 2.0, 3.0, 4.0],
                              "g": [0.0, 0.0, 1.0, 1.0]})
        panel = frame[frame["g"] == 1.0]
        masks = {"__q1": pd.Series([True, True, True, False],
                                   index=frame.index)}
        lp = {"type": "lpoly", "yvar": "y", "xvar": "x", "qual_col": "__q1"}
        assert dr._dash_by_panel_dropped(panel, frame, [lp], masks)
        lp2 = {"type": "lpoly", "yvar": "y", "xvar": "x", "in_expr": "2/4"}
        assert not dr._dash_by_panel_dropped(panel, frame, [lp2], None)
        lp3 = {"type": "lpoly", "yvar": "y", "xvar": "x", "in_expr": "1/3"}
        assert dr._dash_by_panel_dropped(panel, frame, [lp3], None)
        sc = {"type": "scatter", "yvar": "y", "xvar": "x", "in_expr": "1/1"}
        assert not dr._dash_by_panel_dropped(panel, frame, [sc], None)

    def test_panel_dropped_on_hostile_input(self):
        """Adversarial: a plot that is not a dict, names a variable the
        data does not carry or a qualifier column that is not there, or
        carries a qualifier the whitelist refuses, leaves the panel in place
        without raising and runs nothing; 200,000 rows under twenty layers
        are counted in bounded time."""
        import time
        import pandas as pd
        frame = pd.DataFrame({"y": [1.0, 2.0], "x": [1.0, 2.0]})
        hostile = ["lpoly", None,
                   {"type": "lpoly", "yvar": "nope", "xvar": "x"},
                   {"type": "lpoly", "yvar": "y", "xvar": "x",
                    "qual_col": "__missing"},
                   {"type": "lfit", "yvar": "y", "xvar": "x",
                    "if_expr": "__import__('os').system('echo x')"}]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            got = [dr._dash_by_panel_dropped(frame, frame, [h], {})
                   for h in hostile]
        assert got == [False] * 5
        big = pd.DataFrame({"y": np.arange(200000.0),
                            "x": np.arange(200000.0),
                            "g": np.arange(200000) % 2})
        t0 = time.perf_counter()
        assert not dr._dash_by_panel_dropped(
            big[big["g"] == 0], big,
            [{"type": "lpoly", "yvar": "y", "xvar": "x",
              "if_expr": "y > 5"}] * 20, None)
        assert time.perf_counter() - t0 < 60.0

    def test_mark_insufficient_marks_each_renderer(self):
        """GlyphMapper._mark_insufficient: a renderer or a list, each
        marked and handed back; the second note follows regress's only."""
        from bokeh.plotting import figure
        f = figure()
        a, b = f.line(x=[], y=[]), f.varea(x=[], y1=[], y2=[])
        pair = [a, b]
        assert dr.GlyphMapper._mark_insufficient(pair) is pair
        assert a._dash_insufficient is True and b._dash_insufficient is True
        dr.GlyphMapper._mark_unfit(pair, "regress")
        c = dr.GlyphMapper._mark_insufficient(f.line(x=[], y=[]))
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr._dash_note_empty_layer("", 1, "lfitci", 1, pair)
            # Unmarked by _mark_unfit: no note, and no second one.
            dr._dash_note_empty_layer("", 2, "lfit", 0, [c])
        assert [str(w.message) for w in caught] == [
            f"dash: plot 1 (lfitci): {_REG}",
            "dash: plot 1 (lfitci): insufficient observations"]

    def test_insufficient_is_given_once_per_layer_and_quoted(self, tmp_path):
        """Adversarial: a hostile graph name is shown by repr() in the
        second note too; forty one-observation lfit layers give forty
        pairs, in bounded time."""
        import time
        spec = make_spec([_layer("lfit") for _ in range(40)],
                         graph_name="g<b>\nx")
        t0 = time.perf_counter()
        _r, notes = _saved(tmp_path, spec,
                           _payload(["y", "x"], _xy_rows([1], [2])))
        assert time.perf_counter() - t0 < 120.0
        ins = [n for n in notes if n.endswith("insufficient observations")]
        assert len(ins) == 40
        assert all(n.startswith("dash: graph 'g<b>\\nx' plot ") for n in ins)


# ----------------------------------------------------------------------
# by(, total): the Total panel is one more panel (BUGS.md, S3 batch)
# ----------------------------------------------------------------------
#
# "A by() given only in a later || segment, and by()'s total panel, are not
# answered as twoway answers them".  Measured 24sep2026 with the console
# binary on auto, counting panels with .Graph.n after `nodraw'
# (test_parser.cscript P1A-84):
#   the Total panel is drawn after the groups and answered as they are:
#   lfit and lfitci on one observation leave it out after regress's note
#   and "insufficient observations"; lpoly and lpolyci on one or none, and
#   kdensity on one, leave it out in silence.  `lfit mpg weight if _n==1 |
#   _n==60, by(foreign, total)' draws the Total panel alone, rc 0; `lfit
#   mpg weight if _n==1, by(foreign, total)' leaves every panel out,
#   "nothing to graph", r(198).
#   the Total panel holds the rows of every group: the rows whose by()
#   value is missing only under missing (bygraph_g.class runs it with the
#   groups' missvar).
#   total is TOTal in bygraph_g.class: tot, tota and total.
# dash drew the Total panel whatever it held, and read total alone.

_BY_TOTAL_TYPES = ["lfit", "lfitci", "lpoly", "lpolyci", "kdensity"]


def _by_total_spec(plots):
    spec = make_spec(plots)
    spec["graphs"][0]["graph_options"]["by"] = "g, total"
    return spec


class TestAByTotalPanelIsAnsweredAsTwowayAnswersIt:

    @pytest.mark.parametrize("ptype", _BY_TOTAL_TYPES)
    def test_a_one_observation_total_panel_is_left_out(self, tmp_path,
                                                       ptype):
        """One observation in all: its group and the Total panel are both
        left out, and nothing is left to graph."""
        rows = [{"y": 20.0, "x": 2000.0, "g": 0.0}]
        spec = _by_total_spec([_layer(ptype)])
        for panels, notes in _by_both(tmp_path, spec, rows,
                                      "bytot1_" + ptype):
            assert panels == 1, (ptype, panels)
            assert "dash: graph 'g1': nothing to graph." in notes, notes
            ins = [n for n in notes if n.endswith("insufficient observations")]
            assert len(ins) == (2 if ptype in ("lfit", "lfitci") else 0), notes

    @pytest.mark.parametrize("ptype", _BY_TOTAL_TYPES)
    def test_the_total_panel_is_drawn_when_every_group_is_left_out(
            self, tmp_path, ptype):
        rows = [{"y": 20.0, "x": 2000.0, "g": 0.0},
                {"y": 25.0, "x": 3000.0, "g": 1.0}]
        spec = _by_total_spec([_layer(ptype)])
        for panels, notes in _by_both(tmp_path, spec, rows,
                                      "bytot2_" + ptype):
            assert panels == 1, (ptype, panels)
            assert not [n for n in notes if "nothing to graph" in n], notes
            ins = [n for n in notes if n.endswith("insufficient observations")]
            assert len(ins) == (2 if ptype in ("lfit", "lfitci") else 0), notes

    def test_the_total_panel_leaves_out_rows_whose_by_value_is_missing(
            self, tmp_path):
        """lpoly on one row of g 0 and three of g missing: the group and
        the Total panel, which holds the rows whose by() value is not
        missing, are both left out; under missing the missing group and
        the Total panel, of four, are drawn."""
        rows = [{"y": 20.0, "x": 2000.0, "g": 0.0}] + [
            {"y": 25.0 + i, "x": 3000.0 + 100 * i, "g": None}
            for i in range(3)]
        spec = _by_total_spec([_layer("lpoly")])
        for panels, notes in _by_both(tmp_path, spec, rows, "bytotmiss"):
            assert panels == 1
            assert "dash: graph 'g1': nothing to graph." in notes, notes
        spec["graphs"][0]["graph_options"]["by"] = "g, total missing"
        for panels, notes in _by_both(_sub(tmp_path, "m"), spec, rows,
                                      "bytotmiss2"):
            assert panels == 2
            assert not [n for n in notes if "nothing to graph" in n], notes

    @pytest.mark.parametrize("sub,want", [
        ("total", True), ("tota", True), ("tot", True), ("to", False),
        ("total(1)", False), ('title("total")', False),
        ("title(tot) cols(2)", False)])
    def test_total_is_read_as_bygraph_reads_it(self, sub, want):
        """TOTal in bygraph_g.class; a sub-option's argument is never read
        for it (adversarial)."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _v, _c, total, _m, _u = dr._dash_parse_by("g, " + sub)
        assert total is want

    def test_a_hostile_total_spec_is_bounded(self, tmp_path):
        """Adversarial: 300 groups of one observation under by(, total)
        with twenty lpoly layers are all left out but the Total panel, in
        bounded time, and nothing is run from the by() text."""
        import time
        rows = [{"y": float(i % 7), "x": float(i), "g": float(i)}
                for i in range(300)]
        spec = _by_total_spec([_layer("lpoly") for _ in range(20)])
        spec["graphs"][0]["graph_options"]["by"] = (
            "g, total title(\"__import__('os').system('echo x')\")")
        t0 = time.perf_counter()
        r, _notes = _saved(tmp_path, spec, _payload(["y", "x", "g"], rows))
        assert time.perf_counter() - t0 < 120.0
        assert len(r.figures) == 1
