"""A served filter move keeps each layer's own rows, and clears the
selections whose rows it replaces -- as Stata selects and the saved page
draws.

Measured 24sep2026 at 2df1900 (T5), the served app's filter callback
(``_on_filter_change`` in ServerAppBuilder's app template) run by setting a
widget and calling its registered callbacks, the saved page's own scripts
run under node, and Stata's answers measured with the console binary:

* **A layer's own if()/in() was lost at the first move.**  The callback
  wrote every row the move kept for the graph into each layer's source.
  sysuse auto, an unlinked ``(scatter mpg weight in 40/60) (lfit mpg weight
  in 40/60)`` with the dropdown on Foreign: the scatter drew all 22 foreign
  cars where Stata's ``count if foreign == 1 in 40/60`` and the saved page
  give 8 (the redrawn lfit was already right).  scatter, connected's and
  rconnected's markers, rbar, rspike and dot, with an own ``in 3/8`` or
  ``if mpg > 18`` on test_mode_parity.py's ten observations, all drew the
  graph's rows.  (test_mode_parity.py ``TestALayersOwnQualifierAfterAMove``
  and the parity entries it names hold the cases on those ten rows.)
* **A derived column named other rows.**  A column the layer derives -- the
  marker-label text -- was taken from the pre-move snapshot at the row
  LABEL, read as a position: under a graph's ``if mpg > 18`` a range move
  left four markers and two labels, '4' and '3', where Stata writes 5, 4,
  4, 4, and Bokeh warned that the columns differ in length.
* **A by() Total panel took back the rows with a missing by() value.**
  With observation 10's foreign missing and a price range, the served Total
  panel drew 6 observations and its lfit was fitted on them (29.4709 at
  weight 1800) where Stata's by(foreign, total) serset holds 5 and its
  regress gives 29.5622; before the move the panel held 9 rows, none of
  them observation 10.
* **A selection survived the move and named other rows.**  With update(brush)
  and observations 1-3 brushed, a move to Foreign left selected.indices at
  [0, 1, 2] -- now observations 2, 4 and 6, lit up although never brushed --
  and the card at 21.3333.  The saved page's script clears every source it
  writes, which fires its brush script with nothing selected, and that
  counts the brushed source's rows: the card reads 23.4, Stata's ``summarize
  mpg if foreign == 1``.  Clearing alone would not have matched it: the
  served brush callback counted the WHOLE frame when nothing was selected
  (21.5), so a brush cleared on a graph ``if foreign == 1`` read 21.5 where
  the saved page reads 23.4 even without a move.  Since WP-29 P0.11 the
  graph's source holds only the rows its layers draw, so with a layer's
  own ``in 3/8`` the card after the move reads 25.66667, Stata's
  ``summarize mpg if foreign == 1 in 3/8``.

The saved page is the specification wherever it is right; where it is not,
the test says so and holds the served app to Stata alone.
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.models import ColumnDataSource, Div, GlyphRenderer

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_filter_exclude import _node  # noqa: E402
from test_help_claims_4 import _encode  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402
from conftest import drawn_renderers  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "kpi_pctile_truth.json")

_DROPDOWN = "foreign, type(dropdown)"
_RANGE = "price, type(range)"
_PRICE_RANGE = (4500.0, 11385.0)

# G1 (WP-28): the marker-label column is named under the __dash prefix.
_MLABEL_REP = dr._DASH_MLABEL_PREFIX + "rep"
_MLABEL_X = dr._DASH_MLABEL_PREFIX + "x"


# ===========================================================================
# Helpers
# ===========================================================================

def _auto():
    """sysuse auto's price, mpg, weight, foreign and rep78, in its order, as
    Stata holds them (the committed fixture test_help_claims_4 reads)."""
    with open(_FIXTURE, encoding="utf-8") as fh:
        cols = json.load(fh)["auto"]
    return pd.DataFrame({k: [np.nan if v is None else float(v) for v in vals]
                         for k, vals in cols.items()})


def _figures(doc):
    """The served document's figures, in layout order."""
    out = []

    def visit(m):
        if isinstance(m, (list, tuple)):
            for x in m:
                visit(x)
            return
        if m is None:
            return
        if type(m).__name__ == "figure":
            out.append(m)
            return
        for attr in ("children", "tabs", "child"):
            k = getattr(m, attr, None)
            if k is not None:
                visit(k)

    for root in doc.roots:
        visit(root)
    return out


def _cards(texts):
    """``{name: shown value}`` of every KPI card among *texts*."""
    out = {}
    for t in texts:
        c = tp._kpi_card(t)
        if c:
            out[c[0]] = c[1]
    return out


def _served_cards(doc):
    return _cards(d.text for d in doc.select({"type": Div}))


def _move(doc, kind, want):
    """Fire the one widget of *kind* in *doc*: a Select to the option
    labelled *want*, a slider to the value *want*."""
    (w,) = [x for x in tp._widgets_of(doc) if type(x).__name__ == kind]
    if kind == "Select":
        (raw,) = [v for v, lab in w.options if lab == want]
        tp._fire(w, raw)
    else:
        tp._fire(w, want)


def _drawn_source(fig):
    """The data source a figure's first glyph draws from."""
    return [r.data_source for r in drawn_renderers(fig)
            if isinstance(r, GlyphRenderer)][0]


# BokehJS runs a CustomJS body as a strict-mode function whose parameters
# are the args' names, then cb_obj and cb_data.  Every runner below starts
# from test_help_claims_4's: the args' models replaced by stand-ins
# (_encode), one stand-in per model, so identity is what the page has.
_RUNNER_HEAD = r"""
"use strict";
const REG = {};
for (const [id, lit] of Object.entries(RAW.models))
    REG[id] = Object.assign({}, lit);
const resolve = (x) => {
  if (Array.isArray(x)) return x.map(resolve);
  if (x && typeof x === "object") {
    if ("__ref__" in x) return REG[x.__ref__];
    const o = {};
    for (const [k, v] of Object.entries(x)) o[k] = resolve(v);
    return o;
  }
  return x;
};
const run = (cb, cb_obj) => {
  const args = resolve(cb.args);
  const names = Object.keys(args);
  new Function(...names, "cb_obj", "cb_data", '"use strict";\n' + cb.code)(
    ...names.map((n) => args[n]), cb_obj, {});
};
"""

# The page's filter script once; then the rows one view draws, by row id.
_VIEW_RUNNER = _RUNNER_HEAD + r"""
for (const o of Object.values(REG)) {
  if (o.__type__ === "ColumnDataSource") {
    o.selected = {indices: []};
    o.change = {emit() {}};
  } else if (o.__type__ === "BooleanFilter") {
    o.change = {emit() {}};
  }
}
run({args: RAW.args, code: RAW.code}, null);
const src = REG[RAW.src], flt = REG[RAW.flt];
const ids = src.data[RAW.row_id];
const drawn = [];
flt.booleans.forEach((b, i) => { if (b) drawn.push(ids[i] + 1); });
process.stdout.write(JSON.stringify({rows: ids.length, drawn}));
"""


def _run_node(payload, runner):
    """Run *runner* under node with ``RAW`` = *payload*; its JSON output."""
    with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False,
                                     encoding="utf-8") as fh:
        fh.write("const RAW = " + json.dumps(payload) + ";\n" + runner)
        path = fh.name
    try:
        res = subprocess.run([_node(), path], capture_output=True, text=True,
                             timeout=300)
    finally:
        os.unlink(path)
    assert res.returncode == 0, (
        "the page's own scripts failed under node:\n" + res.stderr[:1500])
    return json.loads(res.stdout)


# ===========================================================================
# 1. _dash_refresh_unlinked, the helper the move now writes each source with
# ===========================================================================

def _layer_source():
    """test_mode_parity's ten observations, and the source the served app
    builds for a scatter labelled by rep with its own ``in 3/8``: the rows
    of its own (labels 2-7) and the label text it derives."""
    df = tp._DF.copy()
    own = df.iloc[2:8]
    src = ColumnDataSource(own[["weight", "mpg"]])
    src.data[_MLABEL_REP] = ["r%d" % v for v in own["rep"]]
    return df, src, {c: list(v) for c, v in src.data.items()}


class TestTheUnlinkedRefresh:

    def test_it_writes_the_rows_of_its_own_that_the_move_keeps(self):
        df, src, snap = _layer_source()
        frame = df[df["foreign"] == 1]            # labels 1, 3, 5, 7, 9
        out = dr._dash_refresh_unlinked(src, frame, snap)
        data = dict(src.data)
        assert data == out
        assert list(data["index"]) == [3, 5, 7]
        assert list(data["weight"]) == [1800.0, 3100.0, 2010.0]
        assert list(data["mpg"]) == [30.0, 19.0, 28.0]
        # The derived column keeps each row's own value: rep 5, 3, 4.
        assert list(data[_MLABEL_REP]) == ["r5", "r3", "r4"]

    def test_a_row_the_source_never_held_is_not_added(self):
        """A row dropped at the first draw -- its x missing -- stays out
        after a move, as on the saved page, and every column keeps one
        value per row."""
        df, _, _ = _layer_source()
        df.loc[4, "weight"] = np.nan
        clean = df.iloc[2:8].dropna(subset=["weight"])
        src = ColumnDataSource(clean[["weight", "mpg"]])
        snap = {c: list(v) for c, v in src.data.items()}
        dr._dash_refresh_unlinked(src, df, snap)
        assert list(src.data["index"]) == [2, 3, 5, 6, 7]
        assert {len(v) for v in src.data.values()} == {5}

    def test_a_source_without_row_labels_takes_the_frames_rows(self):
        """A graph's placeholder -- the dataset's columns, no ``index`` --
        is written with the frame's rows, as it always was."""
        df = tp._DF.copy()
        src = ColumnDataSource({"weight": df["weight"].tolist(),
                                "mpg": df["mpg"].tolist()})
        snap = {c: list(v) for c, v in src.data.items()}
        frame = df[df["foreign"] == 0]
        dr._dash_refresh_unlinked(src, frame, snap)
        assert list(src.data["weight"]) == frame["weight"].tolist()
        assert "index" not in src.data

    def test_a_move_that_keeps_nothing_empties_every_column(self):
        df, src, snap = _layer_source()
        dr._dash_refresh_unlinked(src, df.iloc[0:0], snap)
        assert {k: len(v) for k, v in src.data.items()} == {
            k: 0 for k in snap}

    def test_the_rule_it_replaced_differs_on_this_source(self):
        """Guards the first test: the rule this replaced -- every row the
        frame holds, and a derived column read at the row label as a
        position -- gives five rows and a derived column three long on the
        same source, so the test can tell the two apart."""
        df, _, snap = _layer_source()
        frame = df[df["foreign"] == 1]
        n = len(snap[_MLABEL_REP])
        old = {"index": frame.index.tolist(),
               "weight": frame["weight"].tolist(),
               _MLABEL_REP: [snap[_MLABEL_REP][i]
                                 for i in frame.index.tolist() if 0 <= i < n]}
        assert {k: len(v) for k, v in old.items()} == {
            "index": 5, "weight": 5, _MLABEL_REP: 3}


# ===========================================================================
# 2. The reported case, on sysuse auto
# ===========================================================================

class TestTheReportedCase:
    """sysuse auto, unlinked ``(scatter mpg weight in 40/60) (lfit mpg weight
    in 40/60)``, the dropdown moved to Foreign.  Stata, 24sep2026: ``count
    if foreign == 1 in 40/60`` is 8 -- observations 53 (Audi 5000) to 60
    (Fiat Strada) -- of 22 foreign cars and 21 observations in 40/60;
    ``regress mpg weight if foreign == 1 in 40/60`` gives 27.1737 at weight
    2020 and 19.352 at 2830, the rows' least and greatest weight."""

    _SPEC = tp._spec([plot_for("scatter", in_expr="40/60"),
                      plot_for("lfit", in_expr="40/60")],
                     {"filter": _DROPDOWN})

    @pytest.fixture(autouse=True)
    def _on_auto(self, monkeypatch):
        monkeypatch.setattr(tp, "_DF", _auto())

    @staticmethod
    def _observations(prof):
        """The observations (1-based) a figure's scatter draws, and its
        fitted line's ends."""
        sc, fit = prof["glyphs"][0], prof["glyphs"][1]
        weights = sc["coords"]["x"][1]
        mpgs = sc["coords"]["y"][1]
        auto = _auto()
        obs = sorted(int(auto.index[(auto["weight"] == w)
                                    & (auto["mpg"] == m)][0]) + 1
                     for w, m in zip(weights, mpgs))
        ends = ((fit["coords"]["x"][1][0], fit["coords"]["x"][1][-1]),
                (fit["coords"]["y"][1][0], fit["coords"]["y"][1][-1]))
        return obs, ends

    def test_the_served_scatter_keeps_its_in_after_the_move(self):
        doc, _ = tp._served(self._SPEC)
        (fig,) = _figures(doc)
        before, _ = self._observations(tp._figure_profile(fig))
        assert before == list(range(40, 61))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _move(doc, "Select", "Foreign")
        obs, ends = self._observations(tp._figure_profile(fig))
        assert obs == list(range(53, 61)), obs
        assert ends == ((2020.0, 2830.0), (27.1737, 19.352)), ends

    def test_the_saved_page_draws_the_same(self):
        """The saved renderer given the move as an ``if``, the oracle
        TestAFilterMoveAgrees uses."""
        std, _ = tp._saved_with_qualifier(self._SPEC, "foreign == 1")
        (prof,) = std
        obs, ends = self._observations(prof)
        assert obs == list(range(53, 61)), obs
        assert ends == ((2020.0, 2830.0), (27.1737, 19.352)), ends

    def test_the_saved_pages_own_script_draws_the_same(self):
        """The saved page itself: its filter script, run under node, keeps
        the scatter's view on observations 53-60 of the 8 rows its layers
        draw (21 drawn before the move).  Row ids are the page's ranks
        (WP-29 P0.11), mapped back to observations through
        ``r._page_labels``."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r, _ = tp._standalone(self._SPEC)
        (fig,) = r.figures.values()
        sc = [g for g in drawn_renderers(fig) if isinstance(g, GlyphRenderer)][0]
        flt = sc.view.filter
        assert sum(bool(b) for b in flt.booleans) == 21
        (w,), (cb,) = r.filter_widgets, r.filter_callbacks
        (w.value,) = [v for v, lab in w.options if lab == "Foreign"]
        models = {}
        payload = {"models": models, "args": _encode(dict(cb.args), models),
                   "code": cb.code, "src": _encode(sc.data_source,
                                                   models)["__ref__"],
                   "flt": _encode(flt, models)["__ref__"],
                   "row_id": dr._ROW_ID_COLUMN}
        out = _run_node(payload, _VIEW_RUNNER)
        # Flipped (WP-29 P0.11): the source held all 22 foreign rows; it
        # holds the 8 its layers draw (Stata: count if foreign==1 in 40/60),
        # numbered by the page's ranks.
        assert out["rows"] == 8, out
        assert [r._page_labels[i - 1] + 1 for i in out["drawn"]] == list(
            range(53, 61)), out


# ===========================================================================
# 3. A by() Total panel after a move
# ===========================================================================

def _missing_foreign():
    df = tp._DF.copy()
    df.loc[9, "foreign"] = np.nan       # observation 10, price 11385
    return df


class TestTheTotalPanelAfterAMove:
    """by(foreign, total), observation 10's foreign missing, a price range
    of 4500-11385.  Stata, 24sep2026: ``twoway scatter mpg weight if price
    >= 4500 & price <= 11385, by(foreign, total)`` leaves sersets of 2, 3
    and 5 observations -- the Total panel never holds the missing value
    (``count if ... & !missing(foreign)`` is 5, without it 6) -- and
    ``regress mpg weight`` on those 5 gives 29.5622 at weight 1800 and
    13.1101 at 4080.  The served move handed the Total panel every row the
    range kept, observation 10 included."""

    @pytest.fixture(autouse=True)
    def _with_a_missing_group(self, monkeypatch):
        monkeypatch.setattr(tp, "_DF", _missing_foreign())

    @staticmethod
    def _spec(ptype):
        return tp._spec([plot_for(ptype)], {"filter": _RANGE},
                        {"by": "foreign, total"})

    @staticmethod
    def _served(spec):
        doc, _ = tp._served(spec)
        figs = _figures(doc)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _move(doc, "RangeSlider", _PRICE_RANGE)
        return [tp._figure_profile(f) for f in figs]

    @staticmethod
    def _saved(spec):
        std, _ = tp._saved_with_qualifier(
            spec, "price >= 4500 & price <= 11385")
        return std

    def test_each_panels_scatter_holds_statas_rows(self):
        spec = self._spec("scatter")
        for mode, profs in (("served", self._served(spec)),
                            ("saved", self._saved(spec))):
            rows = [p["glyphs"][0]["rows"] for p in profs]
            assert rows == [2, 3, 5], (mode, rows)

    def test_the_total_panels_fit_is_statas(self):
        spec = self._spec("lfit")
        for mode, profs in (("served", self._served(spec)),
                            ("saved", self._saved(spec))):
            c = profs[2]["glyphs"][0]["coords"]
            ends = ((c["x"][1][0], c["x"][1][-1]),
                    (c["y"][1][0], c["y"][1][-1]))
            assert ends == ((1800.0, 4080.0), (29.5622, 13.1101)), (mode,
                                                                    ends)


# ===========================================================================
# 4. A selection across a move
# ===========================================================================

# The saved page's scripts, run as BokehJS runs them, with one addition:
# setting a source's ``selected.indices`` to a different value runs the
# js_on_change("indices") callbacks the page attached to that source --
# BokehJS emits the change only when the value differs -- which is how the
# page's filter script, by clearing a selection, runs its brush script.
_SEL_RUNNER = _RUNNER_HEAD + r"""
const same = (a, b) => a.length === b.length && a.every((v, i) => v === b[i]);
for (const [id, o] of Object.entries(REG)) {
  if (o.__type__ === "ColumnDataSource") {
    let ix = [];
    const sel = {};
    Object.defineProperty(sel, "indices", {
      get() { return ix; },
      set(v) {
        const old = ix; ix = v;
        if (same(old, v)) return;
        for (const cb of (RAW.brush[id] || [])) run(cb, sel);
      }});
    o.selected = sel;
    o.change = {emit() {}};
  } else if (o.__type__ === "BooleanFilter") {
    o.change = {emit() {}};
  }
}
const cards = () => Object.values(REG).filter((o) => o.__type__ === "Div")
  .map((o) => o.text);
const out = {};
REG[RAW.brushed].selected.indices = RAW.indices;
out.brushed = cards();
for (const step of RAW.then) {
  if (step === "move") run(RAW.filter, null);
  else REG[RAW.brushed].selected.indices = step;
}
out.after = cards();
out.selected = REG[RAW.brushed].selected.indices;
process.stdout.write(JSON.stringify(out));
"""


def _saved_selection(spec, figure, indices, then, move=None):
    """``(cards once brushed, cards after, selection after)`` on the saved
    page: *indices* of *figure*'s drawn source brushed, then each step of
    *then* -- ``"move"`` runs the filter script with its widget at *move*,
    a list sets the selection."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r, _ = tp._standalone(spec)
    brushed = _drawn_source(list(r.figures.values())[figure])
    models = {}
    payload = {"models": models, "brush": {}, "indices": list(indices),
               "then": then, "filter": None}
    if move is not None:
        (w,), (fcb,) = r.filter_widgets, r.filter_callbacks
        kind, want = move
        w.value = ([v for v, lab in w.options if lab == want][0]
                   if kind == "Select" else want)
        payload["filter"] = {"args": _encode(dict(fcb.args), models),
                             "code": fcb.code}
    payload["brushed"] = _encode(brushed, models)["__ref__"]
    for src in list(r.sources.values()) + [brushed]:
        for lst in (src.selected.js_property_callbacks or {}).values():
            for cb in (lst if isinstance(lst, list) else [lst]):
                sid = _encode(src, models)["__ref__"]
                entry = {"args": _encode(dict(cb.args), models),
                         "code": cb.code}
                if entry not in payload["brush"].setdefault(sid, []):
                    payload["brush"][sid].append(entry)
    assert payload["brush"].get(payload["brushed"]), (
        "the brushed source carries no brush script")
    out = _run_node(payload, _SEL_RUNNER)
    return _cards(out["brushed"]), _cards(out["after"]), out["selected"]


def _served_selection(spec, figure, indices, then, move=None):
    """The same, in one served session: the brush sets the source's
    selection (its callback runs, as a browser's would make it), a move
    fires the widget's own callbacks."""
    doc, _ = tp._served(spec)
    src = _drawn_source(_figures(doc)[figure])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        src.selected.indices = list(indices)
        brushed = _served_cards(doc)
        for step in then:
            if step == "move":
                _move(doc, *move)
            else:
                src.selected.indices = list(step)
    return brushed, _served_cards(doc), list(src.selected.indices)


def _sc(**kw):
    return plot_for("scatter", **kw)


#: (name, spec, brushed figure, brushed rows, move, Stata's card after it).
#: Stata, 24sep2026 on _DF's ten observations: ``summarize mpg if foreign
#: == 1`` 23.4; ``... & mpg > 18`` 25; ``... & mpg > 20`` 27; ``summarize
#: mpg if foreign == 0 & price >= 4500 & price <= 11385`` 17.5.  Brushed
#: first: rows 1-3 of the source (``summarize mpg in 1/3``, 21.3333).
_SELECTIONS = [
    ("update(brush)", tp._spec([_sc()], {"filter": _DROPDOWN},
                               kpis=[tp._kpi(update="brush")]),
     0, [0, 1, 2], ("Select", "Foreign"), "23.4"),
    ("update(both)", tp._spec([_sc()], {"filter": _DROPDOWN},
                              kpis=[tp._kpi(update="both")]),
     0, [0, 1, 2], ("Select", "Foreign"), "23.4"),
    # The brushed graph's rows: its own `if mpg > 18' among Foreign.
    ("update(brush), the graph's own if",
     tp._spec([_sc()], {"filter": _DROPDOWN}, if_expr="mpg > 18",
              kpis=[tp._kpi(update="brush")]),
     0, [0, 1, 2], ("Select", "Foreign"), "25"),
    # update(both): the filter's number, over every row the move keeps.
    ("update(both), the graph's own if",
     tp._spec([_sc()], {"filter": _DROPDOWN}, if_expr="mpg > 18",
              kpis=[tp._kpi(update="both")]),
     0, [0, 1, 2], ("Select", "Foreign"), "23.4"),
    # A layer's own in: the saved page brushes the GRAPH's source, which
    # holds the rows its layers draw, 3-8 (WP-29 P0.11).  Flipped: 23.4
    # counted rows the layer never draws; Stata: summarize mpg if
    # foreign == 1 in 3/8, 25.66667.
    ("update(brush), the layer's own in",
     tp._spec([_sc(in_expr="3/8")], {"filter": _DROPDOWN},
              kpis=[tp._kpi(update="brush")]),
     0, [0, 1, 2], ("Select", "Foreign"), "25.66667"),
    ("update(brush), the card's own if",
     tp._spec([_sc()], {"filter": _DROPDOWN},
              kpis=[tp._kpi(update="brush", if_expr="mpg > 20")]),
     0, [0, 1, 2], ("Select", "Foreign"), "27"),
    ("update(brush), a linked pair",
     tp._spec(None, {"filter": _DROPDOWN, "link": "g1 g2"},
              graphs=[("g1", [_sc()]), ("g2", [_sc()])],
              kpis=[tp._kpi(update="brush")]),
     0, [0, 1, 2], ("Select", "Foreign"), "23.4"),
    ("update(brush), a by() panel, range",
     tp._spec([_sc()], {"filter": _RANGE}, {"by": "foreign"},
              kpis=[tp._kpi(update="brush")]),
     0, [0, 1], ("RangeSlider", _PRICE_RANGE), "17.5"),
]


@pytest.mark.parametrize("name,spec,figure,rows,move,stata", _SELECTIONS,
                         ids=[s[0] for s in _SELECTIONS])
class TestASelectionAfterAMove:
    """Brush, then move a filter: the served selection is cleared and the
    card reads the saved page's number, which is Stata's."""

    def test_the_card_is_the_saved_pages_and_statas(self, name, spec, figure,
                                                    rows, move, stata):
        _, srv_after, _ = _served_selection(spec, figure, rows, ["move"],
                                            move)
        _, std_after, _ = _saved_selection(spec, figure, rows, ["move"],
                                           move)
        assert std_after == {"k1": stata}, (name, std_after)
        assert srv_after == std_after, (
            f"{name}: after the move the served card reads {srv_after}, "
            f"the saved page's {std_after}")

    def test_the_selection_is_cleared(self, name, spec, figure, rows, move,
                                      stata):
        """A selection names positions, and the move put other rows there:
        kept, it lights up observations nobody brushed."""
        _, _, srv_sel = _served_selection(spec, figure, rows, ["move"], move)
        _, _, std_sel = _saved_selection(spec, figure, rows, ["move"], move)
        assert std_sel == [] and srv_sel == [], (name, std_sel, srv_sel)

    def test_the_brush_itself_changed_the_card(self, name, spec, figure, rows,
                                               move, stata):
        """Guards the guard: the brush moved the card off the move's
        number, so the number after the move is the move's doing."""
        brushed, _, _ = _served_selection(spec, figure, rows, [], move)
        assert brushed.get("k1") not in (None, stata), (name, brushed)


class TestAClearedBrushCountsTheGraphsRows:
    """No move: brush, then clear.  The saved page's brush script counts
    its brushed source whole when nothing is selected -- the graph's rows --
    and the served one counted every row of the data.  A graph ``if
    foreign == 1``: Stata's ``summarize mpg if foreign == 1`` is 23.4, and
    of all ten 21.5."""

    _SPEC = tp._spec([_sc()], kpis=[tp._kpi(update="brush")],
                     if_expr="foreign == 1")

    def test_both_modes_read_the_graphs_rows(self):
        _, srv, _ = _served_selection(self._SPEC, 0, [0, 1], [[]])
        _, std, _ = _saved_selection(self._SPEC, 0, [0, 1], [[]])
        assert std == {"k1": "23.4"}, std
        assert srv == std, (srv, std)

    def test_a_graph_of_every_row_still_reads_every_row(self):
        spec = tp._spec([_sc()], kpis=[tp._kpi(update="brush")])
        _, srv, _ = _served_selection(spec, 0, [0, 1], [[]])
        assert srv == {"k1": "21.5"}, srv


# ===========================================================================
# 5. Adversarial (CLAUDE.md rule 18): served_widget_model_changes
# ===========================================================================

class TestAdversarialFilterMoves:
    """What a client can send -- any value its widget admits, any selection
    -- against a layer with its own qualifier."""

    _SPEC = tp._spec([plot_for("scatter", in_expr="3/8"),
                      plot_for("scatter", if_expr="mpg > 18")],
                     {"filter": _DROPDOWN})

    @staticmethod
    def _rows(doc, labels=None):
        """Each layer's observations: its served ``index`` labels, which
        are page ranks (WP-29 P0.11), mapped back through the saved page's
        ``_page_labels``."""
        (fig,) = _figures(doc)
        return [sorted(int(labels[int(i)]) if labels is not None else int(i)
                       for i in r.data_source.data["index"])
                for r in drawn_renderers(fig) if isinstance(r, GlyphRenderer)]

    def _after(self, *values):
        """The layers' rows in a fresh session after the Select is set to
        each of *values* in turn.  Fresh, and few: setting a value runs the
        throttled callback and _fire runs it again, and past the bucket's
        ten a call waits on a timer a bare Document never runs.  (Served
        labels are page ranks, mapped back through the saved page's
        ``_page_labels``; WP-29 P0.11.)"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            labels = tp._standalone(self._SPEC)[0]._page_labels
        doc, _ = tp._served(self._SPEC)
        (w,) = [x for x in tp._widgets_of(doc) if type(x).__name__ == "Select"]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for v in values:
                tp._fire(w, v)
        # Flipped (WP-29 P0.11): labels were observation positions; they
        # are ranks of the planned rows {0, 2, 3, 4, 5, 6, 7, 9}.
        return self._rows(doc, labels)

    def test_no_widget_value_widens_a_layers_own_rows(self):
        """Bypass: every value the Select admits -- its "All" sentinel, a
        value outside its options, the empty string, NUL, a very long one,
        another spelling of a code -- leaves each layer inside its own rows
        (labels 2-7 for in 3/8; mpg > 18 for the if)."""
        own_in = set(range(2, 8))
        own_if = set(tp._DF.index[tp._DF["mpg"] > 18])
        for v in ("__all__", "not-an-option", "", "\x00", "9" * 100000,
                  "1.0"):
            a, b = self._after(v)
            assert set(a) <= own_in and set(b) <= own_if, (v, a, b)
        # Back at "All" after Foreign, each layer draws its own rows whole.
        assert self._after("1", "__all__") == [sorted(own_in),
                                               sorted(own_if)]

    def test_a_selection_cannot_outlive_the_rows_it_named(self):
        """Bypass: indices past the end, negative and huge, brushed before a
        move, are gone after it; none is carried onto the new rows."""
        spec = tp._spec([plot_for("scatter", in_expr="3/8")],
                        {"filter": _DROPDOWN},
                        kpis=[tp._kpi(update="brush")])
        doc, _ = tp._served(spec)
        (fig,) = _figures(doc)
        src = _drawn_source(fig)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            src.selected.indices = [-1, 0, 5, 10 ** 12, 2 ** 31 - 1]
            _move(doc, "Select", "Foreign")
        assert list(src.selected.indices) == []
        # Stata: summarize mpg if foreign == 1 in 3/8 -- the rows the graph
        # draws, as the saved page's cleared brush counts them.  Flipped
        # (WP-29 P0.11): 23.4 counted foreign rows outside the layer's in.
        assert _served_cards(doc) == {"k1": "25.66667"}

    def test_a_value_is_data_not_a_qualifier(self, tmp_path):
        """Injection: a Select value written as code, as a qualifier, or as
        markup is compared as a value -- it selects nothing, runs nothing,
        and the layers' own qualifiers are not rebuilt from it."""
        mark = tmp_path / "evaluated"
        for v in ("__import__('os').system('touch %s')" % mark,
                  "1 | 1", "foreign == 1 | foreign == 0",
                  "<img src=x onerror=alert(1)>", "index"):
            assert self._after(v) == [[], []], v
        assert not mark.exists()

    def test_a_move_over_many_rows_is_linear(self):
        """Exhaustion: the refresh matches rows by a hash, not by a search
        per row -- 300,000 rows kept from a 600,000-row snapshot in well
        under the time a quadratic match would need (hours)."""
        n = 600_000
        ids = np.arange(n)
        src = ColumnDataSource({"index": ids, "x": ids.astype(float),
                                _MLABEL_X: ["%d" % i for i in ids]})
        snap = {c: list(v) for c, v in src.data.items()}
        frame = pd.DataFrame({"x": ids[::2].astype(float)}, index=ids[::2])
        t0 = time.monotonic()
        dr._dash_refresh_unlinked(src, frame, snap)
        took = time.monotonic() - t0
        assert len(src.data["index"]) == n // 2
        assert src.data[_MLABEL_X][-1] == "%d" % (n - 2)
        assert took < 20, took


# ---------------------------------------------------------------------------
# WP-29 P0.18: a served move copies the redrawn bar width
# ---------------------------------------------------------------------------

def _vbar_widths(figs):
    return [g["coords"].get("width") for f in figs for g in f["glyphs"]
            if g["type"] == "VBar"]


def _served_source(spec):
    """The generated server app's source text for *spec*."""
    tag, sp, dp = tp._write(spec)
    ap = os.path.join(tempfile.mkdtemp(), f"app_{tag}.py")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(ap)
    with open(ap, encoding="utf-8") as fh:
        return fh.read()


def _sources_of(mode, spec):
    """Every ColumnDataSource a mode's document holds for *spec*."""
    if mode == "saved":
        r, _ = tp._standalone(spec)
    else:
        doc, _ = tp._served(spec)
        figs = [m for m in tp._walk_models(doc)
                if type(m).__name__ == "figure"]
        r = None
    figs = list(r.figures.values()) if r is not None else figs
    return [g.data_source for f in figs
            for g in getattr(f, "renderers", [])
            if getattr(g, "data_source", None) is not None]


def _bar_widths_and_notes(mode, spec):
    if mode == "saved":
        r, caught = tp._standalone(spec)
        figs = list(r.figures.values())
    else:
        doc, caught = tp._served(spec)
        figs = [m for m in tp._walk_models(doc)
                if type(m).__name__ == "figure"]
    ws = [g.glyph.width for f in figs
          for g in getattr(f, "renderers", [])
          if type(getattr(g, "glyph", None)).__name__ == "VBar"]
    return ws, caught


class TestTheRedrawGeometry:
    """No width is taken from the kept rows any more (WP-30 P1.17a), so a
    served move has no geometry to copy: the redraw's widths equal the
    live ones, and ``_dash_copy_redraw_geometry`` is gone."""

    def test_a_bar_takes_the_redraws_width(self):
        """Flipped (WP-30 P1.17a): the live width 168 was wrong because
        twoway draws a bar one x unit wide and caps as long as a marker of its msize (P1.17a)."""
        spec = tp._spec([plot_for("bar")], {"filter": _DROPDOWN})
        figs, _ = tp._served_after_move(spec, ("Select", "Foreign"))
        widths = _vbar_widths(figs)
        assert widths and all(w == ("value", 1.0) for w in widths), widths
        assert not hasattr(dr, "_dash_copy_redraw_geometry")
        assert "_dash_copy_redraw_geometry" not in _served_source(spec)

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_an_untagged_source_is_left_alone(self, mode):
        """Flipped (WP-30 P1.17a): no source is tagged at all, because
        twoway draws a bar one x unit wide and caps as long as a marker of its msize (P1.17a)."""
        spec = tp._spec([plot_for("bar"), plot_for("rbar"),
                         plot_for("rcap"), plot_for("rcapsym")],
                        {"filter": _DROPDOWN})
        srcs = _sources_of(mode, spec)
        assert srcs
        for src in srcs:
            assert not hasattr(src, "_dash_spacing_glyphs")
            assert not hasattr(src, "_dash_spacing")

    @pytest.mark.parametrize("mode", ["saved", "served"])
    @pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1.0,
                                     "text", None],
                             ids=["nan", "inf", "-1", "text", "None"])
    def test_a_non_finite_or_non_positive_width_is_ignored(self, bad, mode):
        """A spec barwidth that is not a finite positive number draws one
        x unit with one note, and nothing raises.

        Flipped (WP-30 P1.17a): the copy guard it pinned is gone because
        twoway draws a bar one x unit wide and caps as long as a marker of its msize (P1.17a).
        """
        spec = tp._spec([plot_for("bar", {"barwidth": str(bad)})],
                        {"filter": _DROPDOWN})
        widths, caught = _bar_widths_and_notes(mode, spec)
        assert widths == [1.0], widths
        assert sum("barwidth" in w for w in caught) == 1, caught

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_a_zero_width_is_drawn(self, mode):
        """barwidth(0) draws bars of no width, with no note, as twoway draws
        them.

        Flipped (WP-35 basic:PT-13): 0 was ignored as non-positive; twoway
        draws it (value_codes_truth.json barwidth_0).
        """
        spec = tp._spec([plot_for("bar", {"barwidth": "0"})],
                        {"filter": _DROPDOWN})
        widths, caught = _bar_widths_and_notes(mode, spec)
        assert widths == [0.0], widths
        assert not any("barwidth" in w for w in caught), caught

    def test_extra_glyphs_are_zipped_to_the_shorter(self):
        """A graph with a bar and an rbar keeps both widths after a served
        move.

        Flipped (WP-30 P1.17a): the zip of spacing glyphs is gone because
        twoway draws a bar one x unit wide and caps as long as a marker of its msize (P1.17a).
        """
        spec = tp._spec([plot_for("bar"), plot_for("rbar")],
                        {"filter": _DROPDOWN})
        figs, _ = tp._served_after_move(spec, ("Select", "Foreign"))
        widths = _vbar_widths(figs)
        assert widths == [("value", 1.0), ("value", 1.0)], widths


class TestTheServedBarAfterAMove:

    @pytest.mark.parametrize("t", ["bar", "rbar"])
    def test_the_served_width_is_the_kept_rows_spacing(self, t):
        """Flipped (WP-30 P1.17a): 168 was wrong because twoway draws a bar one x unit wide and caps as long as a marker of its msize (P1.17a)."""
        spec = tp._spec([plot_for(t)], {"filter": "foreign, type(dropdown)"})
        figs, _ = tp._served_after_move(spec, ("Select", "Foreign"))
        widths = [g["coords"].get("width") for f in figs for g in f["glyphs"]
                  if g["type"] == "VBar"]
        assert widths and all(w == ("value", 1.0) for w in widths), widths
