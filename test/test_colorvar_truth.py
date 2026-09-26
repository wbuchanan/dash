"""test_colorvar_truth.py -- dash's colorvar() groups against twoway's own
(GAPS2 X2).

test/fixtures/colorvar_truth.json is written by
scripts/extract_colorvar_truth.do: for each probe, twoway's exported SVG
is read through scripts/svg_truth.py and every in-region marker's fill is
recorded in document order, which the fixture's self-check proves is
observation order.  Each probe's options are rendered through dash's own
mapper over the same column, and the partition of observations by dash's
colour factor must equal the partition by twoway's fill.
"""
import json
import os
import re
import sys
import warnings

import numpy as np
import pytest
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "colorvar_truth.json")


def _truth():
    if not os.path.exists(_FIXTURE):
        pytest.fail("section 16 task 16-03 must land first: "
                    "test/fixtures/colorvar_truth.json is missing")
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _probe_ids():
    if not os.path.exists(_FIXTURE):
        return ["missing-fixture"]
    with open(_FIXTURE, encoding="utf-8") as fh:
        return sorted(json.load(fh)["probes"])


_FLAGS = ("colordiscrete", "colorvarminmax")
_VALUED = ("colorvar", "colorcuts", "colorlevels")


def _opts_of(command):
    """The colorvar options of a twoway command line (test helper only)."""
    out = {}
    for k in _VALUED:
        m = re.search(r"\b%s\(([^)]*)\)" % k, command)
        if m:
            out[k] = m.group(1).strip()
    for k in _FLAGS:
        if re.search(r"\b%s\b" % k, command):
            out[k] = k
    return out


def _canonical(labels):
    seen, out = {}, []
    for lab in labels:
        seen.setdefault(lab, len(seen))
        out.append(seen[lab])
    return out


class TestAgainstTwoway:

    @pytest.mark.parametrize("pid", _probe_ids())
    def test_every_probe_partitions_the_observations_as_twoway_does(self, pid):
        truth = _truth()
        probe = truth["probes"][pid]
        if "twoway_rc" in probe:
            # A refusal probe: dash answers with twoway's return code.
            assert probe["rc"] == probe["twoway_rc"], probe
            return
        assert probe["rc"] == 0
        col = truth["_data"][probe["dataset"]]
        opts = _opts_of(probe["command"])
        values = [np.nan if v is None else v for v in col[opts["colorvar"]]]
        assert probe["n_markers"] == len(values)
        if not ({"colordiscrete", "colorcuts", "colorlevels"} & set(opts)):
            return  # the continuous default is not compared (DISCOVERY Q5)
        gm = dr.GlyphMapper(dr.OptionTranslator(), dr.SchemeParser("s2color"))
        src = ColumnDataSource({"v": values, "y": [1.0] * len(values)})
        fig = figure()
        rend = fig.scatter(x="v", y="y", source=src)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            gm._apply_colorvar(fig, rend, src, dict(opts, colorvar="v"))
        binned = list(src.data["_cvar_v_bin"])
        assert len(set(binned)) == probe["n_groups"], (pid, sorted(set(binned)))
        if truth["_meta"]["marker_order_selfcheck"] == "observation":
            assert _canonical(binned) == _canonical(probe["fill_groups"]), pid
        else:
            assert sorted(np.bincount(_canonical(binned))) == \
                sorted(np.bincount(probe["fill_groups"]))

    def test_the_fixture_self_check_held(self):
        assert _truth()["_meta"]["marker_order_selfcheck"] == "observation"

    def test_the_fixture_meta_carries_the_four_provenance_keys(self):
        meta = _truth()["_meta"]
        for key in ("stata_version", "born_date", "dash_commit", "extracted"):
            assert key in meta
