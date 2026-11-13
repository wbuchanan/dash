"""
test_layout_batch_js.py -- the size callbacks run inside the page's layout
queue (WP-50 WE.7, BUGS.md "A page of many graphs takes minutes to
load").  The browser behaviour is test_page_load_layouts.py's (release
tier); this checks how the scripts are put together, without Chrome.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402


def test_the_batched_scripts_wrap_their_code():
    """_dash_batched_js puts the queue before the body and runs the body
    inside dash_batch, returning what the body returns; the span, margin,
    by() fit and key-cell callbacks are built with it."""
    js = dr._dash_batched_js("x.visible = true; return 3;")
    assert js.startswith(dr._DASH_RELAYOUT_JS)
    assert js[len(dr._DASH_RELAYOUT_JS):] == (
        "return dash_batch(() => {x.visible = true; return 3;});\n")
    for name in ("_DASH_SPAN_JS", "_DASH_GRAPH_MARGIN_JS", "_DASH_BY_FIT_JS",
                 "_DASH_KEY_CELL_JS"):
        code = getattr(dr, name)
        assert code.startswith(dr._DASH_RELAYOUT_JS), name
        assert "return dash_batch(() => {" in code and code.endswith("});\n"), name
