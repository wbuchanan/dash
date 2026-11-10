"""
test_varlabel_options.py -- yvarlabel() and xvarlabel() stand in for the
variables' labels in the default axis titles and the legend keys, as twoway
draws them (WP-31 D8).

The defect (measured at 0aa96dc): neither option was declared; ``dash
scatter mpg weight, xvarlabel("Pounds")`` drew "Weight (lbs.)" and named
the option in the generic note.

twoway (StataNow 19.5, scripts/extract_varlabel_mlabel_truth.do, fixture
test/fixtures/varlabel_mlabel_truth.json): ``yvarlabel("Miles")`` titles
the y axis "Miles", ``xvarlabel("Pounds")`` the x axis "Pounds";
``xvarlabel("")`` draws no x title; ``scatter mpg price weight,
yvarlabel("A" "B")`` keys the legend "A" and "B" (one string per y
variable, advanced_options.sthlp); all rc 0 without a note.

This file also holds the helpers the other S34 files share.
"""
import hashlib
import json
import os
import re
import sys
import warnings

import pandas as pd
import pytest
from bokeh.document import Document

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)
sys.path.insert(0, _ROOT)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from conftest import load_app, make_data_json, render_models  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "varlabel_mlabel_truth.json")
with open(_FIXTURE, encoding="utf-8") as _fh:
    T = json.load(_fh)

MODES = ("saved", "served")
VL = {"mpg": "Mileage (mpg)", "weight": "Weight (lbs.)", "price": "Price",
      "lo": "lo", "hi": "hi", "make": "Make and Model"}
DF = pd.DataFrame({
    "mpg": [22.0, 17.0, 22.0], "weight": [2930.0, 3350.0, 2640.0],
    "price": [4099.0, 4749.0, 3799.0],
    "lo": [20.0, 15.0, 20.0], "hi": [24.0, 19.0, 24.0],
    "make": ["AMC Concord", "AMC Pacer", "AMC Spirit"],
})
_N = [0]


def ado_text():
    with open(os.path.join(_ROOT, "dash.ado"), encoding="utf-8") as fh:
        return fh.read()


def mata_text():
    with open(os.path.join(_ROOT, "dash_parse.mata"), encoding="utf-8") as fh:
        return fh.read()


def figs(mode, tmp_path, plots, df=DF, vl=VL, bo=None, go=None):
    """(figures, notes) of one graph of *plots* over *df* in *mode*."""
    spec = tp._spec(plots, bo, go)
    _N[0] += 1
    sp = os.path.join(str(tmp_path), "spec_%d.json" % _N[0])
    dp = os.path.join(str(tmp_path), "data_%d.json" % _N[0])
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    data = make_data_json(df, variable_labels=vl)
    # Real jsonio marks a string variable (the served app coerces an
    # unmarked column to NaN).
    for c in df.columns:
        if pd.api.types.is_string_dtype(df[c]) or df[c].dtype == object:
            data["StataJSON"]["variableIsString"][c] = True
            data["StataJSON"]["variableTypeIsString"][c] = True
    with open(dp, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    if mode == "saved":
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            r = dr.DashRenderer(sp, dp, os.path.join(str(tmp_path),
                                                     "o_%d.html" % _N[0]))
            render_models(r)
        return list(r.figures.values()), [str(w.message) for w in caught]
    ap = os.path.join(str(tmp_path), "app_%d.py" % _N[0])
    with warnings.catch_warnings(record=True) as built:
        warnings.simplefilter("always")
        dr.ServerAppBuilder(sp, dp).build(ap)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mod = load_app(ap, "_s34_app_%d" % _N[0], draw=False)
    from bokeh.io import curdoc
    curdoc().clear()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        doc = Document()
        mod.make_document(doc)
    out = [m for m in tp._walk_models(doc) if type(m).__name__ == "figure"]
    return out, [str(w.message) for w in list(built) + list(caught)]


def axis_titles(fig):
    """(y title, x title) as drawn ("" for none)."""
    return (fig.yaxis[0].axis_label or "", fig.xaxis[0].axis_label or "")


def legend_keys(fig):
    out = []
    for lg in fig.legend:
        for it in lg.items:
            lab = it.label
            out.append(lab.get("value") if isinstance(lab, dict)
                       else getattr(lab, "value", lab))
    return out


def sc(**o):
    return {"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": o}


# ---------------------------------------------------------------------------
# The fixture
# ---------------------------------------------------------------------------

class TestTheFixture:

    def test_meta(self):
        assert sorted(T["_meta"]) == ["born_date", "dash_commit", "extracted",
                                      "source", "stata_version"]
        assert all(T["_meta"][k] for k in T["_meta"])
        assert T["_meta"]["source"] == \
            "scripts/extract_varlabel_mlabel_truth.do"

    def test_keys(self):
        # WP-47 47-02: varformat, mlabel_pattern and empty added.
        assert sorted(T) == ["_meta", "align", "bardefault", "c14", "empty",
                             "malign", "mlabel_pattern", "mlabstyle",
                             "mlalign", "msangle", "mwidth", "prefix",
                             "varformat", "varlabel"]
        v = T["varlabel"]
        assert (v["both"]["ytitle"], v["both"]["xtitle"]) == ("Miles",
                                                             "Pounds")
        assert v["x_empty"]["xtitle"] is None
        assert all(v[k]["rc"] == 0 and v[k]["notes"] == [] for k in v)


# ---------------------------------------------------------------------------
# The series labels
# ---------------------------------------------------------------------------

_SERIES = {
    # case: (options, expected (y, x)) -- read from the fixture's titles.
    # The spec carries each value as typed, quotes and all (dash.ado
    # _dash_label_split and _dash_varlabel_tail).
    "y": ({"yvarlabel": '"Miles"'}, ("varlabel", "y")),
    "x": ({"xvarlabel": '"Pounds"'}, ("varlabel", "x")),
    "both": ({"yvarlabel": '"Miles"', "xvarlabel": '"Pounds"'},
             ("varlabel", "both")),
    "x_empty": ({"xvarlabel": '""'}, ("varlabel", "x_empty")),
}


class TestVarlabels:

    @pytest.mark.parametrize("case", sorted(_SERIES))
    def test_series(self, case):
        opts, (g, k) = _SERIES[case]
        rec = T[g][k]
        got = dr._dash_layer_series(sc(**opts), VL)
        assert got == [(rec["ytitle"] or "", rec["xtitle"] or "")]

    def test_range_and_fit_layers(self):
        v = T["varlabel"]

        def rng(**o):
            return dr._dash_layer_series(
                {"type": "rscatter", "yvar1": "lo", "yvar2": "hi",
                 "xvar": "weight", "options": o}, VL)

        def fit(t, **o):
            return dr._dash_layer_series(
                {"type": t, "yvar": "mpg", "xvar": "weight", "options": o},
                VL)

        assert rng(yvarlabel='"Band"', xvarlabel='"Pounds"') == [
            (v["range"]["ytitle"], v["range"]["xtitle"])]
        # The second string is the upper boundary's (compound quotes too).
        assert rng(yvarlabel='"Band" `"Top"\'')[0][0] == "Band/Top"
        assert v["range_two"]["ytitle"] == "Band/Top"
        assert fit("lfit", yvarlabel='"Q"', xvarlabel='"Pounds"') == [
            (v["fit"]["ytitle"], v["fit"]["xtitle"])]
        # A ci fit: the band "Q/95% CI", the line "Q", as twoway keys them.
        assert [y for y, _ in fit("lfitci", yvarlabel='"Q"')] == \
            [t["text"] for t in v["fitci"]["texts"]][-2:]
        # pc and the x pair: xvarlabel() is the first x's only.
        pc = dr._dash_layer_series(
            {"type": "pcspike", "y1var": "lo", "x1var": "weight",
             "y2var": "hi", "x2var": "mpg",
             "options": {"xvarlabel": '"P"'}}, VL)
        assert pc == [("lo/hi", "P/Mileage (mpg)")]

    @pytest.mark.parametrize("mode", MODES)
    def test_axis_titles(self, mode, tmp_path):
        for case in ("both", "x_empty"):
            rec = T["varlabel"][case]
            f, notes = figs(mode, tmp_path, [sc(**_SERIES[case][0])])
            assert axis_titles(f[0]) == (rec["ytitle"] or "",
                                         rec["xtitle"] or ""), case
            assert not [n for n in notes if "varlabel" in n], notes

    @pytest.mark.parametrize("mode", MODES)
    def test_legend_keys(self, mode, tmp_path):
        rec = T["varlabel"]["y_two"]
        f, _ = figs(mode, tmp_path,
                    [sc(yvarlabel='"A" "B"'),
                     {"type": "scatter", "yvar": "price", "xvar": "weight",
                      "options": {"yvarlabel": '"B"'}}])
        keys = legend_keys(f[0])
        assert keys == ["A", "B"]
        texts = [t["text"] for t in rec["texts"]]
        assert "A" in texts and "B" in texts and "Price" not in texts

    def test_unchanged_without_the_options(self):
        # Every bare plot type's series, digested at 0aa96dc: the options
        # absent, nothing moves.
        types = ("scatter line connected area bar spike lfit qfit lfitci "
                 "qfitci lowess lpoly lpolyci fpfit fpfitci histogram "
                 "kdensity rarea rbar rspike rcap rline rconnected dot "
                 "dropline rcapsym scatteri pcspike pcarrow pcbarrow pci "
                 "pcscatter tsline tsrline mspline mband rscatter function "
                 "pccapsym pcarrowi rpcap rpspike contour contourline").split()
        vl = {"mpg": "Mileage (mpg)", "weight": "Weight (lbs.)",
              "price": "Price", "foreign": "Car origin"}
        rows = [dr._dash_layer_series(plot_for(t), vl) for t in types]
        assert hashlib.sha256(json.dumps(rows, sort_keys=True).encode()
                              ).hexdigest() == (
            "f360495c08e199eac9c9e32526871eed1db06831a06ebf7ec6056496b1a59c86")


# ---------------------------------------------------------------------------
# The declarations
# ---------------------------------------------------------------------------

class TestTheDeclarations:

    def test_each_name(self):
        ado = ado_text()
        assert "YVARLabel(string asis) XVARLabel(string asis)" in ado
        assert "_dash_label_split" in ado
        for o in ("yvarlabel", "xvarlabel"):
            assert re.search(r"sreturn local %s\s+: copy local %s" % (o, o),
                             ado), o
        m = re.search(r"foreach key in mcolor msymbol(.*?)\{", ado, re.S)
        keys = m.group(1).replace("///", " ").split()
        assert {"yvarlabel", "xvarlabel"} <= set(keys)
        m = re.search(r"string scalar _dash_stylelist_keys\(\)\s*\{(.*?)\}",
                      mata_text(), re.S)
        # Not stylelists: a range layer's two boundaries read two strings
        # and a quoted "" is a value (_dash_varlabel_tail).
        sl = m.group(1).replace('"', " ").split()
        assert "yvarlabel" not in sl and "xvarlabel" not in sl
        assert "_dash_varlabel_tail(st_global(\"s(yvarlabel)\"), `series')" \
            in ado


# ---------------------------------------------------------------------------
# WP-47 MS-2 (with TR-6): every plot type takes yvarlabel()/xvarlabel()
# ---------------------------------------------------------------------------
#
# The defect (measured at f9bf176): scatteri, pci, pcarrowi, function,
# kdensity and histogram kept their fixed texts ("y"/"x", "y/yb"/"x/xb",
# the function's name, "kdensity mpg"/"x", the scale word) whatever
# yvarlabel()/xvarlabel() gave.  twoway (varlabel_mlabel_truth.json, the
# MS-2 rows): scatteri and function are titled Q/R, kdensity D/M,
# histogram "D/Density" over M ("D/Frequency" under frequency), pci and
# pcarrowi "Q/R" over the two lines "S" and "/xb"; a function keyed by
# yvarlab("y=x") is keyed "y=x".

def _fn(**o):
    return {"type": "function", "expr": "x", "yname": "y",
            "options": dict({"range": "0 1"}, **o)}


_MS2 = {
    # case: (plots, index of the plot under test)
    "scatteri": ([{"type": "scatteri", "values": [[20.0, 3000.0],
                                                  [25.0, 4000.0]],
                   "options": {"yvarlabel": '"Q"', "xvarlabel": '"R"'}}], 0),
    "function": ([_fn(yvarlabel='"Q"', xvarlabel='"R"')], 0),
    "function_key": ([sc(), {"type": "function", "expr": "20",
                             "yname": "y",
                             "options": {"range": "2000 4000",
                                         "yvarlabel": '"y=x"'}}], 1),
    "kdensity": ([{"type": "kdensity", "var": "mpg",
                   "options": {"xvarlabel": '"M"', "yvarlabel": '"D"'}}], 0),
    "histogram": ([{"type": "histogram", "var": "mpg",
                    "options": {"xvarlabel": '"M"', "yvarlabel": '"D"'}}], 0),
    "histfreq": ([{"type": "histogram", "var": "mpg",
                   "options": {"frequency": "frequency",
                               "yvarlabel": '"D"'}}], 0),
    "pci": ([{"type": "pci", "values": [[20.0, 2000.0, 30.0, 4000.0]],
              "options": {"yvarlabel": '"Q" "R"', "xvarlabel": '"S"'}}], 0),
    "pcarrowi": ([{"type": "pcarrowi",
                   "values": [[20.0, 2000.0, 30.0, 4000.0]],
                   "options": {"yvarlabel": '"Q" "R"',
                               "xvarlabel": '"S"'}}], 0),
}


def _title(lines):
    """A fixture title's lines as dash writes a title: one string, a line
    break between lines."""
    return "\n".join(lines or [])


class TestEveryTypeTakesThem:

    def test_the_rows(self):
        v = T["varlabel"]
        for case in _MS2:
            assert v[case]["rc"] == 0 and v[case]["notes"] == [], case
        # pci's x title is two lines, as twoway draws it.
        assert v["pci"]["xtitle_lines"] == ["S", "/xb"]

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("case", sorted(_MS2))
    def test_titles(self, mode, case, tmp_path):
        rec = T["varlabel"][case]
        plots, _ = _MS2[case]
        f, notes = figs(mode, tmp_path, plots)
        assert axis_titles(f[0]) == (_title(rec["ytitle_lines"]),
                                     _title(rec["xtitle_lines"])), case
        assert not [n for n in notes if "varlabel" in n], notes

    @pytest.mark.parametrize("case", sorted(_MS2))
    def test_key(self, case):
        rec = T["varlabel"][case]
        plots, i = _MS2[case]
        assert dr._dash_legend_key(plots[i], VL) == rec["legend_labels"][-1]

    @pytest.mark.parametrize("mode", MODES)
    def test_drawn_keys(self, mode, tmp_path):
        rec = T["varlabel"]["function_key"]
        f, _ = figs(mode, tmp_path, _MS2["function_key"][0])
        assert rec["legend_drawn"]
        assert legend_keys(f[0]) == rec["legend_labels"]

    def test_the_words(self):
        # _dash_varlabel_words: one string per quoted or compound-quoted
        # value, "" an empty string, a bare word itself; a non-string none.
        assert dr._dash_varlabel_words('"A" `"B C"\' "" d') == \
            ["A", "B C", "", "d"]
        assert dr._dash_varlabel_words(None) == []

    def test_help(self):
        # AC-47-02.3: the help says every plot type takes them.
        with open(os.path.join(_ROOT, "dash.sthlp"), encoding="utf-8") as fh:
            hlp = " ".join(fh.read().split())
        assert ("as {cmd:twoway} reads them, on every plot type: the axis "
                "titles and the legend keys take them, {cmd:histogram} "
                "joining a {cmd:yvarlabel()} to its scale word "
                "({cmd:D/Density})") in hlp


# ---------------------------------------------------------------------------
# WP-47 MS-3 (with MS-4): yvarlabel("") is the name; a variable's last
# label relabels it in every plot drawn from the same rows
# ---------------------------------------------------------------------------
#
# The defect (measured at 669a502): yvarlabel("") keyed the layer by its
# type ("scatter") and drew no y title, and a label applied only to its
# own layer.  twoway (varlabel_mlabel_truth.json): scatter mpg weight,
# yvarlabel("") is titled and keyed "mpg"; (scatter mpg weight,
# yvarlabel("A")) (scatter mpg length, yvarlabel("B")) keys B, B under
# the y title B -- the last label given for mpg wins in every plot --
# but only among plots of the same if/in: (scatter mpg weight if
# foreign) (scatter mpg weight if !foreign, yvarlabel("B")) keys
# "Mileage (mpg)", B; and a fit's label is its own: (scatter mpg weight,
# yvarlabel("A")) (lfit mpg weight) keys A, "Fitted values", and
# (lfit mpg weight, yvarlabel("Q")) (scatter mpg weight) Q,
# "Mileage (mpg)".

DF3 = DF.assign(length=[186.0, 173.0, 168.0], __dashq1=[1, 0, 1],
                __dashq2=[0, 1, 0])
VL3 = dict(VL, length="Length (in.)")


def _sp(y, x="weight", **o):
    return {"type": "scatter", "yvar": y, "xvar": x, "options": o}


_MS3 = {
    "y_empty": [_sp("mpg", yvarlabel='""')],
    "y_empty_two": [_sp("mpg", yvarlabel='"" "B"'),
                    _sp("price", yvarlabel='"B"')],
    "y_two_empty": [_sp("mpg", yvarlabel='"A" ""'),
                    _sp("price", yvarlabel='""')],
    "graph_last": [_sp("mpg"), _sp("mpg", yvarlabel='"B"')],
    "graph_two": [_sp("mpg", yvarlabel='"A"'),
                  _sp("mpg", "length", yvarlabel='"B"')],
    "graph_other": [_sp("mpg", yvarlabel='"A"'), _sp("price")],
    "graph_x": [_sp("mpg", xvarlabel='"W"'), _sp("price")],
    "graph_fit1": [_sp("mpg", yvarlabel='"A"'),
                   {"type": "lfit", "yvar": "mpg", "xvar": "weight",
                    "options": {}}],
    "graph_fit2": [{"type": "lfit", "yvar": "mpg", "xvar": "weight",
                    "options": {"yvarlabel": '"Q"'}}, _sp("mpg")],
    "graph_ifin": [dict(_sp("mpg"), qual_col="__dashq1"),
                   dict(_sp("mpg", yvarlabel='"B"'), qual_col="__dashq2")],
}


def _expect(case):
    rec = T["varlabel"][case]
    return (_title(rec["ytitle_lines"]), _title(rec["xtitle_lines"]),
            rec["legend_labels"] if rec["legend_drawn"] else None)


def _drawn(mode, tmp_path, plots):
    # The qualifier columns only where a plot names one (the renderer
    # refuses a __dash column no plot names).
    df = (DF3 if any(p.get("qual_col") for p in plots)
          else DF3.drop(columns=["__dashq1", "__dashq2"]))
    f, _ = figs(mode, tmp_path, plots, df=df, vl=VL3)
    keys = [k for lg in f[0].legend if lg.visible
            for k in [it.label.get("value") if isinstance(it.label, dict)
                      else getattr(it.label, "value", it.label)
                      for it in lg.items]]
    return axis_titles(f[0]) + (keys or None,)


class TestEmptyMeansTheName:

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("case", ["y_empty", "y_empty_two",
                                      "y_two_empty"])
    def test_case(self, mode, case, tmp_path):
        assert _drawn(mode, tmp_path, _MS3[case]) == _expect(case)


class TestGraphWide:

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("case", sorted(k for k in _MS3
                                            if k.startswith("graph_")))
    def test_case(self, mode, case, tmp_path):
        assert _drawn(mode, tmp_path, _MS3[case]) == _expect(case)

    def test_the_map(self):
        # Keyed by the plots' rows (qualifier column, if, in): a later
        # plot's label overrides an earlier one's for the same variable.
        got = dr._dash_graph_varlabels(_MS3["graph_two"])
        assert got == {("", "", ""): {"y": {"mpg": "B"}, "x": {}}}
        got = dr._dash_graph_varlabels(_MS3["graph_ifin"])
        assert got == {("__dashq1", "", ""): {"y": {}, "x": {}},
                       ("__dashq2", "", ""): {"y": {"mpg": "B"}, "x": {}}}
        # A fit's label is its own; anything not a dict is skipped.
        assert dr._dash_graph_varlabels(
            _MS3["graph_fit2"] + [None, {"options": 3}]) == {
                ("", "", ""): {"y": {}, "x": {}}}
        assert dr._dash_varlabel_group(
            {"qual_col": "__dashq3", "if_expr": " x>1 ", "in_expr": None}) \
            == ("__dashq3", "x>1", "")
        assert dr._dash_varlabel_group(None) == ("", "", "")

    def test_help(self):
        # AC-47-02.3: the help states the graph-wide rule and the "" rule.
        with open(os.path.join(_ROOT, "dash.sthlp"), encoding="utf-8") as fh:
            hlp = " ".join(fh.read().split())
        assert ("in every plot of the graph drawn from the same rows (the "
                "same {cmd:if} and {cmd:in}): the last one given for a "
                "variable wins") in hlp
        assert ("{cmd:yvarlabel(\"\")} shows the variable's name, and "
                "{cmd:xvarlabel(\"\")} draws no x title") in hlp
