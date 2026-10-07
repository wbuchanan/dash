"""The Stata display-format writer and its JavaScript twin (WP-28 S04).

Both twins are held, row for row, to test/fixtures/format_truth.json --
what Stata's own ``display %fmt (value)`` printed, padding included --
written by scripts/extract_format_truth.do.  The fixture, not a derived
rule, is the arbiter.

While iterating run only this file (CLAUDE.md rule 11):
``python3 -m pytest test/test_display_format_writer.py -q``.
"""
import html
import json
import math
import os
import re
import sys
import time

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from js_runner import run_js, requires_node  # noqa: E402

FIXTURE = os.path.join(_ROOT, "test", "fixtures", "format_truth.json")
SCRIPT = os.path.join(_ROOT, "scripts", "extract_format_truth.do")


def _fixture():
    if not os.path.exists(FIXTURE):
        pytest.fail("task 04-03 must land first: "
                    "test/fixtures/format_truth.json is missing")
    with open(FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _is_extended_missing(raw):
    return raw.startswith(".") and raw != "." and not raw[1:2].isdigit()


def _numeric_rows(fx):
    """Every numeric row except .a: extended missing values are G12's,
    out of scope here (dash reads every missing value as ".")."""
    out = []
    for fmt, rec in fx["numeric_formats"].items():
        for v in rec["values"]:
            if _is_extended_missing(v["value"]):
                continue
            out.append((fmt, v["value"], v["storage"], v["display"]))
    return out


def _date_rows(fx):
    """Every date row Stata itself wrote (rc 0); %tdCCYY!c!!x is refused
    by Stata with r(120) and is recorded, not written."""
    out = []
    for fmt, rec in fx["date_formats"].items():
        for v in rec["values"]:
            if v["rc"] == 0:
                out.append((fmt, v["value"], v["display"]))
    return out


def _val(raw):
    return float("nan") if raw == "." else float(raw)


def test_the_fixture_is_present_and_large_enough():
    fx = _fixture()
    n_num = sum(len(v["values"]) for v in fx["numeric_formats"].values())
    n_date = sum(len(v["values"]) for v in fx["date_formats"].values())
    assert n_num >= 1000 and n_date >= 150
    assert fx["confirm"]["%21x"] == 0 and fx["confirm"]["%16H"] == 0
    assert len(fx["kpi"]) >= 100


def test_the_fixture_carries_the_provenance_stamp():
    meta = _fixture()["_meta"]
    for key in ("stata_version", "born_date", "dash_commit", "extracted"):
        assert isinstance(meta.get(key), str) and meta[key], key
    assert re.fullmatch(r"[0-9a-f]{40}", meta["dash_commit"])


def test_fixture_and_script_are_named():
    # Literal paths, for test_fixtures_are_committed.py.
    assert os.path.exists(os.path.join(_ROOT, "test/fixtures/format_truth.json"))
    assert os.path.exists(os.path.join(_ROOT, "scripts/extract_format_truth.do"))


class TestPythonWriter:

    def test_every_numeric_display_matches_stata_exactly(self):
        rows = _numeric_rows(_fixture())
        assert len(rows) >= 1000
        wrong = [(f, r, s, dr._dash_fmt(_val(r), f, storage=s), want)
                 for f, r, s, want in rows
                 if dr._dash_fmt(_val(r), f, storage=s) != want]
        assert not wrong, wrong[:20]

    def test_narrow_widths_1_to_7_follow_the_fixture(self):
        fx = _fixture()
        for fmt in ("%1.0f", "%2.0f", "%3.0g", "%4.0g", "%5.0g", "%6.0g",
                    "%7.0g"):
            vals = fx["numeric_formats"][fmt]["values"]
            assert len(vals) >= 10
            for v in vals:
                if _is_extended_missing(v["value"]):
                    continue
                got = dr._dash_fmt(_val(v["value"]), fmt, storage=v["storage"])
                assert got == v["display"], (fmt, v)

    def test_every_date_display_matches_stata_exactly(self):
        rows = _date_rows(_fixture())
        assert len(rows) >= 150
        wrong = [(f, r, dr._dash_fmt(_val(r), f), want)
                 for f, r, want in rows if dr._dash_fmt(_val(r), f) != want]
        assert not wrong, wrong[:20]

    def test_text_strips_and_missing_is_a_dot(self):
        assert dr._dash_fmt_text(float("nan"), "%9.2f") == "."
        assert dr._dash_fmt_text(None, "%td") == "."
        row = [v for v in _fixture()["numeric_formats"]["%10.0g"]["values"]
               if v["value"] == "6165.2567" and v["storage"] == "double"][0]
        assert dr._dash_fmt_text(6165.2567, "%10.0g") == row["display"].strip()

    def test_a_refused_or_unknown_format_is_written_in_9_0g(self):
        want = dr._dash_fmt_text(1.5, "%9.0g")
        for fmt in ("%21x", "%16H", "%9.999999999f", "bogus",
                    "%1" + "0" * 5000 + ".2f"):
            t0 = time.time()
            got = dr._dash_fmt_text(1.5, fmt)
            assert time.time() - t0 < 1 and len(got) <= 64
            assert got == want, fmt

    def test_the_html_escape_rule_the_twin_follows(self):
        s = '<a href="x">&\'</a>'
        assert html.escape(s, quote=True) == (
            "&lt;a href=&quot;x&quot;&gt;&amp;&#x27;&lt;/a&gt;")
        plain = "abc XYZ 123 ,.;:!?" * 11
        assert html.escape(plain, quote=True) == plain


class TestParser:

    @pytest.mark.parametrize("fmt,kind", [
        ("%9.2f", "f"), ("%12.0gc", "g"), ("%-12.3e", "e"), ("%9,2fc", "f"),
        ("%09.2f", "f"), ("%td", "t"), ("%tdCCYY-NN-DD", "t"),
        ("%21x", "x"), ("%16H", "H"), ("%16L", "H"), ("%12s", None),
        ("%9.2", None), ("%2046.2f", None), ("%9.30f", None),
        ("%٩.2f", None)])
    def test_kinds(self, fmt, kind):
        assert dr._dash_fmt_kind(fmt) == kind
        p = dr._dash_fmt_parse(fmt)
        if fmt == "%9,2fc":
            assert p["comma_dec"] and p["group"]
        if fmt == "%09.2f":
            assert p["zero"]
        if fmt == "%tdCCYY-NN-DD":
            assert p["tkind"] == "d" and p["picture"] == "CCYY-NN-DD"

    def test_refusal_messages(self):
        assert "%21x" in dr._dash_fmt_refusal("%21x")
        assert "hexadecimal" in dr._dash_fmt_refusal("%21x")
        assert "IEEE" in dr._dash_fmt_refusal("%16H")
        assert "not a display format" in dr._dash_fmt_refusal("%9.2")
        assert dr._dash_fmt_refusal("%9.2f") is None
        assert dr._dash_fmt_refusal("%tm") is None


def _ms_of_day(stata_day):
    return stata_day * 86_400_000 + dr._STATA_EPOCH_UNIX_MS


STATA_VALUE_CASES = [
    (_ms_of_day(15000), "td", 15000.0),
    # 978,393,600,000 ms is 2001-01-02 00:00 UTC:
    # (978393600000 + 315619200000) / 86400000 = 14977.0
    (978393600000, "td", 14977.0),
    (_ms_of_day(14610), "tm", 480.0),            # 01jan2000 -> 2000m1
    (_ms_of_day(14610 + 14), "tm", 480.0),       # mid-month floors
    (_ms_of_day(14610), "tq", 160.0),
    (_ms_of_day(14610), "th", 80.0),
    (_ms_of_day(14610), "ty", 2000.0),
    (_ms_of_day(14610), "tw", 2080.0),           # 1960w1 + 40 years
    (_ms_of_day(14975), "tw", 2131.0),           # 31dec2000: week 51, not 52
    (15000 + dr._STATA_EPOCH_UNIX_MS, "tc", 15000.0),
]


class TestStataValueOf:

    def test_each_kind(self):
        for ms, kind, want in STATA_VALUE_CASES:
            assert dr._dash_stata_value_of(ms, kind) == want, (ms, kind)
        for bad in (None, float("nan"), "x"):
            assert dr._dash_stata_value_of(bad, "td") is None
        assert dr._dash_stata_value_of(_ms_of_day(2936550), "td") is None


class TestExport:

    def test_the_writer_sends_storage_types(self, tmp_path):
        from test_string_value_export import FakeSfi
        fake = FakeSfi({"x": [1.0, 2.0], "y": [3.0, None], "s": ["a", "b"]},
                       {"x": "float", "y": "double", "s": "str8"})
        path = str(tmp_path / "d.json")
        assert dr._dash_write_stata_data(path, "x y s", sfi=fake) == ""
        doc = json.load(open(path))
        assert doc["storageTypes"] == {"x": "float", "y": "double", "s": "str8"}


class TestLoaders:

    def test_both_loaders_carry_g_and_e_formats(self):
        import pandas as pd
        df = pd.DataFrame({"p": [1.0], "e": [2.0], "f": [3.0], "d": [0.0]})
        _, nf = dr._dash_load_columns(
            df, {"p": "%8.0gc", "e": "%10.3e", "f": "%9.2f", "d": "%td"}, [])
        assert nf == {"p": "%8.0gc", "e": "%10.3e", "f": "%9.2f"}

    def test_a_variables_own_x_format_falls_back_with_one_note(self):
        import pandas as pd
        dr._DASH_NOTED.clear() if hasattr(dr, "_DASH_NOTED") else None
        df = pd.DataFrame({"h": [1.0]})
        with pytest.warns(UserWarning) as rec:
            _, nf = dr._dash_load_columns(df, {"h": "%21x"}, [])
            dr._dash_load_columns(df.copy(), {"h": "%21x"}, [])
        assert nf == {"h": "%9.0g"}
        msgs = [str(w.message) for w in rec if "%21x" in str(w.message)]
        assert len(msgs) == 1 and "'h'" in msgs[0]


class TestTheGuard:

    # Inverted by WP-28 section 11 (GAPS2 E1), which removed the guard: a
    # card on a %g variable is written in that variable's own format.
    def test_a_card_on_a_g_variable_uses_its_own_format(self):
        assert dr._dash_effective_kpi_fmt({}, "price", {"price": "%8.0gc"}) == "%8.0gc"
        assert dr._dash_effective_kpi_fmt({}, "price", {"price": "%9.2f"}) == "%9.2f"


class TestConsumers:

    def test_format_stata_numeric_delegates(self):
        # GAPS2 E3/G6, WP-28 S12: _format_stata_numeric was deleted; its
        # callers use _dash_fmt_text, whose missing value is ".".
        assert dr._dash_fmt_text(1234.5678, "%9.3e") == "1.23e+03"
        assert dr._dash_fmt_text(float("nan"), "%9.2f") == "."
        assert dr._dash_fmt_text(1000.03, "%9,2fc") == "1.000,03"


class TestDashAdo:

    def _branch(self):
        text = open(os.path.join(_ROOT, "dash.ado"), encoding="utf-8").read()
        m = re.search(r'regexm\(scalar\(`V\'\), "(\^%-\?\[0-9\]\*\[xHL\]\$)"\)',
                      text)
        assert m, "dash.ado's format branch holds no %x/%H/%L refusal"
        return m.group(1)

    def test_the_ado_refuses_what_the_renderer_refuses(self):
        rx = re.compile(self._branch())
        conf = _fixture()["confirm"]
        for fmt, rc in conf.items():
            if rc != 0:
                continue
            refused = dr._dash_fmt_kind(fmt) in ("x", "H")
            assert bool(rx.search(fmt)) == refused, fmt
        for fmt in ("%9.2f", "%10.0g", "%9,2fc", "%tm", "%-12.3e"):
            assert not rx.search(fmt)

    def test_the_help_names_the_refusal(self):
        text = open(os.path.join(_ROOT, "dash.sthlp"), encoding="utf-8").read()
        i = text.index("%21x")
        near = text[max(0, i - 600): i + 600]
        assert "r(198)" in near


# ---------------------------------------------------------------------------
# The JavaScript twin, under node
# ---------------------------------------------------------------------------

def _js(harness):
    return run_js(dr._DASH_FMT_JS + "\n" + harness)


@requires_node
class TestJavaScriptTwin:

    def test_every_fixture_row_matches_under_node(self):
        fx = _fixture()
        rows = [[f, r, s, w] for f, r, s, w in _numeric_rows(fx)]
        rows += [[f, r, None, w] for f, r, w in _date_rows(fx)]
        out = _js("var rows = %s; var bad = [];"
                  "rows.forEach(function (r) {"
                  " var v = r[1] === '.' ? NaN : Number(r[1]);"
                  " var g = dash_fmt(v, r[0], r[2]);"
                  " if (g !== r[3]) bad.push([r[0], r[1], r[2], g, r[3]]); });"
                  "process.stdout.write(JSON.stringify(bad));" % json.dumps(rows))
        assert not out, out[:20]

    def test_the_twins_agree_where_the_languages_disagree(self):
        vals = [1e-7, 5e-7, 1e-6, 1.5e-5, 1e-4, 1e15, 1e16,
                9999999999999998.0, 1e20, 1e21, -0.0]
        fmts = ["%9.0g", "%12.0g", "%20.0g", "%9.2f", "%12,2gc", "%10.3e"]
        cases = [[v, f] for v in vals for f in fmts]
        got = _js("var c = %s; process.stdout.write(JSON.stringify("
                  "c.map(function (x) { return dash_fmt(x[0], x[1]); })));"
                  % json.dumps(cases))
        want = [dr._dash_fmt(v, f) for v, f in cases]
        assert got == want
        f32 = [0.1, 0.3, 1e-7, 16777217, 3.4e38]
        got = _js("process.stdout.write(JSON.stringify(%s.map(dash_float32_text)));"
                  % json.dumps(f32))
        assert got == [dr._dash_float32_text(v) for v in f32]

    def test_stata_value_of_agrees_with_python(self):
        cases = [[ms, k] for ms, k, _ in STATA_VALUE_CASES]
        got = _js("process.stdout.write(JSON.stringify(%s.map(function (c) {"
                  " return dash_stata_value_of(c[0], c[1]); })));"
                  % json.dumps(cases))
        assert got == [w for _, _, w in STATA_VALUE_CASES]
        assert _js("process.stdout.write(JSON.stringify("
                   "dash_stata_value_of(978393600000, 'td')));") == 14977

    def test_years_below_1000_are_not_remapped(self):
        assert _js("process.stdout.write(JSON.stringify("
                   "dash_fmt(-679350, '%td')));") == "01jan0100"

    def test_dash_html_escape_escapes_the_five_characters(self):
        s = '<a href="x">&\'</a>'
        plain = "abc XYZ 123 ,.;:!?"
        got = _js("process.stdout.write(JSON.stringify([dash_html_escape(%s),"
                  " dash_html_escape(%s), dash_html_escape(null),"
                  " dash_html_escape(undefined), dash_html_escape(5)]));"
                  % (json.dumps(s), json.dumps(plain)))
        assert got == [html.escape(s, quote=True), plain, "", "", "5"]

    def test_every_shipped_script_defines_dash_fmt_once(self):
        for code in (dr._FILTER_JS, dr._DASH_CSV_SAVED_JS,
                     dr._DASH_CSV_SERVED_JS):
            assert code.count("function dash_fmt(") == 1
        import inspect
        brush = inspect.getsource(dr.DashRenderer)
        assert "_DASH_FMT_JS + _helpers + _pctl + _BRUSH_JS" in brush
        served = inspect.getsource(dr.ServerAppBuilder)
        assert '"_DASH_FMT_JS"' in served

    def test_bounds_under_node(self):
        t0 = time.time()
        got = _js("process.stdout.write(JSON.stringify([dash_fmt(1.5, '%%9.999999999f'),"
                  " dash_fmt(1.5, %s)]));" % json.dumps("%1" + "0" * 5000 + ".2f"))
        assert time.time() - t0 < 5
        assert all(len(g) <= 64 for g in got)


# ---------------------------------------------------------------------------
# WP-30 P1.5.7: narrow explicit-digit g, e and f formats.  Measured
# 03oct2026 (StataNow 19.5): over 3,234 display rows the writer differed
# from Stata on 457 g, 440 e and 46 f rows.  The rows below are Stata's
# own text; format_truth.json's narrow_formats holds the full grid.
# ---------------------------------------------------------------------------

_NARROW_ROWS = [
    (0.0001, "%6.4g", " 1.0e-04"),
    (12345, "%6.2e", " 1.2e+04"),
    (1.23, "%10.1g", "       1.2"),
    (0.123, "%3.1g", " .12"),
    (0.00001, "%12.2g", "      .00001"),
    (999.96, "%10.3g", "   1.0e+03"),
    (1234567, "%3.1f", " 1.2e+06"),
    (0.000123, "%7.4g", " .00012"),
    (0, "%3.2g", "   0"),
    (0.000012345, "%10.4g", " .00001234"),
]


def _narrow_rows(fx):
    out = []
    for fmt, rec in fx.get("narrow_formats", {}).items():
        for v in rec["values"]:
            if v["rc"] == 0:
                out.append((fmt, v["value"], v["display"]))
    return out


class TestNarrowExplicitDigits:

    def test_the_measured_rows_in_python(self):
        wrong = [(v, f, dr._dash_fmt(v, f), want) for v, f, want in _NARROW_ROWS
                 if dr._dash_fmt(v, f) != want]
        assert not wrong, wrong

    @requires_node
    def test_the_measured_rows_under_node(self):
        rows = [[v, f, w] for v, f, w in _NARROW_ROWS]
        out = _js("var rows = %s; var bad = [];"
                  "rows.forEach(function (r) {"
                  " var g = dash_fmt(r[0], r[1]);"
                  " if (g !== r[2]) bad.push([r[0], r[1], g, r[2]]); });"
                  "process.stdout.write(JSON.stringify(bad));" % json.dumps(rows))
        assert not out, out

    def test_sci_decimals_keep_their_floor(self):
        assert dr._dash_sci_decimals(6, 2, 2) == 1
        assert dr._dash_sci_decimals(6, 2, 4, sig_digits=True) == 1
        assert dr._dash_sci_decimals(9, 3, 4, sig_digits=True) == 1
        assert dr._dash_sci_decimals(12, 2, 0) == 5


class TestNarrowFixture:

    def test_every_row_in_python(self):
        rows = _narrow_rows(_fixture())
        assert len(rows) >= 5600
        wrong = [(f, r, dr._dash_fmt(_val(r), f), want) for f, r, want in rows
                 if dr._dash_fmt(_val(r), f) != want]
        assert not wrong, (len(wrong), wrong[:20])

    @requires_node
    def test_every_row_under_node(self):
        rows = [[f, r, w] for f, r, w in _narrow_rows(_fixture())]
        assert len(rows) >= 5600
        out = _js("var rows = %s; var bad = [];"
                  "rows.forEach(function (r) {"
                  " var g = dash_fmt(Number(r[1]), r[0]);"
                  " if (g !== r[2]) bad.push([r[0], r[1], g, r[2]]); });"
                  "process.stdout.write(JSON.stringify(bad));" % json.dumps(rows))
        assert not out, out[:2000]
