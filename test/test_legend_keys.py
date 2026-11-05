"""
test_legend_keys.py -- the legend's keys as twoway draws them (WP-43
section 43-04): textfirst and stacked (LT-21), which keys merge (MS-10)
and a turned kdensity's or function's key text (RH-13).

twoway's facts are measured (scripts/extract_legend_keys_truth.do ->
test/fixtures/legend_keys_truth.json); each mode's legend is built here
and read as a model.  textfirst and stacked are drawn by the Legend's own
stylesheet (``_dash_legend_key_order``, ruling D69), which only a browser
lays out: test_legend_keys_browser.py measures it in Chrome.
"""
import json
import math
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_by_axes_keys as bk  # noqa: E402
from conftest import drawn_renderers, is_key_proxy  # noqa: E402

MODES = ("saved", "served")

_TRUTH = json.load(open(os.path.join(_HERE, "fixtures",
                                     "legend_keys_truth.json")))


def _texts(case):
    """twoway's texts of fixture *case*: ``{text: (x, y, anchor)}``."""
    return {e["text"]: (float(e["a"]["x"]), float(e["a"]["y"]),
                        e["a"].get("text-anchor", "start"))
            for e in _TRUTH[case]["els"] if e["tag"] == "text"}


def _key_marks(case):
    """twoway's key symbols of fixture *case* below the plot region:
    ``[(left, right, centre y), ...]`` sorted by left edge (a marker's
    filled circle, a line's segment)."""
    row = _TRUTH[case]
    pb = row["plot"]["bottom"]
    out = []
    for e in row["els"]:
        a = e["a"]
        if (e["tag"] == "circle" and float(a["cy"]) > pb
                and "fill:none" not in a.get("style", "")):
            r = float(a["r"])
            out.append((float(a["cx"]) - r, float(a["cx"]) + r,
                        float(a["cy"])))
        elif (e["tag"] == "line" and "y1" in a and float(a["y1"]) > pb
              and a["y1"] == a["y2"]):
            out.append((float(a["x1"]), float(a["x2"]), float(a["y1"])))
    return sorted(out)


def _legend(mode, plots, legend_opt, scheme="s2color", go=None):
    """``(series Legend, notes)`` of one graph of *plots* in *mode*."""
    from bokeh.models import Legend
    g = dict(go or {})
    g["legend"] = legend_opt
    spec = bk._spec([bk._graph("g1", plots, g, title=False)], scheme=scheme)
    roots, notes, _owner = bk._build(mode, spec)
    legs = [m for r in roots for m in r.references()
            if isinstance(m, Legend)
            and str(m.name or "") != "dash_colorvar_legend"]
    legs = [lg for lg in legs if lg.items]
    assert legs, "no legend"
    return legs[0], notes


def _sheet(legend, tag):
    """The CSS of *legend*'s stylesheet tagged *tag*, '' for none."""
    for ss in legend.stylesheets:
        if tag in (getattr(ss, "tags", None) or []):
            return ss.css
    return ""


_TWO = [bk._p("scatter"), bk._p("line", y="headroom")]


class TestTheFixture:
    """twoway's measured facts the LT-21 key order rests on."""

    def test_every_probe_drew(self):
        rows = {k: v for k, v in _TRUTH.items() if k != "_meta"}
        assert len(rows) >= 50
        assert all(v["rc"] == 0 for v in rows.values())
        assert _TRUTH["_meta"]["source"] == \
            "scripts/extract_legend_keys_truth.do"

    def test_textfirst(self):
        """textfirst: each text ends (anchor end) one keygap before its
        key; the legend's box is the control's."""
        ctl, first = _key_marks("cell_ctl"), _key_marks("textfirst")
        t = _texts("textfirst")
        assert t["Mileage (mpg)"][2] == "end" and t["Price"][2] == "end"
        assert t["Mileage (mpg)"][0] < first[0][0]
        assert t["Price"][0] < first[1][0]
        assert 50 < first[1][0] - t["Price"][0] < 65
        assert [e for e in _TRUTH["textfirst"]["els"] if e["tag"] == "rect"
                ][-1]["a"]["width"] == [
            e for e in _TRUTH["cell_ctl"]["els"] if e["tag"] == "rect"
        ][-1]["a"]["width"]
        assert ctl[0][0] < _texts("cell_ctl")["Mileage (mpg)"][0]

    def test_textfirst_column(self):
        """textfirst cols(1): the texts end at one x and the keys share
        one column, a marker centred in the line's key box."""
        t = _texts("textfirst_cols1")
        ends = {t[k][0] for k in ("Mileage (mpg)", "Price",
                                  "Turn circle (ft.)")}
        assert len(ends) == 1
        marks = _key_marks("textfirst_cols1")
        line = [m for m in marks if 300 < m[1] - m[0] < 1000][0]
        dots = [m for m in marks if m[1] - m[0] < 100]
        for d in dots:
            assert abs((d[0] + d[1]) / 2 - (line[0] + line[1]) / 2) < 1

    def test_stacked(self):
        """stacked: each text under its key at the key's left; under
        textfirst the text above it."""
        for case, below in (("stacked", True), ("textfirst_stacked", False)):
            marks, t = _key_marks(case), _texts(case)
            for m, name in zip(marks, ("Mileage (mpg)", "Price")):
                assert (t[name][1] > m[2]) == below, case
                assert abs(t[name][0] - m[0]) < 5, case


class TestKeyOrder:
    """textfirst and stacked reach the Legend's own stylesheet, in both
    modes, and print nothing."""

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("opt,want", [
        ("textfirst", "flex-direction:row-reverse"),
        ("stacked", "flex-direction:column;align-items:flex-start"),
        ("textfirst stacked",
         "flex-direction:column-reverse;align-items:flex-start"),
        ("stac textf", "flex-direction:column-reverse"),
    ])
    def test_css(self, mode, opt, want):
        lg, notes = _legend(mode, _TWO, opt)
        assert want in _sheet(lg, "dash_legend_keyorder")
        assert not [n for n in notes if "legend()" in n], notes

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("opt", ["", "textfirst notextfirst",
                                     "stacked nostacked", "notextfirst",
                                     "nostacked"])
    def test_none(self, mode, opt):
        lg, notes = _legend(mode, _TWO, opt)
        assert _sheet(lg, "dash_legend_keyorder") == ""
        assert not [n for n in notes if "legend()" in n], notes

    def test_only_fixed_words(self):
        """The helper writes one of three fixed rules, whatever else the
        legend holds."""
        from bokeh.models import Legend
        seen = set()
        for words in ({"textfirst"}, {"stacked"}, {"textfirst", "stacked"},
                      {"textfirst", "x</style>"}, set()):
            lg = Legend()
            seen.add(dr._dash_legend_key_order(lg, words))
        assert seen == {
            ".bk-grid .bk-item{flex-direction:row-reverse;}",
            ".bk-grid .bk-item{flex-direction:column;"
            "align-items:flex-start;}",
            ".bk-grid .bk-item{flex-direction:column-reverse;"
            "align-items:flex-start;}", ""}

    def test_by_cell_copies_it(self):
        """by()'s legend cell copies the panel legend's stylesheets."""
        from bokeh.models import Legend
        spec = bk._spec([bk._graph("g1", _TWO, {"by": "foreign",
                                                "legend": "textfirst"},
                                   title=False)], scheme="s2color")
        roots, _n, _o = bk._build("saved", spec)
        cells = [m for r in roots for m in r.references()
                 if isinstance(m, Legend) and m.visible and m.items
                 and "row-reverse" in _sheet(m, "dash_legend_keyorder")]
        assert cells


def _fixture_keys(case):
    """twoway's key texts of fixture *case*, in reading order: the texts
    of its legend (the key rows below its plot's title row), found as the
    texts that share a row with another key text or sit inside the
    legend's frame; [] when twoway drew no legend."""
    import re
    row = _TRUTH[case]
    texts = [(float(e["a"]["y"]), float(e["a"]["x"]), e["text"])
             for e in row["els"] if e["tag"] == "text"
             and not re.fullmatch(r"[-0-9.,]+", e["text"])]
    titles = {"x", "Weight (lbs.)", "Density", "Mileage (mpg)",
              "Turn circle (ft.)", "Price", "y", "Fitted values",
              "Percent", "Frequency"}
    frames = [e["a"] for e in row["els"] if e["tag"] == "rect"
              and "stroke:" in e["a"].get("style", "")
              and float(e["a"].get("height", 0)) < 1000]
    out = []
    for y, x, t in texts:
        inside = any(float(f["x"]) <= x <= float(f["x"]) + float(f["width"])
                     and float(f["y"]) <= y <= float(f["y"])
                     + float(f["height"]) for f in frames)
        if inside or (t not in titles and re.fullmatch(r"v[0-9/v]+", t)):
            out.append((round(y, 1), x, t))
    return [t for _y, _x, t in sorted(out)]


def _lines_data(n=16):
    """10 rows of x and v1..v<n> = x + i, the merge_s* probes' data."""
    import pandas as pd
    from conftest import make_data_json
    df = pd.DataFrame({"x": [float(i) for i in range(1, 11)]})
    for i in range(1, n + 1):
        df["v%d" % i] = df["x"] + i
    return make_data_json(df)


def _keys_of(mode, plots, scheme="s2color", data=None, go=None):
    """``(key texts, legend visible)`` of one graph in *mode*."""
    from bokeh.models import Legend
    g = dict(go or {})
    spec = bk._spec([bk._graph("g1", plots, g, title=False)], scheme=scheme)
    roots, _notes, _owner = bk._build(mode, spec, data)
    for r in roots:
        for m in r.references():
            if (isinstance(m, Legend) and m.items
                    and str(m.name or "") != "dash_colorvar_legend"):
                return ([it.label.get("value") if isinstance(it.label, dict)
                         else it.label.value for it in m.items],
                        bool(m.visible))
    return [], False


def _line(y, **o):
    return {"type": "line", "yvar": y, "xvar": "x",
            "options": dict({"sort": "sort"}, **o)}


class TestMergeRule:
    """MS-10: twoway merges two keys when they are the same kind of plot
    in the same pstyle with no style option of their own
    (legend_g.class rebuild: "<type stylename>:<style stylename>"), not
    when they look alike."""

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("n", (14, 15, 16))
    def test_s1mono_lines(self, mode, n):
        """line v1-v<n> x under s1mono: 14 and 15 keys, none merged
        (s1mono's p6 and p14 look alike); 16 merges v16 into v1."""
        want = _fixture_keys("merge_s1mono%d" % n)
        assert len(want) == min(n, 15)
        keys, shown = _keys_of(mode, [_line("v%d" % i)
                                      for i in range(1, n + 1)],
                               scheme="s1mono", data=_lines_data())
        assert keys == want and shown

    @pytest.mark.parametrize("mode", MODES)
    def test_s2color_cycle(self, mode):
        """line v1-v16 x under s2color: v16 draws in p1 and is v1's key."""
        want = _fixture_keys("merge_s2color16")
        assert want[0] == "v1/v16" and len(want) == 15
        keys, _shown = _keys_of(mode, [_line("v%d" % i)
                                       for i in range(1, 17)],
                                data=_lines_data())
        assert keys == want

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("case,plots,n_keys", [
        # kdensity is a line: with line in pstyle(p1), one key, no legend.
        ("merge_cross", [bk._p("kdensity", y="mpg", x="",
                               pstyle="p1"),
                         bk._p("line", pstyle="p1", sort="sort")], 1),
        ("merge_cross_lfit", [bk._p("lfit", pstyle="p1"),
                              bk._p("line", pstyle="p1", sort="sort")], 1),
        # scatter and line: two kinds, two keys.
        ("merge_cross_sc", [bk._p("scatter", pstyle="p1"),
                            bk._p("line", pstyle="p1", sort="sort")], 2),
        # recast(line) is a line.
        ("merge_recast", [bk._p("scatter", pstyle="p1", recast="line",
                                sort="sort"),
                          bk._p("line", y="headroom", pstyle="p1",
                                sort="sort")], 1),
    ])
    def test_cross_type(self, mode, case, plots, n_keys):
        assert len(_fixture_keys(case)) == (0 if n_keys == 1 else n_keys)
        keys, shown = _keys_of(mode, plots)
        assert len(keys) == n_keys
        assert shown == (n_keys > 1)

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("plots,want", [
        # Two histograms: one "Density" key, no legend (hist_only).
        ([bk._p("histogram", y="mpg", x=""),
          bk._p("histogram", y="headroom", x="")], ["Density"]),
        # pstyle(p1) twice: one key (merge_pstyle).
        ([bk._p("scatter", pstyle="p1"),
          bk._p("scatter", y="headroom", pstyle="p1")],
         ["Mileage (mpg)/Headroom (in.)"]),
        # p1 and p2: two keys (merge_p1p2).
        ([bk._p("scatter", pstyle="p1"),
          bk._p("scatter", y="headroom", pstyle="p2")],
         ["Mileage (mpg)", "Headroom (in.)"]),
        # A style option keeps a key apart.
        ([bk._p("scatter", pstyle="p1"),
          bk._p("scatter", y="headroom", pstyle="p1", mcolor="red")],
         ["Mileage (mpg)", "Headroom (in.)"]),
        # Two lfitci: one band key, two line keys (merge_lfitci).
        ([bk._p("lfitci"), bk._p("lfitci", y="headroom")],
         ["95% CI", "Fitted values", "Fitted values"]),
    ])
    def test_guards(self, mode, plots, want):
        keys, _shown = _keys_of(mode, plots)
        assert keys == want

    @pytest.mark.parametrize("plot,band,idx,want", [
        ({"type": "line", "options": {}}, False, 5, ("line", "p6")),
        ({"type": "kdensity", "options": {}}, False, 0, ("line", "p1")),
        ({"type": "lfit", "options": {"pstyle": " P2 "}}, False, 0,
         ("line", "p2")),
        ({"type": "scatter", "options": {"recast": "line"}}, False, 1,
         ("line", "p2")),
        ({"type": "histogram", "options": {}}, False, 3,
         ("bar", "histogram")),
        ({"type": "lfitci", "options": {}}, True, 0, ("rarea", "ci")),
        ({"type": "lfitci", "options": {"ciplot": "rcap"}}, True, 0,
         ("rcap", "ci")),
        ({"type": "lfitci", "options": {}}, False, 0, ("line", "p1")),
        ({"type": "scatteri", "options": {"p": "p3"}}, False, 0,
         ("scatter", "p3")),
        ("not a dict", False, 2, ("", "p3")),
    ])
    def test_style_id(self, plot, band, idx, want):
        assert dr._dash_key_style_id(plot, band, idx) == want



def _kd(**o):
    return {"type": "kdensity", "yvar": "mpg", "xvar": "",
            "options": dict({"xaxis": "2"}, **o)}


def _fn(**o):
    return {"type": "function", "expr": "x^2",
            "options": dict({"range": "0 2", "xaxis": "2"}, **o)}


class TestHorizontalKey:
    """RH-13: twoway keys a turned kdensity or function by its grid's
    name, x (twoway_kdensity_parse.class and twoway_function_parse.class
    swap the varlist under yxswitch); recast(area) and recast(bar) keep
    the name (legend_keys_truth.json hz_*, vt_*)."""

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("case,layer,want", [
        ("hz_kdensity", _kd(horizontal="horizontal"), "x"),
        ("vt_kdensity", _kd(), "kdensity mpg"),
    ])
    def test_kdensity(self, mode, case, layer, want):
        assert _fixture_keys(case) == ["Mileage (mpg)", want]
        keys, _shown = _keys_of(mode, [bk._p("scatter"), layer])
        assert keys == ["Mileage (mpg)", want]

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("case,layer,want", [
        ("hz_function", _fn(horizontal="horizontal"), "x"),
        ("vt_function", _fn(), "y"),
    ])
    def test_function(self, mode, case, layer, want):
        assert _fixture_keys(case) == ["Mileage (mpg)", want]
        keys, _shown = _keys_of(mode, [bk._p("scatter"), layer])
        assert keys == ["Mileage (mpg)", want]

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("target", ("area", "bar"))
    def test_recast(self, mode, target):
        assert _fixture_keys("hz_kd_" + target) == ["Mileage (mpg)",
                                                    "kdensity mpg"]
        keys, _shown = _keys_of(mode, [bk._p("scatter"),
                                       _kd(horizontal="horizontal",
                                           recast=target)])
        assert keys == ["Mileage (mpg)", "kdensity mpg"]


# ---- LT-21: marker keys at the marker's size (the key painter) ----------

def _sc(y="mpg", **o):
    return bk._p("scatter", y=y, **o)


def _figs(mode, plots, scheme="s2color", go=None):
    """The figures of one graph of *plots* in *mode*."""
    from bokeh.models import Plot
    spec = bk._spec([bk._graph("g1", plots, dict(go or {}), title=False)],
                    scheme=scheme)
    roots, _notes, _owner = bk._build(mode, spec)
    out = []
    for r in roots:
        out += [m for m in r.references() if isinstance(m, Plot)
                and m not in out]
    return out


def _proxies(fig):
    return [r for r in fig.renderers if is_key_proxy(r)]


def _twoway_marker(case):
    """twoway's marker keys of *case* in text sizes: each filled key
    marker's width over the key text's font size."""
    fs = [float(e["a"]["style"].split("font-size:")[1].split("px")[0])
          for e in _TRUTH[case]["els"] if e["tag"] == "text"
          and e["text"] == "Mileage (mpg)"][0]
    return [(m[1] - m[0]) / fs for m in _key_marks(case)
            if m[1] - m[0] < 200]


#: The marker probes: (plots, scheme, graph options).
_MARKER_CASES = {
    "mk_s2color": ([_sc(), _sc("headroom")], "s2color", None),
    "mk_large": ([_sc(msize="large"), _sc("headroom")], "s2color", None),
    "mk_economist": ([_sc(), _sc("headroom")], "economist", None),
    "mk_scale": ([_sc(), _sc("headroom")], "s2color", {"scale": "1.5"}),
}


class TestMarkerKeySize:
    """LT-21: twoway draws a key marker at the plot's own marker size
    (its width over the key text's size: s2color 0.527, msize(large)
    0.787, economist 0.951, at scale(1.5) the same 0.527), and a legend of
    marker keys only as wide as its marker, whatever symxsize() says
    (mk_symx); Bokeh drew 0.4 of the key box."""

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("case", sorted(_MARKER_CASES))
    def test_size_and_angle(self, mode, case):
        plots, scheme, go = _MARKER_CASES[case]
        lg, _n = _legend(mode, plots, "", scheme=scheme, go=go)
        fs = dr.OptionTranslator.css_to_pt(lg.label_text_font_size) * 4 / 3
        want = _twoway_marker(case)
        for it, tw in zip(lg.items, want):
            [p] = it.renderers
            assert str(p.name) == "__dash_keyproxy"
            real = p._dash_key_for
            assert p.glyph.size == real.glyph.size
            cb = p.glyph.defs["@dash_key"]
            assert cb.args["real"] is real
            assert cb.args["mk"] == real.glyph.marker
            got = (p.glyph.size + p.glyph.line_width) / fs
            assert abs(got - tw) < 0.01, (case, got, tw)
        width = (lg.items[0].renderers[0].glyph.size
                 + lg.items[0].renderers[0].glyph.line_width)
        # glyph_width is a whole px count, rounded again by scale().
        assert abs(lg.glyph_width - width) <= 1

    @pytest.mark.parametrize("mode", MODES)
    def test_angle(self, mode):
        """msangle(45) reaches the painter (mk_angle: twoway turns the
        square key 45 degrees)."""
        assert any("rotate(-45.00" in e["a"].get("transform", "")
                   for e in _TRUTH["mk_angle"]["els"])
        lg, _n = _legend(mode, [_sc(msymbol="S", msangle="45"),
                                _sc("headroom")], "")
        cb = lg.items[0].renderers[0].glyph.defs["@dash_key"]
        assert cb.args["mk"] == "square"
        assert abs(cb.args["angle"] - 0.785398) < 1e-4

    @pytest.mark.parametrize("mode", MODES)
    def test_marker_only_width(self, mode):
        """symxsize(30) leaves a marker-only legend's keys at the
        marker's width (mk_symx), and a legend with a line key keeps the
        key box (mk_line: the line key is symxsize wide)."""
        assert _key_marks("mk_symx") == _key_marks("mk_s2color")
        two = [_sc(), _sc("headroom")]
        plain, _n = _legend(mode, two, "")
        wide, _n = _legend(mode, two, "symxsize(30)")
        assert plain.glyph_width == wide.glyph_width < 10
        mixed, _n = _legend(mode, [_sc(), bk._p("line", y="headroom")], "")
        assert mixed.glyph_width == 50
        assert mixed.glyph_height >= 13


def _box_rules(legend):
    """``{item index (1-based): {part: {prop: value}}}`` of *legend*'s
    key-box stylesheet (``dash_legend_keybox``), each part ``glyph`` or
    ``label``."""
    import re
    css = _sheet(legend, "dash_legend_keybox")
    out = {}
    for n, part, body in re.findall(
            r"\.bk-item:nth-child\((\d+)\) \.bk-(glyph|label)\{([^}]*)\}",
            css):
        d = out.setdefault(int(n), {}).setdefault(part, {})
        for decl in body.split(";"):
            if ":" in decl:
                k, v = decl.split(":", 1)
                d[k.strip()] = v.strip()
    return out


def _em(v):
    return float(v[:-2]) if v.endswith("em") else float("nan")


class TestKeyBoxes:
    """LT-21 residual: twoway's key column is as wide as its widest key
    (legend_keys_truth.json cell_ctl: a marker key beside a line key in
    another column only its marker's width, 44.06 units -- the marker's
    size, its outline overhanging -- with its text one key gap after it,
    as the line's text is after the line; cols1: a marker in the line's
    column centred in the line's width, every text at one x).  Bokeh has
    one glyph_width a legend: dash keeps each canvas that wide and moves
    it and its text by the Legend's own stylesheet (dash_legend_keybox,
    _dash_legend_key_boxes), numbers only."""

    def test_fixture(self):
        marks = _key_marks("cell_ctl")
        t = _texts("cell_ctl")
        dot, line = marks
        # The marker's box is its size (the outline's centre line, r
        # 22.03), its ink 26.35 a side: the text one key gap after the
        # box, as the line's text is after the line.
        box_right = (dot[0] + dot[1]) / 2 + 22.03
        gap_dot = t["Mileage (mpg)"][0] - box_right
        gap_line = t["Price"][0] - line[1]
        assert abs(gap_dot - gap_line) < 0.5
        col = _key_marks("cols1")
        lines = [m for m in col if 300 < m[1] - m[0] < 1000]
        dots = [m for m in col if m[1] - m[0] < 100]
        assert len(lines) == 1 and len(dots) == 2
        for d in dots:
            assert abs((d[0] + d[1]) / 2 - (lines[0][0] + lines[0][1]) / 2) \
                < 0.2
        assert len({v[0] for k, v in _texts("cols1").items()
                    if k in ("Mileage (mpg)", "Price",
                             "Turn circle (ft.)")}) == 1

    @pytest.mark.parametrize("mode", MODES)
    def test_marker_beside_a_line(self, mode):
        """The marker's column is its size wide: its text moves back by
        the canvas's width less the marker's size; the line's item keeps
        its place; the canvas stays glyph_width wide, moved so the marker
        sits at the column's centre."""
        lg, _n = _legend(mode, [_sc(), bk._p("line", y="headroom")], "")
        fs = dr.OptionTranslator.css_to_pt(lg.label_text_font_size) * 4 / 3
        size = lg.items[0].renderers[0].glyph.size
        rules = _box_rules(lg)
        d = lg.glyph_width - size
        assert d > 20
        assert abs(_em(rules[1]["label"]["margin-left"]) + d / fs) < 0.01
        tx = rules[1]["glyph"]["translate"].split()[0]
        assert abs(float(tx[:-1]) + 100 * d / 2 / lg.glyph_width) < 0.1
        assert 2 not in rules

    @pytest.mark.parametrize("mode", MODES)
    def test_column_shares_the_widest(self, mode):
        """cols(1): one key column, the line's width: no item moves."""
        lg, _n = _legend(mode, [_sc(), bk._p("line", y="headroom"),
                                _sc("turn")], "cols(1)")
        assert _box_rules(lg) == {}

    @pytest.mark.parametrize("mode", MODES)
    def test_textfirst_moves_the_other_side(self, mode):
        lg, _n = _legend(mode, [_sc(), bk._p("line", y="headroom")],
                         "textfirst")
        rules = _box_rules(lg)
        assert "margin-right" in rules[1]["label"]
        assert float(rules[1]["glyph"]["translate"].split()[0][:-1]) > 0

    @pytest.mark.parametrize("mode", MODES)
    def test_markers_only_each_column_its_own(self, mode):
        """Two columns of markers, one large: the small marker's column is
        its own size wide (each column twoway's own width)."""
        lg, _n = _legend(mode, [_sc(msize="large"), _sc("headroom")], "")
        rules = _box_rules(lg)
        small = lg.items[1].renderers[0].glyph.size
        assert abs(_em(rules[2]["label"]["margin-left"])
                   + (lg.glyph_width - small) / (
                       dr.OptionTranslator.css_to_pt(
                           lg.label_text_font_size) * 4 / 3)) < 0.01

    def test_only_numbers_reach_the_css(self):
        import re
        lg, _n = _legend("saved", [_sc(), bk._p("line", y="headroom")],
                         'textfirst label(1 "a{}<b>;x")')
        css = _sheet(lg, "dash_legend_keybox")
        assert css
        assert re.fullmatch(r"[a-z0-9.%: ;{}()\-]+", css.replace(
            ".bk-grid .bk-item:nth-child", "").replace(".bk-", "")), css


def _glyph_move(legend, n):
    """``(x %, y %)`` of item *n*'s (1-based) canvas move, 0 for none."""
    t = _box_rules(legend).get(n, {}).get("glyph", {}).get("translate")
    if not t:
        return (0.0, 0.0)
    x, y = t.split()
    return (float(x[:-1]), float(y[:-1]))


#: symplacement()'s compass values: twoway's move of the keys in their row
#: (legend_keys_truth.json symp_*: up, down or none).
_SYMP = {"n": -1, "ne": -1, "nw": -1, "12": -1, "top": -1, "NE": -1,
         "sw": 1, "s": 1, "se": 1, "6": 1, "bottom": 1,
         "left": 0, "c": 0, "e": 0, "w": 0, "right": 0, "bogus": 0}


def _symp_case(v):
    return "symp_" + v if v in ("left", "n", "sw") else "symp_x" + v


class TestSymplacement:
    """LT-21 residual: symplacement() places each key in its row and its
    column (legend_keys_truth.json symp_*, cols1_symp_*): a north value
    puts the key's top -- a marker's size, a line's 44.06 units -- at the
    top of a box max(symysize(), the text size) high centred on the text
    (27.97 units up at s2color's sizes; symysize(6) 64.4; size(large)
    47.9; scale(1.5) 41.9), a south value its bottom at the box's bottom;
    in a column wider than the key, west and east put it at the column's
    left or right (cols1_symp_w, _e); a name twoway does not know is
    noted and drawn as the default."""

    def test_fixture(self):
        base = _key_marks("cell_ctl")
        for v, sign in _SYMP.items():
            got = _key_marks(_symp_case(v))
            for m, b in zip(got, base):
                assert abs(m[2] - b[2] - sign * 27.965) < 0.05, (v, m, b)
            assert [m[:2] for m in got] == [b[:2] for b in base], v
        assert "compass2dir" in _TRUTH["symp_xbogus"]["lines"][0]
        # The box is max(symysize(), the text size) high: the marker's
        # top (r 22.03) at its top.
        t = _texts("symp_n_symy")["Price"][1] - 0.35 * 99.99
        assert abs(_key_marks("symp_n_symy")[0][2] - (t - 172.8 / 2 + 22.03)) \
            < 0.1
        t = _texts("symp_n_size")["Price"][1] - 0.35 * 139.96
        assert abs(_key_marks("symp_n_size")[0][2] - (t - 139.96 / 2 + 22.03)) \
            < 0.1
        col, w, e = (_key_marks(c) for c in ("cols1", "cols1_symp_w",
                                             "cols1_symp_e"))
        line = [m for m in col if 300 < m[1] - m[0] < 1000][0]
        dots_w = [m for m in w if m[1] - m[0] < 100]
        dots_e = [m for m in e if m[1] - m[0] < 100]
        assert all(abs((d[0] + d[1]) / 2 - (line[0] + 22.03)) < 0.1
                   for d in dots_w)
        assert all(abs((d[0] + d[1]) / 2 - (line[1] - 22.03)) < 0.2
                   for d in dots_e)

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("v", ["n", "sw", "c", "left", "12", "NE"])
    def test_row_move(self, mode, v):
        """Each key moves up or down by its share of its canvas: half the
        box max(symysize(), text size) less its own half height."""
        lg, notes = _legend(mode, [_sc(), bk._p("line", y="headroom")],
                            "symplacement(%s)" % v)
        assert not any("symplacement" in str(n) for n in notes), notes
        fs = dr.OptionTranslator.css_to_pt(lg.label_text_font_size) * 4 / 3
        symy = 3.4722 * 2.88 * 4 / 3
        size = lg.items[0].renderers[0].glyph.size
        line_half = 22.03 / 28.8 * 2.88 * 4 / 3
        for n, half in ((1, size / 2), (2, line_half)):
            want = _SYMP[v] * (max(symy, fs) / 2 - half) / lg.glyph_height
            assert abs(_glyph_move(lg, n)[1] - 100 * want) < 1.5, (v, n)

    @pytest.mark.parametrize("mode", MODES)
    def test_column_w_and_e(self, mode):
        """cols(1): west puts the marker at the line's column's left, east
        at its right; the line does not move."""
        plots = [_sc(), bk._p("line", y="headroom"), _sc("turn")]
        for v, sign in (("w", -1), ("e", 1), ("ne", 1)):
            lg, _n = _legend(mode, plots, "cols(1) symplacement(%s)" % v)
            size = lg.items[0].renderers[0].glyph.size
            want = sign * (lg.glyph_width - size) / 2 / lg.glyph_width
            assert abs(_glyph_move(lg, 1)[0] - 100 * want) < 0.5, v
            assert _glyph_move(lg, 2)[0] == 0.0, v

    def test_bogus_is_noted(self):
        lg, notes = _legend("saved", [_sc(), bk._p("line", y="headroom")],
                            "symplacement(bogus)")
        assert any("bogus" in str(n) and "compass" in str(n)
                   for n in notes), notes
        assert _glyph_move(lg, 1) == _glyph_move(
            _legend("saved", [_sc(), bk._p("line", y="headroom")], "")[0], 1)


class TestNoteAndCaption:
    """LT-21 residual: legend(note()) and legend(caption()) are written
    under the keys inside the box, left-aligned, note in the scheme's
    small_body (79.94 of 99.99 units), caption in body, each line a text
    size apart (legend_keys_truth.json note, caption, note_caption,
    note_two, note_size, textfirst_note); dash writes them in the Legend's
    title slot below the keys (a DOM text node, never CSS), its stylesheet
    tagged dash_legend_note placing and sizing it.  Beside the legend's
    own title() or subtitle() twoway draws both (title_note,
    subtitle_note); the title slot holds one, so note() and caption()
    stay named there."""

    def test_fixture(self):
        for case, size in (("note", 79.94), ("caption", 99.99),
                           ("note_size", 139.96)):
            row = [e for e in _TRUTH[case]["els"] if e["tag"] == "text"
                   and e["text"] in ("N", "C")]
            assert len(row) == 1, case
            a = row[0]["a"]
            assert "text-anchor" not in a, case
            assert ("font-size:%.2fpx" % size) in a["style"], case
        # Left-aligned with the keys, under them.
        n = _texts("note")["N"]
        assert abs(n[0] - _key_marks("note")[0][0]) < 15
        assert n[1] > _texts("note")["Price"][1]
        n1, n2 = _texts("note_two")["N1"], _texts("note_two")["N2"]
        assert abs(n2[1] - n1[1] - 79.94) < 0.1
        assert _texts("textfirst_note")["N"][0] == n[0]
        # Beside the legend's title(), twoway draws both.
        t = _texts("title_note")
        assert "T" in t and "N" in t and t["T"][1] < t["N"][1]

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("opt,text", [('note("N")', "N"),
                                          ('caption("C")', "C"),
                                          ('note("N1" "N2")', "N1\nN2"),
                                          ('note("N") caption("C")',
                                           "N\nC")])
    def test_in_the_title_slot(self, mode, opt, text):
        lg, notes = _legend(mode, [_sc(), bk._p("line", y="headroom")], opt)
        assert lg.title == text
        assert lg.title_location == "below"
        assert lg.title_text_font_style == "normal"
        assert not any("note(" in str(n) or "caption(" in str(n)
                       for n in notes), notes
        css = _sheet(lg, "dash_legend_note")
        assert ".bk-title{" in css and "text-align:left" in css
        key = dr.OptionTranslator.css_to_pt(lg.label_text_font_size)
        box = dr.OptionTranslator.css_to_pt(lg.title_text_font_size)
        want = 0.8 if opt.startswith("note") and "caption" not in opt \
            else 1.0
        assert abs(box / key - want) < 0.01, (box, key)
        if "caption" in opt and "note" in opt:
            assert "::first-line{font-size:0.8em" in css

    @pytest.mark.parametrize("mode", MODES)
    def test_size(self, mode):
        lg, _n = _legend(mode, [_sc(), bk._p("line", y="headroom")],
                         'note("N", size(large))')
        key = dr.OptionTranslator.css_to_pt(lg.label_text_font_size)
        box = dr.OptionTranslator.css_to_pt(lg.title_text_font_size)
        assert abs(box / key - 139.96 / 99.99) < 0.02

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("opt", ['subtitle("S") caption("C")',
                                     'note("N1" "N2") caption("C")'])
    def test_still_named_beside_a_title(self, mode, opt):
        lg, notes = _legend(mode, [_sc(), bk._p("line", y="headroom")], opt)
        word = "caption(" if "caption" in opt else "note("
        assert any(word in str(n) for n in notes), notes
        assert _sheet(lg, "dash_legend_note") == "" or "N1" in opt


class TestWeightedMarkerKey:
    """LT-21 residual: twoway draws a weighted marker layer's key at the
    layer's own msize(), whatever the weights (legend_keys_truth.json
    wt_marker, wt_line, wt_trunk, wt_all: the key's circle r 26.35 as
    mk_s2color's; wt_large: 39.34 as mk_large's), where BokehJS drew a
    field-sized Scatter's key at 0.4 of the key box."""

    def test_fixture(self):
        for case, like in (("wt_marker", "mk_s2color"),
                           ("wt_line", "mk_line"), ("wt_trunk", "mk_line"),
                           ("wt_all", "mk_line"), ("wt_large", None)):
            w = _key_marks(case)[0][1] - _key_marks(case)[0][0]
            want = (_key_marks(like)[0][1] - _key_marks(like)[0][0]
                    if like else 2 * 39.34)
            assert abs(w - want) < 0.01, case
        assert abs(_key_marks("mk_large")[0][1]
                   - _key_marks("mk_large")[0][0] - 2 * 39.34) < 0.01

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("msize", ["", "large"])
    def test_painted_at_the_unweighted_size(self, mode, msize):
        o = {"weight": "aweight", "wexp": "headroom"}
        if msize:
            o["msize"] = msize
        plain, _n = _legend(mode, [_sc(**({"msize": msize} if msize
                                          else {})),
                                   bk._p("line", y="headroom")], "")
        lg, _n = _legend(mode, [_sc(**o), bk._p("line", y="headroom")], "")
        [p] = lg.items[0].renderers
        assert str(p.name) == "__dash_keyproxy"
        [q] = plain.items[0].renderers
        assert abs(p.glyph.size - q.glyph.size) < 1e-9
        assert isinstance(p._dash_key_for.glyph.size, str) or \
            "field" in str(p._dash_key_for.glyph.size)


def _tw_widths():
    """twoway's width estimate of each character of tw_width, in its
    text's size: ten of the character in an added text centred on its
    estimate's middle (placement(e) margin(zero)), its left end at its
    column's marker; ``{character: width}``."""
    import html
    row = _TRUTH["tw_width"]
    anchors = sorted({float(e["a"]["cx"]) for e in row["els"]
                      if e["tag"] == "circle"})
    chars = [chr(c) for c in range(32, 127) if c not in (34, 92, 96)]
    texts = []
    for e in row["els"]:
        t = html.unescape(e.get("text") or "")
        if e["tag"] == "text" and e["a"].get("text-anchor") == "middle" \
                and (t == "" or (len(t) == 10 and len(set(t)) == 1)):
            texts.append((t, e["a"]))
    texts = texts[:len(chars)]
    out = {}
    for ch, (t, a) in zip(chars, texts):
        assert t.replace("\xa0", " ").strip() == ch.strip() * (10 if
                                                                ch.strip()
                                                                else 0)
        x = float(a["x"])
        fs = float(a["style"].split("font-size:")[1].split("px")[0])
        out[ch] = 2 * (x - max(v for v in anchors if v < x)) / 10 / fs
    return out


def _tw_legend(case):
    """twoway's legend of fixture *case*: ``(box left, box width, graph
    width, graph height, [(text, start)], text size)``."""
    row = _TRUTH[case]
    W, H = row["viewbox"][2], row["viewbox"][3]
    texts = [(e["text"], float(e["a"]["x"]), float(e["a"]["y"]),
              float(e["a"]["style"].split("font-size:")[1].split("px")[0]))
             for e in row["els"] if e["tag"] == "text"
             and e["text"] in ("Mileage (mpg)", "Headroom (in.)",
                               "Repair record 1978", "Price",
                               "Turn circle (ft.)", "a" * 10, "a" * 12)]
    y = texts[0][2]
    [box] = [e["a"] for e in row["els"] if e["tag"] == "rect"
             and "fill:none" not in e["a"].get("style", "")
             and float(e["a"]["y"]) < y < float(e["a"]["y"])
             + float(e["a"]["height"]) and float(e["a"]["width"]) < 0.995 * W]
    return (float(box["x"]), float(box["width"]), W, H,
            [(t, x) for t, x, _y, _f in texts], texts[0][3])


class TestLegendFit:
    """twoway keeps a legend above or below the plot inside the graph: it
    lays the columns out by its own estimate of each text's width
    (tw_width), and a legend wider than the graph less the graph region's
    margin and 1.2 relative units (times scale()) a side is drawn that
    wide, its columns moved together, each text drawn whole
    (econ_long*, s2_long_scale, econ_a10, econ_a12).  dash sets the box's
    width and the columns' shares by the Legend's own stylesheet tagged
    ``dash_legend_fit`` (_dash_legend_fit); BokehJS would lay the columns
    out at the drawn texts' widths and overflow the figure."""

    def test_the_width_table(self):
        got = _tw_widths()
        assert len(got) == 92
        for ch, w in got.items():
            assert abs(w - dr._DASH_TW_CHAR_STEPS[ch]
                       * dr._DASH_TW_CHAR_STEP) < 0.0015, (ch, w)
        assert dr._dash_tw_text_em("") == 0
        assert dr._dash_tw_text_em("ab\nM") == pytest.approx(
            2 * 53 * dr._DASH_TW_CHAR_STEP)
        # A character twoway's table was not read for: a digit's width.
        assert dr._dash_tw_text_em("é") == pytest.approx(
            dr._dash_tw_text_em("0"))

    def test_the_estimate_is_the_columns_spacing(self):
        """econ3 fits: its columns' spacings differ by the estimates'
        difference of their texts (4.18 text sizes)."""
        _x, _w, _W, _H, texts, fs = _tw_legend("econ3")
        (t0, x0), (t1, x1), (_t2, x2) = texts
        got = ((x1 - x0) - (x2 - x1)) / fs
        want = dr._dash_tw_text_em(t0) - dr._dash_tw_text_em(t1)
        assert abs(got - want) < 0.005, (got, want)

    def test_the_limit(self):
        """The box from each edge: the graph region's margin (medium,
        zero, large) plus 1.2 units times scale(); s2color's legend,
        centred under the plot, meets the limit on its right."""
        M = dr._DASH_MARGIN_RS
        for case, m, k in (("econ_long", M["medium"], 1.0),
                           ("econ_long_m0", M["zero"], 1.0),
                           ("econ_long_ml", M["large"], 1.0),
                           ("econ_long_scale", M["medium"], 1.5)):
            x, w, W, H, _t, _f = _tw_legend(case)
            rs = min(W, H) / 100
            want = m + dr._DASH_LEGEND_FIT_RS * k
            assert abs(x / rs - want) < 0.01, case
            assert abs((W - x - w) / rs - want) < 0.01, case
        x, w, W, H, _t, _f = _tw_legend("s2_long_scale")
        assert abs((W - x - w) / (min(W, H) / 100)
                   - (M["medium"] + 1.5 * dr._DASH_LEGEND_FIT_RS)) < 0.01

    def test_the_columns_move_together(self):
        """econ_long: each column starts at the same share of its spacing
        at the estimate (0.813): the starts moved in proportion."""
        x, w, W, H, texts, fs = _tw_legend("econ_long")
        (t0, x0), (t1, x1), (_t2, x2) = texts
        _a, _b, _c, _d, ref, _f = _tw_legend("econ3")
        # The fixed part of a column's spacing (key, gaps), from econ3.
        fixed = (ref[1][1] - ref[0][1]) / fs - dr._dash_tw_text_em(ref[0][0])
        s0 = (x1 - x0) / fs / (dr._dash_tw_text_em(t0) + fixed)
        s1 = (x2 - x1) / fs / (dr._dash_tw_text_em(t1) + fixed)
        assert abs(s0 - s1) < 0.002 and 0.8 < s0 < 0.82, (s0, s1)

    def test_ten_fit_twelve_do_not(self):
        x, w, W, H, _t, _f = _tw_legend("econ_a10")
        lim = W - 2 * (dr._DASH_MARGIN_RS["medium"]
                       + dr._DASH_LEGEND_FIT_RS) * min(W, H) / 100
        assert w < lim - 5
        x, w, W, H, _t, _f = _tw_legend("econ_a12")
        assert abs(w - lim) < 0.05

    @pytest.mark.parametrize("mode", MODES)
    def test_the_fit_sheet(self, mode):
        """The long-texted economist legend: the box twoway's width in
        key text sizes (econ_long: 23.72), three columns' shares."""
        import re
        _x, w, _W, _H, _t, fs_tw = _tw_legend("econ_long")
        lg, _n = _legend(mode, [_sc(), _sc("headroom"), _sc("rep78")],
                         "cols(3)", scheme="economist")
        css = _sheet(lg, "dash_legend_fit")
        m = re.search(r"width:calc\(([0-9.e+]+)px \* var\(--dash-k, 1\)\)",
                      css)
        assert m, css
        fs =dr.OptionTranslator.css_to_pt(lg.label_text_font_size) \
            * dr.OptionTranslator.PX_PER_PT
        assert abs(float(m.group(1)) / fs - w / fs_tw) < 0.05, (css, fs)
        shares = re.findall(r"minmax\(0,([0-9.e+]+)fr\)", css)
        assert len(shares) == 3 and all(float(v) > 0 for v in shares)
        assert "box-sizing:border-box" in css
        # Only numbers and fixed words reach the CSS.
        assert "Mileage" not in css

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("plots, opt, scheme", [
        ([_sc(), _sc("price"), _sc("turn")], "cols(3)", "economist"),
        (_TWO, "", "s2color"),
        ([_sc(), _sc("headroom"), _sc("rep78")], "cols(1)", "economist"),
    ])
    def test_no_sheet_when_it_fits(self, mode, plots, opt, scheme):
        """econ3's texts fit (twoway's box 0.86 of the graph), as do a
        two-key s2color legend and the long texts in one column."""
        lg, _n = _legend(mode, plots, opt, scheme=scheme)
        assert _sheet(lg, "dash_legend_fit") == ""


class TestEndMarkersOnTheEnds:
    """PIC-11's documented difference, closed (WP-43 LT-21, batch 43.6):
    twoway centres rcapsym's, pccapsym's and dropline's end markers on
    the key's ends, overhanging the symxsize() box (sh_rcapsym: circles
    r 26.35 at the line's 730.37 and 1104.84, the text 59.9 after the
    line's end as after rcap's; sh_rcapsym_cols1: a marker key in that
    column centred on the line).  The canvas is the box plus the marker,
    moved so the box sits in its column and the text one key gap after
    the box; the painter draws no inset."""

    def test_fixture(self):
        for case in ("sh_rcapsym", "sh_pccapsym"):
            marks = _key_marks(case)
            line = [m for m in marks if 300 < m[1] - m[0] < 1000][0]
            dots = sorted((m[0] + m[1]) / 2 for m in marks
                          if m[1] - m[0] < 100 and m[0] < line[1] + 100)
            assert abs(dots[0] - line[0]) < 0.01 and \
                abs(dots[1] - line[1]) < 0.01, case
        t, tr = _texts("sh_rcapsym"), _texts("sh_rcap")
        assert t["Mileage (mpg)/Turn circle (ft.)"][0] == \
            tr["Mileage (mpg)/Turn circle (ft.)"][0]

    @pytest.mark.parametrize("mode", MODES)
    def test_canvas_and_moves(self, mode):
        [fig] = _figs(mode, [_shape_plot("rcapsym"), _sc()])
        [lg] = [l for l in fig.legend if l.items]
        shaft, ends = lg.items[0].renderers
        over = ends.glyph.size + ends.glyph.line_width
        fs = dr.OptionTranslator.css_to_pt(lg.label_text_font_size) * 4 / 3
        rules = _box_rules(lg)
        # The shape's item: the canvas half the overhang left, its text
        # back by the overhang.
        assert abs(_em(rules[1]["label"]["margin-left"]) + over / fs) < 0.02
        assert abs(_glyph_move(lg, 1)[0] + 100 * over / 2
                   / lg.glyph_width) < 0.2


class TestKeyPainter:
    """The painted key's proxy is 42-02's form: legend-only, on its
    layer's own source and view filter, out of every HoverTool and
    DataRange1d, its visible linked to the layer's; a colorvar layer's
    42-02 proxy is reused, never doubled."""

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("plots", [
        [_sc(), _sc("headroom")],
        [_sc(msymbol="T"), _sc("headroom", msymbol="D"), _sc("turn",
                                                          msymbol="X")],
        [_sc(connect="l"), bk._p("line", y="headroom")],
    ], ids=["two", "symbols", "connected"])
    def test_not_in_hover_or_range(self, mode, plots):
        from bokeh.models import DataRange1d, HoverTool
        [fig] = _figs(mode, plots)
        prox = _proxies(fig)
        assert prox
        for p in prox:
            real = p._dash_key_for
            assert real._dash_key_proxy is p
            assert p.data_source is real.data_source
            assert p.view.filter is real.view.filter
            assert p.tags == ["dash_key_proxy", str(real.name or "")]
            assert p.js_property_callbacks.get("change:visible")
            for f in ("x", "y"):
                v = getattr(p.glyph, f)
                v = getattr(v, "value", v)
                assert v != v
        for m in fig.references():
            if isinstance(m, HoverTool) and m.renderers != "auto":
                assert not set(map(id, m.renderers)) & set(map(id, prox))
            if isinstance(m, DataRange1d) and m.renderers != "auto":
                assert not set(map(id, m.renderers)) & set(map(id, prox))

    @pytest.mark.parametrize("mode", MODES)
    def test_colorvar_proxy_reused(self, mode):
        """scatter mpg weight, colorvar(rep78): the layer keeps its one
        42-02 proxy, its glyph now the painter, its colours kept."""
        [fig] = [f for f in _figs(mode, [_sc(colorvar="rep78"),
                                         _sc("headroom")]) if _proxies(f)]
        cv = [p for p in _proxies(fig)
              if p._dash_key_for is fig.renderers[0]]
        assert len(cv) == 1
        [p] = cv
        assert "@dash_key" in p.glyph.defs
        assert str(p.glyph.fill_color).lower() == "#1a476f"

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("plots,go,n", [
        ([_sc()], {}, 0),
        ([_sc(), _sc("headroom")], {"legend": "off"}, 0),
        ([_sc(), _sc("headroom")], {"legend": "nodraw"}, 0),
        ([_sc()], {"legend": "on"}, 1),
        ([_sc(), _sc("headroom")], {}, 2),
    ], ids=["one_key", "off", "nodraw", "one_key_on", "two"])
    def test_only_a_drawn_legend_is_painted(self, mode, plots, go, n):
        """A legend twoway does not draw (one key, off, nodraw) gets no
        key proxy: it would be a renderer, a source view and a painter in
        the page for a key nobody sees (WP-43 LT-21)."""
        [fig] = _figs(mode, plots, go=go)
        assert len(_proxies(fig)) == n

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("legend", [
        "order(1 2 1)", 'order(1 2 1) lastlabel(3 "Z")'])
    def test_a_repeated_key_has_one_proxy(self, mode, legend):
        """order(1 2 1) draws plot 1's key twice, in one shared item, and
        lastlabel() on the repeat a fresh item with the same layer: each
        layer keeps one proxy, both rows hold it, and the legend of
        markers stays as wide as its marker."""
        [fig] = _figs(mode, [_sc(), _sc("headroom")], go={"legend": legend})
        prox = _proxies(fig)
        assert len(prox) == 2
        [lg] = [l for l in fig.legend if l.items]
        assert lg.items[0].renderers == lg.items[2].renderers
        assert all(r in prox for it in lg.items for r in it.renderers)
        g = prox[0].glyph
        assert lg.glyph_width == int(round(g.size + g.line_width))

    def test_unpaintable_glyphs_keep_their_key(self):
        """A field-sized marker (a weighted layer) keeps Bokeh's key."""
        from bokeh.models import ColumnDataSource, Legend, LegendItem
        from bokeh.plotting import figure
        f = figure()
        src = ColumnDataSource({"x": [1.0], "y": [1.0], "s": [3.0]})
        r = f.scatter("x", "y", size="s", source=src)
        lg = Legend(items=[LegendItem(label="a", renderers=[r])])
        assert dr._dash_key_painter(f, lg) == 0
        assert lg.items[0].renderers == [r]

    def test_spec_value(self):
        from bokeh.core.properties import field, value
        assert dr._dash_spec_value(3.0) == 3.0
        assert dr._dash_spec_value(value(2.0)) == 2.0
        assert dr._dash_spec_value({"value": "red"}) == "red"
        assert dr._dash_spec_value(field("s")) is None
        assert dr._dash_spec_value({"field": "s"}) is None

    def test_stale_follow_finds_a_painted_item(self):
        """The served stale cue reaches an item that holds the frozen
        layer's proxy (_dash_points_stale_follow)."""
        from bokeh.models import ColumnDataSource, Legend, LegendItem
        from bokeh.plotting import figure
        f = figure()
        src = ColumnDataSource({"x": [1.0], "y": [1.0]})
        r = f.scatter("x", "y", size=6, source=src)
        lg = Legend(items=[LegendItem(label="Fit", renderers=[r])])
        f.add_layout(lg)
        assert dr._dash_key_painter(f, lg) == 1
        cue = dr._dash_stale_cue_title()
        dr._dash_points_stale_follow({("g1", 0): {
            "frozen": [r], "cue": cue, "fig": f, "stale": True}})
        assert lg.items[0].label.value == \
            "Fit" + dr._DASH_STALE_SUFFIX["fit"]


def _paint(real_count, size, mk="circle", angle=0.0):
    """The ctx calls _DASH_KEY_PAINT_JS makes under node for a layer whose
    own view keeps *real_count* rows (None: a view with no indices yet)."""
    import js_runner
    code = dr._DASH_KEY_PAINT_JS
    view = ("null" if real_count is None
            else "{indices: {count: %d}}" % real_count)
    src = """
const calls = [];
const ctx = new Proxy({}, {get: (t, k) => (...a) => { calls.push(k); }});
const visuals = {fill: {apply: () => calls.push("fill")},
                 hatch: {apply: () => {}},
                 line: {apply: () => calls.push("line")}};
const run = new Function("real", "mk", "angle", "cb_obj", "cb_data", %s);
run({view: %s}, %s, %s, {size: {value: %s}},
    {ctx, i: 0, r: 2, visuals});
process.stdout.write(JSON.stringify(calls));
""" % (json.dumps(code), view, json.dumps(mk), json.dumps(angle),
       json.dumps(size))
    return js_runner.run_js(src)


class TestThePainterScript:
    """The painter draws from its args and the glyph's size, and draws
    nothing while its layer's own view keeps no row, as BokehJS's
    draw_legend skips a renderer whose view is empty (R4-26)."""

    def test_draws_at_the_glyph_size(self):
        import js_runner
        js_runner.node()
        calls = _paint(3, 9.0)
        assert "arc" in calls and "fill" in calls and "line" in calls
        sq = _paint(3, 9.0, "square", 0.785)
        assert "rect" in sq and "rotate" in sq

    @pytest.mark.parametrize("count", [0, None])
    def test_empty_view_draws_nothing(self, count):
        import js_runner
        js_runner.node()
        assert _paint(count, 9.0) == []

    def test_bad_size_draws_nothing(self):
        import js_runner
        js_runner.node()
        assert _paint(3, -1) == [] and _paint(3, 1e9) == []


# ---------------------------------------------------------------------------
# PIC-11: the keys of rcap, rcapsym, pccapsym, dropline, pcarrow, pcbarrow
# and rarea in twoway's shapes
# ---------------------------------------------------------------------------

#: twoway's SVG units per legend unit and dash's px per unit (s2color, a
#: 2880-unit-high graph; legend_geometry_truth.json's own constants).
_SVG_PER_UNIT = 28.8
_PX_PER_UNIT = 2.88 * 4.0 / 3.0


def _shape_plot(t, **o):
    """*t*'s plot over the auto columns this file's pages carry."""
    from test_server_layer_defects import plot_for
    p = plot_for(t, dict(o))
    return {k: (v.replace("price", "headroom").replace("foreign", "headroom")
                if isinstance(v, str) else v) for k, v in p.items()}


def _twoway_shape(case):
    """twoway's first key of fixture *case*, below its plot region: the
    key's lines ``[(x1, y1, x2, y2), ...]``, circles ``[(cx, cy, r)]`` and
    rects ``[(x, y, w, h, style)]`` in SVG units."""
    row = _TRUTH[case]
    pb = row["plot"]["bottom"] + 150
    lines, circles, rects = [], [], []
    for e in row["els"]:
        a = e["a"]
        if e["tag"] == "line" and float(a["y1"]) > pb:
            lines.append(tuple(float(a[k]) for k in ("x1", "y1", "x2",
                                                      "y2")))
        elif e["tag"] == "circle" and float(a["cy"]) > pb \
                and "fill:none" not in a.get("style", ""):
            circles.append((float(a["cx"]), float(a["cy"]), float(a["r"])))
        elif e["tag"] == "rect" and float(a["y"]) > pb \
                and float(a["height"]) < 150:
            rects.append((float(a["x"]), float(a["y"]), float(a["width"]),
                          float(a["height"]), a.get("style", "")))
    x0 = min([min(l[0], l[2]) for l in lines] + [r[0] for r in rects])
    x1 = x0 + 400
    return ([l for l in lines if l[0] <= x1 and l[2] <= x1],
            [c for c in circles if c[0] <= x1],
            [r for r in rects if r[0] <= x1])


def _shape_args(it):
    return [(p.glyph.defs["@dash_key"].args.get("shape"),
             p.glyph.defs["@dash_key"].args.get("ends"))
            for p in it.renderers]


_SHAPES = {
    "rcap": [("cap", 2)],
    "rcapsym": [("shaft", 2), ("ends", 2)],
    "pccapsym": [("shaft", 2), ("ends", 2)],
    "dropline": [("shaft", 1), ("ends", 1)],
    "pcarrow": [("head", 1)],
    "pcbarrow": [("head", 2)],
    "rarea": [(("rect"), None)],
}


class TestKeyShapes:
    """Each of the seven plot types is keyed in twoway's shape (PIC-11,
    legend_keys_truth.json sh_*) by key proxies in 42-02's form, the key
    box symxsize() long as twoway's line keys are."""

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("ptype", sorted(_SHAPES))
    def test_shape(self, mode, ptype):
        [fig] = _figs(mode, [_shape_plot(ptype), _sc()])
        [lg] = [l for l in fig.legend if l.items]
        it = lg.items[0]
        assert it.renderers and all(is_key_proxy(p) for p in it.renderers)
        assert _shape_args(it) == _SHAPES[ptype]
        layer = [r for r in drawn_renderers(fig)
                 if not is_key_proxy(r)][:6]
        for p in it.renderers:
            assert p._dash_key_for in layer
            assert p._dash_key_for._dash_key_proxy is p
            assert p.data_source is p._dash_key_for.data_source
            assert p.js_property_callbacks.get("change:visible")
        # twoway's line keys are symxsize() long (sh_*: 374.47 of 2880
        # units, 13 units); the marker key beside them keeps that box.
        lines, _c, rects = _twoway_shape("sh_" + ptype)
        span = max([abs(l[2] - l[0]) for l in lines]
                   + [r[2] for r in rects])
        symx = int(round(span / _SVG_PER_UNIT * _PX_PER_UNIT))
        assert symx == 50
        # Flipped (WP-43 LT-21, batch 43.6): an end marker is centred on
        # its end (TestEndMarkersOnTheEnds), so the canvas of a legend
        # holding one is the key box plus the marker; the painter draws
        # the shape in the box (kw).
        ends = [p for p in it.renderers
                if p.glyph.defs["@dash_key"].args.get("shape") == "ends"]
        over = (ends[0].glyph.size + ends[0].glyph.line_width) if ends \
            else 0.0
        assert lg.glyph_width == int(round(symx + over))
        for p in it.renderers:
            kw = p.glyph.defs["@dash_key"].args.get("kw", 1.0)
            assert abs(kw * lg.glyph_width - symx) < 1e-6

    @pytest.mark.parametrize("mode", MODES)
    def test_rcap_caps_are_the_cap_size(self, mode):
        """rcap's caps are its cap marker's size: 44.05 units high at
        s2color (sh_rcap), drawn 5.87 px."""
        [fig] = _figs(mode, [_shape_plot("rcap"), _sc()])
        [p] = [l for l in fig.legend if l.items][0].items[0].renderers
        lines, _c, _r = _twoway_shape("sh_rcap")
        caps = [abs(l[3] - l[1]) for l in lines if l[0] == l[2]]
        assert len(caps) == 2
        want = caps[0] / _SVG_PER_UNIT * _PX_PER_UNIT
        assert p.glyph.size == pytest.approx(want, abs=0.05)

    @pytest.mark.parametrize("mode", MODES)
    def test_ends_carry_the_marker(self, mode):
        """rcapsym's, pccapsym's and dropline's ends are the layer's marker
        (sh_rcapsym: a circle r 26.35 centred on each end of the line;
        sh_dropline on its right end), at the marker's size."""
        for t in ("rcapsym", "dropline"):
            [fig] = _figs(mode, [_shape_plot(t), _sc()])
            shaft, ends = [l for l in fig.legend
                           if l.items][0].items[0].renderers
            _l, circles, _r = _twoway_shape("sh_" + t)
            assert len(circles) == (2 if t == "rcapsym" else 1)
            want = 2 * circles[0][2] / _SVG_PER_UNIT * _PX_PER_UNIT
            g = ends.glyph
            assert g.size + g.line_width == pytest.approx(want, abs=0.1)
            args = shaft.glyph.defs["@dash_key"].args
            assert args["mark"] is g

    @pytest.mark.parametrize("mode", MODES)
    def test_arrow_head(self, mode):
        """pcarrow's head: two barbs back from the tip, 38.61 x 21.03
        units (sh_pcarrow): 43.97 units long at 28.6 degrees."""
        [fig] = _figs(mode, [_shape_plot("pcarrow"), _sc()])
        [p] = [l for l in fig.legend if l.items][0].items[0].renderers
        lines, _c, _r = _twoway_shape("sh_pcarrow")
        barbs = [l for l in lines if l[1] != l[3]]
        assert len(barbs) == 2
        dx, dy = abs(barbs[0][2] - barbs[0][0]), abs(barbs[0][3]
                                                     - barbs[0][1])
        args = p.glyph.defs["@dash_key"].args
        assert args["angle"] == pytest.approx(math.atan2(dy, dx), abs=0.01)
        assert p.glyph.size == pytest.approx(
            math.hypot(dx, dy) / _SVG_PER_UNIT * _PX_PER_UNIT, abs=0.1)

    @pytest.mark.parametrize("mode", MODES)
    def test_rarea_rect(self, mode):
        """rarea's key: a rect the key box's size (sh_rarea: 374.47 x
        99.99 units) in the area's fill, outlined inside its edge in the
        outline's colour and width."""
        [fig] = _figs(mode, [_shape_plot("rarea"), _sc()])
        [lg] = [l for l in fig.legend if l.items]
        [p] = lg.items[0].renderers
        _l, _c, rects = _twoway_shape("sh_rarea")
        fill = [r for r in rects if "fill:none" not in r[4]][0]
        line = [r for r in rects if "fill:none" in r[4]][0]
        assert lg.glyph_height == int(round(fill[3] / _SVG_PER_UNIT
                                            * _PX_PER_UNIT))
        g = p.glyph
        assert g.fill_color.lower() == fill[4].split("fill:")[1][:7].lower()
        assert g.line_color.lower() == line[4].split("stroke:")[1][:7].lower()
        # The outline inside the edge: inset by half its width.
        assert line[0] - fill[0] == pytest.approx(
            float(line[4].split("stroke-width:")[1]) / 2, abs=0.01)

    @pytest.mark.parametrize("mode", MODES)
    def test_by_matches_every_panel(self, mode):
        """by()'s legend cell holds the painted shape's clones and every
        panel's proxies of it (42-02's _dash_key_for branch of
        _dash_by_panel_matches); each proxy's visible is linked to every
        renderer of its layer, so a click hides the series everywhere."""
        from bokeh.models import Legend
        figs = _figs(mode, [_shape_plot("rcapsym"), _sc()],
                     go={"by": "foreign"})
        cells = list({id(lg): lg for f in figs
                      for lg in f.select({"type": Legend})
                      if str(lg.name or "") == "dash_by_legend_key"}
                     .values())
        assert len(cells) == 1
        item = cells[0].items[0]
        prox = [r for r in item.renderers if is_key_proxy(r)]
        panels = [f for f in figs if _proxies(f)]
        assert len(panels) == 2
        assert len(prox) == 4          # shaft and ends, in both panels
        assert {id(p) for p in prox} == {id(p) for f in panels
                                         for p in _proxies(f)
                                         if p in prox}
        for p in prox:
            n = len(p.js_property_callbacks.get("change:visible", []))
            assert n >= (1 if p.glyph.defs["@dash_key"].args["shape"]
                         == "shaft" else 2), p

    @pytest.mark.parametrize("mode", MODES)
    def test_one_proxy_per_renderer(self, mode):
        """A shape item's renderers each keep one proxy, a repeated key
        (order(1 2 1)) included."""
        [fig] = _figs(mode, [_shape_plot("rcapsym"), _sc()],
                      go={"legend": "order(1 2 1)"})
        prox = _proxies(fig)
        assert len(prox) == len({id(p._dash_key_for) for p in prox}) == 3
        [lg] = [l for l in fig.legend if l.items]
        assert lg.items[0].renderers == lg.items[2].renderers


def _paint_shape(shape, ends, count=3, size=6.0, gw=50, gh=13, barb=0.0):
    """The ctx calls _DASH_KEY_PAINT_JS makes under node for *shape*."""
    import js_runner
    src = """
const calls = [];
const ctx = new Proxy({}, {get: (t, k) => (...a) => {
  calls.push([k, a.map((v) => Math.round(v * 100) / 100)]); }});
const visuals = {fill: {apply: () => calls.push(["fill"])},
                 hatch: {apply: () => {}},
                 line: {apply: () => calls.push(["line"])}};
const run = new Function("real", "mk", "angle", "shape", "ends", "legend",
                         "mark", "barb", "cb_obj", "cb_data", %s);
run({view: {indices: {count: %d}}}, "circle", 0.5, %s, %s,
    {glyph_width: %s, glyph_height: %s}, {size: 6, line_width: 1},
    %s, {size: {value: %s}, line_width: {value: 1}},
    {ctx, i: 0, visuals});
process.stdout.write(JSON.stringify(calls));
""" % (json.dumps(dr._DASH_KEY_PAINT_JS), count, json.dumps(shape),
       json.dumps(ends), gw, gh, json.dumps(barb), json.dumps(size))
    return js_runner.run_js(src)


class TestTheShapeScript:
    """The painter draws each shape from its args and the legend's key
    box, and nothing while its layer's view keeps no row."""

    def test_cap(self):
        import js_runner
        js_runner.node()
        calls = _paint_shape("cap", 2)
        moves = [c[1] for c in calls if c[0] in ("moveTo", "lineTo")]
        # The line across the box, then a cap of the size at each end.
        assert moves[:2] == [[-25, 0], [25, 0]]
        assert [-24.5, -3] in moves and [24.5, 3] in moves

    def test_ends_and_shaft(self):
        import js_runner
        js_runner.node()
        two = [c for c in _paint_shape("ends", 2) if c[0] == "translate"]
        one = [c for c in _paint_shape("ends", 1) if c[0] == "translate"]
        # Each marker centred on an end moved in by its outer half size.
        assert two == [["translate", [-21.5, 0]], ["translate", [21.5, 0]]]
        assert one == [["translate", [21.5, 0]]]
        shaft = [c[1] for c in _paint_shape("shaft", 1)
                 if c[0] in ("moveTo", "lineTo")]
        assert shaft == [[-25, 0], [21.5, 0]]

    def test_head_and_rect(self):
        import js_runner
        js_runner.node()
        head = [c[1] for c in _paint_shape("head", 2)
                if c[0] in ("moveTo", "lineTo")]
        assert [-24.5, 0] in head and [24.5, 0] in head
        rect = [c for c in _paint_shape("rect", 0) if c[0] == "rect"]
        assert rect[0][1] == [-25, -6.5, 50, 13]
        assert rect[1][1] == [-24.5, -6, 49, 12]

    @pytest.mark.parametrize("shape", ["cap", "ends", "shaft", "head",
                                       "rect"])
    def test_empty_view_draws_nothing(self, shape):
        import js_runner
        js_runner.node()
        assert _paint_shape(shape, 2, count=0) == []
