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
        h = _flat(_help())
        i = h.index("{ul:Not drawn.}")
        para = h[i:h.index("{pstd}", i)]
        assert "Two {cmd:twoway} plot types are not drawn" in para
        assert "{cmd:sunflower}" in para
        assert "{cmd:matamatrix(}" in para
        src = _mata()
        body = _between(src, "string scalar _dash_undrawn_plottype(",
                        "\n}\n")
        assert re.findall(r'anyof\(\("([a-z]+)"\)', body) == ["sunflower"]
        assert "string scalar _dash_matamatrix_typed(" in src


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
        assert "{cmd:%tC}" in para and "{cmd:xscale(log)}" in para
        assert "is meaningless for the date variable" in para
        src = _render()
        assert ("dash: xscale(log) is meaningless for the date variable "
                in src)
        assert "drawing a date axis instead." in src


# ---------------------------------------------------------------------------
# E10b (DECISIONS D36): the style files dash does not read
# ---------------------------------------------------------------------------

class TestTheUnreadStyleFiles:
    def test_the_help_gives_the_measured_picture(self):
        # Measured 18oct2026 with a color-zqred.style (set rgb "255 0 0")
        # and a textboxstyle-zqbig.style (set size huge, set color red) on
        # the ado-path: twoway draws red markers, and huge red marker labels
        # and titles; dash draws black markers with "mcolor(zqred) is not a
        # recognised colour; using black.", the body text style with
        # "mlabtextstyle(zqbig) is not a recognised text style; using the
        # body text style." and a title in the default style with "named
        # style zqbig not found in class textboxstyle, default attributes
        # used".
        h = _flat(_help())
        i = h.index("The {cmd:textboxstyle} and {cmd:color} style files are "
                    "not read")
        para = h[i:h.index("{phang2}", i)]
        assert "{cmd:color-mine.style}" in para
        assert "{cmd:textboxstyle-mine.style}" in para
        # Flipped (18oct2026): the note is twoway's, naming the colour.
        assert ("named style mine not found in class color, default "
                "attributes used") in para
        assert "not found in class textboxstyle, default attributes used" \
            in para
        assert "using the body text style" in para

    def test_the_reader_still_skips_both_classes(self):
        # The day SchemeParser reads either class, this paragraph is wrong.
        m = re.search(r'_STYLE_FILE_CLASSES: "tuple\[str, \.\.\.\]" = \('
                      r'\s*([^)]*)\)', _render())
        classes = re.findall(r'"(\w+)"', m.group(1))
        assert classes == ["seriesstyle", "markerstyle", "areastyle",
                           "linestyle", "shadestyle"]
        assert ('f"{prefix}: {head} is not a recognised {what}; using '
                '{using}.",') in _render()
