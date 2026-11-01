"""test_server_optional_deps.py — a missing package must not lie or kill the app.

The standalone renderer has a stated contract for optional packages, written
into ``_optional_import``'s own docstring: a missing or broken package
degrades *that one plot type* to an empty glyph and warns, rather than
aborting the dashboard. The generated server app followed neither half.

**statsmodels — silent wrong numbers, the worst kind.** With statsmodels
unimportable, the app's ``_compute_lowess`` returned the raw cleaned points
and drew them as the lowess curve. Measured on this machine, where
statsmodels genuinely cannot import (``packaging`` is absent):

    line renderer x == raw sorted weight   True   (20 of 20)
    line renderer y == raw mpg             True   (20 of 20)

so the user is shown their own scatter joined up, labelled as a smoother,
with no warning and rc 0. The standalone path warns and draws an empty line
for the same input.

Since WP-18 the app's lowess is Stata's smoother in numpy (copied in with
``GlyphMapper``): there is no statsmodels import in the app at all, and the
first class below pins that instead of the fallback's shape.

**scipy — the whole app dies.** ``from scipy import stats`` sits at module
scope of the generated app, unguarded, so a missing scipy breaks a plain
scatter that uses no scipy at all. Measured with an import hook blocking
scipy: the server app raised ``ModuleNotFoundError`` on import while the
standalone renderer rendered the same spec fine.

``except ImportError`` is also too narrow. It catches this machine's
``ModuleNotFoundError``, but a package that is *present and broken* raises
something else — which is exactly why ``_optional_import`` caught
``Exception``.

Since WP-18 neither package is imported anywhere: every statistical layer
is computed with numpy, ``_optional_import`` is gone, and so is the app's
guarded scipy import, which nothing read.  The classes below pin that.
"""
import json
import os
import sys
import tempfile

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

from dash_render import ServerAppBuilder

from conftest import exec_app, make_spec, make_data_json


def _build(plots, tmpdir):
    df = pd.DataFrame({
        "mpg": np.linspace(12.0, 41.0, 20),
        "weight": np.linspace(1760.0, 4840.0, 20),
    })
    spec = make_spec(plots)
    sp = os.path.join(tmpdir, "s.json")
    dp = os.path.join(tmpdir, "d.json")
    op = os.path.join(tmpdir, "app.py")
    with open(sp, "w") as f:
        json.dump(spec, f)
    with open(dp, "w") as f:
        json.dump(make_data_json(df), f)
    ServerAppBuilder(sp, dp).build(op)
    return op, df


def _module(app_path):
    with open(app_path, encoding="utf-8") as fh:
        src = fh.read()
    ns = {"__name__": "dash_app_under_test"}
    exec_app(src.split("if __name__ !=")[0], app_path, ns)
    return ns


_SCATTER = [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
             "options": {}}]
_LOWESS = [{"type": "lowess", "yvar": "mpg", "xvar": "weight",
            "options": {}}]


class TestLowessNeedsNoStatsmodelsInTheApp:
    """WP-18: the app's lowess is Stata's own smoother in numpy, copied in
    with ``GlyphMapper``.  There is no statsmodels import left to guard and
    no ``_compute_lowess`` fallback left to fake a curve with -- the tests
    this class replaces pinned that fallback (empty, warned, ``except
    Exception``); the property that replaced it is stronger: a lowess app
    draws the curve with statsmodels entirely unavailable.
    """

    def test_the_app_imports_no_statsmodels(self, tmp_path):
        app, _ = _build(_LOWESS, str(tmp_path))
        with open(app, encoding="utf-8") as fh:
            src = fh.read()
        code = "\n".join(l.split("#", 1)[0] for l in src.splitlines())
        assert "statsmodels" not in code, (
            "the generated app still imports statsmodels for lowess")
        assert "_compute_lowess" not in code, (
            "the dead textual _compute_lowess copy is back in the app")

    def test_a_lowess_app_draws_the_curve_without_statsmodels(self, tmp_path):
        app, df = _build(_LOWESS, str(tmp_path))

        class _Block:
            def find_spec(self, name, path=None, target=None):
                if name.split(".")[0] == "statsmodels":
                    raise ModuleNotFoundError("No module named 'statsmodels'")
                return None

        from bokeh.document import Document
        from bokeh.models import ColumnDataSource
        saved = list(sys.meta_path)
        removed = {k: v for k, v in sys.modules.items()
                   if k == "statsmodels" or k.startswith("statsmodels.")}
        for k in removed:
            del sys.modules[k]
        sys.meta_path.insert(0, _Block())
        try:
            mod = _module(app)
            doc = Document()
            mod["make_document"](doc)
        finally:
            sys.meta_path[:] = saved
            sys.modules.update(removed)
        curves = [m for m in doc.select({"type": ColumnDataSource})
                  if "x_lw" in m.data]
        assert curves, "no lowess line source in the served document"
        xs = list(curves[0].data["x_lw"])
        ys = list(curves[0].data["y_lw"])
        assert len(xs) == len(df) and len(ys) == len(df), (
            f"lowess drew {len(xs)} points; Stata draws one per observation")
        assert ys != df["mpg"].tolist(), (
            "the raw data was returned as the lowess curve")


class TestScipyDoesNotKillTheWholeApp:

    def test_the_import_is_guarded(self, tmp_path):
        app, _ = _build(_SCATTER, str(tmp_path))
        with open(app, encoding="utf-8") as fh:
            src = fh.read()
        lines = [l for l in src.splitlines()
                 if l.startswith("from scipy") or l.startswith("import scipy")]
        assert not lines, (
            f"scipy is imported at module scope, so a missing scipy breaks "
            f"every plot type including ones that never use it: {lines}"
        )

    def test_a_scatter_app_loads_without_scipy(self, tmp_path):
        """The measurement that showed the two paths disagree."""
        app, _ = _build(_SCATTER, str(tmp_path))

        class _Block:
            def find_module(self, name, path=None):
                return self if name.split(".")[0] == "scipy" else None

            def find_spec(self, name, path=None, target=None):
                if name.split(".")[0] == "scipy":
                    raise ModuleNotFoundError("No module named 'scipy'")
                return None

        blocker = _Block()
        saved = list(sys.meta_path)
        removed = {k: v for k, v in sys.modules.items()
                   if k == "scipy" or k.startswith("scipy.")}
        for k in removed:
            del sys.modules[k]
        sys.meta_path.insert(0, blocker)
        try:
            _module(app)          # must not raise
        finally:
            sys.meta_path[:] = saved
            sys.modules.update(removed)

    def test_the_guard_reports_its_absence(self, tmp_path):
        """No served layer imports scipy or statsmodels at all.

        This required a `_HAS_SCIPY' flag beside a guarded scipy import so
        a consumer could degrade.  Since WP-18 no layer needs scipy
        (lfitci's linregress went with the weights, kdensity's
        gaussian_kde with S07, mspline's Pchip with WP-18) and lowess is
        Stata's smoother in numpy, so the guarded import was read by
        nothing and is gone: an app that cannot miss a package is the
        stronger state.  The check parses the app built with EVERY
        statistical layer, so an import re-added inside any method --
        where a text scan of module-level lines would not look -- fails
        it, and a docstring that merely names scipy does not.
        """
        import ast
        plots = [{"type": t, "yvar": "mpg", "xvar": "weight", "options": {}}
                 for t in ("lfit", "qfit", "lfitci", "qfitci", "lowess",
                           "lpoly", "lpolyci", "fpfit", "fpfitci", "mspline",
                           "mband")]
        plots += [{"type": t, "yvar": "mpg", "options": {}}
                  for t in ("kdensity", "histogram")]
        app, _ = _build(plots, str(tmp_path))
        with open(app, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            found += [n for n in names
                      if n.split(".")[0] in ("scipy", "statsmodels")]
        assert not found, (
            "the served app imports %s although no layer needs it" % found)
