"""dash.sthlp's resource limits, each beside twoway's answer (WP-40 40-02).

twoway has no caps; dash keeps count caps (graphs, plots, by() groups, tabs,
filters, dropdown values, reference lines, added texts, table rows, image
panels) and a few fixed ones (n(), bin(), lpoly's degree, histogram bins,
axis ticks, marker size, fpfit's grid, expanded text, the axis ranges a
build asks Stata's tick routine for).  Ruling M10 / Q44 with P4-3 keeps
every count cap and documents each in two places: a one-line sub-point
under the Differences item "Resource limits" and the full statement, with
twoway's answer, under Resource limits.  The size caps (embedded cells,
page bytes) went with P4-3 (33-15) and no image is bounded by its bytes
(A-18), so the help says that dash, like twoway, takes data of any size.

Each class reads the value its sentence states from the code (dash.ado,
dash_render.py, dash_parse.mata) and asserts the help states that value.
twoway's answers are measured beside dash's in test_wp40_truth.cscript's
S02 blocks (Q4002-1..8).
"""
import ast
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_HELP = os.path.join(_ROOT, "dash.sthlp")
_ADO = os.path.join(_ROOT, "dash.ado")
_RENDER = os.path.join(_ROOT, "dash_render.py")
_MATA = os.path.join(_ROOT, "dash_parse.mata")
_LINK = "{help dash##limits:Resource limits}"


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _help():
    return _read(_HELP)


def _between(text, start, end):
    i = text.index(start)
    j = text.index(end, i + len(start))
    return text[i:j]


def _flat(text):
    """Lines joined, runs of blanks made one."""
    return " ".join(text.split())


def _sentences(text):
    """*text* cut at each sentence end (a period followed by two blanks or
    a line end), each sentence flattened."""
    parts = re.split(r"(?<=\.)(?:  +|[ \t]*\n\s*)", text.strip())
    return [_flat(p) for p in parts if p.strip()]


def _limits():
    return _between(_help(), "{marker limits}", "{marker examples}")


def _diff():
    return _between(_help(), "{marker differences}", "{marker subcommands}")


def _item():
    """The Differences item "Resource limits" with its sub-points: from its
    number to the next numbered item or the end of the section."""
    d = _diff()
    m = re.search(r"^\{phang2\}(\d+)\.  \{ul:Resource limits\.\}", d, re.M)
    assert m, "no Differences item 'Resource limits'"
    nxt = re.search(r"^\{phang2\}\d+\.  ", d[m.end():], re.M)
    return d[m.start():m.end() + nxt.start()] if nxt else d[m.start():]


def _item_head():
    """The item's own paragraph, without its sub-points."""
    it = _item()
    i = it.find("\n{phang2}    {ul:")
    return it if i < 0 else it[:i]


def _sub(heading):
    """The one line of the item's sub-point *heading*."""
    for line in _item().split("\n"):
        if line.startswith("{phang2}    {ul:%s}" % heading):
            return line
    raise AssertionError("no sub-point %r" % heading)


def _fixed():
    """The Fixed limits paragraph of Resource limits alone: from its
    heading to the next line that starts {pstd} or {marker."""
    lim = _limits()
    i = lim.index("{ul:Fixed limits.}")
    m = re.search(r"^\{(?:pstd|marker)", lim[i:], re.M)
    return lim[i:i + m.start()] if m else lim[i:]


def _fixed_sentence(needle):
    hits = [s for s in _sentences(_fixed()) if needle in s]
    assert hits, "no Fixed limits sentence holds %r" % needle
    return hits[0]


def _table_row(glob):
    """The Resource limits table row of $<glob>, flattened."""
    lim = _limits()
    i = lim.index("{synopt:{cmd:$%s}}" % glob)
    j = lim.index("{p_end}", i)
    return _flat(lim[i:j])


def _limits_table():
    """_DASH_LIMITS as dash_render.py writes it: key -> (default, ceiling,
    global)."""
    src = _read(_RENDER)
    i = src.index("_DASH_LIMITS = {")
    j = src.index("\n}\n", i)
    return ast.literal_eval(src[i + len("_DASH_LIMITS = "):j + 2])


def _constant(path, name):
    m = re.search(r"^\s*%s(?::\s*\w+)?\s*=\s*([0-9_.]+)" % re.escape(name),
                  _read(path), re.M)
    assert m, "%s not found in %s" % (name, os.path.basename(path))
    return int(float(m.group(1).replace("_", "")))


def _n(value):
    """A count as the help writes it: 1,000; 300."""
    return format(value, ",")


def _assert_sub_point(line):
    """D-40-02.a: a sub-point is one line ending in the link."""
    assert line.endswith("; see %s." % _LINK), line


# ---------------------------------------------------------------------------
# plat:PT-8 (syn:SD-16, sil:SD-22): no size limit; the count limits
# ---------------------------------------------------------------------------

class TestNoSizeAndCounts:
    """dash, like twoway, sets no size limit (P4-3); its count limits are
    listed under Differences and stated beside twoway's answer under
    Resource limits (Q4002-1 measures reference lines and added texts)."""

    def test_the_item_is_the_last_numbered_one(self):
        d = _diff()
        nums = [int(n) for n in re.findall(r"^\{phang2\}(\d+)\.", d, re.M)]
        head = re.search(r"^\{phang2\}(\d+)\.  \{ul:Resource limits\.\}",
                         d, re.M)
        assert head, "no Differences item 'Resource limits'"
        assert int(head.group(1)) == max(nums) == len(nums)
        h = _flat(_item_head())
        assert ("{cmd:twoway} draws any amount of data and any number of "
                "plots, panels, lines and texts; {cmd:dash} also takes "
                "data of any size") in h
        assert _LINK in h

    def test_the_sub_point_lists_the_count_limits(self):
        sub = _sub("No size limit; count limits.")
        _assert_sub_point(sub)
        assert "Like {cmd:twoway}, {cmd:dash} takes data and builds pages " \
               "of any size" in sub
        table = _limits_table()
        for key, (default, _ceiling, glob) in table.items():
            if key in ("plots", "by_groups"):
                continue  # plat:PT-9's and plat:PT-10's own sub-points
            assert "{cmd:$%s}" % glob in sub, glob
            assert _n(default) in sub, (glob, default)
        assert "{cmd:r(134)}" in sub

    def test_the_table_states_each_limit(self):
        for _key, (default, ceiling, glob) in _limits_table().items():
            row = _table_row(glob)
            assert "default %s" % _n(default) in row, (glob, row)
            assert "at most %s" % _n(ceiling) in row, (glob, row)

    def test_the_intro_says_no_size_limit(self):
        lim = _flat(_limits())
        assert ("Neither {cmd:twoway} nor {cmd:dash} limits the size of "
                "the data or of the page") in lim
        assert ("{cmd:twoway} has none of the count limits below either: "
                "it draws any number of plots, panels, lines and texts."
                ) in lim

    def test_no_size_cap_is_left_in_the_code(self):
        table = _limits_table()
        assert "cells" not in table and "bytes" not in table, sorted(table)

    def test_no_image_byte_bound(self):
        """A-18: no image is bounded by its bytes; $dash_max_images counts
        image panels."""
        for path in (_RENDER, _ADO):
            assert "_DASH_IMAGE_MAX_BYTES" not in _read(path), path
        lim = _flat(_limits())
        assert "no image panel is limited by its file size" in lim
        assert "{cmd:$dash_max_images} counts images, not bytes" in lim
        assert "{cmd:$dash_max_images}" in _sub("No size limit; count limits.")
        for text in (lim, _flat(_diff())):
            assert "10 MB" not in text and "10,000,000 bytes" not in text

    def test_the_silent_list_names_the_build_bound(self):
        """D-40-02.a/f: the item's list of silent limits names the axis
        ranges a build asks Stata's tick routine for."""
        bound = _constant(_RENDER, "_DASH_STATA_ORACLE_MAX")
        hits = [s for s in _sentences(_item_head()) if "are silent" in s]
        assert hits, "no sentence of the item says which limits are silent"
        assert str(bound) in hits[0], hits[0]


# ---------------------------------------------------------------------------
# plat:PT-9: the plot limit counts plots, twoway's counts variables
# ---------------------------------------------------------------------------

class TestPlotsNotVariables:
    """dash's limit is plots in a graph; twoway's is 100 variables in one
    plot, x included (limits.sthlp; Q4002-2 measures both examples)."""

    def test_the_row_gives_twoways_limit(self):
        default = _limits_table()["plots"][0]
        row = _table_row("dash_max_plots")
        assert "default %s" % _n(default) in row
        assert ("{cmd:twoway}'s own limit is 100 variables in one plot, x "
                "included: it refuses {cmd:scatter y1-y100 x}, \"too many "
                "variables specified\", {cmd:r(103)}, which {cmd:dash} "
                "draws, and draws {cmd:(scatter y1-y60 x) (scatter y61-y120 "
                "x)}, which {cmd:dash} refuses at the default.") in row

    def test_the_sub_point(self):
        sub = _sub("Plots, not variables.")
        _assert_sub_point(sub)
        assert ("The plot limit counts a graph's plots, %s at the default, "
                "where {cmd:twoway} counts the variables of one plot"
                % _n(_limits_table()["plots"][0])) in sub


# ---------------------------------------------------------------------------
# plat:PT-10 (BY-22): by() draws its first 100 groups; twoway draws all
# ---------------------------------------------------------------------------

class TestByGroups:
    """Q4002-3: twoway draws 120 panels where dash draws 100 with a note."""

    def test_the_row_gives_twoways_answer(self):
        default = _limits_table()["by_groups"][0]
        row = _table_row("dash_max_by_groups")
        assert "default %s" % _n(default) in row
        assert "{cmd:twoway} draws every group." in row

    def test_the_sub_point(self):
        sub = _sub("by() groups.")
        _assert_sub_point(sub)
        assert ("A {cmd:by()} graph draws its first %s groups, with a note, "
                "where {cmd:twoway} draws all"
                % _n(_limits_table()["by_groups"][0])) in sub


# ---------------------------------------------------------------------------
# stat:PT-15 (DT-17): n(), bin() and lpoly's degree
# ---------------------------------------------------------------------------

def _rule_tokens(name):
    """The *name*= tokens of dash.ado's _dash_option_rules, as (upper
    bound or None, types or None for "every other type")."""
    ado = _read(_ADO)
    i = ado.index("program define _dash_option_rules")
    body = ado[i:ado.index("\nend\n", i)]
    out = []
    for tok in body.split():
        if not tok.startswith(name + "="):
            continue
        spec, _at, types = tok[len(name) + 1:].partition("@")
        parts = spec.split(",")
        if parts[0] not in ("int", "num", "pos"):
            continue  # n=style and the like are no count
        hi = int(parts[2]) if len(parts) > 2 and parts[2] else None
        out.append((hi, types.split("|") if types else None))
    assert out, "no %s= token in _dash_option_rules" % name
    return out


def _n_pairs():
    """The n() rules grouped: {bound: [types, "other" for no type list]},
    and the types whose n() has no upper bound."""
    bounded, unbounded = {}, []
    for hi, types in _rule_tokens("n"):
        if hi is None:
            unbounded.extend(types or ["other"])
        else:
            bounded.setdefault(hi, []).extend(types or ["other"])
    return bounded, unbounded


def _type_words(t):
    return ("the other types that take {cmd:n()}" if t == "other"
            else "{cmd:%s}" % t)


class TestNBinDegree:
    """n() past its bound and bin() above 1,000 are refused where twoway
    draws them (mspline's 300 is twoway's own); fpfitci and the linear
    and quadratic fits take any n() as twoway does; lpoly fits at most
    degree 30 (Q4002-4 measures twoway beside dash)."""

    def test_the_fixed_limits_paragraph(self):
        f = _flat(_fixed())
        assert f.startswith("{ul:Fixed limits.} These have no global; each "
                            "is a guard on what one layer or option asks "
                            "{cmd:dash} to draw.")

    def test_each_n_bound_is_stated_with_its_types(self):
        bounded, unbounded = _n_pairs()
        assert bounded and unbounded
        refused = [s for s in _sentences(_fixed()) if "is refused" in s
                   and "{cmd:n()}" in s]
        assert refused, "no sentence says n() is refused"
        for hi, types in bounded.items():
            assert _n(hi) in refused[0], hi
            for t in types:
                assert _type_words(t) in refused[0], (hi, t)
        anyn = [s for s in _sentences(_fixed()) if "any {cmd:n()}" in s]
        assert anyn, "no sentence names the types that take any n()"
        for t in unbounded:
            assert "{cmd:%s}" % t in anyn[0], t
            for s in _sentences(_fixed()):
                if "refused" in s:
                    assert "{cmd:%s}" % t not in s, (t, s)

    def test_bin_and_degree(self):
        (hi, _types), = _rule_tokens("bin")
        s = _fixed_sentence("{cmd:bin()} above")
        assert "{cmd:bin()} above %s is refused with {cmd:r(198)}, where " \
               "{cmd:twoway} draws it" % _n(hi) in s
        deg = _constant(_RENDER, "_LPOLY_DEGREE_FIT_MAX")
        s = _fixed_sentence("{cmd:degree()}")
        assert "fitted at most at degree %d" % deg in s
        assert "with a note, where {cmd:twoway} fits any degree" in s

    def test_the_sub_point(self):
        bounded, unbounded = _n_pairs()
        sub = _sub("n(), bin() and degree().")
        _assert_sub_point(sub)
        for hi in bounded:
            assert _n(hi) in sub, hi
        for t in unbounded:
            assert "{cmd:%s}" % t in sub, t
        (hi, _types), = _rule_tokens("bin")
        assert "{cmd:bin()} above %s are refused" % _n(hi) in sub
        assert "fits at most degree %d" % _constant(
            _RENDER, "_LPOLY_DEGREE_FIT_MAX") in sub


# ---------------------------------------------------------------------------
# sil:SD-1: histogram width() or discrete needing more than 1,000 bins
# ---------------------------------------------------------------------------

class TestHistogramBins:
    """Past _MAX_BINS bins, empty ones counted, discrete is squeezed into
    that many bars and width() is dropped; twoway draws the occupied bins
    (Q4002-5).  HR-19: "one bar per distinct value" is qualified."""

    def test_the_discrete_sentence_is_qualified(self):
        bins = _constant(_RENDER, "_MAX_BINS")
        h = _flat(_help())
        assert ("With {cmd:discrete} it draws one bar per distinct value -- "
                "as long as the range needs at most %s bars of that width, "
                "empty ones counted: beyond that the values are squeezed "
                "into %s bars, with a note, where {cmd:twoway} draws only "
                "the bars that hold observations ({cmd:histogram price, "
                "discrete} draws 74)" % (_n(bins), _n(bins))) in h

    def test_the_fixed_limit(self):
        bins = _constant(_RENDER, "_MAX_BINS")
        s = _fixed_sentence("{cmd:histogram}")
        assert ("A {cmd:histogram} whose {cmd:width()} or {cmd:discrete} "
                "would need more than %s bins over its range, empty ones "
                "counted, is drawn with %s bins under {cmd:discrete} and "
                "with the default bins in place of {cmd:width()}, with a "
                "note; {cmd:twoway} draws the occupied bins"
                % (_n(bins), _n(bins))) in s

    def test_the_sub_point(self):
        sub = _sub("Histogram bins.")
        _assert_sub_point(sub)
        assert ("{cmd:width()} or {cmd:discrete} needing more than %s bins "
                "is rebinned" % _n(_constant(_RENDER, "_MAX_BINS"))) in sub


# ---------------------------------------------------------------------------
# AX-16 (sil:SD-10): 2,000 ticks; 256 axis ranges asked of Stata a build
# ---------------------------------------------------------------------------

class TestTicks:
    """More than _MAX_AXIS_TICKS ticks keep the default ticks with a note
    and #N above it is clamped silently, where twoway draws every tick
    (Q4002-6); a build asks Stata's tick routine for at most
    _DASH_STATA_ORACLE_MAX ranges (A-18, D-40-02.f)."""

    def test_the_axis_paragraph(self):
        ticks = _n(_constant(_RENDER, "_MAX_AXIS_TICKS"))
        h = _flat(_help())
        assert ("More than %s ticks in any form keep the axis's default "
                "ticks, with a note; {cmd:#}{it:N} above %s is taken as %s, "
                "silently, and {cmd:twoway} draws every tick it is asked "
                "for ({cmd:xtick(1500(1)5000)}: 3,501)."
                % (ticks, ticks, ticks)) in h

    def test_the_fixed_limit(self):
        ticks = _n(_constant(_RENDER, "_MAX_AXIS_TICKS"))
        s = _fixed_sentence("ticks in any form")
        assert ("more than %s ticks in any form keeps the axis's default "
                "ticks, with a note, and {cmd:#}{it:N} above %s is taken as "
                "%s, silently, where {cmd:twoway} draws every tick it is "
                "asked for" % (ticks, ticks, ticks)) in s

    def test_the_build_bound_is_stated(self):
        bound = str(_constant(_RENDER, "_DASH_STATA_ORACLE_MAX"))
        s = _fixed_sentence("tick routine")
        assert bound in s and "silently" in s, s
        assert ("where {cmd:twoway} asks the routine for every axis it "
                "draws") in s
        sub = _sub("Ticks.")
        _assert_sub_point(sub)
        assert bound in sub
        assert ("More than %s ticks keep the default ticks"
                % _n(_constant(_RENDER, "_MAX_AXIS_TICKS"))) in sub


# ---------------------------------------------------------------------------
# sil:SD-11: msize() above 1,000 units is drawn at the default
# ---------------------------------------------------------------------------

def _size_max():
    m = re.search(r"_SIZE_MAX_RS: float = ([0-9.]+)", _read(_RENDER))
    assert m, "_SIZE_MAX_RS not found"
    return int(float(m.group(1)))


class TestMarkerSize:
    """HR-19: msize() "any number" is corrected; above _SIZE_MAX_RS units
    the scheme's default is drawn with a note, where twoway draws it
    (Q4002-7)."""

    _SAYS = ("({cmd:msize()} and the other marker sizes at most %s units: a "
             "larger size is drawn at the scheme's default with a note, "
             "where {cmd:twoway} draws it)")

    def test_the_option_values_sentence(self):
        h = _flat(_help())
        assert ("{cmd:mlabgap()}, {cmd:mlabposition()} and {cmd:fintensity()} "
                "any number " + self._SAYS % _n(_size_max())) in h

    def test_the_fixed_limit(self):
        s = _fixed_sentence("{cmd:msize()}")
        assert ("{cmd:msize()} and the other marker sizes take at most %s "
                "units: a larger size is drawn at the scheme's default with "
                "a note, where {cmd:twoway} draws it" % _n(_size_max())) in s

    def test_the_sub_point(self):
        sub = _sub("Marker size.")
        _assert_sub_point(sub)
        assert ("{cmd:msize()} above %s units is drawn at the default"
                % _n(_size_max())) in sub


# ---------------------------------------------------------------------------
# sil:SD-12: fpfit and fpfitci above 20,000 distinct x
# ---------------------------------------------------------------------------

class TestFpfitGrid:
    """Above _FP_GRID_MAX distinct x the fit is evaluated on that many
    evenly spaced x, silently, where twoway predicts at every distinct x
    (no cscript probe: 20,000 distinct x is a slow build)."""

    def test_the_constant_is_stated(self):
        grid = _n(_constant(_RENDER, "_FP_GRID_MAX"))
        s = _fixed_sentence("{cmd:fpfitci} with more than")
        assert ("{cmd:fpfit} and {cmd:fpfitci} with more than %s distinct x "
                "are evaluated at %s evenly spaced x across the range, where "
                "{cmd:twoway} predicts at every distinct x" % (grid, grid)) in s

    def test_the_sub_point(self):
        sub = _sub("fpfit's grid.")
        _assert_sub_point(sub)
        assert ("Above %s distinct x the fit is evaluated on %s points"
                % ((_n(_constant(_RENDER, "_FP_GRID_MAX")),) * 2)) in sub
