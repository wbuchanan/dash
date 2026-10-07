"""scripts/svg_chrome.py on synthetic twoway-shaped SVG (WP-30 P1.2a).

Each case writes a minimal SVG modelled on twoway's export (the sentinel
``<rect ... style="fill:none;stroke:#010203;stroke-width:W"/>``, ``<line>``
ticks, ``<text ... text-anchor=...>``), so no Stata is needed.
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import svg_chrome as sc  # noqa: E402

_HEAD = '<svg viewBox="0 0 1000 800" xmlns="http://www.w3.org/2000/svg">\n'
# The region: 100..900 x 100..700 once grown by half the stroke (W=4).
_SENT = ('<rect x="102" y="102" width="796" height="596" '
         'style="fill:none;stroke:#010203;stroke-width:4"/>\n')


def _svg(tmp_path, body, name="g.svg"):
    p = tmp_path / name
    p.write_text(_HEAD + _SENT + body + "</svg>\n", encoding="utf-8")
    return str(p)


def _line(x1, y1, x2, y2, stroke="#000000", w=1.6):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'style="stroke:{stroke};stroke-width:{w}"/>\n')


class TestTheRegion:

    def test_the_sentinel_rect_grown_by_half_its_stroke(self, tmp_path):
        r = sc.svg_region(_svg(tmp_path, ""))
        assert (r["left"], r["top"], r["right"], r["bottom"]) == (
            100, 100, 900, 700)
        assert r["rs"] == 8.0

    def test_no_sentinel_is_none(self, tmp_path):
        p = tmp_path / "n.svg"
        p.write_text(_HEAD + "</svg>")
        assert sc.svg_region(str(p)) is None


class TestTextPlace:

    def test_anchor_and_side_and_weight(self, tmp_path):
        p = _svg(tmp_path,
                 '<text x="500" y="50" text-anchor="middle">TTL</text>\n'
                 '<text x="100" y="750">NTE</text>\n'
                 '<text x="900" y="760" text-anchor="end" '
                 'style="font-weight:bold;font-style:italic">CAP</text>\n')
        r = sc.svg_region(p)
        assert sc.svg_text_place(p, "TTL", r) == {
            "side": "above", "align": "center", "weight": "normal",
            "style": "normal"}
        assert sc.svg_text_place(p, "NTE", r)["align"] == "left"
        c = sc.svg_text_place(p, "CAP", r)
        assert (c["side"], c["align"], c["weight"], c["style"]) == (
            "below", "right", "bold", "italic")


class TestTicks:

    def test_outside_inside_crossing_and_length_in_rs(self, tmp_path):
        out = "".join(_line(x, 700, x, 711.1) for x in (200, 400, 600))
        inside = "".join(_line(100, y, 111.1, y) for y in (200, 400, 600))
        cross = "".join(_line(x, 94.45, x, 105.55) for x in (200, 400, 600))
        p = _svg(tmp_path, out + inside + cross)
        r = sc.svg_region(p)
        b = sc.svg_ticks(p, "bottom", r)
        assert (b["n"], b["position"], b["length_rs"], b["color"]) == (
            3, "outside", 1.388, "#000000")
        assert b["width_rs"] == 0.2
        assert sc.svg_ticks(p, "left", r)["position"] == "inside"
        assert sc.svg_ticks(p, "top", r)["position"] == "crossing"
        assert sc.svg_ticks(p, "right", r)["n"] == 0

    def test_a_dashed_gridline_is_not_a_tick(self, tmp_path):
        dashes = "".join(_line(100 + 16 * i, 300, 108 + 16 * i, 300,
                               "#f0f0f0") for i in range(50))
        p = _svg(tmp_path, dashes)
        r = sc.svg_region(p)
        assert sc.svg_ticks(p, "left", r)["n"] == 0


class TestAxisLine:

    def test_present_and_absent(self, tmp_path):
        p = _svg(tmp_path, _line(100, 700, 900, 700))
        r = sc.svg_region(p)
        assert sc.svg_axis_line(p, "bottom", r) is True
        assert sc.svg_axis_line(p, "left", r) is False


class TestGrid:

    def test_solid_and_dashed(self, tmp_path):
        solid = _line(100, 300, 900, 300, "#eaf2f3")
        dashed = "".join(_line(300, 100 + 16 * i, 300, 108 + 16 * i,
                               "#f0f0f0") for i in range(37))
        p = _svg(tmp_path, solid + dashed)
        r = sc.svg_region(p)
        assert sc.svg_grid(p, "y", r) == {"drawn": True, "dashed": False,
                                          "color": "#eaf2f3"}
        assert sc.svg_grid(p, "x", r)["dashed"] is True


class TestLabels:

    def test_rotation_and_side(self, tmp_path):
        p = _svg(tmp_path,
                 '<text x="80" y="300" transform="rotate(-90 80,300)" '
                 'text-anchor="middle">10</text>\n'
                 '<text x="80" y="500" transform="rotate(-90 80,500)" '
                 'text-anchor="middle">20</text>\n'
                 '<text x="950" y="400" text-anchor="start">5000</text>\n'
                 '<text x="300" y="730" text-anchor="middle">2000</text>\n')
        r = sc.svg_region(p)
        assert sc.svg_label_rotation(p, "y", r, "left") == 90
        assert sc.svg_label_rotation(p, "y", r, "right") == 0
        assert sc.svg_label_rotation(p, "x", r) == 0
        assert sc.svg_label_side(p, "y", r) == ["left", "right"]


class TestHostileSvg:

    def test_a_megabyte_of_angle_brackets_reads_in_under_a_second(
            self, tmp_path):
        p = _svg(tmp_path, "<" * 1_000_000 + '<text x="1" ' * 1000)
        t = time.perf_counter()
        r = sc.svg_region(p)
        sc.svg_text_place(p, "TTL", r)
        assert time.perf_counter() - t < 1.0
