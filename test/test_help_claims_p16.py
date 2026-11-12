"""The help passages the drop-in audit's package 16 found stale (WP-48
section 48-01): each corrected sentence of dash.sthlp, and the docstrings
and coverage-audit rows that repeated them, held to what dash does.

* LT-27 (TestTypoParagraph): the Unsupported section said a typo such as
  ``titel(x)`` "appears in the note" and that xreverse, xcommon, lockaspect
  and the like "reach the note"; dash refuses each as twoway refuses it,
  r(198) (test_help_claims_8.cscript HC8-06, Q4801-1, Q4801-2).
* plot:PT-5 (TestGraphPrefix): a Differences sub-point called graph a
  prefix read before twoway and quoted "unrecognised plot type 'graph'";
  dash refuses graph in every position, as twoway does (Q4801-3).
* basic:PT-16 (TestStalePassages): passages on headlabel, mangle(),
  recast() on dot, degree() above 7, fpfit's bwidth(), the ci outline
  options, mlabel(t*), derived-field names, merged keys, by()'s rescale
  and label box, lalign(), dlalign() and the Not drawn entry's scope, with
  the coverage-audit rows and two docstrings that repeated them
  (Q4801-4 .. Q4801-8, Q4801-10).  Those an earlier section corrected are
  pinned here too.
* GW-22 (TestUnitsAndDrawnOptions): the units sentence and the
  options-given-twice sub-point (Q4801-9).

WP-48 section 48-02:

* RH-15 (TestRecastClaims): the Orientation and Recast paragraphs, held to
  what WP-46 landed (Q4802-1 .. Q4802-6).
* ECO-16 (TestEcosystem): the Stata graph commands and reports paragraph,
  the iframe link, the three recipes and the README caveat (Q4802-7 ..
  Q4802-9, Q4802-11).

The Stata half -- what dash does when the sentence's command is run -- is
test_help_claims_8.cscript's Q4801 and Q4802 blocks.
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


class TestUnitsAndDrawnOptions:
    """GW-22: the units sentence converts #pt, #in and #cm at the smaller of
    xsize() and ysize() (_dash_ref_in; sizing_truth.json ref_*), and the
    options-given-twice sentence does not call clegend(), plegend() or
    pcycle() named in the note (Q4801-9: each given once draws, no note)."""

    def test_units_reference(self):
        assert not _has("(xsize() and ysize() do not change it)")
        assert _has("#pt, #in and #cm, which are converted at the scheme's "
                    "smaller graphsize side (the smaller of xsize() and "
                    "ysize() when either is given, as twoway converts them)")

    def test_drawn_not_noted(self):
        p = _help_prose()
        i = p.index("So are atobs on the fits")
        para = p[i:p.index("An option written in upper case", i)]
        assert "still named in the note" not in para
        assert "dash names in its note that twoway takes once" not in para
        assert ("Given once, atobs, nofit, fitplot(), ciplot(), clegend(), "
                "plegend(), pcycle() and the kernel are drawn and not "
                "named") in para
        assert "the graph-wide settings the Unsupported list names" in para


# ---------------------------------------------------------------------------
# WP-48 section 48-02
# ---------------------------------------------------------------------------

def _orientation():
    p = _help_prose()
    i = p.index("Orientation. horizontal draws a plot on its side")
    return p[i:p.index("Time-series operators.", i)]


def _recast():
    p = _help_prose()
    i = p.index("Recast. recast(plottype)")
    return p[i:p.index("Legend keys and default axis titles.", i)]


class TestRecastClaims:
    """RH-15: the Orientation and Recast paragraphs state what WP-46 landed
    (test_help_claims_8.cscript Q4802-1 .. Q4802-6): horizontal judged on
    the recast target; a range type recast to line, scatter or connected
    turned, to a bar-like type upright (rbar too); scatteri recast to bar
    or area turned; a range type drawn as a yx type keeps both bounds;
    histogram recast(bar) a bin wide, the others one x unit wide; and the
    broken picture twoway draws for histogram and rbar under recast() and
    horizontal linked, not restated."""

    def test_orientation_paragraph(self):
        para = _orientation()
        for s in ("judged on the type recast() names, as twoway judges it",
                  "a range type recast to line, scatter or connected takes "
                  "both and is turned",
                  "recast to bar, area, spike, dropline or dot it takes them "
                  "and is drawn upright",
                  "scatteri recast to bar or area takes them and is turned",
                  "on dot only a recast to bar, area, dot, dropline or spike "
                  "typed in full takes them",
                  "A histogram or rbar recast with horizontal, which twoway "
                  "draws as a broken picture, is drawn as Recast says; see "
                  "Differences from twoway."):
            assert s in para, s
        assert "judged after recast()" not in para

    def test_recast_paragraph(self):
        para = _recast()
        for s in ("a range type named as a yx type draws its first bound and "
                  "keeps both on the axis, in its title and key",
                  "(histogram: one bin wide; the others: one x unit wide)",
                  "A histogram recast with horizontal, and an rbar recast "
                  "with it to line, scatter, connected or a range type, is "
                  "drawn as the exact transpose of the upright layer (an "
                  "rbar recast to bar, area, spike, dropline or dot is drawn "
                  "upright, as every range type recast to one is); twoway "
                  "draws a broken picture there:"):
            assert s in para, s
        assert ("A histogram or rbar recast with horizontal is drawn as the "
                "exact transpose") not in para


class TestEcosystem:
    """ECO-16 (ECO-8): the Stata graph integration section names the graph
    commands and report tools a dashboard cannot serve, with what each says
    (test_help_claims_8.cscript Q4802-11), links the iframe note from
    Exporting, gives recipes for commands that draw through twoway
    (Q4802-7 .. Q4802-9 run them), and the README says a dashboard is no
    Stata graph."""

    @staticmethod
    def _section():
        return _prose(_between(_help(), "{marker graphintegration}",
                               "{marker accessibility}"))

    def test_names_every_command(self):
        sec = self._section()
        i = sec.index("Stata graph commands and reports.")
        para = sec[i:sec.index("A registered graph keeps no data.", i)]
        for s in ("graph describe g1", "graph rename g1 g2",
                  "graph copy g1 g3", "graph drop g1", "graph display g1",
                  'stop with "graph g1 not found", r(111)',
                  "graph replay g1 prints the same words and replays nothing",
                  'graph use g1 looks for a file, "file g1.gph not found", '
                  "r(601)",
                  'a bare graph, which replays the last graph command, '
                  "replays no dash command",
                  '"no existing graph command to replay", r(198)',
                  "webdoc, like dyndoc and markdown, embeds an image file"):
            assert s in para, s
        for s in ("graph use", "graph display", "putpdf image", "putexcel",
                  "dyndoc"):
            assert s in sec, s

    def test_iframe_is_linked(self):
        h = _help()
        i = h.index("{marker iframe}{...}\n{pstd}\nA saved page can be shown "
                    "inside another page with an {cmd:<iframe>}")
        assert h.count("{marker iframe}") == 1 and i > 0
        exp = _between(h, "{marker export}", "{ul:graph export.}")
        assert "{help dash##iframe:" in exp
        assert "{help dash##iframe:" in _between(
            h, "{marker graphintegration}", "{marker accessibility}")

    def test_recipes_present(self):
        sec = _between(_help(), "{ul:Commands that draw through twoway.}",
                       "{marker accessibility}")
        recipes = (
            ("sysuse auto, clear", "summarize mpg",
             "scalar mpg_mean = r(mean)", "scalar mpg_sd = r(sd)",
             "dash (histogram mpg) (function normalden(x, mpg_mean, "
             "mpg_sd), range(mpg))"),
            ("sysuse auto, clear", "regress mpg weight",
             "margins, at(weight=(2000(500)4500))", "matrix T = r(table)'",
             "matrix A = r(at)", "svmat T, names(col)",
             "svmat A, names(at)", "dash (rcap ll ul at1) (connected b at1)"),
            ("sysuse cancer, clear", "stset studytime, failure(died)",
             "sts generate s = s", "dash line s _t, sort connect(J)"))
        for lines in recipes:
            block = "".join("{cmd:%s}{break}\n" % ln for ln in lines[:-1]) \
                + "{cmd:%s}\n{p_end}" % lines[-1]
            assert block in sec, lines[-1]
        p = _prose(sec)
        assert "dash takes the place of twoway only where a command is typed" \
            " as twoway" in p
        assert "held in scalars first" in p
        assert "svmat takes a matrix name, not an expression" in p
        assert "sts generate needs stset data" in p

    def test_readme_caveat(self):
        r = _read(os.path.join(_ROOT, "README.md"))
        i = r.index("`dash scatter mpg weight` where you would write "
                    "`twoway scatter mpg weight`.")
        assert r.count("A dashboard is an HTML page, not a Stata graph: see "
                       "`help dash`, Stata graph integration.") == 1
        assert r.index("A dashboard is an HTML page, not a Stata graph") > i
