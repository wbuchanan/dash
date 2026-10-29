"""
test_zero_obs.py -- a plot with no observation answered as twoway answers
it (WP-37 section 37-01, DG-1).

The defect (measured at b34f411): ``dash contour price mpg weight if price
< 0`` stopped with a Python traceback, r(7102), ``lower_level and
upper_level cannot be NaN``, where twoway draws the empty plot with its
axis titles and its key's title, rc 0.  And a graph registered on data
that had none left at ``dash build`` reached the renderer unanswered.

twoway (scripts/extract_zero_obs_truth.do, test/fixtures/
zero_obs_truth.json: 48 data types in eight cases and the four literal
types in four, 400 probes) draws an empty graph for every type but six:
lpoly and lpolyci "no observations", r(2000); fpfit and fpfitci a note
then "observation numbers out of range", r(198); mband and mspline "bands
must be between 1 and 200", r(198); and a by() graph whose every panel is
empty is "nothing to graph", r(198), for every type.

dash answers it in one check at export, on every route
(``_dash_zero_obs_check`` in dash.ado over ``_dash_zero_obs_rule`` in
dash_parse.mata), and draws the empty contour and its titled key in both
modes (``GlyphMapper._contour_key_empty``).  test_wp37_truth.cscript S01
compares dash with twoway (Q3701-1..6).
"""
import json
import os
import re
import sys

import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")
sys.path.insert(0, _HERE)
sys.path.insert(0, _ROOT)

import test_bar_range_geometry as bg  # noqa: E402
import test_mode_parity as tp  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "zero_obs_truth.json")
_MODES = ("saved", "served")

#: The 40 data types of the research's table and the eight horizontal
#: variants; the literal types and their four cases.
_DATA_TYPES = (
    "scatter line connected area bar spike dropline dot lowess rarea rbar "
    "rspike rcap rcapsym rscatter rline rconnected rpcap rpspike pcspike "
    "pccapsym pcarrow pcbarrow pcscatter tsline tsrline kdensity histogram "
    "contour contourline lfit qfit lfitci qfitci fpfit fpfitci lpoly lpolyci "
    "mband mspline").split()
_HORIZONTAL = "bar area spike dropline rbar rarea rcap histogram".split()
_LITERAL = ("function", "scatteri", "pci", "pcarrowi")
_CASES = ("a", "b1", "b2", "c", "d", "f", "e1", "e2")
_LIT_CASES = ("a", "b1", "c", "e2")


def _ado():
    with open(os.path.join(_ROOT, "dash.ado"), encoding="utf-8") as fh:
        return fh.read()


def _program_body(src, name):
    """The text of `program define <name>` up to its terminating `end`."""
    m = re.search(r"^program define %s\b.*?$" % re.escape(name), src,
                  re.MULTILINE)
    assert m, name
    tail = src[m.end():]
    e = re.search(r"^end\s*$", tail, re.MULTILINE)
    return tail[:e.start()] if e else tail


class TestTheFixture:

    def test_meta_and_size(self):
        with open(_FIXTURE, encoding="utf-8") as fh:
            d = json.load(fh)
        assert sorted(d["_meta"]) == ["born_date", "dash_commit",
                                      "extracted", "source",
                                      "stata_version"]
        assert d["_meta"]["source"] == "scripts/extract_zero_obs_truth.do"
        want = set()
        for t in _DATA_TYPES + [h + "_h" for h in _HORIZONTAL]:
            want |= {"%s.%s" % (t, c) for c in _CASES}
        for t in _LITERAL:
            want |= {"%s.%s" % (t, c) for c in _LIT_CASES}
        assert len(want) == 400
        assert set(d) - {"_meta"} == want
        # The six refusing types, and by() with every panel empty.
        assert d["lpoly.a"]["rc"] == 2000
        assert d["function.e2"]["rc"] == 198
        assert d["contour.a"]["rc"] == 0
        refusing = {k for k, v in d.items() if k != "_meta" and v["rc"]}
        assert len(refusing) == 84


def _plot(ptype="contour"):
    return {"type": ptype, "zvar": "mpg", "yvar": "weight",
            "xvar": "length", "options": {}}


#: No row: the columns the layer reads, empty.
_EMPTY = pd.DataFrame({"mpg": pd.Series([], dtype=float),
                       "weight": pd.Series([], dtype=float),
                       "length": pd.Series([], dtype=float)})


def _figs(mode, tmp_path, plots):
    spec = tp._spec(plots, {"formats": {}})
    return bg._figs(mode, tmp_path, spec, _EMPTY)


def _bars(fig):
    return [m for side in (fig.right, fig.left, fig.above, fig.below,
                           fig.center)
            for m in side if type(m).__name__ == "ContourColorBar"]


class TestAnEmptyContour:

    @pytest.mark.parametrize("mode", _MODES)
    def test_no_rows_draws(self, mode, tmp_path):
        figs, _notes = _figs(mode, tmp_path, [_plot()])
        assert len(figs) == 1
        assert [r for r in figs[0].renderers
                if type(r).__name__ == "ContourRenderer"]

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_key_is_titled_and_empty(self, mode, tmp_path):
        figs, _notes = _figs(mode, tmp_path, [_plot()])
        [cb] = _bars(figs[0])
        assert cb.title == "mpg"
        assert list(cb.ticker.ticks) == []
        # The strip is the bands' fill, transparent, and no outline.
        assert cb.fill_renderer.glyph.fill_alpha == 0.0
        assert cb.bar_line_alpha == 0.0

    @pytest.mark.parametrize("mode", _MODES)
    def test_contourline_no_rows_draws(self, mode, tmp_path):
        figs, _notes = _figs(mode, tmp_path, [_plot("contourline")])
        assert len(figs) == 1
        assert not _bars(figs[0])


class TestTheCheckIsWired:

    def test_both_routes_call_it(self):
        src = _ado()
        for prog in ("_dash_render_immediate", "_dash_prepare_spec"):
            body = _program_body(src, prog)
            writes = [m.start() for m in re.finditer(
                r"_dash_write_data \"", body)]
            assert writes, prog
            for w in writes:
                before = body[:w]
                chk = before.rfind("_dash_zero_obs_check ")
                gen = max(before.rfind("_dash_wexp_gen "),
                          before.rfind("_dash_frames_stack "))
                assert chk > gen > 0, (prog, w)

    def test_every_zero_exit_sets_the_flag(self):
        body = _program_body(_ado(), "_dash_process_segment")
        n = 0
        for word, code in (("observation numbers out of range", "198"),
                           ("bands must be between 1 and 200", "198"),
                           ("no observations", "2000")):
            i = body.find('display as error "%s"' % word)
            assert i > 0, word
            j = body.find("exit %s" % code, i)
            assert 'global dash__zo "`ptype\'"' in body[i:j], word
            n += 1
        assert n == 3

    def test_the_by_block_covers_literal_types(self):
        body = _program_body(_ado(), "_dash_plot")
        assert "if `: length local g_by' & !`_by_lit' {" not in body
        assert "_by_lit" not in body

    def test_graph_keys_are_read_after_the_plots(self):
        body = _program_body(_ado(), "_dash_zero_obs_check")
        reads = re.findall(r"_dash_json_get_str\(([^\n]*)", body)
        graph = [r for r in reads
                 if re.search(r'"(qual_col|qual_col_total|by)"', r)
                 and "`zr'" not in r]
        assert len(graph) == 3
        for r in graph:
            assert r.startswith("substr(") and "`zp' + 1" in r, r
        assert "_dash_zo_records(" in body

    def test_every_by_exit_names_the_plots(self):
        body = _program_body(_ado(), "_dash_plot")
        a = body.find("_dash_by_panels `_by_vars'")
        assert a > 0
        exits = [m.start() for m in re.finditer(r"exit 198", body[a:])][:3]
        assert len(exits) == 3
        prev = 0
        for e in exits:
            assert "_dash_zo_line " in body[a + prev:a + e]
            prev = e

    def test_the_check_runs_where_the_data_is_written(self):
        src = _ado()
        spec = _program_body(src, "_dash_prepare_spec")
        st = spec.find("capture noisily _dash_frames_stack ")
        chk = spec.find(
            "capture noisily frame `_dash_stk': _dash_zero_obs_check ")
        wr = spec.find("frame `_dash_stk': _dash_write_data ")
        assert 0 < st < chk < wr
        # In place or in 35-08's working frame: the prefix _dash_write_data
        # runs under (`_xfp', "" or "frame `_dash_xf':") on both routes.
        for prog in ("_dash_render_immediate", "_dash_prepare_spec"):
            body = _program_body(src, prog)
            w = body.find("capture noisily `_xfp' _dash_write_data ")
            c = body.rfind("capture noisily `_xfp' _dash_zero_obs_check ",
                           0, w)
            assert 0 < c < w, prog
            assert 'local _xfp "frame `_dash_xf\':"' in body[:c], prog

    def test_the_flag_is_dropped_before_each_segment(self):
        body = _program_body(_ado(), "_dash_plot")
        lines = body.splitlines()
        calls = [i for i, ln in enumerate(lines)
                 if "_dash_process_segment `" in ln]
        assert len(calls) == 1
        i = calls[0]
        assert lines[i].strip().startswith(
            "capture noisily _dash_process_segment ")
        assert lines[i - 1].strip() == "capture macro drop dash__zo"
