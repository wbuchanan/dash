"""
test_scheme_linewidth.py -- `linewidth p#' reaches each plot's line as
Stata's chain reaches it.

The defect (BUGS.md, S3): dash had one line width, from `linewidth p',
shared by every drawing site, so a custom scheme's `linewidth p1 vthick'
after `#include s2color' thickened nothing, where Stata thickens plot 1's
line alone.

Stata's truth, measured 24sep2026 with StataNow 19.5 and kept in
test/fixtures/linewidth_chain_truth.json (the schemes, the commands and
the widths read from `.Graph.plotregion1.plot<k>.style.line.width' and
`.style.area.linestyle.width'): the width follows
`linewidth p#<kind>' -> `linewidth p<kind>' -> `linewidth p#' ->
`linewidth p', where the kind is the style file's (linestyle-p#line.style
says `set width scheme p#lineplot'):

* lineplot -- line, lfit, qfit, lowess, lpoly, fpfit, kdensity, function,
  rline and a ci fit's line;
* area -- the outline of area and rarea;
* arrowline -- pcarrow and pcbarrow;
* bar -- bar and rbar, where every Stata scheme sets `linewidth pbar', so
  p# and p never reach a bar;
* none (linestyle-p#.style, `set width scheme p#') -- connected, spike,
  dropline, rspike, rcap, rcapsym, rconnected, pcspike, pccapsym, mspline
  and mband.

A ci band itself takes `linewidth ci' and a histogram `linewidth
histogram'; neither follows p#.
"""
import itertools
import json
import math
import os
import sys
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

with open(os.path.join(_HERE, "fixtures", "linewidth_chain_truth.json"),
          encoding="utf-8") as _fh:
    _T = json.load(_fh)
with open(os.path.join(_HERE, "fixtures", "marker_linewidth_truth.json"),
          encoding="utf-8") as _fh:
    _MK = json.load(_fh)
with open(os.path.join(_HERE, "fixtures", "scheme_truth.json"),
          encoding="utf-8") as _fh:
    _SCHEME_TRUTH = json.load(_fh)

#: Each measured command: the chain dash follows for it, and the attribute
#: of Stata's graph that carries the line dash draws.  A ci fit draws its
#: band first, so its lines are plots 2 and 4, drawn in p1 and p3
#: (dr._dash_plot_style_indices; test_ci_plot_index.py).
_KIND = {
    "line": ("lineplot", "line"), "lfit": ("lineplot", "line"),
    "qfit": ("lineplot", "line"), "lowess": ("lineplot", "line"),
    "lpoly": ("lineplot", "line"), "fpfit": ("lineplot", "line"),
    "kdensity": ("lineplot", "line"), "function": ("lineplot", "line"),
    "rline": ("lineplot", "line"),
    "connected": ("", "line"), "scatterc": ("", "line"),
    "spike": ("", "line"), "dropline": ("", "line"),
    "rspike": ("", "line"), "rcap": ("", "line"), "rcapsym": ("", "line"),
    "rconnected": ("", "line"), "pcspike": ("", "line"),
    "pccapsym": ("", "line"), "mspline": ("", "line"),
    "mband": ("", "line"), "pcarrowi": ("arrowline", "line"),
    "pcarrow": ("arrowline", "line"), "pcbarrow": ("arrowline", "line"),
    "area": ("area", "area_line"), "rarea": ("area", "area_line"),
    "bar": ("bar", "area_line"), "rbar": ("bar", "area_line"),
}
_CI = {"lfitci", "qfitci", "lpolyci", "fpfitci"}

#: s2color's `linewidth pbar thin' (.2, inherited by every scheme that
#: includes s2color) and economist's `pbar vvthin' (.01) and `parea thin'
#: (.2) were not carried by dash's transcriptions, so a bar outline was
#: drawn at Bokeh's 1px and economist's area outline at `linewidth p'
#: (BUGS.md, S3); the extractor now carries them and every width below is
#: compared.


def _px(sp, unit):
    """dash's width for Stata's *unit*: one rule for keywords and numbers
    alike, Stata units x 2.88 pt through line_px (WP-30 P1.12b; it was
    dash's private ladder, medium 1.5 px, and 5 px per number unit)."""
    del sp
    return dr.OptionTranslator.line_px(unit * dr.OptionTranslator.PT_PER_RS)


def _cases():
    out = []
    for s, cmds in sorted(_T["cases"].items()):
        base = _T["schemes"][s].split()[1]
        for cmd, plots in sorted(cmds.items()):
            if cmd in _CI:
                # Both fits' lines: plots 2 and 4, drawn in p1 and p3.
                out.append(pytest.param(s, base, cmd, "lineplot",
                                        [plots["2"]["line"],
                                         plots["4"]["line"]],
                                        id="%s-%s" % (s, cmd)))
                continue
            if cmd not in _KIND:
                continue
            kind, attr = _KIND[cmd]
            want = [plots["1"][attr], plots["2"][attr]]
            out.append(pytest.param(s, base, cmd, kind, want,
                                    id="%s-%s" % (s, cmd)))
    return out


@pytest.fixture
def wd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _parse(wd, name, text):
    (wd / (name + ".scheme")).write_text(text, encoding="utf-8")
    return SchemeParser(name)


class TestTheChainAgainstStata:
    @pytest.mark.parametrize("scheme,base,cmd,kind,want", _cases())
    def test_each_measured_plot(self, wd, scheme, base, cmd, kind, want):
        sp = _parse(wd, scheme, _T["schemes"][scheme])
        idx = dr._dash_plot_style_indices([{"type": cmd}] * len(want))
        for layer, unit in enumerate(want):
            got = sp.plot_line_width(idx[layer], kind)
            assert got == pytest.approx(_px(sp, unit)), (layer, unit, got)

    def test_the_fixture_covers_every_chain(self):
        kinds = {k for k, _ in _KIND.values()} | {"mark"}
        assert kinds == set(SchemeParser._PLOT_LWIDTH_KINDS)
        assert len(_cases()) >= 150


class TestTheChainByKey:
    def test_p1_thickens_plot_one_alone(self, wd):
        sp = _parse(wd, "k1", "#include s2color\nlinewidth p1 vthick\n")
        vthick = dr.OptionTranslator.translate_lwidth("vthick")
        for kind in ("", "lineplot", "area", "arrowline"):
            assert sp.plot_line_width(0, kind) == vthick
            assert [sp.plot_line_width(i, kind) for i in range(1, 15)] == [
                sp.default_line_width] * 14
        # s2color's `linewidth pbar thin' (measured .2 on both plots).
        assert sp.plot_line_width(0, "bar") == \
            dr.OptionTranslator.translate_lwidth("thin")

    def test_the_kind_stub_beats_p_hash(self, wd):
        sp = _parse(wd, "k2", "#include s2color\nlinewidth p1 vthick\n"
                    "linewidth plineplot vvthick\nlinewidth parea thick\n"
                    "linewidth p2arrowline thin\nlinewidth pbar medthick\n")
        tr = dr.OptionTranslator.translate_lwidth
        assert sp.plot_line_width(0, "lineplot") == tr("vvthick")
        assert sp.plot_line_width(4, "lineplot") == tr("vvthick")
        assert sp.plot_line_width(0, "") == tr("vthick")
        assert sp.plot_line_width(0, "area") == tr("thick")
        assert sp.plot_line_width(0, "arrowline") == tr("vthick")
        assert sp.plot_line_width(1, "arrowline") == tr("thin")
        assert sp.plot_line_width(2, "arrowline") == sp.default_line_width
        assert sp.plot_line_width(7, "bar") == tr("medthick")

    def test_p1line_reaches_nothing(self, wd):
        """`linewidth p1line' is no key of any width chain (measured)."""
        sp = _parse(wd, "k3", "#include s2color\nlinewidth p1line vthick\n")
        for kind in ("", "lineplot", "area", "arrowline", "mark"):
            assert sp.plot_line_width(0, kind) == sp.default_line_width
        assert sp.plot_line_width(0, "bar") == \
            dr.OptionTranslator.translate_lwidth("thin")

    def test_a_bare_p_reaches_every_plot_but_a_bar(self, wd):
        sp = _parse(wd, "k4", "#include s2color\nlinewidth p vthick\n")
        vthick = dr.OptionTranslator.translate_lwidth("vthick")
        assert sp.default_line_width == vthick
        for kind in ("", "lineplot", "area", "arrowline", "mark"):
            assert sp.plot_line_width(3, kind) == vthick
        assert sp.plot_line_width(3, "bar") == \
            dr.OptionTranslator.translate_lwidth("thin")

    @pytest.mark.parametrize("scheme", sorted(SchemeParser._BUILTIN_NAMES))
    def test_the_shipped_file_draws_the_widths_it_drew(self, scheme):
        """Every shipped scheme's fifteen plots draw `linewidth p', the one
        width they drew before -- markers' outlines too, since no Stata
        scheme sets `linewidth pmark' -- but for the outlines of bars
        (every Stata scheme's `linewidth pbar') and economist's areas
        (`linewidth parea thin'), which Stata draws at those keys."""
        sp = SchemeParser(scheme)
        truth = _SCHEME_TRUTH[scheme]
        kinds = ["", "lineplot", "arrowline", "mark"]
        if not (truth.get("area_line_width") or {}).get("name"):
            kinds.append("area")
        for kind in kinds:
            assert [sp.plot_line_width(i, kind) for i in range(15)] == [
                sp.default_line_width] * 15, kind


class TestAdversarial:
    def test_the_index_wraps_and_a_hostile_index_is_harmless(self, wd):
        sp = _parse(wd, "a1", "#include s2color\nlinewidth p1 vthick\n")
        assert sp.plot_line_width(15) == sp.plot_line_width(0)
        assert sp.plot_line_width(-1) == sp.plot_line_width(14)
        assert sp.plot_line_width(10 ** 30) == sp.plot_line_width(
            10 ** 30 % 15)
        for bad in (None, "x", float("nan"), float("inf")):
            assert sp.plot_line_width(bad) == sp.plot_line_width(0)

    def test_an_unknown_kind_is_the_plain_chain(self, wd):
        sp = _parse(wd, "a2", "#include s2color\nlinewidth p1 vthick\n"
                    "linewidth p1evil 0\n")
        for kind in ("evil", "../x", "<script>", None, 5):
            assert sp.plot_line_width(0, kind) == sp.plot_line_width(0, "")

    @pytest.mark.parametrize("bad", ["<b>x</b>", "nan", "-5", "inf", "1e308",
                                     "9" * 100_000, "vthick;rm -rf /"])
    def test_a_hostile_width_falls_through_the_chain(self, wd, bad):
        """Injection and exhaustion: a p1 width that is markup, not finite,
        negative or absurd is not drawn; plot 1 falls back to `linewidth p'
        (or, beyond it, to the next key present), with at most one warning
        for the key however many plots ask."""
        sp = _parse(wd, "a3", "#include s2color\nlinewidth p1 %s\n"
                    "linewidth plineplot thick\n" % bad)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            vals = [sp.plot_line_width(i * 15, "") for i in range(50)]
            vals += [sp.plot_line_width(0, "area") for _ in range(50)]
        assert all(math.isfinite(v) and 0 <= v <= sp._LWIDTH_MAX_PX
                   for v in vals)
        assert set(vals) == {sp.default_line_width}, (bad[:20], set(vals))
        assert sp.plot_line_width(0, "lineplot") == \
            dr.OptionTranslator.translate_lwidth("thick")
        assert len([x for x in w if "p1" in str(x.message)]) <= 1


# ---------------------------------------------------------------------------
# Both modes, end to end: every drawing site
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
    "lo2": np.linspace(3.0, 12.0, _N),
    "hi2": np.linspace(25.0, 40.0, _N),
})
_SCHEME = ("#include s2color\nlinewidth p1 vthick\nlinewidth p2 thick\n")


def _layers(ptype):
    if ptype in {"rline", "rarea", "rspike", "rcap", "rcapsym",
                 "rconnected", "rbar"}:
        return [{"type": ptype, "yvar1": "lo", "yvar2": "hi", "xvar": "x",
                 "options": {}},
                {"type": ptype, "yvar1": "lo2", "yvar2": "hi2", "xvar": "x",
                 "options": {}}]
    if ptype.startswith("pc"):
        return [{"type": ptype, "y1var": "lo", "x1var": "x", "y2var": "hi",
                 "x2var": "x2", "options": {}},
                {"type": ptype, "y1var": "lo2", "x1var": "x", "y2var": "hi2",
                 "x2var": "x2", "options": {}}]
    if ptype == "function":
        return [{"type": "function", "expr": "x", "options": {}},
                {"type": "function", "expr": "2*x", "options": {}}]
    if ptype == "kdensity":
        return [{"type": "kdensity", "var": "y", "options": {}},
                {"type": "kdensity", "var": "y2", "options": {}}]
    opts = {"lcolor": "red"} if ptype == "area" else {}
    return [{"type": ptype, "yvar": "y", "xvar": "x", "options": dict(opts)},
            {"type": ptype, "yvar": "y2", "xvar": "x", "options": dict(opts)}]


def _spec(plots, scheme):
    return {"graphs": [{"plots": plots,
                        "graph_options": {"name": "g1", "title": '"t"'},
                        "if_expr": "", "in_expr": ""}],
            "kpis": [],
            "build_options": {"layout": "auto", "link": "", "filter": "",
                              "theme": "", "scheme": scheme,
                              "session_scheme": "", "title": "",
                              "subtitle": "", "registry": "g1", "tabs": "",
                              "filter_position": "top", "csv": "0",
                              "level": "95", "formats": {}, "limits": {}}}


def _figure(mode, wd, plots, scheme):
    from bokeh.document import Document
    from bokeh.plotting import figure as _fig_cls
    tag = next(_SEQ)
    sp = wd / ("spec_%d.json" % tag)
    dp = wd / ("data_%d.json" % tag)
    sp.write_text(json.dumps(_spec(plots, scheme)), encoding="utf-8")
    dp.write_text(json.dumps(make_data_json(_DF)), encoding="utf-8")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if mode == "saved":
            r = dr.DashRenderer(str(sp), str(dp))
            return list(r._build_figures().values())[0]
        ap = str(wd / ("app_%d.py" % tag))
        dr.ServerAppBuilder(str(sp), str(dp)).build(ap)
        mod = load_app(ap, "_lw_app_%d" % tag)
        doc = Document()
        mod.make_document(doc)
    figs = [m for root in doc.roots for m in root.references()
            if isinstance(m, _fig_cls)]
    assert len(figs) == 1
    return figs[0]


_LINE_GLYPHS = {"Line", "Segment", "MultiLine", "VBar"}


def _widths_by_layer(fig):
    """The line widths of the glyphs each of the two layers drew, in
    renderer order; the two layers draw the same glyphs."""
    ws = [r.glyph.line_width for r in fig.renderers
          if type(getattr(r, "glyph", None)).__name__ in _LINE_GLYPHS]
    assert ws and len(ws) % 2 == 0, ws
    h = len(ws) // 2
    return ws[:h], ws[h:]


_SITES = [
    ("line", "lineplot"), ("connected", ""), ("lfit", "lineplot"),
    ("qfit", "lineplot"), ("lowess", "lineplot"), ("lpoly", "lineplot"),
    ("fpfit", "lineplot"), ("kdensity", "lineplot"),
    ("function", "lineplot"), ("mspline", ""), ("mband", ""),
    ("lfitci", "lineplot"), ("qfitci", "lineplot"),
    ("lpolyci", "lineplot"), ("fpfitci", "lineplot"),
    ("spike", ""), ("dropline", ""), ("area", "area"),
    ("rline", "lineplot"), ("rspike", ""), ("rcap", ""), ("rcapsym", ""),
    ("rconnected", ""), ("pcspike", ""), ("pccapsym", ""),
    ("pcarrow", "arrowline"), ("pcbarrow", "arrowline"),
]


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestBothModesDrawEachPlotsWidth:
    @pytest.mark.parametrize("ptype,kind", _SITES)
    def test_linewidth_p1_and_p2(self, mode, wd, ptype, kind):
        """Under `#include s2color' + `linewidth p1 vthick' + `linewidth p2
        thick', layer 1's lines are vthick and layer 2's thick, at every
        site that draws a plot's line (Stata: 1.4 and .8, measured)."""
        (wd / "lwe2e.scheme").write_text(_SCHEME, encoding="utf-8")
        fig = _figure(mode, wd, _layers(ptype), "lwe2e")
        a, b = _widths_by_layer(fig)
        tr = dr.OptionTranslator.translate_lwidth
        assert set(a) == {tr("vthick")}, (ptype, a)
        if ptype in _CI:
            # The second fit's line is plot 4, drawn in p3: `linewidth p'
            # (lwt1, measured .3).
            assert set(b) == {SchemeParser("s2color").default_line_width}, (
                ptype, b)
        else:
            assert set(b) == {tr("thick")}, (ptype, b)

    def test_the_arrows_follow_the_shaft(self, mode, wd):
        # WP-31 C1: the heads are a glyph per layer (the arrowline chain).
        (wd / "lwe2e.scheme").write_text(_SCHEME, encoding="utf-8")
        fig = _figure(mode, wd, _layers("pcarrow"), "lwe2e")
        heads = [r.glyph.line_width for r in fig.renderers
                 if "dash-arrowhead" in (r.tags or [])]
        tr = dr.OptionTranslator.translate_lwidth
        assert set(heads) == {tr("vthick"), tr("thick")}, heads

    def test_an_option_still_wins(self, mode, wd):
        (wd / "lwe2e.scheme").write_text(_SCHEME, encoding="utf-8")
        plots = _layers("line")
        plots[0]["options"] = {"lwidth": "vthin"}
        a, b = _widths_by_layer(_figure(mode, wd, plots, "lwe2e"))
        tr = dr.OptionTranslator.translate_lwidth
        assert a == [tr("vthin")] and b == [tr("thick")]

    def test_a_bar_takes_pbar_not_p1(self, mode, wd):
        """`linewidth p1 vthick' leaves a bar's outline (Stata: s2color's
        `pbar thin', measured .2 on both plots); `linewidth p1bar' reaches
        it (measured .8 under `p1bar thick')."""
        (wd / "lwe2e.scheme").write_text(_SCHEME, encoding="utf-8")
        a, b = _widths_by_layer(_figure(mode, wd, _layers("bar"), "lwe2e"))
        (wd / "lwbar.scheme").write_text(
            "#include s2color\nlinewidth p1bar thick\n", encoding="utf-8")
        c, d = _widths_by_layer(_figure(mode, wd, _layers("bar"), "lwbar"))
        assert a == b == d == [dr.OptionTranslator.translate_lwidth("thin")], (
            a, b, d)
        assert c == [dr.OptionTranslator.translate_lwidth("thick")]

    @pytest.mark.parametrize("ptype", ["pcspike", "pccapsym", "pcarrow",
                                       "pcbarrow", "rcapsym"])
    def test_economist_draws_its_pc_lines_at_linewidth_p(self, mode, wd,
                                                         ptype):
        """economist's `linewidth p 1.2' reaches the paired-coordinate and
        rcapsym lines as it reaches every other plot's (Stata: plot 2 of
        `#include economist' + `linewidth p1 vthick' is 1.2 on pcarrow,
        measured); they were drawn at a fixed 1.5px under every scheme."""
        a, b = _widths_by_layer(_figure(mode, wd, _layers(ptype),
                                        "economist"))
        w = SchemeParser("economist").default_line_width
        assert set(a) == set(b) == {w}, (a, b)

    def test_the_shipped_scheme_is_unchanged(self, mode, wd):
        """s2color: both layers' lines at `linewidth p' (1.5px)."""
        a, b = _widths_by_layer(_figure(mode, wd, _layers("rcap"),
                                        "s2color"))
        assert set(a) == set(b) == {SchemeParser("s2color").default_line_width}


# ---------------------------------------------------------------------------
# Bar and area outlines: linewidth pbar and parea (BUGS.md, S3)
# ---------------------------------------------------------------------------

#: Stata's own values (scheme-s2color.scheme:1246 `linewidth pbar thin',
#: scheme-economist.scheme:211-213 `parea thin' and `pbar vvthin'); every
#: other shipped scheme includes s2color and sets neither.
_PBAR = {s: ("vvthin" if s == "economist" else "thin")
         for s in SchemeParser._BUILTIN_NAMES}
_PAREA = {"economist": "thin"}


class TestBarAndAreaOutlines:
    @pytest.mark.parametrize("scheme", sorted(SchemeParser._BUILTIN_NAMES))
    def test_the_extractor_carries_pbar_and_parea(self, scheme):
        t = _SCHEME_TRUTH[scheme]
        assert (t.get("bar_line_width") or {}).get("name") == _PBAR[scheme]
        assert (t.get("area_line_width") or {}).get("name") == \
            _PAREA.get(scheme)
        sp = SchemeParser(scheme)
        assert sp._props.get("linewidth pbar") == _PBAR[scheme]
        assert sp._props.get("linewidth parea") == _PAREA.get(scheme)

    @pytest.mark.parametrize("scheme", sorted(SchemeParser._BUILTIN_NAMES))
    def test_the_shipped_scheme_draws_pbar_and_parea(self, scheme):
        sp = SchemeParser(scheme)
        tr = dr.OptionTranslator.translate_lwidth
        assert [sp.plot_line_width(i, "bar") for i in range(15)] == [
            tr(_PBAR[scheme])] * 15
        area = (tr(_PAREA[scheme]) if scheme in _PAREA
                else sp.default_line_width)
        assert [sp.plot_line_width(i, "area") for i in range(15)] == [
            area] * 15

    def test_a_standalone_scheme_without_pbar_leaves_the_outline(self, wd):
        """A user file with no #include and no pbar: nothing Stata's chain
        reaches, so the outline is left as Bokeh draws it."""
        sp = _parse(wd, "nopbar", "linewidth p thick\n")
        assert sp.plot_line_width(0, "bar") is None


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestBothModesDrawBarAndAreaOutlines:
    @pytest.mark.parametrize("ptype", ["bar", "rbar"])
    @pytest.mark.parametrize("scheme", ["s2color", "stcolor", "economist"])
    def test_a_bar_outline_is_pbar(self, mode, wd, ptype, scheme):
        a, b = _widths_by_layer(_figure(mode, wd, _layers(ptype), scheme))
        w = dr.OptionTranslator.translate_lwidth(_PBAR[scheme])
        assert a == b == [w], (a, b)

    def test_economists_area_outline_is_parea(self, mode, wd):
        a, b = _widths_by_layer(_figure(mode, wd, _layers("area"),
                                        "economist"))
        w = dr.OptionTranslator.translate_lwidth("thin")
        assert a == b == [w], (a, b)

    def test_an_option_still_wins_on_a_bar(self, mode, wd):
        plots = _layers("bar")
        plots[0]["options"] = {"lwidth": "vthick"}
        a, b = _widths_by_layer(_figure(mode, wd, plots, "s2color"))
        tr = dr.OptionTranslator.translate_lwidth
        assert a == [tr("vthick")] and b == [tr("thin")], (a, b)


# ---------------------------------------------------------------------------
# Marker outlines: linewidth p#mark -> pmark -> p# -> p (BUGS.md, S3)
# ---------------------------------------------------------------------------

_MARK_TYPES = ("scatter", "connected", "scatteri", "dot", "dropline",
               "rcapsym", "rscatter", "rconnected", "pcscatter", "pccapsym")


def _mk_cases():
    out = []
    for s, cmds in sorted(_MK["cases"].items()):
        for cmd, units in sorted(cmds.items()):
            if cmd in _MARK_TYPES:
                out.append(pytest.param(s, cmd, units, id="%s-%s" % (s, cmd)))
    return out


def _mk_parser(wd, scheme):
    if scheme == "economist":
        return SchemeParser("economist")
    return _parse(wd, scheme, _MK["schemes"][scheme])


def _mk_layers(ptype):
    """Three layers of *ptype*, as the fixture's commands draw them."""
    out = []
    for k, (y, lo, hi) in enumerate((("y", "lo", "hi"), ("y2", "lo2", "hi2"),
                                     ("y", "lo", "hi2"))):
        if ptype == "scatteri":
            out.append({"type": "scatteri", "values": [[k + 1, k + 2]],
                        "options": {}})
        elif ptype in ("rcapsym", "rscatter", "rconnected"):
            out.append({"type": ptype, "yvar1": lo, "yvar2": hi, "xvar": "x",
                        "options": {}})
        elif ptype in ("pcscatter", "pccapsym"):
            out.append({"type": ptype, "y1var": lo, "x1var": "x",
                        "y2var": hi, "x2var": "x2", "options": {}})
        else:
            out.append({"type": ptype, "yvar": y, "xvar": "x",
                        "options": {}})
    return out


def _marker_widths(fig, n=3):
    # dot's rows of dots are outlined in linestyle dotmark, no p# marker
    # outline (WP-31 B5b; test/fixtures/dot_truth.json D01, D25).
    ws = [r.glyph.line_width for r in fig.renderers
          if type(getattr(r, "glyph", None)).__name__ == "Scatter"
          and "dash_dots" not in (getattr(r, "tags", None) or ())]
    assert ws and len(ws) % n == 0, ws
    h = len(ws) // n
    return [ws[i * h:(i + 1) * h] for i in range(n)]


class TestMarkerOutlinesAgainstStata:
    @pytest.mark.parametrize("scheme,cmd,units", _mk_cases())
    def test_each_measured_marker(self, wd, scheme, cmd, units):
        sp = _mk_parser(wd, scheme)
        for i, unit in enumerate(units):
            assert sp.plot_line_width(i, "mark") == pytest.approx(
                _px(sp, unit)), (i, unit)

    @pytest.mark.parametrize("scheme", sorted(_MK["cases"]))
    def test_after_a_ci_fit(self, wd, scheme):
        """lfitci || scatter || scatter: the scatters are plots 3 and 4."""
        sp = _mk_parser(wd, scheme)
        units = _MK["cases"][scheme]["ciscatter"]
        idx = dr._dash_plot_style_indices(
            [{"type": "lfitci"}, {"type": "scatter"}, {"type": "scatter"}])
        for layer, unit in ((1, units[2]), (2, units[3])):
            assert sp.plot_line_width(idx[layer], "mark") == pytest.approx(
                _px(sp, unit))

    def test_the_fixture_covers_every_marker_type(self):
        for s, cmds in _MK["cases"].items():
            assert set(_MARK_TYPES) <= set(cmds), s

    @pytest.mark.parametrize("bad", ["<b>x</b>", "nan", "-5", "inf", "1e308",
                                     "9" * 100_000, "thick;rm -rf /"])
    def test_a_hostile_pmark_falls_through(self, wd, bad):
        """Injection and exhaustion: a pmark or p1mark that is markup, not
        finite, negative or absurd is not drawn; the chain goes on to p1
        and p, with at most one warning per key."""
        sp = _parse(wd, "hm", "#include s2color\nlinewidth pmark %s\n"
                    "linewidth p1mark %s\nlinewidth p1 thick\n" % (bad, bad))
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            vals = [sp.plot_line_width(i, "mark") for i in range(300)]
        tr = dr.OptionTranslator.translate_lwidth
        assert set(vals[0::15]) == {tr("thick")}
        assert set(vals[1::15]) == {sp.default_line_width}
        assert len(w) <= 2, [str(x.message)[:80] for x in w]


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestBothModesDrawMarkerOutlines:
    @pytest.mark.parametrize("ptype", _MARK_TYPES)
    def test_mk1_and_economist(self, mode, wd, ptype):
        """mk1 (p1 vthick, p2mark thick): markers 1.4, .8 and .3; economist
        (p 1.2): 1.2 on every marker (measured, every type)."""
        sp = _mk_parser(wd, "mk1")
        got = _marker_widths(_figure(mode, wd, _mk_layers(ptype), "mk1"))
        want = [_px(sp, u) for u in _MK["cases"]["mk1"][ptype]]
        for layer, w in zip(got, want):
            assert layer == pytest.approx([w] * len(layer)), (ptype, got, want)
        got = _marker_widths(_figure(mode, wd, _mk_layers(ptype),
                                     "economist"))
        w = SchemeParser("economist").default_line_width
        assert all(set(layer) == {w} for layer in got), got

    def test_the_shipped_scheme_draws_its_line_width(self, mode, wd):
        """s2color: every marker's outline at `linewidth p' (1.5px), as
        Stata draws it the width of its lines (scheme_visual SVG)."""
        got = _marker_widths(_figure(mode, wd, _mk_layers("scatter"),
                                     "s2color"))
        w = SchemeParser("s2color").default_line_width
        assert all(set(layer) == {w} for layer in got), got

    def test_mlwidth_still_wins(self, mode, wd):
        """mk1, scatter, mlwidth(vthin) || scatter: .15 and .8 (measured)."""
        _mk_parser(wd, "mk1")
        plots = _mk_layers("scatter")[:2]
        plots[0]["options"] = {"mlwidth": "vthin"}
        got = _marker_widths(_figure(mode, wd, plots, "mk1"), 2)
        tr = dr.OptionTranslator.translate_lwidth
        assert got == [[tr("vthin")], [tr("thick")]], got

    def test_a_marker_after_a_ci_fit(self, mode, wd):
        """mk2 (pmark vvthick, p1mark thin), lfitci || scatter || scatter:
        both scatters' markers vvthick; the p# index they take is 3 and 4."""
        _mk_parser(wd, "mk2")
        plots = [{"type": "lfitci", "yvar": "y", "xvar": "x", "options": {}}]
        plots += _mk_layers("scatter")[:2]
        got = _marker_widths(_figure(mode, wd, plots, "mk2"), 2)
        tr = dr.OptionTranslator.translate_lwidth
        assert got == [[tr("vvthick")], [tr("vvthick")]], got


# ---------------------------------------------------------------------------
# lwidth(vvvthick) (BUGS.md, S3)
# ---------------------------------------------------------------------------

class TestVvvthick:
    """Stata's linewidth-vvvthick.style is 4.2 units, drawn 1.615 times
    vvthick's 2.6 (measured 24sep2026 in twoway's SVG: 120.96 and 74.88
    units).  Flipped (WP-30 P1.12b): dash's private ladder compressed the
    upper rungs by a power of 0.588 (6.6px); the ladder is now Stata's,
    linear, 1 unit = 3.84 px, so vvvthick is 4.2 x 3.84 = 16.128px, and a
    name is case-sensitive (twoway notes THICK, measured 03oct2026)."""

    def test_on_the_ladder(self):
        tr = dr.OptionTranslator.translate_lwidth
        assert tr("vvvthick") == pytest.approx(16.128)
        with pytest.raises(ValueError):
            tr(" VVVTHICK ")
        assert tr("vvvthick") > tr("vvthick")
        u = _T["units"]
        assert tr("vvvthick") / tr("vvthick") == pytest.approx(
            u["vvvthick"] / u["vvthick"])

    def test_a_scheme_reads_it(self, wd):
        """lwt2's `linewidth p4 vvvthick'."""
        sp = _parse(wd, "v4", _T["schemes"]["lwt2"])
        assert sp.plot_line_width(3, "") == pytest.approx(16.128)
        assert sp.plot_line_width(3, "mark") == pytest.approx(16.128)
        assert _px(sp, 4.2) == pytest.approx(16.128)

    @pytest.mark.parametrize("bad", ["vvvvthick", "vvvthick;x", "vvv thick",
                                     "vvvthick" * 10_000, "<vvvthick>"])
    def test_a_near_miss_is_still_refused(self, bad):
        with pytest.raises(ValueError):
            dr.OptionTranslator.translate_lwidth(bad)


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestBothModesDrawVvvthick:
    def test_lwidth_and_mlwidth(self, mode, wd):
        plots = [{"type": "line", "yvar": "y", "xvar": "x",
                  "options": {"lwidth": "vvvthick"}},
                 {"type": "scatter", "yvar": "y2", "xvar": "x",
                  "options": {"mlwidth": "vvvthick"}}]
        fig = _figure(mode, wd, plots, "s2color")
        lines = [r.glyph.line_width for r in fig.renderers
                 if type(getattr(r, "glyph", None)).__name__ == "Line"]
        marks = [r.glyph.line_width for r in fig.renderers
                 if type(getattr(r, "glyph", None)).__name__ == "Scatter"]
        assert lines == [pytest.approx(16.128)] and marks == [
            pytest.approx(16.128)], (lines, marks)
