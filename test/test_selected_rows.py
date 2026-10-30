"""Only the rows the graphs draw are exported (WP-40 plat:PT-7).

GAPS4 plat:PT-7 (audit package 5, DG-15): dash exported every observation
of every variable a dashboard uses, whatever its qualifiers selected, so
``dash scatter y x in 1/100`` on 3,000,000 observations wrote, held and
read all 3,000,000 rows where twoway draws 100.  Ruling M10 / Q45 with
P4-3 and A-12: when nothing on the page needs every row -- the one-line
form, or a saved ``dash build`` with no filter(), link(), brush(), csv or
KPI card -- dash marks the rows some graph draws (dash_parse.mata
``_dash_sel_mark``, the page plan's own rule plus a literal by() graph's
panel rows; a lowess layer with ``adjust`` marks every row) after every
working column is made, copies them out of the user's frame with
``frame put`` and exports only those.  Each graph carries its frame's _N
as ``"n_obs"``, which lpoly's grid reads in place of the rows exported.

The guards: ``_selected`` is a Python twin of the Mata rule (D-40-01.b);
TestTheSelectionCoversThePlan checks it holds every row ``_dash_embed_plan``
keeps for each qualified parity-corpus entry, and TestTheDrawingIsUnchanged
renders each such entry from the whole frame and from the selected rows
and compares every figure's profile.  Stata's side is
test/test_wp40_truth.cscript S01 (Q4001-1..10).
"""
import copy
import json
import os
import re
import sys
import warnings

import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_join_order as jo  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from conftest import make_data_json, render_models  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_ADO = os.path.join(_HERE, "..", "dash.ado")
_HELP = os.path.join(_HERE, "..", "dash.sthlp")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _program(name):
    """The text of dash.ado's program *name*, its define line to its end."""
    src = _read(_ADO)
    m = re.search(r"^program define %s\b.*?^end\s*$" % re.escape(name), src,
                  re.S | re.M)
    assert m, name
    return m.group(0)


def _lines(body):
    return body.split("\n")


# ===========================================================================
# The rule's Python twin (D-40-01.b) and the corpus it is checked over
# ===========================================================================

_LITERAL = ("scatteri", "pci", "pcarrowi", "function")


def _col(name, masks, idx):
    if not name:
        return pd.Series(True, index=idx)
    return masks[name].reindex(idx, fill_value=False).astype(bool)


def _selected(spec, frame, masks):
    """The rows _dash_sel_mark marks for *spec*: per graph, each non-literal
    plot's ``G & P`` (and ``Gt & Pt`` when the graph or a plot carries a
    Total twin); a graph of literal plots only, its ``G`` (or ``G | Gt``)
    under by(); every row for a lowess layer with adjust."""
    idx = frame.index
    s = pd.Series(False, index=idx)
    for g in spec.get("graphs") or []:
        go = g.get("graph_options") or {}
        gq, gt = g.get("qual_col", ""), g.get("qual_col_total", "")
        plots = [p for p in (g.get("plots") or []) if isinstance(p, dict)]
        kept = [p for p in plots
                if str(p.get("type", "")).lower() not in _LITERAL]
        tot = bool(gt) or any(p.get("qual_col_total") for p in kept)
        if not kept:
            if str(go.get("by", "") or "").strip():
                s = s | _col(gq, masks, idx)
                if gt:
                    s = s | _col(gt, masks, idx)
            continue
        for p in kept:
            pq, pt = p.get("qual_col", ""), p.get("qual_col_total", "")
            s = s | (_col(gq, masks, idx) & _col(pq, masks, idx))
            if tot:
                s = s | (_col(gt or gq, masks, idx) & _col(pt or pq, masks, idx))
            if (str(p.get("type", "")).lower() == "lowess"
                    and str((p.get("options") or {}).get("adjust", "")
                            or "").strip()):
                return pd.Series(True, index=idx)
    return s


def _has_text_qualifier(o):
    return bool(str(o.get("if_expr", "") or "").strip()
                or str(o.get("in_expr", "") or "").strip())


def _is_qualified(spec):
    for g in spec.get("graphs") or []:
        objs = [g, g.get("graph_options") or {}] + [
            p for p in (g.get("plots") or []) if isinstance(p, dict)]
        if any(_has_text_qualifier(o) or o.get("qual_col") for o in objs):
            return True
    return False


def _selected_mode(spec):
    """No filter(), link(), brush(), csv or KPI card (D-40-01.a)."""
    bo = spec.get("build_options") or {}
    return not (str(bo.get("filter", "") or "").strip()
                or str(bo.get("link", "") or "").strip()
                or str(bo.get("brush", "") or "").strip()
                or bo.get("csv") or spec.get("kpis"))


def _frame_of(spec):
    """The parity frame *spec* is drawn over (test_mode_parity._write)."""
    bo = spec.get("build_options") or {}
    df = tp._DF.copy()
    if bo.get("_parity_frame") == "missing_first_y":
        df = df.assign(mpg=[float("nan")] + list(tp._DF["mpg"][1:]))
    if bo.get("frame_cols"):
        day = pd.Timestamp("1960-01-01") + pd.to_timedelta(tp._DF["when"],
                                                           unit="D")
        df = df.assign(__dashm1=((day.dt.year - 1960) * 12
                                 + day.dt.month - 1).astype(float))
    return df


def _qualify(spec, df):
    """*spec* as dash.ado writes it: each if/in pair evaluated on the whole
    frame into a 0/1 column ``__dashq<k>`` named in "qual_col" (Stata
    evaluates every qualifier before anything is exported).  Returns
    ``(spec, frame with the columns, masks)``."""
    spec = copy.deepcopy(spec)
    bo = spec.get("build_options") or {}
    bo.pop("_parity_frame", None)
    df = df.copy()
    masks = {}

    def take(rows):
        name = "__dashq%d" % (len(masks) + 1)
        df[name] = rows.astype(float)
        masks[name] = rows.astype(bool)
        return name

    for g in spec.get("graphs") or []:
        go = g.get("graph_options") or {}
        rows = None
        if _has_text_qualifier(g):
            rows = dr._dash_embed_rows_of(g, df, {})
        if _has_text_qualifier(go):
            r2 = dr._dash_embed_rows_of(go, df, {})
            rows = r2 if rows is None else (rows | r2)
        for o in (g, go, g.get("options") or {}):
            o.pop("if_expr", None)
            o.pop("in_expr", None)
        if rows is not None:
            g["qual_col"] = take(rows)
        for p in g.get("plots") or []:
            if isinstance(p, dict) and _has_text_qualifier(p):
                p["qual_col"] = take(dr._dash_embed_rows_of(p, df, {}))
                p["if_expr"] = p["in_expr"] = ""
    return spec, df, masks


def _corpus(pred):
    out = []
    for p in tp.CORPUS:
        name, spec = p.values
        if _is_qualified(spec) and pred(spec):
            out.append(pytest.param(name, spec, id=name))
    return out


_QUALIFIED = _corpus(lambda s: True)
_DRAWN = _corpus(_selected_mode)


def _write_inputs(spec, df, tag):
    d = os.path.join(tp._TMP, "sel_%s_%d" % (tag, next(tp._SEQ)))
    os.makedirs(d, exist_ok=True)
    sp, dp = os.path.join(d, "spec.json"), os.path.join(d, "data.json")
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    with open(dp, "w", encoding="utf-8") as fh:
        json.dump(make_data_json(df, tp._VALUE_LABELS, tp._LABEL_NAMES), fh)
    return sp, dp


def _saved_profiles(spec, df):
    """Every figure's profile and the warnings of the saved renderer."""
    sp, dp = _write_inputs(spec, df, "std")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r = render_models(dr.DashRenderer(sp, dp))
    profiles = []
    tp._layout_tree(r._last_layout_root, profiles)
    return (profiles,
            sorted(str(w.message) for w in caught))


class TestTheSelectionCoversThePlan:
    """The rule's rows hold every row the page plan keeps for a graph."""

    @pytest.mark.parametrize("name,spec", _QUALIFIED)
    def test_the_rule_holds_the_plans_rows(self, name, spec):
        q, df, masks = _qualify(spec, _frame_of(spec))
        sel = _selected(q, df, masks)
        plan = dr._dash_embed_plan(q, df, masks, "", [])
        drawn = pd.Series(False, index=df.index)
        for rows in plan["graph_rows"].values():
            drawn = drawn | rows
        missed = sorted(int(i) for i in df.index[drawn & ~sel])
        assert not missed, f"{name}: the plan keeps rows {missed} the rule drops"


class TestTheDrawingIsUnchanged:
    """Each qualified entry a selected-mode build would make draws the same
    figures from the selected rows as from the whole frame."""

    @pytest.mark.parametrize("name,spec", _DRAWN)
    def test_each_qualified_entry(self, name, spec):
        q, df, masks = _qualify(spec, _frame_of(spec))
        sel = _selected(q, df, masks)
        full, full_w = _saved_profiles(q, df)
        sub_spec = copy.deepcopy(q)
        for g in sub_spec.get("graphs") or []:
            g["n_obs"] = int(len(df))
        # No row marked, or every row: today's export (D-40-01.c).
        cut = 0 < int(sel.sum()) < len(df)
        sub = df[sel.values].reset_index(drop=True) if cut else df
        got, got_w = _saved_profiles(sub_spec, sub)
        assert len(got) == len(full), name
        for i, (a, b) in enumerate(zip(full, got)):
            diffs = tp._diff(a, b)
            assert not diffs, f"{name}, figure {i}: {diffs[:5]}"
        assert got_w == full_w, name


# ===========================================================================
# The wiring in dash.ado
# ===========================================================================

_ROUTES = ("_dash_render_immediate", "_dash_prepare_spec")


class TestTheRule:

    @pytest.mark.parametrize("prog", _ROUTES)
    def test_sel_mark_runs_before_the_export_on_both_routes(self, prog):
        lines = _lines(_program(prog))
        exports = [i for i, ln in enumerate(lines)
                   if "_dash_write_data \"" in ln and "program" not in ln]
        assert exports, prog
        for i in exports:
            marks = [j for j in range(i) if "_dash_sel_mark(" in lines[j]]
            ticks = [j for j in range(i)
                     if "_dash_stata_ticks_gen" in lines[j]]
            assert marks, f"{prog}: no _dash_sel_mark before line {i}"
            assert ticks and marks[-1] > ticks[-1], (
                f"{prog}: the rows are marked before the last working column")
        body = "\n".join(lines)
        assert re.search(r"frame put [^\n]*if `_dash_sel'[^\n]*"
                         r"into\(`_dash_sf'\)", body), prog
        fp = body.index("frame `_dash_sf': _dash_write_data")
        assert "capture frame drop `_dash_sf'" in body[fp:], prog

    @pytest.mark.parametrize("prog", _ROUTES)
    def test_keep_only_in_dashs_own_frames(self, prog):
        lines = _lines(_program(prog))
        keeps = [ln for ln in lines if re.search(r"keep if `_dash_sel'", ln)]
        assert keeps, f"{prog}: no keep of the marked rows"
        for ln in keeps:
            # The user's frame is never reduced: a keep under _xfp runs
            # only when _xfp names 35-08's temporary frame.
            assert ("frame `_dash_stk':" in ln
                    or ("`_xfp' quietly keep" in ln
                        and "\"`_xfp'\" != \"\"" in ln)), (
                f"{prog}: a keep outside dash's own frames: {ln.strip()}")

    def test_a_full_stack_exports_every_row(self):
        # 33-07's stack of several frames is not counted by
        # _dash_maxvar_room, so a stack at c(maxvar) has no room for the
        # selection column: its generate is captured and, when it fails,
        # the build exports every row, as before WP-40.
        body = _program("_dash_prepare_spec")
        gen = re.search(r"^\s*(capture )?frame `_dash_stk': quietly "
                        r"generate byte `_dash_sel' = 0\s*$", body, re.M)
        assert gen, "the stack's selection column"
        assert gen.group(1), gen.group(0).strip()
        after = body[gen.end():]
        assert re.match(r"\s*if !_rc \{", after), after[:80]

    def test_full_mode_exports_every_row(self):
        body = _program("_dash_prepare_spec")
        m = re.search(r"local _sel_mode = \((.*)\)\s*$", body, re.M)
        assert m, "the build route's _sel_mode"
        rule = m.group(1)
        for word in ("server", "dash serve", "filter", "link", "brush",
                     "csv", "_has_kpi"):
            assert word in rule, word
        assert re.search(r"local _has_kpi 1", body)

    @pytest.mark.parametrize("prog", _ROUTES)
    def test_no_selected_row_keeps_todays_export(self, prog):
        body = _program(prog)
        assert re.search(r"local _sel_cut = \(`_sel_n' > 0 & "
                         r"`_sel_n' < `_sel_N'\)", body), prog
        for m in re.finditer(r"^(?!\s*//)[^\n]*(frame put|keep if "
                             r"`_dash_sel')[^\n]*", body, re.M):
            # Each is inside an `if `_sel_cut'' block or carries the test.
            opened = body[:m.end()].rfind("if `_sel_cut'")
            assert opened >= 0, m.group(0)


# ===========================================================================
# lpoly's grid follows the graph's _N (D-40-01.d)
# ===========================================================================

def _lpoly_spec(n_obs=None, bo=None):
    spec = tp._spec([plot_for("lpoly", {"bwidth": "5000"})], bo)
    if n_obs is not None:
        spec["graphs"][0]["n_obs"] = n_obs
    return spec


def _lpoly_cfgs(figs):
    return [g._dash_agg_config for f in figs for g in f.renderers
            if getattr(g, "_dash_agg_config", {}).get("type") == "lpoly"]


def _x_lp(figs):
    """Each lpoly layer's grid count: the x_lp points it fits at (its
    bandwidth is wide, so no grid point lacks a neighbour and every one
    is drawn), checked against the refit config's own count."""
    out = []
    for f in figs:
        for r in f.renderers:
            data = getattr(getattr(r, "data_source", None), "data", {}) or {}
            if "x_lp" in data:
                out.append(len(data["x_lp"]))
    assert out == [c["n"] for c in _lpoly_cfgs(figs)], out
    return out


def _foreign():
    return tp._DF[tp._DF["foreign"] == 1].reset_index(drop=True)


class TestTheLpolyGrid:

    def test_the_grid_follows_n_obs_in_both_modes(self):
        spec = _lpoly_spec(74)
        r = jo._saved(spec, _foreign(), labels=True)
        figs = jo._saved_figs(r)
        assert _x_lp(figs) == [50]
        assert [c["n_dataset"] for c in _lpoly_cfgs(figs)] == [74]
        doc = jo._served(spec, _foreign(), labels=True)
        assert _x_lp(jo._served_figs(doc)) == [50]

    def test_set_graph_n_obs(self):
        gm = dr.GlyphMapper()
        gm._set_graph_n_obs({"n_obs": 74})
        assert gm.n_obs == 74
        for bad in ("74", True, -1, 1.5):
            gm._set_graph_n_obs({"n_obs": bad})
            assert gm.n_obs is None, bad
        gm.n_obs = 5
        gm._set_graph_n_obs({})
        assert gm.n_obs is None

    def test_n_obs_is_written_on_both_routes(self):
        imm = _program("_dash_render_immediate")
        put = imm.index('_dash_put_n_obs(st_local("json_spec")')
        assert put < imm.index("local master_json = "), "after master_json"
        assert put > imm.index("_dash_write_data \""), "before the export"
        bld = _program("_dash_prepare_spec")
        gn = bld.index('st_local("_gn_`k\'"')
        assert gn > bld.index("_dash_qual_rewrite("), "before the rewrite"
        app = bld.index('_dash_put_n_obs(st_local("_qg_`k\'")')
        assert app < bld.index(
            'mata: st_local("graphs_json", st_local("graphs_json") + '
            'st_local("_qg_`k\'"))')

    def test_a_served_move_keeps_n_obs(self):
        spec = _lpoly_spec(22, {"filter": "foreign, type(dropdown)"})
        doc = jo._served(spec, tp._DF, labels=True)
        [w] = [w for w in tp._widgets_of(doc) if type(w).__name__ == "Select"]
        want = [v for v, lab in w.options if lab == "Foreign"][0]
        tp._fire(w, want)
        assert _x_lp(jo._served_figs(doc)) == [22]

    def test_without_n_obs_the_dataset_stands_in(self):
        r = jo._saved(_lpoly_spec(), tp._DF, labels=True)
        assert _x_lp(jo._saved_figs(r)) == [len(tp._DF)]


# ===========================================================================
# The help (HR-18)
# ===========================================================================

class TestTheHelp:

    def test_what_dash_exports(self):
        h = _read(_HELP)
        i = h.index("{marker limits}")
        sect = h[i:h.index("{marker", i + 10)]
        assert "{ul:What dash exports.}" in sect
        para = sect[sect.index("{ul:What dash exports.}"):]
        para = " ".join(para[:para.index("{pstd}")].split())
        for words in ("exports only the observations some graph draws",
                      "{cmd:dash scatter y x in 1/100} on 3,000,000 "
                      "observations exports 100",
                      "{cmd:lowess}'s {cmd:adjust}",
                      "A served app, and any other build, export every "
                      "observation",
                      "a filter, a link, a brush or a card can reach any row"):
            assert words in para, words
