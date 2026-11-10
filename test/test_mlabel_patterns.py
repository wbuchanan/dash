"""An mlabel() element naming several variables (WP-31 C10b).

GAPS3 C10: ``_dash_mlabel_list`` validated each unquoted mlabel() element
as one variable, so ``scatter mpg price weight, mlabel(t*)`` was r(111)
where twoway labels mpg with trunk and price with turn.  twoway's
``MLabels(string)`` is expanded with ``unab``; measured in
test/fixtures/parsed_values_truth.json (scripts/extract_parsed_values_truth.do):
``mlabel(t*)`` on two y's labels them trunk, turn; on one y the second
name is dropped (rc 0); ``mlabel(make-foreign)`` is a range; ``mlabel(zz*)``
is r(111) "variable zz* not found".

WP-47 basic:PT-3 corrected the picture: those serset rows are not what
twoway draws.  Measured from its SVG (test/fixtures/varlabel_mlabel_truth.json
mlabel_pattern.*, scripts/extract_varlabel_mlabel_truth.do): an element
that is a pattern naming several variables draws no labels for the y it
falls on -- ``mlabel(t*)`` on one y or two, ``mlabel(make-foreign)`` --
while one naming a single variable (``mlabel(tr*)``) labels its y, and
in ``mlabel(make t*)`` mpg is labelled by make and price by nothing
(``mlabel(t* make)`` the other way round).

The pattern, and only a pattern (an unquoted element of Stata name
characters holding ``*``, ``?``, ``~`` or ``-``), goes through ``unab``;
one name takes its place in the list and several leave that y unlabelled.
The cscript cases U06-02 and Q4702-4 run it in Stata; here the source and
the renderer's reading of the per-y list.
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
    """What dash.ado writes for mlabel(trunk turn) on two y's -- one label
    variable per y -- draws one label set per layer, each from its own
    column (guard: the renderer reads the per-y list).

    Flipped (WP-47 basic:PT-3): this was mlabel(t*), which twoway draws
    with no labels (varlabel_mlabel_truth.json mlabel_pattern.two_y), so
    dash.ado now writes no mlabel for it; the explicit list
    (mlabel_pattern.list) is the case that draws two label sets."""
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


_VL = os.path.join(_HERE, "fixtures", "varlabel_mlabel_truth.json")


def _drawn_labelled_ys(rec, none):
    """How many y's twoway labelled: the case's texts beyond the
    unlabelled twin's, five rows a y."""
    return (len(rec["texts"]) - len(none["texts"])) // 5


class TestPatterns:

    # case: the per-y label variables dash.ado now writes ("." none)
    CASES = {"one_y": ["."], "two_y": [".", "."], "single": ["trunk"],
             "range": ["."], "lead": ["make", "."],
             "trail": [".", "make"], "list": ["trunk", "turn"]}

    def test_the_fixture(self):
        with open(_VL, encoding="utf-8") as fh:
            m = json.load(fh)["mlabel_pattern"]
        for case, ml in self.CASES.items():
            none = m["none" if len(ml) == 1 else "none_two"]
            assert m[case]["rc"] == 0 and m[case]["notes"] == [], case
            assert _drawn_labelled_ys(m[case], none) == \
                len([v for v in ml if v != "."]), case

    def test_the_rule(self):
        # A pattern naming several variables is one element that leaves
        # its y unlabelled, and counts as named (no r(102)).
        body = _program("_dash_mlabel_list")
        assert ("// WP-47 basic:PT-3: twoway draws no labels for an "
                "mlabel() element that names several variables "
                "(varlabel_mlabel_truth.json mlabel_pattern.*)") in body
        assert "if `: word count `_mlx'' > 1 {" in body
        assert "local named `_mlsev'" in body

    @pytest.mark.parametrize("mode", ("saved", "served"))
    @pytest.mark.parametrize("case", sorted(CASES))
    def test_case(self, mode, case):
        """The records dash.ado writes for each case draw twoway's
        number of label sets, with no note."""
        from bokeh.models import LabelSet
        ml = self.CASES[case]
        # The parity data's variables stand in for auto's label variables.
        sub = {"trunk": "price", "turn": "foreign"}
        plots = [plot_for("scatter",
                          {"mlabel": sub.get(v, "foreign")} if v != "."
                          else {}, yvar=y)
                 for v, y in zip(ml, ("mpg", "price"))]
        spec = tp._spec(plots)
        if mode == "saved":
            r, w = tp._standalone(spec)
            models = list(r._last_layout_root.references())
        else:
            doc, w = tp._served(spec)
            models = [m for root in doc.roots for m in root.references()]
        assert len([m for m in models if isinstance(m, LabelSet)]) == \
            len([v for v in ml if v != "."])
        assert not [x for x in w if "mlabel" in str(x)], w


def test_the_help():
    """AC-47-02.3: the help's mlabel() synopt says what twoway draws."""
    with open(os.path.join(_HERE, "..", "dash.sthlp"), encoding="utf-8") as fh:
        hlp = " ".join(fh.read().split())
    assert ("one that names several ({cmd:t*}, {cmd:make-foreign}) draws no "
            "labels for that y, as {cmd:twoway} draws none") in hlp
