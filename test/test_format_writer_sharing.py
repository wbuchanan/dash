"""One Stata writer model per distinct format, and its cost stated
(WP-31 G5).

Each ``CustomJSTickFormatter`` and ``CustomJSHover`` carries the whole
writer (``_DASH_FMT_JS``) in its code.  Bokeh cannot share a model's code
between models, and a tick formatter cannot serve as a tooltip formatter,
so a page holds one tick writer and one tooltip writer per distinct
(format, kind, storage, dp) -- the caches already give that -- and the
help states the size (GAPS3 G5; closed by measurement and documentation).
"""
import os
import re
import sys

import pytest
from bokeh.models import CustomJSHover, CustomJSTickFormatter

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import dash_render as dr  # noqa: E402
import test_by_axes_keys as tk  # noqa: E402
import test_by_grid as tg  # noqa: E402

MODES = ("saved", "served")
_HELP = os.path.join(os.path.dirname(__file__), "..", "dash.sthlp")


def _models(mode):
    plots = [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
              "options": {}},
             {"type": "scatter", "yvar": "headroom", "xvar": "weight",
              "options": {}}]
    graphs = [tk._graph("g%d" % i, plots, {"hover": "mpg weight"})
              for i in (1, 2)]
    spec = tk._spec(graphs, scheme="s2color")
    spec["build_options"]["formats"] = {"mpg": "%8.0g", "weight": "%8.0gc",
                                        "headroom": "%6.1f"}
    roots, _n, _o = tk._build(mode, spec, data=tg._data())
    return [m for r in roots for m in r.references()]


class TestOneWriterPerQuadruple:
    @pytest.mark.parametrize("mode", MODES)
    def test_no_duplicate_models(self, mode):
        ms = _models(mode)
        for cls in (CustomJSTickFormatter, CustomJSHover):
            keys = [tuple(sorted(dict(m.args).items())) for m in ms
                    if isinstance(m, cls)]
            assert keys, cls
            assert len(keys) == len(set(keys)), (cls, keys)

    def test_key_carries_dp(self):
        cache = {}
        a = dr._dash_fmt_tick_formatter("%9.2f", "", "", cache)
        assert dr._dash_fmt_tick_formatter("%9.2f", "", "", cache) is a
        cache2 = {"dp": "comma"}
        b = dr._dash_fmt_tick_formatter("%9.2f", "", "", cache2)
        assert dict(b.args)["dp"] == "comma"
        assert ("tick", "%9.2f", "", "", "comma") in cache2
        h = dr._dash_fmt_hover("%9.2f", "", "", cache)
        assert h is not a and ("hover", "%9.2f", "", "", "period") in cache

    def test_help_states_the_size(self):
        kb = round(len(dr._DASH_FMT_JS) / 1024)
        with open(_HELP, encoding="utf-8") as fh:
            text = re.sub(r"\s+", " ", fh.read())
        assert ("one tick formatter and one tooltip formatter of about "
                "%d KB each" % kb) in text
        assert "share one model between an axis and a tooltip" in text
