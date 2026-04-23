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

    if regexm("`fpath'", "\.\.") {
        display as error "dash: saving() path may not contain '..' (path traversal not allowed)."
        exit(198)
    }
    if !regexm(lower("`fpath'"), "\.html$") {
        display as error "dash: saving() path must end in .html (got: `fpath')"
        exit(198)
    }
    // Reject shell metacharacters to prevent command injection via shell open/start/xdg-open.
    // Blocked characters: ; & | < > ( ) backtick(96) dollar(36) newline(10) carriage-return(13) tab(9)
    // Use char() for chars that Stata would expand/misinterpret inside double-quoted strings.
    local _shell_bad = ";&|<>()" + char(96) + char(36) + char(10) + char(13) + char(9)
    local _pi = 1
    while `_pi' <= length("`_shell_bad'") {
        local _bc = substr("`_shell_bad'", `_pi', 1)
        if strpos(`"`fpath'"', `"`_bc'"') > 0 {
            display as error "dash: saving() path contains disallowed characters (shell metacharacters not permitted)."
            exit(198)
        }
        local _pi = `_pi' + 1
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
    // Full lowercase names are required here because we pre-expand abbreviations
    // in Mata before this call.
    syntax [, ///
        title(string)             subtitle(string)          ///
        note(string asis)         caption(string asis)      ///
        name(string)              saving(string)            ///
        xtitle(string)            ytitle(string)            ///
        xlabel(string asis)       ylabel(string asis)       ///
        xline(string asis)        yline(string asis)        ///
        legend(string asis)       by(string asis)           ///
        xscale(string asis)       yscale(string asis)       ///
        aspectratio(string)       scheme(string)            ///
        plotregion(string asis)   graphregion(string asis)  ///
        bgcolor(string)           plotbgcolor(string)       ///
        link(string)              filter(string asis)       ///
        ytitle2(string)           xtitle2(string)           ///
        ylabel2(string asis)      xlabel2(string asis)      ///
        yscale2(string asis)      xscale2(string asis)      ///
    ]
    sreturn local title       `"`title'"'
    sreturn local subtitle    `"`subtitle'"'
    sreturn local note        `"`note'"'
    sreturn local caption     `"`caption'"'
    sreturn local name        `"`name'"'
    sreturn local saving      `"`saving'"'
    sreturn local xtitle      `"`xtitle'"'
    sreturn local ytitle      `"`ytitle'"'
    sreturn local xlabel      `"`xlabel'"'
    sreturn local ylabel      `"`ylabel'"'
    sreturn local xline       `"`xline'"'
    sreturn local yline       `"`yline'"'
    sreturn local legend      `"`legend'"'
    sreturn local by          `"`by'"'
    sreturn local xscale      `"`xscale'"'
    sreturn local yscale      `"`yscale'"'
    sreturn local aspectratio `"`aspectratio'"'
    sreturn local scheme      `"`scheme'"'
    sreturn local plotregion  `"`plotregion'"'
    sreturn local graphregion `"`graphregion'"'
    sreturn local bgcolor     `"`bgcolor'"'
    sreturn local plotbgcolor `"`plotbgcolor'"'
    sreturn local link        `"`link'"'
    sreturn local filter      `"`filter'"'
    sreturn local ytitle2     `"`ytitle2'"'
    sreturn local xtitle2     `"`xtitle2'"'
    sreturn local ylabel2     `"`ylabel2'"'
    sreturn local xlabel2     `"`xlabel2'"'
    sreturn local yscale2     `"`yscale2'"'
    sreturn local xscale2     `"`xscale2'"'
end


// ================================================================
// _dash_parse_plot_opts
//
// Parse plot-level (and possibly mixed graph-level) options.
// Called as: _dash_parse_plot_opts [, expanded_opts...]
//
// All option keys have already been expanded from abbreviations by
// _dash_expand_opts_str in Mata before this call.
//
// After the call all parsed values are in s() macros.
// ================================================================
program define _dash_parse_plot_opts, sclass
    version 16.0
    syntax [, ///
        mcolor(string)          msymbol(string)         msize(string)         ///
        msangle(string)         mfcolor(string)         mlcolor(string)       ///
        mlabel(string)          mlabcolor(string)       mlabsize(string)      ///
        mlabposition(string)    mlabgap(string)         mlabwidth(string)     ///
        malpha(string)          marker(string)                                ///
        lcolor(string)          lwidth(string)          lpattern(string)      ///
        lalpha(string)          fcolor(string)          fintensity(string)    ///
        falpha(string)                                                         ///
        barwidth(string)        base(string)            blcolor(string)       ///
        bfcolor(string)                                                        ///
        jitter(string)          jseed(string)                                 ///
        yaxis(string)           xaxis(string)                                 ///
        colorvar(string)        colpalette(string)                            ///
        bwidth(string)          degree(string)                                ///
        pstyle(string)          cmissing(string)        recast(string)        ///
        connect(string)                                                        ///
        title(string)           subtitle(string)        note(string asis)     ///
        caption(string asis)    name(string)            saving(string)        ///
        xtitle(string)          ytitle(string)                                ///
        xlabel(string asis)     ylabel(string asis)                           ///
        xline(string asis)      yline(string asis)                            ///
        legend(string asis)     by(string asis)                               ///
        xscale(string asis)     yscale(string asis)                           ///
        aspectratio(string)     scheme(string)                                ///
        plotregion(string asis) graphregion(string asis)                      ///
        bgcolor(string)         plotbgcolor(string)                           ///
        link(string)            filter(string asis)                           ///
        ytitle2(string)         xtitle2(string)                               ///
        ylabel2(string asis)    xlabel2(string asis)                          ///
        yscale2(string asis)    xscale2(string asis)                          ///
    ]
    /* ---- plot-level ---- */
    sreturn local mcolor       "`mcolor'"
    sreturn local msymbol      "`msymbol'"
    sreturn local msize        "`msize'"
    sreturn local msangle      "`msangle'"
    sreturn local mfcolor      "`mfcolor'"
    sreturn local mlcolor      "`mlcolor'"
    sreturn local mlabel       "`mlabel'"
    sreturn local mlabcolor    "`mlabcolor'"
    sreturn local mlabsize     "`mlabsize'"
    sreturn local mlabposition "`mlabposition'"
    sreturn local mlabgap      "`mlabgap'"
    sreturn local mlabwidth    "`mlabwidth'"
    sreturn local malpha       "`malpha'"
    sreturn local marker       "`marker'"
    sreturn local lcolor       "`lcolor'"
    sreturn local lwidth       "`lwidth'"
    sreturn local lpattern     "`lpattern'"
    sreturn local lalpha       "`lalpha'"
    sreturn local fcolor       "`fcolor'"
    sreturn local fintensity   "`fintensity'"
    sreturn local falpha       "`falpha'"
    sreturn local barwidth     "`barwidth'"
    sreturn local base         "`base'"
    sreturn local blcolor      "`blcolor'"
    sreturn local bfcolor      "`bfcolor'"
    sreturn local jitter       "`jitter'"
    sreturn local jseed        "`jseed'"
    sreturn local yaxis        "`yaxis'"
    sreturn local xaxis        "`xaxis'"
    sreturn local colorvar     "`colorvar'"
    sreturn local colpalette   "`colpalette'"
    sreturn local bwidth       "`bwidth'"
    sreturn local degree       "`degree'"
    sreturn local pstyle       "`pstyle'"
    sreturn local cmissing     "`cmissing'"
    sreturn local recast       "`recast'"
    sreturn local connect      "`connect'"
    /* ---- graph-level (returned separately so _dash_plot can accumulate them) ---- */
    sreturn local g_title       `"`title'"'
    sreturn local g_subtitle    `"`subtitle'"'
    sreturn local g_note        `"`note'"'
    sreturn local g_caption     `"`caption'"'
    sreturn local g_name        `"`name'"'
    sreturn local g_saving      `"`saving'"'
    sreturn local g_xtitle      `"`xtitle'"'
    sreturn local g_ytitle      `"`ytitle'"'
    sreturn local g_xlabel      `"`xlabel'"'
    sreturn local g_ylabel      `"`ylabel'"'
    sreturn local g_xline       `"`xline'"'
    sreturn local g_yline       `"`yline'"'
    sreturn local g_legend      `"`legend'"'
    sreturn local g_by          `"`by'"'
    sreturn local g_xscale      `"`xscale'"'
    sreturn local g_yscale      `"`yscale'"'
    sreturn local g_aspectratio `"`aspectratio'"'
    sreturn local g_scheme      `"`scheme'"'
    sreturn local g_plotregion  `"`plotregion'"'
    sreturn local g_graphregion `"`graphregion'"'
    sreturn local g_bgcolor     `"`bgcolor'"'
    sreturn local g_plotbgcolor `"`plotbgcolor'"'
    sreturn local g_link        `"`link'"'
    sreturn local g_filter      `"`filter'"'
    sreturn local g_ytitle2     `"`ytitle2'"'
    sreturn local g_xtitle2     `"`xtitle2'"'
    sreturn local g_ylabel2     `"`ylabel2'"'
    sreturn local g_xlabel2     `"`xlabel2'"'
    sreturn local g_yscale2     `"`yscale2'"'
    sreturn local g_xscale2     `"`xscale2'"'
end


// ================================================================
// _dash_parse_varpart_std  — varlist [if] [in]  (1-to-many vars)
// Sets s(varlist), s(if_clause), s(in_clause)
// ================================================================
program define _dash_parse_varpart_std, sclass
    version 16.0
    syntax varlist [if] [in]
    sreturn local varlist    "`varlist'"
    sreturn local if_clause  `"`if'"'
    sreturn local in_clause  `"`in'"'
end

// ================================================================
// _dash_parse_varpart_1v   — exactly 1 variable
// ================================================================
program define _dash_parse_varpart_1v, sclass
    version 16.0
    syntax varlist(min=1 max=1) [if] [in]
    sreturn local varlist    "`varlist'"
    sreturn local if_clause  `"`if'"'
    sreturn local in_clause  `"`in'"'
end

// ================================================================
// _dash_parse_varpart_3v   — 2 to 3 variables (range plots)
// ================================================================
program define _dash_parse_varpart_3v, sclass
    version 16.0
    syntax varlist(min=2 max=3) [if] [in]
    sreturn local varlist    "`varlist'"
    sreturn local if_clause  `"`if'"'
    sreturn local in_clause  `"`in'"'
end

// ================================================================
// _dash_parse_varpart_4v   — exactly 4 variables (pc* plots)
// ================================================================
program define _dash_parse_varpart_4v, sclass
    version 16.0
    syntax varlist(min=4 max=4) [if] [in]
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
    syntax anything(name=vals) [if] [in]
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
    foreach key in mcolor msymbol msize msangle mfcolor mlcolor mlabel ///
                   mlabcolor mlabsize mlabposition mlabgap mlabwidth    ///
                   malpha marker lcolor lwidth lpattern lalpha          ///
                   fcolor fintensity falpha barwidth base blcolor bfcolor ///
                   jitter jseed yaxis xaxis colorvar colpalette         ///
                   bwidth degree pstyle cmissing recast connect {
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
        mata: _dash_expand_opts_str(`"`opts_raw'"', "opts_exp")
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
        // Standard: 1 or 2 variables; last var is xvar
        if `"`varpart'"' != "" {
            _dash_parse_varpart_std `varpart'
            local vl = "`s(varlist)'"
            local nv : word count `vl'
            local yvar = word("`vl'", 1)
            if `nv' >= 2 local xvar = word("`vl'", `nv')
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

    // Accumulate graph-level options found in this segment into g_* locals
    // (these live in _dash_plot's frame, not here — use c_local to propagate)
    foreach gkey in name saving title subtitle note caption xtitle ytitle ///
                    xlabel ylabel xline yline legend by xscale yscale     ///
                    aspectratio scheme plotregion graphregion bgcolor      ///
                    plotbgcolor link filter                                ///
                    ytitle2 xtitle2 ylabel2 xlabel2 yscale2 xscale2 {
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
        // Encode as JSON array of [y, x] pairs
        local words_raw `"`vals'"'
        local np : word count `words_raw'
        if mod(`np', 2) != 0 {
            display as error "dash: `ptype' requires even number of values (y x pairs), got `np'."
            exit(198)
        }
        local arr "["
        forvalues pi = 1(2)`np' {
            local yv = word(`"`words_raw'"', `pi')
            local xv = word(`"`words_raw'"', `=`pi'+1')
            if `pi' > 1 local arr "`arr',"
            local arr "`arr'[`yv',`xv']"
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

    // Assemble
    local seg_json `"{"type":"`ptype'",`vfields',"options":`_opts_json',"if_expr":"`_jif'","in_expr":"`_jin'"}"'

    c_local `plottype_out' "`ptype'"
    c_local `json_out'     `"`seg_json'"'
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
    foreach gk in name saving title subtitle note caption xtitle ytitle  ///
                  xlabel ylabel xline yline legend by xscale yscale      ///
                  aspectratio scheme plotregion graphregion bgcolor       ///
                  plotbgcolor link filter                                 ///
                  ytitle2 xtitle2 ylabel2 xlabel2 yscale2 xscale2 {
        local g_`gk' ""
    }

    // ---- Parse graph-level opts from paren-mode suffix (if any) ----
    if `"`gopts_raw'"' != "" {
        // Pre-expand abbreviations
        local gopts_exp ""
        mata: _dash_expand_opts_str(`"`gopts_raw'"', "gopts_exp")
        _dash_parse_graph_opts , `gopts_exp'
        foreach gk in name saving title subtitle note caption xtitle ytitle ///
                      xlabel ylabel xline yline legend by xscale yscale    ///
                      aspectratio scheme plotregion graphregion bgcolor     ///
                      plotbgcolor link filter                               ///
                      ytitle2 xtitle2 ylabel2 xlabel2 yscale2 xscale2 {
            if `"`s(`gk')'"' != "" local g_`gk' `"`s(`gk')'"'
        }
    }

    // ---- Parse each plot segment ----
    local plots_json ""
    forvalues k = 1/`n_segs' {
        local seg `"`_seg_`k''"'

        _dash_process_segment `"`seg'"' _pt_k _json_k

        // _dash_process_segment pushes any found graph-level opts
        // into g_* locals via c_local; they are now visible here.

        if `k' > 1 local plots_json `"`plots_json',"'
        local plots_json `"`plots_json'`_json_k'"'
    }

    // ---- Assemble graph_options JSON ----
    // Build JSON from the accumulated g_* locals
    local gopts_json "{"
    local gfirst = 1
    foreach gk in name saving title subtitle note caption xtitle ytitle   ///
                  xlabel ylabel xline yline legend by xscale yscale       ///
                  aspectratio scheme plotregion graphregion bgcolor        ///
                  plotbgcolor link filter                                  ///
                  ytitle2 xtitle2 ylabel2 xlabel2 yscale2 xscale2 {
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
    mata: _dash_json_get_str(`"`plots_json'"', "if_expr", "if_expr")
    mata: _dash_json_get_str(`"`plots_json'"', "in_expr", "in_expr")
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

    // Validate name format
    if !regexm("`name'", "^[a-zA-Z_][a-zA-Z0-9_]{0,31}$") {
        display as error "dash: invalid graph name '`name''. " ///
            "Names must start with a letter or underscore and contain only " ///
            "letters, digits, and underscores (max 32 chars)."
        exit(198)
    }

    // Check for replace sub-option
    local replace_flag = 0
    local raw_lower = lower(`"`raw_spec'"')
    if regexm(`"`raw_lower'"', "name\([^)]*,[ \t]*replace") {
        local replace_flag = 1
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

    quietly jsonio out `needed_vars', ///
        what(all) filenm("`data_json_path'") ///
        metaprint(varnames varlabels vallabs labelnames)

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
    local master_json = `"{"graphs": [`json_spec'], "build_options": {"layout": "1 1", "theme": "default"}}"'

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
        name(string)            ///
        [ FMT(string)           ///
          SUBtitle(string)      ///
          COLOR(string)         ///
          BGCOLOR(string)       ///
          UPDATE(string)        ///
        ]

    if !regexm(`"`statspec'"', "^([a-zA-Z0-9]+)\(([a-zA-Z_][a-zA-Z0-9_]*)\)$") {
        display as error "dash kpi: syntax is stat(varname), e.g. mean(mpg)."
        exit(198)
    }
    local stat    = regexs(1)
    local kpi_var = regexs(2)

    local valid_stats "mean sum count dcount min max median sd p25 p50 p75"
    if !`: list stat in valid_stats' {
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
        quietly codebook `kpi_var' `if' `in'
        local kpi_value = r(unique)
    }
    else if inlist("`stat'", "median", "p25", "p50", "p75") {
        quietly _pctile `kpi_var' `if' `in', p(25 50 75)
        if      "`stat'" == "p25"    local kpi_value = r(r1)
        else if inlist("`stat'", "median", "p50") local kpi_value = r(r2)
        else if "`stat'" == "p75"    local kpi_value = r(r3)
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

    if "`theme'" == "" local theme "default"

    // ---- determine all variables needed ----
    local all_vars ""
    local ntok_reg : word count `registry'
    forvalues k = 1/`ntok_reg' {
        local gname : word `k' of `registry'

        if "${dash_kpi_`gname'}" != "" {
            local kpi_var = "${dash_kpi_`gname'_var}"
            if !`: list kpi_var in all_vars' local all_vars "`all_vars' `kpi_var'"
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
            // Only add if looks like a valid Stata variable name
            if regexm("`_fvar'", "^[a-zA-Z_][a-zA-Z0-9_]*$") {
                if !`: list _fvar in all_vars' {
                    local all_vars "`all_vars' `_fvar'"
                }
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

    quietly jsonio out `all_vars', ///
        what(all) filenm("`data_json_path'") ///
        metaprint(varnames varlabels vallabs labelnames)

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
        _dash_json_str `"`kdisp'"' _kdisp_esc
        _dash_json_str `"`kfmt'"'  _kfmt_esc

        if `n_kpis' > 0 local kpis_json `"`kpis_json', "'
        local kpis_json `"`kpis_json'{"name":"`gname'","stat":"`kstat'","var":"`kvar'","value":"`kval'","display":"`_kdisp_esc'","fmt":"`_kfmt_esc'","title":"`_ktitle_esc'","subtitle":"`_ksub_esc'","color":"`_kcol_esc'","bgcolor":"`_kbg_esc'","update":"`kupdate'"}"'
        local n_kpis = `n_kpis' + 1
    }

    local filter_json ""
    if "`filter'" != "" local filter_json `"`filter'"'

    // Escape build-level title and subtitle for JSON safety
    _dash_json_str `"`title'"'    _title_esc
    _dash_json_str `"`subtitle'"' _subtitle_esc
    // Escape tabs string for JSON embedding
    _dash_json_str `"`tabs'"' _tabs_esc
    local master_json `"{"graphs":[`graphs_json'],"kpis":[`kpis_json'],"build_options":{"layout":"`layout'","link":"`link'","filter":"`filter_json'","theme":"`theme'","title":"`_title_esc'","subtitle":"`_subtitle_esc'","registry":"`registry'","tabs":"`_tabs_esc'","filter_position":"`filterposition'"}}"'

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
        if "`c(os)'" == "MacOSX"  shell open        "`saving'"
        if "`c(os)'" == "Windows" shell start "" "`saving'"
        if "`c(os)'" == "Unix"    shell xdg-open "`saving'"
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

    quietly jsonio out `all_vars', ///
        what(all) filenm("`data_json_path'") ///
        metaprint(varnames varlabels vallabs labelnames)

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
        _dash_json_str `"`kdisp'"' _kdisp_esc
        _dash_json_str `"`kfmt'"'  _kfmt_esc
        if `n_kpis' > 0 local kpis_json `"`kpis_json', "'
        local kpis_json `"`kpis_json'{"name":"`gname'","stat":"`kstat'","var":"`kvar'","value":"`kval'","display":"`_kdisp_esc'","fmt":"`_kfmt_esc'","title":"`_ktitle_esc'","subtitle":"`_ksub_esc'","color":"`_kcol_esc'","bgcolor":"`_kbg_esc'","update":"`kupdate'"}"'
        local n_kpis = `n_kpis' + 1
    }

    local master_json `"{"graphs":[`graphs_json'],"kpis":[`kpis_json'],"build_options":{"layout":"auto","link":"","filter":"","theme":"default","title":"","subtitle":"","registry":"`registry'"}}"'

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

    // Temp path for the generated Bokeh Server .py app (must have .py extension)
    local serve_app_path "`c(tmpdir)'dash_serve_app.py"

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
