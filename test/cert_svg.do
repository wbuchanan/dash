*! cert_svg.do -- shared certification helper: read a twoway SVG through
*! scripts/svg_truth.py.
*!
*! WHY THIS EXISTS
*!
*! Seven certification scripts each wrote their own reader for a twoway
*! SVG (test_help_claims_8.cscript's _hc_svg family, test_help_claims_2's
*! _hc2_rawhas byte search, test_help_claims_5's _hc5_svg,
*! test_help_claims_6's _hc6_first_r, test_bug_regressions's _br03_svg,
*! test_twoway_option_parity's _ztp_count), and none of them knew that
*! Stata writes a run of spaces as U+00A0 (svg_options.sthlp:128-137), so
*! an exact text match on a two-word title could fail for no visible
*! reason.  This file gives every certification script the one reader,
*! scripts/svg_truth.py, through six Stata programs that never let a byte
*! of the SVG reach a Stata macro (the same reason cert_helpers.do exists:
*! Bokeh's JSON, and an SVG's own attribute quoting, break a compound-
*! quoted macro the moment the file's bytes are pasted into one).
*!
*! LOAD ORDER: after `cscript' (which drops every global -- cert_helpers.do
*! says why) and before any `cd' (the scripts directory below is computed
*! from c(pwd), so a script that `cd's away, as test_help_claims_8.cscript
*! does at its line 259, must load this file first).
*!
*!     do "cert_helpers.do"
*!     quietly do "cert_svg.do"
*!
*! Every program below is rclass and CLOBBERS r() -- as cert_file_has does
*! -- so a caller saves what it needs from r() before its next command.
*!
*! No macro is ever interpolated into a Python string literal: every
*! argument (a file path, a text needle, an axis name) crosses through
*! Macro.getLocal, and every answer comes back through Macro.setLocal, read
*! by the calling program as a plain string, then, where a number is
*! wanted, through `real()' -- "." is Stata's own missing-value spelling,
*! so a Python "." reads back as a Stata missing with no extra work.
*!
*! No Python availability gate (WP-36 plat:PT-1, M8): with no Python set,
*! Stata finds one on the first python: line below.  A
*! `python:' block cannot sit inside `program define' (its `end' ends the
*! program), so the four python-backed programs below are one-line calls
*! into functions defined once, here, at load time.
*!
*! TRAP, found the hard way (measured 25sep2026, scratchpad probe_py_
*! scope.do/2.do): a bare one-liner `python: _cert_svg_texts()' written
*! INSIDE a `program define' raises `NameError: name '_cert_svg_texts' is
*! not defined', even though the very same call from the top level of a
*! do-file, right after the block above defines it, works.  A `python:'
*! block at a do-file's top level and a `python:' one-liner inside a
*! `program define' body do not share one exec() globals dict the way a
*! Stata session's Python integration is generally described.  The fix is
*! to name the function through the persistent `__main__' module, not
*! bare: `python: import __main__ as _dash_svg_main;
*! _dash_svg_main._cert_svg_texts()' -- `__main__' IS shared for the whole
*! session (the module object the four functions attached themselves to
*! when the block above ran), so a qualified lookup finds them from any
*! program.  Every call below uses this form.

global dash_nobrowser 1

global cert_svg_scripts "`c(pwd)'/../scripts"
capture confirm file "${cert_svg_scripts}/svg_truth.py"
if _rc {
    display as error "cert_svg.do: scripts/svg_truth.py not found at ${cert_svg_scripts}"
    exit 601
}


python:
import json
import sys
from sfi import Macro

sys.path.insert(0, Macro.getGlobal("cert_svg_scripts"))
import svg_truth


def _cert_svg_texts():
    path = Macro.getLocal("file")
    listfile = Macro.getLocal("list")
    texts = svg_truth.svg_texts(path)
    with open(listfile, "w", encoding="utf-8") as fh:
        for t in texts:
            fh.write(json.dumps(t, sort_keys=True) + "\n")
    sizes = [t["size"] for t in texts if t["size"] is not None]
    Macro.setLocal("cert_svg_n", str(len(texts)))
    Macro.setLocal("cert_svg_list", listfile)
    Macro.setLocal("cert_svg_maxsize", str(max(sizes)) if sizes else ".")
    Macro.setLocal("cert_svg_minsize", str(min(sizes)) if sizes else ".")


def _cert_svg_has_text():
    path = Macro.getLocal("file")
    text = Macro.getLocal("text")
    lower = Macro.getLocal("lowerflag") == "1"
    n = svg_truth.svg_has_text(path, text, lower=lower)
    Macro.setLocal("cert_svg_count", str(n))
    Macro.setLocal("cert_svg_found", "1" if n else "0")


def _cert_svg_fills():
    path = Macro.getLocal("file")
    listfile = Macro.getLocal("list")
    markers = Macro.getLocal("markersflag") == "1"
    fills = (svg_truth.svg_marker_fills(path) if markers
             else svg_truth.svg_fills(path))
    order = sorted(fills, key=lambda c: -fills[c]["n"])
    with open(listfile, "w", encoding="utf-8") as fh:
        for colour in order:
            info = fills[colour]
            kinds = ",".join(f"{k}={v}" for k, v in sorted(info["kinds"].items()))
            opac = ",".join(str(o) for o in info["opacity"])
            fh.write(f"{colour}\t{info['n']}\t{kinds}\t{opac}\n")
    Macro.setLocal("cert_svg_n", str(len(order)))
    Macro.setLocal("cert_svg_colours", " ".join(order))
    Macro.setLocal("cert_svg_list", listfile)


def _cert_svg_extent():
    path = Macro.getLocal("file")
    axis = Macro.getLocal("axis")
    values_raw = Macro.getLocal("values")
    tick_values = [float(v) for v in values_raw.split()] if values_raw else None
    reason = ""
    ext = None
    try:
        ext = svg_truth.svg_axis_extent(path, axis, tick_values=tick_values)
    except ValueError as exc:
        reason = str(exc)
    if ext is None:
        if not reason:
            reason = svg_truth.svg_axis_extent.last_reason or "no fit"
        Macro.setLocal("cert_svg_low", ".")
        Macro.setLocal("cert_svg_high", ".")
        Macro.setLocal("cert_svg_space", "")
        Macro.setLocal("cert_svg_reversed", ".")
        Macro.setLocal("cert_svg_n_ticks", ".")
        Macro.setLocal("cert_svg_reason", reason)
    else:
        Macro.setLocal("cert_svg_low", repr(ext["low"]))
        Macro.setLocal("cert_svg_high", repr(ext["high"]))
        Macro.setLocal("cert_svg_space", ext["space"])
        Macro.setLocal("cert_svg_reversed", "1" if ext["reversed"] else "0")
        Macro.setLocal("cert_svg_n_ticks", str(ext["n_ticks"]))
        Macro.setLocal("cert_svg_reason", "")
end

// ---------------------------------------------------------------------
// cert_svg_export: graph export wrapped so every caller writes to and
// reads from the same place, and defaults to the current graph.
// ---------------------------------------------------------------------
capture program drop cert_svg_export
program define cert_svg_export, rclass
    version 16.0
    syntax [, NAME(string) FILE(string)]

    if `"`file'"' == "" {
        local base = cond(`"`name'"' != "", `"`name'"', "Graph")
        local file "`base'.svg"
    }
    if strpos(`"`file'"', "/") == 0 {
        local dir "`c(tmpdir)'dash_cert_svg"
        capture mkdir "`dir'"
        local file "`dir'/`file'"
    }
    if `"`name'"' != "" {
        capture graph export `"`file'"', name(`name') replace as(svg)
    }
    else {
        capture graph export `"`file'"', replace as(svg)
    }
    return local  file `"`file'"'
    return scalar rc = _rc
end

// ---------------------------------------------------------------------
// cert_svg_texts: every <text> element, through scripts/svg_truth.py.
// r() is clobbered like cert_file_has.
// ---------------------------------------------------------------------
capture program drop cert_svg_texts
program define cert_svg_texts, rclass
    version 16.0
    syntax , FILE(string) [LIST(string)]

    capture confirm file `"`file'"'
    if _rc {
        display as error "cert_svg_texts: cannot open `file'"
        exit 603
    }
    if `"`list'"' == "" local list `"`file'.texts.jsonl"'

    python: import __main__ as _dash_svg_main; _dash_svg_main._cert_svg_texts()

    return scalar n       = `cert_svg_n'
    return local  list    `"`cert_svg_list'"'
    return scalar maxsize = `cert_svg_maxsize'
    return scalar minsize = `cert_svg_minsize'
end

// ---------------------------------------------------------------------
// cert_svg_has_text: an exact, normalised match on one <text> element's
// whole content.  The text is passed through Macro.getLocal, never
// inlined into a Python string literal.
// ---------------------------------------------------------------------
capture program drop cert_svg_has_text
program define cert_svg_has_text, rclass
    version 16.0
    syntax , FILE(string) TEXT(string) [Lower]

    capture confirm file `"`file'"'
    if _rc {
        display as error "cert_svg_has_text: cannot open `file'"
        exit 603
    }
    local lowerflag = cond("`lower'" != "", "1", "0")

    python: import __main__ as _dash_svg_main; _dash_svg_main._cert_svg_has_text()

    return scalar found = `cert_svg_found'
    return scalar count = `cert_svg_count'
end

// ---------------------------------------------------------------------
// cert_svg_fills: fill colours grouped with counts, kinds and opacity.
// markers restricts to circle/path/polygon (svg_marker_fills).
// ---------------------------------------------------------------------
capture program drop cert_svg_fills
program define cert_svg_fills, rclass
    version 16.0
    syntax , FILE(string) [MARKERS LIST(string)]

    capture confirm file `"`file'"'
    if _rc {
        display as error "cert_svg_fills: cannot open `file'"
        exit 603
    }
    if `"`list'"' == "" local list `"`file'.fills.tsv"'
    local markersflag = cond("`markers'" != "", "1", "0")

    python: import __main__ as _dash_svg_main; _dash_svg_main._cert_svg_fills()

    return scalar n       = `cert_svg_n'
    return local  colours `"`cert_svg_colours'"'
    return local  list    `"`cert_svg_list'"'
end

// ---------------------------------------------------------------------
// cert_svg_extent: the drawn extent of one axis, fitted over its ticks.
// values() supplies tick_values in place of unreadable text labels.
// ---------------------------------------------------------------------
capture program drop cert_svg_extent
program define cert_svg_extent, rclass
    version 16.0
    syntax , FILE(string) AXIS(string) [VALUES(numlist)]

    capture confirm file `"`file'"'
    if _rc {
        display as error "cert_svg_extent: cannot open `file'"
        exit 603
    }
    if !inlist(`"`axis'"', "x", "y") {
        display as error "cert_svg_extent: axis() must be x or y"
        exit 198
    }

    python: import __main__ as _dash_svg_main; _dash_svg_main._cert_svg_extent()

    return scalar low      = `cert_svg_low'
    return scalar high     = `cert_svg_high'
    return local  space    `"`cert_svg_space'"'
    return scalar reversed = `cert_svg_reversed'
    return scalar n_ticks  = `cert_svg_n_ticks'
    return local  reason   `"`cert_svg_reason'"'
end

// ---------------------------------------------------------------------
// cert_graph_scale: the .Graph scale/tick members, read with no Python at
// all -- a graph-object query, never a macro built from file content.
//
// TRAP, found the hard way (measured 25sep2026, scratchpad probe_graph_
// scale*.do): a graph-object query is `"` then a backtick, `.<macro-
// expanded path>'`, then the closing `"` -- `` `".`name'...' `` (backtick
// BEFORE the quote) parses as something else entirely and returns empty,
// silently, with no error.  And `real(`".obj.member'"')` -- the query
// nested straight inside `real()` -- also returns missing even with the
// quote order right: the query must be assigned to a local FIRST, in its
// own statement, and only THEN passed to `real()` as `real("`local'")`.
// ---------------------------------------------------------------------
capture program drop cert_graph_scale
program define cert_graph_scale, rclass
    version 16.0
    syntax , AXIS(string) [NAME(string)]

    if !inlist(`"`axis'"', "x", "y") {
        display as error "cert_graph_scale: axis() must be x or y"
        exit 198
    }
    if `"`name'"' == "" local name "Graph"

    local gqmin     "`.`name'.plotregion1.`axis'scale.min'"
    local gqmax     "`.`name'.plotregion1.`axis'scale.max'"
    local gqcurmin  "`.`name'.plotregion1.`axis'scale.curmin'"
    local gqcurmax  "`.`name'.plotregion1.`axis'scale.curmax'"
    local gqmajmin  "`.`name'.`axis'axis1.major.min'"
    local gqmajmax  "`.`name'.`axis'axis1.major.max'"
    local gqmajdelta "`.`name'.`axis'axis1.major.delta'"

    local gsmin     = real("`gqmin'")
    local gsmax     = real("`gqmax'")
    local gscurmin  = real("`gqcurmin'")
    local gscurmax  = real("`gqcurmax'")
    local gmajmin   = real("`gqmajmin'")
    local gmajmax   = real("`gqmajmax'")
    local gmajdelta = real("`gqmajdelta'")

    return scalar min         = `gsmin'
    return scalar max         = `gsmax'
    return scalar curmin      = `gscurmin'
    return scalar curmax      = `gscurmax'
    return scalar major_min   = `gmajmin'
    return scalar major_max   = `gmajmax'
    return scalar major_delta = `gmajdelta'
end
