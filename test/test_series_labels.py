"""Legend keys and default axis titles in twoway's text (WP-30 P1.16).

The defect: dash keyed every computed fit ``Fitted values`` (lowess,
lpoly, mband, mspline, fpfit, function), a range layer by its first
boundary, pc and immediate layers by their type name, drew no key for a
scatteri-only graph with ``legend(on)``, and titled each axis from its
first layer -- a title where twoway draws none, and none for range, pc,
immediate and function layers.

twoway's text, per series (a ci fit draws two, band then line):
data layers ``L(y)`` over ``L(x)``; range layers ``L(y1)/L(y2)`` (one label
when equal); pc layers ``L(y1)/L(y2)`` over ``L(x1)/L(x2)``; scatteri
``y`` over ``x``; pci and pcarrowi ``y/yb`` over ``x/xb``; lfit and qfit
``Fitted values``; fpfit ``Predicted <y name>``; lowess ``lowess <y name>
<x name>``; lpoly ``lpoly smooth: L(y)`` over ``lpoly smoothing grid``;
mband ``Median bands``; mspline ``Median spline``; function its Stata name
before ``=``, else ``y``, over ``x``; a ci band ``<level>% CI``.  Each
axis is titled with its first series' label when its last series' label
is the same, else not at all.

The truth is test/fixtures/series_label_truth.json, 150 probes run through
twoway and dash by scripts/extract_series_label_truth.do.
"""

import json
import os
import pathlib
import sys
import tempfile
import warnings

import pytest
from bokeh.document import Document
from bokeh.models import Axis, Legend, Plot

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

import dash_render as dr  # noqa: E402
from by_panel_probe import grid_cells, side_title  # noqa: E402
from conftest import load_app  # noqa: E402
from test_served_linked_views import _fire  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402
from test_unlabelled_variables import (_filter, _spec, _text,  # noqa: E402
                                       _write_data)

_FIX_PATH = os.path.join(HERE, "fixtures", "series_label_truth.json")
with open(_FIX_PATH, encoding="utf-8") as _fh:
    _FIX = json.load(_fh)
_AUTO_LABELS = _FIX["data"]["auto"]["variableLabels"]

#: Probes whose keys still differ from twoway's, and the item that owns
#: each.  Flipped (WP-31 C13): the eight residuals -- keys twoway merges
#: (P2.50: F31 L01 L02 L04 L05) and the legend twoway leaves off a graph of
#: histograms alone (P2.51: G25 L03 L09) -- match now: dash draws two keys
#: with the same text and style as one, as twoway's legend_g does, and a
#: graph of one key draws no legend.  G20 (one rcap layer under by(),
#: P1.15c) matches: dash shows no legend for its one key either.
_NOT_YET_KEYS = {}

_SIDES = (("left", "y1"), ("right", "y2"), ("below", "x1"), ("above", "x2"))


# ---------------------------------------------------------------------------
# Building the probes: every probe of a data set is one graph of a few
# dashboards (a dashboard holds at most 100 graphs), each graph tagged by a
# note() holding its id so its figures are found in either mode.
# ---------------------------------------------------------------------------
from conftest import render_models  # noqa: E402


def _served_doc(tmp, spec, dp, tag):
    sp = str(tmp / f"spec_{tag}.json")
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    ap = str(tmp / f"app_{tag}.py")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(ap)
    # The import is outside the warning capture: the app attaches itself
    # to curdoc() at import time.
    mod = load_app(ap, f"_sl_app_{tag}")
    doc = Document()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mod.make_document(doc)
    return doc


def _saved_figs(tmp, spec, dp, tag):
    sp = str(tmp / f"spec_{tag}.json")
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = dr.DashRenderer(sp, dp)
        render_models(r)
    return list(r.figures.values())


def _saved_root(tmp, spec, dp, tag):
    """The saved page's layout root.  WP-30 P1.15c: a by() grid's legend
    and axis-title cells are not in ``r.figures``; the probes read every
    cell of the layout."""
    sp = str(tmp / f"spec_{tag}.json")
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = dr.DashRenderer(sp, dp)
        render_models(r)
    return r._last_layout_root


def _note_of(fig):
    for m in list(fig.below) + list(fig.above) + list(fig.center):
        t = getattr(m, "text", None)
        if type(m).__name__ == "Title" and t in _FIX["probes"]:
            return t
    return None


def _summary(figs):
    """``{"keys": [...], "y1": ..., "y2": ..., "x1": ..., "x2": ...}`` over
    *figs*: the sorted keys of the visible series legend (one list, ``[]``
    when none is shown; distinct lists joined when panels differ) and the
    distinct non-empty axis titles on each side, joined by ``;``.  A by()
    grid's title cells (WP-30 P1.15c) title its first y and x axes."""
    keys, sides = set(), dict((k, set()) for _a, k in _SIDES)
    for f in figs:
        st = side_title(f)
        if st is not None and st[1]:
            sides[st[0] + "1"].add(st[1])
        for lg in f.select({"type": Legend}):
            if (getattr(lg, "name", "") == dr._COLORVAR_LEGEND_NAME
                    or lg.visible is False or not lg.items):
                continue
            keys.add(tuple(sorted(str(_text(i.label)) for i in lg.items)))
        for attr, k in _SIDES:
            for a in getattr(f, attr):
                lab = getattr(a, "axis_label", None)
                if lab not in (None, ""):
                    sides[k].add(str(lab))
    out = {"keys": list(sorted(keys)[0]) if len(keys) == 1
           else [";".join(k) for k in sorted(keys)]}
    out.update((k, ";".join(sorted(v))) for k, v in sides.items())
    return out


_CACHE = {}


def _probe_summaries(mode):
    """``{pid: summary}`` for every probe, built in *mode*, once."""
    if mode in _CACHE:
        return _CACHE[mode]
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="dash_sl_"))
    out = {}
    for ds in ("auto", "sp500"):
        dp = str(tmp / f"data_{ds}.json")
        with open(dp, "w", encoding="utf-8") as fh:
            json.dump(_FIX["data"][ds], fh)
        pids = sorted(p for p, v in _FIX["probes"].items() if v["ds"] == ds)
        for c in range(0, len(pids), 50):
            chunk = pids[c:c + 50]
            graphs, points = [], {}
            for pid in chunk:
                g = _FIX["probes"][pid]["dash"]["graph"]
                go = {k: v for k, v in g["graph_options"].items()
                      if k != "name"}
                go["note"] = '"%s"' % pid
                graphs.append(("g_" + pid, g["plots"], go))
                pts = _FIX["probes"][pid]["dash"]["points"]
                if pts is not None:
                    points["g_" + pid] = pts
            spec = _spec(graphs)
            spec["build_options"]["formats"] = _FIX["formats"][ds]
            if points:
                spec["function_points"] = points
            tag = f"{mode}_{ds}_{c}"
            if mode == "saved":
                roots = [_saved_root(tmp, spec, dp, tag)]
            else:
                roots = list(_served_doc(tmp, spec, dp, tag).roots)
            figs = [m for root in roots for m in root.select({"type": Plot})
                    if isinstance(m, Plot)]
            by_pid = {}
            for f in figs:
                pid = _note_of(f)
                if pid is not None and f not in by_pid.setdefault(pid, []):
                    by_pid[pid].append(f)
            # WP-30 P1.15c: a by() graph's legend and axis titles are drawn
            # once, in cells of its grid that carry no note.
            for cells in grid_cells(roots):
                tags = {_note_of(c) for c in cells} - {None}
                if len(tags) == 1:
                    tag_ = tags.pop()
                    by_pid[tag_] += [c for c in cells
                                     if c not in by_pid[tag_]]
            for pid in chunk:
                out[pid] = _summary(by_pid.get(pid, []))
    _CACHE[mode] = out
    return out


def _twoway_keys(pid):
    return sorted(_FIX["probes"][pid]["twoway"]["keys"])


# ---------------------------------------------------------------------------
# The fixture
# ---------------------------------------------------------------------------
class TestTheFixture:
    def test_it_is_stamped(self):
        m = _FIX["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted"):
            assert m.get(k), k
        assert m["scheme"] == "stcolor"
        assert m["probes"] == len(_FIX["probes"]) >= 150
        bad = [p for p, v in _FIX["probes"].items()
               if v["twoway"]["rc"] != 0 or v["dash"]["rc"] != 0
               or not v["dash"]["graph"]]
        assert not bad, bad

    def test_the_axis_objects_agree_with_the_drawing(self):
        bad = []
        for pid, v in sorted(_FIX["probes"].items()):
            text = v["body"] + v["opts"]
            if any(s in text for s in ("by(", "axis(2)", "ts", '"',
                                       "xtitle(", "ytitle(")):
                continue
            tw = v["twoway"]
            if (tw["titles"]["y1"] != "".join(tw["svg_titles"]["left"])
                    or tw["titles"]["x1"]
                    != "".join(tw["svg_titles"]["bottom"])):
                bad.append(pid)
        assert not bad, bad


# ---------------------------------------------------------------------------
# The series rule
# ---------------------------------------------------------------------------
_MPG, _WT = "Mileage (mpg)", "Weight (lbs.)"
_TURN, _LEN = "Turn circle (ft.)", "Length (in.)"
_XY = {"yvar": "mpg", "xvar": "weight"}

#: One spec per row of twoway's table, and twoway's series for it
#: (series_label_truth.json: F01-F16, R01-R08, P01-P05, I01-I03, U01, U02,
#: D01-D07, T01).
_TABLE = [
    ({"type": "scatter", **_XY}, [(_MPG, _WT)]),
    ({"type": "tsline", "yvar": "mpg", "xvar": "weight"}, [(_MPG, _WT)]),
    ({"type": "lowess", **_XY}, [("lowess mpg weight", _WT)]),
    ({"type": "lpoly", **_XY},
     [("lpoly smooth: " + _MPG, "lpoly smoothing grid")]),
    ({"type": "mband", **_XY}, [("Median bands", _WT)]),
    ({"type": "mspline", **_XY}, [("Median spline", _WT)]),
    ({"type": "fpfit", **_XY}, [("Predicted mpg", _WT)]),
    ({"type": "lfit", **_XY}, [("Fitted values", _WT)]),
    ({"type": "qfit", **_XY}, [("Fitted values", _WT)]),
    ({"type": "function", "expr": "x", "yname": "z"}, [("z", "x")]),
    *[({"type": t, "yvar1": "mpg", "yvar2": "turn", "xvar": "weight"},
       [(_MPG + "/" + _TURN, _WT)]) for t in sorted(dr._DASH_RANGE_TYPES)],
    *[({"type": t, "y1var": "mpg", "x1var": "weight", "y2var": "turn",
        "x2var": "length"}, [(_MPG + "/" + _TURN, _WT + "/" + _LEN)])
      for t in sorted(dr._DASH_PC_TYPES)],
    ({"type": "scatteri", "values": [[1, 2]]}, [("y", "x")]),
    ({"type": "pci", "values": [[1, 2, 3, 4]]}, [("y/yb", "x/xb")]),
    ({"type": "pcarrowi", "values": [[1, 2, 3, 4]]}, [("y/yb", "x/xb")]),
    ({"type": "histogram", "var": "mpg"}, [("Density", _MPG)]),
    ({"type": "histogram", "var": "mpg", "options": {"percent": "percent"}},
     [("Percent", _MPG)]),
    ({"type": "kdensity", "var": "mpg"}, [("kdensity mpg", "x")]),
]


class TestTheSeriesRule:
    def test_each_type_gives_twoways_series(self):
        bad = [(p["type"], got, want) for p, want in _TABLE
               for got in [dr._dash_layer_series(p, _AUTO_LABELS)]
               if got != want]
        assert not bad, bad

    def test_names_and_labels_as_twoway_uses_them(self):
        vl = _AUTO_LABELS
        f = dr._dash_layer_series
        assert f({"type": "lowess", "yvar": "m2", "xvar": "weight"},
                 vl)[0][0] == "lowess m2 weight"
        assert f({"type": "lpoly", "yvar": "m2", "xvar": "weight"},
                 vl)[0][0] == "lpoly smooth: m2"
        assert f({"type": "fpfit", "yvar": "m2", "xvar": "weight"},
                 vl)[0][0] == "Predicted m2"
        # Names, never labels, for lowess and fpfit.
        assert f({"type": "fpfit", **_XY}, vl)[0][0] == "Predicted mpg"
        assert f({"type": "lowess", **_XY}, vl)[0][0] == "lowess mpg weight"

    def test_equal_or_missing_boundaries_give_one_label(self):
        vl = _AUTO_LABELS
        f = dr._dash_layer_series
        assert f({"type": "rcap", "yvar1": "turn", "yvar2": "t2",
                  "xvar": "weight"}, vl) == [(_TURN, _WT)]
        assert f({"type": "pcspike", "y1var": "mpg", "x1var": "weight",
                  "y2var": "mpg", "x2var": "weight"}, vl) == [(_MPG, _WT)]
        assert f({"type": "rbar", "yvar1": "mpg", "xvar": "weight"},
                 vl) == [(_MPG, _WT)]

    def test_a_ci_layer_is_two_series_band_first(self):
        vl = _AUTO_LABELS
        f = dr._dash_layer_series
        assert f({"type": "lfitci", **_XY, "options": {"level": "90"}},
                 vl) == [("90% CI", _WT), ("Fitted values", _WT)]
        assert f({"type": "lfitci", **_XY}, vl,
                 default_level=99)[0][0] == "99% CI"
        grid = "lpoly smoothing grid"
        assert f({"type": "lpolyci", **_XY}, vl) == [
            ("95% CI", grid), ("lpoly smooth: " + _MPG, grid)]

    def test_a_function_is_named_as_twoway_names_it(self):
        good = ["z", "_y", "ü", "日本", "a½", "a" * 32]
        bad = ["a" * 33, "1y", "y z", "a$b", "<b>", "", None, 5]
        f = dr._dash_layer_series
        wrong = [n for n in good
                 if f({"type": "function", "yname": n}) != [(n, "x")]]
        wrong += [n for n in bad
                  if f({"type": "function", "yname": n}) != [("y", "x")]]
        if f({"type": "function", "expr": "x"}) != [("y", "x")]:
            wrong.append("missing")
        assert not wrong, wrong

    def test_it_is_total(self):
        for plot, vl in ((None, None), ([], None), ({"type": 3}, None),
                         ({"type": "scatter", "options": [1]}, None),
                         ({"type": "lfitci", "yvar": "mpg", "options": [1]},
                          ["x"]),
                         ({"type": "scatter", "yvar": 7, "xvar": 8}, None)):
            got = dr._dash_layer_series(plot, vl)
            assert got and all(isinstance(a, str) and isinstance(b, str)
                               for a, b in got), (plot, got)


# ---------------------------------------------------------------------------
# The legend keys
# ---------------------------------------------------------------------------
class TestTheLegendKeys:
    def test_the_key_is_the_last_series_y_label(self):
        bad = [p["type"] for p, _w in _TABLE
               if dr._dash_legend_key(p, _AUTO_LABELS)
               != dr._dash_layer_series(p, _AUTO_LABELS)[-1][0]]
        assert not bad, bad
        assert dr._dash_legend_key({"type": "scatter"}) == "scatter"


@pytest.mark.parametrize("mode", ["saved", "served"])
class TestKeysMatchTwoway:
    def test_keys(self, mode):
        got = _probe_summaries(mode)
        bad = ["%s: dash %r, twoway %r" % (pid, got[pid]["keys"],
                                            _twoway_keys(pid))
               for pid in sorted(_FIX["probes"])
               if pid not in _NOT_YET_KEYS
               and got[pid]["keys"] != _twoway_keys(pid)]
        assert not bad, "\n".join(bad)

    def test_the_residuals_still_differ(self, mode):
        # Flipped (WP-31 C13): P2.50 and P2.51 were open; the merge of keys
        # with the same text and style closes both, so no residual is left
        # and test_keys holds every probe.
        got = _probe_summaries(mode)
        same = [pid for pid in _NOT_YET_KEYS
                if got[pid]["keys"] == _twoway_keys(pid)]
        assert not same, same
        assert _NOT_YET_KEYS == {}


class TestScatteriKeys:
    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_alone_is_hidden_without_legend_on(self, mode, tmp_path):
        """One key, as every one-key graph: built, but not shown."""
        spec = _spec([("g1", [plot_for("scatteri")], {"note": '"I00"'})])
        dp = _write_data(tmp_path)
        if mode == "saved":
            figs = _saved_figs(tmp_path, spec, dp, "si")
        else:
            doc = _served_doc(tmp_path, spec, dp, "si")
            figs = [m for r in doc.roots for m in r.select({"type": Plot})]
        legends = [lg for f in figs for lg in f.select({"type": Legend})
                   if getattr(lg, "name", "") != dr._COLORVAR_LEGEND_NAME]
        assert [[_text(i.label) for i in lg.items] for lg in legends] == [
            ["y"]]
        assert legends[0].visible is False


class TestKeysAfterAFilterMove:
    def test_served_keys_survive_a_move(self, tmp_path):
        spec = _spec([("g1", [plot_for("scatter", yvar="y", xvar="x"),
                              plot_for("lowess", yvar="y", xvar="x"),
                              plot_for("rcap", yvar1="y1", yvar2="y2",
                                       xvar="x")], {})],
                     filters=[_filter("x", "range")])
        doc = _served_doc(tmp_path, spec, _write_data(tmp_path), "mv")
        figs = [m for r in doc.roots for m in r.select({"type": Plot})]
        before = _summary(figs)
        assert before["keys"] == sorted(["y", "lowess y x", "y1/y2"])
        _fire(doc, "x", (4.0, 24.0))
        assert _summary(figs) == before


class TestTheServedCopy:
    def test_the_app_carries_the_key_names(self, tmp_path):
        spec = _spec([("g1", [plot_for("scatter", yvar="y", xvar="x")],
                       {})])
        sp = str(tmp_path / "spec.json")
        with open(sp, "w", encoding="utf-8") as fh:
            json.dump(spec, fh)
        ap = str(tmp_path / "app.py")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, _write_data(tmp_path)).build(ap)
        mod = load_app(ap, "_sl_copy_app")
        assert callable(mod._dash_layer_series)
        assert mod._DASH_FIT_KEYS == dr._DASH_FIT_KEYS
        assert callable(mod._dash_axis_default_titles)


# ---------------------------------------------------------------------------
# The default axis titles
# ---------------------------------------------------------------------------
def _sc(y="mpg", x="weight", **opts):
    return {"type": "scatter", "yvar": y, "xvar": x, "options": dict(opts)}


def _fit(t, y="mpg", x="weight", **opts):
    return {"type": t, "yvar": y, "xvar": x, "options": dict(opts)}


_RCAP = {"type": "rcap", "yvar1": "mpg", "yvar2": "turn", "xvar": "weight"}

#: (probe, layers, twoway's (x, y) on the first axes) -- the K rule probes
#: of series_label_truth.json and the cases around them.
_TITLE_CASES = [
    ("K01", [_sc(), _sc(x="length"), _sc()], (_WT, _MPG)),
    ("K02", [_sc(), _sc(x="length"), _sc(x="length")], ("", _MPG)),
    ("K03", [_sc(), _sc("price"), _sc("trunk"), _sc()], (_WT, _MPG)),
    ("K04", [_sc(), _sc("price"), _sc("price"), _sc()], (_WT, _MPG)),
    ("K04b", [_sc(), _sc("price"), _sc(), _sc("price")], (_WT, "")),
    ("K05", [_fit("lfit"), _fit("lfitci")], (_WT, "Fitted values")),
    ("K06", [_fit("lfitci"), _fit("lfit")], (_WT, "")),
    ("K07", [_RCAP, _sc(), _RCAP], (_WT, _MPG + "/" + _TURN)),
    ("K09", [_sc(), _fit("lpoly"), _fit("lfit")], (_WT, "")),
    ("M01", [_sc(), _sc("price")], (_WT, "")),
    ("M04", [_sc(), _sc(x="length")], ("", _MPG)),
    ("U03", [{"type": "histogram", "var": "mpg"},
             {"type": "kdensity", "var": "mpg"}], ("", "")),
    ("empty", [], ("", "")),
    ("not dicts", [None, 3, "x"], ("", "")),
]


class TestTheAxisTitleRule:
    def test_first_equals_last(self):
        bad = [(pid, got, want) for pid, plots, want in _TITLE_CASES
               for got in [dr._dash_axis_default_titles(plots,
                                                        _AUTO_LABELS)]
               if got != want]
        assert not bad, bad

    def test_each_axis_has_its_own_series(self):
        f = dr._dash_axis_default_titles
        vl = _AUTO_LABELS
        k11 = [_sc(), _sc("price", yaxis="2"), _sc("trunk", yaxis="2"),
               _sc("price", yaxis="2")]
        assert f(k11, vl) == (_WT, _MPG)
        assert f(k11, vl, yaxis=2)[1] == "Price"
        m07 = [_sc(), _fit("lfit", "price", yaxis="2")]
        assert f(m07, vl, yaxis=2)[1] == "Fitted values"
        m12 = [_sc(), _sc(yaxis="2"), _sc("price", yaxis="2")]
        assert f(m12, vl, yaxis=2)[1] == ""
        h05 = [_sc(), _fit("lfitci", yaxis="2")]
        assert f(h05, vl) == (_WT, _MPG)
        assert f(h05, vl, yaxis=2)[1] == ""
        m16 = [_sc(), _sc(x="length", xaxis="2")]
        assert f(m16, vl, xaxis=2)[0] == _LEN
        # A layer on both axes counts on each.
        both = [_sc(yaxis="1 2")]
        assert f(both, vl)[1] == f(both, vl, yaxis=2)[1] == _MPG

    def test_it_is_total(self):
        for plots in (None, [], [None], [{"type": 3, "options": [1]}],
                      [{"type": "scatter", "yvar": 7, "options": None}]):
            x, y = dr._dash_axis_default_titles(plots, ["not", "a", "dict"])
            assert isinstance(x, str) and isinstance(y, str)


def _drawn_numbers(probe):
    """twoway's titles keyed by the number dash draws each axis as.

    Flipped (WP-31 D9): twoway's ``titles`` are keyed by the typed axis
    number, and dash renumbers a letter's axes by first use when the first
    layer is not on axis 1 (``_dash_lone_second_axes``; twoway draws the
    first used on the left: H01's svg_titles put Price, axis 2, on the
    left), so each typed number is read as the axis it is drawn as."""
    want = dict(probe["twoway"]["titles"])
    plots = ((probe.get("dash") or {}).get("graph") or {}).get("plots") or []
    for letter in ("y", "x"):
        used = []
        for p in plots:
            nos = dr._dash_axis_nos(p.get("options"), letter)
            if len(nos) != 1:
                used = []
                break
            if nos[0] not in used:
                used.append(nos[0])
        if not used or used[0] == 1:
            continue
        mapping = {t: d + 1 for d, t in enumerate(used)}
        old = {n: want.get(f"{letter}{n}", "") for n in (1, 2)}
        for n in (1, 2):
            want[f"{letter}{n}"] = ""
        for t, d in mapping.items():
            if t in old and d in (1, 2):
                want[f"{letter}{d}"] = old[t]
    return want


@pytest.mark.parametrize("mode", ["saved", "served"])
class TestTitlesMatchTwoway:
    def test_titles(self, mode):
        got = _probe_summaries(mode)
        bad = []
        for pid in sorted(_FIX["probes"]):
            want = _drawn_numbers(_FIX["probes"][pid])
            have = {k: got[pid][k] for k in ("y1", "y2", "x1", "x2")}
            if have != want:
                bad.append("%s: dash %r, twoway %r" % (pid, have, want))
        assert not bad, "\n".join(bad)


class TestTitlesAfterAFilterMove:
    def test_served_titles_survive_a_move(self, tmp_path):
        spec = _spec([("g1", [plot_for("scatter", yvar="y", xvar="x"),
                              plot_for("scatter", yvar="y2", xvar="x")], {}),
                      ("g2", [plot_for("rcap", yvar1="y1", yvar2="y2",
                                       xvar="x")], {})],
                     filters=[_filter("x", "range")])
        doc = _served_doc(tmp_path, spec, _write_data(tmp_path), "tmv")
        figs = [m for r in doc.roots for m in r.select({"type": Plot})]

        def titles():
            return sorted((tuple(str(a.axis_label or "") for a in f.left
                                 if isinstance(a, Axis)),
                           tuple(str(a.axis_label or "") for a in f.below
                                 if isinstance(a, Axis)))
                          for f in figs)
        before = titles()
        assert before == [(("",), ("x",)), (("y1/y2",), ("x",))]
        _fire(doc, "x", (4.0, 24.0))
        assert titles() == before


class TestTheHelp:
    def test_the_help_states_the_key_and_title_rules(self):
        with open(os.path.join(os.path.dirname(HERE), "dash.sthlp"),
                  encoding="utf-8") as fh:
            text = " ".join(fh.read().split())
        for needle in ("Legend keys and default axis titles",
                       "when the last series drawn on it has the same label",
                       "{cmd:lowess} {it:yvar xvar}",
                       "by the rule of the first axis"):
            assert needle in text, needle
