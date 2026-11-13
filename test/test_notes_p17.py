"""Notes for options twoway draws the same picture with (WP-49 49-02).

basic:PT-12: an option or sub-option twoway takes, draws the same picture
with and prints no note for is taken in silence.  The measurement is
test/fixtures/noted_option_truth.json (scripts/extract_noted_option_truth.do):
its ``probes`` for the plot-type options, its ``sub_probes`` for the
sub-options of graph options.  scripts/gen_twoway_takes_table.py writes
the silent rows twice -- dash_parse.mata's ``_dash_tw_silent_tab()`` and
``_dash_tw_silent_sub_tab()``, and dash_render.py's
``_DASH_TW_SILENT_SUB`` -- and these tests hold the blocks to the fixture
and the renderer's sub-option report to the rows, in both modes.
"""
import json
import os
import re
import subprocess
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_FIX = os.path.join(_HERE, "fixtures", "noted_option_truth.json")
with open(_FIX, encoding="utf-8") as _fh:
    _NOTED = json.load(_fh)
_GEN = os.path.join(_ROOT, "scripts", "gen_twoway_takes_table.py")


def _mata_sub_rows():
    with open(os.path.join(_ROOT, "dash_parse.mata"), encoding="utf-8") as fh:
        text = fh.read()
    block = text.split("// BEGIN tw_silent_sub", 1)[1].split(
        "// END tw_silent_sub", 1)[0]
    return re.findall(r'\("([^"]*)", "([^"]*)", "([^"]*)"\)', block)


class TestTheSilentTables:
    def test_blocks_are_current(self):
        """The generator's --check: every silent row, in both files, is
        the fixture's."""
        env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
        res = subprocess.run([sys.executable, _GEN, "--check"], env=env,
                             capture_output=True, text=True, timeout=120)
        assert res.returncode == 0, res.stderr

    def test_mata_and_python_agree(self):
        assert _mata_sub_rows(), "no tw_silent_sub row in dash_parse.mata"
        assert sorted(_mata_sub_rows()) == sorted(dr._DASH_TW_SILENT_SUB)

    def test_each_sub_row_was_measured_silent(self):
        """A row holds only where every probe of it drew twoway's picture
        with no note."""
        for opt, sub, _ty in dr._DASH_TW_SILENT_SUB:
            probes = [p for p in _NOTED["sub_probes"].values()
                      if p["option"] == opt and p["suboption"] == sub]
            assert probes, (opt, sub)
            for p in probes:
                assert (p["twoway_rc"], p["twoway_draws"], p["twoway_notes"]) \
                    == (0, False, []), p["cmd"]


# The graph options that put each silent sub-option on a scatter, and the
# option whose sub-option report would name it.  text() and subtitle() are
# read by dash.ado (_dash_added_text) or drawn, so the renderer reports
# nothing for them; their rows are certified by
# test_twoway_option_parity.cscript:Q4902-3 and S02's blocks.
_ROW_SPECS = {
    ("by", "spacers"): ({"by": "foreign, spacers(ring(2))"}, "by"),
    ("legend", "angle"): ({"legend": "angle(45)"}, "legend"),
    ("legend", "nodrawview"): ({"legend": "nodrawview"}, "legend"),
    ("legend", "nostack"): ({"legend": "nostack"}, "legend"),
    ("legend", "orientation"): ({"legend": "orientation(vertical)"}, "legend"),
    ("legend", "styleonly"): ({"legend": "styleonly"}, "legend"),
    ("subtitle", "width"): ({"by": "foreign", "subtitle": ", width(20)"},
                            "subtitle"),
    ("text", "angle"): (None, "text"),
    ("title", "angle"): ({"title": "T, angle(45)"}, "title"),
    ("title", "astextbox"): ({"title": "T, astextbox"}, "title"),
    ("xscale", "nolog"): ({"xscale": "nolog"}, "xscale"),
    ("ylabel", "labelkeepleadingzero"): (
        {"ylabel": "10(10)30, labelkeepleadingzero"}, "ylabel"),
    ("yscale", "noreverse"): ({"yscale": "noreverse"}, "yscale"),
    ("yscale", "ring"): ({"yscale": "ring(3)"}, "yscale"),
}


def _plots(go):
    if go and "by" in go:
        return [plot_for("scatter", yvar="mpg", xvar="weight")]
    return [plot_for("scatter")]


def _named(warns, option, sub):
    """The sub-option reports for *option* that name *sub*."""
    return [w for w in warns if f"{option}() sub-option" in w and sub in w]


def _sub_ids():
    return ["%s-%s" % (o, s) for o, s, _t in dr._DASH_TW_SILENT_SUB]


class TestSilentRows:
    def test_every_row_has_a_spec(self):
        missing = [(o, s) for o, s, _t in dr._DASH_TW_SILENT_SUB
                   if (o, s) not in _ROW_SPECS]
        assert not missing, missing

    @pytest.mark.parametrize("mode", ["saved", "served"])
    @pytest.mark.parametrize("row", [(o, s) for o, s, _t in dr._DASH_TW_SILENT_SUB],
                             ids=_sub_ids())
    def test_each_sub_row_is_silent(self, mode, row):
        go, option = _ROW_SPECS[row]
        if go is None:
            assert dr._dash_silent_subopt(option, row[1] + "(45)")
            return
        spec = tp._spec(_plots(go), None, go)
        warns = tp._standalone(spec)[1] if mode == "saved" else tp._served(spec)[1]
        assert not _named(warns, option, row[1]), warns


class TestSubOptionSilence:
    @pytest.mark.parametrize("mode", ["saved", "served"])
    @pytest.mark.parametrize("go,option,sub", [
        ({"legend": "nostack"}, "legend", "nostack"),
        ({"xscale": "nolog"}, "xscale", "nolog"),
        ({"ylabel": "10(10)30, labelkeepleadingzero"}, "ylabel",
         "labelkeepleadingzero"),
    ], ids=["legend_nostack", "xscale_nolog", "labelkeepleadingzero"])
    def test_named_words_twoway_draws_the_same_are_silent(self, mode, go,
                                                          option, sub):
        spec = tp._spec(_plots(go), None, go)
        warns = tp._standalone(spec)[1] if mode == "saved" else tp._served(spec)[1]
        assert not [w for w in warns if "sub-option" in w], warns

    def test_an_abbreviation_is_read_as_twoway_reads_it(self):
        """legend(orient(vertical)) is orientation() (its shortest
        spelling), xscale(nolog) whole."""
        assert dr._dash_silent_subopt("legend", "orient(vertical)")
        assert not dr._dash_silent_subopt("legend", "ori(vertical)")
        assert dr._dash_silent_subopt("xscale", "nolog")

    def test_a_word_with_no_row_is_still_named(self):
        """xscale(noreverse) was not measured: it keeps its report; a
        nested option has no rows."""
        assert not dr._dash_silent_subopt("xscale", "noreverse")
        assert not dr._dash_silent_subopt("legend(region)", "angle(45)")
        with pytest.warns(UserWarning, match=r"xscale\(\) sub-option.*noreverse"):
            dr._dash_report_suboptions("xscale", ["nolog", "noreverse"])


# LT-25: a named-style note is twoway's sentence -- "named style <v> not
# found in class <cls>, default attributes used", with no "dash:" before
# it -- printed as many times as twoway prints it
# (noted_option_truth.json lt25).
_LT25 = _NOTED["lt25"]


def _twoway_line(key):
    return _LT25[key]["twoway_notes"][0][len("(note: "):-1]


def _printed(warns):
    """The notes as printed (_dash_emit_note, its "(note:  " and ")"
    off): a named-style note loses dash's mark."""
    return [dr._dash_emit_note(w, sfi=False)[len("(note:  "):-1] for w in warns]


class TestNamedStyleNotes:
    def test_class_worded_note_has_no_prefix(self):
        """title("T", color(bogus)): twoway's line, no "dash:" (R_tcol)."""
        spec = tp._spec([plot_for("scatter")], None,
                        {"title": "T, color(bogus)"})
        for warns in (tp._standalone(spec)[1], tp._served(spec)[1]):
            assert _twoway_line("R_tcol") in _printed(warns), warns
            assert not [w for w in _printed(warns)
                        if w.startswith("dash: named style")]

    def test_the_gsize_note_replaces_dashs_words(self):
        """title("T", size(bogus)): the gsize note (R_tsz), not "is not
        a recognised size"."""
        spec = tp._spec([plot_for("scatter")], None,
                        {"title": "T, size(bogus)"})
        for warns in (tp._standalone(spec)[1], tp._served(spec)[1]):
            assert _twoway_line("R_tsz") in _printed(warns), warns
            assert not [w for w in warns if "not a recognised size" in w]

    def test_printed_twice_when_twoway_does(self):
        """times=2 prints the line twice in one render, as twoway prints
        title position(13)'s clockdir note (R_tpos)."""
        import warnings
        dr._DASH_NOTED.clear()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr._dash_style_note("title(position)", "13", "clock position",
                                cls="clockdir", times=2)
        got = [str(w.message) for w in caught]
        assert _printed(got) == [_twoway_line("R_tpos")] * 2, got
        assert len(set(got)) == 2, "the two copies must not merge"
        printed = [dr._dash_emit_note(g, sfi=False) for g in got]
        assert printed == ["(note:  %s)" % _twoway_line("R_tpos")] * 2

    def test_markup_value_is_inert(self):
        """A value with markup is shown as printable text, cut to 80; the
        class is never the user's."""
        import warnings
        dr._DASH_NOTED.clear()
        bad = "<b>x</b>\n" + "y" * 200
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr._dash_style_note("title(size)", bad, "size", cls="gsize")
        (msg,) = _printed([str(w.message) for w in caught])
        assert msg.startswith("named style <b>x</b>")
        assert msg.endswith(" not found in class gsize, default attributes used")
        tail = " not found in class gsize, default attributes used"
        assert "\n" not in msg
        assert len(msg) <= len("named style ") + 83 + len(tail)
