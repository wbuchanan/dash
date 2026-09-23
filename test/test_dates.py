"""test_dates.py — S08: Stata display formats, dates and the transport bug.

The section's premise turned out to be wrong in a way that matters.  It said a
``%td`` variable "arrives as a raw Stata SIF integer and gets a linear axis
reading 14.0k".  Measured, it does not arrive as a number at all: ``jsonio``
renders every ``%t*`` variable through its display format and emits a JSON
STRING -- ``sp500``'s ``date`` arrives as ``"02jan2001"`` -- while still
reporting ``variableIsString = false`` for it.

``_load_data`` then runs ``pd.to_numeric(errors="coerce")`` over it, so every
date becomes NaN, every row is dropped, and ``dash line close date`` produces
a dashboard containing **zero data points** and returns rc 0.  Verified end to
end against a real Stata run: the embedded Bokeh document has
``"shape":[0]`` for index, date and close.

A second, independent transport defect turned up alongside it: ``_load_data``
reads ``variableTypeIsString``, and real ``jsonio`` emits ``variableIsString``.
The key dash looks for is never present in production, so its string-column
detection has never run outside the test suite -- which fabricates the wrong
key in ``conftest.make_data_json`` and so could not see it.

Expected values come from ``test/fixtures/date_truth.json``, measured in Stata.
"""
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render
from dash_render import DashRenderer

_FIXTURE = os.path.join(_HERE, "fixtures", "date_truth.json")

pytestmark = pytest.mark.skipif(
    not os.path.exists(_FIXTURE),
    reason="test/fixtures/date_truth.json is missing",
)


@pytest.fixture(scope="module")
def truth():
    with open(_FIXTURE) as fh:
        return json.load(fh)


# ======================================================================
# Classifying a Stata format string
# ======================================================================

class TestFormatClassification:

    @pytest.mark.parametrize("fmt,kind", [
        ("%td", "td"), ("%tc", "tc"), ("%tC", "tC"), ("%tw", "tw"),
        ("%tm", "tm"), ("%tq", "tq"), ("%th", "th"), ("%ty", "ty"),
    ])
    def test_the_eight_date_formats(self, fmt, kind):
        assert dash_render._stata_date_kind(fmt) == kind

    def test_tc_and_tC_are_distinguished_case_sensitively(self):
        """They are different formats: %tC carries leap seconds, %tc does not."""
        assert dash_render._stata_date_kind("%tc") == "tc"
        assert dash_render._stata_date_kind("%tC") == "tC"
        assert (dash_render._stata_date_kind("%tc")
                != dash_render._stata_date_kind("%tC"))

    @pytest.mark.parametrize("fmt", [
        "%-td", "%-tc", "%-tm", "%-ty",
    ])
    def test_the_left_aligned_prefix_is_recognised(self, fmt):
        assert dash_render._stata_date_kind(fmt) == fmt[-2:].replace("t", "t")

    @pytest.mark.parametrize("fmt", [
        "%tdCCYY-NN-DD", "%tdD_m_Y", "%tcCCYY-NN-DD!THH:MM:SS",
        "%tmCCYY!mNN",
    ])
    def test_a_custom_date_picture_still_classifies(self, fmt):
        assert dash_render._stata_date_kind(fmt) is not None

    @pytest.mark.parametrize("fmt", [
        "%9.0g", "%9.2f", "%9.0fc", "%12.0gc", "%-9.2f", "%9s", "%10s",
        "", None, "%tt", "%t",
    ])
    def test_non_date_formats_classify_as_none(self, fmt):
        assert dash_render._stata_date_kind(fmt) is None


# ======================================================================
# Epoch conversion — every value Stata gave us
# ======================================================================

class TestEpochConversion:
    """Convert SIF values to timestamps and check against Stata's own ISO."""

    @pytest.mark.parametrize("kind", ["td", "tw", "tm", "tq", "th"])
    def test_calendar_formats_match_statas_iso(self, truth, kind):
        rec = truth["date_formats"][f"%{kind}"]
        vals, want = [], []
        for v in rec["values"]:
            if v.get("iso") in (None, ""):
                continue
            vals.append(float(v["value"]))
            want.append(v["iso"])
        assert vals, f"no usable {kind} values in the fixture"
        got = dash_render._stata_dates_to_datetime(pd.Series(vals), kind)
        for i, (v, w) in enumerate(zip(vals, want)):
            assert str(got.iloc[i].date()) == w, (
                f"%{kind} {v}: dash {got.iloc[i]!r}, Stata {w} "
                f"({rec['values'][i].get('iso_cmd')})"
            )

    def test_td_anchor_value(self, truth):
        """The anchor the section calls out: %td 14977 -> 02jan2001."""
        got = dash_render._stata_dates_to_datetime(pd.Series([14977.0]), "td")
        assert str(got.iloc[0].date()) == "2001-01-02"

    def test_tm_anchors(self, truth):
        got = dash_render._stata_dates_to_datetime(pd.Series([0.0, 745.0]), "tm")
        assert str(got.iloc[0].date()) == "1960-01-01"
        assert str(got.iloc[1].date()) == "2022-02-01"

    def test_ty_is_the_year_itself_not_an_offset(self, truth):
        """display %ty 38 prints 38, not 1998.  Verified in Stata."""
        assert "CONFIRMED" in truth["ty_is_the_year_itself"]["conclusion"]
        got = dash_render._stata_dates_to_datetime(
            pd.Series([1998.0, 2024.0]), "ty")
        assert got.iloc[0].year == 1998
        assert got.iloc[1].year == 2024

    def test_tc_milliseconds(self, truth):
        rec = truth["date_formats"]["%tc"]
        for v in rec["values"]:
            iso = v.get("iso")
            if not iso:
                continue
            got = dash_render._stata_dates_to_datetime(
                pd.Series([float(v["value"])]), "tc")
            assert str(got.iloc[0].date()) == iso[:10], v["display_cmd"]

    def test_tC_differs_from_tc_by_the_accumulated_leap_seconds(self, truth):
        """Leap-second data IS available; treating %tC as %tc is wrong.

        dash converts %tC using the same epoch as %tc and must SAY so rather
        than pretending the two are the same format.
        """
        assert "IS available" in truth["leap_seconds"]["finding"]
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dash_render._stata_dates_to_datetime(
                pd.Series([1234567890123.0]), "tC")
        assert any("leap" in str(w.message).lower() for w in caught), (
            "%tC must warn that leap seconds are not applied"
        )

    def test_missing_values_become_nat(self):
        got = dash_render._stata_dates_to_datetime(
            pd.Series([14977.0, np.nan, 14978.0]), "td")
        assert pd.isna(got.iloc[1])
        assert not pd.isna(got.iloc[0])

    def test_out_of_range_values_warn_rather_than_raise(self):
        """Stata's date range is wider than pandas' nanosecond datetime64."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            got = dash_render._stata_dates_to_datetime(
                pd.Series([14977.0, 1e9]), "td")
        assert got is not None
        assert any("range" in str(w.message).lower() for w in caught)


# ======================================================================
# The transport bug
# ======================================================================

def _jsonio_payload(values, names, is_string=None, labels=None,
                    string_key="variableIsString"):
    """Build a payload shaped the way REAL jsonio emits one."""
    inner = {
        "values": values,
        "variableNames": names,
        "variableLabels": labels or {n: n for n in names},
        "valueLabelNames": {},
        "valueLabels": {},
        string_key: is_string or {n: False for n in names},
    }
    return {"StataJSON": inner}


def _renderer(spec, data, tmp_path):
    sp = tmp_path / "spec.json"
    dp = tmp_path / "data.json"
    op = tmp_path / "out.html"
    sp.write_text(json.dumps(spec))
    dp.write_text(json.dumps(data))
    return DashRenderer(str(sp), str(dp), str(op))


def _minimal_spec(plots, formats=None, level=None):
    build = {"layout": "auto", "link": "", "theme": "default",
             "title": "", "subtitle": "", "registry": "g1"}
    if formats is not None:
        build["formats"] = formats
    if level is not None:
        build["level"] = level
    return {"graphs": [{"plots": plots,
                        "graph_options": {"name": "g1"},
                        "if_expr": "", "in_expr": ""}],
            "kpis": [],
            "build_options": build}


class TestStringColumnDetection:
    """dash reads a key jsonio does not emit."""

    def test_jsonios_real_key_is_honoured(self, tmp_path):
        """Real jsonio emits variableIsString, not variableTypeIsString."""
        data = _jsonio_payload(
            [{"name": "Ford", "mpg": 22.0}, {"name": "Buick", "mpg": 17.0}],
            ["name", "mpg"],
            is_string={"name": True, "mpg": False},
            string_key="variableIsString",
        )
        dr = _renderer(_minimal_spec([]), data, tmp_path)
        dr._load_data()
        assert "name" in dr.string_vars, (
            "dash ignored jsonio's variableIsString, so every string column "
            "is coerced to NaN in production"
        )
        assert list(dr.df["name"]) == ["Ford", "Buick"]

    def test_the_legacy_key_still_works(self, tmp_path):
        """Existing specs and the test helpers use variableTypeIsString."""
        data = _jsonio_payload(
            [{"name": "Ford", "mpg": 22.0}],
            ["name", "mpg"],
            is_string={"name": True, "mpg": False},
            string_key="variableTypeIsString",
        )
        dr = _renderer(_minimal_spec([]), data, tmp_path)
        dr._load_data()
        assert "name" in dr.string_vars


class TestDateColumnsSurviveTransport:

    def test_a_date_column_is_converted_using_the_formats_map(self, tmp_path):
        data = _jsonio_payload(
            [{"date": 14977.0, "close": 1283.27},
             {"date": 14978.0, "close": 1347.56}],
            ["date", "close"],
        )
        spec = _minimal_spec([], formats={"date": "%td", "close": "%9.2f"})
        dr = _renderer(spec, data, tmp_path)
        dr._load_data()
        assert pd.api.types.is_datetime64_any_dtype(dr.df["date"]), (
            f"date came through as {dr.df['date'].dtype}"
        )
        assert str(dr.df["date"].iloc[0].date()) == "2001-01-02"
        assert pd.api.types.is_numeric_dtype(dr.df["close"])

    def test_a_date_that_arrives_as_a_display_string_is_still_recovered(
        self, tmp_path
    ):
        """The production failure: jsonio sends "02jan2001", not 14977.

        dash.ado now transports the numeric value instead, but a spec written
        by an older dash.ado still carries strings, and turning them into NaN
        loses the whole dataset.  Parse them rather than coerce them away.
        """
        data = _jsonio_payload(
            [{"date": "02jan2001", "close": 1283.27},
             {"date": "03jan2001", "close": 1347.56}],
            ["date", "close"],
        )
        spec = _minimal_spec([], formats={"date": "%td"})
        dr = _renderer(spec, data, tmp_path)
        dr._load_data()
        assert dr.df["close"].notna().all()
        assert dr.df["date"].notna().all(), (
            "a date arriving as a display string was coerced to NaN, which "
            "drops every row of the dataset"
        )

    def test_no_formats_key_leaves_everything_alone(self, tmp_path):
        """Backward compatibility: an older dash.ado against a newer renderer."""
        data = _jsonio_payload(
            [{"mpg": 22.0, "weight": 2930.0}, {"mpg": 17.0, "weight": 3350.0}],
            ["mpg", "weight"],
        )
        dr = _renderer(_minimal_spec([]), data, tmp_path)
        dr._load_data()
        assert pd.api.types.is_numeric_dtype(dr.df["mpg"])
        assert list(dr.df["mpg"]) == [22.0, 17.0]

    def test_a_variable_absent_from_the_map_is_untouched(self, tmp_path):
        data = _jsonio_payload(
            [{"date": 14977.0, "other": 5.0}], ["date", "other"])
        spec = _minimal_spec([], formats={"date": "%td"})
        dr = _renderer(spec, data, tmp_path)
        dr._load_data()
        assert pd.api.types.is_numeric_dtype(dr.df["other"])

    def test_a_string_column_is_not_converted_even_with_a_date_format(
        self, tmp_path
    ):
        data = _jsonio_payload(
            [{"label": "not a date"}], ["label"],
            is_string={"label": True})
        spec = _minimal_spec([], formats={"label": "%td"})
        dr = _renderer(spec, data, tmp_path)
        dr._load_data()
        assert list(dr.df["label"]) == ["not a date"]

    def test_the_date_columns_are_recorded_for_later_use(self, tmp_path):
        data = _jsonio_payload(
            [{"date": 14977.0, "mpg": 22.0}], ["date", "mpg"])
        spec = _minimal_spec([], formats={"date": "%td", "mpg": "%9.0g"})
        dr = _renderer(spec, data, tmp_path)
        dr._load_data()
        assert dr.date_vars == {"date": "td"}


# ======================================================================
# Datetime axes
# ======================================================================

class TestDatetimeAxis:

    def _fig(self, tmp_path, plots, formats):
        data = _jsonio_payload(
            [{"date": 14977.0 + i, "close": 1000.0 + i, "vol": 5.0 + i}
             for i in range(10)],
            ["date", "close", "vol"],
        )
        dr = _renderer(_minimal_spec(plots, formats=formats), data, tmp_path)
        return dr._build_figures()["g1"]

    def test_a_date_x_variable_gets_a_datetime_axis(self, tmp_path):
        fig = self._fig(
            tmp_path,
            [{"type": "line", "yvar": "close", "xvar": "date", "options": {}}],
            {"date": "%td"})
        from bokeh.models import DatetimeAxis, LinearAxis
        assert any(isinstance(a, DatetimeAxis) for a in fig.xaxis), (
            f"x axis is {[type(a).__name__ for a in fig.xaxis]}"
        )

    def test_a_numeric_x_variable_does_not(self, tmp_path):
        fig = self._fig(
            tmp_path,
            [{"type": "line", "yvar": "close", "xvar": "vol", "options": {}}],
            {"vol": "%9.0g"})
        from bokeh.models import DatetimeAxis
        assert not any(isinstance(a, DatetimeAxis) for a in fig.xaxis)

    def test_a_date_y_variable_gets_a_datetime_y_axis(self, tmp_path):
        fig = self._fig(
            tmp_path,
            [{"type": "line", "yvar": "date", "xvar": "vol", "options": {}}],
            {"date": "%td"})
        from bokeh.models import DatetimeAxis
        assert any(isinstance(a, DatetimeAxis) for a in fig.yaxis)

    def test_the_data_actually_reaches_the_glyph(self, tmp_path):
        """The regression that matters: 0 points is the current behaviour."""
        fig = self._fig(
            tmp_path,
            [{"type": "line", "yvar": "close", "xvar": "date", "options": {}}],
            {"date": "%td"})
        lengths = [len(r.data_source.data.get("date", []))
                   for r in fig.renderers
                   if "date" in getattr(r.data_source, "data", {})]
        assert lengths and max(lengths) == 10, (
            f"the date series reached the glyph with {lengths} points"
        )

    def test_log_scale_on_a_date_variable_warns_and_stays_a_date(self,
                                                                 tmp_path):
        data = _jsonio_payload(
            [{"date": 14977.0 + i, "close": 1000.0 + i} for i in range(10)],
            ["date", "close"])
        spec = _minimal_spec(
            [{"type": "line", "yvar": "close", "xvar": "date", "options": {}}],
            formats={"date": "%td"})
        spec["graphs"][0]["graph_options"]["xscale"] = "log"
        dr = _renderer(spec, data, tmp_path)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            fig = dr._build_figures()["g1"]
        from bokeh.models import DatetimeAxis
        assert any(isinstance(a, DatetimeAxis) for a in fig.xaxis)
        assert any("date" in str(w.message).lower() for w in caught)


# ======================================================================
# Numeric display formats
# ======================================================================

class TestNumericDisplayFormats:
    """Stata's numeric formats, checked against 150 measured values.

    dash reproduces the MEANING of a display format -- decimal places, comma
    grouping, and the width-driven fallbacks Stata applies when a value does
    not fit -- but not Stata's fixed-width left padding, which exists for
    aligned console columns and has no meaning in an HTML dashboard.  The
    tests therefore compare stripped output.

    Only the ``f``/``fc`` and ``e`` families are reproduced.  ``%g`` is
    Stata's DEFAULT format and carries no user intent, so a value with a
    ``%g`` format is left alone rather than reformatted.
    """

    def _cases(self, truth, families=("f", "fc")):
        import re
        out = []
        for fmt, rec in truth["numeric_formats"].items():
            m = re.fullmatch(r"%-?\d+\.\d+(f|fc|e)", fmt)
            if not m or m.group(1) not in families:
                continue
            for v in rec["values"]:
                raw = str(v["value"])
                if raw.startswith(".") and not raw[1:2].isdigit():
                    continue          # Stata missing / extended missing
                out.append((fmt, float(raw), v["display"]))
        return out

    def test_every_measured_f_and_fc_value_is_reproduced(self, truth):
        cases = self._cases(truth)
        assert len(cases) >= 40, f"only {len(cases)} cases found in the fixture"
        wrong = []
        for fmt, value, want in cases:
            got = dash_render._format_stata_numeric(value, fmt)
            if got.strip() != want.strip():
                wrong.append(f"  {fmt} {value!r}: dash {got.strip()!r}, "
                             f"Stata {want.strip()!r}")
        assert not wrong, (
            f"{len(wrong)} of {len(cases)} formatted values differ from "
            "Stata:\n" + "\n".join(wrong[:25])
        )

    def test_commas_are_dropped_rather_than_overflowing_the_width(self, truth):
        """%9.0fc of -1234567.891 is -1234568, with no commas: they would not fit."""
        got = dash_render._format_stata_numeric(-1234567.891, "%9.0fc")
        assert got.strip() == "-1234568"

    def test_scientific_fallback_when_the_value_cannot_fit(self, truth):
        """%9.2f of 1234567.891 is 1.23e+06, not 1234567.89."""
        got = dash_render._format_stata_numeric(1234567.891, "%9.2f")
        assert got.strip() == "1.23e+06"

    @pytest.mark.parametrize("fmt,want", [
        ("%9.0fc", "0,0"),
        ("%9.2fc", "0,0.00"),
        ("%9.2f", "0.00"),
        ("%9.0f", "0"),
        ("%12.4f", "0.0000"),
    ])
    def test_a_bokeh_tick_pattern_is_produced(self, fmt, want):
        """Ticks and tooltips need a format string, not a formatted value."""
        assert dash_render._stata_numeric_pattern(fmt) == want

    def test_an_unformattable_value_degrades(self):
        assert dash_render._format_stata_numeric(float("nan"), "%9.2f") == ""

    @pytest.mark.parametrize("fmt", ["%td", "%9s", "%9.0g", "%12.0gc", "", None])
    def test_a_format_dash_does_not_reproduce_returns_none(self, fmt):
        """%g is Stata's default and carries no user intent; leave it alone."""
        assert dash_render._stata_numeric_pattern(fmt) is None


# ======================================================================
# Everywhere a value is displayed
# ======================================================================

def _dated_payload(n=12):
    return _jsonio_payload(
        [{"date": 14977.0 + i, "close": 1000.0 + i * 10, "grp": float(i % 2)}
         for i in range(n)],
        ["date", "close", "grp"],
    )


class TestKpiValuesFormatAsDates:
    """`dash kpi max(date)` showed 15340, not a date."""

    def _kpi_text(self, tmp_path, stat, var, fmt=""):
        spec = _minimal_spec([], formats={"date": "%td", "close": "%9.2f"})
        spec["kpis"] = [{"name": "k1", "stat": stat, "var": var,
                         "title": "t", "fmt": fmt}]
        dr = _renderer(spec, _dated_payload(), tmp_path)
        dr.render()
        divs = getattr(dr, "kpi_divs", {})
        assert divs, "no KPI was rendered"
        return "".join(getattr(v, "text", "") for v in divs.values())

    @pytest.mark.parametrize("stat", ["min", "max", "median", "p25", "p75"])
    def test_date_statistics_display_as_dates(self, tmp_path, stat):
        text = self._kpi_text(tmp_path, stat, "date")
        assert "14977" not in text and "15340" not in text, (
            f"kpi {stat}(date) showed the raw Stata value: {text!r}"
        )
        assert "2001" in text, f"kpi {stat}(date) showed {text!r}"

    def test_count_of_a_date_is_still_a_count(self, tmp_path):
        text = self._kpi_text(tmp_path, "count", "date")
        assert "12" in text

    def test_sum_of_a_date_is_reported_as_meaningless(self, tmp_path):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            self._kpi_text(tmp_path, "sum", "date")
        assert any("sum" in str(w.message).lower() for w in caught), (
            "summing dates is meaningless and must be reported"
        )

    def test_a_numeric_kpi_is_unchanged(self, tmp_path):
        text = self._kpi_text(tmp_path, "max", "close", fmt="%9.2f")
        assert "1110.00" in text


class TestDateFilterWidgets:
    """A date range filter produced NO WIDGET at all."""

    def _widgets(self, tmp_path, ftype):
        spec = _minimal_spec(
            [{"type": "line", "yvar": "close", "xvar": "date", "options": {}}],
            formats={"date": "%td"})
        spec["build_options"]["filters"] = [
            {"varname": "date", "type": ftype, "exclude": [], "label": ""}]
        dr = _renderer(spec, _dated_payload(), tmp_path)
        dr.render()
        return list(getattr(dr, "filter_widgets", []))

    def test_a_date_range_filter_produces_a_widget(self, tmp_path):
        w = self._widgets(tmp_path, "range")
        assert w, (
            "a date range filter produced no widget: the datetime64 column "
            "fails the is_numeric_dtype guard and was skipped silently"
        )

    def test_the_range_widget_is_a_date_widget(self, tmp_path):
        from bokeh.models import DateRangeSlider
        w = self._widgets(tmp_path, "range")
        assert any(isinstance(x, DateRangeSlider) for x in w), (
            f"got {[type(x).__name__ for x in w]}"
        )

    def test_a_date_slider_filter_produces_a_date_slider(self, tmp_path):
        from bokeh.models import DateSlider
        w = self._widgets(tmp_path, "slider")
        assert any(isinstance(x, DateSlider) for x in w)

    def test_the_widget_bounds_are_the_data_range(self, tmp_path):
        from bokeh.models import DateRangeSlider
        w = [x for x in self._widgets(tmp_path, "range")
             if isinstance(x, DateRangeSlider)]
        assert w
        lo, hi = w[0].start, w[0].end
        assert pd.Timestamp(lo, unit="ms").year == 2001
        assert pd.Timestamp(hi, unit="ms").year == 2001

    def test_a_date_dropdown_shows_dates_not_epoch_numbers(self, tmp_path):
        from bokeh.models import Select
        w = [x for x in self._widgets(tmp_path, "dropdown")
             if isinstance(x, Select)]
        assert w, "no dropdown was built"
        labels = [o[1] if isinstance(o, tuple) else o for o in w[0].options]
        joined = " ".join(str(x) for x in labels)
        assert "2001" in joined, f"dropdown showed {labels[:4]}"
        assert "14977" not in joined

    def test_a_numeric_filter_is_unchanged(self, tmp_path):
        from bokeh.models import RangeSlider
        spec = _minimal_spec(
            [{"type": "line", "yvar": "close", "xvar": "grp", "options": {}}])
        spec["build_options"]["filters"] = [
            {"varname": "close", "type": "range", "exclude": [], "label": ""}]
        dr = _renderer(spec, _dated_payload(), tmp_path)
        dr.render()
        assert any(isinstance(x, RangeSlider)
                   for x in dr.filter_widgets)


class TestHoverShowsDates:

    def test_a_date_column_gets_a_datetime_tooltip_formatter(self, tmp_path):
        from bokeh.models import HoverTool
        spec = _minimal_spec(
            [{"type": "line", "yvar": "close", "xvar": "date", "options": {}}],
            formats={"date": "%td"})
        dr = _renderer(spec, _dated_payload(), tmp_path)
        fig = dr._build_figures()["g1"]
        hovers = [t for t in fig.tools if isinstance(t, HoverTool)]
        assert hovers, "no hover tool on the figure"
        assert any(
            getattr(h, "formatters", None)
            and any("datetime" in str(v) for v in h.formatters.values())
            for h in hovers
        ), "the date column has no datetime tooltip formatter"

    def test_tooltips_use_variable_labels_not_raw_names(self, tmp_path):
        """self.variable_labels is loaded and used for axes but not tooltips."""
        from bokeh.models import HoverTool
        data = _dated_payload()
        data["StataJSON"]["variableLabels"] = {
            "date": "Trading date", "close": "Closing price", "grp": "Group"}
        spec = _minimal_spec(
            [{"type": "line", "yvar": "close", "xvar": "date", "options": {}}],
            formats={"date": "%td"})
        dr = _renderer(spec, data, tmp_path)
        fig = dr._build_figures()["g1"]
        text = " ".join(
            str(h.tooltips) for h in fig.tools if isinstance(h, HoverTool))
        assert "Closing price" in text, (
            f"tooltips label rows with raw variable names: {text[:200]}"
        )


class TestDateFilterActuallyFilters:
    """The plan said to VERIFY the wire format rather than assume it.

    Verified, and it was wrong: Bokeh sends the live column as epoch
    milliseconds, but dash's own ``orig_data`` snapshot serialised the same
    column as date STRINGS ("2001-01-02 00:00:00"), because
    ``_to_serialisable`` calls ``float(v)``, which raises on a Timestamp and
    falls through to ``str(v)``.  The filter callback then compared a string
    against the slider's numeric bounds, so dragging the slider filtered
    nothing and every date KPI collapsed to 0.
    """

    def _rendered(self, tmp_path):
        spec = _minimal_spec(
            [{"type": "line", "yvar": "close", "xvar": "date", "options": {}}],
            formats={"date": "%td"})
        spec["build_options"]["filters"] = [
            {"varname": "date", "type": "range", "exclude": [], "label": ""}]
        spec["build_options"]["link"] = "g1"
        spec["kpis"] = [{"name": "k1", "stat": "max", "var": "date",
                         "title": "Last", "fmt": ""}]
        dr = _renderer(spec, _dated_payload(), tmp_path)
        dr.render()
        return dr

    def test_the_snapshot_and_the_live_column_use_the_same_representation(
        self, tmp_path
    ):
        dr = self._rendered(tmp_path)
        assert dr.filter_callbacks, "no filter callback was built"
        cb = dr.filter_callbacks[0]
        snap = dict(cb.args["orig_source"].data)
        assert "date" in snap, "the snapshot has no date column"
        vals = [v for v in snap["date"] if v is not None]
        assert vals, "the snapshot's date column is empty"
        assert all(isinstance(v, (int, float)) for v in vals), (
            f"the snapshot serialised dates as {type(vals[0]).__name__}: "
            f"{vals[0]!r} — the filter JS compares this against the slider's "
            f"numeric bounds and will never match"
        )

    def test_the_snapshot_values_are_epoch_milliseconds(self, tmp_path):
        dr = self._rendered(tmp_path)
        snap = dict(dr.filter_callbacks[0].args["orig_source"].data)
        first = [v for v in snap["date"] if v is not None][0]
        assert pd.Timestamp(first, unit="ms").date().isoformat() == "2001-01-02"

    def test_every_per_source_snapshot_agrees_too(self, tmp_path):
        dr = self._rendered(tmp_path)
        cb = dr.filter_callbacks[0]
        for raw in cb.args.get("all_graph_sources_orig_json", []):
            snap = json.loads(raw)
            if "date" not in snap:
                continue
            vals = [v for v in snap["date"] if v is not None]
            assert all(isinstance(v, (int, float)) for v in vals), (
                f"a per-source snapshot serialised dates as "
                f"{type(vals[0]).__name__}"
            )

    def test_the_slider_bounds_and_the_snapshot_are_on_the_same_scale(
        self, tmp_path
    ):
        """A mismatch here silently filters nothing, which is the worst case."""
        from bokeh.models import DateRangeSlider
        dr = self._rendered(tmp_path)
        sliders = [w for w in dr.filter_widgets
                   if isinstance(w, DateRangeSlider)]
        assert sliders
        snap = dict(dr.filter_callbacks[0].args["orig_source"].data)
        vals = [v for v in snap["date"] if v is not None]
        assert min(vals) == pytest.approx(float(sliders[0].start))
        assert max(vals) == pytest.approx(float(sliders[0].end))

    def test_the_kpi_config_tells_the_callback_it_is_a_date(self, tmp_path):
        """Otherwise a filtered date KPI renders as a number."""
        dr = self._rendered(tmp_path)
        cfg = json.loads(dr.filter_callbacks[0].args["kpi_config_json"])
        assert cfg, "no KPI reached the callback"
        assert any(c.get("datekind") == "td" for c in cfg), (
            f"the KPI config carries no date kind: {cfg}"
        )

    def test_the_javascript_formats_a_date_kpi_as_a_date(self):
        js = dash_render._FILTER_JS
        assert "datekind" in js, (
            "the filter callback cannot format a date KPI as a date"
        )


class TestFacetAndMarkerLabels:

    def test_a_by_facet_on_a_date_reads_as_a_date(self, tmp_path):
        data = _jsonio_payload(
            [{"date": 14977.0 + (i // 3), "y": float(i), "x": float(i)}
             for i in range(6)],
            ["date", "y", "x"])
        spec = _minimal_spec(
            [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}],
            formats={"date": "%td"})
        spec["graphs"][0]["graph_options"]["by"] = "date"
        dr = _renderer(spec, data, tmp_path)
        dr._load_data()
        label = dr._facet_label(["date"], pd.Timestamp("2001-01-02"))
        assert "2001" in label and "14977" not in label, label

    def test_mlabel_on_a_date_prints_dates(self, tmp_path):
        from bokeh.models import LabelSet
        data = _jsonio_payload(
            [{"date": 14977.0 + i, "y": float(i), "x": float(i)}
             for i in range(4)],
            ["date", "y", "x"])
        spec = _minimal_spec(
            [{"type": "scatter", "yvar": "y", "xvar": "x",
              "options": {"mlabel": "date"}}],
            formats={"date": "%td"})
        dr = _renderer(spec, data, tmp_path)
        fig = dr._build_figures()["g1"]
        labels = [r for r in fig.center if isinstance(r, LabelSet)]
        assert labels, "no marker labels were drawn"
        col = labels[0].text
        src = labels[0].source
        texts = [str(t) for t in src.data[col]]
        assert any("2001" in t for t in texts), texts[:3]
        assert not any(t.startswith("14977") for t in texts), texts[:3]

    def test_mlabel_on_a_plain_variable_is_unchanged(self, tmp_path):
        from bokeh.models import LabelSet
        data = _jsonio_payload(
            [{"y": float(i), "x": float(i)} for i in range(4)], ["y", "x"])
        spec = _minimal_spec(
            [{"type": "scatter", "yvar": "y", "xvar": "x",
              "options": {"mlabel": "y"}}])
        dr = _renderer(spec, data, tmp_path)
        fig = dr._build_figures()["g1"]
        labels = [r for r in fig.center if isinstance(r, LabelSet)]
        # The values as they are, not dates.  (They are drawn from a column
        # derived beside the variable's -- every numeric label is, so a
        # missing value reads "." and a served filter's redraw keeps the
        # column -- rather than from the variable's own column.)
        assert labels
        texts = list(labels[0].source.data[labels[0].text])
        assert texts == [0.0, 1.0, 2.0, 3.0], texts


class TestAMissingDateDoesNotBreakAFilteredPage:
    """Found by WP-21, measured 23sep2026 at ed41e8a: a saved dashboard
    with a filter, over a %td variable holding one missing value, failed
    to render at all -- ``ValueError: Out of range float values are not
    JSON compliant: nan``.  ``_make_source`` built every column with
    ``tolist()``, so a date column became Timestamps with a ``NaT`` in the
    list, and Bokeh writes ``NaT`` in a list as a float NaN, which JSON
    refuses.  Without a filter the source never reached the document;
    the filter callbacks' arguments carry it in."""

    def _data(self):
        vals = _dated_payload()
        rows = vals["StataJSON"]["values"]
        rows[3]["date"] = None
        return vals

    @pytest.mark.parametrize("ftype", ["range", "dropdown"])
    def test_the_page_renders(self, tmp_path, ftype):
        spec = _minimal_spec(
            [{"type": "line", "yvar": "close", "xvar": "date",
              "options": {}}], formats={"date": "%td"})
        spec["build_options"]["filters"] = [
            {"varname": "close" if ftype == "range" else "date",
             "type": ftype, "exclude": [], "label": ""}]
        dr = _renderer(spec, self._data(), tmp_path)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            html = dr.render()
        assert "<html" in html.lower()

    def test_the_source_keeps_the_missing_date_missing(self, tmp_path):
        spec = _minimal_spec(
            [{"type": "line", "yvar": "close", "xvar": "date",
              "options": {}}], formats={"date": "%td"})
        spec["build_options"]["filters"] = [
            {"varname": "close", "type": "range", "exclude": [], "label": ""}]
        dr = _renderer(spec, self._data(), tmp_path)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.render()
        col = list(dr.sources["g1"].data["date"])
        assert pd.isna(col[3])
        assert not pd.isna(col[2]) and not pd.isna(col[4])
