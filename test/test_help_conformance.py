"""`dash.sthlp` and `dash.ado` are checked against each other, mechanically.

Sixteen sections of work added roughly a hundred option declarations to
`dash.ado`. The help file did not follow, and nothing made it: reading two
files side by side is how 98 accepted options ended up undocumented, how five
options that dash honours ended up under a heading that says they are
unsupported, and how `xlabel()` came to be advertised with two different
minimum abbreviations nine lines apart.

This file is the test that stops them separating again. It asserts in BOTH
directions, because one direction only is how the undocumented half grew.

The help is not meant to restate `twoway`. `dash.sthlp:127-131` redirects the
reader to Stata's own documentation for anything that behaves as it does in
`twoway`, and that is the right call -- so requiring every accepted option to
be documented here would demand a second copy of the twoway manual. The rule
used instead is mechanical: `test/fixtures/abbrev_truth.json` records every
option probed against REAL twoway, so an option in that file is one the
redirect covers, and an option **not** in it is dash's own invention and has
no other documentation anywhere. Those must be in the help.

Parsing the help is the part that goes wrong quietly. SMCL puts an option
name in several shapes, and the naive regexes each miss most of the surface:
a strict ``{cmdab:a:b}`` with a closing-brace anchor finds 9 of 28 options,
because the tail carries the open paren (``{cmdab:ml:abel(}``) or a whole
argument (``{cmdab:xsc:ale(log)}``); a colon-only ``{opt:...}`` finds none at
all, because this file uses the space form throughout, which is the entire
Unsupported section; and "first token of a synopt row" sweeps in the eleven
KPI statistic names, the thirteen server-mode comparison rows and an empty
label. Each rule below exists because one of those failures was measured.

WP-23 closed three gaps the rule above left open.  An option dash invented
passed when it was merely MENTIONED in prose; it now needs a definition
entry -- a {synopt} row, a {phang}/{phang2} entry or the Syntax block.  An
ALIAS passed whenever its full option was documented, so `mlg()` was
honoured with no word of it in the help; now every spelling dash accepts and
twoway does not -- the aliases dash.ado folds into another option, the plot
types dash's expander abbreviates further than twoway, and the options it
declares with a shorter minimum -- must be named in the help beside the
option it stands for.  "twoway does not" is measured, never assumed:
`abbrev_truth.json`, or `alias_spelling_truth.json`
(scripts/extract_alias_spelling_truth.do) for what that file does not
probe, and a spelling neither measured fails until it is.  And in the other
direction, every synonym the help states must be one dash takes.
"""
import json
import os
import re
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from test_abbreviations import (_folds, _program_body,  # noqa: E402
                                _resolves_to, _syntax_options)

_ADO = os.path.join(_HERE, "..", "dash.ado")
_MATA = os.path.join(_HERE, "..", "dash_parse.mata")
_HELP = os.path.join(_HERE, "..", "dash.sthlp")
_TRUTH = os.path.join(_HERE, "fixtures", "abbrev_truth.json")
_SPELLINGS = os.path.join(_HERE, "fixtures", "alias_spelling_truth.json")
_CATCHALL = os.path.join(_HERE, "fixtures", "catchall_options_truth.json")


# ---------------------------------------------------------------------------
# The help side
# ---------------------------------------------------------------------------

# Tables whose rows are values, not options: the KPI statistic list and the
# server-vs-standalone feature comparison. Keyed by the {marker} they follow
# so that moving them does not silently re-admit them.
_NON_OPTION_TABLES = ("kpi_statistics", "mode_comparison")

# Names that look like options but are not: the generated app's CLI flags,
# Stata globals and c() settings, and SMCL's own brace escapes.
_NOT_OPTIONS = re.compile(r"^(?:--|\$|c\(|-\(|\)-)")


def _help_text():
    with open(_HELP, encoding="utf-8") as fh:
        return fh.read()


def _name_from_cmdab(head, tail):
    """`{cmdab:ml:abel(}` is mlabel, min ml. An empty tail (`{cmdab:fmt:}`)
    is legal and means the full name admits no abbreviation."""
    return (head + re.match(r"^[A-Za-z0-9_]*", tail).group(0)).lower()


def _help_options():
    """Every option the help DEFINES, with the minimum it advertises.

    Returns ``{name: set_of_claimed_minimums}``. A name with no ``{cmdab:}``
    anywhere maps to an empty set -- documented, but with no abbreviation
    claim to check.
    """
    lines = _help_text().split("\n")
    syntax_lo, syntax_hi = None, None
    for i, ln in enumerate(lines):
        if ln.startswith("{marker syntax}"):
            syntax_lo = i
        elif syntax_lo is not None and ln.startswith("{marker description}"):
            syntax_hi = i
            break
    assert syntax_lo is not None and syntax_hi is not None, (
        "the Syntax section markers moved; every check below would go blind"
    )

    # Which {marker} each line sits under, so a table can be excluded by
    # section rather than by guessing at its contents.
    section, sections = "", []
    for ln in lines:
        m = re.match(r"\{marker ([a-z_]+)\}", ln)
        if m:
            section = m.group(1)
        sections.append(section)

    # The statistic table lives under {marker kpi} and the comparison table
    # under {marker server_mode}; name them so the exclusion is explicit.
    excluded = {"kpi": "kpi_statistics", "server_mode": "mode_comparison"}

    out: "dict[str, set]" = {}
    in_phang = False
    for i, ln in enumerate(lines):
        stripped = ln.lstrip()
        in_syntax = syntax_lo <= i < syntax_hi
        is_synopt = stripped.startswith("{synopt:")
        # A {phang2} entry may run over several lines, and a grouped entry
        # opens with {ul:...} and lists its options on the lines below. The
        # block ends at the blank line before the next paragraph.
        if stripped.startswith("{phang2}") or stripped.startswith("{phang}"):
            in_phang = bool(re.match(
                r"\{phang2?\}\s*(\{(opt|opth|cmdab|cmd)[: ]|\{ul:)", stripped))
        elif not stripped:
            in_phang = False
        if not (in_syntax or is_synopt or in_phang):
            continue                       # prose: a weaker tier, see below
        if is_synopt and excluded.get(sections[i]) in _NON_OPTION_TABLES:
            continue

        # {cmdab:head:tail...} -- no closing-brace anchor, the tail may carry
        # a paren or a whole argument.
        for head, tail in re.findall(r"\{cmdab:([A-Za-z0-9_]+):([^}]*)", ln):
            name = _name_from_cmdab(head, tail)
            if name and not _NOT_OPTIONS.match(name):
                out.setdefault(name, set()).add(head.lower())
        # {opt name(...)} / {opth name(...)} -- BOTH the colon and the space
        # form; never try to balance the parentheses.
        for name in re.findall(r"\{opth?[: ]\s*,?\s*([A-Za-z_][A-Za-z0-9_]*)",
                               ln):
            if not _NOT_OPTIONS.match(name):
                out.setdefault(name.lower(), set())
        # {cmd:name(} and {cmd:, name(} -- a leading comma introduces a
        # sub-option, which is still a documented name.  {cmd:r(198)} is a
        # return code, not r(): it passed as "accepted" only while dash.ado
        # declared an R() of its own, which WP-23 TR-23.6 removed.
        for name in re.findall(
                r"\{cmd:\s*,?\s*(?!r\(\d+\)\})([A-Za-z_][A-Za-z0-9_]*)\(", ln):
            if not _NOT_OPTIONS.match(name):
                out.setdefault(name.lower(), set())
    return out


#: The SMCL forms that name an option or a plot type, each capturing the
#: name: {cmdab:head:tail}, {opt name}/{opth name} in the colon and the space
#: form, and {cmd:name(} or a bare {cmd:name}, which is how the help writes
#: an alias ({cmd:pbgc()}) and a plot type ({cmd:sc}).
_TOKEN = re.compile(
    r"\{cmdab:(?P<head>[A-Za-z0-9_]+):(?P<tail>[^}]*)"
    r"|\{opth?[: ]\s*,?\s*(?P<opt>[A-Za-z_][A-Za-z0-9_]*)"
    r"|\{cmd:\s*,?\s*(?!r\(\d+\)\})(?P<cmd>[A-Za-z_][A-Za-z0-9_]*)\s*(?=[(}])")


def _option_tokens(text):
    """The option and plot-type names `text' writes in SMCL, in order."""
    out = []
    for m in _TOKEN.finditer(text):
        if m.group("head") is not None:
            out.append(_name_from_cmdab(m.group("head"), m.group("tail")))
        else:
            out.append((m.group("opt") or m.group("cmd")).lower())
    return out


def _help_entries():
    """The help cut into the blocks a synonym must share with its option.

    Returns ``[(kind, section, text)]``.  An entry starts at a blank line, a
    {synopt} row, a {phang}/{phang2} line, a {pstd} or {p ...} paragraph, a
    {title} or a {marker}, and a {synopt} row ends at its {p_end}.  ``kind``
    is "definition" for a {synopt} row, for a {phang}/{phang2} entry that
    opens with an option or a {ul:} heading (the rule _help_options uses)
    and for anything in the Syntax section, and "prose" otherwise.  The KPI
    statistic and server-mode comparison rows are left out, as _help_options
    leaves them out.
    """
    starts = ("{synopt:", "{phang", "{pstd}", "{p ", "{title:", "{marker",
              "{synoptline", "{synoptset")
    excluded = {"kpi", "server_mode"}
    entries, cur, kind, section, where = [], [], None, "", ""

    def flush():
        if cur and not (kind == "synopt" and where in excluded):
            entries.append(("definition" if kind == "synopt"
                            else kind or "prose", where, "\n".join(cur)))

    for ln in _help_text().split("\n"):
        s = ln.lstrip()
        m = re.match(r"\{marker ([a-z_]+)\}", s)
        if m:
            section = m.group(1)
        if not s or s.startswith(starts):
            flush()
            cur, kind, where = [], None, section
            if not s:
                continue
            if section == "syntax":
                kind = "definition"
            elif s.startswith("{synopt:"):
                kind = "synopt"
            elif re.match(r"\{phang2?\}\s*(\{(opt|opth|cmdab|cmd)[: ]|\{ul:)",
                          s):
                kind = "definition"
            else:
                kind = "prose"
        cur.append(ln)
        if kind == "synopt" and "{p_end}" in ln:
            flush()
            cur, kind = [], None
    flush()
    return entries


def _defined_names():
    """Every option name a definition entry writes -- a whole {synopt} row,
    a {phang}/{phang2} entry, the Syntax block."""
    out = set()
    for kind, _, text in _help_entries():
        if kind == "definition":
            out.update(_option_tokens(text))
    return out


def _named_together(spelling, name, sections=()):
    """Does the help name `spelling' as a spelling of `name'?

    Either with {cmdab:spelling:rest}, where spelling+rest is `name', or by
    naming both in one definition entry -- or in any entry of `sections'."""
    for m in _TOKEN.finditer(_help_text()):
        if (m.group("head") and m.group("head").lower() == spelling
                and _name_from_cmdab(m.group("head"), m.group("tail")) == name):
            return True
    for kind, where, text in _help_entries():
        if kind == "definition" or where in sections:
            toks = _option_tokens(text)
            if spelling in toks and name in toks:
                return True
    return False


def _help_synonym_claims():
    """``[(spelling, option, entry)]`` for every synonym the help states.

    An "Abbreviation:" or "Abbreviations:" names spellings of its {synopt}
    row's own option -- the first option the row writes -- unless it pairs
    them, "{cmd:x()} for {cmd:y()}", which it may do anywhere.  A spelling
    that is no abbreviation of its option (pbgc() of plotbgcolor(), mlg()
    of mlabgap()) is written as a synonym -- "Synonym:", "Synonyms, dash's
    own:" or "a synonym, {cmd:mlg()}" -- and read the same way, taking only
    the names written as options, with their parentheses, so that a word
    of the sentence around them ({cmd:twoway}) is not claimed."""
    out = []
    for kind, where, text in _help_entries():
        m = re.search(r"(Abbreviations?:|Synonyms?\b[^:]*?:|a synonym,)"
                      r"(.*?)(?:\{p_end\}|\.\s|\.$|$)", text, re.S)
        if not m:
            continue
        synonym = not m.group(1).startswith("Abbreviation")
        claim = m.group(2)
        pairs = re.findall(r"\{cmd:([a-z0-9_]+)(?:\(\))?\}\s+for\s+"
                           r"\{cmd:([a-z0-9_]+)(?:\(\))?\}", claim)
        if pairs:
            out += [(a, b, text) for a, b in pairs]
        elif text.lstrip().startswith("{synopt:"):
            owner = _option_tokens(text)[0]
            name_rx = (r"\{cmd:([a-z0-9_]+)\(\)\}" if synonym
                       else r"\{cmd:([a-z0-9_]+)(?:\(\))?\}")
            out += [(a, owner, text) for a in re.findall(name_rx, claim)]
    return out


# ---------------------------------------------------------------------------
# The ado side
# ---------------------------------------------------------------------------

_PROGRAMS = ("_dash_parse_plot_opts", "_dash_parse_graph_opts", "_dash_build",
             "_dash_kpi", "_dash_prepare_spec", "_dash_serve_spec",
             # WP-31 B4b: contour's options, read before the plot parser's.
             "_dash_contour_split",
             # WP-31 S34: yvarlabel() and the other options the plot
             # parser's syntax has no room for.
             "_dash_label_split",
             # WP-33 33-06: dash image's caption(), alt() and link().
             "_dash_image")

# Declared by `syntax' for internal plumbing; never typed by a user.  The
# only exceptions to "every spelling dash accepts is documented", each with
# the reason it is not a user's option.  sort1() is not here: it is how
# -syntax- names the argument form of sort(), but twoway's own class file
# declares it the same way and takes sort1(t) as sort(t) (measured,
# alias_spelling_truth.json), so the redirect to twoway covers it.
_INTERNAL = {
    "specpath": "_dash_prepare_spec and _dash_serve_spec: the spec file "
                "path _dash_build and _dash_serve hand them",
    "datapath": "_dash_prepare_spec and _dash_serve_spec: the data file "
                "path _dash_build and _dash_serve hand them",
    "cmdname":  "_dash_prepare_spec: the subcommand (build or serve) that "
                "called it, for its messages",
    "inherit":  "_dash_prepare_spec: set by _dash_serve_spec so the options "
                "of an earlier dash build carry over",
    "renderpy": "_dash_do_render: the path of dash_render.py",
    "spec":     "_dash_do_render and _dash_browser_wanted: the spec path "
                "or text",
    "data":     "_dash_do_render: the data file path",
    "output":   "_dash_do_render: the HTML or .py path to write",
    "mode":     "_dash_do_render: standalone or server",
}


def _ado_text():
    with open(_ADO, encoding="utf-8") as fh:
        return fh.read()


def _ado_declarations():
    """``{name: declared_minimum}`` over every user-facing syntax statement."""
    src = _ado_text()
    out = {}
    for prog in _PROGRAMS:
        body = _program_body(src, prog)
        assert body, f"program {prog} not found; the parser is looking in the wrong place"
        for mn, full in _syntax_options(body):
            if full not in _INTERNAL:
                out.setdefault(full, mn)
    return out


def _pending(prog):
    src = _ado_text()
    i = src.index("program define " + prog)
    j = src.index("local _dash_unknown", i)
    return set(re.findall(r"_dash_pending' (\w+)\"", src[i:j]))


def _ignored_options():
    return _pending("_dash_parse_plot_opts") | _pending("_dash_parse_graph_opts")


def _unsupported_section():
    """Option names listed under the help's Unsupported heading."""
    h = _help_text()
    i = h.index("{marker unsupported}")
    j = h.index("{marker dependencies}", i)
    # An {opt} inside a {phang2} ENTRY defines an option; an {opt} in a
    # {pstd} paragraph is prose. A grouped entry opens with {ul:Heading.} and
    # lists its options on the lines below, so the block runs from the
    # {phang2} to the blank line that ends it. Cross-references inside an
    # entry are written {cmd:...}, which is not collected here.
    out, in_entry = set(), False
    for ln in h[i:j].split("\n"):
        stripped = ln.lstrip()
        if stripped.startswith("{phang2}") or stripped.startswith("{phang}"):
            in_entry = True
        elif not stripped or stripped.startswith("{pstd}"):
            in_entry = False
        if in_entry:
            out.update(n.lower() for n in re.findall(
                r"\{opth?[: ]\s*([A-Za-z_][A-Za-z0-9_]*)", stripped))
    return out


def _undeclared_twoway_options():
    """The spellings of `_dash_rep_und_tab`'s rows (dash_parse.mata) that no
    syntax statement of dash.ado declares: twoway options dash leaves to the
    catch-all, each of which test/fixtures/catchall_options_truth.json must
    have probed.  The first two columns of each row are the option and the
    spelling (noX for the no half of a pair); a pair is declared when either
    half is."""
    with open(_MATA, encoding="utf-8") as fh:
        src = fh.read()
    i = src.index("string matrix _dash_rep_und_tab()")
    j = src.index("return(t)", i)
    decl = _ado_declarations()
    out = set()
    for opt, full in re.findall(
            r't = t \\ \("([a-z0-9_]+)",\s*"([a-z0-9_]+)"', src[i:j]):
        if not ({opt, full, "no" + opt} & set(decl)):
            out.add(full)
    return out


def _catchall_truth():
    with open(_CATCHALL, encoding="utf-8") as fh:
        return json.load(fh)


def _catchall_options():
    """twoway options dash takes once and names in its note without a
    pending declaration (measured: scripts/extract_catchall_options_truth.do)."""
    return set(_catchall_truth()["options"])


def _twoway_options():
    """Options probed against real twoway, so covered by the help's redirect."""
    with open(_TRUTH, encoding="utf-8") as fh:
        return set(json.load(fh)["options"])


def _abbrev_truth():
    with open(_TRUTH, encoding="utf-8") as fh:
        return json.load(fh)


def _spelling_truth():
    """twoway's verdict on the spellings abbrev_truth.json does not probe;
    written by scripts/extract_alias_spelling_truth.do."""
    with open(_SPELLINGS, encoding="utf-8") as fh:
        return json.load(fh)


def _dashonly_refused():
    """Every spelling of _dash_dashonly_list() (dash_parse.mata), from its
    minimum to its full name: the spellings twoway refuses that dash took,
    refused since WP-35 DT-15 as twoway refuses them (DECISIONS.md P4-7,
    D53).  The help names them only in the dashonly paragraph, to say so."""
    src = open(_MATA, encoding="utf-8").read()
    i = src.index("string matrix _dash_dashonly_list()")
    body = src[i:src.index("\n}\n", i)]
    out = set()
    for full, mn in re.findall(
            r'"([^"]*)", "([^"]*)", "[^"]*", "[^"]*", "[^"]*"', body):
        out |= {full[:L] for L in range(len(mn), len(full) + 1)}
    return out


def _fold_aliases():
    """``{alias: {target, ...}}`` for every option dash.ado folds into another.

    Two shapes, both read from the code rather than listed here: the
    ``if "`a'" != "" & "`t'" == "" local t "`a'"`` folds of the two option
    parsers, and the s() folds of the _dash_fold_* programs, which read an
    option's value out of s() and write it back under another name once the
    plot type is known -- bw() into bwidth() or barwidth().  Each is read in
    the form that copies through compound quotes and in the form that
    copies by value (``mata: st_local("v", st_global("s(o)"))``,
    ``sreturn local t : copy local v``), which dash.ado uses since
    24sep2026: a copy through the quotes expanded a macro in the user's
    text again (test_json_escaping.cscript JSE-69)."""
    src = _ado_text()
    out = {}
    for prog in ("_dash_parse_plot_opts", "_dash_parse_graph_opts"):
        for alias, target in _folds(_program_body(src, prog)):
            out.setdefault(alias, set()).add(target)
    reads = (r"""^\s*local (\w+) `"`s\((\w+)\)'"'""",
             r"""^\s*mata: st_local\("(\w+)", st_global\("s\((\w+)\)"\)\)""")
    writes = (r"""\bsreturn local (\w+)\s+`"`%s'"'""",
              r"""\bsreturn local (\w+)\s+: copy local %s\b""")
    for prog in re.findall(r"^program define (_dash_fold_\w+)", src, re.M):
        body = _program_body(src, prog)
        for rd in reads:
            for loc, opt in re.findall(rd, body, re.M):
                for wr in writes:
                    for target in re.findall(wr % re.escape(loc), body):
                        if target != opt:
                            out.setdefault(opt, set()).add(target)
    return out


def _plottype_minimums():
    """``{plot type: shortest spelling dash takes}``, from the table in
    dash_parse.mata's _dash_expand_plottype_str."""
    with open(_MATA, encoding="utf-8") as fh:
        src = fh.read()
    i = src.index("string scalar _dash_expand_plottype_str(")
    j = src.index("\n}\n", i)
    return dict(re.findall(r'\("([a-z]+)",\s*"([a-z]+)"\)', src[i:j]))


def _twoway_takes(spelling, option):
    """True if twoway takes `spelling' as `option', False if it measurably
    does not, None if neither fixture measured it.

    abbrev_truth.json's min_abbrev is the shortest prefix twoway accepts AND
    resolves to the option, so a shorter prefix is not the option in twoway;
    alias_spelling_truth.json holds the rest, per plot-type context (a
    spelling twoway takes in one context, as bw() is bwidth() on lpoly, is
    twoway's)."""
    truth = _abbrev_truth()
    e = truth["options"].get(option)
    if e and option.startswith(spelling):
        return len(spelling) >= len(e["min_abbrev"])
    rows = [r for r in _spelling_truth()["options"].get(spelling, [])
            if r["target"] == option]
    if any(r["twoway_accepts"] for r in rows):
        return True
    if rows and all(r["twoway_accepts"] is False for r in rows):
        return False
    r = truth["abbrev_resolution"].get(spelling) or {}
    if r.get("stata_resolves_to"):
        return r["stata_resolves_to"] == option
    if "rejects" in (r.get("status") or ""):
        return False
    return None


def _twoway_takes_plottype(spelling, ptype):
    """The same for a plot type."""
    probe = _spelling_truth()["plottypes"].get(ptype, {}).get(
        "probes", {}).get(spelling)
    if probe is not None:
        return probe["twoway_accepts"]
    e = _abbrev_truth()["plottypes"].get(ptype)
    if e and ptype.startswith(spelling):
        return len(spelling) >= len(e["min_abbrev"])
    return None


#: WP-31 B4b: contour's own options, each drawn by twoway contour or
#: contourline rc 0 in test/fixtures/contour_truth.json (the probe that
#: typed it in full).
_CONTOUR_PROBES = {
    "ccuts": ("draw", "ccuts"), "levels": ("draw", "levels5"),
    "minmax": ("draw", "levels5_minmax"), "crule": ("draw", "crule_hue"),
    "scolor": ("draw", "scolor_only"), "ecolor": ("draw", "crule_linear"),
    "ccolors": ("draw", "ccolors"), "clabels": ("draw", "clabels"),
    "format": ("draw", "format"), "interp": ("draw", "interp_shepard"),
    "reversekey": ("draw", "reversekey"), "clwidths": ("line", "clwidths"),
    "clpatterns": ("line", "clpatterns"),
    "colorlines": ("line", "colorlines"),
}


def _contour_takes(name):
    probe = _CONTOUR_PROBES.get(name)
    if probe is None:
        return False
    with open(os.path.join(_HERE, "fixtures", "contour_truth.json"),
              encoding="utf-8") as fh:
        truth = json.load(fh)
    return truth[probe[0]][probe[1]]["rc"] == 0


def _twoway_spelling(name):
    """Does twoway take `name' as an option, or as an abbreviation of one,
    in any context a fixture measured?  Then the help's redirect covers it."""
    if _contour_takes(name):
        return True
    truth = _abbrev_truth()
    if any(o.startswith(name) and len(name) >= len(e["min_abbrev"])
           for o, e in truth["options"].items()):
        return True
    return any(r["twoway_accepts"]
               for r in _spelling_truth()["options"].get(name, []))


def _dash_takes(spelling, option):
    """Does dash take `spelling' as `option' -- a fold, or the option the
    plot or graph parser binds the spelling to on first use?"""
    if option in _fold_aliases().get(spelling, ()):
        return True
    src = _ado_text()
    return any(
        _resolves_to(spelling, _syntax_options(_program_body(src, p))) == option
        for p in ("_dash_parse_plot_opts", "_dash_parse_graph_opts"))


# ---------------------------------------------------------------------------
# Guards on the parsers themselves
# ---------------------------------------------------------------------------

class TestTheParsersFoundSomething:
    """Every assertion below is vacuous if a parser silently returns little."""

    def test_the_help_parser_finds_the_whole_surface(self):
        found = _help_options()
        assert len(found) >= 50, (
            f"only {len(found)} options parsed out of dash.sthlp; the naive "
            f"regexes found 9-17, so this parser has regressed to one of them"
        )
        # The floor above only tells this parser from the naive ones.
        # Measured 24sep2026: 134 names, and losing any one of its readers
        # still clears 50 -- 116 without {cmd:name(} (eighteen names, among
        # them graphregion, plotregion, lcolor and format, which no other
        # guard here looks for), 76 without the space form of {opt}, 85
        # without the {phang} entries, 90 without the {synopt} rows.  The
        # count is pinned: a change to the help that adds or drops a
        # definition moves it on purpose, and is re-measured here.  138
        # since the S3 batch's ci band: acolor(), alcolor(), alwidth() and
        # alpattern(), twoway's fitarea options.  143 since WP-28 batch 2
        # (S16, GAPS2 X2): colorlevels(), colorvarminmax, zlabel(),
        # ztitle() and zscale() (measured 30sep2026).  147 since WP-29
        # P0.5 documented ytick2(), xtick2(), yline2() and xline2().  149
        # since WP-29 P0.9 documented lpolyci's pwidth() and var().  150
        # since WP-30 batch 5's help names yaxis() as an option.  152 since
        # WP-30 P1.5 documented xvarformat() and yvarformat().  158 since
        # WP-30 P1.14a: the ten named styles' rows, less the Unsupported
        # entry's four.
        # 158 -> 161: P1.14b's Unsupported entry names dstyle(),
        # dlstyle() and bmlinestyle().
        # 161 -> 162: P1.8a's cmissings() entry.
        # 162 -> 163: P1.8b's Recast entry adds recastas() and type() and
        # the Unsupported entry's recast() leaves; 163 -> 165: P1.31a's
        # dash serve maxsessions() and idletimeout().
        # 165 -> 166: P1.9a's Orientation entry names xaxis(2) beside
        # yaxis(2) (horizontal and vertical move there from Unsupported).
        # 166 -> 173: P1.6's time-axis rows name the seven t-options
        # (tmlabel() and tmtick() in the Unsupported entry too).
        # 173 -> 178: P1.6's tlabel2() .. ttitle2() rows.
        # 178 -> 177: P1.10 text() drawn, its Unsupported entry gone (the
        # Added text paragraph is prose under Plot types).
        # 177 -> 179: P1.10 part 2's ttext() entry defines ttext() and
        # text().
        # 179 -> 183: C1 the Arrowheads entries define mangle(),
        # barbsize() and headlabel, and name mfcolor() in barbsize()'s.
        # 183 -> 184: A4 the Unsupported entry defines mlalign().
        # 184 -> 192: C4 the Fit options entry defines atobs, nofit,
        # fitplot(), ciplot(), smoothplot(), estopts(), predopts(), estcmd();
        # 192 -> 198: C5 the synopt entries of gap() baroffset() area()
        # boundary droplines() nodropbase.
        # 198 -> 208: C8b the synopt entries of colorrule() colorstart()
        # colorend() colorfillonly colorformissing() colorkeysrange
        # colorkeysreverse colorallowmultiple colorotherlabel() and the
        # graph options clegend() plegend() pcycle(); colorlist() and
        # coloruseplegend leave Unsupported for synopt entries.
        # 208 -> 217: B5b the synopt entries of dotextend() ndots()
        # dsymbol() dcolor() dfcolor() dsize() dlcolor() dlwidth() and the
        # Unsupported entry's dlalign() (dstyle() and dlstyle() move).
        # 217 -> 219: D1 the Unsupported entry "Minor ticks and minor
        # labels" goes (xmtick() .. tmtick()) and four synopt rows define
        # ymtick2() ymlabel2() xmtick2() xmlabel2().
        # 219 -> 221: B4b the Unsupported entry "Contour options" names
        # two contour options; 221 -> 211: D2 the Unsupported entry
        # "Alternative titles" goes.
        # 211 -> 213: D8 the yvarlabel() xvarlabel() entry.
        # 213 -> 216: C17 the mlabprefix() mlabsuffix() and lalign() entries.
        # 216 -> 217: E3 the mlalign() mlabstyle() entry adds mlabstyle().
        # 217 -> 216: E2 mlpattern() leaves the Unsupported list.
        # 216 -> 217: H2t the Data tables entry defines table; 217 -> 218:
        # H2f filter()'s direction() entry.
        # 218 -> 219: H2l the dash build syntax and synopt define brush().
        # 219 -> 272: J1 the 53 twoway options that reach the catch-all
        # (catchall_options_truth.json) are listed under Unsupported.
        # 272 -> 266: WP-32 at() blabel() ciopts() fitopts() lineopts()
        # mlabwidth() leave the Unsupported entries: refused, as twoway
        # refuses them (noted_option_truth.json).
        # 266 -> 265: WP-32 play() leaves the Not drawn entry.
        # 265 -> 265: WP-32 two contour options leave the Unsupported
        # entries for two entries of the contour paragraph.
        # 265 -> 266: dash image's alt() (WP-33 33-06).
        # 266 -> 265: WP-35 syn:SD-20c symbol() leaves the Unsupported
        # list (read as msymbol()); subchar() left it and joined the
        # synopts (stat:PT-6), one for one.
        # 265 -> 266: syn:SD-22 the contour note defines levels() (WP-35 35-06).
        # 265 -> 237: WP-35 DT-15 the definitions of the 28 options twoway
        # refuses that dash took (ytitle2() .. ttitle2(), malpha(), lalpha(),
        # falpha(), jseed(), marker(), plotbgcolor(), colpalette(),
        # colornlevels(), colormissing()) leave the help: dash refuses them.
        # 266 -> 265: WP-35 stat:PT-8 weight leaves the Unsupported list
        # (lowess weight taken silently).
        # 237 -> 236: WP-37 D65 a contour option's definition leaves.
        assert len(found) == 236, (
            f"{len(found)} options parsed out of dash.sthlp, 236 measured "
            f"30oct2026: a reader of the parser lost a form, or the help "
            f"gained or lost a definition and this count must follow it"
        )

    def test_the_help_parser_handles_a_paren_carrying_tail(self):
        """{cmdab:ml:abel(} -- the construct that defeats a brace anchor."""
        assert "mlabel" in _help_options()

    def test_the_help_parser_handles_an_argument_carrying_tail(self):
        """{cmdab:xsc:ale(log)} -- a whole argument inside the directive."""
        assert "xscale" in _help_options()

    def test_the_help_parser_handles_the_space_form_of_opt(self):
        """The entire Unsupported section uses `{opt name(...)}`."""
        assert "recast" in _help_options()

    def test_the_help_parser_handles_an_empty_cmdab_tail(self):
        """{cmdab:fmt:} means fmt, which admits no abbreviation."""
        assert "fmt" in _help_options()

    def test_the_help_parser_excludes_the_statistic_table(self, monkeypatch):
        """The KPI statistic rows are values, not options."""
        found = _help_options()
        assert "dcount" not in found and "median" not in found
        # The table writes its rows {synopt:{cmd:dcount}}, and no reader of
        # _help_options takes a bare {cmd:name} -- its {cmd: form wants the
        # "(" -- so the check above held with the exclusion of the table
        # deleted (measured 24sep2026: the same 134 names either way).  The
        # exclusion is what keeps the rows out once a reader takes them, as
        # _TOKEN already does, so it is tried on a row every reader takes:
        # {opt dcount} under {marker kpi} must be dropped, and the same row
        # under another section read -- the control that the row is seen.
        def parsed(section):
            text = ("{marker syntax}\n{marker description}\n"
                    "{marker %s}\n{synopt:{opt dcount}}number of distinct "
                    "non-missing values{p_end}\n" % section)
            monkeypatch.setattr(sys.modules[__name__], "_help_text",
                                lambda: text)
            return _help_options()
        assert "dcount" in parsed("filters"), (
            "the control row {synopt:{opt dcount}} was not read at all, so "
            "the exclusion below proves nothing")
        assert "dcount" not in parsed("kpi"), (
            "a {synopt} row of the KPI statistic table was read as an "
            "option: the exclusion of the table no longer holds")

    # The floors these were ("at least 120", "at least 20", "at least 3", ...)
    # told a reader that found something from one that found nothing, and
    # no more: a reader that lost part of what it reads cleared them.  Each
    # count below was measured 24sep2026, with the break each floor let
    # through; a change to dash.ado or the help that moves one moves it on
    # purpose, and is re-measured here.

    def test_the_ado_parser_finds_the_whole_surface(self):
        # 167 options.  _dash_kpi's syntax moved into a helper program,
        # _dash_kpi left calling it, took the two options only it declares
        # out of the scan: 165, above "120", and the check that every
        # dash-only option is documented no longer saw them.  (The plot
        # parser alone declares 90 options no other program does.)  171
        # since the S3 batch declared the four fitarea options.  176 since
        # WP-28 batch 2 (S16) declared colorlevels, colorvarminmax, zlabel,
        # ztitle and zscale (measured 30sep2026).  180 since WP-29 P0.5
        # declared ytick2, xtick2, yline2 and xline2.  182 since WP-30 P1.5
        # declared xvarformat and yvarformat.  188 since WP-30 P1.14a
        # declared astyle, alstyle, bstyle, blstyle, clstyle and p.
        # 188 -> 191: P1.14b declared dstyle, dlstyle and bmlinestyle.
        # 191 -> 192: P1.8a declared cmissings(), twoway's spelling.
        # 192 -> 194: P1.8b declared recastas() and type(); 194 -> 196:
        # P1.31a declared maxsessions() and idletimeout().
        # 196 -> 203: P1.6 declared the seven time-axis options.
        # 203 -> 208: P1.6 part 2 declared tlabel2() .. ttitle2().
        # 208 -> 209: P1.10 part 2 declared ttext().
        # 209 -> 212: C1 mangle barbsize headlabel declared; 212 -> 213: C2
        # mwidth declared
        # 213 -> 214: A4 mlalign declared
        # 214 -> 222: C4 atobs estopts predopts estcmd fitplot ciplot
        # smoothplot nofit declared; 222 -> 228: C5 gap baroffset area
        # boundary droplines nodropbase declared
        # 228 -> 240: C8b colorstart colorend colorrule colorfillonly
        # colorformissing colorkeysrange colorkeysreverse
        # colorallowmultiple colorotherlabel clegend plegend pcycle declared
        # 240 -> 249: B5b the nine dot options declared
        # 249 -> 253: D1 xmlabel2 ymlabel2 xmtick2 ymtick2 declared
        # 253 -> 269: B4b contour's sixteen options (_dash_contour_split)
        # 269 -> 271: D8 yvarlabel xvarlabel declared (_dash_label_split)
        # 271 -> 274: C17 mlabprefix mlabsuffix lalign declared there
        # 274 -> 275: E3 mlabstyle declared there
        # 275 -> 277: H2t table and table2 declared (both parsers and
        # _dash_label_split)
        # 277 -> 278: H2l brush() declared by dash build's syntaxes
        # 278 -> 279: dash image's alt() (WP-33 33-06).
        # 279 -> 280: WP-35 stat:PT-6 function's subchar() declared
        # 280 -> 282: WP-37 stat:PT-12 xlog and xtransform() declared
        # (_dash_label_split).
        # 282 -> 281: WP-37 D65 a contour flag leaves _dash_contour_split.
        assert len(_ado_declarations()) == 281

    def test_the_ignored_list_was_found(self):
        # 44 names, all of them in the plot parser's list (the graph
        # parser's 23 are among them).  The plot parser initialising
        # `_dash_unknown' at its top, before that list, ended the scan of
        # the parser there: 23, above "20".  48 since the S3 batch named
        # the four fitarea options off the ci types.
        # Flipped (WP-30 P1.14a): 48 -> 44, the four named styles drawn.
        # 44 -> 47: P1.14b dstyle, dlstyle and bmlinestyle, kept and named.
        # Flipped (WP-30 P1.24): 47 was wrong because twoway draws
        # mlabvposition() per row (mlabvpos_truth.json A).
        # 47 -> 46: P1.24 mlabvposition() honoured
        # 46 -> 45: P1.24 mlabtextstyle() honoured (part 2)
        # 45 -> 44: P1.8b recast() honoured
        # 44 -> 42: P1.9a horizontal drawn, vertical silent
        # 42 -> 44: P1.6 tmlabel() and tmtick() stored and named
        # 44 -> 43: P1.10 text() drawn
        # 43 -> 44: A4 mlalign() declared and named
        # 44 -> 42: C6 cmissing() and connect() drawn everywhere
        # 42 -> 40: C8b colorlist() and coloruseplegend drawn
        # 40 -> 39: B5b dstyle() dlstyle() drawn, dlalign() named
        # 39 -> 33: D1 xmlabel xmtick tmlabel tmtick ymlabel ymtick drawn
        # 33 -> 35: B4b two contour options named; 35 -> 25: D2
        # the eight edge titles drawn, title2() and subtitle2() refused
        # 25 -> 20: D5 fxsize fysize scale xoverhangs yoverhangs drawn;
        # 20 -> 19: E3 mlalign() read by the renderer
        # 19 -> 18: E2 mlpattern() taken as twoway draws it (solid)
        # 18 -> 10: WP-32 at blabel ciopts filter fitopts link lineopts
        # mlabwidth refused, as twoway refuses them
        # 10 -> 9: WP-32 play() refused, as twoway refuses a recording it
        # cannot find or read
        # 9 -> 7: WP-32 two contour options drawn
        assert len(_ignored_options()) == 7

    def test_the_unsupported_section_was_found(self):
        # 44 names.  A blank line inside the first grouped entry of the
        # Unsupported section ended that entry after its first line: 37,
        # above "3".  48 with the fitarea options' entry (S3 batch).
        # Flipped (WP-30 P1.14a): 48 -> 44, the Named styles entry gone.
        # 44 -> 47: P1.14b's Dot and marker back-line styles entry.
        # Flipped (WP-30 P1.24): 47 was wrong because twoway draws
        # mlabvposition() per row (mlabvpos_truth.json A).
        # 47 -> 46: P1.24 mlabvposition() honoured
        # 46 -> 45: P1.24 mlabtextstyle() honoured, its entry gone
        # 45 -> 44: P1.8b recast() honoured; its residual is cross-referenced
        # 44 -> 42: P1.9a horizontal drawn, vertical silent; the entry is
        # "Bar labels and positions"
        # 42 -> 44: P1.6 names tmlabel() and tmtick() in "Minor ticks and
        # minor labels"
        # 44 -> 43: P1.10 text() drawn, its entry gone
        # 43 -> 44: A4 mlalign() in the marker outline entry
        # 44 -> 42: C6 cmissing() and connect() leave the "Not drawn" entry
        # 42 -> 40: C8b the "colorvar() sub-options" entry goes
        # 40 -> 39: B5b dstyle() and dlstyle() leave it with their entry,
        # dlalign() joins the marker outline entry
        # 39 -> 33: D1 the "Minor ticks and minor labels" entry goes
        # 33 -> 35: B4b the "Contour options" entry, two contour options;
        # 35 -> 25: D2 the "Alternative titles" entry goes
        # 25 -> 20: D5 the "Sizing for graph combine" and "Room for long
        # end labels" entries go; 20 -> 19: E3 mlalign() leaves the
        # Unsupported entry.  19 -> 18: E2 mlpattern() leaves it.
        # 18 -> 71: J1 the 53 names that reach the catch-all join the 18
        # pending ones (catchall_options_truth.json).
        # 71 -> 63: WP-32 the eight options twoway refuses on every type
        # leave it (at blabel ciopts filter fitopts link lineopts mlabwidth).
        # 63 -> 62: WP-32 play() leaves it (refused; prose says so).
        # 62 -> 60: WP-32 the Contour options entry goes (its two options
        # drawn).
        # 60 -> 59: WP-32 baroffset() on rbar beside mwidth drawn
        # (catchall_options_truth.json re-extracted).
        # 59 -> 58: WP-35 stat:PT-6 subchar() drawn on function
        # 58 -> 57: WP-35 syn:SD-20c symbol() read as msymbol()
        # 57 -> 56: WP-35 GW-3 maxaxes() checked
        # 56 -> 55: WP-35 stat:PT-8 lowess weight taken
        # 55 -> 53: WP-37 stat:PT-12 xlog and xtransform() drawn on lfit
        # and lfitci, taken silently on qfit, qfitci and fpfitci
        # (catchall_options_truth.json re-extracted).
        assert len(_unsupported_section()) == 53

    def test_the_undeclared_table_was_found(self):
        # WP-31 J1: 29 spellings of _dash_rep_und_tab's 52 rows are declared
        # by no syntax statement (measured 18oct2026); fewer than 20 means
        # the reader lost the table.
        assert len(_undeclared_twoway_options()) >= 20

    def test_the_catchall_fixture_was_found(self):
        d = _catchall_truth()
        assert sorted(d["_meta"]) == ["born_date", "dash_commit",
                                      "extracted", "source", "stata_version"]
        assert d["_meta"]["source"] == \
            "scripts/extract_catchall_options_truth.do"
        assert len(d["options"]) >= 20

    def test_the_token_reader_reads_every_form(self):
        assert _option_tokens(
            "{cmdab:ml:abel(} {opt jitter(#)} {opt:colordiscrete} "
            "{opth by(varlist)} {cmd:pbgc()} {cmd:sc}, {cmd:. dash}") == [
            "mlabel", "jitter", "colordiscrete", "by", "pbgc", "sc"]

    def test_the_entry_parser_cuts_the_help_into_entries(self):
        entries = _help_entries()
        defs = [t for k, _, t in entries if k == "definition"]
        # 320 definition entries (WP-27 added the saving() paragraph and
        # the $dash_max_bytes row; the S3 batch the scheme's Reference
        # lines paragraph; 321 with the fitarea options' Unsupported
        # entry).  330 since WP-28 batch 2 (measured 30sep2026): S16's
        # five colorvar()/colour-key rows (colorlevels, colorvarminmax,
        # zlabel, ztitle, zscale) and S14's four axis-rule rows (a/b,
        # x y to z, # "text", #N numlist); the B7, X1/E2 and S14 edits
        # to xtitle2, ytitle2, type(dropdown), exclude() and a(b)c
        # rewrote entries without adding any.  331 with S15's legend
        # lastlabel() row (GAPS2 B5).  The six rows of the
        # second-axis table
        # written as {p2col:} rows, which the cutter starts no entry at,
        # left 311 -- above "150", with those rows read as prose.
        # 335 with WP-29 P0.5's four second-axis rows (ytick2, xtick2,
        # yline2, xline2); 337 with P0.2's two by() rescale rows; 339 with
        # P0.9's pwidth() and var() rows; 340 with WP-30 P1.35's {ul:Stata}
        # Dependencies paragraph (the Stata 19 floor); 346 with WP-30
        # P1.25a's six scheme rows (meta ... stgcolor_mv); 347 with WP-30
        # P1.27's {ul:Batch and set graphics off.} paragraph; 348 with WP-30
        # P1.5's xvarformat()/yvarformat() entry; 350 with WP-30 P1.15a's
        # two by() text rows (title() subtitle() note() caption(), note(""));
        # 352 with WP-30 P1.11b's two {ul:Text in graphs.} paragraphs.
        # 361 with WP-30 P1.14a's ten named-style rows, less the
        # Unsupported Named styles entry.
        # 361 -> 363: P1.14b's {ul:Named styles.} scheme paragraph and
        # its Unsupported Dot and marker back-line styles entry.
        # 363 -> 364: P1.24's mlabv:position() row.
        # 364 -> 367: WP-30 P1.20a's Region Styling rows (ten for seven:
        # each drawn sub-option, the graph region and the canvas).
        # 367 -> 368: WP-30 P1.21a's $dash_max_reflines row.
        # 368 -> 369: P1.8a's cmissings() entry.
        # 369 -> 372: P1.7's {ul:Time-series operators.} paragraph and
        # its example's lines.
        # 372 -> 373: P1.8b's {ul:Recast.} entry; 373 -> 375: P1.31a's
        # maxsessions() and idletimeout() rows; 375 -> 377: P1.20b's
        # plotregion(margin()) and ifcolor() rows; 377 -> 383: P1.15b's
        # six by() rows (rows(), holes(), colfirst, compact, iscale(),
        # imargin()); 383 -> 384: P1.9a's {ul:Orientation.} entry (the
        # Unsupported entry it replaces stays, as "Bar labels and positions").
        # 384 -> 391: P1.6's seven time-axis option rows; 391 -> 396: its
        # five axis-2 rows (part 2).
        # 396 -> 402: P1.15c's six by() rows (iyaxes ixaxes, noedgelabel,
        # noytitles noxtitles, legend(), ilegends, clegend(on)).
        # WP-30 P1.28b: 402 -> 403, the toolbar's Save as SVG row.
        # 403 -> 404: P1.10's Added text paragraph under Plot types.
        # 404 -> 405: P1.10 part 2's ttext() entry.
        # WP-30 P1.27: 405 -> 407, the nodraw and graph-prefix differences.
        # 407 -> 410: C1 the three Arrowheads entries under Plot types.
        # 410 -> 397: A2 the Synonyms table's thirteen entries went (dash
        # takes no plot-type spelling twoway refuses).
        # 397 -> 398: C4 the Fit options entry; 398 -> 404: C5 the six
        # synopt entries gap() .. nodropbase.
        # 404 -> 417: C8b eleven colorvar synopt entries and three graph
        # ones, less the Unsupported entry they replace.
        # 417 -> 427: B5b the ten synopt entries dotextend() .. dlwidth().
        # 427 -> 428: B1 the Plot types table's "range with a point" row.
        # 428 -> 431: D1 four synopt rows ymtick2() .. xmlabel2(), less
        # the Unsupported entry "Minor ticks and minor labels".
        # 431 -> 433: B4b the Plot types table's "surface" row and the
        # Unsupported entry "Contour options"; 433 -> 432: D2 the
        # Unsupported entry "Alternative titles" goes.
        # 432 -> 437: D4 five synopt rows holes() .. textwidth().
        # 437 -> 439: D5 four sizing entries (aspectratio(), scale(),
        # fysize()/fxsize(), the overhangs), less the two Unsupported
        # entries "Sizing for graph combine" and "Room for long end labels";
        # 439 -> 440: D8 the yvarlabel() xvarlabel() entry.
        # 440 -> 442: C17 the mlabprefix() mlabsuffix() and lalign() entries.
        # 442 -> 443: E3 the mlalign() mlabstyle() entry.
        # 443 -> 444: D14 the Tabs example of a tab's own layout().
        # 444 -> 447: H2t the Data tables entries (table, table(rows(#)
        # open)) and the $dash_max_table_rows row; 447 -> 449: H2f
        # filter()'s type(multi) and direction() entries.
        # 449 -> 450: H2l the brush() synopt entry.
        # 450 -> 452: H2k the weighted KPI example's two lines.
        # 452 -> 453: H2x the toolbar table's Save dashboard entry.
        # 453 -> 462: J1 nine Unsupported entries for the names that reach
        # the catch-all (Area, bar and line edge styles .. Graph-wide
        # settings).
        # 462 -> 466: J2 the Linking section's four example lines.
        # 466 -> 468: I2 the Installation section's net install and
        # dash_setup lines.
        # 468 -> 465: WP-32 the Options of other commands, Bar labels and
        # Build-time options entries go (refused, as twoway refuses them).
        # 465 -> 466: WP-32 the Contour options entry goes, the contour
        # paragraph's two option entries come.
        # 466 -> 464: the $dash_max_cells and $dash_max_bytes rows removed (WP-33 33-15)
        # 464 -> 467: dash image's syntax line, Image panels section and $dash_max_images row (WP-33 33-06)
        # 467 -> 474: the Graphs from several frames paragraph (WP-33 33-07)
        # 474 -> 475: syn:SD-3 the p1() to p20() Differences entry (WP-35 35-02)
        # 475 -> 476: the Differences entry Plot-type names in lower case
        # only (WP-35 plot:PT-3)
        # 476 -> 477: WP-35 stat:PT-6 the subchar(name) synopt
        # 477 -> 478: syn:SD-22 the Differences entry contour with levels()
        # (WP-35 35-06)
        # 478 -> 450: WP-35 DT-15 the entries of the 28 refused options leave.
        # 450 -> 449: WP-37 D65 a contour option's entry leaves.
        # old -> new: 449 -> 450: syn:SD-17 the Differences item A dashboard
        # is not a Stata graph's sub-point name() registers (WP-38 38-01).
        # old -> new: 450 -> 451: GW-12 its sub-point No graph memory.
        # old -> new: 451 -> 452: ECO-1 its sub-point Data at build.
        # old -> new: 452 -> 453: ECO-4 its sub-point graph combine.
        assert len(defs) == 453, (  # 352 -> 361: P1.14a Named styles
            f"{len(defs)} definition entries cut out of dash.sthlp, 453 "
            f"measured 30oct2026")
        # Flipped (WP-35 DT-15): the entry of plotbgcolor() and pbgc() left
        # the help, as dash refuses both as twoway refuses them (P4-7).
        assert not any("pbgc" in _option_tokens(t) for t in defs), (
            "an entry still defines pbgc()")
        assert any("plotregion" in _option_tokens(t) for t in defs)
        assert not any("dcount" in _option_tokens(t) for t in defs), (
            "the KPI statistic table was read as option entries")
        assert any(k == "prose" for k, _, _ in entries)

    def test_the_fold_scan_finds_the_aliases(self):
        aliases = _fold_aliases()
        # 12 aliases.  One fold written in plain quotes rather than
        # compound ones -- `if "`xla2'" != "" ...' -- is no fold the scan
        # reads: 11, above "10", and the check that the help names xla2()
        # beside xlabel2() never asked about it.
        assert len(aliases) == 12, f"{len(aliases)} folds found, 12 measured"
        assert aliases.get("mlg") == {"mlabgap"}
        assert aliases.get("bins") == {"bin"}
        # Flipped (WP-35 stat:PT-14): bw() read as barwidth() was wrong
        # because twoway refuses bw() off the bandwidth types (P4-7);
        # _dash_fold_bw folds it into bwidth() alone.
        assert aliases.get("bw") == {"bwidth"}, (
            "the s() fold of _dash_fold_bw was not read")

    def test_the_plot_type_table_was_found(self):
        mins = _plottype_minimums()
        assert len(mins) >= 38, f"only {len(mins)} plot types read"
        assert mins.get("scatter") == "sc" and mins.get("pcarrowi") == "pcarrowi"
        # Measured 24sep2026: 40 rows, one for each of the 40 plot types
        # the renderer draws, so the floor of 38 passed with two rows gone
        # and a type whose row is missing is never asked about below.  The
        # table read must name exactly the types dash draws.
        import dash_render as dr
        drawn = dr._dash_plot_type_names()
        assert set(mins) == drawn, (
            f"plot types dash draws with no row read from "
            f"_dash_expand_plottype_str: {sorted(drawn - set(mins))}; rows for "
            f"types it does not draw: {sorted(set(mins) - drawn)}")

    def test_the_spelling_fixture_was_found(self):
        st = _spelling_truth()
        assert {"bins", "bw", "sort1"} <= set(st["options"])
        assert "tsrline" in st["plottypes"] and "area" in st["plottypes"]
        assert _twoway_takes("mlg", "mlabgap") is False       # abbrev_truth
        assert _twoway_takes("t", "t1title") is True          # abbrev_truth
        assert _twoway_takes("bw", "barwidth") is False       # the new file
        assert _twoway_takes_plottype("ar", "area") is False
        assert _twoway_takes_plottype("sc", "scatter") is True

    def test_the_synonym_claims_were_found(self):
        claims = {(a, b) for a, b, _ in _help_synonym_claims()}
        # 12 claims.  One written "Also {cmd:yti2()}" rather than
        # "Synonym: {cmd:yti2()}" is no claim the reader takes: 11, above
        # "8", and never checked against what dash takes.
        # 12 -> 2: WP-35 DT-15 the synonym claims of yti2() .. xsc2(),
        # cv(), colv(), pbgc() and jseed() leave the help: dash refuses them.
        assert len(claims) == 2, f"{len(claims)} synonym claims read, 2 measured"
        assert ("pbgc", "plotbgcolor") not in claims
        assert ("plotr", "plotregion") in claims


# ---------------------------------------------------------------------------
# 1. Everything the help defines must be accepted
# ---------------------------------------------------------------------------

class TestEveryDocumentedOptionIsAccepted:
    def test_no_documented_option_is_rejected(self):
        declared = _ado_declarations()
        documented = _help_options()
        # Sub-options live inside another option's parentheses and so are
        # never declared by `syntax' themselves.
        subopts = {"type", "exclude", "label", "format", "replace", "cols",
                   "rows", "color", "lcolor", "lwidth", "fcolor", "off", "on",
                   "range", "degree", "estopts",
                   # WP-31 H2f: filter()'s direction().
                   "direction"}
        # WP-29 P0.9: lpolyci's pwidth() and var() are read out of the
        # catch-all by value (_dash_lpolyci_opts), undeclared so that the
        # repeat check refuses either written twice, as twoway does.
        subopts |= {"pwidth", "var"}
        # WP-31 J1: the twoway options measured reaching the catch-all are
        # documented as accepted and named, never declared.
        subopts |= _catchall_options()
        # WP-35 GW-3: maxaxes() is read out of the options as typed and
        # checked as twoway checks it (_dash_maxaxes_val), never declared.
        subopts |= {"maxaxes"}
        missing = sorted(set(documented) - set(declared) - subopts)
        assert not missing, (
            f"{len(missing)} options the help documents are not declared by "
            f"any syntax statement, so `dash' would report them as unknown: "
            f"{missing}"
        )


# ---------------------------------------------------------------------------
# 2. The abbreviations the help advertises must be the ones dash accepts
# ---------------------------------------------------------------------------

class TestAbbreviationsAgree:
    def test_every_cmdab_claim_matches_the_declaration(self):
        declared = _ado_declarations()
        # WP-31 A3b: name() is declared twice with two minimums -- a graph's
        # NAME(), twoway's full name, and dash kpi's NAMe(), whose nam()
        # the help documents for dash kpi -- so a claim is held to the
        # declaration of any command that takes the option.
        src = _ado_text()
        every = {}
        for prog in _PROGRAMS:
            for mn, full in _syntax_options(_program_body(src, prog)):
                every.setdefault(full, set()).add(mn)
        bad = []
        for name, claims in sorted(_help_options().items()):
            if name not in declared:
                continue
            for claim in sorted(claims):
                if claim not in every.get(name, {declared[name]}):
                    bad.append(f"{name}: help says {claim!r}, "
                               f"dash.ado accepts {declared[name]!r}")
        assert not bad, (
            "the help advertises a different minimum abbreviation from the "
            "one dash accepts:\n  " + "\n  ".join(bad)
        )

    def test_the_help_does_not_contradict_itself(self):
        two = {n: sorted(c) for n, c in _help_options().items() if len(c) > 1}
        assert not two, (
            f"the help advertises two different minimum abbreviations for "
            f"the same option: {two}"
        )


# ---------------------------------------------------------------------------
# 3. Everything dash invented must be documented
# ---------------------------------------------------------------------------

class TestEveryDashOnlyOptionIsDocumented:
    def test_an_option_twoway_does_not_have_is_documented(self):
        """Documented means DEFINED: a {synopt} row, a {phang}/{phang2} entry
        or the Syntax block.  It used to be enough for the name to appear in
        prose anywhere, or for an alias's full option to be documented --
        which is how mlg() went unmentioned while dash honoured it, and how
        marker() passed on the word "marker" in SMCL's own {marker} tags."""
        documented = set(_help_options()) | _defined_names()
        # WP-31 D2: title2() and subtitle2() are declared only so that dash
        # refuses them in twoway's words, r(198); no command runs with
        # them, so there is nothing to define -- the Unsupported section's
        # prose says they are refused.
        refused = {"title2", "subtitle2"}
        # Flipped (WP-32): blabel(), ciopts(), fitopts(), lineopts() and
        # mlabwidth() were defined by Unsupported entries that said dash
        # named them; twoway refuses each on every type, r(198), and dash
        # now does (noted_option_truth.json), so the section's prose says
        # they are refused, as for title2().
        refused |= {"blabel", "ciopts", "fitopts", "lineopts", "mlabwidth"}
        # WP-32: play() is refused as twoway refuses a recording it cannot
        # find or read; the section's prose says how it is looked for.
        refused |= {"play"}
        # WP-31 H2t: table2() is the second declaration of table, its
        # argument form -- the user types table(rows(#) open), which the
        # Data tables entry defines; no command is written as table2().
        internal = {"table2"}
        # WP-35 DT-15: the spellings twoway refuses that dash took are
        # refused as twoway refuses them; the dashonly paragraph says so.
        internal |= _dashonly_refused()
        h = _help_text()
        assert "{opt table(rows(#) open)}" in h
        sec = h[h.index("{marker unsupported}"):h.index("{marker dependencies}")]
        for name in refused:
            assert ("{opt %s(" % name) in sec and "r(198)" in sec, name
        undocumented = sorted(name for name in _ado_declarations()
                              if not _twoway_spelling(name)
                              and name not in documented
                              and name not in refused
                              and name not in internal)
        assert not undocumented, (
            f"{len(undocumented)} options exist only in dash -- twoway has no "
            f"such option, so the help's redirect to the twoway manual cannot "
            f"cover them -- and no {{synopt}}, {{phang}} entry or Syntax line "
            f"of dash.sthlp defines them: {undocumented}"
        )


# ---------------------------------------------------------------------------
# 3b. Every spelling dash takes and twoway does not must be named
# ---------------------------------------------------------------------------

class TestEveryDashOnlySpellingIsNamed:
    """A spelling twoway does not take is not covered by the redirect to the
    twoway manual either, whatever its option is: the help has to say it is
    a spelling of that option, in the option's entry or in {cmdab:}."""

    def test_every_fold_twoway_does_not_take_is_named_beside_its_option(self):
        bad, unmeasured = [], []
        for alias, targets in sorted(_fold_aliases().items()):
            # WP-35 DT-15: a fold of a spelling dash refuses as twoway does
            # is never reached by a typed word, so the help names it only
            # as refused (the dashonly paragraph).
            if alias in _dashonly_refused():
                continue
            for target in sorted(targets):
                verdict = _twoway_takes(alias, target)
                if verdict is None:
                    unmeasured.append(f"{alias}() as {target}()")
                elif verdict is False and not _named_together(alias, target):
                    bad.append(f"{alias}() for {target}()")
        assert not unmeasured, (
            f"dash.ado folds these into another option, and neither fixture "
            f"says whether twoway takes them; measure them with "
            f"scripts/extract_alias_spelling_truth.do: {unmeasured}")
        assert not bad, (
            f"dash.ado folds {len(bad)} spelling(s) twoway does not take into "
            f"another option, and no definition entry of dash.sthlp names "
            f"them beside it: {bad}")

    def test_every_plot_type_abbreviation_twoway_does_not_take_is_named(self):
        bad, unmeasured = [], []
        for ptype, dmin in sorted(_plottype_minimums().items()):
            extra = []
            for L in range(len(dmin), len(ptype) + 1):
                s = ptype[:L]
                verdict = _twoway_takes_plottype(s, ptype)
                if verdict is None and s != ptype:
                    unmeasured.append(f"{s} for {ptype}")
                elif verdict is False:
                    extra.append(s)
            if extra and not _named_together(extra[0], ptype,
                                             sections=("plottypes",)):
                bad.append(f"{extra[0]} for {ptype} ({', '.join(extra)})")
        assert not unmeasured, (
            f"dash's expander takes these and neither fixture says whether "
            f"twoway does; measure them with "
            f"scripts/extract_alias_spelling_truth.do: {unmeasured}")
        assert not bad, (
            f"dash abbreviates {len(bad)} plot type(s) further than twoway "
            f"(measured: 'is not a twoway plot type', r(198)), and dash.sthlp "
            f"does not name the shortest spelling beside the type -- in the "
            f"Plot types section, a definition entry or {{cmdab:}} -- so "
            f"'abbreviated as twoway allows' is not the whole truth: {bad}")

    def test_every_option_abbreviation_twoway_does_not_take_is_named(self):
        """Options both declare, which dash abbreviates further than twoway
        (the minimum twoway accepts, measured in abbrev_truth.json)."""
        src = _ado_text()
        truth = _abbrev_truth()["options"]
        extra = {}
        for prog in ("_dash_parse_plot_opts", "_dash_parse_graph_opts"):
            decls = _syntax_options(_program_body(src, prog))
            for mn, full in decls:
                if full not in truth:
                    continue
                for L in range(len(mn), len(full) + 1):
                    s = full[:L]
                    if (_resolves_to(s, decls) == full
                            and _twoway_takes(s, full) is False):
                        extra.setdefault(full, set()).add(s)
        bad = [f"{min(v, key=len)}() for {full}() ({', '.join(sorted(v))})"
               for full, v in sorted(extra.items())
               if not _named_together(min(v, key=len), full)]
        assert not bad, (
            f"dash abbreviates {len(bad)} option(s) further than twoway, and "
            f"dash.sthlp does not name the shortest spelling beside the "
            f"option: {bad}")


# ---------------------------------------------------------------------------
# 3c. Every synonym the help states must be one dash takes
# ---------------------------------------------------------------------------

class TestEverySynonymTheHelpStatesIsTaken:
    def test_every_stated_synonym_is_a_spelling_dash_takes(self):
        bad = sorted({f"{a}() for {b}()" for a, b, _ in _help_synonym_claims()
                      if not _dash_takes(a, b)})
        assert not bad, (
            f"dash.sthlp names these as spellings of an option, and dash "
            f"takes them as no such thing: {bad}")


# ---------------------------------------------------------------------------
# 4. The Unsupported section must say what dash actually ignores
# ---------------------------------------------------------------------------

class TestTheUnsupportedSectionIsTrue:
    def test_nothing_listed_there_is_honoured(self):
        listed = _unsupported_section()
        # WP-31 J1: what dash names is the pending blocks and the names
        # that reach the catch-all (catchall_options_truth.json).
        ignored = _ignored_options() | _catchall_options()
        honoured = sorted(listed - ignored)
        assert not honoured, (
            f"{len(honoured)} options are documented under \"Unsupported "
            f"Stata twoway options\" although dash honours them, so the help "
            f"tells the user to stop using something that works: {honoured}"
        )

    def test_everything_dash_ignores_is_listed_there(self):
        listed = _unsupported_section()
        missing = sorted(_ignored_options() - listed)
        assert not missing, (
            f"dash accepts {len(missing)} options and reports each one as "
            f"ignored, but the help's list of unsupported options does not "
            f"name them: {missing}"
        )


    def test_every_accepted_undrawn_option_is_listed(self):
        # WP-31 J1: a name that reaches the catch-all is named in the note
        # as a pending one is, so the list names it too.
        listed = _unsupported_section()
        missing = sorted(_catchall_options() - listed)
        assert not missing, (
            f"dash takes {len(missing)} twoway options once and names them "
            f"in its note, but the help's list of unsupported options does "
            f"not name them: {missing}")

    def test_every_undeclared_table_name_was_probed(self):
        # The fixture must have measured each twoway option the duplicate
        # table knows and dash.ado does not declare, or a name could reach
        # the note unlisted.
        probed = set(_catchall_truth()["probes"])
        unprobed = sorted(_undeclared_twoway_options() - probed)
        assert not unprobed, (
            "scripts/extract_catchall_options_truth.do does not probe "
            f"{unprobed}; add them and run it again")

    def test_every_probe_twoway_refuses_dash_refuses_in_its_words(self):
        # MLF-01 (18oct2026): mlabfontface() reached the note although
        # twoway refuses it; a probe twoway refuses is refused by dash
        # with twoway's rc and first error line.
        bad = sorted(
            (k, p["twoway_rc"], p["twoway_message"], p["dash_rc"],
             p["dash_message"])
            for k, p in _catchall_truth()["probes"].items()
            if p["twoway_rc"] and (p["dash_rc"] != p["twoway_rc"]
                                   or p["dash_message"] != p["twoway_message"]))
        assert not bad, bad

    def test_every_name_twoway_refuses_is_named(self):
        # A name dash notes that twoway refuses on that plot is no twoway
        # option there; the help says so in its prose.
        h = _help_text()
        i = h.index("{marker unsupported}")
        j = h.index("{marker dependencies}", i)
        absent = sorted(n for n in _catchall_truth()["twoway_refuses"]
                        if "{cmd:" + n not in h[i:j])
        assert not absent, absent


# ---------------------------------------------------------------------------
# 5. The KPI statistics the command accepts must be the ones it documents
# ---------------------------------------------------------------------------

class TestKpiStatisticsAreDocumented:
    @staticmethod
    def _valid_stats():
        m = re.search(r'local valid_stats\s+"([^"]+)"', _ado_text())
        assert m, "dash.ado's valid_stats list moved"
        return m.group(1).split()

    def test_the_list_was_found(self):
        """Guards the guard below: a moved `valid_stats' list must fail
        here rather than let the table check pass on nothing.

        All 15 statistics (measured 24sep2026).  The list continued on a
        second `local valid_stats "`valid_stats' ..."' line -- p25, p50 and
        p75 added there -- read 12, above the "10" this was, and the table
        check never asked about the three."""
        # 15 -> 18: kurtosis, semean and range (WP-31 H2k).
        assert len(self._valid_stats()) == 18

    def test_every_accepted_statistic_is_in_the_table(self):
        """A help-to-code consistency guard, deliberately over text: every
        statistic dash.ado's `valid_stats' accepts is in the help's KPI
        table, so a statistic added to the code cannot go undocumented."""
        h = _help_text()
        i = h.index("{marker kpi}")
        j = h.index("{marker server_mode}", i)
        table = h[i:j]
        missing = [s for s in self._valid_stats()
                   if not re.search(r"\{cmd:%s\}" % re.escape(s), table)]
        assert not missing, (
            f"`dash kpi' accepts {missing} and the help's table of supported "
            f"statistics does not list them"
        )


# ---------------------------------------------------------------------------
# 6. Every internal link must resolve
# ---------------------------------------------------------------------------

class TestInternalLinksResolve:
    """`{help dash##scheme:Stata scheme support}` pointed at nothing.

    dash.sthlp:176 told the reader to see a section on scheme support "below".
    There was no `{marker scheme}` anywhere in the file and no such section;
    scheme() was documented under the heading that says it is unsupported.
    A reader who followed the link landed at the top of the help.
    """

    def test_every_marker_reference_has_a_marker(self):
        h = _help_text()
        markers = set(re.findall(r"\{marker ([a-z_0-9]+)\}", h))
        refs = set(re.findall(r"dash##([a-z_0-9]+)", h))
        dead = sorted(refs - markers)
        assert not dead, (
            f"the help links to {dead}, and no {{marker}} of that name "
            f"exists, so the link goes nowhere"
        )

    def test_the_markers_are_unique(self):
        h = _help_text()
        seen, dupes = set(), set()
        for m in re.findall(r"\{marker ([a-z_0-9]+)\}", h):
            (dupes if m in seen else seen).add(m)
        assert not dupes, f"duplicate {{marker}} names: {sorted(dupes)}"

    def test_the_reference_scan_found_something(self):
        # 73 links to 29 markers (WP-29 P0.12a: the dash serve entry links
        # its per-launch key to Server Mode).
        # 72 links to 29 markers (WP-29 P0.12b: the "Temporary files and
        # privacy" section, its viewerjumpto line and five links to it;
        # WP-29 P0.13 F4: the Blocking behavior paragraph links to it too;
        # WP-29 P0.10: the Tooltips paragraph links its hover() counting
        # rule to Resource limits).
        # 64 links to 28 markers (measured 25sep2026, after WP-28 E14
        # dropped the "At phone width" paragraph's link to Server Mode --
        # the served app's phone behaviour is now stated inline, since it
        # matches the saved page's, rather than sent to a section that
        # explained the difference; 65 to 28 before, after the S3 batch's
        # three ci band links, to ciband and unsupported; 62 to 27 after
        # TR-27.2's two links from "At phone width" and Figure
        # proportions; 60 before).
        # A link whose marker
        # is written with a capital -- {help dash##Scheme:...}, to no
        # marker at all -- is no link the scan reads: 59, above the "10"
        # this was, and the dead link passed the check above.
        # 75 after WP-29 P0.11's two links to Description (the Exporting
        # sentence and the data limit's paragraph; flipped from 73).
        # 75 -> 77, 29 -> 30: WP-30 P1.29 the saving() and server entries
        # link the new "Characters in saving()" paragraph (saving_chars).
        refs = re.findall(r"dash##[a-z_0-9]+", _help_text())
        # 77 -> 78 links, 30 -> 31 markers: WP-30 batch 4 (P1.19, P1.27).
        # 78 -> 80 links: WP-30 P1.1b, mlabel() and jitter() link Style lists.
        # 80 -> 86 links to 31 -> 32 markers: WP-30 P1.28a links Exporting
        # and Stored results (jump list, Description, Stored results) and
        # adds the results marker.
        # 86 -> 90 links to 32 -> 33 markers: WP-30 P1.13a adds the
        # Colours paragraph (colours) and links it from Option values, the
        # region options and the scheme-file paragraph.
        # 90 -> 91 links, 33 -> 34 markers: WP-30 P1.14a adds Named styles
        # (namedstyles), linked from pwidth() and the band's look; the
        # Unsupported entry's link to ciband went with the entry.
        # 91 -> 92 links: P1.14b's named-styles paragraph links the
        # scheme section.
        # 92 -> 93 links: P1.24's mlabt:extstyle() row links Style lists.
        # 93 -> 95 links: P1.31a's maxsessions() row and Server Mode's
        # flag list link Resource limits.
        # 95 -> 97 links, 34 -> 35 targets: P1.10's Added text paragraph
        # links Resource limits and, for the first time, Graph text.
        # 97 -> 98 links, 35 -> 36 targets: WP-31 D3 links the textbox
        # sentence to the new Textbox options paragraph.
        # 98 -> 99 links: WP-31 D2b links the Edge titles paragraph to it.
        # 99 -> 100: E4 the empty-parentheses sentence links Style lists.
        # 100 -> 102 links, 36 -> 37 targets: H2t the table_rows limit
        # and the saved-versus-served table link the new Data tables entry.
        # 102 -> 103 links: H2l the brush() synopt links Linking and
        # Brushing.
        # 103 -> 104 links: H2x the Images paragraph links The toolbar;
        # 104 -> 105 and 37 -> 38 targets: K6 the Accessibility jump link
        # (dash##accessibility).
        # 105 -> 121 links, 38 -> 44 targets: I2 the Jump To list names
        # every titled section (15 new jumps, six of them to sections no
        # link named: install, alsosee and four others) and the
        # Installation paragraph links Dependencies.
        # 121 -> 119: the hover() paragraph's link to Resource limits and
        # the data-limit paragraph's link to Description removed with the
        # size caps (WP-33 33-15)
        # 119 -> 121 links, 44 -> 45 targets: the Image panels jump link
        # (dash##image) and its link to Resource limits (WP-33 33-06).
        # 121 -> 122 links, 45 -> 46 targets: the qualifier paragraph's
        # link to Graphs from several frames (dash##frames, WP-33 33-07).
        # 122 -> 123 links: the scale() paragraph links Differences from
        # twoway for dash's measured scale() differences (WP-33 GW-11).
        # 123 -> 124 links: the Jump To entry for Graphs from several
        # frames (WP-33 33-07, batch 33.3 gate).
        # 124 -> 125 links, 46 -> 47 targets: syn:SD-3 the Differences entry
        # links the p1() to p20() sentence, dash##pnum (WP-35 35-02).
        # 125 -> 126 links: the Differences entry Plot-type names in lower
        # case only links Plot types (WP-35 plot:PT-3).
        # 126 -> 127 links, 47 -> 48 targets: syn:SD-22 the Differences
        # entry links its contour note, dash##contour_unknown (WP-35 35-06).
        # 127 -> 128 links: basic:PT-13 the Option values paragraph links
        # Resource limits for bin() and n() (WP-35 35-05).
        # 128 -> 132 links, 48 -> 49 targets: WP-35 DT-15 the Option values
        # paragraph, the Differences entry, hover()'s entry and the Data
        # tables section link dash's own options, dash##dashonly.
        # 132 -> 134 links: plat:PT-5 the drop-in paragraph and the
        # Differences entry Tested on one platform link Dependencies
        # (WP-36 36-04).
        # 134 -> 135 links: plat:PT-2 the Differences entry Stata 19 or
        # later links Dependencies (WP-36 36-04).
        # 135 -> 136 links: plat:PT-6 the saving() characters paragraph's
        # tilde rule links Dependencies (WP-36 36-04).
        # 136 -> 137 links: plat:PT-14 the Differences entry Large data
        # take time and memory links Resource limits (WP-36 36-04).
        # 137 -> 138 links: stat:PT-16 the Differences entry lpolyci where
        # the pilot has no residual degrees of freedom links Statistical
        # Layer Options (WP-37 37-05).
        # 138 -> 139 links: DT-26 the Differences entry Numeric limits of
        # the estimators links Statistical Layer Options (WP-37 37-05).
        # 139 -> 140 links: stat:PT-21 the Differences entry Points whose
        # sort keys tie links Plot types (WP-37 37-05).
        # old -> new: 140 -> 144 links, 49 -> 50 targets: syn:SD-17 the new
        # section Stata graph integration (dash##graphintegration): its Jump
        # To entry, the Description's caveat, the Differences item and its
        # sub-point name() registers (WP-38 38-01).
        # old -> new: 144 -> 148 links: GW-12 the sub-point No graph memory,
        # the Description's and Exporting's links to the section and its
        # Graph memory paragraph's link to Exporting (WP-38 38-01).
        # old -> new: 148 -> 151 links: ECO-1 the sub-point Data at build
        # and its paragraph's links to Description and Graphs from several
        # frames (WP-38 38-01).
        # old -> new: 151 -> 153 links: ECO-4 the sub-point graph combine
        # and its paragraph's link to Layout (WP-38 38-01).
        assert len(refs) == 153 and len(set(refs)) == 50
