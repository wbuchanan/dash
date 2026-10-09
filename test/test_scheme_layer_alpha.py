"""A scheme's declared colour opacity reaches every layer (WP-30 P1.4a).

Measured in StataNow 19.5 (`graph export' SVG, 03oct2026, plan section 24
Evidence E7; test/fixtures/scheme_layer_truth.json): under sttrans, whose
every p# colour is ``"26 71 111 %20"``, twoway strokes and fills every fit,
smooth, function, spike, range, paired-coordinate and immediate layer at
opacity 0.20, its arrow heads and range caps included.  The confidence band
is drawn in ``color ci_area`` with no opacity.  dash drew all of these at
1.0, and rarea at 0.5 under every scheme.

The thirteen types test_help_claims_8's TestTheSchemeOpacityStopsWhere
TheHelpSays covers are not repeated here.
"""

import json
import os
import re
import sys

import pytest
from bokeh.models import Arrow, GlyphRenderer, Select

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_scheme_resolution import MODES, _draw  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures",
                        "scheme_layer_truth.json")
with open(_FIXTURE, encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)

#: The layer types not already covered by test_help_claims_8's opacity test.
_TYPES = ("qfit", "lowess", "lpoly", "fpfit", "mspline", "qfitci",
          "lpolyci", "fpfitci", "rcapsym", "rline", "tsrline", "rscatter",
          "rbar", "pcarrow", "pcarrowi", "pcbarrow", "pccapsym", "pcscatter")

_BAND = "#c0c0c0"


def _renderers(fig):
    return [r for r in fig.renderers if isinstance(r, GlyphRenderer)
            and not dr._dash_is_swatch(r)]


def _fig(plots, scheme, mode, bo=None):
    b = {"scheme": scheme}
    b.update(bo or {})
    d = _draw(tp._spec(plots, b), mode)
    assert len(d.figures) == 1
    return d.figures[0]


def _col(v):
    return str(getattr(v, "value", v)).lower()


def _alphas(fig, band=_BAND):
    """{alpha} of every drawn line and fill of *fig*, the band's colour,
    a glyph with no outline (alpha 0) and Arrow annotations aside."""
    out = set()
    for r in _renderers(fig):
        g = r.glyph
        name = type(g).__name__
        if "line_alpha" in g.properties() and _col(g.line_color) != band \
                and name not in ("VArea",) and g.line_alpha != 0:
            out.add(round(float(g.line_alpha), 4))
        if name in ("Scatter", "VBar", "VArea", "Quad") and \
                _col(g.fill_color) != band and g.fill_alpha != 0:
            out.add(round(float(g.fill_alpha), 4))
    for a in fig.select({"type": Arrow}):
        out.add(round(float(a.line_alpha), 4))
        for h in (a.end, a.start):
            if h is not None:
                out.add(round(float(h.line_alpha), 4))
    return out


@pytest.mark.parametrize("mode", MODES)
class TestSttransReachesEveryLayer:
    def test_each_type(self, mode):
        """Every line, segment, cap, marker and range fill is drawn at 0.2
        under sttrans; rbar's fill too (its outline is not drawn)."""
        bad = []
        for t in _TYPES:
            got = _alphas(_fig([plot_for(t)], "sttrans", mode))
            if got != {0.2}:
                bad.append(f"{t}: {sorted(got)}")
        assert not bad, bad

    def test_the_arrow_heads(self, mode):
        for t in ("pcarrow", "pcbarrow"):
            fig = _fig([plot_for(t)], "sttrans", mode)
            arrows = fig.select({"type": Arrow})
            assert arrows, t
            for a in arrows:
                heads = [h for h in (a.end, a.start) if h is not None]
                assert [a.line_alpha] + [h.line_alpha for h in heads] == \
                    pytest.approx([0.2] * (1 + len(heads))), t

    def test_the_empty_fit_line(self, mode):
        """A fit with no rows still keys its line at the declared opacity."""
        for t in ("lfit", "lfitci"):
            p = plot_for(t)
            p["options"]["if"] = "price > 99999"
            spec = tp._spec([p], {"scheme": "sttrans"})
            spec["graphs"][0]["if_expr"] = "price > 99999"
            fig = _draw(spec, mode).figures[0]
            lines = [r.glyph for r in _renderers(fig)
                     if type(r.glyph).__name__ == "Line"]
            assert lines and all(g.line_alpha == pytest.approx(0.2)
                                 for g in lines), (t, lines)


@pytest.mark.parametrize("mode", MODES)
class TestUserColoursUnderSttrans:
    def test_a_colour_without_pct_keeps_the_scheme_opacity(self, mode):
        fig = _fig([plot_for("rspike", {"lcolor": "red"})], "sttrans", mode)
        seg = [r.glyph for r in _renderers(fig)]
        assert [(_col(g.line_color), g.line_alpha) for g in seg] == \
            [("#ff0000", pytest.approx(0.2))]


@pytest.mark.parametrize("mode", MODES)
class TestTheCiLineRestyle:
    @pytest.mark.parametrize("ps, want", [("ci", 1.0), ("p3", 0.2)])
    def test_pstyle_sets_the_lines_opacity(self, mode, ps, want):
        """twoway: `lfitci, pstyle(ci)' draws its line #808080 opaque under
        sttrans; `pstyle(p3)' draws it #DDCC77 at 0.20."""
        fig = _fig([plot_for("lfitci", {"pstyle": ps})], "sttrans", mode)
        lines = [r.glyph for r in _renderers(fig)
                 if type(r.glyph).__name__ == "Line"]
        assert [g.line_alpha for g in lines] == [pytest.approx(want)]


class TestAfterAFilterMove:
    def test_the_served_glyphs_keep_their_opacity(self):
        spec = tp._spec([plot_for("lfit"), plot_for("rspike"),
                         plot_for("pcarrow")],
                        {"scheme": "sttrans",
                         "filter": "foreign, type(dropdown)"})
        doc, _ = tp._served(spec)
        sel = [w for w in tp._widgets_of(doc) if isinstance(w, Select)][0]
        tp._fire(sel, [v for v, lab in sel.options if lab == "Foreign"][0])
        figs = [m for m in tp._walk_models(doc)
                if type(m).__name__ in ("figure", "Figure")]
        assert figs
        assert _alphas(figs[0]) == {0.2}


class TestOtherSchemesDeclareNothing:
    def test_the_helper(self):
        """``_scheme_alpha_kw`` is empty under every scheme that declares
        no opacity, so their glyphs are built as before; sttrans gets
        both alphas when asked."""
        types = ("line", "spike", "rspike", "rcap", "rbar", "pcspike",
                 "pcarrow", "pcbarrow", "pccapsym", "scatter")
        bad = []
        for name in sorted(dr.SchemeParser._BUILTIN_NAMES - {"sttrans"}):
            gm = dr.GlyphMapper(scheme=dr.SchemeParser(name))
            for i in range(15):
                for t in types:
                    if gm._scheme_alpha_kw(i, t, fill=True):
                        bad.append((name, i, t))
        assert not bad, bad[:10]
        gm = dr.GlyphMapper(scheme=dr.SchemeParser("sttrans"))
        assert gm._scheme_alpha_kw(0, "rbar", fill=True, line=False) == \
            {"fill_alpha": pytest.approx(0.2)}
        assert gm._scheme_alpha_kw(0, "line") == \
            {"line_alpha": pytest.approx(0.2)}


# ---------------------------------------------------------------------------
# twoway's own SVG: every opacity probe, one test per mode
# ---------------------------------------------------------------------------

_OPT = re.compile(r"(\w+)\(([^)]*)\)")


def _probe_plot(p):
    cmd = p["command"]
    t = cmd.split()[0]
    opts = {}
    if "," in cmd and not t.startswith("function"):
        opts = dict(_OPT.findall(cmd.split(",", 1)[1]))
    return plot_for(t, opts)


def _twoway_alphas(p, band=_BAND):
    out = set()
    for e in p["elements"]:
        if e["stroke"] in ("#eaf2f3",) or band in (e["fill"], e["stroke"]):
            continue
        if e["fill"] not in (None, "none"):
            out.add(e["fill_opacity"] if e["fill_opacity"] is not None
                    else 1.0)
        if e["stroke"] not in (None, "none"):
            out.add(e["stroke_opacity"] if e["stroke_opacity"] is not None
                    else 1.0)
    return out


class TestTheFixture:
    def test_meta_is_stamped(self):
        m = TRUTH["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted"):
            assert m.get(k), k
        assert all(p["rc"] == 0 for p in TRUTH["probes"].values())


@pytest.mark.parametrize("mode", MODES)
class TestTwowaysOpacity:
    def test_each_probe(self, mode):
        """dash's alphas equal twoway's on every opacity probe; the band
        and the grid aside."""
        bad = []
        for pid, p in sorted(TRUTH["probes"].items()):
            if p["group"] not in ("opacity", "opacity_user"):
                continue
            want = _twoway_alphas(p)
            got = _alphas(_fig([_probe_plot(p)], p["scheme"], mode))
            if got != want:
                bad.append(f"{pid}: twoway {sorted(want)}, dash {sorted(got)}")
        assert not bad, bad
