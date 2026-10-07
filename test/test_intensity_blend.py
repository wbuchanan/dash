"""Intensity is an opaque blend and markers are opaque (WP-30 P1.2b, M1).

twoway draws a marker opaque unless its colour carries %NN, the scheme
declares an opacity (sttrans) or malpha() is given, and draws an intensity
as a colour: towards white below 100 and divided above it under
``naturally_white 1``, multiplied under ``naturally_white 0`` (s1rcolor),
then clamped to the smallest non-zero channel.  dash drew every marker at
alpha 0.8, drew fintensity() as an alpha, clamped it to [0, 1] and left
bar and area fills unblended (GAPS2 D11).

Every expected value below is twoway's, read from its SVG export
(StataNow 19.5 MP, measured 03oct2026, plan section 16 Evidence E3, and
test/fixtures/intensity_truth.json); none is computed through dash_render.
"""

import json
import os
import re
import sys
import warnings
from pathlib import Path

import pytest
from bokeh.models import CustomJS, GlyphRenderer

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_scheme_resolution import MODES, _draw, _props_scheme  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

G = dr.GlyphMapper


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _drawn(plots, mode, scheme=None):
    bo = {"scheme": scheme} if scheme else {}
    return _draw(tp._spec(plots, bo, {}), mode)


def _renderers(d):
    return [r for f in d.figures for r in f.renderers
            if isinstance(r, GlyphRenderer)]


def _of(d, cls):
    return [r for r in _renderers(d) if type(r.glyph).__name__ == cls]


def _fill(d, cls):
    rs = _of(d, cls)
    assert rs, f"no {cls} drawn: {[type(r.glyph).__name__ for r in _renderers(d)]}"
    return str(rs[0].glyph.fill_color).lower(), rs[0].glyph.fill_alpha


def _notes(d, option="fintensity"):
    return [m for m in d.warnings if f"{option}(" in m]


def _user_scheme(tmp_path, monkeypatch, name, lines):
    monkeypatch.chdir(tmp_path)
    (tmp_path / f"{name}.scheme").write_text(
        "#include s2color\n" + "".join(l + "\n" for l in lines),
        encoding="utf-8")
    return name


_RANGE_PLOT = {"rbar": "VBar", "rarea": "VArea"}


# ---------------------------------------------------------------------------
# The blend and the reader
# ---------------------------------------------------------------------------

class TestTheBlend:
    def test_above_full_divides_and_clamps(self):
        b = G._blend_intensity
        assert b("#1a476f", 1.5) == "#112f4a"
        assert b("#1a476f", 10) == "#03070b"
        assert b("#1a476f", 50) == "#010102"
        assert b("#1a476f", 60) == "#010304"
        assert b("#1a476f", 9999.99) == "#010304"
        assert b("#ffffff", 99.99) == "#030303"

    def test_naturally_white_0_multiplies(self):
        b = G._blend_intensity
        assert b("#1a476f", 0.5, False) == "#0d2438"
        assert b("#1a476f", 1.5, False) == "#276ba7"
        assert b("#1a476f", 0, False) == "#010304"
        assert b("#1a476f", 0.01, False) == "#010304"
        assert b("#ff0000", 0, False) == "#010000"
        assert b("#c86403", 0.01, False) == "#432101"
        assert b("#ffff00", 100, False) == "#ffff00"
        assert b("#ffff00", 0.8, False) == "#cccc00"

    def test_below_full_is_unchanged(self):
        """Guard: the blend towards white dash already drew."""
        b = G._blend_intensity
        assert b("#1a476f", 0.8) == "#486c8c"
        assert b("#1a476f", 0.5) == "#8da3b7"
        assert b("#1a476f", 0) == "#ffffff"
        assert b("#ff0000", 0.5) == "#ff8080"
        assert b("#1a476f", -1) == "#ffffff"
        assert b("notahex", 0.5) == "notahex"


class TestTheFintensityParser:
    def test_numbers_names_and_missing(self):
        want = {"50": 0.5, "150": 1.5, "-5": 0.0, "1d3": 10.0,
                "inten200": 2.0, "max": 9999.99, "full": 1.0,
                "inten50": 0.5, ".": None, "": None}
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            got = {k: G._fintensity_value(k) for k in want}
        for k, v in want.items():
            if v is None:
                assert got[k] is None, k
            else:
                assert got[k] == pytest.approx(v), (k, got[k])
        assert not [w for w in caught if "fintensity(" in str(w.message)]

    def test_an_unknown_name_is_full_with_one_note(self):
        for raw in ("abc", "inten150", "inten55", "INTEN50", "Full", ".a",
                    "()", "x" * 200):
            d = _drawn([plot_for("bar", {"fcolor": "navy",
                                         "fintensity": raw})], "standalone")
            assert _fill(d, "VBar")[0] == "#1a476f", raw
            assert len(_notes(d)) == 1, (raw, d.warnings)


class TestTheSchemeChains:
    def test_intensity_above_full_reaches_the_chains(self):
        props = dict(dr.SchemeParser("s2color")._props)
        props.update({"intensity p1bar": "inten200",
                      "intensity p1area": "150"})
        s = _props_scheme(props)
        assert s.p_bar_intensity[0] == pytest.approx(2.0)
        assert s.p_area_intensity[0] == pytest.approx(1.5)


# ---------------------------------------------------------------------------
# Markers
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", MODES)
class TestMarkersAreOpaque:
    def test_default_markers(self, mode):
        plots = [plot_for(p) for p in ("scatter", "connected", "dot",
                                       "rconnected")]
        for scheme in ("s2color", "stcolor", "s1rcolor", "economist"):
            d = _drawn(plots, mode, scheme)
            sc = _of(d, "Scatter")
            assert len(sc) >= 5, (scheme, len(sc))
            assert [(r.glyph.fill_alpha, r.glyph.line_alpha)
                    for r in sc] == [(1.0, 1.0)] * len(sc), scheme

    def test_a_declared_or_asked_opacity_still_wins(self, mode):
        """Guard: sttrans's %20, %NN and malpha() set the opacity."""
        d = _drawn([plot_for("scatter")], mode, "sttrans")
        assert _of(d, "Scatter")[0].glyph.fill_alpha == pytest.approx(0.2)
        d = _drawn([plot_for("scatter", {"mcolor": "navy%50"})], mode)
        assert _of(d, "Scatter")[0].glyph.fill_alpha == pytest.approx(0.5)
        d = _drawn([plot_for("scatter", {"malpha": "40"})], mode)
        assert _of(d, "Scatter")[0].glyph.fill_alpha == pytest.approx(0.4)


# ---------------------------------------------------------------------------
# Fills
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", MODES)
class TestFillsAreAnOpaqueBlend:
    def test_default_fills(self, mode):
        assert _fill(_drawn([plot_for("bar")], mode), "VBar") == \
            ("#486c8c", 1.0)
        d = _drawn([plot_for("bar"), plot_for("bar", yvar="price")], mode)
        assert [str(r.glyph.fill_color).lower() for r in _of(d, "VBar")] \
            == ["#486c8c", "#a65d62"]
        assert _fill(_drawn([plot_for("bar")], mode, "stcolor"),
                     "VBar")[0] == "#489dff"
        assert _fill(_drawn([plot_for("bar")], mode, "s1rcolor"),
                     "VBar") == ("#cccc00", 1.0)
        assert _fill(_drawn([plot_for("area")], mode), "VArea") == \
            ("#486c8c", 1.0)
        assert _fill(_drawn([plot_for("rbar")], mode), "VBar") == \
            ("#486c8c", 1.0)
        assert _fill(_drawn([plot_for("rarea")], mode), "VArea")[0] == \
            "#486c8c"

    def test_user_colours_take_the_intensity(self, mode):
        for p, o, cls in (("bar", {"fcolor": "yellow"}, "VBar"),
                          ("bar", {"color": "yellow"}, "VBar"),
                          ("bar", {"bfcolor": "yellow"}, "VBar"),
                          ("area", {"fcolor": "yellow"}, "VArea")):
            assert _fill(_drawn([plot_for(p, o)], mode), cls)[0] == \
                "#ffff33", (p, o)
        assert _fill(_drawn([plot_for("rarea", {"color": "red"})], mode),
                     "VArea")[0] == "#ff3333"
        d = _drawn([plot_for("rbar", {"color": "red"})], mode)
        g = _of(d, "VBar")[0].glyph
        assert str(g.fill_color).lower() == "#ff3333"
        assert str(g.line_color).lower() == "#ff0000"

    def test_an_opacity_is_kept_beside_the_blend(self, mode):
        assert _fill(_drawn([plot_for("bar", {"fcolor": "navy%50"})], mode),
                     "VBar") == ("#486c8c", 0.5)
        c, a = _fill(_drawn([plot_for("bar")], mode, "sttrans"), "VBar")
        assert (c, round(a, 6)) == ("#486c8c", 0.2)
        c, a = _fill(_drawn([plot_for("bar", {"fcolor": "navy"})], mode,
                            "sttrans"), "VBar")
        assert (c, round(a, 6)) == ("#486c8c", 0.2)


_MEASURED = {"50": "#8da3b7", "150": "#112f4a", "1000": "#03070b",
             "0": "#ffffff", "-5": "#ffffff", "5000": "#010102",
             "6000": "#010304", "9999": "#010304", "inten200": "#0d2438",
             "max": "#010304", "full": "#1a476f", "inten50": "#8da3b7",
             ".": "#486c8c"}


@pytest.mark.parametrize("mode", MODES)
class TestFintensityIsABlend:
    def test_the_measured_values(self, mode):
        for v, want in _MEASURED.items():
            d = _drawn([plot_for("bar", {"fcolor": "navy",
                                         "fintensity": v})], mode)
            assert _fill(d, "VBar") == (want, 1.0), v
            assert _notes(d) == [], (v, d.warnings)

    def test_an_unknown_intensity_is_full_with_the_note(self, mode):
        for v in ("abc", "inten150", "INTEN50", "Full", ".a"):
            d = _drawn([plot_for("bar", {"fcolor": "navy",
                                         "fintensity": v})], mode)
            assert _fill(d, "VBar")[0] == "#1a476f", v
            notes = _notes(d)
            assert len(notes) == 1 and f"fintensity({v})" in notes[0], notes

    def test_naturally_white_0(self, mode):
        for v, want in (("50", "#0d2438"), ("150", "#276ba7"),
                        ("0", "#010304"), ("1", "#010304")):
            d = _drawn([plot_for("bar", {"fcolor": "navy",
                                         "fintensity": v})], mode, "s1rcolor")
            assert _fill(d, "VBar")[0] == want, v
        d = _drawn([plot_for("bar", {"fcolor": "red", "fintensity": "0"})],
                   mode, "s1rcolor")
        assert _fill(d, "VBar")[0] == "#010000"
        d = _drawn([plot_for("area", {"fcolor": "navy", "fintensity": "50"})],
                   mode, "s1rcolor")
        assert _fill(d, "VArea")[0] == "#0d2438"

    def test_every_fill_type(self, mode):
        for p, cls in (("area", "VArea"), ("rarea", "VArea"), ("rbar", "VBar"),
                       ("histogram", "Quad")):
            d = _drawn([plot_for(p, {"fcolor": "navy", "fintensity": "50"})],
                       mode)
            assert _fill(d, cls)[0] == "#8da3b7", p


@pytest.mark.parametrize("mode", MODES)
class TestCiBandIntensity:
    def test_the_measured_bands(self, mode):
        d = _drawn([plot_for("lfitci", {"fintensity": "150"})], mode)
        assert _fill(d, "VArea")[0] == "#808080"
        d = _drawn([plot_for("lfitci", {"fintensity": "50"})], mode,
                   "s1rcolor")
        assert _fill(d, "VArea")[0] == "#282828"

    def test_the_default_band_and_negative_intensity(self, mode):
        """Guard: the default band and fintensity(-5), white."""
        assert _fill(_drawn([plot_for("lfitci")], mode), "VArea")[0] == \
            "#c0c0c0"
        d = _drawn([plot_for("lfitci", {"fintensity": "-5"})], mode)
        assert _fill(d, "VArea")[0] == "#ffffff"


@pytest.mark.parametrize("mode", MODES)
class TestBrushedFillsKeepTheBlend:
    def test_the_nonselection_copy_has_the_drawn_colour(self, mode):
        for p, opts, cls, want in (
                ("bar", {"fcolor": "navy", "fintensity": "50"}, "VBar",
                 "#8da3b7"),
                ("bar", {"fcolor": "yellow"}, "VBar", "#ffff33"),
                ("area", {"fcolor": "yellow"}, "VArea", "#ffff33"),
                ("histogram", {"fcolor": "red"}, "Quad", "#ff0000"),
                ("rbar", {"color": "red"}, "VBar", "#ff3333")):
            r = _of(_drawn([plot_for(p, opts)], mode), cls)[0]
            assert str(r.glyph.fill_color).lower() == want, p
            for attr in ("nonselection_glyph", "muted_glyph"):
                copy = getattr(r, attr)
                assert str(copy.fill_color).lower() == want, (
                    p, attr, copy.fill_color)
            assert r.nonselection_glyph.fill_alpha != r.glyph.fill_alpha, p


class TestAfterAFilterMove:
    def test_the_served_app_redraws_the_same_colours(self, tmp_path):
        import test_served_linked_views as lv
        graphs = [
            lv._graph("g1", [plot_for("scatter")]),
            lv._graph("g2", [{"type": "bar", "yvar": "mpg",
                              "xvar": "weight", "options": {}}]),
            lv._graph("g3", [{"type": "area", "yvar": "mpg",
                              "xvar": "weight",
                              "options": {"fcolor": "navy",
                                          "fintensity": "50"}}]),
        ]
        spec = lv._spec(graphs, [lv._filter("dropdown")], link="")
        doc = lv._served_doc(tmp_path, spec)
        want = {"Scatter": ("#1a476f", 1.0, 1.0), "VBar": ("#486c8c", 1.0),
                "VArea": ("#8da3b7", 1.0)}

        def styles():
            out = {}
            for r in doc.select({"type": GlyphRenderer}):
                g = r.glyph
                k = type(g).__name__
                if k in want:
                    v = (str(g.fill_color).lower(), g.fill_alpha)
                    if k == "Scatter":
                        v += (g.line_alpha,)
                    out.setdefault(k, set()).add(v)
            return out

        before = styles()
        assert before == {k: {v} for k, v in want.items()}, before
        lv._fire(doc, "foreign", "1")
        assert styles() == before

    def test_no_page_script_writes_a_fill(self):
        """Guard: no page script restyles a fill, so the saved page needs
        no JavaScript twin of the blend."""
        pat = re.compile(r"\.fill_(color|alpha)\s*=(?!=)")
        for name in dir(dr):
            if name.endswith("_JS") and isinstance(getattr(dr, name), str):
                assert not pat.search(getattr(dr, name)), name
        d = _drawn([plot_for("bar"), plot_for("scatter")], "standalone")
        for f in d.figures:
            for m in f.references():
                if isinstance(m, CustomJS):
                    assert not pat.search(m.code), m.code[:200]


@pytest.mark.parametrize("mode", MODES)
class TestGraphBarKeysAreNotRead:
    def test_intensity_bar_and_area_are_ignored(self, tmp_path, monkeypatch,
                                                mode):
        dn = _user_scheme(tmp_path, monkeypatch, "s16dn",
                          ["intensity p1bar inten40",
                           "intensity p1area inten40"])
        assert _fill(_drawn([plot_for("bar")], mode, dn), "VBar")[0] == \
            "#a3b5c5"
        assert _fill(_drawn([plot_for("area")], mode, dn), "VArea")[0] == \
            "#a3b5c5"
        ig = _user_scheme(tmp_path, monkeypatch, "s16ig",
                          ["intensity bar inten40", "intensity area inten40"])
        for p, cls in (("bar", "VBar"), ("area", "VArea")):
            d = _drawn([plot_for(p)], mode, ig)
            assert _fill(d, cls) == ("#486c8c", 1.0), p
            assert not [m for m in d.warnings if "intensity" in m], d.warnings

    def test_the_parser_no_longer_carries_them(self, mode):
        sp = dr.SchemeParser("s2color")
        assert not hasattr(sp, "bar_alpha")
        assert not hasattr(sp, "area_alpha")


@pytest.mark.parametrize("mode", MODES)
class TestTheHistogramUntilS24:
    def test_s1rcolor_is_opaque(self, mode):
        d = _drawn([plot_for("histogram", {"fcolor": "navy"})], mode,
                   "s1rcolor")
        assert _fill(d, "Quad") == ("#1a476f", 1.0)

    def test_s2color_keeps_the_full_colour(self, mode):
        """Guard: s2color's histogram is twoway's full intensity."""
        assert _fill(_drawn([plot_for("histogram")], mode), "Quad") == \
            ("#1a476f", 1.0)
        d = _drawn([plot_for("histogram", {"fcolor": "navy"})], mode)
        assert _fill(d, "Quad") == ("#1a476f", 1.0)


class TestBothModesShareTheCode:
    def test_the_served_mapper_has_the_reader(self):
        from test_scheme_resolution import _served
        _, mod, _ = _served(tp._spec([plot_for("bar")], {}, {}))
        assert "inten200" in mod.SchemeParser._INTENSITY
        assert "max" in mod.SchemeParser._INTENSITY
        assert hasattr(mod.GlyphMapper, "_fintensity_value")


# ---------------------------------------------------------------------------
# The fixture: twoway's SVG for every probe
# ---------------------------------------------------------------------------

_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "intensity_truth.json"
_FIX = (json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
        if _FIXTURE_PATH.exists() else {"_meta": {}, "probes": {}})
_PROBES = _FIX["probes"]
_EXCLUDED = set((_FIX["_meta"].get("excluded") or {}))

#: A probe's command as a dash spec: (plots, scheme, glyph class, attr).
_RX = re.compile(r"^(?:\(?)(\w+)\s+([^,()]*?)(?:,\s*(.*?))?\)?$")
_KIND_GLYPH = {"scatter": "Scatter", "connected": "Scatter",
               "dot": "Scatter", "rconnected": "Scatter", "bar": "VBar",
               "rbar": "VBar", "area": "VArea", "rarea": "VArea",
               "histogram": "Quad", "lfitci": "VArea"}


#: auto's rep78 is the test data's rep.
_VARS = {"rep78": "rep"}


def _opts(text):
    """`fcolor(navy) fintensity(50) lcolor(none)' -> options, lcolor
    dropped (the probes clear the outline only so the fill is legible)."""
    out = {}
    for k, v in re.findall(r"(\w+)\(([^()]*(?:\([^()]*\))?[^()]*)\)",
                           text or ""):
        if k in ("lcolor", "yaxis"):
            continue
        out[k] = v.strip().strip('"')
    return out


def _probe_plots(cmd):
    """The dash plots of a probe's twoway command (one or two layers)."""
    layers = re.findall(r"\(([^()]*(?:\([^()]*\)[^()]*)*)\)", cmd) \
        if cmd.strip().startswith("(") else [cmd]
    plots = []
    for layer in layers:
        head, _, opt = layer.partition(",")
        words = head.split()
        ptype, vars_ = words[0], [w for w in words[1:] if not w.startswith("if")]
        vars_ = [_VARS.get(w, w) for w in vars_
                 if re.fullmatch(r"[A-Za-z_]\w*", w)]
        o = _opts(opt)
        if ptype == "histogram":
            p = {"type": "histogram", "var": "mpg", "options": o}
        elif ptype in ("rbar", "rarea", "rconnected"):
            p = {"type": ptype, "yvar1": "mpg", "yvar2": "price",
                 "xvar": vars_[2] if len(vars_) > 2 else "weight",
                 "options": o}
        else:
            p = {"type": ptype, "yvar": vars_[0], "xvar": vars_[1],
                 "options": o}
        plots.append(p)
    return plots


def _probe_ids():
    return sorted(k for k, v in _PROBES.items()
                  if v.get("owner") != "S24" and k not in _EXCLUDED
                  and v.get("fill"))


class TestTheFixture:
    def test_the_meta_stamp(self):
        """Guard: the fixture is stamped and every probe ran."""
        m = _FIX["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted"):
            assert m.get(k), k
        assert _PROBES and all(v["rc"] == 0 for v in _PROBES.values())

    def test_twoways_notes_are_recorded(self):
        """Guard: twoway notes an unknown intensity name, never `.'."""
        for k in ("fi_abc", "fi_inten150", "fi_INTEN50", "fi_Full",
                  "fi_dota"):
            assert any("not found in class intensity" in n
                       for n in _PROBES[k]["notes"]), k
        for k in ("fi_dot", "fi_full"):
            assert _PROBES[k]["notes"] == [], k


class _Mismatch(Exception):
    """One fixture row that differs; collected, never swallowed: the
    loop that catches it fails naming every such row."""


def _expect(ok, why):
    if not ok:
        raise _Mismatch(why)


def _mismatches(ids, check):
    """``"id: why"`` for each id whose ``check(id)`` raised _Mismatch."""
    bad = []
    for i in ids:
        try:
            check(i)
        except _Mismatch as e:
            bad.append("%s: %s" % (i, str(e).splitlines()[0] if str(e)
                                   else "differs"))
    return bad


@pytest.mark.parametrize("mode", MODES)
class TestStataFills:
    def test_each_probe(self, mode, tmp_path):
        """Every probe; the failing probe ids are listed together."""
        from bokeh.io import curdoc
        pids = _probe_ids()
        assert pids, _FIXTURE_PATH

        def check(pid):
            try:
                with pytest.MonkeyPatch.context() as mp:
                    self._one(pid, mode, tmp_path, mp)
            finally:
                curdoc().clear()
        bad = _mismatches(pids, check)
        assert not bad, "%d of %d probes differ:\n%s" % (
            len(bad), len(pids), "\n".join(bad))

    @staticmethod
    def _one(pid, mode, tmp_path, monkeypatch):
        pr = _PROBES[pid]
        scheme = pr["scheme"]
        if scheme in ("s16up", "s16dn"):
            _user_scheme(tmp_path, monkeypatch, scheme, {
                "s16up": ["intensity p1bar inten200",
                          "intensity p1area 150"],
                "s16dn": ["intensity p1bar inten40",
                          "intensity p1area inten40"]}[scheme])
        plots = _probe_plots(pr["command"])
        d = _drawn(plots, mode, scheme)
        cls = _KIND_GLYPH[plots[0]["type"]]
        rs = _of(d, cls)
        _expect(rs, (pid, [type(r.glyph).__name__ for r in _renderers(d)]))
        if pr.get("fills") and len(pr["fills"]) > 1:
            got = [str(r.glyph.fill_color).lower() for r in rs]
            _expect(got == [c.lower() for c in pr["fills"]], (pid, got))
            return
        g = rs[0].glyph
        _expect(str(g.fill_color).lower() == pr["fill"].lower(), pid)
        want_a = 1.0 if pr.get("opacity") is None else float(pr["opacity"])
        if cls != "VArea" or plots[0]["type"] != "rarea":
            _expect(g.fill_alpha == pytest.approx(want_a), pid)
        if pr.get("stroke"):
            _expect(str(g.line_color).lower() == pr["stroke"].lower(), pid)
