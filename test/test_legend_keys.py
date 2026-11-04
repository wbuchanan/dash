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
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_by_axes_keys as bk  # noqa: E402

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
