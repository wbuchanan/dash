#!/usr/bin/env python3
"""RETIRED (WP-30 P1.34): historical, do not run.

S05 wiring: accept every option, and report by name the ones dash ignores.

Run AFTER regen_option_surface.py (which adds Stata's catch-all `*` to both
syntax blocks).  Idempotent-ish: always run it on a freshly generated dash.ado.
"""
import sys

sys.exit("scripts/wire_option_reporting.py is retired (WP-30 P1.34): historical, do not run; add an option in dash.ado's five option-surface places by hand")

import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
inv = json.load(open("/tmp/dash-wf/b2/option_inventory.json"))
PENDING, GRAPH, PLOT = inv["pending"], set(inv["graph"]), set(inv["plot"])

s = open(REPO + "/dash.ado").read()

# ---- S04 fixups that the generator does not own -------------------------
s = s.replace("    // Full lowercase names are required here because we "
              "pre-expand abbreviations\n    // in Mata before this call.\n", "")
s = s.replace("        TItle(string)           ///\n        name(string)            ///",
              "        TItle(string)           ///\n        NAMe(string)            ///")
s = s.replace("          UPDATE(string)        ///", "          UPDate(string)        ///")
s = s.replace(
    "        SUBTITLE2(string)         NODRAW                    PLAY(string) ///",
    "        SUBTITLE2(string)         NODRAW                    PLAY(string) ///\n"
    "        T(string)                 B(string)                 L(string) ///\n"
    "        R(string) ///")

ALIAS = '''
    // twoway accepts t(), b(), l() and r() as abbreviations of t1title(),
    // b1title(), l1title() and r1title().  Stata derives the minimum from the
    // leading run of capitals and the digit in "t1title" ends that run, so
    // "T1title" yields "t1", never "t".  The four single-letter forms are
    // declared separately and folded in here.  Measured against real twoway --
    // see test/fixtures/abbrev_truth.json.
    if `"`t'"' != "" & `"`t1title'"' == "" local t1title `"`t'"'
    if `"`b'"' != "" & `"`b1title'"' == "" local b1title `"`b'"'
    if `"`l'"' != "" & `"`l1title'"' == "" local l1title `"`l'"'
    if `"`r'"' != "" & `"`r1title'"' == "" local r1title `"`r'"'
'''


def pending_block(names):
    out = [
        "    // Options dash accepts but does not yet honour.  Each supplied one",
        "    // is recorded by name so it is reported rather than silently",
        "    // dropped while the owning section is outstanding.",
        '    local _dash_pending ""',
    ]
    for n in sorted(names):
        out.append('    if `"`%s\'"\' != "" local _dash_pending '
                   '`"`_dash_pending\' %s"\'' % (n, n))
    out.append("    // Whatever Stata could not match at all, via the trailing *.")
    out.append('    local _dash_unknown `"`options\'"\'')
    return "\n".join(out) + "\n"


# The plot parser declares the graph-level options too, so it must check both.
SCOPES = {
    "_dash_parse_graph_opts": [n for n in PENDING if n in GRAPH],
    "_dash_parse_plot_opts": [n for n in PENDING if n in GRAPH or n in PLOT],
}
for prog, names in SCOPES.items():
    i = s.index("program define " + prog)
    j = s.index("\n    sreturn local ", i)
    s = s[:j] + "\n" + ALIAS + "\n" + pending_block(names) + s[j:]
    k = s.index("\nend", s.index("program define " + prog))
    s = s[:k] + ('\n    sreturn local _pending  `"`_dash_pending\'"\''
                 '\n    sreturn local _unknown  `"`_dash_unknown\'"\'') + s[k:]

# ---- collect per segment -------------------------------------------------
anchor = "    // Accumulate graph-level options found in this segment into g_* locals"
s = s.replace(anchor, '''    // Accumulate this segment's unsupported options so _dash_plot can report
    // them once for the whole command rather than once per plot segment.
    // c_local cannot read the caller's local, so hand back only THIS
    // segment's list and let _dash_plot append it.
    c_local _seg_ignored_out `"`s(_pending)' `s(_unknown)'"'

''' + anchor, 1)

# ---- initialise and report once per command ------------------------------
a2 = '    // ---- Parse each plot segment ----\n    local plots_json ""'
s = s.replace(a2, '    local _dash_ignored_acc ""\n\n' + a2, 1)

# append each segment's handback right after _dash_process_segment returns
call = "        _dash_process_segment `\"`seg'\"' _pt_k _json_k\n"
assert call in s, "segment call site not found"
# initialise BEFORE the call -- _dash_process_segment sets it via c_local, so
# clearing it afterwards would wipe what we are trying to collect.
s = s.replace(call, '''        local _seg_ignored_out ""
''' + call, 1)
s = s.replace(
    "        // _dash_process_segment pushes any found graph-level opts",
    '''        if `"`_seg_ignored_out'"' != "" {
            local _dash_ignored_acc `"`_dash_ignored_acc' `_seg_ignored_out'"'
        }

        // _dash_process_segment pushes any found graph-level opts''', 1)

a3 = "    // ---- Assemble graph_options JSON ----"
s = s.replace(a3, '''    // ---- Report unsupported options, once, naming every one ----
    // dash accepts every twoway option so a pasted command never aborts; an
    // option it cannot honour is named here instead of vanishing.  One note
    // per command listing all of them.
    if `"`_dash_ignored_acc'"' != "" {
        _dash_report_ignored `"`_dash_ignored_acc'"'
    }

''' + a3, 1)

HELPER = '''
// ================================================================
// _dash_report_ignored  — one note per command naming every option
//                         dash accepted but did not honour
// ================================================================
program define _dash_report_ignored
    version 16.0
    args raw

    // `raw' mixes bare option names (pending, from the declared set) with the
    // verbatim text Stata could not match (unknown, from the trailing *).  Cut
    // each token at its opening parenthesis so the user sees option names, not
    // the values they supplied.
    local seen ""
    local out  ""
    foreach tok of local raw {
        local ppos = strpos("`tok'", "(")
        if `ppos' > 0 local tok = substr("`tok'", 1, `ppos' - 1)
        local tok = strtrim("`tok'")
        if "`tok'" == "" continue

        local dup = 0
        foreach prev of local seen {
            if "`prev'" == "`tok'" local dup = 1
        }
        if `dup' continue

        local seen `"`seen' `tok'"'
        local out  `"`out' `tok'()"'
    }
    if `"`out'"' == "" exit

    display as text "dash: ignoring unsupported option(s):" as result `"`out'"'
end

'''
marker = ("// ================================================================\n"
          "// _dash_plot  — parse and route a plot definition (v2.0)")
s = s.replace(marker, HELPER + marker, 1)

open(REPO + "/dash.ado", "w").write(s)
print("S05 wired: catch-all reporting, %d pending options tracked" % len(PENDING))
