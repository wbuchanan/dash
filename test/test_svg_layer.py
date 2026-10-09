"""scripts/svg_layer.py reads every drawn element of a Stata SVG
(WP-30 P1.4a).  The elements are Stata 19.5's own, copied from `graph
export' files (03oct2026)."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import svg_layer as sl  # noqa: E402

_HEAD = ('<svg version="1.1" viewBox="0 0 3960 2880" '
         'xmlns="http://www.w3.org/2000/svg" '
         'xmlns:xlink="http://www.w3.org/1999/xlink">\n'
         '<rect x="0" y="0" width="3960" height="2880" '
         'style="fill:#FFFFFF;stroke:none"/>\n')

#: shape -> the elements Stata writes for one marker of it.
_MARKERS = {
    "circle": '<circle cx="345.63" cy="164.22" r="19.08" '
              'style="fill:#1A476F;fill-opacity:0.20"/>'
              '<circle cx="345.63" cy="164.22" r="15.03" '
              'style="fill:none;stroke:#1A476F;stroke-opacity:0.20;'
              'stroke-width:8.10"/>',
    "square": '<rect x="319.29" y="137.87" width="52.69" height="52.70" '
              'style="fill:#606060"/><rect x="323.61" y="142.19" '
              'width="44.05" height="44.06" style="fill:none;'
              'stroke:#606060;stroke-width:8.64"/>',
    "diamond": '<polygon points="314.45,164.22 345.63,133.04 376.82,164.22 '
               '345.63,195.41" style="fill:none;stroke:#606060;'
               'stroke-width:8.64"/>',
    "triangle": '<polygon points="345.63,126.25 312.75,183.21 378.52,183.21"'
                ' style="fill:#606060"/><polygon points="345.63,134.89 '
                '320.23,178.89 371.03,178.89" style="fill:none;'
                'stroke:#606060;stroke-width:8.64"/>',
    "x": '<line x1="334.61" y1="175.25" x2="356.66" y2="153.20" '
         'style="fill:none;stroke:#606060;stroke-width:8.64"/>'
         '<line x1="356.66" y1="175.25" x2="334.61" y2="153.20" '
         'style="fill:none;stroke:#606060;stroke-width:8.64"/>',
    "plus": '<line x1="323.61" y1="164.22" x2="367.66" y2="164.22" '
            'style="fill:none;stroke:#606060;stroke-width:8.64"/>'
            '<line x1="345.63" y1="186.25" x2="345.63" y2="142.19" '
            'style="fill:none;stroke:#606060;stroke-width:8.64"/>',
    "v": '<path d="M326.56 142.19 L345.63 175.24 L364.71 142.19" '
         'style="fill:none;stroke:#606060;stroke-width:8.64"/>',
}


def _svg(tmp_path, body, name="g.svg"):
    p = tmp_path / name
    p.write_text(_HEAD + body + "\n</svg>\n", encoding="utf-8")
    return str(p)


class TestSvgElements:
    def test_each_kind(self, tmp_path):
        body = (_MARKERS["circle"] + _MARKERS["diamond"] + _MARKERS["x"]
                + '<defs><path id="path_a" d="M10 10 L50 10 L50 90"/></defs>'
                '<use xlink:href="#path_a" style="stroke:none;'
                'fill:#486C8C;fill-opacity:0.20"/>')
        els = sl.svg_elements(_svg(tmp_path, body))
        assert [e["kind"] for e in els] == \
            ["circle", "circle", "polygon", "line", "line", "path"]
        c = els[0]
        assert (c["fill"], c["fill_opacity"], c["stroke"],
                c["extent"]) == ("#1a476f", 0.2, None, pytest.approx(38.16))
        assert (els[1]["stroke"], els[1]["stroke_opacity"],
                els[1]["stroke_width"]) == ("#1a476f", 0.2, 8.1)
        assert els[2]["extent"] == pytest.approx(62.37)
        assert (els[5]["fill"], els[5]["fill_opacity"],
                els[5]["extent"]) == ("#486c8c", 0.2, 80.0)


class TestMarkerShape:
    def test_each_shape(self, tmp_path):
        got = {}
        for shape, body in _MARKERS.items():
            ms = sl.markers(sl.svg_elements(_svg(tmp_path, body, shape)))
            assert len(ms) == 1, shape
            got[shape] = sl.marker_shape(ms[0])
        assert got == {s: s for s in _MARKERS}
        lone = sl.svg_elements(_svg(tmp_path, _MARKERS["x"][:120] + "/>",
                                    "lone"))
        assert sl.marker_shape(lone[:1]) is None


class TestHollow:
    def test_stroke_only(self, tmp_path):
        tri = sl.markers(sl.svg_elements(_svg(tmp_path,
                                              _MARKERS["triangle"])))[0]
        dia = sl.markers(sl.svg_elements(_svg(tmp_path, _MARKERS["diamond"],
                                              "d")))[0]
        assert (sl.hollow(tri), sl.hollow(dia)) == (False, True)
        # The stroked outline's extent, not the fill's.
        assert sl.stroke_extent(tri) == pytest.approx(50.8)
