"""test_binary_data_file.py -- the data file's numbers are binary arrays
(GAPS3 G3b; BUGS.md "The data file embeds numbers as JSON text (about 0.5
GB per million values)").

``_dash_write_stata_data`` wrote every number as JSON text inside one
object per observation, the variable's name repeated in each: a million
values were 19.8 MB (ten variables of 100,000 observations, half doubles,
half ints, 5% missing; 16.6 MB as one int variable), measured 19oct2026.
The writer now writes the file column by column (``dataFormat``
``_DASH_DATA_FORMAT``): a numeric variable is one base64 string of
little-endian float64 -- float32 where every value is exactly a float32,
as a byte, int or float variable always is -- each missing value a NaN and
an extended missing value's letter in ``extendedMissing`` as before; a
string variable a JSON list of its text.  Both loaders read it through
``_dash_read_data_json`` and ``_dash_columns_frame``; the old row layout
is still read.
"""
import base64
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

import dash_render as dr  # noqa: E402
from conftest import exec_app, make_spec  # noqa: E402
from test_extended_missing import _Missing, _Sfi  # noqa: E402
from test_string_value_export import ADVERSARIAL, FakeSfi  # noqa: E402


def _fake():
    """y a double with missing values, x a long, g a byte, d a double of
    whole numbers, big a double no float32 holds, s text."""
    n = len(ADVERSARIAL)
    y = [i / 3 for i in range(n)]
    y[2] = y[5] = None
    g = [float(i % 3) for i in range(n)]
    g[1] = None
    big = [1e300 if i % 2 else 0.1 for i in range(n)]
    return FakeSfi(
        {"y": y, "x": [float(i + 1) for i in range(n)], "g": g,
         "d": [float(i * 10) for i in range(n)], "big": big,
         "s": list(ADVERSARIAL)},
        {"y": "double", "x": "long", "g": "byte", "d": "double",
         "big": "double", "s": "str"},
        var_labels={"g": "Group"})


def _write(tmp_path, fake, names, fname="data.json"):
    path = str(tmp_path / fname)
    assert dr._dash_write_stata_data(path, names, sfi=fake) == ""
    return path


def _raw(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _old_layout(fake, names):
    """The same data in the row layout the writer wrote before (jsonio's):
    one object per observation, a missing number the text "null"."""
    n = fake.Data.getObsTotal()
    rows = []
    for i in range(n):
        row = {}
        for v in names:
            x = fake.columns[v][i]
            if str(fake.types[v]).startswith("str"):
                row[v] = x
            else:
                row[v] = "null" if x is None else float(x)
        rows.append(row)
    return {"values": rows, "variableNames": list(names),
            "variableIsString": {v: str(fake.types[v]).startswith("str")
                                 for v in names},
            "variableLabels": {v: "" for v in names},
            "valueLabels": {}, "valueLabelNames": {},
            "numberOfRecords": n, "numberOfVariables": len(names)}


def _spec_file(tmp_path, yvar="y", xvar="x"):
    sp = str(tmp_path / "spec.json")
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(make_spec([{"type": "scatter", "yvar": yvar,
                              "xvar": xvar, "options": {}}]), fh)
    return sp


def _saved_frame(sp, dp):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return dr.DashRenderer(sp, dp).df


def _served_frame(tmp_path, sp, dp):
    op = str(tmp_path / ("app_%s.py" % os.path.basename(dp)))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(op)
    with open(op, encoding="utf-8") as fh:
        src = fh.read()
    ns: dict = {}
    exec_app(src.split("if __name__ !=")[0], op, ns)
    return ns["_load_spec_and_data"]()[1]


def _column(dtype, values):
    return {"dtype": dtype, "base64": base64.b64encode(
        np.asarray(values, dtype=dtype).tobytes()).decode("ascii")}


def _doc(**over):
    doc = {"dataFormat": dr._DASH_DATA_FORMAT,
           "columns": {"y": _column("<f8", [1.5, np.nan]),
                       "s": ["a", "b"]},
           "variableNames": ["y", "s"],
           "variableIsString": {"y": False, "s": True},
           "variableLabels": {}, "valueLabels": {}, "valueLabelNames": {},
           "numberOfRecords": 2, "numberOfVariables": 2}
    doc.update(over)
    return doc


# ===========================================================================
# The writer
# ===========================================================================

class TestTheWriterWritesColumns:

    def test_numbers_are_base64_typed_arrays(self, tmp_path):
        fake = _fake()
        d = _raw(_write(tmp_path, fake, "y x g d big s"))
        assert d["dataFormat"] == dr._DASH_DATA_FORMAT
        assert "values" not in d
        assert d["variableNames"] == ["y", "x", "g", "d", "big", "s"]
        assert d["numberOfRecords"] == len(ADVERSARIAL)
        assert d["columns"]["s"] == ADVERSARIAL
        for v in ("y", "x", "g", "d", "big"):
            col = d["columns"][v]
            assert set(col) == {"dtype", "base64"}
            got = np.frombuffer(base64.b64decode(col["base64"]),
                                dtype=col["dtype"]).astype(float)
            want = np.array(fake.columns[v], dtype=float)
            assert np.array_equal(got, want, equal_nan=True), v

    def test_float32_only_where_every_value_is_one(self, tmp_path):
        d = _raw(_write(tmp_path, _fake(), "y x g d big"))["columns"]
        assert {v: d[v]["dtype"] for v in d} == {
            "y": "<f8", "x": "<f4", "g": "<f4", "d": "<f4", "big": "<f8"}

    def test_a_million_values_take_under_eleven_bytes_each(self, tmp_path):
        """19.8 MB for a million values in the row layout (measured
        19oct2026); at most 8 bytes of base64 for each 6 of double now.
        Measured on 100,000 doubles that no float32 holds."""
        n = 100_000
        fake = FakeSfi({"v": [i / 7 for i in range(n)]}, {"v": "double"})
        path = _write(tmp_path, fake, "v")
        assert os.path.getsize(path) < 11 * n

    def test_no_observations(self, tmp_path):
        fake = FakeSfi({"y": [], "s": []}, {"y": "double", "s": "str"})
        d = _raw(_write(tmp_path, fake, "y s"))
        assert d["numberOfRecords"] == 0
        assert d["columns"] == {"y": {"dtype": "<f4", "base64": ""},
                                "s": []}


# ===========================================================================
# The reader
# ===========================================================================

class TestTheReader:

    def test_columns_decode_to_arrays_and_text(self):
        got = dr._dash_read_data_json(json.dumps(_doc()))
        y = got["columns"]["y"]
        assert isinstance(y, np.ndarray) and y.dtype == np.float64
        assert y[0] == 1.5 and np.isnan(y[1])
        assert got["columns"]["s"] == ["a", "b"]

    def test_a_number_no_double_holds_is_missing(self):
        doc = _doc(columns={"y": _column("<f8", [np.inf, -np.inf]),
                            "s": ["a", "b"]})
        got = dr._dash_read_data_json(json.dumps(doc))["columns"]["y"]
        assert np.isnan(got).all()

    def test_the_columns_are_writable_copies(self):
        y = dr._dash_read_data_json(json.dumps(_doc()))["columns"]["y"]
        assert y.flags.writeable      # np.frombuffer alone is read-only
        y[0] = 2.0
        assert y[0] == 2.0

    @pytest.mark.parametrize("change", [
        {"dataFormat": "dash-columns-99"},
        {"numberOfRecords": 3},
        {"numberOfRecords": -1},
        {"numberOfRecords": True},
        {"numberOfRecords": "2"},
        {"columns": {"y": _column("<f8", [1.5, 2.0])}},
        {"columns": {"y": _column("<i8", [1, 2]), "s": ["a", "b"]}},
        {"columns": {"y": _column(">f8", [1.5, 2.0]), "s": ["a", "b"]}},
        {"columns": {"y": {"dtype": "<f8", "base64": "!!!!"},
                     "s": ["a", "b"]}},
        {"columns": {"y": {"dtype": "<f8", "base64": 7}, "s": ["a", "b"]}},
        {"columns": {"y": _column("<f8", [1.5]), "s": ["a", "b"]}},
        {"columns": {"y": _column("<f8", [1.5, 2.0]), "s": ["a"]}},
        {"columns": {"y": _column("<f8", [1.5, 2.0]), "s": ["a", 1]}},
        {"columns": {"y": ["1", "2"], "s": ["a", "b"]}},
        {"columns": {"y": _column("<f8", [1.5, 2.0]),
                     "s": _column("<f8", [1.5, 2.0])}},
        {"columns": [1, 2]},
        {"variableNames": "y s"},
    ], ids=["format", "short", "negative", "bool", "text_count",
            "a_column_missing", "int_dtype", "big_endian", "bad_base64",
            "base64_not_text", "too_few_bytes", "too_few_strings",
            "a_number_as_text", "numbers_as_text", "a_string_as_numbers",
            "columns_a_list", "names_a_string"])
    def test_a_malformed_file_is_refused(self, change):
        with pytest.raises(ValueError):
            dr._dash_read_data_json(json.dumps(_doc(**change)))

    def test_an_extended_missing_letter_is_its_code_column(self, tmp_path):
        raw = [1.0, _Missing.getValue(".a"), _Missing.getValue("."),
               _Missing.getValue(".b"), 3.0]
        path = str(tmp_path / "d.json")
        assert dr._dash_write_stata_data(path, "rep78", sfi=_Sfi(raw)) == ""
        with open(path, encoding="utf-8") as fh:
            got = dr._dash_read_data_json(fh.read())
        assert got["columns"]["__dashm_rep78"] == ["", "a", "", "b", ""]
        assert got["variableIsString"]["__dashm_rep78"] is True
        assert np.array_equal(got["columns"]["rep78"],
                              [1.0, np.nan, np.nan, np.nan, 3.0],
                              equal_nan=True)


# ===========================================================================
# Both loaders: the same frame from either layout
# ===========================================================================

class TestBothLoaders:

    _NAMES = ["y", "x", "g", "d", "big", "s"]

    def _pair(self, tmp_path):
        fake = _fake()
        new = _write(tmp_path, fake, " ".join(self._NAMES), "new.json")
        old = str(tmp_path / "old.json")
        with open(old, "w", encoding="utf-8") as fh:
            json.dump(_old_layout(fake, self._NAMES), fh)
        return _spec_file(tmp_path), new, old

    def test_the_saved_loader_reads_both_layouts_alike(self, tmp_path):
        sp, new, old = self._pair(tmp_path)
        a, b = _saved_frame(sp, new), _saved_frame(sp, old)
        pd.testing.assert_frame_equal(a[self._NAMES], b[self._NAMES])
        assert a["s"].tolist() == ADVERSARIAL

    def test_the_served_loader_reads_both_layouts_alike(self, tmp_path):
        sp, new, old = self._pair(tmp_path)
        a = _served_frame(tmp_path, sp, new)
        b = _served_frame(tmp_path, sp, old)
        pd.testing.assert_frame_equal(a[self._NAMES], b[self._NAMES])
        assert a["s"].tolist() == ADVERSARIAL

    def test_extended_missing_reaches_both_loaders(self, tmp_path):
        raw = [1.0, _Missing.getValue(".a"), _Missing.getValue("."), 3.0]
        dp = str(tmp_path / "d.json")
        assert dr._dash_write_stata_data(dp, "rep78", sfi=_Sfi(raw)) == ""
        sp = _spec_file(tmp_path, "rep78", "rep78")
        for df in (_saved_frame(sp, dp), _served_frame(tmp_path, sp, dp)):
            assert df["__dashm_rep78"].tolist() == ["", "a", "", ""]
            assert np.array_equal(df["rep78"].to_numpy(dtype=float),
                                  [1.0, np.nan, np.nan, 3.0], equal_nan=True)

    def test_no_observations_keeps_the_variables(self, tmp_path):
        fake = FakeSfi({"y": [], "x": []}, {"y": "double", "x": "double"})
        dp = _write(tmp_path, fake, "y x")
        sp = _spec_file(tmp_path)
        for df in (_saved_frame(sp, dp), _served_frame(tmp_path, sp, dp)):
            assert list(df.columns)[:2] == ["y", "x"] and len(df) == 0

    def test_the_served_app_carries_the_frame_reader(self, tmp_path):
        sp, new, _old = self._pair(tmp_path)
        op = str(tmp_path / "app.py")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, new).build(op)
        with open(op, encoding="utf-8") as fh:
            src = fh.read()
        assert "def _dash_columns_frame(" in src
        assert "def _dash_decode_columns(" in src
