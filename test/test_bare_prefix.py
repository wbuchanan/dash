"""WP-31 A1: `dash twoway' with nothing after it draws an empty graph.

twoway alone draws an empty graph, rc 0, with no plot in its plot region,
and takes graph options after a bare comma (`twoway, title(T)' draws the
title T): measured 13oct2026, test/fixtures/bare_prefix_truth.json bare.*.
dash refused `dash twoway', `dash tw' and `dash graph twoway', r(198),
"dash: empty plot specification.".

The prefix route (dash.ado) tells _dash_plot that the prefix stood alone,
and _dash_split_segs (dash_parse.mata) then returns no segment instead of
refusing; the graph registers with "plots":[] and both renderers draw one
figure with its axes and no layer.  test_wp31_truth.cscript U08-3 runs it
through Stata; this file pins the drawing of such a spec and the route.
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
        from bokeh.models import GlyphRenderer
        figs = _figures(tmp_path, mode)
        assert len(figs) == 1, figs
        f = figs[0]
        assert list(f.select({"type": GlyphRenderer})) == []
        assert len(f.left) >= 1 and len(f.below) >= 1, (f.left, f.below)

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
        assert "global dash__bare_tw 1" in ado
        assert "capture macro drop dash__bare_tw" in ado
        assert ("_dash_split_segs(strtrim(st_local(\"0\")), `_bare_tw')"
                in ado)
