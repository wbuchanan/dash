*! dash.ado  v2.0
*! Main entry point for the dash command — interactive HTML dashboards
*! from Stata twoway syntax.
*!
*! Subcommands:
*!   dash <plot_spec> [if] [in] [, <opts>]   — immediate single-graph render
*!       or                                   — named graph (accumulate for build)
*!   dash kpi <stat>(varname) [if] [in] [, <opts>]
*!   dash build [, <build_opts>]
*!   dash clear
*!   dash serve [, <serve_opts>]
*!
*! Architecture (v2.0):
*!   - Mata handles ONLY segment splitting (|| / () syntax) and option-key
*!     abbreviation expansion.
*!   - ALL option parsing uses Stata's built-in -syntax- command, which
*!     provides correct varlist/if/in handling and unambiguous option matching.
*!   - JSON assembly is done in Stata using string concatenation after parsing.
*!
*! Author:  (see dash.sthlp)
*! Version: 2.0  27mar2026

// ================================================================
// Load Mata library (dash_parse.mata)
// ================================================================
// dash_parse.mata must be on the ado-path alongside dash.ado.
// findfile locates it; capture run compiles its Mata functions.
// capture is used because run of a .mata file returns rc=3000
// (Mata compilation marker) — that is normal and not an error.
// r(fn) is saved to a local immediately to survive any r() clearing.
// This top-level code executes once when dash.ado is first loaded.
// ================================================================
// Load Mata library (dash_parse.mata)
// ================================================================
// Strategy 1: use findfile to search the ado-path (works when the
//   current directory or the package's PLUS/d/ directory is on the path).
// Strategy 2: locate dash.ado via findfile to derive the package directory.
// capture run handles the Mata compilation rc=3000 without aborting.
capture findfile dash_parse.mata
if _rc == 0 {
    local _dash_matalib "`r(fn)'"
}
else {
    // Derive path from dash.ado's own location
    capture findfile dash.ado
    if _rc == 0 {
        local _dash_ado_fn "`r(fn)'"
        local _dash_matalib = substr("`_dash_ado_fn'", 1, ///
            strlen("`_dash_ado_fn'") - strlen("dash.ado")) + "dash_parse.mata"
        capture confirm file "`_dash_matalib'"
        if _rc != 0 local _dash_matalib ""
    }
}
if `"`_dash_matalib'"' != "" {
    capture run "`_dash_matalib'"
}

program define dash
    version 16.0

    // ----------------------------------------------------------------
    // Subcommand routing
    // ----------------------------------------------------------------
    // Extract the subcommand name: everything up to the first space or
    // comma.  This handles both "dash kpi ..." and "dash build, ..."
    // (where the comma immediately follows the subcommand name).
    // Compound quotes are used with regexm/substr so that double-quoted
    // option values like title("My Title") are handled safely.
    local _subcmd ""
    if regexm(`"`0'"', "^([a-zA-Z][a-zA-Z0-9_]*)") {
        local _subcmd = regexs(1)
    }
    // Remaining text after the subcommand word (may start with , or space)
    local _subcmd_len = strlen("`_subcmd'")
    local _args = substr(`"`0'"', `_subcmd_len' + 1, .)

    if "`_subcmd'" == "kpi" {
        _dash_kpi `_args'
        exit
    }
    if "`_subcmd'" == "build" {
        _dash_build `_args'
        exit
    }
    if "`_subcmd'" == "clear" {
        _dash_clear
        exit
    }
    if "`_subcmd'" == "serve" {
        _dash_serve `_args'
        exit
    }

    // ----------------------------------------------------------------
    // Plot definition  (pass full args including plot-type word)
    // ----------------------------------------------------------------
    _dash_plot `0'
end


// ================================================================
// _dash_do_render  — invoke the Python renderer (private helper)
//
// In Stata, python:...end ALWAYS terminates the enclosing program
// define block.  Any Stata code written after a python:...end inside
// a program define is executed at file-load time rather than as part
// of the program, and the subsequent end token is then unrecognised
// (r(199)).
//
// The fix: isolate the python: block in this dedicated helper so that
// post-render Stata code (browser open, display messages) can live
// in the CALLER program after calling _dash_do_render.
//
// Syntax:
//   _dash_do_render, SPEC(path) DATA(path) OUTPUT(path)           ///
//                    RENDERPY(path) [MODE(string)]
//
// mode defaults to "standalone" if omitted.
// ================================================================
program define _dash_do_render
    version 16.0
    syntax, SPEC(string) DATA(string) OUTPUT(string) RENDERPY(string) ///
            [MODE(string)]
    if `"`mode'"' == "" local mode "standalone"

    // Escape each path so double-quotes and backslashes in user-supplied paths
    // cannot break the Python string literal or inject code.  _dash_json_str
    // replaces \ with \\ and " with \", which makes the values safe for
    // regular double-quoted Python string literals.
    _dash_json_str `"`spec'"'     _py_spec
    _dash_json_str `"`data'"'     _py_data
    _dash_json_str `"`output'"'   _py_output
    _dash_json_str `"`mode'"'     _py_mode
    _dash_json_str `"`renderpy'"' _py_renderpy

    // Single-line python: calls are used here instead of a python:...end block.
    // Reason: python:...end blocks inside program defines trigger an
    // IndentationError when the ado file is loaded from the adopath (Stata
    // prepends indentation to the stored block on ado-path loads).
    // Single-line python: statements do not have this issue.
    python: import sys, runpy
    python: sys.argv = ["dash_render.py", "--spec", "`_py_spec'", "--data", "`_py_data'", "--output", "`_py_output'", "--mode", "`_py_mode'"]
    python: runpy.run_path("`_py_renderpy'", run_name="__main__")
end


// ================================================================
// _dash_validate_path  — check saving() path is safe
// ================================================================
program define _dash_validate_path
    version 16.0
    args fpath

    // FIRST, before anything expands the path inside an expression.
    // Every check below reads `fpath' inside quotes, and a path containing
    // a double quote died in the first of them with
    //     too few quotes
    //     r(132)
    // so the strpos+char() check at the end -- the one written specifically
    // to catch that character -- never ran.  It failed closed, but the user
    // saw a quoting error rather than the diagnostic this program exists to
    // give.  _dash_path_badchar() reads the macro through st_local(), where
    // its contents are a value and cannot be parsed as code.
    mata: st_local("_pv_bad", strofreal(_dash_path_badchar(st_local("fpath"))))
    if `_pv_bad' != 0 {
        display as error "dash: saving() path contains disallowed characters (shell metacharacters not permitted)."
        exit(198)
    }

    if regexm("`fpath'", "\.\.") {
        display as error "dash: saving() path may not contain '..' (path traversal not allowed)."
        exit(198)
    }
    if !regexm(lower("`fpath'"), "\.html$") {
        display as error "dash: saving() path must end in .html (got: `fpath')"
        exit(198)
    }
    // Reject shell metacharacters to prevent command injection via shell open/start/xdg-open.
    // Printable metacharacters checked via regexm character class.
    // Chars that Stata would misinterpret during macro expansion (backtick=96, dollar=36)
    // and control characters (tab=9, newline=10, CR=13) checked via strpos+char() to
    // avoid the "too few quotes" crash that occurs when a compound-quoted macro value
    // contains a backtick.
    // Parentheses are NOT rejected: every shell call site quotes the path
    // ("shell open \"`saving_path'\""), inside which ( and ) are literal, and
    // rejecting them broke every Windows path under "Program Files (x86)".
    // The characters that genuinely matter inside double quotes are handled
    // below; the rest are kept as defence in depth since paths rarely contain
    // them.
    if regexm("`fpath'", `"[;&|<>]"') {
        display as error "dash: saving() path contains disallowed characters (shell metacharacters not permitted)."
        exit(198)
    }
    // 34 = double quote, which would terminate the quoted argument at the
    // shell call site; it was previously not checked at all.
    foreach _cnum of numlist 96 36 34 9 10 13 {
        if strpos("`fpath'", char(`_cnum')) > 0 {
            display as error "dash: saving() path contains disallowed characters (shell metacharacters not permitted)."
            exit(198)
        }
    }
end


// ================================================================
// _dash_json_str  — simple JSON string escaping in pure Stata
// Usage:  _dash_json_str `"`raw'"' "_escaped"
// After: local escaped contains the JSON-safe string (no surrounding quotes)
// ================================================================
program define _dash_json_str
    version 16.0
    args raw_val out_macro
    // Escape backslash first (must be first)
    local v = subinstr(`"`raw_val'"', `"\"', `"\\"', .)
    local v = subinstr(`"`v'"', `"""', `"\""', .)
    local v = subinstr(`"`v'"', char(9),  `"\t"', .)
    local v = subinstr(`"`v'"', char(10), `"\n"', .)
    local v = subinstr(`"`v'"', char(13), `"\r"', .)
    c_local `out_macro' `"`v'"'
end


// ================================================================
// _dash_kv_json  — emit one JSON key:value pair fragment
// Sets c_local `out_macro' = `"\"key\":\"escaped_val\""'
// Only emits if val is non-empty (or force=1 passed).
// ================================================================
program define _dash_kv_json
    version 16.0
    args key val out_macro
    if `"`val'"' == "" {
        c_local `out_macro' ""
        exit
    }
    _dash_json_str `"`val'"' _esc
    c_local `out_macro' `""`key'":"`_esc'""'
end


// ================================================================
// _dash_parse_graph_opts
//
// Parse a raw graph-level options string using Stata's syntax command.
// Called as: _dash_parse_graph_opts [, opts...]
//            (i.e. pass the raw options string preceded by a comma)
//
// After the call all parsed values are in s() macros.
// ================================================================
program define _dash_parse_graph_opts, sclass
    version 16.0
    // Accept all standard graph-level options.
    // NOTE: this block is generated by scripts/regen_option_surface.py
    // from test/fixtures/abbrev_truth.json.  Do not hand-edit; the same
    // option list appears in several places and the generator keeps them
    // in step.  Capitalised letters are the minimum abbreviation, measured
    // against real twoway rather than guessed.
    // NOTE: this block is generated by scripts/regen_option_surface.py
    // from test/fixtures/abbrev_truth.json.  Do not hand-edit; the same
    // option list appears in several places and the generator keeps them
    // in step.  Capitalised letters are the minimum abbreviation, measured
    // against real twoway rather than guessed.
    // The trailing * is Stata's own catch-all: any option not declared
    // above is collected into `options' instead of aborting the user's
    // do-file.  dash.sthlp has always claimed copy-pasted twoway commands
    // still run; without this they did not.  Unmatched options are
    // reported by name, once per command -- never silently dropped.
    syntax [, ///
        TItle(string)             SUBtitle(string)          NOTE(string asis) ///
        CAPtion(string asis)      NAMe(string)              SAVing(string) ///
        XTitle(string)            YTitle(string)            XLabel(string asis) ///
        YLabel(string asis)       XLIne(string asis)        YLIne(string asis) ///
        LEGend(string asis)       BY(string asis)           XSCale(string asis) ///
        YSCale(string asis)       ASPectratio(string)       SCHeme(string) ///
        PLOTRegion(string asis)   GRAPHRegion(string asis)  BGColor(string) ///
        PLOTBGCOLOR(string)       LINK(string)              FILTer(string asis) ///
        YTITLE2(string)           XTITLE2(string)           YLABEL2(string asis) ///
        XLABEL2(string asis)      YSCALE2(string asis)      XSCALE2(string asis) ///
        XSIZe(string)             YSIZe(string)             FXSIZE(string) ///
        FYSIZE(string)            SCALE(string)             TEXT(string asis) ///
        HOVer(string)             ///
        XTICk(string asis)        YTICk(string asis)        XMTick(string asis) ///
        YMTick(string asis)       XMLabel(string asis)      YMLabel(string asis) ///
        T1title(string)           T2title(string)           B1title(string) ///
        B2title(string)           L1title(string)           L2title(string) ///
        R1title(string)           R2title(string)           TITLE2(string) ///
        SUBTITLE2(string)         NODRAW                    PLAY(string) ///
        T(string)                 B(string)                 L(string) ///
        R(string) ///
        PBGC(string)              XLA2(string asis)         XSC2(string asis) ///
        XTI2(string)              YLA2(string asis)         YSC2(string asis) ///
        YTI2(string) ///
        * ///
    ]

    // twoway accepts t(), b(), l() and r() as abbreviations of t1title(),
    // b1title(), l1title() and r1title().  Stata's -syntax- derives the
    // minimum abbreviation from the leading run of capitals, and the digit in
    // "t1title" ends that run, so "T1title" yields a minimum of "t1", not "t".
    // The four single-letter forms are therefore declared as explicit aliases
    // and folded in here.  Verified against real twoway with a .gph resolution
    // oracle -- see test/fixtures/abbrev_truth.json.
    if `"`t'"' != "" & `"`t1title'"' == "" local t1title `"`t'"'
    if `"`b'"' != "" & `"`b1title'"' == "" local b1title `"`b'"'
    if `"`l'"' != "" & `"`l1title'"' == "" local l1title `"`l'"'
    if `"`r'"' != "" & `"`r1title'"' == "" local r1title `"`r'"'
    // Fold alias forms onto their real option locals.  These are
    // ALIASES, not prefixes, so Stata's truncation-based abbreviation
    // cannot express them; they are declared above and merged here.
    // twoway accepts none of them, so this is a superset and cannot
    // break drop-in parity, but it keeps existing dash do-files working.
    if `"`pbgc'"' != "" & `"`plotbgcolor'"' == "" local plotbgcolor `"`pbgc'"'
    if `"`xla2'"' != "" & `"`xlabel2'"' == "" local xlabel2 `"`xla2'"'
    if `"`xsc2'"' != "" & `"`xscale2'"' == "" local xscale2 `"`xsc2'"'
    if `"`xti2'"' != "" & `"`xtitle2'"' == "" local xtitle2 `"`xti2'"'
    if `"`yla2'"' != "" & `"`ylabel2'"' == "" local ylabel2 `"`yla2'"'
    if `"`ysc2'"' != "" & `"`yscale2'"' == "" local yscale2 `"`ysc2'"'
    if `"`yti2'"' != "" & `"`ytitle2'"' == "" local ytitle2 `"`yti2'"'


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

    // Options dash accepts but does not yet honour.  Each supplied one
    // is recorded by name so it is reported rather than silently
    // dropped while the owning section is outstanding.
    local _dash_pending ""
    if `"`b1title'"' != "" local _dash_pending `"`_dash_pending' b1title"'
    if `"`b2title'"' != "" local _dash_pending `"`_dash_pending' b2title"'
    if `"`fxsize'"' != "" local _dash_pending `"`_dash_pending' fxsize"'
    if `"`fysize'"' != "" local _dash_pending `"`_dash_pending' fysize"'
    if `"`l1title'"' != "" local _dash_pending `"`_dash_pending' l1title"'
    if `"`l2title'"' != "" local _dash_pending `"`_dash_pending' l2title"'
    if `"`nodraw'"' != "" local _dash_pending `"`_dash_pending' nodraw"'
    if `"`play'"' != "" local _dash_pending `"`_dash_pending' play"'
    if `"`r1title'"' != "" local _dash_pending `"`_dash_pending' r1title"'
    if `"`r2title'"' != "" local _dash_pending `"`_dash_pending' r2title"'
    if `"`scale'"' != "" local _dash_pending `"`_dash_pending' scale"'
    if `"`scheme'"' != "" local _dash_pending `"`_dash_pending' scheme"'
    if `"`subtitle2'"' != "" local _dash_pending `"`_dash_pending' subtitle2"'
    if `"`t1title'"' != "" local _dash_pending `"`_dash_pending' t1title"'
    if `"`t2title'"' != "" local _dash_pending `"`_dash_pending' t2title"'
    if `"`text'"' != "" local _dash_pending `"`_dash_pending' text"'
    if `"`title2'"' != "" local _dash_pending `"`_dash_pending' title2"'
    if `"`xmlabel'"' != "" local _dash_pending `"`_dash_pending' xmlabel"'
    if `"`xmtick'"' != "" local _dash_pending `"`_dash_pending' xmtick"'
    if `"`xsize'"' != "" local _dash_pending `"`_dash_pending' xsize"'
    if `"`xtick'"' != "" local _dash_pending `"`_dash_pending' xtick"'
    if `"`ymlabel'"' != "" local _dash_pending `"`_dash_pending' ymlabel"'
    if `"`ymtick'"' != "" local _dash_pending `"`_dash_pending' ymtick"'
    if `"`ysize'"' != "" local _dash_pending `"`_dash_pending' ysize"'
    if `"`ytick'"' != "" local _dash_pending `"`_dash_pending' ytick"'
    // Whatever Stata could not match at all, via the trailing *.
    local _dash_unknown `"`options'"'

    sreturn local title        `"`title'"'
    sreturn local subtitle     `"`subtitle'"'
    sreturn local note         `"`note'"'
    sreturn local caption      `"`caption'"'
    sreturn local name         `"`name'"'
    sreturn local saving       `"`saving'"'
    sreturn local xtitle       `"`xtitle'"'
    sreturn local ytitle       `"`ytitle'"'
    sreturn local xlabel       `"`xlabel'"'
    sreturn local ylabel       `"`ylabel'"'
    sreturn local xline        `"`xline'"'
    sreturn local yline        `"`yline'"'
    sreturn local legend       `"`legend'"'
    sreturn local by           `"`by'"'
    sreturn local xscale       `"`xscale'"'
    sreturn local yscale       `"`yscale'"'
    sreturn local aspectratio  `"`aspectratio'"'
    sreturn local scheme       `"`scheme'"'
    sreturn local plotregion   `"`plotregion'"'
    sreturn local graphregion  `"`graphregion'"'
    sreturn local bgcolor      `"`bgcolor'"'
    sreturn local plotbgcolor  `"`plotbgcolor'"'
    sreturn local link         `"`link'"'
    sreturn local filter       `"`filter'"'
    sreturn local ytitle2      `"`ytitle2'"'
    sreturn local xtitle2      `"`xtitle2'"'
    sreturn local ylabel2      `"`ylabel2'"'
    sreturn local xlabel2      `"`xlabel2'"'
    sreturn local yscale2      `"`yscale2'"'
    sreturn local xscale2      `"`xscale2'"'
    sreturn local xsize        `"`xsize'"'
    sreturn local ysize        `"`ysize'"'
    sreturn local fxsize       `"`fxsize'"'
    sreturn local fysize       `"`fysize'"'
    sreturn local scale        `"`scale'"'
    sreturn local hover        `"`hover'"'
    sreturn local text         `"`text'"'
    sreturn local xtick        `"`xtick'"'
    sreturn local ytick        `"`ytick'"'
    sreturn local xmtick       `"`xmtick'"'
    sreturn local ymtick       `"`ymtick'"'
    sreturn local xmlabel      `"`xmlabel'"'
    sreturn local ymlabel      `"`ymlabel'"'
    sreturn local t1title      `"`t1title'"'
    sreturn local t2title      `"`t2title'"'
    sreturn local b1title      `"`b1title'"'
    sreturn local b2title      `"`b2title'"'
    sreturn local l1title      `"`l1title'"'
    sreturn local l2title      `"`l2title'"'
    sreturn local r1title      `"`r1title'"'
    sreturn local r2title      `"`r2title'"'
    sreturn local title2       `"`title2'"'
    sreturn local subtitle2    `"`subtitle2'"'
    sreturn local nodraw       `"`nodraw'"'
    sreturn local play         `"`play'"'
    sreturn local _pending  `"`_dash_pending'"'
    sreturn local _unknown  `"`_dash_unknown'"'
end


// ================================================================
// _dash_parse_plot_opts
//
// Parse plot-level (and possibly mixed graph-level) options.
// Called as: _dash_parse_plot_opts [, expanded_opts...]
//
// All option keys have already been expanded from abbreviations by
//
// After the call all parsed values are in s() macros.
// ================================================================
program define _dash_parse_plot_opts, sclass
    version 16.0
    // NOTE: this block is generated by scripts/regen_option_surface.py
    // from test/fixtures/abbrev_truth.json.  Do not hand-edit; the same
    // option list appears in several places and the generator keeps them
    // in step.  Capitalised letters are the minimum abbreviation, measured
    // against real twoway rather than guessed.
    // NOTE: this block is generated by scripts/regen_option_surface.py
    // from test/fixtures/abbrev_truth.json.  Do not hand-edit; the same
    // option list appears in several places and the generator keeps them
    // in step.  Capitalised letters are the minimum abbreviation, measured
    // against real twoway rather than guessed.
    // The trailing * is Stata's own catch-all: any option not declared
    // above is collected into `options' instead of aborting the user's
    // do-file.  dash.sthlp has always claimed copy-pasted twoway commands
    // still run; without this they did not.  Unmatched options are
    // reported by name, once per command -- never silently dropped.
    syntax [, ///
        MColor(string)            Msymbol(string)           MSIze(string) ///
        MSAngle(string)           MFColor(string)           MLColor(string) ///
        MLabel(string)            MLABColor(string)         MLABSize(string) ///
        MLABPosition(string)      MLABGap(string)           MLABWidth(string) ///
        MALpha(string)            MARKER(string)            LColor(string) ///
        LWidth(string)            LPattern(string)          LALpha(string) ///
        FColor(string)            FIntensity(string)        FAlpha(string) ///
        BARWidth(string)          BASE(string)              BLColor(string) ///
        BFColor(string)           JITter(string)            JSEed(string) ///
        YAXis(string)             XAXis(string)             COLORVar(string) ///
        COLPALette(string)        COLORDIScrete             COLORUSEPLEGend ///
        COLORNlevels(string)      COLORCUTs(string asis)    COLORMissing(string) ///
        BWIDth(string)            DEGree(string)            PSTYle(string) ///
        CMISSing(string)          RECAST(string)            Connect(string) ///
        BIN(string)               BINS(string)              Width(string) ///
        START(string) ///
        PERCENT                   FREQuency                 DENsity ///
        FRACtion                  Kernel(string)            N(string) ///
        LEvel(string)             BAnds(string)             AT(string asis) ///
        CIOPTS(string asis)       LINEOPTS(string asis)     FITOPTS(string asis) ///
        COLor(string)             MLWidth(string)           MSTyle(string) ///
        LStyle(string)            MLStyle(string)           MLPattern(string) ///
        BLABEL(string)            HORizontal                VERTical ///
        SORT                      RAnge(string asis)        COLORLIst(string asis) ///
        JITTERSEED(string)        TItle(string)             SUBtitle(string) ///
        NOTE(string asis)         CAPtion(string asis)      NAMe(string) ///
        SAVing(string)            XTitle(string)            YTitle(string) ///
        XLabel(string asis)       YLabel(string asis)       XLIne(string asis) ///
        YLIne(string asis)        LEGend(string asis)       BY(string asis) ///
        XSCale(string asis)       YSCale(string asis)       ASPectratio(string) ///
        SCHeme(string)            PLOTRegion(string asis)   GRAPHRegion(string asis) ///
        BGColor(string)           PLOTBGCOLOR(string)       LINK(string) ///
        FILTer(string asis)       YTITLE2(string)           XTITLE2(string) ///
        YLABEL2(string asis)      XLABEL2(string asis)      YSCALE2(string asis) ///
        XSCALE2(string asis)      XSIZe(string)             YSIZe(string) ///
        FXSIZE(string)            FYSIZE(string)            SCALE(string) ///
        TEXT(string asis)         XTICk(string asis)        YTICk(string asis) ///
        HOVer(string)             ///
        XMTick(string asis)       YMTick(string asis)       XMLabel(string asis) ///
        YMLabel(string asis)      T1title(string)           T2title(string) ///
        B1title(string)           B2title(string)           L1title(string) ///
        L2title(string)           R1title(string)           R2title(string) ///
        TITLE2(string)            SUBTITLE2(string)         NODRAW ///
        PLAY(string) ///
        BW(string)                MLG(string)               CV(string) ///
        COLV(string)              PBGC(string)              XLA2(string asis) ///
        XSC2(string asis)         XTI2(string)              YLA2(string asis) ///
        YSC2(string asis)         YTI2(string) ///
        * ///
    ]
    /* ---- plot-level ---- */

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
    // Fold alias forms onto their real option locals.  These are
    // ALIASES, not prefixes, so Stata's truncation-based abbreviation
    // cannot express them; they are declared above and merged here.
    // twoway accepts none of them, so this is a superset and cannot
    // break drop-in parity, but it keeps existing dash do-files working.
    // twoway histogram spells the bin count bins(); dash historically
    // declared only bin().  Stata accepts bin(), bins() and b() -- all
    // measured -- and they mean the same thing.
    if `"`bins'"' != "" & `"`bin'"' == "" local bin `"`bins'"'

    // level() is validated HERE, where the user can see the error,
    // rather than becoming a Python exception inside the renderer.
    if `"`level'"' != "" {
        capture confirm number `level'
        if _rc {
            display as error "level() must be a number between 0 and 100"
            exit 198
        }
        if `level' <= 0 | `level' >= 100 {
            display as error "level() must be between 0 and 100 (exclusive)"
            exit 198
        }
    }

    if `"`bw'"' != "" & `"`barwidth'"' == "" local barwidth `"`bw'"'
    if `"`mlg'"' != "" & `"`mlabgap'"' == "" local mlabgap `"`mlg'"'
    if `"`cv'"' != "" & `"`colorvar'"' == "" local colorvar `"`cv'"'
    if `"`colv'"' != "" & `"`colorvar'"' == "" local colorvar `"`colv'"'
    if `"`pbgc'"' != "" & `"`plotbgcolor'"' == "" local plotbgcolor `"`pbgc'"'
    if `"`xla2'"' != "" & `"`xlabel2'"' == "" local xlabel2 `"`xla2'"'
    if `"`xsc2'"' != "" & `"`xscale2'"' == "" local xscale2 `"`xsc2'"'
    if `"`xti2'"' != "" & `"`xtitle2'"' == "" local xtitle2 `"`xti2'"'
    if `"`yla2'"' != "" & `"`ylabel2'"' == "" local ylabel2 `"`yla2'"'
    if `"`ysc2'"' != "" & `"`yscale2'"' == "" local yscale2 `"`ysc2'"'
    if `"`yti2'"' != "" & `"`ytitle2'"' == "" local ytitle2 `"`yti2'"'

    // Options dash accepts but does not yet honour.  Each supplied one
    // is recorded by name so it is reported rather than silently
    // dropped while the owning section is outstanding.
    local _dash_pending ""
    if `"`at'"' != "" local _dash_pending `"`_dash_pending' at"'
    if `"`b1title'"' != "" local _dash_pending `"`_dash_pending' b1title"'
    if `"`b2title'"' != "" local _dash_pending `"`_dash_pending' b2title"'
    if `"`bands'"' != "" local _dash_pending `"`_dash_pending' bands"'
    if `"`bin'"' != "" local _dash_pending `"`_dash_pending' bin"'
    if `"`blabel'"' != "" local _dash_pending `"`_dash_pending' blabel"'
    if `"`ciopts'"' != "" local _dash_pending `"`_dash_pending' ciopts"'
    if `"`cmissing'"' != "" local _dash_pending `"`_dash_pending' cmissing"'
    if `"`color'"' != "" local _dash_pending `"`_dash_pending' color"'
    if `"`colorlist'"' != "" local _dash_pending `"`_dash_pending' colorlist"'
    if `"`coloruseplegend'"' != "" local _dash_pending `"`_dash_pending' coloruseplegend"'
    if `"`connect'"' != "" local _dash_pending `"`_dash_pending' connect"'
    if `"`density'"' != "" local _dash_pending `"`_dash_pending' density"'
    if `"`falpha'"' != "" local _dash_pending `"`_dash_pending' falpha"'
    if `"`fitopts'"' != "" local _dash_pending `"`_dash_pending' fitopts"'
    if `"`fraction'"' != "" local _dash_pending `"`_dash_pending' fraction"'
    if `"`frequency'"' != "" local _dash_pending `"`_dash_pending' frequency"'
    if `"`fxsize'"' != "" local _dash_pending `"`_dash_pending' fxsize"'
    if `"`fysize'"' != "" local _dash_pending `"`_dash_pending' fysize"'
    if `"`horizontal'"' != "" local _dash_pending `"`_dash_pending' horizontal"'
    if `"`jitterseed'"' != "" local _dash_pending `"`_dash_pending' jitterseed"'
    if `"`kernel'"' != "" local _dash_pending `"`_dash_pending' kernel"'
    if `"`l1title'"' != "" local _dash_pending `"`_dash_pending' l1title"'
    if `"`l2title'"' != "" local _dash_pending `"`_dash_pending' l2title"'
    if `"`level'"' != "" local _dash_pending `"`_dash_pending' level"'
    if `"`lineopts'"' != "" local _dash_pending `"`_dash_pending' lineopts"'
    if `"`lstyle'"' != "" local _dash_pending `"`_dash_pending' lstyle"'
    if `"`mlabwidth'"' != "" local _dash_pending `"`_dash_pending' mlabwidth"'
    if `"`mlcolor'"' != "" local _dash_pending `"`_dash_pending' mlcolor"'
    if `"`mlpattern'"' != "" local _dash_pending `"`_dash_pending' mlpattern"'
    if `"`mlstyle'"' != "" local _dash_pending `"`_dash_pending' mlstyle"'
    if `"`mlwidth'"' != "" local _dash_pending `"`_dash_pending' mlwidth"'
    if `"`mstyle'"' != "" local _dash_pending `"`_dash_pending' mstyle"'
    if `"`n'"' != "" local _dash_pending `"`_dash_pending' n"'
    if `"`nodraw'"' != "" local _dash_pending `"`_dash_pending' nodraw"'
    if `"`percent'"' != "" local _dash_pending `"`_dash_pending' percent"'
    if `"`play'"' != "" local _dash_pending `"`_dash_pending' play"'
    if `"`pstyle'"' != "" local _dash_pending `"`_dash_pending' pstyle"'
    if `"`r1title'"' != "" local _dash_pending `"`_dash_pending' r1title"'
    if `"`r2title'"' != "" local _dash_pending `"`_dash_pending' r2title"'
    if `"`range'"' != "" local _dash_pending `"`_dash_pending' range"'
    if `"`recast'"' != "" local _dash_pending `"`_dash_pending' recast"'
    if `"`scale'"' != "" local _dash_pending `"`_dash_pending' scale"'
    if `"`scheme'"' != "" local _dash_pending `"`_dash_pending' scheme"'
    if `"`sort'"' != "" local _dash_pending `"`_dash_pending' sort"'
    if `"`start'"' != "" local _dash_pending `"`_dash_pending' start"'
    if `"`subtitle2'"' != "" local _dash_pending `"`_dash_pending' subtitle2"'
    if `"`t1title'"' != "" local _dash_pending `"`_dash_pending' t1title"'
    if `"`t2title'"' != "" local _dash_pending `"`_dash_pending' t2title"'
    if `"`text'"' != "" local _dash_pending `"`_dash_pending' text"'
    if `"`title2'"' != "" local _dash_pending `"`_dash_pending' title2"'
    if `"`vertical'"' != "" local _dash_pending `"`_dash_pending' vertical"'
    if `"`width'"' != "" local _dash_pending `"`_dash_pending' width"'
    if `"`xmlabel'"' != "" local _dash_pending `"`_dash_pending' xmlabel"'
    if `"`xmtick'"' != "" local _dash_pending `"`_dash_pending' xmtick"'
    if `"`xsize'"' != "" local _dash_pending `"`_dash_pending' xsize"'
    if `"`xtick'"' != "" local _dash_pending `"`_dash_pending' xtick"'
    if `"`ymlabel'"' != "" local _dash_pending `"`_dash_pending' ymlabel"'
    if `"`ymtick'"' != "" local _dash_pending `"`_dash_pending' ymtick"'
    if `"`ysize'"' != "" local _dash_pending `"`_dash_pending' ysize"'
    if `"`ytick'"' != "" local _dash_pending `"`_dash_pending' ytick"'
    // Whatever Stata could not match at all, via the trailing *.
    local _dash_unknown `"`options'"'

    sreturn local mcolor           `"`mcolor'"'
    sreturn local msymbol          `"`msymbol'"'
    sreturn local msize            `"`msize'"'
    sreturn local msangle          `"`msangle'"'
    sreturn local mfcolor          `"`mfcolor'"'
    sreturn local mlcolor          `"`mlcolor'"'
    sreturn local mlabel           `"`mlabel'"'
    sreturn local mlabcolor        `"`mlabcolor'"'
    sreturn local mlabsize         `"`mlabsize'"'
    sreturn local mlabposition     `"`mlabposition'"'
    sreturn local mlabgap          `"`mlabgap'"'
    sreturn local mlabwidth        `"`mlabwidth'"'
    sreturn local malpha           `"`malpha'"'
    sreturn local marker           `"`marker'"'
    sreturn local lcolor           `"`lcolor'"'
    sreturn local lwidth           `"`lwidth'"'
    sreturn local lpattern         `"`lpattern'"'
    sreturn local lalpha           `"`lalpha'"'
    sreturn local fcolor           `"`fcolor'"'
    sreturn local fintensity       `"`fintensity'"'
    sreturn local falpha           `"`falpha'"'
    sreturn local barwidth         `"`barwidth'"'
    sreturn local base             `"`base'"'
    sreturn local blcolor          `"`blcolor'"'
    sreturn local bfcolor          `"`bfcolor'"'
    sreturn local jitter           `"`jitter'"'
    sreturn local jseed            `"`jseed'"'
    sreturn local yaxis            `"`yaxis'"'
    sreturn local xaxis            `"`xaxis'"'
    sreturn local colorvar         `"`colorvar'"'
    sreturn local colpalette       `"`colpalette'"'
    sreturn local colordiscrete    `"`colordiscrete'"'
    sreturn local coloruseplegend  `"`coloruseplegend'"'
    sreturn local colornlevels     `"`colornlevels'"'
    sreturn local colorcuts        `"`colorcuts'"'
    sreturn local colormissing     `"`colormissing'"'
    sreturn local bwidth           `"`bwidth'"'
    sreturn local degree           `"`degree'"'
    sreturn local pstyle           `"`pstyle'"'
    sreturn local cmissing         `"`cmissing'"'
    sreturn local recast           `"`recast'"'
    sreturn local connect          `"`connect'"'
    sreturn local bin              `"`bin'"'
    sreturn local width            `"`width'"'
    sreturn local start            `"`start'"'
    sreturn local percent          `"`percent'"'
    sreturn local frequency        `"`frequency'"'
    sreturn local density          `"`density'"'
    sreturn local fraction         `"`fraction'"'
    sreturn local kernel           `"`kernel'"'
    sreturn local n                `"`n'"'
    sreturn local level            `"`level'"'
    sreturn local bands            `"`bands'"'
    sreturn local at               `"`at'"'
    sreturn local ciopts           `"`ciopts'"'
    sreturn local lineopts         `"`lineopts'"'
    sreturn local fitopts          `"`fitopts'"'
    sreturn local color            `"`color'"'
    sreturn local mlwidth          `"`mlwidth'"'
    sreturn local mstyle           `"`mstyle'"'
    sreturn local lstyle           `"`lstyle'"'
    sreturn local mlstyle          `"`mlstyle'"'
    sreturn local mlpattern        `"`mlpattern'"'
    sreturn local blabel           `"`blabel'"'
    sreturn local horizontal       `"`horizontal'"'
    sreturn local vertical         `"`vertical'"'
    sreturn local sort             `"`sort'"'
    sreturn local range            `"`range'"'
    sreturn local colorlist        `"`colorlist'"'
    sreturn local jitterseed       `"`jitterseed'"'
    /* ---- graph-level (returned separately so _dash_plot can accumulate them) ---- */
    sreturn local g_title        `"`title'"'
    sreturn local g_subtitle     `"`subtitle'"'
    sreturn local g_note         `"`note'"'
    sreturn local g_caption      `"`caption'"'
    sreturn local g_name         `"`name'"'
    sreturn local g_saving       `"`saving'"'
    sreturn local g_xtitle       `"`xtitle'"'
    sreturn local g_ytitle       `"`ytitle'"'
    sreturn local g_xlabel       `"`xlabel'"'
    sreturn local g_ylabel       `"`ylabel'"'
    sreturn local g_xline        `"`xline'"'
    sreturn local g_yline        `"`yline'"'
    sreturn local g_legend       `"`legend'"'
    sreturn local g_by           `"`by'"'
    sreturn local g_xscale       `"`xscale'"'
    sreturn local g_yscale       `"`yscale'"'
    sreturn local g_aspectratio  `"`aspectratio'"'
    sreturn local g_scheme       `"`scheme'"'
    sreturn local g_plotregion   `"`plotregion'"'
    sreturn local g_graphregion  `"`graphregion'"'
    sreturn local g_bgcolor      `"`bgcolor'"'
    sreturn local g_plotbgcolor  `"`plotbgcolor'"'
    sreturn local g_link         `"`link'"'
    sreturn local g_filter       `"`filter'"'
    sreturn local g_ytitle2      `"`ytitle2'"'
    sreturn local g_xtitle2      `"`xtitle2'"'
    sreturn local g_ylabel2      `"`ylabel2'"'
    sreturn local g_xlabel2      `"`xlabel2'"'
    sreturn local g_yscale2      `"`yscale2'"'
    sreturn local g_xscale2      `"`xscale2'"'
    sreturn local g_xsize        `"`xsize'"'
    sreturn local g_ysize        `"`ysize'"'
    sreturn local g_fxsize       `"`fxsize'"'
    sreturn local g_fysize       `"`fysize'"'
    sreturn local g_scale        `"`scale'"'
    sreturn local g_hover        `"`hover'"'
    sreturn local g_text         `"`text'"'
    sreturn local g_xtick        `"`xtick'"'
    sreturn local g_ytick        `"`ytick'"'
    sreturn local g_xmtick       `"`xmtick'"'
    sreturn local g_ymtick       `"`ymtick'"'
    sreturn local g_xmlabel      `"`xmlabel'"'
    sreturn local g_ymlabel      `"`ymlabel'"'
    sreturn local g_t1title      `"`t1title'"'
    sreturn local g_t2title      `"`t2title'"'
    sreturn local g_b1title      `"`b1title'"'
    sreturn local g_b2title      `"`b2title'"'
    sreturn local g_l1title      `"`l1title'"'
    sreturn local g_l2title      `"`l2title'"'
    sreturn local g_r1title      `"`r1title'"'
    sreturn local g_r2title      `"`r2title'"'
    sreturn local g_title2       `"`title2'"'
    sreturn local g_subtitle2    `"`subtitle2'"'
    sreturn local g_nodraw       `"`nodraw'"'
    sreturn local g_play         `"`play'"'
    sreturn local _pending  `"`_dash_pending'"'
    sreturn local _unknown  `"`_dash_unknown'"'
end


// ================================================================
// _dash_parse_varpart_std  — varlist [if] [in]  (1-to-many vars)
// Sets s(varlist), s(if_clause), s(in_clause)
// ================================================================
program define _dash_parse_varpart_std, sclass
    version 16.0
    syntax varlist [if] [in] [aweight fweight pweight iweight]
    // dash does not weight its glyphs, but a pasted twoway command may carry
    // a weight expression and must not abort; it is reported as ignored.
    if `"`weight'"' != "" sreturn local _weight `"`weight'"'
    sreturn local varlist    "`varlist'"
    sreturn local if_clause  `"`if'"'
    sreturn local in_clause  `"`in'"'
end

// ================================================================
// _dash_parse_varpart_1v   — exactly 1 variable
// ================================================================
program define _dash_parse_varpart_1v, sclass
    version 16.0
    syntax varlist(min=1 max=1) [if] [in] [aweight fweight pweight iweight]
    // dash does not weight its glyphs, but a pasted twoway command may carry
    // a weight expression and must not abort; it is reported as ignored.
    if `"`weight'"' != "" sreturn local _weight `"`weight'"'
    sreturn local varlist    "`varlist'"
    sreturn local if_clause  `"`if'"'
    sreturn local in_clause  `"`in'"'
end

// ================================================================
// _dash_parse_varpart_3v   — 2 to 3 variables (range plots)
// ================================================================
program define _dash_parse_varpart_3v, sclass
    version 16.0
    syntax varlist(min=2 max=3) [if] [in] [aweight fweight pweight iweight]
    // dash does not weight its glyphs, but a pasted twoway command may carry
    // a weight expression and must not abort; it is reported as ignored.
    if `"`weight'"' != "" sreturn local _weight `"`weight'"'
    sreturn local varlist    "`varlist'"
    sreturn local if_clause  `"`if'"'
    sreturn local in_clause  `"`in'"'
end

// ================================================================
// _dash_parse_varpart_4v   — exactly 4 variables (pc* plots)
// ================================================================
program define _dash_parse_varpart_4v, sclass
    version 16.0
    syntax varlist(min=4 max=4) [if] [in] [aweight fweight pweight iweight]
    // dash does not weight its glyphs, but a pasted twoway command may carry
    // a weight expression and must not abort; it is reported as ignored.
    if `"`weight'"' != "" sreturn local _weight `"`weight'"'
    sreturn local varlist    "`varlist'"
    sreturn local if_clause  `"`if'"'
    sreturn local in_clause  `"`in'"'
end

// ================================================================
// _dash_parse_varpart_any  — arbitrary tokens [if] [in]
// Used for scatteri (literal numbers), pci, function
// ================================================================
program define _dash_parse_varpart_any, sclass
    version 16.0
    // equalok: twoway function's documented form is `function y = exp`.  Without
    // it Stata rejects the "=" with r(101) "=exp not allowed", which made the
    // `y=` stripper further down unreachable and the canonical form unusable.
    syntax anything(name=vals equalok) [if] [in]
    sreturn local vals       `"`vals'"'
    sreturn local if_clause  `"`if'"'
    sreturn local in_clause  `"`in'"'
end


// ================================================================
// _dash_plot_opts_to_json
//
// Emit the "options" JSON object fragment from s() values.
// Sets c_local `out_macro' to the JSON string.
// ================================================================
program define _dash_plot_opts_to_json, rclass
    version 16.0
    args out_macro

    local parts ""
    local nparts = 0

    // Helper: append a k:v JSON pair if value non-empty
    foreach key in mcolor msymbol msize msangle mfcolor mlcolor mlabel mlabcolor ///
                   mlabsize mlabposition mlabgap mlabwidth malpha marker lcolor ///
                   lwidth lpattern lalpha fcolor fintensity falpha barwidth base ///
                   blcolor bfcolor jitter jseed yaxis xaxis colorvar colpalette ///
                   colordiscrete coloruseplegend colornlevels colorcuts colormissing ///
                   bwidth degree pstyle cmissing recast connect bin width start ///
                   percent frequency density fraction kernel n level bands at ciopts ///
                   lineopts fitopts color mlwidth mstyle lstyle mlstyle mlpattern ///
                   blabel horizontal vertical sort range colorlist jitterseed {
        local val `"`s(`key')'"'
        if `"`val'"' != "" {
            _dash_json_str `"`val'"' _jv
            if `nparts' > 0 local parts `"`parts',"'
            local parts `"`parts'"`key'":"`_jv'""'
            local nparts = `nparts' + 1
        }
    }

    c_local `out_macro' `"{`parts'}"'
end


// ================================================================
// _dash_graph_opts_to_json
//
// Build the "graph_options" JSON object from g_* locals.
// Clears g_* locals from the caller context when done.
// Returns JSON via c_local `out_macro'.
// ================================================================
program define _dash_graph_opts_to_json, rclass
    version 16.0
    args out_macro

    local parts ""
    local nparts = 0

    foreach key in name saving title subtitle note caption               ///
                   xtitle ytitle xlabel ylabel xline yline legend by     ///
                   xscale yscale aspectratio scheme plotregion graphregion ///
                   bgcolor plotbgcolor link filter                        ///
                   ytitle2 xtitle2 ylabel2 xlabel2 yscale2 xscale2 {
        local val `"`g_`key''"'
        if `"`val'"' != "" {
            _dash_json_str `"`val'"' _jv
            if `nparts' > 0 local parts `"`parts',"'
            local parts `"`parts'"`key'":"`_jv'""'
            local nparts = `nparts' + 1
        }
    }

    c_local `out_macro' `"{`parts'}"'
end


// ================================================================
// _dash_process_segment
//
// Parse one plot segment (full text including plot type name),
// and build its JSON fragment.
//
// Usage:  _dash_process_segment `"`seg_text'"' `plottype_out' `json_out'
//
// After the call:
//   - c_local `plottype_out' = expanded plot type name
//   - c_local `json_out'     = JSON fragment for this plot
//   - Caller's g_* locals are updated if graph-level opts were found.
// ================================================================
program define _dash_process_segment, rclass
    version 16.0
    args seg_text plottype_out json_out

    // ---- extract plot type (first word) ----
    gettoken plottype rest : seg_text
    mata: _dash_expand_plottype(strlower("`plottype'"), "_pt_exp")
    local ptype "`_pt_exp'"

    if "`ptype'" == "" {
        display as error "dash: unrecognised plot type '`plottype''. " _n ///
            "Supported: scatter line connected area bar spike " _n ///
            "lfit qfit lfitci qfitci lowess lpoly lpolyci fpfit fpfitci " _n ///
            "histogram kdensity rarea rbar rspike rcap rline rconnected " _n ///
            "dot dropline rcapsym scatteri pcspike pcarrow pcbarrow " _n ///
            "pci pcscatter tsline tsrline mspline mband rscatter function"
        exit(198)
    }

    // ---- find comma separating varpart from options ----
    local comma_pos = 0
    mata: _dash_comma_pos(`"`rest'"', "comma_pos")

    if `comma_pos' > 0 {
        local varpart  = strtrim(substr(`"`rest'"', 1, `comma_pos' - 1))
        local opts_raw = strtrim(substr(`"`rest'"', `comma_pos' + 1, .))
    }
    else {
        local varpart  = strtrim(`"`rest'"')
        local opts_raw ""
    }

    // ---- pre-expand option abbreviations ----
    local opts_exp ""
    if `"`opts_raw'"' != "" {
        // Option keys used to be rewritten here by Mata before -syntax- saw
        // them.  That pre-pass is gone: dash.ado now declares Stata's own
        // measured minimum abbreviations, so Stata resolves prefixes itself.
        local opts_exp `"`opts_raw'"'  
    }

    // ---- parse varlist + if/in using type-appropriate syntax program ----
    // Determine varpart syntax group for this plot type:
    //   1v  : histogram kdensity
    //   3v  : rarea rbar rspike rcap rline rconnected rcapsym rscatter tsrline
    //   4v  : pcspike pcarrow pcbarrow
    //   any : scatteri pci pcscatter function
    //   std : everything else (including dot)

    local yvar  ""
    local xvar  ""
    local yvar1 ""
    local yvar2 ""
    local y1var ""
    local x1var ""
    local y2var ""
    local x2var ""
    local expr  ""
    local vals  ""
    local if_cl ""
    local in_cl ""

    if inlist("`ptype'", "histogram", "kdensity") {
        _dash_parse_varpart_1v `varpart'
        local yvar    = word("`s(varlist)'", 1)
        local if_cl   `"`s(if_clause)'"'
        local in_cl   `"`s(in_clause)'"'
    }
    else if inlist("`ptype'", "rarea", "rbar", "rspike", "rcap", "rline", ///
                               "rconnected", "rcapsym", "rscatter", "tsrline") {
        _dash_parse_varpart_3v `varpart'
        local vl = "`s(varlist)'"
        local yvar1 = word("`vl'", 1)
        local yvar2 = word("`vl'", 2)
        local xvar  = word("`vl'", 3)
        local if_cl `"`s(if_clause)'"'
        local in_cl `"`s(in_clause)'"'
    }
    else if inlist("`ptype'", "pcspike", "pcarrow", "pcbarrow") {
        _dash_parse_varpart_4v `varpart'
        local vl = "`s(varlist)'"
        local y1var = word("`vl'", 1)
        local x1var = word("`vl'", 2)
        local y2var = word("`vl'", 3)
        local x2var = word("`vl'", 4)
        local if_cl `"`s(if_clause)'"'
        local in_cl `"`s(in_clause)'"'
    }
    else if inlist("`ptype'", "scatteri", "pci", "pcscatter", "function") {
        _dash_parse_varpart_any `varpart'
        if "`ptype'" == "function" {
            // Remove optional "y=" prefix
            local vals = regexr(strtrim(`"`s(vals)'"'), "^[a-zA-Z][a-zA-Z0-9_]*[ ]*=[ ]*", "")
            local expr `"`vals'"'
        }
        else {
            local vals `"`s(vals)'"'
        }
        local if_cl `"`s(if_clause)'"'
        local in_cl `"`s(in_clause)'"'
    }
    else {
        // Standard: the LAST variable is x; every variable before it is a
        // y-variable and becomes its own plot, exactly as twoway does.
        //   twoway scatter mpg price weight  ->  two series
        // dash used to keep word 1 and the last word and silently discard
        // everything between, so that command drew ONE series and half the
        // user's data vanished with no error and no warning.
        if `"`varpart'"' != "" {
            _dash_parse_varpart_std `varpart'
            local vl = "`s(varlist)'"
            local nv : word count `vl'
            local yvar = word("`vl'", 1)
            if `nv' >= 2 {
                local xvar = word("`vl'", `nv')
                local nyv = `nv' - 1
                local yvarlist ""
                forvalues vi = 1/`nyv' {
                    local _thisy = word("`vl'", `vi')
                    local yvarlist `"`yvarlist' `_thisy'"'
                }
                local yvarlist = strtrim(`"`yvarlist'"')
            }
            else {
                local yvarlist "`yvar'"
                // tsline/tsrline with no x take the time variable from tsset,
                // as twoway does.  Without this xvar stayed empty, the renderer
                // hit a KeyError on "" and the user saw r(7102).
                if inlist("`ptype'", "tsline", "tsrline") {
                    local xvar `"`_dta[_TStvar]'"'
                    if `"`xvar'"' == "" {
                        // r(111) is what twoway itself returns here, verified
                        // by probe: `twoway tsline mpg' on un-tsset data gives
                        // r(111), and rc=0 once the data are tsset.
                        display as error "dash: `ptype' needs a time variable. " ///
                            "Either tsset your data first, or give the x " ///
                            "variable explicitly, as in: dash `ptype' `yvar' timevar"
                        exit(111)
                    }
                }
            }
            local if_cl `"`s(if_clause)'"'
            local in_cl `"`s(in_clause)'"'
        }
    }

    // Strip the "if"/"in" keyword prefix that syntax leaves in the macros.
    // Stata may store `if' as either " if <expr>" (with leading space) or
    // "if <expr>" (without leading space) depending on the context.
    // Using regexr() to strip the prefix robustly handles both cases.
    local if_expr ""
    local in_expr ""
    if `"`if_cl'"' != "" {
        local if_expr = strtrim(regexr(`"`if_cl'"', "^[ ]*if[ ]+", ""))
    }
    if `"`in_cl'"' != "" {
        local in_expr = strtrim(regexr(`"`in_cl'"', "^[ ]*in[ ]+", ""))
    }

    // ---- parse options (clear stale sreturn values first) ----
    sreturn clear
    if `"`opts_exp'"' != "" {
        _dash_parse_plot_opts , `opts_exp'
    }

    // Accumulate this segment's unsupported options so _dash_plot can report
    // them once for the whole command rather than once per plot segment.
    // c_local cannot read the caller's local, so hand back only THIS
    // segment's list and let _dash_plot append it.
    c_local _seg_ignored_out `"`s(_pending)' `s(_unknown)'"'

    // Accumulate graph-level options found in this segment into g_* locals
    // (these live in _dash_plot's frame, not here — use c_local to propagate)
    foreach gkey in title subtitle note caption name saving xtitle ytitle xlabel ///
            ylabel xline yline legend by xscale yscale aspectratio scheme ///
            plotregion graphregion bgcolor plotbgcolor link filter ytitle2 ///
            xtitle2 ylabel2 xlabel2 yscale2 xscale2 xsize ysize fxsize fysize ///
            scale text hover xtick ytick xmtick ymtick xmlabel ymlabel t1title ///
            t2title b1title b2title l1title l2title r1title r2title title2 ///
            subtitle2 nodraw play {
        local gval `"`s(g_`gkey')'"'
        if `"`gval'"' != "" {
            c_local g_`gkey' `"`gval'"'
        }
    }

    // ---- build plot JSON ----
    // Variable fields
    local vfields ""

    if inlist("`ptype'", "histogram", "kdensity") {
        _dash_json_str "`yvar'" _jyv
        local vfields `""var":"`_jyv'""'
    }
    else if inlist("`ptype'", "rarea", "rbar", "rspike", "rcap", "rline", ///
                               "rconnected", "rcapsym", "rscatter", "tsrline") {
        _dash_json_str "`yvar1'" _jy1
        _dash_json_str "`yvar2'" _jy2
        _dash_json_str "`xvar'"  _jxv
        local vfields `""yvar1":"`_jy1'","yvar2":"`_jy2'","xvar":"`_jxv'""'
    }
    else if inlist("`ptype'", "pcspike", "pcarrow", "pcbarrow") {
        _dash_json_str "`y1var'" _jy1
        _dash_json_str "`x1var'" _jx1
        _dash_json_str "`y2var'" _jy2
        _dash_json_str "`x2var'" _jx2
        local vfields `""y1var":"`_jy1'","x1var":"`_jx1'","y2var":"`_jy2'","x2var":"`_jx2'""'
    }
    else if "`ptype'" == "function" {
        _dash_json_str `"`expr'"' _jex
        local vfields `""expr":"`_jex'""'
    }
    else if inlist("`ptype'", "scatteri", "pci", "pcscatter") {
        // Encode as a JSON array of [y, x] pairs, each optionally followed by a
        // quoted marker label:   scatteri 20 3000 "A" 30 4000 "B"
        // This used to pair tokens blindly, checking only that the count was
        // even, so a labelled list came out sheared -- [[20,3000],["A",30],
        // [4000,"B"]] -- which is not even the right shape.
        local words_raw `"`vals'"'
        local np : word count `words_raw'
        // A point's label rides on its own pair as an optional third element,
        // [y, x, "label"], which is the shape map_scatteri reads.
        local arr "["
        local nfirst = 1
        local pi = 1
        while `pi' <= `np' {
            local yv `"`=word(`"`words_raw'"', `pi')'"'
            local xv `"`=word(`"`words_raw'"', `=`pi'+1')'"'
            if `"`xv'"' == "" {
                display as error "dash: `ptype' needs coordinates in y x pairs;" ///
                    " '`yv'' has no matching x value."
                exit(198)
            }
            local pi = `pi' + 2

            // A following NON-NUMERIC token is this point's marker label --
            // but ONLY for scatteri.  pci and pcscatter take four values per
            // record (pcscatter's are variable NAMES, which are non-numeric by
            // definition), so applying the heuristic there would swallow a
            // coordinate and shear the whole list.
            local lab ""
            if `pi' <= `np' & "`ptype'" == "scatteri" {
                local nxt `"`=word(`"`words_raw'"', `pi')'"'
                if missing(real(`"`nxt'"')) & `"`nxt'"' != "" {
                    local lab = subinstr(`"`nxt'"', `"""', "", .)
                    local pi = `pi' + 1
                }
            }

            if !`nfirst' local arr "`arr',"
            if `"`lab'"' == "" {
                local arr "`arr'[`yv',`xv']"
            }
            else {
                _dash_json_str `"`lab'"' _jlab
                local arr `"`arr'[`yv',`xv',"`_jlab'"]"'
            }
            local nfirst = 0
        }
        local arr "`arr']"
        local vfields `""values":`arr'"'
    }
    else {
        _dash_json_str "`yvar'" _jyv
        _dash_json_str "`xvar'" _jxv
        local vfields `""yvar":"`_jyv'","xvar":"`_jxv'""'
    }

    // Options JSON
    _dash_plot_opts_to_json _opts_json

    // if/in
    _dash_json_str "`if_expr'" _jif
    _dash_json_str "`in_expr'" _jin

    // Assemble.  A standard varlist with several y-variables produces ONE plot
    // object per y-variable; they are comma-joined here and the caller splices
    // them into the plots array exactly as it does separate segments, so each
    // gets its own scheme style index downstream.
    if `"`yvarlist'"' != "" {
        local seg_json ""
        local _nyv : word count `yvarlist'
        forvalues _yi = 1/`_nyv' {
            local _thisy = word(`"`yvarlist'"', `_yi')
            _dash_json_str "`_thisy'" _jyv
            _dash_json_str "`xvar'"   _jxv
            local vfields `""yvar":"`_jyv'","xvar":"`_jxv'""'
            if `_yi' > 1 local seg_json `"`seg_json',"'
            local seg_json `"`seg_json'{"type":"`ptype'",`vfields',"options":`_opts_json',"if_expr":"`_jif'","in_expr":"`_jin'"}"'
        }
    }
    else {
        local seg_json `"{"type":"`ptype'",`vfields',"options":`_opts_json',"if_expr":"`_jif'","in_expr":"`_jin'"}"'
    }

    c_local `plottype_out' "`ptype'"
    c_local `json_out'     `"`seg_json'"'
end




// ================================================================
// _dash_formats_json  -- build the "formats" map, and name the date
//                        variables that need numeric transport
//
// jsonio cannot emit display formats: its metadata branch is gated on
// inlist("`metaprint'`filenm'", ...) -- a CONCATENATION -- so with a
// non-empty filenm() the branch never fires and metaprint() is a no-op.
// StataAllToJSON has no format field either; it holds
// Variables.getDisplayFmt() internally and never serializes it.  So dash
// carries the formats itself, in its own master JSON.  jsonio is not
// modified.
// ================================================================
program define _dash_formats_json
    version 16.0
    args varlist_in out_macro datevars_macro

    local parts ""
    local nparts = 0
    local datevars ""

    foreach v of local varlist_in {
        capture confirm variable `v'
        if _rc continue
        local f : format `v'
        if `"`f'"' == "" continue

        _dash_json_str `"`f'"' _fjv
        if `nparts' > 0 local parts `"`parts',"'
        local parts `"`parts'"`v'":"`_fjv'""'
        local nparts = `nparts' + 1

        // %t and %-t followed by one of the eight kind letters, case
        // sensitively: %tc and %tC are different formats.
        if regexm(`"`f'"', "^%-?t[cCdhmqwy]") {
            local datevars `"`datevars' `v'"'
        }
    }

    c_local `out_macro'      `"{`parts'}"'
    c_local `datevars_macro' `"`datevars'"'
end


// ================================================================
// _dash_date_fmts_swap / _dash_date_fmts_restore
//
// jsonio renders a %t* variable THROUGH its display format and emits a
// JSON string ("02jan2001"), while still reporting variableIsString=false
// for it.  The renderer then coerced that to a missing value and dropped
// every row, so `dash line close date` produced a dashboard containing no
// data at all.  Giving the variable a plain numeric format for the
// duration of the jsonio call transports the underlying value intact; the
// original format is restored immediately afterwards and travels
// separately in the "formats" map.
// ================================================================
program define _dash_date_fmts_swap
    version 16.0
    args datevars

    local saved ""
    foreach v of local datevars {
        local f : format `v'
        local saved `"`saved' `f'"'
        format `v' %12.0g
    }
    c_local _dash_saved_fmts `"`saved'"'
end

program define _dash_date_fmts_restore
    version 16.0
    args datevars saved

    local i = 0
    foreach v of local datevars {
        local ++i
        local f : word `i' of `saved'
        if `"`f'"' != "" capture format `v' `f'
    }
end

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

// ================================================================
// _dash_plot  — parse and route a plot definition (v2.0)
// ================================================================
program define _dash_plot
    version 16.0

    // ---- UTF-8 safety check ----
    mata: _dash_check_utf8(strtrim(`"`0'"'))

    // ---- Split on || / () into segments + graph opts ----
    mata: _dash_split_segs(strtrim(`"`0'"'))
    // Now locals _n_segs, _seg_1 .. _seg_N, _graph_opts_raw are set.

    local n_segs   = `_n_segs'
    local gopts_raw `"`_graph_opts_raw'"'

    // ---- Initialise graph-level option accumulators ----
    foreach gk in title subtitle note caption name saving xtitle ytitle xlabel ///
          ylabel xline yline legend by xscale yscale aspectratio scheme ///
          plotregion graphregion bgcolor plotbgcolor link filter ytitle2 ///
          xtitle2 ylabel2 xlabel2 yscale2 xscale2 xsize ysize fxsize fysize ///
          scale text hover xtick ytick xmtick ymtick xmlabel ymlabel t1title ///
          t2title b1title b2title l1title l2title r1title r2title title2 ///
          subtitle2 nodraw play {
        local g_`gk' ""
    }

    // ---- Parse graph-level opts from paren-mode suffix (if any) ----
    if `"`gopts_raw'"' != "" {
        // Pre-expand abbreviations
        local gopts_exp ""
        local gopts_exp `"`gopts_raw'"'  
        _dash_parse_graph_opts , `gopts_exp'
        foreach gk in title subtitle note caption name saving xtitle ytitle xlabel ///
              ylabel xline yline legend by xscale yscale aspectratio scheme ///
              plotregion graphregion bgcolor plotbgcolor link filter ytitle2 ///
              xtitle2 ylabel2 xlabel2 yscale2 xscale2 xsize ysize fxsize fysize ///
              scale text hover xtick ytick xmtick ymtick xmlabel ymlabel t1title ///
              t2title b1title b2title l1title l2title r1title r2title title2 ///
              subtitle2 nodraw play {
            if `"`s(`gk')'"' != "" local g_`gk' `"`s(`gk')'"'
        }
    }

    local _dash_ignored_acc ""

    // ---- Parse each plot segment ----
    local plots_json ""
    forvalues k = 1/`n_segs' {
        local seg `"`_seg_`k''"'

        local _seg_ignored_out ""
        _dash_process_segment `"`seg'"' _pt_k _json_k

        if `"`_seg_ignored_out'"' != "" {
            local _dash_ignored_acc `"`_dash_ignored_acc' `_seg_ignored_out'"'
        }

        // _dash_process_segment pushes any found graph-level opts
        // into g_* locals via c_local; they are now visible here.

        if `k' > 1 local plots_json `"`plots_json',"'
        local plots_json `"`plots_json'`_json_k'"'
    }

    // ---- Report unsupported options, once, naming every one ----
    // dash accepts every twoway option so a pasted command never aborts; an
    // option it cannot honour is named here instead of vanishing.  One note
    // per command listing all of them.
    if `"`_dash_ignored_acc'"' != "" {
        _dash_report_ignored `"`_dash_ignored_acc'"'
    }

    // ---- Assemble graph_options JSON ----
    // Build JSON from the accumulated g_* locals
    local gopts_json "{"
    local gfirst = 1
    foreach gk in title subtitle note caption name saving xtitle ytitle xlabel ///
          ylabel xline yline legend by xscale yscale aspectratio scheme ///
          plotregion graphregion bgcolor plotbgcolor link filter ytitle2 ///
          xtitle2 ylabel2 xlabel2 yscale2 xscale2 xsize ysize fxsize fysize ///
          scale text hover xtick ytick xmtick ymtick xmlabel ymlabel t1title ///
          t2title b1title b2title l1title l2title r1title r2title title2 ///
          subtitle2 nodraw play {
        local gv `"`g_`gk''"'
        if `"`gv'"' != "" {
            _dash_json_str `"`gv'"' _gjv
            if !`gfirst' local gopts_json `"`gopts_json',"'
            local gopts_json `"`gopts_json'"`gk'":"`_gjv'""'
            local gfirst = 0
        }
    }
    local gopts_json `"`gopts_json'}"'

    // ---- Assemble full single-graph JSON ----
    // Promote if_expr / in_expr from the first plot segment to the graph level.
    // The renderer looks for graph-level "if_expr"/"in_expr" in graph_options or
    // at the top level; per-plot qualifiers are not read in build/server flows.
    // We use _dash_json_get_str to extract the first occurrence from plots_json —
    // this correctly handles \" escape sequences inside the value.
    local if_expr ""
    local in_expr ""
    // Only promote when there is ONE segment, in which case the qualifier was
    // written on the command as a whole.  With several segments each layer
    // carries its own if_expr and the renderer applies it per layer; promoting
    // the FIRST layer's qualifier here used to apply it to every layer, so
    //   dash (scatter y x) (scatter y x if foreign)
    // filtered both layers or neither.
    if `n_segs' == 1 {
        mata: _dash_json_get_str(`"`plots_json'"', "if_expr", "if_expr")
        mata: _dash_json_get_str(`"`plots_json'"', "in_expr", "in_expr")
    }
    _dash_json_str `"`if_expr'"' _jif_top
    _dash_json_str `"`in_expr'"' _jin_top

    local graph_json `"{"plots":[`plots_json'],"graph_options":`gopts_json',"if_expr":"`_jif_top'","in_expr":"`_jin_top'"}"'

    // ---- Route: named or immediate ----
    local graph_name `"`g_name'"'

    if `"`graph_name'"' != "" {
        _dash_register_graph `"`graph_name'"' `"`0'"' `"`graph_json'"'
    }
    else {
        _dash_render_immediate `"`graph_json'"' `"`0'"'
    }
end


// ================================================================
// _dash_register_graph  — store named graph in global registry
// ================================================================
program define _dash_register_graph
    version 16.0
    args name raw_spec json_spec

    // Split off a ", replace" sub-option BEFORE validating the name.  Stata's
    // name(string) captures the whole of "g1, replace", which then failed the
    // name regex below -- so name(g1, replace) was impossible, and the error
    // message further down told the user to type the very syntax that could
    // not work.
    local replace_flag = 0
    local _nm = strtrim(`"`name'"')
    if regexm(`"`_nm'"', "^([^,]+)[ \t]*,[ \t]*replace[ \t]*$") {
        local _nm = strtrim(regexs(1))
        local replace_flag = 1
    }
    local name `"`_nm'"'

    // Validate name format
    if !regexm("`name'", "^[a-zA-Z_][a-zA-Z0-9_]{0,31}$") {
        display as error "dash: invalid graph name '`name''. " ///
            "Names must start with a letter or underscore and contain only " ///
            "letters, digits, and underscores (max 32 chars)."
        exit(198)
    }

    // Paren-mode fallback: the sub-option may have been written on the graph
    // suffix rather than captured in name().
    if `replace_flag' == 0 {
        local raw_lower = lower(`"`raw_spec'"')
        if regexm(`"`raw_lower'"', "name\([^)]*,[ \t]*replace") {
            local replace_flag = 1
        }
    }

    // Check if name already in registry
    local registry = "${dash_graph_registry}"
    local already  = 0
    local ntokens : word count `registry'
    forvalues k = 1/`ntokens' {
        if "`:word `k' of `registry''" == "`name'" local already = 1
    }

    if `already' == 1 & `replace_flag' == 0 {
        display as error "dash: graph name '`name'' already exists. " ///
            "Use name(`name', replace) to overwrite."
        exit(198)
    }

    // Store spec and JSON
    global dash_spec_`name' `"`raw_spec'"'
    global dash_json_`name' `"`json_spec'"'

    // Update registry
    if `already' == 0 {
        if "${dash_graph_registry}" == "" {
            global dash_graph_registry "`name'"
        }
        else {
            global dash_graph_registry "${dash_graph_registry} `name'"
        }
    }

    display as text "dash: graph '`name'' registered."
end


// ================================================================
// _dash_render_immediate  — single-graph render path
// ================================================================
program define _dash_render_immediate
    version 16.0
    args json_spec raw_spec

    // ---- Extract saving() path from JSON ----
    local saving_path ""
    local open_browser = 0

    local spos = strpos(`"`json_spec'"', `""saving":"')
    if `spos' > 0 {
        local after_sav = substr(`"`json_spec'"', `spos' + 10, .)
        local saving_path = substr(`"`after_sav'"', 1, strpos(`"`after_sav'"', `"""') - 1)
    }

    if `"`saving_path'"' != "" {
        // twoway accepts saving(name), saving(name.gph) and
        // saving(name, replace).  Normalise all three to a .html path BEFORE
        // validating: validation demands a .html suffix, and it used to run
        // before the suffix was appended, so every twoway-shaped saving()
        // aborted with r(198).
        local _sv = strtrim(`"`saving_path'"')
        if regexm(`"`_sv'"', "^(.+)[ \t]*,[ \t]*replace[ \t]*$") {
            local _sv = strtrim(regexs(1))
            local replace = "replace"
        }
        if regexm(lower(`"`_sv'"'), "\.gph$") {
            local _sv = substr(`"`_sv'"', 1, strlen(`"`_sv'"') - 4)
            display as text "dash: saving() writes HTML, not a Stata .gph;" ///
                " using `_sv'.html"
        }
        if !regexm(lower(`"`_sv'"'), "\.html$") local _sv `"`_sv'.html"'
        local saving_path `"`_sv'"'
        _dash_validate_path "`saving_path'"
    }
    else {
        tempfile saving_path_tmp
        local saving_path = "`saving_path_tmp'.html"
        local open_browser = 1
    }

    if !regexm(lower("`saving_path'"), "\.html$") {
        local saving_path = "`saving_path'.html"
    }

    // ---- Determine variables needed ----
    local needed_vars ""
    mata: _dash_extract_vars(`"`json_spec'"', "needed_vars")

    // ...including the ones named only in by() or in an if-qualifier.
    // _dash_extract_vars reads plot-variable keys only, so the one-line form
    //     dash scatter mpg weight, by(foreign) saving(out.html)
    // serialised no `foreign' column at all: the renderer had nothing to
    // facet on, drew ONE panel instead of two and carried no value labels,
    // while the identical graph through `dash build' -- which has always
    // called _dash_extract_qual_vars -- drew two labelled panels.  Two
    // serialisation paths, one of them incomplete.
    local _qualvars ""
    mata: _dash_extract_qual_vars(`"`json_spec'"', "_qualvars")
    foreach _qv of local _qualvars {
        capture confirm variable `_qv'
        if _rc == 0 {
            if !`: list _qv in needed_vars' local needed_vars "`needed_vars' `_qv'"
        }
    }
    local needed_vars = strtrim("`needed_vars'")

    // scatteri, pci, pcscatter and function take literal coordinates or an
    // expression rather than variables, so having no varlist is correct for
    // them -- this guard used to reject those plot types outright.
    local _varfree = 0
    foreach _vf in scatteri pci pcscatter function {
        if strpos(`"`json_spec'"', `""type":"`_vf'""') > 0 local _varfree = 1
    }
    if "`needed_vars'" == "" & `_varfree' {
        // Nothing to serialise, but jsonio still needs a non-empty varlist, so
        // send a single variable the renderer will simply not read.
        capture unab _allv : _all
        if _rc == 0 local needed_vars : word 1 of `_allv'
    }
    if "`needed_vars'" == "" {
        display as error "dash: no variables identified in plot specification."
        exit(198)
    }

    // ---- Serialize data via jsonio ----
    tempfile data_json_path spec_json_path

    // Always export ALL rows for the needed variables.  Do NOT pre-filter with
    // if/in qualifiers here: multiple plots in the same graph can have different
    // qualifiers, and applying only the first plot's qualifier would silently
    // discard rows needed by other plots.  The Python renderer applies per-graph
    // filtering via _apply_graph_filter() using the graph-level "if_expr" /
    // "in_expr" fields that were promoted to the graph JSON by _dash_plot.

    // Check jsonio
    capture which jsonio
    if _rc != 0 {
        display as error "dash: jsonio is required but not found. Run dash_setup first."
        exit(198)
    }

    // Collect display formats, and transport date variables as
    // numbers so jsonio does not render them to text.
    _dash_formats_json "`needed_vars'" _dash_fmt_json _dash_date_vars
    local _dash_saved_fmts ""
    if `"`_dash_date_vars'"' != "" {
        _dash_date_fmts_swap "`_dash_date_vars'"
    }
    quietly jsonio out `needed_vars', ///
        what(all) filenm("`data_json_path'") ///
        metaprint(varnames varlabels vallabs labelnames)

    // Restore the user's formats immediately, whether or not
    // jsonio succeeded: the data in memory is theirs.
    if `"`_dash_date_vars'"' != "" {
        _dash_date_fmts_restore "`_dash_date_vars'" "`_dash_saved_fmts'"
    }

    // jsonio returns non-zero _rc as part of normal operation (internal Stata
    // commands like restore set _rc).  Check for actual failure by verifying
    // the output file was created, not by checking _rc.
    capture confirm file "`data_json_path'"
    if _rc != 0 {
        display as error "dash: jsonio failed to serialize data. " ///
            "Check that all variables exist and the data is loaded."
        exit(198)
    }

    // ---- Write spec JSON to temp file ----
    // Carry the session confidence level so the renderer does not have to
    // assume 95.  A per-plot level() overrides it.
    local _dash_lvl = c(level)
    local _dash_sess_scheme = c(scheme)
    _dash_json_str `"`_dash_sess_scheme'"' _sess_scheme_esc
    local master_json = `"{"graphs": [`json_spec'], "build_options": {"layout": "1 1", "theme": "", "session_scheme": "`_sess_scheme_esc'", "level": "`_dash_lvl'", "formats": `_dash_fmt_json'}}"'

    tempname fh
    file open `fh' using "`spec_json_path'", write replace text
    file write `fh' `"`master_json'"'
    file close `fh'

    // ---- Locate dash_render.py ----
    // Strategy: use findfile to locate dash_render.py on the adopath.
    // This works for both development installs (dash/ on adopath) and
    // package installs (PLUS/d/ on adopath).
    capture findfile dash_render.py
    if _rc == 0 {
        local render_py "`r(fn)'"
    }
    else {
        // Fallback: derive path from dash.ado location
        capture findfile dash.ado
        if _rc == 0 {
            local _ado_fn "`r(fn)'"
            local render_py = substr("`_ado_fn'", 1, ///
                strlen("`_ado_fn'") - strlen("dash.ado")) + "dash_render.py"
        }
        else {
            local render_py "`c(sysdir_plus)'d/dash_render.py"
        }
    }

    // ---- Invoke Python renderer via helper ----
    // (python:...end must be in a dedicated program; see _dash_do_render)
    _dash_do_render, spec("`spec_json_path'") data("`data_json_path'") ///
        output("`saving_path'") renderpy("`render_py'")

    // ---- Open in browser if no explicit saving() ----
    // The same suppression as `dash build'.  This path sets open_browser
    // only when no saving() was given, but a do-file run in batch still does
    // not want a browser window.
    if "${dash_nobrowser}" != "" local open_browser = 0
    // Stata's own nodraw, which this path already parses, means "build it but
    // do not display it".  Opening a browser window is displaying it.
    // nodraw is a flag, so its serialised value is the word itself; an
    // unset flag serialises as an empty string, which must NOT suppress.
    if strpos(`"`json_spec'"', `""nodraw":"nodraw""') > 0 local open_browser = 0
    if "`open_browser'" == "1" {
        // On Windows, `start` treats its first quoted argument as the window
        // title, not the file path.  Supply an empty title ("") so the second
        // quoted argument is interpreted as the target file.
        if "`c(os)'" == "MacOSX"  shell open        "`saving_path'"
        if "`c(os)'" == "Windows" shell start "" "`saving_path'"
        if "`c(os)'" == "Unix"    shell xdg-open "`saving_path'"
    }
    else {
        display as text `"dash: dashboard saved to `saving_path'"'
    }
end


// ================================================================
// _dash_clear  — reset global registry
// ================================================================
program define _dash_clear
    version 16.0

    local registry = "${dash_graph_registry}"
    if "`registry'" != "" {
        local ntok : word count `registry'
        forvalues k = 1/`ntok' {
            local gname : word `k' of `registry'
            capture macro drop dash_spec_`gname'
            capture macro drop dash_json_`gname'
            capture macro drop dash_opts_`gname'
            capture macro drop dash_kpi_`gname'
            capture macro drop dash_kpi_`gname'_stat
            capture macro drop dash_kpi_`gname'_var
            capture macro drop dash_kpi_`gname'_val
            capture macro drop dash_kpi_`gname'_disp
            capture macro drop dash_kpi_`gname'_fmt
            capture macro drop dash_kpi_`gname'_tit
            capture macro drop dash_kpi_`gname'_sub
            capture macro drop dash_kpi_`gname'_col
            capture macro drop dash_kpi_`gname'_bg
            capture macro drop dash_kpi_`gname'_upd
        }
    }

    macro drop dash_graph_registry
    macro drop _dash_*

    display as text "dash: registry cleared."
end


// ================================================================
// _dash_kpi  — KPI subcommand
// ================================================================
program define _dash_kpi
    version 16.0

    syntax anything(name=statspec) [if] [in] , ///
        TItle(string)           ///
        NAMe(string)            ///
        [ FMT(string)           ///
          SUBtitle(string)      ///
          COLOR(string)         ///
          BGCOLOR(string)       ///
          UPDate(string)        ///
        ]

    if !regexm(`"`statspec'"', "^([a-zA-Z0-9]+)\(([a-zA-Z_][a-zA-Z0-9_]*)\)$") {
        display as error "dash kpi: syntax is stat(varname), e.g. mean(mpg)."
        exit(198)
    }
    local stat    = regexs(1)
    local kpi_var = regexs(2)

    local valid_stats "mean sum count dcount min max median sd var cv iqr skewness p25 p50 p75"
    // pNN for any percentile, not just the three _pctile was frozen at.
    local is_pctile = 0
    if regexm("`stat'", "^p([0-9]+)$") local is_pctile = 1
    if `is_pctile' {
        local pnum = real(regexs(1))
        if `pnum' <= 0 | `pnum' >= 100 {
            display as error "dash kpi: percentile must be between 1 and 99"
            exit(198)
        }
    }
    if !`: list stat in valid_stats' & !`is_pctile' {
        display as error "dash kpi: unsupported statistic '`stat''. Choose from: `valid_stats'"
        exit(198)
    }

    confirm variable `kpi_var'

    if !regexm("`name'", "^[a-zA-Z_][a-zA-Z0-9_]{0,31}$") {
        display as error "dash kpi: invalid name '`name''."
        exit(198)
    }

    if "`update'" == "" local update "filter"
    if !inlist("`update'", "filter", "brush", "both") {
        display as error "dash kpi: update() must be filter, brush, or both."
        exit(198)
    }

    local kpi_value ""

    if inlist("`stat'", "mean", "sum", "min", "max", "sd", "count") {
        quietly summarize `kpi_var' `if' `in'
        if      "`stat'" == "mean"  local kpi_value = r(mean)
        else if "`stat'" == "sum"   local kpi_value = r(sum)
        else if "`stat'" == "min"   local kpi_value = r(min)
        else if "`stat'" == "max"   local kpi_value = r(max)
        else if "`stat'" == "sd"    local kpi_value = r(sd)
        else if "`stat'" == "count" local kpi_value = r(N)
    }
    else if "`stat'" == "dcount" {
        // codebook is NOT r-class: r(unique) is always missing, so this
        // statistic has never produced a value.  Measured alternatives:
        // inspect gives r(N_unique) but stops reporting at 100 distinct and
        // is numeric-only; tabulate dies at 200k distinct; levelsof fails
        // once r(levels) exceeds c(macrolen).  egen group() has no ceiling,
        // works for string and numeric alike, and was the fastest measured.
        tempvar _dash_grp
        quietly egen `_dash_grp' = group(`kpi_var') `if' `in'
        quietly summarize `_dash_grp', meanonly
        local kpi_value = cond(r(N) == 0, 0, r(max))
    }
    else if "`stat'" == "median" {
        quietly _pctile `kpi_var' `if' `in', p(50)
        local kpi_value = r(r1)
    }
    else if "`stat'" == "iqr" {
        quietly _pctile `kpi_var' `if' `in', p(25 75)
        local kpi_value = r(r2) - r(r1)
    }
    else if `is_pctile' {
        // Any percentile, not the three p(25 50 75) was frozen at.
        quietly _pctile `kpi_var' `if' `in', p(`pnum')
        local kpi_value = r(r1)
    }
    else if inlist("`stat'", "var", "cv", "skewness") {
        quietly summarize `kpi_var' `if' `in', detail
        if      "`stat'" == "var"      local kpi_value = r(Var)
        else if "`stat'" == "cv"       local kpi_value = cond(r(mean)==0, ., r(sd)/r(mean))
        else if "`stat'" == "skewness" local kpi_value = r(skewness)
    }

    local kpi_display = "`kpi_value'"
    if "`fmt'" != "" {
        local kpi_display : display `fmt' `kpi_value'
        local kpi_display = strtrim("`kpi_display'")
    }

    // Store each KPI field in its own global so multi-word titles/subtitles
    // are preserved.  A marker global (value "1") allows the registry to
    // detect that this name is a KPI rather than a graph.
    global dash_kpi_`name'       "1"
    global dash_kpi_`name'_stat  "`stat'"
    global dash_kpi_`name'_var   "`kpi_var'"
    global dash_kpi_`name'_val   "`kpi_value'"
    global dash_kpi_`name'_disp  "`kpi_display'"
    global dash_kpi_`name'_fmt   "`fmt'"
    global dash_kpi_`name'_tit   "`title'"
    global dash_kpi_`name'_sub   "`subtitle'"
    global dash_kpi_`name'_col   "`color'"
    global dash_kpi_`name'_bg    "`bgcolor'"
    global dash_kpi_`name'_upd   "`update'"
    // The KPI's own if/in.  Stata computes the right value above and
    // stores it, but the renderer recomputes from the full frame, so
    // without these `dash kpi mean(mpg) if foreign==1` displayed the
    // UNCONDITIONAL mean.
    local _kif = strtrim(regexr(`"`if'"', "^[ ]*if[ ]+", ""))
    local _kin = strtrim(regexr(`"`in'"', "^[ ]*in[ ]+", ""))
    global dash_kpi_`name'_if    `"`_kif'"'
    global dash_kpi_`name'_in    `"`_kin'"'

    local registry = "${dash_graph_registry}"
    local already  = 0
    local ntok : word count `registry'
    forvalues k = 1/`ntok' {
        if "`:word `k' of `registry''" == "`name'" local already = 1
    }
    if `already' == 0 {
        if "${dash_graph_registry}" == "" global dash_graph_registry "`name'"
        else global dash_graph_registry "${dash_graph_registry} `name'"
    }

    display as text "dash: KPI '`name'' registered (`stat'(`kpi_var') = `kpi_display')."
end


// ================================================================
// _dash_build  — build dashboard
// ================================================================
program define _dash_build
    version 16.0

    // Pre-extract ALL filter() options from `0' before -syntax- runs.
    // Stata's -syntax- only accepts one option of a given name; using two
    // filter() options (as in full_dashboard.do) would trigger an error.
    // _dash_extract_filters() scans `0', removes every filter(...) group,
    // joins their contents with " || ", and stores them in `_filter_parts'.
    // The cleaned command is stored in `_cmd_nofilter' and assigned back to
    // `0' so that -syntax- sees only the remaining options.
    mata: _dash_extract_filters("_filter_parts", "_cmd_nofilter")
    local filter `"`_filter_parts'"'
    local 0      `"`_cmd_nofilter'"'

    syntax [, ///
        SAVing(string)          ///
        TItle(string)           ///
        SUBtitle(string)        ///
        LAYout(string)          ///
        LINK(string)            ///
        THEME(string)           ///
        SCHeme(string)          ///
        NOBRowser               ///
        REPLACE                 ///
        SERVER                  ///
        TABS(string asis)       ///
        FILTERPOSition(string)  ///
    ]

    // ---- check registry is not empty ----
    if "${dash_graph_registry}" == "" {
        display as error "dash build: no graphs registered. Define graphs with name() before running dash build."
        exit(198)
    }

    // ---- validate saving() ----
    if "`saving'" == "" {
        display as error "dash build: saving() is required."
        exit(198)
    }
    if "`server'" != "" {
        if regexm("`saving'", "\.\.") {
            display as error "dash build: saving() path may not contain '..' (path traversal not allowed)."
            exit(198)
        }
        if !regexm(lower("`saving'"), "\.py$") {
            display as error "dash build: server mode requires saving() path ending in .py (got: `saving')"
            exit(198)
        }
    }
    else {
        _dash_validate_path "`saving'"
    }

    if "`replace'" == "" {
        capture confirm new file "`saving'"
        if _rc != 0 {
            display as error "dash build: file '`saving'' already exists. Use replace option to overwrite."
            exit(198)
        }
    }

    // ---- validate layout ----
    if "`layout'" == "" local layout "auto"
    if "`layout'" != "auto" {
        // Require strictly positive integers in "N M" grid layout.
        // ^[1-9][0-9]* rejects zero and leading-zero forms (e.g. "0 0", "0 2").
        if !regexm("`layout'", "^[1-9][0-9]* [1-9][0-9]*$") & ///
           !regexm("`layout'", "^[a-zA-Z_][a-zA-Z0-9_]*:[0-9]+,[0-9]+") & ///
           !regexm(lower("`layout'"), "^bs") {
            display as error "dash build: layout() must be 'auto', 'N M' grid (N and M >= 1), 'name:row,col' placement, or 'bs[: spec]' Bootstrap layout."
            exit(198)
        }
    }

    // ---- validate filter_position ----
    if "`filterposition'" == "" local filterposition "top"
    if "`filterposition'" != "top" & "`filterposition'" != "left" {
        display as error "dash build: filter_position() must be 'top' (default) or 'left' (sidebar)."
        exit(198)
    }

    // ---- validate link() names ----
    local registry = "${dash_graph_registry}"
    if "`link'" != "" & "`link'" != "_all" {
        local ntok_link : word count `link'
        forvalues k = 1/`ntok_link' {
            local lname : word `k' of `link'
            if !`: list lname in registry' {
                display as error "dash build: link() name '`lname'' not found in registry."
                exit(198)
            }
        }
    }

    // ---- validate filter() exclude() names ----
    // Iterate over ALL exclude(...) groups in the (possibly ||/;-joined) filter string.
    if "`filter'" != "" {
        local _excl_rem "`filter'"
        local _excl_pos = strpos("`_excl_rem'", "exclude(")
        while `_excl_pos' > 0 {
            local _excl_inner = substr("`_excl_rem'", `_excl_pos' + 8, .)
            local _excl_end   = strpos("`_excl_inner'", ")")
            if `_excl_end' > 0 {
                local _excl_names = strtrim(substr("`_excl_inner'", 1, `_excl_end' - 1))
                local n_excl : word count `_excl_names'
                forvalues ke = 1/`n_excl' {
                    local ename : word `ke' of `_excl_names'
                    if !`: list ename in registry' {
                        display as error "dash build: filter exclude() name '`ename'' not found in registry."
                        exit(198)
                    }
                }
                // Advance past the closing ) of this exclude() group
                local _excl_rem = substr("`_excl_inner'", `_excl_end' + 1, .)
            }
            else {
                // Malformed exclude() — no closing paren; stop scanning
                continue, break
            }
            local _excl_pos = strpos("`_excl_rem'", "exclude(")
        }
    }

    // Do NOT substitute "default" for an unspecified theme.  "default" is a
    // real theme name that resolves to s2color, so writing it here made the
    // session's own c(scheme) unreachable -- the renderer's precedence is
    // scheme() then theme() then c(scheme), and a theme was always present.
    // An empty theme means "the user did not ask", which is the truth.

    // ---- determine all variables needed ----
    local all_vars ""
    local ntok_reg : word count `registry'
    forvalues k = 1/`ntok_reg' {
        local gname : word `k' of `registry'

        if "${dash_kpi_`gname'}" != "" {
            local kpi_var = "${dash_kpi_`gname'_var}"
            if !`: list kpi_var in all_vars' local all_vars "`all_vars' `kpi_var'"
            // A KPI qualifier may name variables that appear nowhere else
            // (dash kpi mean(mpg) if foreign==1 needs foreign serialised, or
            // the renderer cannot reproduce the conditional value).
            local _kifx = "${dash_kpi_`gname'_if}"
            if `"`_kifx'"' != "" {
                _dash_json_str `"`_kifx'"' _kifx_esc
                local kqvars ""
                mata: _dash_extract_qual_vars(`"{"if_expr":"`_kifx_esc'"}"', "kqvars")
                foreach v of local kqvars {
                    capture confirm variable `v'
                    if _rc == 0 {
                        if !`: list v in all_vars' local all_vars "`all_vars' `v'"
                    }
                }
            }
            continue
        }

        // Use strlen to check if JSON global is set WITHOUT embedding JSON in a
        // double-quoted expression (which would break when JSON contains " chars)
        local _chk : strlen global dash_json_`gname'
        if `_chk' > 0 {
            local gvars ""
            mata: _dash_extract_vars(`"${dash_json_`gname'}"', "gvars")
            foreach v of local gvars {
                if !`: list v in all_vars' local all_vars "`all_vars' `v'"
            }
            // Also extract variables referenced only in qualifiers (if_expr)
            // and faceting (by) — these may not appear in any plot-variable key
            // but must be serialised so the renderer can apply them correctly.
            local qvars ""
            mata: _dash_extract_qual_vars(`"${dash_json_`gname'}"', "qvars")
            foreach v of local qvars {
                capture confirm variable `v'
                if _rc == 0 {
                    if !`: list v in all_vars' local all_vars "`all_vars' `v'"
                }
            }
        }
    }

    // ---- also include filter variables in the serialization ----
    // Filter variables (e.g. foreign from filter(foreign, type(dropdown)))
    // may not appear in any graph or KPI spec.  Without explicit inclusion,
    // jsonio would never serialize them, so the Python filter widgets would
    // be silently skipped.  Parse the || -delimited filter spec and add each
    // variable name (first token before the comma in each segment).
    if `"`filter'"' != "" {
        local _filt_work `"`filter'"'
        // Normalize semicolons to "||" so that semicolon-delimited multi-filter
        // strings (e.g. "foreign, type(dropdown); weight, type(range)") are split
        // the same way as the Python renderer's _parse_filter_raw does.
        local _filt_work = subinstr(`"`_filt_work'"', ";", "||", .)
        local _filt_done = 0
        while !`_filt_done' {
            local _pipe_pos = strpos(`"`_filt_work'"', "||")
            if `_pipe_pos' > 0 {
                local _this_seg = strtrim(substr(`"`_filt_work'"', 1, `_pipe_pos' - 1))
                local _filt_work = strtrim(substr(`"`_filt_work'"', `_pipe_pos' + 2, .))
            }
            else {
                local _this_seg = strtrim(`"`_filt_work'"')
                local _filt_done = 1
            }
            // Extract variable name: first word before the comma
            local _comma_pos = strpos(`"`_this_seg'"', ",")
            if `_comma_pos' > 0 {
                local _fvar = strtrim(substr(`"`_this_seg'"', 1, `_comma_pos' - 1))
            }
            else {
                local _fvar = word(`"`_this_seg'"', 1)
            }
            // A filter must name a real variable.  Silently skipping one
            // that does not look like a variable name meant
            //     dash build, filter(<script>alert, type(dropdown))
            // returned rc 0 and produced a dashboard carrying a filter that
            // did nothing, with no message anywhere.  Every other Stata
            // command rejects a name it cannot resolve, and so does this.
            //
            // The offending token is echoed only after being reduced to
            // characters that are safe to display: a value that reaches
            // here is by definition not a variable name, and interpolating
            // it into a message is the same hazard the path validator had.
            if !regexm("`_fvar'", "^[a-zA-Z_][a-zA-Z0-9_]*$") {
                mata: st_local("_fvar_safe", ///
                    regexr(st_local("_fvar"), "[^A-Za-z0-9_.\-]+", "?"))
                display as error "dash build: filter() names '`_fvar_safe''," ///
                    " which is not a valid Stata variable name."
                exit(198)
            }
            capture confirm variable `_fvar'
            if _rc != 0 {
                display as error "dash build: filter() variable `_fvar' not found."
                exit(111)
            }
            if !`: list _fvar in all_vars' {
                local all_vars "`all_vars' `_fvar'"
            }
        }
    }

    local all_vars = strtrim("`all_vars'")

    if "`all_vars'" == "" {
        display as error "dash build: no variables identified across registered graphs."
        exit(198)
    }

    // ---- serialize data via jsonio ----
    capture which jsonio
    if _rc != 0 {
        display as error "dash: jsonio is required but not found. Run dash_setup first."
        exit(198)
    }

    tempfile data_json_path master_json_path

    // Collect display formats, and transport date variables as
    // numbers so jsonio does not render them to text.
    _dash_formats_json "`all_vars'" _dash_fmt_json _dash_date_vars
    local _dash_saved_fmts ""
    if `"`_dash_date_vars'"' != "" {
        _dash_date_fmts_swap "`_dash_date_vars'"
    }
    quietly jsonio out `all_vars', ///
        what(all) filenm("`data_json_path'") ///
        metaprint(varnames varlabels vallabs labelnames)

    // Restore the user's formats immediately, whether or not
    // jsonio succeeded: the data in memory is theirs.
    if `"`_dash_date_vars'"' != "" {
        _dash_date_fmts_restore "`_dash_date_vars'" "`_dash_saved_fmts'"
    }

    capture confirm file "`data_json_path'"
    if _rc != 0 {
        display as error "dash build: jsonio failed to serialize data."
        exit(198)
    }

    // ---- assemble master JSON ----
    local graphs_json ""
    local n_graphs = 0

    forvalues k = 1/`ntok_reg' {
        local gname : word `k' of `registry'
        if "${dash_kpi_`gname'}" != "" continue

        if `n_graphs' > 0 local graphs_json `"`graphs_json', "'
        local graphs_json `"`graphs_json'${dash_json_`gname'}"'
        local n_graphs = `n_graphs' + 1
    }

    // assemble KPIs JSON
    local kpis_json ""
    local n_kpis = 0
    forvalues k = 1/`ntok_reg' {
        local gname : word `k' of `registry'
        if "${dash_kpi_`gname'}" == "" continue

        // Read each KPI field from its dedicated global (preserves multi-word values)
        // then JSON-escape the string fields before insertion.
        local kstat   = "${dash_kpi_`gname'_stat}"
        local kvar    = "${dash_kpi_`gname'_var}"
        local kval    = "${dash_kpi_`gname'_val}"
        local kdisp   = "${dash_kpi_`gname'_disp}"
        local kfmt    = "${dash_kpi_`gname'_fmt}"
        _dash_json_str `"${dash_kpi_`gname'_tit}"' _ktitle_esc
        _dash_json_str `"${dash_kpi_`gname'_sub}"' _ksub_esc
        _dash_json_str `"${dash_kpi_`gname'_col}"' _kcol_esc
        _dash_json_str `"${dash_kpi_`gname'_bg}"'  _kbg_esc
        local kupdate = "${dash_kpi_`gname'_upd}"
        _dash_json_str `"${dash_kpi_`gname'_if}"' _kif_esc
        _dash_json_str `"${dash_kpi_`gname'_in}"' _kin_esc
        _dash_json_str `"`kdisp'"' _kdisp_esc
        _dash_json_str `"`kfmt'"'  _kfmt_esc

        if `n_kpis' > 0 local kpis_json `"`kpis_json', "'
        local kpis_json `"`kpis_json'{"name":"`gname'","stat":"`kstat'","var":"`kvar'","value":"`kval'","display":"`_kdisp_esc'","fmt":"`_kfmt_esc'","title":"`_ktitle_esc'","subtitle":"`_ksub_esc'","color":"`_kcol_esc'","bgcolor":"`_kbg_esc'","update":"`kupdate'","if_expr":"`_kif_esc'","in_expr":"`_kin_esc'"}"'
        local n_kpis = `n_kpis' + 1
    }

    local filter_json ""
    if "`filter'" != "" local filter_json `"`filter'"'

    // Escape build-level title and subtitle for JSON safety
    _dash_json_str `"`title'"'    _title_esc
    _dash_json_str `"`subtitle'"' _subtitle_esc
    // Escape tabs string for JSON embedding
    _dash_json_str `"`tabs'"' _tabs_esc
    // Carry the session confidence level so the renderer does not have to
    // assume 95.  A per-plot level() overrides it.
    local _dash_lvl = c(level)
    // The session's own scheme.  A Stata user has already chosen how their
    // graphs should look; without this dash was the one command in the
    // session that ignored it.  An explicit scheme() or theme() still wins --
    // the renderer applies them in that order.
    local _dash_sess_scheme = c(scheme)
    _dash_json_str `"`scheme'"'            _scheme_esc
    _dash_json_str `"`_dash_sess_scheme'"' _sess_scheme_esc
    local master_json `"{"graphs":[`graphs_json'],"kpis":[`kpis_json'],"build_options":{"layout":"`layout'","link":"`link'","filter":"`filter_json'","theme":"`theme'","scheme":"`_scheme_esc'","session_scheme":"`_sess_scheme_esc'","title":"`_title_esc'","subtitle":"`_subtitle_esc'","registry":"`registry'","tabs":"`_tabs_esc'","filter_position":"`filterposition'","level":"`_dash_lvl'","formats":`_dash_fmt_json'}}"'

    tempname fh
    file open `fh' using "`master_json_path'", write replace text
    file write `fh' `"`master_json'"'
    file close `fh'

    // ---- Locate dash_render.py ----
    // Strategy: use findfile to locate dash_render.py on the adopath.
    // This works for both development installs (dash/ on adopath) and
    // package installs (PLUS/d/ on adopath).
    capture findfile dash_render.py
    if _rc == 0 {
        local render_py "`r(fn)'"
    }
    else {
        // Fallback: derive path from dash.ado location
        capture findfile dash.ado
        if _rc == 0 {
            local _ado_fn "`r(fn)'"
            local render_py = substr("`_ado_fn'", 1, ///
                strlen("`_ado_fn'") - strlen("dash.ado")) + "dash_render.py"
        }
        else {
            local render_py "`c(sysdir_plus)'d/dash_render.py"
        }
    }

    local render_mode "standalone"
    if "`server'" != "" local render_mode "server"

    // ---- Invoke Python renderer via helper ----
    // (python:...end must be in a dedicated program; see _dash_do_render)
    _dash_do_render, spec("`master_json_path'") data("`data_json_path'") ///
        output("`saving'") renderpy("`render_py'") mode("`render_mode'")

    if "`server'" != "" {
        display as text `"dash build: server app written to `saving'"'
        display as text `"  To launch: bokeh serve `saving'"'
    }
    else {
        display as text `"dash: dashboard saved to `saving'"'
        // nobrowser, or the global the certification runner sets once.
        // There was no way to suppress this at all: a suite that builds
        // twenty dashboards opened twenty browser tabs, and so did any
        // do-file run in batch.
        if "`nobrowser'" == "" & "${dash_nobrowser}" == "" {
            if "`c(os)'" == "MacOSX"  shell open        "`saving'"
            if "`c(os)'" == "Windows" shell start "" "`saving'"
            if "`c(os)'" == "Unix"    shell xdg-open "`saving'"
        }
    }
end


// ================================================================
// _dash_serve  — launch Bokeh Server for live interactive mode
// ================================================================
program define _dash_serve
    version 16.0

    syntax [, PORT(string) NOBROWSER TIMEOUT(string)]

    if "`port'"    == "" local port    "5006"
    if "`timeout'" == "" local timeout "0"

    if !regexm("`port'", "^[0-9]+$") {
        display as error "dash serve: port() must be a positive integer (got: `port')"
        exit(198)
    }
    local port_int = real("`port'")
    if `port_int' < 1024 | `port_int' > 65535 {
        display as error "dash serve: port() must be between 1024 and 65535 (got: `port')"
        exit(198)
    }
    if !regexm("`timeout'", "^[0-9]+$") {
        display as error "dash serve: timeout() must be a non-negative integer in minutes (got: `timeout')"
        exit(198)
    }

    if "${dash_graph_registry}" == "" {
        display as error "dash serve: no graphs registered. Define graphs with name() before running dash serve."
        exit(198)
    }

    // ---- determine all variables needed ----
    local all_vars ""
    local registry = "${dash_graph_registry}"
    local ntok_reg : word count `registry'
    forvalues k = 1/`ntok_reg' {
        local gname : word `k' of `registry'

        if "${dash_kpi_`gname'}" != "" {
            local kpi_var = "${dash_kpi_`gname'_var}"
            if !`: list kpi_var in all_vars' local all_vars "`all_vars' `kpi_var'"
            // A KPI qualifier may name variables that appear nowhere else
            // (dash kpi mean(mpg) if foreign==1 needs foreign serialised, or
            // the renderer cannot reproduce the conditional value).
            local _kifx = "${dash_kpi_`gname'_if}"
            if `"`_kifx'"' != "" {
                _dash_json_str `"`_kifx'"' _kifx_esc
                local kqvars ""
                mata: _dash_extract_qual_vars(`"{"if_expr":"`_kifx_esc'"}"', "kqvars")
                foreach v of local kqvars {
                    capture confirm variable `v'
                    if _rc == 0 {
                        if !`: list v in all_vars' local all_vars "`all_vars' `v'"
                    }
                }
            }
            continue
        }

        local _chk : strlen global dash_json_`gname'
        if `_chk' > 0 {
            local gvars ""
            mata: _dash_extract_vars(`"${dash_json_`gname'}"', "gvars")
            foreach v of local gvars {
                if !`: list v in all_vars' local all_vars "`all_vars' `v'"
            }
            // Also extract qualifier (if_expr) and facet (by) variables.
            local qvars ""
            mata: _dash_extract_qual_vars(`"${dash_json_`gname'}"', "qvars")
            foreach v of local qvars {
                capture confirm variable `v'
                if _rc == 0 {
                    if !`: list v in all_vars' local all_vars "`all_vars' `v'"
                }
            }
        }
    }
    local all_vars = strtrim("`all_vars'")

    if "`all_vars'" == "" {
        display as error "dash serve: no variables identified across registered graphs."
        exit(198)
    }

    capture which jsonio
    if _rc != 0 {
        display as error "dash: jsonio is required but not found. Run dash_setup first."
        exit(198)
    }

    tempfile data_json_path master_json_path

    // Collect display formats, and transport date variables as
    // numbers so jsonio does not render them to text.
    _dash_formats_json "`all_vars'" _dash_fmt_json _dash_date_vars
    local _dash_saved_fmts ""
    if `"`_dash_date_vars'"' != "" {
        _dash_date_fmts_swap "`_dash_date_vars'"
    }
    quietly jsonio out `all_vars', ///
        what(all) filenm("`data_json_path'") ///
        metaprint(varnames varlabels vallabs labelnames)

    // Restore the user's formats immediately, whether or not
    // jsonio succeeded: the data in memory is theirs.
    if `"`_dash_date_vars'"' != "" {
        _dash_date_fmts_restore "`_dash_date_vars'" "`_dash_saved_fmts'"
    }

    capture confirm file "`data_json_path'"
    if _rc != 0 {
        display as error "dash serve: jsonio failed to serialize data."
        exit(198)
    }

    // ---- assemble master JSON ----
    local graphs_json ""
    local n_graphs = 0
    forvalues k = 1/`ntok_reg' {
        local gname : word `k' of `registry'
        if "${dash_kpi_`gname'}" != "" continue
        if `n_graphs' > 0 local graphs_json `"`graphs_json', "'
        local graphs_json `"`graphs_json'${dash_json_`gname'}"'
        local n_graphs = `n_graphs' + 1
    }

    local kpis_json ""
    local n_kpis = 0
    forvalues k = 1/`ntok_reg' {
        local gname : word `k' of `registry'
        if "${dash_kpi_`gname'}" == "" continue
        // Read each KPI field from its dedicated global (preserves multi-word values)
        // then JSON-escape the string fields before insertion.
        local kstat   = "${dash_kpi_`gname'_stat}"
        local kvar    = "${dash_kpi_`gname'_var}"
        local kval    = "${dash_kpi_`gname'_val}"
        local kdisp   = "${dash_kpi_`gname'_disp}"
        local kfmt    = "${dash_kpi_`gname'_fmt}"
        _dash_json_str `"${dash_kpi_`gname'_tit}"' _ktitle_esc
        _dash_json_str `"${dash_kpi_`gname'_sub}"' _ksub_esc
        _dash_json_str `"${dash_kpi_`gname'_col}"' _kcol_esc
        _dash_json_str `"${dash_kpi_`gname'_bg}"'  _kbg_esc
        local kupdate = "${dash_kpi_`gname'_upd}"
        _dash_json_str `"${dash_kpi_`gname'_if}"' _kif_esc
        _dash_json_str `"${dash_kpi_`gname'_in}"' _kin_esc
        _dash_json_str `"`kdisp'"' _kdisp_esc
        _dash_json_str `"`kfmt'"'  _kfmt_esc
        if `n_kpis' > 0 local kpis_json `"`kpis_json', "'
        local kpis_json `"`kpis_json'{"name":"`gname'","stat":"`kstat'","var":"`kvar'","value":"`kval'","display":"`_kdisp_esc'","fmt":"`_kfmt_esc'","title":"`_ktitle_esc'","subtitle":"`_ksub_esc'","color":"`_kcol_esc'","bgcolor":"`_kbg_esc'","update":"`kupdate'","if_expr":"`_kif_esc'","in_expr":"`_kin_esc'"}"'
        local n_kpis = `n_kpis' + 1
    }

    // Carry the session confidence level so the renderer does not have to
    // assume 95.  A per-plot level() overrides it.
    local _dash_lvl = c(level)
    local _dash_sess_scheme = c(scheme)
    _dash_json_str `"`_dash_sess_scheme'"' _sess_scheme_esc
    local master_json `"{"graphs":[`graphs_json'],"kpis":[`kpis_json'],"build_options":{"layout":"auto","link":"","filter":"","theme":"","session_scheme":"`_sess_scheme_esc'","title":"","subtitle":"","registry":"`registry'","level":"`_dash_lvl'","formats":`_dash_fmt_json'}}"'

    tempname fh
    file open `fh' using "`master_json_path'", write replace text
    file write `fh' `"`master_json'"'
    file close `fh'

    // ---- Locate dash_render.py ----
    capture findfile dash_render.py
    if _rc == 0 {
        local render_py "`r(fn)'"
    }
    else {
        capture findfile dash.ado
        if _rc == 0 {
            local _ado_fn "`r(fn)'"
            local render_py = substr("`_ado_fn'", 1, ///
                strlen("`_ado_fn'") - strlen("dash.ado")) + "dash_render.py"
        }
        else {
            local render_py "`c(sysdir_plus)'d/dash_render.py"
        }
    }

    local no_browser_flag ""
    if "`nobrowser'" == "nobrowser" local no_browser_flag "--no-browser"

    // Temp path for the generated Bokeh Server .py app (must have .py extension).
    // Use tempfile to generate a unique base path so concurrent dash serve
    // invocations do not overwrite each other's app file.
    tempfile _serve_app_base
    local serve_app_path "`_serve_app_base'.py"

    // Escape paths for safe Python string literal interpolation (see _dash_do_render).
    _dash_json_str `"`master_json_path'"' _py_master
    _dash_json_str `"`data_json_path'"'   _py_data
    _dash_json_str `"`serve_app_path'"'   _py_serve
    _dash_json_str `"`render_py'"'        _py_render

    // Single-line python: calls to avoid ado-path IndentationError (see _dash_do_render).
    python: import sys, runpy
    python: sys.argv = ["dash_render.py", "--spec", "`_py_master'", "--data", "`_py_data'", "--output", "`_py_serve'", "--mode", "server", "--port", "`port_int'", "--timeout", "`timeout'"]
    if "`no_browser_flag'" != "" {
        python: sys.argv.append("--no-browser")
    }
    python: runpy.run_path("`_py_render'", run_name="__main__")
end
