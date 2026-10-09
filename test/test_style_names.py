"""Stata's other style names (WP-30 P1.14b, section 36).

twoway draws every style name of Stata's style files, not only p1-p15:
``lstyle(refline)``, ``pstyle(ci)``, ``mstyle(histogram)``,
``astyle(p3bar)``, ``none`` and the rest, and draws a name it does not know
in its class's default attributes with a note.  dash drew p1-p15 only and
noted every other name (D-32b).  Each expectation is twoway's, measured in
StataNow 19.5: literal values from the plan's E9 (research p1-14 §2.3-2.4)
and test/fixtures/style_name_truth.json from
scripts/extract_style_name_truth.do; widths and sizes go through
``OptionTranslator`` alone.  Register rows P1.14.1, P1.14.3, P1.14.5,
P1.14.9.
"""

from __future__ import annotations

import json
import os
import sys
import time
import warnings

import pytest
from bokeh.models import GlyphRenderer
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
import test_scheme_resolution as tsr  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

MODES = tsr.MODES
T = dr.OptionTranslator
SP = dr.SchemeParser

_FIX = os.path.join(_HERE, "fixtures")
with open(os.path.join(_FIX, "style_name_truth.json"), encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)
with open(os.path.join(_FIX, "scheme_truth.json"), encoding="utf-8") as _fh:
    SCHEME_META = json.load(_fh)["_meta"]

#: twoway's values (plan E9.1-E9.3).
S2_REFLINE, P1, ST_P2 = "#2d6d66", "#1a85ff", "#d41159"
W = {k: T.translate_lwidth(k) for k in (".3", ".2", ".15")}


def _hex(c):
    return c.lower() if isinstance(c, str) else c


def _draw(plots, scheme="stcolor", mode="standalone", graph=None):
    """What *mode* drew for one graph of *plots*: (renderers, notes)."""
    if isinstance(plots, dict):
        plots = [plots]
    d = tsr._draw(tp._spec(list(plots), {"scheme": scheme}, graph or {}),
                  mode)
    rs = [r for f in d.figures for r in f.renderers
          if isinstance(r, GlyphRenderer)]
    return rs, [m for m in d.warnings if m.startswith("dash")]


def _one(rs, kind, k=0):
    gs = [r.glyph for r in rs if type(r.glyph).__name__ == kind]
    assert len(gs) > k, f"no {kind} drawn"
    return gs[k]


def _notes(fn):
    """The ``dash: named style`` notes *fn* raises, with the per-render
    de-duplication reset first."""
    dr._dash_reset_notes()
    with warnings.catch_warnings(record=True) as got:
        warnings.simplefilter("always")
        fn()
    return [str(w.message) for w in got
            if "named style" in str(w.message)
            or "not found in scheme" in str(w.message)]


# ---------------------------------------------------------------------------
# 36-01: regression tests (each failed at the batch-12 base)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", MODES)
class TestTheTableNames:
    def test_s2color_lstyle_refline(self, mode):
        rs, notes = _draw(plot_for("line", {"lstyle": "refline"}), "s2color",
                          mode)
        g = _one(rs, "Line")
        assert (_hex(g.line_color), list(g.line_dash)) == (S2_REFLINE, [])
        assert g.line_width == pytest.approx(W[".3"])
        assert not [n for n in notes if "refline" in n], notes


@pytest.mark.parametrize("mode", MODES)
class TestPstyleCi:
    def test_stcolor_scatter(self, mode):
        rs, _ = _draw(plot_for("scatter", {"pstyle": "ci"}), "stcolor", mode)
        g = _one(rs, "Scatter")
        assert _hex(g.fill_color) == "#a0a0a0"
        ratio = g.size / SP("stcolor").default_marker_size(0)
        assert ratio == pytest.approx(1.52778 / 1.04166, rel=0.01)


@pytest.mark.parametrize("mode", MODES)
class TestSeriesForms:
    def test_stcolor_area_astyle_p3bar(self, mode):
        rs, _ = _draw(plot_for("area", {"astyle": "p3bar"}), "stcolor", mode)
        g = _one(rs, "VArea")
        assert _hex(g.fill_color) == dr.GlyphMapper._blend_intensity(
            "#00bf7f", 0.8)


@pytest.mark.parametrize("mode", MODES)
class TestMarkerForms:
    def test_stcolor_mstyle_histogram(self, mode):
        rs, _ = _draw(plot_for("scatter", {"mstyle": "histogram"}),
                      "stcolor", mode)
        g = _one(rs, "Scatter")
        assert (_hex(g.fill_color), _hex(g.line_color)) == ("#1a85ff",
                                                            "#5faaff")
        assert g.line_width == pytest.approx(W[".15"])


@pytest.mark.parametrize("mode", MODES)
class TestNone:
    def test_none_draws_nothing(self, mode):
        """lstyle(none), mstyle(none), astyle(none): nothing drawn (E9.3,
        research t4's SVGs)."""
        bad = []
        for ptype, opt, kind, attrs in (
                ("line", "lstyle", "Line", ("line_alpha",)),
                ("scatter", "mstyle", "Scatter", ("fill_alpha",
                                                  "line_alpha")),
                ("area", "astyle", "VArea", ("fill_alpha",))):
            rs, _ = _draw(plot_for(ptype, {opt: "none"}), "stcolor", mode)
            g = _one(rs, kind)
            bad += [(opt, a) for a in attrs if getattr(g, a) != 0]
        assert not bad


@pytest.mark.parametrize("mode", MODES)
class TestUnknown:
    def test_the_class_defaults(self, mode):
        """An unknown name draws its class's default (E9.3): lstyle the
        foreground line, astyle the background area, pstyle p1 (on plot 2
        too), mstyle p1's marker with plot 2's line kept."""
        rs, _ = _draw([plot_for("line", {"lstyle": "bogus"})], "stcolor",
                      mode)
        g = _one(rs, "Line")
        assert (_hex(g.line_color), g.line_width) == ("#000000",
                                                      pytest.approx(W[".2"]))
        rs, _ = _draw(plot_for("area", {"astyle": "bogus"}), "s2color", mode)
        assert _hex(_one(rs, "VArea").fill_color) == "#eaf2f3"
        rs, _ = _draw([plot_for("scatter"),
                       plot_for("connected", {"mstyle": "bogus"})],
                      "stcolor", mode)
        g = _one(rs, "Scatter", 1)
        assert _hex(g.fill_color) == P1
        assert _hex(_one(rs, "Line").line_color) == ST_P2

    def test_s1rcolor_lstyle_bogus_is_white(self, mode):
        rs, _ = _draw(plot_for("line", {"lstyle": "bogus"}), "s1rcolor",
                      mode)
        assert _hex(_one(rs, "Line").line_color) == "#ffffff"


class TestKinds:
    def test_p0_p03_p16line_p3other_are_unknown(self):
        sp = SP("stcolor")
        got = {n: sp._style_kind("seriesstyle", n)
               for n in ("p0", "p03", "p16line", "p3other", "p3mark", "P3",
                         "p3bar", "fpall", "p3", "", "p#bar")}
        assert got == {"p0": "unknown", "p03": "unknown",
                       "p16line": "unknown", "p3other": "unknown",
                       "p3mark": "unknown", "P3": "unknown",
                       "p3bar": "table", "fpall": "known", "p3": "p",
                       "": "blank", "p#bar": "unknown"}


@pytest.mark.parametrize("mode", MODES)
class TestTheNote:
    def test_twoways_words_once(self, mode):
        """Two layers with the same bad name print one line (S06's
        channel; E9.4)."""
        _, notes = _draw([plot_for("area", {"astyle": "bogus"}),
                          plot_for("area", {"astyle": "bogus"})], "s2color",
                         mode)
        want = ("dash: named style bogus not found in class areastyle, "
                "default attributes used")
        assert [n for n in notes if "named style" in n] == [want]

    def test_known_not_drawn_is_named(self, mode):
        rs, notes = _draw(plot_for("scatter", {"pstyle": "fpall"}),
                          "stcolor", mode)
        assert _hex(_one(rs, "Scatter").fill_color) == P1
        assert [n for n in notes if "named style" in n] == [
            "dash: named style fpall of class seriesstyle is not drawn by "
            "dash; default attributes used"]


class TestTheUndrawnOptions:
    def test_dstyle_bogus_is_noted(self):
        """D-36i, E9.7: dstyle(bogus) is twoway's markerstyle note,
        dlstyle()/bmlinestyle() its linestyle note; a table name is
        silent and nothing is drawn from them."""
        gm = dr.GlyphMapper(scheme=SP("stcolor"))
        got = {k: _notes(lambda k=k: gm._style_plan({k: "bogus"}))
               for k in ("dstyle", "dlstyle", "bmlinestyle")}
        txt = "dash: named style bogus not found in class {}, default " \
              "attributes used"
        assert got == {"dstyle": [txt.format("markerstyle")],
                       "dlstyle": [txt.format("linestyle")],
                       "bmlinestyle": [txt.format("linestyle")]}
        assert _notes(lambda: gm._style_plan({"dstyle": "p3"})) == []
        assert gm._style_plan({"dstyle": "p3"}) is None


@pytest.mark.parametrize("mode", MODES)
class TestQuotes:
    def test_one_pair_of_quotes_is_unwrapped(self, mode):
        rs, notes = _draw(plot_for("line", {"lstyle": '"refline"'}),
                          "s2color", mode)
        assert _hex(_one(rs, "Line").line_color) == S2_REFLINE
        assert not [n for n in notes if "named style" in n]


class TestAGraphsOwnScheme:
    @pytest.mark.parametrize("mode", MODES)
    def test_a_graphs_own_scheme_reaches_the_style(self, mode):
        """A graph's scheme(stcolor) in an s2color dashboard draws stcolor's
        refline (E9.1), saved and served (the served app's per-graph scheme
        is section 34's _dash_under_graph_scheme)."""
        rs, _ = _draw(plot_for("line", {"lstyle": "refline"}), "s2color",
                      mode, graph={"scheme": "stcolor"})
        assert _hex(_one(rs, "Line").line_color) == "#000000"


class TestCiTypes:
    def test_each_c_record(self):
        """Every C record (lfitci, lpolyci, qfitci under pstyle()): the band
        and the fit line equal twoway's, one loop over the rows."""
        bad = []
        recs = TRUTH["records"]
        for rid in sorted(r for r in recs if r.startswith("C|")
                          and r.endswith("|band")):
            _, scheme, fit, name, _part = rid.split("|")
            gm = dr.GlyphMapper(scheme=SP(scheme))
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                st = gm._ci_band_style({"pstyle": name})
                fig = figure()
                ln = fig.line([1, 2], [1, 2])
                gm._ci_line_restyle(ln, {"pstyle": name})
            area = recs[rid]["area"]
            line = recs[rid[:-4] + "line"]["line"]
            want = (area["fill"], round(area["intensity"] / 100.0, 3),
                    area["line"], line["color"],
                    round(T.translate_lwidth(str(line["width"])), 3))
            got = (_hex(st["fill"]), round(st["intensity"], 3),
                   _hex(st["line"]), _hex(ln.glyph.line_color),
                   round(ln.glyph.line_width, 3))
            if want != got:
                bad.append((rid, want, got))
        assert not bad, "\n".join(map(str, bad))


class TestAUserScheme:
    def test_a_child_override_reaches_lstyle_refline(self, tmp_path,
                                                     monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "rz.scheme").write_text(
            "#include s2color\ncolor refline red\n", encoding="utf-8")
        assert SP("rz.scheme").style_bundle("line", "refline")["line"] == \
            "#ff0000"

    def test_unread_directives_stay_and_print_nothing(self, tmp_path,
                                                      monkeypatch):
        """Guard (S33's D-33d, ratification row 4)."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "uz.scheme").write_text(
            "#include s2color\ncolor refline red\nclockdir p 9\n",
            encoding="utf-8")
        sp = SP("uz.scheme")
        dr._dash_reset_notes()
        with warnings.catch_warnings(record=True) as got:
            warnings.simplefilter("always")
            sp.style_bundle("line", "refline")
        assert sp._props.get("clockdir p") == "9"
        assert not [w for w in got if "dash scheme:" in str(w.message)]

    def test_a_missing_key_takes_s2colors_value(self, tmp_path,
                                                monkeypatch):
        """D-36g: a scheme with no #include and no `color refline' draws
        s2color's value, noted once in scheme.class's words."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "bz.scheme").write_text("color p1 red\n",
                                            encoding="utf-8")
        sp = SP("bz.scheme")
        out = {}
        notes = _notes(lambda: out.update(
            b=sp.style_bundle("line", "refline")))
        assert out["b"]["line"] == S2_REFLINE
        assert "dash: color refline not found in scheme, default attributes" \
            " used -- s2color's value" in notes
        assert len(notes) == len(set(notes))
        # A memo hit re-emits it for a later render.
        assert "dash: color refline not found in scheme, default " \
            "attributes used -- s2color's value" in _notes(
                lambda: sp.style_bundle("line", "refline"))


class TestTheFallback:
    def test_every_table_name_matches_s2color(self):
        fb, s2 = SP.fallback(), SP("s2color")
        bad = []
        for stata_class, tok in (("seriesstyle", "series.line"),
                                 ("seriesstyle", "series.area"),
                                 ("seriesstyle", "series.marker"),
                                 ("markerstyle", "marker"),
                                 ("areastyle", "area"),
                                 ("linestyle", "line")):
            for f in SP._STYLE_TABLE[stata_class]:
                n = f.replace("#", "3")
                a, b = fb.style_bundle(tok, n), s2.style_bundle(tok, n)
                if a is None or a != b:
                    bad.append((tok, n))
        assert not bad


class TestTheShapes:
    def test_each_class_has_p1s_keys(self):
        sp = SP("stcolor")
        for cls in ("marker", "line", "area"):
            assert set(sp.style_bundle(cls, "ci")) == \
                set(sp.style_bundle(cls, "p1")), cls
        for role in ("marker", "line", "area"):
            assert set(sp.style_bundle("series." + role, "ci")) == \
                set(sp.style_bundle(role, "p1")), role


_HOSTILE = ["../x", "p3;rm -rf", "{bf:x}", "\x00", "x" * 10000, "ｐ３",
            "p٣", "REFLINE", "refline\n", '""refline""', '"refline']


class TestAdversarial:
    def test_hostile_names_are_inert_and_noted(self):
        """TR-36.20: each draws the foreground line and is noted once, at
        most 80 printable characters of name; nothing raises."""
        sp = SP("stcolor")
        fg = sp.style_bundle("line", "foreground")
        bad = []
        for name in _HOSTILE:
            out = {}
            notes = _notes(lambda: out.update(b=sp.style_bundle("line",
                                                                 name)))
            if out["b"] != fg or len(notes) != 1:
                bad.append((name[:20], notes))
                continue
            shown = notes[0][len("dash: named style "):].split(
                " not found")[0]
            if len(shown) > 80 or any(ord(c) < 32 for c in shown):
                bad.append((name[:20], "shown"))
        assert not bad

    def test_ten_thousand_names_are_bounded(self):
        sp = SP("stcolor")
        sp.style_bundle("line", "refline")
        before = dict(sp.__dict__["_style_memo"])
        read = []

        class Spy(dict):
            def get(self, k, d=None):
                read.append(k)
                return dict.get(self, k, d)
        sp._props = Spy(sp._props)
        t0 = time.monotonic()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for i in range(10000):
                sp.style_bundle("line", f"zz{i}")
        assert time.monotonic() - t0 < 1.0
        assert set(sp.__dict__["_style_memo"]) - set(before) <= {
            ("line", "<default>")}
        assert not [k for k in read if "zz" in str(k)]


@pytest.mark.parametrize("mode", MODES)
class TestAfterAFilterMove:
    def test_served_style_survives_a_move(self, mode, tmp_path):
        import test_served_linked_views as lv
        spec = lv._spec([lv._graph("g1", plots=[
            plot_for("line", {"lstyle": "refline"})], scheme="s2color")],
            [lv._filter("range")], link="")
        if mode == "served":
            doc = lv._served_doc(tmp_path, spec)

            def look():
                [r] = [r for r in doc.select({"type": GlyphRenderer})
                       if type(r.glyph).__name__ == "Line"]
                return _hex(r.glyph.line_color)
            before = look()
            lv._fire(doc, "price", (4000.0, 5000.0))
            assert before == look() == S2_REFLINE
            return
        # Saved: a computed layer keeps the style on the stale cue.
        from conftest import render_models
        from test_adversarial_matrix import _write_inputs
        spec = lv._spec([lv._graph("g1", plots=[
            plot_for("lfit", {"lstyle": "refline"})], scheme="s2color")],
            [lv._filter("range")], link="")
        sp, dp = _write_inputs(tmp_path, spec)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = dr.DashRenderer(sp, dp)
            render_models(r)
        [line] = [rr for f in r.figures.values() for rr in f.renderers
                  if isinstance(rr, GlyphRenderer)
                  and type(rr.glyph).__name__ == "Line"]
        assert _hex(line.muted_glyph.line_color) == S2_REFLINE


# ---------------------------------------------------------------------------
# 36-03: against the fixture (one test per fixture grid, every row)
# ---------------------------------------------------------------------------

_TOKENS = {"pstyle": ("series.marker", "series.line", "series.area"),
           "mstyle": ("marker",), "lstyle": ("line",), "astyle": ("area",)}


def _op(v):
    return None if v is None or v >= 100 else round(v / 100.0, 2)


def _alpha(a):
    return None if a is None or a >= 1.0 else round(a, 2)


def _want(rec, role):
    """twoway's record for *role* in dash's units."""
    if role == "line":
        r = rec["line"]
        return {"line": None if r["none"] else r["color"],
                "line_alpha": None if r["none"] else _op(r["opacity"]),
                "line_width": round(T.translate_lwidth(str(r["width"])), 3),
                "line_dash": list(T.translate_lpattern(r["pattern"]))}
    if role == "area":
        r = rec["area"]
        out = {"fill": None if r["fill_none"] else r["fill"],
               "fill_alpha": None if r["fill_none"] else _op(
                   r["fill_opacity"]),
               "intensity": round(r["intensity"] / 100.0, 3),
               "line": None if r["line_none"] else r["line"]}
        if not r["line_none"]:
            out["line_width"] = round(
                T.translate_lwidth(str(r["line_width"])), 3)
        return out
    r = rec["marker"]
    if r["symbol"] == "none":
        return {"symbol": "none"}
    return {"fill": None if r["fill_none"] else r["fill"],
            "line": None if r["line_none"] else r["line"],
            "line_width": round(T.translate_lwidth(str(r["line_width"])), 3),
            "symbol": T.translate_msymbol(r["symbol"]),
            "size": round(T.translate_msize(str(r["size"])), 3)}


def _got(b, role, want):
    if role == "marker" and want == {"symbol": "none"}:
        return {"symbol": "none" if b["fill"] is None and b["line"] is None
                else b["symbol"]}
    out = {}
    for k in want:
        v = b.get(k)
        if k in ("line", "fill"):
            v = _hex(v)
        elif k in ("line_alpha", "fill_alpha"):
            v = _alpha(v)
        elif k in ("line_width", "size", "intensity"):
            v = round(float(v or 0.0), 3)
        elif k == "line_dash":
            v = list(v or [])
        out[k] = v
    return out


#: N rows dash does not draw as twoway does, each for a filed reason.
_N_EXCLUDED = {
    ("lstyle", "plotregion"): (
        "dash-*.scheme's `color plotregion_line' is the plot region's drawn "
        "border (S07's plotregion_line_truth), not Stata's key of that name; "
        "lstyle(plotregion) reads it (filed for the closeout)"),
}


def _compare(grid):
    bad = []
    parsers: dict = {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for rid, rec in sorted(TRUTH["records"].items()):
            if not rid.startswith(grid + "|"):
                continue
            _, scheme, opt, name = rid.split("|")
            if (opt, name) in _N_EXCLUDED:
                continue
            sp = parsers.setdefault(scheme, SP(scheme))
            for tok in _TOKENS[opt]:
                role = tok.rsplit(".", 1)[-1]
                want = _want(rec, role)
                got = _got(sp.style_bundle(tok, name), role, want)
                if got != want:
                    bad.append((rid, tok, want, got))
    return bad


class TestAgainstStata:
    def test_every_n_record(self):
        """Every table name of every class under each of the 26 schemes
        (grid N) equals twoway's resolved style."""
        bad = _compare("N")
        assert not bad, "\n".join(map(str, bad[:30])) + f"\n({len(bad)})"


class TestDefaultAttributes:
    def test_every_u_record(self):
        """Every name twoway does not know (grid U) draws twoway's default
        attributes, and twoway's notes are dash's, prefixed ``dash:``."""
        bad = _compare("U")
        for cid, notes in TRUTH["notes"].items():
            if not cid.startswith("U|"):
                continue
            _, scheme, opt, _call = cid.split("|")
            names = TRUTH["cmds"][cid]
            sp = SP(scheme)
            want = sorted({"dash: " + n[len("(note: "):-1] for n in notes})
            toks = [t.split("(", 1)[1].rstrip(")") for t in
                    names.replace(")", ") ").split() if f"{opt}(" in t]
            got = sorted(set(_notes(lambda: [sp.style_bundle(
                _TOKENS[opt][0], n) for n in toks])))
            if want != got:
                bad.append((cid, want, got))
        assert not bad, "\n".join(map(str, bad[:30])) + f"\n({len(bad)})"


class TestKnownNotDrawn:
    def test_each_k_record(self):
        """K: twoway draws Stata's own names with no note; dash draws the
        class default and names them (D-36c)."""
        bad = []
        sp = SP("stcolor")
        for rid, rec in TRUTH["records"].items():
            if not rid.startswith("K|"):
                continue
            _, _s, opt, name = rid.split("|")
            if rec["rc"] != 0 or TRUTH["notes"][rid]:
                bad.append((rid, "twoway"))
            cls = {"pstyle": "seriesstyle", "mstyle": "markerstyle",
                   "astyle": "areastyle"}[opt]
            if _notes(lambda: sp.style_bundle(_TOKENS[opt][0], name)) != [
                    f"dash: named style {name} of class {cls} is not drawn "
                    f"by dash; default attributes used"]:
                bad.append((rid, "dash"))
        assert not bad


class TestDeclaredNotDrawn:
    def test_each_d_record(self):
        """D: twoway accepts dstyle/dlstyle/bmlinestyle and their
        abbreviations (rc 0) and refuses bm() r(198); its notes for a bad
        name are dash's (D-36i)."""
        notes = TRUTH["notes"]
        rcs = {}
        for rid, cmd in TRUTH["cmds"].items():
            if rid.startswith("D|"):
                rcs[cmd.split(",", 1)[1].split()[0]] = rid
        assert set(rcs) >= {"dstyle(p3)", "dst(p3)", "dlstyle(p3)",
                            "dl(p3)", "dls(p3)", "bmlinestyle(p3)",
                            "bml(p3)", "bm(p3)"}
        gm = dr.GlyphMapper(scheme=SP("stcolor"))
        for opt, cls in (("dstyle", "markerstyle"), ("dlstyle", "linestyle"),
                         ("bmlinestyle", "linestyle")):
            want = ["dash: " + n[len("(note: "):-1]
                    for n in notes[rcs[f"{opt}(bogus)"]]]
            assert _notes(lambda: gm._style_plan({opt: "bogus"})) == want
            assert cls in want[0]


class TestHostileNames:
    def test_each_h_record(self):
        """H: twoway refuses none (rc 0); dash draws the default (refline
        for one pair of quotes) and notes every other name once."""
        bad = []
        sp = SP("stcolor")
        recs = TRUTH["records"]
        for rid, rec in recs.items():
            if not rid.startswith("H|"):
                continue
            name, opt = rec["name"], rid.split("|")[2]
            tok = _TOKENS[opt][1 if opt == "pstyle" else 0]
            out = {}
            notes = _notes(lambda: out.update(b=sp.style_bundle(tok, name)))
            # One pair of quotes is unwrapped (D-36j): lstyle("refline") is
            # refline, silent; pstyle("refline") is a seriesstyle twoway
            # does not know, noted.
            quiet = name == '"refline"' and opt == "lstyle"
            if rec["rc"] != 0 or bool(TRUTH["notes"][rec["call"]]) == quiet:
                bad.append((rid, "twoway"))
            if len(notes) != (0 if quiet else 1):
                bad.append((rid, notes))
            if out["b"]["line"] != rec["line"]["color"]:
                bad.append((rid, out["b"]["line"], rec["line"]["color"]))
        assert not bad


class TestS32sOtherNameRows:
    def test_each_u_row(self):
        """S32's U rows (named_style_truth.json): every other name now
        draws as twoway drew it on plot 1."""
        with open(os.path.join(_FIX, "named_style_truth.json"),
                  encoding="utf-8") as fh:
            cases = json.load(fh)["cases"]
        sp = SP("stcolor")
        bad = []
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for cid, c in cases.items():
                if not cid.startswith("U-") or c["rc"] != 0:
                    continue
                _, _t, opt, name = cid.split("-", 3)
                rec = c["plots"]["1"]
                b = sp.style_bundle(_TOKENS[opt][-1 if opt != "pstyle"
                                                 else 1], name)
                if opt == "mstyle":
                    want, got = rec["ml"], b["line"]
                elif opt == "astyle":
                    want, got = rec["af"], b["fill"]
                else:
                    want, got = rec["lc"], b["line"]
                want = "#%02x%02x%02x" % tuple(int(x) for x in want.split())
                none = (rec.get("ms") == "none" and opt == "mstyle") or (
                    opt != "mstyle" and got is None)
                if not none and _hex(got) != want:
                    bad.append((cid, want, got))
        assert not bad, bad


class TestTheStyleTable:
    def test_it_is_19_5s_files(self):
        want = SCHEME_META["style_files"]
        got = {c: {f: [list(r) for r in rows] for f, rows in t.items()}
               for c, t in SP._STYLE_TABLE.items()}
        assert got == want
        assert len(SP._STYLE_TABLE["linestyle"]) == 75

    def test_known_lists_match(self):
        assert {c: sorted(v) for c, v in SP._STYLE_KNOWN.items()} == \
            SCHEME_META["style_known"]


class TestTheFixture:
    def test_meta_is_stamped(self):
        m = TRUTH["_meta"]
        assert {"stata_version", "born_date", "dash_commit", "extracted",
                "source", "seconds"} <= set(m)
        assert sorted(TRUTH["schemes"]) == sorted(SP._BUILTIN_NAMES)
