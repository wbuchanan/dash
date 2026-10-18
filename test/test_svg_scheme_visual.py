"""scripts/svg_scheme_visual.py on synthetic twoway-shaped SVG (WP-32, K3).

Each case is a minimal SVG laid out as Stata's writer lays one out
(the canvas, the graph region's fill and outline, the plot region, the
plots, then the texts), so no Stata is needed.  The reader's run over
Stata's own renders is test/test_scheme_visual_truth.py's record.
"""

import math
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import svg_scheme_visual as sv  # noqa: E402

_HEAD = ('<svg version="1.1" width="5.500in" height="4.000in" '
         'viewBox="0 0 3960 2880">\n'
         '<rect x="0" y="0" width="3960" height="2880" '
         'style="fill:#EAF2F3;stroke:none"/>\n'
         '<rect x="0" y="0" width="3960" height="2880" style="fill:#EAF2F3"/>\n'
         '<rect x="2" y="2" width="3956" height="2876" '
         'style="fill:none;stroke:#EAF2F3;stroke-width:5.76"/>\n')
_PLOT = ('<rect x="400" y="400" width="3400" height="1600" style="fill:#FFFFFF"/>\n'
         '<rect x="403" y="403" width="3394" height="1594" '
         'style="fill:none;stroke:#000000;stroke-width:5.76"/>\n')


def _text(label, x=100, y=100, size=99.99, fill="#000000"):
    return (f'<text x="{x}" y="{y}" style="font-family:\'Helvetica\';'
            f'font-size:{size}px;fill:{fill}">{label}</text>\n')


def _circle(cx, cy, colour="#1A476F", r=26.35, w=8.64):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" style="fill:{colour}"/>\n'
            f'<circle cx="{cx}" cy="{cy}" r="{r - w / 2}" '
            f'style="fill:none;stroke:{colour};stroke-width:{w}"/>\n')


def _diamond(cx, cy, half, colour="#A0A0A0", w=8.64):
    pts = f"{cx},{cy - half} {cx + half},{cy} {cx},{cy + half} {cx - half},{cy}"
    return (f'<polygon points="{pts}" style="fill:{colour}"/>\n'
            f'<polygon points="{pts}" style="fill:none;stroke:{colour};'
            f'stroke-width:{w}"/>\n')


def _els(body, tail=""):
    return sv.elements(_HEAD + _PLOT + body + tail + "</svg>\n")


class TestTheDocument:

    def test_elements_are_read_in_order_with_their_styles(self):
        els = sv.elements(_HEAD + '<circle cx="1" cy="2" r="3" style="fill:#AB'
                          'CDEF;fill-opacity:0.20"/>' + _text("A B"))
        assert [e["kind"] for e in els] == ["rect"] * 3 + ["circle", "text"]
        c, t = els[3], els[4]
        assert (c["fill"], c["fill_opacity"], c["stroke_opacity"]) == (
            "#abcdef", 0.2, 1.0)
        assert (t["text"], t["size"], t["fill"]) == ("A B", 99.99, "#000000")

    def test_the_graph_size_and_viewbox(self):
        assert sv.graph_size(_HEAD) == ([5.5, 4.0], [3960.0, 2880.0])
        with pytest.raises(ValueError):
            sv.graph_size("<svg/>")


class TestTheRegions:

    def test_the_plot_region_follows_the_graph_region(self):
        r = sv.regions(_els(_circle(500, 500)))
        assert r["graph_region_background"] == "#eaf2f3"
        assert r["plot_region_background_effective"] == "#ffffff"
        assert r["plot_region_border"] == {
            "color": "#000000", "width_units": 5.76, "visible": True}

    def test_no_plot_region_shows_the_graph_region(self):
        els = sv.elements(_HEAD + _circle(500, 500) + "</svg>")
        r = sv.regions(els)
        assert r["plot_region_background_effective"] == "#eaf2f3"
        assert r["plot_region_border"]["visible"] is False

    def test_a_box_behind_a_text_and_a_transparent_outline(self):
        box = ('<rect x="50" y="50" width="200" height="100" style="fill:#FFFFFF"/>\n'
               '<rect x="52" y="52" width="196" height="96" style="fill:none;'
               'stroke:#000000;stroke-opacity:0.00;stroke-width:5"/>\n')
        lg = sv.text_box(_els(box, _text("LK1")), "LK1", "#eaf2f3")
        assert lg == {"has_background": True, "background": "#ffffff",
                      "has_border": True, "border_color": "#000000",
                      "border_visible": False}
        none = sv.text_box(_els("", _text("LK1")), "LK1", "#eaf2f3")
        assert (none["has_background"], none["has_border"]) == (False, False)

    def test_the_fonts_are_read_by_their_text(self):
        tail = "".join(_text(t, size=s) for t, s in (
            ("TTL", 139.96), ("SUB", 110.01), ("XTL", 99.99), ("LK1", 99.99),
            ("NTE", 79.94), ("2,000", 99.99)))
        f = sv.fonts(_els("", tail), 2880.0)
        assert f["title"]["pct_of_height"] == pytest.approx(4.8597, abs=1e-4)
        assert f["note"]["units"] == 79.94
        assert f["tick_label"]["units"] == 99.99


class TestTheSeries:

    def test_three_bands_of_markers(self):
        body = "".join(_circle(500 + 100 * k, 1900 - 600 * b, colour=c)
                       for k in range(20)
                       for b, c in enumerate(("#111111", "#222222", "#333333")))
        legend = _circle(500, 2500, "#111111")
        m = sv.markers(_els(body, _text("LK1") + legend), 2880.0)
        assert [m[p]["color"] for p in ("p1", "p2", "p3")] == [
            "#111111", "#222222", "#333333"]
        p1 = m["p1"]
        assert (p1["symbol"], p1["solid"], p1["n_drawn"]) == ("circle", True, 20)
        # The centre line of the outline: 2 * (26.35 - 4.32).
        assert p1["nominal_size_units"] == pytest.approx(44.06)

    def test_a_diamond_is_named_and_sized_by_its_side(self):
        body = "".join(_diamond(500 + 100 * k, 1900 - 600 * b, 31.18)
                       for k in range(20) for b in range(3))
        m = sv.markers(_els(body), 2880.0)
        assert m["p2"]["symbol"] == "diamond"
        assert m["p2"]["nominal_size_units"] == pytest.approx(
            2 * 31.18 / math.sqrt(2), abs=0.01)

    def test_solid_and_dashed_lines(self):
        solid = ('<path d=" M500 1900 L600 1850 L700 1900" '
                 'style="fill:none;stroke:#1A476F;stroke-width:8.64"/>\n')
        dashed = "".join(
            f'<line x1="{500 + 50 * k}" y1="{1300 + 10 * k}" x2="{520 + 50 * k}" '
            f'y2="{1305 + 10 * k}" style="stroke:#000000;stroke-width:8.64"/>\n'
            for k in range(5))
        third = solid.replace("1900", "700").replace("1850", "650")
        grid = ('<line x1="400" y1="1000" x2="3800" y2="1000" '
                'style="stroke:#EAF2F3;stroke-width:8.64"/>\n')
        ln = sv.lines(_els(grid + solid + dashed + third), 2880.0)
        assert [ln[p]["pattern"] for p in ("p1", "p2", "p3")] == [
            "solid", "dashed", "solid"]
        assert ln["p2"]["color"] == "#000000"
        assert ln["p1"]["width_pct_of_height"] == pytest.approx(0.3)

    def test_the_histogram_bars(self):
        bars = "".join(
            f'<rect x="{500 + 400 * k}" y="{1000 + 100 * k}" width="400" '
            f'height="{1000 - 100 * k}" style="fill:#CAC27E"/>\n'
            f'<rect x="{504 + 400 * k}" y="{1004 + 100 * k}" width="392" '
            f'height="{992 - 100 * k}" style="fill:none;stroke:#D7D29E;'
            f'stroke-width:8.64"/>\n' for k in range(4))
        h = sv.histogram(_els(bars), 2880.0)
        assert h == {"n_bars": 4, "fill": "#cac27e", "fill_opacity": 1.0,
                     "outline_color": "#d7d29e", "outline_width_units": 8.64,
                     "outline_width_pct_of_height": 0.3}


class TestTheLadder:

    def test_a_size_is_named_within_one_percent(self):
        ladder = {"small": 1.0396, "medium": 1.5299}
        assert sv.symbol_name(1.5300, ladder) == "medium"
        assert sv.symbol_name(2.2009, ladder) is None

    def test_bands_split_at_the_widest_gaps(self):
        got = sv._bands([1, 2, 10, 11, 20], key=lambda v: v)
        assert got == [[20], [11, 10], [2, 1]]
        with pytest.raises(ValueError):
            sv._bands([1, 2], key=lambda v: v)
