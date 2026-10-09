"""conftest.render_models: a render's models without the page's
serialisation (the test-suite speed-up of 08oct2026)."""

import os
import sys
import warnings

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from bokeh.embed import json_item  # noqa: E402
from conftest import render_models  # noqa: E402


def _renderer():
    _, sp, dp = tp._write(tp._spec([tp._sc(), tp.plot_for("lfit")]))
    return dr.DashRenderer(sp, dp)


def _strip(o):
    if isinstance(o, dict):
        return {k: _strip(v) for k, v in o.items() if k != "id"}
    if isinstance(o, (list, tuple)):
        return [_strip(v) for v in o]
    return o


class TestRenderModels:

    def test_the_models_are_the_full_renders(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            full = _renderer()
            page = full.render()
            fast = render_models(_renderer())
        assert "<script" in page
        assert list(fast.figures) == list(full.figures)
        for name in full.figures:
            assert (_strip(json_item(fast.figures[name])["doc"])
                    == _strip(json_item(full.figures[name])["doc"]))

    def test_file_html_is_restored(self):
        real = dr.file_html
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            render_models(_renderer())
        assert dr.file_html is real
