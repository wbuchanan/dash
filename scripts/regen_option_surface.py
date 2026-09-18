#!/usr/bin/env python3
"""Regenerate dash.ado's option surface from one canonical inventory.

dash.ado repeats the option list in five places (two syntax blocks, two sreturn
blocks, the plot-option JSON key list, and the graph-level propagation loops).
Keeping them in sync by hand is how they drifted.  This script is the single
source of truth; run it, don't hand-edit those blocks.

Minimum abbreviations come from test/fixtures/abbrev_truth.json, which was
measured against real twoway with a .gph resolution oracle.  dash-only options
(no twoway equivalent) keep the short form dash already accepted.
"""
import json
import re
import sys

REPO = "/Users/billy/Desktop/Programs/StataPrograms/d/dash"
truth = json.load(open(REPO + "/test/fixtures/abbrev_truth.json"))
TRUTH_OPTS = truth["options"]

# dash-only options: no twoway equivalent, so keep today's accepted short form
DASH_ONLY_MIN = {
    "bgcolor": "bgc", "plotbgcolor": "pbgc", "link": "link", "filter": "filt",
    "ytitle2": "yti2", "xtitle2": "xti2", "ylabel2": "yla2", "xlabel2": "xla2",
    "yscale2": "ysc2", "xscale2": "xsc2", "mlabwidth": "mlabw", "malpha": "mal",
    "marker": "marker", "lalpha": "lal", "falpha": "fa", "jseed": "jse",
    "colpalette": "colpal", "colornlevels": "colorn", "colormissing": "colorm",
    "bwidth": "bwidth",
}

FLAGS = {
    "percent", "frequency", "density", "fraction", "horizontal", "vertical",
    "sort", "nodraw", "colordiscrete", "coloruseplegend",
}
ASIS = {
    "note", "caption", "xlabel", "ylabel", "xline", "yline", "legend", "by",
    "xscale", "yscale", "plotregion", "graphregion", "filter", "colorcuts",
    "ylabel2", "xlabel2", "yscale2", "xscale2",
    "text", "xtick", "ytick", "xmtick", "ymtick", "xmlabel", "ymlabel",
    "ciopts", "lineopts", "fitopts", "at", "colorlist", "range",
}

# (name, owning section) -- section None means already implemented
GRAPH = [
    ("title", None), ("subtitle", None), ("note", None), ("caption", None),
    ("name", None), ("saving", None), ("xtitle", None), ("ytitle", None),
    ("xlabel", None), ("ylabel", None), ("xline", None), ("yline", None),
    ("legend", None), ("by", None), ("xscale", None), ("yscale", None),
    ("aspectratio", None), ("scheme", None), ("plotregion", None),
    ("graphregion", None), ("bgcolor", None), ("plotbgcolor", None),
    ("link", None), ("filter", None),
    ("ytitle2", None), ("xtitle2", None), ("ylabel2", None), ("xlabel2", None),
    ("yscale2", None), ("xscale2", None),
    # --- accepted here, honoured by a later section ---
    ("xsize", "S10"), ("ysize", "S10"), ("fxsize", "S10"), ("fysize", "S10"),
    ("scale", "S10"),
    ("text", "S09"), ("xtick", "S09"), ("ytick", "S09"), ("xmtick", "S09"),
    ("ymtick", "S09"), ("xmlabel", "S09"), ("ymlabel", "S09"),
    ("t1title", "S09"), ("t2title", "S09"), ("b1title", "S09"),
    ("b2title", "S09"), ("l1title", "S09"), ("l2title", "S09"),
    ("r1title", "S09"), ("r2title", "S09"), ("title2", "S09"),
    ("subtitle2", "S09"),
    # --- accepted and reported as ignored, permanently ---
    ("nodraw", "IGNORE"), ("play", "IGNORE"),
]

PLOT = [
    ("mcolor", None), ("msymbol", None), ("msize", None), ("msangle", None),
    ("mfcolor", None), ("mlcolor", None), ("mlabel", None), ("mlabcolor", None),
    ("mlabsize", None), ("mlabposition", None), ("mlabgap", None),
    ("mlabwidth", None), ("malpha", None), ("marker", None),
    ("lcolor", None), ("lwidth", None), ("lpattern", None), ("lalpha", None),
    ("fcolor", None), ("fintensity", None), ("falpha", None),
    ("barwidth", None), ("base", None), ("blcolor", None), ("bfcolor", None),
    ("jitter", None), ("jseed", None), ("yaxis", None), ("xaxis", None),
    ("colorvar", None), ("colpalette", None), ("colordiscrete", None),
    ("coloruseplegend", None), ("colornlevels", None), ("colorcuts", None),
    ("colormissing", None), ("bwidth", None), ("degree", None),
    ("pstyle", None), ("cmissing", None), ("recast", None), ("connect", None),
    # --- accepted here, honoured by a later section ---
    ("bin", "S07"), ("width", "S07"), ("start", "S07"), ("percent", "S07"),
    ("frequency", "S07"), ("density", "S07"), ("fraction", "S07"),
    ("kernel", "S07"), ("n", "S07"), ("level", "S07"), ("bands", "S07"),
    ("at", "S07"), ("ciopts", "S07"), ("lineopts", "S07"), ("fitopts", "S07"),
    ("color", "S09"), ("mlwidth", "S09"), ("mstyle", "S09"),
    ("lstyle", "S09"), ("mlstyle", "S09"), ("mlpattern", "S09"),
    ("blabel", "S09"),
    ("horizontal", "S06"), ("vertical", "S06"), ("sort", "S06"),
    # Real twoway spellings dash never declared.  `jitterseed` is Stata's name
    # for what dash calls `jseed`; `colorlist` is Stata's, `colpalette` dash's.
    # Both spellings are accepted so either dialect works.
    ("range", "S07"), ("colorlist", "S09"), ("jitterseed", "S07"),
]

GRAPH_NAMES = [n for n, _ in GRAPH]
PLOT_NAMES = [n for n, _ in PLOT]
PENDING = {n: s for n, s in GRAPH + PLOT if s}


# Short forms dash historically accepted via the Mata table.  Where one is
# SHORTER than Stata's measured minimum we keep it too, provided it introduces
# no ambiguity: accepting more than twoway does is a superset, so it cannot
# break drop-in parity, and it keeps existing dash do-files working.
HISTORICAL_MIN = {
    "aspectratio": "asp", "name": "nam", "jitter": "jit", "colorvar": "cv",
    "mlabgap": "mlg", "barwidth": "bw", "bwidth": "bwid",
}


def base_min(name):
    entry = TRUTH_OPTS.get(name)
    mn = entry.get("min_abbrev") if entry else None
    if not mn:
        mn = DASH_ONLY_MIN.get(name, name)
    if not name.startswith(mn):
        mn = name  # measured minimum is not a prefix -> require the full name
    return mn


def resolve_minimums(names):
    """Choose each option's minimum, preferring the shorter of Stata's and
    dash's historical form, but only where that creates no ambiguity."""
    mins = {n: base_min(n) for n in names}

    def ambiguous(mins):
        """Any token that would match more than one option?"""
        bad = set()
        for n in names:
            for ln in range(len(mins[n]), len(n) + 1):
                tok = n[:ln]
                hits = [o for o in names
                        if len(tok) >= len(mins[o]) and o.startswith(tok)]
                if len(hits) > 1:
                    bad.add(tok)
        return bad

    assert not ambiguous(mins), "measured minimums are already ambiguous"
    for n in names:
        hist = HISTORICAL_MIN.get(n)
        if not hist or not n.startswith(hist) or len(hist) >= len(mins[n]):
            continue
        trial = dict(mins)
        trial[n] = hist
        if not ambiguous(trial):
            mins[n] = hist
        else:
            print("    kept Stata minimum for %-12s (%r would be ambiguous)"
                  % (n, hist))
    return mins


def declare(name, mins=None):
    """Return the syntax declaration with the minimum abbreviation capitalised."""
    mn = (mins or {}).get(name) or base_min(name)
    head, tail = name[:len(mn)].upper(), name[len(mn):]
    if name in FLAGS:
        return head + tail
    typ = "(string asis)" if name in ASIS else "(string)"
    return head + tail + typ


def syntax_block(names, indent="        "):
    mins = resolve_minimums(names)
    decls = [declare(n, mins) for n in names]
    width = max(len(d) for d in decls) + 2
    out, row = [], []
    for d in decls:
        row.append(d.ljust(width))
        if len(row) == 3:
            out.append(indent + "".join(row).rstrip())
            row = []
    if row:
        out.append(indent + "".join(row).rstrip())
    return " ///\n".join(out)


def sreturn_block(names, prefix="", indent="    "):
    width = max(len(n) for n in names) + 1
    lines = []
    for n in names:
        lines.append(indent + "sreturn local " + (prefix + n).ljust(width + len(prefix))
                     + " `\"`" + n + "'\"'")
    return "\n".join(lines)


def wrapped_list(names, cont_indent):
    """Wrap a space-separated name list across Stata continuation lines.

    The first chunk is returned bare (it follows `foreach x in ` on the same
    line); every later chunk is preceded by ` ///` + a newline + cont_indent.
    """
    lines, row = [], []
    for n in names:
        row.append(n)
        if len(" ".join(row)) > 58:
            lines.append(" ".join(row))
            row = []
    if row:
        lines.append(" ".join(row))
    out = lines[0]
    for chunk in lines[1:]:
        out += " ///\n" + cont_indent + chunk
    return out


src = open(REPO + "/dash.ado").read()
orig = src

MARK = ("    // NOTE: this block is generated by scripts/regen_option_surface.py\n"
        "    // from test/fixtures/abbrev_truth.json.  Do not hand-edit; the same\n"
        "    // option list appears in several places and the generator keeps them\n"
        "    // in step.  Capitalised letters are the minimum abbreviation, measured\n"
        "    // against real twoway rather than guessed.\n")


def splice(src, start_pat, end_pat, new, label):
    i = src.index(start_pat)
    j = src.index(end_pat, i) + len(end_pat)
    print("  spliced %-34s %5d -> %5d chars" % (label, j - i, len(new)))
    return src[:i] + new + src[j:]


# 1. graph-opts syntax block
new_graph_syntax = (MARK + "    syntax [, ///\n" + syntax_block(GRAPH_NAMES) + " ///\n    ]")
i = src.index("program define _dash_parse_graph_opts")
gs = src.index("    syntax [, ///", i)
ge = src.index("\n    ]", gs) + len("\n    ]")
# keep any preceding comment lines out of the replacement
src = src[:gs] + new_graph_syntax + src[ge:]
print("  graph syntax block rewritten")

# 2. graph-opts sreturn block
i = src.index("program define _dash_parse_graph_opts")
ss = src.index("    sreturn local ", i)
se = src.index("\nend", ss)
src = src[:ss] + sreturn_block(GRAPH_NAMES) + src[se:]
print("  graph sreturn block rewritten")

# 3. plot-opts syntax block
i = src.index("program define _dash_parse_plot_opts")
ps = src.index("    syntax [, ///", i)
pe = src.index("\n    ]", ps) + len("\n    ]")
new_plot_syntax = (MARK + "    syntax [, ///\n"
                   + syntax_block(PLOT_NAMES + GRAPH_NAMES) + " ///\n    ]")
src = src[:ps] + new_plot_syntax + src[pe:]
print("  plot syntax block rewritten")

# 4. plot-opts sreturn block (plot-level, then graph-level as g_*)
i = src.index("program define _dash_parse_plot_opts")
ss = src.index("    /* ---- plot-level ---- */", i)
se = src.index("\nend", ss)
new_sr = ("    /* ---- plot-level ---- */\n" + sreturn_block(PLOT_NAMES)
          + "\n    /* ---- graph-level (returned separately so _dash_plot can"
            " accumulate them) ---- */\n" + sreturn_block(GRAPH_NAMES, prefix="g_"))
src = src[:ss] + new_sr + src[se:]
print("  plot sreturn block rewritten")

# 5. plot-option JSON key list
i = src.index("program define _dash_plot_opts_to_json")
ks = src.index("    foreach key in ", i)
ke = src.index(" {\n", ks) + len(" {")
src = src[:ks] + "    foreach key in " + wrapped_list(
    PLOT_NAMES, " " * 19) + " {" + src[ke:]
print("  plot JSON key list rewritten")

# 6. every graph-level propagation loop (three of them, identical shape)
n_loops = 0
for pat in ("foreach gkey in ", "foreach gk in "):
    while True:
        try:
            a = src.index(pat)
        except ValueError:
            break
        b = src.index(" {\n", a) + len(" {")
        indent = " " * (len(src[:a].rsplit("\n", 1)[-1]))
        src = src[:a] + pat.replace("foreach", "FOREACHDONE") + wrapped_list(
            GRAPH_NAMES, indent + " " * (len(pat) - len("foreach "))) + " {" + src[b:]
        n_loops += 1
src = src.replace("FOREACHDONE", "foreach")
print("  graph-level propagation loops rewritten:", n_loops)

# 7. record which options are pending so the reporter can name them
pending_lines = "\n".join(
    '    local _dash_pending_%s "%s"' % (n, s) for n, s in sorted(PENDING.items()))

open(REPO + "/dash.ado", "w").write(src)
print("\ndash.ado: %d -> %d chars" % (len(orig), len(src)))
print("graph options: %d  plot options: %d  pending: %d"
      % (len(GRAPH_NAMES), len(PLOT_NAMES), len(PENDING)))
json.dump({"graph": GRAPH_NAMES, "plot": PLOT_NAMES, "pending": PENDING},
          open("/tmp/dash-wf/b2/option_inventory.json", "w"), indent=1)
