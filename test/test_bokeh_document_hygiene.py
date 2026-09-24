"""Every test starts with an empty process-global Bokeh document.

A generated server app calls ``make_document(curdoc())`` when it is
imported, so each app a test exec's leaves its models in ``curdoc()``.
Nothing cleared it: Bokeh walks that document on every later operation,
the served render path climbed from 0.19 s to about 1.8 s per test over a
run, and the accumulated state flipped eleven outcomes (ten spurious skips
and one spurious pass).  conftest.py now clears the document after every
test.  These tests pin the mechanism and the fix.
"""
import importlib.util
import json
import os
import sys

import pytest
from bokeh.io import curdoc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
import dash_render as dr  # noqa: E402
from conftest import _clear_bokeh_curdoc, make_data_json, make_spec  # noqa: E402


def _exec_generated_app(tmp_path, auto_df):
    """Build a served app from a scatter spec and import it, as the server
    tests do.  Importing is what pollutes ``curdoc()``."""
    sp, dp, ap = (str(tmp_path / n) for n in ("s.json", "d.json", "app.py"))
    with open(sp, "w") as fh:
        json.dump(make_spec([{"type": "scatter", "yvar": "mpg",
                              "xvar": "weight", "options": {}}]), fh)
    with open(dp, "w") as fh:
        json.dump(make_data_json(auto_df), fh)
    dr.ServerAppBuilder(sp, dp).build(ap)
    ms = importlib.util.spec_from_file_location("_hygiene_app", ap)
    mod = importlib.util.module_from_spec(ms)
    ms.loader.exec_module(mod)


def test_every_test_starts_with_an_empty_global_document(request):
    assert "_clear_bokeh_curdoc" in request.fixturenames, (
        "the clearing fixture is not autouse any more")
    assert list(curdoc().roots) == []


def test_the_fixture_clears_what_an_imported_app_leaves_behind(tmp_path, auto_df):
    _exec_generated_app(tmp_path, auto_df)
    assert curdoc().roots, (
        "importing a generated app no longer touches curdoc(); the fixture "
        "may be unnecessary, re-measure before removing it")
    gen = _clear_bokeh_curdoc.__wrapped__()   # drive the fixture by hand
    next(gen)                                 # set-up: nothing
    with pytest.raises(StopIteration):
        next(gen)                             # tear-down: clear
    assert list(curdoc().roots) == []


def test_clearing_is_idempotent_on_an_empty_document():
    gen = _clear_bokeh_curdoc.__wrapped__()
    next(gen)
    with pytest.raises(StopIteration):
        next(gen)
    assert list(curdoc().roots) == []
