"""Date literals in y options (WP-31 A8).

The defect: ``dash scatter mpg weight, ylabel(2000m1)`` was accepted where
twoway refuses it, "invalid label specifier, :  2000m1:", r(198), and
``yscale(range(2000m1))`` where twoway says "range() invalid -- invalid
numlist", r(121) (measured on StataNow 19.5, also on a %tm y variable:
test/fixtures/weight_operator_truth.json ``ydates``).  _dash_taxis_fold
refused the x forms only: its globals ``dash__tf_<key>`` carried no y key
and its refusal loop ran over the x options.

The Stata side is pinned by test/test_wp31_truth.cscript U07-6.
"""

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
_Y = ("ylabel", "ytick", "ymlabel", "ymtick", "ylabel2", "ytick2", "yscale",
      "yscale2")

with open(os.path.join(HERE, "fixtures", "weight_operator_truth.json"),
          encoding="utf-8") as _fh:
    _YD = json.load(_fh)["ydates"]


def _ado():
    with open(os.path.join(REPO, "dash.ado"), encoding="utf-8") as fh:
        return fh.read()


class TestYDateLiterals:
    def test_the_round_trip_lists(self):
        """Both dash__tf_ lists (out to _dash_taxis_fold and back) carry
        the eight y keys."""
        ado = _ado()
        lists = re.findall(r"foreach _tk in ((?:[^{]|\n)*?)\{\s*\n\s*mata: "
                           r"st_(?:global|local)\(\"(?:dash__tf_|g_)", ado)
        assert len(lists) == 2, lists
        for body in lists:
            words = body.replace("///", " ").split()
            for k in _Y:
                assert k in words, (k, words)

    def test_the_y_loop_exists(self):
        ado = _ado()
        fold = ado[ado.index("program define _dash_taxis_fold\n"):]
        fold = fold[:fold.index("\nend\n")]
        loop = ("foreach c in ylabel:1 ytick:1 ymlabel:1 ymtick:1 "
                "ylabel2:1 ytick2:1 yscale:3 yscale2:3 {")
        assert loop in fold
        body = fold[fold.index(loop):]
        body = body[:body.index("\n    }\n")]
        # twoway's words, as the fixture holds them.
        assert _YD["ylabel"]["text"] == "invalid label specifier, :  2000m1:"
        assert _YD["yscale"]["text"] == "range() invalid -- invalid numlist"
        assert ('display as error "%s"\n                exit 121' %
                _YD["yscale"]["text"]) in body
        assert ('_dash_say("err", "invalid label specifier, :  ", '
                'st_local("_xd_tok"), ":")') in body

    def test_twoway_refuses_every_form_but_a_number(self):
        """D-07.e: a %tm y variable does not make twoway read the date, so
        no y form is left open; ylabel(480) draws."""
        for k, rec in _YD.items():
            if k in ("ylabel_tfmt_lit", "ylabel_num"):
                assert rec["rc"] == 0, k
            else:
                assert rec["rc"] in (198, 121), k
