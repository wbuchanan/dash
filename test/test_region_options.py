"""plotregion()/graphregion() read as twoway's region parser reads them
(WP-30 P1.20a, section 38): the reader's units and both modes.

The defect: dash read only color()/fcolor(), lcolor() and lwidth() of a
region, by full name and with a regular expression, so ``c(red)`` drew
nothing, ``none`` drew black, ``%NN`` was dropped, ``style()``,
``lstyle()``, ``lpattern()`` and the graph region's outline were ignored,
and ``bgcolor()`` coloured the graph region.  twoway's parser is
``_fr_area_parse_and_log.ado`` (E3): each sub-option at every spelling
from its capitals, applied in a fixed order whatever the typed order.
twoway's drawing (E4) is checked probe by probe in test_region_truth.py;
here are the reader's own branches, the notes, the canvas order (IR-2:
bgcolor() lies under the graph region), filter moves, hostile text and the
empty path.
"""

import json
import os
import re
import sys
import warnings

import pytest
from bokeh.models import Select
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_S2 = dr.SchemeParser("s2color")
_BASE = {"fill": "#ffffff", "fill_alpha": 1.0, "line": "#ffffff",
         "line_alpha": 1.0, "line_width": 0.768, "line_dash": []}
_HEX = re.compile(r"#[0-9a-f]{6}")


def _spec(go, n=1, **bo):
    return tp._spec(graphs=[(f"g{i}", [plot_for("scatter")], dict(go))
                            for i in range(n)], build_options=bo)


def _figs(mode, spec):
    if mode == "saved":
        r, caught = tp._standalone(spec)
        roots = [r._last_layout_root]
    else:
        doc, caught = tp._served(spec)
        roots = doc.roots
    return [f for root in roots for f in root.select({"type": figure})], caught


def _region(f):
    return (f.background_fill_color, f.border_fill_color,
            f.outline_line_color, f.outline_line_alpha, f.outline_line_width,
            list(f.outline_line_dash), f.border_line_color,
            f.border_line_width)


class TestTheSpec:
    def test_abbreviations_read_as_full_names(self):
        s, named = dr._dash_region_spec("fc(red) lc(navy) lw(thick) lp(dash)",
                                        "plotregion", _BASE, _S2, 4.0)
        assert (s["fill"], s["line"]) == ("#ff0000", "#1a476f")
        assert s["line_width"] == dr.OptionTranslator.translate_lwidth("thick")
        assert s["line_dash"] == dr.OptionTranslator.translate_lpattern("dash")
        assert named == []

    def test_a_wrong_case_none_is_black_with_a_note(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            s, _ = dr._dash_region_spec("fcolor(NONE)", "plotregion", _BASE,
                                        _S2, 4.0)
        assert s["fill"] == "#000000"
        # Flipped: an unknown colour is noted in twoway's words, naming the
        # style, not the option (74050cb).
        assert any("named style NONE not found in class color"
                   in str(x.message) for x in w)

    def test_a_bad_width_or_pattern_keeps_the_default_with_a_note(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            s, _ = dr._dash_region_spec("lwidth(abc) lpattern(bogus)",
                                        "plotregion", _BASE, _S2, 4.0)
        assert (s["line_width"], s["line_dash"]) == (0.768, [])
        msgs = " ".join(str(x.message) for x in w)
        assert "plotregion(lwidth(abc))" in msgs
        assert "plotregion(lpattern(bogus))" in msgs

    def test_what_is_named(self):
        """Flipped (WP-30 P1.20b): plotregion's ilcolor() and margin() were
        named as not drawn; that was wrong because twoway draws them and
        dash now does (margin_truth.json).  graphregion's stay named.

        Flipped (WP-31 D11): shadestyle(), intensity(), marginonly and
        graphregion's margin() were named; that was wrong because twoway
        draws them and dash now does (region_remainder_truth.json): only
        lalign() and the graph region's inner outline stay named."""
        _, named = dr._dash_region_spec(
            "lalign(inside) ilcolor(red) margin(zero) shadestyle(x) "
            "intensity(50) marginonly", "plotregion", _BASE, _S2, 4.0)
        assert named == ["lalign(inside)"]
        _, named = dr._dash_region_spec(
            "lalign(inside) ilcolor(red) margin(zero) marginonly",
            "graphregion", _BASE, _S2, 4.0)
        assert named == ["lalign(inside)", "ilcolor(red)"]
        _, named = dr._dash_region_spec(" ".join(["lalign(1)"] * 25),
                                        "plotregion", _BASE, _S2, 4.0)
        assert named == ["lalign(1)"] * 10 + ["(+15 more)"]


class TestTheBlend:
    def test_over_under(self):
        assert dr._dash_region_blend("#ff0000", 0.5, "#0000ff") == "#800080"
        assert dr._dash_region_blend("#ff0000", None, "#0000ff") == "#ff0000"
        assert dr._dash_region_blend("#ff0000", 1.0, "#0000ff") == "#ff0000"
        with pytest.raises(ValueError):
            dr._dash_region_blend("red", 0.5, "#0000ff")


class TestTheEmptyPathIsInert:
    def test_untouched(self):
        fig = figure()
        _S2.apply_to_figure(fig)
        before = {k: getattr(fig, k) for k in fig.properties()
                  if k.startswith(("background_fill", "border_",
                                   "outline_line"))}
        dr._dash_apply_regions(fig, {"title": "x", "plotregion": "  "}, _S2)
        assert {k: getattr(fig, k) for k in before} == before


class TestBothModes:
    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_one_note_per_region(self, mode):
        go = {"plotregion": "lalign(inside) ifcolor(red)",
              "graphregion": "margin(zero)"}
        _, caught = _figs(mode, _spec(go))
        notes = [c for c in caught if "region() sub-option" in c]
        # Flipped (WP-30 P1.20b): ifcolor(red) was named; that was wrong
        # because twoway draws the plot region's inner box, and dash does.
        # Flipped (WP-31 D11): graphregion(margin(zero)) was named; that was
        # wrong because twoway draws it, and dash does (_dash_graph_margin).
        assert sorted(notes) == [
            "dash: plotregion() sub-option(s) not implemented and ignored: "
            "lalign(inside)"], notes


_GO = {"plotregion": "c(red) lc(navy) lp(dash) lw(thick)",
       "graphregion": "fcolor(red%50) lcolor(blue)", "bgcolor": "blue"}


class TestAfterAFilterMove:
    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_regions_survive(self, mode):
        spec = _spec(_GO, filter="foreign, type(dropdown)")
        if mode == "saved":
            import test_saved_filter_layers as sf
            r = sf._render(spec)
            figs = list(r._last_layout_root.select({"type": figure}))
            before = [_region(f) for f in figs]
            sf._move(r, ("Select", "Foreign"))
        else:
            doc, _ = tp._served(spec)
            figs = [f for root in doc.roots
                    for f in root.select({"type": figure})]
            before = [_region(f) for f in figs]
            w = [x for x in tp._widgets_of(doc) if isinstance(x, Select)][0]
            tp._fire(w, [v for v, lab in w.options if lab == "Foreign"][0])
        after = [_region(f) for f in figs]
        assert before == after
        # color() beats lcolor() for the outline (E3); red at .5 over blue.
        assert before[0][:3] == ("#ff0000", "#800080", "#ff0000")


_HOSTILE = [
    'color("red;}</style><script>x</script>")',
    "ifcolor(red;background:url(x))",
    "margin(1;x:y)",
    "lcolor(" + "a" * 100_000 + ")",
    "c(" * 10_000 + ")" * 10_000,
    "lcolor(red\x00blue)",
    "lcolor(‮)",
]


class TestHostileRegionText:
    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_inert(self, mode):
        spec = tp._spec(graphs=[(f"g{i}", [plot_for("scatter")],
                                 {"plotregion": h, "graphregion": h,
                                  "bgcolor": h})
                                for i, h in enumerate(_HOSTILE)])
        figs, caught = _figs(mode, spec)
        assert len(figs) == len(_HOSTILE)
        for f in figs:
            for v in _region(f):
                ok = (v is None or isinstance(v, (int, float))
                      or (isinstance(v, str) and _HEX.fullmatch(v))
                      or (isinstance(v, list)
                          and all(isinstance(x, (int, float)) for x in v)))
                assert ok, v
        # Each echoed value is _dash_display's: printable, 80 at most.
        for c in caught:
            assert c.isprintable() and len(c) <= 400, c[:120]
        if mode == "saved":
            spec1 = tp._spec([plot_for("scatter")], None,
                             {"plotregion": _HOSTILE[0]})
            _, _, page = tp._standalone_page(spec1)
            assert "<script>x</script>" not in page


class TestTheHelp:
    def test_the_help_is_twoways(self):
        with open(os.path.join(_HERE, "..", "dash.sthlp"),
                  encoding="utf-8") as fh:
            text = fh.read()
        start = text.index("{marker region_options}")
        sec = text[start:text.index("{marker ", start + 10)]
        assert "{cmd:plotregion(color(}" in sec and "shortest {cmd:c()}" in sec
        assert "bgcolor(red) graphregion(color(none))" in sec
        assert "colors the graph region itself" not in text
