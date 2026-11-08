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
          "align", "location", "start", "end", "ticks")


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
