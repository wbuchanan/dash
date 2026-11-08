"""The region remainder (WP-31 D11, section 37): graphregion(margin()),
the regions' intensity() and shadestyle(), the graph region's inner fill
words, marginonly, the schemes' ``shadestyle plotregion none`` and the
margin style names twoway refuses, in both modes.

The defect (GAPS3 D11): dash named graphregion(margin()), intensity(),
shadestyle(), ifcolor()/icolor()/iintensity()/ishadestyle() and
marginonly as not drawn; parsed ``L+10`` as zeros; drew
``margin(allsides-ms)`` from its style file where twoway fails r(7); and
filled the plot region of s1color and its family white where twoway
leaves it unfilled.  The truth is test/fixtures/region_remainder_truth.json
(scripts/extract_region_remainder_truth.do): every rect of each twoway
SVG, in document order (canvas, graph region fill and outline, the inner
box when drawn, plot region fill and outline).
"""

import json
import os
import re
import sys
import warnings

import pytest
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402
from js_runner import requires_node  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "region_remainder_truth.json")
_ROOT = os.path.join(_HERE, "..")
_MODES = ("saved", "served")
#: SVG units per 1% of min(W, H) at twoway's 5.5 x 4 graph (2880 / 100).
_UNIT = 28.8


def _truth():
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


_T = _truth()
_P = _T["probes"]


def _roles(rec):
    """``(graph fill, plot fill)`` twoway paints: the canvas colour shows
    where the graph region is unfilled, the graph region's (or the inner
    box's) where the plot region is."""
    rs = rec["rects"]
    canvas = rs[0]["fill"]
    full = [r for r in rs[1:] if r["x"] < 1 and r["fill"] not in (None, "none")]
    graph = full[0]["fill"] if full else canvas
    inner = [r for r in rs[1:] if 1 <= r["x"] < 200
             and r["fill"] not in (None, "none")]
    under = inner[0]["fill"] if inner else graph
    plot = [r for r in rs[1:] if r["x"] >= 200
            and r["fill"] not in (None, "none")]
    return graph, (plot[0]["fill"] if plot else under), bool(plot)


def _build(mode, cases, scheme=None):
    """{case: figure} for *cases* ({case: graph options}), one graph per
    case in one build, matched by a title naming the case."""
    graphs = []
    names = {}
    for i, (case, go) in enumerate(cases.items()):
        g = dict(go)
        g["title"] = "C%d" % i
        if scheme:
            g.setdefault("scheme", scheme)
        names["C%d" % i] = case
        graphs.append(("g%d" % i, [plot_for("scatter")], g))
    spec = tp._spec(graphs=graphs)
    if mode == "saved":
        r, caught = tp._standalone(spec)
        roots = [r._last_layout_root]
    else:
        doc, caught = tp._served(spec)
        roots = doc.roots
    out = {}
    for root in roots:
        for f in root.select({"type": figure}):
            t = f.title.text if f.title is not None else ""
            if t in names:
                out[names[t]] = f
    return out, caught


from conftest import group_by_params  # noqa: E402

#: The classes read one build per (page, mode) (``_cached``): with every
#: test of a mode on one worker each page is built once.
xdist_group_of = group_by_params("region_remainder", "mode")
_CACHE = {}


def _msg(w):
    return str(getattr(w, "message", w))


def _cached(key, mode, cases):
    k = (key, mode)
    if k not in _CACHE:
        _CACHE[k] = _build(mode, cases)
    return _CACHE[k]


def _go(cmd):
    """The graph options of a probe's ``twoway scatter mpg weight, ...``
    command, as dash.ado hands them to the renderer: region options only,
    plus the scheme."""
    opts = cmd.split(",", 1)[1] if "," in cmd else ""
    out = {}
    for name in ("graphregion", "plotregion"):
        parts = []
        for m in re.finditer(name + r"\(", opts):
            depth, i = 1, m.end()
            while i < len(opts) and depth:
                depth += {"(": 1, ")": -1}.get(opts[i], 0)
                i += 1
            parts.append(opts[m.end():i - 1])
        if parts:
            out[name] = " ".join(parts)
    for name in ("xsize", "ysize"):
        m = re.search(name + r"\(([^)]*)\)", opts)
        if m:
            out[name] = m.group(1)
    return out


def _cases(prefix):
    return {k: dict(_go(v["cmd"]), scheme=v["scheme"])
            for k, v in _P.items() if k.startswith(prefix)}


# ---------------------------------------------------------------------------
# The fixture
# ---------------------------------------------------------------------------

class TestTheFixture:
    def test_meta(self):
        assert sorted(_T["_meta"]) == ["born_date", "dash_commit",
                                       "extracted", "source",
                                       "stata_version", "units"]
        assert _T["_meta"]["source"] == \
            "scripts/extract_region_remainder_truth.do"

    def test_keys(self):
        for pre in ("gmargin.", "refusals.", "intensity.", "shade.",
                    "inner.", "s1."):
            assert any(k.startswith(pre) for k in _P), pre
        assert _P["gmargin.stub"]["stub_margin_graph"] == "medium"
        assert _P["refusals.allsides-ms"]["rc"] == 7


# ---------------------------------------------------------------------------
# graphregion(margin())
# ---------------------------------------------------------------------------

_GM = {k: v for k, v in _cases("gmargin.").items() if k != "gmargin.stub"}
_SIDES = (("left", "min_border_left"), ("right", "min_border_right"),
          ("bottom", "min_border_bottom"), ("top", "min_border_top"))


def _want_gaps(case):
    """twoway's gap change on each side, in % of min(W, H)."""
    g0 = _P["gmargin.stub"]["gaps"]
    g = _P[case]["gaps"]
    return {s: (g[s] - g0[s]) / _UNIT for s, _ in _SIDES}


class TestGraphMargin:
    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("case", sorted(_GM))
    def test_form(self, mode, case):
        """Each side grows by twoway's gap change at the figure's size,
        within 1 px; an untouched side keeps None."""
        figs, _ = _cached("gm", mode, _GM)
        f = figs[case]
        # Flipped (WP-45 VF-4): min(W, H) was the stretched figure's
        # Bokeh default 600 x 600; the figure was held in a 160-560 px band
        # at 2.88 pt a unit, and twoway draws its graph's shape (VF-4,
        # DECISIONS A-1): the graph's box, its xsize()/ysize() or the
        # scheme's graphsize at 96 px an inch.
        short = min(f._dash_nominal_px)
        bad = []
        for side, attr in _SIDES:
            d = _want_gaps(case)[side]
            got = getattr(f, attr)
            if abs(d) < 0.05:
                # Unchanged in twoway (10-pt is 3.47% to medium's 3.5%):
                # None, or the inherited border within 1 px.
                if got is not None and abs(got - f.min_border) > 1.0:
                    bad.append((side, got, None))
                continue
            want = max(0.0, f.min_border + d / 100.0 * short)
            if got is None or abs(got - want) > 1.0:
                bad.append((side, got, round(want, 2)))
        assert not bad, bad

    def test_adds_not_assigns(self):
        f = figure(width=400, height=300)
        f.min_border_left = 20
        dr._dash_graph_margin(f, dr.SchemeParser("s2color"),
                              {"graphregion": "margin(l+5)"})
        # Flipped (WP-45 VF-4): 5% of the built 300 px; the share is of the
        # graph's box, s2color's 5.5 x 4 in at 96 px (384 px short side).
        assert f.min_border_left == 20 + round(0.05 * 384)
        assert (f.min_border_right, f.min_border_top,
                f.min_border_bottom) == (None, None, None)

    @requires_node
    def test_a_resize_redraws_the_margin(self):
        """D39 D-37.a: twoway's margin is a share of the graph's smaller
        side whatever its size, so the borders follow a resize of the page:
        the figure carries its one size follow on its outer size, whose
        "sides" part sets each changed side to its border before the
        margin plus the change times min(W, H).

        Flipped (WP-45 VF-4): the follow was a CustomJS of the margin's
        own with ``sides`` in its args; it is the figure's one guarded
        follow (``_dash_graph_follow``, args ``fig`` and ``item``), which
        43-01's per-figure dispatcher will take over as a kind."""
        f = figure(width=400, height=300)
        f.min_border_left = 20
        dr._dash_graph_margin(f, dr.SchemeParser("s2color"),
                              {"graphregion": "margin(l+5 t+10)"})
        cbs = [cb for k in ("outer_width", "outer_height")
               for cb in f.js_property_callbacks.get("change:" + k, [])]
        assert len(cbs) == 2 and cbs[0] is cbs[1]
        cb = cbs[0]
        assert cb.code == dr._DASH_GRAPH_MARGIN_JS
        assert cb.args["item"] is f._dash_gm_item
        from js_runner import run_js
        src = """
const fig = {outer_width: 1000, outer_height: 500, min_border_left: %d,
             min_border_right: null, min_border_top: %d,
             min_border_bottom: null, min_border: 5};
const item = %s;
(function (fig, item) { %s })(fig, item);
console.log(JSON.stringify(fig));
""" % (f.min_border_left, f.min_border_top, json.dumps(cb.args["item"]),
            cb.code)
        got = run_js(src)
        # At 1000 x 500: left 20 + 25, top 5 (min_border) + 50.
        assert got["min_border_left"] == 45
        assert got["min_border_top"] == 55
        assert got["min_border_right"] is None

    def test_served_copy(self):
        with open(os.path.join(_ROOT, "dash_render.py"),
                  encoding="utf-8") as fh:
            src = fh.read()
        assert src.count('"_dash_graph_margin",') == 1
        assert src.count('"_DASH_GRAPH_MARGIN_JS",') == 1
        assert re.search(r'"_dash_plot_margin",\s*"_dash_graph_margin",',
                         src)

    @pytest.mark.parametrize("mode", _MODES)
    def test_no_margin_leaves_borders_none(self, mode):
        figs, _ = _cached("none", mode, {
            "plain": {}, "fill": {"graphregion": "fcolor(red)"},
            "pmargin": {"plotregion": "margin(large)"}})
        for case, f in figs.items():
            assert (f.min_border_left, f.min_border_right,
                    f.min_border_bottom, f.min_border_top) == \
                (None, None, None, None), case

    @pytest.mark.parametrize("mode", _MODES)
    def test_one_side_leaves_the_others_none(self, mode):
        figs, _ = _cached("gm", mode, _GM)
        f = figs["gmargin.l+5"]
        assert f.min_border_left is not None
        assert (f.min_border_right, f.min_border_bottom,
                f.min_border_top) == (None, None, None)

    def test_l_plus_10_as_twoway(self):
        """``L+10``: twoway reads ``L`` as a gsize it does not know
        (medium, 3.8194) for the left and adds 10 to the right."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            dr._dash_reset_notes()
            sides, noted = dr._dash_margin_sides(
                "L+10", [3.5] * 4, dr.SchemeParser("s2color"), 4.0)
        want = [3.5 + _want_gaps("gmargin.L+10")[s] for s, _ in _SIDES]
        assert all(abs(a - b) < 0.02 for a, b in zip(sides, want)), \
            (sides, want)
        assert noted is None
        assert any("named style L not found in class gsize" in str(x.message)
                   for x in w)


# ---------------------------------------------------------------------------
# intensity()
# ---------------------------------------------------------------------------

_IN = _cases("intensity.")


class TestIntensity:
    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("case", sorted(_IN))
    def test_each(self, mode, case):
        figs, _ = _cached("in", mode, _IN)
        f = figs[case]
        graph, plot, _ = _roles(_P[case])
        assert (f.border_fill_color, f.background_fill_color) == \
            (graph, plot)

    def test_same_mixer_as_fintensity(self):
        spec = tp._spec(graphs=[
            ("r", [plot_for("scatter")],
             {"plotregion": "fcolor(navy) intensity(inten50)"}),
            ("b", [plot_for("bar", {"fcolor": "navy",
                                    "fintensity": "inten50"})], {})])
        r, _ = tp._standalone(spec)
        figs = list(r._last_layout_root.select({"type": figure}))
        region = {f.background_fill_color for f in figs}
        bars = {getattr(gr.glyph, "fill_color", None)
                for f in figs for gr in f.renderers
                if hasattr(gr, "glyph")}
        assert "#8da3b7" in region and "#8da3b7" in bars


# ---------------------------------------------------------------------------
# shadestyle() and the schemes' unfilled plot region
# ---------------------------------------------------------------------------

_SH = _cases("shade.")
_S1 = _cases("s1.")


class TestShade:
    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("case", sorted(_SH))
    def test_words(self, mode, case):
        figs, _ = _cached("sh", mode, _SH)
        f = figs[case]
        graph, plot, _ = _roles(_P[case])
        assert (f.border_fill_color, f.background_fill_color) == \
            (graph, plot)

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("region", ("plot", "graph"))
    def test_none(self, mode, region):
        """shadestyle(none) leaves the region unfilled: what lies under it
        shows."""
        figs, _ = _cached("sh", mode, _SH)
        f = figs["shade.none." + region]
        if region == "plot":
            assert f.background_fill_color == f.border_fill_color
        else:
            assert f.border_fill_color == _P["shade.none.graph"]["rects"][0]["fill"]

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("case", sorted(_S1))
    def test_s1color_unfilled(self, mode, case):
        figs, _ = _cached("s1", mode, _S1)
        f = figs[case]
        graph, plot, filled = _roles(_P[case])
        assert (f.border_fill_color, f.background_fill_color) == \
            (graph, plot)
        if not filled:
            assert f.background_fill_color == f.border_fill_color

    @pytest.mark.parametrize("mode", _MODES)
    def test_red_graph_shows_through(self, mode):
        figs, _ = _cached("s1", mode, _S1)
        assert figs["s1.red_graph"].background_fill_color == "#ff0000"

    @pytest.mark.parametrize("mode", _MODES)
    def test_override(self, mode):
        figs, _ = _cached("s1", mode, _S1)
        assert figs["s1.override"].background_fill_color == "#ffff00"

    @pytest.mark.parametrize("scheme", ("s1color", "s1mono", "s1rcolor",
                                        "s1manual", "stmono1", "s2color"))
    def test_stub_read(self, scheme):
        assert dr.SchemeParser(scheme).plotregion_shade == \
            _P["s1." + scheme]["stub_shadestyle_plotregion"]

    def test_graph_margin_stub_read(self):
        assert dr.SchemeParser("s2color").graph_margin_sides == [3.5] * 4


# ---------------------------------------------------------------------------
# The graph region's inner box and marginonly
# ---------------------------------------------------------------------------

_INNER = _cases("inner.")


class TestInner:
    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("case", sorted(_INNER))
    def test_fill(self, mode, case):
        """The inner fill words fill the border (D-37.b: Bokeh paints the
        margin and the inner box as one); marginonly drops a copy's box
        edits, as _fr_area_parse_and_log.ado does."""
        figs, _ = _cached("inner", mode, _INNER)
        f = figs[case]
        rs = _P[case]["rects"]
        inner = [r for r in rs[1:] if 1 <= r["x"] < 200
                 and r["fill"] not in (None, "none")]
        graph, plot, _ = _roles(_P[case])
        want_border = inner[0]["fill"] if inner else graph
        assert f.border_fill_color == want_border
        if not inner:
            assert f.background_fill_color == plot

    @pytest.mark.parametrize("mode", _MODES)
    def test_named(self, mode):
        """Flipped (WP-45 ST-21): the inner outline words and lalign() were
        named as not drawn; that was wrong because twoway draws them and
        dash now does (figure_geometry_truth.json I_ilc, I_gla): graphregion()
        names none of these words."""
        spec = tp._spec(graphs=[("g", [plot_for("scatter")], {
            "graphregion": "ifcolor(red) ilcolor(blue) ilwidth(thick) "
                           "istyle(none) lalign(inside) intensity(50) "
                           "shadestyle(none) marginonly margin(l+1)"})])
        if mode == "saved":
            _, caught = tp._standalone(spec)
        else:
            _, caught = tp._served(spec)
        msgs = [_msg(w) for w in caught if "graphregion" in _msg(w)]
        assert msgs == [], msgs


# ---------------------------------------------------------------------------
# marginonly and the plot region's inner box
# ---------------------------------------------------------------------------

_PMO = {k: v for k, v in _cases("inner.p_").items()
        if k != "inner.p_marginonly_copy"}


def _tw_inner(rec):
    """twoway drew the plot region's inner box: a rect inside the plot
    region's fill (x beyond 400 units)."""
    return any(r["x"] > 400 for r in rec["rects"])


class TestPlotMarginonly:
    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("case", sorted(_PMO))
    def test_inner_box(self, mode, case):
        """plotregion(marginonly) drops the copy's inner-box edits too
        (measured: ifcolor(red) marginonly draws no inner box)."""
        figs, _ = _cached("pmo", mode, _PMO)
        f = figs[case]
        boxes = [r for r in f.renderers + f.center
                 if "dash_inner_box" in (getattr(r, "tags", None) or [])]
        assert bool(boxes) == _tw_inner(_P[case]), case


# ---------------------------------------------------------------------------
# The refused margin names
# ---------------------------------------------------------------------------

class TestRefusals:
    def test_every_refused_text_is_checked(self):
        """Every margin text twoway refuses (refusals.*, terms.*, gterms.*)
        is put to dash in test_option_validation.cscript U37-04, where
        dash's rc and line are compared with twoway's in the same run."""
        with open(os.path.join(_HERE, "test_option_validation.cscript"),
                  encoding="utf-8") as fh:
            src = fh.read()
        m = re.search(r"// U37-04.*?_u05_judge U37-04", src, re.S)
        assert m
        texts = {re.search(r"margin\((.*)\)\)$", v["cmd"]).group(1)
                 for k, v in _P.items()
                 if k.startswith(("refusals.", "terms.", "gterms."))
                 and v["rc"]}
        missing = sorted(t for t in texts if '"%s|' % t not in m.group(0))
        assert texts and not missing, missing

    def test_the_rule_is_margin_class(self):
        """dash_parse.mata refuses by margin.class's rule, not by a table
        of names."""
        with open(os.path.join(_ROOT, "dash_parse.mata"),
                  encoding="utf-8") as fh:
            src = fh.read()
        assert "real scalar _dash_margin_term_rc(" in src
        assert "_dash_margin_refused_table" not in src



# ---------------------------------------------------------------------------
# Silence
# ---------------------------------------------------------------------------

_SILENT = {"gmargin": {"graphregion": "margin(large)"},
           "pintensity": {"plotregion": "intensity(inten50)"},
           "gintensity": {"graphregion": "intensity(inten80)"},
           "pshade": {"plotregion": "shadestyle(none)"},
           "ifill": {"graphregion": "ifcolor(red) iintensity(50) "
                                    "ishadestyle(none)"},
           "marginonly": {"graphregion": "fcolor(red) marginonly"}}


class TestSilentWhenHonoured:
    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("sub", sorted(_SILENT))
    def test_no_warning(self, mode, sub):
        spec = tp._spec(graphs=[("g", [plot_for("scatter")], _SILENT[sub])])
        if mode == "saved":
            _, caught = tp._standalone(spec)
        else:
            _, caught = tp._served(spec)
        msgs = [_msg(w) for w in caught if "region" in _msg(w)]
        assert not msgs, msgs
