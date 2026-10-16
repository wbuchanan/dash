"""Comments that describe the code (WP-31 F5).

``map_qfitci``'s docstring described a 500-resample bootstrap where the band
is analytic, the module header narrated fpfitci's former bootstrap, and
``_dash_fold_typed``'s comment said dash always joins line types in x order
(false since WP-29 P0.1: the data's order, or x order under ``sort``).
"""
import inspect
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import dash_render as dr  # noqa: E402

_ROOT = os.path.join(os.path.dirname(__file__), "..")


def _read(name):
    with open(os.path.join(_ROOT, name), encoding="utf-8") as fh:
        return fh.read()


class TestComments:
    def test_qfitci_docstring(self):
        doc = inspect.getdoc(dr.GlyphMapper.map_qfitci)
        assert "500 resamples" not in doc
        assert "_dash_fitci_se" in doc
        assert "LinAlgError" in doc

    def test_header_no_bootstrap_narrative(self):
        src = _read("dash_render.py")
        head = src[:src.index("_FP_GRID_MAX = ")]
        assert "200-resample bootstrap" not in head
        # The resample count names the one function that still uses it.
        block = head[head.index("# Optional scientific dependencies"):
                     head.index("_N_BOOT_DEFAULT = ")]
        assert "_bootstrap_ci" in block and "LinAlgError" in block

    def test_fold_typed_comment(self):
        src = _read("dash.ado")
        assert "dash always joins line, connected, area" not in src
        i = src.index('local sort_types "line connected area tsline')
        comment = src[src.rindex("// A bare sort", 0, i):i]
        assert re.search(r"data's\s+(//\s*)?order", comment)
        assert "WP-29 P0.1" in comment
