"""
test_value_labels_drawn.py -- GAPS2 G16 (WP-28 S14): value labels on axes
through ``valuelabel`` (minimum ``val``) and in ``hover()`` tooltips.

Before the fix (measured at 91d97be): `xlabel(1/5, valuelabel)` was named
("sub-option(s) not implemented and ignored: valuelabel") and drew 1..5;
`hover(foreign)` showed 0/1 where list and browse show Domestic/Foreign.
twoway's reading is test/fixtures/axis_truth.json, group g16_valuelabel.
"""
import os
import re
import sys
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_axis_label_grammar import (  # noqa: E402
    _MODES, _figures, _rep_frame, _sc, _xaxis, _ticks, truth)
from test_server_layer_defects import plot_for  # noqa: E402

_LABELS = {1.0: "Poor", 2.0: "Fair", 3.0: "Average", 4.0: "Good",
           5.0: "Excellent"}


def _rep(mode, tmp_path, go, plots=None, record=None):
    df, vl, names = _rep_frame()
    return _figures(mode, tmp_path, df, plots or [_sc(x="rep78")], go,
                    value_labels=vl, label_names=names, record=record)


class TestValueLabelsOnAxes:
    @pytest.mark.parametrize("mode", _MODES)
    def test_valuelabel_draws_the_label_set(self, mode, tmp_path):
        rec = []
        fig = _rep(mode, tmp_path, {"xlabel": "1/5, valuelabel"},
                   record=rec)[0]
        ax = _xaxis(fig)
        assert dict(ax.major_label_overrides) == _LABELS
        assert not [w for w in rec if "sub-option" in w], rec

    @pytest.mark.parametrize("mode", _MODES)
    def test_val_is_the_minimum_abbreviation(self, mode, tmp_path):
        fig = _rep(mode, tmp_path, {"xlabel": "1/5, val"})[0]
        assert dict(_xaxis(fig).major_label_overrides) == _LABELS
        assert not dr._dash_parse_axis_spec("1/5, va")["valuelabel"]

    def test_an_unlabelled_code_keeps_its_number(self, tmp_path):
        fig = _rep("saved", tmp_path, {"xlabel": "0/6, valuelabel"})[0]
        ax = _xaxis(fig)
        assert _ticks(ax) == [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        ov = dict(ax.major_label_overrides)
        assert 0.0 not in ov and 6.0 not in ov and ov[3.0] == "Average"

    @pytest.mark.parametrize("mode", _MODES)
    def test_y_options_map_through_the_first_y_variable(self, mode,
                                                        tmp_path):
        fig = _rep(mode, tmp_path, {"ylabel": "1/5, valuelabel"},
                   [_sc(y="rep78", x="mpg")])[0]
        left = [a for a in fig.left
                if getattr(a, "y_range_name", "default") == "default"][0]
        assert dict(left.major_label_overrides) == _LABELS

    @pytest.mark.parametrize("mode", _MODES)
    def test_ylabel2_maps_through_the_second_axis_layer(self, mode,
                                                        tmp_path):
        fig = _rep(mode, tmp_path, {"ylabel2": "1/5, valuelabel"},
                   [_sc(), _sc(y="rep78", yaxis="2")])[0]
        right = [a for a in fig.right
                 if getattr(a, "y_range_name", "") == "y2"][0]
        assert dict(right.major_label_overrides) == _LABELS

    def test_explicit_text_and_a_value_label_on_one_tick(self, truth,
                                                        tmp_path):
        # twoway (probe g16_vl_mixed): the explicit "one" wins at 1.
        assert "one" in truth["probes"]["g16_vl_mixed"]["texts"]
        assert "Poor" not in truth["probes"]["g16_vl_mixed"]["texts"]
        fig = _rep("saved", tmp_path,
                   {"xlabel": '1 "one" 2/5, valuelabel'})[0]
        ov = dict(_xaxis(fig).major_label_overrides)
        assert ov[1.0] == "one" and ov[2.0] == "Fair"

    @pytest.mark.parametrize("mode", _MODES)
    def test_without_valuelabel_nothing_changes(self, mode, tmp_path):
        fig = _rep(mode, tmp_path, {"xlabel": "1/5"})[0]
        assert not dict(_xaxis(fig).major_label_overrides)

    def test_the_default_ticker_keeps_its_formatter(self, tmp_path):
        from bokeh.models import FixedTicker
        fig = _rep("saved", tmp_path, {"xlabel": ", valuelabel"})[0]
        ax = _xaxis(fig)
        assert not isinstance(ax.ticker, FixedTicker)
        assert dict(ax.major_label_overrides) == _LABELS

    @pytest.mark.parametrize("mode", _MODES)
    def test_by_panels_each_carry_the_overrides(self, mode, tmp_path):
        figs = _rep(mode, tmp_path, {"xlabel": "1/5, valuelabel",
                                     "by": "foreign"})
        assert len(figs) >= 2
        for f in figs:
            assert dict(_xaxis(f).major_label_overrides) == _LABELS

    def test_every_g16_probe_draws_the_texts_twoway_drew(self, truth):
        p = truth["probes"]
        for pid in ("g16_vl_slash", "g16_vl_abbrev", "g16_vl_default",
                    "g16_vl_y"):
            for t in _LABELS.values():
                assert t in p[pid]["texts"], (pid, t)
        assert p["g16_vl_by"]["texts"].count("Excellent") == 2
        assert "0" in p["g16_vl_unlabelled"]["texts"]
        assert "Poor" not in p["g16_vl_off"]["texts"]


class TestTheLookup:
    def test_by_set_name(self):
        assert dr._dash_value_labels_for(
            "r", {"rl": {"0": "Zero"}}, {"r": "rl"}) == {"0": "Zero"}

    def test_by_variable_name_as_jsonio_writes_it(self):
        assert dr._dash_value_labels_for(
            "r", {"r": {"0": "Zero"}}, {"r": "rl"}) == {"0": "Zero"}

    def test_none(self):
        assert dr._dash_value_labels_for("r", None, None) == {}
        assert dr._dash_value_labels_for("", {"": {"1": "x"}}, {}) == {}

    def test_a_non_dict_is_empty(self):
        assert dr._dash_value_labels_for("r", {"r": "oops"}, {}) == {}
        assert dr._dash_value_labels_for("r", ["x"], "y") == {}

    def test_the_five_copies_are_gone(self):
        with open(os.path.join(_HERE, "..", "dash_render.py"),
                  encoding="utf-8") as fh:
            src = fh.read()
        assert len(re.findall(r"value_labels\.get\(labelset", src)) == 1


def _hover_rows(fig):
    from bokeh.models import HoverTool
    return [t.tooltips for t in fig.tools if isinstance(t, HoverTool)]


class TestHoverShowsValueLabels:
    def _both(self, go, plots=None):
        spec = tp._spec(plots or [tp.plot_for("scatter")], None, go)
        r, _ = tp._standalone(spec)
        doc, _ = tp._served(spec)
        saved = list(r.figures.values())[0]
        served = [m for m in tp._walk_models(doc)
                  if type(m).__name__ == "figure"][0]
        return saved, served

    def test_hover_foreign_shows_domestic_and_foreign(self):
        for fig in self._both({"hover": "foreign"}):
            rows = _hover_rows(fig)[0]
            assert "@{__dash_hover_foreign}" in [v for _k, v in rows], rows
            src = fig.renderers[0].data_source
            assert src.data["__dash_hover_foreign"][:2] == ["Domestic",
                                                            "Foreign"]

    def test_the_column_is_on_every_source_the_tooltip_attaches_to(self):
        for fig in self._both({"hover": "foreign"},
                              [tp.plot_for("scatter"), tp.plot_for("bar")]):
            from bokeh.models import HoverTool
            for t in [t for t in fig.tools if isinstance(t, HoverTool)]:
                fields = [v for _k, v in t.tooltips]
                if "@{__dash_hover_foreign}" not in fields:
                    continue
                for r in t.renderers:
                    assert "__dash_hover_foreign" in r.data_source.data

    def test_the_saved_snapshot_carries_the_column(self):
        spec = tp._spec([tp.plot_for("scatter")], None, {"hover": "foreign"})
        _r, _w, page = tp._standalone_page(spec)
        assert "__dash_hover_foreign" in page
        assert "Domestic" in page

    def test_a_served_redraw_re_adds_the_column(self):
        src = dr.ColumnDataSource(data={"foreign": [0.0, 1.0]})
        dr._dash_add_hover_text(src, "foreign", {"0": "Domestic",
                                                 "1": "Foreign"})
        src.data = {"foreign": [1.0]}      # a redraw from the frame
        assert "__dash_hover_foreign" not in src.data
        dr._dash_add_hover_text(src, "foreign", {"1": "Foreign"})
        assert src.data["__dash_hover_foreign"] == ["Foreign"]
        with open(os.path.join(_HERE, "..", "dash_render.py"),
                  encoding="utf-8") as fh:
            src_text = fh.read()
        at = src_text.index("_live.data = _dash_keep_jitter(")
        assert "_dash_add_hover_text(_live" in src_text[at:at + 600]

    def test_a_hostile_value_label_is_data(self, tmp_path):
        bad = "<img src=x onerror=alert(1)>"
        df, _vl, _n = _rep_frame()
        vl = {"origin": {"0": bad, "1": "ok"}}
        for mode in _MODES:
            fig = _figures(mode, tmp_path, df, [_sc()], {"hover": "foreign"},
                           value_labels=vl,
                           label_names={"foreign": "origin"})[0]
            fields = [v for rows in _hover_rows(fig) for _k, v in rows]
            assert not [f for f in fields if "{safe}" in f]
            assert bad in fig.renderers[0].data_source.data[
                "__dash_hover_foreign"]

    def test_the_parity_cases_with_hover_foreign(self):
        saved, served = self._both({"hover": "foreign"},
                                   [tp.plot_for("bar")])
        assert _hover_rows(saved) == _hover_rows(served)
        a = saved.renderers[0].data_source.data["__dash_hover_foreign"]
        b = served.renderers[0].data_source.data["__dash_hover_foreign"]
        assert list(a) == list(b)

    def test_the_row_helper_takes_text_col_last(self):
        assert dr._dash_hover_row(
            "foreign", "Foreign", text_col="__dash_hover_foreign") == (
            ("Foreign", "@{__dash_hover_foreign}"), None)
        assert dr._dash_hover_text_column("foreign") == "__dash_hover_foreign"
        import inspect
        ps = list(inspect.signature(dr._dash_build_hover).parameters)
        # GAPS2 E3/G6, WP-28 S12: formats, storage_types and fmt_cache are
        # appended after the value-label parameters.
        assert ps[-6:] == ["layers", "value_labels", "value_label_names",
                           "formats", "storage_types", "fmt_cache"]

    def test_no_labels_no_column(self):
        src = dr.ColumnDataSource(data={"mpg": [1.0]})
        assert dr._dash_add_hover_text(src, "price", {"1": "x"}) is None
        src.data["__dash_hover_mpg"] = ["keep"]
        assert dr._dash_add_hover_text(src, "mpg", {"1": "x"}) == \
            "__dash_hover_mpg"
        assert src.data["__dash_hover_mpg"] == ["keep"]
