"""Bare `dash' draws the empty graph bare `twoway' draws.

dash replaces twoway, so `dash' alone is `twoway' alone, which draws an
empty graph, rc 0, with no plot in its plot region, and takes graph options
and a qualifier with no plot: `twoway, title(T)' draws the title T, and
`twoway if foreign==1' and `twoway ||' are rc 0 too (measured 13oct2026,
test/fixtures/bare_prefix_truth.json bare.*; maintainer decision
14oct2026).  dash refused each, r(198), "dash: empty plot specification."
or "dash: no plot specifications found."  (`dash twoway' and `dash tw' are
`twoway twoway' and `twoway tw', refused: test_parser.cscript TW-01.)

_dash_plot passes allow_empty to _dash_split_segs (dash_parse.mata), which
then returns no segment instead of refusing; the graph registers with
"plots":[] and both renderers draw one figure with no layer and, as twoway
draws it, no axis (WP-35 plot:PT-4: the axes are hidden).
test_parser.cscript TW-02 runs it through Stata against twoway.
"""
import json
import os
import re
import sys
import warnings

import pandas as pd
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import dash_render as dr  # noqa: E402
from conftest import exec_app, make_data_json, make_spec  # noqa: E402
_CURDOC_ATTACH = "if __name__ != '__main__':\n    make_document(curdoc())"


def _read(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as fh:
        return fh.read()


def _figures(tmp_path, mode, title=""):
    """The figures one mode draws for a graph with no plot."""
    from bokeh.document import Document
    from bokeh.plotting import figure as _fig_type
    spec = make_spec([])
    if title:
        spec["graphs"][0]["graph_options"]["title"] = title
    sp, dp, ap = (str(tmp_path / n) for n in ("spec.json", "data.json",
                                              "app.py"))
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    with open(dp, "w", encoding="utf-8") as fh:
        json.dump(make_data_json(pd.DataFrame({"x": [1.0, 2.0]})), fh)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if mode == "saved":
            r = dr.DashRenderer(sp, dp)
            r.render()
            return list(r.figures.values())
        dr.ServerAppBuilder(sp, dp).build(ap)
        with open(ap, encoding="utf-8") as fh:
            src = fh.read()
        assert _CURDOC_ATTACH in src
        ns = {"__name__": "dash_bare_app"}
        doc = Document()
        exec_app(src.replace(_CURDOC_ATTACH, "pass"), "dash_bare_app.py", ns)
        ns["make_document"](doc)
        return list(doc.select({"type": _fig_type}))


class TestTheEmptyGraph:

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_axes_and_no_layer(self, tmp_path, mode):
        # Flipped (WP-35 plot:PT-4): two visible axes on the empty graph
        # were wrong because twoway draws none (command_grammar_truth.json
        # empty.svg.*: no <line>); every axis and grid is hidden.
        from bokeh.models import Axis, GlyphRenderer, Grid
        figs = _figures(tmp_path, mode)
        assert len(figs) == 1, figs
        f = figs[0]
        assert list(f.select({"type": GlyphRenderer})) == []
        axes = list(f.select({"type": Axis}))
        grids = list(f.select({"type": Grid}))
        assert axes and grids, (axes, grids)
        assert not any(m.visible for m in axes + grids), (axes, grids)

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_bokeh_logs_no_missing_renderers(self, tmp_path, mode):
        """twoway draws the empty graph in silence; Bokeh's validation
        warned W-1000 MISSING_RENDERERS into Stata's output."""
        from bokeh.core.validation import check_integrity
        for f in _figures(tmp_path, mode):
            issues = check_integrity(list(f.references()))
            names = [w.name for w in issues.warning]
            assert "MISSING_RENDERERS" not in names, names

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_the_title_is_drawn(self, tmp_path, mode):
        f = _figures(tmp_path, mode, title="T")[0]
        assert f.title is not None and f.title.text == "T"

    def test_the_mata_route_exists(self):
        mata = _read("dash_parse.mata")
        assert re.search(r"void _dash_split_segs\(string scalar input, "
                         r"\| real scalar allow_empty\)", mata)
        assert "real scalar _dash_spec_has_plots(string scalar json)" in mata
        ado = _read("dash.ado")
        assert "_dash_split_segs(strtrim(st_local(\"0\")), 1)" in ado
        assert "dash__bare_tw" not in ado
