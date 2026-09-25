"""test_data_file_numbers.py -- a number in the data file is read as Stata
holds it, in both loaders (BUGS.md, S3 batch: "A 401-digit integer in the
data file stops both loaders").

Stata holds every number as a double, or as missing: the largest double is
about 8.99e307, and Stata has no infinity or NaN.  dash's own writer
(``_dash_write_stata_data``) writes every number as a double, so an integer
literal -- or one too large for a double -- reaches the loaders only from a
hand-written or corrupted file.  Python's JSON reader made such a literal an
int of any size; ``pd.DataFrame`` then stopped with OverflowError (an int
beyond int64), and past 4300 digits the reader itself stopped with
ValueError.  Both loaders now read the file through
``_dash_read_data_json``: an integer is the double Stata would hold, a value
beyond a double's range and the NaN/Infinity literals are missing.
"""
import json
import os
import sys
import time
import warnings

import numpy as np
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import make_spec  # noqa: E402

_SCATTER = {"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}
_BIG = "9" * 401


def _data_text(literals):
    """A data file whose ``y`` holds each of *literals* verbatim (x = 1..n),
    written as text so a literal Python's writer would not emit survives."""
    payload = {"StataJSON": {
        "variableNames": ["y", "x"],
        "variableLabels": {"y": "y", "x": "x"},
        "valueLabels": {}, "valueLabelNames": {},
        "variableIsString": {"y": False, "x": False},
        "values": [{"y": "@@%d@@" % i, "x": float(i + 1)}
                   for i in range(len(literals))],
    }}
    text = json.dumps(payload)
    for i, lit in enumerate(literals):
        text = text.replace('"@@%d@@"' % i, lit)
    return text


def _files(tmp_path, literals):
    sp = os.path.join(str(tmp_path), "spec.json")
    dp = os.path.join(str(tmp_path), "data.json")
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(make_spec([dict(_SCATTER)]), fh)
    with open(dp, "w", encoding="utf-8") as fh:
        fh.write(_data_text(literals))
    return sp, dp


def _saved_y(tmp_path, literals):
    sp, dp = _files(tmp_path, literals)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = dr.DashRenderer(sp, dp)
        r.render()
    return np.asarray(r.df["y"], dtype=float), r


def _served_y(tmp_path, literals):
    sp, dp = _files(tmp_path, literals)
    op = os.path.join(str(tmp_path), "app.py")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(op)
    with open(op, encoding="utf-8") as fh:
        src = fh.read()
    ns: dict = {}
    exec(compile(src.split("if __name__ !=")[0], op, "exec"), ns)
    _spec, df, _meta = ns["_load_spec_and_data"]()
    return np.asarray(df["y"], dtype=float)


_CASES = [
    # (literal, what Stata holds)
    (_BIG, np.nan),                          # beyond a double: missing
    ("-" + _BIG, np.nan),
    ("1e400", np.nan),
    ("-1e400", np.nan),
    ("NaN", np.nan),                         # no NaN or infinity in Stata
    ("Infinity", np.nan),
    ("-Infinity", np.nan),
    (str(2 ** 60 + 1), float(2 ** 60)),      # the double nearest
    (str(10 ** 300), 1e300),
    ("-" + str(10 ** 20 + 7), -1e20),
    ("12", 12.0),
    ("2.5", 2.5),
]
_IDS = ["401_digits", "minus_401_digits", "1e400", "minus_1e400", "NaN",
        "Infinity", "minus_Infinity", "2_60_plus_1", "1e300_as_int",
        "minus_1e20_plus_7", "small_int", "float"]


def _same(got, want):
    return (np.isnan(got) and np.isnan(want)) or got == want


class TestBothLoadersReadANumberAsStataHoldsIt:

    @pytest.mark.parametrize("lit,want", _CASES, ids=_IDS)
    def test_the_saved_loader(self, tmp_path, lit, want):
        y, _r = _saved_y(tmp_path, [lit, "3.0"])
        assert len(y) == 2
        assert _same(y[0], want), (lit[:30], y[0], want)
        assert y[1] == 3.0

    @pytest.mark.parametrize("lit,want", _CASES, ids=_IDS)
    def test_the_served_loader(self, tmp_path, lit, want):
        y = _served_y(tmp_path, [lit, "3.0"])
        assert len(y) == 2
        assert _same(y[0], want), (lit[:30], y[0], want)
        assert y[1] == 3.0

    def test_the_saved_page_draws_the_other_rows(self, tmp_path):
        """The row Stata holds as missing is not drawn; the rest are."""
        _y, r = _saved_y(tmp_path, [_BIG, "3.0", "4.0"])
        rend = r.figures["g1"].renderers[0]
        ys = list(rend.data_source.data[rend.glyph.y])
        assert sorted(v for v in ys if v == v) == [3.0, 4.0]


class TestTheReader:
    """``_dash_read_data_json`` itself."""

    def test_a_small_integer_stays_an_integer(self):
        """jsonio's metadata -- numberOfRecords, firstRecordId -- and an
        old file's integer values keep the type they had."""
        got = dr._dash_read_data_json('{"n": 74, "v": [1, -3, 0]}')
        assert got == {"n": 74, "v": [1, -3, 0]}
        assert all(type(v) is int for v in got["v"]) and type(got["n"]) is int

    def test_an_integer_beyond_2_53_is_the_nearest_double(self):
        got = dr._dash_read_data_json("[9007199254740993]")
        assert got == [9007199254740992.0] and type(got[0]) is float

    def test_every_out_of_range_value_is_missing(self):
        got = dr._dash_read_data_json(
            "[%s, 1e309, -1e309, NaN, Infinity, -Infinity]" % _BIG)
        assert got == [None] * 6

    def test_a_float_is_read_as_before(self):
        got = dr._dash_read_data_json("[0.1, -2.5e-300, 1.7976931348623157e308]")
        assert got == [0.1, -2.5e-300, 1.7976931348623157e308]

    def test_text_is_left_alone(self):
        got = dr._dash_read_data_json('{"s": "NaN", "t": "%s"}' % _BIG)
        assert got == {"s": "NaN", "t": _BIG}

    def test_the_served_app_carries_the_reader(self, tmp_path):
        sp, dp = _files(tmp_path, ["1.0"])
        op = os.path.join(str(tmp_path), "app.py")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(op)
        with open(op, encoding="utf-8") as fh:
            src = fh.read()
        assert "def _dash_read_data_json(" in src
        assert "_dash_read_data_json(base64.b64decode(_DATA_B64)" in src


class TestAdversarialNumbers:
    """Resource exhaustion through a number: bounded time, no stop."""

    def test_a_million_digit_integer(self, tmp_path):
        lit = "7" * 1_000_000
        t0 = time.perf_counter()
        y, _r = _saved_y(tmp_path, [lit, "3.0"])
        ys = _served_y(tmp_path, [lit, "3.0"])
        assert time.perf_counter() - t0 < 60.0
        assert np.isnan(y[0]) and y[1] == 3.0
        assert np.isnan(ys[0]) and ys[1] == 3.0

    def test_a_million_digit_fraction_and_exponent(self):
        lits = ["0." + "0" * 999_999 + "1", "1" + "0" * 999_999 + "e-999990",
                "1e" + "9" * 100_000, "-1e-" + "9" * 100_000]
        t0 = time.perf_counter()
        got = dr._dash_read_data_json("[%s]" % ", ".join(lits))
        assert time.perf_counter() - t0 < 30.0
        assert got[0] == 0.0 and got[1] == 1e9
        assert got[2] is None and got[3] == 0.0

    def test_many_huge_integers(self):
        """Two thousand 5,000-digit integers (10 MB): each past Python's
        4,300-digit integer limit, which stopped the reader."""
        text = "[%s]" % ", ".join(["8" * 5000] * 2000)
        t0 = time.perf_counter()
        got = dr._dash_read_data_json(text)
        assert time.perf_counter() - t0 < 30.0
        assert got == [None] * 2000

    def test_a_numeric_column_holding_the_text_infinity_is_missing(
            self, tmp_path):
        """Text in a numeric column is coerced by _dash_load_columns;
        'Infinity' became inf, a value Stata cannot hold."""
        y, _r = _saved_y(tmp_path, ['"Infinity"', '"-inf"', "3.0"])
        assert np.isnan(y[0]) and np.isnan(y[1]) and y[2] == 3.0
        ys = _served_y(tmp_path, ['"Infinity"', '"-inf"', "3.0"])
        assert np.isnan(ys[0]) and np.isnan(ys[1]) and ys[2] == 3.0
