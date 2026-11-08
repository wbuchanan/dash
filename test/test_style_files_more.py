"""Style files and schemes as twoway finds them (WP-45 section 45-03).

twoway resolves a style name of any class through findfile: a
``linewidth-zqw.style`` holding ``set val 2`` on the ado-path makes
``lwidth(zqw)`` draw as ``lwidth(2)``, with no note (ST-7).  Every
expectation is twoway's, measured in StataNow 19.5 by
scripts/extract_style_leaf_truth.do into test/fixtures/style_leaf_truth.json:
each ``L_<class>`` record is a draw with the file's name and a draw with its
value typed, whose exported SVGs are the same picture.  The files are the
fixture's own, written to a directory the spec passes as its ado-path.
"""

from __future__ import annotations

import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
import test_scheme_resolution as tsr  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

SP = dr.SchemeParser
T = dr.OptionTranslator
MODES = tsr.MODES

with open(os.path.join(_HERE, "fixtures", "style_leaf_truth.json"),
          encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)


def _files_dir(tmp_path):
    """The fixture's style and scheme files in a directory of their own."""
    d = tmp_path / "ado"
    d.mkdir(exist_ok=True)
    for name, text in TRUTH["files"].items():
        if "/" in name:
            continue
        (d / name).write_text(text, encoding="utf-8")
    return str(d)


#: The visual attributes a draw is compared on, wherever a model has them.
_ATTRS = ("line_dash", "line_width", "line_color", "line_alpha",
          "fill_color", "fill_alpha", "hatch_alpha", "size", "angle",
          "text_font_size", "text_color", "text_alpha", "text_align",
          "text_baseline", "x_offset", "y_offset", "min_border_left",
          "min_border_right", "min_border_top", "min_border_bottom",
          "align", "location", "start", "end", "ticks", "spacing", "ncols",
          "nrows", "label_width", "orientation")


def _sig(drawn):
    """Every model's visual attributes, ids left out, as a sorted list."""
    out = []
    for f in drawn.figures:
        for m in f.references():
            row = []
            for a in _ATTRS:
                if a in m.properties():
                    v = getattr(m, a, None)
                    row.append((a, repr(v)))
            if row:
                out.append((type(m).__name__, tuple(row)))
    return sorted(out)


def _drawn(plots, graph, mode, dirs):
    b = {"scheme": "s2color", "scheme_dirs": list(dirs)}
    return tsr._draw(tp._spec(list(plots), b, graph or {}), mode)


def _notes(d):
    return [m for m in d.msgs if "dash" in m] if hasattr(d, "msgs") else \
        [m for m in d.warnings if m.startswith("dash")]


#: (fixture key, probe (plots, graph options), reference) in dash's spec
#: form: each probe names the fixture's file, each reference types its value
#: as twoway's reference draw typed it.
def _sc(**o):
    return [plot_for("scatter", o)]


def _ln(**o):
    return [plot_for("line", o)]


LEAF = {
    "L_linepattern_b": ((_ln(lpattern="zqpb"), {}),
                        (_ln(lpattern="longdash_dot"), {})),
    "L_linewidth": ((_ln(lwidth="zqw"), {}), (_ln(lwidth="2"), {})),
    "L_symbolsize": ((_sc(msize="zqs"), {}), (_sc(msize="5"), {})),
    "L_gsize": ((_sc(), {"title": '"T", size(zqg)'}),
                (_sc(), {"title": '"T", size(10)'})),
    "L_gsize_pt": ((_sc(), {"title": '"T", size(zqp)'}),
                   (_sc(), {"title": '"T", size(18pt)'})),
    "L_mlabsize": ((_sc(mlabel="mpg", mlabsize="zqg"), {}),
                   (_sc(mlabel="mpg", mlabsize="10"), {})),
    "L_intensity": (([plot_for("bar", {"fintensity": "zqi"})], {}),
                    ([plot_for("bar", {"fintensity": "30"})], {})),
    "L_anglestyle": ((_sc(mlabel="mpg", mlabangle="zqa"), {}),
                     (_sc(mlabel="mpg", mlabangle="30"), {})),
    "L_msangle": ((_sc(msymbol="T", msangle="zqa"), {}),
                  (_sc(msymbol="T", msangle="30"), {})),
    "L_margin": ((_sc(), {"plotregion": "margin(zqm)"}),
                 (_sc(), {"plotregion": "margin(5 5 5 5)"})),
    "L_margin_n": ((_sc(), {"plotregion": "margin(zqn)"}),
                   (_sc(), {"plotregion": "margin(2 4 8 6)"})),
}


class TestTheFixture:
    def test_meta(self):
        assert sorted(TRUTH["_meta"]) == ["born_date", "dash_commit",
                                          "extracted", "source",
                                          "stata_version"]

    def test_twoway_draws_each_file_as_its_value(self):
        for k in list(LEAF) + ["L_color", "L_lcolor", "L_textboxstyle",
                               "L_mlabtextstyle"]:
            rec = TRUTH[k]
            assert rec["rc"] == 0 and not rec["notes"], k
            assert rec["same_as_reference"] == 1, k
        assert TRUTH["L_linepattern"]["same_as_solid"] == 0


class TestLeafFiles:
    """ST-7: the seven leaf classes (linepattern, linewidth, symbolsize,
    gsize, intensity, anglestyle, margin) read from their files."""

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("key", sorted(LEAF))
    def test_class(self, key, mode, tmp_path):
        d = _files_dir(tmp_path)
        (pp, pg), (rp, rg) = LEAF[key]
        probe = _drawn(pp, pg, mode, (d,))
        ref = _drawn(rp, rg, mode, (d,))
        assert not _notes(probe), (key, _notes(probe))
        assert _sig(probe) == _sig(ref), key

    @pytest.mark.parametrize("mode", MODES)
    def test_class_linepattern(self, mode, tmp_path):
        """``set pattern "4 1 1 1"``: four relative units on, one off, one
        on, one off -- not solid (twoway's draw is not its solid one)."""
        d = _files_dir(tmp_path)
        probe = _drawn(_ln(lpattern="zqpat"), {}, mode, (d,))
        assert not _notes(probe), _notes(probe)
        unit = T.PT_PER_RS * T.PX_PER_PT
        want = [max(1, int(round(n * unit))) for n in (4, 1, 1, 1)]
        dashes = [list(r.glyph.line_dash) for f in probe.figures
                  for r in f.renderers if hasattr(r, "glyph")
                  and hasattr(r.glyph, "line_dash")]
        assert want in dashes, dashes

    def test_an_unknown_name_is_still_noted(self, tmp_path):
        d = _files_dir(tmp_path)
        probe = _drawn(_ln(lwidth="zqnofile"), {}, "standalone", (d,))
        assert any("zqnofile" in m for m in _notes(probe))


class TestTheLeafReader:
    """``SchemeParser.leaf_value`` and its helpers (WP-45 ST-7)."""

    def test_leaf_value(self, tmp_path):
        sp = SP("s2color", ado_dirs=(_files_dir(tmp_path),))
        got = {(c, n): sp.leaf_value(c, n) for c, n in (
            ("linepattern", "zqpat"), ("linewidth", "zqw"),
            ("symbolsize", "zqs"), ("gsize", "zqg"), ("gsize", "zqp"),
            ("intensity", "zqi"), ("anglestyle", "zqa"),
            ("margin", "zqn"), ("linewidth", "nofile"),
            ("seriesstyle", "zqw"), ("linewidth", "../x"))}
        assert got == {
            ("linepattern", "zqpat"): "4 1 1 1", ("linewidth", "zqw"): "2",
            ("symbolsize", "zqs"): "5", ("gsize", "zqg"): "10",
            ("gsize", "zqp"): "18pt", ("intensity", "zqi"): "30",
            ("anglestyle", "zqa"): "30", ("margin", "zqn"): "2 4 8 6",
            ("linewidth", "nofile"): None, ("seriesstyle", "zqw"): None,
            ("linewidth", "../x"): None}

    def test_leaf_native(self):
        sp = SP("s2color")
        assert sp._leaf_native("linewidth", "thick")
        assert sp._leaf_native("linepattern", "-.")
        assert sp._leaf_native("margin", "medium")
        assert sp._leaf_native("gsize", "2")
        assert not sp._leaf_native("linewidth", "zqw")

    def test_the_module_lookup(self, tmp_path):
        sp = SP("s2color", ado_dirs=(_files_dir(tmp_path),))
        old = dr._DASH_LEAF_SOURCE[0]
        try:
            dr._DASH_LEAF_SOURCE[0] = None
            assert dr._dash_leaf_value("linewidth", "zqw") is None
            dr._DASH_LEAF_SOURCE[0] = sp
            assert dr._dash_leaf_value("linewidth", "zqw") == "2"
        finally:
            dr._DASH_LEAF_SOURCE[0] = old

    @pytest.mark.parametrize("mode", MODES)
    def test_rows_travel(self, mode, tmp_path):
        """The rows read at registration draw on a host without the files
        (``style_rows_for_spec`` -> ``build_options["_style_rows"]``)."""
        d = _files_dir(tmp_path)
        plots = _ln(lwidth="zqw", lpattern="zqpb")
        go = {"title": '"T", size(zqg)', "plotregion": "margin(zqn)"}
        rows = SP.style_rows_for_spec(tp._spec(plots, {}, go), (d,))
        assert {"linewidth zqw", "linepattern zqpb", "gsize zqg",
                "margin zqn"} <= set(rows)
        assert dr._dash_style_rows_of({"_style_rows": rows}).keys() == \
            rows.keys()
        b = {"scheme": "s2color", "scheme_dirs": [], "_style_rows": rows}
        probe = tsr._draw(tp._spec(plots, b, go), mode)
        ref = _drawn(_ln(lwidth="2", lpattern="longdash_dot"),
                     {"title": '"T", size(10)',
                      "plotregion": "margin(2 4 8 6)"}, mode, ())
        assert not _notes(probe), _notes(probe)
        assert _sig(probe) == _sig(ref)


#: ST-15's probes: a color-zqc.style (set rgb "200 30 40") and a
#: textboxstyle-zqt.style (heading's lines with set size huge and set
#: color red), each against its value typed.
COLOUR_TEXTBOX = {
    "L_color": ((_sc(mcolor="zqc"), {}), (_sc(mcolor='"200 30 40"'), {})),
    "L_lcolor": ((_ln(lcolor="zqc"), {}), (_ln(lcolor='"200 30 40"'), {})),
    "L_textboxstyle": ((_sc(), {"title": '"T", tstyle(zqt)'}),
                       (_sc(), {"title": '"T", size(huge) color(red)'})),
    "L_mlabtextstyle": ((_sc(mlabel="mpg", mlabtextstyle="zqt"), {}),
                        (_sc(mlabel="mpg", mlabsize="huge",
                             mlabcolor="red"), {})),
}


class TestColourAndTextboxFiles:
    """ST-15: color-*.style and textboxstyle-*.style files are read."""

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("key", sorted(COLOUR_TEXTBOX))
    def test_class(self, key, mode, tmp_path):
        d = _files_dir(tmp_path)
        (pp, pg), (rp, rg) = COLOUR_TEXTBOX[key]
        probe = _drawn(pp, pg, mode, (d,))
        ref = _drawn(rp, rg, mode, (d,))
        assert not _notes(probe), (key, _notes(probe))
        assert _sig(probe) == _sig(ref), key


def _base_like(tmp_path):
    """A directory BASE-like for the walk: its s/ holds Stata's
    scheme.class (the class that reads every scheme), as BASE's does."""
    b = tmp_path / "base"
    (b / "s").mkdir(parents=True, exist_ok=True)
    (b / "s" / "scheme.class").write_text("* stand-in\n", encoding="utf-8")
    return str(b)


def _order_dir(tmp_path):
    d = tmp_path / "order"
    d.mkdir(exist_ok=True)
    (d / "scheme-economist.scheme").write_text(
        TRUTH["files"]["ORDER/scheme-economist.scheme"], encoding="utf-8")
    return str(d)


class TestShippedNameOrder:
    """ST-10: findfile's first hit decides; a shipped name's translation
    stands at BASE's place on the ado-path (S_order: before BASE twoway
    draws the user's file, s2color with red markers; after it, its own)."""

    def test_the_fixture(self):
        o = TRUTH["S_order"]
        assert o["find_before"] == "ORDER/scheme-economist.scheme"
        assert o["find_after"] == "BASE/scheme-economist.scheme"
        assert o["before"]["same_as_s2color_mcolor_red"] == 1
        assert o["after"]["same_as_native"] == 1

    def test_before_and_after_base(self, tmp_path):
        u, b = _order_dir(tmp_path), _base_like(tmp_path)
        before = SP("economist", ado_dirs=(u, b))
        after = SP("economist", ado_dirs=(b, u))
        native = SP("economist")
        s2 = SP("s2color")
        assert os.path.dirname(before._resolve_path("economist")) == \
            os.path.realpath(u)
        assert before.default_color(0, "scatter") == "#ff0000"
        assert before.css_block() != native.css_block()
        assert before._props.get("color background") == \
            s2._props.get("color background")
        assert after._resolve_path("economist") == \
            native._resolve_path("economist")
        assert after.default_color(0, "scatter") == \
            native.default_color(0, "scatter")

    @pytest.mark.parametrize("mode", MODES)
    def test_drawn(self, mode, tmp_path):
        u, b = _order_dir(tmp_path), _base_like(tmp_path)
        d = tsr._draw(tp._spec(_sc(), {"scheme": "economist",
                                       "scheme_dirs": [u, b]}, {}), mode)
        ref = tsr._draw(tp._spec(_sc(mcolor="red"), {"scheme": "s2color"},
                                 {}), mode)
        assert _sig(d) == _sig(ref)

    def test_a_same_name_include_reads_the_translation(self, tmp_path):
        """A user's scheme-economist.scheme that includes economist reads
        dash's translation there, never itself (the loop guard)."""
        u, b = tmp_path / "u", _base_like(tmp_path)
        u.mkdir()
        (u / "scheme-economist.scheme").write_text(
            "#include economist\ncolor p1 red\n", encoding="utf-8")
        sp = SP("economist", ado_dirs=(str(u), b))
        native = SP("economist")
        assert sp.default_color(0, "scatter") == "#ff0000"
        assert sp._props.get("color background") == \
            native._props.get("color background")


def _two(o1=None, o2=None):
    return [plot_for("scatter", dict(o1 or {})),
            plot_for("scatter", dict(o2 or {}), yvar="price")]


#: ST-17's directives (D_ records), each a user scheme w45<x>.scheme
#: (#include s2color plus one line) against s2color with the option the
#: directive stands for: (scheme, plots, graph options) probe, then
#: reference.
DIRECTIVES = {
    "D_clockdir_p": (("w45p", _sc(mlabel="mpg"), {}),
                     ("s2color", _sc(mlabel="mpg", mlabposition="9"), {})),
    "D_clockdir_p2": (("w45q", _two({"mlabel": "mpg"}, {"mlabel": "mpg"}),
                       {}),
                      ("s2color", _two({"mlabel": "mpg"},
                                       {"mlabel": "mpg",
                                        "mlabposition": "9"}), {})),
    "D_textboxstyle": (("w45t", _sc(), {"title": '"T"'}),
                       ("s2color", _sc(),
                        {"title": '"T", size(medium) color(black)'})),
    "D_legend_col_gap": (("w45g", _two(), {"legend": "cols(2)"}),
                         ("s2color", _two(),
                          {"legend": "cols(2) colgap(huge)"})),
    "D_title_position": (("w45c", _sc(), {"title": '"T"'}),
                         ("s2color", _sc(), {"title": '"T", position(3)'})),
}


class TestDirectives:
    """ST-17: a user scheme's clockdir p and p#, textboxstyle title,
    legend_col_gap and title_position, drawn as twoway draws them."""

    def test_the_fixture(self):
        for k in DIRECTIVES:
            r = TRUTH[k]
            assert r["rc"] == 0 and not r["notes"], k
            assert r["same_as_reference"] == 1, k
        # yesno plabelboxed draws nothing on a twoway graph (measured):
        # the same picture as s2color's, so nothing is drawn for it.
        assert TRUTH["D_plabelboxed"]["same_as_base"] == 1

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("key", sorted(DIRECTIVES))
    def test_directive(self, key, mode, tmp_path):
        d = _files_dir(tmp_path)
        (ps, pp, pg), (rs, rp, rg) = DIRECTIVES[key]
        probe = tsr._draw(tp._spec(pp, {"scheme": ps, "scheme_dirs": [d]},
                                   pg), mode)
        ref = tsr._draw(tp._spec(rp, {"scheme": rs, "scheme_dirs": [d]},
                                 rg), mode)
        assert not _notes(probe), (key, _notes(probe))
        assert _sig(probe) == _sig(ref), key

    @pytest.mark.parametrize("mode", MODES)
    def test_plabelboxed_draws_nothing(self, mode, tmp_path):
        d = _files_dir(tmp_path)
        probe = tsr._draw(tp._spec(_sc(mlabel="mpg"), {
            "scheme": "w45b", "scheme_dirs": [d]}, {}), mode)
        ref = tsr._draw(tp._spec(_sc(mlabel="mpg"), {
            "scheme": "s2color", "scheme_dirs": [d]}, {}), mode)
        assert _sig(probe) == _sig(ref)

    def test_p_clock(self, tmp_path):
        d = _files_dir(tmp_path)
        p = SP("w45p", ado_dirs=(d,))
        q = SP("w45q", ado_dirs=(d,))
        assert [p.p_clock(i) for i in (0, 1)] == ["9", "9"]
        assert [q.p_clock(i) for i in (0, 1)] == [None, "9"]
        assert SP("s2color").p_clock(0) is None

    def test_the_box_styles(self, tmp_path):
        d = _files_dir(tmp_path)
        t = SP("w45t", ado_dirs=(d,))
        s2 = SP("s2color")
        assert (t.title_font_size, t.title_color) == s2.textbox_style(
            "subheading")
        assert (s2.title_font_size, s2.title_color) == (
            s2.heading_font_size, s2.title_color)
        assert (s2.subtitle_font_size, s2.caption_font_size) == (
            s2.subheading_font_size, s2.body_font_size)

    def test_the_guards_are_documented(self):
        """D-45-03.d: the path, size and link guards stay, stated in the
        scheme section and in one Differences entry linking to it."""
        with open(os.path.join(os.path.dirname(_HERE), "dash.sthlp"),
                  encoding="utf-8") as fh:
            h = " ".join(fh.read().split())

        def _between(text, a, b):
            i = text.index(a)
            return text[i:text.index(b, i)]

        para = _between(h, "Four things differ from {cmd:twoway}, for "
                           "safety", "and {cmd:s2color} is drawn.")
        assert "a scheme is a name, never a path" in para
        assert "at most 1,048,576 bytes" in para
        assert "a link out of that directory is not followed" in para
        diff = _between(h, "{ul:Scheme and style files are read with safety "
                           "bounds.}", "{marker subcommands}")
        assert "{help dash##scheme:Stata scheme support}" in diff
        assert "over 1,048,576 bytes" in diff


def _ado():
    with open(os.path.join(os.path.dirname(_HERE), "dash.ado"),
              encoding="utf-8") as fh:
        return fh.read()


class TestUnknownScheme:
    """ST-16: an unknown graph-level scheme() draws s2color with twoway's
    note (U_unknown, U_path: rc 0, "(note: scheme <name> not found, using
    s2color)", the same SVG as s2color's); dash build's and dash serve's
    scheme() keep their refusal."""

    def test_the_fixture(self):
        for k, name in (("U_unknown", "nosuchscheme"), ("U_path", "../nosuch")):
            r = TRUTH[k]
            assert r["rc"] == 0 and r["same_as_s2color"] == 1, k
            assert r["notes"] == ["(note: scheme %s not found, using "
                                  "s2color)" % name], k

    def test_ado_text(self):
        src = _ado()
        i = src.index('else if "`kind\'" == "scheme" {')
        body = src[i:src.index('else if "`kind\'" == "format" {', i)]
        # The graph option's kind notes in twoway's words and draws s2color.
        assert '"(note: scheme ", st_strscalar(st_local("T")), " not found, ' \
            'using s2color)"' in body
        assert 'local norm "s2color"' in body
        # dash build's and dash serve's check stays a refusal.
        assert ('_dash_validate_value "`cmdname\'" "scheme" "scheme,strict" '
                '`"`macval(scheme)\'"\' ""') in src
