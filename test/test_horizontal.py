"""horizontal drawn as twoway draws it (WP-30 P1.9a, section 49).

twoway draws ``horizontal`` on 24 types as the exact transpose of the
upright layer, axes, default titles and date labels swapped, ``yaxis(2)``
physical (test/fixtures/horizontal_truth.json, written by
scripts/extract_horizontal_truth.do).  dash draws each layer upright and
turns it once (``_dash_transpose_layer`` with ``_DASH_TRANSPOSE``, in both
build loops); every reader of a layer's axis variables goes through
``_dash_role_letter``.  The refusals are dash.ado's (``_dash_hz_check``):
the HZ cases of test/test_option_validation.cscript.
"""

import json
import math
import os
import re
import sys
import warnings

import pandas as pd
import pytest
from bokeh.models import ColumnDataSource, LabelSet
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_join_order as jo  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "horizontal_truth.json")
_ADO = os.path.join(os.path.dirname(_HERE), "dash.ado")
MODES = ("saved", "served")
_SLOTS = ("glyph", "selection_glyph", "nonselection_glyph", "hover_glyph",
          "muted_glyph")
_TURNED = ("area bar spike dropline dot histogram kdensity rarea rbar rspike "
           "rcap rcapsym rline rconnected rscatter pcspike pcarrow pcbarrow "
           "pcscatter pccapsym pci pcarrowi function tsrline").split()
_MLABEL = {"bar", "dropline", "rcapsym", "dot", "rscatter", "rconnected",
           "pcscatter"}
_H = {"horizontal": "horizontal"}


def _truth():
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _build(spec, mode, df=None):
    df = tp._DF if df is None else df
    if mode == "saved":
        return jo._saved_figs(jo._saved(spec, df))
    return jo._served_figs(jo._served(spec, df))


def _opts(t, extra=None):
    o = {"mlabel": "mpg"} if t in _MLABEL else {}
    o.update(extra or {})
    return o


_BUILT = {}


def _pairs(mode):
    """``{type: (upright fig, horizontal fig)}`` from one build per mode."""
    if mode not in _BUILT:
        graphs = []
        for i, t in enumerate(_TURNED):
            graphs.append((f"u{i}", [plot_for(t, _opts(t))]))
            graphs.append((f"h{i}", [plot_for(t, _opts(t, _H))]))
        figs = _build(tp._spec(graphs=graphs), mode)
        _BUILT[mode] = {t: (figs[2 * i], figs[2 * i + 1])
                        for i, t in enumerate(_TURNED)}
    return _BUILT[mode]


def _props(m):
    return {k: v for k, v in m.properties_with_values(
        include_defaults=False).items() if k not in ("id",)}


def _num(v):
    v = v.get("value") if isinstance(v, dict) else getattr(v, "value", v)
    return float(v)


def _norm(v):
    """A property value with a field named as a string or a Field, and a
    number given bare or as a Value, written one way."""
    if isinstance(v, str):
        return {"field": v, "transform": None}
    if hasattr(v, "field") and isinstance(getattr(v, "field"), str):
        t = getattr(v, "transform", None)
        return {"field": v.field,
                "transform": None if t is None
                or "Unspecified" in type(t).__name__ else repr(t)}
    if hasattr(v, "value") and not isinstance(v, dict):
        return {"value": v.value}
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return {"value": float(v)}
    return v


def _spec_eq(a, b):
    if isinstance(a, dict) and isinstance(b, dict) and not (
            {"field", "value"} & (set(a) | set(b))):
        return set(a) == set(b) and all(_spec_eq(a[k], b[k]) for k in a)
    return json.dumps(_norm(a), default=repr, sort_keys=True) == json.dumps(
        _norm(b), default=repr, sort_keys=True)


def _layer_annotations(fig):
    return [a for a in fig.center if type(a).__name__ in dr._DASH_TRANSPOSE]


# ===========================================================================
# Type sets and the role rule
# ===========================================================================

class TestTheTypeSets:

    def test_sets_equal_twoways(self):
        """The two type sets are twoway's measured accept sets, and
        dash.ado's lists are the same."""
        acc = _truth()["accept"]
        h = {t for t, v in acc.items() if v["h"]["rc"] == 0}
        v = {t for t, r in acc.items() if r["v"]["rc"] == 0}
        # WP-31 B1: rpcap and rpspike take both, measured in
        # test/fixtures/rangept_truth.json (probes horizontal.*, vertical.*).
        with open(os.path.join(_HERE, "fixtures", "rangept_truth.json"),
                  encoding="utf-8") as fh:
            rp = json.load(fh)["probes"]
        h |= {t for t in ("rpcap", "rpspike")
              if rp["horizontal." + t]["rc"] == 0}
        v |= {t for t in ("rpcap", "rpspike")
              if rp["vertical." + t]["rc"] == 0}
        # 24 -> 26 and 22 -> 24: WP-31 B1 rpcap and rpspike drawn.
        assert set(dr._DASH_HORIZONTAL_TYPES) == h and len(h) == 26
        assert set(dr._DASH_VERTICAL_TYPES) == v and len(v) == 24
        with open(_ADO, encoding="utf-8") as fh:
            ado = fh.read()
        for name, want in (("_hz_htypes", h), ("_hz_vtypes", v),
                           ("_hz_derived",
                            set(dr._DASH_DERIVED_ORIENT_TYPES))):
            m = re.search(r"local %s\s+(.*?)\n" % name, ado)
            assert m, name
            assert set(m.group(1).replace("///", "").split()) == want, name


class TestTheRoleRule:

    def test_is_horizontal_and_role_letter(self):
        """Own type, recast target, a refusing type, no flag; and the role
        letter each answers."""
        cases = [
            (plot_for("bar", _H), True),
            (plot_for("kdensity", dict(_H, recast="line")), True),
            (plot_for("lfit", dict(_H, recast="bar")), True),
            (plot_for("scatter", _H), False),
            (plot_for("bar", {"vertical": "vertical"}), False),
            (plot_for("bar"), False),
            ("not a plot", False),
        ]
        bad = []
        for p, want in cases:
            got = dr._dash_is_horizontal(p)
            role = (dr._dash_role_letter(p, "x"), dr._dash_role_letter(p, "y"),
                    dr._dash_role_letter(p, "z"))
            if got != want or role != (("y", "x", "z") if want
                                       else ("x", "y", "z")):
                bad.append((p, got, role))
        assert not bad, bad


# ===========================================================================
# The transposition
# ===========================================================================

class TestEveryTurnedTypeIsMapped:

    def test_type(self):
        """Every glyph and annotation class the 24 upright types emit is in
        the property map."""
        bad = []
        for t, (up, _h) in _pairs("saved").items():
            for r in up.renderers:
                for s in _SLOTS:
                    m = getattr(r, s, None)
                    if hasattr(m, "properties_with_values") and \
                            type(m).__name__ not in dr._DASH_TRANSPOSE:
                        bad.append((t, type(m).__name__))
            for a in up.center:
                if type(a).__name__ not in ("Grid", "Legend") and \
                        type(a).__name__ not in dr._DASH_TRANSPOSE:
                    bad.append((t, type(a).__name__))
        assert not bad, bad


@pytest.mark.parametrize("mode", MODES)
class TestHorizontalIsTheTranspose:

    def test_type(self, mode):
        """Each of the 24 types: every renderer's horizontal glyph, in all
        five slots, is the upright one under the map (styles and alpha
        kept, rcap caps turned by pi/2); its annotations' pairs swapped;
        the axis hull of each letter is the upright one of the other; the
        default titles swap."""
        bad = []
        for t, (up, hz) in _pairs(mode).items():
            ur, hr = up.renderers, hz.renderers
            if len(ur) != len(hr):
                bad.append((t, "renderers", len(ur), len(hr)))
                continue
            for a, b in zip(ur, hr):
                for s in _SLOTS:
                    ga, gb = getattr(a, s, None), getattr(b, s, None)
                    if not hasattr(ga, "properties_with_values"):
                        continue
                    cls, pairs = dr._DASH_TRANSPOSE[type(ga).__name__]
                    if type(gb).__name__ != cls:
                        bad.append((t, s, type(gb).__name__))
                        continue
                    pa, pb = _props(ga), _props(gb)
                    for p, q in pairs:
                        if not _spec_eq(pa.pop(p, None), pb.pop(q, None)) or \
                                not _spec_eq(pa.pop(q, None), pb.pop(p, None)):
                            bad.append((t, s, p, q))
                    if "dash_cap" in (a.tags or ()):
                        if not math.isclose(_num(pb.pop("angle", 0.0)),
                                            _num(pa.pop("angle", 0.0))
                                            + math.pi / 2):
                            bad.append((t, s, "cap angle"))
                    if not _spec_eq(pa, pb):
                        bad.append((t, s, "props", sorted(set(pa) ^ set(pb))
                                    or [k for k in pa if not _spec_eq(
                                        pa[k], pb.get(k))]))
            for a, b in zip(_layer_annotations(up), _layer_annotations(hz)):
                for p, q in dr._DASH_TRANSPOSE[type(a).__name__][1]:
                    if not _spec_eq(getattr(a, p), getattr(b, q)):
                        bad.append((t, type(a).__name__, p))
                for k in ("x_offset", "y_offset", "angle", "text_align",
                          "text_baseline"):
                    if hasattr(a, k) and not _spec_eq(getattr(a, k),
                                                      getattr(b, k)):
                        bad.append((t, type(a).__name__, k))
            hu = {h["key"][1]: (h["lo"], h["hi"])
                  for h in getattr(up, "_dash_hull_entries", ())}
            hh = {h["key"][1]: (h["lo"], h["hi"])
                  for h in getattr(hz, "_dash_hull_entries", ())}
            if hu.get("x") != hh.get("y") or hu.get("y") != hh.get("x"):
                bad.append((t, "hull", hu, hh))
            if (up.xaxis[0].axis_label, up.yaxis[0].axis_label) != \
                    (hz.yaxis[0].axis_label, hz.xaxis[0].axis_label):
                bad.append((t, "titles"))
            if any(type(r.glyph).__name__ in ("VBar", "VArea")
                   for r in hz.renderers):
                bad.append((t, "upright glyph left"))
        assert not bad, bad


class TestSwatchesAreSkipped:

    def test_dot_colorvar(self):
        """A colorvar() key's swatches and the key itself stay as drawn."""
        figs = _build(tp._spec(graphs=[
            ("u", [plot_for("dot", {"colorvar": "price",
                                    "colordiscrete": "colordiscrete"})]),
            ("h", [plot_for("dot", {"colorvar": "price",
                                    "colordiscrete": "colordiscrete",
                                    "horizontal": "horizontal"})])]),
            "saved")
        sw = [[_props(r.glyph) for r in f.renderers if dr._dash_is_swatch(r)]
              for f in figs]
        assert sw[0] and _spec_eq(sw[0], sw[1])
        keys = [[type(a).__name__ for a in list(f.right) + list(f.center)
                 if type(a).__name__ in ("Legend", "ColorBar")] for f in figs]
        assert keys[0] == keys[1]
        assert {type(r.glyph).__name__ for r in figs[1].renderers
                if not dr._dash_is_swatch(r)} == {"Scatter"}


class TestAnUnmappedGlyphIsNoted:

    def test_a_fake_class(self):
        """A glyph class the map does not hold is left upright, with one
        note; a mapped one beside it turns."""
        fig = figure()
        src = ColumnDataSource({"x": [1.0, 2.0], "y": [3.0, 4.0]})
        odd = fig.ellipse(x="x", y="y", width=1, height=1, source=src)
        ok = fig.scatter(x="x", y="y", source=src)
        dr._DASH_NOTED.clear()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr._dash_transpose_layer(fig, [odd, ok], [], "bar")
            dr._dash_transpose_layer(fig, [odd], [], "bar")
        msgs = [str(w.message) for w in caught]
        assert msgs == ["(note: horizontal: bar is drawn upright; dash "
                        "cannot turn a Ellipse)"]
        assert _norm(odd.glyph.x)["field"] == "x"
        assert _norm(ok.glyph.x)["field"] == "y"


# ===========================================================================
# Axes against twoway
# ===========================================================================

_TDF = pd.DataFrame({
    "Xvar": [1.0, 2.0, 3.0, 4.0, 5.0],
    "Yvar": [10.0, 30.0, 20.0, 50.0, 40.0],
    "Lovar": [5.0, 25.0, 15.0, 45.0, 35.0],
    "Hivar": [15.0, 35.0, 25.0, 55.0, 45.0],
    "Day": [21922.0 + 25 * i for i in range(5)],
    "Tvar": [1.0, 2.0, 3.0, 4.0, 5.0],
})


def _tplot(t, opts=None, y="Yvar", x="Xvar"):
    o = dict(opts or {})
    if t in ("histogram", "kdensity"):
        return {"type": t, "var": y, "options": o}
    if t in ("rarea", "rbar", "rspike", "rcap", "rcapsym", "rline",
             "rconnected", "rscatter"):
        return {"type": t, "yvar1": "Lovar", "yvar2": "Hivar", "xvar": x,
                "options": o}
    if t == "tsrline":
        return {"type": t, "yvar1": "Lovar", "yvar2": "Hivar",
                "xvar": "Tvar", "options": o}
    if t in dr._DASH_RANGEPT_TYPES:
        # WP-31 B1: the range and its marker at y3.
        return {"type": t, "yvar1": "Lovar", "yvar2": "Hivar", "yvar": y,
                "xvar": x, "options": o}
    if t in ("pcspike", "pccapsym", "pcarrow", "pcbarrow", "pcscatter"):
        return {"type": t, "y1var": "Lovar", "x1var": x, "y2var": "Hivar",
                "x2var": x, "options": o}
    if t in ("pci", "pcarrowi"):
        return {"type": t, "values": [[1.0, 1.0, 2.0, 2.0]], "options": o}
    if t == "function":
        return {"type": t, "expr": "x^2", "options": dict(o, range="0 2")}
    return {"type": t, "yvar": y, "xvar": x, "options": o}


#: The fixture's draw rows as dash plots.
_DRAW = dict({t: [_tplot(t, _H)] for t in _TURNED}, **{
    "T-sc-barh": [_tplot("scatter"), _tplot("bar", _H)],
    "T-sc-barh-sc": [_tplot("scatter"), _tplot("bar", _H),
                     _tplot("scatter")],
    "T-barh-barh": [_tplot("bar", _H), _tplot("bar", _H)],
    "T-rcaph-sc": [_tplot("rcap", _H), _tplot("scatter", y="Xvar",
                                              x="Yvar")],
    "HZ-25": [_tplot("bar", _H, x="Day")],
    "HZ-26": [_tplot("scatter", x="Day"), _tplot("bar", _H, x="Day")],
    "HZ-27": [_tplot("bar", _H, x="Day"), _tplot("scatter", x="Day")],
    "HZ-28": [_tplot("scatter"), _tplot("bar", dict(_H, yaxis="2"))],
    "hist-d": [_tplot("histogram", _H, y="Day")],
})
#: Read apart: twoway writes HZ-28's mixed x title "Xvar..." (a two-label
#: axis), which dash leaves untitled by S19's rule; its y and y2 titles are
#: compared.  tsrline's x is its time variable here.
_NO_XTITLE = {"HZ-28"}
#: A date and a number share each axis: a numeric axis labelled in the
#: first layer's format (S35's mixed axis), read by test_mixed_order.
_MIXED = {"HZ-26", "HZ-27"}
_DRAWN = {}


def _drawn(mode):
    if mode not in _DRAWN:
        ids = list(_DRAW)
        spec = tp._spec(graphs=[(f"d{i}", _DRAW[k]) for i, k in
                                enumerate(ids)],
                        build_options={"formats": {"Day": "%td"}})
        _DRAWN[mode] = dict(zip(ids, _build(spec, mode, _TDF)))
    return _DRAWN[mode]


def _is_date_label(s):
    return bool(re.fullmatch(r"\d\d[a-z]{3}\d{4}", s))


@pytest.mark.parametrize("mode", MODES)
class TestTheAxesFollowTheLayer:

    def test_titles_and_date_axes(self, mode):
        """Every draw row: the default x, y and y2 titles are twoway's, and
        the axis twoway labels with dates is dash's date axis."""
        truth = _truth()["draw"]
        figs = _drawn(mode)
        bad = []
        for k, fig in figs.items():
            want = truth[k]
            y2 = [ax for ax in fig.right if getattr(ax, "y_range_name",
                                                    "default") == "y2"]
            got = {"xtitle": fig.xaxis[0].axis_label or "",
                   "ytitle": fig.yaxis[0].axis_label or "",
                   "y2title": (y2[0].axis_label or "") if y2 else ""}
            for key in ("xtitle", "ytitle", "y2title"):
                if key == "xtitle" and k in _NO_XTITLE:
                    continue
                # twoway's kdensity title names the variable, y there.
                w = want[key].replace("kdensity y", "kdensity Yvar")
                if got[key] != w:
                    bad.append((k, key, got[key], want[key]))
            kinds = getattr(fig, "_dash_date_kinds", (None, None))
            for i, ax in enumerate(("x" if k not in _MIXED else (),
                                    "y" if k not in _MIXED else ())):
                if not ax:
                    continue
                dated = any(_is_date_label(s) for s in want[ax + "labels"])
                if dated != bool(kinds[i]):
                    bad.append((k, ax, "date kind", kinds[i]))
        assert not bad, bad

    def test_mixed_order(self, mode):
        """E3's mixed orders: the axis whose first layer draws the date
        is labelled in its format, the other in numbers."""
        truth = _truth()["draw"]
        bad = []
        for k in sorted(_MIXED):
            for ax in ("x", "y"):
                fmt = dr._dash_axis_unit_format(_DRAW[k], ax, {"Day": "td"},
                                                {"Day": "%td"})
                dated = any(_is_date_label(s)
                            for s in truth[k][ax + "labels"])
                if bool(fmt) != dated:
                    bad.append((k, ax, fmt))
                kinds = getattr(_drawn(mode)[k], "_dash_date_kinds",
                                (None, None))
                if any(kinds):
                    bad.append((k, "kinds", kinds))
        assert not bad, bad

    def test_bar_on_y2(self, mode):
        """``(scatter y x) (bar y x, horizontal yaxis(2))``: the bar is on
        y2, whose range spans the bar's x values."""
        fig = _drawn(mode)["HZ-28"]
        bars = [r for r in fig.renderers
                if type(r.glyph).__name__ == "HBar"]
        assert bars and all(r.y_range_name == "y2" for r in bars)
        rng = fig.extra_y_ranges["y2"]
        assert rng.start < 1.0 and rng.end > 5.0 and rng.end < 10.0


def test_tick_formats_follow_the_layer():
    """A ``%9.0fc`` y on a horizontal bar formats the x axis."""
    fmts = dr._dash_axis_tick_formats(
        [plot_for("bar", _H)], {"mpg": "%9.0fc", "weight": "%8.2f"})
    assert fmts["x"] == ("%9.0fc", False)
    assert fmts["y"] == ("%8.2f", False)


class TestTheHullSeesTransposedGlyphs:

    def test_the_saved_plan_carries_bar_heights(self):
        """S21's saved axis plan reads a turned bar on y (centre and
        height) and its default base on x."""
        r = jo._saved(tp._spec(plots=[plot_for("bar", _H)]), tp._DF)
        fig = jo._saved_figs(r)[0]
        plan = dr._dash_axis_plan({"g1": fig}, {})
        text = plan[0]
        hb = [g for g in fig.renderers if type(g.glyph).__name__ == "HBar"]
        assert hb
        bs = dr._dash_base_spec(hb[0])
        assert bs and bs["letter"] == "x" and bs["prop"] == "left"
        bars = [b for g in json.loads(text) for pnl in g["panels"]
                for ax in pnl["axes"] if ax["letter"] == "y"
                for b in ax.get("bars", ())]
        assert bars and all("wf" in b or "wv" in b for b in bars)


# ===========================================================================
# The upright guard
# ===========================================================================

class TestUprightIsUntouched:

    def test_every_type(self, monkeypatch):
        """Guard: without the flag, every type's normalised saved page is
        the one built with ``vertical`` and the one built while the
        transposition raises (it never runs)."""
        from test_varlist_expansion import normalise_bokeh_html
        types = sorted(dr._dash_plot_type_names())

        def page(extra):
            spec = tp._spec(graphs=[(f"g{i}", [plot_for(t, dict(extra))])
                                    for i, t in enumerate(types)])
            return normalise_bokeh_html(jo._saved(spec, tp._DF,
                                                  page=True)[2])
        plain = page({})
        vert = page({"vertical": "vertical"})

        def _boom(*_a, **_k):
            raise AssertionError("transposed an upright layer")
        monkeypatch.setattr(dr, "_dash_transpose_layer", _boom,
                            raising=False)
        patched = page({})
        # 40 -> 42: WP-31 B1 rpcap and rpspike drawn.
        assert len(types) == 42
        assert plain == patched
        assert plain == vert
