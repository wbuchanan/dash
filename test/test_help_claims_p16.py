"""The help passages the drop-in audit's package 16 found stale (WP-48
section 48-01): each corrected sentence of dash.sthlp, and the docstrings
and coverage-audit rows that repeated them, held to what dash does.

* LT-27 (TestTypoParagraph): the Unsupported section said a typo such as
  ``titel(x)`` "appears in the note" and that xreverse, xcommon, lockaspect
  and the like "reach the note"; dash refuses each as twoway refuses it,
  r(198) (test_help_claims_8.cscript HC8-06, Q4801-1, Q4801-2).

The Stata half -- what dash does when the sentence's command is run -- is
test_help_claims_8.cscript's Q4801 block.
"""
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_HELP = os.path.join(_ROOT, "dash.sthlp")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _help():
    return _read(_HELP)


def _between(text, start, end):
    i = text.index(start)
    j = text.index(end, i + len(start))
    return text[i:j]


def _prose(text):
    """SMCL reduced to its words: directives unwrapped, lines joined."""
    t = re.sub(r"\{(?:cmd|it|opt|bf|ul|cmdab)[: ]([^{}]*)\}", r"\1", text)
    t = re.sub(r"\{helpb? [^:}]*:([^}]*)\}", r"\1", t)
    t = re.sub(r"\{helpb? ([^:}]*)\}", r"\1", t)
    return re.sub(r"\s+", " ", t)


def _paragraphs(text):
    """The {pstd}/{phang2} paragraphs of *text*, each reduced to prose."""
    return [_prose(p) for p in re.split(r"\{(?:pstd|phang2?)\}", text)]


def _unsupported():
    return _between(_help(), "{marker unsupported}", "{marker dependencies}")


class TestTypoParagraph:
    """LT-27: the two paragraphs at the end of the Unsupported section."""

    def test_titel_is_refused(self):
        sec = _prose(_unsupported())
        assert ("titl(x) abbreviates title() and works, titel(x) is "
                "option titel() not allowed, r(198)") in sec
        assert "appears in the note" not in sec
        assert "reported as ignored rather than" not in sec
        # The sub-option notes print the token as typed, value and all
        # (Q4801-1: legend(note("N")) is named note("N")).
        assert "never the values supplied" not in sec

    def test_names_are_refused(self):
        paras = [p for p in _paragraphs(_unsupported()) if "xreverse" in p]
        assert len(paras) == 1, paras
        p = paras[0]
        assert "reach the note" not in p
        assert ("refuses them as twoway refuses them, option xreverse not "
                "allowed, r(198)") in p
        for word in ("xscale(reverse)", "xscale(alt)", "graph combine",
                     "plotregion()", "legend()", "clegend()", "addplot()",
                     "lockaspect, zoom() and ddensity are options of no "
                     "Stata graph command"):
            assert word in p, word


class TestGraphPrefix:
    """plot:PT-5: dash refuses graph in every position, as twoway refuses
    twoway graph ... (Q4801-3); the Differences paragraph that called it a
    prefix read before twoway, refused as "unrecognised plot type
    'graph'", is gone."""

    def test_no_prefix_paragraph(self):
        h = _help()
        flat = re.sub(r"\s+", " ", h)
        assert "unrecognised plot type" not in flat
        assert "graph is read only before twoway" not in flat
        p = _prose(_between(h, "{marker syntax}", "{marker description}"))
        assert ("so are tw, two, twow, twowa, graph, gr, gra and grap, in "
                "any case, before a plot, alone or before options") in p


_AUDIT = os.path.join(_ROOT, "TWOWAY_COVERAGE_AUDIT.md")
_RENDER = os.path.join(_ROOT, "dash_render.py")
_LPOLY_TEST = os.path.join(_HERE, "test_lpoly_degree.py")

_PROSE = {}


def _help_prose():
    """The whole help reduced to prose, once."""
    if "help" not in _PROSE:
        _PROSE["help"] = _prose(_help())
    return _PROSE["help"]


def _has(phrase):
    return phrase in _help_prose()


class TestStalePassages:
    """basic:PT-16: each passage the audit listed states what dash does at
    the WP-48 base (probes Q4801-4 .. Q4801-8 and Q4801-10)."""

    def test_mangle_barbsize_headlabel(self):
        # Already corrected by 47-01 (f2d63fc, WP-47 basic:PT-1).
        assert not _has("On the other plot types these three options are "
                        "named in the note")
        assert _has("mangle() and barbsize() off the arrow types are taken "
                    "in silence, as twoway draws nothing different with them")
        assert _has("on every other type it is refused, as twoway refuses "
                    "it")

    def test_headlabel_pc(self):
        # Already corrected by 47-01 (f2d63fc); Q4801-4 measures it.
        assert not _has("on pcscatter and pccapsym dash names it in the note")
        assert _has("headlabel moves those labels to the second point, the "
                    "head, on pcscatter, pccapsym, pcarrow, pcbarrow and "
                    "pcarrowi, as twoway does")

    def test_recast_on_dot(self):
        # Q4801-5: dot mpg weight, recast(line) -- rc 0, no note.
        assert not _has("recast() is taken and named in the note")
        assert _has("On dot, recast() is taken in silence: twoway reads it "
                    "there and draws the dot graph unchanged, and so does "
                    "dash")

    def test_degree_above_7(self):
        # Q4801-6: lpoly mpg weight, degree(8) -- rc 0, with a note.
        assert not _has("dash refuses more than 7")
        assert _has("twoway takes any whole number from 0 up, and so does "
                    "dash: above 7, where Stata's rule-of-thumb constants "
                    "stop, it is drawn with the note (note: dash: "
                    "lpoly degree(8) is drawn; above degree 7 the result can "
                    "differ from Stata's.)")

    def test_fpfit_bwidth(self):
        # Q4801-7: fpfit mpg weight, bwidth(2) -- r(198) in both.
        assert not _has("so a pasted command still runs, and reports that "
                        "they were ignored")
        assert _has("dash refuses them as Stata does, option bwidth() not "
                    "allowed, r(198)")

    def test_acolor_off_ci(self):
        # Q4801-8: scatter mpg weight, acolor(red) -- rc 0, no note.
        assert not _has("alpattern() are named in the note (see")
        assert _has("On the other plot types acolor(), alcolor(), alwidth() "
                    "and alpattern() are drawn as the fill and line options "
                    "they stand for, or taken in silence where twoway draws "
                    "nothing different with them")

    def test_mlabel_pattern(self):
        # Already corrected by 47-02 (b6ae36c, WP-47 basic:PT-3).
        assert not _has("an element of mlabel() that names several "
                        "variables, such as t*")
        assert _has("one that names several (t*, make-foreign) draws no "
                    "labels for that y, as twoway draws none")

    def test_shadowed_fields(self):
        assert not _has("shadowed by the derived field in hover() and "
                        "mlabel()")
        assert _has("draws its own values as a plot variable and in hover() "
                    "and mlabel() too")

    def test_merged_keys(self):
        assert not _has("are still drawn by dash")
        assert _has("Keys twoway merges into one are merged by dash as "
                    "twoway merges them")

    def test_style_rescale(self):
        # Already corrected by WP-41 (b17deeb, BY-18); Q4801-10 measures it.
        assert not _has("only their separate scales are drawn, with a note")
        assert _has("by(varlist, style(rescale))}and style(combine): drawn "
                    "as twoway draws them")

    def test_subtitle_box(self):
        # Q4801-10: by(foreign) subtitle(, fcolor(red) lcolor(blue)) and
        # subtitle(, nobox) -- rc 0, no note.
        assert not _has("do not restyle it in dash and are named in a note")
        assert _has("subtitle()'s fcolor(), lcolor() and nobox restyle it, "
                    "with no note")

    def test_lalign(self):
        # Already corrected by 47-03 (4ef9650, WP-47 basic:PT-4).
        assert not _has("lalign(alignmentstyle), inside a plot, is taken as "
                        "twoway takes it")
        assert _has("lalign(alignmentstyle), inside a plot, is drawn as "
                    "twoway draws it")

    def test_dlalign(self):
        # Already corrected by 47-03 (45602f2, WP-47 basic:PT-5).
        assert not _has("dash draws it centred, and twoway draws the same "
                        "picture with it")
        assert _has("dlalign(linealignmentstyle)}dot: where the dots' "
                    "outline lies, as mlalign()")

    def test_every_plot_type(self):
        # The headlabel list was corrected by 47-01 (f2d63fc); the scope of
        # the measurement is the fixture's.
        assert not _has("headlabel on pcspike, pccapsym, pcscatter")
        assert not _has("measured on every plot type")
        assert _has("measured with graph export SVG on each of the 44 plot "
                    "types for every option test/fixtures/"
                    "noted_option_truth.json probes")

    def test_coverage_audit_headlabel(self):
        rows = [ln for ln in _read(_AUDIT).splitlines()
                if "headlabel" in ln and ln.startswith("|")]
        assert rows
        for ln in rows:
            for stale in ("`headlabel` and detailed arrowhead controls",
                          "`headlabel` and jitter unavailable",
                          "`headlabel` limitations", "or `headlabel`"):
                assert stale not in ln, (stale, ln)
        for t in ("pcarrowi", "pccapsym", "pcarrow", "pcbarrow",
                  "pcscatter"):
            row = [ln for ln in rows if "| `%s` |" % t in ln]
            assert len(row) == 1, t
            assert "headlabel" in row[0] and "drawn" in row[0], row[0]

    def test_dot_style_docstring(self):
        # Already corrected by 47-03 (45602f2, WP-47 basic:PT-5).
        src = _read(_RENDER)
        i = src.index("    def _dot_style(")
        doc = src[i:src.index('"""', src.index('"""', i) + 3)]
        assert "named by dash.ado" not in doc
        assert "dlalign() sizes the dots' outline as twoway" in \
            re.sub(r"\s+", " ", doc)

    def test_lpoly_degree_docstring(self):
        src = _read(_LPOLY_TEST)
        doc = re.sub(r"\s+", " ", src[:src.index('"""', 3)])
        assert "stays dash's own bound" not in doc
        assert "degree(8) -- which twoway draws -- is drawn with a note" \
            in doc
