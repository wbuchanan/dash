"""The maintainer's per-word rulings on the spellings dash took and twoway
refuses (WP-35 section 35-07, DT-15).

DECISIONS.md P4-7 (20oct2026): "Unless the options are specific to
functionality that only dash provides, the syntax should mirror twoway
syntax as close as possible."  D53 (22oct2026) extends it to every
abbreviation or synonym dash took and twoway refuses.  P4-9: a refused
synonym's second line names twoway's spelling.

KEEP: the options only a dashboard has (kept, listed in one help
paragraph).  REFUSE: refused as twoway refuses them, in the section's
table order.  ELSEWHERE: ruled refused and implemented by another
section.  HINT: the second line of each REFUSE word that has one.
"""

KEEP = ("hover()", "table")

REFUSE = (
    "ytitle2()", "ylabel2()", "yscale2()", "xtitle2()", "xlabel2()",
    "xscale2()", "yti2()", "yla2()", "ysc2()", "xti2()", "xla2()",
    "xsc2()", "ytick2()", "xtick2()", "yline2()", "xline2()", "ymtick2()",
    "ymlabel2()", "xmtick2()", "xmlabel2()", "tlabel2()", "ttick2()",
    "tline2()", "tscale2()", "ttitle2()", "marker()", "malpha()",
    "lalpha()", "falpha()", "jseed()", "mlg()", "cv()", "colv()",
    "colornlevels()", "colormissing()", "plotbgcolor()", "pbgc()",
    "colpalette()",
    "kernel(GAUSSIAN)", "xsize(())", "colorvar(<string var>)",
)

ELSEWHERE = {
    "if keeping no row with colorvar()": "42-05 CV-14",
    "title(\"'90s\")": "43-05 LT-24",
}

_AXIS2 = {
    "ytitle2()": "ytitle", "ylabel2()": "ylabel", "yscale2()": "yscale",
    "xtitle2()": "xtitle", "xlabel2()": "xlabel", "xscale2()": "xscale",
    "yti2()": "ytitle", "yla2()": "ylabel", "ysc2()": "yscale",
    "xti2()": "xtitle", "xla2()": "xlabel", "xsc2()": "xscale",
    "ytick2()": "ytick", "xtick2()": "xtick", "yline2()": "yline",
    "xline2()": "xline", "ymtick2()": "ymtick", "ymlabel2()": "ymlabel",
    "xmtick2()": "xmtick", "xmlabel2()": "xmlabel", "tlabel2()": "tlabel",
    "ttick2()": "ttick", "tline2()": "tline", "tscale2()": "tscale",
    "ttitle2()": "ttitle",
}

HINT = {w: "use %s(..., axis(2))" % b for w, b in _AXIS2.items()}
HINT.update({
    "marker()": "use msymbol()",
    "malpha()": "use mcolor(<color>%<#>)",
    "lalpha()": "use lcolor(<color>%<#>)",
    "falpha()": "use fcolor(<color>%<#>)",
    "jseed()": "use jitterseed()",
    "mlg()": "use mlabgap()",
    "cv()": "use colorvar()",
    "colv()": "use colorvar()",
    "colornlevels()": "use colorlevels()",
    "colormissing()": "use colorformissing()",
    "plotbgcolor()": "use plotregion(fcolor())",
    "pbgc()": "use plotregion(fcolor())",
    "colpalette()": "use colorlist() or colorrule()",
    "kernel(GAUSSIAN)": "use kernel(<value in lower case>)",
})

#: The fixture key of each measured row (test/fixtures/dash_only_words_truth.json).
FIXTURE_KEY = {w: w[:-2] for w in REFUSE if w.endswith("()")}
FIXTURE_KEY.update({"kernel(GAUSSIAN)": "V1", "xsize(())": "V2",
                    "colorvar(<string var>)": "V3",
                    "hover()": "hover", "table": "table",
                    "if keeping no row with colorvar()": "V4",
                    "title(\"'90s\")": "V5"})

#: The spellings of the kept words, from dash's minimum (hov) to the full
#: name, for the known-differences tables (D-35-07.f).
KEEP_SPELLINGS = ("hov", "hove", "hover", "table")
