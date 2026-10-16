"""Dead size constants and the histogram's scheme opacity (WP-31 E13).

``OptionTranslator._SIZE_MAP`` was read by no size path (every size goes
through ``resolve_size``) yet the served app's header serialised it as a
global; ``SchemeParser._GSIZE_NUMERIC_PT_PER_UNIT`` (2.88) duplicated
``OptionTranslator.PT_PER_RS``.  Both are gone: one constant gives
points per Stata relative unit.  The histogram's scheme ``%NN`` opacity
is pinned by test_scheme_consumption.py::TestHistogramSchemeOpacity
against twoway's ``fill-opacity`` (test/fixtures/
colour_width_edges_truth.json ``hist.pct``, scripts/
extract_colour_width_edges_truth.do).
"""
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402

FIXTURE = os.path.join(_HERE, "fixtures", "colour_width_edges_truth.json")
with open(FIXTURE, encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)

#: Every probe the section's tests read.
KEYS = ("sl.eq_glued", "sl.eq_trail", "sl.paren", "sl.msym_unknown",
        "sl.quoted_comma", "lw.vvthin", "lw.vvthin_x10", "lw.medium",
        "lw.medium_x2", "lw.medium_x0_5", "ol.rarea", "ol.rbar",
        "ol.line_medium", "ci.inten200", "ci.p1shade_inten200",
        "hist.pct", "unclear.navy52", "unclear.fgbg",
        "c4b.s2color.ciplot_rline", "c4b.stcolor.ciplot_rcap",
        "lal.l", "lal.lal", "lal.lalp")


class TestTheFixture:
    def test_meta(self):
        meta = TRUTH["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted",
                  "source"):
            assert meta.get(k), k
        assert meta["source"] == "scripts/extract_colour_width_edges_truth.do"

    def test_keys(self):
        missing = [k for k in KEYS if k not in TRUTH]
        assert not missing, missing
        assert sum(k.startswith("sc.") for k in TRUTH) == 13


class TestDeadConstants:
    def test_size_map_gone(self):
        assert not hasattr(dr.OptionTranslator, "_SIZE_MAP")

    def test_app_header_has_no_size_map(self):
        import inspect
        src = inspect.getsource(dr.ServerAppBuilder)
        assert "_SIZE_MAP" not in src
        assert "_SIZE_MAP" not in open(dr.__file__, encoding="utf-8").read()

    def test_one_pt_per_unit_constant(self):
        assert not hasattr(dr.SchemeParser, "_GSIZE_NUMERIC_PT_PER_UNIT")
        sp = dr.SchemeParser.__new__(dr.SchemeParser)
        sp._props = {"gsize heading": "50"}
        assert sp._gsize("gsize heading") == "144pt"
        assert dr.OptionTranslator.PT_PER_RS == 2.88
