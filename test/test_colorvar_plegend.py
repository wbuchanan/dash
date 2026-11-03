"""
test_colorvar_plegend.py -- the colour key's interplay with the plot
legend (WP-42 section 42-04).

What twoway draws is measured, not modelled, by
scripts/extract_colorvar_plegend_truth.do into
test/fixtures/colorvar_plegend_truth.json (StataNow 19.5, sysuse auto):

* CV-4: ``colordiscrete coloruseplegend`` keys the levels in a box right
  of the plot, highest first and then ``Other`` (K5: 5 4 3 2 1 Other),
  untitled, each text the level in the variable's display format, not its
  value label (K6: foreign keyed 1 0), marker swatches even under
  colorkeysrange (C28), framed in the scheme's legend box (s2color: a
  white box with a black frame; stcolor: white on white, ST), and
  colorotherlabel() names the gray entry (X1).

Every test that draws runs in both modes: the saved page (DashRenderer)
and the served app (ServerAppBuilder); both run the same GlyphMapper.
"""
from __future__ import annotations

import itertools
import json
import os
import sys
import warnings

import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import Legend

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import load_app, make_data_json, render_models  # noqa: E402
from test_server_layer_defects import (_figures_of, make_spec,  # noqa: E402
                                       plot_for)

_FIX = os.path.join(_HERE, "fixtures", "colorvar_plegend_truth.json")
with open(_FIX, encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)
PROBES = TRUTH["probes"]
MODES = ["saved", "served"]

with open(os.path.join(_HERE, "fixtures", "colorvar_truth.json"),
          encoding="utf-8") as _fh:
    _AUTO = json.load(_fh)["_data"]["auto"]
#: sysuse auto's columns (colorvar_truth.json's copy of them).
AUTO = pd.DataFrame({k: [float("nan") if v is None else float(v)
                         for v in vs] for k, vs in _AUTO.items()})
_LABELS = dict(
    value_labels={"origin": {"0": "Domestic", "1": "Foreign"}},
    value_label_names={"foreign": "origin"},
    variable_labels={"rep78": "Repair record 1978", "foreign": "Car origin",
                     "mpg": "Mileage (mpg)", "weight": "Weight (lbs.)",
                     "price": "Price"})
_FORMATS = {"rep78": "%8.0g", "foreign": "%8.0g", "price": "%8.0gc",
            "mpg": "%8.0g", "weight": "%8.0gc"}

_SEQ = itertools.count()
_CACHE: dict = {}


@pytest.fixture(scope="module")
def tmp(tmp_path_factory):
    return tmp_path_factory.mktemp("cvp")


def _build(tmp, mode, plots, go=None, df=None, scheme=""):
    """The figures of a one-graph spec of *plots* over sysuse auto, in
    *mode*."""
    key = (mode, json.dumps([plots, go, scheme], sort_keys=True),
           None if df is None else id(df))
    if key in _CACHE:
        return _CACHE[key]
    spec = make_spec(plots, build_options={"formats": dict(_FORMATS),
                                           "scheme": scheme},
                     graph_options=go)
    tag = next(_SEQ)
    sp = tmp / f"cvp_spec_{tag}.json"
    dp = tmp / f"cvp_data_{tag}.json"
    sp.write_text(json.dumps(spec))
    dp.write_text(json.dumps(make_data_json(AUTO if df is None else df,
                                            **_LABELS)))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if mode == "saved":
            r = dr.DashRenderer(str(sp), str(dp))
            render_models(r)
            figs = list(r.figures.values())
        else:
            ap = tmp / f"cvp_app_{tag}.py"
            dr.ServerAppBuilder(str(sp), str(dp)).build(str(ap))
            mod = load_app(str(ap), f"_cvp_{tag}", draw=False)
            doc = Document()
            mod.make_document(doc)
            figs = _figures_of(doc)
    _CACHE[key] = figs
    return figs


def _sc(**opts):
    return plot_for("scatter", opts)


#: Each probe's layers and graph options, as dash.ado writes them.
_K5 = dict(colorvar="rep78", colordiscrete="colordiscrete",
           coloruseplegend="coloruseplegend")
_PLEGEND_PROBES = {
    "K5": ([_sc(**_K5)], None, ""),
    "K6": ([_sc(colorvar="foreign", colordiscrete="colordiscrete",
                coloruseplegend="coloruseplegend")], None, ""),
    "X1": ([_sc(**_K5, colorotherlabel="rest")], None, ""),
    "C28": ([_sc(**_K5, colorkeysrange="colorkeysrange")], None, ""),
    "ST": ([_sc(**_K5)], None, "stcolor"),
}


def _cv_legends(fig):
    return [m for side in ("right", "left", "above", "below", "center")
            for m in getattr(fig, side)
            if isinstance(m, Legend) and m.name == dr._COLORVAR_LEGEND_NAME]


def _label(it):
    return str(getattr(it.label, "value", it.label))


def _hex(c):
    c = str(c or "").strip().lower()
    if c.startswith("#"):
        return c[:7]
    from bokeh.colors import named
    nc = getattr(named, c, None)
    return nc.to_hex().lower() if nc is not None else c


def _near(a, b):
    a, b = _hex(a), _hex(b)
    try:
        return max(abs(int(a[j:j + 2], 16) - int(b[j:j + 2], 16))
                   for j in (1, 3, 5)) <= 1
    except ValueError:
        return a == b


def _swatch_colour(r):
    g = r.glyph
    return getattr(g, "fill_color", None) or getattr(g, "line_color", None)


class TestTheFixture:

    def test_meta(self):
        meta = TRUTH["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted"):
            assert meta.get(k), k
        assert meta["source"] == "scripts/extract_colorvar_plegend_truth.do"

    def test_the_k5_key(self):
        assert PROBES["K5"]["key"]["texts"] == ["5", "4", "3", "2", "1",
                                                "Other"]


class TestThePlegendKey:
    """CV-4: the coloruseplegend key, as twoway draws it."""

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("probe", sorted(_PLEGEND_PROBES))
    def test_probe(self, tmp, probe, mode):
        plots, go, scheme = _PLEGEND_PROBES[probe]
        [f] = _build(tmp, mode, plots, go, scheme=scheme)
        tw = PROBES[probe]["key"]
        [lg] = _cv_legends(f)
        assert lg.visible is not False
        # The texts, top to bottom: highest level first, then Other, in
        # the variable's display format (K6: 1 0, not Foreign Domestic).
        assert [_label(it) for it in lg.items] == tw["texts"]
        # Untitled (K5: no text but the levels right of the plot).
        assert not (lg.title or "").strip(), lg.title
        # The scheme's legend box: twoway's white fill and its frame.
        box = tw["box"]
        # The box's fill: the filled rect drawn round its frame (a few
        # units out), not the graph region behind it.
        fill = next(r["fill"] for r in PROBES[probe]["rects"]
                    if r["fill"] not in (None, "none")
                    and 0 < box["x"] - r["x"] < 10
                    and 0 < box["y"] - r["y"] < 10)
        assert _near(lg.background_fill_color, fill)
        assert (lg.background_fill_alpha or 0) > 0
        assert _near(lg.border_line_color, box["stroke"]), \
            (lg.border_line_color, box["stroke"])
        assert (lg.border_line_alpha or 0) > 0
        # Marker swatches (colorkeysrange too, C28), in twoway's colours.
        want = [c for c in tw["fills"] if c != "none"]
        got = [_swatch_colour(it.renderers[0]) for it in lg.items]
        assert all(type(it.renderers[0].glyph).__name__ == "Scatter"
                   for it in lg.items)
        assert len(got) == len(want) and all(
            _near(g, w) for g, w in zip(got, want)), (got, want)


# ---------------------------------------------------------------------------
# After a filter move (BR-42-04.4): the twins against a fresh build
# ---------------------------------------------------------------------------

import test_mode_parity as tp  # noqa: E402


def _legend_record(models):
    """Every colour Legend's (text, swatch colour) rows among *models*."""
    out = []
    for m in models:
        if isinstance(m, Legend) and m.name == dr._COLORVAR_LEGEND_NAME \
                and m.items:
            out.append([(_label(it), _hex(_swatch_colour(it.renderers[0])))
                        for it in m.items])
    return sorted(out)


_PL = {"colorvar": "rep", "colordiscrete": "colordiscrete",
       "coloruseplegend": "coloruseplegend"}
#: A range move on price keeps rep's levels 4 and 5 of 3, 4 and 5.
_MOVE_CASES = {
    "plegend levels": tp._move_case(
        "plegend levels", tp._MOVES[1], [plot_for("scatter", dict(_PL))]),
    "plegend cuts": tp._move_case(
        "plegend cuts", tp._MOVES[1],
        [plot_for("scatter", dict(_PL, colorcuts="3 4 5"))]),
}


@pytest.mark.parametrize("name", sorted(_MOVE_CASES))
class TestAfterAMove:
    """After a filter move the coloruseplegend key keeps its levels
    highest first, in the variable's format, served (the Python twin) and
    saved (the page's script under node), equal to a fresh build over the
    kept rows."""

    def test_twins_agree(self, name):
        import js_runner
        _name, spec, action, oracle = _MOVE_CASES[name].values
        q = json.loads(json.dumps(spec))
        q["build_options"]["filter"] = ""
        for g in q["graphs"]:
            g["if_expr"] = oracle
        r0, _ = tp._standalone(q)
        want = _legend_record(r0._last_layout_root.references())
        assert want and [t for t, _c in want[0]][:2] == ["5", "4"], want
        before, _ = tp._standalone(spec)
        assert want != _legend_record(
            before._last_layout_root.references())
        doc, _ = tp._served(spec)
        kind, label = action
        w = [x for x in tp._widgets_of(doc) if type(x).__name__ == kind][0]
        tp._fire(w, tp._move_widget_value(w, kind, label))
        assert _legend_record([m for root in doc.roots
                               for m in root.references()]) == want
        r, _ = tp._standalone(spec)
        w, cb = [(w, cb) for w, cb in zip(r.filter_widgets,
                                          r.filter_callbacks)
                 if type(w).__name__ == kind][0]
        session = js_runner.JsSession(r.filter_callbacks)
        session.set(w, tp._move_widget_value(w, kind, label))
        session.run(cb)
        assert _legend_record(r._last_layout_root.references()) == want


# ---------------------------------------------------------------------------
# CV-5: legend()'s size and grid sub-options leave every colour key
# ---------------------------------------------------------------------------

_LFIT = plot_for("lfit", {})
#: probe: (its layers and graph options, the probe it draws its key as).
_LEGEND_PROBES = {
    "M3": (([_sc(**_K5)], {"legend": "off"}), "K5"),
    "M4": (([_sc(**_K5)], {"legend": "rows(1)"}), "K5"),
    "Q3": (([_sc(**_K5), _LFIT], {"legend": "size(huge)"}), "K5"),
}
_CELL_PROBES = {
    "Q1": (([_sc(colorvar="price"), _LFIT], {"legend": "size(huge)"}), "Q0"),
    "P12": (([_sc(colorvar="price"), _LFIT], {"legend": "rows(1)"}), "Q0"),
}


def _plot_legends(fig):
    return [m for m in fig.legend if m.name != dr._COLORVAR_LEGEND_NAME]


def _legend_style(lg):
    return (str(lg.label_text_font_size), lg.orientation, lg.nrows,
            lg.ncols, lg.visible is not False)


def _kv(fig):
    """The figure's colour key cell, as colour_bins.KeyView."""
    import colour_bins
    [kv] = colour_bins.key_views(fig)
    return kv


class TestLegendLeavesTheKey:
    """CV-5: legend(off), legend(rows()) and legend(size()) leave the
    colour key as twoway leaves it (M3, M4, Q3: the coloruseplegend key's
    texts at K5's size and places; Q1, P12: the key cell's at Q0's)."""

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("probe", sorted(_LEGEND_PROBES))
    def test_probe(self, tmp, probe, mode):
        (plots, go), base = _LEGEND_PROBES[probe]
        tw, tw0 = PROBES[probe]["key"], PROBES[base]["key"]
        assert tw["texts"] == tw0["texts"] and tw["sizes"] == tw0["sizes"]
        # Stacked one under another, as without the option (M4: one x).
        assert len({round(x) for x, _y in tw["text_pos"]}) == 1
        [f] = _build(tmp, mode, plots, go)
        [f0] = _build(tmp, mode, [_sc(**_K5)])
        [lg] = _cv_legends(f)
        [lg0] = _cv_legends(f0)
        assert _legend_style(lg) == _legend_style(lg0), \
            (_legend_style(lg), _legend_style(lg0))

    @pytest.mark.parametrize("mode", MODES)
    def test_the_plot_legend_takes_it(self, tmp, mode):
        # Q3: the plot legend's texts at twice the key's size (199.98).
        assert {t["size"] for t in PROBES["Q3"]["texts"]
                if t["text"] == "Fitted values"} == {199.98}
        (plots, go), _b = _LEGEND_PROBES["Q3"]
        [f] = _build(tmp, mode, plots, go)
        [f0] = _build(tmp, mode, plots)
        T = dr.OptionTranslator
        [p] = [m for m in _plot_legends(f) if m.visible is not False]
        [p0] = [m for m in _plot_legends(f0) if m.visible is not False]
        assert T.css_to_pt(p.label_text_font_size) > \
            T.css_to_pt(p0.label_text_font_size)

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("probe", sorted(_CELL_PROBES))
    def test_cell(self, tmp, probe, mode):
        (plots, go), base = _CELL_PROBES[probe]
        tw, tw0 = PROBES[probe]["key"], PROBES[base]["key"]
        assert tw["texts"] == tw0["texts"] and tw["sizes"] == tw0["sizes"]
        [f] = _build(tmp, mode, plots, go)
        [f0] = _build(tmp, mode, plots)
        kv, kv0 = _kv(f), _kv(f0)
        assert kv.major_label_overrides == kv0.major_label_overrides
        assert str(kv.cell._dash_keycell["axis"].major_label_text_font_size) \
            == str(kv0.cell._dash_keycell["axis"].major_label_text_font_size)

    @pytest.mark.parametrize("mode", MODES)
    def test_contourline_levels(self, tmp, mode):
        """contourline's colorlines key is a colour key too: measured
        03nov2026 (sysuse sandstone, ``twoway contourline depth northing
        easting, colorlines``), its texts 8000 7900 .. at 112.56 units in
        one column with and without legend(size(huge)) or
        legend(rows(1))."""
        cl = [plot_for("contourline", {"colorlines": "colorlines"})]
        [f0] = _build(tmp, mode, cl)
        [lg0] = _cv_legends(f0)
        for go in ({"legend": "size(huge)"}, {"legend": "rows(1)"}):
            [f] = _build(tmp, mode, cl, go)
            [lg] = _cv_legends(f)
            assert _legend_style(lg) == _legend_style(lg0), go
