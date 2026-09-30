"""A served figure had no legend at all.

Not one of the 44 glyph calls in the generated app's plot loop passed
``legend_label``, so Bokeh built nothing. **Measured** on a scatter with an
lfit over it: standalone drew one legend with two items; the served document
drew none, and there was no way to tell the fit from the points.

Two more defects sat behind it, both invisible while there was no legend to
act on:

* the whole ``legend()`` block was emitted **before** the plot loop, so
  ``fig.legend`` was empty when ``legend(position(6))``, ``legend(cols(2))``,
  ``legend(order())`` and ``legend(off)`` were applied;
* ``legend(off)`` was tested with ``_leg_opt == 'off'`` — exact equality —
  so ``legend(pos(6) off)`` did nothing; and ``'on'`` was in the placement
  map, which the standalone renderer had already removed as a bug: ``on`` is
  not a placement.
"""
import importlib.util
import itertools
import json
import os
import sys
import warnings

import pandas as pd
import pytest
from bokeh.document import Document

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
from conftest import make_data_json

_SEQ = itertools.count()
_DF = pd.DataFrame({
    "mpg": [22.0, 18.0, 25.0, 30.0, 21.0, 19.0],
    "weight": [2930.0, 3350.0, 2200.0, 1800.0, 3000.0, 3100.0],
    "foreign": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
})
_TWO = [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}},
        {"type": "lfit", "yvar": "mpg", "xvar": "weight", "options": {}}]
_ONE = [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}]


def _figs(tmp_path, plots, graph_options=None, server=True):
    tag = next(_SEQ)
    go = dict(graph_options or {}, name="g1")
    spec = tmp_path / f"s_{tag}.json"
    data = tmp_path / f"d_{tag}.json"
    spec.write_text(json.dumps({
        "graphs": [{"name": "g1", "graph_options": go, "options": {},
                    "plots": plots}],
        "kpis": [],
        "build_options": {"layout": "auto", "link": "", "filter": "",
                          "theme": "", "scheme": "", "session_scheme": "",
                          "title": "", "subtitle": "", "registry": "g1",
                          "tabs": "", "filter_position": "top",
                          "level": "95", "formats": {}}}))
    data.write_text(json.dumps(make_data_json(_DF)))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if not server:
            r = dr.DashRenderer(str(spec), str(data))
            r.render()
            return list(r.figures.values())
        ap = tmp_path / f"a_{tag}.py"
        dr.ServerAppBuilder(str(spec), str(data)).build(str(ap))
        ms = importlib.util.spec_from_file_location(f"_leg_{tag}", str(ap))
        mod = importlib.util.module_from_spec(ms)
        ms.loader.exec_module(mod)
        doc = Document()
        mod.make_document(doc)
        return [m for m in doc.select({"type": object})
                if type(m).__name__ == "figure"]


def _profile(figs):
    f = figs[0]
    return (len(f.legend),
            [len(l.items) for l in f.legend],
            [l.visible for l in f.legend])


class TestAServedFigureHasALegend:
    def test_two_series(self, tmp_path):
        assert _profile(_figs(tmp_path, _TWO)) == (1, [2], [True])

    def test_it_matches_standalone(self, tmp_path):
        assert (_profile(_figs(tmp_path, _TWO, server=True))
                == _profile(_figs(tmp_path, _TWO, server=False)))

    def test_one_series_builds_a_hidden_legend_like_standalone(self, tmp_path):
        """twoway draws no legend for a single series."""
        assert (_profile(_figs(tmp_path, _ONE, server=True))
                == _profile(_figs(tmp_path, _ONE, server=False))
                == (1, [1], [False]))

    def test_the_labels_name_the_series(self, tmp_path):
        """Stata's keys, which are not the y variable twice.

        This asserted that EVERY key contained "mpg", which was true only
        because the generated app labelled all 38 plot types with the y
        variable -- the very thing that left "no way to tell the fit from
        the points", as this file's own opening paragraph puts it.  Stata
        keys a computed layer "Fitted values"; the saved dashboard has done
        so since WP-02 and the served one does since WP-10.
        """
        f = _figs(tmp_path, _TWO)[0]
        labels = [getattr(i.label, "value", i.label) for i in f.legend[0].items]
        assert labels == ["mpg", "Fitted values"], labels

    def test_the_labels_are_the_ones_the_saved_dashboard_draws(self, tmp_path):
        """The control: one keying rule, not two."""
        def _labels(server):
            f = _figs(tmp_path, _TWO, server=server)[0]
            return [getattr(i.label, "value", i.label)
                    for i in f.legend[0].items]
        assert _labels(True) == _labels(False)

    def test_a_confidence_band_is_keyed_apart_from_its_line(self, tmp_path):
        """One layer, two keys -- and the band's carries the level."""
        plots = [{"type": "lfitci", "yvar": "mpg", "xvar": "weight",
                  "options": {}}]
        f = _figs(tmp_path, plots)[0]
        labels = [getattr(i.label, "value", i.label) for i in f.legend[0].items]
        assert labels == ["95% CI", "Fitted values"], labels

    def test_a_faceted_graph_still_has_one(self, tmp_path):
        figs = _figs(tmp_path, _TWO, {"by": "foreign"})
        assert figs and all(len(f.legend) == 1 for f in figs)


class TestTheLegendOptionsNowReachIt:
    def test_off_is_matched_as_a_word(self, tmp_path):
        """legend(pos(6) off) was compared for exact equality with 'off'."""
        figs = _figs(tmp_path, _TWO, {"legend": "pos(6) off"})
        # The two-series graph draws one legend; all() over an empty legend
        # list is vacuously True, so a graph that drew none would pass this
        # "hidden" check (measured 24sep2026: one legend).
        assert len(figs[0].legend) == 1
        assert all(not l.visible for l in figs[0].legend)

    def test_plain_off_still_works(self, tmp_path):
        figs = _figs(tmp_path, _TWO, {"legend": "off"})
        assert len(figs[0].legend) == 1
        assert all(not l.visible for l in figs[0].legend)

    def test_a_clock_position_is_applied(self, tmp_path):
        """position(6), twoway's own spelling of "below the plot"."""
        figs = _figs(tmp_path, _TWO, {"legend": "position(6)"})
        f = figs[0]
        assert any(l in f.below for l in f.legend)

    def test_a_bare_direction_word_is_not_a_placement(self, tmp_path):
        """legend(bottom) is not twoway's -- it refuses it, "option bottom
        not allowed", r(198), and dash.ado refuses it too (WP-23).  This
        asserted it was applied, at bottom_center INSIDE the plot, where
        twoway places nothing; a spec that carries one is now named and the
        legend left where it would be without it."""
        plain = _figs(tmp_path, _TWO)[0]
        f = _figs(tmp_path, _TWO, {"legend": "bottom"})[0]
        assert [str(l.location) for l in f.legend] == [
            str(l.location) for l in plain.legend]
        assert not any(l.location == "bottom_center" for l in f.legend)

    def test_cols_is_applied(self, tmp_path):
        figs = _figs(tmp_path, _TWO, {"legend": "cols(2)"})
        assert any(getattr(l, "ncols", None) == 2 for l in figs[0].legend)

    def test_label_overrides_the_series_name(self, tmp_path):
        figs = _figs(tmp_path, _TWO, {"legend": 'label(1 "Cars")'})
        labels = [getattr(i.label, "value", i.label)
                  for i in figs[0].legend[0].items]
        assert "Cars" in labels[0]

    def test_order_text_and_a_text_only_row_are_served(self, tmp_path):
        """WP-28 B5: order() text retitles a key and a - inserts a row
        with no renderers, in the served app as in the saved page."""
        figs = _figs(tmp_path, _TWO,
                     {"legend": 'order(1 "Cars" - "Note" 2)'})
        items = figs[0].legend[0].items
        labels = [getattr(i.label, "value", None) or i.label.get("value")
                  for i in items]
        assert labels == ["Cars", "Note", "Fitted values"], labels
        assert list(items[1].renderers) == []
        assert items[0].renderers and items[2].renderers

    def test_lastlabel_is_applied_not_named(self, tmp_path):
        """WP-28 B5: lastlabel() was named as not implemented."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            figs = _figs(tmp_path, _TWO, {"legend": 'lastlabel(2 "L")'})
        items = figs[0].legend[0].items
        labels = [getattr(i.label, "value", None) or i.label.get("value")
                  for i in items]
        assert labels == ["mpg", "L"], labels
        assert not [w for w in caught if "sub-option" in str(w.message)]

    def test_on_is_not_a_placement(self, tmp_path):
        """The standalone renderer removed 'on' from the map as a bug."""
        figs = _figs(tmp_path, _TWO, {"legend": "on"})
        assert len(figs[0].legend) == 1
        assert all(l.visible for l in figs[0].legend)
