"""test_date_range.py -- a date past 2262 no longer empties its variable (WP-25).

Measured 24sep2026 under the interpreter Stata renders every dashboard with
-- ``c(python_exec)``, /opt/anaconda3/bin/python3: pandas 2.3.3, numpy
2.3.5, bokeh 3.8.0 -- and under the development one (Homebrew python3:
pandas 3.0.1, numpy 2.4.3, bokeh 3.9.0):

* ``_stata_dates_to_datetime`` converted a column with one pandas call into
  NANOsecond datetime64, whose range is 1677-09-21 to 2262-04-11.  Under
  pandas 2.3 one value past it -- %td 1000000 (27nov4697) in
  fixtures/date_truth.json, or a 31dec9999 "no end date" placeholder --
  made ``pd.to_timedelta`` raise, and the handler emptied EVERY date of the
  column: the axis, the tooltips, the filters, the KPIs, the marker labels,
  the panel titles and the download showed nothing, in both render modes,
  and the warning said every value was out of range.  Under pandas 3.0 the
  %tw/%tm/%tq/%th/%ty path raised an uncaught pandas AssertionError instead.
  Dates are now converted element by element into MILLISECOND datetime64,
  under either pandas: every date Stata shows converts, and a value Stata
  itself prints as a bare number is missing alone, and counted.
* Every layer computed from a date column -- fits, smoothers, densities,
  histograms, areas, spikes, droplines and range layers -- read it with
  ``np.asarray(col, dtype=float)``: in nanoseconds under pandas 2.3 and
  microseconds under 3.0, a million or a thousand times off the axis the
  scatter beside it is drawn on in milliseconds, and a missing date at
  -9.2e18.  pcarrow and pcbarrow refused a date coordinate outright; a
  bar over a date was 0.8 ms wide; rscatter's, pcscatter's and the
  jitter's date columns carried a missing date into JSON as NaN, which
  failed the page (pandas 2.3), and under pandas 3.0 a hover() or mlabel()
  date past 2262 raised OverflowError out of Bokeh and lost the page.
* The served download and the saved page's snapshot wrote a date through
  ``Timestamp.value``, nanoseconds, which raises past 2262; a KPI's date
  was read with ``pd.Timestamp(<float>, unit="ms")``, which pandas 2.3
  refuses past 2262, and the card showed the bare number.

Every expected date is Stata's, measured with the console binary
(the console binary, ``stata-mp -b``) and cited beside it.  Epoch milliseconds are
days after 01jan1970 times 86,400,000; 01jan1960, Stata's day 0, is
-3,653 days (so %td 14977 is (14977 - 3653) * 86400000 = 978393600000).
"""
import base64
import gzip
import json
import math
import os
import sys
import time
import tracemalloc
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.embed import json_item
from bokeh.models import (Arrow, DateRangeSlider, DateSlider, DatetimeAxis,
                          GlyphRenderer,
                          HoverTool, LabelSet, LinearColorMapper, VBar)

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import make_data_json, exec_app  # noqa: E402

_ATTACH = "if __name__ != '__main__':\n    make_document(curdoc())"

# `display %tdCCYY-NN-DD <n>' (24sep2026): 14977 2001-01-02, 14978
# 2001-01-03, 14979 2001-01-04, 14980 2001-01-05, 2936549 9999-12-31.
_DATES = [14977.0, 14978.0, 14979.0, 14980.0, 2936549.0]
_ISO = ["2001-01-02", "2001-01-03", "2001-01-04", "2001-01-05", "9999-12-31"]
_MS = [978393600000.0, 978480000000.0, 978566400000.0, 978652800000.0,
       253402214400000.0]
# `display %td 2936550' prints 2936550: one day past Stata's last date is no
# date at all (24sep2026).
_PAST = 2936550.0


from conftest import render_models  # noqa: E402

# WP-47 MS-15: the marker labels are Text glyph renderers; a reader of the
# LabelSets they were reads them as conftest.MarkerLabels, beside any
# other LabelSet.
from bokeh.models import LabelSet  # noqa: E402
from conftest import MarkerLabels, mlabel_sets  # noqa: E402
_MLS = (LabelSet, MarkerLabels)


def _mls_center(fig):
    return list(fig.center) + mlabel_sets(fig)


def _mls_select(doc):
    return list(doc.select({"type": LabelSet})) + mlabel_sets(doc)


def _mls_all(objs):
    objs = list(objs)
    return objs + mlabel_sets(objs)



def _iso(ts):
    # Not strftime("%Y"): glibc writes the year 100 as 100, macOS as 0100
    # (GitHub's runner, 15nov2026).
    if pd.isna(ts):
        return None
    ts = pd.Timestamp(ts)
    return f"{ts.year:04d}-{ts.month:02d}-{ts.day:02d}"


def _iso_ms(ts):
    ts = pd.Timestamp(ts)
    return (f"{_iso(ts)}T{ts.hour:02d}:{ts.minute:02d}:{ts.second:02d}."
            f"{ts.microsecond // 1000:03d}")


def _outside(msgs):
    """The conversion's out-of-range notes among *msgs* -- "N value(s) of a
    %td variable fall outside ...", in its old wording and its new."""
    return [m for m in msgs if "fall outside" in m]


def _convert(values, kind):
    """(result, [range warnings]) from the conversion."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        got = dr._stata_dates_to_datetime(pd.Series(values), kind)
    return got, _outside(str(w.message) for w in caught)


def _count(msgs):
    """The number a range warning gives, or 0 for none."""
    assert len(msgs) <= 1, msgs
    return int(msgs[0].split()[1]) if msgs else 0


# ---------------------------------------------------------------------------
# Both render modes from one spec
# ---------------------------------------------------------------------------

def _spec(plots, formats=None, filters=None, kpis=None, graph_options=None,
          csv=False):
    go = {"name": "g1"}
    go.update(graph_options or {})
    bo = {"layout": "auto", "link": "", "filter": "", "title": "",
          "subtitle": "", "tabs": "", "filter_position": "top",
          "level": "95", "formats": dict(formats or {"date": "%td"}),
          "registry": " ".join(["g1"] + [k["name"] for k in kpis or []])}
    if filters:
        bo["filters"] = list(filters)
    if csv:
        bo["csv"] = "1"
    return {"graphs": [{"plots": plots, "graph_options": go,
                        "if_expr": "", "in_expr": ""}],
            "kpis": list(kpis or []), "build_options": bo}


def _kpi(name, stat, var="date"):
    return {"name": name, "stat": stat, "var": var, "fmt": "", "title": name,
            "subtitle": "", "color": "", "bgcolor": "", "update": "filter",
            "if_expr": "", "in_expr": ""}


def _filter(ftype, var="date"):
    return {"varname": var, "type": ftype, "exclude": [], "label": ""}


def _write(tmp_path, spec, data):
    """*data* is a DataFrame, or a ready data-JSON dict."""
    if isinstance(data, pd.DataFrame):
        data = make_data_json(data)
    sp = os.path.join(str(tmp_path), "spec.json")
    dp = os.path.join(str(tmp_path), "data.json")
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    with open(dp, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    return sp, dp


def _saved(tmp_path, spec, data):
    """(renderer, warnings) from the saved-dashboard renderer, rendered."""
    sp, dp = _write(tmp_path, spec, data)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r = dr.DashRenderer(sp, dp, os.path.join(str(tmp_path), "o.html"))
        render_models(r)
    return r, [str(w.message) for w in caught]


def _served(tmp_path, spec, data):
    """(document, warnings) from one session of the generated app."""
    sp, dp = _write(tmp_path, spec, data)
    ap = os.path.join(str(tmp_path), "app.py")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        dr.ServerAppBuilder(sp, dp).build(ap)
        with open(ap, encoding="utf-8") as fh:
            src = fh.read()
        assert _ATTACH in src
        ns = {"__name__": "date_range_app"}
        exec_app(src.replace(_ATTACH, "pass"), ap, ns)
        doc = Document()
        ns["make_document"](doc)
        # Everything in it must be writable as the page's JSON.
        doc.to_json()
    return doc, [str(w.message) for w in caught]


def _frame(values=_DATES):
    return pd.DataFrame({"date": list(values),
                         "close": [float(i + 1) for i in range(len(values))]})


def _document_columns(model, name):
    """Column *name* of every ColumnDataSource as Bokeh writes the model
    into a page -- ``json_item``, the same serialiser ``file_html`` and a
    server session use -- decoded to numbers."""
    found = []

    def _decode(v):
        if isinstance(v, dict) and v.get("type") == "ndarray":
            arr = v["array"]
            if isinstance(arr, dict) and arr.get("type") == "bytes":
                raw = base64.b64decode(arr["data"])
                if raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                return np.frombuffer(raw, dtype=v["dtype"]).tolist()
            return list(arr)
        return v

    def _walk(o):
        if isinstance(o, dict):
            if o.get("name") == "ColumnDataSource":
                data = o.get("attributes", {}).get("data", {})
                if isinstance(data, dict) and data.get("type") == "map":
                    for k, v in data.get("entries", []):
                        if k == name:
                            found.append(_decode(v))
            for v in o.values():
                _walk(v)
        elif isinstance(o, list):
            for v in o:
                _walk(v)

    _walk(json.loads(json.dumps(json_item(model))))
    return found


def _drawn_date(fig, var="date"):
    """The date column of the glyph that draws *var*, as ISO dates."""
    cols = [r.data_source.data[var] for r in fig.renderers
            if isinstance(r, GlyphRenderer) and var in r.data_source.data]
    assert cols, f"no glyph draws {var}"
    return [_iso(v) for v in cols[0]]


# ===========================================================================
# 1. The conversion: element by element, in milliseconds, Stata's range
# ===========================================================================

# Stata's own range, measured 24sep2026 (`display %<kind> <n>' and
# `display %tdCCYY-NN-DD dof<k>(<n>)'): the first and the last value each
# format shows as a date, and that date.  One past either end Stata prints
# as the bare number (`display %tw 418080' is 4.2e+05, `display %ty 10000'
# 1.0e+04, `display %tc 253717920000000' 2.53718e+14).
_LIMITS = [
    ("td", -679350, "0100-01-01", 2936549, "9999-12-31"),
    ("tc", -58695840000000, "0100-01-01", 253717919999999, "9999-12-31"),
    ("tw", -96720, "0100-01-01", 418079, "9999-12-24"),
    ("tm", -22320, "0100-01-01", 96479, "9999-12-01"),
    ("tq", -7440, "0100-01-01", 32159, "9999-10-01"),
    ("th", -3720, "0100-01-01", 16079, "9999-07-01"),
    ("ty", 100, "0100-01-01", 9999, "9999-01-01"),
]


class TestTheConversionHoldsStatasWholeRange:

    def test_the_reported_column_converts_whole_and_warns_of_nothing(self):
        """The twelve %td values of date_truth.json, 27nov4697 among them:
        pandas 2.3 emptied all twelve and said all twelve were out of
        range (the failing test_dates.py case, measured 24sep2026)."""
        with open(os.path.join(_HERE, "fixtures", "date_truth.json")) as fh:
            rec = json.load(fh)["date_formats"]["%td"]["values"]
        vals = [float(v["value"]) for v in rec]
        got, msgs = _convert(vals, "td")
        assert [_iso(v) for v in got] == [v["iso"] for v in rec]
        assert msgs == []

    def test_a_31dec9999_placeholder_converts_beside_ordinary_dates(self):
        got, msgs = _convert(_DATES[:2] + [math.nan] + _DATES[4:], "td")
        assert [_iso(v) for v in got] == _ISO[:2] + [None] + _ISO[4:]
        # A missing value was never a date, and is not counted.
        assert msgs == []

    def test_a_value_past_statas_range_is_missing_alone_and_counted(self):
        # `display %td -679351' prints -679351, `display %td 2936550'
        # 2936550: neither is a date to Stata (24sep2026).
        got, msgs = _convert([14977.0, _PAST, -679351.0, 14978.0], "td")
        assert [_iso(v) for v in got] == [
            "2001-01-02", None, None, "2001-01-03"]
        assert _count(msgs) == 2
        assert "01jan0100 to 31dec9999" in msgs[0]

    @pytest.mark.parametrize("kind,lo,lo_iso,hi,hi_iso", _LIMITS)
    def test_the_first_and_last_date_convert_and_one_past_is_missing(
            self, kind, lo, lo_iso, hi, hi_iso):
        got, msgs = _convert([lo - 1.0, float(lo), float(hi), hi + 1.0],
                             kind)
        assert [_iso(v) for v in got] == [None, lo_iso, hi_iso, None]
        assert _count(msgs) == 2

    def test_a_clock_value_keeps_its_millisecond_at_both_ends(self):
        # `display %tcCCYY-NN-DD!THH:MM:SS.sss' of the first and last
        # values (24sep2026).
        got, _ = _convert([-58695840000000.0, 253717919999999.0], "tc")
        assert [_iso_ms(v) for v in got] == [
            "0100-01-01T00:00:00.000", "9999-12-31T23:59:59.999"]

    @pytest.mark.parametrize("kind", sorted(dr._STATA_DATE_KINDS))
    def test_every_kind_is_held_in_milliseconds_under_either_pandas(
            self, kind):
        """datetime64[ns] under pandas 2.3 and [us] under 3.0 for %td and
        %tc before: one unit, whichever pandas renders."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            got = dr._stata_dates_to_datetime(
                pd.Series([1960.0 if kind == "ty" else 0.0]), kind)
        assert str(got.dtype) == "datetime64[ms]"

    @pytest.mark.parametrize("kind,value,want", [
        # As Stata shows each (24sep2026): a %td fraction is its day
        # (`display %tdCCYY-NN-DD 14977.9' 2001-01-02, `-0.5' 1959-12-31,
        # `2936549.9' 9999-12-31), a %tc fraction its millisecond, floored
        # (`1.9999' .001, `-0.5' 23:59:59.999, `-1.5' 23:59:59.998), and a
        # period's fraction its period (`display %tw 51.5' 1960w52 =
        # 1960-12-23, `-0.5' 1959w52 = 1959-12-24, `%tm 745.5' 2022m2,
        # `-0.5' 1959m12, `%ty 1998.7' 1998).
        ("td", 14977.9, "2001-01-02"),
        ("td", -0.5, "1959-12-31"),
        ("td", 2936549.9, "9999-12-31"),
        ("tc", 1.9999, "1960-01-01T00:00:00.001"),
        ("tc", -0.5, "1959-12-31T23:59:59.999"),
        ("tc", -1.5, "1959-12-31T23:59:59.998"),
        ("tw", 51.5, "1960-12-23"),
        ("tw", -0.5, "1959-12-24"),
        ("tm", 745.5, "2022-02-01"),
        ("tm", -0.5, "1959-12-01"),
        ("ty", 1998.7, "1998-01-01"),
    ])
    def test_a_fraction_is_floored_as_stata_shows_it(self, kind, value, want):
        got, _ = _convert([value], kind)
        mine = (_iso_ms(got.iloc[0]) if "T" in want else _iso(got.iloc[0]))
        assert mine == want

    def test_a_fraction_below_the_first_day_is_no_date(self):
        # `display %tdCCYY-NN-DD -679350.5' prints -679350.5 (24sep2026).
        got, msgs = _convert([-679350.5], "td")
        assert pd.isna(got.iloc[0]) and _count(msgs) == 1

    def test_a_td_fraction_keeps_its_place_on_the_axis(self):
        """The day is Stata's; the time of day is the value's position."""
        got, _ = _convert([14977.5], "td")
        assert got.iloc[0] == pd.Timestamp("2001-01-02 12:00:00")

    @pytest.mark.parametrize("value,want", [
        # `display mdy(1,1,1000)' -350632, `mdy(9,21,1677)' -103099,
        # `mdy(4,11,2262)' 110404, `mdy(4,12,2262)' 110405 and
        # `mdy(11,27,4697)' 1000000; `display %tdCCYY-NN-DD' of
        # mdy(10,4,1582)+1 = -137784 is 1582-10-05 (no Julian switch), of
        # mdy(2,28,1000)+1 = -350573 1000-03-01 and of mdy(2,28,1700)+1 =
        # -94903 1700-03-01 (neither a leap year), of mdy(2,28,2000)+1 =
        # 14669 2000-02-29 (24sep2026).  Stata's calendar is proleptic
        # Gregorian, as numpy's is.
        (-350632.0, "1000-01-01"), (-103099.0, "1677-09-21"),
        (110404.0, "2262-04-11"), (110405.0, "2262-04-12"),
        (1000000.0, "4697-11-27"), (-137784.0, "1582-10-05"),
        (-350573.0, "1000-03-01"), (-94903.0, "1700-03-01"),
        (14669.0, "2000-02-29"),
    ])
    def test_statas_calendar(self, value, want):
        got, msgs = _convert([value], "td")
        assert _iso(got.iloc[0]) == want and msgs == []

    def test_the_result_has_a_fresh_index(self):
        got, _ = _convert(pd.Series([14977.0, 14978.0], index=[7, 3]), "td")
        assert list(got.index) == [0, 1]

    def test_an_unknown_kind_is_every_value_missing_and_no_warning(self):
        got, msgs = _convert([14977.0], "tx")
        assert pd.isna(got.iloc[0]) and msgs == []
        assert str(got.dtype) == "datetime64[ms]"


# ===========================================================================
# 2. Hostile values (CLAUDE.md rule 18): overflow, and exhaustion
# ===========================================================================

_GOOD = {"td": 14977.0, "tc": 0.0, "tC": 0.0, "tw": 0.0, "tm": 0.0,
         "tq": 0.0, "th": 0.0, "ty": 1960.0}


class TestHostileDateValues:

    @pytest.mark.parametrize("kind", sorted(dr._STATA_DATE_KINDS))
    def test_non_finite_and_huge_values_are_missing_and_counted(self, kind):
        """An infinity, NaN, 1e300 and the largest doubles: each is missing
        on its own and the one date beside them converts.  NaN is a missing
        value, not an unrepresentable one, so the count is six, not seven."""
        vals = [math.inf, -math.inf, math.nan, 1e300, -1e300,
                1.7976931348623157e308, -1.7976931348623157e308, _GOOD[kind]]
        got, msgs = _convert(vals, kind)
        assert got.isna().tolist() == [True] * 7 + [False]
        assert _count(msgs) == 6

    def test_an_integer_too_large_for_a_double_is_counted_not_raised(self):
        """pd.to_numeric raises for a whole column on one such integer,
        errors="coerce" or not (measured under both pandas, 24sep2026)."""
        got, msgs = _convert(
            pd.Series([10 ** 400, -(10 ** 400), 14977, None, "x"],
                      dtype=object), "td")
        assert [_iso(v) for v in got] == [None, None, "2001-01-02", None,
                                          None]
        assert _count(msgs) == 2

    @pytest.mark.parametrize("kind,lo,hi", [
        ("td", -1e6, 3e6), ("tc", -6e13, 3e14), ("tw", -1e5, 5e5),
        ("tm", -3e4, 1e5), ("ty", 0.0, 11000.0)])
    def test_two_million_values_convert_in_bounded_time_and_memory(
            self, kind, lo, hi):
        """Linear in the column, with no per-value Python: measured
        24sep2026 at under 0.1 s and 39 to 90 bytes per value (peak, all
        numpy temporaries) under both interpreters for 2,000,000 values,
        a tenth of them non-finite, 1e300 or beyond Stata's range."""
        n = 2_000_000
        vals = np.random.default_rng(0).uniform(lo, hi, n)
        vals[::997], vals[1::997] = math.inf, -math.inf
        vals[2::997], vals[3::997] = math.nan, 1e300
        series = pd.Series(vals)
        tracemalloc.start()
        try:
            t0 = time.perf_counter()
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                got = dr._stata_dates_to_datetime(series, kind)
            elapsed = time.perf_counter() - t0
            _cur, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        assert len(got) == n
        assert elapsed < 10.0, f"{elapsed:.2f}s for {n:,} values"
        assert peak < 200 * n, f"{peak / n:.0f} bytes per value"

    def test_a_hostile_date_in_the_data_file_is_one_missing_point(
            self, tmp_path):
        """Through the real input, the data JSON: Infinity, -Infinity, NaN
        and 1e400 (which json reads as an infinity) are what a hand-made
        file can hold that Stata cannot, and a markup string is text where
        a date belongs.  Each is missing alone; the markup reaches no model
        of either mode's document."""
        bad = "<img src=x onerror=alert(1)>"
        data = make_data_json(_frame([14977.0 + i for i in range(8)]))
        rows = data["StataJSON"]["values"]
        rows[1]["date"], rows[2]["date"] = math.inf, -math.inf
        rows[3]["date"], rows[4]["date"] = 7.77e77, 1e300
        rows[5]["date"], rows[6]["date"] = math.nan, bad
        # json writes an infinity as Infinity and NaN as NaN, and reads
        # 1e400 back as an infinity.
        text = json.dumps(data).replace("7.77e+77", "1e400")
        spec = _spec([{"type": "scatter", "yvar": "close", "xvar": "date",
                       "options": {"mlabel": "date"}}],
                     filters=[_filter("range")], csv=True)
        sp, dp = _write(tmp_path, spec, {})
        with open(dp, "w", encoding="utf-8") as fh:
            fh.write(text)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            r = dr.DashRenderer(sp, dp, os.path.join(str(tmp_path), "o.html"))
            html = r.render()
        # `display %tdCCYY-NN-DD 14977' 2001-01-02, 14984 2001-01-09.  The
        # dataset holds each hostile value as a missing date, alone, and the
        # scatter draws the two dates, as twoway leaves out a missing x.
        assert [_iso(v) for v in r.df["date"]] == [
            "2001-01-02", None, None, None, None, None, None, "2001-01-09"]
        assert _drawn_date(r.figures["g1"]) == ["2001-01-02", "2001-01-09"]
        counts = _outside(str(w.message) for w in caught)
        # 1e300 alone: the data file's reader (_dash_read_data_json, S3
        # batch) reads Infinity, -Infinity and 1e400 as missing, as Stata,
        # which holds no infinity, would hold them, so only 1e300 reaches
        # the date conversion as a number outside Stata's range.  NaN and
        # the text are missing values, as text in a numeric column is.
        assert _count(counts) == 1
        assert "<html" in html.lower() and bad not in html
        doc, _w = _served(tmp_path, spec, json.loads(text))
        assert bad not in json.dumps(doc.to_json(), default=str)


# ===========================================================================
# 3. The saved page, over a variable ending in a 31dec9999 placeholder
# ===========================================================================

_LABELLED = [{"type": "scatter", "yvar": "close", "xvar": "date",
              "options": {"mlabel": "date"}}]
# The labels dash writes for _DATES: Stata's own %td text (02jan2001 ...
# 31dec9999).  GAPS2 E3/G6, WP-28 S12: was "02 Jan 2001" (dash's own
# day-month-year text, not Stata's display).
_LABELS = [dr._dash_fmt_text(d, "%td") for d in _DATES]


def _td(v):
    """Stata's %td text of day *v* ("." for missing), the oracle."""
    return dr._dash_fmt_text(v, "%td")


def _card(text, name):
    import re
    m = re.search(r'id="kpi_val_%s"[^>]*>([^<]*)<' % name, text or "")
    return m.group(1) if m else None


def _plain_with_dates(v):
    """test_filter_exclude's JSON reader, taught a datetime64 the way Bokeh
    writes one -- epoch milliseconds, NaT as null -- so the node harness
    can carry a date column into the page's callback."""
    import test_filter_exclude as tfe
    if isinstance(v, np.datetime64):
        return None if np.isnat(v) else float(
            v.astype("datetime64[ms]").astype(np.int64))
    return tfe._plain_orig(v)


class TestTheSavedPageHoldsThePlaceholder:

    def test_the_glyph_draws_every_date(self, tmp_path):
        r, _w = _saved(tmp_path, _spec(_LABELLED), _frame())
        assert _drawn_date(r.figures["g1"]) == _ISO

    def test_the_page_carries_every_date_in_epoch_milliseconds(self, tmp_path):
        """What Bokeh writes into the page for the column, decoded."""
        r, _w = _saved(tmp_path, _spec(_LABELLED), _frame())
        cols = _document_columns(r.figures["g1"], "date")
        assert cols and all(c == _MS for c in cols), cols

    def test_no_value_is_reported_out_of_range(self, tmp_path):
        _r, w = _saved(tmp_path, _spec(_LABELLED), _frame())
        assert _outside(w) == []

    def test_the_axis_and_tooltip_read_the_column_as_dates(self, tmp_path):
        from bokeh.models import DatetimeAxis
        r, _w = _saved(tmp_path, _spec(_LABELLED), _frame())
        fig = r.figures["g1"]
        assert any(isinstance(a, DatetimeAxis) for a in fig.xaxis)
        hover = [t for t in fig.tools if isinstance(t, HoverTool)]
        # GAPS2 E3/G6, WP-28 S12: a Stata-format CustomJSHover, not Bokeh's
        # "datetime"; it writes Stata's %td text of each date.
        from bokeh.models import CustomJSHover
        from test_display_format_sites import js_texts
        fm = [f for h in hover for k, f in dict(h.formatters or {}).items()
              if k == "@{date}"]
        assert fm and isinstance(fm[0], CustomJSHover)
        assert js_texts(fm[0], _MS, "value") == _LABELS

    def test_a_range_filter_spans_every_date(self, tmp_path):
        r, _w = _saved(tmp_path, _spec(_LABELLED, filters=[_filter("range")]),
                       _frame())
        (w,) = [x for x in r.filter_widgets if isinstance(x, DateRangeSlider)]
        assert (w.start, w.end) == (_MS[0], _MS[-1])
        assert tuple(w.value) == (_MS[0], _MS[-1])

    def test_a_slider_filter_spans_every_date(self, tmp_path):
        r, _w = _saved(tmp_path, _spec(_LABELLED, filters=[_filter("slider")]),
                       _frame())
        (w,) = [x for x in r.filter_widgets if isinstance(x, DateSlider)]
        assert (w.start, w.end, w.value) == (_MS[0], _MS[-1], _MS[0])

    def test_the_filter_snapshot_holds_every_date(self, tmp_path):
        r, _w = _saved(tmp_path, _spec(_LABELLED, filters=[_filter("range")]),
                       _frame())
        snap = r.filter_callbacks[0].args["orig_source"].data["date"]
        assert list(snap) == _MS

    def test_a_kpi_reads_the_placeholder_as_its_date(self, tmp_path):
        kpis = [_kpi("k1", "max"), _kpi("k2", "min")]
        r, _w = _saved(tmp_path, _spec(_LABELLED, kpis=kpis), _frame())
        assert _card(r.kpi_divs["k1"].text, "k1") == "31dec9999"  # Stata %td (WP-28 section 11, GAPS2 E1)
        assert _card(r.kpi_divs["k2"].text, "k2") == "02jan2001"

    def test_the_filter_callback_recomputes_a_kpi_across_the_placeholder(
            self, tmp_path, monkeypatch):
        """The saved page's own callback, run under node: the slider moved
        to 02jan2001..05jan2001 leaves max(date) at 05 Jan 2001, and at its
        full extent the card is 31 Dec 9999 again."""
        import test_filter_exclude as tfe
        import test_filter_widget_data as tfw
        monkeypatch.setattr(tfe, "_plain_orig", tfe._plain, raising=False)
        monkeypatch.setattr(tfe, "_plain", _plain_with_dates)
        spec = _spec(_LABELLED, filters=[_filter("range")],
                     kpis=[_kpi("k1", "max")])
        r, _w = _saved(tmp_path, spec, _frame())
        (w,), (cb,) = r.filter_widgets, r.filter_callbacks
        card = r.kpi_divs["k1"].id
        w.value = (_MS[0], _MS[3])
        assert _card(tfw._div_texts_after(cb.args, cb.code)[card],
                     "k1") == "05jan2001"  # Stata %td (WP-28 section 11, E1)
        w.value = (_MS[0], _MS[4])
        assert _card(tfw._div_texts_after(cb.args, cb.code)[card],
                     "k1") == "31dec9999"

    def test_the_marker_labels_write_the_placeholder_as_a_date(self, tmp_path):
        # GAPS2 E3/G6, WP-28 S12: _LABELS is Stata's %td text now.
        r, _w = _saved(tmp_path, _spec(_LABELLED), _frame())
        (ls,) = [x for x in _mls_center(r.figures["g1"]) if isinstance(x, _MLS)]
        assert list(ls.source.data[ls.text]) == _LABELS

    def test_a_by_panel_of_the_placeholder_is_titled_with_its_date(
            self, tmp_path):
        df = pd.DataFrame({"date": [14977.0, 14977.0, 2936549.0, 2936549.0],
                           "close": [1.0, 2.0, 3.0, 4.0],
                           "x": [1.0, 2.0, 3.0, 4.0]})
        spec = _spec([{"type": "scatter", "yvar": "close", "xvar": "x",
                       "options": {}}], graph_options={"by": "date"})
        r, _w = _saved(tmp_path, spec, df)
        # Flipped (WP-30 P1.15a): the date is the panel's label row.
        from by_panel_probe import panel_label
        assert [panel_label(r.figures[k]) for k in ("g1__by__0", "g1__by__1")
                ] == ["14977", "2936549"]  # Flipped (WP-41 BY-16): twoway writes the number; a date past 2262 is no "(missing)"

    def test_the_download_writes_the_placeholder(self, tmp_path):
        from test_export import _saved_file
        spec = _spec(_LABELLED, filters=[_filter("range")], csv=True)
        r, _w = _saved(tmp_path, spec, _frame())
        lines = _saved_file(r, {}).split("\r\n")
        assert lines[0] == "date,close"
        assert [ln.split(",")[0] for ln in lines[1:6]] == _ISO

    @pytest.mark.parametrize("ptype", ["spike", "bar", "rcap"])
    def test_a_hover_variable_carries_every_date(self, tmp_path, ptype):
        """A layer that rebuilds its source carries hover(date) along;
        before, pandas 2.3 carried four missing dates and pandas 3.0 lost
        the whole page to an OverflowError (measured 24sep2026)."""
        p = ({"type": ptype, "yvar1": "close", "yvar2": "x", "xvar": "x",
              "options": {}} if ptype == "rcap" else
             {"type": ptype, "yvar": "close", "xvar": "x", "options": {}})
        df = _frame(_DATES[:2] + [_DATES[4], math.nan])
        df["x"] = [1.0, 2.0, 3.0, 4.0]
        r, _w = _saved(tmp_path, _spec([p], graph_options={"hover": "date"}),
                       df)
        fig = r.figures["g1"]
        (col,) = _document_columns(fig, "date")
        assert col[:3] == [_MS[0], _MS[1], _MS[4]]
        assert col[3] is None or math.isnan(col[3])
        hover = [t for t in fig.tools if isinstance(t, HoverTool)]
        # GAPS2 E3/G6, WP-28 S12: a Stata-format hover, not {%F}.
        assert ("date", "@{date}{custom}") in list(hover[0].tooltips)

    def test_a_value_past_statas_range_is_one_missing_point(self, tmp_path):
        # GAPS2 E3/G6, WP-28 S12: _LABELS is Stata's %td text now.
        spec = _spec(_LABELLED, filters=[_filter("range")])
        r, w = _saved(tmp_path, spec, _frame(_DATES[:4] + [_PAST]))
        assert [_iso(v) for v in r.df["date"]] == _ISO[:4] + [None]
        # The four dates are drawn and labelled; the value Stata prints as
        # a number is a missing x, which twoway leaves out.
        assert _drawn_date(r.figures["g1"]) == _ISO[:4]
        (ls,) = [x for x in _mls_center(r.figures["g1"]) if isinstance(x, _MLS)]
        assert list(ls.source.data[ls.text]) == _LABELS[:4]
        snap = r.filter_callbacks[0].args["orig_source"].data["date"]
        assert list(snap) == _MS[:4] + [None]
        assert _count(_outside(w)) == 1


# ===========================================================================
# 4. The served app: what it converts, over the same variable
# ===========================================================================
#
# The served frame is loaded by the saved loader's own column reader
# (_dash_load_columns, WP-27), so it holds the same datetime64[ms] dates; its
# figures, cards and widgets are held to the saved page's in
# test_served_dates.py.

class TestTheServedAppWritesThePlaceholder:

    def test_the_marker_labels_write_the_placeholder_as_a_date(self, tmp_path):
        # GAPS2 E3/G6, WP-28 S12: _LABELS is Stata's %td text now.
        doc, _w = _served(tmp_path, _spec(_LABELLED), _frame())
        (ls,) = list(_mls_select(doc))
        assert list(ls.source.data[ls.text]) == _LABELS

    def test_a_by_panel_of_the_placeholder_is_titled_with_its_date(
            self, tmp_path):
        from bokeh.models import Plot
        df = pd.DataFrame({"date": [14977.0, 14977.0, 2936549.0, 2936549.0],
                           "close": [1.0, 2.0, 3.0, 4.0],
                           "x": [1.0, 2.0, 3.0, 4.0]})
        spec = _spec([{"type": "scatter", "yvar": "close", "xvar": "x",
                       "options": {}}], graph_options={"by": "date"})
        doc, _w = _served(tmp_path, spec, df)
        # Flipped (WP-30 P1.15a): the date is the panel's label row.
        from by_panel_probe import panel_label
        titles = sorted(panel_label(p) for p in doc.select({"type": Plot})
                        if panel_label(p))
        # Flipped (WP-41 BY-16): twoway writes the number; a date past 2262
        # is no "(missing)".
        assert titles == ["14977", "2936549"]

    def test_the_download_writes_the_placeholder(self, tmp_path):
        """Under pandas 3 the click raised OverflowError out of
        Timestamp.value; under 2.3 every date downloaded empty."""
        from test_export import _csv_source, _served_file
        spec = _spec(_LABELLED, filters=[_filter("range", "close")], csv=True)
        doc, _w = _served(tmp_path, spec, _frame())
        lines = _served_file(doc, {}).split("\r\n")
        assert list(_csv_source(doc).data["date"]) == _MS
        assert [ln.split(",")[0] for ln in lines[1:6]] == _ISO

    def test_a_value_past_statas_range_downloads_empty_alone(self, tmp_path):
        from test_export import _csv_source, _served_file
        spec = _spec(_LABELLED, csv=True)
        doc, _w = _served(tmp_path, spec, _frame(_DATES[:4] + [_PAST]))
        lines = _served_file(doc, {}).split("\r\n")
        assert list(_csv_source(doc).data["date"]) == _MS[:4] + [None]
        assert [ln.split(",")[0] for ln in lines[1:6]] == _ISO[:4] + [""]


# ===========================================================================
# 5. Every layer computed from a date column lands on the date axis
# ===========================================================================

# Twelve dates thirty days apart: `display %tdCCYY-NN-DD 14977' 2001-01-02
# and `14977+330' 2001-11-28 (24sep2026).
_SPREAD = [14977.0 + 30 * i for i in range(12)]
_LO_MS, _HI_MS = 978393600000.0, 978393600000.0 + 330 * 86400000.0
_HALF_GAP = 15 * 86400000.0     # a cap or a bar reaches half a gap past

_RANGE = {"rarea", "rbar", "rspike", "rcap", "rline", "rconnected",
          "rcapsym", "rscatter", "tsrline"}
_PC = {"pcspike", "pcarrow", "pcbarrow", "pcscatter", "pccapsym"}
# WP-29 P0.8 (section 05): every type that reads a date column is here.
# lpoly and lpolyci were left out because they drew nothing on these twelve
# 30-day rows, with the default bandwidth and with any bwidth() read in
# milliseconds; with bwidth(60) read in days (_plot_for) they draw, at the
# dates on the date axis.  Their default bandwidth on these rows is section
# 11's to measure, so this pins only the explicit one (A10).
_COMPUTED = sorted(
    t for t in dr._dash_plot_type_names()
    if t not in ("scatteri", "pci", "pcarrowi", "function"))


def _plot_for(ptype, options=None):
    o = dict(options or {})
    if ptype in ("lpoly", "lpolyci"):
        # WP-29 P0.8 (section 05): sixty days, read in the date's units.
        o.setdefault("bwidth", "60")
    if ptype in ("histogram", "kdensity"):
        return {"type": ptype, "var": "date", "options": o}
    if ptype in _RANGE:
        return {"type": ptype, "yvar1": "lo", "yvar2": "hi", "xvar": "date",
                "options": o}
    if ptype in dr._DASH_CONTOUR_TYPES:
        # WP-31 B4b: z y x, the date on x.
        return {"type": ptype, "zvar": "hi", "yvar": "lo", "xvar": "date",
                "options": o}
    if ptype in dr._DASH_RANGEPT_TYPES:
        # WP-31 B1: the range and its marker (y3).
        return {"type": ptype, "yvar1": "lo", "yvar2": "hi", "yvar": "hi",
                "xvar": "date", "options": o}
    if ptype in _PC:
        return {"type": ptype, "y1var": "lo", "x1var": "date", "y2var": "hi",
                "x2var": "date", "options": o}
    return {"type": ptype, "yvar": "lo", "xvar": "date", "options": o}


def _bounds_for(ptype):
    """The x extent a lone *ptype* layer over ``_spread_frame``'s dates may
    reach: epoch ms on its date axis, or -- for a type twoway labels with
    the date's numbers (WP-44 AX-18) -- Stata's days on a numeric axis."""
    # Flipped (WP-44 AX-18): epoch ms for lfit, kdensity and the like was
    # wrong because twoway labels their lone axis with the date's numbers,
    # so their layers are drawn at Stata's day numbers.
    if ptype in dr._DASH_NUMBER_FIRST_TYPES:
        return tuple(dr._dash_unix_ms_to_unit(v, "d") for v in (
            _LO_MS - _HALF_GAP, _HI_MS + _HALF_GAP))
    return (_LO_MS - _HALF_GAP, _HI_MS + _HALF_GAP)


def _spread_frame(hole=False):
    vals = list(_SPREAD)
    if hole:
        vals[3] = math.nan
    return pd.DataFrame({"date": vals,
                         "lo": [float(i) for i in range(12)],
                         "hi": [float(i) + 2.0 for i in range(12)]})


def _x_extents(fig):
    """(glyph, attribute, lowest, highest) of every x each renderer draws,
    read as the page reads it: a date in epoch milliseconds."""
    out = []
    for r in fig.renderers:
        g = getattr(r, "glyph", None)
        if g is None:
            # A contour renderer draws through its children; its extent
            # rides on the layer's invisible corner scatter (WP-31 B4b).
            continue
        data = r.data_source.data
        for attr in ("x", "left", "right", "x0", "x1"):
            if attr not in g.properties():
                continue
            spec = getattr(g, attr)
            field = (spec if isinstance(spec, str)
                     else getattr(spec, "field", None) if not isinstance(
                         spec, dict) else spec.get("field"))
            if not field or field not in data:
                continue
            col = data[field]
            vals = (pd.to_datetime(pd.Series(list(col))) if not isinstance(
                col, np.ndarray) and len(col) and hasattr(col[0], "year")
                else col)
            ms = dr._dash_float_values(vals)
            ms = ms[~np.isnan(ms)]
            if ms.size:
                out.append((type(g).__name__, attr, float(ms.min()),
                            float(ms.max())))
    for a in fig.center:
        if isinstance(a, Arrow):
            # ONE annotation over the shaft's source (BUGS.md, 24sep2026):
            # its x ends are columns, read as the page reads them.
            ends = []
            for spec in (a.x_start, a.x_end):
                f = getattr(spec, "field", None)
                col = (list(a.source.data[f]) if f else [spec])
                vals = (pd.to_datetime(pd.Series(col)) if len(col)
                        and hasattr(col[0], "year") else pd.Series(col))
                ms = dr._dash_float_values(vals)
                ends.extend(ms[~np.isnan(ms)].tolist())
            if ends:
                out.append(("Arrow", "x", float(min(ends)),
                            float(max(ends))))
    return out


class TestAComputedLayerIsDrawnOnTheDateAxis:

    @pytest.mark.parametrize("hole", [False, True],
                             ids=["dates", "a-missing-date"])
    @pytest.mark.parametrize("ptype", _COMPUTED)
    def test_every_x_it_draws_lies_among_the_dates(self, tmp_path, ptype,
                                                   hole):
        """Nanoseconds under pandas 2.3 (9.8e17) and microseconds under 3.0
        (9.8e14) where the axis is milliseconds (9.8e11); a missing date
        drew to -9.2e18; pcarrow and pcbarrow raised (24sep2026)."""
        opts = {"mlabel": "date"} if ptype in ("rscatter", "pcscatter") \
            else {}
        r, _w = _saved(tmp_path, _spec([_plot_for(ptype, opts)]),
                       _spread_frame(hole))
        ext = _x_extents(r.figures["g1"])
        assert ext, "the layer drew nothing"
        lo, hi = _bounds_for(ptype)
        wrong = [e for e in ext if not (lo <= e[2] and e[3] <= hi)]
        assert not wrong, wrong

    def test_a_bar_over_dates_is_as_wide_as_their_spacing(self, tmp_path):
        """One day, in milliseconds (twoway's bar_size 1 on a %td axis,
        fixture widths.bar_td_daily); it was 0.8 ms.

        Flipped (WP-30 P1.17a): 0.8 of the thirty-day gap was wrong because
        twoway draws a bar one x unit wide and caps as long as a marker of its msize (P1.17a).
        """
        r, _w = _saved(tmp_path, _spec([_plot_for("bar")]), _spread_frame())
        widths = [x.glyph.width for x in r.figures["g1"].renderers
                  if isinstance(x.glyph, VBar)]
        assert widths == [86400000.0]

    def test_a_dropline_labels_a_date_with_its_date(self, tmp_path):
        """Its own date column was replaced by floats, read as Stata days,
        and every label was "."."""
        r, _w = _saved(tmp_path, _spec([_plot_for("dropline",
                                                  {"mlabel": "date"})]),
                       _spread_frame())
        (ls,) = [x for x in _mls_center(r.figures["g1"]) if isinstance(x, _MLS)]
        labels = list(ls.source.data[ls.text])
        # `display %td 14977' 02jan2001, `display %td 14977+330' 28nov2001.
        # GAPS2 E3/G6, WP-28 S12: Stata's text, 02jan2001 .. 28nov2001.
        assert labels[0] == _td(14977.0) and labels[-1] == _td(14977.0 + 330)
        assert "." not in labels

    def test_a_jittered_date_with_a_missing_one_stays_on_the_axis(
            self, tmp_path):
        spec = _spec([_plot_for("scatter", {"jitter": "5",
                                            "jitterseed": "1"})])
        r, _w = _saved(tmp_path, spec, _spread_frame(hole=True))
        # G1 (WP-28): the jitter columns are named under the __dash prefix.
        cols = [np.asarray(x.data_source.data[dr._DASH_JITTER_X], dtype=float)
                for x in r.figures["g1"].renderers
                if dr._DASH_JITTER_X in x.data_source.data]
        assert cols
        span = _HI_MS - _LO_MS
        finite = cols[0][np.isfinite(cols[0])]
        assert finite.min() >= _LO_MS - 0.05 * span
        assert finite.max() <= _HI_MS + 0.05 * span

    # A date LABEL beside numeric coordinates: the placeholder and a missing
    # date ride along with drawn points.  `display %td 14977' 02jan2001,
    # `display %td 2936549' 31dec9999 (24sep2026).
    _LABEL_DATES = [14977.0, 2936549.0, math.nan, 14978.0]

    def _labelled(self, tmp_path, plot):
        df = pd.DataFrame({"date": self._LABEL_DATES,
                           "lo": [1.0, 2.0, 3.0, 4.0],
                           "hi": [2.0, 3.0, 4.0, 5.0]})
        r, _w = _saved(tmp_path, _spec([plot]), df)
        return [list(x.source.data[x.text]) for x in _mls_center(r.figures["g1"])
                if isinstance(x, _MLS)]

    def test_rscatter_labels_a_missing_and_a_far_date(self, tmp_path):
        """Both ends labelled; a missing date in its label list failed the
        page's JSON (a bare NaN)."""
        (labels,) = self._labelled(tmp_path, {
            "type": "rscatter", "yvar1": "lo", "yvar2": "hi", "xvar": "lo",
            "options": {"mlabel": "date"}})
        # GAPS2 E3/G6, WP-28 S12: Stata's %td text.
        assert labels == [_td(v) for v in self._LABEL_DATES] * 2

    def test_pcscatter_labels_a_missing_and_a_far_date(self, tmp_path):
        """The first point labelled; a list of Timestamps raised in Bokeh
        past 2262 (pandas 3) and a missing one failed the JSON (2.3)."""
        (labels,) = self._labelled(tmp_path, {
            "type": "pcscatter", "y1var": "lo", "x1var": "hi", "y2var": "hi",
            "x2var": "lo", "options": {"mlabel": "date"}})
        # GAPS2 E3/G6, WP-28 S12: Stata's %td text.
        assert labels[:4] == [_td(v) for v in self._LABEL_DATES]

    @pytest.mark.parametrize("ptype", ["pcarrow", "pcbarrow", "pccapsym"])
    def test_a_pc_arrow_labels_a_missing_and_a_far_date(self, tmp_path,
                                                         ptype):
        (labels,) = self._labelled(tmp_path, {
            "type": ptype, "y1var": "lo", "x1var": "hi", "y2var": "hi",
            "x2var": "lo", "options": {"mlabel": "date"}})
        # GAPS2 E3/G6, WP-28 S12: Stata's %td text.
        assert labels[:4] == [_td(v) for v in self._LABEL_DATES]

    def test_a_jittered_layer_carries_a_date_label_with_a_missing_one(
            self, tmp_path):
        """The jitter source copied every column into a list, and a missing
        date in one failed the page's JSON."""
        (labels,) = self._labelled(tmp_path, {
            "type": "scatter", "yvar": "lo", "xvar": "hi",
            "options": {"jitter": "5", "jitterseed": "1", "mlabel": "date"}})
        # GAPS2 E3/G6, WP-28 S12: Stata's %td text.
        assert labels == [_td(v) for v in self._LABEL_DATES]

    def test_a_date_colour_scale_runs_between_its_first_and_last_date(
            self, tmp_path):
        df = pd.DataFrame({"date": _SPREAD,
                           "lo": [float(i) for i in range(12)],
                           "hi": [float(i) for i in range(12)]})
        spec = _spec([{"type": "scatter", "yvar": "lo", "xvar": "hi",
                       "options": {"colorvar": "date"}}])
        r, _w = _saved(tmp_path, spec, df)
        maps = []
        for x in r.figures["g1"].renderers:
            fc = getattr(x.glyph, "fill_color", None)
            tr = (fc.get("transform") if isinstance(fc, dict)
                  else getattr(fc, "transform", None))
            if isinstance(tr, LinearColorMapper):
                maps.append((tr.low, tr.high))
        # Flipped (WP-42 CV-8): the continuous key was a 256-step gradient
        # from the first date to the last; twoway bins at its z ticks
        # (CV-8), so the stepped mapper reaches one tick step past them --
        # still in epoch milliseconds, within a few spans of the dates.
        [(lo, hi)] = maps
        assert lo <= _LO_MS and hi >= _HI_MS
        assert hi - lo <= 4 * (_HI_MS - _LO_MS)

    def test_xlabel_minmax_ticks_the_first_and_last_date(self, tmp_path):
        spec = _spec([_plot_for("scatter")],
                     graph_options={"xlabel": "minmax"})
        r, _w = _saved(tmp_path, spec, _spread_frame(hole=True))
        ticks = [getattr(a.ticker, "ticks", None) for a in r.figures["g1"].xaxis]
        assert ticks == [[_LO_MS, _HI_MS]]

    def test_a_date_on_a_second_axis_is_ranged_in_milliseconds(
            self, tmp_path):
        spec = _spec([{"type": "scatter", "yvar": "lo", "xvar": "hi",
                       "options": {}},
                      {"type": "line", "yvar": "date", "xvar": "hi",
                       "options": {"yaxis": "2"}}])
        r, _w = _saved(tmp_path, spec, _spread_frame(hole=True))
        fig = r.figures["g1"]
        (y2,) = fig.extra_y_ranges.values()
        (ax,) = [a for a in fig.right if a.y_range_name != "default"]
        # The hull of the data and its ticks (WP-30 P1.3a), in milliseconds,
        # with twoway's margin either side.  Flipped (WP-30 P1.23a): a
        # second axis of dates is a DatetimeAxis that keeps Bokeh's date
        # ticker, as the first axis does (S44 gives it twoway's), so the
        # hull is the data's alone; it read a numeric axis's fixed ticks.
        assert isinstance(ax, DatetimeAxis), type(ax).__name__
        ticks = list(getattr(ax.ticker, "ticks", None) or [])
        lo = min([_LO_MS] + ticks[:1])
        hi = max([_HI_MS] + ticks[-1:])
        assert lo - 0.1 * (hi - lo) <= y2.start <= _LO_MS
        assert _HI_MS <= y2.end <= hi + 0.1 * (hi - lo)


# ===========================================================================
# 6. The helpers the dates pass through
# ===========================================================================

class TestTheDateHelpers:

    def test_the_float_reader_reads_a_date_in_milliseconds(self):
        for unit in ("ns", "us", "ms", "s"):
            arr = np.array(["2001-01-02", "NaT"], dtype=f"datetime64[{unit}]")
            got = dr._dash_float_values(arr)
            assert got[0] == 978393600000.0 and math.isnan(got[1]), unit

    def test_the_float_reader_reads_a_far_date_from_a_series(self):
        s = dr._stata_dates_to_datetime(pd.Series(_DATES), "td")
        assert dr._dash_float_values(s).tolist() == _MS

    def test_the_float_reader_leaves_every_other_column_as_it_was(self):
        assert dr._dash_float_values([1, None, 2.5]).tolist()[::2] == [
            1.0, 2.5]
        assert math.isnan(dr._dash_float_values([1, None, 2.5])[1])
        with pytest.raises((TypeError, ValueError)):
            dr._dash_float_values(["a", "b"])
        got = dr._dash_float_values(["a", "3"], coerce=True)
        assert math.isnan(got[0]) and got[1] == 3.0

    def test_the_float_reader_survives_a_ragged_column(self):
        got = dr._dash_float_values([[1, 2], [3]], coerce=True)
        assert len(got) == 2 and np.isnan(got).all()

    @pytest.mark.parametrize("value", [
        pd.Timestamp("9999-12-31").as_unit("ms"),
        np.datetime64("9999-12-31", "ms"),
        pd.Timestamp("9999-12-31").as_unit("us")])
    def test_a_json_value_of_the_placeholder_is_its_milliseconds(self, value):
        """Timestamp.value is nanoseconds and raised OverflowError."""
        assert dr._dash_json_value(value) == 253402214400000.0

    def test_a_json_value_floors_to_the_millisecond_as_before(self):
        assert dr._dash_json_value(
            pd.Timestamp("1959-12-31 23:59:59.9995")) == -315619200001.0
        assert dr._dash_json_value(pd.Timestamp("2001-01-02")) == _MS[0]

    @pytest.mark.parametrize("value,kind,want", [
        # A KPI's statistic reaches the writer as epoch milliseconds;
        # pandas 2.3 refused the float past 2262.  Expected text is Stata's
        # own `display %td`/`%ty`, measured 30sep2026: 2936549 -> 31dec9999,
        # -679350 -> 01jan0100, 100 -> 0100.
        (253402214400000.0, "td", "31dec9999"),
        (np.float64(253402214400000.0), "td", "31dec9999"),
        (np.int64(978393600000), "td", "02jan2001"),
        (-59011459200000.0, "td", "01jan0100"),
        (-59011459200000.0, "ty", "0100"),
        (float("nan"), "td", "."),
        (float("inf"), "td", "."),
    ])
    def test_the_date_writer(self, value, kind, want):
        # GAPS2 E3: dates are written through the one Stata writer; the
        # fixed-picture helper this used to test (_format_date_value_
        # standalone) was removed once nothing called it.
        sv = dr._dash_stata_value_of(value, kind)
        assert dr._dash_fmt_text(sv, "%" + kind) == want

    def test_a_kpi_sum_of_dates_neither_wraps_nor_names_the_wrong_epoch(
            self):
        """40,000 dates in 9999 sum past int64's 9.2e18; as int64 the sum
        wrapped silently.  WP-29 P0.20 (section 05): the sum is of the
        Stata values, days since 01jan1960, as summarize reports it (it
        was epoch milliseconds since 01jan1970), and still never wraps."""
        col = pd.Series(np.full(40_000, np.datetime64("9999-12-31", "ms")))
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            vals = dr._dash_kpi_column(col, "sum", "date", "td")
        total = dr.DashRenderer._kpi_statistic(vals, "sum")
        assert total == pytest.approx(40_000 * 2936549.0, rel=1e-12)
        assert any("days since 01jan1960" in str(w.message)
                   for w in caught)
        assert dr.DashRenderer._kpi_statistic(vals, "max") == 2936549.0

    def test_a_date_that_arrives_as_text_is_held_in_milliseconds(
            self, tmp_path):
        """The legacy transport (jsonio's own "02jan2001") lands in the one
        unit too; pandas parses it to nanoseconds under 2.3."""
        data = make_data_json(pd.DataFrame({"date": ["02jan2001",
                                                      "03jan2001"],
                                            "close": [1.0, 2.0]}))
        sp, dp = _write(tmp_path, _spec([]), data)
        r = dr.DashRenderer(sp, dp)
        r._load_data()
        assert str(r.df["date"].dtype) == "datetime64[ms]"
        assert [_iso(v) for v in r.df["date"]] == _ISO[:2]

    def test_the_page_callback_writes_a_kpi_year_in_four_digits(self):
        """The first render writes 01 Jan 0100; the callback wrote a
        filtered card's year with getUTCFullYear(), 100."""
        # WP-28 section 11 (GAPS2 E1): the card is Stata's display of its
        # %t picture, written by dash_fmt_text; it read 01 Jan 0100,
        # 0100, Jan 0100 and 01 Jan 0100 00:00:00.
        js = dr._FILTER_JS
        from test_export import _run_js
        start = js.index("        let text;")
        end = js.index("        // Rebuild the complete Div HTML", start)
        body = js[start:end]
        got = _run_js(
            dr._DASH_FMT_JS +
            "const out = {};\n"
            "for (const kind of ['td', 'ty', 'tm', 'tc']) {\n"
            "  const k = {datekind: kind, fmt: '%' + kind};\n"
            # WP-29 P0.20 (section 05): the statistic reaches the card as
            # its Stata value, 01jan0100 in each kind; it was epoch ms.
            "  const result = {td: -679350, ty: 100, tm: -22320,"
            " tc: -58695840000000}[kind];\n"
            + body +
            "  out[kind] = text;\n}\n"
            "process.stdout.write(JSON.stringify(out));\n")
        assert got == {"td": "01jan0100", "ty": "0100", "tm": "0100m1",
                       "tc": "01jan0100 00:00:00"}


# ---------------------------------------------------------------------------
# WP-29 P0.16: a date colorvar() under a layer's own if
# ---------------------------------------------------------------------------

def _ms_of(td):
    """A %td day as the page holds it: epoch milliseconds."""
    return (td - 3653.0) * 86400000.0


class TestADateColorvarUnderALayersIf:
    """The colour key of a %td colorvar() is drawn from the layer's own
    rows, its mapper in epoch milliseconds, its text in Stata days, in both modes -- a served frame's date
    column is datetime64, which the domain reads on the column itself."""

    _PLOT = {"type": "scatter", "yvar": "lo", "xvar": "hi",
             "options": {"colorvar": "date"}, "if_expr": "lo >= 6"}

    def _root(self, tmp_path, mode, extra=None):
        plot = dict(self._PLOT,
                    options=dict(self._PLOT["options"], **(extra or {})))
        spec = _spec([plot])
        if mode == "saved":
            r, _w = _saved(tmp_path, spec, _spread_frame())
            return r._last_layout_root
        doc, _w = _served(tmp_path, spec, _spread_frame())
        return doc

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_the_key_spans_the_layers_dates(self, tmp_path, mode):
        import colour_bins as cb
        bars = cb.colour_bars(self._root(tmp_path, mode))
        # Flipped (WP-42 CV-8): the continuous key was a 256-step gradient
        # over the layer's dates; twoway bins at its z ticks (CV-8): the
        # stepped bar holds the layer's dates, not the graph's first.
        [(lo, hi)] = bars
        lo6, hi11 = _ms_of(_SPREAD[6]), _ms_of(_SPREAD[11])
        assert lo <= lo6 and hi >= hi11 and lo > _ms_of(_SPREAD[0])
        assert hi - lo <= 4 * (hi11 - lo6)

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_colorlevels_cut_the_layers_dates(self, tmp_path, mode):
        import colour_bins as cb
        root = self._root(tmp_path, mode, {"colorlevels": "3"})
        (rend,) = cb.colour_renderers(root)
        bounds = sorted({b for lo_hi in cb.interval_bounds(
            cb.colour_mapper(rend).factors) for b in lo_hi if b is not None})
        lo, hi = _SPREAD[6], _SPREAD[11]
        want = [lo + k * (hi - lo) / 3 for k in (1, 2)]
        assert len(bounds) == 4
        # WP-30 P1.23b: bounds in epoch milliseconds were wrong because
        # twoway cuts and writes a date key in its Stata days (15,098
        # 15,219), in %8.0gc.
        for got, w in zip(bounds[1:3], want):
            assert abs(got - w) <= 0.5, (bounds, want)
        assert abs(bounds[0] - lo) <= 0.5 and abs(bounds[-1] - hi) <= 0.5
