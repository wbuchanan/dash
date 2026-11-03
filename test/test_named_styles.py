"""The named styles p1-p15 (WP-30 P1.14a, section 32).

twoway styles a plot with ``pstyle()``, ``p()``, ``lstyle()``,
``clstyle()``, ``mstyle()``, ``mlstyle()``, ``astyle()``, ``alstyle()``,
``bstyle()`` and ``blstyle()``; dash named every one of them as ignored
(``pstyle()`` was drawn on the four ci fits only).  Each expectation below
is twoway's own, measured in StataNow 19.5 (the plan's E3 and
test/fixtures/named_style_truth.json from
scripts/extract_named_style_truth.do), written as a literal hex or
converted through ``OptionTranslator`` alone -- never through the
``SchemeParser``/``GlyphMapper`` code under test, except where a test says
it holds the bundle against the fixture.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import warnings

import pytest
from bokeh.models import CustomJS, GlyphRenderer

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
import test_scheme_resolution as tsr  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

MODES = tsr.MODES
T = dr.OptionTranslator

_FIXTURE = os.path.join(_HERE, "fixtures", "named_style_truth.json")
with open(_FIXTURE, encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)
CASES = TRUTH["cases"]

#: twoway's colours (stcolor unless named): p1, p3, p4; p3 under s2color;
#: p3's marker under s1mono; p3 and p4 at areastyle's intensity 80.
P1, P3, P4 = "#1a85ff", "#00bf7f", "#ffd400"
S2_P3, MONO_P3 = "#55752f", "#808080"
P3_AREA, P4_AREA, RED_AREA = "#33cc99", "#ffdd33", "#ff3333"
RED, BLACK = "#ff0000", "#000000"
#: twoway's .3 (linewidth p#) and vshortdash (s1mono's p3line) in dash's
#: units.
W03 = T.translate_lwidth(".3")
VSHORT = list(T.translate_lpattern("vshortdash"))


from conftest import render_models  # noqa: E402


def _hex(c):
    return c.lower() if isinstance(c, str) else c


def _draw(plots, scheme="stcolor", mode="standalone"):
    """What *mode* drew for one graph of *plots*: (renderers, notes)."""
    if isinstance(plots, dict):
        plots = [plots]
    d = tsr._draw(tp._spec(list(plots), {"scheme": scheme}, {}), mode)
    rs = [r for f in d.figures for r in f.renderers
          if isinstance(r, GlyphRenderer)]
    return rs, [m for m in d.warnings if m.startswith("dash")]


def _glyphs(plots, kind, scheme="stcolor", mode="standalone"):
    rs, _ = _draw(plots, scheme, mode)
    return [r.glyph for r in rs if type(r.glyph).__name__ == kind]


def _one(plots, kind, scheme="stcolor", mode="standalone"):
    gs = _glyphs(plots, kind, scheme, mode)
    assert gs, f"no {kind} drawn"
    return gs[0]


# ---------------------------------------------------------------------------
# 32-01: the regression tests (each failed at the batch-11 base)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", MODES)
class TestPstyle:
    def test_scatter_pstyle_p3_is_p3(self, mode):
        g = _one(plot_for("scatter", {"pstyle": "p3"}), "Scatter",
                 "s2color", mode)
        assert _hex(g.fill_color) == S2_P3

    def test_line_pstyle_takes_the_connect_chain(self, mode):
        """s1mono's pstyle(p3) line is linestyle p3: black, vshortdash --
        not plot 3's grey solid."""
        g = _one(plot_for("line", {"pstyle": "p3"}), "Line", "s1mono", mode)
        assert (_hex(g.line_color), list(g.line_dash)) == (BLACK, VSHORT)

    def test_bar_pstyle_is_areastyle_p3(self, mode):
        g = _one(plot_for("bar", {"pstyle": "p3"}), "VBar", "stcolor", mode)
        assert (_hex(g.fill_color), _hex(g.line_color)) == (P3_AREA, P3)
        assert g.line_width == pytest.approx(W03)


@pytest.mark.parametrize("mode", MODES)
class TestLstyle:
    def test_s1mono_line_lstyle_p3(self, mode):
        g = _one(plot_for("line", {"lstyle": "p3"}), "Line", "s1mono", mode)
        assert (_hex(g.line_color), list(g.line_dash)) == (BLACK, VSHORT)

    def test_spike_lstyle_reaches_the_outline(self, mode):
        g = _one(plot_for("spike", {"lstyle": "p3"}), "Segment",
                 "stcolor", mode)
        assert _hex(g.line_color) == P3


@pytest.mark.parametrize("mode", MODES)
class TestMstyle:
    def test_s1mono_mstyle_p3_is_a_grey_square(self, mode):
        g = _one(plot_for("scatter", {"mstyle": "p3"}), "Scatter",
                 "s1mono", mode)
        assert (_hex(g.fill_color), g.marker) == (MONO_P3, "square")


@pytest.mark.parametrize("mode", MODES)
class TestMlstyle:
    def test_outline_only(self, mode):
        g = _one(plot_for("scatter", {"mlstyle": "p3"}), "Scatter",
                 "stcolor", mode)
        assert (_hex(g.line_color), _hex(g.fill_color)) == (P3, P1)


@pytest.mark.parametrize("mode", MODES)
class TestAstyleBstyle:
    def test_area_astyle_p3(self, mode):
        g = _one(plot_for("area", {"astyle": "p3"}), "VArea", "stcolor",
                 mode)
        assert _hex(g.fill_color) == P3_AREA

    def test_bar_bstyle_p3(self, mode):
        g = _one(plot_for("bar", {"bstyle": "p3"}), "VBar", "stcolor", mode)
        assert (_hex(g.fill_color), _hex(g.line_color)) == (P3_AREA, P3)

    def test_bar_blstyle_p3_outline_only(self, mode):
        plain = _one(plot_for("bar"), "VBar", "stcolor", mode)
        g = _one(plot_for("bar", {"blstyle": "p3"}), "VBar", "stcolor", mode)
        assert _hex(g.line_color) == P3
        assert _hex(g.fill_color) == _hex(plain.fill_color)


@pytest.mark.parametrize("mode", MODES)
class TestClstyle:
    def test_connected_clstyle_is_the_connecting_line(self, mode):
        g = _one(plot_for("connected", {"clstyle": "p3"}), "Line",
                 "stcolor", mode)
        assert _hex(g.line_color) == P3

    def test_spike_clstyle_is_silent_and_unchanged(self, mode):
        """Guard: clstyle() never reaches a spike (dash.ado clears it off
        the type, and the renderer has no connecting line there)."""
        plain = _one(plot_for("spike"), "Segment", "stcolor", mode)
        rs, notes = _draw(plot_for("spike", {"clstyle": "p3"}), "stcolor",
                          mode)
        [g] = [r.glyph for r in rs if type(r.glyph).__name__ == "Segment"]
        assert _hex(g.line_color) == _hex(plain.line_color)
        assert not [n for n in notes if "clstyle" in n]


@pytest.mark.parametrize("mode", MODES)
class TestFactorOrder:
    """An option wins over a style before it and loses to one after it
    (register P1.14.2; E3)."""

    def test_color_then_mstyle_is_p4(self, mode):
        g = _one(plot_for("scatter", {"color": "red", "mstyle": "p4"}),
                 "Scatter", "stcolor", mode)
        assert _hex(g.fill_color) == P4

    def test_mcolor_then_pstyle_is_red(self, mode):
        g = _one(plot_for("scatter", {"mcolor": "red", "pstyle": "p3"}),
                 "Scatter", "stcolor", mode)
        assert _hex(g.fill_color) == RED

    def test_mlcolor_then_mstyle_keeps_the_red_outline(self, mode):
        g = _one(plot_for("scatter", {"mlcolor": "red", "mstyle": "p4"}),
                 "Scatter", "stcolor", mode)
        assert (_hex(g.fill_color), _hex(g.line_color)) == (P4, RED)

    def test_color_then_astyle_on_area_is_p4(self, mode):
        g = _one(plot_for("area", {"color": "red", "astyle": "p4"}),
                 "VArea", "stcolor", mode)
        assert _hex(g.fill_color) == P4_AREA

    def test_area_color_then_pstyle_is_red(self, mode):
        g = _one(plot_for("area", {"color": "red", "pstyle": "p4"}),
                 "VArea", "stcolor", mode)
        assert _hex(g.fill_color) == RED_AREA

    def test_lwidth_then_lstyle_keeps_the_width(self, mode):
        g = _one(plot_for("line", {"lwidth": "thick", "lstyle": "p3"}),
                 "Line", "stcolor", mode)
        assert _hex(g.line_color) == P3
        assert g.line_width == pytest.approx(T.translate_lwidth("thick"))

    def test_fintensity_then_astyle_keeps_30(self, mode):
        g = _one(plot_for("area", {"fintensity": "30", "astyle": "p4"}),
                 "VArea", "stcolor", mode)
        # p4 (255 212 0) at intensity 30: 255 - (255 - c) * .3.
        assert _hex(g.fill_color) == "#fff2b3"

    def test_dropline_color_then_pstyle_is_red(self, mode):
        rs, _ = _draw(plot_for("dropline", {"mcolor": "red",
                                            "pstyle": "p4"}), "stcolor", mode)
        colours = {type(r.glyph).__name__: _hex(r.glyph.line_color)
                   for r in rs}
        assert colours == {"Segment": RED, "Scatter": RED}

    def test_scatteri_mcolor_then_pstyle_is_red(self, mode):
        g = _one(plot_for("scatteri", {"mcolor": "red", "pstyle": "p3"}),
                 "Scatter", "stcolor", mode)
        assert _hex(g.fill_color) == RED

    def test_pcarrow_lcolor_then_pstyle_is_red(self, mode):
        g = _one(plot_for("pcarrow", {"lcolor": "red", "pstyle": "p3"}),
                 "Segment", "stcolor", mode)
        assert _hex(g.line_color) == RED


@pytest.mark.parametrize("mode", MODES)
class TestP:
    def test_p_overrides_mcolor(self, mode):
        g = _one(plot_for("scatter", {"mcolor": "red", "p": "p3"}),
                 "Scatter", "stcolor", mode)
        assert _hex(g.fill_color) == P3

    def test_p_on_lfitci_draws_p3(self, mode):
        rs, _ = _draw(plot_for("lfitci", {"p": "p3"}), "stcolor", mode)
        [band] = [r.glyph for r in rs if type(r.glyph).__name__ == "VArea"]
        [line] = [r.glyph for r in rs if type(r.glyph).__name__ == "Line"]
        assert (_hex(band.fill_color), _hex(line.line_color)) == (P3_AREA, P3)


@pytest.mark.parametrize("mode", MODES)
class TestNumbering:
    def test_the_next_layer_keeps_p2(self, mode):
        """(scatter, pstyle(p3)) (scatter): p3 then p2 (E3)."""
        gs = _glyphs([plot_for("scatter", {"pstyle": "p3"}),
                      plot_for("scatter")], "Scatter", "s2color", mode)
        assert [_hex(g.fill_color) for g in gs] == [S2_P3, "#90353b"]

    def test_scatteri_and_function_take_the_index(self, mode):
        rs, _ = _draw([plot_for("scatteri", {"pstyle": "p3"}),
                       plot_for("function", {"pstyle": "p4"})], "stcolor",
                      mode)
        got = [(type(r.glyph).__name__,
                _hex(getattr(r.glyph, "fill_color", None)
                     if type(r.glyph).__name__ == "Scatter"
                     else r.glyph.line_color)) for r in rs]
        assert got == [("Scatter", P3), ("Line", P4)]

    def test_pci_and_pcarrowi_take_the_index(self, mode):
        rs, _ = _draw([plot_for("pci", {"pstyle": "p5"}),
                       plot_for("pcarrowi", {"pstyle": "p6"})], "stcolor",
                      mode)
        got = [_hex(r.glyph.line_color) for r in rs
               if type(r.glyph).__name__ == "Segment"]
        # stcolor's p5 and p6 (measured N08).
        exp = [_rgb(CASES["N08"]["plots"][k]["al"]) for k in ("1", "2")]
        assert got == exp


@pytest.mark.parametrize("mode", MODES)
class TestLists:
    def test_two_y_split(self, mode):
        """The spec objects dash.ado writes for scatter y1 y2 x,
        pstyle(p3 p4) draw p3 then p4 (N02)."""
        gs = _glyphs([plot_for("scatter", {"pstyle": "p3"}),
                      plot_for("scatter", {"pstyle": "p4"},
                               yvar="price")], "Scatter", "stcolor", mode)
        assert [_hex(g.fill_color) for g in gs] == [P3, P4]


_NOTE = ("dash: named style bogus not found in class linestyle, default "
         "attributes used")


@pytest.mark.parametrize("mode", MODES)
class TestOtherNames:
    def test_noted_once_and_drawn_as_the_layer(self, mode):
        # Flipped (WP-30 P1.14b): "noted, drawn as the layer's p1" was
        # wrong because twoway draws lstyle(refline) as refline, silently
        # (stcolor: black at .3; plan E9.1); D-32b's interim rule retired.
        rs, notes = _draw(plot_for("line", {"lstyle": "refline"}),
                          "stcolor", mode)
        assert not [n for n in notes if "refline" in n], notes
        [g] = [r.glyph for r in rs]
        assert _hex(g.line_color) == BLACK
        assert g.line_width == pytest.approx(W03)

    def test_unused_option_is_silent(self, mode):
        """M6: lstyle() on scatter is a role scatter does not draw."""
        # Flipped (WP-30 P1.14b): "silent" was wrong because twoway notes
        # an unknown name even on a role the layer does not draw
        # (`scatter, lstyle(bogus)', plan E9.4): once, in its words.
        _, notes = _draw(plot_for("scatter", {"lstyle": "bogus"}),
                         "stcolor", mode)
        assert [n for n in notes if "bogus" in n] == [_NOTE], notes


class TestAfterAFilterMove:
    def test_served_style_survives_a_move(self, tmp_path):
        import test_served_linked_views as lv
        spec = lv._spec([lv._graph("g1", plots=[
            plot_for("scatter", {"pstyle": "p3"})], scheme="stcolor")],
            [lv._filter("range")], link="")
        doc = lv._served_doc(tmp_path, spec)

        def look():
            [r] = [r for r in doc.select({"type": GlyphRenderer})
                   if type(r.glyph).__name__ == "Scatter"]
            return _hex(r.glyph.fill_color), lv._drawn_served(r)

        before = look()
        lv._fire(doc, "price", (4000.0, 5000.0))
        after = look()
        assert before[0] == after[0] == P3
        assert before[1] != after[1]

    def test_no_page_script_writes_a_style(self):
        """Guard (TR-32.13): no saved-page script assigns a glyph style, so
        the style a page is built with is the one it keeps."""
        pat = re.compile(r"\.(line_color|fill_color|line_dash|line_width|"
                         r"marker|size)\s*=[^=]")
        texts = [v for k, v in vars(dr).items()
                 if k.endswith("_JS") and isinstance(v, str)]
        # The page is built: its document holds the page's scripts.
        r, _, _page = tp._standalone_page(tp._spec(
            [plot_for("scatter", {"pstyle": "p3"})], {"scheme": "stcolor"},
            {}))
        for f in r.figures.values():
            texts += [m.code for m in f.document.select({"type": CustomJS})]
        # WP-32 (maintainer ruling over WP-29 BR-07.4): a colorvar() key's
        # level lines are recoloured over the kept rows after a move, as
        # twoway colours them -- a colour level, not a named style.
        relevel = dr._DASH_CVAR_RELEVEL_JS
        assert {m.group(1) for m in pat.finditer(relevel)} == {"line_color"}
        lvl = "r.glyph.line_color = colour;"
        assert relevel.count(lvl) == len(list(pat.finditer(relevel)))
        texts = [t.replace(lvl, "") for t in texts]
        # WP-42 LT-22 (the same ruling): contourline's level legend keys
        # the kept rows' cuts after a move, each key its level's line
        # colour and width (dash_contourline_legend) -- a level, not a
        # named style.
        lt22 = ("if (g.line_color !== c) g.line_color = c;",
                "if (g.line_width !== w) g.line_width = w;")
        assert all(dr._FILTER_JS.count(w) == 1 for w in lt22)
        for w in lt22:
            texts = [t.replace(w, "") for t in texts]
        assert texts and not [t for t in texts if pat.search(t)]


class TestLegendAndStale:
    @pytest.mark.parametrize("mode", MODES)
    def test_the_legend_key_is_the_named_style(self, mode):
        d = tsr._draw(tp._spec([plot_for("scatter", {"pstyle": "p3"})],
                               {"scheme": "stcolor"}, {}), mode)
        legends = [lg for f in d.figures for lg in f.legend]
        keyed = [r for lg in legends for it in lg.items
                 for r in it.renderers]
        assert keyed and _hex(keyed[0].glyph.fill_color) == P3

    def test_a_computed_layer_keeps_its_style_on_the_stale_cue(self,
                                                               tmp_path):
        """Saved only: the stale cue is the saved page's (WP-29 P0.17)."""
        import test_served_linked_views as lv
        from test_adversarial_matrix import _write_inputs
        spec = lv._spec([lv._graph("g1", plots=[
            plot_for("lfit", {"lstyle": "p3"})], scheme="stcolor")],
            [lv._filter("range")], link="")
        sp, dp = _write_inputs(tmp_path, spec)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = dr.DashRenderer(sp, dp)
            render_models(r)
        [line] = [rr for f in r.figures.values() for rr in f.renderers
                  if isinstance(rr, GlyphRenderer)
                  and type(rr.glyph).__name__ == "Line"]
        assert _hex(line.muted_glyph.line_color) == P3


@pytest.mark.parametrize("mode", MODES)
class TestColorvar:
    def test_colorvar_keeps_its_mapping(self, mode):
        """Guard: a colorvar() layer's colours stay mapped under
        pstyle()."""
        g = _one(plot_for("scatter", {"colorvar": "price", "pstyle": "p3"}),
                 "Scatter", "stcolor", mode)
        assert not isinstance(g.fill_color, str)


@pytest.mark.parametrize("mode", MODES)
class TestBrushedAndMutedCopies:
    def test_the_copies_carry_the_named_style(self, mode):
        """S08's sync (A37) gives the nonselection and muted copies the
        named style's values, the restyle at a mapper site included."""
        cases = [("scatter", {"pstyle": "p3"}, "s2color", "Scatter",
                  ("fill_color", "marker", "size")),
                 ("line", {"lstyle": "p3"}, "s1mono", "Line",
                  ("line_color", "line_width", "line_dash")),
                 ("bar", {"pstyle": "p3"}, "stcolor", "VBar",
                  ("fill_color",))]
        bad = []
        for ptype, opts, scheme, kind, attrs in cases:
            rs, _ = _draw(plot_for(ptype, opts), scheme, mode)
            [r] = [r for r in rs if type(r.glyph).__name__ == kind]
            for copy in ("nonselection_glyph", "muted_glyph"):
                c = getattr(r, copy)
                for a in attrs:
                    if getattr(c, a) != getattr(r.glyph, a):
                        bad.append((ptype, copy, a))
            if ptype == "line" and list(r.glyph.line_dash) != VSHORT:
                bad.append((ptype, "glyph", "line_dash"))
            if ptype == "bar" and _hex(r.glyph.fill_color) != P3_AREA:
                bad.append((ptype, "glyph", "fill_color"))
            ns = r.nonselection_glyph
            a = "fill_alpha" if kind != "Line" else "line_alpha"
            if getattr(ns, a) == getattr(r.glyph, a):
                bad.append((ptype, "nonselection", a))
        assert not bad


_HOSTILE = ["{bf:x}", '"p3"', "`p3'", "$HOME", "../x", "p3;rm -rf /",
            "p３", "p03", "P3", " "]


@pytest.mark.parametrize("mode", MODES)
class TestAdversarial:
    def test_hostile_names_are_noted_shortened_and_inert(self, mode):
        """Every name outside p1-p15 is drawn as the layer and, unless
        blank, noted once with the name shown printable."""
        # Flipped (WP-30 P1.14b): D-32b's "dash: mstyle(...)" text was
        # wrong because the note is now twoway's "named style ... not found
        # in class markerstyle" (D-36d), and '"p3"' is p3, silently, as
        # twoway unwraps one pair of quotes (D-36j, plan E9.6).
        bad = []
        for name in _HOSTILE:
            rs, notes = _draw(plot_for("scatter", {"mstyle": name}),
                              "stcolor", mode)
            g = [r.glyph for r in rs][0]
            if _hex(g.fill_color) != (P3 if name == '"p3"' else P1):
                bad.append((name, g.fill_color))
            mine = [n for n in notes if n.startswith("dash: named style")]
            if len(mine) != (0 if not name.strip() or name == '"p3"'
                             else 1):
                bad.append((name, mine))
            if any(len(n) > 200 or any(ord(ch) < 32 for ch in n)
                   for n in mine):
                bad.append((name, "long or control"))
        assert not bad

    def test_a_huge_name_is_bounded_in_time(self, mode):
        name = "p" * 100_000
        t0 = time.monotonic()
        _, notes = _draw(plot_for("scatter", {"pstyle": name}), "stcolor",
                         mode)
        assert time.monotonic() - t0 < 2.0 + (3.0 if mode == "served" else 0)
        # Flipped (WP-30 P1.14b): the "dash: pstyle(" prefix was wrong
        # because the note is twoway's "named style ..." (D-36d).
        [n] = [n for n in notes if n.startswith("dash: named style")]
        assert len(n) < 200


class TestTheHelp:
    _HELP = open(os.path.join(os.path.dirname(_HERE), "dash.sthlp"),
                 encoding="utf-8").read()

    def test_the_named_styles_paragraph_states_the_order(self):
        i = self._HELP.index("{marker namedstyles}")
        para = self._HELP[i:self._HELP.index("{marker scheme}", i)]
        for needle in ("mcolor(red) pstyle(p3)", "color(red) mstyle(p4)",
                       "{cmd:p()}", "p1", "p15"):
            assert needle in para, needle

    def test_2282_no_longer_says_p_is_pstyle(self):
        assert "{cmd:p()} is {cmd:pstyle()}" not in self._HELP
        assert "p() is pstyle()" not in self._HELP


# ---------------------------------------------------------------------------
# 32-03: the fixture-driven tests
# ---------------------------------------------------------------------------

def _rgb(s):
    """``"0 191 127"`` -> ``"#00bf7f"``."""
    return "#%02x%02x%02x" % tuple(int(float(v)) for v in s.split())


def _blend(hexval, f):
    rgb = [int(hexval[k:k + 2], 16) for k in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(
        int(255 - (255 - c) * f + 0.5) for c in rgb)


class TestTheFixture:
    def test_meta_is_stamped(self):
        m = TRUTH["_meta"]
        assert all(m.get(k) for k in ("stata_version", "born_date",
                                      "dash_commit", "extracted"))

    def test_every_shipped_scheme_is_recorded(self):
        assert set(TRUTH["schemes"]) == set(dr.SchemeParser._BUILTIN_NAMES)

    def test_twoways_notes_are_recorded(self):
        """twoway notes an unknown seriesstyle (U rows) and refuses pst()
        (A11)."""
        assert CASES["U-scatter-pstyle-bogus"]["notes"]
        assert CASES["A11"]["rc"] == 198


class TestStyleBundle:
    def test_against_stata(self):
        """Every scheme's p1-p15 bundles equal twoway's seriesstyle p#
        (grid B), one loop over the 390 rows."""
        bad = []
        for cid, c in CASES.items():
            if not cid.startswith("B-"):
                continue
            scheme, k = cid[2:].rsplit("-p", 1)
            sp = dr.SchemeParser(scheme)
            name = "p" + k
            rec = c["plots"]["1"]
            m = sp.style_bundle("marker", name)
            ln = sp.style_bundle("line", name)
            ar = sp.style_bundle("area", name)
            want = {
                "marker.fill": _rgb(rec["mf"]),
                "marker.line": _rgb(rec["ml"]),
                "marker.symbol": T.translate_msymbol(rec["ms"]),
                "marker.size": round(T.translate_msize(rec["msz"]), 3),
                "marker.line_width": round(T.translate_lwidth(rec["mlw"]), 3),
                "line.line": _rgb(rec["lc"]),
                "line.line_width": round(T.translate_lwidth(rec["lw"]), 3),
                "line.line_dash": list(T.translate_lpattern(rec["lp"])),
                "area.fill": _rgb(rec["af"]),
                "area.intensity": round(float(rec["ai"]) / 100.0, 3),
                "area.line": _rgb(rec["al"]),
                "area.line_width": round(T.translate_lwidth(rec["alw"]), 3),
                "area.line_dash": list(T.translate_lpattern(rec["alp"])),
            }
            got = {
                "marker.fill": _hex(m["fill"]),
                "marker.line": _hex(m["line"]),
                "marker.symbol": m["symbol"],
                "marker.size": round(m["size"], 3),
                "marker.line_width": round(m["line_width"], 3),
                "line.line": _hex(ln["line"]),
                "line.line_width": round(ln["line_width"], 3),
                "line.line_dash": list(ln["line_dash"]),
                "area.fill": _hex(ar["fill"]),
                "area.intensity": round(ar["intensity"], 3),
                "area.line": _hex(ar["line"]),
                "area.line_width": round(ar["line_width"] or 0.0, 3),
                "area.line_dash": list(ar["line_dash"]),
            }
            for key in want:
                if want[key] != got[key]:
                    bad.append((cid, key, want[key], got[key]))
        assert not bad, "\n".join(map(str, bad[:40])) + f"\n({len(bad)})"

    def test_the_marker_bundle_is_the_scatter_default(self):
        """The marker bundle is what map_scatter draws at that index."""
        bad = []
        for scheme in sorted(dr.SchemeParser._BUILTIN_NAMES):
            sp = dr.SchemeParser(scheme)
            for k in range(15):
                b = sp.style_bundle("marker", "p%d" % (k + 1))
                exp = (sp.default_color(k, "scatter"),
                       sp.default_markline(k)[0], sp.default_symbol(k),
                       sp.default_marker_size(k))
                if (b["fill"], b["line"], b["symbol"], b["size"]) != exp:
                    bad.append((scheme, k))
        assert not bad

    def test_names_are_exact(self):
        # Flipped (WP-30 P1.14b): None for a name outside p1-p15 was wrong
        # because twoway draws it in the class's default attributes (the
        # foreground line, plan E9.3); only a blank name or an unknown
        # class gives None.
        sp = dr.SchemeParser("stcolor")
        fg = sp.style_bundle("line", "foreground")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for name in ("P3", "p16", "p03", "p 3", "p0", "p3x"):
                assert sp.style_bundle("line", name) == fg, name
        assert sp.style_bundle("line", "") is None
        assert sp.style_bundle("line", " p15 ") is not None
        assert sp.style_bundle("nonsense", "p3") is None


#: R-grid rows dash does not draw as twoway does, each for a filed reason.
# Flipped (WP-32): area and rarea's lstyle(), alstyle() and blstyle()
# were excluded (P2.12), which was wrong: twoway draws the area's outline
# in the named line style (test/fixtures/noted_option_truth.json), and
# dash now does (BUGS.md "Options twoway draws that dash still names").
# Flipped (WP-32): the pc arrowheads' mstyle() and mlstyle() were
# excluded (P2.8), which was wrong: twoway strokes the heads in the named
# style (noted_option_truth.json), and dash now does.
_ROLE_EXCLUDED: dict = {}
_CL_TYPES = set("line connected lfit qfit fpfit lpoly lowess mspline mband "
                "kdensity function tsline lfitci qfitci lpolyci "
                "fpfitci".split())
_OPTS = ("pstyle", "p", "lstyle", "clstyle", "mstyle", "mlstyle", "astyle",
         "alstyle", "bstyle", "blstyle")


def _drawn_colours(fig):
    out = set()
    for r in fig.renderers:
        if not isinstance(r, GlyphRenderer):
            continue
        g = r.glyph
        for c, a, w in (("line_color", "line_alpha", "line_width"),
                        ("fill_color", "fill_alpha", None)):
            v = getattr(g, c, None)
            if isinstance(v, str) and getattr(g, a, 1) not in (0, 0.0) and (
                    w is None or getattr(g, w, 1)):
                out.add(v.lower())
    return out


class TestRoles:
    def test_against_stata(self):
        """Each type takes each style on the line twoway styles with it
        (grid R, saved): a p3 colour the style brings is drawn exactly when
        twoway's SVG draws it.  One page holds thirty rows; a colour
        either side draws with no style is not evidence."""
        bad = []
        for scheme in ("stcolor", "s1mono"):
            b = CASES[f"B-{scheme}-p3"]["plots"]["1"]
            p3 = {_rgb(b["mf"]), _rgb(b["ml"]), _rgb(b["lc"]),
                  _rgb(b["al"]), _blend(_rgb(b["af"]),
                                        float(b["ai"]) / 100)}
            types = sorted({cid.split("-")[2] for cid in CASES
                            if cid.startswith(f"R-{scheme}-")})
            graphs = [(f"g_{t}_none", [plot_for(t)], {"scheme": scheme})
                      for t in types]
            for t in types:
                for o in _OPTS:
                    if (o == "clstyle" and t not in _CL_TYPES) or (
                            (t, o) in _ROLE_EXCLUDED):
                        continue
                    graphs.append((f"g_{t}_{o}", [plot_for(t, {o: "p3"})],
                                   {"scheme": scheme}))
            figs = {}
            for i in range(0, len(graphs), 30):      # within the page limits
                r, _ = tp._standalone(tp._spec(graphs=graphs[i:i + 30]))
                figs.update(r.figures)
            for name, _plots, _go in graphs:
                _, t, o = name.split("_")
                if o == "none":
                    continue
                none = CASES[f"R-{scheme}-{t}-none"]["svg"]
                base = {h for h, _ in none["strokes"] + none["fills"]}
                # A colour either side draws without the style tells
                # nothing about where the style went.
                info = p3 - base - _drawn_colours(figs[f"g_{t}_none"])
                if not info:
                    continue
                row = CASES[f"R-{scheme}-{t}-{o}"]["svg"]
                tw = bool(info & {h for h, _ in row["strokes"]
                                  + row["fills"]})
                da = bool(info & _drawn_colours(figs[name]))
                if tw != da:
                    bad.append((scheme, t, o, tw, da))
        assert not bad, "\n".join(map(str, bad))


def _f_options(cmd):
    """The options dash.ado writes for a fixture command's one layer."""
    opts = {}
    for k, v in re.findall(r"(\w+)\(([^)]*)\)", cmd.split(",", 1)[1]):
        opts.setdefault(k, v) if k == "p" else opts.__setitem__(k, v)
    if "p" in opts:
        for k in list(opts):
            if k not in ("p", "mlabel", "connect", "cmissing"):
                del opts[k]
    return opts


#: Record field -> (glyph class, attribute, how) for the rows compared.
_F_FIELDS = {
    "scatter": [("1", "mf", "Scatter", "fill_color"),
                ("1", "ml", "Scatter", "line_color")],
    "line": [("1", "lc", "Line", "line_color")],
    "connected": [("1", "lc", "Line", "line_color"),
                  ("1", "mf", "Scatter", "fill_color")],
    "area": [("1", "af+", "VArea", "fill_color")],
    "bar": [("1", "af+", "VBar", "fill_color"),
            ("1", "al", "VBar", "line_color")],
    "spike": [("1", "al", "Segment", "line_color")],
    "rcap": [("1", "al", "Segment", "line_color")],
    "dropline": [("1", "mf", "Scatter", "fill_color")],
    "lfitci": [("1", "af+", "VArea", "fill_color"),
               ("2", "lc", "Line", "line_color")],
}


def _measured_rows(prefix, mode):
    bad = []
    for cid, c in sorted(CASES.items()):
        if not re.fullmatch(prefix + r"\d\d", cid) or c["rc"]:
            continue
        cmd = c["cmd"]
        t = cmd.split()[0]
        if t not in _F_FIELDS:
            continue
        rs, _ = _draw(plot_for(t, _f_options(cmd)), c["scheme"], mode)
        for k, field, kind, attr in _F_FIELDS[t]:
            rec = c["plots"][k]
            want = (_blend(_rgb(rec["af"]), float(rec["ai"]) / 100)
                    if field == "af+" else _rgb(rec[field]))
            got = [_hex(getattr(r.glyph, attr)) for r in rs
                   if type(r.glyph).__name__ == kind]
            if not got or got[0] != want:
                bad.append((cid, cmd, field, want, got[:1]))
    return bad


@pytest.mark.parametrize("mode", MODES)
class TestMeasuredRows:
    def test_each_factor_order_row(self, mode):
        bad = _measured_rows("F", mode)
        assert not bad, "\n".join(map(str, bad))

    def test_each_p_row(self, mode):
        bad = _measured_rows("P", mode)
        assert not bad, "\n".join(map(str, bad))


class TestPlanUnits:
    def _m(self):
        return dr.GlyphMapper(scheme=dr.SchemeParser("stcolor"))

    def test_shadowed_options_are_dropped(self):
        m = self._m()
        o = {"color": "red", "mstyle": "p4", "mlcolor": "blue"}
        assert m._style_options(o, ("marker", "mline")) == {
            "mstyle": "p4", "mlcolor": "blue"}
        # mcolor() shadowed on the outline alone fills only.
        o = {"mcolor": "red", "mlstyle": "p3"}
        assert m._style_options(o, ("marker", "mline")) == {
            "mlstyle": "p3", "mfcolor": "red"}
        # dropline's mcolor() on its drop: no role there, kept unless
        # shadowed everywhere.
        assert "mcolor" in m._style_options({"mcolor": "red",
                                             "lstyle": "p3"}, ("aline",))
        plain = {"mcolor": "red"}
        assert m._style_options(plain, ("marker",)) is plain

    def test_only_named_roles_change(self):
        from bokeh.plotting import figure
        m = self._m()
        r = figure().scatter(x=[1], y=[1], fill_color="#123456",
                             line_color="#654321")
        m._style_restyle(r, {"mlstyle": "p3"}, ("marker", "mline"))
        assert (_hex(r.glyph.fill_color), _hex(r.glyph.line_color)) == (
            "#123456", P3)
        r.glyph.line_color = "#000001"
        m._style_restyle(r, {"mlstyle": "p3"}, ("mline",))
        assert r.glyph.line_color == "#000001"     # once per role

    def test_style_value_falls_back(self):
        m = self._m()
        assert m._style_value({}, "area", "fill", "x") == "x"
        assert m._style_value({"astyle": "p3"}, "area", "fill", "x") == P3
        assert m._style_value({"astyle": "p3"}, "line", "line", "x") == "x"


#: One corpus case per plot type, drawn with the plan bypassed and not.
def _corpus_sample():
    seen, out = set(), []
    for ps in tp.CORPUS:
        spec = ps.values[1]
        types = {p.get("type") for g in spec.get("graphs", [])
                 for p in g.get("plots", [])}
        if types - seen:
            seen |= types
            out.append(ps)
    return out


class TestTheEmptyPlanIsInert:
    def test_the_corpus_draws_the_same_with_the_plan_bypassed(self,
                                                            monkeypatch):
        """No corpus case but section 32's own holds a style key, and a
        case of every plot type draws the same saved page with _style_plan
        forced to None (TR-32.16a).  The served app copies GlyphMapper by
        source, so the patch cannot reach it; its identity is the parity
        corpus's (test_mode_parity) with no style key present."""
        keys = {k for k, v in dr.GlyphMapper._STYLE_FACTORS
                if isinstance(v, dict)}
        # WP-30 P1.14b adds section 36's two cases (other named styles).
        own = {"named styles p1-p15", "p() and the plot index",
               "named styles on a ci fit", "other named styles",
               "an unknown named style",
               # WP-31 E10 adds section 44's style-file case.
               "pstyle(fpall) and lstyle(refline) from style files "
               "(WP-31 E10)"}
        holders = {ps.values[0] for ps in tp.CORPUS
                   for g in ps.values[1].get("graphs", [])
                   for p in g.get("plots", [])
                   if keys & set(p.get("options", {}))}
        assert holders <= own
        from test_varlist_expansion import normalise_bokeh_html

        def both(spec):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                _, page, _ = tsr._standalone(spec)
            return normalise_bokeh_html(page)

        sample = [ps for ps in _corpus_sample() if ps.values[0] not in own]
        first = {ps.values[0]: both(ps.values[1]) for ps in sample}
        monkeypatch.setattr(dr.GlyphMapper, "_style_plan",
                            lambda self, options: None)
        diff = [ps.values[0] for ps in sample
                if both(ps.values[1]) != first[ps.values[0]]]
        assert not diff
