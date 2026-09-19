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

**scipy — the whole app dies.** ``from scipy import stats`` sits at module
scope of the generated app, unguarded, so a missing scipy breaks a plain
scatter that uses no scipy at all. Measured with an import hook blocking
scipy: the server app raised ``ModuleNotFoundError`` on import while the
standalone renderer rendered the same spec fine.

``except ImportError`` is also too narrow. It catches this machine's
``ModuleNotFoundError``, but a package that is *present and broken* raises
something else — which is exactly why ``_optional_import`` catches
``Exception``.
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

from conftest import make_spec, make_data_json


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
    exec(compile(src.split("if __name__ !=")[0], app_path, "exec"), ns)
    return ns


_SCATTER = [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
             "options": {}}]
_LOWESS = [{"type": "lowess", "yvar": "mpg", "xvar": "weight",
            "options": {}}]


class TestLowessDoesNotFakeACurve:

    def test_a_missing_smoother_draws_nothing_rather_than_the_raw_data(
            self, tmp_path):
        app, df = _build(_LOWESS, str(tmp_path))
        mod = _module(app)
        if mod.get("_HAS_STATSMODELS"):
            pytest.skip("statsmodels imports here; the fallback is unreachable")
        out = mod["_compute_lowess"](df, "mpg", "weight")
        raw_x = sorted(df["weight"].tolist())
        assert list(out["x"]) != raw_x, (
            "the raw data was returned as the lowess curve: the user is "
            "shown their own scatter joined up, labelled a smoother"
        )
        assert not out["x"] and not out["y"], (
            f"a layer that cannot be computed must be empty; got "
            f"{len(out['x'])} points"
        )

    def test_it_warns(self, tmp_path):
        app, df = _build(_LOWESS, str(tmp_path))
        mod = _module(app)
        if mod.get("_HAS_STATSMODELS"):
            pytest.skip("statsmodels imports here")
        import warnings
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            mod["_compute_lowess"](df, "mpg", "weight")
        msgs = " ".join(str(w.message) for w in caught)
        assert "statsmodels" in msgs, (
            f"nothing told the user why the curve is missing: {msgs!r}"
        )

    def test_a_broken_package_is_caught_too(self, tmp_path):
        """`except ImportError` misses a package that is present but broken.

        That is the reason _optional_import catches Exception, and its
        docstring says so.
        """
        app, _ = _build(_LOWESS, str(tmp_path))
        with open(app, encoding="utf-8") as fh:
            src = fh.read()
        i = src.index("import statsmodels")
        window = src[i:i + 400]
        assert "except Exception" in window, (
            "the statsmodels guard catches only ImportError, so a present "
            "but broken install still aborts"
        )


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
        app, _ = _build(_SCATTER, str(tmp_path))
        with open(app, encoding="utf-8") as fh:
            src = fh.read()
        assert "_HAS_SCIPY" in src, (
            "nothing records whether scipy is available, so a consumer "
            "cannot degrade gracefully"
        )
