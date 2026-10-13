"""An mlabel() element naming several variables (WP-31 C10b).

GAPS3 C10: ``_dash_mlabel_list`` validated each unquoted mlabel() element
as one variable, so ``scatter mpg price weight, mlabel(t*)`` was r(111)
where twoway labels mpg with trunk and price with turn.  twoway's
``MLabels(string)`` is expanded with ``unab``; measured in
test/fixtures/parsed_values_truth.json (scripts/extract_parsed_values_truth.do):
``mlabel(t*)`` on two y's labels them trunk, turn; on one y the second
name is dropped (rc 0); ``mlabel(make-foreign)`` is a range; ``mlabel(zz*)``
is r(111) "variable zz* not found".

The pattern, and only a pattern (an unquoted element of Stata name
characters holding ``*``, ``?``, ``~`` or ``-``), goes through ``unab``;
its names take its place in the list.  The cscript case U06-02 runs it in
Stata; here the source and the renderer's reading of the per-y list.
"""
import json
import os
import re
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_ADO = os.path.join(_HERE, "..", "dash.ado")
_FIX = os.path.join(_HERE, "fixtures", "parsed_values_truth.json")


def _program(name):
    with open(_ADO, encoding="utf-8") as fh:
        src = fh.read()
    start = src.index("program define " + name)
    return src[start:src.index("\nend\n", start)]


class TestTheFixture:
    def test_twoways_readings(self):
        with open(_FIX, encoding="utf-8") as fh:
            m = json.load(fh)["mlabel"]
        assert m["pattern"]["rc"] == 0
        assert m["pattern"]["vars"][-2:] == ["trunk", "turn"]
        assert m["extra_names"]["rc"] == 0
        assert m["range"]["rc"] == 0
        assert (m["bad_pattern"]["rc"], m["bad_pattern"]["message"]) == \
            (111, "variable zz* not found")


class TestTheSplice:
    def test_unab_is_used(self):
        body = _program("_dash_mlabel_list")
        assert re.search(r"capture unab \S+ : ", body)
        assert "fvunab" not in body and "tsunab" not in body

    def test_the_pattern_is_bounded(self):
        body = _program("_dash_mlabel_list")
        assert '"^[A-Za-z_*?~][A-Za-z0-9_*?~-]*$"' in body
        assert '"[*?~-]"' in body


@pytest.mark.parametrize("mode", ("saved", "served"))
def test_two_labelsets(mode):
    """What dash.ado writes for mlabel(t*) on two y's -- one label
    variable per y -- draws one label set per layer, each from its own
    column (guard: the renderer reads the per-y list)."""
    from bokeh.models import LabelSet
    spec = tp._spec([plot_for("scatter", {"mlabel": "price"}),
                     plot_for("scatter", {"mlabel": "foreign"},
                              yvar="price")])
    if mode == "saved":
        r, _w = tp._standalone(spec)
        models = list(r._last_layout_root.references())
    else:
        doc, _w = tp._served(spec)
        models = [m for root in doc.roots for m in root.references()]
    sets = [m for m in models if isinstance(m, LabelSet)]
    assert len(sets) == 2
    texts = sorted(str(s.text.field if hasattr(s.text, "field") else s.text)
                   for s in sets)
    assert len(set(texts)) == 2
