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
