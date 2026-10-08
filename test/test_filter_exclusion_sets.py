"""test_filter_exclusion_sets.py -- every target is masked by exactly the
filters whose exclude() does not name it, on every move (GAPS2 E2).

Measured at 91d97be (both modes): filter(price, ... exclude(g1 k1)) beside
a foreign dropdown; price -> [4000, 5000], foreign -> 1, price -> its full
range left g1=3, g2=5, k1=3 where the widgets imply 5.  Each callback
masked with every widget but wrote only the targets its OWN trigger did
not exclude, so an excluded target kept whatever the last other move
wrote.  The four-state sequence itself is
test_help_claims_3.py::TestAnExclusionHoldsAgainstEveryMove.
"""
import json
import os
import sys
import warnings

import pytest
from bokeh.models import RangeSlider, Select

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import js_runner  # noqa: E402
import test_filter_exclude as tfe  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_help_claims_3 import (TestAnExclusionHoldsAgainstEveryMove as  # noqa: E402
                                _Seq, _card_value, _kpi_card)


from conftest import render_models  # noqa: E402


def _two_filter_spec(graphs, kpis=(), price_excl=(), link=""):
    names = [g["graph_options"]["name"] for g in graphs] + [
        k["name"] for k in kpis]
    return {"graphs": graphs, "kpis": list(kpis),
            "build_options": {
                "layout": "auto", "link": link, "theme": "", "title": "",
                "subtitle": "", "registry": " ".join(names),
                "filters": [{"varname": "foreign", "type": "dropdown"},
                            {"varname": "price", "type": "range",
                             "exclude": list(price_excl)}]}}


def _render(tmp_path, spec):
    tmp_path.mkdir(parents=True, exist_ok=True)
    sp, dp = tfe._write_inputs(tmp_path, spec)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = dr.DashRenderer(sp, dp)
        render_models(r)
    return r


def _saved_after(tmp_path, spec, order):
    """Rows per figure title and card text after the moves in *order*."""
    r = _render(tmp_path, spec)
    (w_for, w_price), (cb_for, cb_price) = (r.filter_widgets,
                                            r.filter_callbacks)
    s = js_runner.JsSession(r.filter_callbacks)
    for which in order:
        w, cb, v = ((w_for, cb_for, 1.0) if which == "foreign"
                    else (w_price, cb_price, _Seq.PRICE))
        s.set(w, v)
        s.run(cb)
    out = {tfe._key(f): tfe._rows(tfe._renderer_source(f))
           for f in r.figures.values()}
    for name, div in r.kpi_divs.items():
        out[name] = _card_value(div.text, name)
    return out


def _served_after(tmp_path, spec, order):
    from bokeh.document import Document
    from bokeh.models import Div
    tmp_path.mkdir(parents=True, exist_ok=True)
    sp, dp = tfe._write_inputs(tmp_path, spec)
    app = os.path.join(str(tmp_path), "app_%s.py" % "_".join(order))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(app)
    with open(app, encoding="utf-8") as fh:
        ns = tfe._load_app(fh.read(), "e2_%s" % "_".join(order))
    doc = Document()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ns["make_document"](doc)
        [w_for] = list(doc.select({"type": Select}))
        [w_price] = list(doc.select({"type": RangeSlider}))
        for which in order:
            tp._fire(*((w_for, 1.0) if which == "foreign"
                       else (w_price, _Seq.PRICE)))
    out = tfe._served_rows(doc)
    for d in doc.select({"type": Div}):
        for name in ("k1", "k2"):
            v = _card_value(d.text, name)
            if v:
                out[name] = v
    return out


class TestTheOrderOfMoves:

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_the_order_of_moves_does_not_matter(self, tmp_path, mode):
        run = _saved_after if mode == "saved" else _served_after
        a = run(tmp_path / "a", _Seq.SPEC, ["price", "foreign"])
        b = run(tmp_path / "b", _Seq.SPEC, ["foreign", "price"])
        assert a == b == {"g1": 5, "g2": 3, "k1": "5"}


class TestAnExcludedKpi:

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_an_excluded_kpi_is_recomputed_by_the_filters_that_apply_to_it(
            self, tmp_path, mode):
        spec = _two_filter_spec([tfe._graph("g1")],
                                [_kpi_card("k1"), _kpi_card("k2")],
                                price_excl=["k1"])
        run = _saved_after if mode == "saved" else _served_after
        got = run(tmp_path, spec, ["price", "foreign"])
        assert (got["k1"], got["k2"]) == ("5", "3")


class TestALinkGroupIsOneTarget:

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_a_link_group_is_one_target(self, tmp_path, mode):
        run = _saved_after if mode == "saved" else _served_after
        one = _two_filter_spec([tfe._graph("g1"), tfe._graph("g2")],
                               price_excl=["g1"], link="g1 g2")
        got = run(tmp_path / "one", one, ["price", "foreign"])
        assert (got["g1"], got["g2"]) == (3, 3)
        both = _two_filter_spec([tfe._graph("g1"), tfe._graph("g2")],
                                price_excl=["g1", "g2"], link="g1 g2")
        got = run(tmp_path / "both", both, ["price", "foreign"])
        assert (got["g1"], got["g2"]) == (5, 5)


class TestAByPanelFollowsItsOwner:

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_a_by_panel_follows_its_owner_across_moves(self, tmp_path, mode):
        run = _saved_after if mode == "saved" else _served_after
        spec = _two_filter_spec([tfe._graph("g1", by="foreign"),
                                 tfe._graph("g2")], price_excl=["g1"])
        got = run(tmp_path, spec, ["price", "foreign"])
        # Flipped (WP-30 P1.15a): panels keyed "g1 <label>" (tfe._key);
        # "g1 — 0" was the title, which held the label.
        p0, p1 = ("g1 %s" % g for g in ("0", "1"))
        assert (got[p0], got[p1], got["g2"]) == (0, 5, 3)


class TestTheCallbackArgs:

    def test_every_source_is_filtered_or_protected_and_use_is_recorded(
            self, tmp_path):
        spec = _two_filter_spec([tfe._graph("g1"), tfe._graph("g2"),
                                 tfe._graph("g3")], price_excl=["g1"])
        spec["build_options"]["filters"][0]["exclude"] = ["g3"]
        spec["build_options"]["filters"][1]["exclude"] = ["g1", "g3"]
        r = _render(tmp_path, spec)
        cb0, cb1 = r.filter_callbacks
        for key in ("graph_use_json", "derived_use_json", "kpi_config_json"):
            assert cb0.args[key] == cb1.args[key]
        srcs = cb0.args["all_graph_sources"]
        use = json.loads(cb0.args["graph_use_json"])
        assert len(use) == len(srcs) and all(use)
        by_id = {s.id: u for s, u in zip(srcs, use)}
        assert by_id[r.sources["g1"].id] == [0]
        assert by_id[r.sources["g2"].id] == [0, 1]
        assert [s.id for s in cb0.args["excluded_sources"]] == [
            r.sources["g3"].id]

    def test_the_kpi_marker_is_kept_once_before_the_loop(self):
        js = dr._FILTER_JS
        a = js.index("// ---- KPI recompute, shared by")
        b = js.index("function dash_apply_kpis(")
        c = js.index("dash_apply_kpis(new_data,")
        assert a < b < c
        assert js[c:].startswith("dash_apply_kpis(new_data, [], [], ROW_ID);")
        assert "dash_apply_kpis(_grp_data, _grp.config, _grp.divs, ROW_ID)" \
            in js[c:]
        assert js[a:c].count("dash_apply_kpis(new_data,") == 0


class TestTheHelpers:

    def test_filter_applies_and_widgets_for(self):
        owner = {"g1__by__0": "g1"}
        assert dr._dash_filter_applies("g2", ["g1"], owner)
        assert not dr._dash_filter_applies("g1", ["g1"], owner)
        assert not dr._dash_filter_applies("g1__by__0", ["g1"], owner)
        assert dr._dash_filter_applies(None, ["g1"], owner, ["g1", "g2"])
        assert not dr._dash_filter_applies(None, ["g1", "g2"], owner,
                                           ["g1", "g2"])

        class W:
            def __init__(self, excl):
                self._dash_exclude = excl
        a, b = W(["g1"]), W([])
        assert dr._dash_widgets_for("g1", [a, b], owner) == [b]
        assert dr._dash_widgets_for("g2", [a, b], owner) == [a, b]


_TRUTH = os.path.join(_HERE, "fixtures", "filter_truth.json")


def _truth():
    if not os.path.exists(_TRUTH):
        pytest.fail("section 17 task 17-08 must land first: "
                    "test/fixtures/filter_truth.json is missing")
    with open(_TRUTH, encoding="utf-8") as fh:
        return json.load(fh)


class TestAutoAgainstStata:
    """test/fixtures/filter_truth.json (scripts/extract_filter_truth.do):
    on sysuse auto, g1 and k1 excluded from price; foreign -> 1 then price
    -> [4000, 5000]: the excluded pair equals Stata's foreign==1 count and
    mean, the rest the intersection, in both modes."""

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_auto_matches_stata(self, tmp_path, mode):
        import numpy as np
        import pandas as pd
        import filter_truth_check as ftc
        t = _truth()
        df = pd.DataFrame(t["data"])
        df["weight"] = np.arange(len(df), dtype=float)
        spec = ftc.spec_of([ftc.scatter_graph("g1", "mpg", "price"),
                            ftc.scatter_graph("g2", "mpg", "weight")],
                           [{"varname": "foreign", "type": "dropdown"},
                            {"varname": "price", "type": "range",
                             "exclude": ["g1", "k1"]}],
                           [ftc.kpi("k1"), ftc.kpi("k2")])
        run = ftc.saved if mode == "saved" else ftc.served
        st, _ = run(df, set(), spec, [(0, 1.0), (1, (4000.0, 5000.0))])
        one, both = t["foreign_1"], t["foreign_1_price_4000_5000"]
        assert st["g1"][0] == one["count"] and st["k1"] == str(one["count"])
        assert st["g2"][0] == both["count"] and st["k2"] == str(both["count"])
        assert st["g1"][1] == pytest.approx(one["mean_mpg"], rel=1e-9)
        assert st["g2"][1] == pytest.approx(both["mean_mpg"], rel=1e-9)

    def test_the_fixture_meta_carries_the_four_provenance_keys(self):
        meta = _truth()["_meta"]
        for key in ("stata_version", "born_date", "dash_commit", "extracted"):
            assert key in meta
