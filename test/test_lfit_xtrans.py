"""lfit and lfitci on a transformed x, and Stata's fits per by() panel
(WP-37 stat:PT-12).

Measured on StataNow 19.5 (test/test_wp37_truth.cscript S04): twoway's
``twoway_lfit_parse.class`` hands ``xlog`` (as ``ln(X)``, which wins over
``xtransform()``) and ``xtransform(exp)`` to ``twoway__lfit_serset``, which
regresses y on the transformed x and draws the fit over the untransformed
x -- ``lfit mpg weight, xtransform(X^2) n(7)`` draws 27.499, 25.558,
23.123, ... -- at 100 points when n() is 3 or not given.  dash drew the
straight line and named the option.  qfit, qfitci and fpfitci take both
options and draw without them; fpfit refuses them, "option xlog not
allowed", r(198).  Under by() twoway fits each panel's own rows, for these
options and for estopts(), predopts() and estcmd() alike (DECISIONS A-12,
P5-1); dash fitted the whole sample once and drew it in every panel.

dash.ado now runs twoway's generator with ``xtrans()`` at registration
(``_dash_fit_points``), once per by() group under by(), and writes
``{"panels": [{"key": [<by() values>], "points": ...}], "total": ...}``;
both renderers give each panel the entry whose key is its own by() values
(``_dash_by_key_of``, ``_dash_fit_panel_spec``).
"""
import os
import re
import sys

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_function_panels import _figures  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_ROOT = os.path.dirname(_HERE)
_MODES = ["saved", "served"]

_A = {"x": [1800.0, 3000.0, 4080.0], "y": [31.0, 24.0, 20.5], "nobs": 0}
_B = {"x": [1800.0, 3000.0, 4080.0], "y": [27.0, 22.0, 18.0], "nobs": 0}
_T = {"x": [1800.0, 3000.0, 4080.0], "y": [29.0, 23.0, 19.0], "nobs": 0}
_CI = {"x": [1800.0, 4080.0], "y": [30.0, 20.0], "lo": [28.0, 18.0],
       "hi": [32.0, 22.0], "nobs": 0}


def _read(name):
    with open(os.path.join(_ROOT, name), encoding="utf-8") as fh:
        return fh.read()


def _program(src, name):
    """The text of ado program *name*, from its define to its end."""
    i = src.index("program define " + name)
    j = src.index("\nend\n", i)
    return src[i:j]


def _fit_gate(src):
    """_dash_process_segment's fit route: from the _ft_types line to the
    program's end."""
    seg = _program(src, "_dash_process_segment")
    return seg[seg.index('local _ft_types "'):]


def _panel_lines(mode, spec):
    """``[[(y, lo-or-None)], ...]``: each panel's Line ys (and VArea y1),
    in layout order."""
    if mode == "saved":
        r, w = tp._standalone(spec)
        roots = [r._last_layout_root]
    else:
        doc, w = tp._served(spec)
        roots = list(doc.roots)
    figs = []
    for root in roots:
        _figures(root, figs)
    out = []
    for f in figs:
        ys = [list(np.asarray(g.data_source.data[g.glyph.y], dtype=float))
              for g in f.renderers if type(g.glyph).__name__ == "Line"]
        band = [list(np.asarray(g.data_source.data[g.glyph.y1], dtype=float))
                for g in f.renderers if type(g.glyph).__name__ == "VArea"]
        out.append((ys[-1] if ys else None, band[0] if band else None))
    return out, w


def _by_spec(points, by="foreign", ptype="lfit", extra=None):
    opts = {"xlog": "xlog", "points": points}
    opts.update(extra or {})
    return tp._spec([plot_for(ptype, opts)], graph_options={"by": by})


# ---------------------------------------------------------------------------
# The Stata side: the route through twoway's generator
# ---------------------------------------------------------------------------

class TestTheRoute:

    def test_the_gate_covers_xlog_and_xtransform(self):
        gate = _fit_gate(_read("dash.ado"))
        assert 'st_global("s(xtransform)")' in gate
        assert 'st_global("s(xlog)")' in gate
        assert 'local _ft_x "ln(X)"' in gate
        assert "xtrans(`macval(_ft_x)')" in gate

    def test_fit_points_takes_xtrans(self):
        prog = _program(_read("dash.ado"), "_dash_fit_points")
        assert "XTRans(string asis)" in prog
        # twoway_lfit_parse.class: n(3), the default, is 100 points with a
        # transform (measured: n(3) xlog draws 100).
        assert re.search(r'if `"`macval\(xtrans\)\'"\' != "" & "`pts\'" == '
                         r'"3" local pts 100', prog), prog[:400]
        assert "xtrans(`macval(xtrans)')" in prog

    def test_under_by_the_fit_is_per_panel(self):
        gate = _fit_gate(_read("dash.ado"))
        assert "_dash_fit_panel_key(" in gate
        assert "_dash_fit_panel_add(" in gate
        assert '"panels"' in gate
        mata = _read("dash_parse.mata")
        for fn in ("string scalar _dash_fit_panel_key(",
                   "void _dash_fit_panel_add("):
            assert fn in mata, fn

    def test_estopts_under_by_is_per_panel(self):
        # The by() branch hangs on _ft_on and the graph's by() alone, so an
        # estopts(), predopts() or estcmd() fit under by() reaches it too.
        gate = _fit_gate(_read("dash.ado"))
        assert re.search(r"if `: length local _ss_by' \{", gate), gate[:600]
        i = gate.index("if `: length local _ss_by' {")
        assert "_dash_by_parts" in gate[i:]

    def test_no_fit_notes_the_options(self):
        # xlog and xtransform() are declared (read by _dash_label_split),
        # so no fit's note names them; the types twoway refuses them on are
        # refused in _dash_fit_opts_check.
        src = _read("dash.ado")
        split = _program(src, "_dash_label_split")
        assert "XLOG" in split and "XTRansform(string asis)" in split
        chk = _program(src, "_dash_fit_opts_check")
        assert 'local _fo_xlog "lfit qfit lfitci qfitci fpfitci"' in chk
        assert 'local _fo_xtransform "lfit qfit lfitci qfitci fpfitci"' in chk


# ---------------------------------------------------------------------------
# The renderers: Stata's points drawn as given
# ---------------------------------------------------------------------------

class TestTheDrawing:

    @pytest.mark.parametrize("mode", _MODES)
    def test_points_are_drawn(self, mode):
        guard = getattr(dr.GlyphMapper, "_fit_points_draw", None)
        assert guard is not None
        spec = tp._spec([plot_for("lfit", {"xtransform": "X^2",
                                           "points": dict(_A)})])
        got, _w = _panel_lines(mode, spec)
        assert got[0][0] == _A["y"]

    @pytest.mark.parametrize("mode", _MODES)
    def test_no_note_for_lfit(self, mode):
        spec = tp._spec([plot_for("lfit", {"xlog": "xlog",
                                           "points": dict(_A)})])
        _got, w = _panel_lines(mode, spec)
        assert not [m for m in w if "xlog" in m], w


# ---------------------------------------------------------------------------
# by(): each panel's own points
# ---------------------------------------------------------------------------

class TestThePanels:

    @pytest.mark.parametrize("mode", _MODES)
    def test_each_panel_takes_its_own_points(self, mode):
        spec = _by_spec({"panels": [{"key": [1], "points": dict(_B)},
                                    {"key": [0], "points": dict(_A)}]})
        got, w = _panel_lines(mode, spec)
        assert [g[0] for g in got] == [_A["y"], _B["y"]], (got, w)
        assert not [m for m in w if "cannot be read" in m], w

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_total_panel(self, mode):
        spec = _by_spec({"panels": [{"key": [0], "points": dict(_A)},
                                    {"key": [1], "points": dict(_B)}],
                         "total": dict(_T)}, by="foreign, total")
        got, _w = _panel_lines(mode, spec)
        assert [g[0] for g in got] == [_A["y"], _B["y"], _T["y"]]

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_ci_band_per_panel(self, mode):
        b = dict(_CI, y=[25.0, 15.0], lo=[23.0, 13.0], hi=[27.0, 17.0])
        spec = _by_spec({"panels": [{"key": [0], "points": dict(_CI)},
                                    {"key": [1], "points": b}]},
                        ptype="lfitci")
        got, _w = _panel_lines(mode, spec)
        assert [g[0] for g in got] == [_CI["y"], b["y"]]
        assert [g[1] for g in got] == [_CI["lo"], b["lo"]]

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_missing_key(self, mode, monkeypatch):
        # by(rep, missing): the "." panel's key is the code text, as bytes.
        # (A string by() key is matched as text the same way; the test
        # frame's writer carries no string column, so test_the_key_of_a_
        # panel and test_a_panel_with_no_entry_is_empty pin it.)
        df = tp._DF.assign(
            rep=[3.0, float("nan"), 3.0, 5.0, float("nan"), 3.0, 5.0, 4.0,
                 3.0, 4.0])
        monkeypatch.setattr(tp, "_DF", df)
        spec = tp._spec([plot_for("lfit", {"xlog": "xlog", "points": {
            "panels": [{"key": [3], "points": dict(_A)},
                       {"key": [4], "points": dict(_B)},
                       {"key": [5], "points": dict(_T)},
                       {"key": [{"s": [46]}], "points": dict(_CI)}]}})],
            graph_options={"by": "rep, missing"})
        got, _w = _panel_lines(mode, spec)
        assert [g[0] for g in got] == [_A["y"], _B["y"], _T["y"], _CI["y"]]

    def test_the_key_of_a_panel(self):
        key_of = getattr(dr, "_dash_by_key_of", None)
        assert key_of is not None
        cp = dr._DASH_CODE_PREFIX
        assert key_of(pd.DataFrame({"foreign": [1.0, 1.0]}), "foreign") == [1.0]
        assert key_of(pd.DataFrame({"make": ["a"], "foreign": [0.0]}),
                      "make foreign, total") == ["a", 0.0]
        assert key_of(pd.DataFrame({"rep": [np.nan]}), "rep, missing") == ["."]
        assert key_of(pd.DataFrame({"rep": [np.nan], cp + "rep": ["b"]}),
                      "rep, missing") == [".b"]
        assert key_of(pd.DataFrame({"rep": [np.nan], cp + "rep": [""]}),
                      "rep, missing") == ["."]
        assert key_of(pd.DataFrame({"rep": []}), "rep") is None

    def test_a_panel_with_no_entry_is_empty(self):
        spec_of = getattr(dr, "_dash_fit_panel_spec", None)
        assert spec_of is not None
        g = {"plots": [{"type": "lfitci", "options": {"points": {
            "panels": [{"key": [0], "points": dict(_CI)}]}}},
            {"type": "scatter", "options": {}}]}
        got = spec_of(g, [0.0])
        assert got["plots"][0]["options"]["points"] == _CI
        # text keys travel as their bytes (_dash_fit_panel_key)
        gs = {"plots": [{"type": "lfit", "options": {"points": {
            "panels": [{"key": [{"s": [46, 97]}, 2], "points": dict(_A)}]}}}]}
        assert spec_of(gs, [".a", 2.0])["plots"][0]["options"]["points"] == _A
        assert spec_of(gs, [".a", "2"])["plots"][0]["options"]["points"][
            "x"] == []
        assert got["plots"][1] is g["plots"][1]
        none = spec_of(g, [1.0])["plots"][0]["options"]["points"]
        assert none == {"x": [], "y": [], "lo": [], "hi": [], "nobs": 0}
        assert spec_of(g, None, True)["plots"][0]["options"]["points"] == {
            "x": [], "y": [], "lo": [], "hi": [], "nobs": 0}
        flat = {"plots": [{"type": "lfit", "options": {"points": dict(_A)}}]}
        assert spec_of(flat, [0.0]) is flat
        # a function layer's points are _dash_fn_panel_spec's, not these
        fn = {"plots": [{"type": "function", "points": {"panels": {}}}]}
        assert spec_of(fn, [0.0]) is fn


# ---------------------------------------------------------------------------
# The help
# ---------------------------------------------------------------------------

class TestTheHelp:

    def test_unsupported_drops_the_options(self):
        h = _read("dash.sthlp")
        i = h.index("{phang2}{ul:Type-specific options.}")
        j = h.index("{phang2}", i + 10)
        assert "xlog" not in h[i:j] and "xtransform" not in h[i:j]

    def test_the_lfit_paragraph(self):
        h = _read("dash.sthlp")
        i = h.index("{phang}{ul:Fit options.}")
        j = h.index("{phang}{ul:Recast.}", i)
        para = " ".join(h[i:j].split())
        assert ("{opt xlog} and {opt xtransform(exp)} on {cmd:lfit} and "
                "{cmd:lfitci} fit {it:y} on the transformed {it:x}") in para
        assert "{cmd:fpfit} refuses them" in para
        assert "is made once in each panel from that panel's rows" in para
