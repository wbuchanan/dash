"""
test_range_mlabel_rule.py -- a range plot labelled by one of its own
variables is answered as twoway answers it (WP-31 C14).

The defect (measured at 536abd8): ``dash rscatter lo hi weight,
mlabel(lo)`` drew where twoway refuses it.

twoway (StataNow 19.5, scripts/extract_varlabel_mlabel_truth.do, fixture
test/fixtures/varlabel_mlabel_truth.json c14.*): y2xview_parse puts the
label variables in the layer's list and takes them off before counting,
so a label variable that is also plotted leaves too few: every range type
answers "<type> requires 3 variables: <list>", r(102), the list being
the plotted and label variables once each (mlabel(lo make): "lo hi
weight make"); rpcap and rpspike "you must specify four variables with
twoway <type>", r(102); mlabel(make) draws.  mlabvposition(p9) beside
mlabel(lo) brings the count back to 3 and twoway draws it
(test_twoway_option_parity.cscript MV-11).
"""
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from test_varlabel_options import T, ado_text  # noqa: E402


class TestTheRule:

    def test_the_fixture(self):
        c = T["c14"]
        assert c["other"]["rc"] == 0
        for k, r in c.items():
            if k != "other":
                assert r["rc"] == 102, k
        assert c["y_other"]["error"] == \
            "rscatter requires 3 variables: lo hi weight make"
        assert c["rpcap_y"]["error"] == \
            "you must specify four variables with twoway rpcap"

    def test_dash_ado_carries_the_fixture_literals(self):
        ado = ado_text()
        m = re.search(r"program define _dash_fold_mlabr\b(.*?)\nend\n", ado,
                      re.S)
        assert m, "_dash_fold_mlabr is not defined"
        body = m.group(1)
        assert '" requires 3 variables: "' in body
        assert '"you must specify four variables with twoway "' in body
        assert "exit 102" in body
        assert re.search(r"_dash_fold_mlabv [^\n]*\n\s*_dash_fold_mlabr ",
                         ado)
