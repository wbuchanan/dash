"""A bare colour intensity or opacity takes the site's own colour (WP-30
P1.13b, plan section 43).

twoway reads ``mcolor(*.5)`` as the colour the marker would draw without
the option, at half intensity; ``%50`` as that colour at half opacity.
dash kept the default unadjusted.  The measured truth is
test/fixtures/bare_intensity_truth.json (scripts/
extract_bare_intensity_truth.do): per scheme, probe and value, the colours
of twoway's SVG that the option introduced.
"""

import json
import os
import re
import sys
import warnings
from unittest import mock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

import dash_render as dr  # noqa: E402
import test_mode_parity as tmp  # noqa: E402
from test_mode_parity import (_layout_tree, _served, _spec,  # noqa: E402
                              _standalone)
from test_server_layer_defects import plot_for  # noqa: E402
from probe_groups import probe_params, representative  # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))
_FIX = os.path.join(_HERE, "fixtures", "bare_intensity_truth.json")
_SCHEMES = ("s1rcolor", "s2color", "stcolor", "sttrans")
_VALUES = ("*.5", "*2", "%50", "*.5%50")


def _truth():
    with open(_FIX, encoding="utf-8") as fh:
        return json.load(fh)


# probe id -> (plots, graph options, the colour families checked).  The
# value replaces "@".  Families: "fill" (glyph fills and the regions'
# fills), "stroke" (glyph lines, axis lines, outlines), "text".
_P = {
    "P01": ([("scatter", {"mcolor": "@"})], {}, ("fill", "stroke")),
    "P02": ([("scatter", {"mfcolor": "@"})], {}, ("fill",)),
    "P03": ([("scatter", {"mlcolor": "@"})], {}, ("stroke",)),
    "P04": ([("scatter", {"pstyle": "p3", "mcolor": "@"})], {},
            ("fill", "stroke")),
    "P05": ([("line", {"lcolor": "@"})], {}, ("stroke",)),
    "P06": ([("connected", {"lcolor": "@"})], {}, ("stroke",)),
    "P07": ([("bar", {"color": "@"})], {}, ("fill", "stroke")),
    "P08": ([("bar", {"fcolor": "@"})], {}, ("fill",)),
    "P09": ([("bar", {"fcolor": "@", "fintensity": "50"})], {}, ("fill",)),
    "P10": ([("bar", {"lcolor": "@"})], {}, ("stroke",)),
    "P11": ([("area", {"fcolor": "@"})], {}, ("fill",)),
    "P12": ([("rarea", {"fcolor": "@"})], {}, ("fill",)),
    "P15": ([("dropline", {"lcolor": "@"})], {}, ("stroke",)),
    "P16": ([("rcap", {"lcolor": "@"})], {}, ("stroke",)),
    "P17": ([("pcarrow", {"lcolor": "@"})], {}, ("stroke",)),
    "P18": ([("scatteri", {"mcolor": "@"})], {}, ("fill", "stroke")),
    "P19": ([("scatter", {"mlabel": "foreign", "mlabcolor": "@"})], {},
            ("text",)),
    "P20": ([("scatter", {})], {"title": "T, color(@)"}, ("text",)),
    "P21": ([("scatter", {})], {"subtitle": "S, color(@)"}, ("text",)),
    "P22": ([("scatter", {})], {"note": "N, color(@)"}, ("text",)),
    "P23": ([("scatter", {})], {"caption": "C, color(@)"}, ("text",)),
    "P24": ([("scatter", {})], {"ytitle": "Y, color(@)"}, ("text",)),
    "P25": ([("scatter", {})], {"ylabel": ", labcolor(@)"}, ("text",)),
    "P26": ([("scatter", {})], {"yscale": "lcolor(@)"}, ("stroke",)),
    "P30": ([("scatter", {})], {"xline": "3000, lcolor(@)"}, ("stroke",)),
    "P31": ([("scatter", {}), ("scatter", {"yaxis": "2", "mcolor": "@"},
                               "price")], {}, ("fill", "stroke")),
}


def _plots(pid, v):
    out = []
    for entry in _P[pid][0]:
        ptype, opts = entry[0], entry[1]
        extra = {"yvar": entry[2]} if len(entry) > 2 else {}
        out.append(plot_for(ptype, {k: x.replace("@", v)
                                    for k, x in opts.items()}, **extra))
    return out


def _go(pid, v):
    return {k: x.replace("@", v) for k, x in _P[pid][1].items()}


def _graphs(scheme, values=_VALUES):
    """Every (probe, value) of *scheme*'s fixture, for each of *values*,
    as one graph each."""
    gs, keys = [], []
    for pid in sorted(_P):
        for v in values:
            name = f"g{len(gs)}"
            gs.append((name, _plots(pid, v), _go(pid, v)))
            keys.append((name, pid, v))
    return gs, keys


_FAMILIES = {
    "fill": (("fill_color", "fill_alpha"),),
    "stroke": (("line_color", "line_alpha"),
               ("axis_line_color", "axis_line_alpha")),
    "text": (("text_color", "text_alpha"),
             ("axis_label_text_color", "axis_label_text_alpha"),
             ("major_label_text_color", "major_label_text_alpha")),
}


def _drawn(fig):
    """{family: {(hex, alpha)}} over every model of *fig*."""
    out = {k: set() for k in _FAMILIES}
    for m in fig.references():
        for fam, pairs in _FAMILIES.items():
            for cp, ap in pairs:
                if cp not in m.properties() or ap not in m.properties():
                    continue
                c, a = getattr(m, cp), getattr(m, ap)
                if isinstance(c, str) and re.fullmatch(r"#[0-9a-fA-F]{6}",
                                                        c):
                    a = a if isinstance(a, (int, float)) else 1.0
                    out[fam].add((c.lower(), round(float(a), 2)))
    return out


def _wanted(rec, families):
    """{family: {(hex, opacity)}} the probe's option introduced."""
    out = {k: set() for k in families}
    for e in rec["new"]:
        if e["tag"] == "text":
            if "text" in out:
                out["text"].add((e["fill"], round(e["fill_opacity"], 2)))
            continue
        if "fill" in out and e["fill"] not in (None, "none"):
            out["fill"].add((e["fill"], round(e["fill_opacity"], 2)))
        if "stroke" in out and e["stroke"] not in (None, "none"):
            out["stroke"].add((e["stroke"], round(e["stroke_opacity"], 2)))
    return out


def _saved_figures(spec):
    """{graph name: figure} of the saved page."""
    r, _w = _standalone(spec)
    return dict(r.figures)


def _served_figures(spec):
    """{graph name: figure} of the served document: its figures in the
    page's order are the graphs' (test_mode_parity pairs them so)."""
    doc, _w = _served(spec)
    figs = []
    with mock.patch.object(tmp, "_figure_profile", lambda m: m):
        for root in doc.roots:
            _layout_tree(root, figs)
    names = [g["name"] for g in spec["graphs"]]
    assert len(figs) == len(names), (len(figs), len(names))
    return dict(zip(names, figs))


# ---------------------------------------------------------------------------


class TestTheFixture:
    def test_it_is_stamped(self):
        d = _truth()
        for k in ("stata_version", "born_date", "dash_commit", "extracted"):
            assert d["_meta"].get(k), k
        assert sorted(d["schemes"]) == list(_SCHEMES)
        for s in _SCHEMES:
            for pid in _P:
                assert sorted(d["schemes"][s][pid]) == sorted(_VALUES), \
                    (s, pid)


class TestTheRule:
    def test_the_base_rule(self):
        T = dr.OptionTranslator
        assert T.stata_colour("*.5", base="#1a476f") == \
            ("ok", "#8da3b7", None)
        assert T.stata_colour("%50", base="#1a476f") == \
            ("ok", "#1a476f", 0.5)
        for v in ("*.5%50", "%50*.5"):
            assert T.stata_colour(v, base="#1A476F") == \
                ("ok", "#8da3b7", 0.5), v
        assert T.stata_colour("*.5", base="#ffff00",
                              naturally_white=False) == \
            ("ok", "#808000", None)
        # Without a base: S30's answer, the site keeps its colour.
        assert T.stata_colour("*.5") == ("ok", None, None)
        # A colour of its own ignores the base.
        assert T.stata_colour("red", base="#1a476f")[1] == "#ff0000"

    def test_the_base_is_never_text(self):
        T = dr.OptionTranslator
        hexre = re.compile(r"#[0-9a-f]{6}")
        for base in ("red; x:1", "#fff", 123, "x" * 10_000, None,
                     "#1a476f; background:url(x)"):
            st, hx, _a = T.stata_colour("*.5", base=base)
            assert hx is None, base
        for v in ("*1e400", "*" + "9" * 10_000, "%50" * 4000):
            st, hx, _a = T.stata_colour(v, base="#1a476f")
            assert hx is None or hexre.fullmatch(hx), (v[:20], hx)


class TestTheTextReader:
    def test_keywords(self):
        got = dr._textbox_color({"color": "*.5"}, None, base="#1e2d53",
                                with_alpha=True)
        assert got == ("#8f96a9", None)
        assert dr._textbox_color({"color": "red%50"}, None,
                                 with_alpha=True) == ("#ff0000", 0.5)
        # Without the keywords: the old answer, no colour for a bare form.
        assert dr._textbox_color({"color": "*.5"}, "#123456") == "#123456"
        assert dr._textbox_color({}, None, with_alpha=True) == (None, None)


#: The keys "<scheme>/<value>" (one build of every probe each).  The
#: gate's served subset (probe_groups.representative, pytest speed,
#: 22oct2026): the diagonal that pairs each scheme with a different value,
#: so every scheme and every value is built served, and every sixth key of
#: the rest; release checks every key served.
_KEYS = ["%s/%s" % (s, v) for s in _SCHEMES for v in _VALUES]
_DIAGONAL = ["%s/%s" % sv for sv in zip(_SCHEMES, _VALUES)]
_PARAMS = probe_params(_KEYS, representative(_KEYS, always=_DIAGONAL,
                                             stride=6))


class TestEverySite:
    """Every probe of every scheme against twoway, one build per scheme,
    value and mode; every mismatch reported."""

    @pytest.mark.parametrize("mode,group", _PARAMS)
    def test_probe(self, mode, group):
        d = _truth()
        bad = []
        for key in group:
            scheme, _, value = key.partition("/")
            # One build per scheme and value: 26 graphs (a page holds at
            # most 100).
            gs, keys = _graphs(scheme, (value,))
            spec = _spec(graphs=gs, build_options={"scheme": scheme})
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                byname = (_saved_figures(spec) if mode == "saved"
                          else _served_figures(spec))
            for name, pid, v in keys:
                rec = d["schemes"][scheme][pid][v]
                if rec["rc"] != 0:
                    continue
                fig = byname.get(name)
                if fig is None:
                    bad.append(f"{scheme} {pid} {v}: no figure {name}")
                    continue
                got = _drawn(fig)
                for fam, want in _wanted(rec, _P[pid][2]).items():
                    miss = sorted(w for w in want if w not in got[fam])
                    if miss:
                        bad.append(f"{scheme} {pid} {v} {fam}: twoway "
                                   f"{miss}, dash {sorted(got[fam])}")
        assert not bad, f"{len(bad)} mismatches:\n" + "\n".join(bad)


class TestUnknownAtDirectSites:
    """An unknown colour at a direct site draws black, noted once, as
    twoway draws it (fixture U01-U05; a bar's fill is black at the bar's
    intensity, #333333)."""

    def test_site(self):
        d = _truth()["schemes"]["s2color"]
        cases = {
            "U01": ([plot_for("bar", {"color": "bogus"})], {}, "fill"),
            "U02": ([plot_for("area", {"color": "bogus"})], {}, "fill"),
            "U03": ([plot_for("dropline", {"lcolor": "bogus"})], {},
                    "stroke"),
            "U04": ([plot_for("scatter", {"mlabel": "foreign",
                                          "mlabcolor": "bogus"})], {},
                    "text"),
            "U05": ([plot_for("scatter", {})],
                    {"xline": "3000, lcolor(bogus)"}, "stroke"),
        }
        bad = []
        for uid, (plots, go, fam) in sorted(cases.items()):
            rec = d[uid]["bogus"]
            assert rec["notes"], uid
            want = _wanted(rec, (fam,))[fam]
            spec = _spec(plots, {"scheme": "s2color"}, go)
            r, caught = _standalone(spec)
            notes = [w for w in caught if "bogus" in w]
            fig = r.figures["g1"]
            got = _drawn(fig)[fam]
            miss = sorted(w for w in want if w not in got)
            if miss or len(notes) != 1:
                bad.append(f"{uid}: twoway {miss} not in {sorted(got)}; "
                           f"notes {notes}")
        assert not bad, "\n".join(bad)


class TestTheKpi:
    def test_bare_forms(self):
        assert dr._resolve_kpi_color("*.5", "#1a476f", "color") == "#8da3b7"
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            assert dr._resolve_kpi_color("*.5", "", "bgcolor") == ""
        assert not caught
        # Colours accepted before keep their colour.
        for v, want in (("navy", "#1a476f"), ("Navy", "#1a476f"),
                        ("#ABC", "#abc"), ("red%50", "#ff0000")):
            assert dr._resolve_kpi_color(v, "#000000", "color") == want, v


class TestColormissing:
    def test_bare_form(self):
        spec = _spec([plot_for("scatter", {"colorvar": "price",
                                           "colormissing": "*.5"})])
        r, _w = _standalone(spec)
        nan = {m.nan_color for m in r._last_layout_root.references()
               if "nan_color" in m.properties()}
        # #808080 at half intensity (naturally white): #c0c0c0.
        assert "#c0c0c0" in nan, nan


class TestAfterAFilterMove:
    """The served app redraws a layer through the same mapper after a
    move: the colours of a bare form survive it."""

    def test_colours_survive(self):
        spec = _spec([plot_for("scatter", {"mcolor": "*.5"}),
                      plot_for("bar", {"fcolor": "*.7"})],
                     {"scheme": "s2color", "filter": "foreign"},
                     {"title": "T, color(*.5)",
                      "xline": "3000, lcolor(%50)"})
        doc, _w = _served(spec)
        fig = [m for root in doc.roots for m in root.references()
               if type(m).__name__ == "figure"][0]
        before = _drawn(fig)
        sel = [m for root in doc.roots for m in root.references()
               if type(m).__name__ in ("Select", "MultiChoice",
                                       "MultiSelect")]
        assert sel, "no filter widget"
        w = sel[0]
        opts = [o[0] if isinstance(o, (list, tuple)) else o
                for o in w.options]
        w.value = (opts[-1] if type(w).__name__ == "Select"
                   else [opts[-1]])
        after = _drawn(fig)
        # p1 navy*.5; p2's maroon*.7 at the bar's intensity; the heading
        # dknavy*.5; the xyline colour at half opacity.
        for fam, pair in (("fill", ("#8da3b7", 1.0)),
                          ("fill", ("#c18e91", 1.0)),
                          ("text", ("#8f96a9", 1.0)),
                          ("stroke", ("#c10534", 0.5))):
            assert pair in before[fam], (fam, pair, sorted(before[fam]))
        assert after == before


class TestTheHelp:
    def test_the_rule_is_documented(self):
        with open(os.path.join(_HERE, "..", "dash.sthlp"),
                  encoding="utf-8") as fh:
            text = fh.read()
        assert "mcolor(*.5)" in text
        flat = " ".join(text.split())
        assert "the colour the element would draw without the option" in flat
        # S30's interim sentence is gone.
        assert "{cmd:%}{it:#} keeps the default colour" not in flat
