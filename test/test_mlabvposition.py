"""mlabvposition(varname): each marker label at its own row's clock
(WP-30 P1.24).

The defect: dash.ado declared mlabvposition() and put it on the pending
list, so it never reached the spec; ``dash scatter y x, mlabel(lab)
mlabvposition(pos)`` drew every label at 3 o'clock and named the option in
its note.  It also accepted the option where twoway refuses it (the range
and fit types, a second copy, two names, an expression, a missing
variable).

twoway (StataNow 19.5, twoway_yxview_parse.class:187, :308-317) declares
``MLABVposition(name)``, unabbreviates it and appends it to the layer's
varlist.  It reads the variable row by row: a whole number 0-12 is that
clock; a missing value, and every row of a string variable, takes
``mlabposition()`` (else 3), silently; any other number is drawn at 12 with
a note.  ``test/fixtures/mlabvpos_truth.json`` (scripts/
extract_mlabvpos_truth.do) holds, per probe and label row, the clock twoway
draws it at, against references drawn with ``mlabposition(k)``.  The
refusals are pinned against live twoway in test_twoway_option_parity.cscript
(MV-01..MV-11) and the drawing in test_wp30_truth.cscript (MV-20..MV-24).
"""

import json
import math
import os
import re
import sys
import tempfile
import warnings
import itertools

import numpy as np
import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import ColumnDataSource, LabelSet

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import load_app, make_data_json, render_models  # noqa: E402
from test_mode_parity import _spec as _mp_spec  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402
import test_unsupported_report_is_true as _uri  # noqa: E402

_FIX = json.load(open(os.path.join(_HERE, "fixtures",
                                   "mlabvpos_truth.json"),
                      encoding="utf-8"))
_DATA = pd.DataFrame(_FIX["_meta"]["data"]).astype(
    {c: float for c in ("x", "y", "pos", "bpos", "dpos", "p9", "g", "y2",
                        "x2", "y3")} | {"lab": object, "spos": object})
_ADO = open(os.path.join(_ROOT, "dash.ado"), encoding="utf-8").read()
_MATA = open(os.path.join(_ROOT, "dash_parse.mata"), encoding="utf-8").read()
_HELP = open(os.path.join(_ROOT, "dash.sthlp"), encoding="utf-8").read()
_SEQ = itertools.count()
_TMP = tempfile.mkdtemp(prefix="dash_mlabvpos_")
_CLOCK = dr.GlyphMapper._MLABEL_CLOCK


def _plot(ptype, options, **vars_):
    if ptype.startswith("pc"):
        p = {"type": ptype, "y1var": "y", "x1var": "x", "y2var": "y3",
             "x2var": "x2"}
    else:
        p = {"type": ptype, "yvar": "y", "xvar": "x"}
    p.update(vars_)
    p["options"] = dict(options)
    return p


def _write(spec, df):
    tag = next(_SEQ)
    sp = os.path.join(_TMP, f"spec_{tag}.json")
    dp = os.path.join(_TMP, f"data_{tag}.json")
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    data = make_data_json(df)
    for c in df.columns:
        if df[c].dtype == object:
            data["StataJSON"]["variableIsString"][c] = True
            data["StataJSON"]["variableTypeIsString"][c] = True
    with open(dp, "w") as fh:
        json.dump(data, fh)
    return tag, sp, dp


def _spec(plots, go=None, bo=None):
    return _mp_spec(plots, dict({"scheme": "stcolor"}, **(bo or {})), go)


def _saved(spec, df=_DATA):
    _, sp, dp = _write(spec, df)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = render_models(dr.DashRenderer(sp, dp))
    return list(r._last_layout_root.references())


def _served(spec, df=_DATA):
    tag, sp, dp = _write(spec, df)
    ap = os.path.join(_TMP, f"app_{tag}.py")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(ap)
        mod = load_app(ap, f"_mlabvpos_{tag}")
        doc = Document()
        mod.make_document(doc)
    return [m for root in doc.roots for m in root.references()]


def _models(mode, plots, go=None, bo=None, df=_DATA):
    spec = _spec(plots, go, bo)
    return (_saved if mode == "saved" else _served)(spec, df)


def _rows(ls, prop):
    v = getattr(ls, prop)
    f = _field(v)
    if isinstance(v, str) and v not in ls.source.data:
        f = None
    n = len(ls.source.data[_field(ls.text)])
    if f is not None:
        return list(ls.source.data[f])
    val = getattr(v, "value", v)
    return [val] * n


def _field(v):
    if isinstance(v, str):
        return v
    if isinstance(v, dict):
        return v.get("field")
    return getattr(v, "field", None)


def _clock_of(xo, yo, align, baseline):
    """The k of _MLABEL_CLOCK whose anchor is (align, baseline) and whose
    unit vector the offset runs along; 0 for a label centred on its point."""
    xo, yo = float(xo), float(yo)
    if abs(xo) < 1e-9 and abs(yo) < 1e-9:
        return 0 if (align, baseline) == ("center", "middle") else None
    d = math.hypot(xo, yo)
    for k in range(1, 13):
        (ux, uy), anch = _CLOCK[k][1], _CLOCK[k][2]
        if anch == (align, baseline) and abs(xo / d - ux) < 1e-6 \
                and abs(yo / d - uy) < 1e-6:
            return k
    return None


def _clocks_of(models):
    """{label text: [clock, ...]} over every drawn label row."""
    out = {}
    for ls in models:
        if not isinstance(ls, LabelSet):
            continue
        texts = list(ls.source.data[_field(ls.text)])
        xs = list(ls.source.data[_field(ls.x)])
        ys = list(ls.source.data[_field(ls.y)])
        cols = [_rows(ls, p) for p in ("x_offset", "y_offset", "text_align",
                                       "text_baseline")]
        for i, t in enumerate(texts):
            if pd.isna(xs[i]) or pd.isna(ys[i]):
                continue
            out.setdefault(str(t), []).append(
                _clock_of(*(c[i] for c in cols)))
    return out


def _want(probe):
    return {lab: [k] for lab, k in _FIX["probes"][probe]["clock"].items()}


# ---------------------------------------------------------------------------
# The fixture
# ---------------------------------------------------------------------------

class TestTheFixture:
    def test_it_is_stamped(self):
        m = _FIX["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted"):
            assert m.get(k), k
        assert m["stata_version"].startswith("19.")
        assert m["scheme"] == "stcolor"
        want = {"A", "C", "G", "K3", "E2", "DT", "BY", "MY2", "RSQ", "SI"} | {
            f"T_{t}" for t in ("connected", "bar", "dot", "dropline",
                               "pcscatter", "pccapsym", "pcarrow",
                               "pcbarrow")}
        assert set(_FIX["probes"]) == want
        notes = " ".join(_FIX["probes"]["A"]["notes"])
        for v in ("3.5", "13", "-1"):
            assert f"named style {v} not found" in notes


# ---------------------------------------------------------------------------
# The spec carries it
# ---------------------------------------------------------------------------

def _program(text, name):
    m = re.search(r"^program define " + name + r"\b.*?^end\b", text,
                  re.S | re.M)
    assert m, name
    return m.group(0)


class TestTheSpecCarriesIt:
    def test_the_parser_writes_it(self):
        body = _program(_ADO, "_dash_parse_plot_opts")
        assert re.search(r"sreturn local mlabvposition\s+: copy local "
                         r"mlabvposition", body)
        assert "_dash_pending' mlabvposition" not in body
        keys = _program(_ADO, "_dash_plot_opts_to_json")
        assert re.search(r"\bmlabvposition\b", keys)

    def test_the_mata_extractor_lists_it(self):
        m = re.search(r"void _dash_extract_vars\(.*?varlist = \"\"", _MATA,
                      re.S)
        assert m and 'char(34)+"mlabvposition"+char(34)' in m.group(0)

    def test_the_renderer_carries_its_column(self):
        assert "mlabvposition" in dr._DASH_OPT_VAR_KEYS
        o = {"mlabel": "lab", "mlabvposition": "pos"}
        assert dr._dash_option_columns(o) == ["lab", "pos"]
        assert dr._dash_option_columns(o, columns=["lab"]) == ["lab"]
        for bad in ("pos x", "a$b", "p" * 33):
            assert dr._dash_option_columns({"mlabvposition": bad}) == []


# ---------------------------------------------------------------------------
# Every declared option reaches the spec (BR-37.9)
# ---------------------------------------------------------------------------

_DECL = re.compile(r"\b([A-Z][A-Za-z0-9]*)\s*\(")
_FLAG = re.compile(r"\b(?:no)?([A-Z][A-Za-z0-9]*)\b")

#: Declared, and on purpose not written to the spec.
#: Flipped (WP-30 P1.24 part 2): mlabtextstyle left it, serialised as a
#: style list.
# Flipped (WP-31 D5): xoverhangs and yoverhangs ("P2.13 (Sizing)") were
# allowed to reach no spec; they are drawn and written now.
_ALLOW = {}
# table2: TABLE2() is table's argument form, folded onto s(table) by
# _dash_table_fold (WP-31 H2t).
_GRAPH_ALIASES = {"pbgc", "xla2", "xsc2", "xti2", "yla2", "ysc2", "yti2",
                  "table2"}


def _declared(prog):
    """The option names a program's syntax command declares, lower case."""
    body = _program(_ADO, prog)
    # The syntax command runs to its first line without a /// tail.
    lines, out = body.splitlines(), []
    start = next(i for i, ln in enumerate(lines)
                 if re.match(r"\s*syntax\b", ln))
    for ln in lines[start:]:
        out.append(ln.split("//")[0] if "///" not in ln
                   else ln.split("///")[0])
        if "///" not in ln:
            break
    text = " ".join(out)
    names = set()
    for tok in re.findall(r"\*|[A-Za-z][A-Za-z0-9_]*(?:\([^)]*\))?", text):
        word = re.match(r"[A-Za-z][A-Za-z0-9_]*", tok)
        if not word or not re.search(r"[A-Z]", word.group(0)[:1]) \
                and not word.group(0).startswith("no"):
            continue
        names.add(word.group(0).lower())
    names.discard("syntax")
    return names, body


def _s_returns(body):
    return set(re.findall(r"sreturn local (?:g_)?([A-Za-z0-9_]+)", body))


class TestDeclaredOptionsReachTheSpec:
    def test_every_declared_plot_option_has_an_s_return(self):
        names, body = _declared("_dash_parse_plot_opts")
        sret = _s_returns(body)
        missing = sorted(n for n in names
                         if n not in sret and n not in _uri.ALIASES
                         and n.removeprefix("no") not in sret
                         and n not in _ALLOW)
        assert not missing, missing

    def test_every_plain_s_return_is_written(self):
        _, body = _declared("_dash_parse_plot_opts")
        keys = set(re.findall(r"[a-z0-9_]+",
                              _program(_ADO, "_dash_plot_opts_to_json")))
        allowed = {"sort1": "read by _dash_sort_opt, never written",
                   "bw": "folded by _dash_fold_bw",
                   # WP-31 C4: twoway declares it and never reads it.
                   "smoothplot": "taken and emptied by _dash_fit_opts_check"}
        plain = set(re.findall(r"sreturn local ([a-z0-9]+)\b", body))
        missing = sorted(n for n in plain
                         if n not in keys and n not in allowed
                         and not n.startswith("_"))
        assert not missing, missing

    def test_every_declared_graph_option_has_an_s_return(self):
        names, body = _declared("_dash_parse_graph_opts")
        sret = _s_returns(body)
        missing = sorted(n for n in names
                         if n not in sret and n not in _GRAPH_ALIASES
                         and n not in _ALLOW
                         and n.removeprefix("no") not in sret
                         and n not in _uri.ALIASES)
        assert not missing, missing

    def test_the_allowlist_is_live(self):
        names, body = _declared("_dash_parse_plot_opts")
        sret = _s_returns(body)
        for n in _ALLOW:
            assert n in names and n not in sret, n


# ---------------------------------------------------------------------------
# The name, and the per-row columns
# ---------------------------------------------------------------------------

class TestTheName:
    def test_one_stata_name_or_nothing(self):
        for ok in ("pos", " pos ", "ü"):
            assert dr._dash_mlabvpos_name({"mlabvposition": ok}) == ok.strip()
        for bad in ("", None, "pos x", "1p", "<b>", "a$b", "p" * 33, 5):
            assert dr._dash_mlabvpos_name({"mlabvposition": bad}) == ""
        assert dr._dash_mlabvpos_name(None) == ""


def _mapper():
    return dr.GlyphMapper(scheme=dr.SchemeParser.fallback())


_POS = [float(i) for i in range(13)] + [np.nan, 3.5, 13.0, -1.0, np.nan]


def _expected(fallback):
    return ([i for i in range(13)] + [fallback, 12, 12, 12, fallback])


class TestThePerRowColumns:
    def test_every_clock_and_the_fallbacks(self, recwarn):
        dr._DASH_NOTED.clear()
        for fb in (3, 9):
            src = ColumnDataSource({"pos": list(_POS)})
            names = _mapper()._mlabel_vpos_columns(
                src, {"mlabvposition": "pos"}, fb, 10.0)
            xo, yo, al, bl = (list(src.data[n]) for n in names)
            for i, k in enumerate(_expected(fb)):
                (ux, uy), anch = _CLOCK[k][1], _CLOCK[k][2]
                want = (0.0, 0.0) if k == 0 else (10 * ux, 10 * uy)
                assert (xo[i], yo[i]) == pytest.approx(want), (fb, i)
                assert (al[i], bl[i]) == anch, (fb, i)
        msgs = [str(w.message) for w in recwarn.list
                if "mlabvposition(pos)" in str(w.message)]
        assert any("3.5, 13, -1 are not a whole number" in m for m in msgs)

    def test_the_gap_runs_along_each_rows_direction(self):
        src = ColumnDataSource({"pos": list(_POS)})
        m = _mapper()
        a = m._mlabel_vpos_columns(src, {"mlabvposition": "pos"}, 3, 10.0)
        b = m._mlabel_vpos_columns(src, {"mlabvposition": "pos"}, 3, 15.0)
        for i, k in enumerate(_expected(3)):
            dx = src.data[b[0]][i] - src.data[a[0]][i]
            dy = src.data[b[1]][i] - src.data[a[1]][i]
            want = (0.0, 0.0) if k == 0 else (5 * _CLOCK[k][1][0],
                                              5 * _CLOCK[k][1][1])
            assert (dx, dy) == pytest.approx(want), i

    def test_a_string_column_is_the_fallback_silently(self, recwarn):
        src = ColumnDataSource({"spos": ["1", "9", "."]})
        assert _mapper()._mlabel_vpos_columns(
            src, {"mlabvposition": "spos"}, 6, 10.0) is None
        assert not [w for w in recwarn.list
                    if "mlabvposition" in str(w.message)]

    def test_a_date_column_is_read_in_stata_units(self):
        days = pd.to_datetime("1960-01-01") + pd.to_timedelta(
            np.arange(13), unit="D")
        src = ColumnDataSource({"d": np.asarray(days, dtype="datetime64[ms]")})
        m = _mapper()
        m.date_vars = {"d": "td"}
        names = m._mlabel_vpos_columns(src, {"mlabvposition": "d"}, 3, 10.0)
        got = [_clock_of(*(src.data[n][i] for n in names))
               for i in range(13)]
        assert got == list(range(13))

    def test_out_of_range_values_get_one_capped_note(self, recwarn):
        dr._DASH_NOTED.clear()
        src = ColumnDataSource({"q": [100.0 + i for i in range(25)]})
        _mapper()._mlabel_vpos_columns(src, {"mlabvposition": "q"}, 3, 10.0)
        msgs = [str(w.message) for w in recwarn.list
                if "mlabvposition(q)" in str(w.message)]
        assert len(msgs) == 1
        assert "109 and 15 more are not" in msgs[0]
        assert "110" not in msgs[0]

    def test_names_are_keyed_by_fallback_and_distance(self):
        src = ColumnDataSource({"pos": list(_POS)})
        m = _mapper()
        a = m._mlabel_vpos_columns(src, {"mlabvposition": "pos"}, 3, 10.0)
        b = m._mlabel_vpos_columns(src, {"mlabvposition": "pos"}, 9, 15.0)
        assert not set(a) & set(b)
        assert all(n.startswith("__dash_mlabvpos_pos_") for n in a + b)


# ---------------------------------------------------------------------------
# Drawn as twoway draws it, in both modes (the fixture)
# ---------------------------------------------------------------------------

_SCATTER_PROBES = {
    "A": ({"mlabvposition": "pos"}, None, None),
    "C": ({"mlabvposition": "pos", "mlabposition": "9"}, None, None),
    "G": ({"mlabvposition": "pos", "mlabgap": "5"}, None, None),
    "K3": ({"mlabvposition": "bpos"}, None, None),
    "E2": ({"mlabvposition": "spos", "mlabposition": "6"}, None, None),
    "DT": ({"mlabvposition": "dpos"}, None, {"formats": {"dpos": "%td"}}),
    "BY": ({"mlabvposition": "pos"}, {"by": "g"}, None),
}

#: Flipped (WP-31 C15): T_bar's missing rows were recorded as not yet
#: drawn where twoway draws them (dash's bar labels defaulted to 3), which
#: was wrong once bar's labels default to 12 as twoway's; none is left.
_NOT_YET = {}


@pytest.mark.parametrize("mode", ["saved", "served"])
class TestTheSavedAndServedPages:
    def test_case(self, mode):
        bad = []
        for probe, (opts, go, bo) in _SCATTER_PROBES.items():
            got = _clocks_of(_models(mode, [_plot(
                "scatter", dict({"mlabel": "lab"}, **opts))], go, bo))
            if got != _want(probe):
                bad.append((probe, got))
        # MY2: one variable for every y, both series at 9.
        got = _clocks_of(_models(mode, [
            _plot("scatter", {"mlabel": "lab", "mlabvposition": "p9"}),
            _plot("scatter", {"mlabel": "lab", "mlabvposition": "p9"},
                  yvar="y2")]))
        if any(v != [9, 9] for v in got.values()) or len(got) != 18:
            bad.append(("MY2", got))
        assert not bad, bad


@pytest.mark.parametrize("mode", ["saved", "served"])
class TestEveryLabellingType:
    def test_type(self, mode):
        bad = []
        for probe in sorted(_FIX["probes"]):
            if not probe.startswith("T_"):
                continue
            got = _clocks_of(_models(mode, [_plot(
                probe[2:], {"mlabel": "lab", "mlabvposition": "pos"})]))
            want = _want(probe)
            for lab in want:
                if (probe, lab) in _NOT_YET:
                    assert got.get(lab) != want[lab], (probe, lab)
                elif got.get(lab) != want[lab]:
                    bad.append((probe, lab, got.get(lab), want[lab]))
        assert not bad, bad

    def test_a_variable_named_like_a_derived_column(self, mode):
        bad = []
        for ptype, var in (("dropline", "x"), ("dropline", "y"),
                           ("dropline", "y0"), ("pcscatter", "x"),
                           ("pcscatter", "y")):
            df = _DATA.assign(**{"pp": _DATA["pos"]})
            df = df.rename(columns={"x": "xx", "y": "yy"})
            df[var] = df["pp"]
            plot = _plot(ptype, {"mlabel": "lab", "mlabvposition": var})
            for k in ("xvar", "x1var"):
                if k in plot:
                    plot[k] = "xx"
            for k in ("yvar", "y1var"):
                if k in plot:
                    plot[k] = "yy"
            got = _clocks_of(_models(mode, [plot], df=df))
            if got != _want("A"):
                bad.append((ptype, var, got))
        assert not bad, bad

    def test_a_view_keeps_the_rows_clocks(self, mode):
        want = _want("A")
        bad = []
        for kw in ({"if_expr": "g == 1"}, {"in_expr": "1/9"}):
            spec = _mp_spec([_plot("scatter", {"mlabel": "lab",
                                               "mlabvposition": "pos"},
                                   **kw)], {"scheme": "stcolor"})
            got = _clocks_of((_saved if mode == "saved" else _served)(spec))
            if not got or any(got[t] != want[t] for t in got):
                bad.append((kw, got))
        assert not bad, bad

    def test_the_range_quirk_is_drawn_per_row(self, mode):
        assert _FIX["probes"]["RSQ"]["anchors"] == ["end"]
        got = _clocks_of(_models(mode, [{
            "type": "rscatter", "yvar1": "y", "yvar2": "y2", "xvar": "x",
            "options": {"mlabel": "y", "mlabvposition": "p9"}}]))
        assert got and all(set(v) == {9} for v in got.values()), got


class TestTheImmediateTypes:
    def test_scatteri_ignores_it(self):
        assert _FIX["probes"]["SI"]["equal_to_ref"] is True
        vals = [[1.0, 1.0, "a"], [2.0, 2.0, "b"]]
        for mode in ("saved", "served"):
            a = _clocks_of(_models(mode, [{"type": "scatteri", "values": vals,
                                           "options": {"mlabvposition":
                                                       "p9"}}]))
            b = _clocks_of(_models(mode, [{"type": "scatteri", "values": vals,
                                           "options": {}}]))
            assert a == b, mode


class TestNoLabelNoColumns:
    def test_without_mlabel_nothing_is_added(self):
        ms = _models("saved", [_plot("scatter", {"mlabvposition": "pos"})])
        assert not [m for m in ms if isinstance(m, LabelSet)]
        for m in ms:
            if isinstance(m, ColumnDataSource):
                assert not [c for c in m.data
                            if c.startswith("__dash_mlabvpos_")]


class TestOffsetsArePhysical:
    def test_offsets_do_not_depend_on_the_data(self):
        def offsets(df, yvar, xvar):
            out = []
            for ls in _models("saved", [_plot("scatter", {
                    "mlabel": "lab", "mlabvposition": "pos"},
                    yvar=yvar, xvar=xvar)], df=df):
                if isinstance(ls, LabelSet):
                    out.append([list(_rows(ls, p)) for p in
                                ("x_offset", "y_offset")])
            return out
        big = _DATA.assign(x=_DATA["x"] * 1000, y=_DATA["y"] * 1000)
        a = offsets(_DATA, "y", "x")
        assert a == offsets(big, "y", "x") == offsets(_DATA, "x", "y")


class TestAfterAFilterMove:
    @pytest.mark.parametrize("case", ["linked", "unlinked", "pcarrow"])
    def test_served_moves(self, case):
        import test_served_filter_move as sfm
        df = _DATA.assign(rep=_DATA["pos"])
        ptype = "pcarrow" if case == "pcarrow" else "scatter"
        plots = [_plot(ptype, {"mlabel": "lab", "mlabvposition": "pos"})]
        bo = {"filter": "g, type(dropdown)"}
        if case == "unlinked":
            bo["link"] = "none"
        spec = _spec(plots, None, bo)
        tag, sp, dp = _write(spec, df)
        ap = os.path.join(_TMP, f"app_{tag}.py")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(ap)
            mod = load_app(ap, f"_mlabvpos_mv_{tag}")
            doc = Document()
            mod.make_document(doc)
            sfm._move(doc, "Select", "1")
        ms = [m for root in doc.roots for m in root.references()]
        got = _clocks_of(ms)
        want = _want("A")
        kept = {f"R{i + 1}" for i in range(18) if _DATA["g"][i] == 1}
        assert set(got) == kept, sorted(got)
        assert all(got[t] == want[t] for t in got), got


class TestTheServedCopy:
    def test_the_app_defines_the_names(self):
        spec = _spec([_plot("scatter", {"mlabel": "lab",
                                        "mlabvposition": "pos"})])
        tag, sp, dp = _write(spec, _DATA)
        ap = os.path.join(_TMP, f"app_{tag}.py")
        dr.ServerAppBuilder(sp, dp).build(ap)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mod = load_app(ap, f"_mlabvpos_copy_{tag}")
        assert callable(mod._dash_mlabvpos_name)
        assert mod.GlyphMapper._MLABVPOS_VALUES == "__dash_mlabvpos_values"


class TestTheHelp:
    def test_the_help_documents_it(self):
        assert "{cmdab:mlabv:position(}" in _HELP
        unsup = _HELP[_HELP.index("{marker unsupported}"):]
        assert "mlabvposition" not in unsup.split("{marker", 2)[1]
        assert "{ul:Marker-label placement" not in _HELP
