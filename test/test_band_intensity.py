"""A pstyle(p#) CI band's scheme intensity and colour (WP-31 E7).

Measured in StataNow 19.5 (`graph export' SVG, 16oct2026;
test/fixtures/colour_width_edges_truth.json ci.*,
scripts/extract_colour_width_edges_truth.do): `lfitci ..., pstyle(p1)'
and `astyle(p1)' draw the band in shadestyle p#'s chain, `color' and
`intensity' p#shade -> pshade -> p# -> p (style/shadestyle-p#.style),
not p#bar's or p#other's: `intensity p1bar inten200' leaves it at
s2color's inten80 (#486c8c), `intensity p1shade inten200' draws navy at
twice full (#0d2438), `intensity pshade inten50' at half (#8da3b7), and
`color p1shade red' red (#ff3333) where `color p1other red' changes
nothing.  dash read `intensity p1bar' clamped to full (navy) and
`color p1other'.
"""
import json
import os
import sys

import pytest
from bokeh.models import GlyphRenderer

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_scheme_resolution import MODES, _draw, _props_scheme  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

with open(os.path.join(_HERE, "fixtures", "colour_width_edges_truth.json"),
          encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)

#: probe key -> the scheme lines it adds to s2color.
SCHEMES = {
    "ci.base": [],
    "ci.inten200": ["intensity p1bar inten200"],
    "ci.p1shade_inten200": ["intensity p1shade inten200"],
    "ci.pshade_inten50": ["intensity pshade inten50"],
    "ci.p1_inten50_p1shade_inten200": ["intensity p1 inten50",
                                       "intensity p1shade inten200"],
    "ci.p_inten200": ["intensity p inten200"],
    "ci.color_p1shade": ["color p1shade red"],
    "ci.color_p1other": ["color p1other red"],
}


def _twoway_fill(key):
    """The band's fill: the <use> twoway fills (the polygon)."""
    return [e[1] for e in TRUTH[key]["elements"]
            if e[0] == "use" and e[1] not in ("", "none")][0]


def _props(lines):
    props = dict(dr.SchemeParser("s2color")._props)
    for ln in lines:
        k1, k2, v = ln.split(None, 2)
        props[f"{k1} {k2}"] = v
    return props


def _band_fill(mode, tmp_path, monkeypatch, lines):
    (tmp_path / "u41b.scheme").write_text(
        "#include s2color\n" + "".join(ln + "\n" for ln in lines),
        encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    d = _draw(tp._spec([plot_for("lfitci", {"pstyle": "p1"})],
                       {"scheme": "u41b"}), mode)
    gs = [r.glyph for r in d.figures[0].renderers
          if isinstance(r, GlyphRenderer) and not dr._dash_is_swatch(r)
          and type(r.glyph).__name__ in ("VArea", "Patch", "HArea")]
    assert gs, [type(r.glyph).__name__ for r in d.figures[0].renderers]
    return str(gs[0].fill_color).lower()


class TestBandIntensity:
    def test_above_full_kept(self):
        s = _props_scheme(_props(SCHEMES["ci.p1shade_inten200"]))
        assert s.p_other_band_styles[0]["intensity"] == pytest.approx(2.0)

    def test_the_chain_is_shadestyle_pnums(self):
        want = {"ci.base": 0.8, "ci.inten200": 0.8,
                "ci.pshade_inten50": 0.5,
                "ci.p1_inten50_p1shade_inten200": 2.0,
                "ci.p_inten200": 2.0}
        for key, f in want.items():
            s = _props_scheme(_props(SCHEMES[key]))
            assert s.p_other_band_styles[0]["intensity"] == \
                pytest.approx(f), key

    @pytest.mark.parametrize("mode", MODES)
    def test_fill_matches_twoway(self, mode, tmp_path, monkeypatch):
        bad = []
        for key, lines in SCHEMES.items():
            got = _band_fill(mode, tmp_path, monkeypatch, lines)
            if got != _twoway_fill(key):
                bad.append((key, got, _twoway_fill(key)))
        assert not bad, bad
