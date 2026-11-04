"""
test_ci_plot_index.py -- a ci fit counts as two plots in the p# cycle.

The defect (BUGS.md, S3): "After a ci plot, the next layer takes the next
layer's colour, where Stata counts the ci band as a plot".  dash gave each
layer its layer index as its plot index, so `lfitci || lfitci || lfit' drew
its lines in p1, p2 and p3, where Stata draws them in p1, p3 and p5.

Stata's truth, measured 24sep2026 with StataNow 19.5 and kept in
test/fixtures/ci_plot_index_truth.json: a ci fit (lfitci, qfitci, lpolyci,
fpfitci) draws two plots, its band (pstyle ci) and its line;
twoway_lfitci_parse.class gives the line seriesid(`seriesid'-1), and a
seriesid of 0 draws as p1.  A layer that is plot n draws in p((n-1) mod 15
+ 1); a ci layer whose line is plot n in that less one, p1 where it is 0.
Everything keyed on the plot index follows: colour, line width, pattern,
symbol, marker size.

WP-34 PIC-3 (BUGS.md "A ci type with nofit still uses two plot numbers, so
every later layer takes the wrong p# style"): under nofit a ci fit draws
its band alone, one plot (twoway_lfitci_parse.class sets .n = 1 without
.fit), for the p# cycle and the legend's numbers.  The fixture's
'<type>nf' layers are that type with nofit ('lfitcinfr' adds
ciplot(rline)), measured 24oct2026.
"""
import itertools
import json
import os
import sys
import time
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402
from dash_render import SchemeParser  # noqa: E402
from conftest import make_data_json, load_app  # noqa: E402
from conftest import drawn_renderers  # noqa: E402

with open(os.path.join(_HERE, "fixtures", "ci_plot_index_truth.json"),
          encoding="utf-8") as _fh:
    _T = json.load(_fh)

#: The custom scheme the z1 cases were measured under.
_Z1 = ("#include s2color\nlinewidth p1 vthick\nlinewidth p15 vvthick\n"
       "linewidth p14 thick\n")


def _expand(layers):
    """The fixture's layer list with 'N*scatter' spelled out, and the
    number of leading layers it stood for."""
    out, lead = [], 0
    for t in layers:
        if "*" in t:
            n, typ = t.split("*")
            out += [typ] * int(n)
            lead = int(n)
        else:
            out.append(t)
    return out, lead


def _want(case):
    types, lead = _expand(case["layers"])
    return types, [i % 15 for i in range(lead)] + [p - 1 for p in case["pstyle"]]


#: The fixture's nofit layer names (WP-34 PIC-3): the type and the options
#: the extract drew it with.
_NOFIT = {"lfitcinf": ("lfitci", {"nofit": "nofit"}),
          "qfitcinf": ("qfitci", {"nofit": "nofit"}),
          "lpolycinf": ("lpolyci", {"nofit": "nofit"}),
          "fpfitcinf": ("fpfitci", {"nofit": "nofit"}),
          "lfitcinfr": ("lfitci", {"nofit": "nofit", "ciplot": "rline"})}


def _bare(t):
    """A plot dict of the fixture's layer name *t* with no variables."""
    if t in _NOFIT:
        typ, opts = _NOFIT[t]
        return {"type": typ, "options": dict(opts)}
    return {"type": t}


_IDS = [c["id"] for c in _T["cases"]]


class TestTheIndexAgainstStata:
    @pytest.mark.parametrize("case", _T["cases"], ids=_IDS)
    def test_each_measured_sequence(self, case):
        types, want = _want(case)
        plots = [_bare(t) for t in types]
        assert dr._dash_plot_style_indices(plots) == want

    def test_the_nofit_cases_were_measured(self):
        """The extract measured the nofit sequences and twoway numbered
        the nofit layer as one plot: in lfitcinf scatter lfit the scatter
        is p2 and the lfit p3 (WP-34 PIC-3)."""
        got = {c["id"]: c["pstyle"] for c in _T["cases"] if "nf" in c["id"]}
        assert len(got) == 8
        assert got["lfitcinf_scatter_lfit"] == [1, 2, 3]
        assert got["lfitcinf_lfitci_lfit"] == [1, 2, 4]

    def test_the_fixture_colours_are_s2colors(self):
        sp = SchemeParser("s2color")
        assert [sp.default_color(i, "scatter").lstrip("#").lower()
                for i in range(15)] == _T["p_colors"]["s2color"]

    def test_every_ci_type_takes_two_plots(self):
        for t in ("lfitci", "qfitci", "lpolyci", "fpfitci"):
            assert dr._dash_plot_style_indices(
                [{"type": t}, {"type": t}, {"type": "scatter"}]) == [0, 2, 4]
            # The type as a spec may spell it.
            assert dr._dash_plot_style_indices(
                [{"type": t.upper()}, {"type": "line"}]) == [0, 2]

    def test_no_ci_is_the_layer_index(self):
        plots = [{"type": "scatter"}] * 40
        assert dr._dash_plot_style_indices(plots) == [
            i % 15 for i in range(40)]


class TestTheNofitCount:
    def test_the_count(self):
        """_dash_ci_plot_count (WP-34 PIC-3): 2 for a ci fit, 1 under
        nofit, 1 for any other layer or anything that is no dict."""
        c = dr._dash_ci_plot_count
        for t in ("lfitci", "qfitci", "lpolyci", "fpfitci", " LFITCI "):
            assert c({"type": t}) == 2
            assert c({"type": t, "options": {}}) == 2
            assert c({"type": t, "options": {"nofit": ""}}) == 2
            assert c({"type": t, "options": {"nofit": "  "}}) == 2
            assert c({"type": t, "options": {"nofit": None}}) == 2
            assert c({"type": t, "options": {"nofit": "nofit"}}) == 1
            assert c({"type": t, "options": {"nofit": "nofit",
                                             "ciplot": "rline"}}) == 1
            # options that are no dict are no nofit.
            assert c({"type": t, "options": "nofit"}) == 2
        for t in ("scatter", "lfit", "line", "", None, 5, ["lfitci"]):
            assert c({"type": t}) == 1
            assert c({"type": t, "options": {"nofit": "nofit"}}) == 1
        for bad in (None, 7, "lfitci", ["lfitci"], ("lfitci",)):
            assert c(bad) == 1

    def test_the_counters_agree(self):
        """The p# pass, the legend's numbers and _dash_apply_legend's map
        count a nofit layer as one plot: lfitci nofit then scatter is p1,
        p2 (WP-34 PIC-3)."""
        from bokeh.models import (ColumnDataSource, GlyphRenderer, Line,
                                  Scatter, VArea)
        plots = [{"type": "lfitci", "yvar": "mpg", "xvar": "weight",
                  "options": {"nofit": "nofit"}},
                 {"type": "scatter", "yvar": "mpg", "xvar": "weight",
                  "options": {}},
                 {"type": "lfit", "yvar": "mpg", "xvar": "weight",
                  "options": {}}]
        assert dr._dash_plot_style_indices(plots) == [0, 1, 2]
        src = ColumnDataSource({"x": [1, 2], "y": [1, 2], "y2": [2, 3]})

        def gr(g):
            return GlyphRenderer(glyph=g, data_source=src)
        band, s1, fit = (gr(VArea(x="x", y1="y", y2="y2")),
                         gr(Scatter(x="x", y="y")), gr(Line(x="x", y="y")))
        got = dr._dash_legend_keys(
            [(plots[0], [band]), (plots[1], [s1]), (plots[2], [fit])],
            {}, 95)
        assert [(n, t) for n, t, _ in got] == [
            (1, "95% CI"), (2, "mpg"), (3, "Fitted values")]


class TestAdversarial:
    @pytest.mark.parametrize("bad", [None, 5, "", "<script>", "lfitci;x",
                                     ["lfitci"], {"t": 1}, float("nan")])
    def test_a_hostile_type_is_one_plot(self, bad):
        """Injection: a type that is not a string, or no type dash knows,
        counts as one plot and raises nothing."""
        got = dr._dash_plot_style_indices(
            [{"type": bad}, {"type": "scatter"}])
        assert got == [0, 1]

    @pytest.mark.parametrize("bad", [None, 7, "lfitci", ["x"]])
    def test_a_plot_that_is_not_a_dict_is_one_plot(self, bad):
        assert dr._dash_plot_style_indices(
            [bad, {"type": "lfitci"}, {"type": "line"}]) == [0, 1, 3]

    def test_no_plots(self):
        assert dr._dash_plot_style_indices([]) == []
        assert dr._dash_plot_style_indices(None) == []

    def test_many_plots_are_linear(self):
        """Resource exhaustion: 200,000 layers are indexed in one pass, each
        index within the fifteen-plot cycle."""
        plots = [{"type": "lfitci"}, {"type": "scatter"}] * 100_000
        t0 = time.perf_counter()
        got = dr._dash_plot_style_indices(plots)
        assert time.perf_counter() - t0 < 5.0
        assert len(got) == 200_000 and set(got) <= set(range(15))


# ---------------------------------------------------------------------------
# Both modes, end to end
# ---------------------------------------------------------------------------

_SEQ = itertools.count()
_N = 40
_DF = pd.DataFrame({
    "x": np.linspace(1.0, 40.0, _N),
    "x2": np.linspace(2.0, 41.0, _N),
    "y": np.sin(np.linspace(0, 3, _N)) * 10 + 20 + np.linspace(0, 5, _N),
    "y2": np.cos(np.linspace(0, 3, _N)) * 10 + 30,
    "lo": np.linspace(5.0, 15.0, _N),
    "hi": np.linspace(20.0, 35.0, _N),
})


def _layer(t, k):
    y = "y" if k % 2 == 0 else "y2"
    if t in _NOFIT:
        typ, opts = _NOFIT[t]
        return {"type": typ, "yvar": y, "xvar": "x", "options": dict(opts)}
    if t in ("rarea", "rcap", "rcapsym"):
        return {"type": t, "yvar1": "lo", "yvar2": "hi", "xvar": "x",
                "options": {}}
    if t == "pcarrow":
        return {"type": t, "y1var": "lo", "x1var": "x", "y2var": "hi",
                "x2var": "x2", "options": {}}
    if t in ("histogram", "kdensity"):
        return {"type": t, "var": y, "options": {}}
    return {"type": t, "yvar": y, "xvar": "x", "options": {}}


def _spec(plots, scheme, legend=""):
    return {"graphs": [{"plots": plots,
                        "graph_options": dict(
                            {"name": "g1", "title": '"t"'},
                            **({"legend": legend} if legend else {})),
                        "if_expr": "", "in_expr": ""}],
            "kpis": [],
            "build_options": {"layout": "auto", "link": "", "filter": "",
                              "theme": "", "scheme": scheme,
                              "session_scheme": "", "title": "",
                              "subtitle": "", "registry": "g1", "tabs": "",
                              "filter_position": "top", "csv": "0",
                              "level": "95", "formats": {}, "limits": {}}}


def _figure(mode, wd, plots, scheme, legend=""):
    from bokeh.document import Document
    from bokeh.plotting import figure as _fig_cls
    tag = next(_SEQ)
    sp = wd / ("spec_%d.json" % tag)
    dp = wd / ("data_%d.json" % tag)
    sp.write_text(json.dumps(_spec(plots, scheme, legend)), encoding="utf-8")
    dp.write_text(json.dumps(make_data_json(_DF)), encoding="utf-8")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if mode == "saved":
            r = dr.DashRenderer(str(sp), str(dp))
            return list(r._build_figures().values())[0]
        ap = str(wd / ("app_%d.py" % tag))
        dr.ServerAppBuilder(str(sp), str(dp)).build(ap)
        mod = load_app(ap, "_ci_app_%d" % tag, draw=False)
        doc = Document()
        mod.make_document(doc)
    figs = [m for root in doc.roots for m in root.references()
            if isinstance(m, _fig_cls)]
    assert len(figs) == 1
    return figs[0]


@pytest.fixture
def wd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "z1.scheme").write_text(_Z1, encoding="utf-8")
    return tmp_path


def _hex(c):
    return str(c).lstrip("#").lower()


#: The glyphs that carry each layer's p# colour, and the scheme cycle each
#: reads.  A ci layer's line; its band is Stata's ci style.
_DRAWS = {"scatter": [("Scatter", "scatter")], "line": [("Line", "line")],
          "lfit": [("Line", "line")], "lfitci": [("Line", "line")],
          "qfitci": [("Line", "line")], "lpolyci": [("Line", "line")],
          "fpfitci": [("Line", "line")],
          "connected": [("Line", "connected"), ("Scatter", "scatter")],
          # Flipped (WP-30 P1.17a): twoway draws rcap caps as long as a
          # marker of its msize, so dash draws them as dash Scatters.
          "rcap": [("Segment", "rcap"), ("Scatter", "rcap")],
          "rcapsym": [("Segment", "rcapsym"), ("Scatter", "scatter")],
          "pcarrow": [("Segment", "pcarrow")], "rarea": [("VArea", "area")],
          # WP-34 PIC-3: a nofit layer draws its band alone, in pstyle ci;
          # the layers after it carry the p# it counts for.
          "lfitcinf": [], "qfitcinf": [], "lpolycinf": [], "fpfitcinf": [],
          "lfitcinfr": []}


def _drawn(fig, glyph):
    out = []
    for r in drawn_renderers(fig):
        g = getattr(r, "glyph", None)
        if type(g).__name__ != glyph:
            continue
        # A ci band drawn as a line by ciplot(rline) is pstyle ci, no p#;
        # a nofit layer's hidden fit line (kept for the refit) is no plot.
        if getattr(r, "_dash_ci_band", False) \
                or getattr(r, "_dash_nofit", False):
            continue
        c = getattr(g, "fill_color" if glyph in ("Scatter", "VArea")
                    else "line_color")
        out.append(_hex(c))
    return out


_E2E = [c for c in _T["cases"]
        if all(_expand(c["layers"])[0].count(t) == 0
               for t in ("histogram", "kdensity"))]


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestBothModes:
    @pytest.mark.parametrize("case", _E2E, ids=[c["id"] for c in _E2E])
    def test_each_layer_takes_statas_plot_index(self, mode, wd, case):
        """Every layer's colour, and its line's width, is the p# Stata
        draws it in, in both modes."""
        types, want = _want(case)
        plots = [_layer(t, k) for k, t in enumerate(types)]
        fig = _figure(mode, wd, plots, case["scheme"])
        sp = SchemeParser(case["scheme"])
        for glyph in sorted({g for t in types for g, _ in _DRAWS[t]}):
            # A VArea's fill is the p# colour at the p#area intensity
            # (WP-30 P1.2b; twoway's SVG, plan section 16 Evidence E3);
            # the plot index rule pinned here is unchanged.
            expect = [_hex(sp.default_color(i, cyc)) if g != "VArea"
                      else _hex(dr.GlyphMapper._blend_intensity(
                          sp.default_color(i, cyc),
                          sp.p_area_intensity[i % 15], sp.naturally_white))
                      for t, i in zip(types, want)
                      for g, cyc in _DRAWS[t] if g == glyph]
            got = _drawn(fig, glyph)
            # rcapsym draws its spike as one Segment.
            dedup = [c for k, c in enumerate(got) if k == 0 or got[k - 1] != c]
            assert dedup == [c for k, c in enumerate(expect)
                             if k == 0 or expect[k - 1] != c], (glyph, got)

    def test_the_line_widths_follow_the_index(self, mode, wd):
        """Under z1 (p1 vthick, p14 thick, p15 vvthick), 13 scatters then
        lfitci then line: the fit's line is p14 (thick) and the line after
        it p1 (vthick), as Stata draws them (measured)."""
        types = ["scatter"] * 13 + ["lfitci", "line"]
        plots = [_layer(t, k) for k, t in enumerate(types)]
        fig = _figure(mode, wd, plots, "z1")
        widths = [r.glyph.line_width for r in drawn_renderers(fig)
                  if type(getattr(r, "glyph", None)).__name__ == "Line"]
        tr = dr.OptionTranslator.translate_lwidth
        assert widths == [tr("thick"), tr("vthick")], widths

    def test_s1mono_symbols_follow_the_index(self, mode, wd):
        """s1mono, scatter || lpolyci || scatter: the second scatter is p4,
        a triangle (measured), not p3's diamond."""
        plots = [_layer(t, k) for k, t in
                 enumerate(["scatter", "lpolyci", "scatter"])]
        fig = _figure(mode, wd, plots, "s1mono")
        marks = [r.glyph.marker for r in drawn_renderers(fig)
                 if type(getattr(r, "glyph", None)).__name__ == "Scatter"]
        sp = SchemeParser("s1mono")
        assert marks == [sp.default_symbol(0), sp.default_symbol(3)], marks
        assert sp.default_symbol(3) == "triangle"

    def test_order_counts_a_ci_layer_as_two_keys(self, mode, wd):
        """WP-28 B5: scatter || lfitci || scatter is keys 1, 2 (band),
        3 (fit) and 4, so order(4 1) draws the second scatter's key then
        the first's (text_truth.json l_ci_order_last), by Stata's plot
        number; order(2 3) the band then the fit."""
        plots = [_layer(t, k) for k, t in
                 enumerate(["scatter", "lfitci", "scatter"])]
        sp = SchemeParser("s2color")
        for opt, want in (("order(4 1)", [sp.default_color(3, "scatter"),
                                          sp.default_color(0, "scatter")]),
                          ("order(2 3)", ["#c0c0c0",
                                          sp.default_color(1, "line")])):
            fig = _figure(mode, wd, plots, "s2color", opt)
            items = [it for lg in fig.legend for it in lg.items]
            assert len(items) == 2, (opt, [it.label for it in items])
            for it, c in zip(items, want):
                g = it.renderers[0].glyph
                col = (getattr(g, "fill_color", None)
                       or getattr(g, "line_color"))
                assert _hex(col) == _hex(c), (opt, it.label, col, c)

    def test_order_counts_nofit_as_one(self, mode, wd):
        """WP-34 PIC-3: (lfitci, nofit) (scatter) (lfit), legend(order(2
        3)) keys the scatter and the lfit, as twoway does
        (ci_plot_index_truth.json legend_nofit: "Mileage (mpg)", the
        scatter's y, then "Fitted values"); the scatter's key in p2's
        colour and the fit's in p3's."""
        want = _T["legend_nofit"]["keys"]
        assert want == ["Mileage (mpg)", "Fitted values"]
        plots = [_layer("lfitcinf", 0), _layer("scatter", 1),
                 _layer("lfit", 2)]
        sp = SchemeParser("s2color")
        fig = _figure(mode, wd, plots, "s2color", "order(2 3)")
        items = [it for lg in fig.legend for it in lg.items]
        labels = [it.label.get("value") if isinstance(it.label, dict)
                  else getattr(it.label, "value", it.label) for it in items]
        # The scatter's y here is y2, unlabelled: its key is its name.
        assert labels == ["y2", want[1]], labels
        for it, c in zip(items, [sp.default_color(1, "scatter"),
                                 sp.default_color(2, "line")]):
            g = it.renderers[0].glyph
            col = getattr(g, "fill_color", None) or getattr(g, "line_color")
            assert _hex(col) == _hex(c), (it.label, col, c)

    def test_the_legend_keeps_its_keys_in_order(self, mode, wd):
        """scatter || lfitci || scatter: four keys in layer order -- the
        first scatter, the band, the fit, the second scatter -- each key's
        renderers drawn in its layer's colour, the band's in the scheme's
        ci style (s2color's gs12, #C0C0C0: BUGS.md "A ci band is filled in
        its line's colour, where Stata fills it in pstyle ci")."""
        plots = [_layer(t, k) for k, t in
                 enumerate(["scatter", "lfitci", "scatter"])]
        fig = _figure(mode, wd, plots, "s2color")
        items = [it for lg in fig.legend for it in lg.items]
        assert len(items) == 4, [it.label for it in items]
        sp = SchemeParser("s2color")
        want = [sp.default_color(0, "scatter"), "#c0c0c0",
                sp.default_color(1, "line"), sp.default_color(3, "scatter")]
        for it, c in zip(items, want):
            g = it.renderers[0].glyph
            col = getattr(g, "fill_color", None) or getattr(g, "line_color")
            assert _hex(col) == _hex(c), (it.label, col, c)


class TestTheHelp:
    def test_the_nofit_sentence(self):
        """WP-34 PIC-3: the legend's numbering sentence says a nofit ci fit
        is one plot (dash.sthlp, the legend section)."""
        from test_help_claims_1 import _between, _help
        text = " ".join(_between(_help(), "Keys are numbered as",
                                 "{cmd:label(}").split())
        assert ("a confidence-interval fit such as {cmd:lfitci} is two, its "
                "band {it:n} and its line {it:n}+1, and one under "
                "{cmd:nofit}, which draws its band alone, as {cmd:twoway} "
                "numbers it.") in text
