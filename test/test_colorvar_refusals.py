"""test_colorvar_refusals.py -- WP-42 section 42-05: colordiscrete
colorlevels() cuts (CV-2), the colorvar value refusals (CV-9), the
malformed colour-key options (CV-10) and the colorvar() layer with no
observation (CV-14), against twoway's own answers.

test/fixtures/colorvar_refusal_truth.json is written by
scripts/extract_colorvar_refusal_truth.do: each probe run drawn under
capture noisily, its rc and printed lines, and for a drawn graph the key's
texts (right of the plot region, top to bottom) and the in-region marker
fills.  The refusals themselves are compared with dash live by
test/test_option_validation.cscript (Q4205-2, Q4205-4) and
test/test_wp42_truth.cscript (Q4205-3); this file pins the arithmetic, the
two renderers and the code that gives those answers.
"""
import functools
import json
import os
import re
import sys

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_colorvar_truth as ct  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "colorvar_refusal_truth.json")
_MODES = ["saved", "served"]


@functools.lru_cache(maxsize=None)
def _truth():
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _probe(key):
    return _truth()["probes"][key]


def _read(name):
    with open(os.path.join(_ROOT, name), encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# CV-2: colordiscrete colorlevels(k) makes k cuts at the range over k + 1.
# ---------------------------------------------------------------------------

#: probe -> (dataset, type, y, x, colorvar options)
_L = {
    "L1": ("auto", "scatter", "mpg", "weight",
           {"colorvar": "rep78", "colordiscrete": "colordiscrete",
            "colorlevels": "4"}),
    "L2": ("steps", "scatter", "y", "x",
           {"colorvar": "z", "colordiscrete": "colordiscrete",
            "colorlevels": "4"}),
    "L3": ("steps", "scatter", "y", "x",
           {"colorvar": "z", "colordiscrete": "colordiscrete",
            "colorlevels": "4", "colorvarminmax": "colorvarminmax"}),
    "L4": ("steps", "scatter", "y", "x",
           {"colorvar": "z", "colorlevels": "4"}),
    "L5": ("steps", "line", "y", "x",
           {"colorvar": "z", "colordiscrete": "colordiscrete",
            "colorlevels": "4"}),
}


def _frame(ds):
    d = _truth()["_data"][ds]
    return pd.DataFrame({k: [np.nan if v is None else float(v) for v in vs]
                         for k, vs in d.items()})


@functools.lru_cache(maxsize=None)
def _models(pid, mode):
    ds, ptype, y, x, opts = _L[pid]
    p = plot_for(ptype, dict(opts))
    p.update(yvar=y, xvar=x)
    spec = tp._spec([p])
    saved = tp._DF
    tp._DF = _frame(ds)
    try:
        return ct._render(spec, mode)
    finally:
        tp._DF = saved


def _numbers(texts):
    """The key's cut values, sorted.  Its order, its '(missing)' entry and
    its interval texts ('0\u201325': the closed outer ends twoway does not
    write) are the key cell's, CV-3's, so an interval key gives its inner
    bounds."""
    num = r"-?[\d,]*\.?\d+"
    plain = [t.strip() for t in texts]
    if any("\u2013" in t for t in plain):
        vals = sorted({float(v.replace(",", "")) for t in plain
                       for v in re.findall(num, t)})
        return vals[1:-1]
    return sorted(float(t.replace(",", "")) for t in plain
                  if re.fullmatch(num, t))


class TestTheCutRule:

    def test_discrete_adds_one_step(self):
        z = np.arange(0.0, 101.0, 10.0)
        assert dr._dash_colorvar_cuts(z, None, 4, False, discrete=True) \
            == [20.0, 40.0, 60.0, 80.0]
        assert dr._dash_colorvar_cuts(z, None, 4, True, discrete=True) \
            == [0.0, 20.0, 40.0, 60.0, 80.0, 100.0]
        assert dr._dash_colorvar_cuts(z, None, 4, False) == [25.0, 50.0,
                                                             75.0]
        # The keyword default leaves colorcuts() alone.
        assert dr._dash_colorvar_cuts(z, [30, 60], None, False,
                                      discrete=True) == [30.0, 60.0]


class TestAgainstTwoway:
    """L1-L5 drawn by dash, saved and served: the key's numbers equal
    twoway's, and each marker's colour group as twoway's."""

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("pid", sorted(_L))
    def test_probe(self, pid, mode):
        probe = _probe(pid)
        assert probe["rc"] == 0
        d_texts, _framed = ct._dash_key(_models(pid, mode))
        assert _numbers(d_texts) == _numbers(probe["key_texts"]), \
            (pid, d_texts, probe["key_texts"])
        if _L[pid][1] != "scatter":
            return
        got = {}
        for f in ct.cb._figures(_models(pid, mode)):
            for c, n in ct._dash_colours(f, "scatter").items():
                got[c] = got.get(c, 0) + n
        want = {}
        for c in probe["marker_fills"]:
            want[c] = want.get(c, 0) + 1
        assert ct._cv_same_counts(got, want) is None, pid


class TestTheRelevelTwins:
    """After a move the saved page's JS and the served Python cut L2's z
    alike, with the colordiscrete step."""

    def test_discrete_levels_agree(self):
        from js_runner import run_js
        js = dr._DASH_CVAR_RELEVEL_JS
        m = re.search(r"function dash_cvar_relevel_bins\(pl, kv\) \{", js)
        assert m, "dash_cvar_relevel_bins is not in _DASH_CVAR_RELEVEL_JS"
        # The levels rule the JS twin runs, lifted whole from its body
        # (WP-42 CV-12: the one-value branch beside it).
        body = js[m.start():]
        rule = re.search(r"\n(    // Under colordiscrete one more step.*?"
                         r"\n    \}\n)", body, re.S)
        assert rule, "the JS levels rule moved"
        cases = [(True, 0.0, 100.0, 4, False), (False, 0.0, 100.0, 4, False),
                 (False, 3.0, 3.0, 3, False), (False, 3.0, 3.0, 3, True),
                 (True, 3.0, 3.0, 2, False)]
        script = ("const out = [];\n"
                  "for (const [disc, lo, hi, n, mm] of %s) {\n"
                  "  const pl = {nlevels: n, discrete: disc, minmax: mm,"
                  " cuts: null}; let eff = [];\n" % json.dumps(cases)
                  + rule.group(1) + "\n  out.push(eff);\n}\n"
                  "console.log(JSON.stringify(out));\n")
        js_out = run_js(script)
        z = np.arange(0.0, 101.0, 10.0)
        py = [dr._dash_colorvar_cuts(z if lo != hi else [lo], None, n, mm,
                                     discrete=d)
              for d, lo, hi, n, mm in cases]
        assert [[round(v, 9) for v in e] for e in js_out] == \
            [[round(v, 9) for v in e] for e in py]
        assert py[2:] == [[3.0, 3.0], [3.0, 3.0, 3.0, 3.0], [3.0, 3.0]]
        assert py[0] == [20.0, 40.0, 60.0, 80.0]

    def test_the_served_twin_passes_the_flag(self):
        src = _read("dash_render.py")
        start = src.index("def _dash_cvar_relevel_bins(")
        body = src[start:src.index("\ndef ", start + 10)]
        assert 'discrete=bool(plan.get("discrete"))' in body


class TestTheHelp:

    def test_the_colordiscrete_levels_sentence(self):
        text = " ".join(_read("dash.sthlp").split())
        assert ("{cmd:colorlevels(}{it:#}{cmd:)} makes {it:#} cuts at the "
                "range over {it:#} + 1, each cut a level, as {cmd:twoway} "
                "draws them ({cmd:colorlevels(4)} over 0 to 100 cuts at 20 "
                "40 60 80") in text


# ---------------------------------------------------------------------------
# CV-9: colorcuts(), colorlevels() and colorvar() through twoway's commands.
# ---------------------------------------------------------------------------

def _program(src, name):
    start = src.index("program define %s" % name)
    return src[start:src.index("\nend\n", start)]


class TestTheAdoText:

    def test_twoways_commands(self):
        src = _read("dash.ado")
        body = _program(src, "_dash_cv_value_check")
        assert "confirm numeric variable `macval(value)'" in body
        assert "syntax , COLORCUTs(numlist sort)" in body
        assert "syntax [ , COLORLEVels(integer -9999) ]" in body
        assert "_dash_so_unsafe" in body
        vv = _program(src, "_dash_validate_value")
        assert "_dash_cv_value_check" in vv
        # 35-07's string-colorvar lines are given by confirm now.
        assert "found where numeric variable expected" not in src

    def test_key_option_checks(self):
        """CV-10: clegend() is read when a layer has colorvar(), plegend()
        when one has coloruseplegend, zscale() always (twoway's tables,
        measured: K_*), and zlabel() joins the label-list refusals."""
        src = _read("dash.ado")
        start = src.index("program define _dash_plot\n")
        body = src[start:src.index("\nend\n", start)]
        assert "if `_g_cvn' _dash_subopt_check clegend" in body
        assert "if `_g_cvupl' _dash_subopt_check plegend" in body
        assert "_dash_subopt_check zscale" in body
        loop = re.search(r"foreach _alo in ([^{]*)\{", body).group(1)
        assert "zlabel" in loop.split()

    def test_the_clegend_table_is_twoways(self):
        """Every clegend() word twoway draws is in the table, and every
        word it refuses at the graph level is not (K_cleg_<word>)."""
        src = _read("dash_parse.mata")
        start = src.index('if (fam == "clegend")')
        block = src[start:src.index("}", start)]
        rows = set(re.findall(r'"([a-z0-9]+)", "[a-z0-9]+", "1"', block))
        for key, p in _truth()["probes"].items():
            m = re.fullmatch(r"K_cleg_([a-z0-9]+)", key)
            if not m or m.group(1) in ("bogus", "bogusp", "abbrev"):
                continue
            assert (m.group(1) in rows) == (p["rc"] == 0), (key, p["rc"])


# ---------------------------------------------------------------------------
# CV-14: a colorvar() layer with no observation, as twoway answers it.
# ---------------------------------------------------------------------------

#: E_* probes twoway refuses for the layer itself (not by()'s byempty).
_E_REFUSED = ("E_empty", "E_empty_in", "E_empty_line", "E_empty_levels",
              "E_empty_cuts", "E_nodata", "E_two")
#: E_* probes twoway draws: colordiscrete (colorvar(i.x) too) and the
#: all-missing layers.
_E_DRAWN = ("E_empty_disc", "E_nodata_disc", "E_empty_ipre", "E_allmiss",
            "E_allmiss_y")


def _mata_function(src, name):
    start = src.index(" %s(" % name, src.index("\nstring rowvector " + name))
    return src[start:src.index("\n}\n", start)]


class TestTheEmptyLayer:

    def test_the_rule_matches_the_fixture(self):
        body = _mata_function(_read("dash_parse.mata"),
                              "_dash_zero_obs_cvrule")
        lits = re.findall(r'"([^"]*)"', body)
        rows = _truth()["probes"]
        for key in _E_REFUSED:
            p = rows[key]
            assert p["rc"] != 0, key
            assert str(p["rc"]) in lits, key
            for ln in p["lines"]:
                assert ln in lits, (key, ln)
        for key in _E_DRAWN:
            assert rows[key]["rc"] == 0, key
        # The colordiscrete rule: twoway draws the empty discrete layer.
        assert "discrete" in body
        chk = _program(_read("dash.ado"), "_dash_zero_obs_check")
        assert "_dash_zero_obs_cvrule(" in chk
        assert re.search(r"foreach key in [^{]*\bcolorvar colordiscrete\b", chk)

    def test_the_help_sentence(self):
        text = " ".join(_read("dash.sthlp").split())
        assert ("A {cmd:colorvar()} layer whose {cmd:if} or {cmd:in} keeps "
                "no observation is refused with {cmd:twoway}'s message and "
                "return code, r(3001), as {cmd:twoway} answers it when it "
                "draws the graph, unless it is {cmd:colordiscrete}") in text
        assert "draws no key ({cmd:twoway} stops with r(3001))" not in text
