*! dash.ado
*! Main entry point for the dash command — interactive HTML dashboards
*! from Stata twoway syntax.
*!
*! Subcommands:
*!   dash <plot_spec> [if] [in] [, <opts>]   — immediate single-graph render
*!       or                                   — named graph (accumulate for build)
*!   dash kpi <stat>(varname) [if] [in] [, <opts>]
*!   dash build [, <build_opts>]
*!   dash clear
*!
*! Author:  (see dash.sthlp)
*! Version: 1.0.0  25mar2026

program define dash
    version 16.0

    // ----------------------------------------------------------------
    // Capture the full command string before any parsing  (P1A-44)
    // ----------------------------------------------------------------
    local raw_input `0'

    // ----------------------------------------------------------------
    // Detect subcommand  (P1A-45)
    // Subcommands: kpi, build, clear — everything else is a plot definition.
    // ----------------------------------------------------------------
    local first_token : word 1 of `raw_input'

    if "`first_token'" == "kpi" {
        // ---- KPI subcommand ----
        local kpi_rest = substr("`raw_input'", 4, .)
        _dash_kpi `kpi_rest'
        exit
    }

    if "`first_token'" == "build" {
        // ---- Build subcommand ----
        local build_rest = substr("`raw_input'", 6, .)
        _dash_build `build_rest'
        exit
    }

    if "`first_token'" == "clear" {
        // ---- Clear subcommand ----
        _dash_clear
        exit
    }

    if "`first_token'" == "serve" {
        // ---- Serve subcommand — launch Bokeh Server ----
        local serve_rest = substr("`raw_input'", 6, .)
        _dash_serve `serve_rest'
        exit
    }

    // ----------------------------------------------------------------
    // Plot definition — immediate render or named accumulation
    // ----------------------------------------------------------------
    _dash_plot `raw_input'
end


// ================================================================
// _dash_plot  — parse and route a plot definition
// ================================================================
program define _dash_plot
    version 16.0
    local raw `0'

    // ---- UTF-8 safety check before any processing  (P1A-54) ----
    mata: _dash_check_utf8("`raw'")

    // ---- Extract name() from the raw string if present  (P1B-01) ----
    // We do a simple regex scan: look for , name( or name(
    // We use a Stata option parser for graph-level options only after the
    // last top-level comma.  The Mata parser handles full parsing.
    //
    // Strategy: call Mata to parse → get JSON → inspect graph_options.name
    // The Mata parser stores the JSON in local macro dash_json.
    local dash_json ""
    mata: dash_parse("`raw'", "dash_json")

    // ---- Determine if named or immediate mode ----
    // Extract name from JSON (look for "name":"<id>")
    local graph_name ""
    local json_val = `"`dash_json'"'
    // Simple extraction: find "name": in graph_options section
    local npos = strpos(`"`json_val'"', `""name":"')
    if `npos' > 0 {
        local after_name = substr(`"`json_val'"', `npos' + 8, .)
        local graph_name = substr(`"`after_name'"', 1, strpos(`"`after_name'"', `"""') - 1)
    }

    if "`graph_name'" != "" {
        // ---- Named graph — store in global registry  (P1B-03 to P1B-06) ----
        _dash_register_graph "`graph_name'" `"`raw'"' `"`dash_json'"'
    }
    else {
        // ---- Immediate single-graph render  (P1A-46) ----
        _dash_render_immediate `"`dash_json'"' `"`raw'"'
    }
end


// ================================================================
// _dash_check_utf8  — Mata helper exposed for use in ado
// ================================================================
mata:
void _dash_check_utf8(string scalar s) {
    if (!_is_utf8(s)) {
        errprintf("dash: input contains non-UTF-8 bytes.\n")
        exit(198)
    }
}
end


// ================================================================
// _dash_register_graph  — store named graph in global registry
// ================================================================
program define _dash_register_graph
    version 16.0
    args name raw_spec json_spec

    // ---- validate name format  (P1B-02) ----
    if !regexm("`name'", "^[a-zA-Z_][a-zA-Z0-9_]{0,31}$") {
        display as error "dash: invalid graph name '`name''. "
        display as error "Names must start with a letter or underscore and contain only letters, digits, and underscores (max 32 chars)."
        exit(198)
    }

    // ---- check for replace sub-option in name()  (P1B-05, P1B-06) ----
    // Look for ", replace" inside the name() option value
    local replace_flag = 0
    local npos = strpos(`"`json_spec'"', `""name":"')
    // Check raw spec for name(..., replace)
    local raw_lower = lower(`"`raw_spec'"')
    if regexm(`"`raw_lower'"', "name\([^)]*,[ \t]*replace") {
        local replace_flag = 1
    }

    // Check if name already in registry
    local registry = "${dash_graph_registry}"
    local already = 0
    local ntokens : word count `registry'
    forvalues k = 1/`ntokens' {
        if "`:word `k' of `registry''" == "`name'" {
            local already = 1
        }
    }

    if `already' == 1 & `replace_flag' == 0 {
        display as error "dash: graph name '`name'' already exists. Use name(`name', replace) to overwrite."
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
// _dash_render_immediate  — single-graph render path  (P1A-46 to P1A-55)
// ================================================================
program define _dash_render_immediate
    version 16.0
    args json_spec raw_spec

    // ---- Extract saving() path from graph_options in JSON  (P1A-47) ----
    local saving_path ""
    local saving_replace = 0
    local open_browser = 0

    local spos = strpos(`"`json_spec'"', `""saving":"')
    if `spos' > 0 {
        local after_sav = substr(`"`json_spec'"', `spos' + 10, .)
        local saving_path = substr(`"`after_sav'"', 1, strpos(`"`after_sav'"', `"""') - 1)
    }

    // Validate saving() path if provided  (P1A-47)
    if "`saving_path'" != "" {
        _dash_validate_path "`saving_path'"
    }
    else {
        // default: temp file
        tempfile saving_path_tmp
        local saving_path = "`saving_path_tmp'.html"
        local open_browser = 1
    }

    // Ensure .html extension
    if !regexm(lower("`saving_path'"), "\.html$") {
        local saving_path = "`saving_path'.html"
    }

    // ---- Determine variables needed from JSON  (P1A-49) ----
    local needed_vars ""
    mata: _dash_extract_vars("`json_spec'", "dash_needed_vars")
    local needed_vars = "`dash_needed_vars'"

    if "`needed_vars'" == "" {
        display as error "dash: no variables identified in plot specification."
        exit(198)
    }

    // ---- Serialize data via jsonio  (P1A-50) ----
    tempfile data_json_path spec_json_path

    // Extract if/in from JSON for jsonio qualifier
    local if_expr ""
    local in_expr ""
    local ipos = strpos(`"`json_spec'"', `""if_expr":"')
    if `ipos' > 0 {
        local after_if = substr(`"`json_spec'"', `ipos' + 11, .)
        local if_expr = substr(`"`after_if'"', 1, strpos(`"`after_if'"', `"""') - 1)
    }
    local inpos = strpos(`"`json_spec'"', `""in_expr":"')
    if `inpos' > 0 {
        local after_in = substr(`"`json_spec'"', `inpos' + 11, .)
        local in_expr = substr(`"`after_in'"', 1, strpos(`"`after_in'"', `"""') - 1)
    }

    local if_clause ""
    local in_clause ""
    if "`if_expr'" != "" local if_clause "if `if_expr'"
    if "`in_expr'" != "" local in_clause "in `in_expr'"

    // Check jsonio is available
    capture which jsonio
    if _rc != 0 {
        display as error "dash: jsonio is required but not found. Run dash_setup first."
        exit(198)
    }

    quietly jsonio out `needed_vars' `if_clause' `in_clause', ///
        what(all) filenm("`data_json_path'") ///
        metaprint(varnames varlabels vallabs labelnames)

    if _rc != 0 {
        display as error "dash: jsonio failed to serialize data. Check that all variables exist and the data is loaded."
        exit(_rc)
    }

    // ---- Write spec JSON to temp file  (P1A-51) ----
    // Build a master JSON wrapping the graph spec
    local master_json = `"{"graphs": [`json_spec'], "build_options": {"layout": "1 1", "theme": "default"}}"'

    tempname fh
    file open `fh' using "`spec_json_path'", write replace text
    file write `fh' `"`master_json'"'
    file close `fh'

    // ---- Locate dash_render.py  (P1A-51, P1A-52) ----
    // dash_render.py is co-installed with dash.ado in the adopath d/ directory.
    local render_py "`c(sysdir_plus)'d/dash_render.py"

    python:
import sys, runpy

sys.argv = [
    "dash_render.py",
    "--spec",  r"`spec_json_path'",
    "--data",  r"`data_json_path'",
    "--output", r"`saving_path'"
]

try:
    runpy.run_path(r"`render_py'", run_name="__main__")
except SystemExit as e:
    if e.code not in (None, 0):
        from sfi import SFIToolkit
        SFIToolkit.error(int(e.code) if isinstance(e.code, int) else 198)
end

    // ---- Open in browser if no explicit saving()  (P1A-53) ----
    if "`open_browser'" == "1" {
        local open_cmd ""
        if "`c(os)'" == "MacOSX"  local open_cmd "shell open"
        if "`c(os)'" == "Windows" local open_cmd "shell start"
        if "`c(os)'" == "Unix"    local open_cmd "shell xdg-open"

        if "`open_cmd'" != "" {
            `open_cmd' "`saving_path'"
        }
    }
    else {
        display as text `"dash: dashboard saved to `saving_path'"'
    }
end


// ================================================================
// _dash_extract_vars  — Mata helper to pull variable names from JSON
// ================================================================
mata:
void _dash_extract_vars(string scalar json_str, string scalar out_macro) {
    // Extract all "yvar", "xvar", "var", "yvar1", "yvar2" values from JSON
    string rowvector keys
    string scalar found, varlist, val
    real scalar pos, endpos

    keys    = ("\"yvar\":", "\"xvar\":", "\"var\":", "\"yvar1\":", "\"yvar2\":")
    varlist = ""

    real scalar k
    for (k = 1; k <= cols(keys); k++) {
        pos = 1
        while (pos <= strlen(json_str)) {
            pos = strpos(substr(json_str, pos, .), keys[k])
            if (pos == 0) break
            // advance to start of value (past the key and colon)
            pos = pos + strlen(keys[k]) + (pos - 1)
            // skip whitespace and opening quote
            while (pos <= strlen(json_str) & (substr(json_str, pos, 1) == " " | substr(json_str, pos, 1) == char(9))) pos++
            if (pos <= strlen(json_str) & substr(json_str, pos, 1) == char(34)) {
                pos++  // skip opening quote
                endpos = pos
                while (endpos <= strlen(json_str) & substr(json_str, endpos, 1) != char(34)) endpos++
                val = substr(json_str, pos, endpos - pos)
                if (val != "" & !anyof(tokens(varlist), val)) {
                    if (varlist != "") varlist = varlist + " "
                    varlist = varlist + val
                }
                pos = endpos + 1
            }
        }
    }

    st_local(out_macro, strtrim(varlist))
}
end


// ================================================================
// _dash_validate_path  — check saving() path is safe  (P1A-47)
// ================================================================
program define _dash_validate_path
    version 16.0
    args fpath

    // Reject path traversal attempts
    if regexm("`fpath'", "\.\.") {
        display as error "dash: saving() path may not contain '..' (path traversal not allowed)."
        exit(198)
    }

    // Must end in .html (case-insensitive)
    if !regexm(lower("`fpath'"), "\.html$") {
        display as error "dash: saving() path must end in .html (got: `fpath')"
        exit(198)
    }
end


// ================================================================
// _dash_clear  — reset global registry  (P1B-07)
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
        }
    }

    // Also clear any dash_kpi_* globals not in registry
    macro drop dash_graph_registry
    macro drop _dash_*

    display as text "dash: registry cleared."
end


// ================================================================
// _dash_kpi  — KPI subcommand  (P2-01 to P2-10)
// ================================================================
program define _dash_kpi
    version 16.0

    // Parse:  stat(varname) [if] [in] , title() name() [fmt() subtitle() color() bgcolor() update()]
    syntax anything(name=statspec) [if] [in] , ///
        TItle(string)           ///
        name(string)            ///
        [ FMT(string)           ///
          SUBtitle(string)      ///
          COLOR(string)         ///
          BGCOLOR(string)       ///
          UPDATE(string)        ///
        ]

    // ---- parse statspec: must be stat(varname) ----
    if !regexm(`"`statspec'"', "^([a-zA-Z0-9]+)\(([a-zA-Z_][a-zA-Z0-9_]*)\)$") {
        display as error "dash kpi: syntax is stat(varname), e.g. mean(mpg)."
        exit(198)
    }
    local stat    = regexs(1)
    local kpi_var = regexs(2)

    // ---- validate stat is supported  (P2-02) ----
    local valid_stats "mean sum count dcount min max median sd p25 p50 p75"
    if !`: list stat in valid_stats' {
        display as error "dash kpi: unsupported statistic '`stat''. Choose from: `valid_stats'"
        exit(198)
    }

    // ---- validate variable exists ----
    confirm variable `kpi_var'

    // ---- validate name  (P1B-02) ----
    if !regexm("`name'", "^[a-zA-Z_][a-zA-Z0-9_]{0,31}$") {
        display as error "dash kpi: invalid name '`name''."
        exit(198)
    }

    // ---- validate update() option  (P2-09) ----
    if "`update'" == "" local update "filter"
    if !inlist("`update'", "filter", "brush", "both") {
        display as error "dash kpi: update() must be filter, brush, or both."
        exit(198)
    }

    // ---- compute KPI value  (P2-03 to P2-08) ----
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
        // distinct count via codebook  (P2-05)
        quietly codebook `kpi_var' `if' `in'
        local kpi_value = r(unique)
    }
    else if inlist("`stat'", "median", "p25", "p50", "p75") {
        // percentiles via _pctile  (P2-06)
        quietly _pctile `kpi_var' `if' `in', p(25 50 75)
        if      "`stat'" == "p25"    local kpi_value = r(r1)
        else if inlist("`stat'", "median", "p50") local kpi_value = r(r2)
        else if "`stat'" == "p75"    local kpi_value = r(r3)
    }

    // ---- apply fmt() if specified  (P2-08) ----
    local kpi_display = "`kpi_value'"
    if "`fmt'" != "" {
        local kpi_display : display `fmt' `kpi_value'
        local kpi_display = strtrim("`kpi_display'")
    }

    // ---- store KPI definition  (P2-10) ----
    // Format: stat;varname;value;display;fmt;title;subtitle;color;bgcolor;update
    global dash_kpi_`name' = "`stat';`kpi_var';`kpi_value';`kpi_display';`fmt';`title';`subtitle';`color';`bgcolor';`update'"

    // ---- register in graph registry ----
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
// _dash_build  — build dashboard  (P1B-08 to P1B-19)
// ================================================================
program define _dash_build
    version 16.0

    syntax [, ///
        SAVing(string)          ///
        TItle(string)           ///
        SUBtitle(string)        ///
        LAYout(string)          ///
        LINK(string)            ///
        FILTER(string)          ///
        THEME(string)           ///
        REPLACE                 ///
        SERVER                  ///
    ]

    // ---- check registry is not empty ----
    if "${dash_graph_registry}" == "" {
        display as error "dash build: no graphs registered. Define graphs with name() before running dash build."
        exit(198)
    }

    // ---- validate saving()  (P1B-10) ----
    if "`saving'" == "" {
        display as error "dash build: saving() is required."
        exit(198)
    }
    if "`server'" != "" {
        // server mode: must end in .py
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

    // ---- validate layout  (P1B-13) ----
    if "`layout'" == "" local layout "auto"
    if "`layout'" != "auto" {
        if !regexm("`layout'", "^[0-9]+ [0-9]+$") & !regexm("`layout'", "^[a-zA-Z_][a-zA-Z0-9_]*:[0-9]+,[0-9]+") {
            display as error "dash build: layout() must be 'auto', 'rows cols' integers, or 'name:row,col ...' placement syntax."
            exit(198)
        }
    }

    // ---- validate link() names exist  (P1B-11) ----
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

    // ---- validate filter(... exclude()) names exist in registry  (P1B-12) ----
    // The filter() option may contain exclude(namelist) sub-options.
    // We do a simple scan: look for "exclude(" in the filter string and
    // validate each name inside.
    if "`filter'" != "" {
        local excl_start = strpos("`filter'", "exclude(")
        if `excl_start' > 0 {
            local excl_inner = substr("`filter'", `excl_start' + 8, .)
            local excl_end   = strpos("`excl_inner'", ")")
            if `excl_end' > 0 {
                local excl_names = strtrim(substr("`excl_inner'", 1, `excl_end' - 1))
                local n_excl : word count `excl_names'
                forvalues ke = 1/`n_excl' {
                    local ename : word `ke' of `excl_names'
                    if !`: list ename in registry' {
                        display as error "dash build: filter exclude() name '`ename'' not found in registry."
                        exit(198)
                    }
                }
            }
        }
    }

    // ---- set theme default  ----
    if "`theme'" == "" local theme "default"

    // ---- determine all variables needed  (P1B-15) ----
    local all_vars ""
    local ntok_reg : word count `registry'
    forvalues k = 1/`ntok_reg' {
        local gname : word `k' of `registry'

        // Skip KPI-only entries (they store their var separately)
        if "${dash_kpi_`gname'}" != "" {
            local kpi_def = "${dash_kpi_`gname'}"
            local kpi_var = word(subinstr("`kpi_def'", ";", " ", .), 2)
            if !`: list kpi_var in all_vars' local all_vars "`all_vars' `kpi_var'"
            continue
        }

        if "${dash_json_`gname'}" != "" {
            local gvars ""
            mata: _dash_extract_vars("${dash_json_`gname'}", "gvars")
            foreach v of local gvars {
                if !`: list v in all_vars' local all_vars "`all_vars' `v'"
            }
        }
    }
    local all_vars = strtrim("`all_vars'")

    if "`all_vars'" == "" {
        display as error "dash build: no variables identified across registered graphs."
        exit(198)
    }

    // ---- serialize data via jsonio  (P1B-16) ----
    capture which jsonio
    if _rc != 0 {
        display as error "dash: jsonio is required but not found. Run dash_setup first."
        exit(198)
    }

    tempfile data_json_path master_json_path

    quietly jsonio out `all_vars', ///
        what(all) filenm("`data_json_path'") ///
        metaprint(varnames varlabels vallabs labelnames)

    if _rc != 0 {
        display as error "dash build: jsonio failed to serialize data."
        exit(_rc)
    }

    // ---- assemble master JSON  (P1B-17) ----
    local graphs_json ""
    local n_graphs = 0

    forvalues k = 1/`ntok_reg' {
        local gname : word `k' of `registry'

        // Skip KPIs — handled separately
        if "${dash_kpi_`gname'}" != "" continue

        if `n_graphs' > 0 local graphs_json = `"`graphs_json', "'
        local graphs_json = `"`graphs_json'${dash_json_`gname'}"'
        local n_graphs = `n_graphs' + 1
    }

    // assemble KPIs JSON
    local kpis_json ""
    local n_kpis = 0
    forvalues k = 1/`ntok_reg' {
        local gname : word `k' of `registry'
        if "${dash_kpi_`gname'}" == "" continue

        local kpi_def = "${dash_kpi_`gname'}"
        // fields: stat;varname;value;display;fmt;title;subtitle;color;bgcolor;update
        local kstat    = word(subinstr("`kpi_def'", ";", " ", .), 1)
        local kvar     = word(subinstr("`kpi_def'", ";", " ", .), 2)
        local kval     = word(subinstr("`kpi_def'", ";", " ", .), 3)
        local kdisp    = word(subinstr("`kpi_def'", ";", " ", .), 4)
        local kfmt     = word(subinstr("`kpi_def'", ";", " ", .), 5)
        local ktitle   = word(subinstr("`kpi_def'", ";", " ", .), 6)
        local ksub     = word(subinstr("`kpi_def'", ";", " ", .), 7)
        local kcolor   = word(subinstr("`kpi_def'", ";", " ", .), 8)
        local kbg      = word(subinstr("`kpi_def'", ";", " ", .), 9)
        local kupdate  = word(subinstr("`kpi_def'", ";", " ", .), 10)

        if `n_kpis' > 0 local kpis_json = `"`kpis_json', "'
        local kpis_json = `"`kpis_json'{"name":"`gname'","stat":"`kstat'","var":"`kvar'","value":"`kval'","display":"`kdisp'","fmt":"`kfmt'","title":"`ktitle'","subtitle":"`ksub'","color":"`kcolor'","bgcolor":"`kbg'","update":"`kupdate'"}"'
        local n_kpis = `n_kpis' + 1
    }

    // assemble filter JSON if provided
    local filter_json = `"""'
    if "`filter'" != "" {
        local filter_json = `"`filter'"'
    }

    local master_json = `"{"graphs":[`graphs_json'],"kpis":[`kpis_json'],"build_options":{"layout":"`layout'","link":"`link'","filter":"`filter_json'","theme":"`theme'","title":"`title'","subtitle":"`subtitle'","registry":"`registry'"}}"'

    // ---- write master JSON to temp file ----
    tempname fh
    file open `fh' using "`master_json_path'", write replace text
    file write `fh' `"`master_json'"'
    file close `fh'

    // ---- Locate dash_render.py  (P1B-18) ----
    local render_py "`c(sysdir_plus)'d/dash_render.py"

    // ---- determine rendering mode ----
    local render_mode "standalone"
    if "`server'" != "" local render_mode "server"

    // ---- call Python renderer  (P1B-18, P1B-19) ----
    python:
import sys, runpy

sys.argv = [
    "dash_render.py",
    "--spec",   r"`master_json_path'",
    "--data",   r"`data_json_path'",
    "--output", r"`saving'",
    "--mode",   "`render_mode'"
]

try:
    runpy.run_path(r"`render_py'", run_name="__main__")
except SystemExit as e:
    if e.code not in (None, 0):
        from sfi import SFIToolkit
        SFIToolkit.error(int(e.code) if isinstance(e.code, int) else 198)
end

    if "`server'" != "" {
        display as text `"dash build: server app written to `saving'"'
        display as text `"  To launch: bokeh serve `saving'"'
        display as text `"  Or use:    dash serve (uses the current registry)"'
    }
    else {
        display as text `"dash: dashboard saved to `saving'"'
        // ---- open in browser ----
        if "`c(os)'" == "MacOSX"  shell open "`saving'"
        if "`c(os)'" == "Windows" shell start "`saving'"
        if "`c(os)'" == "Unix"    shell xdg-open "`saving'"
    }
end


// ================================================================
// _dash_serve  — launch Bokeh Server for live interactive mode
//               (P4-01 to P4-15)
// ================================================================
program define _dash_serve
    version 16.0

    syntax [, PORT(string) NOBROWSER TIMEOUT(string)]

    // ---- defaults ----
    if "`port'" == ""    local port    "5006"
    if "`timeout'" == "" local timeout "0"

    // ---- validate port: must be integer  (P4-03) ----
    if !regexm("`port'", "^[0-9]+$") {
        display as error "dash serve: port() must be a positive integer (got: `port')"
        exit(198)
    }
    local port_int = real("`port'")

    // ---- validate port: must be in valid range  (P4-04) ----
    if `port_int' < 1024 | `port_int' > 65535 {
        display as error "dash serve: port() must be between 1024 and 65535 (got: `port')"
        exit(198)
    }

    // ---- validate timeout  (P4-05) ----
    if !regexm("`timeout'", "^[0-9]+$") {
        display as error "dash serve: timeout() must be a non-negative integer in minutes (got: `timeout')"
        exit(198)
    }
    local timeout_int = real("`timeout'")

    // ---- require non-empty registry  (P4-06) ----
    if "${dash_graph_registry}" == "" {
        display as error "dash serve: no graphs registered. Define graphs with name() before running dash serve."
        exit(198)
    }

    // ---- determine all variables needed  (P4-07) ----
    local all_vars ""
    local registry = "${dash_graph_registry}"
    local ntok_reg : word count `registry'
    forvalues k = 1/`ntok_reg' {
        local gname : word `k' of `registry'

        if "${dash_kpi_`gname'}" != "" {
            local kpi_def = "${dash_kpi_`gname'}"
            local kpi_var = word(subinstr("`kpi_def'", ";", " ", .), 2)
            if !`: list kpi_var in all_vars' local all_vars "`all_vars' `kpi_var'"
            continue
        }

        if "${dash_json_`gname'}" != "" {
            local gvars ""
            mata: _dash_extract_vars("${dash_json_`gname'}", "gvars")
            foreach v of local gvars {
                if !`: list v in all_vars' local all_vars "`all_vars' `v'"
            }
        }
    }
    local all_vars = strtrim("`all_vars'")

    if "`all_vars'" == "" {
        display as error "dash serve: no variables identified across registered graphs."
        exit(198)
    }

    // ---- check jsonio  (P4-08) ----
    capture which jsonio
    if _rc != 0 {
        display as error "dash: jsonio is required but not found. Run dash_setup first."
        exit(198)
    }

    // ---- serialize data via jsonio  (P4-08) ----
    tempfile data_json_path master_json_path
    quietly jsonio out `all_vars', ///
        what(all) filenm("`data_json_path'") ///
        metaprint(varnames varlabels vallabs labelnames)
    if _rc != 0 {
        display as error "dash serve: jsonio failed to serialize data."
        exit(_rc)
    }

    // ---- assemble master JSON  (P4-09) ----
    local graphs_json ""
    local n_graphs = 0
    forvalues k = 1/`ntok_reg' {
        local gname : word `k' of `registry'
        if "${dash_kpi_`gname'}" != "" continue
        if `n_graphs' > 0 local graphs_json = `"`graphs_json', "'
        local graphs_json = `"`graphs_json'${dash_json_`gname'}"'
        local n_graphs = `n_graphs' + 1
    }

    local kpis_json ""
    local n_kpis = 0
    forvalues k = 1/`ntok_reg' {
        local gname : word `k' of `registry'
        if "${dash_kpi_`gname'}" == "" continue
        local kpi_def = "${dash_kpi_`gname'}"
        local kstat   = word(subinstr("`kpi_def'", ";", " ", .), 1)
        local kvar    = word(subinstr("`kpi_def'", ";", " ", .), 2)
        local kval    = word(subinstr("`kpi_def'", ";", " ", .), 3)
        local kdisp   = word(subinstr("`kpi_def'", ";", " ", .), 4)
        local kfmt    = word(subinstr("`kpi_def'", ";", " ", .), 5)
        local ktitle  = word(subinstr("`kpi_def'", ";", " ", .), 6)
        local ksub    = word(subinstr("`kpi_def'", ";", " ", .), 7)
        local kcolor  = word(subinstr("`kpi_def'", ";", " ", .), 8)
        local kbg     = word(subinstr("`kpi_def'", ";", " ", .), 9)
        local kupdate = word(subinstr("`kpi_def'", ";", " ", .), 10)
        if `n_kpis' > 0 local kpis_json = `"`kpis_json', "'
        local kpis_json = `"`kpis_json'{"name":"`gname'","stat":"`kstat'","var":"`kvar'","value":"`kval'","display":"`kdisp'","fmt":"`kfmt'","title":"`ktitle'","subtitle":"`ksub'","color":"`kcolor'","bgcolor":"`kbg'","update":"`kupdate'"}"'
        local n_kpis = `n_kpis' + 1
    }

    local master_json = `"{"graphs":[`graphs_json'],"kpis":[`kpis_json'],"build_options":{"layout":"auto","link":"","filter":"","theme":"default","title":"","subtitle":"","registry":"`registry'","mode":"server","port":"`port'"}}"'

    tempname fh
    file open `fh' using "`master_json_path'", write replace text
    file write `fh' `"`master_json'"'
    file close `fh'

    // ---- locate dash_render.py  (P4-10) ----
    local render_py "`c(sysdir_plus)'d/dash_render.py"

    // ---- generate server app .py file  (P4-10) ----
    tempfile app_py_tmp
    local app_py_path = "`app_py_tmp'.py"

    python:
import sys, runpy

sys.argv = [
    "dash_render.py",
    "--spec",   r"`master_json_path'",
    "--data",   r"`data_json_path'",
    "--output", r"`app_py_path'",
    "--mode",   "server"
]
try:
    runpy.run_path(r"`render_py'", run_name="__main__")
except SystemExit as e:
    if e.code not in (None, 0):
        from sfi import SFIToolkit
        SFIToolkit.error(int(e.code) if isinstance(e.code, int) else 198)
end

    // ---- display server info before blocking  (P4-11) ----
    display as text `"dash serve: Starting Bokeh Server on port `port'..."'
    display as text `"  Dashboard URL: http://localhost:`port'/"'
    display as text `"  Press Break to stop the server."'

    // ---- determine whether to open browser  (P4-13) ----
    local open_int = 1
    if "`nobrowser'" != "" local open_int = 0

    // ---- launch Bokeh Server  (P4-12, P4-14, P4-15) ----
    python:
import sys, runpy

# Load make_document from the generated server app file
_app_globals = runpy.run_path(r"`app_py_path'")
_make_doc = _app_globals.get("make_document")
if _make_doc is None:
    from sfi import SFIToolkit
    SFIToolkit.displayln("dash serve: make_document not found in generated app file.")
    SFIToolkit.error(198)

from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler

_port = `port_int'
_timeout_min = `timeout_int'
_open_browser = (`open_int' == 1)

_server = Server(
    {'/': Application(FunctionHandler(_make_doc))},
    port=_port,
    allow_websocket_origin=[f'localhost:{_port}'],
    num_procs=1
)
_server.start()

if _open_browser:
    _server.io_loop.add_callback(_server.show, '/')

if _timeout_min > 0:
    def _stop_server():
        _server.io_loop.stop()
    _server.io_loop.call_later(_timeout_min * 60, _stop_server)

try:
    _server.io_loop.start()
except KeyboardInterrupt:
    pass
finally:
    _server.stop()
end

    display as text "dash serve: Server stopped."
end
