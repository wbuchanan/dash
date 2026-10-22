"""
test_corpus_verdict.py -- the corpus's verdict engine (WP-33 33-05).

scripts/corpus/verdict.py reads twoway's SVG and dash's view dump into the
same checks (ticks, labels, titles, legend keys, markers, plot-region shape,
colours), compares them within the tolerances test/fixtures/
corpus_verdict_rules.json records, explains each difference by a live row
of the ledger (test/fixtures/corpus_ledger.json) and gives Same, Close or
Differs by DECISIONS A-4: geometry and colours decide Differs, the image
score only moves a clean pair from Same to Close.  TestInChrome and
TestSsimParity are release tier.
"""
import base64
import json
import os
import re
import shutil
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HERE = os.path.join(_ROOT, "test")
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import responsive_probe  # noqa: E402
from scripts.corpus import ledger, verdict  # noqa: E402

_SMOKE = os.path.join(_HERE, "fixtures", "svg_truth_smoke.svg")
_CHROME = responsive_probe.find_chrome()
_RULES = {"tick_rel": 1e-6, "extent_rel": 0.01, "aspect_abs": 0.005, "colour_tol": 2,
          "T_same": 0.9, "T_close": 0.8, "text_rel": 0.05, "inset_abs": 0.005,
          "size_rel": 0.05}


def _rdr(glyph="Scatter", n=3, x=(1, 3), y=(2, 4), marker="circle", fill="#1a85ff",
         line="#1a85ff", fill_alpha=None, line_alpha=None, visible=True,
         line_width=None, size=None):
    return {"glyph": glyph, "n": n, "x": list(x) if x else None, "y": list(y) if y else None,
            "marker": marker if glyph == "Scatter" else None, "fill": fill, "line": line,
            "line_width": line_width or {"value": 1}, "fill_alpha": fill_alpha,
            "line_alpha": line_alpha, "visible": visible, "size": size}


def _view(renderers=None, legend=("Domestic cars", "Foreign cars"), frame=(40, 10, 600, 300),
          yscale="linear"):
    return {"figures": [{
        "id": "p1", "bbox": [0, 0, 720, 432], "frame": list(frame),
        "axes": [{"side": "below", "dim": 0, "ticks": [2000, 3000, 4000, 5000],
                  "labels": ["2,000", "3,000", "4,000", "5,000"], "title": "Weight (lbs.)",
                  "scale": "linear", "tick_px": [100, 250, 400, 550]},
                 {"side": "left", "dim": 1, "ticks": [10, 20, 30, 40],
                  "labels": ["10", "20", "30", "40"], "title": "Miles per gallon",
                  "scale": yscale, "tick_px": [300, 150, 70, 10]}],
        "titles": [{"text": "", "align": "center", "side": "above"},
                   {"text": "Smoke  title", "align": "center", "side": "above"}],
        "legend": [{"label": t, "glyphs": ["Scatter"]} for t in legend],
        "renderers": renderers if renderers is not None else [_rdr()]}]}


def _geo(**kw):
    g = {"panels": 1, "x_ticks": [0.0, 10.0], "y_ticks": [0.0, 5.0], "x_labels": ["0", "10"],
         "y_labels": ["0", "5"], "axis_titles": ["x", "y"], "titles": [], "legend": [],
         "glyphs": None, "glyph_counts": [], "glyph_extents": None, "markers": [],
         "marker_shape": [], "frame_aspect": 1.5, "colours": {"set": [], "unread": 0},
         "x_span": 10.0, "y_span": 5.0}
    g.update(kw)
    return g


def _states(**kw):
    return dict(kw)


def _row(gaps4_id, check, plottype="*", when="*"):
    m = re.match(r"^(\S+?)(?: \((documented|residual)\))?$", gaps4_id)
    return {"gaps4_id": gaps4_id, "id": m.group(1), "form": m.group(2) or "plain",
            "check": check, "plottype": plottype, "when": when, "note": "n"}


class TestTwowayGeometry:

    def test_the_smoke_svg(self):
        g = verdict.twoway_geometry(_SMOKE)
        assert g["x_ticks"] == [2000.0, 3000.0, 4000.0, 5000.0]
        assert g["y_ticks"] == [10.0, 20.0, 30.0, 40.0]
        assert g["x_labels"] == ["2,000", "3,000", "4,000", "5,000"]
        assert g["y_labels"] == ["10", "20", "30", "40"]
        assert g["titles"] == ["Smoke  title"]
        assert g["axis_titles"] == ["Weight (lbs.)", "Miles per gallon"]
        assert g["legend"] == ["Domestic cars", "Foreign cars"]
        assert g["glyphs"] == 74 and g["glyph_counts"] == [52, 22]
        assert g["marker_shape"] == ["circle"]
        assert g["panels"] == 1
        assert g["x_scale"] == "linear" and g["y_scale"] == "linear"
        ext = g["glyph_extents"]
        assert abs(ext["x"][0] - 1760) < 5 and abs(ext["y"][1] - 41) < 0.2

    def test_the_smoke_colours(self):
        c = verdict.twoway_geometry(_SMOKE)["colours"]
        assert c["set"] == ["#1a85ff", "#d41159"]
        assert "#f0f0f0" not in c["set"] and "#ffffff" not in c["set"]


class TestSizesAndMargins:
    # D49: text size, the plot region's outer insets, marker size and line
    # width, each relative to the figure, on both sides.

    def test_the_smoke_svg(self):
        g = verdict.twoway_geometry(_SMOKE)
        # Tick labels 112.56 units on a 5400-unit canvas.
        assert g["text_size"] == round(112.56 / 5400, 5)
        assert g["insets"] == [round(522.79 / 5400, 4), round(309.82 / 3240, 4),
                               round((5400 - 4275.62) / 5400, 4),
                               round((3240 - 2766.65) / 3240, 4)]
        assert len(g["marker_sizes"]) == 1 and 0.005 < g["marker_sizes"][0] < 0.02
        assert g["line_widths"] == []

    def test_a_view_and_its_svg(self, tmp_path):
        svg = tmp_path / "d.svg"
        svg.write_text('<svg><text font-size="12px" x="1">2,000</text>'
                       '<text font-size="9pt" x="2">Smoke  title</text></svg>',
                       encoding="utf-8")
        g = verdict.dash_geometry(_view([
            _rdr(n=5, size={"value": 6}, line_width={"value": 1.2}),
            _rdr(glyph="Line", line_width={"value": 2.4})]), str(svg))
        assert g["text_size"] == round(12 / 720, 5)
        assert g["insets"] == [round(40 / 720, 4), round(10 / 432, 4),
                               round(80 / 720, 4), round(122 / 432, 4)]
        assert g["marker_sizes"] == [round(7.2 / 720, 5)]
        assert g["line_widths"] == [round(2.4 / 720, 5)]

    def test_compare(self):
        tw = _geo(text_size=0.02, insets=[0.1, 0.1, 0.1, 0.1], marker_sizes=[0.01],
                  line_widths=[0.002])
        same = _geo(text_size=0.0205, insets=[0.102, 0.1, 0.1, 0.1],
                    marker_sizes=[0.0102], line_widths=[0.00202])
        assert verdict.compare(tw, same, _RULES) == []
        off = _geo(text_size=0.0178, insets=[0.12, 0.1, 0.1, 0.1], marker_sizes=[0.0089],
                   line_widths=[0.00178])
        assert [d["check"] for d in verdict.compare(tw, off, _RULES)] == [
            "text_size", "margins", "marker_size", "line_width"]
        assert verdict.summary(verdict.compare(tw, off, _RULES)) == \
            "text size, margins, marker size, line width"

    def test_colour_opacity(self):
        assert verdict.rgb("#1a85ff80") == (26, 133, 255, 128)
        assert verdict.colour_diff(["#1a85ff"], ["#1a85ff80"], 2) == (["#1a85ff"],
                                                                      ["#1a85ff80"])
        g = verdict.dash_geometry(_view([_rdr(fill="#1a85ff", line="#1a85ff",
                                              fill_alpha={"value": 0.5})]))
        assert g["colours"]["set"] == ["#1a85ff", "#1a85ff80"]


class TestOutlines:
    # D51: an outline dash strokes on a bar, histogram, rbar or area where
    # twoway strokes none is its own check, outside line_width.

    def _svg(self, tmp_path, stroked):
        text = open(_SMOKE, encoding="utf-8").read()
        bars = '<rect x="1000.00" y="1500.00" width="12.00" height="60.00" style="fill:#489DFF"/>\n'
        if stroked:
            bars += ('<rect x="1003.24" y="1503.24" width="5.52" height="53.52" '
                     'style="fill:none;stroke:#1A85FF;stroke-width:6.48"/>\n')
        p = tmp_path / ("s%d.svg" % stroked)
        p.write_text(text.replace("</svg>", bars + "</svg>"), encoding="utf-8")
        return str(p)

    def test_twoway_bars(self, tmp_path):
        assert verdict.twoway_geometry(_SMOKE)["outlined"] is None
        g = verdict.twoway_geometry(self._svg(tmp_path, False))
        assert g["outlined"] is False and g["glyphs"] == 74
        g = verdict.twoway_geometry(self._svg(tmp_path, True))
        assert g["outlined"] is True and round(6.48 / 5400, 5) in g["line_widths"]

    def test_dash_bars(self):
        bar = _rdr(glyph="VBar", fill={"value": "#489dff"}, line={"value": "#1a85ff"},
                   line_width={"value": 0.768})
        g = verdict.dash_geometry(_view([bar]))
        assert g["outlined"] is True
        g = verdict.dash_geometry(_view([dict(bar, line_alpha={"value": 0})]))
        assert g["outlined"] is False
        assert verdict.dash_geometry(_view())["outlined"] is None

    def test_compare(self):
        tw = _geo(outlined=False, line_widths=[0.0018], line_widths_lines=[0.0018])
        da = _geo(outlined=True, line_widths=[0.0018, 0.00107], line_widths_lines=[0.0018])
        assert [d["check"] for d in verdict.compare(tw, da, _RULES)] == ["outline_extra"]
        both = _geo(outlined=True, line_widths=[0.0012], line_widths_lines=[])
        assert verdict.compare(both, dict(both, line_widths=[0.00107]), _RULES)[0]["check"] \
            == "line_width"
        assert verdict.summary([{"check": "outline_extra"}]) == "bar outline"


class TestMarkerLabels:
    # D50 (MS-15): twoway lets a marker label run past the plot region; dash
    # clips it at the region's edge.

    def test_twoway_label_past_the_region(self, tmp_path):
        text = open(_SMOKE, encoding="utf-8").read()
        assert verdict.twoway_geometry(_SMOKE)["labels_outside"] is None
        # A label anchored at its end just inside the left edge runs past it.
        lab = ('<text x="600.00" y="1500.00" style="font-family:\'Helvetica\';'
               'font-size:89.94px;fill:#1A85ff" text-anchor="end">Honduras</text>\n')
        p = tmp_path / "lab.svg"
        p.write_text(text.replace("</svg>", lab + "</svg>"), encoding="utf-8")
        assert verdict.twoway_geometry(str(p))["labels_outside"] is True
        lab = lab.replace('x="600.00"', 'x="2400.00"')
        p.write_text(text.replace("</svg>", lab + "</svg>"), encoding="utf-8")
        assert verdict.twoway_geometry(str(p))["labels_outside"] is False

    def test_dash_clips_its_labels(self, tmp_path):
        svg = tmp_path / "d.svg"
        clipped = ('<g clip-path="url(#d5)"><text font-size="8pt" x="20.8" y="171" '
                   'text-anchor="start">Honduras</text></g>')
        svg.write_text("<svg>" + clipped + "</svg>", encoding="utf-8")
        assert verdict.dash_geometry(_view(), str(svg))["labels_outside"] is False
        free = '<text font-size="8pt" x="45" y="171" text-anchor="start">Honduras</text>'
        svg.write_text("<svg>" + free + "</svg>", encoding="utf-8")
        assert verdict.dash_geometry(_view(), str(svg))["labels_outside"] is False
        svg.write_text("<svg></svg>", encoding="utf-8")
        assert verdict.dash_geometry(_view(), str(svg))["labels_outside"] is None
        free = '<text font-size="8pt" x="60" y="171" text-anchor="end">Honduras</text>'
        svg.write_text("<svg>" + free + "</svg>", encoding="utf-8")
        assert verdict.dash_geometry(_view(), str(svg))["labels_outside"] is True

    def test_compare(self):
        d = verdict.compare(_geo(labels_outside=True), _geo(labels_outside=False), _RULES)
        assert d == [{"check": "marker_labels", "twoway": True, "dash": False,
                      "within_tol": False}]
        assert verdict.compare(_geo(labels_outside=None), _geo(labels_outside=False),
                               _RULES) == []
        assert verdict.summary(d) == "marker labels"


class TestDashGeometry:

    def test_axes_titles_legend_glyphs(self):
        g = verdict.dash_geometry(_view([_rdr(n=52, marker="circle"),
                                         _rdr(n=22, marker="cross", fill="#d41159",
                                              line="#d41159", x=(5, 9), y=(0, 2))],
                                        yscale="log"))
        assert g["x_ticks"] == [2000, 3000, 4000, 5000]
        assert g["y_labels"] == ["10", "20", "30", "40"]
        assert g["axis_titles"] == ["Weight (lbs.)", "Miles per gallon"]
        assert g["titles"] == ["Smoke  title"]
        assert g["legend"] == ["Domestic cars", "Foreign cars"]
        assert g["glyphs"] == 74 and g["glyph_counts"] == [52, 22]
        assert g["marker_shape"] == ["circle", "plus"]
        assert g["glyph_extents"] == {"x": [1, 9], "y": [0, 4]}
        assert g["frame_aspect"] == 2.0 and g["panels"] == 1
        assert g["x_scale"] == "linear" and g["y_scale"] == "log"
        # Tick positions as shares of the plot region, from its low edge.
        assert g["x_tick_pos"] == [0.1, 0.35, 0.6, 0.85]
        assert g["y_tick_pos"] == [0.0333, 0.5333, 0.8, 1.0]

    def test_hidden_colours_are_left_out(self):
        g = verdict.dash_geometry(_view([
            _rdr(glyph="Patch", n=10, fill={"value": "#1a85ff"}, line="#1f77b4",
                 line_alpha=0),
            _rdr(fill="#00ff00", line="#d41159", fill_alpha={"value": 0}),
            _rdr(fill="#123456", line="#654321", visible=False),
            _rdr(glyph="Line", fill={"field": "c"}, line=None)]))
        assert g["colours"]["set"] == ["#1a85ff", "#d41159"]
        assert g["colours"]["unread"] == 1

    def test_a_hidden_legend_is_left_out(self, tmp_path):
        svg = tmp_path / "d.svg"
        svg.write_text("<svg><text x='1'>Miles per gallon</text>"
                       "<text x='2'>Domestic cars</text></svg>", encoding="utf-8")
        g = verdict.dash_geometry(_view(legend=("Domestic cars", "Miles per gallon")), str(svg))
        assert g["legend"] == ["Domestic cars"]


class TestCompare:

    def test_tolerances(self):
        tw = _geo(x_ticks=[0.0, 10.0], x_span=10.0, frame_aspect=1.5)
        same = _geo(x_ticks=[0.000001, 10.0], frame_aspect=1.504)
        assert verdict.compare(tw, same, _RULES) == []
        off = _geo(x_ticks=[0.1, 10.0], frame_aspect=1.6, x_labels=["0", "10"])
        assert {d["check"] for d in verdict.compare(tw, off, _RULES)} == {"x_ticks",
                                                                          "frame_aspect"}
        big = _geo(x_labels=["2,000"])
        d = verdict.compare(_geo(x_labels=["2000"]), big, _RULES)
        assert [x["check"] for x in d] == ["x_labels"]
        assert d[0] == {"check": "x_labels", "twoway": ["2000"], "dash": ["2,000"],
                        "within_tol": False}

    def test_labels_twoway_leaves_off(self):
        # D48 (BY-32): twoway draws no x labels on a by() panel above the
        # bottom row; dash labels it.  That is its own check.
        d = verdict.compare(_geo(x_labels=[], x_ticks=[]), _geo(), _RULES)
        assert [x["check"] for x in d] == ["x_labels_none"]
        d = verdict.compare(_geo(), _geo(x_labels=[], x_ticks=[]), _RULES)
        assert [x["check"] for x in d] == ["x_labels"]
        assert verdict.summary([{"check": "x_labels_none"}]) == "x-axis labels"

    def test_axis_scale(self):
        # D46: a log axis against a linear one is a geometry difference.
        d = verdict.compare(_geo(y_scale="linear"), _geo(y_scale="log"), _RULES)
        assert d == [{"check": "y_scale", "twoway": "linear", "dash": "log",
                      "within_tol": False}]
        assert verdict.compare(_geo(y_scale=None), _geo(y_scale="log"), _RULES) == []
        assert verdict.compare(_geo(x_scale="log"), _geo(x_scale="log"), _RULES) == []
        assert verdict.summary(d) == "y-axis scale"

    def test_colours(self):
        assert verdict.rgb("#1A85FF") == (26, 133, 255)
        assert verdict.rgb("#fff") == (255, 255, 255)
        assert verdict.rgb("rgb(1, 2, 3)") == (1, 2, 3)
        assert verdict.rgb("navy") is None
        assert verdict.colour_diff(["#1a85ff"], ["#1b86fe"], 2) == ([], [])
        assert verdict.colour_diff(["#1a85ff"], ["#ff0000"], 2) == (["#1a85ff"], ["#ff0000"])
        assert verdict.colour_diff(["#1a85ff", "navy"], ["#1a85ff"], 2) == ([], [])
        assert verdict.colour_distances(["#1a85ff"], ["#1b86fe"]) == [1, 1]
        tw = _geo(colours={"set": ["#1a85ff"], "unread": 0})
        d = verdict.compare(tw, _geo(colours={"set": ["#ff0000"], "unread": 0}), _RULES)
        assert d == [{"check": "colours", "twoway": ["#1a85ff"], "dash": ["#ff0000"],
                      "within_tol": False}]
        assert verdict.compare(tw, _geo(colours={"set": [], "unread": 2}), _RULES) == []

    def test_marker_shape_and_extents(self):
        ext = {"x": [0.0, 10.0], "y": [0.0, 5.0]}
        tw = _geo(glyphs=3, glyph_counts=[3], marker_shape=["circle"], glyph_extents=ext)
        da = _geo(glyphs=3, glyph_counts=[3], marker_shape=["triangle"],
                  glyph_extents={"x": [0.05, 10.0], "y": [0.0, 5.0]})
        assert [d["check"] for d in verdict.compare(tw, da, _RULES)] == ["marker_shape"]
        far = dict(da, marker_shape=["circle"], glyph_extents={"x": [0.2, 10.0],
                                                               "y": [0.0, 5.0]})
        assert [d["check"] for d in verdict.compare(tw, far, _RULES)] == ["glyph_extents"]
        g = verdict.dash_geometry(_view([_rdr(marker="cross")]))
        assert g["marker_shape"] == ["plus"]
        none = _geo()
        assert verdict.compare(tw, none, _RULES) == []
        rev = _geo(glyphs=3, glyph_counts=[3], marker_shape=["circle"])
        assert verdict.compare(rev, far, _RULES) == []

    def test_a_reversed_axis_gives_no_extents(self, tmp_path):
        text = open(_SMOKE, encoding="utf-8").read()
        p = tmp_path / "rev.svg"
        # Number the y labels the other way up: the fit is reversed.
        for a, b in (("10<", "@1<"), ("40<", "10<"), ("@1<", "40<"),
                     ("20<", "@2<"), ("30<", "20<"), ("@2<", "30<")):
            text = text.replace(">" + a, ">" + b)
        p.write_text(text, encoding="utf-8")
        g = verdict.twoway_geometry(str(p))
        assert g["glyphs"] == 74 and g["glyph_extents"] is None
        far = _geo(glyphs=74, glyph_counts=[52, 22], marker_shape=["circle"],
                   glyph_extents={"x": [1000.0, 9000.0], "y": [0.0, 99.0]})
        assert "glyph_extents" not in [d["check"] for d in verdict.compare(g, far, _RULES)]


class TestLedger:

    def test_explain(self):
        d = [{"check": "x_ticks", "twoway": [1], "dash": [2], "within_tol": False}]
        ex = {"id": "e", "plottype": "histogram", "cmd": "twoway histogram mpg, by(foreign)"}
        open_ = {"AX-4": "open"}
        assert verdict.explain(d, ex, [_row("AX-4", "x_ticks", "histogram")],
                               open_)[0]["gaps4"] == "AX-4"
        assert verdict.explain(d, ex, [_row("AX-4", "x_ticks")],
                               {"AX-4": "closed"})[0]["gaps4"] is None
        assert verdict.explain(d, ex, [_row("AX-4", "x_ticks", "scatter")],
                               open_)[0]["gaps4"] is None
        assert verdict.explain(d, ex, [_row("AX-2", "x_ticks", "*", r"\bby\(")],
                               {"AX-2": "open"})[0]["gaps4"] == "AX-2"
        assert verdict.explain(d, ex, [_row("AX-2", "x_ticks", "*", r"range\(")],
                               {"AX-2": "open"})[0]["gaps4"] is None
        assert verdict.explain(d, ex, [_row("AX-4", "y_ticks")], open_)[0]["gaps4"] is None
        assert verdict.explain(d, ex, [_row("GW-6 (documented)", "x_ticks")],
                               {"GW-6": "documented"})[0]["gaps4"] == "GW-6 (documented)"
        assert verdict.explain(d, ex, [_row("GW-6 (residual)", "x_ticks")],
                               {"GW-6": "partly"})[0]["gaps4"] == "GW-6 (residual)"
        assert verdict.explain(d, ex, [_row("GW-6 (residual)", "x_ticks")],
                               {"GW-6": "documented"})[0]["gaps4"] is None

    def test_load_ledger(self, tmp_path):
        p = tmp_path / "l.json"
        p.write_text(json.dumps({"_meta": {}, "rows": [_row("AX-4", "x_ticks")]}))
        assert verdict.load_ledger(str(p)) == [_row("AX-4", "x_ticks")]


class TestSsim:

    def test_basic_properties(self):
        import numpy
        rng = numpy.random.default_rng(3)
        a = rng.integers(0, 256, (48, 64)).astype(float)
        assert abs(verdict.ssim(a, a) - 1.0) < 1e-9
        assert verdict.ssim(a, 255 - a) < 0.1
        b = numpy.clip(a + rng.normal(0, 20, a.shape), 0, 255)
        assert abs(verdict.ssim(a, b) - verdict.ssim(b, a)) < 1e-12


@pytest.mark.release
class TestSsimParity:

    def test_against_scikit_image(self):
        metrics = pytest.importorskip("skimage.metrics")
        import numpy
        rng = numpy.random.default_rng(7)
        a = rng.integers(0, 256, (48, 64)).astype(float)
        b = numpy.clip(a + rng.normal(0, 40, a.shape), 0, 255)
        ref = metrics.structural_similarity(a, b, gaussian_weights=True, sigma=1.5,
                                            use_sample_covariance=False, data_range=255)
        assert round(verdict.ssim(a, b), 4) == round(float(ref), 4)


class TestVerdict:

    def test_every_branch(self):
        v = verdict.verdict
        rc = {"check": "rc", "twoway": "r(198)", "dash": "r(0)", "within_tol": False}
        fl = {"check": "first_line", "twoway": "a", "dash": "b", "within_tol": False}
        assert v(198, 198, "a", "a", [], None, _RULES) == "Same"
        assert v(198, 198, "a", "b", [dict(fl, gaps4=None)], None, _RULES) == "Differs"
        assert v(198, 198, "a", "b", [dict(fl, gaps4="X-1")], None, _RULES) == "Close"
        assert v(198, 0, "a", None, [dict(rc, gaps4="X-1 (documented)")], None,
                 _RULES) == "Close"
        assert v(198, 0, "a", None, [dict(rc, gaps4=None)], None, _RULES) == "Differs"
        geo = {"check": "x_ticks", "twoway": [1], "dash": [2], "within_tol": False}
        assert v(0, 0, None, None, [dict(geo, gaps4=None)], 1.0, _RULES) == "Differs"
        assert v(0, 0, None, None, [dict(geo, gaps4="AX-4")], 0.1, _RULES) == "Close"
        assert v(0, 0, None, None, [], 0.95, _RULES) == "Same"
        assert v(0, 0, None, None, [], 0.5, _RULES) == "Close"
        assert v(0, 0, None, None, [], None, _RULES) == "Close"
        assert v(0, 0, None, None, [], 0.1, dict(_RULES, T_same=None)) == "Same"


class TestSummary:

    def test_wording(self):
        d = [{"check": "x_ticks", "gaps4": "AX-4"}, {"check": "legend", "gaps4": None}]
        assert verdict.summary(d) == "x-axis ticks, legend keys"
        assert verdict.summary([{"check": "x_ticks"}, {"check": "y_ticks"}]) == \
            "x-axis ticks, y-axis ticks"
        assert verdict.summary([]) == "Same"
        under = [k for k in verdict.STATA_TERMS if "_" in k]
        for k in verdict.STATA_TERMS:
            s = verdict.summary([{"check": k, "gaps4": "AX-4"}])
            assert not re.search(r"\b[A-Z]{2,4}-[0-9]+\b", s), s
            assert not any(u in s for u in under), s
        everything = verdict.summary([{"check": k} for k in verdict.STATA_TERMS] * 5)
        assert len(everything) <= 200 and not everything.endswith(",")
        with pytest.raises(KeyError):
            verdict.summary([{"check": "no_such_check"}])


class TestGallery:

    def test_only_what_twoway_draws(self):
        rc = {"check": "rc", "twoway": "r(0)", "dash": "r(198)", "within_tol": False}
        g = verdict.gallery
        assert g({"rc_twoway": 198, "rc_dash": 198, "differences": [], "skip": None}) is False
        assert g({"rc_twoway": 0, "rc_dash": 198, "skip": None,
                  "differences": [dict(rc, gaps4="SD-1 (documented)")]}) is False
        assert g({"rc_twoway": 0, "rc_dash": 198, "skip": None,
                  "differences": [dict(rc, gaps4="SD-1")]}) is True
        assert g({"rc_twoway": 0, "rc_dash": 0, "differences": [], "skip": None}) is True
        assert g({"rc_twoway": 0, "rc_dash": 0, "differences": [], "skip": "x"}) is False


class _StubProbe:

    def __init__(self, w, h):
        self.w, self.h = w, h

    def eval_async(self, expr):
        assert "drawImage" in expr
        return base64.b64encode(bytes([200]) * (self.w * self.h)).decode("ascii")

    def __exit__(self, *exc):
        return False


class TestJudge:

    def _run(self, tmp_path):
        (tmp_path / "twoway").mkdir()
        (tmp_path / "dash").mkdir()
        shutil.copy(_SMOKE, tmp_path / "twoway" / "e1.svg")
        shutil.copy(_SMOKE, tmp_path / "dash" / "e1.svg")
        (tmp_path / "dash" / "e1.view.json").write_text(json.dumps(_view([
            _rdr(n=52, x=(1760, 4840), y=(12, 41)),
            _rdr(n=22, fill="#d41159", line="#d41159", x=(1760, 4840), y=(12, 41))])))
        ex = {"id": "e1", "plottype": "scatter", "source": "help",
              "cmd": "twoway scatter mpg weight"}
        tw = {"id": "e1", "rc": 0, "first_line": None, "svg": "twoway/e1.svg",
              "width_in": 0.5, "height_in": 0.25, "skip": None}
        da = {"id": "e1", "rc": 0, "first_line": None, "svg": "dash/e1.svg",
              "view": "dash/e1.view.json", "size_matched": True, "w": 48, "h": 24,
              "skip": None}
        return ex, tw, da

    def test_a_row_has_every_published_key(self, tmp_path):
        ex, tw, da = self._run(tmp_path)
        row = verdict.judge(ex, tw, da, str(tmp_path), _RULES, [], {},
                            probe=_StubProbe(48, 24))
        assert set(row) == set(verdict.ROW_KEYS) == {
            "id", "plottype", "source", "rc_twoway", "rc_dash", "rc_pair", "first_twoway",
            "first_dash", "verdict", "ssim", "size_matched", "panels", "differences",
            "checks", "ledger", "summary", "colours", "gallery", "skip"}
        assert row["ssim"] == 1.0 and row["rc_pair"] == [0, 0]
        assert row["panels"] == "1 of 1" and row["gallery"] is True
        assert row["colours"]["twoway"] == ["#1a85ff", "#d41159"]
        assert row["verdict"] in ("Same", "Close", "Differs")
        skipped = verdict.judge(ex, dict(tw, rc=None, skip="setup rc 111"), da,
                                str(tmp_path), _RULES, [], {}, probe=_StubProbe(48, 24))
        assert skipped["verdict"] is None and skipped["gallery"] is False
        assert skipped["skip"] == "setup rc 111"

    def test_the_image_step(self, tmp_path):
        ex, tw, da = self._run(tmp_path)
        loose = dict(_RULES, aspect_abs=1.0, text_rel=10.0, inset_abs=1.0, size_rel=10.0)
        row = verdict.judge(ex, tw, da, str(tmp_path), dict(loose, T_same=0.99), [], {},
                            probe=_StubProbe(48, 24))
        assert row["verdict"] == "Same" and row["differences"] == []
        assert row["summary"] == "Same"
        row = verdict.judge(ex, tw, da, str(tmp_path), dict(loose, T_same=1.5), [], {},
                            probe=_StubProbe(48, 24))
        assert row["verdict"] == "Close" and row["checks"] == ["image"]
        assert row["summary"] == "picture"
        row = verdict.judge(ex, tw, da, str(tmp_path),
                            dict(_RULES, text_rel=10.0, inset_abs=1.0, size_rel=10.0),
                            [{"gaps4_id": "GW-6", "id": "GW-6", "form": "plain",
                              "check": "frame_aspect", "plottype": "*", "when": "*",
                              "note": "n"}], {"GW-6": "open"}, probe=_StubProbe(48, 24))
        assert row["verdict"] == "Close" and row["ledger"] == ["GW-6"]
        assert row["summary"] == "plot region shape"

    def test_a_refusal_pair(self, tmp_path):
        ex, tw, da = self._run(tmp_path)
        tw = dict(tw, rc=198, first_line="option nosuch not allowed", svg=None)
        da = dict(da, rc=198, first_line="option nosuch  not allowed", svg=None)
        row = verdict.judge(ex, tw, da, str(tmp_path), _RULES, [], {})
        assert row["verdict"] == "Same" and row["gallery"] is False

    def test_run_writes_every_row(self, tmp_path, monkeypatch):
        ex, tw, da = self._run(tmp_path)
        for name, rows in (("examples", [ex]), ("twoway", [tw]), ("dash", [da])):
            (tmp_path / (name + ".jsonl")).write_text(json.dumps(rows[0]) + "\n")
        rules = tmp_path / "rules.json"
        rules.write_text(json.dumps(_RULES))
        led = tmp_path / "ledger.json"
        led.write_text(json.dumps({"_meta": {}, "rows": []}))
        monkeypatch.setattr(verdict, "_open_probe", lambda run_dir: _StubProbe(48, 24))
        c = verdict.run(str(tmp_path), str(rules), str(led))
        assert sum(c.values()) == 1
        rows = [json.loads(x) for x in (tmp_path / "verdicts.jsonl").read_text().splitlines()]
        assert [r["id"] for r in rows] == ["e1"]
        assert verdict.main(["--run", str(tmp_path), "--rules", str(rules),
                             "--ledger", str(led)]) == 0


@pytest.mark.release
@pytest.mark.skipif(not _CHROME, reason="headless Chrome is not installed "
                    "(set DASH_CHROME); a skip is red under DASH_STRICT=1")
class TestInChrome:

    def test_raster_and_score(self, tmp_path):
        text = open(_SMOKE, encoding="utf-8").read()
        probe = verdict._open_probe(str(tmp_path))
        try:
            a = verdict.raster(probe, text, 360, 216)
            b = verdict.raster(probe, text, 360, 216)
            c = verdict.raster(probe, text.replace(">Smoke", ">"), 360, 216)
        finally:
            probe.__exit__(None, None, None)
        assert a.shape == (216, 360)
        assert verdict.ssim(a, b) == 1.0
        assert verdict.ssim(a, c) < 1.0
