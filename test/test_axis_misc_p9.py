"""
test_axis_misc_p9.py
WP-44 section 44-05: a lone second axis drawn without gridlines (MS-12) and
the words twoway refuses in an axis label list (DG-9).

twoway draws axis 2 and higher in the ``*_nogrid`` axis style
(twowaygraph_g.class ``create_axes``; ``style/axisstyle-vertical_nogrid.style``
``set draw_major_grid no``).  The truth is test/fixtures/axis_misc_truth.json
(scripts/extract_axis_misc_truth.do): ``ms12.y2`` -- ``scatter mpg weight,
yaxis(2)`` -- has no gridline, ``ms12.control`` and ``ms12.y2_grid``
(``ylabel(, grid axis(2))``) have them.

Run with:  pytest test/test_axis_misc_p9.py -q -n0
"""
import importlib.util as _ilu
import itertools as _it
import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import dash_render as _dr  # noqa: E402

_ROOT = os.path.join(os.path.dirname(__file__), "..")
_TRUTH = os.path.join(_ROOT, "test", "fixtures", "axis_misc_truth.json")
_MODES = ("saved", "served")
_SEQ = _it.count()


def _truth():
    with open(_TRUTH, encoding="utf-8") as fh:
        return json.load(fh)


def _grid_strokes(row, kind):
    """The non-black strokes of a key's horizontal (y grid) or vertical
    (x grid) lines: twoway's gridlines (axis lines and ticks are black)."""
    return sorted({ln["stroke"] for ln in row.get(kind, [])
                   if ln.get("stroke") not in (None, "#000000")})


def _spec(plots, graph_opts=None):
    data = {"x": [float(v) for v in range(1, 21)],
            "y": [float(v * 3 % 17) for v in range(1, 21)]}
    data_json = {"StataJSON": {
        "variableNames": list(data),
        "variableLabels": {k: k for k in data},
        "valueLabels": {}, "valueLabelNames": {},
        "variableTypeIsString": {k: False for k in data},
        "values": [{k: data[k][i] for k in data} for i in range(20)]}}
    go = {"name": "fig1"}
    go.update(graph_opts or {})
    spec = {"graphs": [{"plots": plots, "graph_options": go,
                        "if_expr": "", "in_expr": ""}],
            "kpis": [],
            "build_options": {"layout": "auto", "link": "", "filter": "",
                              "theme": "default", "title": "",
                              "subtitle": "", "registry": "fig1"}}
    return spec, data_json


def _write(plots, graph_opts=None):
    spec, data_json = _spec(plots, graph_opts)
    d = tempfile.mkdtemp(prefix="dash_p9_")
    sp, dp = os.path.join(d, "spec.json"), os.path.join(d, "data.json")
    with open(sp, "w") as f:
        json.dump(spec, f)
    with open(dp, "w") as f:
        json.dump(data_json, f)
    return d, sp, dp


def _figure(mode, plots, graph_opts=None):
    """The one figure the saved renderer or the served app draws."""
    from bokeh.document import Document
    from bokeh.plotting import figure as _fig_cls
    d, sp, dp = _write(plots, graph_opts)
    if mode == "saved":
        return list(_dr.DashRenderer(sp, dp)._build_figures().values())[0]
    ap = os.path.join(d, "app.py")
    _dr.ServerAppBuilder(sp, dp).build(ap)
    ms = _ilu.spec_from_file_location("_p9_app_%d" % next(_SEQ), ap)
    mod = _ilu.module_from_spec(ms)
    ms.loader.exec_module(mod)
    doc = Document()
    mod.make_document(doc)
    figs = [m for root in doc.roots for m in root.references()
            if isinstance(m, _fig_cls)]
    assert len(figs) == 1, figs
    return figs[0]


def _colours(grids):
    return [g.grid_line_color for g in grids]


def _scatter(**opts):
    return [{"type": "scatter", "yvar": "y", "xvar": "x", "options": opts}]


_PCI = [{"type": "pci", "options": {"yaxis": "2"},
         "values": [[20.0, 3000.0, 30.0, 4000.0]]}]


@pytest.mark.parametrize("mode", _MODES)
class TestLoneAxisGrid:
    """MS-12: a graph whose every layer is on yaxis(2) (or xaxis(2), or a
    third .. ninth axis) draws that axis in its own default look -- no
    gridlines unless asked -- as twoway draws it."""

    def test_no_grid(self, mode):
        t = _truth()
        assert _grid_strokes(t["ms12.y2"], "hlines") == []
        assert _grid_strokes(t["ms12.y3"], "hlines") == []
        assert _grid_strokes(t["ms12.y2_stcolor"], "hlines") == []
        assert _grid_strokes(t["ms12.y2_y3"], "hlines") == []
        for plots, go in ((_scatter(yaxis="2"), None),
                          (_scatter(yaxis="3"), None),
                          (_scatter(yaxis="2"), {"scheme": "stcolor"}),
                          (_scatter(yaxis="2") + _scatter(yaxis="3"), None)):
            fig = _figure(mode, plots, go)
            assert _colours(fig.ygrid) == [None] * len(fig.ygrid), (plots,
                                                                    go)

    def test_grid_when_asked(self, mode):
        """ylabel(, grid axis(2)) -- dash's internal ylabel2 after the
        axis(2) route -- still draws the grid (ms12.y2_grid)."""
        assert _grid_strokes(_truth()["ms12.y2_grid"], "hlines") \
            == ["#eaf2f3"]
        fig = _figure(mode, _scatter(yaxis="2"), {"ylabel2": ", grid"})
        assert [c for c in _colours(fig.ygrid) if c is not None]

    def test_pci_lone_axis(self, mode):
        assert _grid_strokes(_truth()["ms12.pci_y2"], "hlines") == []
        fig = _figure(mode, _PCI)
        assert _colours(fig.ygrid) == [None] * len(fig.ygrid)

    def test_axis_one_unchanged(self, mode):
        """Control: a graph on axis 1 keeps the scheme's y grid
        (ms12.control), and a lone yaxis(2) keeps the x axis's look."""
        assert _grid_strokes(_truth()["ms12.control"], "hlines") \
            == ["#eaf2f3"]
        fig = _figure(mode, _scatter())
        assert [c for c in _colours(fig.ygrid) if c is not None]
        fig = _figure(mode, _scatter(yaxis="2"), {"scheme": "stcolor"})
        assert _grid_strokes(_truth()["ms12.y2_stcolor"], "vlines") \
            == ["#f0f0f0"]
        assert [c for c in _colours(fig.xgrid) if c is not None]

    def test_lone_x_axis(self, mode):
        """Under stcolor, whose first x axis draws a grid, a lone xaxis(2)
        draws none (ms12.x2_stcolor beside ms12.control_stcolor)."""
        t = _truth()
        assert _grid_strokes(t["ms12.control_stcolor"], "vlines") \
            == ["#f0f0f0"]
        assert _grid_strokes(t["ms12.x2_stcolor"], "vlines") == []
        fig = _figure(mode, _scatter(xaxis="2"), {"scheme": "stcolor"})
        assert _colours(fig.xgrid) == [None] * len(fig.xgrid)
        assert [c for c in _colours(fig.ygrid) if c is not None]

    def test_served_reads_the_marker(self, mode):
        """The marker _dash_lone_second_axes writes is in the spec both
        modes draw from, and the served app carries the function that
        reads it."""
        spec, _ = _spec(_scatter(yaxis="2"))
        out = _dr._dash_lone_second_axes(spec)
        assert out["graphs"][0]["graph_options"]["_dash_lone_from"] \
            == {"y": 2}
        assert "_dash_lone_from" not in spec["graphs"][0]["graph_options"]
        if mode == "served":
            d, sp, dp = _write(_scatter(yaxis="2"))
            ap = os.path.join(d, "app.py")
            _dr.ServerAppBuilder(sp, dp).build(ap)
            with open(ap, encoding="utf-8") as fh:
                src = fh.read()
            assert "def _dash_lone_axis_look(" in src
            assert '"_dash_lone_from"' in src


class TestLoneAxisLook:
    """_dash_lone_axis_look on its own: the grid of a dimension whose drawn
    axis 1 came from axis k >= 2 goes off when the scheme's axis-2 style
    draws no major grid."""

    def _fig(self):
        from bokeh.plotting import figure
        fig = figure()
        for g in list(fig.xgrid) + list(fig.ygrid):
            g.grid_line_color = "#eaf2f3"
        return fig

    def test_no_marker_no_change(self):
        fig = self._fig()
        _dr._dash_lone_axis_look(fig, {})
        assert _colours(fig.ygrid) == ["#eaf2f3"]
        assert _colours(fig.xgrid) == ["#eaf2f3"]

    def test_marker_turns_that_grid_off(self):
        fig = self._fig()
        _dr._dash_lone_axis_look(fig, {"_dash_lone_from": {"y": 3}})
        assert _colours(fig.ygrid) == [None]
        assert _colours(fig.xgrid) == ["#eaf2f3"]

    def test_a_withgrid_style_keeps_it(self):
        class _S:
            axis_styles = {("y", 2): "vertical_withgrid",
                           ("x", 2): "horizontal_nogrid"}
        fig = self._fig()
        _dr._dash_lone_axis_look(fig, {"_dash_lone_from": {"y": 2, "x": 2}},
                                 scheme=_S())
        assert _colours(fig.ygrid) == ["#eaf2f3"]
        assert _colours(fig.xgrid) == [None]

    def test_a_bad_marker_is_ignored(self):
        fig = self._fig()
        for bad in ("y", {"y": "2"}, {"y": True}, {"y": 1}, {"z": 2}, None):
            _dr._dash_lone_axis_look(fig, {"_dash_lone_from": bad})
        assert _colours(fig.ygrid) == ["#eaf2f3"]


class TestLabelWords:
    """DG-9: twoway reads each run of a label or tick list between its
    labels with numlist (_gs_parse_and_log_tickset.ado NumTextList), so a
    bare word, .a or a date function is refused r(198); dash refuses it at
    registration (test_option_validation.cscript Q4405-2, Q4405-3, from
    axis_misc_truth.json dg9.*)."""

    def test_the_help_sentence(self):
        import re
        with open(os.path.join(_ROOT, "dash.sthlp"), encoding="utf-8") as fh:
            text = re.sub(r"\s+", " ", fh.read())
        assert ("a word that is no value, form, rule or label is refused as "
                "{cmd:twoway} refuses it ({cmd:invalid label specifier}, "
                "{cmd:r(198)})") in text
        assert "a word that is no value, form, rule or label is named in " \
            "the note" not in text

    def test_the_truth_refuses_words(self):
        """The fixture's twoway answers the cscript compares with."""
        t = _truth()
        for k in ("dg9.T11", "dg9.abc_xlabel", "dg9.abc_ymtick",
                  "dg9.dot_a", "dg9.accept_td", "dg9.fn_word"):
            assert t[k]["rc"] == 198, k
            assert t[k]["raw_message"].startswith(
                "invalid label specifier, :  "), k
        assert t["dg9.T11"]["raw_message"] \
            == "invalid label specifier, :  1/5 .a:"
        for k in ("dg9.accept_neg", "dg9.accept_exp", "dg9.accept_to",
                  "dg9.accept_spaced_rule", "dg9.accept_lead_dot_rule"):
            assert t[k]["rc"] == 0, k
