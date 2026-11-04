"""A qualifier's logical operators select the rows Stata selects, in both modes.

Measured by the maintainer 23sep2026 at c0200c0 on sysuse auto, and again
24sep2026 at 2df1900 with the console binary: ``if !foreign`` and
``if ~foreign`` were translated to pandas' ``~foreign``, which pandas cannot
apply to a float ("ufunc 'invert' not supported for the input types"), so
the qualifier was skipped with a warning and both modes drew all 74 cars
where Stata's ``count if !foreign`` is 52.  Measuring the rest of the logical
operators found more of the same rule broken:

* ``if foreign`` -- a number standing alone as the condition -- was handed to
  ``DataFrame.query`` as it was, and pandas indexed the frame BY ITS VALUES:
  both modes drew observation 1 fifty-two times and observation 2 twenty-two
  times, with no warning, where Stata draws the 22 foreign cars.
* ``if foreign & rep78 == 3`` (a number beside ``&`` or ``|``) was skipped:
  "unsupported operand type(s) for &: 'float' and 'bool'".
* ``if foreign ! = 1``, ``~ = 1``, ``mpg < = 20`` and ``mpg > = 20`` -- Stata
  reads a blank inside a two-character operator (52, 52, 38 and 39 rows) --
  were skipped as invalid syntax.
* a chain of comparisons was read as Python chains them (``10 < mpg < 20``
  is ``10 < mpg and mpg < 20``), where Stata evaluates ``(10 < mpg) < 20``,
  true for every car, and ranks the relational operators ``!=``, ``>``,
  ``<``, ``<=``, ``>=``, ``==`` from tightest to loosest (measured below).

Stata's rule for all of them: a number is true when it is not zero, and a
missing value is not zero, so ``!x`` is true exactly where x == 0; ``!``
binds tighter than any other operator, so ``!foreign == 1`` is
``(!foreign) == 1``; and ``!`` on a string is a type mismatch, r(109).

The oracle for every case is Stata itself, measured 24sep2026 with
the console binary, ``stata-mp -b do``, on the twelve observations of
``_LG_ROWS`` (entered with ``input``): each case's rows are Stata's
``levelsof id if <qualifier>``, and a refused case's return code is
``capture count if <qualifier>``'s.  The x the scatter draws is ``id``, so
the drawn x values name the rows drawn.  The saved page is read from the
document embedded in the HTML ``DashRenderer.render`` returns; the served
app is the generated module's ``make_document`` run on a fresh Document.
test_qualifier_literals.cscript QL-16..QL-19 run the same rules through
Stata itself on sysuse auto, on both routes.
"""
import base64
import html as _html
import json
import math
import os
import re
import sys
import time
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import exec_app  # noqa: E402
from conftest import drawn_renderers, is_key_proxy  # noqa: E402

# ---------------------------------------------------------------------------
# The data: (id, g, x, r, s, m), exactly as Stata was given it with `input'
# (x a float, s a str4).  g is 0/1 like foreign; x holds zeros, a negative,
# fractions and two missing values; r is like rep78, never zero and missing
# three times; s is a string with empty values; m is like mpg.  w, the KPI's
# variable, is 2000 + 50*id.
# ---------------------------------------------------------------------------
_NA = float("nan")
_LG_ROWS = [
    (1, 0, 0.0, 3, "", 12), (2, 1, 1.0, 4, "a", 15),
    (3, 0, -1.0, _NA, "b", 18), (4, 1, 0.5, 5, "", 21),
    (5, 0, _NA, 1, "AMC", 24), (6, 1, 0.0, 3, "x", 27),
    (7, 0, 2.0, _NA, "", 30), (8, 1, _NA, 2, "a", 33),
    (9, 0, 0.0, 4, "zz", 11), (10, 1, -0.25, 3, "", 19),
    (11, 0, 3.0, 5, "b", 20), (12, 1, 0.0, _NA, "q", 22),
]
_ALL = frozenset(range(1, 13))
_ODD = frozenset({1, 3, 5, 7, 9, 11})      # g == 0
_EVEN = frozenset({2, 4, 6, 8, 10, 12})    # g == 1
_X_ZERO = frozenset({1, 6, 9, 12})         # x == 0
_X_TRUE = frozenset({2, 3, 4, 5, 7, 8, 10, 11})   # x != 0, missing included


def _rows(text):
    return frozenset(int(t) for t in text.split())


#: (label, qualifier, Stata's rows).  Each rows value is Stata's
#: `levelsof id if <qualifier>' on _LG_ROWS (console binary, 24sep2026).
_NOT_CASES = [
    ("bang", "!g", _ODD),
    ("tilde", "~g", _ODD),
    ("bang_blank", "! g", _ODD),
    ("tilde_blank", "~ g", _ODD),
    ("bang_paren", "!(g)", _ODD),
    ("bang_of_comparison", "!(g == 1)", _ODD),
    ("parenthesised_bang", "(!g)", _ODD),
    ("bang_bang", "!!g", _EVEN),
    ("bang_tilde", "!~g", _EVEN),
    ("tilde_tilde", "~~g", _EVEN),
    ("bang_blank_bang", "! ! g", _EVEN),
    # ! binds tighter than a comparison: (!g) == 1, (!g) == 0, ...
    ("bang_then_eq_1", "!g == 1", _ODD),
    ("bang_then_eq_0", "!g == 0", _EVEN),
    ("bang_then_ne_1", "!g != 1", _EVEN),
    ("bang_then_spaced_ne", "!g ! = 1", _EVEN),
    ("bang_then_gt_0", "!g > 0", _ODD),
    ("bang_then_lt_1", "!g < 1", _EVEN),
    # ~= is not-equal, written against a not in either spelling.
    ("bang_then_tilde_ne", "!g~=1", _EVEN),
    ("tilde_then_tilde_ne", "~g~=1", _EVEN),
    ("bang_then_tilde_ne_0", "!g ~= 0", _ODD),
    ("tilde_ne_unspaced", "g~=0", _EVEN),
    ("bang_number_tilde_ne", "!x ~= 1", _X_TRUE),
    ("tildes_both_ways", "~x~=0 & ~g", _rows("1 9")),
    ("bang_and", "!g & r == 3", _rows("1")),
    ("bang_or", "!g | r == 5", _rows("1 3 4 5 7 9 11")),
    ("bang_unspaced", "!g==1&r==3", _rows("1")),
    ("bang_or_unspaced", "!g==0|g==1", _EVEN),
    ("two_bangs_of_comparisons", "!(g == 1) & !(r == 3)",
     _rows("3 5 7 9 11")),
    # A number: true when not zero -- a missing value included.
    ("bang_number", "!x", _X_ZERO),
    ("tilde_number", "~x", _X_ZERO),
    ("bang_bang_number", "!!x", _X_TRUE),
    ("bang_number_eq_0", "!x == 0", _X_TRUE),
    ("bang_negated_number", "!(-x)", _X_ZERO),
    ("bang_number_and_bang", "!x & !g", _rows("1 9")),
    ("bang_never_zero", "!r", frozenset()),
    ("bang_bang_never_zero", "!!r", _ALL),
    ("bang_never_zero_eq_0", "!r == 0", _ALL),
    ("bang_missing", "!missing(r)", _rows("1 2 4 5 6 8 9 10 11")),
    ("tilde_missing", "~missing(r)", _rows("1 2 4 5 6 8 9 10 11")),
    ("bang_inlist", "!inlist(r, 3, 4)", _rows("3 4 5 7 8 11 12")),
    ("bang_inrange", "!inrange(r, 2, 4)", _rows("3 4 5 7 11 12")),
    ("bang_string_comparison", '!(s == "a")',
     _rows("1 3 4 5 6 7 9 10 11 12")),
]

#: A number standing alone where Stata wants a true/false value.
_TRUTH_CASES = [
    ("bare", "g", _EVEN),
    ("bare_parenthesised", "(g)", _EVEN),
    ("bare_with_zeros_and_missing", "x", _X_TRUE),
    ("bare_never_zero", "r", _ALL),
    ("bare_and", "g & r == 3", _rows("6 10")),
    ("bare_or", "g | r == 5", _rows("2 4 6 8 10 11 12")),
    ("two_bare_and", "g & x", _rows("2 4 8 10")),
    ("two_bare_or", "x | g", _rows("2 3 4 5 6 7 8 10 11 12")),
    ("bare_negated", "-x", _X_TRUE),
]

#: A blank inside a two-character operator: Stata reads the operator.
_SPACED_CASES = [
    ("bang_blank_equals", "g ! = 1", _ODD),
    ("tilde_blank_equals", "g ~ = 1", _ODD),
    ("bang_two_blanks_equals", "g !  = 1", _ODD),
    ("less_blank_equals", "m < = 20", _rows("1 2 3 9 10 11")),
    ("greater_blank_equals", "m > = 20", _rows("4 5 6 7 8 11 12")),
]

#: Relational operators chained: Stata evaluates left to right with its own
#: ranking, != > < <= >= == from tightest to loosest, then & and |.
_CHAIN_CASES = [
    ("lt_lt", "10 < m < 20", _ALL),                 # (10 < m) < 20
    ("gt_gt", "m > 20 > 0", _rows("4 5 6 7 8 12")),  # (m > 20) > 0
    ("eq_gt", "m == 22 > 0", frozenset()),          # m == (22 > 0)
    ("eq_gt_self", "g == g > 0", _ALL),             # g == (g > 0)
    ("gt_lt", "m > 20 < 1", _rows("1 2 3 9 10 11")),  # (m > 20) < 1
    ("lt_gt", "1 < m > 20", frozenset()),           # 1 < (m > 20)
    ("eq_ne", "g == 0 != 0", _ODD),                 # g == (0 != 0)
    ("le_ge", "0 <= m >= 25", frozenset()),         # (0 <= m) >= 25
    ("and_before_or", "g == 1 | g == 0 & r == 3", _rows("1 2 4 6 8 10 12")),
]

_APPLIED = _NOT_CASES + _TRUTH_CASES + _SPACED_CASES + _CHAIN_CASES
_APPLIED_IDS = [c[0] for c in _APPLIED]

#: Stata refuses these: `capture count if' is r(109) "type mismatch".
_MISMATCH = ["!s", "~s", "s", "-s", "s & g", "g | s", "s == 1", 'g == "a"',
             '!s == "x"', "!(s)"]
#: ... r(198) "invalid syntax": a sign right after !, or a ! with nothing
#: to apply to, or ! and ~ before `=='.
_INVALID = ["!-x", "~-x", "! -x", "!+x", "!!-x", "!", "g !", "g ! == 1",
            "g ~ == 1"]
#: ... r(111) "nosuch not found".
_UNKNOWN = ["nosuch == 1", "!nosuch", "g == 1 & nosuch == 1", "nosuch"]


def _frame():
    return pd.DataFrame({
        "id": [float(r[0]) for r in _LG_ROWS],
        "g": [float(r[1]) for r in _LG_ROWS],
        "x": [r[2] for r in _LG_ROWS],
        "r": [float(r[3]) for r in _LG_ROWS],
        "s": [r[4] for r in _LG_ROWS],
        "m": [float(r[5]) for r in _LG_ROWS],
        "w": [2000.0 + 50.0 * r[0] for r in _LG_ROWS],
    })


def _w_sum(rows):
    return sum(2000.0 + 50.0 * i for i in rows)


def _spec(qualifier, kpi=False, filt=""):
    """One scatter of m on id, qualified as dash.ado writes a one-segment
    command: on the plot AND promoted to the graph (``_dash_plot``); a KPI,
    ``sum(w)`` under the same qualifier, when *kpi*."""
    plot = {"type": "scatter", "yvar": "m", "xvar": "id", "options": {},
            "if_expr": qualifier, "in_expr": ""}
    kpis = []
    if kpi:
        kpis = [{"name": "k1", "stat": "sum", "var": "w", "fmt": "%9.0f",
                 "title": "W", "subtitle": "", "color": "", "bgcolor": "",
                 "update": "filter", "if_expr": qualifier, "in_expr": ""}]
    return {
        "graphs": [{"plots": [plot], "graph_options": {"name": "g1"},
                    "if_expr": qualifier, "in_expr": ""}],
        "kpis": kpis,
        "build_options": {
            "layout": "auto", "link": "", "filter": filt, "theme": "",
            "scheme": "", "session_scheme": "", "title": "", "subtitle": "",
            "registry": "g1" + (" k1" if kpi else ""), "tabs": "",
            "filter_position": "top", "level": "95", "formats": {}},
    }


def _write(tmp_path, spec, df=None):
    """Spec and data files; ``s`` is flagged a string the way jsonio flags
    one (variableIsString), and a missing number is JSON null."""
    df = _frame() if df is None else df
    sp = os.path.join(str(tmp_path), "spec.json")
    dp = os.path.join(str(tmp_path), "data.json")
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    cols = list(df.columns)
    values = [{k: (None if isinstance(v, float) and math.isnan(v) else v)
               for k, v in rec.items()}
              for rec in df.to_dict(orient="records")]
    strings = {c: not pd.api.types.is_numeric_dtype(df[c]) for c in cols}
    with open(dp, "w", encoding="utf-8") as fh:
        json.dump({"StataJSON": {
            "variableNames": cols, "variableLabels": {c: c for c in cols},
            "valueLabels": {}, "valueLabelNames": {},
            "variableIsString": strings, "variableTypeIsString": strings,
            "values": values}}, fh)
    return sp, dp


def _arr(v):
    """A column of a serialised Bokeh document, whichever encoding."""
    if isinstance(v, list):
        return v
    if isinstance(v, dict) and v.get("type") == "ndarray":
        a = v.get("array")
        if isinstance(a, list):
            return a
        if isinstance(a, dict) and a.get("type") == "bytes":
            return list(np.frombuffer(base64.b64decode(a["data"]),
                                      dtype=v.get("dtype", "float64")))
    return []


def _keep(n, kind, values):
    if kind == "BooleanFilter":
        return [i for i, b in enumerate(list(values)[:n]) if b]
    if kind == "IndexFilter":
        return [int(i) for i in values if 0 <= int(i) < n]
    return list(range(n))


def _page_scatter(page):
    """(rows the scatter's source carries, the ids it draws through its
    view) read from the document embedded in a saved page."""
    m = re.search(r'<script type="application/json"[^>]*>(.*?)</script>',
                  page, re.S)
    assert m, "the saved page embeds no document"
    docs = json.loads(_html.unescape(m.group(1)))
    objs, stack = {}, [docs]
    while stack:
        v = stack.pop()
        if isinstance(v, dict):
            if v.get("type") == "object" and "id" in v and "name" in v:
                objs[v["id"]] = v
            stack.extend(v.values())
        elif isinstance(v, list):
            stack.extend(v)

    def ref(v):
        return objs.get(v["id"], v) if isinstance(v, dict) and "id" in v \
            else v

    found = []
    for o in objs.values():
        if o["name"] not in ("Figure", "Plot"):
            continue
        for rr in o.get("attributes", {}).get("renderers", []):
            g = ref(rr)
            a = g.get("attributes", {})
            if g.get("name") != "GlyphRenderer" or is_key_proxy(g) or \
                    ref(a.get("glyph", {})).get("name") != "Scatter":
                continue
            data = dict((k, v) for k, v in ref(a.get("data_source", {}))
                        .get("attributes", {}).get("data", {})
                        .get("entries", []))
            xs = [float(x) for x in _arr(data.get("id"))]
            view = ref(a.get("view", {}))
            f = ref(view.get("attributes", {}).get("filter", {}))
            kind = f.get("name", "") if isinstance(f, dict) else ""
            fa = f.get("attributes", {}) if isinstance(f, dict) else {}
            vals = _arr(fa.get("booleans" if kind == "BooleanFilter"
                               else "indices", []))
            found.append((len(xs), [xs[i] for i in _keep(len(xs), kind,
                                                        vals)]))
    assert len(found) == 1, f"expected one scatter layer, found {len(found)}"
    carried, drawn = found[0]
    return carried, sorted(int(v) for v in drawn)


def _doc_scatter(roots):
    """The same reading of a live document's models."""
    from bokeh.models import GlyphRenderer, Plot
    found = []
    for root in roots:
        for fig in root.select({"type": Plot}):
            for r in drawn_renderers(fig):
                if isinstance(r, GlyphRenderer) and \
                        type(r.glyph).__name__ == "Scatter":
                    found.append(r)
    assert len(found) == 1, f"expected one scatter layer, found {len(found)}"
    r = found[0]
    xs = [float(v) for v in r.data_source.data["id"]]
    f = getattr(r.view, "filter", None)
    kind = type(f).__name__ if f is not None else ""
    vals = (f.booleans if kind == "BooleanFilter"
            else f.indices if kind == "IndexFilter" else [])
    return len(xs), sorted(int(xs[i]) for i in _keep(len(xs), kind, vals))


def _saved(tmp_path, spec, df=None):
    """(saved page, renderer, warning texts)."""
    sp, dp = _write(tmp_path, spec, df)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r = dr.DashRenderer(sp, dp)
        page = r.render()
    return page, r, [f"{type(w.message).__name__}: {w.message}"
                     for w in caught]


def _served(tmp_path, spec, df=None):
    """(document, warning texts) from the generated app, run the way
    ``bokeh serve`` runs it: its make_document on a fresh Document."""
    from bokeh.document import Document
    sp, dp = _write(tmp_path, spec, df)
    ap = os.path.join(str(tmp_path), "app.py")
    with warnings.catch_warnings(record=True) as built:
        warnings.simplefilter("always")
        dr.ServerAppBuilder(sp, dp).build(ap)
    with open(ap, encoding="utf-8") as fh:
        src = fh.read()
    attach = "if __name__ != '__main__':\n    make_document(curdoc())"
    assert attach in src, "the generated app's curdoc attach moved"
    ns = {"__name__": "_lg_app"}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        exec_app(src.replace(attach, "pass"), "_lg_app.py", ns)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        doc = Document()
        ns["make_document"](doc)
    return doc, [f"{type(w.message).__name__}: {w.message}"
                 for w in list(built) + list(caught)]


@pytest.fixture(scope="module")
def served_app(tmp_path_factory):
    """The generated app's namespace -- its own copies of the qualifier
    readers -- without its curdoc attach."""
    tmp = tmp_path_factory.mktemp("lg_app")
    sp, dp = _write(tmp, _spec("g"))
    ap = os.path.join(str(tmp), "app.py")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(ap)
    with open(ap, encoding="utf-8") as fh:
        src = fh.read()
    attach = "if __name__ != '__main__':\n    make_document(curdoc())"
    assert attach in src, "the generated app's curdoc attach moved"
    ns = {"__name__": "_lg_app_ns"}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        exec_app(src.replace(attach, "pass"), "_lg_app_ns.py", ns)
    # The app's own function, not the renderer's.
    assert ns["_dash_qualified_frame"].__module__ == "_lg_app_ns"
    return ns


def _skips(msgs):
    return [m for m in msgs if "filter skipped" in m]


def _kpi(divs):
    for d in divs:
        m = re.search(r'id="kpi_val_k1"[^>]*>([^<]*)<', d.text or "")
        if m:
            return m.group(1).strip()
    raise AssertionError("no KPI card k1 was drawn")


# ---------------------------------------------------------------------------
# What each mode draws, against Stata's rows
# ---------------------------------------------------------------------------

class TestEachModeDrawsStatasRows:
    """Every case of _APPLIED, in both modes: the scatter draws exactly the
    rows Stata's `levelsof' names, the source carries only those rows (the
    graph's promoted qualifier restricts it), and nothing is skipped."""

    @pytest.mark.parametrize("label,qualifier,rows", _APPLIED,
                             ids=_APPLIED_IDS)
    def test_the_saved_page(self, tmp_path, label, qualifier, rows):
        page, _r, msgs = _saved(tmp_path, _spec(qualifier))
        carried, drawn = _page_scatter(page)
        assert not _skips(msgs), (label, _skips(msgs))
        assert drawn == sorted(rows), (
            f"{label}: `if {qualifier}' drew rows {drawn} on the saved "
            f"page; Stata selects {sorted(rows)}")
        assert carried == len(rows), (label, carried, len(rows))

    @pytest.mark.parametrize("label,qualifier,rows", _APPLIED,
                             ids=_APPLIED_IDS)
    def test_the_served_app(self, tmp_path, label, qualifier, rows):
        doc, msgs = _served(tmp_path, _spec(qualifier))
        carried, drawn = _doc_scatter(doc.roots)
        assert not _skips(msgs), (label, _skips(msgs))
        assert drawn == sorted(rows), (
            f"{label}: `if {qualifier}' drew rows {drawn} in the served "
            f"app; Stata selects {sorted(rows)}")
        assert carried == len(rows), (label, carried, len(rows))


#: Cases whose KPI and filter-move checks run: every operator family once,
#: each selecting some rows but not all (a KPI over no rows is its own
#: rule, test_kpi_values.py's).
_SAMPLE = [c for c in _APPLIED if c[0] in (
    "bang", "tilde", "bang_then_eq_1", "bang_or", "bang_number",
    "bang_inrange", "bare", "bare_and", "two_bare_or",
    "bang_blank_equals", "less_blank_equals", "gt_lt", "eq_ne")]


class TestAKpiSumsStatasRows:
    """``dash kpi sum(w) if <qualifier>``: both cards read Stata's sum --
    ``summarize w if <qualifier>, meanonly``'s r(sum), which is the sum of
    2000 + 50*id over the rows above; both were measured."""

    @pytest.mark.parametrize("label,qualifier,rows", _SAMPLE,
                             ids=[c[0] for c in _SAMPLE])
    def test_in_both_modes(self, tmp_path, label, qualifier, rows):
        from bokeh.models import Div
        spec = _spec(qualifier, kpi=True)
        _page, r, _ = _saved(tmp_path, spec)
        saved = _kpi(r.kpi_divs.values())
        doc, _ = _served(tmp_path, spec)
        served = _kpi([d for root in doc.roots
                       for d in root.select({"type": Div})])
        want = "%.0f" % _w_sum(rows)
        assert (saved, served) == (want, want), (
            f"{label}: `dash kpi sum(w) if {qualifier}' reads saved "
            f"{saved!r}, served {served!r}; Stata sums {want}")


class TestAFilterMoveKeepsTheQualifier:
    """The served filter callback applies the graph's qualifier again after
    every move, through its own copy of the translation: after a range
    filter moves to m in [10, 21] the scatter draws the qualifier's rows
    within that range."""

    @pytest.mark.parametrize("label,qualifier,rows", _SAMPLE,
                             ids=[c[0] for c in _SAMPLE])
    def test_a_range_move(self, tmp_path, label, qualifier, rows):
        from bokeh.models import RangeSlider
        doc, _ = _served(tmp_path, _spec(qualifier, filt="m, type(range)"))
        sliders = [s for root in doc.roots
                   for s in root.select({"type": RangeSlider})]
        assert len(sliders) == 1, sliders
        w = sliders[0]
        lo, hi = 10.0, 21.0
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            w.value = (lo, hi)
            for key in ("value", "value_throttled"):
                for cb in list(w._callbacks.get(key, [])):
                    cb("value", None, (lo, hi))
        _carried, drawn = _doc_scatter(doc.roots)
        m_of = {r[0]: r[5] for r in _LG_ROWS}
        kept = sorted(i for i in rows if lo <= m_of[i] <= hi)
        assert drawn == kept, (
            f"{label}: after the move the served scatter drew {drawn}; the "
            f"qualifier and the range keep {kept}")
        assert not _skips([str(c.message) for c in caught])


# ---------------------------------------------------------------------------
# What Stata refuses is refused aloud: every row drawn, the reason given
# ---------------------------------------------------------------------------

def _refused_in_both_modes(tmp_path, qualifier, reason):
    page, _r, saved_msgs = _saved(tmp_path, _spec(qualifier))
    doc, served_msgs = _served(tmp_path, _spec(qualifier))
    everything = sorted(_ALL)
    assert _page_scatter(page)[1] == everything, qualifier
    assert _doc_scatter(doc.roots)[1] == everything, qualifier
    for tag, msgs in (("saved", saved_msgs), ("served", served_msgs)):
        skipped = _skips(msgs)
        assert skipped, f"{tag}: `if {qualifier}' was not reported: {msgs}"
        assert all(m.endswith("filter skipped -- " + reason)
                   for m in skipped), (tag, qualifier, skipped)


class TestATypeMismatchIsRefusedAloud:
    """``!`` on a string -- and a string anywhere Stata wants a number -- is
    Stata's type mismatch, r(109) (each of _MISMATCH, measured).  Translated
    to ``~(s != 0)``, pandas would compare the text with 0 and select no
    row without a word; the qualifier is skipped instead, in Stata's
    words.  Before the fix (measured 24sep2026 at 2df1900) ``s == 1`` and
    ``g == "a"`` silently drew no row in both modes, and the rest were
    skipped in pandas' words: "bad operand type for unary ~: 'str'",
    "unsupported operand type(s) for &: 'str' and 'float'", and for a bare
    ``s`` a KeyError listing the column's values."""

    @pytest.mark.parametrize("qualifier", _MISMATCH)
    def test_in_both_modes(self, tmp_path, qualifier):
        _refused_in_both_modes(tmp_path, qualifier, "type mismatch")

    def test_the_check_reads_the_frames_types(self):
        df = _frame()
        assert dr._dash_if_type_problem('~((s != 0))', df) == \
            "type mismatch"
        assert dr._dash_if_type_problem('(s == "a") & (g != 0)', df) is None
        assert dr._dash_if_type_problem("(g == 1) | (x != 0)", df) is None
        # A column of nothing but missing values is a number, not text.
        df2 = pd.DataFrame({"z": [None, None]})
        assert dr._dash_if_type_problem("~((z != 0))", df2) is None
        # The precedence is pandas': & and | bind loosest, so this is two
        # comparisons, each of text with text or number with number.
        assert dr._dash_if_type_problem('s == "a" & g == 1', df) is None


class TestInvalidSyntaxIsRefusedAloud:
    """Stata refuses a sign right after ``!`` or ``~`` (``!-x``, ``!+x``),
    a ``!`` with nothing to apply to, and ``! ==``, r(198) "invalid
    syntax" (each of _INVALID, measured).  Written ``~-x``, pandas would
    try the bitwise inverse of -x, and read ``~-(g == 1)`` without a word;
    the ``!`` is kept, which no parser accepts."""

    @pytest.mark.parametrize("qualifier", _INVALID)
    def test_in_both_modes(self, tmp_path, qualifier):
        _refused_in_both_modes(tmp_path, qualifier,
                               "invalid syntax (<unknown>, line 1)")


class TestAnUnknownVariableIsNamed:
    """A qualifier naming a column the data lack was reported as "invalid
    syntax (<unknown>, line 1)", Python's words for a parse error; Stata
    names the variable (r(111), each of _UNKNOWN).  Reached from Stata
    through an abbreviation dash.ado does not expand yet (BUGS.md, "A
    qualifier that abbreviates a variable is skipped by the renderer") and
    by any spec written by hand."""

    @pytest.mark.parametrize("qualifier", _UNKNOWN)
    def test_in_both_modes(self, tmp_path, qualifier):
        _refused_in_both_modes(tmp_path, qualifier,
                               "variable nosuch not found")

    @pytest.mark.parametrize("qualifier,name", [
        ("_n <= 3", "_n"), ("m > _pi", "_pi"), ("_n == _N", "_n")])
    def test_a_stata_system_value_is_not_called_a_variable(
            self, tmp_path, qualifier, name):
        """``_n``, ``_N`` and ``_pi`` are Stata's own values, not
        variables: ``count if _n <= 10`` on auto is 10, ``mpg > _pi * 7``
        31 and ``_n == _N`` 1 (measured 24sep2026), and dash.ado hands such
        a qualifier to the renderer, which cannot evaluate them.  The
        warning says so rather than "variable _n not found"."""
        _refused_in_both_modes(tmp_path, qualifier,
                               f"{name} is not supported in a qualifier")

    def test_the_first_unknown_name_is_the_one_named(self):
        cols = ["g", "x"]
        assert dr._dash_if_unknown_name("(b == 1) & (a == 1)", cols) == "b"
        assert dr._dash_if_unknown_name("(g == 1)", cols) is None
        # A construct the whitelist refuses is not a missing variable, and
        # keeps the words the injection tests pin.
        assert dr._dash_if_unknown_name(
            "g == __import__('os').system('true')", cols) is None
        assert dr._dash_if_unknown_name("g ==", cols) is None
        # The name is echoed, so a long one is cut to Stata's 32.
        long = "v" * 5000
        assert dr._dash_if_unknown_name(long + " == 1", cols) == \
            "v" * 32 + "..."


class TestAMinusBeforeATrueFalseValueIsRefused:
    """Stata negates a true/false value numerically: ``-!g`` is -1 where g
    is 0, and ``-(g == 1)`` is -1 where g is 1 (measured: rows 1 3 5 7 9 11
    and 2 4 6 8 10 12).  pandas reads a minus on a true/false column as a
    logical not, so ``-(g == 1)`` would draw the other six rows without a
    word; the qualifier language dash evaluates has no arithmetic to say
    it with, so the qualifier is refused aloud."""

    @pytest.mark.parametrize("qualifier", ["-!g", "-(g == 1)"])
    def test_in_both_modes(self, tmp_path, qualifier):
        _refused_in_both_modes(
            tmp_path, qualifier,
            "a minus sign before a true/false value is not supported")


#: The missing idioms on a variable named e-acute (a copy of r) and one
#: named e-acute x (a copy of x): Stata's `levelsof id if' (console binary,
#: 24sep2026).
_E, _EX = "\u00e9", "\u00e9x"
_UNICODE_CASES = [
    ("idiom_on_a_unicode_name", _E + " < .", _rows("1 2 4 5 6 8 9 10 11")),
    ("idiom_on_a_name_ending_in_ascii", _EX + " < .",
     _rows("1 2 3 4 6 7 9 10 11 12")),
    ("missing_idiom_on_a_unicode_name", _EX + " >= .", _rows("5 8")),
    ("missing_function_on_a_unicode_name", "!missing(" + _E + ")",
     _rows("1 2 4 5 6 8 9 10 11")),
    ("idiom_and_a_not", _E + " != . & !" + _EX, _rows("1 6 9")),
]


class TestAMissingIdiomReadsAWholeName:
    """``x < .`` and its kin were matched from any character of a name
    that began with an ASCII letter, and from none of one that did not: a
    variable named e-acute was left as it came, which Python cannot
    parse, and one named e-acute x became e-acute followed by
    ``(x == x)``, a call --
    each skipped, every row drawn.  Anchored at the whole name, the
    idioms read it as Stata does."""

    @pytest.mark.parametrize("label,qualifier,rows", _UNICODE_CASES,
                             ids=[c[0] for c in _UNICODE_CASES])
    def test_in_both_modes(self, tmp_path, label, qualifier, rows):
        df = _frame()
        df[_E] = df["r"]
        df[_EX] = df["x"]
        page, _r, saved_msgs = _saved(tmp_path, _spec(qualifier), df)
        doc, served_msgs = _served(tmp_path, _spec(qualifier), df)
        assert not _skips(saved_msgs + served_msgs), (label, saved_msgs,
                                                       served_msgs)
        assert _page_scatter(page)[1] == sorted(rows), label
        assert _doc_scatter(doc.roots)[1] == sorted(rows), label


class TestABackslashInALiteralIsText:
    """BUGS.md BUG-PARSE-1's renderer half, the part no test held: a
    backslash before an ordinary letter.  Read as Python source,
    ``"C:\\data"`` raised SyntaxWarning "invalid escape sequence '\\d'"
    (a SyntaxError in a later Python) in both modes -- the escape reading
    WP-24 replaced (7c28802), whose decoy cases (backslash-n,
    backslash-u, a trailing backslash) are test_server.py
    TestIfExprQuoteHandling and test_qualifier_literals.cscript QL-01..04.
    Stata compares the characters: ``count if s == "C:\\data"`` is 1 on
    this frame (measured 24sep2026)."""

    def test_in_both_modes(self, tmp_path):
        df = _frame()
        df.loc[0, "s"] = "C:\\data"
        q = 's == "C:\\data"'
        page, _r, saved_msgs = _saved(tmp_path, _spec(q), df)
        doc, served_msgs = _served(tmp_path, _spec(q), df)
        for tag, msgs in (("saved", saved_msgs), ("served", served_msgs)):
            assert not [m for m in msgs if "SyntaxWarning" in m
                        or "escape" in m], (tag, msgs)
            assert not _skips(msgs), (tag, msgs)
        assert _page_scatter(page)[1] == [1]
        assert _doc_scatter(doc.roots)[1] == [1]


# ---------------------------------------------------------------------------
# The translation itself
# ---------------------------------------------------------------------------

class TestTheTranslation:
    """``_stata_logic_to_pandas`` on masked qualifier text."""

    @pytest.mark.parametrize("stata,rows", [
        ("!g", _ODD), ("~~g", _EVEN), ("!g == 1", _ODD), ("g", _EVEN),
        ("x | g", _rows("2 3 4 5 6 7 8 10 11 12")),
        ("10 < m < 20", _ALL), ("m == 22 > 0", frozenset()),
    ])
    def test_the_query_selects_statas_rows(self, stata, rows):
        df = _frame()
        out = dr._stata_logic_to_pandas(stata)
        assert dr._validate_if_expr(out, df.columns), out
        got = df.query(out, engine="python")
        assert sorted(int(v) for v in got["id"]) == sorted(rows), (stata,
                                                                   out)

    def test_a_not_keeps_its_tilde(self):
        # test_security_surface.py reads the translation this way.
        assert "~" in dr._stata_logic_to_pandas("!foreign")

    def test_what_it_cannot_read_is_left_to_the_whitelist(self):
        # A call, an attribute, a keyword and an unknown character are not
        # Stata's qualifier grammar: the text comes back with its logical
        # nots spelled ~, as before, for the whitelist to refuse.
        for text in ("__import__(\x010\x01)", "g.real", "g and x",
                     "g @ x", "!f(g)"):
            out = dr._stata_logic_to_pandas(text)
            assert out == re.sub(r"!(?!=)", "~", text), (text, out)

    def test_a_sign_after_a_not_stays_unreadable(self):
        # Stata: r(198).  The ! stays a !, which no parser accepts.
        for text in ("!-x", "~-x", "!+x", "!!-x"):
            out = dr._stata_logic_to_pandas(text)
            assert "!" in out and not dr._validate_if_expr(out, ["x"]), out


# ---------------------------------------------------------------------------
# CLAUDE.md rule 18 -- registered in test_adversarial_matrix.py's SURFACES
# under if_in_qualifiers
# ---------------------------------------------------------------------------

class TestAdversarialLogicalOperators:

    @pytest.mark.parametrize("qualifier", [
        "\uff01g",          # FULLWIDTH EXCLAMATION MARK
        "\uff5eg",          # FULLWIDTH TILDE
        "\u00acg",          # NOT SIGN
        "g \uff01= 1",      # a look-alike inside not-equal
        "!\u00a0g",         # a no-break space where a blank would do
        "g !\u00a0= 1",
    ], ids=["fullwidth_bang", "fullwidth_tilde", "not_sign",
            "fullwidth_bang_equals", "nbsp_after_bang", "nbsp_in_not_equal"])
    def test_a_lookalike_operator_is_not_read_as_one(self, tmp_path,
                                                     qualifier):
        """Bypass: only the ASCII spellings are Stata's operators -- Stata
        refuses all six, r(198) "invalid name" or "invalid '!'" (measured
        24sep2026).  A look-alike reaches neither the rewrite nor pandas as
        an operator; the qualifier is refused aloud in both modes."""
        _refused_in_both_modes(tmp_path, qualifier,
                               "invalid syntax (<unknown>, line 1)")

    @pytest.mark.parametrize("qualifier", [
        "!(g == __import__('os').system('touch SENTINEL'))",
        "!g | @os.system('touch SENTINEL')",
        "~~g & (lambda: __import__('os').system('touch SENTINEL'))()",
        "!g.__class__.__init__.__globals__['os'].system('touch SENTINEL')",
        "!(g)[0] | __import__('os').system('touch SENTINEL')",
    ], ids=["call_under_bang", "at_reference", "lambda_after_tildes",
            "attribute_chain", "subscript_then_call"])
    def test_a_payload_behind_a_not_does_not_run(self, tmp_path, qualifier):
        """Injection: wrapping an operand in ``(... != 0)`` adds only a
        comparison with zero.  Whatever the operand holds still meets the
        whitelist, which refuses it: nothing runs, every row is drawn, and
        both modes say the qualifier was skipped."""
        sentinel = os.path.join(str(tmp_path), "SENTINEL")
        q = qualifier.replace("SENTINEL", sentinel)
        out = dr._stata_if_to_pandas(q)
        assert not dr._validate_if_expr(out, list(_frame().columns)), out
        _refused_in_both_modes(tmp_path, q,
                               "invalid syntax (<unknown>, line 1)")
        assert not os.path.exists(sentinel), "the qualifier ran code"

    @pytest.mark.parametrize("qualifier", [
        "!" * 20000 + "g",
        "~" * 20000 + "(g == 1)",
        " | ".join(["!g"] * 5000),
        " & ".join(["g"] * 5000),
        "!(" * 3000 + "g" + ")" * 3000,
        "10 < " * 3000 + "m",
    ], ids=["20000_bangs", "20000_tildes_before_a_comparison",
            "5000_term_or", "5000_term_and", "3000_nested_bang_groups",
            "3000_link_chain"])
    def test_a_qualifier_past_the_bound_is_refused_in_bounded_time(
            self, served_app, qualifier):
        """Exhaustion: the translation is one pass over the tokens, with no
        recursion, and its output grows by a constant per operator; a tree
        deeper than the whitelist's bound is refused aloud, not raised, in
        bounded time -- by the renderer's reader and by the served app's
        copy of it.  Stata refuses the four long ones itself, r(130)
        "expression too long", and the console binary crashed on the
        20,000 ~ (segmentation fault), so 20,000 ! was not tried; it
        applies 2,000 ! (6 rows), which dash refuses, as it refused them
        before, past the whitelist's bound (measured 24sep2026)."""
        out = dr._stata_if_to_pandas(qualifier)
        assert len(out) <= 12 * len(qualifier) + 64
        for reader in (dr._dash_qualified_frame,
                       served_app["_dash_qualified_frame"]):
            t0 = time.monotonic()
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                got = reader(_frame(), qualifier, "", "t")
            took = time.monotonic() - t0
            assert took < 20, took
            assert len(got) == len(_LG_ROWS)
            assert _skips([str(c.message) for c in caught]), qualifier

    @pytest.mark.parametrize("qualifier", [
        "!" * 250 + "v" * 1_000_000,
        " & ".join(["v" * 20_000] * 250),
        "(" + " | ".join(["!v" + "w" * 20_000] * 250) + ")",
    ], ids=["long_name_under_250_nots", "250_term_and_of_long_names",
            "250_term_or_of_long_nots"])
    def test_a_long_operand_under_many_operators_costs_linear_memory(
            self, qualifier):
        """Exhaustion: the translation writes the query once, from the
        root down, so a deep tree over a long operand costs the length of
        the text and not the length times the depth -- written node by
        node, each of 250 nots over a 1 MB name held its own copy, 250 MB,
        and the chains of 250 terms held every prefix of themselves.
        Measured with tracemalloc 24sep2026: the peak is 9.5 bytes per
        character of input, most of it _mask_string_literals' list of
        characters, for all three; it is held to 16, and the time to a few
        seconds.  The time is taken on a call of its own, outside
        tracemalloc, whose bookkeeping it would otherwise measure: under
        the Python Stata ships (3.13.9) the translation takes 1.3 s and
        tracemalloc turned that into 9 to 11 s, past the bound, while
        adding nothing to what the call itself costs (measured 24sep2026,
        WP-25)."""
        import tracemalloc
        t0 = time.monotonic()
        out = dr._stata_if_to_pandas(qualifier)
        took = time.monotonic() - t0
        tracemalloc.start()
        try:
            dr._stata_if_to_pandas(qualifier)
            _cur, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        assert len(out) <= 2 * len(qualifier) + 12 * 256
        assert peak <= 16 * len(qualifier), (peak, len(qualifier))
        assert took < 10, took

    @pytest.mark.parametrize("qualifier", [
        "v" * 30_000 + " == 1",
        "v" * 30_000 + " < .",
        "v" * 1_000_000 + " >= .",
        "9" * 1_000_000 + "x",
        "!" + " " * 1_000_000 + "g",
    ], ids=["30k_name", "30k_name_missing_idiom", "1m_name_missing_idiom",
            "1m_digits_then_a_letter", "1m_blanks_after_a_bang"])
    def test_a_long_name_is_read_in_linear_time(self, qualifier):
        """Exhaustion, found by the test above: the seven missing-idiom
        patterns (``x < .`` ...) matched a name from any of its characters
        and gave the rest back one at a time, so the translation was
        quadratic in the length of a name -- 0.05 s at 1,000 characters,
        0.8 s at 4,000, 3.2 s at 8,000 (measured 24sep2026 on 2df1900), so
        a name of 30,000 took about 45 s and one of a million most of a
        day, in both modes.  Anchored at a name's first character they are
        linear; so is the number pattern, whose quantifiers never share a
        digit."""
        t0 = time.monotonic()
        dr._stata_if_to_pandas(qualifier)
        took = time.monotonic() - t0
        assert took < 5, (len(qualifier), took)

    def test_redundant_parentheses_cost_nothing(self, tmp_path):
        """Exhaustion, the other way: 3,000 parentheses around ``!g`` are
        no tree at all, and Stata applies the qualifier, 6 rows (measured
        24sep2026).  Written back as they came they would be refused by
        Python's parser, which allows 200; the reader leaves them out."""
        q = "(" * 3000 + "!g" + ")" * 3000
        t0 = time.monotonic()
        page, _r, saved_msgs = _saved(tmp_path, _spec(q))
        doc, served_msgs = _served(tmp_path, _spec(q))
        assert time.monotonic() - t0 < 60
        assert _page_scatter(page)[1] == sorted(_ODD)
        assert _doc_scatter(doc.roots)[1] == sorted(_ODD)
        assert not _skips(saved_msgs + served_msgs)
