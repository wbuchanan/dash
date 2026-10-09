"""A dashboard carried one full copy of the dataset per filter widget.

Every filter callback was given its own serialised snapshot:

    for _fc, _cb in zip(built_filter_specs, self.filter_callbacks):
        ...
        _cb.args["orig_data_json"] = json.dumps(_orig_data)

and, in the same loop, its own list of per-graph-source snapshots. Bokeh
writes each CustomJS's args into the document separately, so k filters meant
k copies of the data -- and because each filter also adds a column to every
copy, the growth is quadratic in the filter count.

Measured on 8,000 rows x 6 columns, before the fix:

    0 filters     1.63 MB
    1 filter      2.81 MB
    2 filters     3.62 MB
    3 filters     5.58 MB
    5 filters    11.47 MB

The survey measured the same shape at scale: 100,000 rows with five sliders
produced 169.6 MB of HTML at 2.77 GB RSS, against 5.98 MB with no filters.
The file is then loaded, parsed and held by the browser, and nothing warned:
the render returned rc 0 and the user found out when they opened it.

The snapshot is passed as a ColumnDataSource now. Bokeh serialises a model
once and refers to it by id from each callback, so the data appears in the
document once however many filters there are.
"""
import json
import os
import sys
import tempfile
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
from conftest import make_data_json

_N = 4000
_RNG = np.random.default_rng(7)
_DF = pd.DataFrame({f"v{i}": _RNG.normal(size=_N) for i in range(5)})
_DF["g"] = _RNG.integers(0, 4, _N).astype(float)


def _build(n_filters, tmp_path):
    filters = "; ".join(f"v{i}, type(range)" for i in range(n_filters))
    spec = {"graphs": [{"name": "g1", "graph_options": {"name": "g1"},
                        "options": {},
                        "plots": [{"type": "scatter", "yvar": "v0",
                                   "xvar": "v1", "options": {}}]}],
            "kpis": [],
            "build_options": {"layout": "auto", "registry": "g1",
                              "level": "95", "formats": {}, "theme": "",
                              "scheme": "", "session_scheme": "",
                              "filter": filters}}
    sp = tmp_path / f"s_{n_filters}.json"
    dp = tmp_path / f"d_{n_filters}.json"
    sp.write_text(json.dumps(spec))
    dp.write_text(json.dumps(make_data_json(_DF)))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = dr.DashRenderer(str(sp), str(dp))
        html = r.render()
    return r, html


@pytest.fixture(scope="module")
def sizes(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("payload")
    out = {}
    for k in (0, 1, 3, 5):
        r, html = _build(k, tmp_path)
        # Each document must hold the filters it is measured for (it does,
        # measured 24sep2026).  Were only the first filter built, the 1-, 3-
        # and 5-filter documents would be one size, and both growth checks
        # below would pass however many copies of the data one filter made.
        assert len(r.filter_callbacks) == k, (
            f"the {k}-filter document built {len(r.filter_callbacks)} "
            f"filter(s)"
        )
        out[k] = len(html)
    return out


# One worker for the class, so the module's pages are measured once,
# not once per worker its tests land on (WP-30 test performance A4;
# measured 07oct2026: 2.6 s on two).
@pytest.mark.xdist_group(name="filter-payload-sizes")
class TestTheDataIsNotCopiedPerFilter:
    def test_the_measurement_is_meaningful(self, sizes):
        """Guards the guard: a tiny document would make the ratios noise."""
        assert sizes[0] > 500_000, (
            f"the no-filter document is only {sizes[0]} bytes; the growth "
            f"checks below would be measuring rounding"
        )

    def test_a_filter_does_not_cost_a_dataset(self, sizes):
        """The marginal cost of a filter must be a fraction of the data.

        Some marginal cost is legitimate: the widget, its callback, and one
        more column in the (single) snapshot, since a filter variable is a
        column. What must not happen is a whole further copy of the data.
        """
        data_cost = sizes[1] - sizes[0]
        per_filter = (sizes[5] - sizes[1]) / 4.0
        assert per_filter < 0.5 * data_cost, (
            f"each extra filter adds {per_filter:,.0f} bytes against a "
            f"dataset costing {data_cost:,} -- the data is being copied per "
            f"widget"
        )

    def test_growth_is_not_quadratic(self, sizes):
        """Each extra filter must cost about the same, not more each time."""
        first = sizes[1] - sizes[0]
        last_two = (sizes[5] - sizes[3]) / 2.0
        assert last_two <= first, (
            f"the 4th and 5th filters cost {last_two:,.0f} bytes each and "
            f"the 1st cost {first:,.0f}; the cost per filter is rising"
        )


class TestEveryCallbackSharesOneSnapshot:
    def test_the_primary_snapshot_is_one_model(self, tmp_path):
        r, _html = _build(4, tmp_path)
        assert len(r.filter_callbacks) == 4
        snaps = [cb.args.get("orig_source") for cb in r.filter_callbacks]
        assert all(s is not None for s in snaps), (
            "a callback has no shared snapshot source"
        )
        assert len({id(s) for s in snaps}) == 1, (
            "each callback holds its own snapshot, so Bokeh writes the "
            "dataset into the document once per filter"
        )

    def test_the_snapshot_holds_the_data(self, tmp_path):
        r, _html = _build(2, tmp_path)
        data = r.filter_callbacks[0].args["orig_source"].data
        assert len(data["v0"]) == _N
        assert dr._ROW_ID_COLUMN in data, (
            "the snapshot must carry the row identity the callback masks on"
        )

    def test_the_graph_snapshots_are_shared_too(self, tmp_path):
        r, _html = _build(3, tmp_path)
        per_cb = [cb.args.get("all_graph_sources_orig")
                  for cb in r.filter_callbacks]
        assert all(p is not None for p in per_cb)
        ids = [{id(m) for m in p} for p in per_cb]
        assert set.intersection(*ids), (
            "no graph snapshot model is shared between callbacks"
        )
