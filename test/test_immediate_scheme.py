"""The scheme a user asks for on a single command must be the scheme drawn.

`dash scatter mpg weight, scheme(economist)` takes the immediate render path.
That path writes its own master JSON (dash.ado, `_dash_render_immediate`) with
`"theme": ""` and no `"scheme"` key at all, while `scheme()` is parsed and
stored on the *graph*.  The renderer resolves the dashboard scheme from
`build_options` only, so the graph-level value was read by nothing: the
explicit option lost silently to the session's own `c(scheme)`.

Silently, and in favour of a plausible alternative, which is the bad case --
the dashboard renders, it just isn't the one that was asked for.
"""
import json
import os
import sys

import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
from conftest import make_data_json


def _render(tmp_path, build_options, graph_options):
    graph = {
        "name": "g1",
        "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                   "options": {}}],
        "options": graph_options,
    }
    spec = tmp_path / "spec.json"
    data = tmp_path / "data.json"
    spec.write_text(json.dumps({"graphs": [graph],
                                "build_options": build_options}))
    df = pd.DataFrame({"mpg": [22.0, 18.0, 25.0, 30.0],
                       "weight": [2930.0, 3350.0, 2200.0, 1800.0]})
    data.write_text(json.dumps(make_data_json(df)))
    return dr.DashRenderer(str(spec), str(data))


# The literal build_options `_dash_render_immediate` writes.
IMMEDIATE = {"layout": "1 1", "theme": "", "session_scheme": "stcolor",
             "level": "95", "formats": {}}


class TestGraphLevelScheme:
    def test_graph_scheme_beats_the_session_scheme(self, tmp_path):
        r = _render(tmp_path, dict(IMMEDIATE), {"scheme": "economist"})
        assert r.scheme.name == "economist"

    def test_session_scheme_still_applies_when_no_option_is_given(self, tmp_path):
        r = _render(tmp_path, dict(IMMEDIATE), {})
        assert r.scheme.name == "stcolor"

    def test_build_level_scheme_beats_the_graph_level_one(self, tmp_path):
        bo = dict(IMMEDIATE, scheme="s1mono")
        r = _render(tmp_path, bo, {"scheme": "economist"})
        assert r.scheme.name == "s1mono"

    def test_build_level_theme_beats_the_graph_level_scheme(self, tmp_path):
        bo = dict(IMMEDIATE, theme="mono")
        r = _render(tmp_path, bo, {"scheme": "economist"})
        assert r.scheme.name != "economist"

    def test_an_unknown_graph_scheme_warns_and_falls_back_like_any_other(self, tmp_path):
        """Same treatment as an unknown scheme on `dash build'.

        Not the session scheme: an unrecognised name is reported and resolved
        to s2color wherever it was written, so the two places a user can name
        a scheme do not behave differently when the name is wrong.
        """
        with pytest.warns(UserWarning, match="not a known theme or scheme"):
            r = _render(tmp_path, dict(IMMEDIATE), {"scheme": "no_such_scheme"})
        assert r.scheme.name == "s2color"

    def test_the_first_graphs_scheme_wins_and_the_conflict_is_reported(self, tmp_path):
        """Two graphs, two different scheme() values, one page to draw."""
        graphs = [
            {"name": "g1", "plots": [{"type": "scatter", "yvar": "mpg",
                                      "xvar": "weight", "options": {}}],
             "options": {"scheme": "economist"}},
            {"name": "g2", "plots": [{"type": "line", "yvar": "mpg",
                                      "xvar": "weight", "options": {}}],
             "options": {"scheme": "s1mono"}},
        ]
        spec = tmp_path / "spec2.json"
        data = tmp_path / "data2.json"
        spec.write_text(json.dumps({"graphs": graphs,
                                    "build_options": dict(IMMEDIATE)}))
        df = pd.DataFrame({"mpg": [22.0, 18.0], "weight": [2930.0, 3350.0]})
        data.write_text(json.dumps(make_data_json(df)))
        with pytest.warns(UserWarning, match="scheme"):
            r = dr.DashRenderer(str(spec), str(data))
        assert r.scheme.name == "economist"
