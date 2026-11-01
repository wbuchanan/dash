"""by()'s econ, stata7, rescale and combine bystyles (WP-31 section 44,
D10c).

Measured (scripts/extract_bystyle_truth.do -> test/fixtures/
bystyle_truth.json, s2color): twoway draws ``by(rep78, style(econ))``,
``style(stata7)`` and ``style(rescale)`` exactly -- the exported SVGs are
line for line the same -- as ``by(rep78, <words>) <options>`` read from
their bygraphstyle files: econ is the default with ``subtitle(,
margin(small)) plotregion(color(edkbg) margin(t=5))``; stata7 ``edgelabel
ixaxes iyaxes imargin(small)`` with its twoway_options and an unboxed
label; rescale ``rescale individual imargin(medsmall)`` with a boxed
label in the foreground line and ``#3`` labels.  dash named econ and
stata7 and drew only rescale's and combine's separate scales.  combine's
graph regions (``combineregion``, which twoway itself does not find) do
not reduce to options: its scales are drawn, the rest named.
"""
import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_by_axes_keys as tk  # noqa: E402
import test_by_remainder as tr  # noqa: E402

with open(os.path.join(_HERE, "fixtures", "bystyle_truth.json"),
          encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)

MODES = ("saved", "served")
_EXACT = ("econ", "stata7", "rescale")
_ALL = _EXACT + ("combine",)
#: combine's regions: graph combine's layout, not by()'s grid (M17).
_COMBINE_NOTE = ("dash: by() sub-option style(combine): its panels are laid "
                 "out on by()'s grid, not in graph combine's regions.")


def _drawn_opts(style):
    return _opts(TRUTH["styles"][style]["options"])


def _opts(text):
    """``{key: value}`` of an option text as dash.ado writes a graph's
    options (``ylabels(#3)`` is ylabel ``#3``)."""
    canon = {"ylabels": "ylabel", "xlabels": "xlabel", "xmticks": "xmtick",
             "ymticks": "ymtick"}
    out = {}
    for tok in dr._dash_by_tokens(text):
        name, arg = tok.split("(", 1)
        out[canon.get(name, name)] = arg[:-1]
    return out


class TestTheFixture:
    def test_meta_and_measure(self):
        assert sorted(TRUTH["_meta"]) == ["born_date", "dash_commit",
                                          "extracted", "source",
                                          "stata_version"]
        for s in _EXACT:
            assert TRUTH["styles"][s]["diff_lines"] == 0, s
        assert TRUTH["styles"]["combine"]["diff_lines"] > 0


class TestTheExpansion:
    @pytest.mark.parametrize("style", _ALL)
    def test_measured(self, style):
        rec = TRUTH["styles"][style]
        spec = tk._spec([tk._graph("g", tk._TWO,
                                   {"by": f"rep78, style({style})"})])
        out = dr._dash_bystyle_route(spec)
        go = out["graphs"][0]["graph_options"]
        words = dr._dash_by_tokens(go["by"].partition(",")[2])
        assert words == rec["by_words"].split(), words
        for k, v in _drawn_opts(style).items():
            assert go.get(k) == v, (k, go.get(k), v)

    def test_a_users_own_option_wins(self):
        spec = tk._spec([tk._graph("g", tk._TWO, {
            "by": "rep78, style(rescale)", "xlabel": "#6"})])
        go = dr._dash_bystyle_route(spec)["graphs"][0]["graph_options"]
        assert go["xlabel"] == "#6" and go["ylabel"] == "#3"

    @pytest.mark.parametrize("subs,want", [
        # Measured 18oct2026 (StataNow 19.5, auto, scatter mpg weight,
        # by(foreign, ...), .Graph.graphs[k] scales): style(rescale)
        # noyrescale draws both panels' y 10-41 and x 1800-5000 and
        # 1760-4000; noxrescale x 1760-5000 twice and y 10-34 and 10-41;
        # norescale 1760-5000 and 10-41 twice; style(combine) noyrescale
        # y 10-41 twice and x 1800-5000 and 1500-3500.
        ("style(rescale) noyrescale", {"x"}),
        ("style(rescale) noxrescale", {"y"}),
        ("style(rescale) norescale", set()),
        ("style(rescale)", {"x", "y"}),
        ("style(combine) noyrescale", {"x"})])
    def test_a_no_word_beside_the_style_still_wins(self, subs, want):
        """BUGS.md "Harness guards" (WP-32): the expansion wrote the word
        rescale for style(rescale), and rescale beats noyrescale, so the y
        axis the user kept shared was rescaled per panel."""
        spec = tk._spec([tk._graph("g", tk._TWO,
                                   {"by": "foreign, " + subs})])
        by = dr._dash_bystyle_route(spec)["graphs"][0]["graph_options"]["by"]
        assert set(dr._dash_by_rescale(by)) == want, by

    def test_combine_and_others_untouched(self):
        # Flipped (WP-41 BY-4): style(compact) was left untouched, which
        # was wrong because twoway draws compact's outlines
        # (bygraphstyle-compact.style:39); it is routed to its words now.
        for by in ("rep78", 'rep78, title("style(econ)")'):
            spec = tk._spec([tk._graph("g", tk._TWO, {"by": by})])
            assert dr._dash_bystyle_route(spec)["graphs"][0][
                "graph_options"]["by"] == by
        spec = tk._spec([tk._graph("g", tk._TWO,
                                   {"by": "rep78, style(compact)"})])
        go = dr._dash_bystyle_route(spec)["graphs"][0]["graph_options"]
        assert go["by"] == "rep78, compact"
        assert go["plotregion"] == "lstyle(foreground)"


def _summary(roots):
    out = []
    for name, g in sorted(tk._grids(roots).items()):
        for c in g.children:
            f = c[0]
            out.append((name, type(f).__name__,
                        len(getattr(f, "renderers", []) or []),
                        tuple(sorted(type(a).__name__ for a in
                                     (f.left + f.below + f.above + f.right)))))
    return out


@pytest.mark.parametrize("mode", MODES)
class TestDrawn:
    @pytest.mark.parametrize("style", _EXACT)
    def test_as_its_expansion(self, mode, style):
        rec = TRUTH["styles"][style]
        by_words = (", " + rec["by_words"]) if rec["by_words"] else ""
        a = tk._spec([tk._graph("g", tk._TWO,
                                {"by": f"rep78, style({style})"})],
                     scheme="s2color")
        go = dict({"by": "rep78" + by_words}, **_drawn_opts(style))
        b = tk._spec([tk._graph("g", tk._TWO, go)], scheme="s2color")
        ra, na, _ = tk._build(mode, a, data=tr._data())
        rb, nb, _ = tk._build(mode, b, data=tr._data())
        assert _summary(ra) == _summary(rb)
        assert [n for n in na if f"style({style})" in n] == []
        assert [n for n in na if "not implemented" in n] == \
            [n for n in nb if "not implemented" in n]

    def test_combine_names_its_regions(self, mode):
        spec = tk._spec([tk._graph("g", tk._TWO,
                                   {"by": "rep78, style(combine)"})],
                        scheme="s2color")
        _r, notes, _ = tk._build(mode, spec, data=tr._data())
        assert [n for n in notes if "style(combine)" in n] == [_COMBINE_NOTE]


def _boxes(roots):
    from bokeh.models import ColorBar
    out = []
    for r in roots:
        for m in r.references():
            if isinstance(m, ColorBar) and m.name == "dash_by_label_box":
                out.append(m)
    return out


@pytest.mark.parametrize("mode", MODES)
class TestTheNamedPartsDrawn:
    def test_econ_label_margin(self, mode):
        """margin(small): the label box is as much taller than the
        default's as twoway draws it (bystyle_econ against bystyle_default
        label rects, by_remainder_truth.json)."""
        def h(pid):
            return [x for x in tr._probe(pid)["rects"]
                    if x["fill"] == "#d9e6eb"][0]["h"]
        f = tr._probe("bystyle_default")["texts"]
        font = [x for x in f if x["t"] == "1"][0]["size"]
        want = (h("bystyle_econ") - font) / (h("bystyle_default") - font)
        got = []
        for by in ("rep78, style(econ)", "rep78"):
            spec = tk._spec([tk._graph("g", tk._TWO, {"by": by})],
                            scheme="s2color")
            roots, _n, _o = tk._build(mode, spec, data=tr._data())
            b = _boxes(roots)[0]
            fpx = float(str(b.major_label_text_font_size).rstrip("px"))
            got.append(b.height - fpx)
        # Whole pixels: each box height is rounded once.
        assert abs(got[0] - want * got[1]) <= 1.0, (got, want)

    def test_rescale_outline_is_the_foreground_line(self, mode):
        spec = tk._spec([tk._graph("g", tk._TWO,
                                   {"by": "rep78, style(rescale)"})],
                        scheme="s2color")
        roots, _n, _o = tk._build(mode, spec, data=tr._data())
        fg = dr.SchemeParser("s2color").style_bundle("line", "foreground")
        assert {str(b.bar_line_color).lower() for b in _boxes(roots)} == {
            fg["line"]}

    def test_stata7_minor_ticks_take_the_major_length(self, mode):
        """xmticks(##4, style(major_horiz_nolabel)): twoway draws the minor
        ticks as long as the majors (39.97 against 20.04 units, measured
        against xmticks(##4))."""
        spec = tk._spec([tk._graph("g", tk._TWO,
                                   {"by": "rep78, style(stata7)"})],
                        scheme="s2color")
        roots, _n, _o = tk._build(mode, spec, data=tr._data())
        from bokeh.models import LinearAxis
        axes = [m for r in roots for m in r.references()
                if isinstance(m, LinearAxis) and m.minor_tick_out]
        assert axes and all(a.minor_tick_out == a.major_tick_out
                            for a in axes)
