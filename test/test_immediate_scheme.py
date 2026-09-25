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


def _render(tmp_path, build_options, graph_options, key="graph_options"):
    """Render one graph.

    `key' is which JSON key the graph's options live under.  dash.ado writes
    "graph_options"; an earlier version of this test used "options", which is
    a PLOT key, so every assertion here passed against a shape dash never
    emits while the real command still drew the wrong scheme.
    """
    graph = {
        "name": "g1",
        "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                   "options": {}}],
        key: dict(graph_options, name="g1"),
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


class TestTheKeyDashAdoActuallyWrites:
    """dash.ado emits "graph_options"; "options" belongs to a plot."""

    def test_graph_options_is_read(self, tmp_path):
        r = _render(tmp_path, dict(IMMEDIATE), {"scheme": "economist"},
                    key="graph_options")
        assert r.scheme.name == "economist"

    def test_options_still_works_for_older_specs(self, tmp_path):
        r = _render(tmp_path, dict(IMMEDIATE), {"scheme": "economist"},
                    key="options")
        assert r.scheme.name == "economist"

    def test_the_shape_dash_ado_writes_end_to_end(self, tmp_path):
        """The literal graph object dash.ado assembles (dash.ado:1482)."""
        import json as _json

        import pandas as _pd

        graph = {"plots": [{"type": "scatter", "yvar": "mpg",
                            "xvar": "weight", "options": {}}],
                 "graph_options": {"name": "g1", "scheme": "economist"},
                 "if_expr": "", "in_expr": ""}
        master = {"graphs": [graph], "build_options": dict(IMMEDIATE)}
        spec = tmp_path / "real.json"
        data = tmp_path / "realdata.json"
        spec.write_text(_json.dumps(master))
        df = _pd.DataFrame({"mpg": [22.0, 18.0], "weight": [2930.0, 3350.0]})
        data.write_text(_json.dumps(make_data_json(df)))
        assert dr._resolve_scheme_name(master) == "economist"
        assert dr.DashRenderer(str(spec), str(data)).scheme.name == "economist"


class TestAnIncludeNoteIsPrintedOncePerBuild:
    """`dash scatter mpg weight, scheme(inc)` where inc.scheme holds an
    #include that resolves nowhere.  twoway prints "(note: scheme X not
    found, using s2color)" once (measured 24sep2026, S3 batch: `twoway
    scatter mpg weight, scheme(b2inc) nodraw` prints it once).  dash
    printed it twice: the build's scheme and the graph's own scheme() were
    two parses of one file in one render (DashRenderer.__init__ and
    DashRenderer._make_figure)."""

    _NOTE_A = "(note: scheme b2nosuch not found, using s2color)"
    _NOTE_B = "(note: scheme b2other not found, using s2color)"

    @pytest.fixture
    def wd(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "b2inc.scheme").write_text(
            "#include b2nosuch\n#include b2other\n"
            "color background #123456\n", encoding="utf-8")
        return tmp_path

    @staticmethod
    def _write(wd, build_options, graph_options, n_graphs=1):
        graphs = [{"plots": [{"type": "scatter", "yvar": "mpg",
                              "xvar": "weight", "options": {}}],
                   "graph_options": dict(graph_options, name="g%d" % i),
                   "if_expr": "", "in_expr": ""}
                  for i in range(1, n_graphs + 1)]
        spec = wd / "spec.json"
        data = wd / "data.json"
        spec.write_text(json.dumps({"graphs": graphs,
                                    "build_options": build_options}))
        df = pd.DataFrame({"mpg": [22.0, 18.0, 25.0, 30.0],
                           "weight": [2930.0, 3350.0, 2200.0, 1800.0]})
        data.write_text(json.dumps(make_data_json(df)))
        return str(spec), str(data)

    def _build(self, wd, build_options, graph_options, n_graphs=1):
        import warnings
        spec, data = self._write(wd, build_options, graph_options, n_graphs)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            r = dr.DashRenderer(spec, data)
            r.render()
        return r, [str(w.message) for w in caught]

    def _count(self, said):
        return (sum(self._NOTE_A in m for m in said),
                sum(self._NOTE_B in m for m in said))

    def test_the_immediate_route_notes_each_include_once(self, wd):
        r, said = self._build(wd, dict(IMMEDIATE), {"scheme": "b2inc"})
        assert r.scheme.name == "b2inc"
        assert self._count(said) == (1, 1), said

    def test_a_build_scheme_and_a_graph_scheme_note_once(self, wd):
        bo = dict(IMMEDIATE, scheme="b2inc")
        _r, said = self._build(wd, bo, {"scheme": "b2inc"}, n_graphs=3)
        assert self._count(said) == (1, 1), said

    def test_a_graph_scheme_other_than_the_builds_is_still_noted(self, wd):
        """The graph's scheme is not the build's: its note is not lost."""
        bo = dict(IMMEDIATE, scheme="s1mono")
        r, said = self._build(wd, bo, {"scheme": "b2inc"}, n_graphs=2)
        assert r.scheme.name == "s1mono"
        assert self._count(said) == (1, 1), said

    def test_two_builds_each_note(self, wd):
        """Once per BUILD, not once per process: a second render in the
        same Python session (a second `dash scatter`) says it again."""
        _r, first = self._build(wd, dict(IMMEDIATE), {"scheme": "b2inc"})
        _r, second = self._build(wd, dict(IMMEDIATE), {"scheme": "b2inc"})
        assert self._count(first) == (1, 1), first
        assert self._count(second) == (1, 1), second

    def test_the_served_builder_notes_each_include_once(self, wd):
        import warnings
        spec, data = self._write(wd, dict(IMMEDIATE, scheme="b2inc"),
                                 {"scheme": "b2inc"})
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr.ServerAppBuilder(spec, data).build(str(wd / "app.py"))
        said = [str(w.message) for w in caught]
        assert self._count(said) == (1, 1), said

    def test_many_graphs_share_one_parse(self, wd, monkeypatch):
        """Adversarial (resource exhaustion): 50 graphs each naming the
        same scheme parse it once per build, not once per graph."""
        calls = []
        real = dr.SchemeParser._parse_file

        def counting(self, path, _visited, _depth=0, *a, **k):
            if _depth == 0:
                calls.append(path)
            return real(self, path, _visited, _depth, *a, **k)

        monkeypatch.setattr(dr.SchemeParser, "_parse_file", counting)
        _r, said = self._build(wd, dict(IMMEDIATE), {"scheme": "b2inc"},
                               n_graphs=50)
        assert self._count(said) == (1, 1), said
        assert len([p for p in calls if p.endswith("b2inc.scheme")]) == 1
