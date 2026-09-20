"""`pci` and `pcscatter` drew nothing, silently.

Both are in dash's advertised plot-type table and both produced a titled,
axed, empty plot region with rc 0 and no warning. Measured, on a spec built
the way dash.ado builds one:

    pcspike     -> renderers: 1
    pcarrow     -> renderers: 1
    pcbarrow    -> renderers: 1
    pcscatter   -> renderers: 0
    pci         -> renderers: 0

Two separate causes.

`pcscatter` takes four VARIABLES in Stata -- `pcscatter y1 x1 y2 x2' -- and
dash.ado routed it through the literal-coordinate parser it uses for
`scatteri'. Measured, `dash pcscatter mpg weight mpg price' wrote

    "values":[[mpg,weight],[mpg,price]]

which is not even valid JSON: the variable names are bare identifiers inside
an array. It is now parsed as the four-variable plot it is, alongside
pcspike, pcarrow and pcbarrow.

`pci` takes literal coordinates -- `pci 20 3000 30 4000' -- and dash.ado
writes them correctly as `"values":[[20,3000],[30,4000]]'. The renderer had
no branch that read them: `map_pci' delegated to `map_pcspike', which wants
variable names, and the render loop did not route `pci' there in any case.

The conformance corpus cannot see either defect, because every command in it
is given `name()', which registers the spec and never renders it.
"""
import json
import os
import sys
import tempfile
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr

_DATA = {
    "variableNames": ["y1", "x1", "y2", "x2"],
    "values": [{"y1": 1.0, "x1": 1.0, "y2": 2.0, "x2": 2.0},
               {"y1": 3.0, "x1": 3.0, "y2": 4.0, "x2": 4.0}],
}


def _render(plot, quiet=True):
    td = tempfile.mkdtemp()
    spec = {"graphs": [{"graph_options": {"name": "g1"}, "plots": [plot]}],
            "kpis": [], "build_options": {"layout": "auto"}}
    sp, dp = os.path.join(td, "s.json"), os.path.join(td, "d.json")
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(_DATA, fh)
    # `quiet' has to be optional: an inner catch_warnings(ignore) swallows
    # the warning an outer catch_warnings(record=True) is trying to read, so
    # a test that asserts a warning was issued sees none and fails for the
    # wrong reason.
    if quiet:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = dr.DashRenderer(sp, dp)
            r.render()
    else:
        r = dr.DashRenderer(sp, dp)
        r.render()
    return r.figures["g1"]


def _vars(ptype):
    return {"type": ptype, "y1var": "y1", "x1var": "x1",
            "y2var": "y2", "x2var": "x2", "options": {}}


class TestEveryPairedCoordinateTypeDraws:
    @pytest.mark.parametrize("ptype", ["pcspike", "pcarrow", "pcbarrow",
                                       "pcscatter"])
    def test_a_four_variable_type_draws(self, ptype):
        fig = _render(_vars(ptype))
        assert len(fig.renderers) >= 1, (
            f"`dash {ptype} y1 x1 y2 x2' draws nothing and says nothing"
        )

    def test_pci_draws_from_literal_coordinates(self):
        """dash.ado writes `pci 20 3000 30 4000' as [[20,3000],[30,4000]]."""
        fig = _render({"type": "pci",
                       "values": [[20.0, 3000.0], [30.0, 4000.0]],
                       "options": {}})
        assert len(fig.renderers) >= 1, (
            "`dash pci 20 3000 30 4000' draws nothing and says nothing"
        )

    def test_pci_puts_the_segment_where_stata_does(self):
        """values are (y, x) pairs, as scatteri's are."""
        fig = _render({"type": "pci",
                       "values": [[20.0, 3000.0], [30.0, 4000.0]],
                       "options": {}})
        src = fig.renderers[0].data_source.data
        assert [float(v) for v in src["x0"]] == [3000.0]
        assert [float(v) for v in src["y0"]] == [20.0]
        assert [float(v) for v in src["x1"]] == [4000.0]
        assert [float(v) for v in src["y1"]] == [30.0]

    def test_pci_draws_one_segment_per_pair_of_points(self):
        fig = _render({"type": "pci",
                       "values": [[1.0, 1.0], [2.0, 2.0],
                                  [3.0, 3.0], [4.0, 4.0]],
                       "options": {}})
        assert len(fig.renderers[0].data_source.data["x0"]) == 2

    def test_an_odd_number_of_points_is_reported_not_fatal(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            fig = _render({"type": "pci",
                           "values": [[1.0, 1.0], [2.0, 2.0], [3.0, 3.0]],
                           "options": {}}, quiet=False)
        assert len(fig.renderers) >= 1
        assert any("pci" in str(w.message) for w in caught), (
            "an unpaired coordinate is dropped without a word"
        )

    def test_no_values_draws_nothing_without_raising(self):
        fig = _render({"type": "pci", "values": [], "options": {}})
        assert isinstance(len(fig.renderers), int)


class TestDashAdoRoutesPcscatterAsVariables:
    def test_pcscatter_is_parsed_with_the_four_variable_types(self):
        with open(os.path.join(_HERE, "..", "dash.ado"),
                  encoding="utf-8") as fh:
            src = fh.read()
        i = src.index("_dash_parse_varpart_4v `varpart'")
        branch = src[max(0, i - 300):i]
        assert '"pcscatter"' in branch, (
            "pcscatter is still routed to the literal-coordinate parser, so "
            "its variable names are written into the spec as bare "
            "identifiers inside a JSON array"
        )

    def test_pcscatter_is_not_in_the_literal_list(self):
        with open(os.path.join(_HERE, "..", "dash.ado"),
                  encoding="utf-8") as fh:
            src = fh.read()
        i = src.index('_dash_parse_varpart_any `varpart\'')
        head = src[max(0, i - 300):i]
        assert '"pcscatter"' not in head, (
            "pcscatter takes four variables, not literal coordinates"
        )
