"""Extended missing values .a-.z keep their letter (WP-31 G1).

The data writer wrote every missing value, ``.`` and ``.a`` to ``.z``, as
jsonio's ``null``, so a ``by(, missing)`` graph drew one "(missing)" panel
where twoway draws ``.a`` and ``.b`` apart, a marker label and a tooltip
showed ``.``, and a dropdown offered no code (GAPS3 G1).  The writer now
records each letter in ``extendedMissing``; the reader turns it into a text
column ``__dashm_<var>`` both modes carry.  Truth:
test/fixtures/data_locale_truth.json (scripts/extract_data_locale_truth.do).
"""
import copy
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import dash_render as dr  # noqa: E402
import test_by_axes_keys as tk  # noqa: E402
import test_by_grid as tg  # noqa: E402
from by_panel_probe import panel_label  # noqa: E402
from js_runner import mask_parity  # noqa: E402

_FIX = os.path.join(os.path.dirname(__file__), "fixtures",
                    "data_locale_truth.json")
MODES = ("saved", "served")


def _truth():
    with open(_FIX, encoding="utf-8") as fh:
        return json.load(fh)


def _data(labelled=False):
    """by_grid's auto data with rep78's five missing rows coded as the
    extractor codes them: the first two .a, the other three .b."""
    data = copy.deepcopy(tg._data())
    miss = [i for i, r in enumerate(data["values"])
            if not isinstance(r.get("rep78"), float)]
    assert len(miss) == 5
    data["extendedMissing"] = {"rep78": {
        str(i): ("a" if k < 2 else "b") for k, i in enumerate(miss)}}
    if labelled:
        data["valueLabels"]["rl"] = {
            str(dr._DASH_MISSING_LABEL_KEY + 1): "Not asked"}
        data["valueLabelNames"]["rep78"] = "rl"
    return data


def _scatter(**opts):
    return [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
             "options": dict(opts)}]


def _build(mode, plots, go, data, filt=""):
    spec = tk._spec([tk._graph("g", plots, go)], scheme="s2color",
                    filt=filt)
    return tk._build(mode, spec, data=data)


def _sources(roots):
    from bokeh.models import ColumnDataSource
    out = []
    for root in roots:
        for m in root.references():
            if isinstance(m, ColumnDataSource):
                out.append(m)
    return out


def _panel_titles(roots):
    from bokeh.models import GridPlot
    best = []
    for root in roots:
        for m in root.references():
            if isinstance(m, GridPlot):
                got = [panel_label(c[0]) for c in m.children
                       if type(c[0]).__name__ == "figure"
                       and panel_label(c[0])]
                if len(got) > len(best):
                    best = got
    return best


class TestTheFixture:
    def test_meta(self):
        t = _truth()
        assert sorted(t["_meta"]) == ["born_date", "dash_commit",
                                      "extracted", "source",
                                      "stata_version"]
        assert t["_meta"]["source"] == "scripts/extract_data_locale_truth.do"
        assert t["em.by_missing"]["rc"] == 0


class _Missing:
    """sfi.Missing's numbers: . is 2^1023, .a .. .z the 26 after it."""
    _BASE = 8.98846567431158e307

    @classmethod
    def getValue(cls, val=None):
        if val in (None, "."):
            return cls._BASE
        return float(np.nextafter(cls._BASE, np.inf)) * (
            1 + (ord(val[1]) - ord("a") + 1) * 1e-15)


class _Sfi:
    """A stand-in for Stata's interface holding one numeric variable."""

    def __init__(self, raw):
        fake = self
        self.raw = raw

        class Data:
            @staticmethod
            def getObsTotal():
                return len(fake.raw)

            @staticmethod
            def isVarTypeString(v):
                return False

            @staticmethod
            def getVarType(v):
                return "byte"

            @staticmethod
            def isVarTypeStrL(v):
                return False

            @staticmethod
            def getVarIndex(v):
                return 0

            @staticmethod
            def get(var, missingval="default"):
                if missingval is None:
                    return [None if x >= _Missing._BASE else x
                            for x in fake.raw]
                return list(fake.raw)

            @staticmethod
            def getVarLabel(v):
                return ""

            @staticmethod
            def getFormattedValue(j, i, vl):
                # Stata's display text: a byte .a is "       .a" in %8.0g
                # (sfi's numeric reads give it as ".").
                x = fake.raw[i]
                if x < _Missing._BASE:
                    return "%8.0g" % x
                for c in "abcdefghijklmnopqrstuvwxyz":
                    if x == _Missing.getValue("." + c):
                        return "      ." + c
                return "       ."

        class ValueLabel:
            @staticmethod
            def getVarValueLabel(v):
                return ""

        class SFIToolkit:
            @staticmethod
            def stata(cmd):
                raise AssertionError(cmd)

        self.Data, self.ValueLabel, self.SFIToolkit = Data, ValueLabel, \
            SFIToolkit
        self.Missing = _Missing


class TestTheDataPath:
    def test_writer_emits_codes(self, tmp_path):
        raw = [1.0, _Missing.getValue(".a"), _Missing.getValue("."),
               _Missing.getValue(".b"), 3.0]
        path = tmp_path / "d.json"
        assert dr._dash_write_stata_data(str(path), "rep78",
                                         sfi=_Sfi(raw)) == ""
        doc = json.loads(path.read_text())
        # Flipped (WP-32, G3b): the values are a binary column, each
        # missing one a NaN.
        got = dr._dash_read_data_json(path.read_text())["columns"]["rep78"]
        assert np.array_equal(got, [1.0, np.nan, np.nan, np.nan, 3.0],
                              equal_nan=True)
        assert doc["extendedMissing"] == {"rep78": {"1": "a", "3": "b"}}

    def test_writer_omits_the_key_without_codes(self, tmp_path):
        path = tmp_path / "d.json"
        dr._dash_write_stata_data(str(path), "rep78", sfi=_Sfi(
            [1.0, _Missing.getValue(".")]))
        assert "extendedMissing" not in json.loads(path.read_text())

    def test_loader_builds_code_column(self):
        doc = dr._dash_read_data_json(json.dumps(_data()))
        assert "__dashm_rep78" in doc["variableNames"]
        assert doc["variableIsString"]["__dashm_rep78"] is True
        codes = [r["__dashm_rep78"] for r in doc["values"]]
        assert codes.count("a") == 2 and codes.count("b") == 3
        assert codes.count("") == len(codes) - 5
        assert "extendedMissing" not in doc

    def test_loader_ignores_bad_codes(self):
        data = _data()
        data["extendedMissing"] = {"rep78": {"2": "A", "999": "a",
                                             "x": "b", "6": "<b>"},
                                   "nosuch": {"1": "a"}}
        doc = dr._dash_read_data_json(json.dumps(data))
        assert "__dashm_rep78" not in doc["variableNames"]
        assert "__dashm_nosuch" not in doc["variableNames"]


class TestByMissing:
    @pytest.mark.parametrize("mode", MODES)
    def test_panels(self, mode):
        roots, _n, _o = _build(mode, _scatter(), {"by": "rep78, missing"},
                               _data())
        want = _truth()["em.by_missing"]
        assert _panel_titles(roots) == want["titles"]
        assert len(_panel_titles(roots)) == want["panels"]

    @pytest.mark.parametrize("mode", MODES)
    def test_labelled(self, mode):
        roots, _n, _o = _build(mode, _scatter(), {"by": "rep78, missing"},
                               _data(labelled=True))
        assert _panel_titles(roots) == \
            _truth()["em.by_missing_labelled"]["titles"]


class TestLabelsAndTooltips:
    @pytest.mark.parametrize("mode", MODES)
    def test_mlabel(self, mode):
        roots, _n, _o = _build(mode, _scatter(mlabel="rep78"), {}, _data())
        col = dr._DASH_MLABEL_PREFIX + "rep78"
        texts = [t for s in _sources(roots) if col in s.data
                 for t in s.data[col]]
        got = {t: texts.count(t) for t in set(texts) if t.startswith(".")}
        assert got == _truth()["em.mlabel"]["labels"]

    @pytest.mark.parametrize("mode", MODES)
    def test_tooltip_column_is_carried(self, mode):
        from bokeh.models import HoverTool
        roots, _n, _o = _build(mode, _scatter(), {"hover": "rep78"},
                               _data())
        srcs = [s for s in _sources(roots) if "__dasht_rep78" in s.data]
        assert srcs, mode
        vals = list(srcs[0].data["__dasht_rep78"])
        assert vals.count(".a") == 2 and vals.count(".b") == 3
        assert "3" in vals
        fields = [f for root in roots for m in root.references()
                  if isinstance(m, HoverTool)
                  for _l, f in (m.tooltips or [])]
        assert "@{__dasht_rep78}" in fields
        assert not any("__dasht_rep78" in f and "{custom}" in f
                       for f in fields)

    def test_served_tooltip_label(self):
        roots, _n, _o = _build("served", _scatter(), {"hover": "rep78"},
                               _data(labelled=True))
        vals = [v for s in _sources(roots)
                for c in s.data if c.startswith("__dash_hover_rep78")
                for v in s.data[c]]
        assert vals.count("Not asked") == 2 and vals.count(".b") == 3


def _dropdown(roots):
    from bokeh.models import Select
    for root in roots:
        for m in root.references():
            if isinstance(m, Select):
                return m
    return None


class TestFilters:
    @pytest.mark.parametrize("mode", MODES)
    def test_options(self, mode):
        roots, _n, _o = _build(mode, _scatter(), {}, _data(),
                               filt="rep78, type(dropdown)")
        w = _dropdown(roots)
        assert w is not None
        opts = [tuple(o) if isinstance(o, (list, tuple)) else (o, o)
                for o in w.options]
        assert ("__dashm_rep78=a", ".a") in opts
        assert ("__dashm_rep78=b", ".b") in opts

    def test_move(self):
        df = pd.DataFrame({"rep78": [1.0, np.nan, np.nan, 3.0, np.nan],
                           "__dashm_rep78": ["", "a", "", "", "b"]})
        spec = {"varname": "rep78", "type": "dropdown",
                "sentinel": "__all__", "numeric": True}
        js, py = mask_parity(df, [spec], ["__dashm_rep78=a"])
        assert js == [False, True, False, False, False]
        assert py == js
        js, py = mask_parity(df, [spec], ["__dashm_rep78=b"])
        assert js == py == [False, False, False, False, True]


class TestAfterAMove:
    def test_saved(self):
        roots, _n, owner = _build("saved", _scatter(), {"hover": "rep78"},
                                  _data(), filt="rep78, type(dropdown)")
        # The snapshot every move rebuilds from carries the code column,
        # so the mask and the tooltip text follow the rows.
        assert any("__dashm_rep78" in s.data and len(s.data["__dashm_rep78"])
                   == 74 for s in _sources(roots))

    def test_served(self):
        roots, _n, doc = _build("served", _scatter(), {"hover": "rep78"},
                                _data(), filt="rep78, type(dropdown)")
        w = _dropdown(roots)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            w.value = "__dashm_rep78=b"
        srcs = [s for s in _sources(roots) if "__dashm_rep78" in s.data
                and "mpg" in s.data and len(s.data["mpg"]) < 74]
        assert srcs
        assert set(srcs[0].data["__dashm_rep78"]) == {"b"}

    def test_served_redraw_keeps_the_text(self):
        # An aggregate layer's served redraw rebuilds its source from the
        # frame, which carries no derived column; the coded tooltip text
        # follows its rows from the snapshot (a variable without labels).
        snap = {"index": [10, 11, 12], "rep78": [3.0, np.nan, np.nan],
                "__dasht_rep78": ["3", ".a", "."]}
        new = {"index": [12, 11], "rep78": [np.nan, np.nan]}
        got = dr._dash_keep_jitter(new, snap)
        assert got["__dasht_rep78"] == [".", ".a"]


class TestHelpers:
    def test_code_text(self):
        key = str(dr._DASH_MISSING_LABEL_KEY + 2)
        assert dr._dash_code_text("b", {key: "Refused"}) == "Refused"
        assert dr._dash_code_text("a", {key: "Refused"}) == ".a"
        assert dr._dash_code_text("z") == ".z"

    def test_add_code_text(self):
        from bokeh.models import ColumnDataSource
        src = ColumnDataSource({"v": [1234.5, np.nan, np.nan],
                                "__dashm_v": ["", "c", ""]})
        assert dr._dash_add_code_text(src, "v", "%9.1fc") == "__dasht_v"
        assert src.data["__dasht_v"] == ["1,234.5", ".c", "."]
        assert dr._dash_add_code_text(ColumnDataSource({"v": [1.0]}),
                                      "v") is None

    def test_with_codes(self):
        assert dr._dash_with_codes(["a", "b"], ["a", "b", "__dashm_b"]) == \
            ["a", "b", "__dashm_b"]
        assert dr._dash_with_codes(["a"], ["a"]) == ["a"]

    def test_attach_without_the_key_changes_nothing(self):
        doc = {"variableNames": ["v"], "values": [{"v": 1.0}]}
        assert dr._dash_attach_missing_codes(copy.deepcopy(doc)) == doc
