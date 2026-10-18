"""test_server_dispatch.py -- the served app draws every plot type through
the renderer's own dispatch, counted from the app's syntax tree.

WP-09 replaced the app's ``if/elif ptype == '...'`` chain (38 types drawn a
second time, in emitted string literals) with the renderer's dispatch
tables copied into the app.  What held that collapse was a hand count of
the app's text (test_server.py: six ``"elif ptype == '<type>':"`` strings
absent and one ``"def _dash_draw_layer("``), which a branch spelled any
other way -- ``if ptype in (...)``, ``pt == ...``, ``.get('type') == ...``
-- passed (BUGS.md "Harness guards", GAPS3 K4).

Here the generated app is parsed.  Every module-level function and class
the app copies verbatim from dash_render.py (the same syntax tree) is the
renderer's own code and shared by both modes; every other statement is the
app's own, and each comparison it makes against a plot-type name is
counted.  The count is pinned exactly: the four types the caller handles
before the table in both renderers (scatteri, pci, pcarrowi and function,
which take no shared (y, x) source), the band smoothers' row-order rule,
and the launcher's warm-up of the slow estimators.  A new per-type branch
in the app's own code fails here, however it is spelled.
"""
import ast
import collections
import json
import os
import sys
import tempfile

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import make_data_json, make_spec  # noqa: E402
from test_server_layer_defects import ALL_TYPES, _DF, plot_for  # noqa: E402

#: The functions the app must carry as the renderer's own code: the tables,
#: the two adders and the layer source.
_DISPATCH = ("_dash_glyph_dispatch", "_dash_pc_dispatch", "_dash_add_glyph",
             "_dash_add_pc_glyph", "_dash_layer_source")

#: The app's own plot-type tests, measured 18oct2026 (WP-32): (the
#: innermost definition holding it, the types it compares) -> how many.
_APP_OWN_TYPE_TESTS = {
    # The one per-layer drawer (make_document's, called by every graph,
    # by() panel and move): the caller dispatch DashRenderer._make_figure
    # makes before the table.
    ("_dash_draw_layer", ("scatteri",)): 1,
    ("_dash_draw_layer", ("pci",)): 1,
    ("_dash_draw_layer", ("pcarrowi",)): 1,
    ("_dash_draw_layer", ("function",)): 1,
    # mband and mspline join in x order (their curve is a smooth over x).
    ("_dash_draw_layer", ("mband", "mspline")): 1,
    # The launcher's start line names the slow estimators it warms up.
    ("<module>", ("fpfit", "fpfitci", "kdensity", "lowess", "lpoly",
                  "lpolyci")): 1,
}


def _compared_types(node, types):
    """The plot-type names a Compare node tests against (a string constant,
    or a tuple, list or set of them, on either side), sorted; () when none
    is one."""
    found = set()
    for c in [node.left] + list(node.comparators):
        if isinstance(c, ast.Constant):
            vals = [c.value]
        elif isinstance(c, (ast.Tuple, ast.List, ast.Set)):
            vals = [e.value for e in c.elts if isinstance(e, ast.Constant)]
        else:
            vals = []
        found |= {v for v in vals if isinstance(v, str) and v in types}
    return tuple(sorted(found))


def _renderer_defs(tree):
    """{name: {ast.dump of each definition of that name}} over the whole
    renderer module, nested definitions included."""
    out = collections.defaultdict(set)
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                          ast.ClassDef)):
            out[n.name].add(ast.dump(n))
    return out


def _own_type_tests(app_tree, renderer_defs, types):
    """Counter of (holder, types) over the app's own code: every top-level
    statement except a definition that is a verbatim copy of the
    renderer's."""
    seen = collections.Counter()
    defs = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)

    def _walk(node, holder):
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, ast.Compare):
                hit = _compared_types(ch, types)
                if hit:
                    seen[(holder, hit)] += 1
            _walk(ch, ch.name if isinstance(ch, defs) else holder)

    for stmt in app_tree.body:
        if isinstance(stmt, defs):
            if ast.dump(stmt) in renderer_defs.get(stmt.name, ()):
                continue
            _walk(stmt, stmt.name)
        else:
            _walk(ast.Module(body=[stmt], type_ignores=[]), "<module>")
    return seen


def _top_level_defs(app_tree):
    return collections.Counter(
        n.name for n in app_tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                          ast.ClassDef)))


@pytest.fixture(scope="module")
def trees():
    """(app tree, renderer tree): an app whose spec holds one layer of
    every plot type, though the app's code does not depend on the spec
    (measured: the same 682 definitions for one scatter)."""
    plots = [plot_for(t) for t in ALL_TYPES
             if t not in ("contour", "contourline")]
    d = tempfile.mkdtemp(prefix="dash_dispatch_")
    sp, dp, ap = (os.path.join(d, n) for n in ("s.json", "d.json", "app.py"))
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(make_spec(plots), fh)
    with open(dp, "w", encoding="utf-8") as fh:
        json.dump(make_data_json(_DF), fh)
    dr.ServerAppBuilder(sp, dp).build(ap)
    with open(ap, encoding="utf-8") as fh:
        app = ast.parse(fh.read())
    with open(dr.__file__, encoding="utf-8") as fh:
        ren = ast.parse(fh.read())
    return app, ren


class TestTheAppHasNoDispatchOfItsOwn:

    def test_its_own_code_tests_plot_types_only_where_pinned(self, trees):
        app, ren = trees
        got = _own_type_tests(app, _renderer_defs(ren),
                              set(dr._dash_plot_type_names()))
        assert dict(got) == _APP_OWN_TYPE_TESTS, (
            "the served app's own code compares plot types other than as "
            "pinned (a per-type branch outside the shared dispatch?): "
            "only in the app %s; only in the pin %s" % (
                sorted(set(got.items()) - set(_APP_OWN_TYPE_TESTS.items())),
                sorted(set(_APP_OWN_TYPE_TESTS.items()) - set(got.items()))))

    @pytest.mark.parametrize("name", _DISPATCH)
    def test_the_dispatch_is_the_renderers_own_code(self, trees, name):
        app, ren = trees
        assert _top_level_defs(app)[name] == 1, name
        copy = next(n for n in app.body if getattr(n, "name", "") == name)
        assert ast.dump(copy) in _renderer_defs(ren)[name], (
            "%s in the app is not the renderer's definition" % name)

    def test_one_layer_drawer(self, trees):
        """The hand count it replaces: ``src.count("def _dash_draw_layer(")``
        was 1, which a second drawer named otherwise passed."""
        app, _ren = trees
        names = collections.Counter(
            n.name for n in ast.walk(app)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
        assert names["_dash_draw_layer"] == 1, names["_dash_draw_layer"]

    def test_the_counter_sees_every_spelling(self):
        types = {"line", "scatter", "lfit"}
        src = (
            "def _copied(p):\n    return p == 'line'\n"
            "def make_document(doc, ptype, pt, l):\n"
            "    if ptype == 'line': pass\n"
            "    elif pt in ('scatter', 'lfit'): pass\n"
            "    if l.get('type') != 'lfit': pass\n"
            "    if ptype == 'not a type': pass\n"
            "    def _inner():\n"
            "        return 'scatter' == ptype\n"
            "if ptype in ['line']: pass\n")
        app = ast.parse(src)
        ren = _renderer_defs(ast.parse(
            "def _copied(p):\n    return p == 'line'\n"))
        got = _own_type_tests(app, ren, types)
        assert dict(got) == {
            ("make_document", ("line",)): 1,
            ("make_document", ("lfit", "scatter")): 1,
            ("make_document", ("lfit",)): 1,
            ("_inner", ("scatter",)): 1,
            ("<module>", ("line",)): 1}, dict(got)
