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
pcspike, pcarrow and pcbarrow.  That half is Stata's, and is certified by
running it: test_parser.cscript P1A-56 hands `pcscatter mpg weight turn
length' to dash.ado's own segment parser and requires the four keys y1var,
x1var, y2var and x2var in the JSON it writes -- measured (WP-24) to fail
when pcscatter is moved back to the literal family.  This file used to
check the routing by reading dash.ado as text for the family each parser's
branch names; P1A-56 fails on the same change, so those two source-shape
tests were removed rather than kept as a second, weaker copy.  The tests
below are the renderer's half: the spec as dash.ado writes it draws.

`pci` takes literal coordinates -- `pci 20 3000 30 4000' -- which dash.ado
then wrote as `"values":[[20,3000],[30,4000]]'. The renderer had no branch
that read them: `map_pci' delegated to `map_pcspike', which wants variable
names, and the render loop did not route `pci' there in any case.  Since
23sep2026 dash.ado writes one record per segment, `[[20,3000,30,4000]]', the
record pcarrowi writes, with a label and clock position when they are given
(test_immediate_values.py; test_parser.cscript P1A-63..65).

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
        """dash.ado writes `pci 20 3000 30 4000' as [[20,3000,30,4000]]."""
        fig = _render({"type": "pci",
                       "values": [[20.0, 3000.0, 30.0, 4000.0]],
                       "options": {}})
        assert len(fig.renderers) >= 1, (
            "`dash pci 20 3000 30 4000' draws nothing and says nothing"
        )

    def test_pci_puts_the_segment_where_stata_does(self):
        """A record is y1 x1 y2 x2, in twoway's order."""
        fig = _render({"type": "pci",
                       "values": [[20.0, 3000.0, 30.0, 4000.0]],
                       "options": {}})
        src = fig.renderers[0].data_source.data
        assert [float(v) for v in src["x0"]] == [3000.0]
        assert [float(v) for v in src["y0"]] == [20.0]
        assert [float(v) for v in src["x1"]] == [4000.0]
        assert [float(v) for v in src["y1"]] == [30.0]

    def test_pci_draws_one_segment_per_record(self):
        fig = _render({"type": "pci",
                       "values": [[1.0, 1.0, 2.0, 2.0],
                                  [3.0, 3.0, 4.0, 4.0]],
                       "options": {}})
        assert len(fig.renderers[0].data_source.data["x0"]) == 2

    def test_a_record_that_is_not_one_is_reported_not_drawn(self):
        """An incomplete last segment is dropped by dash.ado, with a note
        (test_parser.cscript P1A-65); a spec that still carries one -- a
        spec written by hand is an input too -- is refused naming pci
        rather than drawn wrong: the figure is not built, and the error
        says which figure and why."""
        with pytest.raises(RuntimeError,
                           match=r"figure 'g1'.*pci records are"):
            _render({"type": "pci",
                     "values": [[1.0, 1.0, 2.0, 2.0], [3.0, 3.0]],
                     "options": {}}, quiet=False)

    def test_no_values_draws_nothing_without_raising(self):
        fig = _render({"type": "pci", "values": [], "options": {}})
        assert isinstance(len(fig.renderers), int)
