"""test_server_data_shape.py — the server app read the data wrongly.

Two defects in one function, both in the generated app's
``_load_spec_and_data``, both silent, and both invisible to the ~450 existing
server tests because those build a DataFrame themselves rather than letting
the app decode its own embedded payload.

**1. Every string variable became NaN.** The app asks the payload for
``variableTypeIsString``. Real ``jsonio`` output does not contain that key —
it emits ``variableIsString``. Measured on the real shape:

    standalone   make dtype str      first value 'car0'
    server       make dtype float64  first value nan

Because the key is missing, ``type_is_str.get(col, False)`` is False for every
column and ``pd.to_numeric(..., errors="coerce")`` is applied to the strings.
So in server mode a ``type(dropdown)`` filter on a string variable has no
values, ``mlabel()`` labels nothing, and ``by()`` on a string groups nothing —
with no error anywhere.

**2. A wrapped payload yielded no data at all.** ``DashRenderer`` accepts both
shapes — ``self.data_json.get("StataJSON", self.data_json)`` — because jsonio
has emitted both over its life. The generated app reads only the top level, so
a wrapped payload gave it zero rows, an empty ``ColumnDataSource``, and a chart
whose glyph refers to columns that do not exist. Bokeh logs
``BAD_COLUMN_NAME`` and serves a blank plot.

The two loaders must agree; that is what these tests pin.
"""
import json
import os
import sys
import tempfile

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

from dash_render import DashRenderer, ServerAppBuilder

from conftest import exec_app, make_spec, make_data_json


from conftest import render_models  # noqa: E402


def _flat_payload():
    """The shape real jsonio emits: flat, ``variableIsString``, no wrapper."""
    return {
        "variableNames": ["mpg", "make"],
        "variableLabels": {"mpg": "Mileage (mpg)", "make": "Make and model"},
        "valueLabels": {},
        "valueLabelNames": {},
        "variableIsString": {"mpg": False, "make": True},
        "values": [{"mpg": 12.0 + i, "make": "car%d" % i} for i in range(6)],
    }


def _wrapped_payload():
    """The other shape jsonio has emitted, which DashRenderer accepts."""
    return {"StataJSON": _flat_payload()}


def _server_frame(payload, tmpdir):
    """Run the generated app's own loader and return its DataFrame."""
    spec = make_spec([{"type": "scatter", "yvar": "mpg", "xvar": "mpg",
                       "options": {}}])
    sp = os.path.join(tmpdir, "s.json")
    dp = os.path.join(tmpdir, "d.json")
    op = os.path.join(tmpdir, "app.py")
    with open(sp, "w") as f:
        json.dump(spec, f)
    with open(dp, "w") as f:
        json.dump(payload, f)
    ServerAppBuilder(sp, dp).build(op)
    with open(op, encoding="utf-8") as fh:
        src = fh.read()
    ns: dict = {}
    # Everything up to the attach line: defining the module is enough, and
    # attaching a document needs a Bokeh session this test does not have.
    exec_app(src.split("if __name__ !=")[0], op, ns)
    _spec, df, _meta = ns["_load_spec_and_data"]()
    return df


def _standalone_frame(payload, tmpdir):
    spec = make_spec([{"type": "scatter", "yvar": "mpg", "xvar": "mpg",
                       "options": {}}])
    sp = os.path.join(tmpdir, "s2.json")
    dp = os.path.join(tmpdir, "d2.json")
    op = os.path.join(tmpdir, "x.html")
    with open(sp, "w") as f:
        json.dump(spec, f)
    with open(dp, "w") as f:
        json.dump(payload, f)
    dr = DashRenderer(sp, dp, op)
    render_models(dr)
    return dr.df


@pytest.fixture
def tmpdir_path(tmp_path):
    return str(tmp_path)


class TestStringVariablesSurvive:
    """The live defect: real Stata data, strings turned to NaN."""

    def test_a_string_column_is_not_coerced_to_nan(self, tmpdir_path):
        df = _server_frame(_flat_payload(), tmpdir_path)
        assert "make" in df.columns
        assert df["make"].notna().all(), (
            "every value of a string variable became NaN; the loader asks "
            "for `variableTypeIsString' and real jsonio emits "
            "`variableIsString'"
        )
        assert str(df["make"].iloc[0]) == "car0", df["make"].iloc[0]

    def test_a_numeric_column_is_still_numeric(self, tmpdir_path):
        df = _server_frame(_flat_payload(), tmpdir_path)
        assert pd.api.types.is_numeric_dtype(df["mpg"])
        assert float(df["mpg"].iloc[0]) == 12.0

    def test_the_legacy_key_still_works(self, tmpdir_path):
        """Some payloads carry the other spelling; accept both."""
        payload = _flat_payload()
        payload["variableTypeIsString"] = payload.pop("variableIsString")
        df = _server_frame(payload, tmpdir_path)
        assert str(df["make"].iloc[0]) == "car0"

    def test_both_loaders_agree(self, tmpdir_path):
        srv = _server_frame(_flat_payload(), tmpdir_path)
        std = _standalone_frame(_flat_payload(), tmpdir_path)
        assert list(srv.columns) == list(std.columns)
        assert len(srv) == len(std)
        assert [str(v) for v in srv["make"]] == [str(v) for v in std["make"]]


class TestAWrappedPayloadIsUnwrapped:
    """DashRenderer accepts both shapes; the generated app accepted one."""

    def test_a_wrapped_payload_yields_rows(self, tmpdir_path):
        df = _server_frame(_wrapped_payload(), tmpdir_path)
        assert len(df) == 6, (
            "a StataJSON-wrapped payload gave the app zero rows, so its "
            "ColumnDataSource is empty and every glyph refers to a column "
            "that does not exist"
        )

    def test_a_wrapped_payload_has_the_columns(self, tmpdir_path):
        df = _server_frame(_wrapped_payload(), tmpdir_path)
        assert {"mpg", "make"} <= set(df.columns)

    def test_both_shapes_give_the_same_frame(self, tmpdir_path):
        flat = _server_frame(_flat_payload(), tmpdir_path)
        wrapped = _server_frame(_wrapped_payload(), tmpdir_path)
        assert list(flat.columns) == list(wrapped.columns)
        assert len(flat) == len(wrapped)

    def test_the_standalone_renderer_accepts_both_too(self, tmpdir_path):
        """The behaviour being matched, stated so it cannot silently change."""
        a = _standalone_frame(_flat_payload(), tmpdir_path)
        b = _standalone_frame(_wrapped_payload(), tmpdir_path)
        assert len(a) == len(b) == 6


class TestVariableLabelsSurviveToo:
    """They travel in the same payload and are read the same way."""

    def test_the_label_reaches_the_app(self, tmpdir_path):
        spec = make_spec([{"type": "scatter", "yvar": "mpg", "xvar": "mpg",
                           "options": {}}])
        sp = os.path.join(tmpdir_path, "s.json")
        dp = os.path.join(tmpdir_path, "d.json")
        op = os.path.join(tmpdir_path, "app.py")
        with open(sp, "w") as f:
            json.dump(spec, f)
        with open(dp, "w") as f:
            json.dump(_wrapped_payload(), f)
        ServerAppBuilder(sp, dp).build(op)
        with open(op, encoding="utf-8") as fh:
            src = fh.read()
        ns: dict = {}
        exec_app(src.split("if __name__ !=")[0], op, ns)
        _spec, _df, meta = ns["_load_spec_and_data"]()
        assert meta["var_labels"].get("mpg") == "Mileage (mpg)"
