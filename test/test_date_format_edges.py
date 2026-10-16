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


#: The weekday calendar u46 of the measurement: 01jan2024 to 30jan2024
#: without weekends, %tb 0..21 (bcal describe), its %td days by dofb().
_U46_TD = [23376, 23377, 23378, 23379, 23380, 23383, 23384, 23385, 23386,
           23387, 23390, 23391, 23392, 23393, 23394, 23397, 23398, 23399,
           23400, 23401, 23404, 23405]
_U46 = {"min": 0, "td": _U46_TD}
#: (format, value, Stata's display text) -- measured, StataNow 19.5.
_TB_ROWS = [("%tbu46", 5, "08jan2024"), ("%tbu46", 0, "01jan2024"),
            ("%tbu46", 5.5, "08jan2024"), ("%tbu46", 21, "30jan2024"),
            ("%tbu46:CCYY-NN-DD", 5, "2024-01-08"),
            ("%tbu46", 22, "       22"), ("%tbu46", -5, "       -5")]


class TestBusinessCalendars:

    @pytest.mark.parametrize("fmt,value,want", _TB_ROWS)
    def test_tb_text(self, fmt, value, want):
        assert dr._dash_fmt(value, fmt, bcal=_U46) == want
        assert dr._dash_fmt_kind(fmt) == "t"

    @requires_node
    def test_tb_tooltip_js(self):
        got = run_js(dr._DASH_FMT_JS + "\nvar T = " + json.dumps(_U46)
                     + ";\nprocess.stdout.write(JSON.stringify("
                     + json.dumps([[f, v] for f, v, _w in _TB_ROWS])
                     + ".map(function (r) { return dash_fmt(r[1], r[0], "
                       "null, false, 'period', T); })));")
        assert got == [w for _f, _v, w in _TB_ROWS]

    def test_tb_is_a_numeric_axis_format(self):
        import pandas as pd
        df = pd.DataFrame({"bd": [0.0, 5.0, 21.0]})
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dates, numeric = dr._dash_load_columns(df, {"bd": "%tbu46"},
                                                   set())
        assert "bd" not in dates and numeric.get("bd") == "%tbu46"

    def test_tb_formatter_carries_the_calendar(self):
        cache = {}
        dr._dash_page_settings(None, cache, {"bcal": {"u46": _U46}})
        m = dr._dash_fmt_tick_formatter("%tbu46", "", "double", cache)
        assert m.args["bcal"] == _U46
        n = dr._dash_fmt_tick_formatter("%9.0g", "", "double", cache)
        assert "bcal" not in n.args

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_tb_ticks(self, mode):
        import test_mode_parity as tp
        spec = tp._spec([{"type": "scatter", "yvar": "mpg", "xvar": "rep",
                          "options": {}}],
                        {"formats": {"rep": "%tbu46"},
                         "bcal": {"u46": _U46}})
        if mode == "saved":
            r, _w = tp._standalone(spec)
            models = list(r._last_layout_root.references())
        else:
            doc, _w = tp._served(spec)
            models = [m for root in doc.roots for m in root.references()]
        fmts = [m for m in models
                if type(m).__name__ == "CustomJSTickFormatter"
                and m.args.get("fmt") == "%tbu46"]
        assert fmts and all(m.args.get("bcal") == _U46 for m in fmts)

    def test_the_calendar_is_read_at_registration(self):
        with open(os.path.join(_ROOT, "dash.ado"), encoding="utf-8") as fh:
            ado = fh.read()
        assert "program define _dash_bcal_table" in ado
        assert "bcal describe" in ado and "dofb(" in ado
