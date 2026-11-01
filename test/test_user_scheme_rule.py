"""A user scheme's colorvar() default colour rule (WP-31 section 44, C8c).

twoway takes a colorvar() key's default rule from the scheme -- ``zyx2rule
contour`` (the last line wins), its begin and end from ``shadestyle
contour_begin`` and ``contour_end`` (the shadestyle files read ``color
contour_begin`` / ``contour_end``) -- and a hue rule keeps the begin
shade's saturation and value (zyx2style.class ``hue``: each level is a
copy of the begin shade with its hue set).  dash gave every scheme it does
not ship s2color's blue-to-red hue.  Expectations are twoway's, measured
in StataNow 19.5 by scripts/extract_user_scheme_rule_truth.do into
test/fixtures/user_scheme_rule_truth.json.
"""

from __future__ import annotations

import json
import os
import sys
import warnings

import pytest
from bokeh.document import Document

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_colorvar_options as tco  # noqa: E402
from conftest import load_app, make_data_json, render_models  # noqa: E402
from test_server_layer_defects import (_figures_of, make_spec,  # noqa: E402
                                       plot_for)

with open(os.path.join(_HERE, "fixtures", "user_scheme_rule_truth.json"),
          encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)
with open(os.path.join(_HERE, "fixtures", "style_files_truth.json"),
          encoding="utf-8") as _fh:
    BASE = json.load(_fh)["find_base"]
needs_base = pytest.mark.skipif(
    not os.path.isdir(os.path.join(BASE, "s")),
    reason="Stata's scheme files are not here")

#: Records dash does not match, each for a reason.
_EXCLUDED = {
    ("uc4", "S2"): ("twoway draws colorlevels(2) at the begin shade's "
                    "intensity (inten50) and colordiscrete at full "
                    "intensity; dash draws both at full intensity, as "
                    "colordiscrete"),
}


def _dir(tmp_path):
    d = tmp_path / "ado"
    (d / "style").mkdir(parents=True, exist_ok=True)
    for s, rec in TRUTH["schemes"].items():
        (d / f"scheme-{s}.scheme").write_text(
            "\n".join(rec["lines"]) + "\n", encoding="utf-8")
    (d / "style" / "shadestyle-u44s.style").write_text(
        "set color red\nset intensity inten50\n", encoding="utf-8")
    return str(d)


def _palette(sp, k):
    rule, s, e = dr._dash_colorrule_default(sp)
    return dr._dash_colorrule_palette(rule, s, e, k,
                                      scheme_p=list(sp.p_colors),
                                      sv=dr._dash_colorrule_sv(sp))


class TestTheFixture:
    def test_meta(self):
        assert sorted(TRUTH["_meta"]) == ["born_date", "dash_commit",
                                          "extracted", "source",
                                          "stata_version"]
        assert all(r["S2"]["rc"] == 0 and r["S5"]["rc"] == 0
                   for r in TRUTH["schemes"].values())


@needs_base
class TestUserSchemes:
    @pytest.mark.parametrize("scheme", sorted(TRUTH["schemes"]))
    def test_default(self, scheme, tmp_path):
        d = _dir(tmp_path)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            sp = dr.SchemeParser(scheme, ado_dirs=(d, BASE))
        rec = TRUTH["schemes"][scheme]
        bad = []
        for probe, k, n in (("S2", 2, 2), ("S5", 6, 5)):
            if (scheme, probe) in _EXCLUDED:
                continue
            want = list(reversed(rec[probe]["key"]["fills"]))
            got = _palette(sp, k)[:n]
            if not tco._close(got, want):
                bad.append((probe, got, want))
        assert not bad

    def test_shipped_schemes_keep_their_measured_rule(self):
        for s in ("s2color", "stcolor", "s1mono", "economist"):
            sp = dr.SchemeParser(s, ado_dirs=(BASE,))
            assert dr._dash_colorrule_default(sp) == \
                dr._dash_colorrule_default(dr.SchemeParser(s))
            assert "@stata zyx2default" not in sp._props
        # A hue under s2color and stcolor keeps blue's full saturation
        # and value, as D01-D09 measured.
        for s in ("s2color", "stcolor"):
            assert dr._dash_colorrule_sv(dr.SchemeParser(s)) == (1.0, 1.0)


@needs_base
@pytest.mark.parametrize("mode", ["saved", "served"])
class TestDrawn:
    def test_uc2_levels(self, mode, tmp_path):
        """scheme(uc2): green to orange at green's value, both modes."""
        d = _dir(tmp_path)
        spec = make_spec([plot_for("scatter", {
            "colorvar": "rep78", "colordiscrete": "colordiscrete"})],
            graph_options={"scheme": "uc2"})
        spec["build_options"]["scheme_dirs"] = [d, BASE]
        sp, dp = tmp_path / "s.json", tmp_path / "d.json"
        sp.write_text(json.dumps(spec))
        dp.write_text(json.dumps(make_data_json(tco._DF)))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if mode == "saved":
                r = dr.DashRenderer(str(sp), str(dp))
                render_models(r)
                figs = list(r.figures.values())
            else:
                ap = tmp_path / "app.py"
                dr.ServerAppBuilder(str(sp), str(dp)).build(str(ap))
                mod = load_app(str(ap), f"_uc2_{mode}", draw=False)
                doc = Document()
                mod.make_document(doc)
                figs = _figures_of(doc)
        want = list(reversed(TRUTH["schemes"]["uc2"]["S5"]["key"]["fills"]))
        got = list(tco._mapper(figs[0]).palette)
        assert tco._close(got, want), (got, want)
