"""Stata's colour grammar in options and scheme files (WP-30 P1.13a).

twoway reads ``colour*#`` (towards white below 1, divided above it with a
clamp, multiplied under ``system naturally_white 0``), CMYK ``"C M Y K"``,
HSV ``"hsv H S V"``, ``bg``/``fg``/``background``/``foreground`` from the
scheme, and ``%#`` beside ``*#`` in either order.  It draws an unknown or
wrong-case colour black with a note, keeps the default for a malformed hex,
multiplier or opacity in silence, and refuses a comma-written plot colour
with ``invalid '<word>'``, r(198).  In a scheme file a malformed value draws
white and commas separate numbers.  dash refused every one of the new forms
with a note and drew an unknown colour in the scheme's colour (GAPS2 D7).

Truth is test/fixtures/colour_grammar_truth.json, written by
scripts/extract_colour_grammar_truth.do from StataNow 19.5's SVG export
(plan section 30, Evidence E3); every expected colour below is twoway's,
never computed through dash_render.
"""

import json
import os
import re
import sys
import warnings

import pytest
from bokeh.models import CustomJS, GlyphRenderer, Span

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_scheme_resolution import MODES, _draw  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402
from conftest import drawn_renderers  # noqa: E402

OT = dr.OptionTranslator
_FIXTURE = os.path.join(_HERE, "fixtures", "colour_grammar_truth.json")
_HEX = re.compile(r"#[0-9a-f]{6}")
_STATUSES = ("ok", "keep", "unknown")


def _truth():
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _unquote(v):
    """The value as dash's spec and scheme reader carry it: one enclosing
    pair of double quotes removed."""
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] == '"':
        return v[1:-1]
    return v


def _comma_word(value):
    """The word twoway names refusing a comma-written colour (E3): the first
    word after the first comma, words split at blanks and commas, unless the
    text after the comma starts with one; ``editcopy`` with no word."""
    v = _unquote(value)
    if '"' in v or "," not in v:
        return None
    rest = v[v.index(",") + 1:]
    if rest.startswith(","):
        return None
    words = rest.replace(",", " ").split()
    return words[0][:80] if words else "editcopy"


def _scheme_file(tmp_path, monkeypatch, name, lines):
    monkeypatch.chdir(tmp_path)
    (tmp_path / f"{name}.scheme").write_text(
        "#include s2color\n" + "".join(x + "\n" for x in lines),
        encoding="utf-8")
    return name


def _parse(name):
    """(SchemeParser, warnings) for scheme *name*."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        sp = dr.SchemeParser(name)
    return sp, [str(w.message) for w in caught]


def _noted(fn, *a, **kw):
    """(result, warnings) of one call, the per-render de-duplication reset."""
    dr._DASH_NOTED.clear()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        out = fn(*a, **kw)
    return out, [str(w.message) for w in caught]


def _close(a, b):
    if a is None or b is None:
        return (a in (None, 1.0)) and (b in (None, 1.0))
    return abs(float(a) - float(b)) < 1e-9


# ---------------------------------------------------------------------------
# Stata truth
# ---------------------------------------------------------------------------

class TestStataTruth:
    def test_the_meta_stamp(self):
        meta = _truth()["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted"):
            assert meta.get(k), k
        assert len(meta["excluded"]) == 2, meta["excluded"]

    def test_each_probe(self, tmp_path, monkeypatch):
        """Every measured probe the reader owns, in its context and scheme:
        options through the mapper's own translator, scheme files through
        SchemeParser, comma refusals in twoway's words.  One test, every
        mismatch reported."""
        d = _truth()
        skip = set(d["_meta"]["excluded"])
        bad = []
        parsers = {}

        def parser(s):
            if s not in parsers:
                parsers[s] = dr.SchemeParser(s)
            return parsers[s]

        monkeypatch.chdir(tmp_path)
        for pid, p in sorted(d["probes"].items()):
            if pid in skip or p["owner"] or p["group"] == "site":
                continue
            val = _unquote(p["value"])
            if p["group"] in ("opt", "s1r", "bgs"):
                sp = parser(p["scheme"])
                tr = dr.GlyphMapper(scheme=sp).tr
                (hx, a), msgs = _noted(tr.parse_color_alpha, val, "mcolor")
                if hx is None and a is None:
                    got = (sp.p_colors[0], None, 0)
                elif hx is None:        # a bare *# or %#: S43's base
                    got = (p["fill"], a, len(msgs))
                else:
                    got = (hx, a, len(msgs))
                want = (p["fill"], p["opacity"], 1 if p["notes"] else 0)
            elif p["group"] == "sch":
                name = f"cgs_{pid}"
                (tmp_path / f"{name}.scheme").write_text(
                    f"#include s2color\ncolor p1 {p['value']}\n",
                    encoding="utf-8")
                sp, msgs = _parse(name)
                msgs = [m for m in msgs if "color p1" in m]
                got = (sp.p_colors[0], sp.p_alphas[0], len(msgs))
                want = (p["fill"], p["opacity"], 1 if p["notes"] else 0)
            elif p["group"] == "bgfg":
                tag, _, body = p["value"].partition(": ")
                if tag == "t05":
                    # D-30e, a measured residual: dash's own files write
                    # every colour as hex, so a hex background is a name to
                    # bg; twoway's named-style lookup fails (black, noted).
                    continue
                lines, _, opt = body.partition(" + ")
                name = f"cgb_{pid}"
                (tmp_path / f"{name}.scheme").write_text(
                    "#include s2color\n" + "".join(
                        x.strip() + "\n" for x in lines.split(";")),
                    encoding="utf-8")
                sp, _msgs = _parse(name)
                if opt:
                    v = opt[len("mcolor("):-1]
                    (hx, _a), _m = _noted(
                        dr.GlyphMapper(scheme=sp).tr.parse_color_alpha, v,
                        "mcolor")
                else:
                    hx = sp.p_colors[0]
                got = (hx, sp.background_color)
                want = (p["fill"], p["region"])
            elif p["group"] == "comma":
                got = (p["rc"], p["refusal"])
                w = _comma_word(p["value"])
                want = ((198, f"invalid '{w}'") if w and "bgcolor" not in
                        p["command"] else (0, None))
            else:
                continue
            same = (got[0] == want[0] and all(
                _close(x, y) if isinstance(x, (float, type(None))) and
                isinstance(y, (float, type(None))) else x == y
                for x, y in zip(got[1:], want[1:])))
            if not same:
                bad.append(f"{pid} {p['value']!r}: dash {got}, twoway {want}")
        assert not bad, "\n".join(bad)


# ---------------------------------------------------------------------------
# The pure reader
# ---------------------------------------------------------------------------

class TestTheParts:
    def test_either_order(self):
        cases = {"navy*.5%50": ("navy", ".5", "50"),
                 "navy%50*.5": ("navy", ".5", "50"),
                 "navy*.5*2": ("navy", ".5*2", None),
                 "red%": ("red", None, ""),
                 "navy": ("navy", None, None)}
        got = {k: OT._colour_parts(k) for k in cases}
        assert got == cases

    def test_the_commas_twoway_draws(self):
        """Every other comma-separated part, joined by blanks (measured
        18oct2026: 1,,2 is "1 2", 1, ,2 "1 2", 255,,0,,0 red)."""
        cases = {"1,,2": "1 2", "1, ,2": "1 2", "255,,0,,0": "255 0 0",
                 ",,red": "red", "red*2,,blue": "red*2 blue",
                 "navy": "navy", "255 0 0": "255 0 0",
                 # Forms twoway refuses, kept as written for dash.ado.
                 "255,0,0": "255,0,0", "red,": "red,"}
        assert {k: OT._colour_commas(k) for k in cases} == cases

    def test_one_enclosing_quote_pair_is_removed(self):
        """A plain or compound pair around the whole colour is removed; a
        quote with no partner, or quotes inside, are kept."""
        cases = {'"1 2 3"': "1 2 3", '`"1 2 3"\'': "1 2 3",
                 '"255 0 0': '"255 0 0', 'navy': 'navy',
                 '"a" "b"': '"a" "b"'}
        assert {k: OT._colour_unquote(k) for k in cases} == cases


class TestOutputIsAlwaysHex:
    HOSTILE = ["x" * 10000, "red*nan", "red*inf", "red*1e400", "*" * 500,
               "%%%", "#}a{b;c", "red*٥", "١٢ 0 0", "red\x00",
               "hsv nan 1 1", "0 0 0 inf", "red%nan", "1,2,3", "1,2,3,4,5"]

    def test_hostile_inputs(self):
        bad = []
        for ctx in ("option", "scheme"):
            for v in self.HOSTILE:
                try:
                    st, hx, a = OT.stata_colour(v, context=ctx)
                except Exception as exc:  # noqa: BLE001
                    raise AssertionError(
                        f"{ctx} {v[:20]!r}: raised {exc!r}") from exc
                if st not in _STATUSES or (
                        hx is not None and not _HEX.fullmatch(hx)) or (
                        a is not None and not 0 <= a <= 1):
                    bad.append(f"{ctx} {v[:20]!r}: {(st, hx, a)}")
        assert not bad, "\n".join(bad)


# ---------------------------------------------------------------------------
# The three readers delegate
# ---------------------------------------------------------------------------

class TestTheTranslatorsDelegate:
    def test_translate_mcolor_returns_the_grammars_hex_or_raises(self):
        assert OT.translate_mcolor("navy*.5") == "#8da3b7"
        assert OT.translate_mcolor("#FF0000") == "#ff0000"
        bad = []
        for v in ("Navy", "grey", "bogus", "#f00", "255,0,128", "%50", "",
                  "red*abc", "x" * 10000):
            try:
                OT.translate_mcolor(v)
                bad.append(v[:20])
            except ValueError as exc:
                assert "Unknown Stata color" in str(exc)
        assert not bad, f"accepted: {bad}"

    def test_parse_color_alpha_draws_an_unknown_colour_black(self):
        out, msgs = _noted(OT.parse_color_alpha, "bogus", "mcolor")
        assert out == ("#000000", None)
        # Flipped (18oct2026): dash's own wording was wrong because twoway
        # notes an unknown colour in its words, naming the colour alone.
        assert msgs == ["dash: named style bogus not found in class color, "
                        "default attributes used"], msgs
        out, msgs = _noted(OT.parse_color_alpha, "Red%50")
        assert out == ("#000000", 0.5) and msgs == []

    def test_parse_color_alpha_keeps_the_default_in_silence(self):
        for v in ("#F00", "red%150", "red*abc", "*abc", ""):
            out, msgs = _noted(OT.parse_color_alpha, v, "mcolor")
            assert out == (None, None) and msgs == [], (v, out, msgs)

    def test_translate_lcolor_passes_the_context(self):
        assert OT.translate_lcolor("fg", foreground="#ffffff") == "#ffffff"
        assert OT.translate_lcolor("navy*.5", naturally_white=False) \
            == "#0d2438"


class TestTheMapperReadsItsScheme:
    def test_a_graphs_own_scheme_is_read(self):
        """The bound translator reads the scheme the mapper holds at call
        time, so a graph-level scheme() swapped onto it is honoured."""
        g = dr.GlyphMapper(scheme=dr.SchemeParser("s1rcolor"))
        assert g.tr.translate_mcolor("fg") == "#ffffff"
        assert g.tr.translate_mcolor("navy*.5") == "#0d2438"
        g.scheme = dr.SchemeParser("stcolor")
        assert g.tr.translate_mcolor("bg") == "#ffffff"
        assert g.tr.parse_color_alpha("navy*.5") == ("#8da3b7", None)
        # an explicit keyword still wins
        assert g.tr.translate_mcolor("bg", background="#123456") == "#123456"

    def test_a_plain_translator_is_bound_and_another_object_kept(self):
        g = dr.GlyphMapper(OT(), dr.SchemeParser("s1rcolor"))
        assert g.tr.translate_mcolor("fg") == "#ffffff"
        other = object()
        assert dr.GlyphMapper(other).tr is other

    def test_the_context_of_a_scheme(self):
        assert OT.scheme_colour_context(dr.SchemeParser("s2color")) == {
            "background": "#eaf2f3", "foreground": "#000000",
            "naturally_white": True}
        assert OT.scheme_colour_context(None) == {}


# ---------------------------------------------------------------------------
# Scheme files
# ---------------------------------------------------------------------------

class TestSchemeFiles:
    def test_an_unreadable_key_draws_black_with_one_note(
            self, tmp_path, monkeypatch):
        name = _scheme_file(tmp_path, monkeypatch, "cgkeys", [
            "color background bogus", "color heading bogus",
            "color plotregion bogus", "color p1lineplot bogus",
            "color p1bar bogus"])
        sp, msgs = _parse(name)
        assert (sp.background_color, sp.title_color, sp.plotregion_color,
                sp.p_lineplot_colors[0], sp.p_bar_colors[0]) == ("#000000",) * 5
        for key in ("color background", "color heading", "color plotregion",
                    "color p1lineplot", "color p1bar"):
            hits = [m for m in msgs if f"(from '{key}')" in m]
            assert hits == [f"dash scheme: colour 'bogus' (from '{key}') is "
                            "not a colour; using black, as twoway does."], \
                (key, msgs)

    def test_a_malformed_value_draws_white_in_silence(
            self, tmp_path, monkeypatch):
        name = _scheme_file(tmp_path, monkeypatch, "cgwhite", [
            "color background #}a{b;c", "color heading navy*abc",
            "color p1 %50"])
        sp, msgs = _parse(name)
        assert (sp.background_color, sp.title_color) == ("#ffffff",) * 2
        assert (sp.p_colors[0], sp.p_alphas[0]) == ("#ffffff", 0.5)
        assert not [m for m in msgs if "dash scheme: colour" in m], msgs
        assert "#}a{b;c" not in sp.css_block()

    def test_foreground_is_read(self, tmp_path, monkeypatch):
        assert dr.SchemeParser("s2color").foreground_color == "#000000"
        assert dr.SchemeParser("s1rcolor").foreground_color == "#ffffff"
        name = _scheme_file(tmp_path, monkeypatch, "cgfg",
                            ["color foreground red"])
        sp, _ = _parse(name)
        assert (sp.foreground_color, sp.fg_lookup) == ("#ff0000", "#ff0000")

    def test_absent_keys_keep_their_defaults(self, tmp_path, monkeypatch):
        """Guard: an absent key is silent inheritance."""
        fb = dr.SchemeParser.fallback()
        s2 = dr.SchemeParser("s2color")
        assert (fb.background_color, fb.title_color) == \
            (s2.background_color, s2.title_color)
        monkeypatch.chdir(tmp_path)
        (tmp_path / "cgbare.scheme").write_text("color p1 red\n",
                                                encoding="utf-8")
        sp, _ = _parse("cgbare")
        assert sp.background_color == "#d9e8f0"

    def test_a_long_scheme_value_is_named_briefly(self, tmp_path,
                                                  monkeypatch):
        name = _scheme_file(tmp_path, monkeypatch, "cglong",
                            ["color heading " + "x" * 10000])
        sp, msgs = _parse(name)
        hits = [m for m in msgs if "color heading" in m]
        assert sp.title_color == "#000000"
        assert len(hits) == 1 and len(hits[0]) < 400, hits


# ---------------------------------------------------------------------------
# Module readers and the KPI
# ---------------------------------------------------------------------------

class TestModuleReaders:
    def test_textbox_colour(self):
        out, msgs = _noted(dr._textbox_color, {"color": "bogus"}, None)
        # Flipped (18oct2026): twoway's wording, not dash's.
        assert out == "#000000" and msgs == [
            "dash: named style bogus not found in class color, default attributes "
            "used"]
        assert _noted(dr._textbox_color, {"color": "#F00"}, None) == (None, [])
        assert dr._textbox_color({"color": "navy*.5"}, None) == "#8da3b7"

    def test_graph_colour(self):
        out, msgs = _noted(dr._dash_graph_color, "graphregion(color)", "bogus")
        assert out == "#000000" and len(msgs) == 1, msgs
        assert _noted(dr._dash_graph_color, "bgcolor", "#F00") == ("", [])

    @pytest.mark.parametrize("mode", MODES)
    def test_refline_colour(self, mode):
        d = _draw(tp._spec([plot_for("scatter")], None,
                           {"xline": "3000, lcolor(bogus)"}), mode)
        spans = [x for x in d.fig.center if isinstance(x, Span)]
        assert [s.line_color for s in spans] == ["#000000"]
        # Flipped (18oct2026): twoway's wording, which names the colour
        # and not the option.
        assert [m for m in d.warnings if "class color" in m] == [
            "dash: named style bogus not found in class color, default attributes "
            "used"]
        d = _draw(tp._spec([plot_for("scatter")], {"scheme": "s1rcolor"},
                           {"xline": "3000, lcolor(fg)"}), mode)
        spans = [x for x in d.fig.center if isinstance(x, Span)]
        assert [s.line_color for s in spans] == ["#ffffff"]


class TestTheKpiKeepsItsLeniency:
    def test_values_accepted_today_are_unchanged(self):
        """Guard: every KPI colour accepted before keeps its colour."""
        want = {"Navy": "#1a476f", "grey": "#808080", "dimgrey": "#e8e8e8",
                "bluishgrey": "#d9e6eb", "ltbluishgrey": "#eaf2f3",
                "#FFF": "#fff", "rebeccapurple": "rebeccapurple",
                "rgb(1,2,3)": "rgb(1,2,3)", "navy": "#1a476f"}
        got = {k: dr._resolve_kpi_color(k, "#d0d0d0", "color") for k in want}
        assert got == want

    def test_the_kpi_reads_the_grammar(self):
        got = {k: dr._resolve_kpi_color(k, "#d0d0d0", "color")
               for k in ("navy*.5", "hsv 240 1 1", "NAVY*.5")}
        assert got == {"navy*.5": "#8da3b7", "hsv 240 1 1": "#0000ff",
                       "NAVY*.5": "#8da3b7"}


# ---------------------------------------------------------------------------
# Drawn, in both modes and after a move
# ---------------------------------------------------------------------------

def _glyphs(d, cls):
    return [r.glyph for f in d.figures for r in drawn_renderers(f)
            if isinstance(r, GlyphRenderer) and type(r.glyph).__name__ == cls]


@pytest.mark.parametrize("mode", MODES)
class TestBothModes:
    def test_scatter_forms(self, mode):
        """One branch each: the grammar, unknown, malformed, opacity."""
        plots = [plot_for("scatter", {"mcolor": "navy*.5"}),
                 plot_for("scatter", {"mcolor": "bogus"}),
                 plot_for("scatter", {"mcolor": "red*abc"}),
                 plot_for("scatter", {"mcolor": "navy%50*.5"})]
        d = _draw(tp._spec(plots, None, {}), mode)
        got = [(str(g.fill_color).lower(), g.fill_alpha)
               for g in _glyphs(d, "Scatter")]
        p2 = d.scheme.p_colors[2]
        assert got == [("#8da3b7", 1.0), ("#000000", 1.0), (p2, 1.0),
                       ("#8da3b7", 0.5)], got
        # Flipped (18oct2026): twoway's wording, not dash's.
        assert [m for m in d.warnings if "class color" in m] == [
            "dash: named style bogus not found in class color, default attributes "
            "used"]

    def test_s1rcolor(self, mode):
        d = _draw(tp._spec([plot_for("scatter", {"mcolor": "fg"}),
                            plot_for("scatter", {"mcolor": "navy*.5"})],
                           {"scheme": "s1rcolor"}, {}), mode)
        assert [str(g.fill_color).lower() for g in _glyphs(d, "Scatter")] \
            == ["#ffffff", "#0d2438"]

    def test_a_user_scheme(self, mode, tmp_path, monkeypatch):
        name = _scheme_file(tmp_path, monkeypatch, "cguser",
                            ["color p1 navy*.5", "color background bogus"])
        d = _draw(tp._spec([plot_for("scatter")], {"scheme": name}, {}), mode)
        assert str(_glyphs(d, "Scatter")[0].fill_color).lower() == "#8da3b7"
        assert d.fig.border_fill_color == "#000000"

    @pytest.mark.parametrize("plot,go,read,want", [
        (("scatter", {"mcolor": "nosuchcolour"}), {},
         lambda d: [(str(g.fill_color).lower(), str(g.line_color).lower())
                    for g in _glyphs(d, "Scatter")],
         [("#000000", "#000000")]),
        (("line", {"lcolor": "nosuchcolour"}), {},
         lambda d: [str(g.line_color).lower() for g in _glyphs(d, "Line")],
         ["#000000"]),
        # Black at the area's fill intensity, as twoway's SVG has it.
        (("area", {"fcolor": "nosuchcolour"}), {},
         lambda d: [str(g.fill_color).lower() for g in _glyphs(d, "VArea")
                    + _glyphs(d, "Patch")][:1],
         ["#333333"]),
        (("scatter", {}), {"title": '"T", color(nosuchcolour)'},
         lambda d: str(d.fig.title.text_color).lower(), "#000000"),
    ], ids=["mcolor", "lcolor", "fcolor", "title_color"])
    def test_an_unknown_colour_is_noted_in_twoways_words(self, mode, plot,
                                                         go, read, want):
        """Measured 18oct2026 (StataNow 19.5, s2color): twoway draws an
        unknown colour name black -- marker fill and outline #000000, a
        line #000000, an area fill #333333 (black at the area's
        intensity), a title #000000 -- and notes "named style nosuchcolour
        not found in class color, default attributes used".  dash drew the
        same colours and noted "dash: mcolor(nosuchcolour) is not a
        recognised colour; using black." instead; it notes twoway's words
        after "dash: ", its note channel's mark."""
        d = _draw(tp._spec([plot_for(*plot)], None, go), mode)
        assert read(d) == want
        assert [m for m in d.warnings if "nosuchcolour" in m] == [
            "dash: named style nosuchcolour not found in class color, "
            "default attributes used"], d.warnings

    # Flipped (18oct2026, BUGS.md "mcolor(255 0,0) is refused where twoway
    # notes the named style and draws"): the renderer is handed one colour
    # -- dash.ado gives each y its own stylelist element, so mcolor(300 0 0)
    # reaches it as "300" -- and a colour holding blanks came quoted or as
    # a sub-option, which twoway names whole: mcolor("300 0 0") notes
    # "named style 300 0 0", title("T", color(red blue)) "named style red
    # blue", mcolor("red blue%50") "named style red blue".
    @pytest.mark.parametrize("value,named", [
        ("bogus%50", "bogus"), ("bogus*2", "bogus"), ("RED", "RED"),
        ("300 0 0", "300 0 0"), ("hsv 400 2 2", "hsv 400 2 2"),
        ("bogus foo", "bogus foo"), ("red blue%50", "red blue"),
        ("1 2*2", "1 2"),
    ])
    def test_the_note_names_what_twoway_names(self, mode, value, named):
        """twoway names the whole colour, its %# and *# left off (measured
        18oct2026: mcolor(bogus%50) notes "named style bogus",
        mcolor("hsv 400 2 2") "named style hsv 400 2 2")."""
        d = _draw(tp._spec([plot_for("scatter", {"mcolor": value})], None,
                           {}), mode)
        assert [m for m in d.warnings if "class color" in m] == [
            "dash: named style %s not found in class color, default "
            "attributes used" % named], d.warnings

    @pytest.mark.parametrize("plot,go,read,want,named", [
        (("scatter", {"mcolor": "1,,2"}), {}, "marker", "#000000", "1 2"),
        (("scatter", {"mcolor": "255,,0,,0"}), {}, "marker", "#ff0000", None),
        (("scatter", {"mcolor": ",,red"}), {}, "marker", "#ff0000", None),
        (("scatter", {"mcolor": "red,,blue"}), {}, "marker", "#000000",
         "red blue"),
        (("scatter", {"mcolor": "red*2,,blue"}), {}, "marker", "#1a476f",
         None),
        (("scatter", {}), {"title": '"T", color(1,,2)'}, "title", "#000000",
         "1 2"),
        (("scatter", {}), {"title": '"T", color(255,,0,,0)'}, "title",
         "#ff0000", None),
        (("scatter", {}), {"xline": "3000, lcolor(red,,blue)"}, "xline",
         "#000000", "red blue"),
    ], ids=["one_two", "rgb", "lead", "two_names", "keep", "title",
            "title_rgb", "xline"])
    def test_a_comma_colour_twoway_draws_is_its_blank_form(
            self, mode, plot, go, read, want, named):
        """Measured 18oct2026 (StataNow 19.5, s2color, SVG export): a
        colour written with commas that twoway does not refuse -- every
        second comma-separated part blank -- is drawn as its other parts
        joined by blanks: mcolor(255,,0,,0) and mcolor(,,red) red,
        mcolor(1,,2) black with "named style 1 2 not found",
        mcolor(red*2,,blue) as mcolor(red*2 blue), the scheme's #1a476f
        without a note; on a title and an xline alike."""
        d = _draw(tp._spec([plot_for(*plot)], None, go), mode)
        got = {
            "marker": lambda: str(_glyphs(d, "Scatter")[0].fill_color),
            "title": lambda: str(d.fig.title.text_color),
            "xline": lambda: str([x.line_color for x in d.fig.center
                                  if isinstance(x, Span)][0]),
        }[read]().lower()
        assert got == want
        assert [m for m in d.warnings if "class color" in m] == (
            ["dash: named style %s not found in class color, default "
             "attributes used" % named] if named else []), d.warnings

    @pytest.mark.parametrize("go,read,want,named", [
        ({"title": '"T", color("1 2 3")'}, "title", "#010203", None),
        ({"title": '"T", color(`"1 2 3"\')'}, "title", "#010203", None),
        ({"xline": '3000, lcolor("1 2 3")'}, "xline", "#010203", None),
        ({"title": '"T", color("1,,2")'}, "title", "#000000", "1 2"),
        ({"title": '"T", color("bogus")'}, "title", "#000000", "bogus"),
    ], ids=["title", "compound", "xline", "commas", "unknown"])
    def test_a_quoted_sub_option_colour_is_its_text(self, mode, go, read,
                                                    want, named):
        """Measured 18oct2026 (StataNow 19.5, s2color, SVG export;
        test/fixtures/colour_width_edges_truth.json sp.title.color):
        title("T", color("1 2 3")), its compound-quoted form and
        xline(3000, lcolor("1 2 3")) draw #010203; color("1,,2") notes
        "named style 1 2" and color("bogus") "named style bogus", without
        the quotes.  dash drew them black, noting the quoted text."""
        d = _draw(tp._spec([plot_for("scatter")], None, go), mode)
        got = {
            "title": lambda: str(d.fig.title.text_color),
            "xline": lambda: str([x.line_color for x in d.fig.center
                                  if isinstance(x, Span)][0]),
        }[read]().lower()
        assert got == want
        assert [m for m in d.warnings if "class color" in m] == (
            ["dash: named style %s not found in class color, default "
             "attributes used" % named] if named else []), d.warnings

    def test_the_site_probes(self, mode):
        """The fixture's site probes dash owns: lines, bars, titles,
        reference lines and the graph region, as twoway drew them."""
        probes = _truth()["probes"]
        cases = {
            "site_01": ([plot_for("line", {"lcolor": "navy*.5"})], {},
                        lambda d: _glyphs(d, "Line")[0].line_color),
            "site_02": ([plot_for("line", {"lcolor": "bogus"})], {},
                        lambda d: _glyphs(d, "Line")[0].line_color),
            "site_03": ([plot_for("bar", {"lcolor": "none",
                                          "fcolor": "bogus"})], {},
                        lambda d: _glyphs(d, "VBar")[0].fill_color),
            "site_04": ([plot_for("bar", {"lcolor": "none",
                                          "color": "navy*.5"})], {},
                        lambda d: _glyphs(d, "VBar")[0].fill_color),
            "site_05": ([plot_for("scatter")], {"title": '"T", color(bogus)'},
                        lambda d: d.fig.title.text_color),
            "site_06": ([plot_for("scatter")],
                        {"title": '"T", color(navy*.5)'},
                        lambda d: d.fig.title.text_color),
            "site_07": ([plot_for("scatter")], {"xline": "3000, lcolor(bogus)"},
                        lambda d: [x.line_color for x in d.fig.center
                                   if isinstance(x, Span)][0]),
            "site_08": ([plot_for("scatter")],
                        {"graphregion": "color(bogus)"},
                        lambda d: d.fig.border_fill_color),
        }
        bad = []
        for pid, (plots, go, read) in cases.items():
            p = probes[pid]
            want = p["fill"] or (p["region"] if pid == "site_08"
                                 else p["vstrokes"][0])
            got = str(read(_draw(tp._spec(plots, None, go), mode))).lower()
            if got != want:
                bad.append(f"{pid} {p['command']}: dash {got}, twoway {want}")
        assert not bad, "\n".join(bad)


class TestAfterAFilterMove:
    def test_the_served_app_redraws_the_same_colours(self, tmp_path,
                                                     monkeypatch):
        import test_served_linked_views as lv
        name = _scheme_file(tmp_path, monkeypatch, "cgmove",
                            ["color p1 navy*.5"])
        graphs = [lv._graph("g1", [plot_for("scatter",
                                            {"mcolor": "navy*.5%50"})]),
                  lv._graph("g2", [plot_for("scatter")])]
        spec = lv._spec(graphs, [lv._filter("dropdown")], link="")
        spec["build_options"]["scheme"] = name
        doc = lv._served_doc(tmp_path, spec)

        def fills():
            return sorted({(str(r.glyph.fill_color).lower(),
                            r.glyph.fill_alpha)
                           for r in doc.select({"type": GlyphRenderer})
                           if type(r.glyph).__name__ == "Scatter"})

        before = fills()
        assert before == [("#8da3b7", 0.5), ("#8da3b7", 1.0)], before
        lv._fire(doc, "foreign", "1")
        assert fills() == before

    def test_the_saved_page_writes_only_build_colours(self):
        spec = tp._spec([plot_for("scatter")], None, {},
                        kpis=[tp._kpi(color="navy*.5")])
        d = _draw(spec, "standalone")
        assert any("#8da3b7" in c for c in d.page.split("kpi")[1:]) or \
            "#8da3b7" in d.page
        for f in d.figures:
            for m in f.references():
                if isinstance(m, CustomJS):
                    assert "navy*.5" not in m.code
                    assert "navy*.5" not in json.dumps(
                        {k: str(v) for k, v in m.args.items()})


# ---------------------------------------------------------------------------
# The scheme extractor
# ---------------------------------------------------------------------------

class TestExtractorAgrees:
    def test_the_intensity_rule(self):
        import extract_scheme_truth as ex
        bad = []
        for nw in (True, False):
            for c in (0, 1, 26, 71, 111, 128, 255):
                for f in (0, .01, .5, 1, 1.5, 2, 10, 51, 100, 255):
                    rgb = (c, 255 - c, min(255, c + 40))
                    hx = "#%02x%02x%02x" % rgb
                    a = "#%02x%02x%02x" % tuple(ex._apply_intensity(
                        rgb, f, naturally_white=nw))
                    b = dr.GlyphMapper._blend_intensity(hx, f, nw)
                    if a != b:
                        bad.append(f"{hx}*{f} nw={nw}: {a} != {b}")
        assert not bad, "\n".join(bad[:20])

    def test_the_resolver(self):
        import extract_scheme_truth as ex
        base = ex.DEFAULT_STATA_BASE
        if not os.path.isdir(os.path.join(base, "style")):
            pytest.skip("Stata's ado/base is not installed here")
        res = ex.ColorResolver(ex.SchemeResolver(base))
        want = {"navy*.5": "#8da3b7", "0 0 0 255": "#000000",
                "hsv 240 1 1": "#0000ff", "0 255 255 0": "#ff0000",
                "1,2,3,4": "#faf9f8", "navy*1.5": "#112f4a",
                "Navy": None, "bogus": None}
        got = {k: res.resolve_with_opacity(k)[0] for k in want}
        got = {k: (v.lower() if v else v) for k, v in got.items()}
        assert got == want


# ---------------------------------------------------------------------------
# dash.ado refuses a comma-written plot colour
# ---------------------------------------------------------------------------

class TestTheCommaIsRefusedInStata:
    def test_the_rules_name_the_colour_kind(self):
        with open(os.path.join(_ROOT, "dash.ado"), encoding="utf-8") as fh:
            ado = fh.read()
        for opt in ("mcolor", "mfcolor", "mlcolor", "mlabcolor", "lcolor",
                    "fcolor", "color", "acolor", "alcolor", "bfcolor",
                    "blcolor", "clcolor"):
            assert re.search(rf"\b{opt}=colour\b", ado), opt
        assert '"`kind\'" == "colour"' in ado
