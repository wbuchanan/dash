"""WP-31 D1c: the minor-label edges section 24 left (section 33, D20).

Three differences from twoway:

* a ``format()`` on ``xmlabel(##N)`` wrote the labels in it at the build,
  but the saved page's after-move text used the axis's own writer;
* ``ymlabel()``/``xmlabel()``/``ymtick()`` on ``axis(2)`` took an
  ``angle()`` outside -360..360, which twoway refuses r(198) "textangle
  must be between -360.000 and 360.000" (test/fixtures/axis_look_truth.json
  m2_angle_y, m2_angle_x, m2_tick_y; test_option_validation.cscript
  U33-09);
* an evenly spaced list typed as a list (``xlabel(1000 2000 3000)
  xmtick(##5)``) was drawn as the rule it spells, where twoway draws one
  tick at 0 (test/fixtures/minor_tick_truth.json m_between_even_list):
  dash.ado expanded ``a(b)c`` before the renderer could tell the two
  apart.  dash.ado now keeps a lone ``a(b)c`` as typed, and the renderer
  reads a typed list as no rule (test_wp31_truth.cscript U33-10).

While iterating: ``python3 -m pytest test/test_minor_label_edges.py -q``.
"""
import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_default_axes as tda  # noqa: E402
import test_minor_ticks as tmt  # noqa: E402
from conftest import render_models  # noqa: E402

_MODES = ("saved", "served")
_MT = tmt._T
_AL = json.load(open(os.path.join(_HERE, "fixtures", "axis_look_truth.json"),
                     encoding="utf-8"))


def _saved(go):
    spec = tda._spec(tmt._SC, go, formats=tmt._FORMATS)
    _tag, sp, dp = tda._write(spec)
    return render_models(dr.DashRenderer(sp, dp))


def _minor_entry(r):
    plan_json, models = dr._dash_axis_plan(r.figures, {}, zoom=False)
    plan = json.loads(plan_json) if isinstance(plan_json, str) else plan_json
    for g in plan:
        for p in g["panels"]:
            for a in p["axes"]:
                if a.get("minor") and a["letter"] == "x":
                    return a, models
    return None, models


class TestTheFixtures:
    def test_axis2_angle(self):
        for k in ("m2_angle_y", "m2_angle_x", "m2_tick_y", "m1_angle_y"):
            assert _AL[k]["rc"] == 198, k
            assert _AL[k]["log"] == [
                "textangle must be between -360.000 and 360.000"], k

    def test_even_list(self):
        assert _MT["m_between_even_list"]["positions"] == [0.0]


class TestTheFormatAfterAMove:
    def test_the_page_writes_in_the_format(self):
        r = _saved({"xlabel": "0(1000)5000",
                    "xmlabel": "##2, format(%9.2f)"})
        a, models = _minor_entry(r)
        assert a is not None and a["minor"]["fm"] >= 0
        fm = models[a["minor"]["fm"]]
        assert dict(fm.args)["fmt"] == "%9.2f"

    def test_without_a_format_the_axis_writer(self):
        r = _saved({"xlabel": "0(1000)5000", "xmlabel": "##2"})
        a, models = _minor_entry(r)
        f = list(r.figures.values())[0]
        assert models[a["minor"]["fm"]] is tda._axis(f, "x").formatter


class TestATypedList:
    @pytest.mark.parametrize("mode", _MODES)
    def test_an_even_typed_list_draws_the_tick_at_0(self, mode):
        f = tmt._figs(mode, {"xlabel": "1000 2000 3000", "xmtick": "##5"})[0]
        assert tmt._minor(f, "x") == _MT["m_between_even_list"]["positions"]

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_rule_as_typed_is_a_rule(self, mode):
        f = tmt._figs(mode, {"xlabel": "1000(1000)3000", "xmtick": "##5"})[0]
        got = tmt._minor(f, "x")
        assert got[0] == pytest.approx(1000.0) and len(got) == 20, got

    def test_the_page_reads_no_rule_after_a_move(self):
        r = _saved({"xlabel": "1000 2000 3000", "xmtick": "##5"})
        a, _models = _minor_entry(r)
        assert a["minor"]["list"] == 1
        r = _saved({"xlabel": "1000(1000)3000", "xmtick": "##5"})
        a, _models = _minor_entry(r)
        assert a["minor"]["list"] == 0

    def test_the_js_reads_no_rule_for_a_list(self):
        import js_runner
        src = dr._DASH_AXIS_FINISH_JS + """
const fx = {ticks: []};
const models = [fx];
const mn = {tb: 5, lb: 0, fx: 0, src: -1, fm: -1, nfix: 0,
            maj: [1000, 2000, 3000]};
const out = [];
for (const lst of [0, 1]) {
  mn.list = lst;
  dash_minor_place({kind: null, mode: "none", ticker: -1, minor: mn,
                    extra: []}, models, 0, 3000);
  out.push(fx.ticks.length);
}
console.log(JSON.stringify(out));
"""
        n_rule, n_list = js_runner.run_js(src)
        assert n_rule > 1 and n_list == 0
