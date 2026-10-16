"""%d, %tb and xvarformat(bogus) as twoway reads them (WP-31 G7).

Measured (StataNow 19.5): ``display %d 20000`` is 04oct2014 and
``%dCCYY-NN-DD`` 2014-10-04 -- %d is %td's old name -- where dash wrote
%9.0g with a note; ``twoway scatter mpg weight, xvarformat(bogus)`` prints
"bogus not found" and draws, rc 0, where dash's note was its own sentence.
"""
import json
import os
import sys
import warnings

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import dash_render as dr  # noqa: E402
from js_runner import requires_node, run_js  # noqa: E402

_ROOT = os.path.join(os.path.dirname(__file__), "..")

#: (format, Stata value, what Stata displays) -- measured.
_D_ROWS = [("%d", 20000, "04oct2014"),
           ("%dCCYY-NN-DD", 20000, "2014-10-04"),
           ("%td", 20000, "04oct2014")]


class TestFormats:

    @pytest.mark.parametrize("fmt,value,want", _D_ROWS)
    def test_percent_d_is_td(self, fmt, value, want):
        assert dr._dash_fmt(value, fmt) == want
        assert dr._dash_fmt_kind(fmt) == "t"
        assert dr._stata_date_kind(fmt) == "td"

    @requires_node
    def test_percent_d_js(self):
        got = run_js(dr._DASH_FMT_JS + "\nprocess.stdout.write(JSON.stringify("
                     + json.dumps([[f, v] for f, v, _w in _D_ROWS])
                     + ".map(function (r) { return dash_fmt(r[1], r[0]); })));")
        assert got == [w for _f, _v, w in _D_ROWS]

    def test_percent_d_is_a_date_at_registration(self):
        with open(os.path.join(_ROOT, "dash.ado"), encoding="utf-8") as fh:
            ado = fh.read()
        assert '"^%-?(t[cCdhmqwy]|d)"' in ado

    def test_xvarformat_bogus_words(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            got = dr._dash_varformat_writable("bogus", True, "x")
        assert got == "%9.0g"
        assert [str(m.message) for m in w] == ["bogus not found"]
