"""text() and ttext() drawn as twoway draws them (WP-30 P1.10, section 56).

twoway draws each copy of ``text(y x "line" ...)`` at its point in data
units, with its own sub-options, in every by() panel, on axis 2 when asked
and outside the plot region when the point is, never widening an axis
(test/fixtures/added_text_truth.json, written by
scripts/extract_added_text_truth.do).  dash.ado parses the copies by value
(``_dash_added_text``, ``_dash_at_opts``; Mata ``_dash_at_parse``) and
writes one ``added_text`` record per point into the graph's options; the
renderer draws each as a data-unit ``Label`` tagged ``dash_added_text``
(``_dash_added_text``), in the saved page and the served app.  The
refusals, the merge of repeated copies and the injection cases are Stata's
and live in the AT cases of test/test_twoway_option_parity.cscript,
test/test_json_escaping.cscript and test/test_resource_limits.cscript; the
hostile and TeX texts are test/test_label_sinks.py's ``added_text`` sink.
"""

import json
import math
import os
import re
import sys
import warnings

import pytest
from bokeh.models import Label

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_join_order as jo  # noqa: E402
import test_mode_parity as tp  # noqa: E402
import test_saved_filter_layers as sfl  # noqa: E402
from conftest import render_models  # noqa: E402
from js_runner import requires_node  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402
from probe_groups import probe_params, representative  # noqa: E402

_ROOT = os.path.dirname(_HERE)
_FIXTURE = os.path.join(_HERE, "fixtures", "added_text_truth.json")
_ADO = os.path.join(_ROOT, "dash.ado")
_MATA = os.path.join(_ROOT, "dash_parse.mata")
_HELP = os.path.join(_ROOT, "dash.sthlp")
MODES = ("saved", "served")

with open(_FIXTURE, encoding="utf-8") as _fh:
    _FIX = json.load(_fh)

#: The direction a Label's anchor puts its text in, from the point.
_ANCHOR_DIR = {"bottom_center": "n", "bottom_left": "ne",
               "center_left": "e", "top_left": "se", "top_center": "s",
               "top_right": "sw", "center_right": "w",
               "bottom_right": "nw", "center": "c"}


def _at(y, x, lines, opts="", ya=1, xa=1, kind="text"):
    """One record as dash.ado's _dash_at_json writes it."""
    return {"at_kind": kind, "at_y": y, "at_x": x, "at_yaxis": ya,
            "at_xaxis": xa, "at_lines": list(lines), "at_opts": opts}


def _spec(records, plots=None, go=None, bo=None):
    g = dict(go or {})
    g["added_text"] = list(records)
    g["added_text_n"] = str(len(records))
    return tp._spec(plots or [plot_for("scatter")],
                    dict({"scheme": "stcolor"}, **(bo or {})), g)


def _saved(spec, df=None, caught=None):
    _, sp, dp = jo._write(spec, tp._DF if df is None else df,
                          tp._VALUE_LABELS, tp._LABEL_NAMES)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        r = render_models(dr.DashRenderer(sp, dp))
    if caught is not None:
        caught.extend(str(x.message) for x in w)
    return r


def _figs(spec, mode, df=None, caught=None):
    """The figures of *spec* built in *mode*; every warning raised goes to
    *caught* when given."""
    if mode == "saved":
        return jo._saved_figs(_saved(spec, df, caught))
    doc, msgs = jo._served(spec, tp._DF if df is None else df, msgs=True)
    if caught is not None:
        caught.extend(msgs)
    return jo._served_figs(doc)


def _labels(fig):
    return [m for m in fig.center
            if isinstance(m, Label) and "dash_added_text" in (m.tags or [])]


def _all_labels(spec, mode, df=None):
    return [lab for f in _figs(spec, mode, df) for lab in _labels(f)]


def _pt(size):
    m = re.fullmatch(r"([0-9.]+)(pt|px)", str(size))
    assert m, f"font size {size!r} is not a pt or px string"
    return float(m.group(1)) * (0.75 if m.group(2) == "px" else 1.0)


def _angle_of(rotate):
    """twoway's SVG rotation (degrees, clockwise on screen) as a Bokeh
    angle (radians, counter-clockwise), in [0, 2pi)."""
    return math.radians(-(rotate or 0.0)) % (2 * math.pi)


# ---------------------------------------------------------------------------
# The fixture and the tables read from it
# ---------------------------------------------------------------------------

class TestTheFixture:
    def test_it_is_stamped(self):
        m = _FIX["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted",
                  "compass", "orient"):
            assert k in m, k
        assert str(m["stata_version"]).startswith("19.")
        assert re.fullmatch(r"[0-9a-f]{40}", m["dash_commit"])
        for pid in ("aaa", "two", "lines", "far", "vert", "box", "by", "y2",
                    "just", "log", "rev", "r_onept", "r_nosuch", "r_y2",
                    "tt_m", "tt_d", "tt_m13", "tt_two1", "tt_xl9"):
            assert pid in _FIX["probes"], pid


class TestTheTables:
    def test_they_are_the_fixtures(self):
        comp = {k: v for k, v in _FIX["_meta"]["compass"].items() if v}
        assert set(dr._DASH_ADDED_TEXT_PLACE) == set(comp.values())
        # Mata's _dash_at_place reads through compass2dir's one table,
        # _dash_style_word (Flipped, WP-45 ST-1: its own synonym table is
        # gone; the Python twin of that table gives the fixture's answer for
        # every spelling, and cscript Q4502-3 pins the Mata twin row by row).
        with open(_MATA, encoding="utf-8") as fh:
            src = fh.read()
        body = src[src.index("string scalar _dash_at_place("):]
        body = body[:body.index("\n}\n")]
        assert 'return(_dash_style_word("compass2dir", p))' in body
        for k, v in comp.items():
            assert dr._dash_style_word("compass2dir", k) == v, k
        for k, v in _FIX["_meta"]["compass"].items():
            if not v:
                assert dr._dash_style_word("compass2dir", k) == "", k
        # The anchors put the text where twoway measured it.
        for canon, anchor in dr._DASH_ADDED_TEXT_PLACE.items():
            assert _ANCHOR_DIR[anchor] == canon, canon
        orient = {k: _angle_of(v) for k, v in _FIX["_meta"]["orient"].items()
                  if v is not None}
        got = {k: v % (2 * math.pi)
               for k, v in dr._DASH_ADDED_TEXT_ORIENT.items()}
        assert set(got) == set(orient)
        for k in orient:
            assert math.isclose(got[k], orient[k], abs_tol=1e-9), k


class TestTheOptions:
    def test_each_drawn_sub_option(self):
        o = dr._dash_added_text_opts(
            "size(large) color(red) placement(ne) justification(left) "
            "orientation(vertical) box fcolor(yellow) lcolor(blue) "
            "lwidth(thick) margin(medium)")
        assert o["anchor"] == "bottom_left"
        assert math.isclose(o["angle"], math.pi / 2)
        assert o["align"] == "left"
        assert o["px"] is not None and o["color"] == "#ff0000"
        assert o["box"] is True
        assert (o["fill"], o["line"]) == ("#ffff00", "#0000ff")
        assert o["lwidth"] > 0 and len(o["padding"]) == 4
        assert all(p > 0 for p in o["padding"].values())
        empty = dr._dash_added_text_opts("")
        assert all(v is None for v in empty.values()), empty
        seen = set()
        # Flipped: width() is drawn (WP-43 LT-20); angle() is a sub-option
        # dash still names once and does not draw.
        # Flipped (WP-49 basic:PT-12): angle() is taken in silence, as
        # twoway draws the same picture with it and prints nothing
        # (noted_option_truth.json sub_probes text(30 3000 "x", angle(45)));
        # drawview(), which dash does not draw and no silent row holds, is
        # the word named once.
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            o = dr._dash_added_text_opts("drawview(yes)", seen, "g1")
            dr._dash_added_text_opts("drawview(yes)", seen, "g1")
        assert all(v is None for v in o.values()), o
        assert sum("drawview" in str(x.message) for x in w) == 1
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            dr._dash_added_text_opts("angle(5)", set(), "g1")
        assert not [x for x in w if "angle" in str(x.message)]


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", MODES)
class TestTheTextIsDrawn:
    def test_one_point(self, mode):
        labs = _all_labels(_spec([_at(30, 3000, ["AAA"])]), mode)
        assert len(labs) == 1
        lab = labs[0]
        assert (lab.x, lab.y, lab.text) == (3000, 30, "AAA")
        assert (lab.x_units, lab.y_units, lab.anchor) == ("data", "data",
                                                          "center")
        sch = dr.SchemeParser("stcolor")
        assert lab.text_font_size == sch.text_option_font_size
        assert lab.text_color == sch.text_option_color
        assert lab.background_fill_color is None


#: Each drawn auto probe of the fixture, as the records dash.ado writes for
#: it, and the graph options its command sets.  `noted' is left out: its
#: width() and linegap() are named, not drawn (register P1.10.2); its
#: tstyle(heading) is drawn since WP-31 D13 (test_added_text_style.py).
_PROBE_RECORDS = {
    "aaa": [_at(30, 3000, ["AAA"])],
    "two": [_at(30, 3000, ["AAA"], "size(large) color(red)"),
            _at(20, 4000, ["BBB"])],
    "lines": [_at(30, 3000, ["L1", "L2"])],
    "far": [_at(100, 3000, ["FAR"])],
    "above": [_at(43, 3000, ["ABOVE"])],
    "vert": [_at(30, 3000, ["VVV"], "orientation(vertical)")],
    "rvert": [_at(30, 3000, ["RVV"], "orientation(rvertical)")],
    "rhor": [_at(30, 3000, ["RHH"], "orientation(rhorizontal)")],
    "box": [_at(30, 3000, ["BOX"],
                "box fcolor(yellow) lcolor(blue) margin(medium)")],
    "just": [_at(30, 3000, ["J1", "JJJJJJ2"], "justification(left) box")],
    "level_pg": [_at(30, 3000, ["PG"]), _at(20, 4000, ["GL"])],
    "level_seg": [_at(30, 3000, ["S1"]), _at(20, 4000, ["S2"])],
    "log": [_at(30, 3000, ["LOG"])],
    "rev": [_at(30, 3000, ["REV"])],
    "size_x2": [_at(30, 3000, ["SZA"], "size(*2)")],
    "size_pt": [_at(30, 3000, ["SZB"], "size(20pt)")],
    "size_5": [_at(30, 3000, ["SZC"], "size(5)")],
    "size_huge": [_at(30, 3000, ["SZD"], "size(huge)")],
    "trail": [_at(30, 3000, ["TRL"])],
    "html": [_at(30, 3000, ["<b>x</b>&amp;"])],
    "abbr": [_at(30, 3000, ["ABR"],
                 "size(large) color(red) orientation(vert)")],
    "r_e3": [_at(30, 3000, ["E3"])],
    "tt_num": [_at(30, 3000, ["TTN"], kind="ttext")],
}
_PROBE_GO = {"log": {"xscale": "log"}, "rev": {"xscale": "reverse"}}


def _place_probes():
    """The placement probes: each spelling's record carries the canonical
    name dash.ado writes (east for a name twoway notes)."""
    out = {}
    for pid, rec in _FIX["probes"].items():
        m = re.search(r"place\(([a-z0-9]+)\)", rec["cmd"])
        if pid.startswith("pl_") and m:
            canon = _FIX["_meta"]["compass"].get(m.group(1)) or "e"
            out[pid] = [_at(30, 3000, ["PX"], f"placement({canon})")]
        m = re.search(r"orientation\(([a-z]+)\)", rec["cmd"])
        if pid.startswith("or_") and m:
            ok = _FIX["_meta"]["orient"].get(m.group(1)) is not None
            out[pid] = [_at(30, 3000, ["OX"],
                            f"orientation({m.group(1)})" if ok else "")]
    return out


def _probes():
    return dict(_PROBE_RECORDS, **_place_probes())


_COMPASS = {"n": "cardinal", "e": "cardinal", "s": "cardinal",
            "w": "cardinal", "c": "centre"}


def _category(pid):
    """A probe's family for the served subset: a placement probe (pl_#)
    by its compass class (cardinal, diagonal or centre), an orientation
    probe (or_#) by its angle, every other probe on its own."""
    fam = re.sub(r"_\d+$", "", pid)
    opts = str(_probes()[pid][0].get("at_opts", ""))
    if fam == "pl":
        m = re.search(r"placement\((\w+)\)", opts)
        return (fam, _COMPASS.get(m.group(1) if m else "c", "diagonal"))
    if fam == "or":
        m = re.search(r"orientation\((\w+)\)", opts)
        word = m.group(1) if m else ""
        return (fam, ("r" if word.startswith("r") else "")
                + ("v" if "vert" in word else "h" if "hor" in word else ""))
    return (pid,)


#: Probes per node and the gate's served subset (pytest speed,
#: 22oct2026): the first probe of each _category and every sixth probe of
#: the rest; release checks every probe served.
_PARAMS = probe_params(
    sorted(_probes()), representative(sorted(_probes()), _category,
                                      stride=6), size=8, saved_size=25)
_BASE_PT = {}


def _base_pt(mode):
    """The size of the "aaa" probe's first Label in *mode*: the default
    every probe's size is a ratio to."""
    if mode not in _BASE_PT:
        labs = _all_labels(_spec(_probes()["aaa"]), mode)
        _BASE_PT[mode] = _pt(labs[0].text_font_size)
    return _BASE_PT[mode]


class TestAgainstTwoway:
    @pytest.mark.parametrize("mode,group", _PARAMS)
    def test_probe(self, mode, group):
        """Every drawn probe: lines, size against the default, colour,
        angle, side of the point, position and box, as twoway drew them."""
        probes = _probes()
        base_px = _FIX["probes"]["aaa"]["texts"][0]["size"]
        base_pt = _base_pt(mode)
        bad = []
        for pid in group:
            fx = _FIX["probes"][pid]
            labs = _all_labels(_spec(probes[pid], go=_PROBE_GO.get(pid)),
                               mode)
            if len(labs) != len(probes[pid]):
                bad.append(f"{pid}: {len(labs)} Labels")
                continue
            texts = list(fx["texts"])
            for i, lab in enumerate(labs):
                lines = lab.text.split("\n")
                mine, texts = texts[:len(lines)], texts[len(lines):]
                if [t["text"] for t in mine] != lines:
                    bad.append(f"{pid}: lines {lines} vs "
                               f"{[t['text'] for t in mine]}")
                    continue
                t = mine[0]
                ratio = _pt(lab.text_font_size) / base_pt
                if not math.isclose(ratio, t["size"] / base_px, rel_tol=.01):
                    bad.append(f"{pid}: size ratio {ratio:.4f} vs "
                               f"{t['size'] / base_px:.4f}")
                if lab.text_color != t["fill"]:
                    bad.append(f"{pid}: colour {lab.text_color} vs "
                               f"{t['fill']}")
                if not math.isclose(lab.angle % (2 * math.pi),
                                    _angle_of(t["rotate"]), abs_tol=1e-9):
                    bad.append(f"{pid}: angle {lab.angle}")
                want = fx.get("direction") or "c"
                if _ANCHOR_DIR.get(str(lab.anchor)) != want:
                    bad.append(f"{pid}: anchor {lab.anchor} vs {want}")
                if (t["anchor"] is None) != (lab.text_align == "left"):
                    bad.append(f"{pid}: align {lab.text_align}")
                if i == 0 and fx.get("point") and want == "c":
                    for ax in ("x", "y"):
                        v = getattr(lab, ax)
                        if not math.isclose(v, fx["point"][ax], rel_tol=.005):
                            bad.append(f"{pid}: {ax} {v} vs {fx['point'][ax]}")
                box = fx["boxes"][i] if i < len(fx["boxes"]) else None
                got = (lab.background_fill_color, lab.border_line_color)
                if got != ((box["fill"], box["stroke"]) if box
                           else (None, None)):
                    bad.append(f"{pid}: box {got} vs {box}")
        assert not bad, "\n".join(bad)


@pytest.mark.parametrize("mode", MODES)
class TestSchemeDefaults:
    def test_text_option_keys(self, mode):
        """Each scheme's text colour, and its box's fill and outline."""
        bad = []
        for scheme in ("stcolor", "s2color", "s1mono", "s1rcolor",
                       "s2color8"):
            for pid, opts in ((f"sch_{scheme}", ""), (f"schb_{scheme}", "box")):
                fx = _FIX["probes"].get(pid)
                if fx is None:
                    continue
                labs = _all_labels(_spec([_at(30, 3000, ["S"], opts)],
                                         bo={"scheme": scheme}), mode)
                lab = labs[0]
                want = [fx["texts"][0]["fill"]]
                got = [lab.text_color]
                if fx["boxes"]:
                    want += [fx["boxes"][0]["fill"], fx["boxes"][0]["stroke"]]
                    got += [lab.background_fill_color, lab.border_line_color]
                if got != want:
                    bad.append(f"{scheme} {opts or 'plain'}: {got} vs {want}")
        assert not bad, "\n".join(bad)


@pytest.mark.parametrize("mode", MODES)
class TestAxes:
    def test_dates(self, mode):
        """On a %td axis a number is a date in Stata units, placed through
        the axis's own conversion."""
        spec = _spec([_at(20, 15345, ["D"])],
                     [plot_for("scatter", xvar="when")],
                     bo={"formats": {"when": "%td"}})
        lab = _all_labels(spec, mode)[0]
        assert lab.x == dr._dash_axis_positions([15345], "td")[0]
        assert lab.y == 20

    def test_second_axis(self, mode):
        plots = [plot_for("scatter"),
                 plot_for("scatter", {"yaxis": "2"}, yvar="price")]
        lab = _all_labels(_spec([_at(10000, 3000, ["Y2"], ya=2)], plots),
                          mode)[0]
        assert (lab.y_range_name, lab.y) == ("y2", 10000)
        caught = []
        figs = _figs(_spec([_at(10000, 3000, ["Y2"], ya=2)]), mode,
                     caught=caught)
        assert [lab for f in figs for lab in _labels(f)] == []
        assert sum("added_text entry was not drawn" in m for m in caught) == 1


@pytest.mark.parametrize("mode", MODES)
class TestLongText:
    """twoway draws a typed text() of any length or line count (measured:
    4,097, 20,000 and 100,000 characters, 65 and 300 lines, all rc 0), so
    the renderer draws each one dash.ado writes.  A line past 254 columns
    keeps twoway's last wrapped piece after "> " (_dash_gt_column)."""

    @pytest.mark.parametrize("lines", [["a" * 4100], ["a" * 100000],
                                       [f"l{i}" for i in range(65)],
                                       [f"l{i}" for i in range(300)]],
                             ids=["4100c", "100000c", "65l", "300l"])
    def test_drawn_whole(self, mode, lines):
        caught = []
        figs = _figs(_spec([_at(30, 3000, lines)]), mode, caught=caught)
        labs = [lab for f in figs for lab in _labels(f)]
        def drawn(t):
            if len(t) <= dr._DASH_GT_LINE_WIDTH:
                return t
            return "> " + t[len(t) - (dr._dash_gt_column(len(t)) - 2):]
        assert [lab.text for lab in labs] == [
            "\n".join(drawn(t) for t in lines)]
        assert not any("not drawn" in m for m in caught)

    def test_a_line_that_is_no_string_is_still_refused(self, mode):
        caught = []
        figs = _figs(_spec([_at(30, 3000, ["a", 5])]), mode, caught=caught)
        assert [lab for f in figs for lab in _labels(f)] == []
        assert sum("added_text entry was not drawn" in m for m in caught) == 1


@pytest.mark.parametrize("mode", MODES)
class TestByPanels:
    def test_every_panel(self, mode):
        """Each panel draws each text once, at the panel's text scale
        applied exactly once."""
        rec = [_at(30, 3000, ["BYT"])]
        plain = _all_labels(_spec(rec), mode)[0]
        figs = _figs(_spec(rec, go={"by": "foreign"}), mode)
        panels = [f for f in figs if _labels(f)]
        assert len(panels) == 2
        m = dr._dash_by_size_mult("foreign", 2)
        for f in panels:
            (lab,) = _labels(f)
            assert math.isclose(_pt(lab.text_font_size),
                                _pt(plain.text_font_size) * m, rel_tol=1e-6)


@pytest.mark.parametrize("mode", MODES)
class TestTheHull:
    def test_texts_never_widen_an_axis(self, mode):
        def ranges(spec):
            f = _figs(spec, mode)[0]
            return (f.x_range.start, f.x_range.end, f.y_range.start,
                    f.y_range.end)
        assert ranges(_spec([_at(100, 9000, ["FAR"])])) == ranges(_spec([]))
        assert _all_labels(_spec([_at(100, 9000, ["FAR"])]), mode)[0].y == 100


class TestFilterMove:
    _REC = [_at(30, 3000, ["MV"]), _at(20, 2000, ["MW"], "box")]

    @staticmethod
    def _seen(labels):
        return sorted((lab.text, lab.x, lab.y) for lab in labels)

    @requires_node
    def test_labels_survive_saved(self):
        spec = _spec(self._REC, bo={"filter": sfl._MOVES[0][1]})
        r = _saved(spec)
        before = self._seen(lab for f in jo._saved_figs(r)
                            for lab in _labels(f))
        sfl._move(r, sfl._MOVES[0][2])
        after = self._seen(lab for f in jo._saved_figs(r)
                           for lab in _labels(f))
        assert before == after == [("MV", 3000, 30), ("MW", 2000, 20)]

    def test_labels_survive_served(self):
        spec = _spec(self._REC, bo={"filter": sfl._MOVES[0][1]})
        figs, _ = tp._served_after_move(spec, sfl._MOVES[0][2])
        labs = sorted((a["text"], a["x"], a["y"]) for f in figs
                      for a in f["annotations"] if a["kind"] == "Label"
                      and a["text"] in ("MV", "MW"))
        assert labs == [("MV", 3000, 30), ("MW", 2000, 20)]


# ---------------------------------------------------------------------------
# The spec, the limit, the served copy and the help
# ---------------------------------------------------------------------------

def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


class TestTheSpec:
    def test_the_parser_writes_records(self):
        ado = _read(_ADO)
        assert "_dash_pending' text\"'" not in ado
        mata = _read(_MATA)
        merge = mata[mata.index("string scalar _dash_rep_merge("):]
        merge = merge[:merge.index("\n}\n")]
        assert 'if (cat == "A") return(v1 + char(30) + v2)' in merge
        plot = ado[ado.index("program define _dash_plot\n"):]
        loop = plot[plot.index("// ---- Assemble graph_options JSON ----"):]
        loop = loop[:loop.index("local gv : copy local g_`gk'")]
        # Flipped (WP-30 P1.10 part 2): the loop skips ttext() too.
        assert 'if inlist("`gk\'", "text", "ttext") continue' in loop
        assert "_dash_added_text text" in plot


@pytest.mark.parametrize("mode", MODES)
class TestTheLimit:
    def test_the_row_and_the_renderer_bound(self, mode):
        assert dr._DASH_LIMITS["added_text"] == (1000, 100000,
                                                 "dash_max_added_text")
        row = re.search(r"added_text=([0-9]+),([0-9]+)", _read(_ADO))
        assert row and (int(row.group(1)), int(row.group(2))) == (1000,
                                                                  100000)
        spec = _spec([_at(30, 3000, ["x"])] * 1001)
        # The saved renderer wraps a figure's error (as it wraps the
        # reflines refusal); the served app carries its own copy of the
        # class.
        with pytest.raises(Exception, match="dash_max_added_text") as e:
            _figs(spec, mode)
        err = e.value.__cause__ if mode == "saved" else e.value
        assert type(err).__name__ == "DashLimitError"


class TestTheServedCopy:
    def test_the_app_defines_the_names(self, tmp_path):
        _, sp, dp = jo._write(_spec([_at(30, 3000, ["x"])]), tp._DF)
        ap = tmp_path / "app.py"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(str(ap))
        src = ap.read_text(encoding="utf-8")
        for name in ("def _dash_added_text(", "def _dash_added_text_opts(",
                     "_DASH_ADDED_TEXT_PLACE =", "_DASH_ADDED_TEXT_ORIENT =",
                     "_DASH_ADDED_TEXT_HONOURED ="):
            assert name in src, name


class TestTheHelp:
    def test_the_help_documents_it(self):
        hlp = _read(_HELP)
        plot_types = hlp[hlp.index("{marker plottypes}"):
                         hlp.index("{marker differences}")]
        assert "{marker added_text}" in plot_types
        assert re.search(r"dash_max_added_text\}\}.*?default 1,000, at most"
                         r"\s+100,000", hlp, re.S)
        unsupported = hlp[hlp.index("{marker unsupported}"):]
        assert "{opt text(" not in unsupported


class TestTtext:
    def test_it_is_declared(self):
        """ttext() is declared beside text() in both syntax blocks, set in
        s(), carried by every graph-option list (and written only as
        records), and merged copy by copy as text() is (WP-30 P1.10)."""
        ado = _read(_ADO)
        assert ado.count("TTEXT(string asis)") == 2
        assert "sreturn local ttext " in ado and "sreturn local g_ttext " in ado
        lists = re.findall(r"foreach (?:gk|gkey) in ((?:[^{]|\n)*?)\{", ado)
        assert len(lists) == 7 and all(" text ttext " in " ".join(
            x.replace("///", " ").split()) + " " for x in lists)
        assert 'if inlist("`gk\'", "text", "ttext") continue' in ado
        assert "_dash_added_text ttext" in ado
        mata = _read(_MATA)
        cat = mata[mata.index("string scalar _dash_rep_cat("):]
        cat = cat[:cat.index("\n}\n")]
        assert 'if (anyof(("text", "ttext"), k)) return("A")' in cat

