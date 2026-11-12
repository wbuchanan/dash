"""The help sentences WP-31 section 56 corrected (GAPS3 J1, J2), each held to
the code or a fixture that says what is true.

J1 is the Unsupported section's opening: it said every supplied option "is
named in that command's note, so nothing is dropped in silence", while an
option twoway refuses on a plot type is refused and the names reaching the
catch-all were missing from the list (test_help_conformance.py pins the
list itself).  The J2 tests below each read one sentence of dash.sthlp and
the code it describes.
"""
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")


def _read(name):
    with open(os.path.join(_ROOT, name), encoding="utf-8") as fh:
        return fh.read()


def _help():
    return _read("dash.sthlp")


def _between(text, start, end):
    i = text.index(start)
    return text[i:text.index(end, i)]


def _flat(text):
    """SMCL text with its line breaks and runs of spaces folded to one."""
    return re.sub(r"\s+", " ", text)


class TestTheSilenceSentence:
    def test_it_states_the_refusal_rule(self):
        sec = _flat(_between(_help(), "{marker unsupported}",
                             "{marker dependencies}"))
        assert "dropped in silence" not in sec
        assert "option X() not allowed" in sec
        assert "supplied and not drawn is named in that command's note" in sec


# ---------------------------------------------------------------------------
# J2: the sentences, each with the code it describes
# ---------------------------------------------------------------------------

def _render():
    return _read("dash_render.py")


def _mata():
    return _read("dash_parse.mata")


class TestTheSyntaxLine:
    def test_the_syntax_line_brackets_type(self):
        # filter()'s type() is optional: without it the widget is a
        # dropdown, so the Syntax line must not show it outside brackets.
        syn = _between(_help(), "{marker syntax}", "{marker description}")
        line = [ln for ln in syn.split("\n")
                if ln.startswith("{cmd:filter(}")]
        assert len(line) == 1, line
        assert ("{cmd:filter(}{it:varname} [{cmd:, type(}{it:filter_type}"
                "{cmd:)}") in line[0], line[0]
        assert "Without {cmd:type()} the widget" in _flat(_help())


class TestThePeriodSlider:
    def test_the_period_slider_sentence_is_in_the_slider_paragraph(self):
        h = _help()
        dropdown = _flat(_between(h, "{phang2}{cmd:type(dropdown)}",
                                  "{phang2}{cmd:type(multi)}"))
        rng = _flat(_between(h, "{phang2}{cmd:type(range)}",
                             "{phang2}{cmd:exclude(}"))
        assert "period numbers" not in dropdown
        assert "moves over Stata's period numbers in steps of one" in rng


class TestTheLegendRing:
    def test_ring0_says_what_is_drawn(self):
        # WP-31 S31 draws ring(0) inside the plot region, at position()'s
        # place there (_DASH_CLOCK_INSIDE) or the scheme's clock.
        h = _flat(_help())
        i = h.index("{synopt:{cmdab:leg:end(ring(0))}}")
        row = h[i:h.index("{p_end}", i)]
        assert "inside the plot region" in row
        assert "scheme's clock" in row
        src = _render()
        # Flipped: WP-32 reads the ring from clegend() or the scheme
        # (zyx2legend_ring) before the test.
        assert "ring == 0 and clock in _DASH_CLOCK_INSIDE" in src
        assert "_DASH_CLOCK_INSIDE[clock]" in src


class TestTheMarkerAngle:
    def test_msangle_names_anglestyles(self):
        h = _flat(_help())
        i = h.index("{synopt:{cmdab:msa:ngle(}")
        row = h[i:h.index("{p_end}", i)]
        for nm in ("horizontal", "vertical", "forty_five"):
            assert "{cmd:%s}" % nm in row, nm
        # The renderer reads a name through Stata's anglestyle table.
        m = re.search(r"_DASH_ANGLESTYLES = \{(.*?)\}", _render(), re.S)
        for nm in ("horizontal", "vertical", "forty_five"):
            assert '"%s"' % nm in m.group(1), nm
        assert ('angle_deg = _dash_anglestyle_degrees(options["msangle"])'
                in _render())


class TestTheUndrawnTypes:
    def test_not_drawn_names_every_refused_type(self):
        # Flipped (WP-35 PD-10): the paragraph named two words as twoway
        # plot types dash does not draw; that was wrong (M1).  It now says
        # that any word that is no plot type is refused alike, and the
        # by-name helpers are gone.
        h = _flat(_help())
        i = h.index("{ul:Not a plot type.}")
        para = h[i:h.index("{pstd}", i)]
        assert "Any word that is not a plot type is refused" in para
        assert "is not a twoway plot type" in para
        assert "sunflower" not in para and "matamatrix" not in para
        src = _mata()
        assert "_dash_undrawn_" + "plottype" not in src
        assert "_dash_" + "matamatrix_typed" not in src


class TestTheDotRow:
    def test_dot_sentence_matches_map_dot(self):
        # dot is listed with the types drawn as twoway describes; its rows
        # of dots are drawn (WP-31 B5b, _dot_rows), and the help says so.
        h = _flat(_help())
        tbl = _between(h, "{synopt:points, lines, bars}", "{p_end}")
        assert "{cmd:dot}" in tbl
        assert "{cmd:dot}'s rows of dots, as {cmd:twoway} draws it" in h
        src = _render()
        assert "def map_dot(" in src and "def _dot_rows(" in src


class TestTheRefusalLog:
    def test_the_refusal_log_claim(self):
        # Measured 18oct2026 (D-56.c): the served app's _RateLimiter logs a
        # bound's refusals at most once per window (60 s), counting the
        # ones it held back; the sentence states that rule.
        src = _render()
        assert '"        self._window = 60.0",' in src
        assert "if last is not None and now - last < self._window:" in src
        assert "more were refused since the last line" in src
        para = _flat(_between(_help(), "{cmd:429 Too Many Requests}",
                              "{ul:Recomputation.}"))
        assert "at most once a minute" in para
        assert "refused since its last line" in para
        assert "logs each refusal" not in para


class TestTheFrameRule:
    def test_an_iframe_sentence_exists_and_matches_the_csp(self):
        m = re.search(r"_DASH_CSP_STANDALONE = \((.*?)\n\)", _render(), re.S)
        assert m and "frame-ancestors" not in m.group(1)
        assert "\"frame-ancestors 'none'" in _render() or \
            "frame-ancestors 'none'" in _render()
        h = _flat(_help())
        assert "{cmd:<iframe>}" in h
        i = h.index("{cmd:<iframe>}")
        para = h[h.rindex("{pstd}", 0, i):h.index("{pstd}", i)]
        assert "{cmd:frame-ancestors}" in para
        assert "{cmd:X-Frame-Options: DENY}" in para


class TestTheLinkQualifier:
    def test_a_link_qualifier_example_exists(self):
        sec = _flat(_between(_help(), "{marker linking}", "{marker toolbar}"))
        assert "if foreign == 1" in sec
        assert re.search(r"\{cmd:\. dash build, [^}]*link\(g1 g2\)", sec)
        assert "own {it:if}" in sec
        # Each linked renderer draws over the group's one source through a
        # view of the rows it owns.
        assert "def _dash_linked_views(" in _render()


class TestTheDateLogParagraph:
    def test_a_tc_precedence_paragraph_exists(self):
        h = _flat(_help())
        i = h.index("{ul:Log scales on date axes.}")
        para = h[i:h.index("{pstd}", i)]
        # Flipped (WP-44 AX-18): the paragraph described a note and a
        # dropped log, which was wrong because twoway draws a log scale
        # with date labels; it now says so, and the note is gone.
        assert "{cmd:xscale(log)}" in para and "log scale" in para
        assert "01jan2001 01apr2001 01jul2001 01oct2001 01jan2002" in para
        assert "is meaningless for the date variable" not in para
        src = _render()
        assert "is meaningless for the date variable" not in src
        assert "drawing a date axis instead." not in src


# ---------------------------------------------------------------------------
# E10b (DECISIONS D36): the style files dash does not read
# ---------------------------------------------------------------------------

class TestTheUnreadStyleFiles:
    def test_the_help_gives_the_measured_picture(self):
        # Measured 18oct2026 with a color-zqred.style (set rgb "255 0 0")
        # and a textboxstyle-zqbig.style (set size huge, set color red) on
        # the ado-path: twoway draws red markers, and huge red marker labels
        # and titles.
        # Flipped (WP-45 ST-15): the two classes are read now, as twoway
        # reads them (ST-15; test/fixtures/style_leaf_truth.json L_color,
        # L_textboxstyle, L_mlabtextstyle), so the paragraph says so.
        h = _flat(_help())
        i = h.index("The {cmd:color-*.style} and {cmd:textboxstyle-*.style} "
                    "files are read as {cmd:twoway} reads them")
        para = h[i:h.index("{phang2}", i)]
        assert "{cmd:mcolor(mine)} draws that colour" in para
        assert "{cmd:mlabtextstyle(mine)} draw the file's size and colour" \
            in para
        assert "with no note" in para
        assert "not found in class textboxstyle, default attributes used" \
            not in para

    def test_the_reader_still_skips_both_classes(self):
        # The day SchemeParser reads either class, this paragraph is wrong.
        m = re.search(r'_STYLE_FILE_CLASSES: "tuple\[str, \.\.\.\]" = \('
                      r'\s*([^)]*)\)', _render())
        classes = re.findall(r'"(\w+)"', m.group(1))
        # old -> new: tickstyle, ticksetstyle, gridstyle (WP-44 AX-14);
        # old -> new: axisstyle (WP-44 AX-9);
        # old -> new: ST-7 seven leaf classes read (WP-45 ST-7);
        # old -> new: ST-15 color and textboxstyle read (WP-45 ST-15): the
        # two classes are read now, as twoway reads them.
        assert classes == ["seriesstyle", "markerstyle", "areastyle",
                           "linestyle", "shadestyle", "tickstyle",
                           "ticksetstyle", "gridstyle", "axisstyle",
                           "linepattern", "linewidth", "symbolsize", "gsize",
                           "intensity", "anglestyle", "margin", "color",
                           "textboxstyle"]
        assert ('f"{prefix}: {head} is not a recognised {what}; using '
                '{using}.",') in _render()


# ===========================================================================
# WP-46 RH-8 (documented, Q25): histogram and rbar with recast() and
# horizontal are drawn turned; twoway draws a broken picture there
# ===========================================================================

class TestRecastHorizontalDifference:

    def test_the_sentence(self):
        """The Differences list names the item in one line linked to the
        Recast paragraph, whose note gives the measured example
        (recast_truth.json RH8-01, RH8-02)."""
        text = _help()
        diff = _flat(_between(text, "{marker differences}",
                              "{marker validation}"))
        # Flipped (WP-48 RH-15): "are drawn turned" alone was wrong
        # because an rbar recast to a bar-like type is drawn upright, as
        # every range type recast to one is (test_help_claims_8.cscript
        # Q4802-2).
        assert ("{cmd:histogram} and {cmd:rbar} with {cmd:recast()} and "
                "{cmd:horizontal} are drawn turned (an {cmd:rbar} recast to "
                "{cmd:bar}, {cmd:area}, {cmd:spike}, {cmd:dropline} or "
                "{cmd:dot} upright); {cmd:twoway} draws a broken picture "
                "there -- see {help dash##recast:Recast}") in diff
        assert "{marker recast}" in text
        rec = _flat(_between(text, "{marker recast}", "{it:Legend keys"))
        assert ("{cmd:histogram mpg, recast(bar) horizontal}" in rec
                and "-1.81 to 1.91" in rec
                and "{cmd:rbar} {it:lo hi x}{cmd:, recast(rcap) horizontal}"
                in rec)

    def test_the_example_is_measured(self):
        import json
        with open(os.path.join(_HERE, "fixtures", "recast_truth.json"),
                  encoding="utf-8") as fh:
            p = json.load(fh)["probes"]
        lo, hi = p["RH8-01"]["xrange"]
        assert (round(lo, 2), round(hi, 2)) == (-1.81, 1.91)
        assert p["RH8-01"]["xlabels"][0] == "0"
        # rbar y y2 x, recast(rcap) horizontal: y2 up the y axis, y across.
        t = p["RH8-02"]["texts"]
        assert t.index("y2") < t.index("y") and p["RH8-02"]["yrange"] == [
            4.0, 12.0]

    def test_dash_draws_the_transpose(self):
        """dash draws histogram mpg, recast(bar) horizontal as horizontal
        bars whose right ends are the bins' heights (a guard of the
        documented behaviour), in both modes."""
        import sys
        sys.path.insert(0, _HERE)
        sys.path.insert(0, _ROOT)
        import test_join_order as jo
        import test_mode_parity as tp
        from test_server_layer_defects import plot_for
        from conftest import drawn_renderers
        spec = tp._spec(plots=[plot_for(
            "histogram", {"recast": "bar", "horizontal": "horizontal"})])
        plain = tp._spec(plots=[plot_for("histogram")])
        tops = sorted(float(v) for f in jo._saved_figs(jo._saved(
            plain, tp._DF)) for r in drawn_renderers(f)
            if type(r.glyph).__name__ == "Quad"
            for v in r.data_source.data["top"])
        for figs in (jo._saved_figs(jo._saved(spec, tp._DF)),
                     jo._served_figs(jo._served(spec, tp._DF))):
            bars = [r for f in figs for r in drawn_renderers(f)
                    if type(r.glyph).__name__ == "HBar"]
            assert bars
            got = sorted(float(v) for r in bars
                         for v in r.data_source.data[r.glyph.right])
            assert got == tops
