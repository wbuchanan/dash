"""by()'s econ, stata7, rescale and combine bystyles (WP-31 section 44,
D10c).

Measured (scripts/extract_bystyle_truth.do -> test/fixtures/
bystyle_truth.json, s2color): twoway draws ``by(rep78, style(econ))``,
``style(stata7)`` and ``style(rescale)`` exactly -- the exported SVGs are
line for line the same -- as ``by(rep78, <words>) <options>`` read from
their bygraphstyle files: econ is the default with ``subtitle(,
margin(small)) plotregion(color(edkbg) margin(t=5))``; stata7 ``edgelabel
ixaxes iyaxes imargin(small)`` with its twoway_options and an unboxed
label; rescale ``rescale individual imargin(medsmall)`` with a boxed
label in the foreground line and ``#3`` labels.  dash named econ and
stata7 and drew only rescale's and combine's separate scales.  combine's
graph regions (``combineregion``, which twoway itself does not find) do
not reduce to options: its scales are drawn, the rest named.
"""
import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_by_axes_keys as tk  # noqa: E402
import test_by_remainder as tr  # noqa: E402

with open(os.path.join(_HERE, "fixtures", "bystyle_truth.json"),
          encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)

MODES = ("saved", "served")
_EXACT = ("econ", "stata7", "rescale")
#: The measured options dash does not draw, per style: left out of the
#: expansion and named once (D10c residual).
_LEFT = {"econ": {"subtitle": None},
         "stata7": {"xmtick": "##4", "ymtick": "##4"},
         "rescale": {"subtitle": None}}
_NOTE = {
    "econ": "dash: by() sub-option style(econ): the panel labels' "
            "margin(small) is not drawn; the rest of the style is.",
    "stata7": "dash: by() sub-option style(stata7): the minor ticks' "
              "major_horiz_nolabel and major_vert_nolabel styles are not "
              "drawn; the rest of the style is.",
    "rescale": "dash: by() sub-option style(rescale): the panel labels' "
               "astextbox and foreground outline is not drawn; the rest of "
               "the style is."}


def _drawn_opts(style):
    out = _opts(TRUTH["styles"][style]["options"])
    for k, v in _LEFT[style].items():
        if v is None:
            out.pop(k, None)
        else:
            out[k] = v
    return out


def _opts(text):
    """``{key: value}`` of an option text as dash.ado writes a graph's
    options (``ylabels(#3)`` is ylabel ``#3``)."""
    canon = {"ylabels": "ylabel", "xlabels": "xlabel", "xmticks": "xmtick",
             "ymticks": "ymtick"}
    out = {}
    for tok in dr._dash_by_tokens(text):
        name, arg = tok.split("(", 1)
        out[canon.get(name, name)] = arg[:-1]
    return out


class TestTheFixture:
    def test_meta_and_measure(self):
        assert sorted(TRUTH["_meta"]) == ["born_date", "dash_commit",
                                          "extracted", "source",
                                          "stata_version"]
        for s in _EXACT:
            assert TRUTH["styles"][s]["diff_lines"] == 0, s
        assert TRUTH["styles"]["combine"]["diff_lines"] > 0


class TestTheExpansion:
    @pytest.mark.parametrize("style", _EXACT)
    def test_measured(self, style):
        rec = TRUTH["styles"][style]
        spec = tk._spec([tk._graph("g", tk._TWO,
                                   {"by": f"rep78, style({style})"})])
        out = dr._dash_bystyle_route(spec)
        go = out["graphs"][0]["graph_options"]
        words = dr._dash_by_tokens(go["by"].partition(",")[2])
        assert words == rec["by_words"].split(), words
        for k, v in _drawn_opts(style).items():
            assert go.get(k) == v, (k, go.get(k), v)
        assert "subtitle" not in go or style == "stata7"

    def test_a_users_own_option_wins(self):
        spec = tk._spec([tk._graph("g", tk._TWO, {
            "by": "rep78, style(rescale)", "xlabel": "#6"})])
        go = dr._dash_bystyle_route(spec)["graphs"][0]["graph_options"]
        assert go["xlabel"] == "#6" and go["ylabel"] == "#3"

    def test_combine_and_others_untouched(self):
        for by in ("rep78, style(combine)", "rep78", "rep78, style(compact)",
                   'rep78, title("style(econ)")'):
            spec = tk._spec([tk._graph("g", tk._TWO, {"by": by})])
            assert dr._dash_bystyle_route(spec)["graphs"][0][
                "graph_options"]["by"] == by


def _summary(roots):
    out = []
    for name, g in sorted(tk._grids(roots).items()):
        for c in g.children:
            f = c[0]
            out.append((name, type(f).__name__,
                        len(getattr(f, "renderers", []) or []),
                        tuple(sorted(type(a).__name__ for a in
                                     (f.left + f.below + f.above + f.right)))))
    return out


@pytest.mark.parametrize("mode", MODES)
class TestDrawn:
    @pytest.mark.parametrize("style", _EXACT)
    def test_as_its_expansion(self, mode, style):
        rec = TRUTH["styles"][style]
        by_words = (", " + rec["by_words"]) if rec["by_words"] else ""
        a = tk._spec([tk._graph("g", tk._TWO,
                                {"by": f"rep78, style({style})"})],
                     scheme="s2color")
        go = dict({"by": "rep78" + by_words}, **_drawn_opts(style))
        b = tk._spec([tk._graph("g", tk._TWO, go)], scheme="s2color")
        ra, na, _ = tk._build(mode, a, data=tr._data())
        rb, nb, _ = tk._build(mode, b, data=tr._data())
        assert _summary(ra) == _summary(rb)
        assert [n for n in na if f"style({style})" in n] == [_NOTE[style]]
        assert [n for n in na if "not implemented" in n] == \
            [n for n in nb if "not implemented" in n]

    def test_combine_still_named(self, mode):
        spec = tk._spec([tk._graph("g", tk._TWO,
                                   {"by": "rep78, style(combine)"})],
                        scheme="s2color")
        _r, notes, _ = tk._build(mode, spec, data=tr._data())
        assert [n for n in notes if "style(combine)" in n]
