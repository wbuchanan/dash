"""A scheme's #-pt gsizes at the scheme's own size reference (WP-31
section 44, E11b).

twoway draws ``gsize heading 12-pt`` as 12 points on the graph whatever
its size (scripts/extract_scheme_ref_gsize_truth.do: the title's SVG
font-size is 120 of 720 units an inch under a 3.12 x 2.392 in scheme and
a 5.5 x 4 in one).  dash's 4-inch units hold that as 12 * 4 / ref points,
ref the smaller graphsize side; ``SchemeParser._init_properties`` read the
gsizes before it set ``size_ref_in`` from the scheme's graphsize, so they
converted at 4 in.
"""

from __future__ import annotations

import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
import test_scheme_resolution as tsr  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

with open(os.path.join(_HERE, "fixtures", "scheme_ref_gsize_truth.json"),
          encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)


def _scheme(tmp_path, name):
    d = tmp_path / "ado"
    d.mkdir(exist_ok=True)
    (d / f"scheme-{name}.scheme").write_text(
        "\n".join(TRUTH[name]["lines"]) + "\n", encoding="utf-8")
    return str(d)


def _want(name):
    rec = TRUTH[name]
    pt = rec["title_font_units"] / (rec["viewbox"][1] / rec["height_in"]) \
        * 72.0
    ref = min(rec["width_in"], rec["height_in"])
    return round(pt * 4.0 / ref, 1)


class TestTheFixture:
    def test_meta_and_points(self):
        assert sorted(TRUTH["_meta"]) == ["born_date", "dash_commit",
                                          "extracted", "source",
                                          "stata_version"]
        for s in ("u11a", "u11b"):
            rec = TRUTH[s]
            pt = rec["title_font_units"] / (rec["viewbox"][1]
                                            / rec["height_in"]) * 72.0
            assert pt == pytest.approx(12.0, abs=0.02), s


class TestHeadingAtTheSchemesReference:
    @pytest.mark.parametrize("name", ["u11a", "u11b"])
    def test_heading_font_size(self, name, tmp_path):
        sp = dr.SchemeParser(name, ado_dirs=(_scheme(tmp_path, name),))
        got = float(sp.heading_font_size.rstrip("pt"))
        assert round(got, 1) == _want(name)

    @pytest.mark.parametrize("mode", tsr.MODES)
    def test_drawn_in_both_modes(self, mode, tmp_path):
        d = _scheme(tmp_path, "u11a")
        spec = tp._spec([plot_for("scatter")],
                        {"scheme": "u11a", "scheme_dirs": [d]},
                        {"title": "Tq"})
        drawn = tsr._draw(spec, mode)
        sizes = {str(f.title.text_font_size) for f in drawn.figures
                 if getattr(f.title, "text", "")}
        assert any(abs(float(s.rstrip("pt")) - _want("u11a")) < 0.05
                   for s in sizes if s.endswith("pt")), sizes
