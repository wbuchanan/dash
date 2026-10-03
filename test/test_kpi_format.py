"""KPI cards are written in Stata's display format (WP-28 section 11, GAPS2 E1).

A card is the one place dash promises a format by name: ``dash kpi ...,
fmt(%fmt)``.  GAPS2 E1 measured that the card did not keep the promise:
``fmt(%10.0g)`` of 6165.2567 read ``6e+03`` in both modes and after every
move, ``%9,2f`` showed the raw value, ``%td`` of 15000 showed ``15000.0``,
date KPIs ignored ``fmt()``, a card without ``fmt()`` dropped the variable's
own ``%g`` format, a missing date read ``""`` and then ``—``, and the
page's card rebuild concatenated its text into HTML unescaped.

The oracle is ``test/fixtures/format_truth.json``'s ``kpi`` block: Stata's
own ``display`` text of each statistic, variable and format, measured on
``sysuse auto`` with ``when = mdy(1,1,2000)+_n`` (``%td``) and
``whenm = mofd(when)`` (``%tm``).
"""

import json
import math
import os
import sys
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_help_claims_4 as hc4  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "format_truth.json")
_KPI_TRUTH = os.path.join(_HERE, "fixtures", "kpi_pctile_truth.json")

#: Every variable's display format, as sysuse auto (and the fixture's two
#: date variables) carry them.
_OWN = {"price": "%8.0gc", "mpg": "%8.0g", "weight": "%8.0gc",
        "rep78": "%8.0g", "foreign": "%8.0g", "when": "%td",
        "whenm": "%tm"}
_DATE_KIND = {"when": "td", "whenm": "tm"}


def _load_rows():
    if not os.path.exists(_FIXTURE):
        pytest.fail("test/fixtures/format_truth.json is missing: section 04 "
                    "(WP-28) records it; the KPI tests read its kpi block")
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)["kpi"]


_ROWS = _load_rows()


def _row_id(r):
    return "%s-%s-%s%s" % (r["stat"], r["var"], r["fmt"] or "nofmt",
                           "-if" if r["if"] else "")


def _expected(row):
    """Stata's text for *row*'s card.  With ``fmt()`` it is the row's own
    ``display``; without one the fixture records the raw macro text, and
    dash's documented rule is the variable's own format (a date-valued
    statistic of a date variable its ``%t`` picture, a count ``%9.0g``),
    so the row of the same statistic under that format is the truth
    (``%8.0g`` reads as ``%9.0g`` on these small values)."""
    if row["fmt"]:
        return row["display"]
    own = _OWN[row["var"]]
    if row["var"] in _DATE_KIND and not dr._dash_kpi_date_valued(row["stat"]):
        own = "%9.0g"
    if own == "%8.0g":
        own = "%9.0g"
    for r in _ROWS:
        if (r["stat"], r["var"], r["if"], r["fmt"]) == (
                row["stat"], row["var"], row["if"], own):
            return r["display"]
    return dr._dash_fmt_text(float(row["value"]), own)


def _frame():
    with open(_KPI_TRUTH, encoding="utf-8") as fh:
        truth = json.load(fh)
    df = hc4._auto(truth)
    n = len(df)
    df["when"] = np.arange(14611, 14611 + n, dtype=float)
    stamp = pd.Timestamp("1960-01-01") + pd.to_timedelta(df["when"], unit="D")
    df["whenm"] = ((stamp.dt.year - 1960) * 12
                   + stamp.dt.month - 1).astype(float)
    return df


def _kpi(name, stat, var, fmt, if_expr="", update="filter"):
    return {"name": name, "stat": stat, "var": var, "fmt": fmt,
            "title": "T", "update": update, "if_expr": if_expr}


def _spec(kpis, formats=None):
    return {"graphs": [{"plots": [{"type": "scatter", "yvar": "mpg",
                                   "xvar": "weight", "options": {}}],
                        "graph_options": {"name": "g1"},
                        "if_expr": "", "in_expr": ""}],
            "kpis": kpis,
            "build_options": {"layout": "auto", "link": "", "theme": "",
                              "title": "", "subtitle": "",
                              "formats": dict(_OWN if formats is None
                                              else formats),
                              "filters": [{"varname": "mpg",
                                           "type": "slider"}],
                              "registry": "g1 " + " ".join(
                                  k["name"] for k in kpis)}}


#: A dashboard holds at most 99 cards (dash's resource limit), so the
#: fixture's rows are rendered in pages of 90.
_PAGE = 90


def _row_kpis(page):
    return [_kpi("k%d" % i, r["stat"], r["var"], r["fmt"],
                 r["if"][3:] if r["if"] else "")
            for i, r in enumerate(_ROWS) if i // _PAGE == page]


_PAGES = range((len(_ROWS) + _PAGE - 1) // _PAGE)
_NAMES = {_row_id(r): "k%d" % i for i, r in enumerate(_ROWS)}
_BY_ID = {_row_id(r): r for r in _ROWS}
_IDS = list(_BY_ID)


@pytest.fixture(scope="module")
def df():
    return _frame()


@pytest.fixture(scope="module")
def saved(tmp_path_factory, df):
    return [hc4._saved(tmp_path_factory.mktemp("kf_saved"),
                       _spec(_row_kpis(p)), df) for p in _PAGES]


@pytest.fixture(scope="module")
def saved_cards(saved):
    out = {}
    for r in saved:
        out.update(hc4._cards(d.text for d in r.kpi_divs.values()))
    return out


@pytest.fixture(scope="module")
def served(tmp_path_factory, df):
    return [hc4._served_app(tmp_path_factory.mktemp("kf_served"),
                            _spec(_row_kpis(p)), df) for p in _PAGES]


@pytest.fixture(scope="module")
def served_cards(served):
    out = {}
    for ns in served:
        out.update(hc4._served_cards(hc4._served_session(ns)))
    return out


@pytest.fixture(scope="module")
def saved_moved(saved, df):
    out = {}
    for r in saved:
        out.update(hc4._saved_filter_move(r, 0, float(df["mpg"].min())))
    return out


@pytest.fixture(scope="module")
def served_moved(served, df):
    out = {}
    for ns in served:
        out.update(hc4._served_filter_move(ns, "mpg",
                                           float(df["mpg"].min())))
    return out


# ===========================================================================
# First paint
# ===========================================================================

class TestFirstPaint:

    @pytest.mark.parametrize("rid", _IDS)
    def test_every_kpi_row_of_the_fixture_saved(self, saved, saved_cards,
                                                rid):
        row = _BY_ID[rid]
        if row["value"] != ".":
            got = saved[0]._compute_kpi_stat_on_df(
                saved[0].df, row["stat"], row["var"])
            # WP-29 P0.20 (section 05): every statistic of a date is
            # taken of its Stata values, so it is compared with Stata's
            # directly; it was epoch milliseconds, converted here.
            assert got == pytest.approx(float(row["value"]), rel=1e-9)
        assert saved_cards[_NAMES[rid]] == _expected(row)

    @pytest.mark.parametrize("rid", _IDS)
    def test_every_kpi_row_of_the_fixture_served(self, served_cards, rid):
        assert served_cards[_NAMES[rid]] == _expected(_BY_ID[rid])


# ===========================================================================
# After a filter move (no row removed) and after one that removes rows
# ===========================================================================

class TestAfterAMove:

    @pytest.mark.parametrize("rid", _IDS)
    def test_every_kpi_row_after_a_filter_move_saved(self, saved_moved, rid):
        assert saved_moved[_NAMES[rid]] == _expected(_BY_ID[rid])

    @pytest.mark.parametrize("rid", _IDS)
    def test_every_kpi_row_after_a_filter_move_served(self, served_moved,
                                                      rid):
        assert served_moved[_NAMES[rid]] == _expected(_BY_ID[rid])

    def test_a_move_that_removes_rows_recomputes_and_formats(self, tmp_path,
                                                             df):
        kpis = [_kpi("km", "mean", "price", "%10.0g"),
                _kpi("kd", "max", "when", "%td"),
                _kpi("kn", "mean", "price", "")]
        kept = df[df["mpg"] >= 25]
        want = {"km": dr._dash_fmt_text(kept["price"].mean(), "%10.0g"),
                "kd": dr._dash_fmt_text(kept["when"].max(), "%td"),
                "kn": dr._dash_fmt_text(kept["price"].mean(), "%8.0gc")}
        r = hc4._saved(tmp_path, _spec(kpis), df)
        got = hc4._saved_filter_move(r, 0, 25.0)
        assert {k: got[k] for k in want} == want
        ns = hc4._served_app(tmp_path, _spec(kpis), df)
        got = hc4._served_filter_move(ns, "mpg", 25.0)
        assert {k: got[k] for k in want} == want


# ===========================================================================
# After a brush
# ===========================================================================

class TestAfterABrush:

    def test_the_brushed_card_is_formatted_in_both_modes(self, tmp_path, df):
        kpis = [_kpi("km", "mean", "price", "%10.0g", update="brush"),
                _kpi("kd", "max", "when", "%tdCCYY-NN-DD", update="brush")]
        sel = df.iloc[[0, 1, 2]]
        want = {"km": dr._dash_fmt_text(sel["price"].mean(), "%10.0g"),
                "kd": dr._dash_fmt_text(sel["when"].max(), "%tdCCYY-NN-DD")}
        r = hc4._saved(tmp_path, _spec(kpis), df)
        got = hc4._saved_brush(r, "g1", [0, 1, 2])
        assert {k: got[k] for k in want} == want
        ns = hc4._served_app(tmp_path, _spec(kpis), df)
        got = hc4._served_brush(ns, [0, 1, 2])
        assert {k: got[k] for k in want} == want


# ===========================================================================
# Missing
# ===========================================================================

class TestMissing:

    def test_a_missing_statistic_is_a_dot_everywhere(self, tmp_path, df):
        kpis = [_kpi("kp", "mean", "price", "", "price > 1e9", "both"),
                _kpi("kd", "max", "when", "", "price > 1e9", "both")]
        want = {"kp": ".", "kd": "."}
        r = hc4._saved(tmp_path, _spec(kpis), df)
        opened = hc4._cards(d.text for d in r.kpi_divs.values())
        moved = hc4._saved_filter_move(r, 0, float(df["mpg"].min()))
        brushed = hc4._saved_brush(r, "g1", [0, 1, 2])
        ns = hc4._served_app(tmp_path, _spec(kpis), df)
        s_open = hc4._served_cards(hc4._served_session(ns))
        s_moved = hc4._served_filter_move(ns, "mpg", float(df["mpg"].min()))
        s_brush = hc4._served_brush(ns, [0, 1, 2])
        for where, got in (("saved first paint", opened),
                           ("saved move", moved), ("saved brush", brushed),
                           ("served first paint", s_open),
                           ("served move", s_moved),
                           ("served brush", s_brush)):
            assert {k: got.get(k) for k in want} == want, where


# ===========================================================================
# The effective-format rule
# ===========================================================================

class TestEffectiveFormat:

    @pytest.mark.parametrize("kpi,var,formats,stat,want", [
        ({"fmt": "%9.2f"}, "price", {"price": "%8.0gc"}, "mean", "%9.2f"),
        ({}, "price", {"price": "%8.0gc"}, "mean", "%8.0gc"),
        ({}, "when", {"when": "%tdCCYY-NN-DD"}, "max", "%tdCCYY-NN-DD"),
        ({}, "when", {"when": "%tdCCYY-NN-DD"}, "count", "%9.0g"),
        ({}, "when", {"when": "%tdCCYY-NN-DD"}, "sd", "%9.0g"),
        # A hand-edited fmt() is returned as written (the writer shows
        # %9.0g for it, with one note); a variable's own %x is not placed.
        ({"fmt": "%21x"}, "price", {"price": "%8.0gc"}, "mean", "%21x"),
        ({}, "price", {"price": "%21x"}, "mean", "%9.0g"),
        ({}, "x", {}, "mean", "%9.0g"),
    ])
    def test_the_rule(self, kpi, var, formats, stat, want):
        dates = {"when": "td"}
        assert dr._dash_effective_kpi_fmt(kpi, var, formats, stat,
                                          dates) == want


# ===========================================================================
# Escaping
# ===========================================================================

_BOLD = "%td!<!b!>DD"


class TestEscaping:

    def test_the_js_rebuild_escapes_the_card_text(self, tmp_path, df):
        kpis = [_kpi("kd", "max", "when", _BOLD)]
        r = hc4._saved(tmp_path, _spec(kpis), df)
        opened = r.kpi_divs["kd"].text
        assert "&lt;b&gt;" in opened and "<b>" not in opened
        cb = r.filter_callbacks[0]
        w = r.filter_widgets[0]
        w.value = float(df["mpg"].min())
        texts = hc4._run_js(cb.args, cb.code)
        card = [t for t in texts.values() if 'id="kpi_val_kd"' in (t or "")]
        assert len(card) == 1
        assert "&lt;b&gt;" in card[0] and "<b>" not in card[0]

    def test_the_format_never_reaches_code_or_style(self, tmp_path, df):
        kpis = [_kpi("kd", "max", "when", _BOLD)]
        r = hc4._saved(tmp_path, _spec(kpis), df)
        cb = r.filter_callbacks[0]
        assert _BOLD not in cb.code
        cfg = json.loads(cb.args["kpi_config_json"])
        assert [c["fmt"] for c in cfg] == [_BOLD]


# ===========================================================================
# A hand-edited format the page cannot write
# ===========================================================================

class TestRefusedOnACard:

    def test_a_hand_edited_x_format_falls_back_with_one_note(self, tmp_path,
                                                             df):
        kpis = [_kpi("kx", "mean", "price", "%21x")]
        want = dr._dash_fmt_text(df["price"].mean(), "%9.0g")
        sp, dp = hc4._write_inputs(tmp_path, _spec(kpis), df)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            r = dr.DashRenderer(sp, dp)
            r.render()
        notes = [str(x.message) for x in w if "%21x" in str(x.message)]
        assert len(notes) == 1 and "kx" in notes[0], notes
        assert hc4._cards(d.text for d in r.kpi_divs.values())["kx"] == want
        ns = hc4._served_app(tmp_path, _spec(kpis), df)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            doc = hc4.Document()
            ns["make_document"](doc)
        notes = [str(x.message) for x in w if "%21x" in str(x.message)]
        assert len(notes) == 1 and "kx" in notes[0], notes
        assert hc4._served_cards(doc)["kx"] == want


# ===========================================================================
# The page's config and its script
# ===========================================================================

class TestConfig:

    def test_the_config_carries_fmt_and_storage_and_not_the_legacy_fields(
            self, tmp_path, df):
        kpis = [_kpi("kd", "max", "when", ""), _kpi("kp", "mean", "price", "")]
        r = hc4._saved(tmp_path, _spec(kpis), df)
        cfg = json.loads(r.filter_callbacks[0].args["kpi_config_json"])
        for c in cfg:
            for key in ("fmt", "storage", "datekind", "use"):
                assert key in c, key
            for key in ("numfmt", "decimals", "commas", "general"):
                assert key not in c, key
        assert {c["name"]: c["fmt"] for c in cfg} == {"kd": "%td",
                                                       "kp": "%8.0gc"}
        assert not hasattr(dr.DashRenderer, "_parse_fmt")
        assert not hasattr(dr.DashRenderer, "_kpi_js_number_format")
        assert "function dash_numfmt(" not in dr._FILTER_JS

    def test_the_brush_slice_markers_keep_their_order(self):
        s = dr._FILTER_JS
        assert (s.index("// ---- KPI recompute, shared by")
                < s.index("function dash_apply_kpis(")
                < s.index("dash_apply_kpis(new_data,"))
        assert s.count("dash_apply_kpis(new_data,") == 1


def test_the_node_tests_ran(saved_moved):
    """The after-move cases run under node.  This asks for their fixture
    itself, so it proves node ran whichever worker it lands on; a machine
    without node skips here rather than passing silently (a skip, which
    DASH_STRICT refuses)."""
    assert set(saved_moved) >= {_NAMES[rid] for rid in _IDS}
