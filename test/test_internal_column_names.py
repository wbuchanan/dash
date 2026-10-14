"""G1 (WP-28): every column dash makes up is named under the __dash prefix.

A guard for the rule test_reserved_names.py enforces from the outside: this
file scans dash_render.py's own string constants (the source of truth for
every literal a mapper might still write) and checks the renamed columns are
actually drawn, in both modes.  Section 14's hover text column
(__dash_hover_{var}) must keep the same rule; this file is what would catch
it if it did not.
"""
import ast
import inspect
import os
import sys

import pytest
from bokeh.models import LabelSet

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_DASH_RENDER_PATH = os.path.join(os.path.dirname(_HERE), "dash_render.py")

#: Every "__"-prefixed string constant in dash_render.py that is not a
#: column dash makes: layout/model keys (__missing__, __all__, __tabs__,
#: __fw_<i>__, <name>__by__<i>), Python's own dunders, the qualifier and
#: strL-fix prefixes (their own rule, TR-07.1/TR-07.5), and the JS
#: placeholder _FILTER_JS fills in (TR-07.4).  A bare "__" is
#: _dash_reserved_name's own substring test, not a name.
_ALLOWED_DUNDER_PREFIXES = (
    "__missing__", "__all__", "__tabs__", "__fw_", "__by__",
    "__builtins__", "__name__", "__main__", "__future__",
    # A module's version, read by getattr (WP-30 P1.32's package floor).
    "__version__",
    "__dashq", "__dashfix", "__DASH_ROW_ID__",
    # The tables _FILTER_JS splices in for lpoly (WP-31 F1d).
    "__DASH_LPOLY_ROT_CONSTANTS__", "__DASH_LPOLY_SUPPORT__",
    # Bokeh's session-JWT member _dash_ws_payload bounds (WP-29 P0.12a).
    "__bk__zlib_",
)


def _allowed(const):
    if const == "__":
        return True
    return any(const.startswith(p) for p in _ALLOWED_DUNDER_PREFIXES)


def _string_constants(path):
    """Every string literal dash_render.py holds, including f-string
    literal parts, read by ``ast`` alone -- never by importing the plan or
    this file's own docstring."""
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), filename=path)
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            out.append((node.lineno, node.value))
    return out


class TestEveryInternalColumnIsUnderThePrefix:

    def test_no_column_literal_escapes_the_prefix(self):
        bad = [(ln, v) for ln, v in _string_constants(_DASH_RENDER_PATH)
               if "__mlabel" in v or "_x_jit" in v or "_y_jit" in v
               or "_label__" in v or v.startswith("_cvar_")]
        assert bad == [], bad

    def test_every_dunder_looking_constant_is_allowed_or_under_the_prefix(
            self):
        bad = [(ln, v) for ln, v in _string_constants(_DASH_RENDER_PATH)
               if v.startswith("__") and not v.startswith("__dash")
               and not _allowed(v)]
        assert bad == [], bad


def test_every_column_constant_starts_with_the_prefix():
    for name in ("_DASH_PC_ROW_COLUMN", "_DASH_MLABEL_PREFIX",
                 "_DASH_MLABEL_VALUES", "_DASH_MLABEL_X", "_DASH_MLABEL_Y",
                 "_DASH_JITTER_X", "_DASH_JITTER_Y", "_DASH_CVAR_PREFIX"):
        val = getattr(dr, name)
        assert val.startswith("__dash"), (name, val)
    assert dr._DASH_LABEL_SUFFIX == "_label"
    assert dr._DASH_RESERVED_PREFIX == "__dash"


class TestTheJsTwin:

    def test_the_filter_js_row_id_is_filled_from_the_constant(self):
        src = inspect.getsource(dr)
        start = src.index("_FILTER_JS = (")
        end_marker = ('""").replace("__DASH_ROW_ID__", '
                      'json.dumps(_ROW_ID_COLUMN))')
        end = src.index(end_marker, start) + len(end_marker)
        block = src[start:end]
        assert '"__dash_row__"' not in block
        assert "__DASH_ROW_ID__" in block
        needle = 'const ROW_ID = "%s";' % dr._ROW_ID_COLUMN
        assert dr._FILTER_JS.count(needle) == 1


def _scatter_srcs(fig):
    return [r.data_source for r in fig.renderers
            if type(r.glyph).__name__ == "Scatter"]


class TestTheRenamedColumns:

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_the_marker_label_columns_in_both_modes(self, mode):
        plots = [plot_for("scatter", options={"mlabel": "foreign"}),
                plot_for("scatter", options={"mlabel": "price",
                                             "mlabformat": "%9.2f"})]
        spec = tp._spec(graphs=[("g1", [plots[0]]), ("g2", [plots[1]])])
        figs, _ = tp._figures_in(mode, spec)
        srcs = [s for f in figs for s in _scatter_srcs(f)]
        cols = {c for s in srcs for c in s.data}
        assert (dr._DASH_MLABEL_PREFIX + "foreign") in cols
        assert any(c.startswith(dr._DASH_MLABEL_PREFIX + "price_fmt_")
                   for c in cols)
        assert not any(c.startswith("__mlabel") for c in cols)

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_the_jitter_columns_in_both_modes(self, mode):
        plot = plot_for("scatter", options={"jitter": "5"})
        spec = tp._spec(plots=[plot])
        figs, _ = tp._figures_in(mode, spec)
        [src] = {id(s): s for f in figs for s in _scatter_srcs(f)}.values()
        assert dr._DASH_JITTER_X in src.data
        assert dr._DASH_JITTER_Y in src.data

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_the_jitter_columns_under_link_all(self, mode):
        plots = [plot_for("scatter", options={"jitter": "5"}),
                plot_for("scatter", options={"jitter": "5"})]
        spec = tp._spec(graphs=[("g1", [plots[0]]), ("g2", [plots[1]])],
                        build_options={"link": "_all"})
        figs, _ = tp._figures_in(mode, spec)
        srcs = {id(s): s for f in figs for s in _scatter_srcs(f)}.values()
        cols = {c for s in srcs for c in s.data}
        assert dr._DASH_JITTER_X in cols
        assert (dr._DASH_JITTER_X + "_2") in cols

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_the_pc_and_rscatter_label_columns_in_both_modes(self, mode):
        # __dash_pc_row__ (_DASH_PC_ROW_COLUMN) is a transient key of
        # _pc_clean_with_label's own working frame, never a column of the
        # rendered source: TestTheDashPrefix already pins that a user
        # column of that name is refused at load time, upstream of this
        # mapper, like every other __dash-prefixed name.
        pc = plot_for("pcscatter", options={"mlabel": "rep"})
        rs = plot_for("rscatter", options={"mlabel": "rep"})
        spec = tp._spec(graphs=[("g1", [pc]), ("g2", [rs])])
        figs, _ = tp._figures_in(mode, spec)
        cols = {c for f in figs for r in f.renderers
                if type(r.glyph).__name__ == "Scatter"
                for c in r.data_source.data}
        assert dr._DASH_MLABEL_VALUES in cols
        assert dr._DASH_MLABEL_X in cols
        assert dr._DASH_MLABEL_Y in cols
        assert not any(c.startswith("__mlabel") for c in cols)

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_the_literal_label_column_in_both_modes(self, mode):
        # scatteri's label is a LabelSet, a figure annotation rather than a
        # glyph renderer: fig.select finds it wherever Bokeh attaches it
        # (fig.center on the saved page, the same on the served document).
        plot = {"type": "scatteri",
                "values": [[20.0, 3000.0, "a"], [30.0, 4000.0, "b"]],
                "options": {}}
        spec = tp._spec(plots=[plot])
        figs, _ = tp._figures_in(mode, spec)
        labelsets = [ls for f in figs
                    for ls in f.select({"type": LabelSet})]
        assert labelsets, "no LabelSet drawn"
        cols = {c for ls in labelsets for c in ls.source.data}
        assert "__dash_scatteri_label" in cols
        assert not any(c == "__scatteri_label__" for c in cols)
