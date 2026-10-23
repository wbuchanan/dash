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


def _no_region_svg():
    """plotregion(style(none)) xsca(noline) yline(0, lstyle(foreground)): no
    plot-region rect, a black yline at 0 longer than any other black line."""
    st = "font-family:'Helvetica';font-size:112.56px;fill:#000000"
    out = ['<svg version="1.1" viewBox="0 0 5400 3240">',
           '<rect x="0" y="0" width="5400" height="3240" style="fill:#FFFFFF"/>',
           '<line x1="532" y1="113" x2="532" y2="2774" style="stroke:#000000;stroke-width:5"/>',
           '<line x1="532" y1="1858" x2="5287" y2="1858" style="stroke:#000000;stroke-width:5"/>']
    for y, lab in ((2694, "-.5"), (1858, "0"), (1022, ".5"), (186, "1")):
        out.append('<line x1="492" y1="%d" x2="532" y2="%d" style="stroke:#000000;'
                   'stroke-width:5"/>' % (y, y))
        out.append('<text x="465" y="%d" style="%s" text-anchor="end">%s</text>'
                   % (y + 40, st, lab))
    for x, lab in ((603, "0"), (1756, "&#960;"), (2908, "2&#960;"), (4060, "3&#960;"),
                   (5215, "4&#960;")):
        out.append('<line x1="%d" y1="2774" x2="%d" y2="2814" style="stroke:#000000;'
                   'stroke-width:5"/>' % (x, x))
        out.append('<text x="%d" y="2913" style="%s" text-anchor="middle">%s</text>'
                   % (x, st, lab))
    out.append('<text x="2909" y="3070" style="%s" text-anchor="middle">x</text>' % st)
    out.append('<text x="215" y="1440" style="%s" transform="rotate(-90 215,1440)" '
               'text-anchor="middle">y</text>' % st)
    out.append("</svg>")
    return "\n".join(out)


class TestNoPlotRegionRect:
    # D56 (row 1 of the 23oct2026 review): with no plot-region rect the
    # region was read from the longest black horizontal line -- a yline --
    # so the region ended at y = 0, the y axis's 0 label was read as the x
    # axis's only label and the real x labels as titles.

    def test_the_region_spans_the_y_axis(self, tmp_path):
        p = tmp_path / "f.svg"
        p.write_text(_no_region_svg(), encoding="utf-8")
        g = verdict.twoway_geometry(str(p))
        assert g["x_labels"] == ["0", "\u03c0", "2\u03c0", "3\u03c0", "4\u03c0"]
        assert g["y_ticks"] == [-0.5, 0.0, 0.5, 1.0]
        assert g["axis_titles"] == ["x", "y"]
        assert g["titles"] == []


class TestOverlappingMarkers:
    # D56 (audit-CV-6): two markers of different colours drawn at one spot
    # fall in one group; each is a marker, whatever its colour.

    def test_each_colour_at_one_spot_counts(self, tmp_path):
        text = open(_SMOKE, encoding="utf-8").read()
        red = ('<circle cx="1897.59" cy="1846.80" r="21.74" style="fill:#D41159"/>\n'
               '<circle cx="1897.59" cy="1846.80" r="16.88" style="fill:none;'
               'stroke:#D41159;stroke-width:9.72"/>\n')
        first = '<circle cx="2365.71" cy="2039.68"'
        p = tmp_path / "o.svg"
        p.write_text(text.replace(first, red + first, 1), encoding="utf-8")
        g = verdict.twoway_geometry(str(p))
        assert g["glyphs"] == 75
        assert sum(g["glyph_counts"]) == 75
        # audit-MS-11: half a pixel apart, still two markers.
        p.write_text(text.replace(first, red.replace("1897.59", "1898.09") + first, 1),
                     encoding="utf-8")
        assert verdict.twoway_geometry(str(p))["glyphs"] == 75


class TestTwoYAxes:
    # D56 (audit-MS-11): with a second y axis dash's view gives every
    # renderer's data in its own axis's units, and twoway's markers are
    # read on the first axis only: the y extents are not comparable.

    def test_no_y_extents_on_two_y_axes(self):
        v = _view([_rdr(x=(1, 3), y=(2, 4)), _rdr(x=(1, 3), y=(100, 900))])
        ax = v["figures"][0]["axes"]
        ax.append(dict(ax[1], side="right"))
        g = verdict.dash_geometry(v)
        assert g["y_axes"] == 2
        tw = _geo(glyphs=6, glyph_counts=[3, 3], marker_shape=["circle"],
                  glyph_extents={"x": [1.0, 3.0], "y": [2.0, 4.0]})
        da = dict(tw, glyph_extents=g["glyph_extents"], y_axes=2)
        assert verdict.compare(tw, da, _RULES) == []


class TestCapsAreNoMarkers:
    # D56 (rows 2 and 4 of the 23oct2026 review): dash draws an rcap's or
    # rpcap's caps as Scatter glyphs with Bokeh's "dash" marker; twoway draws
    # them as lines, which no reader takes for a marker.  They are no
    # markers: not counted, no symbol, no position.

    def test_dash_marker_is_left_out(self):
        g = verdict.dash_geometry(_view([
            _rdr(n=74, x=(1760, 4840), y=(12, 41)),
            _rdr(n=74, marker="dash", x=(1760, 4840), y=(9, 41)),
            _rdr(n=74, marker="dash", x=(1760, 4840), y=(12, 44))]))
        assert g["glyphs"] == 74 and g["glyph_counts"] == [74]
        assert g["marker_shape"] == ["circle"]
        assert g["glyph_extents"] == {"x": [1760, 4840], "y": [12, 41]}
        caps = verdict.dash_geometry(_view([_rdr(n=5, marker="dash")]))
        assert caps["glyphs"] is None and caps["marker_shape"] == []
        # ex-comprehensive_demo rcap: a cap's fill is not drawn.
        caps = verdict.dash_geometry(_view([_rdr(n=5, marker="dash", fill="#1a85ff",
                                                 line="#1a476f")]))
        assert caps["colours"]["set"] == ["#1a476f"]


class TestHiddenAxis:
    # D56 (row 3 of the 23oct2026 review): ysca(off) hides dash's y axis,
    # but the view dump still lists its ticks, labels and title.  An axis
    # whose labels the picture does not draw has none.

    def test_an_axis_not_drawn_has_no_labels(self, tmp_path):
        svg = tmp_path / "d.svg"
        svg.write_text("<svg>" + "".join("<text x='%d'>%s</text>" % (k, t) for k, t in
                                         enumerate(["2,000", "3,000", "4,000", "5,000",
                                                    "Weight (lbs.)"])) + "</svg>",
                       encoding="utf-8")
        g = verdict.dash_geometry(_view(legend=()), str(svg))
        assert g["x_labels"] == ["2,000", "3,000", "4,000", "5,000"]
        assert g["y_labels"] == [] and g["y_ticks"] == []
        assert g["axis_titles"] == ["Weight (lbs.)"]


class TestRegionFromGridlines:
    # D56 (help-twoway_function): plotregion(style(none)) ysca(off)
    # xsca(noline) leaves no region rect and no axis line; the dashed
    # gridlines span the region.

    def test_labels_under_gridlines(self, tmp_path):
        st = "font-family:'Helvetica';font-size:112.56px;fill:#000000"
        out = ['<svg version="1.1" viewBox="0 0 5400 3240">',
               '<rect x="0" y="0" width="5400" height="3240" style="fill:#FFFFFF"/>']
        for x, lab in ((600, "-4 SD"), (2900, "Mean"), (5200, "4 SD")):
            for y in range(120, 2800, 97):
                out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" style="stroke:#F0F0F0;'
                           'stroke-width:9.72"/>' % (x, y, x, y + 65))
            out.append('<line x1="%d" y1="2810" x2="%d" y2="2850" style="stroke:#000000;'
                       'stroke-width:5"/>' % (x, x))
            out.append('<text x="%d" y="2950" style="%s" text-anchor="middle">%s</text>'
                       % (x, st, lab))
        out.append("</svg>")
        p = tmp_path / "g.svg"
        p.write_text("\n".join(out), encoding="utf-8")
        assert verdict.twoway_geometry(str(p))["x_labels"] == ["-4 SD", "Mean", "4 SD"]


class TestLabelsWithoutTicks:
    # D56 (gpdf-graph_twoway_bar): xsca(noline) and no tick marks leave
    # twoway's reader no tick to read the labels by; the labels are there.

    def test_labels_drawn_by_both(self):
        tw = _geo(x_labels=[], x_ticks=[], x_tick_n=0, drawn=["12", "10", "10", "12", "x"])
        da = _geo(x_labels=["12", "10", "10", "12"], drawn=[])
        assert verdict.compare(tw, da, _RULES) == []
        tw = dict(tw, drawn=["12", "10", "x"])
        assert [d["check"] for d in verdict.compare(tw, da, _RULES)] == ["x_labels_none"]


class TestASmallBoxIsNoRegion:
    # D56 (help-scatter scheme(economist)): the scheme draws no plot-region
    # rect; the first solid rect is note("1")'s small box.  The long solid
    # gridlines and the axis line span the region instead.

    def test_a_note_box_is_not_the_region(self, tmp_path):
        st = "font-family:'Helvetica';font-size:30px;fill:#000000"
        out = ['<svg version="1.1" viewBox="0 0 1584 1584">',
               '<rect x="0" y="0" width="1584" height="1584" style="fill:#C6D3DF"/>',
               '<rect x="1286" y="55" width="56" height="85" style="fill:#7B92A8"/>',
               '<text x="1333" y="121" style="%s" text-anchor="end">1</text>' % st]
        for y, lab in ((1243, "40"), (896, "50"), (549, "60")):
            out.append('<line x1="55" y1="%d" x2="1342" y2="%d" style="stroke:#FFFFFF;'
                       'stroke-width:3"/>' % (y - 20, y - 20))
            out.append('<text x="1364" y="%d" style="%s">%s</text>' % (y, st, lab))
        out.append('<line x1="55" y1="1263" x2="1342" y2="1263" style="stroke:#000000;'
                   'stroke-width:3"/>')
        for x, lab in ((65, "1900"), (699, "1920"), (1333, "1940")):
            out.append('<line x1="%d" y1="1263" x2="%d" y2="1285" style="stroke:#000000;'
                       'stroke-width:3"/>' % (x, x))
            out.append('<text x="%d" y="1316" style="%s" text-anchor="middle">%s</text>'
                       % (x, st, lab))
        out.append('<text x="699" y="1382" style="%s" text-anchor="middle">Year</text>' % st)
        out.append("</svg>")
        p = tmp_path / "e.svg"
        p.write_text("\n".join(out), encoding="utf-8")
        g = verdict.twoway_geometry(str(p))
        assert g["x_labels"] == ["1900", "1920", "1940"]
        assert "Year" in g["axis_titles"] and "Year" not in g["titles"]


class TestANoteIsNoYLabel:
    # D56 (help-twoway_bar): ylabel(none) leaves no y labels; the note at
    # the bottom left is not one.

    def test_a_note_below_the_region(self, tmp_path):
        st = "font-family:'Helvetica';font-size:89.94px;fill:#000000"
        out = ['<svg version="1.1" viewBox="0 0 5400 3240">',
               '<rect x="0" y="0" width="5400" height="3240" style="fill:#FFFFFF"/>',
               '<rect x="621" y="2629" width="1653" height="140" style="fill:#489DFF"/>']
        for x in (600, 2400, 4200):
            out += ['<line x1="%d" y1="%d" x2="%d" y2="%d" style="stroke:#F0F0F0;'
                    'stroke-width:9.72"/>' % (x, y, x, y + 65) for y in range(310, 2780, 97)]
        out += ['<line x1="%d" y1="2841" x2="%d" y2="2841" style="stroke:#F0F0F0;'
                'stroke-width:9.72"/>' % (x, x + 65) for x in range(252, 4250, 97)]
        out.append('<text x="200" y="3080" style="%s">Source: a note</text>' % st)
        out.append("</svg>")
        p = tmp_path / "n.svg"
        p.write_text("\n".join(out), encoding="utf-8")
        g = verdict.twoway_geometry(str(p))
        assert g["y_labels"] == []
        # The bar (the first solid rect, 1.3% of the canvas) is not the region.
        assert abs(g["frame_aspect"] - (4250 - 252) / (2841 - 310)) < 0.1


class TestTicksWithTextLabels:
    # D56 (row 1): xlabel(0 3.14 "{&pi}" ...) labels ticks with text; only
    # the numeric labels give twoway tick values, so the values cannot be
    # compared -- the number of ticks can.

    def test_count_only(self, tmp_path):
        p = tmp_path / "f.svg"
        p.write_text(_no_region_svg(), encoding="utf-8")
        g = verdict.twoway_geometry(str(p))
        assert g["x_ticks"] == [0.0] and g["x_tick_n"] == 5
        da = dict(g, x_ticks=[0, 3.14, 6.28, 9.42, 12.57])
        assert verdict.compare(g, da, _RULES) == []
        four = dict(g, x_ticks=[0, 3.14, 6.28, 9.42], x_labels=["0", "a", "b", "c"])
        assert [d["check"] for d in verdict.compare(g, four, _RULES)] == ["x_ticks",
                                                                          "x_labels"]

    def test_minor_ticks_are_not_counted(self, tmp_path):
        # help-axis_label_options: xmtick() draws unlabelled tick marks;
        # dash's view lists major ticks only.
        text = _no_region_svg()
        minor = "".join('<line x1="%d" y1="2774" x2="%d" y2="2794" style="stroke:#000000;'
                        'stroke-width:3"/>' % (x, x) for x in (1180, 2330, 3480, 4630))
        p = tmp_path / "m.svg"
        p.write_text(text.replace("</svg>", minor + "</svg>"), encoding="utf-8")
        g = verdict.twoway_geometry(str(p))
        assert g["x_tick_n"] == 5

    def test_same_labels_same_ticks(self):
        # help-twoway_bar: xlabel(-10 "10" -5 "5" ...) shows the same labels
        # as dash; the values twoway's reader parses from them are not the
        # ticks' values.
        tw = _geo(x_ticks=[10.0, 5.0, 5.0, 10.0], x_labels=["10", "5", "5", "10"])
        da = _geo(x_ticks=[-10, -5, 5, 10], x_labels=["10", "5", "5", "10"])
        assert verdict.compare(tw, da, _RULES) == []


class TestTextBoxes:
    # D56 (help-added_text_options): text(..., box bcolor(gs15)) draws a
    # filled box behind added text; it is no glyph, and its fill is no
    # glyph colour (dash draws it as a label background, not a renderer).

    def test_a_box_behind_text_is_no_glyph(self, tmp_path):
        text = open(_SMOKE, encoding="utf-8").read()
        box = ('<rect x="1000.00" y="1000.00" width="800.00" height="300.00" '
               'style="fill:#F0F0F0"/>\n<rect x="1000.00" y="1000.00" width="800.00" '
               'height="300.00" style="fill:none;stroke:#F0F0F0;stroke-width:12.96"/>\n'
               '<text x="1050.00" y="1150.00" style="font-family:'
               '\'Helvetica\';font-size:112.56px;fill:#000000">The 1918 influenza</text>\n')
        p = tmp_path / "box.svg"
        p.write_text(text.replace("</svg>", box + "</svg>"), encoding="utf-8")
        g = verdict.twoway_geometry(str(p))
        assert g["colours"]["set"] == ["#1a85ff", "#d41159"]

    def test_bars_carrying_labels_are_glyphs(self, tmp_path):
        # gpdf-graph_twoway_bar: a pyramid's bars of one colour hold the age
        # labels; they are bars, not boxes.
        bars = "".join('<rect x="2400.00" y="%d.00" width="600.00" height="100.00" '
                       'style="fill:#D41159"/>\n<text x="2410.00" y="%d.00" style="'
                       'font-size:89.94px;fill:#000000">%d to %d</text>\n'
                       % (y, y + 70, k, k + 4) for k, y in ((0, 600), (5, 800), (10, 1000),
                                                            (15, 1200)))
        g = verdict.twoway_geometry(_smoke_plus(tmp_path, bars))
        assert "#d41159" in g["colours"]["set"]

    def test_a_line_over_marker_labels_is_a_glyph(self, tmp_path):
        # help-graph_intro: a fitted line runs over marker labels; it is no box.
        line = ('<path d=" M600.00 2600.00 L2000.00 1500.00 L4200.00 400.00" style="fill:none;'
                'stroke:#00FF00;stroke-width:9.72"/>\n<text x="1500.00" y="1500.00" '
                'style="font-size:89.94px;fill:#1A85FF">Haiti</text>\n')
        g = verdict.twoway_geometry(_smoke_plus(tmp_path, line))
        assert "#00ff00" in g["colours"]["set"]


class TestInsideTicks:
    # D56 (help-tsline): ttick(..., tpos(in)) draws black tick marks inside
    # the region from its bottom edge; they are ticks, not glyphs.

    def test_inside_ticks_are_no_glyph_colour(self, tmp_path):
        t = ('<line x1="3000.00" y1="2726.66" x2="3000.00" y2="2766.66" style="stroke:'
             '#000000;stroke-width:5.76"/>\n')
        g = verdict.twoway_geometry(_smoke_plus(tmp_path, t))
        assert g["colours"]["set"] == ["#1a85ff", "#d41159"]


class TestNumericTitles:
    # D56 (help-graph_display): note("1") draws "1" in both pictures;
    # twoway's reader cannot tell a lone number from an axis label, so
    # neither side reads it as a title.

    def test_a_number_is_no_title(self):
        v = _view()
        v["figures"][0]["titles"].append({"text": "1", "align": "left", "side": "below"})
        assert verdict.dash_geometry(v)["titles"] == ["Smoke  title"]


class TestRaisedText:
    # D56 (gpdf-graph_twoway_pci, help-graph_text): twoway writes
    # {superscript:2} as a raised <tspan>; dash writes "x\u00b2".  The
    # same characters are the same title.

    def test_tspans_are_read_as_their_characters(self, tmp_path):
        text = open(_SMOKE, encoding="utf-8").read()
        sup = ('<text x="2700.00" y="150.00" style="font-family:\'Helvetica\';'
               'font-size:157.44px;fill:#000000" text-anchor="middle">\n\t\t<tspan style='
               '"font-size:157.44px">Characteristics of y = -x</tspan>\n\t\t<tspan '
               'dy="-82.47px" style="font-size:91.79px">2</tspan>\n\t</text>\n')
        p = tmp_path / "sup.svg"
        p.write_text(text.replace("</svg>", sup + "</svg>"), encoding="utf-8")
        g = verdict.twoway_geometry(str(p))
        assert "Characteristics of y = -x2" in g["titles"]
        v = _view()
        v["figures"][0]["titles"].append({"text": "Characteristics of y = -x\u00b2",
                                          "align": "center", "side": "above"})
        assert "Characteristics of y = -x2" in verdict.dash_geometry(v)["titles"]


class TestDrawnPoints:
    # D56 (ex-kelly22ex_categorical): scatter ... if rep78==1 keeps every
    # row in its source and filters it in its view; the markers drawn are
    # the dump's "drawn" count, with their own extents.

    def test_drawn_count_and_extents(self):
        r = _rdr(n=74, x=(142, 233), y=(12, 41))
        r["drawn"] = {"n": 2, "x": [149, 199], "y": [18, 24]}
        g = verdict.dash_geometry(_view([r]))
        assert g["glyphs"] == 2 and g["glyph_counts"] == [2]
        assert g["glyph_extents"] == {"x": [149, 199], "y": [18, 24]}
        r["drawn"] = {"n": 0, "x": None, "y": None}
        assert verdict.dash_geometry(_view([r]))["glyphs"] is None


def _smoke_plus(tmp_path, extra, name="x.svg", replace=()):
    text = open(_SMOKE, encoding="utf-8").read()
    for a, b in replace:
        text = text.replace(a, b)
    p = tmp_path / name
    p.write_text(text.replace("</svg>", extra + "</svg>"), encoding="utf-8")
    return str(p)


_ST = "style=\"font-family:'Helvetica';font-size:112.56px;fill:#000000\""


class TestTitlesOutsideTheTitleArea:
    # D56 (help-graph_intro, gpdf-Graph_intro, audit-RH-13): an x axis drawn
    # above the plot region has its labels and title there -- the title is
    # an axis title, not a title.  help-axis_label_options: a yline's label
    # beside the region is added text, not a title.

    def test_a_top_axis_title(self, tmp_path):
        top = "".join('<text x="%s" y="270.00" %s text-anchor="middle">%s</text>'
                      % (x, _ST, v) for x, v in (("861.47", "0"), ("4204.41", "1")))
        top += '<text x="2399.12" y="200.00" %s text-anchor="middle">Top axis</text>' % _ST
        p = _smoke_plus(tmp_path, top, replace=(('y="243.10"', 'y="60.00"'),))
        assert verdict.twoway_geometry(p)["titles"] == ["Smoke  title"]

    def test_text_beside_the_region(self, tmp_path):
        side = '<text x="4300.00" y="1500.00" %s>12,321 (mean)</text>' % _ST
        assert verdict.twoway_geometry(_smoke_plus(tmp_path, side))["titles"] == [
            "Smoke  title"]


class TestLabelsOfTheOtherAxis:
    # D56 (help-region_options): the y axis's 0 label sits just below the
    # plot region's bottom edge; it is the y axis's, not the x axis's.

    def test_y_labels_are_not_x_labels(self, tmp_path):
        lab = ('<line x1="522.79" y1="2766.66" x2="477.73" y2="2766.66" style="stroke:'
               '#000000;stroke-width:6.48"/><text x="455.29" y="2806.00" %s '
               'text-anchor="end">0</text>' % _ST)
        g = verdict.twoway_geometry(_smoke_plus(tmp_path, lab))
        assert g["x_labels"] == ["2,000", "3,000", "4,000", "5,000"]
        assert g["y_labels"][0] == "0"


class TestMarkerReading:

    def test_big_circles_are_markers(self, tmp_path):
        # gpdf-graph_twoway_scatter [aw=pop]: weighted markers grow past the
        # small-group bound; a circle is still a marker.
        big = ('<circle cx="2000.00" cy="1000.00" r="200.00" style="fill:none;'
               'stroke:#1A85FF;stroke-width:9.72"/>\n')
        g = verdict.twoway_geometry(_smoke_plus(tmp_path, big))
        assert g["glyphs"] == 75

    def test_two_collinear_lines_are_no_plus(self, tmp_path):
        # ex-plot_types_tour contourline: two short contour segments about
        # one centre are not a plus marker; a plus's two lines cross.
        seg = ('<line x1="2000.00" y1="1000.00" x2="2010.00" y2="1002.00" style="stroke:'
               '#000000;stroke-width:4"/>\n<line x1="2010.00" y1="1002.00" x2="2000.00" '
               'y2="1000.00" style="stroke:#000000;stroke-width:4"/>\n')
        g = verdict.twoway_geometry(_smoke_plus(tmp_path, seg))
        assert g["glyphs"] == 74 and g["marker_shape"] == ["circle"]
        plus = ('<line x1="1990.00" y1="1000.00" x2="2010.00" y2="1000.00" style="stroke:'
                '#000000;stroke-width:4"/>\n<line x1="2000.00" y1="990.00" x2="2000.00" '
                'y2="1010.00" style="stroke:#000000;stroke-width:4"/>\n')
        g = verdict.twoway_geometry(_smoke_plus(tmp_path, plus, "p.svg"))
        assert g["marker_shape"] == ["circle", "plus"]

    def test_a_big_x_is_a_marker(self, tmp_path):
        # gpdf-graph_twoway_pci: msize(huge) x markers.
        x = ('<line x1="1800.00" y1="800.00" x2="2200.00" y2="1200.00" style="stroke:'
             '#D41159;stroke-width:9"/>\n<line x1="1800.00" y1="1200.00" x2="2200.00" '
             'y2="800.00" style="stroke:#D41159;stroke-width:9"/>\n')
        g = verdict.twoway_geometry(_smoke_plus(tmp_path, x))
        assert g["glyphs"] == 75 and "x" in g["marker_shape"]

    def test_an_invisible_scatter_is_no_marker(self):
        # contourline: dash's hover points are a Scatter drawn with alpha 0.
        g = verdict.dash_geometry(_view([_rdr(n=2, fill_alpha={"value": 0},
                                              line_alpha={"value": 0})]))
        assert g["glyphs"] is None and g["marker_shape"] == []


class TestTexts:
    # D56 (audit-MS-5): mlabel() with format(%9.2f) labels the markers
    # 22.00 in twoway and 22 in dash: different text, a fundamental
    # difference no label, title or legend check sees.

    def test_text_drawn_on_one_side_only(self):
        tw = _geo(drawn=["0", "10", "x", "y", "22.00", "17.00"])
        da = _geo(drawn=["0", "10", "x", "y", "22", "17"])
        d = verdict.compare(tw, da, _RULES)
        assert d == [{"check": "texts", "twoway": ["17.00", "22.00"], "dash": ["17", "22"],
                      "within_tol": False}]
        assert verdict.summary(d) == "text"
        # The axis labels are the label checks' own.
        tw = _geo(drawn=["0", "10", "x", "y"])
        da = _geo(x_labels=["0", "10", "20"], drawn=["0", "10", "20", "x", "y"])
        assert [x["check"] for x in verdict.compare(tw, da, _RULES)] == ["x_labels"]
        # help-twoway_histogram: a label in the x labels' row the tick reader
        # did not pair is an axis label too.
        tw = _geo(drawn=["0", "10", "50", "x", "y"], axis_texts=["50"])
        assert verdict.compare(tw, _geo(drawn=["0", "10", "x", "y"]), _RULES) == []


class TestColoursAndLegendsByWhatIsDrawn:

    def test_colours_dash_maps_from_data(self):
        # ex-comprehensive_demo colorvar(): dash colours the markers from a
        # column, which the view does not read; twoway's colours for them
        # have no counterpart to judge against.
        tw = _geo(colours={"set": ["#0000ff", "#00ff00", "#1a85ff"], "unread": 0})
        da = _geo(colours={"set": ["#1a85ff"], "unread": 2})
        assert verdict.compare(tw, da, _RULES) == []
        da = _geo(colours={"set": ["#1a85ff", "#ff0000"], "unread": 2})
        assert [d["check"] for d in verdict.compare(tw, da, _RULES)] == ["colours"]

    def test_legend_text_drawn_elsewhere(self):
        # help-clegend_option: twoway's contour legend labels Low, Medium,
        # High; dash draws them on a colour bar, which is no Legend model.
        tw = _geo(legend=["Low", "Medium", "High"], drawn=["Low", "Medium", "High", "Depth"])
        da = _geo(legend=[], drawn=["Low", "Medium", "High", "Depth"])
        assert verdict.compare(tw, da, _RULES) == []
        da = _geo(legend=[], drawn=["Low", "High", "Depth"])
        assert [d["check"] for d in verdict.compare(tw, da, _RULES)] == ["legend"]


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

    def test_line_widths_under_half_a_pixel(self):
        # D56 (row 1): 1.3 px against 1.15 px on a 720-px picture is no
        # visible difference; 1.3 px against 2.6 px is.
        tw = _geo(line_widths=[0.0018])
        rules = dict(_RULES, line_abs=0.0007)
        assert verdict.compare(tw, _geo(line_widths=[0.0016]), rules) == []
        assert [d["check"] for d in verdict.compare(tw, _geo(line_widths=[0.0036]),
                                                     rules)] == ["line_width"]

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
        # Flipped: ticks under the same labels are not compared (D56), so
        # the moved tick is labelled 0.1.
        off = _geo(x_ticks=[0.1, 10.0], frame_aspect=1.6, x_labels=["0.1", "10"])
        assert {d["check"] for d in verdict.compare(tw, off, _RULES)} == {
            "x_ticks", "x_labels", "frame_aspect"}
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
        # Flipped: a colours difference also says whether it is slight (D56).
        assert d == [{"check": "colours", "twoway": ["#1a85ff"], "dash": ["#ff0000"],
                      "within_tol": False, "slight": False}]
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


class TestTiers:
    # D56: text size, margins, marker size and line width, a plot region
    # shape within aspect_close and colours of one hue family within
    # colour_slight can make a pair Close, never Differs.

    _T = dict(_RULES, aspect_close=0.12,
              colour_slight={"hue_deg": 30, "light": 0.2, "grey_sat": 0.15},
              close_only=["text_size", "margins", "marker_size", "line_width"])

    def test_close_only_checks(self):
        for c in ("text_size", "margins", "marker_size", "line_width"):
            d = [{"check": c, "twoway": 1, "dash": 2, "within_tol": False, "gaps4": None}]
            assert verdict.verdict(0, 0, None, None, d, None, self._T) == "Close", c
        d = [{"check": "x_labels", "twoway": ["1"], "dash": ["2"], "within_tol": False,
              "gaps4": None}]
        assert verdict.verdict(0, 0, None, None, d, None, self._T) == "Differs"

    def test_a_large_size_difference_differs(self):
        # help-scatter scheme(economist): dash's text and markers are three
        # times twoway's -- no slight difference.
        rules = dict(self._T, size_close=0.35)
        for c, a, b in (("text_size", 0.02, 0.0695), ("marker_size", [0.008], [0.025])):
            d = [{"check": c, "twoway": a, "dash": b, "within_tol": False, "gaps4": None}]
            assert verdict.verdict(0, 0, None, None, d, None, rules) == "Differs", c
        d = [{"check": "text_size", "twoway": 0.0208, "dash": 0.0185, "within_tol": False,
              "gaps4": "VF-4"}]
        assert verdict.verdict(0, 0, None, None, d, None, rules) == "Close"
        # VF-4 explains 0.889x, not three times.
        d = [dict(d[0], dash=0.0695)]
        assert verdict.verdict(0, 0, None, None, d, None, rules) == "Differs"

    def test_fundamental(self):
        f = verdict.fundamental
        assert not f({"check": "margins", "twoway": [0.1], "dash": [0.2]}, self._T)
        assert f({"check": "legend", "twoway": ["a"], "dash": []}, self._T)
        assert not f({"check": "colours", "twoway": ["#1a85ff"], "dash": ["#3a8fff"],
                      "slight": True}, self._T)
        assert f({"check": "frame_aspect", "twoway": 1.5, "dash": 2.2}, self._T)

    def test_plot_region_shape(self):
        def v(a, b):
            d = [{"check": "frame_aspect", "twoway": a, "dash": b, "within_tol": False,
                  "gaps4": None}]
            return verdict.verdict(0, 0, None, None, d, None, self._T)
        assert v(1.5, 1.6) == "Close"
        assert v(1.5, 2.2) == "Differs"

    def test_slight_colours(self):
        assert verdict.slight_colour("#1a85ff", "#3a8fff", self._T["colour_slight"])
        assert verdict.slight_colour("#1a85ff", "#1a85ffb3", self._T["colour_slight"])
        assert not verdict.slight_colour("#1a85ff", "#ff0000", self._T["colour_slight"])
        assert not verdict.slight_colour("#1a85ff", "#000000", self._T["colour_slight"])
        assert verdict.slight_colour("#808080", "#8c8c8c", self._T["colour_slight"])
        tw = _geo(colours={"set": ["#1a85ff", "#d41159"], "unread": 0})
        da = _geo(colours={"set": ["#3a8fff", "#d41159"], "unread": 0})
        d = verdict.explain(verdict.compare(tw, da, self._T), {}, [], {})
        assert [x["check"] for x in d] == ["colours"]
        assert verdict.verdict(0, 0, None, None, d, None, self._T) == "Close"
        red = _geo(colours={"set": ["#ff0000", "#d41159"], "unread": 0})
        d = verdict.explain(verdict.compare(tw, red, self._T), {}, [], {})
        assert verdict.verdict(0, 0, None, None, d, None, self._T) == "Differs"

    def test_the_summary_leads_with_what_differs(self):
        d = [{"check": "text_size"}, {"check": "margins"}, {"check": "legend"}]
        assert verdict.summary(d, self._T) == "legend keys, text size, margins"


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

    def test_an_example_twoway_refuses_is_not_judged(self, tmp_path, monkeypatch):
        # D52: no verdict row and no count for an example twoway refuses.
        ex, tw, da = self._run(tmp_path)
        ex2 = dict(ex, id="e2", cmd="twoway scatter mpg weight, nosuch")
        tw2 = dict(tw, id="e2", rc=198, first_line="option nosuch not allowed", svg=None)
        da2 = dict(da, id="e2", rc=198, svg=None, view=None)
        for name, rows in (("examples", [ex, ex2]), ("twoway", [tw, tw2]),
                           ("dash", [da, da2])):
            (tmp_path / (name + ".jsonl")).write_text(
                "".join(json.dumps(r) + "\n" for r in rows))
        rules = tmp_path / "rules.json"
        rules.write_text(json.dumps(_RULES))
        led = tmp_path / "ledger.json"
        led.write_text(json.dumps({"_meta": {}, "rows": []}))
        monkeypatch.setattr(verdict, "_open_probe", lambda run_dir: _StubProbe(48, 24))
        c = verdict.run(str(tmp_path), str(rules), str(led))
        assert sum(c.values()) == 1
        rows = [json.loads(x) for x in (tmp_path / "verdicts.jsonl").read_text().splitlines()]
        assert [r["id"] for r in rows] == ["e1"]


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
