*! dash.ado  v0.1.0
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
*! Architecture (0.1.0):
*!   - Every option is parsed by Stata's -syntax-.  twoway's options are
*!     declared with twoway's own minimum abbreviations, so -syntax-
*!     resolves a prefix as twoway does; nothing rewrites an option word
*!     before it.
*!   - dash_parse.mata reads, by value, what must not be parsed as Stata
*!     code -- the command line split into plot segments, user text, the
*!     immediate values of scatteri, pci and pcarrowi, qualifiers and
*!     filter() groups -- and checks what -syntax- cannot, among them the
*!     plot type, UTF-8, layout(), link(), a KPI's percentile and a
*!     saving() path.  Its header lists every function dash.ado calls.
*!   - The spec is JSON assembled in Stata by string concatenation, every
*!     text in it escaped in Mata (_dash_json_str, _dash_json_escape); the
*!     immediate values' records are written by dash_parse.mata.
*!
*! Author:  (see dash.sthlp)
*! Version: 0.1.0  18oct2026

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
// dash's Mata library.  The return code of `run' is DELIBERATELY not used
// as a verdict.  Measured:
//
//     state                       run rc    functions present
//     healthy, first load              0                  yes
//     healthy, loaded a second time 3000                  yes
//     nothing compiles              3000                   no
//     one unrelated function broken  199                  yes
//     file not found           (not run)          not by this
//
// A second load returns the SAME code as a total compile failure, so
// refusing to run on a non-zero rc would break every user -- and every
// certification script -- that loads dash_parse.mata itself before dash.ado.
// ROADMAP TR-07.4 asks for exactly that; it would be a regression.
//
// What is authoritative is whether the functions dash calls are there, and
// _dash_require_mata asks that at the entry to every command.  It is also
// the only check that sees a library cleared mid-session.
if `"`_dash_matalib'"' != "" {
    capture run "`_dash_matalib'"
}

program define dash, rclass
    // WP-30 P1.35: the Stata floor first, before `version', so an older
    // Stata is refused in dash's words; then the Mata guard, the dependency
    // guard, the prefix strip, the rclass dispatch (A154).
    _dash_require_stata
    version 19

    // Every subcommand parses through Mata, so this is the one place that
    // covers all of them.  Without it a broken or missing dash_parse.mata
    // surfaced as "<istmt>: 3499 _dash_check_utf8() not found", naming an
    // internal function and giving the user nothing to act on -- or, for a
    // partial compile, as rc 0 and "graph registered".
    _dash_require_mata

    // WP-30 P1.32: the dependency guard after the Mata guard (A154), for
    // every subcommand but clear: dash clear clears the registry with no
    // Python and prunes through a standard-library path (register P1.32.3).
    // The subcommand is read with the routing's own expression.
    mata: st_local("_dd_sub", ustrregexm(st_local("0"), "^[a-zA-Z][a-zA-Z0-9_]*") ? ustrregexs(0) : "")
    if "`_dd_sub'" != "clear" {
        _dash_require_deps
    }

    // dash replaces twoway, so twoway's own command words are not dash's:
    // `dash twoway scatter y x' is `twoway twoway scatter y x', which
    // twoway refuses, "twoway is not a twoway plot type", r(198) -- and so
    // with tw, two, twow, twowa, graph, gr, gra and grap in any case,
    // before a plot, alone or before options (measured 14oct2026).  WP-30
    // P1.27 read them off as a prefix; they are refused here, by value in
    // Mata, before any subcommand is routed (`dash twoway build' is not a
    // build either).
    mata: _dash_prefix_word()
    if "`_pf_word'" != "" {
        mata: _dash_say("err", "", st_local("_pf_word"), " is not a twoway plot type")
        exit 198
    }

    // WP-30 P1.28a, M8: dash is rclass so that, as after twoway, a command
    // leaves nothing in r() but what it means to return: r(filename), the
    // absolute path of the file a command wrote, posted by _dash_result
    // and return add at the end of each route that can write (build and
    // the plot route).  kpi, clear and serve post
    // nothing, and a refused command posts nothing, because an rclass
    // program that stops with an error leaves r() empty.  _dash_result
    // runs last: an rclass program that errors after its own return keeps
    // it (measured).

    // WP-31 H7: after a build, a serve and the plot route, _dash_py_tidy
    // pops the names they put in Python's __main__.

    // ----------------------------------------------------------------
    // Subcommand routing
    // ----------------------------------------------------------------
    // Extract the subcommand name: everything up to the first space or
    // comma.  This handles both "dash kpi ..." and "dash build, ..."
    // (where the comma immediately follows the subcommand name).
    //
    // Read by value, in Mata.  The command was put inside compound quotes
    // in regexm() and substr(), and a text holding "' -- title("'90s
    // cars"), a qualifier's literal "' or 1 or '" -- ended those quotes
    // early: `dash kpi mean(price), title("'90s price")' stopped here with
    // r(100) ") required", and nothing was registered (measured 24sep2026).
    //
    // The rest of the command is forwarded as a command line, through
    // macval().  A command line built from a macro is expanded again, so
    // text Stata had already expanded once, where the user typed it, was
    // expanded a second time: a title typed Cost in \$US was stored with the
    // global's value, and an =exp typed \`=...' to reach dash as written was
    // evaluated -- \`=filewrite(...)' wrote its file (measured 24sep2026;
    // test_json_escaping.cscript JSE-65..69 for a plot).  macval() hands
    // the text on as the subcommand's `0', as written.
    mata: st_local("_subcmd", ustrregexm(st_local("0"),                   ///
        "^[a-zA-Z][a-zA-Z0-9_]*") ? ustrregexs(0) : "")
    mata: st_local("_args", substr(st_local("0"),                         ///
        strlen(st_local("_subcmd")) + 1, .))

    if "`_subcmd'" == "kpi" {
        _dash_kpi `macval(_args)'
        exit
    }
    if "`_subcmd'" == "image" {
        _dash_image `macval(_args)'
        _dash_py_tidy
        exit
    }
    if "`_subcmd'" == "build" {
        _dash_build `macval(_args)'
        _dash_py_tidy
        _dash_result
        return add
        exit
    }
    if "`_subcmd'" == "clear" {
        _dash_clear
        exit
    }
    if "`_subcmd'" == "serve" {
        _dash_serve `macval(_args)'
        _dash_py_tidy
        exit
    }

    // ----------------------------------------------------------------
    // Plot definition  (pass full args including plot-type word)
    // ----------------------------------------------------------------
    // The caller's version, for a function layer's evaluation: graph.ado
    // sets ._Gr_Global.callerver to it before every graph, and
    // twoway__function_gen evaluates under it (_dash_fn_points; WP-29
    // P0.6).  Read here, where _caller() is the user's.
    global dash__uv = string(_caller())
    _dash_plot `macval(0)'
    _dash_py_tidy
    _dash_result
    return add
end


// ================================================================
// _dash_py_tidy  -- forget the names dash put in Python's __main__ (WP-31 H7)
// ================================================================
// Every program that reaches the renderer binds _dash_xm (and the render,
// serve and dependency check their own names) in Stata's Python __main__,
// where they stayed for the rest of the session.  The dispatcher calls this
// after a build, a serve and the plot route.  A name never set is no error
// (pop with a default), and .clear() makes the line's value None, which a
// one-line python: does not echo.  The guards run first, as before every
// python: line (test_env_guards.cscript ENV-12); by then they only confirm
// what the command already checked.
program define _dash_py_tidy
    version 19
    _dash_require_python
    _dash_require_deps
    capture python: [globals().pop(_n, None) for _n in ("_dash_saved_argv", "_dash_xm", "_dash_render_ns", "_dash_priv_argv", "_dash_dv", "_dash_serve_ns")].clear()
end


// ================================================================
// _dash_result  -- dash's r() (WP-30 P1.28a)
// ================================================================
// r(filename) is the absolute path of the file the command wrote, which
// _dash_render_immediate and _dash_build leave in the global dash__rfile
// as their last statement (through _dash_abs_path); _dash_plot and
// _dash_build drop it first.  The global is read with st_global() and
// returned through macval(): `return local filename "$dash__rfile"'
// expands a $ or a backquote in the path a second time (measured: a$b.html
// came back aZZ.html).  When Stata holds a graph in memory, one note says
// that graph export writes that graph, not the dashboard; it names the
// graphs graph dir, memory lists, not graph describe's current graph,
// which is not the one graph export writes after graph drop, graph close
// or a nodraw draw (measured).  It never draws, drops, displays or
// exports a graph.  It runs once per route, so the note prints at most
// once per command; a graph dropped but still shown in the console's
// Graph window is not in memory and gets no note.  The capture keeps a
// written page from being reported as a failure because of the note.
program define _dash_result, rclass
    version 19
    mata: st_local("_rf", st_global("dash__rfile"))
    capture macro drop dash__rfile
    if `: length local _rf' == 0 exit
    local _gn ""
    capture {
        quietly graph dir, memory
        mata: st_local("_gn", _dash_graph_names(st_global("r(list)"), 5))
    }
    if `: length local _gn' {
        mata: _dash_note("dash: graph export writes the graph in Stata's Graph window, not this dashboard; graphs in memory: ", st_local("_gn"), "")
    }
    return local filename `"`macval(_rf)'"'
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
// ================================================================
// _dash_python_ok  — is a Python set?
// ================================================================
// A pure function of its argument: whether c(python_exec) names a Python
// (`python set exec').  It decides nothing (WP-36 plat:PT-1, M8, C5): with
// none set, Stata finds a Python itself on the first python: line (help
// python), so an empty value is not a refusal.  It chooses the wording of
// _dash_python_failed only.  Nothing in dash runs Python to ask whether
// Python is there (`capture python query', `capture python: pass'); Python
// runs only for the work dash needs anyway.
//
// Syntax:
//   _dash_python_ok "<value of c(python_exec)>"   -> r(ok) 0 or 1
// ================================================================
program define _dash_python_ok, rclass
    version 19
    args probe
    local probe = strtrim(`"`probe'"')
    return scalar ok = cond(`"`probe'"' == "", 0, 1)
end


// ================================================================
// _dash_require_python  -- the entry every python: site passes
// ================================================================
// WP-36 plat:PT-1 (M8, C5): no pre-check.  An empty c(python_exec) means
// no Python is set and Stata finds one itself on the first python: line
// (help python), so nothing is refused here.  A Python that cannot start
// is reported by _dash_require_deps: Stata's own message, then dash's
// advice (_dash_python_failed).  The program stays where it stands, an
// empty hook before every python: site (test_env_guards.cscript ENV-12).
// ================================================================
program define _dash_require_python
    version 19
end


// _dash_python_failed <rc> "<c(python_exec)>"  -- Stata could not start
// the Python it was given or found (WP-36 plat:PT-1).  Stata's own message
// has been shown (capture noisily); this adds what to do, and stops with
// Stata's code (198 when the code read is 0).  Pure in its arguments, so a
// certification script reaches both wordings (Q3601-6, Q3601-7).
program define _dash_python_failed
    version 19
    args rc exe
    if "`rc'" == "" | "`rc'" == "0" local rc 198
    _dash_python_ok `"`exe'"'
    if r(ok) == 1 {
        mata: _dash_say("err", "dash: the Python linked to Stata could not be started (", st_local("exe"), ").")
    }
    else {
        display as error "dash: no Python is set, and Stata could not start one it found by itself."
    }
    if strpos(c(machine_type), "Mac") {
        mata: _dash_say("err", "      Stata reports this computer as ", c("machine_type"), "; on a Mac, Stata and Python must be built for the same processor, both arm64 (Apple Silicon) or both x86_64 (Intel).")
    }
    display as error "      Link Stata to a Python that starts here with {cmd:python set exec} ({help python}), then run {cmd:dash_setup}."
    exit `rc'
end


// ================================================================
// _dash_pyfloor  — the oldest Python dash runs under
// ================================================================
// dash_setup.ado's _dash_pymin and dash_render.py's _DASH_MIN_PYTHON hold
// the same number (a program of one ado-file cannot be called from
// another), pinned by test_version_floor.py::TestThePythonFloorIsOneNumber
// (WP-30 P1.32, register P1.32.4, A123).
//
// Syntax:
//   _dash_pyfloor   -> r(pyfloor) "<major>.<minor>"
// ================================================================
program define _dash_pyfloor, rclass
    version 19
    return local pyfloor "3.11"
end


// ================================================================
// _dash_require_deps  — refuse a Python or a package dash cannot run with
// ================================================================
// WP-30 P1.32 (GAPS2 H6, ROADMAP BR-07.1).  _dash_require_python checks only
// that a Python is configured; a missing numpy, pandas or bokeh then ended
// in a bare ModuleNotFoundError, r(7102), and an old Python in a
// SyntaxError, neither naming the remedy.  This starts the linked Python
// (a first call that sets nothing is tried once more: the first python call
// of a session can fail where Python works), reads its version and whether
// each package is installed, and refuses r(198) in words naming
// c(python_exec) and dash_setup.  It decides from the values the lines set,
// never from _rc; text from the environment is shown only through
// _dash_say.  A package that is installed but will not import is caught
// where the renderer loads (_dash_xm_load), by value.
// ================================================================
program define _dash_require_deps
    version 19
    _dash_require_python
    local _dd_v ""
    local _dd_x ""
    local _dd_prc 0
    capture python: import sys; from sfi import Macro as _dash_M; _dash_M.setLocal("_dd_v", "%d.%d.%d" % tuple(sys.version_info[:3])); _dash_M.setLocal("_dd_x", sys.executable)
    if "`_dd_v'" == "" {
        // The first python call of a session can fail where Python works
        // (test_cscript_hygiene.py's docstring): once more, and this time
        // Stata's own message is shown when it fails (WP-36 plat:PT-1).
        capture noisily python: import sys; from sfi import Macro as _dash_M; _dash_M.setLocal("_dd_v", "%d.%d.%d" % tuple(sys.version_info[:3])); _dash_M.setLocal("_dd_x", sys.executable)
        local _dd_prc = _rc
    }
    if "`_dd_v'" == "" {
        _dash_python_failed `_dd_prc' `"`c(python_exec)'"'
    }
    _dash_pyfloor
    local _dd_floor "`r(pyfloor)'"
    // The version is digits and dots only, built by %d.
    local _dd_vw = subinstr("`_dd_v'", ".", " ", .)
    local _dd_fw = subinstr("`_dd_floor'", ".", " ", .)
    local _dd_vmaj : word 1 of `_dd_vw'
    local _dd_vmin : word 2 of `_dd_vw'
    local _dd_fmaj : word 1 of `_dd_fw'
    local _dd_fmin : word 2 of `_dd_fw'
    if (`_dd_vmaj' < `_dd_fmaj') | (`_dd_vmaj' == `_dd_fmaj' & `_dd_vmin' < `_dd_fmin') {
        mata: _dash_say("err", "dash: Python " + st_local("_dd_v") + " is the Python Stata uses (", _dash_pyname(), "); dash needs Python " + st_local("_dd_floor") + " or later.")
        display as error "      Link a newer Python ({help python}), then run {cmd:dash_setup}."
        exit 198
    }
    local _dd_miss ""
    local _dd_chk ""
    // WP-31 I3: Stata's Python has "" first on sys.path, so a bokeh.py,
    // numpy.py or pandas.py in the working directory was found first; the
    // probe and the renderer's imports run without the working directory,
    // and sys.path is put back.  Captured, as every python: line here is.
    capture python: import sys, os; _dash_sp = list(sys.path); sys.path[:] = [p for p in sys.path if p not in ("", os.getcwd())]
    capture python: import sys, importlib.util; from sfi import Macro as _dash_M; _dash_M.setLocal("_dd_miss", " ".join(m for m in ("numpy", "pandas", "bokeh") if sys.modules.get(m) is None and importlib.util.find_spec(m) is None)); _dash_M.setLocal("_dd_chk", "1")
    capture python: import sys; sys.path[:] = _dash_sp
    if "`_dd_chk'" == "1" & "`_dd_miss'" != "" {
        local _dd_list = subinstr("`_dd_miss'", " ", ", ", .)
        mata: _dash_say("err", "dash: " + st_local("_dd_list") + " not installed for the Python Stata uses (", _dash_pyname(), ").")
        display as error "      Run {cmd:dash_setup} to install what is missing."
        exit 198
    }
end


// ================================================================
// _dash_stata_ok  — is a Stata release at or above a floor?
// ================================================================
// Pure, so that a certification script reaches the refusal on a Stata that
// passes: test_env_guards.cscript drives it by value and stubs it.  Both
// values are read by value in Mata (strtoreal), so text such as "19 | 1"
// is never evaluated; anything unreadable answers 0.  It is written for the
// Stata it refuses: `version 13' and nothing Stata 13 lacks
// (test_version_floor.py::TestTheStataFloor).
//
// Syntax:
//   _dash_stata_ok "<release>" "<floor>"   -> r(ok) 0 or 1, r(shown) "%9.1f"
// ================================================================
program define _dash_stata_ok, rclass
    version 13
    args have want
    mata: st_local("h", strofreal(strtoreal(st_local("have"))))
    mata: st_local("w", strofreal(strtoreal(st_local("want"))))
    local shown : display %9.1f `h'
    local shown `shown'
    return local shown "`shown'"
    return scalar ok = cond(missing(`h') | missing(`w'), 0, `h' >= `w')
end


// ================================================================
// _dash_require_stata  — refuse a Stata below dash's floor, in dash's words
// ================================================================
// The first statement of `dash', before its `version 19': without it an
// older Stata stops at that line with Stata's own "cannot run version 19.0
// programs", naming neither dash nor what it needs.  r(9) is the code Stata
// itself gives (test_wp30_truth.cscript SF-01).  dash_setup.ado's
// _dash_statamin holds the same number, because a program defined in one
// ado-file cannot be called from another; test_version_floor.py pins the
// two equal, and equal to every program's `version' line (WP-30 P1.35).
// ================================================================
program define _dash_require_stata
    version 13
    local floor 19
    _dash_stata_ok "`c(stata_version)'" "`floor'"
    if r(ok) != 1 {
        display as error "dash requires Stata `floor' or later; this is Stata `r(shown)'"
        exit 9
    }
end


// ================================================================
// _dash_require_mata  — refuse to start rather than fail on a missing function
// ================================================================
// `mata describe' of every function dash.ado calls is the witness, for a
// library never loaded, since cleared, or loaded only in part.  The return
// code of `run' is not (see the table at the top of this file): it is 3000
// for a healthy reload and for a total failure alike.  (This header said a
// "recorded load error" witnessed a partial compile; nothing records one,
// and the one-function check that followed passed a partial library --
// WP-24, test_env_guards.cscript ENV-23, test_mata_library_guard.cscript.)
// ================================================================
program define _dash_require_mata
    version 19

    // Every Mata function dash.ado calls, named once.  Checking a single
    // one would pass a library that compiled half way.  _dash_path_badchar
    // was missing, so a library without it passed and the first saving()
    // ended in r(3499) naming it (test_program_coverage.cscript PC-30);
    // test_program_coverage_map.py now fails a call this list does not name.
    local _needed _dash_check_utf8 _dash_route_axis2 _dash_comma_pos _dash_expand_plottype ///
        _dash_extract_filters _dash_extract_links _dash_extract_qual_vars _dash_extract_vars ///
        _dash_dashonly_typed _dash_dashonly_say ///
        _dash_rightmost_keep ///
        _dash_extract_hover_vars ///
        _dash_filter_refusal _dash_filter_setvars _dash_has_name_opt ///
        _dash_seg_by _dash_is_digits _dash_item_globals _dash_json_get_str _dash_json_str_args _dash_scheme_dirs_json ///
        _dash_kpi_pctile _dash_json_escape _dash_dp_format _dash_path_badchar _dash_cmd_metachar ///
        _dash_layout_cells _dash_layout_refusal _dash_link_refusal _dash_tabs_refusal _dash_tabs_unwrap ///
        _dash_legend_first_refusal _dash_bare_string_refusal ///
        _dash_axlabel_refusal ///
        _dash_option_names _dash_qual_expand _dash_qual_reset ///
        _dash_qual_rewrite _dash_qual_take _dash_qual_export _dash_qual_orders ///
        _dash_sort_reset _dash_sort_scan _dash_sort_export ///
        _dash_tsop_reset _dash_tsop_canon _dash_tsop_rewrite _dash_tsop_export _dash_tsop_meta ///
        _dash_wexp_ok _dash_wexp_reset _dash_wexp_rewrite _dash_wexp_export ///
        _dash_frame_set _dash_frame_set_all _dash_frames_reset _dash_frames_keep_add ///
        _dash_frames_keep_of _dash_frames_take _dash_frames_lset _dash_frames_cols_json ///
        _dash_filter_exclude_add _dash_link_split _dash_blank_words ///
        _dash_immediate _dash_say _dash_note _dash_colorrule_check _dash_mlabff_refusal _dash_mlabff_strip _dash_pcycle_bad _dash_opt_tokens _dash_spec_has_plots _dash_spec_types_in _dash_split_segs ///
        _dash_by_scan _dash_by_clamp ///
        _dash_text_args _dash_kernel_full ///
        _dash_unbound_cands _dash_fn_panel_count _dash_bcal_json _dash_fn_points_json _dash_fn_spec_tail _dash_fn_stray_close _dash_rep_scan ///
        _dash_fit_points_json _dash_fit_opt_bad _dash_recast_canon ///
        _dash_rep_keyof _dash_rep_reduce _dash_rep_merge_locals ///
        _dash_at_parse _dash_at_copy _dash_at_dates _dash_at_place _dash_at_orient _dash_at_canon _dash_edge_span _dash_at_records _dash_json_first_num ///
        _dash_stylelist_keys _dash_stylelist_norm _dash_stylelist_pick _dash_stylelist_bad _dash_stylelist_blank _dash_stylelist_paren _dash_stylelist_eqlead _dash_subopt_colour_comma _dash_colour_comma _dash_stylelist_probe _dash_stylelist_locals _dash_varlabel_tail ///
        _dash_connect_canon ///
        _dash_rep_und_scan _dash_rep_und_cross _dash_log_split _dash_logit_typed _dash_barwidth_typed ///
        _dash_hz_order ///
        _dash_foreign_scan _dash_kernel_clash _dash_kernel_flag _dash_zyx_abbrev _dash_rep_optname _dash_lpolyci_opts ///
        _dash_unknown_scan _dash_rep_prefix _dash_pending_note _dash_silent_drop _dash_valued_names ///
        _dash_axis_pieces _dash_axis_fmts _dash_imm_echo ///
        _dash_axreq_clear _dash_axreq_add _dash_axreq_check ///
        _dash_axisn_clear _dash_axisn_json _dash_axisn_tf_in _dash_axisn_tf_out ///
        _dash_axreq_accept_line _dash_reflines_positions ///
        _dash_axbound_list ///
        _dash_taxis_unit _dash_taxis_fmt _dash_tdate_ticks _dash_tdate_lines ///
        _dash_tdate_range _dash_xdate_find ///
        _dash_subreq_check _dash_subreq_accept _dash_so_unsafe ///
        _dash_prefix_word _dash_seg_saving _dash_play_find _dash_grec_ok _dash_saving_parse _dash_launch_quote _dash_launch_warn ///
        _dash_p_take _dash_p_seg _dash_p_unknown ///
        _dash_omit_pair _dash_maxaxes_val ///
        _dash_tw_value_msg ///
        _dash_reserved_prefix _dash_esample_sub _dash_expr_words ///
        _dash_pyname ///
        _dash_abs_path _dash_graph_names _dash_gt_ccl _dash_at_globals _dash_gt_qadded _dash_gt_qtexts _dash_at_isnum

    // Every one of them, not one.  The check asked for _dash_check_utf8
    // alone and took the library for whole when it was there, so a library
    // in memory only in part -- a copy whose compile stopped half way, or a
    // function defined by hand -- passed, and the first command died in
    // Mata with r(3499), "_dash_split_segs() not found" (measured 24sep2026;
    // test_env_guards.cscript ENV-23).  Asking for all of them costs 0.13
    // ms a command (measured, 1000 runs).
    local _missing ""
    foreach f of local _needed {
        quietly capture mata: mata describe `f'()
        if _rc != 0 local _missing `"`_missing' `f'()"'
    }
    if `"`_missing'"' == "" exit

    // Not loaded, or loaded in part.  REPAIR rather than refuse: measured,
    // the library is routinely absent at this point through no fault of the
    // install -- `clear all' drops it, `dash clear' never needed it, and
    // dash.ado's own top-level loader does not always run before the first
    // command when the file is reached through the ado-path.  A guard that
    // simply vetoed here failed test_examples_run.cscript, which runs
    // `clear all' before each of the eleven shipped examples.
    local _src ""
    capture findfile dash_parse.mata
    if _rc == 0 {
        local _src `"`r(fn)'"'
    }
    else {
        capture findfile dash.ado
        if _rc == 0 {
            local _ado `"`r(fn)'"'
            local _beside = substr(`"`_ado'"', 1, ///
                strlen(`"`_ado'"') - strlen("dash.ado")) + "dash_parse.mata"
            capture confirm file `"`_beside'"'
            if _rc == 0 local _src `"`_beside'"'
        }
    }
    if `"`_src'"' != "" {
        // A function already defined stops `run' at its definition, r(3000),
        // so over a library in memory in part the file would define nothing
        // it lacks.  What is there is dropped first -- the library's own
        // names only, every one of which is _dash_* (WP-31 H7: the last
        // four unprefixed ones were renamed, so no hand list is kept;
        // test_session_hygiene.py holds dash_parse.mata to the prefix),
        // and only when there is a file to load it back from.
        capture mata: mata drop _dash_*()
        capture run `"`_src'"'
    }

    // Only now is it a real failure.  Without this the user got
    // "<istmt>: 3499 _dash_check_utf8() not found", naming an internal
    // function, or -- when only part of the library was missing -- rc 0 and
    // "graph registered" for a command that had not run.
    local _missing ""
    foreach f of local _needed {
        quietly capture mata: mata describe `f'()
        if _rc != 0 local _missing `"`_missing' `f'()"'
    }
    if `"`_missing'"' != "" {
        display as error "dash: dash's Mata library could not be loaded."
        display as error "      Missing:`_missing'"
        // Where the file was found, the report says so: it said the library
        // "is not on the ado-path and not beside dash.ado" when it had just
        // been loaded from there (measured 24sep2026; ENV-22).  The path is
        // shown as text, _asis, never as SMCL.
        if `"`_src'"' == "" {
            display as error "      dash_parse.mata is not on the ado-path and " ///
                "not beside dash.ado."
        }
        else {
            display as error "      dash_parse.mata was found but did not load completely."
            display as error "      It is an older or damaged copy, loaded from " _asis `"`_src'"'
        }
        display as error "      Reinstall dash, or run {cmd:dash_setup}."
        exit 198
    }
end


// ================================================================
// _dash_find_render  — locate dash_render.py, once
// ================================================================
// Three programs carried their own copy of this search and the copies
// drifted: each ended with
//
//     local render_py "`c(sysdir_plus)'d/dash_render.py"
//
// which names a path that cannot exist.  Measured from a real `net install'
// into a clean PLUS, Stata files this one by EXTENSION rather than by first
// letter -- PLUS/py/dash_render.py -- while PLUS/d holds dash.ado,
// dash.sthlp, dash_parse.mata and the two dash_setup files and no .py at
// all.  The dash.ado-derived branch assumes the renderer sits beside
// dash.ado and computes the same wrong directory.
//
// Neither is reached on a healthy install: findfile DOES search the
// extension subdirectory, so candidate 1 wins for every installed user
// (measured, rc 0 -> PLUS/py/dash_render.py).  What made them worth
// removing is what happened when they WERE reached -- nothing confirmed the
// file existed, so the path went to `runpy.run_path' and the user got a
// Python FileNotFoundError naming a Stata internal directory, r(7102), and
// no message from dash.  `dash serve' announced "starting Bokeh Server ...
// Stata is blocked until the server stops" first and died after.
//
// Only the two candidates that can succeed are kept.  A candidate under
// $PLUS/py or $PERSONAL/py was considered and rejected: dash executes
// whatever this returns, `confirm file' is an existence check rather than a
// trust check, and those are trees the shipping code never ran from.
//
// Syntax:
//   _dash_find_render
//   -> r(fn), or rc 601 with a message naming what to do.
// ================================================================
program define _dash_find_render, rclass
    version 19

    capture findfile dash_render.py
    if _rc == 0 {
        return local fn `"`r(fn)'"'
        exit
    }

    // Beside dash.ado: the development layout, and any install that keeps
    // the package together.  Confirmed before it is returned, because the
    // caller hands it straight to Python.
    capture findfile dash.ado
    if _rc == 0 {
        local _ado_fn `"`r(fn)'"'
        local _beside = substr(`"`_ado_fn'"', 1, ///
            strlen(`"`_ado_fn'"') - strlen("dash.ado")) + "dash_render.py"
        capture confirm file `"`_beside'"'
        if _rc == 0 {
            return local fn `"`_beside'"'
            exit
        }
    }

    display as error "dash: cannot locate dash_render.py."
    display as error "      Not on the ado-path and not beside dash.ado."
    display as error "      Reinstall dash, or put its directory on the ado-path."
    exit 601
end


program define _dash_do_render
    version 19
    syntax, SPEC(string) DATA(string) OUTPUT(string) RENDERPY(string) ///
            [MODE(string) PRIVate]

    // The directory the page or the app goes in must exist: refused here,
    // before Python, on every route, with twoway's r(603) (JSE-52).
    _dash_saving_dir `"`output'"'

    // Before `python:', not after: a user with no linked Python used to get
    // a raw Stata Python error naming neither dash nor the remedy.
    _dash_require_python
    _dash_require_deps

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

    // The module dash keeps loaded (_dash_xm_load) runs the renderer: its
    // _dash_run_renderer is runpy.run_path(renderpy, run_name="__main__")
    // that compiles the file once a session, while its bytes are unchanged,
    // instead of on every build (0.22 s a build, measured 07oct2026; WP-30
    // test performance B1).  Each build still runs in a new __main__.
    _dash_xm_load

    // Single-line python: calls are used here instead of a python:...end block.
    // Reason: python:...end blocks inside program defines trigger an
    // IndentationError when the ado file is loaded from the adopath (Stata
    // prepends indentation to the stored block on ado-path loads).
    // Single-line python: statements do not have this issue.
    python: import sys
    // WP-31 H7: the session's argv is saved here and put back after the
    // run, before any exit -- the run line is `capture noisily', because a
    // `python:' line that errors leaves the program at once (REVIEW-4
    // R4-24) -- and the names this program puts in __main__ are popped.
    python: _dash_saved_argv = list(sys.argv)
    python: sys.argv = ["dash_render.py", "--spec", "`_py_spec'", "--data", "`_py_data'", "--output", "`_py_output'", "--mode", "`_py_mode'"]
    // private: the one-line form's preview page, written 0600 as a new
    // file and never through a link (WP-29 P0.14; main(private_output)).
    if "`private'" != "" {
        python: _dash_priv_argv = sys.argv.append("--private-output")
    }
    python: _dash_xm = sys.modules["_dash_render_export"]
    // Assign the result.  A single-line `python:' ECHOES the value of the
    // expression it evaluates, and the run returns the executed module's
    // globals dict -- so this line printed the whole of dash_render.py's
    // namespace into the Stata log on EVERY render.  Measured:
    // `dash scatter mpg weight, saving(x.html)' produced a 48 KB, 653-line
    // log, of which the dump began at line 91.  Contrary to project rule 14,
    // and it buries any message dash actually displays.
    capture noisily python: _dash_render_ns = _dash_xm._dash_run_renderer("`_py_renderpy'")
    local _rrc = _rc
    python: sys.argv = _dash_saved_argv
    python: [globals().pop(_n, None) for _n in ('_dash_render_ns', '_dash_priv_argv', '_dash_saved_argv', '_dash_xm')].clear()
    if `_rrc' exit `_rrc'
end


// ================================================================
// _dash_validate_path  — check saving() path is safe
// ================================================================
program define _dash_validate_path
    version 19
    args fpath ext

    // The expected extension, so the server branch can share every other
    // check.  It used to hardcode .html, so server mode skipped the
    // validator entirely and tested only the suffix -- a .py saving() path
    // therefore got no quote check at all.  The checks: the characters
    // _dash_path_badchar refuses (a double quote, backquote, $ and every
    // control character), a leading `-', the suffix (WP-30 P1.27, M11).
    if "`ext'" == "" local ext "html"

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
        display as error "dash: saving() path contains disallowed characters: a double quote, a backquote, $ or a control character."
        exit(198)
    }

    // `~' is not expanded by Stata, and an unexpanded one reached Python and
    // ended in r(7102) -- measured on saving("~/dashtilde.html").  Expanding
    // it is friendlier than rejecting it and is what every other tool does.
    // Only a leading `~/' is expanded: `~user/' would need a password-file
    // lookup dash has no business doing, and a `~' anywhere else in a path
    // is an ordinary character.
    // The caller reads the result back from `_dash_vpath', which this
    // program always sets.  It cannot write through the argument: the
    // arguments are VALUES, not macro names.
    if substr(`"`fpath'"', 1, 2) == "~/" {
        local _home : environment HOME
        if `"`_home'"' == "" {
            display as error "dash: saving() path starts with '~' but HOME is not set; give a full path."
            exit(198)
        }
        local fpath `"`_home'/`=substr(`"`fpath'"', 3, .)'"'
    }

    // A `..' segment is accepted (WP-30 P1.27, M11): saving() is the user's
    // own command, an absolute path was always accepted, and twoway's
    // saving() writes ../up.gph (measured).  dash serve's private app path
    // keeps its `..' check (dash_render.py's _validate_output_path).

    // A leading `-' on the file name makes the shell read the path as a
    // flag: `open -e.html' opens the argument in TextEdit rather than
    // treating it as a file.  Measured, saving("-e.html") was accepted.
    local _base `"`fpath'"'
    if regexm(`"`_base'"', "([^/\\]+)$") local _base = regexs(1)
    // The path is echoed through _dash_say, so a brace in it -- legal in a
    // file name -- is shown as written, not drawn as SMCL (P20-08).
    if substr(`"`_base'"', 1, 1) == "-" {
        display as error "dash: saving() file name may not start with '-'; the shell would read it as an option."
        mata: _dash_say("err", "      Write ./", st_local("_base"), " if that is really the name you want.")
        exit(198)
    }
    if !regexm(lower("`fpath'"), "\.`ext'$") {
        mata: _dash_say("err", "dash: saving() path must end in .`ext' (got: ", st_local("fpath"), ")")
        exit(198)
    }
    // ; & | < > are accepted (WP-30 P1.27, M11), as twoway's saving()
    // accepts them: the opener single-quotes the path on a Mac and Unix,
    // inside which nothing is special, and declines cmd's metacharacters on
    // Windows (_dash_open_page, _dash_cmd_metachar).  Parentheses were
    // never refused (every Windows path under "Program Files (x86)").
    // The quote and control loop below is defence in depth behind the scan.
    // 34 = double quote, which would terminate the quoted argument at the
    // shell call site; it was previously not checked at all.
    foreach _cnum of numlist 96 36 34 9 10 13 {
        if strpos("`fpath'", char(`_cnum')) > 0 {
            display as error "dash: saving() path contains disallowed characters: a double quote, a backquote, $ or a control character."
            exit(198)
        }
    }

    // Always set, so a caller can use it unconditionally.  It differs from
    // what was passed in only when a leading `~/' was expanded.
    c_local _dash_vpath `"`fpath'"'
end


// ================================================================
// _dash_saving_dir  -- the directory a saving() path writes into exists
// ================================================================
// dash creates no directory, and twoway creates none either: twoway
// scatter ..., saving("/nonexistent/x.gph") is r(603), "file
// /nonexistent/x.gph could not be opened".  dash handed such a path to the
// renderer, which died in Python, r(7102) FileNotFoundError, on dash
// build, dash build, server and the one-line form alike --
// saving('/abs/path/x.html) among them, whose directory is '/abs/path --
// and dash build without replace said the file "already exists" (measured
// 24sep2026; test_json_escaping.cscript JSE-52).  Refused before anything
// is rendered, with twoway's code, naming the directory.
//
// Apart from _dash_validate_path, which judges a path's text alone and is
// certified on paths of other machines (test_path_validation.cscript
// PV-07's C:/Program Files (x86)/out.html).  dash build calls this before
// it looks for the file; _dash_do_render, which every route that writes a
// page or an app passes before Python, calls it for the one-line form.
//
// The directory is the path up to its last separator: / everywhere, and \
// on Windows as well -- elsewhere a \ is a character of a file name
// (JSE-09 writes js_a\b.html).  A path with no separator is written in the
// working directory.  Read in Mata, by value, and shown as written.
//
// Usage:  _dash_saving_dir `"<path _dash_validate_path has passed>"'
// ================================================================
program define _dash_saving_dir
    version 19
    args fpath

    mata: st_local("_sd_dir", ustrregexm(st_local("fpath"), ///
        c("os") == "Windows" ? "^.*[/\\]" : "^.*/") ? ustrregexs(0) : "")
    local _sd_len : length local _sd_dir
    if `_sd_len' == 0 exit
    mata: st_local("_sd_ok", strofreal(direxists(st_local("_sd_dir"))))
    if `_sd_ok' exit
    // Named without its trailing separator.
    mata: st_local("_sd_dir", substr(st_local("_sd_dir"), 1, ///
        strlen(st_local("_sd_dir")) - 1))
    mata: _dash_say("err", "dash: file ", st_local("fpath"), " could not be opened:")
    mata: _dash_say("err", "      the directory ", st_local("_sd_dir"), ///
        " does not exist.  Create it first, or save in a directory that exists.")
    exit 603
end


// ================================================================
// _dash_saving_clobber  -- saving() names a file that is there already
// ================================================================
// Without replace an existing file is refused, "<cmd>: file '...' already
// exists. Use replace option to overwrite.", r(198): dash build's message
// and code.  The one-line form had no such check and wrote its page over
// whatever saving() named, rc 0, and took no replace (measured 24sep2026 by
// WP-24; twoway refuses, r(602)).  A directory in the file's place is never
// written: without replace it is a file that exists, as twoway and dash
// build say, and with replace it is refused as twoway refuses it,
// "is read-only; cannot be modified or erased", r(608) -- dash build handed
// it to Python and died there, r(7102) IsADirectoryError.  A symbolic link
// is the file it points to.  The path is read in Mata, by value, and shown
// as written.  Called after _dash_validate_path and _dash_saving_dir.
//
// Usage:  _dash_saving_clobber `"<path>"' "<replace or empty>" "<cmd name>"
// ================================================================
program define _dash_saving_clobber
    version 19
    args fpath replace cmdname

    mata: st_local("_sc_dir", strofreal(direxists(st_local("fpath"))))
    mata: st_local("_sc_file", strofreal(fileexists(st_local("fpath"))))
    if "`replace'" == "" {
        if `_sc_dir' | `_sc_file' {
            mata: _dash_say("err", "`cmdname': file '", st_local("fpath"), "' already exists. Use replace option to overwrite.")
            exit 198
        }
        exit
    }
    if `_sc_dir' {
        mata: _dash_say("err", "`cmdname': file ", st_local("fpath"), " is a directory; it cannot be modified or erased")
        exit 608
    }
end


// ================================================================
// _dash_json_str  -- JSON string escaping, the text read by value in Mata
// Usage:  _dash_json_str `"`raw'"' _escaped
// After: local _escaped contains the JSON-safe string (no surrounding quotes)
// ================================================================
program define _dash_json_str
    version 19

    // JSON forbids EVERY unescaped byte below 0x20 inside a string, not just
    // the three that have short forms.  This escaped backslash, quote, TAB,
    // LF and CR and left the other twenty-seven raw, so
    //     dash build, title("bad" + char(1) + "title")
    // produced invalid JSON and ended in a Python JSONDecodeError with
    // r(7102) -- measured, on both the build and the immediate route.
    //
    // Escaping rather than rejecting is deliberate: the user story asks for
    // "either a clean dash error or a correct dashboard", and a correct
    // dashboard is the better of the two.  A stray control character pasted
    // in from a web page now survives into the title intact.
    //
    // The text is read and escaped in Mata, by value (_dash_json_str_args in
    // dash_parse.mata).  It was read with -args- and escaped by subinstr()
    // calls in compound quotes, and a text holding "' -- a compound-quoted
    // title(), note() or legend label, a compound-quoted literal in a
    // qualifier -- ended those quotes early: it came back empty or cut, with
    // rc 0 (measured 23sep2026 at ad13a0f: title(`"A "B" C"') stored
    // "title":"").  The result holds no backtick, dollar sign or
    // apostrophe -- each is written as its JSON escape, backslash u 0060,
    // 0024 and 0027 -- so every spec line can expand it inside compound
    // quotes.
    mata: _dash_json_str_args()
    c_local `_dash_jsn' `"`_dash_jsv'"'
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
    version 19
    // Accept all standard graph-level options.
    // NOTE: this list and _dash_parse_plot_opts's were first written by
    // scripts/regen_option_surface.py from test/fixtures/abbrev_truth.json,
    // and have been edited by hand since.  The script no longer reproduces
    // them: run over dash.ado (measured 23sep2026, on a copy) it drops the
    // 33 declarations it never knew -- hover(), the WP-22 options, the
    // aliases -- and prepends its note again, which is how that note came
    // to stand here twice.  Do not run it; edit by hand, and
    // keep in step the other places the list appears: the plot parser's
    // syntax, the sreturn blocks, _dash_plot_opts_to_json's key list and
    // the graph-level loops in _dash_process_segment and _dash_plot.
    // Capitalised letters are the minimum abbreviation: as a rule twoway's
    // own where twoway has the option (measured, abbrev_truth.json) --
    // ASPECTratio and NAME are twoway's minimums since WP-31 A3c and A3b
    // (asp() and nam() were shorter, kept from dash's old table),
    // and MEan longer -- and dash's own choice where it has not.
    // -syntax- ends the run of capitals at a digit, so T1title's minimum is
    // t, and YTITLE2's is ytitle -- which YTitle, declared first, takes.
    // The trailing * is Stata's own catch-all: any option not declared
    // above is collected into `options' instead of aborting the user's
    // do-file.  dash.sthlp has always claimed copy-pasted twoway commands
    // still run; without this they did not.  Unmatched options are
    // reported by name, once per command -- never silently dropped.
    // Every text option is string asis, as title() is, so the quotes the
    // user typed reach the spec and the renderer reads the text as twoway's
    // textbox does.  xtitle(), ytitle(), xtitle2(), ytitle2() (and xti2(),
    // yti2()) and t1title() .. r2title() were declared string, and Stata
    // stripped the quotes before the spec was written: ytitle("line 1"
    // "line 2") was stored, and drawn, as one line where twoway draws two,
    // and xtitle(`"a "b" c"') lost the quotes around b (measured 24sep2026;
    // test_json_escaping.cscript JSE-46).
    syntax [, ///
        TItle(string asis)        SUBtitle(string asis)     NOTE(string asis) ///
        CAPtion(string asis)      NAME(string)              SAVing(string) ///
        XTitle(string asis)       YTitle(string asis)       XLabel(string asis) ///
        YLabel(string asis)       XLIne(string asis)        YLIne(string asis) ///
        LEGend(string asis)       BY(string asis)           XSCale(string asis) ///
        YSCale(string asis)       ASPECTratio(string)       SCHeme(string) ///
        PLOTRegion(string asis)   GRAPHRegion(string asis)  BGColor(string) ///
        PLOTBGCOLOR(string)       LINK(string)              FILTer(string asis) ///
        YTITLE2(string asis)      XTITLE2(string asis)      YLABEL2(string asis) ///
        XLABEL2(string asis)      YSCALE2(string asis)      XSCALE2(string asis) ///
        xmlabel2(string asis)     ymlabel2(string asis)     xmtick2(string asis) ///
        ymtick2(string asis) ///
        XSIZe(string)             YSIZe(string)             FXSIZe(string) ///
        FYSIZe(string)            SCALE(string)             TEXT(string asis) ///
        HOVer(string)             TTEXT(string asis) ///
        XTICk(string asis)        YTICk(string asis)        XMTick(string asis) ///
        YMTick(string asis)       XMLabel(string asis)      YMLabel(string asis) ///
        T1title(string asis)      T2title(string asis)      B1title(string asis) ///
        B2title(string asis)      L1title(string asis)      L2title(string asis) ///
        R1title(string asis)      R2title(string asis)      TITLE2(string) ///
        SUBTITLE2(string)         NODRAW                    PLAY(string) ///
        XOVERHANGs                YOVERHANGs                REPLACE ///
        PBGC(string)              XLA2(string asis)         XSC2(string asis) ///
        XTI2(string asis)         YLA2(string asis)         YSC2(string asis) ///
        YTI2(string asis) ///
        ytick2(string asis)       xtick2(string asis)       yline2(string asis) ///
        xline2(string asis) ///
        ZLabel(string asis)       ZTitle(string asis)       ZSCale(string asis) ///
        TLabel(string asis)       TTICk(string asis)        TMLabel(string asis) ///
        TMTick(string asis)       TSCale(string asis)       TTitle(string asis) ///
        TLIne(string asis) ///
        TLABEL2(string asis)      TTICK2(string asis)       TLINE2(string asis) ///
        TSCALE2(string asis)      TTITLE2(string asis) ///
        CLEGend(string asis)      PLEGend(string asis)      PCYCle(string) ///
        TABLE                     TABLE2(string asis) ///
        * ///
    ]
    // WP-31 H2t: table, dash's own, bare or table(rows(#) open), as one
    // value: "on" for the bare word, else the text typed (_dash_table_fold).
    _dash_table_fold `"`table'"' `"`macval(table2)'"'
    local table : copy local _tb_val

    // aspectratio(#[, placement(compassdir)]) as twoway reads it (WP-31
    // D5): the number goes on to the rules, placement() to its own key.
    local aspectplacement ""
    if `: length local aspectratio' {
        _dash_aspect_split `"`macval(aspectratio)'"'
        local aspectratio : copy local _asp_num
        local aspectplacement : copy local _asp_place
    }

    // t(), b(), l() and r() are twoway's abbreviations of t1title(),
    // b1title(), l1title() and r1title(), and T1title() .. R1title() take
    // them as they stand: a digit ends -syntax-'s run of capitals, so
    // T1title's minimum is t (measured 23sep2026; test_abbreviations.py,
    // _syntax_options).  They were once declared again here as T() B() L()
    // R() and folded in, on the belief that the minimum was t1.  Declared
    // after T1title() .. R2title(), which admit t() first, those were
    // reached only by a third t() written after t1title() and t2title(),
    // and the fold then dropped it unnamed.  That t() now reaches the note,
    // as it always did in _dash_parse_plot_opts (WP-23 TR-23.6).
    // Fold alias forms onto their real option locals.  These are
    // ALIASES, not prefixes, so Stata's truncation-based abbreviation
    // cannot express them; they are declared above and merged here.
    // twoway accepts none of them, so this is a superset and cannot
    // break drop-in parity, but it keeps existing dash do-files working.
    if `: length local pbgc' & !`: length local plotbgcolor' local plotbgcolor : copy local pbgc
    if `: length local xla2' & !`: length local xlabel2' local xlabel2 : copy local xla2
    if `: length local xsc2' & !`: length local xscale2' local xscale2 : copy local xsc2
    if `: length local xti2' & !`: length local xtitle2' local xtitle2 : copy local xti2
    if `: length local yla2' & !`: length local ylabel2' local ylabel2 : copy local yla2
    if `: length local ysc2' & !`: length local yscale2' local yscale2 : copy local ysc2
    if `: length local yti2' & !`: length local ytitle2' local ytitle2 : copy local yti2

    // Options dash accepts but does not yet honour.  Each supplied one
    // is recorded by name so it is reported rather than silently
    // dropped while the owning section is outstanding.
    //
    // This list went stale once.  Later sections implemented bin(),
    // level(), kernel(), width(), start(), n(), fraction/percent/
    // frequency, falpha(), mlcolor(), mlwidth() and -- at graph level --
    // scheme(), xsize(), ysize(), xtick() and ytick(), and nothing took
    // them off it.  So
    //     . dash scatter mpg weight, level(90)
    //     dash: ignoring unsupported option(s): level()
    // while the interval was in fact computed at 90.  A note that names
    // the wrong options is worse than no note: it tells the user to stop
    // using something that works.
    //
    // test_unsupported_report_is_true.py reads this block and renders
    // every option it names with two different values, asserting the
    // output does not change.  Implement one and forget to remove it
    // here, and that test fails.
    local _dash_pending ""
    // link() and filter() belong to `dash build' and `dash serve', where
    // the link group and the filter widgets are made.  Written on a graph
    // they were named here as not drawn; twoway refuses both, "option
    // filter() not allowed", r(198), and so does dash (WP-32,
    // _dash_tw_refuses_tab), so neither reaches this list.
    // play() is not named: _dash_play_check refuses it, as twoway refuses
    // a recording it cannot find or read (WP-32).
    // Whatever Stata could not match at all, via the trailing *.
    local _dash_unknown : copy local options

    sreturn local title        : copy local title
    sreturn local subtitle     : copy local subtitle
    sreturn local note         : copy local note
    sreturn local caption      : copy local caption
    sreturn local name         : copy local name
    sreturn local saving       : copy local saving
    sreturn local xtitle       : copy local xtitle
    sreturn local ytitle       : copy local ytitle
    sreturn local xlabel       : copy local xlabel
    sreturn local ylabel       : copy local ylabel
    sreturn local xline        : copy local xline
    sreturn local yline        : copy local yline
    sreturn local legend       : copy local legend
    sreturn local clegend      : copy local clegend
    sreturn local plegend      : copy local plegend
    sreturn local pcycle       : copy local pcycle
    sreturn local by           : copy local by
    sreturn local xscale       : copy local xscale
    sreturn local yscale       : copy local yscale
    sreturn local aspectratio  : copy local aspectratio
    sreturn local aspectplacement : copy local aspectplacement
    sreturn local xoverhangs   : copy local xoverhangs
    sreturn local yoverhangs   : copy local yoverhangs
    sreturn local scheme       : copy local scheme
    sreturn local plotregion   : copy local plotregion
    sreturn local graphregion  : copy local graphregion
    sreturn local bgcolor      : copy local bgcolor
    sreturn local plotbgcolor  : copy local plotbgcolor
    sreturn local link         : copy local link
    sreturn local filter       : copy local filter
    sreturn local ytitle2      : copy local ytitle2
    sreturn local xtitle2      : copy local xtitle2
    sreturn local ylabel2      : copy local ylabel2
    sreturn local xlabel2      : copy local xlabel2
    sreturn local xmlabel2     : copy local xmlabel2
    sreturn local ymlabel2     : copy local ymlabel2
    sreturn local xmtick2      : copy local xmtick2
    sreturn local ymtick2      : copy local ymtick2
    sreturn local yscale2      : copy local yscale2
    sreturn local xscale2      : copy local xscale2
    sreturn local ytick2       : copy local ytick2
    sreturn local xtick2       : copy local xtick2
    sreturn local yline2       : copy local yline2
    sreturn local xline2       : copy local xline2
    // WP-35 DT-15: xsize(()) refused as twoway refuses it (V2; the same
    // rule in _dash_parse_plot_opts).
    foreach _xs in xsize ysize {
        mata: st_local("_xs_e", (strpos(st_local("`_xs'"), "(") ? strtrim(stritrim(subinstr(subinstr(st_local("`_xs'"), "(", " ( ", .), ")", " ) ", .))) : ""))
        if `: length local _xs_e' {
            mata: _dash_say("err", "option(s) ", st_local("_xs_e"), " not allowed")
            exit 198
        }
    }
    sreturn local xsize        : copy local xsize
    sreturn local ysize        : copy local ysize
    sreturn local fxsize       : copy local fxsize
    sreturn local fysize       : copy local fysize
    sreturn local scale        : copy local scale
    sreturn local hover        : copy local hover
    sreturn local text         : copy local text
    sreturn local ttext        : copy local ttext
    sreturn local xtick        : copy local xtick
    sreturn local ytick        : copy local ytick
    sreturn local xmtick       : copy local xmtick
    sreturn local ymtick       : copy local ymtick
    sreturn local xmlabel      : copy local xmlabel
    sreturn local ymlabel      : copy local ymlabel
    sreturn local tlabel       : copy local tlabel
    sreturn local ttick        : copy local ttick
    sreturn local tmlabel      : copy local tmlabel
    sreturn local tmtick       : copy local tmtick
    sreturn local tscale       : copy local tscale
    sreturn local ttitle       : copy local ttitle
    sreturn local tline        : copy local tline
    sreturn local tlabel2      : copy local tlabel2
    sreturn local ttick2       : copy local ttick2
    sreturn local tline2       : copy local tline2
    sreturn local tscale2      : copy local tscale2
    sreturn local ttitle2      : copy local ttitle2
    sreturn local t1title      : copy local t1title
    sreturn local t2title      : copy local t2title
    sreturn local b1title      : copy local b1title
    sreturn local b2title      : copy local b2title
    sreturn local l1title      : copy local l1title
    sreturn local l2title      : copy local l2title
    sreturn local r1title      : copy local r1title
    sreturn local r2title      : copy local r2title
    sreturn local title2       : copy local title2
    sreturn local subtitle2    : copy local subtitle2
    sreturn local zlabel       : copy local zlabel
    sreturn local ztitle       : copy local ztitle
    sreturn local zscale       : copy local zscale
    sreturn local nodraw       : copy local nodraw
    sreturn local play         : copy local play
    sreturn local replace      : copy local replace
    sreturn local table        : copy local table
    sreturn local _pending  : copy local _dash_pending
    sreturn local _unknown  : copy local _dash_unknown
end


// _dash_aspect_split text -- aspectratio(#[, placement(compassdir)]) as
// twoway reads it (WP-31 D5; test/fixtures/sizing_truth.json): the number
// before the comma in the caller's local _asp_num, and placement() as its
// compass direction in _asp_place, "" when it is not given.  Locals, not
// s(): the parser's s() is what _dash_opts_repeats keys a copy by.
// Measured: aspectratio(1, foo) is "option foo not allowed", r(198)
// (syntax's own words, as twoway's), and an unknown placement() name is a
// note, drawn centred (aspect_bad_place).
program define _dash_aspect_split
    version 19
    args text
    local num : copy local text
    local place ""
    local cpos = strpos(`"`macval(text)'"', ",")
    if `cpos' {
        local num = substr(`"`macval(text)'"', 1, `cpos' - 1)
        local 0 = substr(`"`macval(text)'"', `cpos', .)
        syntax [, PLACEment(string)]
        if `: length local placement' {
            mata: st_local("place", _dash_at_place(strtrim(st_local("placement"))))
            if "`place'" == "" {
                mata: _dash_note("named style ", st_local("placement"), " not found in class compass2dir, default attributes used")
            }
        }
    }
    c_local _asp_num = strtrim(`"`macval(num)'"')
    c_local _asp_place `"`place'"'
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
    version 19
    // NOTE: edited by hand, like _dash_parse_graph_opts's list; the NOTE
    // there says why scripts/regen_option_surface.py must not be run over
    // it, and how the capitalised minimums are chosen.
    // The trailing * is Stata's own catch-all: any option not declared
    // above is collected into `options' instead of aborting the user's
    // do-file.  dash.sthlp has always claimed copy-pasted twoway commands
    // still run; without this they did not.  Unmatched options are
    // reported by name, once per command -- never silently dropped.
    // WP-22 TR-22.3 declared the twoway options GAPS.md F3 found in the
    // note as UNKNOWN, with twoway's own minimum abbreviations: CLColor,
    // CLPattern, CLWidth, MLABANGle, MLABFormat, MLABTextstyle and
    // MLABVposition are twoway_yxview_parse.class's declarations, and
    // SORT SORT1() is the pair -syntax- (and that class file) uses for an
    // option written bare, sort, or with an argument, sort(varlist).
    // XVARFormat() and YVARFormat() (WP-30 P1.5): twoway reads a layer's
    // x/yvarformat(); the minimum is xvarf (measured 03oct2026: xvar() and
    // xva() are refused, xvarf() and xvarfo() read).
    // XOVERHANGs and YOVERHANGs are advanced_options.sthlp's xoverhangs and
    // yoverhangs; twoway's measured minimum is xoverhang and yoverhang.
    // The text options are string asis, as in _dash_parse_graph_opts (see
    // the note there on xtitle(), ytitle() and t1title() .. r2title()).
    // log and nolog are twoway's graph option logging, on lowess too, where
    // -syntax- would bind them to LOgit: taken out here, by value, and
    // handed to the catch-all as typed below (_dash_log_split).  dash read
    // lowess mpg weight, log as logit, a different curve, and refused
    // scatter mpg weight, log, where twoway draws both as if log were not
    // there (BUGS.md, S1).
    mata: _dash_log_split("0", "_dash_logw")
    // WP-31 B4b: contour's and contourline's options, read first by
    // _dash_contour_split (the syntax below holds as many options as
    // -syntax- takes); the rest goes on, as typed, to it.
    mata: _dash_zyx_text = st_local("0")
    _dash_contour_split
    // WP-31 S34: yvarlabel(), xvarlabel() and the other options the
    // syntax below has no room for, read the same way (_dash_label_split).
    _dash_label_split
    // WP-31 H2t: table, read by _dash_label_split, folded to one value.
    _dash_table_fold `"`table'"' `"`macval(table2)'"'
    local table : copy local _tb_val
    mata: st_local("0", ", " + _dash_zyx_text)
    syntax [, ///
        MColor(string asis)       Msymbol(string asis)      MSIze(string asis) ///
        MSAngle(string asis)      MFColor(string asis)      MLColor(string asis) ///
        MLabel(string asis)       MLALign(string)           MLABColor(string asis) ///
        MLABSize(string asis) ///
        MLABPosition(string asis) MLABGap(string asis)      MLABWidth(string) ///
        MALpha(string)            MARKER(string)            LColor(string asis) ///
        LWidth(string asis)       LPattern(string asis)     LALPha(string) ///
        FColor(string asis)       FIntensity(string asis)   FAlpha(string) ///
        AColor(string asis)       ALColor(string asis)      ALWidth(string asis) ///
        ALPattern(string asis) ///
        BARWidth(string asis)     BASE(string asis)         BLColor(string asis) ///
        BFColor(string asis)      JITTER(string asis)       JSEed(string) ///
        YAXis(string)             XAXis(string)             COLORVar(string) ///
        COLPALette(string)        COLORDIScrete             COLORUSEPLEGend ///
        COLORNlevels(string)      COLORCUTs(string asis)    COLORMissing(string) ///
        COLORLEVels(string)       COLORVARMINMax ///
        COLORSTart(string)        COLOREnd(string)          COLORRule(string) ///
        COLORFILLONLY             COLORFORMISSing(string)   COLORKEYSRANge ///
        COLORKEYSREVerse          COLORALLOWMULTIPLE        COLOROTHERLABel(string) ///
        CLEGend(string asis)      PLEGend(string asis)      PCYCle(string) ///
        BWIdth(string)            DEGree(string)            PSTYle(string asis) ///
        CMISSing(string asis)     RECAST(string)            Connect(string asis) ///
        CMISSINGS(string asis)    RECASTAs(string)          TYpe(string) ///
        BIN(string)               BINS(string)              Width(string) ///
        START(string) ///
        GAP(string)               BAROFFset(string)         AREA(string) ///
        BOUNDARY                  DROPlines(string)         noDROPBase ///
        DISCrete                  STDP                      STDF ///
        STDR                      MEan                      NOWeight ///
        ATObs ESTopts(string asis) PREDopts(string asis) ESTCmd(string asis) ///
        FITPlot(string) CIPlot(string) SMOOTHPlot(string) noFIT ///
        Adjust                    LOgit ///
        PERCENT                   FREQuency                 DENsity ///
        FRACtion                  Kernel(string)            N(string) ///
        LEvel(string)             BAnds(string)             AT(string asis) ///
        CIOPTS(string asis)       LINEOPTS(string asis)     FITOPTS(string asis) ///
        COLor(string asis)        MLWidth(string asis)      MSTyle(string asis) ///
        LStyle(string asis)       MLStyle(string asis)      MLPattern(string asis) ///
        ASTyle(string asis) ALstyle(string asis) BSTyle(string asis) BLstyle(string asis) CLStyle(string asis) P(string) ///
        DSTyle(string asis)       DLstyle(string asis)      BMLinestyle(string asis) ///
        DOTEXtend(string) NDOTs(string) Dsymbol(string asis) DColor(string asis) ///
        DFColor(string asis) DSIze(string asis) DLColor(string asis) ///
        DLWidth(string asis) DLAlign(string asis) ///
        BLABEL(string)            HORizontal                VERTical ///
        SORT                      RAnge(string asis)        COLORLIst(string asis) ///
        SORT1(string)             CLColor(string asis)      CLPattern(string asis) ///
        CLWidth(string asis)      MLABANGle(string asis)    MLABFormat(string asis) ///
        MLABTextstyle(string asis) MLABVposition(string)    XOVERHANGs ///
        YOVERHANGs ///
        XVARFormat(string)        YVARFormat(string) ///
        JITTERSEED(string)        TItle(string asis)        SUBtitle(string asis) ///
        NOTE(string asis)         CAPtion(string asis)      NAME(string) ///
        SAVing(string)            XTitle(string asis)       YTitle(string asis) ///
        XLabel(string asis)       YLabel(string asis)       XLIne(string asis) ///
        YLIne(string asis)        LEGend(string asis)       BY(string asis) ///
        XSCale(string asis)       YSCale(string asis)       ASPECTratio(string) ///
        SCHeme(string)            PLOTRegion(string asis)   GRAPHRegion(string asis) ///
        BGColor(string)           PLOTBGCOLOR(string)       LINK(string) ///
        FILTer(string asis)       YTITLE2(string asis)      XTITLE2(string asis) ///
        YLABEL2(string asis)      XLABEL2(string asis)      YSCALE2(string asis) ///
        xmlabel2(string asis)     ymlabel2(string asis)     xmtick2(string asis) ///
        ymtick2(string asis) ///
        XSCALE2(string asis)      XSIZe(string)             YSIZe(string) ///
        FXSIZe(string)            FYSIZe(string)            SCALE(string) ///
        TEXT(string asis)         XTICk(string asis)        YTICk(string asis) ///
        HOVer(string)             TTEXT(string asis) ///
        XMTick(string asis)       YMTick(string asis)       XMLabel(string asis) ///
        YMLabel(string asis)      T1title(string asis)      T2title(string asis) ///
        B1title(string asis)      B2title(string asis)      L1title(string asis) ///
        L2title(string asis)      R1title(string asis)      R2title(string asis) ///
        TITLE2(string)            SUBTITLE2(string)         NODRAW ///
        PLAY(string)              REPLACE ///
        BW(string)               MLG(string)               CV(string) ///
        COLV(string)              PBGC(string)              XLA2(string asis) ///
        XSC2(string asis)         XTI2(string asis)         YLA2(string asis) ///
        YSC2(string asis)         YTI2(string asis) ///
        ytick2(string asis)       xtick2(string asis)       yline2(string asis) ///
        xline2(string asis) ///
        ZLabel(string asis)       ZTitle(string asis)       ZSCale(string asis) ///
        TLabel(string asis)       TTICk(string asis)        TMLabel(string asis) ///
        TMTick(string asis)       TSCale(string asis)       TTitle(string asis) ///
        TLIne(string asis) ///
        TLABEL2(string asis)      TTICK2(string asis)       TLINE2(string asis) ///
        TSCALE2(string asis)      TTITLE2(string asis) ///
        MANGle(string) BARBSize(string) HEADlabel ///
        MWidth ///
        * ///
    ]
    // The style options of _dash_stylelist_keys() are string asis so a
    // stylelist keeps its quoted elements whole (WP-30 P1.1a): string took
    // the quotes off, and mcolor("255 0 0" "0 0 255") became one colour.
    // A value of only empty quotes, mcolor(""), is no value, as string made
    // it; every emptiness test below, the folds, _dash_validate_opts and
    // the JSON writer read the value normalised here.
    mata: st_local("_dash_slk", _dash_stylelist_keys())
    foreach _dash_slo of local _dash_slk {
        mata: st_local(st_local("_dash_slo"), _dash_stylelist_norm(st_local(st_local("_dash_slo"))))
    }
    // cmissings() is twoway's own spelling of cmissing() (WP-30 P1.8a): a
    // copy of it is a copy of cmissing(), the rightmost copy read
    // (_dash_opts_repeats keys both as cmissing).
    if `"`macval(cmissings)'"' != "" mata: st_local("cmissing", _dash_stylelist_norm(st_local("cmissings")))
    // aspectratio(#[, placement(compassdir)]) as twoway reads it (WP-31
    // D5): the number goes on to the rules, placement() to its own key.
    local aspectplacement ""
    if `: length local aspectratio' {
        _dash_aspect_split `"`macval(aspectratio)'"'
        local aspectratio : copy local _asp_num
        local aspectplacement : copy local _asp_place
    }
    /* ---- plot-level ---- */

    // t(), b(), l() and r() need no fold: T1title() .. R1title() take them
    // as their own minimum abbreviations (see _dash_parse_graph_opts).
    // bins() is twoway histogram's own name for the bin count --
    // twoway_histogram_parse.class declares BINs(), and bins(5) draws what
    // bin(5) draws (measured 23sep2026) -- where dash declared only bin().
    // b() is not a third spelling of it: twoway reads b(5) as b1title(5),
    // on histogram as everywhere else (measured: the default eight bars,
    // under a bottom title "5"), and so does dash.
    if `: length local bins' & !`: length local bin' local bin : copy local bins

    // kernel(gau) is twoway's kernel(gaussian): each name is taken down to
    // twoway's minimum abbreviation (_dash_kernel_full, measured on lpoly,
    // lpolyci and kdensity), and written out in full before the enum rule
    // judges it and the renderer reads it.  It was refused, r(198).  Read
    // by value, in Mata.
    if `: length local kernel' {
        // WP-35 DT-15: twoway reads a kernel's name in lower case only:
        // kernel(GAUSSIAN) is "invalid kernel function", r(198)
        // (dash_only_words_truth.json V1; DECISIONS.md P4-7, P4-9).
        mata: st_local("_kn_uc", strofreal(ustrregexm(st_local("kernel"), "[A-Z]") & anyof(("epanechnikov", "epan2", "biweight", "cosine", "gaussian", "parzen", "rectangle", "triangle"), _dash_kernel_full(ustrlower(st_local("kernel"))))))
        if `_kn_uc' {
            display as error "invalid kernel function"
            mata: _dash_say("err", "      use kernel(", ustrlower(strtrim(st_local("kernel"))), ")")
            exit 198
        }
        mata: st_local("kernel", _dash_kernel_full(st_local("kernel")))
    }
    // WP-35 DT-15: xsize() or ysize() holding a parenthesis is refused as
    // twoway refuses it, its value written with a blank around each
    // parenthesis: xsize(()) is "option(s) ( ) not allowed", xsize((5))
    // "option(s) ( 5 ) not allowed", r(198) (dash_only_words_truth.json
    // V2; DECISIONS.md P4-7).  Read by value.
    foreach _xs in xsize ysize {
        mata: st_local("_xs_e", (strpos(st_local("`_xs'"), "(") ? strtrim(stritrim(subinstr(subinstr(st_local("`_xs'"), "(", " ( ", .), ")", " ) ", .))) : ""))
        if `: length local _xs_e' {
            mata: _dash_say("err", "option(s) ", st_local("_xs_e"), " not allowed")
            exit 198
        }
    }

    // level() is no longer checked here: its rule (level=num,0,100,x) lives
    // in _dash_option_rules and runs in _dash_validate_opts, once per segment.

    // bw() is NOT folded here: what it means depends on the plot type,
    // which this parser does not know.  twoway reads bw() as bwidth() on
    // the bandwidth types and rejects it everywhere else; _dash_fold_bw,
    // called by _dash_process_segment once the type is known, resolves
    // it.  It used to become barwidth() on every type, so
    // `dash (lpoly mpg weight, bw(400))' drew the rule-of-thumb bandwidth
    // and said nothing.
    // Fold alias forms onto their real option locals.  These are
    // ALIASES, not prefixes, so Stata's truncation-based abbreviation
    // cannot express them; they are declared above and merged here.
    // twoway accepts none of them, so this is a superset and cannot
    // break drop-in parity, but it keeps existing dash do-files working.
    if `: length local mlg' & !`: length local mlabgap' local mlabgap : copy local mlg
    if `: length local cv' & !`: length local colorvar' local colorvar : copy local cv
    if `: length local colv' & !`: length local colorvar' local colorvar : copy local colv
    if `: length local pbgc' & !`: length local plotbgcolor' local plotbgcolor : copy local pbgc
    if `: length local xla2' & !`: length local xlabel2' local xlabel2 : copy local xla2
    if `: length local xsc2' & !`: length local xscale2' local xscale2 : copy local xsc2
    if `: length local xti2' & !`: length local xtitle2' local xtitle2 : copy local xti2
    if `: length local yla2' & !`: length local ylabel2' local ylabel2 : copy local yla2
    if `: length local ysc2' & !`: length local yscale2' local yscale2 : copy local ysc2
    if `: length local yti2' & !`: length local ytitle2' local ytitle2 : copy local yti2
    // colorformissing() is twoway's name for the colour of missing values,
    // dash's colormissing() (WP-31 C8b).  twoway has the one option and
    // refuses colormissing() (colorvar_options_truth.json R04); given
    // both, colorformissing() is read.
    if `"`macval(colorformissing)'"' != "" local colormissing : copy local colorformissing
    // colorvar(i.var) is colorvar(var) colordiscrete coloruseplegend
    // (twoway_yxview_parse.class:213-218), read by value.  On a type
    // twoway does not colour, _dash_cv_drop empties all three.
    mata: st_local("_cv_iv", strofreal(anyof(("i.", "I."), substr(strtrim(st_local("colorvar")), 1, 2))))
    if `_cv_iv' {
        mata: st_local("colorvar", substr(strtrim(st_local("colorvar")), 3, .))
        local colordiscrete colordiscrete
        local coloruseplegend coloruseplegend
    }

    // Options dash accepts but does not yet honour.  Each supplied one
    // is recorded by name so it is reported rather than silently
    // dropped while the owning section is outstanding.
    //
    // This list went stale once.  Later sections implemented bin(),
    // level(), kernel(), width(), start(), n(), fraction/percent/
    // frequency, falpha(), mlcolor(), mlwidth() and -- at graph level --
    // scheme(), xsize(), ysize(), xtick() and ytick(), and nothing took
    // them off it.  So
    //     . dash scatter mpg weight, level(90)
    //     dash: ignoring unsupported option(s): level()
    // while the interval was in fact computed at 90.  A note that names
    // the wrong options is worse than no note: it tells the user to stop
    // using something that works.
    //
    // test_unsupported_report_is_true.py reads this block and renders
    // every option it names with two different values, asserting the
    // output does not change.  Implement one and forget to remove it
    // here, and that test fails.
    local _dash_pending ""
    // at(), blabel(), ciopts(), filter(), fitopts(), link(), lineopts()
    // and mlabwidth() were named here as not drawn; twoway refuses each on
    // every type, "option at() not allowed", r(198), and so does dash, in
    // the list's order (WP-32, _dash_tw_refuses_tab), so none reaches this
    // list.
    // WP-31 A4: mlalign(), twoway's mlal() .. mlalign() (mla() is mlabel(),
    // as in twoway).  WP-31 E3: read by the renderer, which names only
    // what it cannot draw (outside, or a word that is no alignment).
    // WP-30 P1.14b: bmlinestyle() styles a marker's back line (P2.8);
    // dash does not draw it, so it is kept in the spec and named here.
    // WP-31 B5b: dstyle(), dlstyle() and the other d-options are drawn on
    // dot's rows of dots; twoway accepts them on every type and draws
    // nothing else with them (test/fixtures/dot_truth.json D11k, D11n-t),
    // so elsewhere they are silent.
    if `: length local bmlinestyle' local _dash_pending `"`_dash_pending' bmlinestyle"'
    // WP-31 B5b: dlalign() is accepted and named: a stroke cannot be
    // aligned in Bokeh (as mlalign()).
    if `: length local dlalign' local _dash_pending `"`_dash_pending' dlalign"'
    // play() is not named: _dash_play_check refuses it, as twoway refuses
    // a recording it cannot find or read (WP-32).
    // fitarea_options, the look of a ci fit's band: twoway takes ac(),
    // alc(), alw() and alp() (measured 24sep2026; al() is alstyle()).
    // Drawn on lfitci, qfitci, lpolyci and fpfitci (pstyle() and the other
    // named styles are drawn on every type, WP-30 P1.14a) -- where
    // _dash_fold_typed takes them off this list once the
    // type is known; twoway accepts them on every type (rc 0), so
    // elsewhere they are named here.
    if `: length local acolor' local _dash_pending `"`_dash_pending' acolor"'
    if `: length local alcolor' local _dash_pending `"`_dash_pending' alcolor"'
    if `: length local alwidth' local _dash_pending `"`_dash_pending' alwidth"'
    if `: length local alpattern' local _dash_pending `"`_dash_pending' alpattern"'
    // sort(varlist) arrives in `sort1', -syntax-'s name for it, and is
    // returned in s(sort1); it is named here as sort().  _dash_sort_opt
    // checks it as twoway does once the repeats are reduced, honours it
    // on line, connected, area, rline, rarea and rconnected and is silent
    // on tsline and tsrline, taking sort off this list there (WP-29
    // P0.1); on every other type it stays named.
    if `: length local sort1' local _dash_pending `"`_dash_pending' sort"'
    // WP-31 B4b: contour's heatmap drawing and its band outlines.
    // WP-32: heatmap and outlines are drawn on contour as twoway draws
    // them (map_contour's _contour_parts) and change nothing on
    // contourline: not named.
    // scheme(), xsize(), ysize(), xtick() and ytick() are NOT listed.  They
    // are twoway GRAPH-level options, and this program promotes them --
    // `sreturn local g_xsize' and friends just above, picked up by the
    // promotion loop in _dash_process_segment -- so however they are
    // written they reach the renderer and are honoured.  Naming them here
    // told a user who typed dash.sthlp's own example,
    //     dash scatter mpg weight, xsize(10) ysize(2)
    // that dash had ignored two options it had just applied.
    // Whatever Stata could not match at all, via the trailing *, and the
    // log and nolog taken out before -syntax- ran.
    if `: length local _dash_logw' {
        mata: st_local("options", strtrim(st_local("options") + " " + st_local("_dash_logw")))
    }
    local _dash_unknown : copy local options

    sreturn local mcolor           : copy local mcolor
    sreturn local msymbol          : copy local msymbol
    sreturn local msize            : copy local msize
    // WP-31 C1: the arrowhead's half-angle, barb depth and label place,
    // drawn on pcarrow, pcbarrow and pcarrowi (_dash_fold_typed names them
    // on every other type).
    sreturn local mangle           : copy local mangle
    sreturn local barbsize         : copy local barbsize
    sreturn local headlabel        : copy local headlabel
    sreturn local mwidth           : copy local mwidth
    sreturn local msangle          : copy local msangle
    sreturn local mfcolor          : copy local mfcolor
    sreturn local mlcolor          : copy local mlcolor
    sreturn local mlabel           : copy local mlabel
    sreturn local mlabcolor        : copy local mlabcolor
    sreturn local mlabsize         : copy local mlabsize
    sreturn local mlabposition     : copy local mlabposition
    sreturn local mlabgap          : copy local mlabgap
    sreturn local mlabwidth        : copy local mlabwidth
    sreturn local mlalign          : copy local mlalign
    sreturn local malpha           : copy local malpha
    sreturn local marker           : copy local marker
    sreturn local lcolor           : copy local lcolor
    sreturn local lwidth           : copy local lwidth
    sreturn local lpattern         : copy local lpattern
    sreturn local lalpha           : copy local lalpha
    sreturn local fcolor           : copy local fcolor
    sreturn local fintensity       : copy local fintensity
    sreturn local falpha           : copy local falpha
    sreturn local acolor           : copy local acolor
    sreturn local alcolor          : copy local alcolor
    sreturn local alwidth          : copy local alwidth
    sreturn local alpattern        : copy local alpattern
    sreturn local barwidth         : copy local barwidth
    sreturn local base             : copy local base
    sreturn local blcolor          : copy local blcolor
    sreturn local bfcolor          : copy local bfcolor
    sreturn local jitter           : copy local jitter
    sreturn local jseed            : copy local jseed
    sreturn local yaxis            : copy local yaxis
    sreturn local xaxis            : copy local xaxis
    sreturn local colorvar         : copy local colorvar
    sreturn local colpalette       : copy local colpalette
    sreturn local colordiscrete    : copy local colordiscrete
    sreturn local coloruseplegend  : copy local coloruseplegend
    sreturn local colornlevels     : copy local colornlevels
    sreturn local colorcuts        : copy local colorcuts
    sreturn local colormissing     : copy local colormissing
    sreturn local colorlevels      : copy local colorlevels
    sreturn local colorvarminmax   : copy local colorvarminmax
    sreturn local colorstart       : copy local colorstart
    sreturn local colorend         : copy local colorend
    sreturn local colorrule        : copy local colorrule
    sreturn local colorfillonly    : copy local colorfillonly
    sreturn local colorkeysrange   : copy local colorkeysrange
    sreturn local colorkeysreverse : copy local colorkeysreverse
    sreturn local colorallowmultiple : copy local colorallowmultiple
    sreturn local colorotherlabel  : copy local colorotherlabel
    sreturn local bwidth           : copy local bwidth
    sreturn local bw               : copy local bw
    sreturn local degree           : copy local degree
    sreturn local pstyle           : copy local pstyle
    sreturn local cmissing         : copy local cmissing
    // recast() and recastas() are one option to twoway: the rightmost
    // wins; type() is their synonym, read by _dash_recast_opt (P1.8b).
    if `: length local recastas' {
        local _rca_last 1
        if `: length local recast' mata: st_local("_rca_last", strofreal(max((strrpos(st_local("0"), "recasta("), strrpos(st_local("0"), "recastas("))) > strrpos(st_local("0"), "recast(")))
        if `_rca_last' local recast : copy local recastas
    }
    sreturn local recast           : copy local recast
    sreturn local type             : copy local type
    sreturn local connect          : copy local connect
    sreturn local bin              : copy local bin
    sreturn local width            : copy local width
    sreturn local start            : copy local start
    // WP-31 C5: histogram gap() and baroffset(), bar baroffset(),
    // kdensity area() and boundary, function droplines(), area
    // nodropbase (syntax's noDROPBase: local dropbase holds "nodropbase").
    // WP-31 B4b: contour's and contourline's options (zyx2view_parse).
    sreturn local ccuts            : copy local ccuts
    sreturn local levels           : copy local levels
    sreturn local minmax           : copy local minmax
    sreturn local crule            : copy local crule
    sreturn local scolor           : copy local scolor
    sreturn local ecolor           : copy local ecolor
    sreturn local ccolors          : copy local ccolors
    sreturn local clabels          : copy local clabels
    sreturn local format           : copy local format
    sreturn local interp           : copy local interp
    sreturn local clwidths         : copy local clwidths
    sreturn local clpatterns       : copy local clpatterns
    sreturn local reversekey       : copy local reversekey
    sreturn local _heatmap         : copy local heatmap
    sreturn local _outlines        : copy local outlines
    sreturn local colorlines       : copy local colorlines
    sreturn local _le_typed        : copy local _dash_le_typed
    sreturn local gap              : copy local gap
    sreturn local baroffset        : copy local baroffset
    sreturn local area             : copy local area
    sreturn local boundary         : copy local boundary
    sreturn local droplines        : copy local droplines
    sreturn local nodropbase       : copy local dropbase
    sreturn local percent          : copy local percent
    sreturn local frequency        : copy local frequency
    sreturn local density          : copy local density
    sreturn local fraction         : copy local fraction
    sreturn local kernel           : copy local kernel
    sreturn local n                : copy local n
    sreturn local level            : copy local level
    sreturn local bands            : copy local bands
    sreturn local at               : copy local at
    sreturn local ciopts           : copy local ciopts
    sreturn local lineopts         : copy local lineopts
    sreturn local fitopts          : copy local fitopts
    sreturn local color            : copy local color
    sreturn local mlwidth          : copy local mlwidth
    sreturn local mstyle           : copy local mstyle
    sreturn local lstyle           : copy local lstyle
    sreturn local mlstyle          : copy local mlstyle
    // WP-30 P1.14a: the named styles twoway reads (p1-p15 drawn), and p(),
    // twoway's whole-plot style.
    sreturn local astyle           : copy local astyle
    sreturn local alstyle          : copy local alstyle
    sreturn local bstyle           : copy local bstyle
    sreturn local blstyle          : copy local blstyle
    // WP-30 P1.14b: kept and named, not drawn (P2.9, P2.8).
    sreturn local dstyle           : copy local dstyle
    sreturn local dlstyle          : copy local dlstyle
    sreturn local bmlinestyle      : copy local bmlinestyle
    sreturn local dotextend        : copy local dotextend
    sreturn local ndots            : copy local ndots
    sreturn local dsymbol          : copy local dsymbol
    sreturn local dcolor           : copy local dcolor
    sreturn local dfcolor          : copy local dfcolor
    sreturn local dsize            : copy local dsize
    sreturn local dlcolor          : copy local dlcolor
    sreturn local dlwidth          : copy local dlwidth
    sreturn local dlalign          : copy local dlalign
    sreturn local clstyle          : copy local clstyle
    sreturn local p                : copy local p
    sreturn local mlpattern        : copy local mlpattern
    sreturn local blabel           : copy local blabel
    sreturn local horizontal       : copy local horizontal
    sreturn local vertical         : copy local vertical
    sreturn local sort             : copy local sort
    sreturn local sort1            : copy local sort1
    sreturn local range            : copy local range
    sreturn local colorlist        : copy local colorlist
    sreturn local jitterseed       : copy local jitterseed
    // WP-22: the honoured F3 options.  The connecting-line triple is kept
    // or dropped by plot type in _dash_fold_cl, once the type is known.
    sreturn local clcolor          : copy local clcolor
    sreturn local clpattern        : copy local clpattern
    sreturn local clwidth          : copy local clwidth
    sreturn local mlabangle        : copy local mlabangle
    sreturn local mlabformat       : copy local mlabformat
    // WP-30 P1.24: one variable of clock positions, read row by row
    // (_dash_fold_mlabv checks it as twoway does).
    sreturn local mlabvposition    : copy local mlabvposition
    // WP-30 P1.24: a text box style per y, a style list (S11).
    sreturn local mlabtextstyle    : copy local mlabtextstyle
    sreturn local xvarformat       : copy local xvarformat
    sreturn local yvarlabel        : copy local yvarlabel
    sreturn local mlabprefix       : copy local mlabprefix
    sreturn local mlabsuffix       : copy local mlabsuffix
    sreturn local lalign           : copy local lalign
    sreturn local mlabstyle        : copy local mlabstyle
    sreturn local subchar          : copy local subchar
    sreturn local xvarlabel        : copy local xvarlabel
    sreturn local yvarformat       : copy local yvarformat
    // The seven statistical sub-options (WP-18): declared with twoway's own
    // minimum abbreviations (twoway_histogram_parse.class DISCrete;
    // twoway_lfitci_parse.class STDP STDF STDR, none abbreviable;
    // twoway_lowess_parse.class Mean noWeight Adjust LOgit).  MEan is
    // declared one letter longer than twoway's `m': this parser also
    // declares Msymbol(), and test_abbreviations.py refuses a prefix two
    // options could claim.  Which type each belongs to is enforced by the
    // flag rules in _dash_option_rules, not here.
    sreturn local discrete         : copy local discrete
    sreturn local stdp             : copy local stdp
    sreturn local stdf             : copy local stdf
    sreturn local stdr             : copy local stdr
    sreturn local mean             : copy local mean
    sreturn local noweight         : copy local noweight
    sreturn local adjust           : copy local adjust
    sreturn local logit            : copy local logit
    // WP-31 C4: twoway's fit options (twoway_lfit_parse.class ATObs
    // ESTopts() PREDopts(); twoway_fpfit_parse.class ESTCmd();
    // twoway_lfitci_parse.class FITPlot() CIPlot() noFIT;
    // twoway_lpolyci_parse.class SMOOTHPlot()), each with twoway's
    // minimum.  Which type takes each is _dash_fit_opts_check's.
    sreturn local atobs            : copy local atobs
    sreturn local estopts          : copy local estopts
    sreturn local predopts         : copy local predopts
    sreturn local estcmd           : copy local estcmd
    sreturn local fitplot          : copy local fitplot
    sreturn local ciplot           : copy local ciplot
    sreturn local smoothplot       : copy local smoothplot
    sreturn local nofit            : copy local fit
    /* ---- graph-level (returned separately so _dash_plot can accumulate them) ---- */
    sreturn local g_title        : copy local title
    sreturn local g_subtitle     : copy local subtitle
    sreturn local g_note         : copy local note
    sreturn local g_caption      : copy local caption
    sreturn local g_name         : copy local name
    sreturn local g_saving       : copy local saving
    sreturn local g_xtitle       : copy local xtitle
    sreturn local g_ytitle       : copy local ytitle
    sreturn local g_xlabel       : copy local xlabel
    sreturn local g_ylabel       : copy local ylabel
    sreturn local g_xline        : copy local xline
    sreturn local g_yline        : copy local yline
    sreturn local g_legend       : copy local legend
    sreturn local g_clegend      : copy local clegend
    sreturn local g_plegend      : copy local plegend
    sreturn local g_pcycle       : copy local pcycle
    sreturn local g_by           : copy local by
    sreturn local g_xscale       : copy local xscale
    sreturn local g_yscale       : copy local yscale
    sreturn local g_aspectratio  : copy local aspectratio
    sreturn local g_aspectplacement : copy local aspectplacement
    sreturn local g_xoverhangs   : copy local xoverhangs
    sreturn local g_yoverhangs   : copy local yoverhangs
    sreturn local g_scheme       : copy local scheme
    sreturn local g_plotregion   : copy local plotregion
    sreturn local g_graphregion  : copy local graphregion
    sreturn local g_bgcolor      : copy local bgcolor
    sreturn local g_plotbgcolor  : copy local plotbgcolor
    sreturn local g_link         : copy local link
    sreturn local g_filter       : copy local filter
    sreturn local g_ytitle2      : copy local ytitle2
    sreturn local g_xtitle2      : copy local xtitle2
    sreturn local g_ylabel2      : copy local ylabel2
    sreturn local g_xlabel2      : copy local xlabel2
    sreturn local g_xmlabel2     : copy local xmlabel2
    sreturn local g_ymlabel2     : copy local ymlabel2
    sreturn local g_xmtick2      : copy local xmtick2
    sreturn local g_ymtick2      : copy local ymtick2
    sreturn local g_yscale2      : copy local yscale2
    sreturn local g_xscale2      : copy local xscale2
    sreturn local g_ytick2       : copy local ytick2
    sreturn local g_xtick2       : copy local xtick2
    sreturn local g_yline2       : copy local yline2
    sreturn local g_xline2       : copy local xline2
    sreturn local g_xsize        : copy local xsize
    sreturn local g_ysize        : copy local ysize
    sreturn local g_fxsize       : copy local fxsize
    sreturn local g_fysize       : copy local fysize
    sreturn local g_scale        : copy local scale
    sreturn local g_hover        : copy local hover
    sreturn local g_text         : copy local text
    sreturn local g_ttext        : copy local ttext
    sreturn local g_xtick        : copy local xtick
    sreturn local g_ytick        : copy local ytick
    sreturn local g_xmtick       : copy local xmtick
    sreturn local g_ymtick       : copy local ymtick
    sreturn local g_xmlabel      : copy local xmlabel
    sreturn local g_ymlabel      : copy local ymlabel
    sreturn local g_tlabel       : copy local tlabel
    sreturn local g_ttick        : copy local ttick
    sreturn local g_tmlabel      : copy local tmlabel
    sreturn local g_tmtick       : copy local tmtick
    sreturn local g_tscale       : copy local tscale
    sreturn local g_ttitle       : copy local ttitle
    sreturn local g_tline        : copy local tline
    sreturn local g_tlabel2      : copy local tlabel2
    sreturn local g_ttick2       : copy local ttick2
    sreturn local g_tline2       : copy local tline2
    sreturn local g_tscale2      : copy local tscale2
    sreturn local g_ttitle2      : copy local ttitle2
    sreturn local g_t1title      : copy local t1title
    sreturn local g_t2title      : copy local t2title
    sreturn local g_b1title      : copy local b1title
    sreturn local g_b2title      : copy local b2title
    sreturn local g_l1title      : copy local l1title
    sreturn local g_l2title      : copy local l2title
    sreturn local g_r1title      : copy local r1title
    sreturn local g_r2title      : copy local r2title
    sreturn local g_title2       : copy local title2
    sreturn local g_subtitle2    : copy local subtitle2
    sreturn local g_zlabel       : copy local zlabel
    sreturn local g_ztitle       : copy local ztitle
    sreturn local g_zscale       : copy local zscale
    sreturn local g_nodraw       : copy local nodraw
    sreturn local g_play         : copy local play
    sreturn local g_replace      : copy local replace
    sreturn local g_table        : copy local table
    sreturn local _pending  : copy local _dash_pending
    sreturn local _unknown  : copy local _dash_unknown
end


// ================================================================
// _dash_parse_varpart_std  — varlist [if] [in]  (1-to-many vars)
// Sets s(varlist), s(if_clause), s(in_clause)
// ================================================================
program define _dash_parse_varpart_std, sclass
    version 19
    // numeric (GAPS2 G2): twoway's own y/x parser declares `varlist(min=2
    // numeric ts default=none)' (twoway_yxview_parse.class); a string
    // variable here is refused by this line, before any other check runs,
    // with the exact rc and words twoway's own `syntax' gives -- measured
    // identical across every family that takes variables (scatter,
    // histogram, rarea, pcspike, tsline, tsrline, lfit: "string variables
    // not allowed in varlist; <name> is a string variable", r(109)) --
    // never typed here by hand (test_adversarial.cscript SV-01..SV-87,
    // generated by scripts/gen_string_varlists_cscript.py).  Previously a
    // string x or y drew meaningless glyphs with no note.
    syntax varlist(numeric) [if] [in] [aweight fweight pweight iweight]
    // The weight type and its expression are handed to _dash_process_segment,
    // which honours, names or refuses them by plot type (WP-18).  syntax
    // leaves the expression in `exp' WITH its leading `= ' (measured:
    // `[aw=price]' gives exp `= price'); that is stripped here.
    if `"`weight'"' != "" sreturn local _weight `"`weight'"'
    // The expression is stripped in Mata, by value: in compound quotes inside
    // regexr() a weight holding "' -- [aw=cond(make=="'x",1,2)] -- ended
    // them (test_json_escaping.cscript JSE-47).  It and the qualifier go
    // back by `: copy local': through compound quotes a macro in them was
    // expanded again (JSE-66, JSE-69).
    if `: length local exp' {
        mata: st_local("_wx0", strtrim(regexr(st_local("exp"), "^[ ]*=[ ]*", "")))
        sreturn local _wexp : copy local _wx0
    }
    sreturn local varlist    "`varlist'"
    sreturn local if_clause  : copy local if
    sreturn local in_clause  : copy local in
end

// ================================================================
// _dash_parse_varpart_ts  — varlist [if] [in], time-series operators
// allowed (WP-30 P1.7)
//
// _dash_parse_varpart_std with `ts': twoway's y/x parser declares
// varlist(numeric ts), so scatter, line, connected, area, bar, spike,
// dropline, dot, lfit, qfit, lfitci, qfitci, mspline, mband and tsline
// draw L.close, D.close, L(1/2).close (measured on StataNow 19.5).  -syntax-
// hands back twoway's normalised list (l.close -> L.close, L(1/2).x ->
// L.x L2.x) and gives twoway's own refusals: "time variable not set"
// r(111), "<var>:  may not use time-series operators on string variables"
// r(109), "factor-variable operators not allowed" r(101), "<op>:  operator
// invalid" r(198).  fpfit, fpfitci, lowess, lpoly and lpolyci keep
// _dash_parse_varpart_std, refusing operators as twoway does, r(101).
// A separate program, so _std's macro-safe handling stays as certified.
// ================================================================
program define _dash_parse_varpart_ts, sclass
    version 19
    // The refusals and the weight, if and in handling are _std's.
    syntax varlist(numeric ts) [if] [in] [aweight fweight pweight iweight]
    // The weight type and its expression are handed to _dash_process_segment,
    // which honours, names or refuses them by plot type (WP-18).  syntax
    // leaves the expression in `exp' WITH its leading `= ' (measured:
    // `[aw=price]' gives exp `= price'); that is stripped here.
    if `"`weight'"' != "" sreturn local _weight `"`weight'"'
    // The expression is stripped in Mata, by value: in compound quotes inside
    // regexr() a weight holding "' -- [aw=cond(make=="'x",1,2)] -- ended
    // them (test_json_escaping.cscript JSE-47).  It and the qualifier go
    // back by `: copy local': through compound quotes a macro in them was
    // expanded again (JSE-66, JSE-69).
    if `: length local exp' {
        mata: st_local("_wx0", strtrim(regexr(st_local("exp"), "^[ ]*=[ ]*", "")))
        sreturn local _wexp : copy local _wx0
    }
    sreturn local varlist    "`varlist'"
    sreturn local if_clause  : copy local if
    sreturn local in_clause  : copy local in
end

// ================================================================
// _dash_parse_varpart_1v   — exactly 1 variable
// ================================================================
program define _dash_parse_varpart_1v, sclass
    version 19
    // varname(numeric) (GAPS2 G2): twoway's own declaration for the
    // univariate family (histogram.ado, kdensity.ado); varname sets
    // `varlist' too (one word), so the sreturns below stand unchanged.
    // Refuses a string variable with twoway's own rc and words, measured
    // identical to the y/x family's (test_adversarial.cscript
    // SV-01..SV-87).
    syntax varname(numeric) [if] [in] [aweight fweight pweight iweight]
    // The weight type and its expression are handed to _dash_process_segment,
    // which honours, names or refuses them by plot type (WP-18).  syntax
    // leaves the expression in `exp' WITH its leading `= ' (measured:
    // `[aw=price]' gives exp `= price'); that is stripped here.
    if `"`weight'"' != "" sreturn local _weight `"`weight'"'
    // The expression is stripped in Mata, by value: in compound quotes inside
    // regexr() a weight holding "' -- [aw=cond(make=="'x",1,2)] -- ended
    // them (test_json_escaping.cscript JSE-47).  It and the qualifier go
    // back by `: copy local': through compound quotes a macro in them was
    // expanded again (JSE-66, JSE-69).
    if `: length local exp' {
        mata: st_local("_wx0", strtrim(regexr(st_local("exp"), "^[ ]*=[ ]*", "")))
        sreturn local _wexp : copy local _wx0
    }
    sreturn local varlist    "`varlist'"
    sreturn local if_clause  : copy local if
    sreturn local in_clause  : copy local in
end

// ================================================================
// _dash_parse_varpart_3v   — the range plots' variables
//
// Any number: the count is checked by _dash_process_segment, in twoway's
// words for each type.  max=3 answered four variables "too many variables
// specified", where twoway says "rarea requires 3 variables: ...", and
// min=2 refused tsrline's one variable in -syntax-'s words, where twoway
// names the time variable (test_parser.cscript P1A-78).
// ================================================================
program define _dash_parse_varpart_3v, sclass
    version 19
    // numeric (GAPS2 G2): see _dash_parse_varpart_std; the range family
    // (rarea, rbar, rspike, rcap, rline, rconnected, rcapsym, rscatter,
    // tsrline) refuses a string variable the same way, with the same
    // measured words (test_adversarial.cscript SV-01..SV-87).  ts: twoway
    // takes time-series operators here (L.low L.high t draws, WP-30 P1.7);
    // -syntax- refuses them in twoway's words where no tsset is in force.
    syntax varlist(numeric ts) [if] [in] [aweight fweight pweight iweight]
    // The weight type and its expression are handed to _dash_process_segment,
    // which honours, names or refuses them by plot type (WP-18).  syntax
    // leaves the expression in `exp' WITH its leading `= ' (measured:
    // `[aw=price]' gives exp `= price'); that is stripped here.
    if `"`weight'"' != "" sreturn local _weight `"`weight'"'
    // The expression is stripped in Mata, by value: in compound quotes inside
    // regexr() a weight holding "' -- [aw=cond(make=="'x",1,2)] -- ended
    // them (test_json_escaping.cscript JSE-47).  It and the qualifier go
    // back by `: copy local': through compound quotes a macro in them was
    // expanded again (JSE-66, JSE-69).
    if `: length local exp' {
        mata: st_local("_wx0", strtrim(regexr(st_local("exp"), "^[ ]*=[ ]*", "")))
        sreturn local _wexp : copy local _wx0
    }
    sreturn local varlist    "`varlist'"
    sreturn local if_clause  : copy local if
    sreturn local in_clause  : copy local in
end

// ================================================================
// _dash_parse_varpart_4v   — the pc* plots' variables
//
// Any number, checked by _dash_process_segment in twoway's words: "pcspike
// requires 4 variables: mpg weight", where -syntax- said "too few
// variables specified" (test_parser.cscript P1A-78).
// ================================================================
program define _dash_parse_varpart_4v, sclass
    version 19
    // numeric (GAPS2 G2): see _dash_parse_varpart_std; the pc family
    // (pcspike, pcarrow, pcbarrow, pcscatter, pccapsym) refuses a string
    // variable the same way (test_adversarial.cscript SV-01..SV-87).  ts:
    // twoway takes time-series operators here too (WP-30 P1.7).
    syntax varlist(numeric ts) [if] [in] [aweight fweight pweight iweight]
    // The weight type and its expression are handed to _dash_process_segment,
    // which honours, names or refuses them by plot type (WP-18).  syntax
    // leaves the expression in `exp' WITH its leading `= ' (measured:
    // `[aw=price]' gives exp `= price'); that is stripped here.
    if `"`weight'"' != "" sreturn local _weight `"`weight'"'
    // The expression is stripped in Mata, by value: in compound quotes inside
    // regexr() a weight holding "' -- [aw=cond(make=="'x",1,2)] -- ended
    // them (test_json_escaping.cscript JSE-47).  It and the qualifier go
    // back by `: copy local': through compound quotes a macro in them was
    // expanded again (JSE-66, JSE-69).
    if `: length local exp' {
        mata: st_local("_wx0", strtrim(regexr(st_local("exp"), "^[ ]*=[ ]*", "")))
        sreturn local _wexp : copy local _wx0
    }
    sreturn local varlist    "`varlist'"
    sreturn local if_clause  : copy local if
    sreturn local in_clause  : copy local in
end

// ================================================================
// _dash_parse_varpart_any  — arbitrary tokens [if] [in]
// Used for scatteri (literal numbers), pci, function
// ================================================================
program define _dash_parse_varpart_any, sclass
    version 19
    // equalok: twoway function's documented form is `function y = exp`.  Without
    // it Stata rejects the "=" with r(101) "=exp not allowed", which made the
    // `y=` stripper further down unreachable and the canonical form unusable.
    //
    // Weights (WP-23): twoway function takes an aweight, fweight or pweight
    // and draws nothing different; scatteri, pci and pcarrowi refuse all
    // three, r(198) "weights not allowed" (_dash_process_segment); every
    // one refuses an iweight, r(101) "iweights not allowed", and a weight
    // naming no variable r(111) -- measured 23sep2026.  With no weight
    // clause declared, syntax answered every weight with r(101) "weights
    // not allowed".
    //
    // The plain parse runs first, and the weighted one only when it is
    // refused for a weight clause (r(101): the options were split off
    // before this runs).  Declaring weights up front made syntax read a
    // label that looks like one -- scatteri 1 2 "[aw=price]" -- as a
    // weight; twoway reads it as a label (rc 0, measured).  iweight is
    // left undeclared, so syntax gives twoway's own refusal for it,
    // before it reads the expression.
    //
    // The values are optional here: none at all -- `dash scatteri, name(x)',
    // or an if, an in or a weight alone -- is its caller's to refuse, in
    // twoway's words for each type (P1A-70, P1A-71).  syntax answered it
    // with "something required", r(100), which twoway never says.
    capture syntax [anything(name=vals equalok)] [if] [in]
    if _rc == 101 {
        syntax [anything(name=vals equalok)] [if] [in] [aweight fweight pweight]
        if `"`weight'"' != "" sreturn local _weight `"`weight'"'
        if `: length local exp' {
            mata: st_local("_wx0", strtrim(regexr(st_local("exp"), "^[ ]*=[ ]*", "")))
            sreturn local _wexp : copy local _wx0
        }
    }
    else if _rc {
        // Anything else is reported by syntax itself, as it always was.
        syntax [anything(name=vals equalok)] [if] [in]
    }
    // By value, as _dash_parse_varpart_std hands its back: a scatteri label
    // and a qualifier are the user's text (JSE-69).
    sreturn local vals       : copy local vals
    sreturn local if_clause  : copy local if
    sreturn local in_clause  : copy local in
end

// ================================================================
// _dash_graph_qualifier  -- the if/in written after the plot groups
//
// Usage:  _dash_graph_qualifier <qualifier text>
// After:  _gq_if and _gq_in in the caller hold the expression and the
//         range, without their keywords, or "".
//
// The text is every qualifier piece _dash_split_segs found at the top
// level -- after a run of plot groups, or in a `||' piece with no plot,
// `a || b || if foreign==1' -- joined with blanks.  -syntax- reads it as twoway reads it: one
// `if' and one `in', in either order, and nothing else.  Measured against
// twoway, 23sep2026: a second `if' is r(198) there ("multiple global if's
// not allowed") and "invalid syntax" here; a plot group after the
// qualifier is "invalid '('" in both; a stray word is "invalid 'foo'" in
// both.  The keyword is taken off by position: -syntax- guarantees the
// macro starts with it, and `if(foreign==1)', which twoway takes, has no
// blank after it.
// ================================================================
program define _dash_graph_qualifier
    version 19
    syntax [if] [in]
    // The keyword comes off in Mata, by value, and the result goes back by
    // `: copy local'.  In compound quotes inside regexr() a qualifier
    // holding "' ended the quote: if make != "'x" came back as  make !=,
    // with rc 0 (measured 24sep2026; test_json_escaping.cscript JSE-45); and
    // a copy through them expanded a macro in it again (JSE-66).
    mata: st_local("_gi", strtrim(regexr(st_local("if"), "^[ ]*if", "")))
    mata: st_local("_gn", strtrim(regexr(st_local("in"), "^[ ]*in", "")))
    // Its abbreviations written out, as a plot's are in
    // _dash_process_segment (QL-22).
    mata: st_local("_gi", _dash_qual_expand(st_local("_gi")))
    c_local _gq_if : copy local _gi
    c_local _gq_in : copy local _gn
end


// ================================================================
// _dash_fold_bw  -- resolve the bw() alias once the plot type is known.
//
// twoway accepts bw() only as an abbreviation of bwidth(), and only on the
// bandwidth plot types (measured rc 0: lpoly, lpolyci, lowess, kdensity);
// on bar, rbar, histogram, dot, spike, scatter, line, lfit and fpfit it is
// r(198) "option bw() not allowed" (stat_refusal_truth.json bw.<type>),
// and dash refuses it the same way (WP-35 stat:PT-14, P4-7).  On the bar
// family, where dash used to read it as barwidth(), a second line says
// "use barwidth()" (P4-9).  Called after _dash_parse_plot_opts, whose s()
// survives this second sclass call.
//
// It is also where the other options whose reading depends on the plot type
// are resolved: clcolor(), clpattern() and clwidth() (WP-22), in
// _dash_fold_cl below, mlabel(), in _dash_fold_mlab, and width() on
// kdensity, which is twoway's synonym for bwidth() there (WP-23) -- all
// before the early exit for a segment with no bw().
// ================================================================
program define _dash_fold_bw, sclass
    version 19
    args ptype
    _dash_fold_cl "`ptype'"
    _dash_fold_mlab "`ptype'"
    // A kernel written as an option of its own -- lpoly mpg weight,
    // gaussian: twoway's old syntax -- is kernel(gaussian) on lpoly,
    // lpolyci and kdensity, from each shortest spelling (gau, ep, epan2 ..)
    // to the full name (_dash_kernel_flag; measured 24sep2026, the serset
    // of kernel(<name>) each time).  It fell to the catch-all, was named in
    // the note, and the default epanechnikov was drawn.  Two kernels, or one
    // beside kernel(), were refused by _dash_opts_repeats before this; on
    // any other type the word stays where it is.  Read by value.
    mata: _dash_kernel_flag(st_global("s(_unknown)"), st_local("ptype"))
    if `: length local _kf_name' {
        sreturn local kernel : copy local _kf_name
        sreturn local _unknown : copy local _kf_rest
    }
    // WP-29 P0.9: lpolyci's pwidth(#) and var(#), taken out of the
    // catch-all by value (_dash_lpolyci_opts), and twoway's refusals of
    // them and of level(), with twoway's return codes and words, in its
    // order.  The JSON key for var() is lpvar: _dash_extract_vars reads
    // every "var": in a plot's JSON as a variable name.
    mata: _dash_lpolyci_opts(st_global("s(_unknown)"), st_local("ptype"))
    if "`_lpo_rc'" != "0" {
        mata: _dash_say("err", "", st_local("_lpo_msg"), "")
        exit `_lpo_rc'
    }
    if "`ptype'" == "lpolyci" {
        sreturn local pwidth : copy local _lpo_pwidth
        sreturn local lpvar : copy local _lpo_var
        sreturn local _unknown : copy local _lpo_rest
    }
    // kdensity: width(#) is twoway's own synonym for bwidth(#)
    // (twoway_kdensity_parse.class: Width(real 0) BWidth(real 0), the two
    // together "options width() and bwidth() may not be combined", r(198);
    // bw() is bwidth()'s abbreviation there, so it counts as bwidth()).
    // Measured 23sep2026: `twoway kdensity mpg, width(2)' plots bwidth(2)'s
    // serset.  dash's width() is histogram's bin width, and on kdensity it
    // reached the renderer as "width" and changed nothing (WP-23).
    // The values are the user's text, read from s() by value and put back by
    // `: copy local', or through macval() as bwidth() always was: read as
    // `"`s(bw)'"', bw("\`x'") was expanded to nothing and dropped with rc 0
    // (measured 24sep2026; test_json_escaping.cscript JSE-69).
    mata: st_local("_kw", st_global("s(width)"))
    if "`ptype'" == "kdensity" & `: length local _kw' {
        mata: st_local("_fb", strofreal(st_global("s(bwidth)") + st_global("s(bw)") != ""))
        if `_fb' {
            display as error "options width() and bwidth() may not be combined"
            exit 198
        }
        // The value goes on to bwidth()'s rule in _dash_validate_opts, which
        // refuses anything but a positive number.
        sreturn local bwidth `"`macval(_kw)'"'
        sreturn local width ""
    }
    mata: st_local("bw", st_global("s(bw)"))
    if !`: length local bw' exit
    local bandwidth_types "lpoly lpolyci lowess kdensity"
    local bar_types       "bar rbar histogram dot spike"
    if `: list ptype in bandwidth_types' {
        mata: st_local("_fb", strofreal(st_global("s(bwidth)") != ""))
        if `_fb' {
            // twoway: the same option twice.  Measured r(198).
            display as error "option bwidth() may not be repeated: bw() is its abbreviation"
            exit 198
        }
        sreturn local bwidth : copy local bw
    }
    else {
        // Off the bandwidth types twoway refuses it (WP-35 stat:PT-14,
        // P4-7; stat_refusal_truth.json bw.<type>); where dash read it as
        // barwidth(), a second line names twoway's spelling (P4-9).
        display as error "option bw() not allowed"
        if `: list ptype in bar_types' display as error "      use barwidth()"
        exit 198
    }
    sreturn local bw ""
end

// ================================================================
// _dash_fold_stat_words <ptype> `"<options>"'  -- the statistical types'
// spellings twoway reads and dash's declarations do not (WP-35 35-03).
//
// Each branch is one item's; the words are read by value.
//
// lowess m (stat:PT-7): twoway_lowess_parse.class declares Mean, so a bare
// m is mean (measured: the serset of lowess mpg weight, m is mean's,
// test/fixtures/stat_accept_truth.json lowess_m); dash declares MEan,
// one letter longer, so that m stays MColor()'s spelling elsewhere.  The
// word is taken out of the catch-all, by value, and recorded as mean.
// Called directly after _dash_refuse_unbound, before _dash_refuse_unknown
// would refuse the word, and again after _dash_opts_repeats, because
// _dash_refuse_unknown, _dash_refuse_foreign and _dash_opts_repeats parse
// the list again, which undoes what the first call wrote; it only
// rewrites s(), so the second call changes nothing the first one kept.
// ================================================================
program define _dash_fold_stat_words, sclass
    version 19
    args ptype
    // lowess weight (stat:PT-8): twoway_lowess_parse.class declares
    // noWeight, so a bare weight -- w and longer -- is its default and
    // draws as without it (stat_refusal_truth.json lowess.weight, the
    // serset of lowess.none), and beside noweight it is "option noweight
    // not allowed", r(198) (lowess.noweight_weight).  The word is taken
    // out of the catch-all, by value, in silence; with noweight the pair
    // is recorded in the caller's _fsw_nowt, which the caller clears
    // before the first call (_dash_opts_repeats reads weight beside
    // noweight as its other half, so the second call may not see the
    // pair), and refused there, after the list's other refusals, as
    // twoway names an unknown word before it.
    if "`ptype'" == "lowess" {
        mata: st_local("_fsw_t", strofreal(anyof(_dash_opt_tokens(st_global("s(_unknown)")), "m")))
        if `_fsw_t' {
            mata: _fsw_u = _dash_opt_tokens(st_global("s(_unknown)"))
            mata: _fsw_u = select(_fsw_u, _fsw_u :!= "m")
            mata: st_local("_fsw_rest", cols(_fsw_u) ? invtokens(_fsw_u) : "")
            capture mata: mata drop _fsw_u
            sreturn local mean "mean"
            sreturn local _unknown : copy local _fsw_rest
        }
        mata: _fsw_u = _dash_opt_tokens(st_global("s(_unknown)"))
        mata: _fsw_w = J(1, cols(_fsw_u), 0)
        mata: for (_fsw_i = 1; _fsw_i <= cols(_fsw_u); _fsw_i++) _fsw_w[_fsw_i] = strlen(_fsw_u[_fsw_i]) >= 1 & strlen(_fsw_u[_fsw_i]) <= 6 & substr("weight", 1, strlen(_fsw_u[_fsw_i])) == _fsw_u[_fsw_i]
        mata: st_local("_fsw_t", strofreal(any(_fsw_w)))
        if `_fsw_t' {
            mata: _fsw_u = select(_fsw_u, !_fsw_w)
            mata: st_local("_fsw_rest", cols(_fsw_u) ? invtokens(_fsw_u) : "")
            sreturn local _unknown : copy local _fsw_rest
            mata: st_local("_fsw_v", st_global("s(noweight)"))
            if `: length local _fsw_v' c_local _fsw_nowt 1
        }
        capture mata: mata drop _fsw_u _fsw_w _fsw_i
    }
    // contour and contourline (stat:PT-13): twoway_zyx2view_parse.class
    // declares Interp, CLPatterns, CLWidths and COLORLines, so i() ..
    // inter() are interp(), colorl .. colorline colorlines, and clp() ..
    // clpattern() and clw() .. clwidth() -- which this parser binds to
    // the connecting line's clpattern() and clwidth() -- clpatterns() and
    // clwidths() (stat_accept_truth.json contour.*).
    // function's subchar() (stat:PT-6), read by _dash_label_split:
    // twoway_function_parse.class declares SUBChar(name), so off function
    // it is "option subchar() not allowed", two words are "option
    // subchar():  too many names specified", r(103), and a word that is
    // no name "<word> invalid name", r(198) (stat_accept_truth.json
    // subchar.*).  Recorded in the caller's _fsw_subc (off, many or bad)
    // and refused there after the list's other refusals, as twoway names
    // an unknown word before it (subchar.order).
    c_local _fsw_subc ""
    // The edge values twoway takes (stat:PT-9; stat_accept_truth.json
    // bands.<type>.-1, n.<type>.<v>, nr.<type>.<v>): bands(-1) on mspline
    // and mband is Bands(integer -1), the default, and draws as without
    // it.  n() on the fit types is an integer, else "option n() not
    // allowed", r(198) (2.5, -1.5, .); fpfitci takes any integer and does
    // not use it; on lfit, qfit, lfitci and qfitci an integer from 1 up
    // draws that many points, with no upper bound, one from -1 down to
    // minus the dataset's observations (c(N), whatever the if) is an
    // empty fit, drawn by twoway's own generator (_dash_fit_points), and
    // 0 or one below that is "'<n>' invalid observation number", r(198).
    // The refusals are recorded in the caller's _fsw_n0 (obs or bad) and
    // given there; the value is read by value and echoed as typed.
    c_local _fsw_n0 ""
    mata: st_local("_fsw_v", strtrim(st_global("s(bands)")))
    local _fsw_band "mspline mband"
    if `: list ptype in _fsw_band' & "`_fsw_v'" == "-1" sreturn local bands ""
    mata: st_local("_fsw_v", strtrim(st_global("s(n)")))
    local _fsw_ntypes "fpfitci lfit qfit lfitci qfitci"
    if `: list ptype in _fsw_ntypes' & `: length local _fsw_v' {
        mata: _fsw_x = strtoreal(st_local("_fsw_v"))
        mata: st_local("_fsw_ni", strofreal(_fsw_x < . & _fsw_x == floor(_fsw_x)))
        mata: st_local("_fsw_nlo", strofreal(_fsw_x == 0 | _fsw_x < -st_numscalar("c(N)")))
        capture mata: mata drop _fsw_x
        if !`_fsw_ni' c_local _fsw_n0 "bad"
        else if "`ptype'" == "fpfitci" sreturn local n ""
        else if `_fsw_nlo' c_local _fsw_n0 "obs"
    }
    mata: st_local("_fsw_v", st_global("s(subchar)"))
    if `: length local _fsw_v' {
        if "`ptype'" != "function" c_local _fsw_subc "off"
        else if `: word count `_fsw_v'' > 1 c_local _fsw_subc "many"
        else {
            capture confirm name `_fsw_v'
            if _rc c_local _fsw_subc "bad"
        }
    }
    // s() .. symbol() (syn:SD-20c): twoway_yxview_parse.class's Symbol,
    // factored as msymbol() is, on every plot type -- lpolyci s(line) is
    // msymbol(line), and scatter s(Oh) draws msymbol(Oh)'s SVG
    // (stat_accept_truth.json sd20c.*) -- read as msymbol() when no
    // msymbol() is given, the rightmost copy kept, and taken out of the
    // catch-all, by value.
    mata: _fsw_u = _dash_opt_tokens(st_global("s(_unknown)"))
    mata: st_local("_fsw_k", strofreal(cols(_fsw_u)))
    local _fsw_sy ""
    local _fsw_rest ""
    forvalues _fi = 1/`_fsw_k' {
        mata: st_local("_fsw_nm", _dash_rep_optname(_fsw_u[`_fi']))
        mata: st_local("_fsw_p", strofreal(strpos(_fsw_u[`_fi'], "(") > 0))
        if `_fsw_p' & inlist("`_fsw_nm'", "s", "sy", "sym", "symb", "symbo", "symbol") {
            mata: st_local("_fsw_sy", substr(_fsw_u[`_fi'], strpos(_fsw_u[`_fi'], "(") + 1, strlen(_fsw_u[`_fi']) - strpos(_fsw_u[`_fi'], "(") - 1))
            local _fsw_hit 1
        }
        else mata: st_local("_fsw_rest", st_local("_fsw_rest") + (st_local("_fsw_rest") == "" ? "" : " ") + _fsw_u[`_fi'])
    }
    capture mata: mata drop _fsw_u
    if "`_fsw_hit'" == "1" {
        mata: st_local("_fsw_m", strofreal(strtrim(st_global("s(msymbol)")) == ""))
        if `_fsw_m' sreturn local msymbol : copy local _fsw_sy
        sreturn local _unknown : copy local _fsw_rest
    }
    // ty() and typ() on the ci types (syn:SD-7): their parse classes
    // declare TYPE and RECASTas, so only type() in full is refused
    // ("type() option not allowed", by _dash_recast_opt); a shorter
    // spelling draws as ciplot() does (stat_accept_truth.json ty.<type>,
    // ciplot.<type>: one SVG), so it is read as ciplot() when no
    // ciplot() is given.  The spelling is read from the option text, by
    // value.
    mata: _dash_text_args(1, 0, 0)
    mata: st_local("_fsw_ty", strtrim(st_global("s(type)")))
    mata: st_local("_fsw_r", strtrim(st_global("s(recast)")))
    local _fsw_ci "lfitci qfitci fpfitci lpolyci"
    if `: list ptype in _fsw_ci' & `: length local _fsw_ty' & !`: length local _fsw_r' {
        mata: _fsw_u = _dash_opt_tokens(st_local("_dash_txt"))
        mata: st_local("_fsw_k", strofreal(cols(_fsw_u)))
        local _fsw_tn ""
        local _fsw_full 0
        forvalues _fi = 1/`_fsw_k' {
            mata: st_local("_fsw_nm", _dash_rep_optname(_fsw_u[`_fi']))
            if inlist("`_fsw_nm'", "ty", "typ") local _fsw_tn "`_fsw_nm'"
            if "`_fsw_nm'" == "type" local _fsw_full 1
        }
        capture mata: mata drop _fsw_u
        if `_fsw_full' local _fsw_tn "type"
        if "`_fsw_tn'" != "" & "`_fsw_tn'" != "type" {
            mata: st_local("_fsw_c", st_global("s(ciplot)"))
            if !`: length local _fsw_c' sreturn local ciplot : copy local _fsw_ty
            sreturn local type ""
        }
    }
    local _fsw_ct "contour contourline"
    if `: list ptype in _fsw_ct' {
        mata: _dash_zyx_abbrev(st_global("s(_unknown)"), st_local("_dash_txt"))
        if `_za_iset' sreturn local interp : copy local _za_interp
        if `_za_cl' sreturn local colorlines "colorlines"
        sreturn local _unknown : copy local _za_rest
        foreach w in pattern width {
            mata: st_local("_fsw_v", st_global("s(cl`w')"))
            mata: st_local("_fsw_p", strofreal(st_global("s(cl`w's)") == ""))
            if `: length local _fsw_v' & `_fsw_p' {
                sreturn local cl`w's : copy local _fsw_v
                sreturn local cl`w' ""
            }
        }
    }
end

// ================================================================
// _dash_fold_cl  -- keep clcolor(), clpattern() and clwidth() on the plot
//                   types whose CONNECTING line twoway styles with them.
//
// ROADMAP WP-22 AC-22.2.  twoway_yxview_parse.class factors CLColor() to
// line(color()) alone, where LColor() is line(color()) AND
// area(linestyle(color())), and factors the cl options after the l options
// whatever order they were typed in.  Which types draw that `line' style
// was measured 23sep2026 from SVG exports of what twoway draws: on line,
// connected, lfit, qfit, fpfit, lpoly, lowess, mspline, mband, kdensity,
// function and tsline, clX draws exactly what lX draws; on lfitci, qfitci,
// lpolyci and fpfitci it styles the fit line alone; on every other type --
// area, bar, histogram, spike, dropline, dot, scatter, the range and
// paired-coordinate types, scatteri and pci -- the picture is identical to
// one drawn with no option at all, and clwidth(-1), which twoway refuses
// when it draws the line ("gm_linewidth must be between 0.000 and
// 1.0e+04", r(198)), is accepted, because it is never evaluated.
//
// So the three are kept for the renderer on the types that draw the line,
// where it lets them style it in place of lcolor(), lpattern() and
// lwidth(), and dropped everywhere else: twoway draws nothing for them
// there, dash draws nothing either, and the note does not name them,
// because nothing dash draws differs from what twoway draws.  A plot type
// added to dash later is not on the list, and the three are dropped there
// until it is measured.
//
// Called first thing by _dash_fold_bw, so before _dash_validate_opts:
// clwidth()'s rule fires exactly where twoway evaluates the width.
// ================================================================
program define _dash_fold_cl, sclass
    version 19
    args ptype
    // scatter (WP-35 syn:SD-20e): twoway reads the four for scatter's
    // connecting line, drawn when connect() is given, and draws nothing
    // for them without it; they are kept, so the spec records what twoway
    // reads, and the renderer draws no line for them.
    local cl_types "line connected lfit qfit fpfit lpoly lowess mspline mband kdensity function tsline lfitci qfitci lpolyci fpfitci scatter"
    if `: list ptype in cl_types' exit
    sreturn local clcolor   ""
    sreturn local clpattern ""
    sreturn local clwidth   ""
    // clstyle() styles the connecting line only (WP-30 P1.14a, D-32c).
    sreturn local clstyle   ""
end

// ================================================================
// _dash_fold_mlab  -- mlabel() where twoway refuses it, or never reads it.
//
// Measured 23sep2026, one twoway probe per plot type (rc, and the SVG it
// exports): on mspline and mband twoway reads mlabel()'s variable as a
// third plotted variable and refuses the command -- "too many variables
// specified", r(103) -- whatever the variable, string or numeric; a
// variable that does not exist it refuses with r(111) on every type but
// histogram and function, which never read the option at all
// (mlabel(nosuchvar) is rc 0 there, and draws nothing).
//
// So mlabel() is refused on mspline and mband, naming it, when its
// variable exists -- one that does not is refused r(111) by the value
// rules, as twoway refuses it -- and dropped on histogram and function
// before those rules run, so a variable that does not exist is not
// refused where twoway accepts it.  Everywhere else it reaches the
// renderer, which draws the labels where twoway draws them and nowhere
// else: none on line, area, the fits and the range lines, bars and caps,
// among others (dash.sthlp, Marker Label Options).  The note does not
// name mlabel() on those, because twoway draws nothing for it there
// either.
// WP-30 P1.1b: twoway checks the list first (measured 03oct2026): .. on
// histogram and function and = on histogram are r(198) (S08, T01, T04);
// on mspline and mband _dash_mlabel_list's checks precede r(103) (S06-T10).
//
// Called by _dash_fold_bw, after _dash_fold_cl and before
// _dash_validate_opts.  The value is read from s() by value and only ever
// put on a command line through macval(), so a backtick or a dollar sign
// in it cannot become a macro reference.
// ================================================================
program define _dash_fold_mlab, sclass
    version 19
    args ptype
    // By value: read as `"`s(mlabel)'"', mlabel("\`x'") was expanded to
    // nothing, so on histogram it was not dropped and the value rules
    // refused it, r(111), where twoway accepts it (measured 24sep2026;
    // test_json_escaping.cscript JSE-69).
    mata: st_local("v", st_global("s(mlabel)"))
    if !`: length local v' exit
    local mlab_unread  "histogram function"
    local mlab_refused "mspline mband"
    if `: list ptype in mlab_unread' {
        mata: _dash_stylelist_locals(st_local("v"), "_fm")
        forvalues j = 1/`_fmn' {
            if "`_fmq`j''" == "1" continue
            mata: st_local("_c", (st_local("_fmt`j'") == ".." | st_local("_fmt`j'") == "..." | st_local("_fmt`j'") == "=") ? st_local("_fmt`j'") : "")
            if "`_c'" == ".." | "`_c'" == "..." {
                display as error "`_c' not allowed in option mlabel()"
                exit 198
            }
            if "`_c'" == "=" & "`ptype'" == "histogram" {
                display as error "invalid syntax"
                exit 198
            }
        }
        sreturn local mlabel ""
        exit
    }
    if `: list ptype in mlab_refused' {
        _dash_mlabel_list "dash" `"`macval(v)'"' "`ptype'" 1
        display as error "dash: mlabel() is not allowed on `ptype' (twoway: too many variables specified)"
        exit 103
    }
end

// ================================================================
// _dash_mlabv_parse  -- twoway's own reading of mlabvposition().
//
// twoway_yxview_parse.class declares MLABVposition(name) and unabbreviates
// it with unab, so its messages and codes are Stata's: two names
// "option mlabvposition():  too many names specified" r(103), an
// expression "<tok> invalid name" r(198), a missing variable "variable
// <x> not found" r(111).  Not sclass, and never touches s(): the caller's
// s() survives.  Returns the unabbreviated name in the caller's _mv_name.
// ================================================================
program define _dash_mlabv_parse
    version 19
    syntax [, MLABVposition(name)]
    if "`mlabvposition'" != "" unab mlabvposition : `mlabvposition'
    c_local _mv_name `mlabvposition'
end

// ================================================================
// _dash_fold_mlabv  -- mlabvposition() where twoway refuses it, or never
//                      reads it (WP-30 P1.24).
//
// Measured (StataNow 19.5; test/fixtures/mlabvpos_truth.json and the MV
// cases of test_twoway_option_parity.cscript): twoway appends the
// variable to the layer's varlist (twoway_yxview_parse.class:308-317), so
// the types that count their variables refuse it -- the range types and
// tsrline "<type> requires 3 variables: <varlist>", the fits, mspline and
// mband "too many variables specified: <varlist>", lowess, lpoly, lpolyci
// and kdensity "too many variables specified", each r(103).  The range
// types and lfit-like fits subtract the label variables before counting
// (twoway_y2xview_parse.class:36-44, twoway_lfit_parse.class:35-41);
// mspline and mband do not (twoway_mspline_parse.class:25-26).  A name
// already in the list adds nothing, so rscatter y y2 x, mlabvposition(y)
// is accepted, as twoway accepts it.  histogram, function, scatteri, pci
// and pcarrowi never read the option.  Called by _dash_process_segment
// before _dash_fold_bw (so before _dash_fold_mlab); the value is read
// from s() by value and reaches a command line only inside macval(),
// where syntax's name type refuses anything but one name.
// ================================================================
program define _dash_fold_mlabv, sclass
    version 19
    args ptype pvars
    mata: st_local("v", st_global("s(mlabvposition)"))
    if !`: length local v' exit
    local mv_unread "histogram function scatteri pci pcarrowi"
    if `: list ptype in mv_unread' {
        sreturn local mlabvposition ""
        exit
    }
    capture noisily _dash_mlabv_parse , mlabvposition(`macval(v)')
    if _rc exit _rc
    sreturn local mlabvposition `"`_mv_name'"'
    if "`_mv_name'" == "" exit
    local mv_range "rarea rbar rcap rcapsym rconnected rline rscatter rspike tsrline rpcap rpspike"
    local mv_fit   "lfit qfit fpfit lfitci qfitci fpfitci mspline mband"
    local mv_smooth "lowess lpoly lpolyci kdensity"
    local mv_all : list mv_range | mv_fit
    local mv_all : list mv_all | mv_smooth
    if !`: list ptype in mv_all' exit
    // The label variables, without mlabel()'s "." placeholders.
    mata: st_local("ml", invtokens(select(tokens(st_global("s(mlabel)")), tokens(st_global("s(mlabel)")) :!= ".")))
    local labs ""
    if `: length local ml' {
        capture unab labs : `macval(ml)'
        if _rc exit
    }
    local pvars : list retokenize pvars
    local all : list pvars | labs
    local all : list all | _mv_name
    local mv_nosub "mspline mband"
    if `: list ptype in mv_nosub' local counted : copy local all
    else local counted : list all - labs
    local limit 2
    if `: list ptype in mv_range' local limit 3
    if "`ptype'" == "kdensity" local limit 1
    if `: word count `counted'' <= `limit' exit
    if `: list ptype in mv_range' {
        local shown "`ptype'"
        if "`ptype'" == "tsrline" local shown "rline"
        mata: _dash_say("err", st_local("shown") + " requires 3 variables: ", st_local("all"), "")
    }
    else if `: list ptype in mv_fit' {
        mata: _dash_say("err", "too many variables specified: ", st_local("all"), "")
    }
    else display as error "too many variables specified"
    exit 103
end

// ================================================================
// _dash_fold_mlabr  -- a range plot labelled by its own variables
//
// WP-31 C14.  twoway_y2xview_parse.class:35-45 (and y3xview's) puts the
// label variables in the layer's list, each once, and takes them off
// before counting, so mlabel() naming a plotted variable leaves too few:
// "<type> requires 3 variables: <list>" on every range type and "you must
// specify four variables with twoway <type>" on rpcap and rpspike, both
// r(102), the list the plotted, label and mlabvposition() variables once
// each (measured, test/fixtures/varlabel_mlabel_truth.json c14.y, c14.y2,
// c14.x, c14.y_other "rscatter requires 3 variables: lo hi weight make",
// c14.rbar_y .. c14.rpspike_y).  mlabvposition(p9) beside mlabel(lo)
// brings the count back and twoway draws it (test_twoway_option_parity
// MV-11).  Called by _dash_process_segment after _dash_fold_mlabv, which
// leaves the mlabvposition() name in s(); reads s() by value only.
// ================================================================
program define _dash_fold_mlabr
    version 19
    args ptype pvars
    local r3 "rarea rbar rcap rcapsym rconnected rline rscatter rspike"
    local r4 "rpcap rpspike"
    local rall : list r3 | r4
    if !`: list ptype in rall' exit
    mata: st_local("ml", invtokens(select(tokens(st_global("s(mlabel)")), tokens(st_global("s(mlabel)")) :!= ".")))
    if !`: length local ml' exit
    capture unab labs : `macval(ml)'
    if _rc exit
    local pvars : list retokenize pvars
    local dup : list labs & pvars
    if "`dup'" == "" exit
    mata: st_local("mv", st_global("s(mlabvposition)"))
    local all : list pvars | labs
    local all : list all | mv
    local counted : list all - labs
    local limit = cond(`: list ptype in r4', 4, 3)
    if `: word count `counted'' >= `limit' exit
    if `: list ptype in r4' {
        mata: _dash_say("err", "you must specify four variables with twoway " + st_local("ptype"), "", "")
    }
    else mata: _dash_say("err", st_local("ptype") + " requires 3 variables: ", st_local("all"), "")
    exit 102
end

// ================================================================
// _dash_fold_range ptype qual  -- range(varname) as twoway reads it
//
// WP-31 C10a (D-05.a).  _dash_validate_value's range kind hands back
// "@var:<name>" for a variable named in kdensity's or function's range();
// twoway takes that variable's min and max (measured,
// test/fixtures/value_bounds_truth.json range.var_kdensity and
// range.var_function).  Here, once, over the plot's sample -- its own if
// and in and the graph's, the string scalar named by qual -- s(range)
// becomes the two numbers and s(range_var) the name, so both renderers
// and the saved page read numbers as for range(# #).  A move of a filter
// does not move them: twoway draws once.  With no observation (a string
// variable, or one all missing over the sample) function is r(2000) "no
// observations", as twoway's is; kdensity is drawn as twoway draws it,
// an empty curve, in silence (WP-31 C10d).  Called by
// _dash_process_segment after _dash_validate_opts; the name passed the
// kind's regex and confirm variable there.
// ================================================================
program define _dash_fold_range, sclass
    version 19
    args ptype qual
    mata: st_local("v", st_global("s(range)"))
    if substr(`"`macval(v)'"', 1, 5) != "@var:" exit
    local name = substr(`"`v'"', 6, .)
    mata: st_local("_fr_q", st_strscalar(st_local("qual")))
    capture confirm numeric variable `name'
    local _fr_n 0
    if !_rc {
        quietly summarize `name' `macval(_fr_q)', meanonly
        local _fr_n = r(N)
    }
    if `_fr_n' == 0 {
        if "`ptype'" == "function" {
            display as error "no observations"
            exit 2000
        }
        // kdensity: twoway draws an empty curve, rc 0, in silence
        // (WP-31 C10d; estimator_edges_truth.json kd.range_string and
        // kd.range_missing: every serset x and density missing).  The
        // name goes with no numbers, which both renderers draw empty.
        sreturn local range ""
        sreturn local range_var "`name'"
        exit
    }
    local lo = strtrim(string(r(min), "%21.0g"))
    local hi = strtrim(string(r(max), "%21.0g"))
    sreturn local range "`lo' `hi'"
    sreturn local range_var "`name'"
end

// ================================================================
// _dash_contour_split  -- contour's options, read before the plot parser's
//
// WP-31 B4b.  twoway_zyx2view_parse's options, read by a syntax of their
// own out of the option text _dash_parse_plot_opts hands over in the Mata
// string _dash_zyx_text (by value), which gets the rest back as typed:
// that parser's syntax holds as many options as -syntax- takes (one more
// is r(197), measured 15oct2026).  The minimums are twoway's, except
// levels(), interp(), clwidths(), clpatterns() and colorlines, typed in
// full here: their twoway minimums (lev, i, clw, clp, colorl) are already
// level(), the i* options, clwidth(), clpattern() and colorlist()
// (_dash_contour_check reads level() as levels() on the contour types, as
// twoway does).  Sets the caller's locals of the same names, by value.
// ================================================================
program define _dash_contour_split
    version 19
    // le() typed as such: level() on every type, which twoway's contour
    // refuses where it reads lev() .. level() as levels() (measured
    // 15oct2026, contour_truth.json abbrev.le, abbrev.lev .. level).
    _dash_le_typed
    c_local _dash_le_typed `"`_le_typed'"'
    // The text is read only when it may hold one of these options, and
    // then token by token: -syntax-'s catch-all takes the quotes off a
    // bare "string" after the comma, which the plot parser then misreads
    // (test_json_escaping.cscript JSE-69, test_parser.cscript U26-12).
    // Otherwise it is left as typed.
    local zo "ccuts levels minmax crule scolor ecolor ccolors clabels format interp clwidths clpatterns reversekey heatmap outlines colorlines"
    mata: st_local("_zyx_any", strofreal(regexm(strlower(_dash_zyx_text), "(^|[ ,])(cc|lev|minmax|crule|sc|ec|clab|format|interp|clwidths|clpatterns|rev|heatmap|out|colorlines)")))
    if !`_zyx_any' {
        foreach o of local zo {
            c_local `o' ""
        }
        // The text without its comma, as -syntax- hands the rest back.
        mata: _dash_zyx_text = regexr(_dash_zyx_text, "^[ ]*,", "")
        exit
    }
    // Each top-level option (_dash_opt_tokens, by value) is tried alone
    // against contour's declarations; the ones it reads are parsed
    // together, every other token is handed back exactly as typed -- a
    // bare "string" keeps its quotes.
    mata: _dash_zyx_tok = _dash_opt_tokens(regexr(_dash_zyx_text, "^[ ]*,", ""))
    mata: _dash_zyx_in = ""
    mata: _dash_zyx_out = ""
    mata: st_local("_zn", strofreal(cols(_dash_zyx_tok)))
    // WP-35 MS-1: each token read is named by the option it binds to, and
    // only the last copy of a valued option is parsed -- twoway takes the
    // rightmost (twoway_zyx2view_parse.class, _parse combop ...
    // rightmost); a flag keeps every copy, so the syntax below refuses a
    // flag given twice, as twoway's does (_dash_rightmost_keep).
    mata: _dash_zyx_nm = J(1, `_zn', "")
    forvalues _zi = 1/`_zn' {
        mata: st_local("0", ", " + _dash_zyx_tok[`_zi'])
        capture syntax [, CCUTs(string asis) LEVELS(string) MINMAX ///
            CRULE(string asis) SColor(string asis) EColor(string asis) ///
            CColors(string asis) CLABels(string asis) FORMAT(string asis) ///
            INTERP(string asis) CLWIDTHS(string asis) ///
            CLPATTERNS(string asis) REVersekey HEATMAP OUTlines COLORLINES ]
        if _rc mata: _dash_zyx_out = _dash_zyx_out + " " + _dash_zyx_tok[`_zi']
        else {
            local _zyx_in_`_zi' 1
            foreach o of local zo {
                if `: length local `o'' mata: _dash_zyx_nm[`_zi'] = "`o'"
            }
        }
    }
    mata: _dash_zyx_keep = _dash_rightmost_keep(_dash_zyx_nm, "minmax reversekey heatmap outlines colorlines")
    forvalues _zi = 1/`_zn' {
        if "`_zyx_in_`_zi''" == "1" {
            mata: st_local("_k", strofreal(_dash_zyx_keep[`_zi']))
            if `_k' mata: _dash_zyx_in = _dash_zyx_in + " " + _dash_zyx_tok[`_zi']
        }
    }
    mata: mata drop _dash_zyx_nm _dash_zyx_keep
    mata: st_local("0", ", " + _dash_zyx_in)
    syntax [, CCUTs(string asis) LEVELS(string) MINMAX CRULE(string asis) ///
        SColor(string asis) EColor(string asis) CColors(string asis) ///
        CLABels(string asis) FORMAT(string asis) INTERP(string asis) ///
        CLWIDTHS(string asis) CLPATTERNS(string asis) REVersekey ///
        HEATMAP OUTlines COLORLINES ]
    foreach o of local zo {
        c_local `o' `"`macval(`o')'"'
    }
    mata: _dash_zyx_text = strtrim(_dash_zyx_out)
end

// ================================================================
// _dash_label_split  -- options the plot parser's syntax has no room for
//
// WP-31 S34.  The plot parser's syntax holds as many options as -syntax-
// takes (_dash_contour_split), so twoway's yvarlabel() and xvarlabel()
// (advanced_options.sthlp, every yxview type: FactorPlot), mlabprefix(),
// mlabsuffix() and lalign() (WP-31 C17; the seriesstyle options every
// yxview type factors) are read here,
// out of the option text _dash_zyx_text holds (by value), as
// _dash_contour_split reads contour's: each top-level option tried alone
// against these declarations, the ones read parsed together, every other
// token handed back exactly as typed.  The minimums are twoway's (yvarl,
// xvarl; measured: twoway takes yvarl("Q") xvarl("R"), rc 0).  Each value
// is kept as typed, quotes and all, so xvarlabel("") -- no x title, as
// twoway draws it (test/fixtures/varlabel_mlabel_truth.json
// varlabel.x_empty) -- is a value and not an absent option.  function's
// subchar() (WP-35 stat:PT-6; twoway_function_parse.class SUBChar, minimum
// subc) is read here too; _dash_fold_stat_words checks it.  Sets the
// caller's locals of the same names, by value.
// ================================================================
program define _dash_label_split
    version 19
    local lo "yvarlabel xvarlabel mlabprefix mlabsuffix lalign mlabstyle table table2 subchar"
    foreach o of local lo {
        c_local `o' ""
    }
    mata: st_local("_lb_any", strofreal(regexm(strlower(_dash_zyx_text), "(^|[ ,])(yvarl|xvarl|mlabpre|mlabsuf|mlabst|la\(|lal|table|subc)")))
    if !`_lb_any' exit
    mata: _dash_lb_tok = _dash_opt_tokens(_dash_zyx_text)
    mata: _dash_lb_in = ""
    mata: _dash_lb_out = ""
    mata: st_local("_ln", strofreal(cols(_dash_lb_tok)))
    local _lb_tab 0
    // WP-35 MS-1: each token read is named by the option it binds to, and
    // only the last copy of each is parsed, as twoway takes yvarlabel(),
    // xvarlabel(), mlabprefix(), mlabsuffix() rightmost
    // (advanced_options.sthlp; _dash_rightmost_keep).
    mata: _dash_lb_nm = J(1, `_ln', "")
    forvalues _li = 1/`_ln' {
        mata: st_local("0", ", " + _dash_lb_tok[`_li'])
        // la(), lal() .. lalign() are lalign(), as twoway reads them
        // (WP-31 C17b, measured: lal(outside) sets the align outside,
        // test/fixtures/colour_width_edges_truth.json lal.*; l() is
        // l1title()); lalp() .. lalpha() are dash's own lalpha(), the plot
        // parser's LALPha.
        capture syntax [, YVARLabel(string asis) XVARLabel(string asis) ///
            MLABPREfix(string asis) MLABSUFFix(string asis) LAlign(string) ///
            MLABSTyle(string asis) TABLE TABLE2(string asis) SUBChar(string) ]
        local _rc_lb = _rc
        // A second table (WP-31 H2t) goes on with the rest, as typed: the
        // repeat check then refuses it as a second name() is refused.
        if !`_rc_lb' & (`"`table'`macval(table2)'"' != "") {
            if `_lb_tab' local _rc_lb 1
            local _lb_tab 1
        }
        if `_rc_lb' mata: _dash_lb_out = _dash_lb_out + " " + _dash_lb_tok[`_li']
        else {
            local _lb_in_`_li' 1
            foreach o of local lo {
                if `: length local `o'' mata: _dash_lb_nm[`_li'] = "`o'"
            }
        }
    }
    mata: _dash_lb_keep = _dash_rightmost_keep(_dash_lb_nm, "table")
    forvalues _li = 1/`_ln' {
        if "`_lb_in_`_li''" == "1" {
            mata: st_local("_k", strofreal(_dash_lb_keep[`_li']))
            if `_k' mata: _dash_lb_in = _dash_lb_in + " " + _dash_lb_tok[`_li']
        }
    }
    mata: st_local("0", ", " + _dash_lb_in)
    syntax [, YVARLabel(string asis) XVARLabel(string asis) ///
        MLABPREfix(string asis) MLABSUFFix(string asis) LAlign(string) ///
        MLABSTyle(string asis) TABLE TABLE2(string asis) SUBChar(string) ]
    foreach o of local lo {
        c_local `o' `"`macval(`o')'"'
    }
    mata: _dash_zyx_text = strtrim(_dash_lb_out)
    mata: mata drop _dash_lb_tok _dash_lb_in _dash_lb_out _dash_lb_nm _dash_lb_keep
end

// ================================================================
// _dash_le_typed  -- whether le() itself is typed among the plot options
//
// WP-31 B4b.  Reads the option text _dash_zyx_text holds (by value) with
// a syntax that declares LE() alone, so only le( matches -- lev() and
// longer, and a le( inside another option's parentheses or quotes, do
// not -- and sets the caller's local _le_typed to 1 or "".  The text is
// left as it was.
// ================================================================
program define _dash_le_typed
    version 19
    c_local _le_typed ""
    // Only where le( may be typed (see _dash_contour_split on quotes).
    mata: st_local("_le_any", strofreal(regexm(_dash_zyx_text, "(^|[ ,])le\(")))
    if !`_le_any' exit
    mata: st_local("0", _dash_zyx_text)
    syntax [, LE(string asis) * ]
    if `"`macval(le)'"' != "" c_local _le_typed 1
    else c_local _le_typed ""
end

// ================================================================
// _dash_contour_check <own>  -- contour's options read as twoway reads them
//
// WP-31 B4b.  twoway_zyx2view_parse.class:94-198, measured 15oct2026
// (test/fixtures/contour_truth.json refuse.*): every contour option on any
// other type is "option <name>() not allowed" (a flag without the
// parentheses), r(198); ccuts() with levels() is "option ccuts() cannot
// be combined with option levels()", r(198); ccuts() is a numlist, sorted
// (a word that is no number: "ccuts() invalid -- invalid numlist",
// r(121)); levels() an integer ("option levels() incorrectly specified"
// for any other word, "invalid syntax" for a negative one, both r(198);
// levels(0) and levels(1) draw the default cuts; lev() .. level() are
// levels(), as twoway's minimum lev reads them); crule() a zyx2rule
// name, else two notes and r(198), as colorrule() (_dash_colorrule_check).
// Writes the sorted ccuts() back to s(ccuts), a level() to s(levels) and
// an abbreviated crule() (lin) in full to s(crule).
// Called by
// _dash_process_segment before _dash_validate_opts, with the layer's own
// type.  sclass: it touches only s(ccuts), s(levels), s(level) and
// s(crule).
// ================================================================
program define _dash_contour_check, sclass
    version 19
    args own
    local zo "ccuts levels minmax crule scolor ecolor ccolors clabels format interp clwidths clpatterns reversekey heatmap outlines colorlines"
    local zo_flags "minmax reversekey heatmap outlines colorlines"
    if !inlist("`own'", "contour", "contourline") {
        foreach o of local zo {
            local _zs = cond(inlist("`o'", "heatmap", "outlines"), "_`o'", "`o'")
            mata: st_local("_zv", strofreal(st_global("s(`_zs')") != ""))
            if `_zv' {
                local _zp = cond(`: list o in zo_flags', "", "()")
                display as error "option `o'`_zp' not allowed"
                exit 198
            }
        }
        exit
    }
    // twoway's minimum for levels() is lev, so lev(), leve() and level()
    // are levels() on these two types (applicability_truth.json
    // level@contour rc 0); this parser reads them as level() first.
    // le() itself is no levels() to twoway: "option le() not allowed".
    mata: st_local("_zv", strofreal(st_global("s(_le_typed)") != ""))
    if `_zv' {
        display as error "option le() not allowed"
        exit 198
    }
    mata: st_local("_zv", strofreal(st_global("s(level)") != "" & st_global("s(levels)") == ""))
    if `_zv' {
        mata: st_local("_zl", st_global("s(level)"))
        sreturn local levels : copy local _zl
        sreturn local level ""
    }
    mata: st_local("_zv", strofreal(st_global("s(ccuts)") != "" & st_global("s(levels)") != ""))
    if `_zv' {
        display as error "option ccuts() cannot be combined with option levels()"
        exit 198
    }
    mata: st_local("_zc", st_global("s(ccuts)"))
    if `: length local _zc' {
        capture numlist `"`_zc'"', sort
        if _rc {
            display as error "ccuts() invalid -- invalid numlist"
            exit 121
        }
        // twoway draws at most 499 cuts: 500 or more are refused when it
        // draws, r(198) (WP-35 stat:PT-5; stat_refusal_truth.json
        // contour.ccuts_499, contour.ccuts_500).
        if `: word count `r(numlist)'' >= 500 {
            display as error "contour level must be between 0 and 500"
            exit 198
        }
        sreturn local ccuts "`r(numlist)'"
    }
    mata: st_local("_zl", strtrim(st_global("s(levels)")))
    if `: length local _zl' {
        capture confirm integer number `_zl'
        if _rc {
            display as error "option levels() incorrectly specified"
            exit 198
        }
        if `_zl' < 0 {
            display as error "invalid syntax"
            exit 198
        }
        // twoway's bound when it draws: at most 500 levels, r(198) (WP-35
        // stat:PT-5; stat_refusal_truth.json contour.levels_500,
        // contour.levels_501).
        if `_zl' > 500 {
            display as error "contour level must be between 0 and 500"
            exit 198
        }
    }
    mata: st_local("_zr", strtrim(st_global("s(crule)")))
    if `: length local _zr' {
        mata: _dash_colorrule_check(st_local("_zr"))
        // An abbreviated rule (lin) is drawn as the full one (CRA-01).
        if "`_crc'" == "" & `: length local _crf' sreturn local crule : copy local _crf
        if "`_crc'" != "" {
            if "`_crn'" == "" local _crn : copy local _zr
            mata: _dash_note("named style ", st_local("_crn"), " not found in class zyx2rule, default attributes used")
            mata: _dash_note("zyx2rule not found in scheme, default attributes used", "", "")
            exit 198
        }
    }
end

// ================================================================
// _dash_cv_drop <own> <drawn>  -- colorvar() dropped where twoway drops it
//
// WP-31 C8a.  twoway_yxview_parse.class:206-208 empties colorvar() on
// area and rarea and on every class that sets .allowcolorvar = 0 before
// it reads the variable, so on those types colorvar() and its companions
// draw nothing, are named nowhere and are never checked:
// `twoway lfit mpg weight, colorvar(nosuchvar)' is rc 0 (measured
// 14oct2026, test/fixtures/colorvar_types_truth.json, whose cv_silent this
// list equals; test_colorvar_coverage.py::TestTheAdoText pins it).  Called
// by _dash_process_segment before _dash_validate_opts with the layer's own
// type and the type it is drawn as (recast(area) is silent too); empties
// the options in s(), so the JSON writer writes none of them and the
// renderer never sees them; WP-31 C8b added the other colorvar options.
// sclass: it
// touches only those s() macros.
// ================================================================
program define _dash_cv_drop, sclass
    version 19
    args own drawn
    local cv_silent "area contour contourline fpfit fpfitci function histogram kdensity lfit lfitci lowess lpoly lpolyci mband mspline pcarrowi pci qfit qfitci rarea scatteri"
    if !`: list own in cv_silent' & !`: list drawn in cv_silent' exit
    local cv_opts "colorvar colordiscrete colorcuts colpalette colornlevels colormissing colorlevels colorvarminmax"
    local cv_opts "`cv_opts' coloruseplegend colorlist colorstart colorend colorrule colorfillonly"
    local cv_opts "`cv_opts' colorkeysrange colorkeysreverse colorallowmultiple colorotherlabel"
    foreach o of local cv_opts {
        sreturn local `o' ""
    }
end

// ================================================================
// _dash_fold_typed  -- options dash draws on some plot types only, named in
//                      the note on the others.
//
// ROADMAP WP-23 (GAPS.md F4); WP-31 C8a.
//
// WP-31 C8a: colorvar() is drawn on every type twoway colours
// (test/fixtures/colorvar_types_truth.json); on cv_silent twoway drops it
// without a word (twoway_yxview_parse.class:206-208), and so does dash --
// _dash_cv_drop empties it and its companions there before validation, as
// twoway never looks the variable up (colorvar(nosuchvar) rc 0 on lfit).
// Here, after validation, colorvar() with more than one y variable is
// refused on the types twoway refuses it on, in its words: "option
// colorvar() cannot be combined with multiple y variables in a <view>
// plot", r(198) (:231-236; the view of tsline is a line).  jitter() moves
// the markers of every type that draws one (rscatter, rcapsym, pcscatter
// and pccapsym included since C8a), so it is named nowhere.
//
// Called by _dash_process_segment AFTER _dash_validate_opts, so a value
// is refused wherever twoway refuses it (colorvar(nosuchvar) is r(111) on
// every coloured type) before it is named.  The options stay in the spec,
// as the options on the pending lists of _dash_parse_plot_opts do --
// accepted, written, reported -- and the renderer draws nothing for them
// there.  args: ptype (the type the segment is judged as), nser (its y
// variables), vtype (twoway's view type, after recast()).
// sclass: it appends to s(_pending), which the segment hands to
// _dash_report_ignored, writes an abbreviated colorrule() (lin) in full
// to s(colorrule), and touches nothing else in s().
// ================================================================
program define _dash_fold_typed, sclass
    version 19
    args ptype nser vtype
    local named ""
    if "`nser'" == "" local nser 1
    if "`vtype'" == "" local vtype "`ptype'"
    // WP-31 C8a: colorvar() with several y variables, refused as twoway
    // refuses it (colorvar_types_truth.json multi_y).  Whether it was
    // given is read by value: tested as `"`s(colorvar)'"', a value holding
    // a macro reference would be expanded (test_json_escaping.cscript
    // JSE-69).
    local cv_multi "scatter line tsline bar connected dot dropline spike"
    mata: st_local("_ft", strofreal(st_global("s(colorvar)") != ""))
    if `_ft' & `nser' > 1 & `: list vtype in cv_multi' {
        local _cv_view = cond("`vtype'" == "tsline", "line", "`vtype'")
        display as error "option colorvar() cannot be combined with multiple y variables in a `_cv_view' plot"
        exit 198
    }
    // WP-31 C8b: coloruseplegend needs colordiscrete, and colorrule() is
    // read, as twoway_yxview_parse.class:226-228 and :342-395 read them,
    // in its words (colorvar_options_truth.json R01, R02, R02b): an
    // invalid % or * part is "invalid colorrule specification"; a rule
    // twoway has no style for is two notes and r(198).  The rule is read
    // by value, in Mata.
    mata: st_local("_ft", strofreal(st_global("s(colorvar)") != "" & st_global("s(coloruseplegend)") != "" & st_global("s(colordiscrete)") == ""))
    if `_ft' {
        display as error "you must specify option colordiscrete with option coloruseplegend"
        exit 198
    }
    mata: st_local("_ft", strofreal(st_global("s(colorvar)") != ""))
    if `_ft' {
        mata: _dash_colorrule_check(st_global("s(colorrule)"))
        if "`_crc'" == "spec" {
            display as error "invalid colorrule specification"
            exit 198
        }
        if "`_crc'" == "rule" {
            mata: _dash_note("named style ", st_local("_crn"), " not found in class zyx2rule, default attributes used")
            mata: _dash_note("zyx2rule not found in scheme, default attributes used", "", "")
            exit 198
        }
        // An abbreviated rule -- lin, inte, revlinea -- is drawn as the
        // full one, as twoway's zyx2rule reads it (CRA-01).
        if `: length local _crf' sreturn local colorrule : copy local _crf
    }
    local arrow_types "pcarrow pcbarrow pcarrowi"
    // A bare sort: twoway joins a connected type's points in the data's
    // order, or in x order under sort (WP-29 P0.1); dash does the same
    // (map_line, map_area, map_rline, map_rarea and the types drawn through
    // them), so a bare sort on sort_types is drawn and not named.  On every
    // other type it is named, as it was.  sort(varlist) is named by
    // _dash_parse_plot_opts on every type.
    // WP-32: and the marker types, drawn in x order under sort
    // (_dash_sorted_copy).
    local sort_types "line connected area tsline rline rarea rconnected tsrline scatter bar spike dropline dot rbar rspike rcap rcapsym rscatter rpcap rpspike pcspike pccapsym pcarrow pcbarrow pcscatter"
    mata: st_local("_ft", strofreal(st_global("s(sort)") != ""))
    if `_ft' & !`: list ptype in sort_types' {
        mata: st_local("_ft", strofreal(strpos(" " + st_global("s(_pending)") + " ", " sort ") > 0))
        if !`_ft' local named "`named' sort"
    }
    // The fitarea options acolor(), alcolor(), alwidth() and alpattern()
    // are drawn on a ci fit -- its band in the style pstyle()
    // names, and in the scheme's ci style otherwise, as twoway draws it
    // (BUGS.md, S3, "A ci band is filled in its line's colour, where Stata
    // fills it in pstyle ci"; measured 24sep2026) -- so on lfitci, qfitci,
    // lpolyci and fpfitci they come off the list _dash_parse_plot_opts
    // named them on.  The list holds option names only, never values.
    local ci_types "lfitci qfitci lpolyci fpfitci"
    if `: list ptype in ci_types' {
        local ci_drawn "acolor alcolor alwidth alpattern"
        mata: st_local("_ftp", st_global("s(_pending)"))
        local _ftk : list _ftp - ci_drawn
        if "`_ftk'" != "`_ftp'" sreturn local _pending `"`_ftk'"'
    }
    // WP-32 (BUGS.md "The fitarea options are named on the fill, line and
    // paired types, where twoway draws them"): off the ci types twoway
    // draws acolor(), alcolor(), alwidth() and alpattern() as color(),
    // lcolor(), lwidth() and lpattern(), each over the plain option
    // whatever their order (measured 19oct2026, graph export SVG;
    // test/fixtures/noted_option_truth.json and the equivalence probes in
    // scripts/extract_noted_option_truth.do's BUGS entry).  On the fill
    // types acolor() is color(): the fill, which fcolor() still sets, and
    // the outline; on the line types and the paired types with markers it
    // is the line's colour alone, the markers keeping color().  alcolor()
    // is the line's or outline's colour over acolor().  Folded here, so
    // both renderers draw them as the plain options, read by value.
    local af_fill "area bar rarea rbar histogram"
    local af_line "spike tsrline rspike rcap rline pcspike pci dropline rconnected rcapsym rpcap rpspike pccapsym pcarrow pcbarrow pcarrowi"
    if `: list ptype in af_fill' | `: list ptype in af_line' {
        mata: st_local("_fa_ac", strofreal(st_global("s(acolor)") != ""))
        if `_fa_ac' & `: list ptype in af_fill' {
            mata: st_global("s(color)", st_global("s(acolor)"))
        }
        mata: st_local("_fa_lc", strofreal(st_global("s(alcolor)") != "" | st_global("s(acolor)") != ""))
        if `_fa_lc' {
            mata: st_global("s(lcolor)", st_global("s(alcolor)") != "" ? st_global("s(alcolor)") : st_global("s(acolor)"))
        }
        foreach _fa_p in "alwidth lwidth" "alpattern lpattern" {
            gettoken _fa_a _fa_b : _fa_p
            local _fa_b = strtrim("`_fa_b'")
            mata: st_local("_fa_g", strofreal(st_global("s(`_fa_a')") != ""))
            if `_fa_g' mata: st_global("s(`_fa_b')", st_global("s(`_fa_a')"))
        }
        local ci_drawn "acolor alcolor alwidth alpattern"
        mata: st_local("_ftp", st_global("s(_pending)"))
        local _ftk : list _ftp - ci_drawn
        if "`_ftk'" != "`_ftp'" sreturn local _pending `"`_ftk'"'
    }
    // WP-30 P1.14a (P2.12): lstyle(), alstyle() and blstyle() were named
    // on area and rarea.  WP-32: twoway strokes the outline in the named
    // line style (noted_option_truth.json), and map_area and map_rarea
    // draw it so, in the aline role: they are not named.
    // WP-30 P1.14a (P2.8): mstyle() and mlstyle() were named on the arrow
    // types.  WP-32: twoway strokes the heads in the named style
    // (noted_option_truth.json), and _arrow_head_line and _arrow_head_fill
    // draw them so: they are not named.
    // WP-31 C1: mangle(), barbsize() and headlabel draw the arrowhead and
    // its labels on the arrow types only; on every other type (pcspike,
    // pccapsym, pcscatter and pci until section 34 draws headlabel there)
    // they are named.  twoway takes any number for the two sizes
    // (measured 13oct2026: barbsize(-1), barbsize(20000), mangle(400) rc
    // 0; test/fixtures/arrowhead_truth.json refusals).  headlabel twoway
    // takes on the paired-coordinate types and rpcap and rpspike alone;
    // elsewhere it is refused before this, as twoway refuses it (WP-32,
    // _dash_tw_refuses_tab), so it is named only there.
    local _hl_named "mangle barbsize headlabel"
    if !`: list ptype in arrow_types' {
        foreach o of local _hl_named {
            mata: st_local("_ft", strofreal(st_global("s(`o')") != ""))
            if `_ft' local named "`named' `o'"
        }
    }
    // WP-31 C2: rbar draws msize() only with mwidth (twoway's rbarm view);
    // without it the size reaches a marker style nothing draws, so it is
    // named.  mwidth on histogram is drawn by twoway (bars a marker wide)
    // and named here until section 12.  twoway takes mwidth on rbar and
    // histogram only: elsewhere "option mwidth not allowed", r(198)
    // (test/fixtures/rbar_dot_truth.json probes).
    local mw_types "rbar histogram"
    mata: st_local("_ft", strofreal(st_global("s(mwidth)") != ""))
    if `_ft' & !`: list ptype in mw_types' {
        display as error "option mwidth not allowed"
        exit 198
    }
    // WP-32: map_histogram draws mwidth's bars a marker wide, upright and
    // turned, as twoway does (_hist_mwidth_px): not named.
    // WP-31 C5: baroffset() moves rbar's bars in twoway
    // (yxview__barlike_draw draw_fixed), which map_rbar does not draw
    // yet: named there.  On bar and histogram it is drawn; on area, spike,
    // dropline and dot twoway draws nothing different, so it is silent
    // (WP-31 B5b: dot's rows and markers stay where they were under
    // baroffset(.5) and baroffset(5), test/fixtures/dot_truth.json D28,
    // D29).
    // WP-32: map_rbar moves the bars as map_bar does (measured 19oct2026:
    // twoway's rbar rects stand where bar's do), so baroffset() is named on
    // rbar only beside mwidth, whose marker-wide view was not measured
    // with it.
    // WP-32: beside mwidth too, upright and turned, moved in screen units
    // (_DASH_RBO_JS): never named.
    mata: st_local("_ft", strofreal(st_global("s(msize)") != "" & st_global("s(mwidth)") == ""))
    if "`ptype'" == "rbar" & `_ft' local named "`named' msize"
    // WP-32: on contour, alpattern() and sort dash the bands' hairline
    // boundaries, as twoway draws them (_contour_parts): not named.
    if "`ptype'" == "contour" {
        local _ct_drawn "alpattern sort"
        mata: st_local("_ftp", st_global("s(_pending)"))
        local _ftk : list _ftp - _ct_drawn
        if "`_ftk'" != "`_ftp'" sreturn local _pending `"`_ftk'"'
        local named : list named - _ct_drawn
    }
    if "`named'" != "" sreturn local _pending `"`s(_pending)'`named'"'
end

// ================================================================
// _dash_hz_check <ptype> <target> <kind> <S>  -- horizontal and vertical
// refused as twoway refuses them (WP-30 P1.9a)
//
// Called by _dash_process_segment right after _dash_recast_opt, so ptype
// is the type drawn (a base, range, pc or time-series layer's recast
// target) and target the canonical recast() target of a derived layer
// (kind "derived").  Measured on StataNow 19.5
// (test/fixtures/horizontal_truth.json, scripts/extract_horizontal_truth.do):
//   * horizontal is taken by the 24 types of _hz_htypes, vertical by the
//     22 of _hz_vtypes; any other type refuses the flag, "option
//     horizontal not allowed", r(198);
//   * a derived type (_hz_derived) is refused only when it and its recast
//     target both refuse the flag;
//   * a refusing type names the first refused flag in the order typed,
//     as typed (Mata _dash_hz_order; "option vert not allowed"); then the
//     two together are "may not combine
//     options horizontal and vertical", r(198).
// The lists equal dash_render.py's _DASH_HORIZONTAL_TYPES,
// _DASH_VERTICAL_TYPES and _DASH_DERIVED_ORIENT_TYPES (test_horizontal.py).
// S names a string scalar holding the plot's option text, read by value;
// messages are constant text.  sclass:
// it reads s(horizontal) and s(vertical) and changes nothing in s().
// ================================================================
program define _dash_hz_check, sclass
    version 19
    args ptype target kind S
    local _hz_htypes area bar spike dropline dot histogram kdensity rarea rbar rspike rcap rcapsym rline rconnected rscatter rpcap rpspike pcspike pcarrow pcbarrow pcscatter pccapsym pci pcarrowi function tsrline contour contourline
    local _hz_vtypes area bar spike dropline dot histogram rarea rbar rspike rcap rcapsym rline rconnected rscatter rpcap rpspike pcspike pcarrow pcbarrow pcscatter pccapsym pci pcarrowi tsrline contour contourline
    local _hz_derived lfit qfit lfitci qfitci fpfit fpfitci lowess lpoly lpolyci mband mspline kdensity function histogram
    if `"`s(horizontal)'`s(vertical)'"' == "" exit
    mata: st_local("_hz_order", _dash_hz_order(st_strscalar("`S'")))
    if "`_hz_order'" == "" {
        if `"`s(horizontal)'"' != "" local _hz_order horizontal
        if `"`s(vertical)'"' != "" local _hz_order `_hz_order' vertical
    }
    foreach w of local _hz_order {
        local f vertical
        if substr("horizontal", 1, strlen("`w'")) == "`w'" local f horizontal
        if `"`s(`f')'"' == "" continue
        local _hz_ok 0
        if "`f'" == "horizontal" {
            if `: list ptype in _hz_htypes' local _hz_ok 1
            if "`kind'" == "derived" & `: list ptype in _hz_derived' & `: list target in _hz_htypes' local _hz_ok 1
        }
        else {
            if `: list ptype in _hz_vtypes' local _hz_ok 1
            if "`kind'" == "derived" & `: list ptype in _hz_derived' & `: list target in _hz_vtypes' local _hz_ok 1
        }
        if !`_hz_ok' {
            display as error "option `w' not allowed"
            exit 198
        }
    }
    if `"`s(horizontal)'"' != "" & `"`s(vertical)'"' != "" {
        display as error "may not combine options horizontal and vertical"
        exit 198
    }
end

// _dash_subopt_colour_check -- a colour written with commas inside a
// structured option's colour sub-option is refused as twoway refuses it,
// "invalid '2'" for title("T", color("1,2,3")), r(198), on the eleven
// options measured (WP-31 E5, test/fixtures/colour_width_edges_truth.json
// sc.*).  Reads s(g_<host>) by value through Mata
// _dash_subopt_colour_comma, which compares the text and never runs it;
// the words are echoed through _dash_say.  Called by _dash_validate_opts.
program define _dash_subopt_colour_check
    version 19
    foreach _h in title subtitle note caption xline yline xlabel ylabel plotregion graphregion legend {
        mata: st_local("_sc", _dash_subopt_colour_comma(st_global("s(g_" + st_local("_h") + ")")))
        if `"`macval(_sc)'"' != "" {
            mata: _dash_say("err", "", st_local("_sc"), "")
            exit 198
        }
    }
end

// _dash_stylelist_check ptype nser -- a stylelist held to twoway's rules
// before any options object is written (WP-30 P1.1a).  First a .. or ...
// that is not the last element is refused in twoway's words,
// "mcolor(red .. blue):  invalid syntax", r(198), the value echoed as
// stored.  Then a quoted blank element a y uses, mcolor(" " blue), is
// refused in dash's own words (Q-11.1, ratified 06oct2026); twoway
// refuses it too, naming an internal class path.  Then each element a y
// uses is held to the option's rule as a single value is; an element
// past the last y is not checked, as twoway does not check it.  nser is
// the number of y (1 on a single-y type).  Values are read by value.
program define _dash_stylelist_check
    version 19
    args ptype nser
    mata: st_local("_sl_keys", _dash_stylelist_keys())
    // A value twoway's string cannot bind is refused first, as
    // _dash_refuse_unbound refuses it on the other options: these keys are
    // string asis, which binds msize(x"' _dup(3) "INJ" `") where twoway
    // refuses it, "type mismatch", r(109) (test_adversarial P20-18b).  Only
    // a value holding a double quote can fail to bind.  Read by value; the
    // value reaches the probe's command line only through macval().
    foreach key of local _sl_keys {
        mata: st_local("_sl_v", st_global("s(" + st_local("key") + ")"))
        mata: st_local("_sl_q", strofreal(strpos(st_local("_sl_v"), char(34)) > 0))
        if !`_sl_q' continue
        capture _dash_stylelist_bind , v(`macval(_sl_v)')
        if !_rc continue
        if _rc == 1 exit 1
        mata: st_local("_sl_rc", strpos(st_local("_sl_v"), char(34) + char(39)) ? "109" : "198")
        local why = cond(`_sl_rc' == 109, "type mismatch", "parentheses do not balance")
        mata: _dash_say("err", "dash: option ", st_local("key"), ///
            "() has a value Stata cannot read, as twoway reads it: " + st_local("why") + ".")
        exit `_sl_rc'
    }
    foreach key of local _sl_keys {
        mata: st_local("_sl_bad", strofreal(_dash_stylelist_bad(st_global("s(" + st_local("key") + ")"))))
        if `_sl_bad' {
            mata: _dash_say("err", st_local("key") + "(", st_global("s(" + st_local("key") + ")"), "):  invalid syntax")
            exit 198
        }
    }
    // An element opening with "(" is read by twoway as an option and
    // refused, "option(s) ( red ) not allowed"; one led by a glued "="
    // is refused with a class path (WP-31 E4, measured 16oct2026).
    foreach key of local _sl_keys {
        mata: st_local("_sl_p", _dash_stylelist_paren(st_global("s(" + st_local("key") + ")")))
        if `"`macval(_sl_p)'"' != "" {
            mata: _dash_say("err", "option(s) ", st_local("_sl_p"), " not allowed")
            exit 198
        }
        mata: st_local("_sl_e", _dash_stylelist_eqlead(st_global("s(" + st_local("key") + ")")))
        if `"`macval(_sl_e)'"' != "" {
            mata: _dash_say("err", "dash: " + st_local("key") + "() element ", st_local("_sl_e"), " is no style; twoway refuses it too (invalid name)")
            exit 198
        }
    }
    foreach key of local _sl_keys {
        mata: st_local("_sl_j", strofreal(_dash_stylelist_blank(st_global("s(" + st_local("key") + ")"), `nser')))
        if `_sl_j' {
            mata: _dash_say("err", "dash: " + st_local("key") + "() element " + st_local("_sl_j") + " is blank; use . for the default (got: ", st_global("s(" + st_local("key") + ")"), ")")
            exit 198
        }
    }
    _dash_option_rules
    local typed ""
    foreach tok of local _dash_rules_plot {
        local at = strpos("`tok'", "@")
        if `at' {
            local types = substr("`tok'", `at' + 1, .)
            local types : subinstr local types "|" " ", all
            local o = substr("`tok'", 1, strpos("`tok'", "=") - 1)
            if `: list ptype in types' local typed "`typed' `o'"
        }
    }
    foreach tok of local _dash_rules_plot {
        local body "`tok'"
        local at = strpos("`tok'", "@")
        if `at' {
            local body  = substr("`tok'", 1, `at' - 1)
            local types = substr("`tok'", `at' + 1, .)
            local types : subinstr local types "|" " ", all
            if !`: list ptype in types' continue
        }
        local eq   = strpos("`body'", "=")
        local o    = substr("`body'", 1, `eq' - 1)
        local spec = substr("`body'", `eq' + 1, .)
        if !`at' & `: list o in typed' continue
        if !`: list o in _sl_keys' continue
        forvalues i = 1/`nser' {
            mata: st_local("e", _dash_stylelist_pick(st_global("s(" + st_local("o") + ")"), `i'))
            if !`: length local e' continue
            _dash_validate_value "dash" "`o'" "`spec'" `"`macval(e)'"' "`ptype'"
        }
    }
end

// _dash_stylelist_bind , v(<value>) -- rc 0 when -syntax-'s string binds
// <value>, as twoway's declaration of a style option binds it.
program define _dash_stylelist_bind
    version 19
    syntax , V(string)
end

// ================================================================
// _dash_sort_names  -- sort()'s names checked as twoway checks them
//
// twoway reads sort(varlist) with -syntax-'s namelist
// (twoway_yxview_parse.class:187), on every plot type: a malformed name
// is refused with one line naming the first bad character or token --
// "* invalid name" for sort(x*), "( invalid name" for sort(z(1)) -- and
// r(198) (measured on all forty types, WP-29 P0.1).  -confirm names- and
// -syntax, sort(varlist)- answer otherwise.  Called by _dash_sort_opt
// with the value by value; prints twoway's line itself.
// ================================================================
program define _dash_sort_names
    version 19
    syntax [, SORT1(namelist)]
end

// ================================================================
// _dash_sort_opt <ptype>  -- sort(varlist) as twoway reads it
//
// Called by _dash_process_segment after _dash_opts_repeats has reduced
// the list to the copies twoway reads -- of several sort() copies the
// rightmost one that is not empty -- and after _dash_fold_typed.
// Measured on StataNow 19.5 (WP-29 P0.1):
//   * a malformed name is refused on every type (_dash_sort_names);
//   * on the 23 types that draw a serset, each name must be a variable:
//     unab's line, or "<word> is invalid variable name" for if, in, using
//     and with, then "option sort() incorrectly specified", r(198); and
//     at most ten names, _all counting every variable and two of twoway's
//     own: "too many variables specified", the same second line, r(198);
//   * on the other 17 types sort() is not read, rc 0.
// On line, connected, area, rline, rarea and rconnected it is honoured:
// s(sortvars) holds the names unab gave, single-spaced, which the plot's
// JSON carries as "sortvars"; dash.ado makes their rank in Stata at export
// (_dash_sort_gen).  On those six and on tsline and tsrline (which join in
// time order whatever is given) sort comes off the pending list
// _dash_parse_plot_opts named it on; elsewhere it stays named.  The value
// is read by value and reaches a command line only through macval(); the
// only echo of the user's text goes through _dash_say.  sclass: it sets
// s(sortvars) and s(_pending) and touches nothing else in s().
// ================================================================
program define _dash_sort_opt, sclass
    version 19
    args ptype
    mata: st_local("_so_e", strofreal(strtrim(st_global("s(sort1)")) == ""))
    if `_so_e' exit
    mata: st_local("_so_v", st_global("s(sort1)"))
    capture noisily _dash_sort_names , sort1(`macval(_so_v)')
    if _rc exit 198
    local _so_six "line connected area rline rarea rconnected"
    // WP-32: the marker types twoway draws in sort(varlist)'s order, as
    // the renderers draw them (_dash_sorted_copy): their rank is written
    // and sort comes off the pending list, as on the six.
    local _so_ord "scatter bar spike dropline dot rbar rspike rcap rcapsym rscatter rpcap rpspike pcspike pccapsym pcarrow pcbarrow pcscatter"
    local _so_six `_so_six' `_so_ord'
    local _so_ts "tsline tsrline"
    local _so_ser "scatter line connected area bar spike dropline dot rarea rbar rspike rcap rcapsym rscatter rline rconnected rpcap rpspike pcspike pcarrow pcbarrow pcscatter pccapsym mband mspline"
    if `: list ptype in _so_ser' {
        // Every token is a name now (namelist), so tokens() splits it
        // whole and each reaches unab as a name.
        mata: st_local("_so_nt", strofreal(cols(tokens(st_local("_so_v")))))
        local _so_out ""
        local _so_cnt = 0
        forvalues _so_i = 1/`_so_nt' {
            mata: st_local("_so_t", tokens(st_local("_so_v"))[`_so_i'])
            if inlist("`_so_t'", "if", "in", "using", "with") {
                mata: _dash_say("err", "", st_local("_so_t"), " is invalid variable name")
                display as error "option sort() incorrectly specified"
                exit 198
            }
            if "`_so_t'" == "_all" {
                unab _so_u : _all
                local _so_cnt = `_so_cnt' + c(k) + 2
            }
            else {
                capture noisily unab _so_u : `_so_t', max(1)
                if _rc {
                    display as error "option sort() incorrectly specified"
                    exit 198
                }
                local ++_so_cnt
            }
            local _so_out `_so_out' `_so_u'
        }
        if `_so_cnt' > 10 {
            display as error "too many variables specified"
            display as error "option sort() incorrectly specified"
            exit 198
        }
        if `: list ptype in _so_six' sreturn local sortvars "`: list retokenize _so_out'"
    }
    if `: list ptype in _so_six' | `: list ptype in _so_ts' {
        mata: st_local("_so_p", st_global("s(_pending)"))
        local _so_rm "sort"
        if `: list _so_rm in _so_p' {
            local _so_k : list _so_p - _so_rm
            sreturn local _pending `"`_so_k'"'
        }
    }
end

// ================================================================
// _dash_recast_opt <ptype>  -- recast(), recastas() and type() as twoway
// reads them (WP-30 P1.8b)
//
// Called by _dash_process_segment right after _dash_opts_repeats (which
// kept the rightmost copy of each) and before _dash_connect_opt, as
// twoway sets the view type before its connect override
// (twoway_yxview_parse.class:320-324, :1080).  Measured on StataNow 19.5
// (test/fixtures/recast_truth.json, scripts/extract_recast_truth.do):
//   * recast() and recastas() (one option, minimum recast) beat type()
//     in either order; rec(), reca() and recas() are "option rec() not
//     allowed", r(198), naming the spelling typed;
//   * lfitci, qfitci, lpolyci and fpfitci refuse them: "recastas() option
//     not allowed" or "type() option not allowed", r(198);
//   * dot ignores them in silence;
//   * the value is one name for every y; one distinct word repeated is
//     that word, any other multi-word value an unknown name;
//   * the name is read by the source's class (Stata's style/
//     *type-*.style): yxtype, y2xtype (the yx eight and the range types),
//     yxyxtype (the pc types) and functiontype (the yx eight and
//     function), each with twoway's spellings, case-sensitive; a name not
//     in the class prints twoway's two notes and falls back -- yxtype to
//     scatter, y2xtype to rspike, yxyxtype to pcspike, functiontype to
//     function's own line.
// Returns s(_recast_type) (the type drawn: the target for a base, range,
// pc or time-series source, the typed type for a derived one),
// s(_recast_target) (the canonical target, empty when there is none) and
// s(_recast_kind): base, range2yx (a range source drawn as a yx type: its
// first bound), ts, derived, literal (pci and pcarrowi drawn as the pc
// type named, WP-31 C7) or empty; a range target or the fallback on
// histogram is derived.  The value is read by value; echoes go through
// _dash_say and _dash_note.
// ================================================================
program define _dash_recast_opt, sclass
    version 19
    args ptype
    sreturn local _recast_type "`ptype'"
    sreturn local _recast_target ""
    sreturn local _recast_kind ""
    sreturn local _recast_ts ""
    mata: st_local("_rc_bad", ustrregexm(" " + st_global("s(_unknown)"), "[ ,](rec|reca|recas)\(") ? ustrregexs(1) : "")
    if "`_rc_bad'" != "" {
        mata: _dash_say("err", "option ", st_local("_rc_bad"), "() not allowed")
        exit 198
    }
    mata: st_local("_rc_r", strtrim(st_global("s(recast)")))
    mata: st_local("_rc_t", strtrim(st_global("s(type)")))
    local _rc_word "recast"
    if `: length local _rc_r' == 0 {
        local _rc_r : copy local _rc_t
        local _rc_word "type"
    }
    sreturn local recast ""
    sreturn local type ""
    if `: length local _rc_r' == 0 exit
    local _rc_ci "lfitci qfitci lpolyci fpfitci"
    if `: list ptype in _rc_ci' {
        if "`_rc_word'" == "recast" display as error "recastas() option not allowed"
        else display as error "type() option not allowed"
        exit 198
    }
    // WP-31 B5a: twoway reads recast() on dot and draws the dot graph
    // unchanged (twoway dot mpg weight, recast(line) and recast(scatter):
    // rc 0, the same SVG; test/fixtures/rbar_dot_truth.json probes), so
    // it is named in the note, not dropped in silence.
    if "`ptype'" == "dot" {
        _dash_recast_named `_rc_word'
        exit
    }
    // One value for every y: one distinct word, else an unknown name.
    mata: st_local("_rc_v", length(uniqrows(tokens(st_local("_rc_r"))')) == 1 ? tokens(st_local("_rc_r"))[1] : st_local("_rc_r"))
    local _yx      "scatter line connected area bar spike dropline dot"
    local _rng     "rarea rbar rspike rcap rline rconnected rcapsym rscatter tsrline"
    local _pc      "pcspike pccapsym pcarrow pcbarrow pcscatter"
    // rpcap and rpspike are y3xview sources (WP-31 B1): recast() on them
    // finds rpcap or rpspike, else twoway's notes and rpspike
    // (rangept_truth.json recast.*: recast(rspike), (scatter) and (rcap)
    // draw rpspike).
    local _rpt     "rpcap rpspike"
    local _derived "lfit qfit lowess lpoly fpfit mspline mband kdensity function histogram scatteri"
    // pci and pcarrowi are yxyxview sources (twoway_pci_parse.class): the
    // pc names, drawn by the literal mapper (WP-31 C7).
    local _rc_lit "pci pcarrowi"
    if `: list ptype in _pc' local _rc_class yxyxtype
    else if `: list ptype in _rpt' local _rc_class y3xtype
    else if `: list ptype in _rc_lit' local _rc_class yxyxtype
    else if "`ptype'" == "function" local _rc_class functiontype
    else if `: list ptype in _rng' | "`ptype'" == "histogram" local _rc_class y2xtype
    else local _rc_class yxtype
    // name:minimum length, by class (twoway's spellings, measured).
    local _sp_yx "scatter:2 line:2 connected:2 bar:1 area:4 spike:5 dropline:8 dot:3"
    local _sp_rng "rscatter:3 rline:3 rconnected:3 rarea:5 rbar:4 rcap:4 rcapsym:7 rspike:6"
    local _sp_pc "pcarrow:4 pcbarrow:5 pcline:3 pcspike:4 pccapsym:6 pcscatter:4"
    if "`_rc_class'" == "yxyxtype" local _sp "`_sp_pc'"
    else if "`_rc_class'" == "y3xtype" local _sp "rpcap:5 rpspike:7"
    else if "`_rc_class'" == "y2xtype" local _sp "`_sp_yx' `_sp_rng'"
    else if "`_rc_class'" == "functiontype" local _sp "`_sp_yx' function:8"
    else local _sp "`_sp_yx'"
    local _rc_name ""
    mata: st_local("_rb", strofreal(st_local("_rc_v") == "rbarm"))
    if `_rb' & "`_rc_class'" == "y2xtype" local _rc_name rbar
    foreach _e of local _sp {
        if "`_rc_name'" != "" continue, break
        gettoken _n _m : _e, parse(":")
        local _m = substr("`_m'", 2, .)
        mata: st_local("_hit", strofreal(strlen(st_local("_rc_v")) >= `_m' & st_local("_rc_v") == substr("`_n'", 1, strlen(st_local("_rc_v")))))
        if `_hit' local _rc_name "`_n'"
    }
    // pcline is a name of the class's spellings that is not in the class.
    if "`_rc_name'" == "pcline" {
        local _rc_v pcline
        local _rc_name ""
    }
    if "`_rc_name'" == "" {
        mata: _dash_note("named style ", st_local("_rc_v"), " not found in class `_rc_class', default attributes used")
        mata: _dash_note("`_rc_class' not found in scheme, default attributes used", "", "")
        if "`_rc_class'" == "yxtype" local _rc_name scatter
        else if "`_rc_class'" == "y2xtype" local _rc_name rspike
        else if "`_rc_class'" == "yxyxtype" local _rc_name pcspike
        else if "`_rc_class'" == "y3xtype" local _rc_name rpspike
        else exit
    }
    // pci and pcarrowi keep their type; the literal mapper draws the
    // target (area_cmissing_truth.json P01-P05).
    if `: list ptype in _rc_lit' {
        if "`_rc_name'" == "pcspike" & "`ptype'" == "pci" exit
        sreturn local _recast_target "`_rc_name'"
        sreturn local _recast_kind literal
        exit
    }
    if `: list ptype in _derived' {
        if "`_rc_name'" == "function" exit
        // histogram drawn as a range type is drawn, its bins as the range
        // (WP-31 C7; area_cmissing_truth.json H01-H12).
        sreturn local _recast_target "`_rc_name'"
        sreturn local _recast_kind derived
        exit
    }
    if "`_rc_name'" == "`ptype'" exit
    sreturn local _recast_target "`_rc_name'"
    sreturn local _recast_type "`_rc_name'"
    local _ts "tsline tsrline"
    if `: list ptype in _ts' {
        sreturn local _recast_kind ts
    }
    else sreturn local _recast_kind base
    if `: list ptype in _rng' & `: list _rc_name in _yx' {
        sreturn local _recast_kind range2yx
        if "`ptype'" == "tsrline" sreturn local _recast_ts 1
    }
end

// _dash_recast_s <key> <value>: sets s(<key>) for _dash_process_segment,
// an rclass program (WP-30 P1.8b).  <key> is recast or sort1, <value> a
// type or variable name dash wrote, never the user's text.
program define _dash_recast_s, sclass
    version 19
    args key value
    sreturn local `key' "`value'"
end

// _dash_recast_named <word>: recast() (or type()) named as an option dash
// does not draw on this plot (WP-30 P1.8b): dot, which twoway draws
// unchanged (WP-31 B5a).
program define _dash_recast_named, sclass
    version 19
    args word
    mata: st_local("_rn_p", st_global("s(_pending)"))
    sreturn local _pending `"`_rn_p' `word'"'
end

// ================================================================
// _dash_connect_opt <ptype> <nser>  -- connect() and cmissing() as twoway
// reads them (WP-30 P1.8a)
//
// Called by _dash_process_segment right after _dash_opts_repeats, which
// has kept the rightmost copy of each (cmissings() is a copy of
// cmissing()).  Measured on StataNow 19.5 (test/fixtures/
// connect_truth.json, scripts/extract_connect_truth.do):
//   * a .. or ... that is not the last element is refused,
//     "connect(l .. J):  invalid syntax", "cmissings(n .. y):  invalid
//     syntax", r(198) (probes R-01, R-02);
//   * each element the y use is read by twoway's connectstyle and yesno
//     names (_dash_connect_canon; S block); an element past the last y is
//     not read (R_EXTRA);
//   * an unknown connect() name prints "(note:  named style <e> not found
//     in class connectstyle, default attributes used)" once per y and
//     draws direct (P07, C_BOGUS2);
//   * an unknown cmissing() element prints two notes, then on the types
//     that draw a connecting line (cm_refuse, matrix cmissing(x) rc 101)
//     " not allowed", r(101), and elsewhere draws the default.
// It writes s(connect) and s(cmissing) back as blank-separated canonical
// lists ("." for an empty element), so the per-y writer gives each y its
// own value; on scatter s(_cn_types) holds connected for a y given a
// connect() element, else scatter, and s(_cn_any) 1 when any is.  It takes
// connect and cmissing off s(_pending) on every type: dash draws both
// wherever twoway does (WP-31 C6; test/fixtures/area_cmissing_truth.json).
// Values are read by value; echoes go through _dash_say and _dash_note.
// ================================================================
program define _dash_connect_opt, sclass
    version 19
    args ptype nser
    sreturn local _cn_types ""
    sreturn local _cn_any ""
    mata: st_local("_cn_c", st_global("s(connect)"))
    mata: st_local("_cn_m", st_global("s(cmissing)"))
    if !`: length local _cn_c' & !`: length local _cn_m' exit
    local cm_refuse "line connected lfit qfit fpfit lpoly lowess mspline mband kdensity function tsline lfitci qfitci lpolyci fpfitci rline rconnected tsrline"
    if "`nser'" == "" local nser 1
    foreach kind in connect cmissing {
        mata: st_local("_cn_bad", strofreal(_dash_stylelist_bad(st_global("s(`kind')"))))
        if `_cn_bad' {
            local _cn_w "`kind'"
            if "`kind'" == "cmissing" local _cn_w "cmissings"
            mata: _dash_say("err", "`_cn_w'(", st_global("s(`kind')"), "):  invalid syntax")
            exit 198
        }
    }
    local _cn_out ""
    local _cn_types ""
    local _cn_any 0
    if `: length local _cn_c' {
        forvalues i = 1/`nser' {
            mata: st_local("e", _dash_stylelist_pick(st_global("s(connect)"), `i'))
            mata: st_local("v", _dash_connect_canon("connect", st_local("e")))
            if "`v'" == "?" {
                mata: _dash_note("named style ", st_local("e"), " not found in class connectstyle, default attributes used")
                local v direct
            }
            if "`v'" == "" {
                local _cn_out "`_cn_out' ."
                local _cn_types "`_cn_types' scatter"
            }
            else {
                local _cn_out "`_cn_out' `v'"
                local _cn_types "`_cn_types' connected"
                local _cn_any 1
            }
        }
        sreturn local connect "`: list retokenize _cn_out'"
    }
    local _mn_out ""
    if `: length local _cn_m' {
        forvalues i = 1/`nser' {
            mata: st_local("e", _dash_stylelist_pick(st_global("s(cmissing)"), `i'))
            mata: st_local("v", _dash_connect_canon("cmissing", st_local("e")))
            if "`v'" == "?" {
                mata: _dash_note("named style ", st_local("e"), " not found in class yesno, default attributes used")
                mata: _dash_note("yesno not found in scheme, default attributes used", "", "")
                if `: list ptype in cm_refuse' | ("`ptype'" == "scatter" & `_cn_any') {
                    display as error " not allowed"
                    exit 101
                }
                local v ""
            }
            if "`v'" == "" local v "."
            local _mn_out "`_mn_out' `v'"
        }
        sreturn local cmissing "`: list retokenize _mn_out'"
    }
    if "`ptype'" == "scatter" {
        sreturn local _cn_types "`: list retokenize _cn_types'"
        sreturn local _cn_any "`_cn_any'"
    }
    // WP-31 C6: cmissing(n) is drawn on every type (area and rarea split
    // the fill; the estimators break their line at their own missing
    // points) and connect() on rarea, so neither is ever named.
    mata: st_local("_cn_p", st_global("s(_pending)"))
    local _cn_rm "connect cmissing"
    local _cn_k : list _cn_p - _cn_rm
    sreturn local _pending `"`_cn_k'"'
end

// ================================================================
// _dash_subopt_check kind -- twoway's refusals of the sub-options of
// legend() (kind legend), zlabel() (zlabel) and the titles (title), WP-30
// P1.19.  Mata's _dash_subreq_check reads the recorded options with
// twoway's own tables and refuses what twoway refuses, r(198), in its
// words; a cols()/rows()/holes() value it hands back (-1) is put to
// -numlist- as twoway's ParseLogOpts declares it -- integer >0, one
// number (or at most 300 for holes()) -- and a failure is refused with
// twoway's return code and words, "cols() invalid -- invalid number".  A
// value holding a backtick, $, a quote, a backslash or a control byte is
// never put to -numlist- (r(121)).  Each pass accepts one value, so the
// loop ends.  Messages go through _dash_say, never through a macro.
// ================================================================
program define _dash_subopt_check
    version 19
    args kind
    local _so_rc -1
    while `_so_rc' == -1 {
        mata: st_local("_so_rc", strofreal(_dash_subreq_check(st_local("kind"))))
        if `_so_rc' != -1 continue, break
        mata: st_local("_so_bad", strofreal(_dash_so_unsafe(st_local("_so_value"))))
        local _nlrc 121
        if !`_so_bad' {
            if "`_so_kind'" == "N1" {
                capture numlist `"`macval(_so_value)'"', integer range(>0) min(0) max(1)
            }
            else {
                capture numlist `"`macval(_so_value)'"', integer range(>0) max(300)
            }
            local _nlrc = _rc
        }
        if `_nlrc' {
            local _t "invalid numlist"
            if "`_so_kind'" == "N1" {
                if `_nlrc' == 121 local _t "invalid number"
                if `_nlrc' == 123 local _t "single number required"
                if `_nlrc' == 125 local _t "invalid number, outside of allowed range"
                if `_nlrc' == 126 local _t "invalid number, noninteger value"
                if `_nlrc' == 127 local _t "invalid number, missing not allowed"
            }
            else {
                if `_nlrc' == 123 local _t "invalid numlist has too many elements"
                if `_nlrc' == 125 local _t "invalid numlist has elements outside of allowed range"
                if `_nlrc' == 126 local _t "invalid numlist has noninteger elements"
                if `_nlrc' == 127 local _t "invalid numlist has missing values"
            }
            mata: _dash_say("err", st_local("_so_name"), "", "() invalid -- " + st_local("_t"))
            mata: _dash_axreq_clear()
            exit `_nlrc'
        }
        mata: _dash_subreq_accept()
    }
    if `_so_rc' exit `_so_rc'
end

// ================================================================
// _dash_check_legend  -- legend(top), legend(bottom), legend(left) and
//                        legend(right), refused as twoway refuses them.
//
// ROADMAP WP-23 (GAPS.md F4).  twoway has no such keywords: measured
// 23sep2026, `twoway (scatter mpg weight) (lfit mpg weight), legend(top)'
// is "option top not allowed", r(198), and so are bottom, left and right,
// alone or beside another sub-option.  dash.sthlp documented all four and
// the renderer drew them INSIDE the plot (top_center ...), where twoway
// draws nothing; it found the word anywhere in the text, so
// legend(label(1 "left")) moved the legend as well.  They are refused
// here, with twoway's message and the position() that says what was
// meant.
//
// The contents are read one sub-option at a time by -gettoken-, with
// bind (a parenthesised argument is part of its option) and quotes (a
// quoted word stays quoted), so a word inside a quoted label or inside
// another sub-option's parentheses is never taken for the keyword: only a
// bare top-level word is.  -syntax- read them once, and gave up -- rc 0,
// nothing refused -- on a legend() of three thousand words; -gettoken-
// reads that in 0.06 seconds.  The values are only ever expanded through
// macval(), so a backtick in a label cannot become a macro reference.
// Not sclass: it is called from _dash_validate_opts and must not touch s().
// ================================================================
program define _dash_check_legend
    version 19
    // The argument is read by value (_dash_text_args), and neither the text
    // nor a token is put inside quotes in a test: -args- and the tests cut
    // legend(label(1 "'90s") top) at its "', and the top beside it, which
    // twoway refuses, went through with rc 0 (measured 24sep2026;
    // test_json_escaping.cscript JSE-47).  A token is one of the four
    // keywords only when Mata says it is.
    mata: _dash_text_args(0, 0, 0)
    local legval : copy local _dash_txt
    // A word twoway cannot read before the keyword is refused first, as
    // twoway reads them left to right: legend(po(9) top) is "option po()
    // not allowed" (WP-31 D16; tabs_legend_edges_truth.json legend.*).
    mata: st_local("_lgm", _dash_legend_first_refusal(st_local("legval")))
    if `: length local _lgm' {
        mata: _dash_say("err", "", st_local("_lgm"), "")
        exit 198
    }
    local rest `"`macval(legval)'"'
    while `: length local rest' {
        gettoken tok rest : rest, bind quotes
        mata: st_local("_kwhit", anyof(("top", "bottom", "left", "right"), st_local("tok")) ? st_local("tok") : "")
        foreach kw in `_kwhit' {
            if "`kw'" == "top"    local _clk "12"
            if "`kw'" == "top"    local _where "above"
            if "`kw'" == "bottom" local _clk "6"
            if "`kw'" == "bottom" local _where "below"
            if "`kw'" == "left"   local _clk "9"
            if "`kw'" == "left"   local _where "to the left of"
            if "`kw'" == "right"  local _clk "3"
            if "`kw'" == "right"  local _where "to the right of"
            display as error "option `kw' not allowed"
            display as error "      twoway's legend() has no `kw'; legend(position(`_clk')) places the legend `_where' the plot."
            exit 198
        }
    }
end

// BEGIN shipped schemes (WP-17)
// ================================================================
// The one list of what dash can draw by name.
//
// `_dash_schemes' are the twenty-six scheme translations the package ships as
// dash-<name>.scheme -- dash_render.py's SchemeParser._BUILTIN_NAMES is the same
// list, and test/test_scheme_resolution.py holds the two together --
// and `_dash_themes' are the theme() aliases the renderer maps onto them.
// _dash_validate_value reads both for the `scheme' kind and
// _dash_prepare_spec for theme().  Any other scheme -- PLUS/s, PERSONAL,
// SITE, the working directory, a directory added with adopath -- is not
// listed here: it is found along the ado-path as Stata finds it (WP-30
// P1.25b; _dash_scheme_dirs below).
// ================================================================
program define _dash_shipped_schemes
    version 19
    c_local _dash_schemes "economist s1color s1manual s1mono s1rcolor s2color s2color8 s2gcolor s2gmanual s2manual s2mono sj stcolor stcolor_alt stgcolor stgcolor_alt stmono1 stmono2 stsj sttrans meta stcolor_meta stcolor_mv stcoloralias stgcolor_meta stgcolor_mv"
    c_local _dash_themes  "default clean mono dark economist sj"
end
// END shipped schemes (WP-17)

// ----------------------------------------------------------------
// _dash_scheme_dirs -- the ado-path a scheme dash does not ship is looked
// for along (WP-30 P1.25b, M7).  Stata's setscheme runs findfile
// scheme-NAME.scheme and then findfile NAME.scheme (BASE/s/scheme.class:
// 172-173); Mata's _dash_scheme_dirs_json() writes the directories findfile
// walks as a JSON array into the caller's _dash_sdirs, for the spec's
// build_options.scheme_dirs.  The text is passed by value and expanded
// only through macval(), so no directory name is expanded again as a
// macro.
// ----------------------------------------------------------------
program define _dash_scheme_dirs
    version 19
    mata: st_local("j", _dash_scheme_dirs_json())
    c_local _dash_sdirs `"`macval(j)'"'
end

// BEGIN option-validation table (WP-15)
// ================================================================
// Option-value validation.
//
// Principle: dash refuses a value where twoway refuses it, refuses a
// non-number where a number-only option got a word twoway would silently
// ignore, and -- like twoway's own "(note: named style X not found in
// class Y, default attributes used)" -- reports and falls back on the
// scheme where a STYLE NAME (symbol, size, line width, pattern, angle,
// clock position, intensity) is unknown; an unknown colour is drawn black
// with the note, as twoway draws it (WP-30 P1.13a).  Every bound below was
// measured against twoway (22sep2026, StataNow 19.5).  Four bounds are
// dash's own rather than twoway's AND say so in a second sentence of the
// refusal (yaxis/xaxis take twoway's 1..9 since WP-31 C10c): degree 0..7, bin 1..1000, n 2..10000 (mspline's
// n 1..300 and bands 1..200 are twoway's) and the lowess bwidth (0,1].  The other dash-own bounds -- colornlevels 2..256,
// jitter 0..100, level strictly inside 0..100, barwidth > 0, aspectratio
// >= 0, jitterseed()/jseed() >= 0, kdensity bwidth > 0 -- are refused with
// the one sentence only.
//
// Token grammar: option=kind[,p1[,p2[,p3]]][@type1|type2].  Tokens are
// whitespace-separated.  A token with @ applies only to the plot types it
// names; a token without @ applies to every type that has no @ token for
// the same option.  Kinds -- num: a finite number, p1/p2 inclusive bounds
// (either may be empty), p3 = x makes both exclusive; int: an integer,
// p1/p2 bounds; axes (WP-31 C10b): yaxis()/xaxis(), a numlist of axis
// numbers as twoway reads it (integers 1 to 9, twoway's codes and lines
// outside them), each at most p2, normalised to the sorted distinct list
// (2 1 -> 1 2, 1 1 -> 1); pos: a number > 0, p1 an inclusive ceiling; style: a name
// passes untouched, a number must lie in [p1,p2] where bounds are given
// (mlabposition and fintensity have none: twoway accepts 13, 2.5, 150 and
// -5 with a note or silently, and the renderer notes 13 and draws 150 and
// -5 as twoway draws them), and a
// token that looks numeric but overflows real() (1e400) is refused, not
// passed as a name; istyle: a name, or an integer in [p1,p2] (no token
// uses it today); enum: one of the |-separated words, case-insensitive,
// normalised to lower case; numlist: a Stata numlist of between p1 and p2
// numbers (p2 empty = no ceiling), normalised to the expanded,
// blank-separated list (1(1)5 -> 1 2 3 4 5; 0,10 -> 0 10); var: exactly
// one existing variable, abbreviations expanded (unab) and normalised to
// the full name, a time-series expression (L.price on tsset data)
// refused, since dash cannot draw one; varlist: one or more, likewise;
// byvarlist: the text before the first top-level comma is a varlist, the
// rest is kept verbatim; format: a numeric display format (the gate is
// spelled out in _dash_validate_value); scheme (WP-17, WP-30 P1.25b): a
// shipped scheme or theme name from _dash_shipped_schemes,
// case-insensitive (a shipped name may carry the .scheme extension), or a
// scheme Stata finds along the ado-path, scheme-NAME.scheme or
// NAME.scheme -- named, never a path: no blank, control character, `/',
// `\', `:', `..', quote, backtick or dollar sign -- passed through as
// written.  A number that passes a num, int
// or pos rule reaches the renderer in one canonical spelling: an int as
// %21.0f (2.0, 02, +2 and 1E3 -> 2, 2, 2, 1000); a num or pos as written
// when it is a plain decimal or e-notation Python parses, else as %21.0g
// (1d3 -> 1000).  Tabs around a value are trimmed before it is read.
//
// test/test_option_validation.py reads this table out of dash.ado and
// test/test_option_validation.cscript exercises every token against Stata.
// `,u' reads the value in Stata's line-width units (WP-30 P1.12b).
// colour (WP-30 P1.13a): the kind refuses only a comma-written colour,
// as twoway does (invalid '<word>', r(198)); everything else in a colour
// is the renderer's, which draws an unknown colour black with the note,
// as twoway draws it.
// ================================================================
program define _dash_option_rules
    version 19
    // Plot rules: validated once per segment, after _dash_fold_bw, from s().
    local plot ///
        msize=style  mlabsize=style  mlabgap=style ///
        lwidth=style,0,10000,u@area|bar|connected|contour|dropline|fpfit|fpfitci|function|histogram|kdensity|lfit|lfitci|line|lowess|lpoly|lpolyci|mband|mspline|pcarrow|pcarrowi|pcbarrow|pccapsym|pci|pcscatter|pcspike|qfit|qfitci|rarea|rbar|rcap|rcapsym|rconnected|rline|rpcap|rpspike|rspike|spike|tsline|tsrline  lwidth=style ///
        mlwidth=style,0,10000,u@connected|contour|dot|dropline|pcarrow|pcarrowi|pcbarrow|pccapsym|pcscatter|rcapsym|rconnected|rpcap|rpspike|rscatter|scatter|scatteri  mlwidth=style ///
        msangle=style,-360,360@connected|contour|dot|dropline|pcarrow|pcarrowi|pcbarrow|pccapsym|pcscatter|rcapsym|rconnected|rpcap|rpspike|rscatter|scatter|scatteri  msangle=style ///
        mlabposition=style  fintensity=style ///
        jitter=style  jitterseed=style ///
        yaxis=axes,1,9  xaxis=axes,1,9 ///
        base=num  barwidth=num  level=num@lfitci|qfitci|fpfitci ///
        degree=int,0  bwidth=num@lowess  bwidth=num,0@kdensity  bwidth=pos ///
        kernel=enum,epanechnikov|epan2|biweight|cosine|gaussian|parzen|rectangle|triangle ///
        n=int,1,300@mspline  n=int@lfit|qfit|lfitci|qfitci  n=int@fpfitci  n=int,,10000@mband  n=int,1,10000  bin=int,1,1000  width=pos  start=num  bands=int,1,200 ///
        gap=num  baroffset=num  area=num  droplines=numlist,1 ///
        level=num,10,99.99@lpolyci ///
        colorlevels=int ///
        colorcuts=numlist,1  colorvar=var  mlabel=var ///
        range=range,2,2,m@lfit|qfit|lfitci|qfitci  range=range,2,2 ///
        clwidth=style@scatter  clwidth=style,0,10000,u ///
        alwidth=style,0,10000,u@lfitci|qfitci|lpolyci|fpfitci|area|bar|spike|dropline|histogram|rarea|rbar|rspike|rcap|rcapsym|rline|rconnected|tsrline|pcspike|pcarrow|pcbarrow|pcscatter|pccapsym|pci ///
        mlabangle=style,-360,360@scatter|connected|bar|dot|dropline|rcapsym|rconnected|rscatter|pcscatter|pccapsym|scatteri ///
        mcolor=colour mfcolor=colour mlcolor=colour mlabcolor=colour lcolor=colour fcolor=colour color=colour acolor=colour alcolor=colour bfcolor=colour blcolor=colour clcolor=colour
    // alwidth(), the outline of a ci fit's band, has them too: measured
    // 24sep2026, `twoway lfitci mpg weight, alwidth(-1)' and alwidth(20000)
    // are "gm_linewidth must be between 0.000 and 1.0e+04", r(198), and
    // alwidth(0) and alwidth(10000) draw (fixtures/value_truth.json
    // alwidth_1-12).  Drawn, twoway refuses alwidth(-1) on exactly the
    // types listed -- every type with an area or a line style of its own
    // besides the connecting line -- and draws it on line, connected, the
    // fits and smooths, kdensity, function, tsline, scatter, dot, rscatter
    // and scatteri (measured per type 24sep2026; test_ci_band_options
    // .cscript asks twoway again).  Refused where twoway refuses it; dash
    // draws it on the four ci types and names it on every other
    // (_dash_fold_typed).
    // WP-22.  clwidth() has lwidth()'s bounds -- twoway refuses clwidth(-1)
    // and lwidth(-1) alike, "gm_linewidth must be between 0.000 and
    // 1.0e+04", r(198) -- but only where it draws the connecting line;
    // _dash_fold_cl has dropped the triple everywhere else before this runs,
    // so the rule needs no type list.  mlabangle() takes an anglestyle name
    // (never refused: twoway notes an unknown one) or degrees, and twoway
    // refuses a number outside -360..360, "textangle must be between
    // -360.000 and 360.000", r(198), where it draws marker labels --
    // measured 23sep2026 on exactly the types listed (pccapsym with the
    // marker-label parity work; the rule had left it out).  On pcarrow and
    // pcbarrow, which draw labels too, twoway prints that message and
    // returns rc 0, drawing the arrows without their labels, so they are
    // not refused; the renderer reports the angle and draws horizontal.
    // Elsewhere twoway never evaluates the angle, and neither does this
    // table.
    // lwidth()'s 0..10000 bound stands (WP-31 S33, A15): S33's
    // measurement (sizing_truth.json lw_20000) is twoway's gm_linewidth
    // refusal the token already gives.
    // WP-35 basic:PT-13 (test/fixtures/value_codes_truth.json): the bounds
    // twoway does not have are gone.  jitter() and jitterseed() take any
    // value (a word or a negative number twoway draws as none, and
    // _dash_validate_opts drops it), barwidth() any number (-1, twoway's
    // own default, dropped), mband's n() any integer up to dash's 10000
    // (n(0) and n(-5) drawn as none, D61).  lwidth(), mlwidth() and
    // msangle() are held to their bounds only on the types where twoway
    // refuses a value outside them (per_type lwidth_neg, mlwidth_neg,
    // msangle_400); on the others the value draws nothing different and
    // is dropped.  aspectratio() keeps its lower bound: twoway's picture
    // for aspectratio(-1) is a plot region overflowing the graph, which
    // dash does not copy (D59).
    // scale(), fxsize(), fysize() (WP-31 D5, sizing_truth.json): scale()
    // takes 0 and above, a negative number is twoway's gm_linewidth
    // refusal and a word its note, drawn at 1 (mult); fxsize()/fysize()
    // take any number (0 and 150 draw) and refuse a word "option fxsize()
    // incorrectly specified" (optnum).
    // Graph rules: validated once per segment in _dash_validate_opts, from
    // s(g_<opt>) -- so a value inside a segment is refused as twoway refuses
    // it even when a later segment or the after-comma part outranks it --
    // and once per graph in _dash_plot, from the g_<opt> accumulators,
    // after an after-comma option has outranked a segment's.
    // scheme (WP-17): a name the renderer could not resolve used to reach
    // it with rc 0 and be drawn as s2color under a warning, half applied
    // when the file existed and was named bare.  Refused here instead, on
    // the immediate route, on a registered graph and inside a segment
    // alike, by the same rule `dash build' and `dash serve' apply.
    local graph ///
        xsize=style,1,100  ysize=style,1,100  aspectratio=num,0  hover=varlist  by=byvarlist ///
        scale=mult  fxsize=optnum  fysize=optnum ///
        scheme=scheme ///
        xlabel=axislist  ylabel=axislist  xlabel2=axislist  ylabel2=axislist ///
        xtick=axislist  ytick=axislist  xtick2=axislist  ytick2=axislist ///
        xmtick=axislist  ymtick=axislist ///
        xmlabel=axislist  ymlabel=axislist ///
        xmtick2=axislist  ymtick2=axislist  xmlabel2=axislist  ymlabel2=axislist ///
        zlabel=keyformat
    // Flag applicability (WP-18): flag[|flag...]@type[|type...].  A flag
    // written on a type outside its list is refused as twoway refuses it,
    // r(198) "option <flag> not allowed" (measured 23sep2026: scatter
    // discrete, lfit stdf, histogram mean, scatter noweight/logit/adjust,
    // lowess stdp).  Checked in _dash_validate_opts, which also refuses
    // more than one of stdp/stdf/stdr and discrete beside bin()/bins().
    // fpfitci is on the std list (WP-23): twoway fpfitci takes stdp -- its
    // band is the stdp band -- and refuses stdf and stdr in its own words,
    // which _dash_validate_opts reproduces (measured 23sep2026: stdp rc 0;
    // stdf, stdr r(198) "stdf not allowed").  dash refused stdp there.
    // density, fraction, frequency and percent are histogram's alone:
    // twoway refuses each elsewhere, r(198) "option frequency not
    // allowed" (WP-35 stat:PT-2; stat_refusal_truth.json flag.*).
    local flags ///
        discrete@histogram  density|fraction|frequency|percent@histogram ///
        stdp|stdf|stdr@lfitci|qfitci|fpfitci ///
        mean|noweight|adjust|logit@lowess
    // Value lists (WP-30 P1.1b): plot rules twoway reads one element per
    // y of an expanded varlist, checked by _dash_value_list element by
    // element, after the shorthands resolve.
    local values "mlabel jitter base barwidth"
    // Where twoway takes one value and refuses a list, "option barwidth()
    // not allowed", r(198) (measured 03oct2026): option@type|type.
    local onevalue "barwidth@rbar|histogram|rcap|rspike  base@rbar|histogram"
    // Applicability (WP-31 C3, A10): opt@type|type|... lists the plot
    // types twoway accepts the option on; on any other type dash refuses
    // it as twoway's syntax does, r(198) "option <opt>() not allowed"
    // (measured per pair: test/fixtures/applicability_truth.json).
    // BEGIN applies (generated by scripts/gen_applicability_table.py from test/fixtures/applicability_truth.json; do not edit)
    local applies ///
        kernel@lpoly|lpolyci|kdensity ///
        n@lfit|qfit|lfitci|qfitci|fpfitci|lpoly|lpolyci|mspline|mband|kdensity|function ///
        level@contour|contourline|lfitci|qfitci|fpfitci|lpolyci ///
        bwidth@lowess|lpoly|lpolyci|kdensity ///
        bands@mspline|mband ///
        range@lfit|qfit|lfitci|qfitci|kdensity|function ///
        base@area|bar|spike|dropline|dot|function ///
        degree@lpoly|lpolyci ///
        bin@histogram ///
        width@kdensity|histogram ///
        start@histogram ///
        barwidth@area|bar|spike|dropline|dot|rbar|histogram ///
        ndots@area|bar|spike|dropline|dot ///
        dotextend@area|bar|spike|dropline|dot
    // END applies
    c_local _dash_rules_plot  `"`plot'"'
    c_local _dash_rules_graph `"`graph'"'
    c_local _dash_rules_flags `"`flags'"'
    c_local _dash_rules_values "`values'"
    c_local _dash_rules_onevalue "`onevalue'"
    c_local _dash_rules_applies "`applies'"
end

// ----------------------------------------------------------------
// _dash_validate_value  prefix opt spec value ptype
//
// Checks ONE value against ONE spec (the part of a table token after "="
// and before any "@").  On refusal it prints one line, as error, and
// exits 198 -- or 111 for a variable that does not exist, twoway's own
// code for that.  It hands the value back in the caller's local
// _dash_vnorm, normalised where the kind says so (an expanded variable
// name, a lower-cased keyword) and otherwise exactly as it came in.
// The value is only ever expanded through macval(), so a backtick inside
// it cannot become a macro reference when it is tested or echoed.
// rclass, so numlist's and tsrevar's r() stay in here; it never touches
// s(), and it calls no sclass command: tsunab and fvunab clear s(), and
// measured 22sep2026 that wiped every option of the segment being
// validated (colorvar(L.price) jitter(5) msize(large) registered with
// options {}).
// ----------------------------------------------------------------
program define _dash_validate_value, rclass
    version 19
    // The arguments are read by value (_dash_text_args): prefix, opt, spec
    // and ptype are dash's own words and the value the user's text, which
    // -args- cut at a "' in it -- by(foreign, title(`"'90s bc"')) stopped
    // with r(133) (measured 24sep2026; test_json_escaping.cscript JSE-46).
    // Every test below reads the value through the string scalars V and T,
    // never inside quotes.
    mata: _dash_text_args(3, 1, 0)
    local prefix `"`_dash_a1'"'
    local opt    `"`_dash_a2'"'
    local spec   `"`_dash_a3'"'
    local ptype  `"`_dash_a4'"'
    local value : copy local _dash_txt

    local kind ""
    local p1 ""
    local p2 ""
    local p3 ""
    if regexm("`spec'", "^([^,]*),?([^,]*),?([^,]*),?([^,]*)$") {
        local kind = regexs(1)
        local p1   = regexs(2)
        local p2   = regexs(3)
        local p3   = regexs(4)
    }
    local norm `"`macval(value)'"'

    // The numeric reading of the value, with tabs and blanks trimmed off
    // first (syntax strips blanks but keeps tabs, and twoway accepts a
    // tab-padded jitter()).  real() is missing for a word, for "." and for
    // a magnitude beyond c(maxdouble) such as 1e308, and every one of those
    // is "not a number" here.  A scalar keeps full precision for the
    // comparisons below.  `plain' says the text is a decimal or e-notation
    // spelling Python's float() reads back; `numlike' says it is made of
    // digits, signs, dots and exponent letters only (1e400, 1d3), so that a
    // style kind can tell an overflow from a name.
    tempname V T
    mata: st_strscalar(st_local("V"), st_local("value"))
    scalar `T' = ustrtrim(scalar(`V'))
    mata: st_local("tv", st_strscalar(st_local("T")))
    tempname R
    scalar `R' = .
    capture scalar `R' = real(scalar(`T'))
    if _rc scalar `R' = .
    local isnum = (`R' < .)
    local plain   = regexm(scalar(`T'), "^[-+]?([0-9]+\.?[0-9]*|\.[0-9]+)([eE][-+]?[0-9]+)?$")
    local numlike = regexm(scalar(`T'), "^[-+.0-9eEdD]*[0-9][-+.0-9eEdD]*$")

    // Where the bound is dash's own and not twoway's, the message says so.
    local extra ""
    // yaxis()/xaxis() take twoway's 1 to 9 (WP-31 C10c): no sentence.
    // degree() takes every nonnegative integer, as twoway does (WP-31
    // D35; measured: degree(8) to degree(1000) draw); above 7 the renderer
    // notes that the result can differ from Stata's.
    if "`opt'" == "bin" {
        local extra ". dash draws up to 1000 bins."
    }
    else if "`opt'" == "n" & "`ptype'" != "mspline" & `R' > 10000 & `R' < . {
        // mspline's 1..300 is twoway's own ("n must be between 1 and 300");
        // the other types' lower bound 1 is twoway's (WP-31 C10a), the
        // upper 10000 dash's resource limit.
        local extra ". dash evaluates up to 10000 points."
    }

    local bad ""
    // A line width (and scale()) out of twoway's range: its gm_linewidth
    // line, after the chain.
    local lwout 0
    if "`kind'" == "num" {
        if "`p3'" == "x"                     local bad "a number strictly between `p1' and `p2'"
        else if "`p1'" != "" & "`p2'" != ""  local bad "a number between `p1' and `p2'"
        else if "`p1'" != ""                 local bad "a number of at least `p1'"
        else if "`p2'" != ""                 local bad "a number no greater than `p2'"
        else                                 local bad "a number"
        local ok = `isnum'
        if `ok' {
            if "`p3'" == "x" {
                if `R' <= `p1' | `R' >= `p2' local ok = 0
            }
            else {
                if "`p1'" != "" {
                    if `R' < `p1' local ok = 0
                }
                if "`p2'" != "" {
                    if `R' > `p2' local ok = 0
                }
            }
        }
        if `ok' {
            local bad ""
            // As written when Python parses it; a Stata-only spelling
            // such as 1d3 goes out as the number it read.  A copy, not
            // macval() on a one-line if, whose command Stata expands again.
            if `plain' local norm : copy local tv
            else       local norm = strtrim(string(`R', "%21.0g"))
        }
    }
    else if "`kind'" == "int" {
        if "`p1'" != "" & "`p2'" != ""       local bad "an integer between `p1' and `p2'"
        else if "`p1'" != ""                 local bad "an integer of at least `p1'"
        else if "`p2'" != ""                 local bad "an integer no greater than `p2'"
        else                                 local bad "an integer"
        local ok = `isnum'
        if `ok' {
            if `R' != int(`R') local ok = 0
            if "`p1'" != "" {
                if `R' < `p1' local ok = 0
            }
            if "`p2'" != "" {
                if `R' > `p2' local ok = 0
            }
        }
        if `ok' {
            local bad ""
            // One canonical spelling: n(1E3) and degree(2.0) reach the
            // renderer as 1000 and 2, where it calls int() on it.
            local norm = strtrim(string(`R', "%21.0f"))
        }
    }
    else if "`kind'" == "axes" {
        // WP-31 C10b: yaxis()/xaxis() as twoway reads them, a numlist of
        // axis numbers (measured, test/fixtures/parsed_values_truth.json):
        // 0 or 10 is r(125), 1.5 r(126), a word r(121), each "<opt>()
        // invalid -- " and numlist's words; yaxis(1 2) draws the layer on
        // both axes (one scale, _dash_axes_tied in the renderer).  A number
        // twoway takes above p2 is dash's own bound, refused below with the
        // extra sentence.  Normalised to the sorted distinct list: one
        // canonical spelling, yaxis(02) and yaxis(2 1) reach the renderer
        // as 2 and 1 2.  numlist sees the value only when it holds no quote.
        local _ax_rc 121
        if !strpos(scalar(`V'), char(34)) {
            capture numlist `"`macval(value)'"', min(1) integer range(>=1 <=9)
            local _ax_rc = _rc
        }
        if `_ax_rc' {
            local _ax_m "invalid numlist"
            if `_ax_rc' == 122 local _ax_m "invalid numlist has too few elements"
            if `_ax_rc' == 125 local _ax_m "invalid numlist has elements outside of allowed range"
            if `_ax_rc' == 126 local _ax_m "invalid numlist has noninteger elements"
            if !inlist(`_ax_rc', 122, 125, 126) local _ax_rc 121
            display as error "`opt'() invalid -- `_ax_m'"
            exit `_ax_rc'
        }
        local _ax_l `"`r(numlist)'"'
        local _ax_l : list uniq _ax_l
        local _ax_l : list sort _ax_l
        local _ax_hi 0
        foreach _ax_v of local _ax_l {
            if `_ax_v' > `_ax_hi' local _ax_hi `_ax_v'
        }
        if `_ax_hi' > `p2' {
            if `: word count `_ax_l'' == 1 local bad "an integer between `p1' and `p2'"
            else local bad "a list of integers between `p1' and `p2'"
        }
        else local norm `"`_ax_l'"'
    }
    else if "`kind'" == "pos" {
        if "`p1'" != ""                      local bad "a positive number no greater than `p1'"
        else                                 local bad "a positive number"
        local ok = `isnum'
        if `ok' {
            if `R' <= 0 local ok = 0
            if "`p1'" != "" {
                if `R' > `p1' local ok = 0
            }
        }
        if `ok' {
            local bad ""
            if `plain' local norm : copy local tv
            else       local norm = strtrim(string(`R', "%21.0g"))
        }
    }
    else if "`kind'" == "mult" {
        // scale() (WP-31 D5, sizing_truth.json scale_*): twoway draws 0 and
        // above, refuses a negative number when it draws the line widths,
        // r(198) in its gm_linewidth words, and notes a word and draws at 1.
        if `isnum' {
            if `R' < 0 local lwout 1
            if `plain' local norm : copy local tv
            else       local norm = strtrim(string(`R', "%21.0g"))
        }
        else {
            mata: _dash_note("named style ", st_local("tv"), " not found in class numstyle, default attributes used")
            local norm ""
        }
    }
    else if "`kind'" == "optnum" {
        // fxsize()/fysize() (WP-31 D5, sizing_truth.json fx_bad_*, fy_bad_*):
        // any number, a word refused in twoway's words.
        if !`isnum' {
            display as error "option `opt'() incorrectly specified"
            exit 198
        }
        if `plain' local norm : copy local tv
        else       local norm = strtrim(string(`R', "%21.0g"))
    }
    else if "`kind'" == "colour" {
        // WP-30 P1.13a: twoway refuses a comma-written plot colour,
        // mcolor("255,0,128"), with invalid '<word>', r(198).  It reads
        // the colour and its own " editcopy" as parts between commas,
        // every second of which must be blank: the first that is not names
        // its first word (mcolor(red,) is 'editcopy', mcolor(1,,2,3) '3');
        // the rest it draws (mcolor(1,,2) as "1 2"; measured 18oct2026),
        // Mata _dash_colour_comma.  This is one stylelist element, from
        // _dash_stylelist_check (the whole value is not read: mcolor(255
        // 0,0) on one y is the element 255, which twoway draws with its
        // note).  One enclosing pair of double quotes is stripped.
        // Everything else in a colour is the renderer's to read.
        tempname W
        scalar `W' = scalar(`T')
        if ustrlen(scalar(`W')) >= 2 & usubstr(scalar(`W'), 1, 1) == char(34) & usubstr(scalar(`W'), -1, 1) == char(34) {
            scalar `W' = usubstr(scalar(`W'), 2, ustrlen(scalar(`W')) - 2)
        }
        mata: st_strscalar(st_local("W"), _dash_colour_comma(st_strscalar(st_local("W"))))
        scalar `W' = usubstr(scalar(`W'), 1, 80)
        if scalar(`W') != "" {
            mata: _dash_say("err", "invalid '", st_strscalar(st_local("W")), "' ")
            exit 198
        }
        local bad ""
    }
    else if "`kind'" == "style" {
        // A name is a style name and passes untouched: the renderer falls
        // back on the scheme, with a note, if it turns out to be unknown.
        // Only a NUMBER is held to the bounds, which are twoway's own.
        // A token made of digits and exponent letters whose real() is
        // missing (1e400, 1e308) is an overflow, not a name: refused, as
        // twoway's "invalid syntax", so the renderer never sees inf.
        // A number beyond the machine's double range in msize() is drawn by
        // twoway as msize(0) (WP-35 basic:PT-13, D60; value_codes_truth.json
        // msize_1e400_vs0): read as 0.
        local _sinf 0
        if !`isnum' & regexm(scalar(`T'), "^[-+]?([0-9]+\.?[0-9]*|\.[0-9]+)[eEdD]([-+]?[0-9]+)$") {
            if real(regexs(1)) > 0 {
                if log10(real(regexs(1))) + real(regexs(2)) > 308.2547 local _sinf 1
            }
        }
        if `_sinf' & "`opt'" == "msize" local norm "0"
        else if "`p3'" == "u" & "`p1'" != "" & "`p2'" != "" {
            // A line width (WP-30 P1.12b, M5).  twoway (measured
            // 03oct2026) refuses a negative number, *# or #pt/#in/#cm/#rs
            // and an rs value above 10000 with r(198) and its gm_linewidth
            // line; a #pt/#in/#cm or *# that passes 10000 units only once
            // the scheme and graph size are known is the renderer's to
            // note (D-13b).  An overflow (*1e400) passes as a name, as
            // twoway reads it.
            tempname LW
            if regexm(scalar(`T'), "^\*([-+]?([0-9]+\.?[0-9]*|\.[0-9]+)([eEdD][-+]?[0-9]+)?)$") {
                scalar `LW' = real(regexs(1))
                if scalar(`LW') < . & scalar(`LW') < 0 local lwout 1
                // A multiplier past 10000 units of the default scheme's
                // 0.3-unit line (WP-35 basic:PT-13; value_codes_truth.json
                // lwidth_mult_line*: on line, connected and area *33333
                // draws and *33334 is twoway's gm_linewidth refusal).
                else if scalar(`LW') < . & scalar(`LW') * 0.3 > `p2' local lwout 1
            }
            else if regexm(scalar(`T'), "^([-+]?([0-9]+\.?[0-9]*|\.[0-9]+)([eEdD][-+]?[0-9]+)?) *(pt|in|cm|rs)$") {
                local lwunit = regexs(4)
                scalar `LW' = real(regexs(1))
                if scalar(`LW') < . {
                    if scalar(`LW') < 0 local lwout 1
                    else if "`lwunit'" == "rs" & scalar(`LW') > `p2' local lwout 1
                }
            }
            else if `isnum' {
                if `R' < `p1' | `R' > `p2' local lwout 1
            }
            else if `numlike' local bad "a name or a number between `p1' and `p2'"
        }
        else if "`p1'" != "" & "`p2'" != "" {
            if `isnum' {
                if `R' < `p1' | `R' > `p2' local bad "a name or a number between `p1' and `p2'"
            }
            else if `numlike' local bad "a name or a number between `p1' and `p2'"
        }
        else if !`isnum' & `numlike' local bad "a name or a number"
    }
    else if "`kind'" == "istyle" {
        if `isnum' {
            if `R' != int(`R') | `R' < `p1' | `R' > `p2' {
                local bad "a name or an integer between `p1' and `p2'"
            }
        }
        else if `numlike' local bad "a name or an integer between `p1' and `p2'"
    }
    else if "`kind'" == "enum" {
        tempname L
        scalar `L' = lower(scalar(`T'))
        local lv = scalar(`L')
        local choices : subinstr local p1 "|" " ", all
        local hit = 0
        foreach c of local choices {
            if scalar(`L') == "`c'" local hit = 1
        }
        if `hit' local norm : copy local lv
        else {
            local pretty : subinstr local p1 "|" ", ", all
            local bad "one of `pretty'"
        }
    }
    else if "`kind'" == "numlist" {
        if "`p2'" == ""                      local bad "a list of at least `p1' numbers"
        else if "`p1'" == "`p2'"             local bad "a list of exactly `p1' numbers"
        else                                 local bad "a list of between `p1' and `p2' numbers"
        // A numlist holds no double quote; one that does is not one, and is
        // never put on numlist's command line, where a "' in it would end
        // the quotes and let the rest be read as numlist's own options.
        local _nlrc 7
        if !strpos(scalar(`V'), char(34)) {
            capture numlist `"`macval(value)'"'
            local _nlrc = _rc
        }
        if !`_nlrc' {
            local cnt : word count `r(numlist)'
            local ok = (`cnt' >= `p1')
            if "`p2'" != "" {
                if `cnt' > `p2' local ok = 0
            }
            if `ok' {
                local bad ""
                // The expanded, blank-separated list: the renderer splits
                // on blanks and reads floats, so 1(1)5 and 0,10 go out as
                // "1 2 3 4 5" and "0 10".
                local norm `"`r(numlist)'"'
            }
        }
    }
    else if "`kind'" == "range" {
        // WP-31 C10a: range() as twoway reads it (measured,
        // test/fixtures/value_bounds_truth.json).  p3 "m": lfit, qfit,
        // lfitci and qfitci -- Range(numlist min=2 max=2 missingok), a `.'
        // standing for the data's own bound, anything else refused with
        // numlist's code under "range() invalid -- ".  Otherwise kdensity
        // and function: two numbers, or one variable name, whose min and
        // max _dash_fold_range reads over the plot's sample; a variable
        // that does not exist is r(111) in twoway's words, and anything
        // but two numbers "option range() requires two numbers" with
        // numlist's code.  A name reaches confirm only after the regex.
        local _rg_rc 7
        if !strpos(scalar(`V'), char(34)) {
            if "`p3'" == "m" capture numlist `"`macval(value)'"', min(`p1') max(`p2') missingok
            else             capture numlist `"`macval(value)'"', min(`p1') max(`p2')
            local _rg_rc = _rc
        }
        if !`_rg_rc' {
            local norm `"`r(numlist)'"'
        }
        else if "`p3'" == "m" {
            local _rg_m "invalid numlist"
            if `_rg_rc' == 122 local _rg_m "invalid numlist has too few elements"
            if `_rg_rc' == 123 local _rg_m "invalid numlist has too many elements"
            if !inlist(`_rg_rc', 121, 122, 123) local _rg_rc 121
            display as error "range() invalid -- `_rg_m'"
            exit `_rg_rc'
        }
        else if regexm(scalar(`T'), "^[A-Za-z_][A-Za-z0-9_]*$") {
            mata: st_local("_rg_v", st_strscalar(st_local("T")))
            // Stata's own line: "variable nosuch not found", r(111).
            confirm variable `_rg_v'
            // The full name, an abbreviation written out.
            local _rg_full ""
            foreach _rg_x of varlist `_rg_v' {
                local _rg_full `_rg_x'
            }
            local norm "@var:`_rg_full'"
        }
        else {
            if !inlist(`_rg_rc', 121, 122, 123, 127) local _rg_rc 121
            display as error "option range() requires two numbers"
            exit `_rg_rc'
        }
    }
    else if "`kind'" == "axislist" {
        // WP-28 S14 (GAPS2 B1): every numlist run of an axis-label option
        // expanded by Stata's own numlist (_dash_axis_expand); never a
        // refusal -- a run numlist cannot read is left as written and the
        // renderer names or bounds it.
        _dash_axis_expand `"`macval(value)'"'
        mata: st_local("norm", st_global("r(norm)"))
        // A format() word twoway refuses is refused in its words (WP-30
        // P1.5, M5; measured 03oct2026: xlabel(, format(bogus)) and every
        // axis-label option, r(198) "invalid format, <the argument>").
        // A word reaches confirm format only after Mata's gate.
        mata: _dash_axis_fmts(st_local("value"))
        forvalues _i = 1/`_af_n' {
            local _af_bad = !`_af_ok`_i''
            forvalues _j = 1/`_af_nw`_i'' {
                if `_af_bad' continue, break
                capture confirm format `_af_w`_i'_`_j''
                if _rc local _af_bad 1
            }
            if `_af_bad' {
                mata: _dash_say("err", "invalid format, ", _dash_imm_echo(st_local("_af_raw`_i'")), "")
                exit 198
            }
        }
    }
    else if "`kind'" == "keyformat" {
        // zlabel() (WP-30 P1.5, S17's P1.23b): the value goes on as
        // written; only its format() is judged, as the axis-label options'
        // is.  Measured (section 17 E2): zlabel(, format(bogus|%9.2x|
        // %tdbogus)) r(198) "invalid format, <f>"; %12s, %21x, "%9.2f"
        // and format() are accepted.
        local norm `"`macval(value)'"'
        // A format() word twoway refuses is refused in its words (WP-30
        // P1.5, M5; measured 03oct2026: xlabel(, format(bogus)) and every
        // axis-label option, r(198) "invalid format, <the argument>").
        // A word reaches confirm format only after Mata's gate.
        mata: _dash_axis_fmts(st_local("value"))
        forvalues _i = 1/`_af_n' {
            local _af_bad = !`_af_ok`_i''
            forvalues _j = 1/`_af_nw`_i'' {
                if `_af_bad' continue, break
                capture confirm format `_af_w`_i'_`_j''
                if _rc local _af_bad 1
            }
            if `_af_bad' {
                mata: _dash_say("err", "invalid format, ", _dash_imm_echo(st_local("_af_raw`_i'")), "")
                exit 198
            }
        }
    }
    else if inlist("`kind'", "var", "varlist", "byvarlist") {
        local head `"`macval(value)'"'
        local tail ""
        local hastail = 0
        if "`kind'" == "byvarlist" {
            // Split at the first comma outside parentheses: the by-variables
            // come before it, the sub-options (kept verbatim) after it.  The
            // value is read through V: by(foreign, title("'90s by")) is
            // twoway's own form.
            local len = strlen(scalar(`V'))
            local depth = 0
            local cut = 0
            forvalues i = 1/`len' {
                if substr(scalar(`V'), `i', 1) == "(" {
                    local depth = `depth' + 1
                }
                else if substr(scalar(`V'), `i', 1) == ")" {
                    local depth = `depth' - 1
                }
                else if substr(scalar(`V'), `i', 1) == "," & `depth' == 0 {
                    local cut = `i'
                    continue, break
                }
            }
            if `cut' > 0 {
                local head = substr(scalar(`V'), 1, `cut' - 1)
                local tail = strltrim(substr(scalar(`V'), `cut' + 1, .))
                local hastail = 1
            }
            mata: st_local("_bynone", strofreal(strtrim(st_local("head")) == ""))
            if `_bynone' {
                mata: _dash_say("err", "dash: by() must name at least one variable (got: ", st_local("value"), ")")
                exit 198
            }
        }
        // unab expands abbreviations and ranges.  When it refuses, the
        // first token that is not a variable is the one named -- twoway's
        // own "variable X not found" -- without quotes around it: a value
        // that ends in a double quote (by("foreign")) used to close the
        // message's compound quote early and garble it.  A token carrying
        // a time-series operator (L.price) is refused as twoway refuses it
        // in that option, whatever the tsset (WP-31 A6; measured,
        // test/fixtures/weight_operator_truth.json operators.*): mlabel()
        // reads a varname, so "variable L not found", r(111); colorvar()
        // and by() "factor-variable and time-series operators not
        // allowed", r(101).  twoway draws none of them.  hover() is dash's
        // own: there tsrevar (rclass: it leaves s() alone, where tsunab and
        // fvunab clear it) says whether the head is a valid time-series
        // varlist, which dash cannot draw, and it is refused as such.
        local vv ""
        capture unab vv : `macval(head)'
        if _rc {
            capture tsrevar `macval(head)', list
            local ists = (_rc == 0)
            mata: st_local("badvar", strtrim(st_local("head")))
            local tsop = 0
            local fvop = 0
            // Token by token, only when the head holds no double quote: a
            // quoted head is no varlist and is named whole, as it was
            // (by("foreign") names "foreign").  A token is tested through a
            // string scalar, never in quotes.
            mata: st_local("_hdq", strofreal(strpos(st_local("head"), char(34)) > 0))
            if !`_hdq' {
                tempname K
                foreach tok of local head {
                    capture confirm variable `macval(tok)'
                    if _rc {
                        local badvar `"`macval(tok)'"'
                        mata: st_strscalar(st_local("K"), st_local("tok"))
                        // ustrregexm: regexm's engine follows the caller's
                        // version.
                        if ustrregexm(scalar(`K'), "^[LlFfDdSs][LlFfDdSs0-9()/]*\.[A-Za-z_]") local tsop = 1
                        // Factor-variable notation (WP-35 syn:SD-8;
                        // graph_refusal_truth.json fv.*): a # is an
                        // interaction; i. c. o. ib#. #. are operators, read
                        // as the time-series ones are; in mlabel() a name
                        // starting with a digit or with % is no name.
                        else if ustrregexm(scalar(`K'), "#") local fvop = 2
                        else if ustrregexm(scalar(`K'), "^([iIcCoO]|[iI]?[bB][0-9]+|[0-9]+[bB]?|[iI][bB]?\(.*\))+\.[A-Za-z_]") local tsop = 1
                        else if ustrregexm(scalar(`K'), "^[0-9]") local fvop = 3
                        else if ustrregexm(scalar(`K'), "^%") local fvop = 4
                        continue, break
                    }
                }
            }
            if `fvop' == 2 & inlist("`opt'", "colorvar", "by", "mlabel") {
                display as error "interactions not allowed"
                exit 101
            }
            if `fvop' == 3 & "`opt'" == "mlabel" {
                mata: _dash_say("err", "", st_local("badvar"), " invalid name")
                exit 198
            }
            if `fvop' == 4 & "`opt'" == "mlabel" {
                display as error "invalid '%'"
                exit 198
            }
            if `tsop' & "`opt'" == "mlabel" {
                // The operators before the dot: a token the operator test
                // passed holds only letters, digits, ( ) / and the dot.
                local _tsops = substr("`badvar'", 1, strpos("`badvar'", ".") - 1)
                mata: _dash_say("err", "variable ", st_local("_tsops"), " not found")
                exit 111
            }
            if `tsop' & inlist("`opt'", "colorvar", "by") {
                display as error "factor-variable and time-series operators not allowed"
                exit 101
            }
            if `ists' & `tsop' {
                mata: _dash_say("err", "`prefix': `opt'() must name a variable, not a time-series expression (got: ", st_local("value"), ")")
                exit 198
            }
            mata: _dash_say("err", "`prefix': `opt'(): variable ", st_local("badvar"), " not found")
            exit 111
        }
        if "`kind'" == "var" & `: word count `vv'' > 1 {
            mata: _dash_say("err", "`prefix': `opt'() must name one variable (got: ", st_local("value"), ")")
            exit 198
        }
        // WP-35 DT-15: colorvar() naming a string variable is refused as
        // twoway refuses it, r(7) (dash_only_words_truth.json V3;
        // DECISIONS.md P4-7); dash drew a colour per value.
        if "`opt'" == "colorvar" & `: word count `vv'' == 1 {
            capture confirm string variable `vv', exact
            if !_rc {
                mata: _dash_say("err", "'", st_local("vv"), "' found where numeric variable expected")
                exit 7
            }
        }
        // by()'s sub-options, refused in twoway's stages, codes and words
        // (WP-30 P1.15b); the tail is read by value from a string scalar.
        if `hastail' {
            tempname B
            mata: st_strscalar(st_local("B"), st_local("tail"))
            _dash_by_check `B'
            mata: st_local("tail", st_strscalar(st_local("B")))
        }
        local norm `"`vv'"'
        // A block, not a one-line if, whose command Stata expands again,
        // macval() or not: by(foreign, title("b\$G \`=exp'")) was stored
        // with $G's value and the =exp evaluated (measured 24sep2026;
        // test_json_escaping.cscript JSE-69).
        if `hastail' {
            local norm `"`vv', `macval(tail)'"'
        }
    }
    else if "`kind'" == "scheme" {
        // WP-17, WP-30 P1.25b: a shipped translation or a theme alias, by
        // name and case-insensitively (a shipped name with or without the
        // .scheme extension), or a scheme Stata finds as twoway finds it:
        // findfile scheme-NAME.scheme, then findfile NAME.scheme, along the
        // ado-path (BASE/s/scheme.class:172-173) -- the lookup
        // dash_render.py's SchemeParser makes, so a name that passes here
        // resolves there.  A scheme is named, never given as a path: a name
        // holding a blank, a control character, a slash or backslash, a
        // colon, `..', a quote, a backtick or a dollar sign, or longer than
        // 87 characters, is refused before any file is looked for (M7,
        // P1.25.4), read from the scalar T and never from a macro-expanded
        // value; the renderer applies the same rule and its containment,
        // regular-file and size guards again.  A dash- name is the user's
        // own file in the working directory only.  The value goes through
        // as written: the renderer lower-cases shipped names itself.
        _dash_shipped_schemes
        tempname L B
        scalar `L' = lower(scalar(`T'))
        // A shipped name written WITH the extension -- scheme(s2color.scheme),
        // in any case -- is the shipped scheme.  The extension is dropped
        // for the list test only: a theme is not a file and takes no
        // extension.  Read through the string scalars T, L (lower case) and
        // B (without .scheme).
        scalar `B' = scalar(`L')
        if substr(scalar(`L'), -7, .) == ".scheme" {
            scalar `B' = substr(scalar(`L'), 1, strlen(scalar(`L')) - 7)
        }
        local hit = 0
        foreach c of local _dash_schemes {
            if scalar(`B') == "`c'" local hit = 1
        }
        foreach c of local _dash_themes {
            if scalar(`L') == "`c'" local hit = 1
        }
        local named = 1
        if !`hit' & scalar(`T') != "" {
            local named = !ustrregexm(scalar(`T'), "[\s\p{Cc}]") & ///
                          !strpos(scalar(`T'), "/") & ///
                          !strpos(scalar(`T'), char(92)) & ///
                          !strpos(scalar(`T'), ":") & ///
                          !strpos(scalar(`T'), "..") & ///
                          !strpos(scalar(`T'), char(34)) & ///
                          !strpos(scalar(`T'), char(96)) & ///
                          !strpos(scalar(`T'), char(36)) & ///
                          ustrlen(scalar(`T')) <= 87
            if `named' {
                if substr(scalar(`L'), 1, 5) == "dash-" {
                    if substr(scalar(`L'), -7, .) == ".scheme" {
                        capture confirm file `"`macval(tv)'"'
                    }
                    else {
                        capture confirm file `"`macval(tv)'.scheme"'
                    }
                }
                else if substr(scalar(`L'), -7, .) == ".scheme" {
                    capture findfile `"`macval(tv)'"'
                }
                else {
                    capture findfile `"scheme-`macval(tv)'.scheme"'
                    if _rc {
                        capture findfile `"`macval(tv)'.scheme"'
                    }
                }
                if !_rc local hit = 1
            }
        }
        if !`hit' {
            local _sn : list sort _dash_schemes
            local _sn : subinstr local _sn " " ", ", all
            local _tn : list sort _dash_themes
            local _tn : subinstr local _tn " " ", ", all
            local bad "one of `_sn'; a theme (`_tn'); or a scheme Stata finds along the ado-path as scheme-NAME.scheme or NAME.scheme"
            if !`named' {
                local extra ". A scheme is named, never given as a path: a name holding a blank, a quote, a slash or backslash, a colon or .. is not looked for"
            }
        }
    }
    else if "`kind'" == "format" {
        // 1. Character gate: one leading %, then only the characters a
        //    display format can contain -- no quote, blank, backtick, dollar
        //    or parenthesis -- and at most 60 of them.
        // 2. Stata's own judgement: `confirm numeric format' is rc 0 for
        //    %9.2f %12.0fc %-12.3e %9,2fc %tdCCYY-NN-DD %tcHH:MM:SS %21x
        //    %16H and rc 7 for %12s, bogus, 9.2f, %9.2, %9.2f_n, %c, %.
        // The token is then a single proven numeric %fmt, so `: display'
        // can stay the formatter (strofreal() returns "" for a bad format
        // without a word, so it is NOT a validator).
        local ok = 0
        if regexm(scalar(`V'), "^%[A-Za-z0-9_.,:!/+-]+$") & strlen(scalar(`V')) <= 60 {
            capture confirm numeric format `macval(value)'
            if !_rc local ok = 1
        }
        if !`ok' {
            mata: _dash_say("err", "`prefix': `opt'() must be a numeric display format such as %9.2f or %12.0fc (got: ", st_local("value"), ")")
            exit 198
        }
        // 3. confirm passes %21x, %16H and %16L, but the page cannot write
        //    a hexadecimal or IEEE byte dump (WP-28 S04): refused here, as
        //    dash_render.py's _dash_fmt_refusal refuses them.
        if regexm(scalar(`V'), "^%-?[0-9]*[xHL]$") {
            mata: _dash_say("err", "`prefix': `opt'() cannot be written by the dashboard: ", st_local("value"), " (hexadecimal %x and IEEE %H/%L formats are refused)")
            exit 198
        }
    }

    if `lwout' {
        mata: _dash_say("err", "gm_linewidth must be between 0.000 and  1.0e+04", "", "")
        if "`kind'" == "style" {
            mata: _dash_say("err", "`prefix': `opt'() must be a line width from 0 to 10000 Stata units (got: ", st_local("value"), ")")
        }
        exit 198
    }
    // lpoly's and lpolyci's own refusals, in twoway's words and codes
    // (WP-31 C11; test/fixtures/estimator_edges_truth.json lp.D7.*):
    // bwidth(abc) is read as an expression, "variable abc not found",
    // r(111); a bwidth() or n() at or below zero, or a degree() below it,
    // is "<opt>() must be a positive (nonnegative) number"; n(abc) is
    // "option n() not allowed"; an unknown kernel "invalid kernel
    // function", r(198).  degree() above 7 keeps dash's sentence (twoway
    // draws it).
    local _lpf "lpoly lpolyci"
    if `"`bad'"' != "" & `: list ptype in _lpf' {
        if "`opt'" == "bwidth" & regexm(scalar(`T'), "^[A-Za-z_][A-Za-z0-9_]*$") {
            mata: _dash_say("err", "variable ", st_strscalar(st_local("T")), " not found")
            exit 111
        }
        // A number only: other text keeps dash's sentence, which shows it
        // as typed (test_json_escaping.cscript JSE-69); twoway reads it as
        // an expression, and a macro reference typed in it expands there
        // (rc 0, measured 17oct2026), which dash never does.
        if ("`opt'" == "bwidth" & `isnum') | ("`opt'" == "n" & `isnum' & `R' <= 0) {
            display as error "`opt'() must be a positive number"
            exit 198
        }
        if "`opt'" == "n" & !`numlike' {
            display as error "option n() not allowed"
            exit 198
        }
        if "`opt'" == "degree" & `isnum' & `R' < 0 {
            display as error "degree() must be a nonnegative number"
            exit 198
        }
        // degree(abc) and degree(1.5): twoway's integer syntax refuses the
        // option itself (measured, WP-31 D35).
        if "`opt'" == "degree" {
            display as error "option degree() not allowed"
            exit 198
        }
        if "`opt'" == "kernel" {
            display as error "invalid kernel function"
            exit 198
        }
    }
    // Every refusal above and here echoes the value through _dash_say: the
    // value is read from Mata, never expanded into the display line, and
    // shown as written -- `jitter({bf:X})' printed a bold X (P20-02..06).
    // prefix, opt, bad and extra are this program's own words.
    if `"`bad'"' != "" {
        // twoway's own rc and first line where it refuses the value (WP-35
        // basic:PT-9; dash_parse.mata's _dash_tw_value_tab, measured in
        // test/fixtures/value_truth.json and value_codes_truth.json), by
        // the value's class: "." missing; not a number nan, or huge
        // beyond c(maxdouble) and inf beyond the machine's double range
        // (1e308 and 1e400, which twoway answers apart); nonint; below or
        // above the rule's bounds.  A refusal twoway's table does not hold
        // keeps dash's sentence, as lpoly's and lpolyci's do (their own
        // refusals are above: text that is no number keeps dash's
        // sentence there).
        local _tvc ""
        if scalar(`T') == "." local _tvc "missing"
        else if "`kind'" == "enum" | !`isnum' {
            local _tvc "nan"
            if "`kind'" != "enum" & regexm(scalar(`T'), "^[-+]?([0-9]+\.?[0-9]*|\.[0-9]+)[eEdD]([-+]?[0-9]+)$") {
                if real(regexs(1)) > 0 {
                    local _tvc "huge"
                    if log10(real(regexs(1))) + real(regexs(2)) > 308.2547 local _tvc "inf"
                }
            }
        }
        else if inlist("`kind'", "int", "istyle") & `R' != int(`R') local _tvc "nonint"
        else if "`kind'" == "pos" {
            local _tvc "above"
            if `R' <= 0 local _tvc "below"
        }
        else {
            local _tvc "above"
            if "`p1'" != "" {
                if `R' < `p1' | ("`p3'" == "x" & `R' <= `p1') local _tvc "below"
            }
        }
        if "`ptype'" != "" & `: list ptype in _lpf' local _tvc ""
        mata: st_local("_twv", st_local("_tvc") == "" ? "" : _dash_tw_value_msg(st_local("opt"), st_local("ptype"), st_local("_tvc"), st_strscalar(st_local("T"))))
        mata: st_local("_twrc", substr(st_local("_twv"), 1, strpos(st_local("_twv"), "|") - 1))
        if "`_twrc'" != "" {
            mata: _dash_say("err", "", substr(st_local("_twv"), strpos(st_local("_twv"), "|") + 1, .), "")
            exit `_twrc'
        }
        mata: _dash_say("err", "`prefix': `opt'() must be `bad' (got: ", st_local("value"), ")`extra'")
        exit 198
    }
    c_local _dash_vnorm `"`macval(norm)'"'
end

// ----------------------------------------------------------------
// _dash_value_list  prefix opt spec value ptype nser
//
// A value list -- mlabel(), jitter(), base() or barwidth() -- read as
// twoway reads it over an expanded varlist (WP-30 P1.1b): element k is
// the k-th y's, with . = .. ... and padding (_dash_stylelist_pick).  Each
// element a y uses is held to the single value's rule after the
// shorthands resolve; one past the last y is not checked (register
// P1.1.5; twoway draws jitter(2 200) on one y).  A list where twoway takes
// one value is refused in its words (_dash_rules_onevalue; B14-B21).  A
// misplaced .. or a value string cannot bind is left as typed for
// _dash_stylelist_check.  Hands back the caller's _dash_vnorm: nser
// elements, . for the default, "" when none.
// ----------------------------------------------------------------
program define _dash_value_list, rclass
    version 19
    mata: _dash_text_args(3, 2, 0)
    local prefix `"`_dash_a1'"'
    local opt    `"`_dash_a2'"'
    local spec   `"`_dash_a3'"'
    local ptype  `"`_dash_a4'"'
    local nser   `"`_dash_a5'"'
    local value : copy local _dash_txt
    // A value twoway's string cannot bind, or a misplaced .., is left as
    // typed: _dash_stylelist_check refuses it next in twoway's terms
    // (P20-18b's r(109); "<opt>(<value>):  invalid syntax").
    mata: st_local("_vlq", strofreal(strpos(st_local("value"), char(34)) > 0))
    if `_vlq' {
        capture _dash_stylelist_bind , v(`macval(value)')
        if _rc == 1 exit 1
        if _rc {
            c_local _dash_vnorm : copy local value
            exit
        }
    }
    if "`opt'" == "mlabel" {
        _dash_mlabel_list "`prefix'" `"`macval(value)'"' "`ptype'" `nser'
        c_local _dash_vnorm `"`_dash_vnorm'"'
        exit
    }
    _dash_option_rules
    mata: _dash_stylelist_locals(st_local("value"), "_vl")
    foreach tok of local _dash_rules_onevalue {
        local at    = strpos("`tok'", "@")
        local o     = substr("`tok'", 1, `at' - 1)
        local types = substr("`tok'", `at' + 1, .)
        local types : subinstr local types "|" " ", all
        if "`o'" != "`opt'" | !`: list ptype in types' continue
        if `_vln' > 1 | "`_vlq1'" == "1" {
            display as error "option `opt'() not allowed"
            exit 198
        }
        _dash_validate_value "`prefix'" "`opt'" "`spec'" `"`macval(value)'"' "`ptype'"
        c_local _dash_vnorm `"`macval(_dash_vnorm)'"'
        exit
    }
    mata: st_local("_vlbad", strofreal(_dash_stylelist_bad(st_local("value"))))
    if `_vlbad' {
        c_local _dash_vnorm : copy local value
        exit
    }
    local out ""
    local any 0
    forvalues i = 1/`nser' {
        mata: st_local("e", _dash_stylelist_pick(st_local("value"), `i'))
        if !`: length local e' {
            local out "`out' ."
            continue
        }
        _dash_validate_value "`prefix'" "`opt'" "`spec'" `"`macval(e)'"' "`ptype'"
        local out `"`out' `macval(_dash_vnorm)'"'
        local any 1
    }
    if !`any' local out ""
    c_local _dash_vnorm `"`macval(out)'"'
end

// ----------------------------------------------------------------
// _dash_mlabel_list  prefix value ptype nser
//
// mlabel() read as twoway reads it (WP-30 P1.1b; register P1.1.6, P1.1.7),
// in its order and words, measured 03oct2026: left to right, = is
// "=exp not allowed" r(101) (M15, M16, M24) and a missing variable, past
// the last y too, "variable nosuch not found" r(111) (M19-M23); then a
// list naming no variable is "too few variables specified" r(102) (M17,
// M18); then .. or ... anywhere is ".. not allowed in option mlabel()"
// r(198) (M12-M14).  . and an empty quoted element leave that y
// unlabelled.  Each name is checked once.  Hands back the caller's
// _dash_vnorm: nser full names, . for none, "" when no y is labelled.
// ----------------------------------------------------------------
program define _dash_mlabel_list, rclass
    version 19
    mata: _dash_text_args(1, 2, 0)
    local prefix `"`_dash_a1'"'
    local ptype  `"`_dash_a2'"'
    local nser   `"`_dash_a3'"'
    local value : copy local _dash_txt
    mata: _dash_stylelist_locals(st_local("value"), "_ml")
    // WP-31 C10b: an unquoted element that is a varlist pattern -- Stata
    // name characters holding *, ?, ~ or - (t*, make-foreign) -- is
    // expanded by unab, as twoway's MLabels() is, and its names take its
    // place, labelling the following y's; names past the last y are
    // dropped below, as twoway drops them (measured,
    // test/fixtures/parsed_values_truth.json mlabel.*).  unab sees the
    // element only after the pattern regex; a pattern that matches nothing
    // keeps its place and is refused there, in unab's (twoway's) words.
    local _mlm 0
    forvalues j = 1/`_mln' {
        local _mle : copy local _mlt`j'
        local _mlp 0
        if "`_mlq`j''" != "1" {
            mata: st_local("_mlp", strofreal(regexm(st_local("_mle"), "^[A-Za-z_*?~][A-Za-z0-9_*?~-]*$") & regexm(st_local("_mle"), "[*?~-]")))
        }
        if `_mlp' {
            capture unab _mlx : `_mle'
            if !_rc {
                foreach _mlv of local _mlx {
                    local ++_mlm
                    local _mlT`_mlm' `_mlv'
                    local _mlQ`_mlm' 0
                    local _mlP`_mlm' 0
                }
                continue
            }
        }
        local ++_mlm
        local _mlT`_mlm' : copy local _mle
        local _mlQ`_mlm' : copy local _mlq`j'
        local _mlP`_mlm' `_mlp'
    }
    forvalues j = 1/`_mlm' {
        local _mlt`j' : copy local _mlT`j'
        local _mlq`j' : copy local _mlQ`j'
    }
    local _mln `_mlm'
    local seen ""
    local seenres ""
    local dots ""
    local named 0
    forvalues j = 1/`_mln' {
        local _mlr`j' "."
        if `_mlP`j'' {
            // A pattern unab could not expand: its own line, r(111).
            unab _mlx : `_mlt`j''
        }
        mata: st_local("_c", st_local("_mlq`j'") == "1" ? (strtrim(st_local("_mlt`j'")) == "" ? "skip" : "name") : (st_local("_mlt`j'") == "=" ? "eq" : (st_local("_mlt`j'") == "." ? "skip" : ((st_local("_mlt`j'") == ".." | st_local("_mlt`j'") == "...") ? "dots" : "name"))))
        if "`_c'" == "eq" {
            display as error "=exp not allowed"
            exit 101
        }
        if "`_c'" == "skip" continue
        if "`_c'" == "dots" {
            if "`dots'" == "" local dots "`_mlt`j''"
            continue
        }
        local named 1
        mata: st_local("_k", strofreal(max((0, selectindex(tokens(st_local("seen")) :== st_local("_mlt`j'"))))))
        if `_k' {
            local _mlr`j' : word `_k' of `seenres'
            continue
        }
        local t : copy local _mlt`j'
        _dash_validate_value "`prefix'" "mlabel" "var" `"`macval(t)'"' "`ptype'"
        local _mlr`j' `"`_dash_vnorm'"'
        local seen `"`seen' `macval(t)'"'
        local seenres `"`seenres' `_dash_vnorm'"'
    }
    if !`named' {
        display as error "too few variables specified"
        exit 102
    }
    if "`dots'" != "" {
        // A name written against its .. (mlabel(make..)) is twoway's
        // operator refusal (WP-35 basic:PT-9; value_codes_truth.json
        // mlabel_dotdot), from _dash_tw_value_msg's table; a .. standing
        // alone keeps its words.
        mata: st_local("_twv", ustrregexm(st_local("value"), "[A-Za-z0-9_]\.\.") ? _dash_tw_value_msg("mlabel", st_local("ptype"), "dots", st_local("value")) : "")
        mata: st_local("_twrc", substr(st_local("_twv"), 1, strpos(st_local("_twv"), "|") - 1))
        if "`_twrc'" != "" {
            mata: _dash_say("err", "", substr(st_local("_twv"), strpos(st_local("_twv"), "|") + 1, .), "")
            exit `_twrc'
        }
        display as error "`dots' not allowed in option mlabel()"
        exit 198
    }
    local out ""
    local any 0
    forvalues i = 1/`nser' {
        if `i' > `_mln' local out "`out' ."
        else {
            local out "`out' `_mlr`i''"
            if "`_mlr`i''" != "." local any 1
        }
    }
    if !`any' local out ""
    c_local _dash_vnorm "`out'"
end

// ----------------------------------------------------------------
// _dash_axis_expand value
//
// WP-28 S14 (GAPS2 B1).  An axis-label option's value (xlabel(), ylabel(),
// their second-axis twins, xtick(), ytick(), xmtick(), ymtick(), xmlabel(),
// ymlabel()) with every bare numlist run replaced by Stata's own numlist
// expansion -- 1(2)10 becomes 1 3 5 7 9, 10 20 to 40 becomes 10 20 30 40 --
// while strings, sub-options and hostile runs (a backtick, $ or ') are kept
// exactly as written (_dash_axis_pieces).  numlist is always given
// max(2000), dash's own _MAX_AXIS_TICKS: a bare numlist is capped by Stata
// (r(123) above its element limit on 19.5; numlist "1/1800" is rc 0), and
// max(2000) holds it to dash's bound, refusing 0(0.000001)1000000 at once
// (r(123)).
// Never refuses: a run numlist cannot read -- a zero step, a bare word,
// more than 2,000 values -- is left as written, because twoway does not
// refuse those alike (xlabel(1(0)5) is rc 0, xlabel(2000 abc 4000) r(198))
// and numlist's rc cannot tell them apart; the renderer names what it
// cannot draw and bounds the rest.  Read by value (_dash_text_args).
// WP-30 P1.18b: an expanded rule reads as a list, so the rule-versus-list
// distinction twoway draws by is kept here: _dash_axis_pieces rates the
// head (_ap_rule) and its T piece is the tail twoway reads.  After a
// rule-led head (a(b)c, #N, minmax, none) add is spent -- twoway draws
// ylabel(15(10)35, add) as 15 25 35 -- and after a lone a(b)c rule
// norescale is dropped, as twoway draws ylabel(0(10)100, norescale)
// (test/fixtures/axis_add_truth.json).  The tail is rebuilt in Mata from
// its words, never by macro substitution of the user's text.
// Returns r(norm).
// ----------------------------------------------------------------
program define _dash_axis_expand, rclass
    version 19
    mata: _dash_text_args(0, 0, 0)
    local value : copy local _dash_txt
    mata: _dash_axis_pieces(st_local("value"))
    local _n = `_ap_n'
    local out ""
    local tail ""
    forvalues j = 1/`_n' {
        local tag "`_ap_tag`j''"
        local txt : copy local _ap_txt`j'
        if "`tag'" == "T" {
            local tail : copy local txt
            continue
        }
        // WP-31 D1c: a lone a(b)c rule stays as typed (_ap_rule 2), so
        // the renderer can tell it from an evenly spaced list, which
        // twoway reads as no rule for ##N (minor_tick_truth.json
        // m_between_even_list); the renderer expands the rule itself.
        if "`tag'" == "B" & "`_ap_rule'" != "2" {
            capture numlist `"`macval(txt)'"', max(2000)
            if !_rc local txt `"`r(numlist)'"'
        }
        if `"`macval(out)'"' == "" local out : copy local txt
        else                       local out `"`macval(out)' `macval(txt)'"'
    }
    return local norm `"`macval(out)'`macval(tail)'"'
end

// ----------------------------------------------------------------
// _dash_validate_opts ptype
//
// Runs every plot rule against this segment's s() values, once the plot
// type is known and bw() has been folded, and then every graph rule
// against the segment's s(g_<opt>) -- so `(scatter mpg weight,
// xsize(500)) , xsize(5)' is refused as twoway refuses it, although the
// after-comma value would have outranked the segment's.  A rule that
// names plot types applies only to them and displaces the untyped rule
// for the same option.  A normalised value is written back with sreturn
// local; nothing else in s() is touched, and s() is never cleared here.
// Defence in depth: every s() macro is snapshotted first, and one that
// comes back empty from a validation is put back, so a helper that
// clears s() can never again empty the segment's options in silence.
// ----------------------------------------------------------------
program define _dash_validate_opts, sclass
    version 19
    args ptype nser
    if "`nser'" == "" local nser 1
    _dash_option_rules

    // The snapshot, the values and the restore are read and written by
    // value: s() holds the user's text, and a copy through compound quotes
    // expanded a macro in it again (test_json_escaping.cscript JSE-69).
    local _keys : s(macros)
    foreach _k of local _keys {
        mata: st_local("_snap_" + st_local("_k"), st_global("s(" + st_local("_k") + ")"))
    }

    // ---- The statistical flags (WP-18) ----
    // Each belongs to one plot family and is refused elsewhere as twoway
    // refuses it.  stdp, stdf and stdr name one band each: `twoway lfitci
    // mpg weight, stdf stdr' is r(198) "may not combine stdf stdr".
    // discrete decides the bins itself: `twoway histogram rep78, discrete
    // bin(3)' is r(198) "options discrete and bins() may not be combined",
    // while width() and start() combine with it (rc 0).  All measured
    // 23sep2026 (scratchpad/wp18/A/wording.log).
    foreach tok of local _dash_rules_flags {
        local at    = strpos("`tok'", "@")
        local names = substr("`tok'", 1, `at' - 1)
        local types = substr("`tok'", `at' + 1, .)
        local names : subinstr local names "|" " ", all
        local types : subinstr local types "|" " ", all
        if `: list ptype in types' continue
        foreach f of local names {
            if `"`s(`f')'"' != "" {
                display as error "option `f' not allowed"
                exit 198
            }
        }
    }
    local _std ""
    foreach f in stdp stdf stdr {
        if `"`s(`f')'"' != "" local _std "`_std' `f'"
    }
    if `: word count `_std'' > 1 {
        display as error "may not combine`_std'"
        exit 198
    }
    // stdf and stdr need regress's residual variance, which predict will
    // not give after weighted or robust estimation (regres_p.ado): twoway
    // lfitci/qfitci with an aweight say "not possible with weighted data",
    // r(135); with a pweight "option stdf not allowed after robust
    // estimation", r(198).  An fweight is replication and is fine; stdp is
    // fine under all three.  Measured 23sep2026.  s(weight) is set before
    // this runs, and only on a type that honours weights.
    local _std = strtrim("`_std'")
    // fpfitci draws the stdp band and no other: twoway_fpfitci_parse.class
    // runs lfitci's parser first ("may not combine", above) and then
    // refuses stdf and stdr as "stdf not allowed", r(198) (measured
    // 23sep2026).  stdp alone is its default, accepted.
    if "`ptype'" == "fpfitci" & ("`_std'" == "stdf" | "`_std'" == "stdr") {
        display as error "`_std' not allowed"
        exit 198
    }
    if "`_std'" == "stdf" | "`_std'" == "stdr" {
        if `"`s(weight)'"' == "aweight" {
            display as error "not possible with weighted data"
            exit 135
        }
        if `"`s(weight)'"' == "pweight" {
            display as error "option `_std' not allowed after robust estimation"
            exit 198
        }
    }
    mata: st_local("_dbin", strofreal(st_global("s(discrete)") != "" & st_global("s(bin)") != ""))
    if `_dbin' {
        display as error "options discrete and bins() may not be combined"
        exit 198
    }
    // Then bins() with width(), and two of histogram's scale words, as
    // twoway__histogram_gen.ado checks them, r(198), the words in its
    // order whatever order they were typed in (WP-35 stat:PT-1;
    // test/fixtures/stat_refusal_truth.json hist.*).
    mata: st_local("_dbw", strofreal(st_global("s(bin)") != "" & st_global("s(width)") != ""))
    if `_dbw' & "`ptype'" == "histogram" {
        display as error "options bins() and width() may not be combined"
        exit 198
    }
    local _htype ""
    foreach f in density fraction frequency percent {
        if `"`s(`f')'"' != "" local _htype "`_htype' `f'"
    }
    if `: word count `_htype'' > 1 {
        local _htype : list retokenize _htype
        display as error "options `_htype' may not be combined"
        exit 198
    }
    // colorcuts() and colorlevels() (GAPS2 X2, colorvar_options.sthlp:95-98)
    // "may not be combined": twoway refuses the pair with these words, r(198)
    // (measured 26sep2026, test/fixtures/colorvar_truth.json cuts_and_levels).
    mata: st_local("_cvcl", strofreal(st_global("s(colorcuts)") != "" & st_global("s(colorlevels)") != ""))
    if `_cvcl' {
        display as error "may not combine options colorcuts() and colorlevels()"
        exit 198
    }

    // Applicability (WP-31 C3): an option on a type twoway's parser does
    // not declare falls to Stata's syntax there and is refused before any
    // value is read; the same here, naming the option from the table.
    foreach tok of local _dash_rules_applies {
        local at    = strpos("`tok'", "@")
        local o     = substr("`tok'", 1, `at' - 1)
        local types = substr("`tok'", `at' + 1, .)
        local types : subinstr local types "|" " ", all
        if `: list ptype in types' continue
        mata: st_local("_ap_v", strofreal(st_global("s(" + st_local("o") + ")") != ""))
        if `_ap_v' {
            display as error "option `o'() not allowed"
            exit 198
        }
    }
    // WP-31 B5b: ndots() takes any number, its first word read (twoway
    // draws ndots(10 20) with 10 dots, ndots(2.5) and ndots(-3) as given),
    // and anything else is twoway's "option ndots() incorrectly specified",
    // r(198) (test/fixtures/dot_truth.json D04-D04e, D11g, D11v, D11w).
    tempname _ndT
    mata: st_strscalar(st_local("_ndT"), st_global("s(ndots)"))
    if strtrim(scalar(`_ndT')) != "" & missing(real(word(scalar(`_ndT'), 1))) {
        display as error "option ndots() incorrectly specified"
        exit 198
    }

    // Options that have a type-specific rule for THIS type: their untyped
    // rule is skipped below, so the specific one wins.
    local typed ""
    foreach tok of local _dash_rules_plot {
        local at = strpos("`tok'", "@")
        if `at' {
            local types = substr("`tok'", `at' + 1, .)
            local types : subinstr local types "|" " ", all
            local o = substr("`tok'", 1, strpos("`tok'", "=") - 1)
            if `: list ptype in types' local typed "`typed' `o'"
        }
    }
    foreach tok of local _dash_rules_plot {
        local body "`tok'"
        local at = strpos("`tok'", "@")
        if `at' {
            local body  = substr("`tok'", 1, `at' - 1)
            local types = substr("`tok'", `at' + 1, .)
            local types : subinstr local types "|" " ", all
            if !`: list ptype in types' continue
        }
        local eq   = strpos("`body'", "=")
        local o    = substr("`body'", 1, `eq' - 1)
        local spec = substr("`body'", `eq' + 1, .)
        if !`at' & `: list o in typed' continue
        // A colour is held to its rule element by element, for the y's
        // that use one, by _dash_stylelist_check (18oct2026): the whole
        // value is no colour of its own.
        if "`spec'" == "colour" continue
        mata: st_local("v", st_global("s(" + st_local("o") + ")"))
        // The tests read the values by value: in the quotes they were
        // compared in, a title holding "' beside an option with a rule --
        // title("'90s cars") msize(small) -- ended them
        // (test_json_escaping.cscript JSE-42).  The restore is a copy: a
        // one-line if expands its command again, macval() or not.
        if !`: length local v' continue
        if `: list o in _dash_rules_values' {
            _dash_value_list "dash" "`o'" "`spec'" `"`macval(v)'"' "`ptype'" `nser'
        }
        else {
            _dash_validate_value "dash" "`o'" "`spec'" `"`macval(v)'"' "`ptype'"
        }
        foreach _k of local _keys {
            if !`: length local _snap_`_k'' continue
            mata: st_local("_lost", strofreal(st_global("s(" + st_local("_k") + ")") == ""))
            if `_lost' sreturn local `_k' : copy local _snap_`_k'
        }
        mata: st_local("_chg", strofreal(st_local("_dash_vnorm") != st_local("v")))
        if `_chg' {
            sreturn local `o' `"`macval(_dash_vnorm)'"'
            local _snap_`o' : copy local _dash_vnorm
        }
    }

    // Values twoway draws as it draws the plot without them (WP-35
    // basic:PT-13; test/fixtures/value_codes_truth.json): dropped from s(),
    // element by element of a value list, so the spec is the reference's.
    // jitter() a word or below 0 (jitter_m3_ref, jitter_abc_ref);
    // jitterseed() anything but a nonnegative integer (jitterseed_abc;
    // jitterseed(-1) is a new seed each draw in twoway); barwidth(-1),
    // twoway's own default (barwidth_m1_ref); mband's n() below 1
    // (mband_n_0_ref, mband_n_m5, D61); lwidth(), mlwidth() and
    // msangle() outside their bounds on a type whose rule has no bound
    // (per_type rc 0: the picture is the reference's, read by rc alone on
    // contourline and lowess, which twoway draws differently each time).
    foreach _lo in jitter jitterseed barwidth n lwidth mlwidth msangle {
        if "`_lo'" == "n" & "`ptype'" != "mband" continue
        local _lb ""
        if inlist("`_lo'", "lwidth", "mlwidth", "msangle") {
            local _lbt 0
            foreach tok of local _dash_rules_plot {
                if substr("`tok'", 1, strlen("`_lo'") + 7) != "`_lo'=style," | !strpos("`tok'", "@") continue
                local types = substr("`tok'", strpos("`tok'", "@") + 1, .)
                local types : subinstr local types "|" " ", all
                if `: list ptype in types' local _lbt 1
            }
            if `_lbt' continue
            // A connecting line drawn on a marker type: twoway holds
            // lwidth() to its bounds there (test_help_claims_2.cscript
            // HC2-18m: scatter, connect(l) lwidth(-1) is r(198)).
            mata: st_local("_lcn", strofreal("`_lo'" == "lwidth" & strtrim(st_global("s(connect)")) != ""))
            if `_lcn' {
                mata: st_local("_ln", strofreal(cols(tokens(st_global("s(lwidth)")))))
                forvalues _li = 1/`_ln' {
                    mata: st_local("_le", tokens(st_global("s(lwidth)"))[`_li'])
                    _dash_validate_value "dash" "lwidth" "style,0,10000,u" `"`macval(_le)'"' "`ptype'"
                }
                continue
            }
            local _lb "0 10000"
            if "`_lo'" == "msangle" local _lb "-360 360"
        }
        // A misplaced .. is left for _dash_stylelist_check, which refuses
        // it in twoway's words.
        mata: st_local("_ln", strpos(st_global("s(" + st_local("_lo") + ")"), "..") ? "0" : strofreal(cols(tokens(st_global("s(" + st_local("_lo") + ")")))))
        if !`_ln' continue
        // So is a value Stata's string cannot bind (twoway: r(109)).
        mata: st_local("_lq", strofreal(strpos(st_global("s(" + st_local("_lo") + ")"), char(34)) > 0))
        if `_lq' {
            mata: st_local("_lv", st_global("s(" + st_local("_lo") + ")"))
            capture _dash_stylelist_bind , v(`macval(_lv)')
            if _rc == 1 exit 1
            if _rc continue
        }
        local _lout ""
        local _lany 0
        forvalues _li = 1/`_ln' {
            tempname _LS _LR
            mata: st_strscalar(st_local("_LS"), tokens(st_global("s(" + st_local("_lo") + ")"))[`_li'])
            scalar `_LR' = real(scalar(`_LS'))
            local _ldrop 0
            if "`_lo'" == "jitter" local _ldrop = (scalar(`_LR') >= . | scalar(`_LR') < 0)
            else if "`_lo'" == "jitterseed" local _ldrop = (scalar(`_LR') >= . | scalar(`_LR') < 0 | scalar(`_LR') != int(scalar(`_LR')))
            else if "`_lo'" == "barwidth" local _ldrop = (scalar(`_LR') == -1)
            else if "`_lo'" == "n" local _ldrop = (scalar(`_LR') < 1)
            else if "`_lb'" != "" local _ldrop = (scalar(`_LR') < . & (scalar(`_LR') < `: word 1 of `_lb'' | scalar(`_LR') > `: word 2 of `_lb''))
            // A number Python cannot read back as written (1d1) goes on as
            // the number Stata read.
            if !`_ldrop' & !regexm(scalar(`_LS'), "^[-+]?([0-9]+\.?[0-9]*|\.[0-9]+)([eE][-+]?[0-9]+)?$") & scalar(`_LR') < . {
                scalar `_LS' = strtrim(string(scalar(`_LR'), "%21.0g"))
            }
            mata: st_local("_lout", st_local("_lout") + " " + (`_ldrop' ? "." : st_strscalar(st_local("_LS"))))
            if !`_ldrop' local _lany 1
        }
        if !`_lany' local _lout ""
        mata: st_local("_lout", strtrim(st_local("_lout")))
        sreturn local `_lo' `"`macval(_lout)'"'
    }

    // The graph rules, against what this segment wrote in parentheses.
    // _dash_plot validates the after-comma winners again; a value refused
    // here never gets that far.
    foreach tok of local _dash_rules_graph {
        local eq   = strpos("`tok'", "=")
        local o    = substr("`tok'", 1, `eq' - 1)
        local spec = substr("`tok'", `eq' + 1, .)
        mata: st_local("v", st_global("s(g_" + st_local("o") + ")"))
        if !`: length local v' continue
        _dash_validate_value "dash" "`o'" "`spec'" `"`macval(v)'"' ""
        foreach _k of local _keys {
            if !`: length local _snap_`_k'' continue
            mata: st_local("_lost", strofreal(st_global("s(" + st_local("_k") + ")") == ""))
            if `_lost' sreturn local `_k' : copy local _snap_`_k'
        }
        mata: st_local("_chg", strofreal(st_local("_dash_vnorm") != st_local("v")))
        if `_chg' {
            sreturn local g_`o' `"`macval(_dash_vnorm)'"'
        }
    }

    // A colour written with commas inside a structured option's colour
    // sub-option (WP-31 E5).
    _dash_subopt_colour_check

    // WP-29 P0.9: lpolyci's var() <= 0, after the kernel, bwidth and
    // degree rules above, as twoway orders it (measured: var(0) bwidth(0)
    // names bwidth(), var(0) kernel(foo) the kernel).
    if "`ptype'" == "lpolyci" {
        mata: st_local("_lpv", st_global("s(lpvar)"))
        if `: length local _lpv' {
            if !(real("`_lpv'") > 0) {
                display as error "var() must be a positive number"
                exit 198
            }
        }
    }

    // legend(top), (bottom), (left) and (right) inside this segment:
    // refused as twoway refuses them, even where an after-comma legend()
    // outranks this one (WP-23).  _dash_plot checks the value it writes.
    mata: st_local("_leg", st_global("s(g_legend)"))
    if `: length local _leg' {
        _dash_check_legend `"`macval(_leg)'"'
    }
end
// END option-validation table (WP-15)

// BEGIN resource limits (WP-19)
// ================================================================
// Resource limits.
//
// ROADMAP WP-19: no user input may produce unbounded output or memory use
// (BR-19.1), and every limit names the setting that would raise it
// (BR-19.2).  Measured on the development machine, a standalone dashboard
// embedding 2,000,000 values is 47.6 MB of HTML and took 1.0 GB of RSS in
// the renderer; 4,000,000 is 94.9 MB and 2.1 GB; and Chrome cannot hold a
// string longer than about 512 MB, which is roughly 20,000,000 values.
//
// This is the one table of limits.  Each row is key=default,ceiling.  A
// session raises or lowers a limit with global dash_max_<key>: a whole
// number written in digits only, at most nine of them, from 1 to the
// ceiling.  dash.ado enforces graphs, plots, reflines and added_text
// itself and hands every limit the session has set to the renderer as
// build_options.limits; a dashboard has no size cap (P4-3).
// ================================================================
program define _dash_limit_table
    version 19
    local rows ///
        graphs=100,1000 ///
        images=100,1000 ///
        plots=100,1000 ///
        filter_options=1000,100000 ///
        by_groups=100,1000 ///
        tabs=50,500 ///
        filters=20,200 ///
        reflines=10000,100000 ///
        added_text=1000,100000 ///
        table_rows=1000,100000
    c_local _dash_limit_rows "`rows'"
end

// ----------------------------------------------------------------
// _dash_count_fmt <out_macro> <exp>  -- a count for a message: 1,234,567
//
// %30.0fc rather than %12.0fc: the two give the same text for every
// number below 10^12, which covers every limit, but %12.0fc turns a
// thirteen-digit count into 1.23457e+12 (measured), and observations x
// variables can reach that.
// ----------------------------------------------------------------
program define _dash_count_fmt
    version 19
    gettoken out 0 : 0
    local s : display %30.0fc `0'
    local s = strtrim("`s'")
    c_local `out' "`s'"
end

// ----------------------------------------------------------------
// _dash_limit, name(<key>)  -- one limit, with its global validated
//
// r(value)    the effective limit: $dash_max_<key> when set, else the
//             default
// r(default)  r(ceiling)  from _dash_limit_table
// r(global)   the global's name, dash_max_<key>
//
// An unset or empty global means the default.  Anything else must be a
// whole number written in digits only, at most nine of them, from 1 to
// the ceiling, or it is refused with r(198), naming the global and the
// range and echoing the value reduced to safe characters.
//
// The global is read through st_global(), so its contents are a value and
// are never parsed as Stata code, and it is tested with extended macro
// functions, which work on a macro's value without expanding it.  It is
// expanded only once it is known to be nine digits at most.  No regular
// expression decides it: under a caller's version 16 or 17 Stata's old
// engine does not know bounded repetition, so {1,9} silently fails, and
// under StataNow's engine `$' also matches before a trailing newline --
// measured, regexm("12" + char(10), "^[0-9]+$") is 1.
// ----------------------------------------------------------------
program define _dash_limit, rclass
    version 19
    syntax , NAME(string)

    _dash_limit_table
    local def  ""
    local ceil ""
    foreach _row of local _dash_limit_rows {
        local _eq  = strpos("`_row'", "=")
        local _key = substr("`_row'", 1, `_eq' - 1)
        if `"`_key'"' != `"`macval(name)'"' continue
        local _vals = substr("`_row'", `_eq' + 1, .)
        local _cm   = strpos("`_vals'", ",")
        local def   = substr("`_vals'", 1, `_cm' - 1)
        local ceil  = substr("`_vals'", `_cm' + 1, .)
    }
    if "`def'" == "" {
        display as error "dash: internal error: _dash_limit was asked for a limit that does not exist."
        exit 198
    }

    local gname "dash_max_`name'"
    mata: st_local("_raw", st_global(st_local("gname")))
    local _len : strlen local _raw
    local val = `def'
    if `_len' > 0 {
        // Digits only, and nine at most: with every digit taken out,
        // nothing may be left.
        local _ok = (`_len' <= 9)
        if `_ok' {
            local _rest : copy local _raw
            forvalues _d = 0/9 {
                local _rest : subinstr local _rest "`_d'" "", all
            }
            local _restlen : strlen local _rest
            local _ok = (`_restlen' == 0)
        }
        if `_ok' {
            local val = real("`_raw'")
            local _ok = (`val' >= 1 & `val' <= `ceil')
        }
        if !`_ok' {
            // The echo: the first 20 bytes, each outside [A-Za-z0-9_.-]
            // shown as ?.  Read byte by byte from Mata, so a quote, a
            // backtick, a brace or a byte that is not UTF-8 never reaches
            // the display line as anything but a ?.
            local _safe ""
            local _nb = min(`_len', 20)
            forvalues _i = 1/`_nb' {
                mata: st_local("_b", strofreal(ascii(substr(st_local("_raw"), `_i', 1))))
                if inrange(`_b', 48, 57) | inrange(`_b', 65, 90) | ///
                   inrange(`_b', 97, 122) | inlist(`_b', 45, 46, 95) {
                    local _safe "`_safe'`=char(`_b')'"
                }
                else local _safe "`_safe'?"
            }
            local _cut ""
            if `_len' > 20 {
                _dash_count_fmt _len_s `_len'
                local _cut ", the first 20 of `_len_s' characters"
            }
            _dash_count_fmt _ceil_s `ceil'
            _dash_count_fmt _def_s  `def'
            display as error "dash: global `gname' must be a whole number from 1 to `_ceil_s', written in digits only (got '`_safe''`_cut')."
            display as error "      Drop it (macro drop `gname') to use the default, `_def_s'."
            exit 198
        }
    }

    return scalar value   = `val'
    return scalar default = `def'
    return scalar ceiling = `ceil'
    return local  global    "`gname'"
end

// ----------------------------------------------------------------
// _dash_limits_json  -- the limits this session has set, as JSON
//
// r(json) is the object written as build_options.limits: one key for each
// dash_max_<key> global that is set, in table order, validated through
// _dash_limit and written as a plain integer -- {"by_groups":7} -- or {}
// when none is set.  A limit the session has not set is left out, so the
// renderer keeps its own default for it.
// ----------------------------------------------------------------
program define _dash_limits_json, rclass
    version 19
    _dash_limit_table
    local json ""
    local n = 0
    foreach _row of local _dash_limit_rows {
        local _key = substr("`_row'", 1, strpos("`_row'", "=") - 1)
        local _set : strlen global dash_max_`_key'
        if `_set' == 0 continue
        _dash_limit, name(`_key')
        local _v : display %12.0f r(value)
        local _v = strtrim("`_v'")
        if `n' > 0 local json `"`json',"'
        local json `"`json'"`_key'":`_v'"'
        local ++n
    }
    return local json `"{`json'}"'
end

// ----------------------------------------------------------------
// _dash_graph_cap <already>  -- the registry limit
//
// Both registrars call this before they set or retire any global.  The
// graphs limit is read, and its global validated, on every registration;
// the cap itself applies only to a name the registry does not hold yet
// (<already> 0).  A name already registered is a replace and never counts.
// ----------------------------------------------------------------
program define _dash_graph_cap
    version 19
    args already
    _dash_limit, name(graphs)
    local lim  = r(value)
    local ceil = r(ceiling)
    if `already' == 1 exit
    // Image panels have a limit of their own (_dash_image_cap) and are
    // not counted here (WP-33 33-06).
    local n 0
    foreach _g of global dash_graph_registry {
        if "${dash_img_`_g'}" != "1" local ++n
    }
    if `n' < `lim' exit

    _dash_count_fmt _n_s    `n'
    _dash_count_fmt _lim_s  `lim'
    _dash_count_fmt _ceil_s `ceil'
    // A registry can hold more than the limit when the limit was lowered
    // after the items were registered; the message does not then claim
    // the count is the most one dashboard draws.
    if `n' == `lim' local _why "the most one dashboard draws"
    else            local _why "more than the `_lim_s' one dashboard draws"
    display as error "dash: the registry already holds `_n_s' graphs and KPI cards, `_why'."
    display as error "      Run dash clear, reuse a name with name(<name>, replace), or set global dash_max_graphs to a higher value (at most `_ceil_s')."
    exit 134
end

// ----------------------------------------------------------------
// _dash_image_cap <already>  -- the image-panel limit (WP-33 33-06)
//
// As _dash_graph_cap, for the registry's image panels: $dash_max_images
// (default 100, at most 1,000) is read and validated on every image
// registration, and a name already held by an image is a replace and
// never counts.
// ----------------------------------------------------------------
program define _dash_image_cap
    version 19
    args already
    _dash_limit, name(images)
    local lim  = r(value)
    local ceil = r(ceiling)
    if `already' == 1 exit
    local n 0
    foreach _g of global dash_graph_registry {
        if "${dash_img_`_g'}" == "1" local ++n
    }
    if `n' < `lim' exit

    _dash_count_fmt _n_s    `n'
    _dash_count_fmt _lim_s  `lim'
    _dash_count_fmt _ceil_s `ceil'
    if `n' == `lim' local _why "the most one dashboard draws"
    else            local _why "more than the `_lim_s' one dashboard draws"
    display as error "dash: the registry already holds `_n_s' images, `_why'."
    display as error "      Run dash clear, reuse a name with name(<name>, replace), or set global dash_max_images to a higher value (at most `_ceil_s')."
    exit 134
end

// ----------------------------------------------------------------
// _dash_plot_cap_refuse <lim> <ceil> [<n>]  -- the plot-limit refusal
//
// <n> is the graph's plot count when it is known.  It is left off when
// only a running total is known to have passed the limit and segments are
// still to come.
// ----------------------------------------------------------------
program define _dash_plot_cap_refuse
    version 19
    args lim ceil n
    _dash_count_fmt _lim_s  `lim'
    _dash_count_fmt _ceil_s `ceil'
    if "`n'" == "" {
        local _has "more than `_lim_s' plots (each y variable is one), the most one graph draws"
    }
    else {
        _dash_count_fmt _n_s `n'
        local _has "`_n_s' plots (each y variable is one), more than the `_lim_s' one graph draws"
    }
    display as error "dash: this graph has `_has'."
    display as error "      Split it into several graphs, or set global dash_max_plots to a higher value (at most `_ceil_s')."
    exit 134
end

// END resource limits (WP-19)

// ================================================================
// _dash_plot_opts_to_json
//
// Emit the "options" JSON object fragment from s() values.
// Sets c_local `out_macro' to the JSON string.
// ================================================================
program define _dash_plot_opts_to_json, rclass
    version 19
    args out_macro series
    // series is the expanded y the object is for (1 when omitted): a key
    // of _dash_stylelist_keys() writes that y's stylelist element
    // (_dash_stylelist_pick, WP-30 P1.1a), every other key its value.
    if "`series'" == "" local series 1
    mata: st_local("_sl_keys", _dash_stylelist_keys())

    local parts ""
    local nparts = 0
    // p() is twoway's whole-plot style, applied after every other style
    // option: under it twoway discards each explicit style option, for any
    // name, even an unknown one (WP-30 P1.14a, D-32a; measured 03oct2026).
    // The keys it drops, by the measurement that shows each:
    local _dash_p_drops "pstyle color mcolor msymbol marker msize msangle mfcolor"
    // mcolor(red) msize(huge) p(p3): p3's fill and size; mfcolor() lost.
    local _dash_p_drops "`_dash_p_drops' mlcolor mlwidth mlpattern mstyle mlstyle malpha"
    // mlwidth(thick) p(p3): lost; mstyle/mlstyle come before p().
    local _dash_p_drops "`_dash_p_drops' lcolor lwidth lpattern lalpha lstyle"
    // line, lstyle(p4) p(p3): p3.
    local _dash_p_drops "`_dash_p_drops' clcolor clwidth clpattern clstyle"
    // the connecting line's options are lstyle's kin.
    local _dash_p_drops "`_dash_p_drops' acolor alcolor alwidth alpattern astyle alstyle"
    // area, fcolor(red) p(p3): p3's fill.
    local _dash_p_drops "`_dash_p_drops' bstyle blstyle bfcolor blcolor fcolor fintensity falpha"
    // p() sets the whole seriesstyle, dots and marker back line included
    // (twoway_yxview_parse.class:631, 729, 740; WP-30 P1.14b).
    local _dash_p_drops "`_dash_p_drops' dstyle dlstyle bmlinestyle"
    // dcolor(red) p(p3): the dots stay black (WP-31 B5b,
    // test/fixtures/dot_truth.json D27), so the d-options go too.
    local _dash_p_drops "`_dash_p_drops' dsymbol dcolor dfcolor dsize dlcolor dlwidth"
    // p(p3) mcolor(red%50): p3, opacity 100.
    local _dash_p_drops "`_dash_p_drops' mlabcolor mlabsize mlabposition mlabgap mlabangle mlabformat mlabwidth"
    // mlabcolor(red), mlabposition(9), mlabformat(), mlabgap(5) p(p3): each
    // lost.  mlabel, connect, cmissing and sort are kept.
    mata: st_local("_p_on", strofreal(strtrim(st_global("s(p)")) != ""))

    // Helper: append a k:v JSON pair if value non-empty.
    // weight and wexp (WP-18) are not options: _dash_process_segment puts
    // them in s() for a weighted segment on a type that honours weights,
    // and an unweighted segment writes neither key, so its "options" text
    // is byte-identical to what it was.  clcolor, clpattern and clwidth
    // (WP-22) are non-empty only on the types _dash_fold_cl keeps them for.
    foreach key in mcolor msymbol msize msangle mfcolor mlcolor mlabel mlabcolor ///
                   mlabsize mlabposition mlabgap mlabwidth mlalign malpha marker lcolor ///
                   lwidth lpattern lalpha fcolor fintensity falpha barwidth base mwidth ///
                   blcolor bfcolor jitter jseed yaxis xaxis colorvar colpalette ///
                   colordiscrete coloruseplegend colornlevels colorcuts colormissing ///
                   colorlevels colorvarminmax ///
                   colorstart colorend colorrule colorfillonly colorkeysrange ///
                   colorkeysreverse colorallowmultiple colorotherlabel ///
                   bwidth degree pstyle cmissing recast connect bin width start ///
                   percent frequency density fraction kernel n level bands at ciopts ///
                   lineopts fitopts color mlwidth mstyle lstyle mlstyle ///
                   clstyle astyle alstyle bstyle blstyle dstyle dlstyle bmlinestyle p mlpattern ///
                   dotextend ndots dsymbol dcolor dfcolor dsize dlcolor dlwidth dlalign ///
                   blabel horizontal vertical sort range range_var colorlist jitterseed ///
                   discrete stdp stdf stdr mean noweight adjust logit ///
                   clcolor clpattern clwidth mlabangle mlabformat ///
                   mlabvposition mlabtextstyle ///
                   mangle barbsize headlabel ///
                   xvarformat yvarformat yvarlabel xvarlabel ///
                   mlabprefix mlabsuffix lalign mlabstyle ///
                   acolor alcolor alwidth alpattern ///
                   pwidth lpvar ///
                   atobs estopts predopts estcmd fitplot ciplot smoothplot nofit ///
                   gap baroffset area boundary droplines nodropbase ///
                   ccuts levels minmax crule scolor ecolor ccolors clabels ///
                   format interp clwidths clpatterns reversekey colorlines ///
                   weight wexp {
        // Read by value and measured, never copied or compared in quotes: a
        // copy through them expanded a macro in the value again --
        // mcolor("\$G") was stored as $G's value (measured 24sep2026;
        // test_json_escaping.cscript JSE-69).
        if `_p_on' & `: list key in _dash_p_drops' continue
        if `: list key in _sl_keys' {
            mata: st_local("val", _dash_stylelist_pick(st_global("s(" + st_local("key") + ")"), `series'))
        }
        // yvarlabel() (WP-31 D8): this record's strings, as typed, from its
        // own y on (_dash_varlabel_tail); the renderer reads one per y.
        else if "`key'" == "yvarlabel" {
            mata: st_local("val", _dash_varlabel_tail(st_global("s(yvarlabel)"), `series'))
        }
        else mata: st_local("val", st_global("s(" + st_local("key") + ")"))
        if `: length local val' {
            _dash_json_str `"`macval(val)'"' _jv
            if `nparts' > 0 local parts `"`parts',"'
            local parts `"`parts'"`key'":"`_jv'""'
            local nparts = `nparts' + 1
        }
    }

    c_local `out_macro' `"{`parts'}"'
end


// ================================================================
// _dash_seg_weight_s  -- put a segment's weight into s() (WP-18)
//
// _dash_process_segment is rclass, so it cannot sreturn; this sclass
// helper writes s(weight) and s(wexp) beside the parsed options, and
// the rest of s() survives the call as it survives _dash_fold_bw.
// ================================================================
program define _dash_seg_weight_s, sclass
    version 19
    args wtype wvar
    sreturn local weight `"`wtype'"'
    sreturn local wexp   `"`wvar'"'
end

// ================================================================
// _dash_plottype_families  -- the plot-type families, each named once
//
// _dash_process_segment routes a plot type to its varlist parser and its
// JSON keys by family.  It did so with string inlist() tests, and the
// range test was ptype and nine literals -- Stata's limit for a string
// inlist(): measured 23sep2026, ptype and nine literals is rc 0, ptype and
// ten is r(130) "expression too long" -- so a tenth range type could not
// have been added.  Each family is a word list here, tested with
// `: list ptype in <family>', which has no such limit (WP-22 TR-22.4).
// The four routing families are the renderer's _DASH_UNIVARIATE_TYPES,
// _DASH_RANGE_TYPES, _DASH_PC_TYPES and _DASH_LITERAL_TYPES;
// test/test_plottype_families.py holds the two sides together.
//
//   _pt_univar   one variable                       histogram kdensity
//   _pt_range    y1 y2 [x]                          the range types
//   _pt_pc       y1 x1 y2 x2                        the paired-coordinate types
//   _pt_rangept  y1 y2 y3 x                         rpcap rpspike (WP-31 B1)
//   _pt_contour  z y x                              contour contourline (WP-31 B4b)
//   _pt_literal  literal values or an expression    scatteri pci pcarrowi function
//   _pt_imm      immediate values, read as twoway   scatteri pci pcarrowi
//                reads them (dash_parse.mata 2c)
//   _pt_ts       x from tsset when it is not given  tsline tsrline
// ================================================================
program define _dash_plottype_families
    version 19
    c_local _pt_univar  "histogram kdensity"
    c_local _pt_range   "rarea rbar rspike rcap rline rconnected rcapsym rscatter tsrline"
    c_local _pt_pc      "pcspike pcarrow pcbarrow pcscatter pccapsym"
    c_local _pt_rangept "rpcap rpspike"
    c_local _pt_contour "contour contourline"
    c_local _pt_literal "scatteri pci pcarrowi function"
    c_local _pt_imm     "scatteri pci pcarrowi"
    c_local _pt_ts      "tsline tsrline"
    // The fits and smoothers: one y and one x, as twoway takes them.
    // twoway names the variables when it refuses more for all but the
    // three in _pt_onefit_bare (test_parser.cscript P1A-79).
    c_local _pt_onefit  "lfit qfit lfitci qfitci fpfit fpfitci mspline mband lowess lpoly lpolyci"
    c_local _pt_onefit_bare "lowess lpoly lpolyci"
end

// ================================================================
// _dash_by_parts <string scalar>
//
// A by() value, validated (its variables written out), read by value from
// the string scalar: c_local _by_vars gets the variables before the first
// comma outside parentheses, and _by_miss 1 when the sub-options give
// missing -- twoway's MISSing, abbreviated to miss at least
// (bygraph_g.class) -- 0 otherwise, and _by_total 1 when they give total
// (TOTal: tot at least).  A parenthesised sub-option's text,
// title("a miss"), is not read for either.  The value is never put inside
// quotes or on a command line.
// ================================================================
program define _dash_by_parts
    version 19
    args V
    local len = strlen(scalar(`V'))
    local depth = 0
    local cut = 0
    // As the byvarlist validator reads it: the text is compared through
    // the scalar, never through a macro.
    forvalues i = 1/`len' {
        if substr(scalar(`V'), `i', 1) == "(" {
            local depth = `depth' + 1
        }
        else if substr(scalar(`V'), `i', 1) == ")" {
            local depth = `depth' - 1
        }
        else if substr(scalar(`V'), `i', 1) == "," & `depth' == 0 {
            local cut = `i'
            continue, break
        }
    }
    if `cut' > 0 {
        mata: st_local("_bv", strtrim(substr(st_strscalar(st_local("V")), 1, `cut' - 1)))
        mata: st_local("_bt", substr(st_strscalar(st_local("V")), `cut' + 1, .))
    }
    else {
        mata: st_local("_bv", strtrim(st_strscalar(st_local("V"))))
        local _bt ""
    }
    // Parenthesised text is removed, innermost first, before the words are
    // read; each pass removes one pair, so the loop ends.
    mata: _dash_bt = st_local("_bt"); while (ustrregexm(_dash_bt, "\([^()]*\)")) _dash_bt = ustrregexrf(_dash_bt, "\([^()]*\)", " "); st_local("_bm", strofreal(ustrregexm(_dash_bt, "(^|[ ,])miss(i|in|ing)?($|[ ,])"))); st_local("_btot", strofreal(ustrregexm(_dash_bt, "(^|[ ,])tot(a|al)?($|[ ,])")))
    mata: mata drop _dash_bt
    c_local _by_vars `_bv'
    c_local _by_miss `_bm'
    c_local _by_total `_btot'
end

// ================================================================
// _dash_by_check <string scalar>
//
// by()'s sub-options refused as twoway refuses them (WP-30 P1.15b).  The
// tail after the by-variables is read from the string scalar by Mata's
// _dash_by_scan, never expanded.  bygraph_g.class reads by() in three
// stages (measured, test/fixtures/by_grid_truth.json): -syntax- takes the
// first copy of each declared option and checks rows() then cols()
// (r(121), r(123), r(125), r(126)); "may not specify both rows() and
// cols()" (r(198)); holes() (parse_settings); every leftover -- a second
// copy of a word read once, a capitalised or unknown word -- is refused in
// typed order, "option NAME[()] not allowed" (r(198)); iscale() outside
// [0, 10000] fails at draw, "gm_linewidth must be between 0.000 and
// 1.0e+04" (r(198)).  The numbers go to -syntax- with twoway's own
// declarations, and only when they hold numlist characters alone, so the
// words are twoway's and no user text reaches a command line.  A text
// iscale() or imargin() twoway cannot read gets its first note, once.
// Last, rows() or cols() above the by_groups limit is rewritten in the
// scalar to the limit by Mata's _dash_by_clamp, with one note; the caller
// reads the tail back from the scalar.
// ================================================================
program define _dash_by_check
    version 19
    args V
    mata: _dash_by_scan(st_local("V"))
    foreach o in rows cols {
        if `"`_byg_`o''"' != "" {
            if !`_byg_`o'_ok' {
                mata: _dash_say("err", "", "`o'() invalid -- invalid number", "")
                exit 121
            }
            local 0 `", `o'(`_byg_`o'')"'
            capture noisily syntax [, Rows(numlist integer >0 min=0 max=1) Cols(numlist integer >0 min=0 max=1)]
            if _rc {
                exit _rc
            }
        }
    }
    if `"`_byg_rows'"' != "" & `"`_byg_cols'"' != "" {
        mata: _dash_say("err", "", "may not specify both rows() and cols()", "")
        exit 198
    }
    if `"`_byg_holes'"' != "" {
        if !`_byg_holes_ok' {
            mata: _dash_say("err", "", "holes() invalid -- invalid numlist", "")
            exit 121
        }
        local 0 `", holes(`_byg_holes')"'
        capture noisily syntax [, HOLes(numlist integer >0 max=300)]
        if _rc {
            exit _rc
        }
    }
    if `"`_byg_left'"' != "" {
        mata: _dash_say("err", "", st_local("_byg_left"), "")
        exit 198
    }
    if inlist("`_byg_iscale_kind'", "num", "star") {
        if `_byg_iscale_val' < 0 | `_byg_iscale_val' > 10000 {
            mata: _dash_say("err", "", "gm_linewidth must be between 0.000 and  1.0e+04", "")
            exit 198
        }
    }
    if "`_byg_iscale_kind'" == "bad" {
        mata: _dash_note("named style ", st_local("_byg_iscale"), " not found in class numstyle, default attributes used")
    }
    if `_byg_imargin_bad' {
        mata: _dash_note("named style ", st_local("_byg_imargin"), " not found in class margin, default attributes used")
    }
    if `_byg_imargin_neg' {
        mata: _dash_note("", "by(, imargin()) below 0 is drawn as 0", "")
    }
    // Last, since _dash_limit is rclass: rows() and cols() above the
    // by_groups limit are drawn at it, with one note (TR-48.3, BR-48.7).
    // The global's name is built with char(36), never typed here, where
    // Stata would expand it.
    _dash_limit, name(by_groups)
    local _lim = r(value)
    mata: _dash_by_clamp(st_local("V"), `_lim')
    foreach o of local _byg_clamped {
        local _unit = cond("`o'" == "cols", "columns", "rows")
        mata: _dash_note("by(, `o'(#)) is above the by_groups limit of `_lim'; drawn with `_lim' `_unit'; " + char(36), "dash_max_by_groups raises it", "")
    }
end

// ================================================================
// _dash_qual_mark <target> <value> <ifscalar> <inscalar> [varlist]
//
// replace target = value for the rows the if and the in select -- every
// row when both are empty -- evaluated with the data sorted, stably, on
// varlist when one is given: the order twoway evaluates a by() graph's
// qualifiers in (bygraph_g.class, `bysort varlist (sortedby obsnum)';
// test_qualifier_in_stata.cscript QS-16..).  The if and the in are read
// by value from the two string scalars, and the if is put inside the
// parentheses -syntax- proved it cannot leave, never expanded again.
// target and value are variable names (value may be 1), and varlist the
// by() variables _dash_by_parts read from the validated by().
// sortpreserve gives the data their order back; a sort marks nothing
// changed.
// ================================================================
program define _dash_qual_mark, sortpreserve
    version 19
    gettoken target 0 : 0
    gettoken value 0 : 0
    gettoken sif 0 : 0
    gettoken sin order : 0
    local order : list retokenize order
    mata: st_local("_qx", st_strscalar(st_local("sif")))
    mata: st_local("_qn", st_strscalar(st_local("sin")))
    if "`order'" != "" {
        tempvar _obs
        quietly generate double `_obs' = _n
        sort `order' `_obs'
    }
    local q ""
    // Blocks, never a one-line if: Stata expands a one-line if's command
    // again (P1A-83).
    if `: length local _qx' {
        local q `"if (`macval(_qx)')"'
    }
    if `: length local _qn' {
        local q `"`macval(q)' in `macval(_qn)'"'
    }
    quietly replace `target' = `value' `macval(q)'
end

// ================================================================
// _dash_by_panels varlist, panel(varname) [missing total check(varlist)
//                 rules(string)]
//
// The panels of a by(varlist) graph, as twoway draws them (bygraph_g.class
// RunGraph): the groups of the by() variables -- missing values dropped
// unless missing is given -- holding a row where panel() is 1, in sort
// order.  check() names, plot by plot, a 0/1 variable marking each plot's
// sample, and rules() its rule, one word each: R, the command stops when
// the sample has no row in a panel; D0, the panel is left out when it has
// one row or none; D1 and N1, when it has exactly one (N1: lfit and lfitci,
// which print regress's note as they stop).  In each panel the first plot
// whose rule applies decides.  total adds by()'s Total panel, after the
// groups, over the rows of every group and decided as a group is (it
// exists when a group does).  Returns r(n), the rows in panels (0: no
// panel); r(refuse), the place in check() of the plot that stops the
// command in the first panel where one does, or 0; r(kept), the panels
// drawn; r(d1note), 1 when an N1 plot left a panel out.  sortpreserve: the
// data keep their order.  tpanel() and tcheck() are the Total panel's
// panel() and check(), evaluated in the data's order where the groups'
// are evaluated sorted on the by() variables, as twoway evaluates each
// (_dash_qual_mark); the Total panel is drawn when tpanel() selects a row.
// ================================================================
program define _dash_by_panels, rclass sortpreserve
    version 19
    syntax varlist(min=1), PANEL(varname) [MISSing TOTal CHECK(varlist) ///
        RULES(string) TPANEL(varname) TCHECK(varlist)]
    tempvar p tp anyp grp dec deck cnt first
    quietly gen byte `p' = `panel' == 1
    if "`missing'" == "" markout `p' `varlist', strok
    // The Total panel's rows and samples: tpanel() and tcheck(), which
    // the caller evaluated in the data's order as twoway's Total panel
    // evaluates them (bygraph_g.class: bysort one (sortedby obsnum)), or
    // panel() and check().
    if "`tpanel'" == "" local tpanel `panel'
    if "`tcheck'" == "" local tcheck `check'
    quietly gen byte `tp' = 0
    if "`total'" != "" {
        quietly replace `tp' = `tpanel' == 1
        if "`missing'" == "" markout `tp' `varlist', strok
    }
    quietly count if `tp'
    local ntp = r(N)
    quietly count if `p' | `tp'
    return scalar n = r(N)
    return scalar refuse = 0
    return scalar kept = 0
    return scalar d1note = 0
    if r(N) == 0 exit
    quietly bysort `varlist': egen byte `anyp' = max(`p')
    quietly by `varlist': gen long `grp' = (_n == 1) & `anyp'
    quietly replace `grp' = sum(`grp')
    quietly gen byte `dec' = 0
    quietly gen int `deck' = 0
    local k = 0
    foreach c of local check {
        local ++k
        local rule : word `k' of `rules'
        capture drop `cnt'
        quietly by `varlist': egen double `cnt' = total(`c' == 1)
        if "`rule'" == "R"       local ev "2 * (`cnt' == 0)"
        else if "`rule'" == "D0" local ev "(`cnt' <= 1)"
        else if inlist("`rule'", "D1", "N1") local ev "(`cnt' == 1)"
        else continue
        quietly replace `deck' = `k' if `dec' == 0 & `ev' > 0
        quietly replace `dec' = `ev' if `dec' == 0
    }
    // total: the Total panel, drawn after the groups (bygraph_g.class),
    // holds the rows of every group -- `p', whose by() values are missing
    // only under missing -- and is decided as a group is: tdec and tdeck
    // are its `dec' and `deck'.  Each plot's sample lies inside the rows
    // that make the panels, so it is counted over `p'.
    local tdec 0
    local tdeck 0
    // A Total panel over no row is not drawn: twoway's RunGraph counts the
    // graph's qualifier over it and leaves it out.
    if "`total'" != "" & `ntp' == 0 local tdec 1
    if "`total'" != "" & `ntp' > 0 {
        local k = 0
        foreach c of local tcheck {
            local ++k
            local rule : word `k' of `rules'
            quietly count if `c' == 1 & `tp'
            local tc = r(N)
            if "`rule'" == "R"       local ev = 2 * (`tc' == 0)
            else if "`rule'" == "D0" local ev = (`tc' <= 1)
            else if inlist("`rule'", "D1", "N1") local ev = (`tc' == 1)
            else continue
            if `ev' > 0 {
                local tdec `ev'
                local tdeck `k'
                continue, break
            }
        }
    }
    // The first panel, in by() order, that stops the command; the Total
    // panel comes last.
    quietly summarize `grp' if `anyp' & `dec' == 2, meanonly
    if r(N) > 0 {
        local g = r(min)
        quietly summarize `deck' if `anyp' & `grp' == `g', meanonly
        return scalar refuse = r(min)
        exit
    }
    if `tdec' == 2 {
        return scalar refuse = `tdeck'
        exit
    }
    quietly by `varlist': gen byte `first' = (_n == 1) & `anyp'
    quietly count if `first' & `dec' != 1
    return scalar kept = r(N) + ("`total'" != "" & `tdec' != 1)
    local k = 0
    foreach c of local check {
        local ++k
        if "`: word `k' of `rules''" != "N1" continue
        quietly count if `first' & `dec' == 1 & `deck' == `k'
        if r(N) > 0 | (`tdec' == 1 & `tdeck' == `k') return scalar d1note = 1
    }
end

// ================================================================
// _dash_process_segment
//
// Parse one plot segment (full text including plot type name),
// and build its JSON fragment.
//
// Usage:  _dash_process_segment `"`seg_text'"' `plottype_out' `json_out' [nsegs]
//
// nsegs is the number of segments in the graph (default 1); it only
// decides whether a plot-limit refusal can state the graph's plot count.
//
// After the call:
//   - c_local `plottype_out' = expanded plot type name
//   - c_local `json_out'     = JSON fragment for this plot
//   - c_local _seg_nplots_out = number of plot objects in that fragment
//   - Caller's g_* locals are updated if graph-level opts were found.
// ================================================================
program define _dash_process_segment, rclass
    version 19
    // The segment is read by value (_dash_text_args in dash_parse.mata): its
    // text, less the quotes around it, then the two output names and the
    // optional count.  -args- read it inside the compound quotes it was
    // handed in, so a segment holding "' -- title("'90s cars"), if make ==
    // "' or 1 or '" -- was cut at the quote and its next words became the
    // output names: r(100) ") required" and r(198) (measured 24sep2026;
    // test_json_escaping.cscript JSE-42, JSE-44).  The segment's text is
    // then never put inside quotes in an expression or a Mata line, where
    // title(`"'90s cars"') stopped with r(133) (JSE-42): it is measured with
    // `: length local' and cut in Mata.
    mata: _dash_text_args(0, 2, 1)
    local seg_text : copy local _dash_txt
    local plottype_out `_dash_a1'
    local json_out     `_dash_a2'
    local nsegs        `_dash_a3'
    if "`nsegs'" == "" local nsegs 1

    // ---- extract plot type (first word) ----
    // The token is read from Mata by value: expanded inside the quotes of
    // the mata: line, a double quote in it ended the string.  A token that
    // is no plot type is echoed through _dash_say, as written -- `dash
    // {bf:X} mpg weight' printed a bold X (P20-01).
    //
    // The type ends at a blank or a comma, as twoway reads it: `twoway
    // scatteri, name(x)' is refused for the values it lacks.  It was read
    // up to a blank alone, so the comma became part of it and `dash
    // scatteri, name(x)', `dash (pci, name(x))' and every other type with
    // its comma glued on said "unrecognised plot type 'scatteri,'", r(198)
    // (measured 24sep2026; test_parser.cscript P1A-68).  The comma is left
    // in `rest', where it ends the varlist.
    //
    // The word is matched as typed, in lower case only (WP-35 plot:PT-3,
    // M7): twoway refuses Sc, Hist and Rsc, "<word> is not a twoway plot
    // type", r(198), and dash read them in any case.
    gettoken plottype rest : seg_text, parse(" ,")
    mata: _dash_expand_plottype(st_local("plottype"), "_pt_exp")
    local ptype "`_pt_exp'"

    if "`ptype'" == "" {
        // twoway's line for a word that is no plot type (WP-31 A2): dash
        // printed a sentence of its own, and took lfi, ar and eleven more
        // shorter spellings that twoway refuses with this line.  The
        // Supported: list that follows is dash's own.
        mata: _dash_say("err", "", st_local("plottype"), " is not a twoway plot type")
        display as error ///
            "Supported: scatter line connected area bar spike " _n ///
            "lfit qfit lfitci qfitci lowess lpoly lpolyci fpfit fpfitci " _n ///
            "histogram kdensity rarea rbar rspike rcap rline rconnected " _n ///
            "dot dropline rcapsym scatteri pcspike pcarrow pcbarrow " _n ///
            "pccapsym pci pcarrowi pcscatter tsline tsrline mspline mband " _n ///
            "rscatter function rpcap rpspike contour contourline"
        exit(198)
    }

    // The families each plot type is routed by, named once (TR-22.4).
    _dash_plottype_families

    // ---- find comma separating varpart from options ----
    local comma_pos = 0
    mata: _dash_comma_pos(st_local("rest"), "comma_pos")

    if `comma_pos' > 0 {
        mata: st_local("varpart", strtrim(substr(st_local("rest"), 1, `comma_pos' - 1)))
        mata: st_local("opts_raw", strtrim(substr(st_local("rest"), `comma_pos' + 1, .)))
    }
    else {
        mata: st_local("varpart", strtrim(st_local("rest")))
        local opts_raw ""
    }

    // ---- the option text is handed to -syntax- as typed ----
    // Option keys used to be rewritten here by Mata before -syntax- saw
    // them, into an `opts_exp' copy.  That pre-pass is gone: dash.ado
    // declares Stata's own measured minimum abbreviations, so Stata
    // resolves prefixes itself, and opts_raw is what -syntax- reads.

    // ---- parse varlist + if/in using type-appropriate syntax program ----
    // Determine varpart syntax group for this plot type, by its family
    // (_dash_plottype_families):
    //   1v  : _pt_univar   histogram kdensity
    //   3v  : _pt_range    rarea rbar rspike rcap rline rconnected rcapsym
    //                      rscatter tsrline
    //   4v  : _pt_pc       pcspike pcarrow pcbarrow pcscatter pccapsym
    //   4v  : _pt_rangept  rpcap rpspike (y1 y2 y3 x; WP-31 B1)
    //   any : _pt_literal  scatteri pci pcarrowi function
    //
    // pcscatter takes FOUR VARIABLES in Stata -- `pcscatter y1 x1 y2 x2' --
    // and was routed to the literal parser, which wrote its variable names
    // into the spec as bare identifiers inside a JSON array:
    //     "values":[[mpg,weight],[mpg,price]]
    // which is not valid JSON.  The renderer read nothing from it and drew
    // an empty plot region, with rc 0 and no warning.
    //   std : everything else (including dot)

    // s() is not cleared when an sclass program starts, and the weight is
    // read below from s(_weight) and s(_wexp), which a varpart parser sets
    // only when the segment HAS a weight.  The `sreturn clear' further down
    // comes after the weight checks, so a command refused between the two
    // -- lowess or histogram refusing the weight, a weight expression, a
    // non-integer or negative fweight, tsline with no time variable -- left
    // its weight in s(), and the next dash command, written with no weight
    // at all, read it as its own; `dash clear' does not reach s().
    // Measured at 4ede074: after `dash lowess mpg weight [aw=price]'
    // (r(101)), `dash lfit mpg weight, name(g1)' registered an lfit
    // weighted by price; after a refused [aw=price+1], every weighted type
    // was refused with that expression's message; a scatter's note named
    // [aweight] (test_statistical_options.cscript SO-93..SO-96).  Nothing
    // this program reads from s() is set before this line: its caller saved
    // what it needed from _dash_parse_graph_opts before the segment loop.
    sreturn clear

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

    if `: list ptype in _pt_univar' {
        _dash_parse_varpart_1v `macval(varpart)'
        local yvar    = word("`s(varlist)'", 1)
        mata: st_local("if_cl", st_global("s(if_clause)"))
        mata: st_local("in_cl", st_global("s(in_clause)"))
    }
    else if `: list ptype in _pt_range' {
        _dash_parse_varpart_3v `macval(varpart)'
        local vl = "`s(varlist)'"
        local nv : word count `vl'
        // twoway's count, measured 24sep2026 with the console binary: one
        // variable is "too few variables specified", r(102); two are
        // "rscatter requires 3 variables: mpg weight", r(102), and four or
        // more the same words, r(103) -- for every range type in each
        // form, one-line, grouped or after ||.  With two, dash registered
        // the layer with no x and the render stopped in a KeyError
        // traceback, r(7102) (rspike drew nothing, rc 0): BUGS.md, S2.
        // tsrline takes two, and is counted below, after tsset.
        if "`ptype'" != "tsrline" & `nv' != 3 {
            if `nv' == 1 {
                display as error "too few variables specified"
                exit 102
            }
            mata: _dash_say("err", "`ptype' requires 3 variables: ", st_local("vl"), "")
            exit cond(`nv' < 3, 102, 103)
        }
        local yvar1 = word("`vl'", 1)
        local yvar2 = word("`vl'", 2)
        local xvar  = word("`vl'", 3)
        // twoway tsrline y1 y2: two variables, drawn against the time
        // variable tsset set -- there is no x to give.  Measured
        // 23sep2026: `twoway tsrline lo hi' is rc 0 on tsset data and
        // r(111) ("time variable not set") without, and a third variable is
        // r(103) ("rline requires 3 variables: lo hi turn t").  dash used
        // to read a third variable as the x and draw against it, a picture
        // twoway refuses to draw (test_help_claims_1.cscript HC1-09).
        if "`ptype'" == "tsrline" {
            // tsset first, as twoway asks it first: `tsrline lo hi t' on
            // un-tsset data is r(111) there, not r(103).
            if `"`_dta[_TStvar]'"' == "" {
                display as error "dash: tsrline needs a time variable: " ///
                    "tsset your data first, as twoway tsrline does."
                exit(111)
            }
            // twoway draws `rline y1 y2 t' and counts that: `tsrline
            // mpg' is "rline requires 3 variables: mpg t", r(102), and
            // three are the same words, r(103) (measured 24sep2026).
            if `nv' != 2 {
                mata: _dash_say("err", "rline requires 3 variables: ", ///
                    st_local("vl") + " " + st_global("_dta[_TStvar]"), "")
                exit cond(`nv' < 2, 102, 103)
            }
            local xvar `"`_dta[_TStvar]'"'
        }
        mata: st_local("if_cl", st_global("s(if_clause)"))
        mata: st_local("in_cl", st_global("s(in_clause)"))
    }
    else if `: list ptype in _pt_pc' {
        _dash_parse_varpart_4v `macval(varpart)'
        local vl = "`s(varlist)'"
        local nv : word count `vl'
        // twoway: one variable "too few variables specified", r(102); two
        // or three "pcspike requires 4 variables: mpg weight", r(102);
        // five or more the same words, r(103) (measured 24sep2026).
        if `nv' != 4 {
            if `nv' == 1 {
                display as error "too few variables specified"
                exit 102
            }
            mata: _dash_say("err", "`ptype' requires 4 variables: ", st_local("vl"), "")
            exit cond(`nv' < 4, 102, 103)
        }
        local y1var = word("`vl'", 1)
        local x1var = word("`vl'", 2)
        local y2var = word("`vl'", 3)
        local x2var = word("`vl'", 4)
        mata: st_local("if_cl", st_global("s(if_clause)"))
        mata: st_local("in_cl", st_global("s(in_clause)"))
    }
    else if `: list ptype in _pt_rangept' {
        // rpcap and rpspike (WP-31 B1): y1 y2 y3 x, a range from y1 to y2
        // at x and a marker at y3 (twoway_y3xview_parse).  twoway's
        // count, measured 14oct2026 (test/fixtures/rangept_truth.json
        // counts.*): one variable "too few variables specified"; two,
        // three or five "you must specify four variables with twoway
        // rpcap", r(102) below four and r(103) above.
        _dash_parse_varpart_4v `macval(varpart)'
        local vl = "`s(varlist)'"
        local nv : word count `vl'
        if `nv' != 4 {
            if `nv' == 1 {
                display as error "too few variables specified"
                exit 102
            }
            display as error "you must specify four variables with twoway `ptype'"
            exit cond(`nv' < 4, 102, 103)
        }
        local yvar1 = word("`vl'", 1)
        local yvar2 = word("`vl'", 2)
        local yvar  = word("`vl'", 3)
        local xvar  = word("`vl'", 4)
        mata: st_local("if_cl", st_global("s(if_clause)"))
        mata: st_local("in_cl", st_global("s(in_clause)"))
    }
    else if `: list ptype in _pt_contour' {
        // contour and contourline (WP-31 B4b): z y x, as
        // twoway_zyx2view_parse reads them.  twoway's count, measured
        // 15oct2026 (test/fixtures/contour_truth.json refuse.counts_*):
        // one variable "too few variables specified"; two, four or five
        // "<type> requires 3 variables: <varlist>", r(102) below three and
        // r(103) above.
        _dash_parse_varpart_3v `macval(varpart)'
        local vl = "`s(varlist)'"
        local nv : word count `vl'
        if `nv' != 3 {
            if `nv' == 1 {
                display as error "too few variables specified"
                exit 102
            }
            display as error "`ptype' requires 3 variables: `vl'"
            exit cond(`nv' < 3, 102, 103)
        }
        local zvar = word("`vl'", 1)
        local yvar = word("`vl'", 2)
        local xvar = word("`vl'", 3)
        mata: st_local("if_cl", st_global("s(if_clause)"))
        mata: st_local("in_cl", st_global("s(in_clause)"))
    }
    else if `: list ptype in _pt_literal' {
        _dash_parse_varpart_any `macval(varpart)'
        if "`ptype'" == "function" {
            // The text as typed, `y =' and all, for the generator
            // (_dash_fn_points evaluates it after every plot is read; WP-29
            // P0.6).
            mata: st_local("_fn_raw", strtrim(st_global("s(vals)")))
            // The y name twoway keys and titles the layer by: the first
            // token when it is a Stata name followed by `=' (twoway__function_gen's
            // confirm name), any Unicode letter or `_' first, at most 32
            // characters; "" otherwise, read in Mata by value.
            mata: st_local("_fn_yname", (ustrregexm(strtrim(st_global("s(vals)")), "^([\p{L}_][\p{L}\p{N}_]{0,31})[ ]*=") ? ustrregexs(1) : ""))
            // Remove that "name =" prefix, by the same pattern, in Mata: an
            // expression holding "' -- strlen("'x") -- ended the compound
            // quotes it was cut in (test_json_escaping.cscript JSE-47).
            mata: st_local("vals", ustrregexra(strtrim(st_global("s(vals)")), "^[\p{L}_][\p{L}\p{N}_]{0,31}[ ]*=[ ]*", ""))
            local expr : copy local vals
            // No expression is refused in twoway's words: "expression
            // required", r(100), and after a `y =', "nothing found where
            // expression expected", r(111) -- with the comma glued, spaced
            // or absent, in parentheses, after ||, or with only an if, an
            // in or a weight (measured 24sep2026; P1A-71).  dash said
            // "something required", r(100), for the first, and registered
            // `function y =' with rc 0, drawn as an empty layer.
            if !`: length local expr' {
                mata: st_local("_fn_none", strofreal(st_global("s(vals)") == ""))
                if `_fn_none' {
                    display as error "expression required"
                    exit 100
                }
                display as error "nothing found where expression expected"
                exit 111
            }
            // Whatever else twoway refuses in the expression, it refuses
            // when it evaluates it: _dash_plot hands the text to the
            // generator once every plot and by() are checked.
        }
        else {
            mata: st_local("vals", st_global("s(vals)"))
        }
        mata: st_local("if_cl", st_global("s(if_clause)"))
        mata: st_local("in_cl", st_global("s(in_clause)"))
        if `: list ptype in _pt_imm' {
            // twoway's immediate values, one record each:
            //     scatteri  #y #x            [(#clockpos)] ["text for label"]
            //     pci       #y1 #x1 #y2 #x2  [(#clockpos)] ["text for label"]
            //     pcarrowi  #y1 #x1 #y2 #x2  [(#clockpos)] ["text for label"]
            // read in Mata, as a value, as twoway's own parsers read them,
            // and written one record per point, segment or arrow: the
            // coordinates, then "label",clock when either is given.  The
            // grammar and what twoway does with each case are measured in
            // dash_parse.mata, section 2c.  What twoway refuses is refused
            // with its return code, r(198), the token shown as written;
            // what it drops at the end is dropped too -- and named, where
            // twoway says nothing.
            //
            // scatteri and pci used to be written token by token as they
            // were typed, checked only for an even count: `dash pci 0 0 0
            // abc' and `dash scatteri .5 3000' registered, rc 0, as
            // "values":[[0,0],[0,abc]] and [[.5,3000]], which are not JSON,
            // and the render stopped on a JSONDecodeError, r(7102)
            // (measured 23sep2026; test_parser.cscript P1A-60..67).
            if "`ptype'" == "scatteri" {
                local _imm_w    2
                local _imm_unit "point"
                local _imm_nw   "two"
                local _imm_xy   "#y #x"
            }
            else {
                local _imm_w    4
                local _imm_unit = cond("`ptype'" == "pci", "segment", "arrow")
                local _imm_nw   "four"
                local _imm_xy   "#y1 #x1 #y2 #x2"
            }
            mata: _dash_immediate(st_local("vals"), `_imm_w')
            // What ends twoway's loop early: a quoted "" where a record's
            // last coordinate belongs.
            local _imm_q = char(34) + char(34)
            local _imm_empty `"`_imm_q' where a `_imm_unit''s last number belongs ends the list, as in twoway `ptype'."'
            if "`_pci_err'" == "point" {
                mata: _dash_say("err", "dash: `ptype' takes `_imm_nw' numbers for each `_imm_unit', `_imm_xy'; '", st_local("_pci_bad"), "' is not a number.")
                display as error `"      Each `_imm_unit' is `_imm_xy' [(#clockpos)] ["text for label"], as in twoway `ptype'."'
                exit 198
            }
            if "`_pci_err'" == "position" {
                mata: _dash_say("err", "dash: `ptype': invalid position, ", st_local("_pci_bad"), "; a clock position is a number from 0 to 12.")
                exit 198
            }
            if "`_pci_err'" == "none" {
                display as error "dash: `ptype' needs at least one `_imm_unit', `_imm_nw' numbers `_imm_xy'."
                if "`_pci_stop'" == "empty" {
                    mata: _dash_say("err", "      '", st_local("_pci_left"), "': " + st_local("_imm_empty"))
                }
                else if `_pci_hasleft' {
                    mata: _dash_say("err", "      '", st_local("_pci_left"), "' is too little for one.")
                }
                exit 198
            }
            if "`_pci_stop'" == "empty" {
                mata: _dash_note("dash: `ptype' ignored '", st_local("_pci_left"), "' at the end: " + st_local("_imm_empty"))
            }
            else if `_pci_hasleft' {
                mata: _dash_note("dash: `ptype' ignored '", st_local("_pci_left"), "' at the end, too little for another `_imm_unit' (`_imm_xy'), as twoway does.")
            }
            // twoway pci is an immediate pcspike: its serset carries the
            // labels and it draws none of them (measured from its SVG
            // export, with mlabcolor() and mlabposition() or without).
            // Neither does dash -- and it says so, where twoway is silent.
            if "`ptype'" == "pci" & `_pci_nlab' > 0 {
                mata: _dash_note("dash: pci draws no labels, as twoway pci draws none; a scatteri layer can label a point.", "", "")
            }
        }
    }
    else {
        // Standard: the LAST variable is x; every variable before it is a
        // y-variable and becomes its own plot, exactly as twoway does.
        //   twoway scatter mpg price weight  ->  two series
        // dash used to keep word 1 and the last word and silently discard
        // everything between, so that command drew ONE series and half the
        // user's data vanished with no error and no warning.
        //
        // No variable at all is twoway's refusal, "varlist required",
        // r(100), which -syntax- gives in its own words.  The parse was
        // skipped when there was nothing to parse, so `dash scatter ,
        // name(g1)' registered a graph with no variables, rc 0 -- and line,
        // connected, area, bar, spike, dropline, dot, the fits, the
        // smoothers and tsline likewise -- and the bare `dash scatter' was
        // refused as "no variables identified in plot specification",
        // r(198) (measured 24sep2026; test_parser.cscript P1A-69).
        // Time-series operators where twoway takes them (WP-30 P1.7): the
        // fractional-polynomial fits and the smoothers refuse them, as
        // twoway does, r(101).
        // Block form: the one-line `if exp command' form expanded the
        // command a second time, so a qualifier holding `=filewrite()'
        // ran (test_parser.cscript P1A-80, TSO-15).
        local _pt_nots "fpfit fpfitci lowess lpoly lpolyci"
        if `: list ptype in _pt_nots' {
            _dash_parse_varpart_std `macval(varpart)'
        }
        else {
            _dash_parse_varpart_ts `macval(varpart)'
        }
        local vl = "`s(varlist)'"
        local nv : word count `vl'
        local yvar = word("`vl'", 1)
        if `: list ptype in _pt_ts' {
            // twoway tsline y1 [y2 ...]: EVERY variable is a series,
            // each drawn against the time variable tsset set; there is
            // no x to give.  Measured 23sep2026 from twoway's saved
            // .gph: `tsline mpg turn' on tsset data is two lines, mpg
            // and turn, each against t -- and dash drew mpg against
            // turn, reading the last variable as the x.  Without tsset
            // twoway refuses every form, r(111) ("time variable not
            // set"), and so does dash (test_help_claims_1.cscript
            // HC1-09).  tsrline, a range type, is read above.
            local xvar `"`_dta[_TStvar]'"'
            if `"`xvar'"' == "" {
                display as error "dash: `ptype' needs a time variable: " ///
                    "tsset your data first, as twoway `ptype' does."
                exit(111)
            }
            // WP-19: one plot object per series, held to the plot limit
            // before any is built, as the y variables below are.
            if `nv' > 1 {
                _dash_limit, name(plots)
                if `nv' > r(value) {
                    if `nsegs' > 1 _dash_plot_cap_refuse `r(value)' `r(ceiling)'
                    else           _dash_plot_cap_refuse `r(value)' `r(ceiling)' `nv'
                }
            }
            local yvarlist "`vl'"
        }
        else if `nv' >= 3 & `: list ptype in _pt_onefit' {
            // A fit or smoother takes one y and one x.  twoway, measured
            // 24sep2026: "too many variables specified: mpg weight price",
            // r(103), on lfit qfit lfitci qfitci fpfit fpfitci mspline
            // mband; lowess, lpoly and lpolyci say it without the list.
            // dash drew one fit per y variable, rc 0 (P1A-79).
            if `: list ptype in _pt_onefit_bare' {
                display as error "too many variables specified"
            }
            else {
                mata: _dash_say("err", "too many variables specified: ", st_local("vl"), "")
            }
            exit 103
        }
        else if `nv' >= 2 {
            local xvar = word("`vl'", `nv')
            local nyv = `nv' - 1
            // WP-19: one plot object is built per y variable below, so
            // a segment whose y variables alone pass the plot limit is
            // refused here, before any of them is built.  In a graph
            // of several segments only "more than the limit" is known.
            if `nyv' > 1 {
                _dash_limit, name(plots)
                if `nyv' > r(value) {
                    if `nsegs' > 1 _dash_plot_cap_refuse `r(value)' `r(ceiling)'
                    else           _dash_plot_cap_refuse `r(value)' `r(ceiling)' `nyv'
                }
            }
            local yvarlist ""
            forvalues vi = 1/`nyv' {
                local _thisy = word("`vl'", `vi')
                local yvarlist `"`yvarlist' `_thisy'"'
            }
            local yvarlist = strtrim(`"`yvarlist'"')
        }
        else {
            // Every other type on this path takes a y AND an x (tsline,
            // which takes its x from tsset, is read above).  Measured
            // 22sep2026 with the console binary: `twoway bar price',
            // `twoway scatter mpg', and spike, area, line, dropline,
            // connected, dot, the fit and the smoother types all say
            // "too few variables specified" r(102).  dash registered
            // such a segment with rc 0 and the build then died in
            // Python on the empty x column, r(7102).  Refused here,
            // before any JSON is written, in twoway's words: dash said
            // "dash: scatter requires a y and an x variable (got: mpg)"
            // (BUGS.md, S3 batch; test_parser.cscript P1A-82).
            display as error "too few variables specified"
            exit(102)
        }
        mata: st_local("if_cl", st_global("s(if_clause)"))
        mata: st_local("in_cl", st_global("s(in_clause)"))
    }

    // Strip the "if"/"in" keyword prefix that syntax leaves in the macros.
    // Stata may store `if' as either " if <expr>" (with leading space) or
    // "if <expr>" (without leading space) depending on the context.
    // Using regexr() to strip the prefix robustly handles both cases.  In
    // Mata, by value: in compound quotes,  if make == "' or 1 or '"  ended
    // them (measured 24sep2026; test_json_escaping.cscript JSE-44).
    mata: st_local("if_expr", strtrim(regexr(st_local("if_cl"), "^[ ]*if[ ]+", "")))
    mata: st_local("in_expr", strtrim(regexr(st_local("in_cl"), "^[ ]*in[ ]+", "")))
    // Each variable the qualifier abbreviates is written out, as Stata
    // read it against the data in memory: -syntax- has just evaluated it
    // there.  The renderer evaluates the qualifier against the exported
    // columns, which carry full names, so `if dis > 100' named no column
    // and was skipped, every row drawn (measured 24sep2026;
    // test_qualifier_literals.cscript QL-22).  Literals are left as typed.
    mata: st_local("if_expr", _dash_qual_expand(st_local("if_expr")))

    // ---- The plot's sample, for the checks made here ----
    // A weight's values and histogram's start() are checked over the rows
    // the plot draws: its own if and in, and the graph's, written after
    // the plot groups (_dash_plot hands it over in $dash__gq_if and
    // $dash__gq_in, read by value).  The graph's was left out, so
    // `(lfit mpg weight [fw=halfint]) if foreign==1' was refused, r(401),
    // for rows twoway never reads (WP-27; test_help_claims_6.cscript
    // HC6-56).  Two ranges cannot share one `in': the graph's is then
    // marked in a temporary variable and read as a condition.
    mata: st_local("_gq_if_s", st_global("dash__gq_if"))
    mata: st_local("_gq_in_s", st_global("dash__gq_in"))
    local _ps_if ""
    if `: length local if_expr' {
        local _ps_if `"(`macval(if_expr)')"'
    }
    if `: length local _gq_if_s' {
        if `: length local _ps_if' {
            local _ps_if `"`macval(_ps_if)' & (`macval(_gq_if_s)')"'
        }
        else {
            local _ps_if `"(`macval(_gq_if_s)')"'
        }
    }
    local _ps_in ""
    if `: length local in_expr' & `: length local _gq_in_s' {
        tempvar _ps_mark
        quietly gen byte `_ps_mark' = 1 in `macval(_gq_in_s)'
        if `: length local _ps_if' {
            local _ps_if `"`macval(_ps_if)' & !missing(`_ps_mark')"'
        }
        else {
            local _ps_if `"!missing(`_ps_mark')"'
        }
        local _ps_in : copy local in_expr
    }
    else if `: length local in_expr' {
        local _ps_in : copy local in_expr
    }
    else if `: length local _gq_in_s' {
        local _ps_in : copy local _gq_in_s
    }
    local _psq ""
    if `: length local _ps_if' {
        local _psq `"if `macval(_ps_if)'"'
    }
    if `: length local _ps_in' {
        local _psq `"`macval(_psq)' in `macval(_ps_in)'"'
    }

    // ---- parse options (clear stale sreturn values first) ----
    // The varpart parsers sreturn the weight TYPE in s(_weight) and the
    // weight EXPRESSION, without its leading `=', in s(_wexp).  Both are
    // saved before the clear below destroys them.
    mata: st_local("_seg_weight", st_global("s(_weight)"))
    mata: st_local("_seg_wexp", st_global("s(_wexp)"))
    // The weight text as typed, for twoway's yxview reading (WP-31 A5b).
    local _seg_wexp_typed : copy local _seg_wexp

    // ---- weights (WP-18) ----
    // Which type honours which weight is twoway's own acceptance table,
    // measured 23sep2026 (test/fixtures/stat_truth.json, weight_acceptance):
    // iweight is refused on every type; lowess refuses every weight;
    // histogram takes fweight only; kdensity, lpoly and lpolyci refuse
    // pweight; the fit, smoother and band types take aw, fw and pw.  Each
    // refusal is twoway's, r(101), in twoway's words.
    // WP-31 C9: the marker types size their markers by the weight
    // (yxview.class _draw_weighted_points); the markerless glyph types take
    // a weight and draw nothing different, as twoway does, and say nothing
    // (test/fixtures/weighted_markers_truth.json W01-W10).
    local _wt_markers "scatter connected dot dropline rscatter rcapsym rconnected pcscatter pccapsym rpcap rpspike"
    local _wt_honoured "lfit qfit lfitci qfitci lpoly lpolyci fpfit fpfitci histogram kdensity mspline mband `_wt_markers'"
    // The types that refuse a pweight: a list, like every plot-type family,
    // rather than a string inlist() (TR-22.4).
    local _wt_nopw "kdensity lpoly lpolyci"
    if `"`_seg_weight'"' != "" {
        // scatteri, pci and pcarrowi take no weight: twoway refuses an
        // aweight, fweight or pweight there with r(198), "weights not
        // allowed" (measured 23sep2026; an iweight syntax has already
        // refused, r(101), as twoway does).  function takes one and draws
        // nothing different, and is named in the note below by type.
        if `: list ptype in _pt_imm' {
            display as error "weights not allowed"
            exit 198
        }
        local _wt_refused ""
        // WP-31 B4b: twoway's zyx2 parser takes no weight, "weights not
        // allowed", r(101) (contour_truth.json refuse.weight).
        if `: list ptype in _pt_contour' {
            local _wt_refused "weights not allowed"
        }
        else if "`_seg_weight'" == "iweight" {
            local _wt_refused "iweights not allowed"
        }
        else if "`ptype'" == "lowess" {
            local _wt_refused "weights not allowed"
        }
        else if "`ptype'" == "histogram" & "`_seg_weight'" != "fweight" {
            local _wt_refused "`_seg_weight's not allowed"
        }
        else if `: list ptype in _wt_nopw' & "`_seg_weight'" == "pweight" {
            local _wt_refused "pweights not allowed"
        }
        if `"`_wt_refused'"' != "" {
            display as error "`_wt_refused'"
            exit 101
        }
    }
    if `"`_seg_weight'"' != "" & `: list ptype in _wt_honoured' {
        // The data reach the renderer as exported, one column per
        // variable.  A weight that is ONE existing variable is that
        // column: unab expands an abbreviation (`[aw=pri]') to the full
        // name the renderer reads.  It reads a VARLIST, so the expression
        // must first be one name: unab resolves the range `price-price'
        // to price, where twoway weights by the expression price-price,
        // which is zero (measured 23sep2026, rc 0).  confirm name accepts
        // any Stata name, Unicode included, and nothing else.
        local _wx ""
        capture confirm name `macval(_seg_wexp)'
        if !_rc {
            capture unab _wx : `macval(_seg_wexp)'
        }
        if !_rc & `: word count `_wx'' == 1 {
            local _seg_wexp "`_wx'"
        }
        else {
            // An expression (WP-31 A5): twoway evaluates `[aw=price+1]'
            // and `[aw=L.price]' itself (test/fixtures/
            // weight_operator_truth.json weights.*).  A canonical
            // time-series term takes the __dasht route at export
            // (_dash_tsop_rewrite), anything else is generated into
            // __dashw<k> there (_dash_wexp_gen).  Checked now, with
            // Stata's own generate and its words and code, so a bad
            // expression is refused at registration; a text holding a
            // backtick, dollar sign, quote, semicolon, tab or line break
            // never reaches a command line (_dash_wexp_ok).  The spec
            // carries the expression as typed.
            mata: st_local("_wok", strofreal(_dash_wexp_ok(st_local("_seg_wexp"))))
            if !`_wok' {
                mata: _dash_say("err", "dash: [`_seg_weight'=", st_local("_seg_wexp"), "] cannot be evaluated")
                exit 198
            }
            // Quietly, as twoway says nothing of the missing values an
            // expression makes; a refusal is run again noisily, so Stata's
            // own words are shown with its code.
            tempvar _wt
            capture quietly generate double `_wt' = (`macval(_seg_wexp)')
            if _rc {
                local _wrc = _rc
                capture noisily generate double `_wt' = (`macval(_seg_wexp)')
                exit `_wrc'
            }
            capture drop `_wt'
            local _wx "(`macval(_seg_wexp)')"
        }
        // twoway's own checks of the weight's values, measured 23sep2026:
        // a non-integer fweight is r(401) "may not use noninteger frequency
        // weights" on lfit lfitci lpoly lpolyci histogram kdensity; a
        // negative fweight is r(402) "negative weights encountered" on
        // lpoly lpolyci histogram kdensity, and so is a negative aweight on
        // lpoly lpolyci kdensity.  Elsewhere the command is accepted and
        // the renderer does what twoway draws: lfit, qfit, lfitci and
        // qfitci fit as if `if w > 0'; qfit, qfitci, fpfit and fpfitci
        // draw nothing for a non-integer fweight, and fpfit and fpfitci
        // nothing for any negative weight (regress and fracpoly "could not
        // fit model"); mspline and mband ignore the weight.  Each check
        // runs over the plot's own if/in sample -- a bad weight on a row
        // whose y is missing still refuses, one outside the if does not --
        // and a missing weight drops its observation without an error.
        // The graph's qualifier is part of that sample (_psq, above) --
        // except on kdensity, which twoway checks over its own qualifier
        // alone: `(kdensity mpg [aw=w]) if foreign==1', w negative on the
        // domestic cars only, is r(402) in twoway, and [fw=] non-integer
        // there r(401), where the same weights inside the parentheses, or
        // on lfit, lfitci, lpoly, lpolyci or histogram with the graph's
        // qualifier, are rc 0 (measured 24sep2026; HC6-56).
        local _wq : copy local _psq
        if "`ptype'" == "kdensity" {
            local _wq ""
            if `: length local if_expr' {
                local _wq `"if (`macval(if_expr)')"'
            }
            if `: length local in_expr' {
                local _wq `"`macval(_wq)' in `macval(in_expr)'"'
            }
        }
        local _w_neg ""
        if "`_seg_weight'" == "fweight" local _w_neg "lpoly lpolyci histogram kdensity"
        if "`_seg_weight'" == "aweight" local _w_neg "lpoly lpolyci kdensity"
        if "`_seg_weight'" == "fweight" {
            local _fw_int "lfit lfitci lpoly lpolyci histogram kdensity"
            if `: list ptype in _fw_int' {
                capture assert `_wx' == floor(`_wx') | missing(`_wx') `macval(_wq)'
                if _rc {
                    display as error "may not use noninteger frequency weights"
                    exit 401
                }
            }
        }
        if `: list ptype in _w_neg' {
            capture assert `_wx' >= 0 | missing(`_wx') `macval(_wq)'
            if _rc {
                display as error "negative weights encountered"
                exit 402
            }
        }
    }

    // WP-31 C11 (D6): twoway counts lpoly's and lpolyci's sample before it
    // reads their options -- `twoway lpolyci mpg weight if _n == 1,
    // pwidth(0)' and `bwidth(abc)' there are "insufficient observations",
    // r(2001) (estimator_edges_truth.json lp.D6, lp.D6_bw) -- so one row
    // is refused here, before the parser; the count below repeats it for
    // the other types.  Under by() twoway answers panel by panel, later.
    local _d6_fam "lpoly lpolyci"
    if `: list ptype in _d6_fam' & !`: length global dash__g_by' {
        mata: st_local("_d6_by", strofreal(ustrregexm(st_local("opts_raw"), "(^|[ ,])by[(]")))
        if !`_d6_by' {
            local _d6_c "!missing(`yvar', `xvar')"
            if `"`_seg_weight'"' != "" {
                local _d6_c "`_d6_c' & !missing((`_seg_wexp')) & (`_seg_wexp') > 0"
            }
            if `: length local _ps_if' {
                local _d6_c `"`_d6_c' & `macval(_ps_if)'"'
            }
            local _d6_in ""
            if `: length local _ps_in' local _d6_in `"in `macval(_ps_in)'"'
            quietly count if `macval(_d6_c)' `macval(_d6_in)'
            if r(N) == 1 {
                display as error "insufficient observations"
                exit 2001
            }
        }
    }
    // WP-35 DT-15: the first spelling twoway refuses that dash once took
    // (ytitle2(), malpha() ...), found on the options as typed and refused
    // after _dash_refuse_unbound, once no word typed before it is refused
    // first: twoway names the first word of a list it does not take.
    mata: st_local("_do_w", _dash_dashonly_typed(st_local("opts_raw"), 0))
    local _do_wpre : copy local _do_pre
    // WP-35 syn:SD-3: the plot's own p<j>() and the graph's p<k>() for it,
    // merged into its options as twoway applies them (_dash_p_apply).
    _dash_p_apply `ptype' `: word count `yvarlist'' `"`macval(opts_raw)'"'
    sreturn clear
    local _rp_gund_out ""
    local _ptype_typed "`ptype'"
    local _rc_kind ""
    local _fn_rtyped ""
    local _fn_rnorm ""
    local _fn_nval ""
    // A weight-only segment goes through the parser and the validation
    // too, so the weight keys are in s() for the JSON writer and the flag
    // rules run on every segment; the parser takes an empty option list.
    if `: length local opts_raw' | `"`_seg_weight'"' != "" {
        // axis(2) on an axis option -> ytitle2(), ylabel2(), ytick2(),
        // yline2(), yscale2() (x too) before the repeat merge folds copies
        // of one option into one (WP-28 B3, WP-29 P0.5, _dash_route_axis2).
        // The raw text is kept for _dash_plot's axis check, which refuses
        // what twoway refuses once every layer's axis is known.
        local _opts_pre : copy local opts_raw
        mata: st_local("opts_raw", _dash_route_axis2(st_local("opts_raw")))
        _dash_parse_plot_opts , `macval(opts_raw)'
        c_local _seg_axreq_raw : copy local _opts_pre
        // An option it declares whose value -syntax- could not bind:
        // refused as twoway refuses it, not named as unsupported.
        _dash_refuse_unbound _dash_parse_plot_opts `"`macval(opts_raw)'"'
        // WP-35 DT-15: the spelling found above, refused in twoway's words
        // with a line naming twoway's spelling (DECISIONS.md P4-7, P4-9),
        // after the refusal of any word typed before it.
        if `: length local _do_w' {
            if `: length local _do_wpre' {
                sreturn clear
                _dash_parse_plot_opts , `macval(_do_wpre)'
                _dash_refuse_unknown _dash_parse_plot_opts `ptype' `"`macval(_do_wpre)'"'
            }
            mata: _dash_dashonly_say(st_local("_do_w"), "")
        }
        // The statistical types' spellings twoway reads (WP-35 35-03).
        local _fsw_nowt ""
        _dash_fold_stat_words "`ptype'" `"`macval(opts_raw)'"'
        // The first word twoway does not take, in the list's order
        // (WP-32): an unknown word, one in upper case, a spelling short of
        // twoway's minimum, title2().
        _dash_refuse_unknown _dash_parse_plot_opts `ptype' `"`macval(opts_raw)'"'
        // Two omit options in this list, as twoway refuses them (WP-35
        // basic:PT-8; _dash_plot checks the whole command).
        mata: st_local("_omp", _dash_omit_pair(st_local("opts_raw"), st_local("ptype")))
        if `: length local _omp' {
            mata: _dash_say("err", "option ", st_local("_omp"), " not allowed")
            exit 198
        }
        // jitter() spelled shorter than twoway's minimum (WP-31 A3d).
        _dash_refuse_jit
        // name() spelled shorter than twoway's minimum (WP-31 A3b).
        _dash_refuse_nam
        // aspectratio() spelled shorter than twoway's minimum (WP-31 A3c).
        _dash_refuse_asp
        // A second name() in this option list: -syntax- binds the first to
        // NAME() and leaves any other to the catch-all, which is read by
        // value -- it is the user's text.
        mata: st_local("_seg_name2", strofreal(_dash_has_name_opt(st_global("s(_unknown)"))))
        if `_seg_name2' _dash_refuse_second_name
        // An option written in upper case -- ATOBS, MCOLOR(red) -- is no
        // option twoway takes: refused as twoway refuses it, naming the
        // first word it does not take (_dash_refuse_foreign).
        _dash_refuse_foreign _dash_parse_plot_opts `ptype' `"`macval(opts_raw)'"'
        // An option given more than once: read as twoway reads it -- the
        // last copy, the copies merged, or refused (_dash_opts_repeats).
        _dash_opts_repeats _dash_parse_plot_opts `ptype' `"`macval(opts_raw)'"'
        // Again: _dash_refuse_unknown, _dash_refuse_foreign and
        // _dash_opts_repeats parse the list again, which undoes the first
        // call's rewrites (WP-35 35-03).
        _dash_fold_stat_words "`ptype'" `"`macval(opts_raw)'"'
        if "`_fsw_subc'" == "off" {
            display as error "option subchar() not allowed"
            exit 198
        }
        if "`_fsw_subc'" == "many" {
            display as error "option subchar():  too many names specified"
            exit 103
        }
        if "`_fsw_subc'" == "bad" {
            mata: _dash_say("err", "", st_global("s(subchar)"), " invalid name")
            exit 198
        }
        if "`_fsw_n0'" == "bad" {
            display as error "option n() not allowed"
            exit 198
        }
        if "`_fsw_n0'" == "obs" {
            mata: _dash_say("err", "'", strtrim(st_global("s(n)")), "' invalid observation number")
            exit 198
        }
        if "`_fsw_nowt'" == "1" {
            display as error "option noweight not allowed"
            exit 198
        }
        // Two kernels, mlabfontface() (MLF-01) and a graph option given
        // twice, in that order, which twoway refuses only once every
        // plot's own options are read: each is held as the graph's pending
        // refusal (_dash_pend), raised after the last segment (WP-32).
        if `: length local _rp_kref' _dash_pend _dash_refuse_kernel `_rp_kref'
        _dash_refuse_mlabff 0 pend
        if `: length local _rp_gref' _dash_pend _dash_refuse_repeat `_rp_gref'
        // title2() and subtitle2(), which twoway has not (WP-31 D2).
        _dash_refuse_title2 g_ `"`macval(opts_raw)'"'
        // recast(), recastas() and type() as twoway reads them (WP-30
        // P1.8b), before connect(), as twoway sets the view type first: a
        // base, range, pc or time-series layer becomes the type it is
        // drawn as (its typed type kept as recast_from), a derived layer
        // keeps its type and is drawn as the target (options.recast).
        _dash_recast_opt "`ptype'"
        local _rc_kind   "`s(_recast_kind)'"
        local _rc_target "`s(_recast_target)'"
        local _rc_ts     "`s(_recast_ts)'"
        if inlist("`_rc_kind'", "base", "range2yx", "ts") local ptype "`s(_recast_type)'"
        if "`_rc_kind'" == "range2yx" local yvar "`yvar1'"
        // horizontal and vertical refused where twoway refuses them,
        // judged after recast() (WP-30 P1.9a): _dash_hz_check.
        tempname _hz_s
        mata: st_strscalar("`_hz_s'", st_local("opts_raw"))
        _dash_hz_check "`ptype'" "`_rc_target'" "`_rc_kind'" `_hz_s'
        // connect() and cmissing() as twoway reads them (WP-30 P1.8a): a
        // scatter y given a connect() element is twoway's connected type,
        // and the folds, checks and sort below read it as connected.  A
        // derived layer's are judged on the type it is drawn as.
        local _cn_judge "`ptype'"
        if "`_rc_kind'" == "derived" local _cn_judge "`_rc_target'"
        local _cn_n 1
        if `"`yvarlist'"' != "" local _cn_n : word count `yvarlist'
        _dash_connect_opt "`_cn_judge'" `_cn_n'
        local _cn_types `"`s(_cn_types)'"'
        local _cn_any   `"`s(_cn_any)'"'
        local _cn_ptype "`_cn_judge'"
        if "`_cn_judge'" == "scatter" & "`_cn_any'" == "1" local _cn_ptype connected
        // The derived layer's own options are checked as its own type;
        // the drawn type goes to the JSON as options.recast.
        local _rc_own "`_cn_ptype'"
        if "`_rc_kind'" == "derived" {
            local _rc_own "`ptype'"
            local _cn_types ""
            _dash_recast_s recast "`_cn_ptype'"
        }
        // pci and pcarrowi drawn as the pc type named (WP-31 C7).
        if "`_rc_kind'" == "literal" _dash_recast_s recast "`_rc_target'"
        // function's range() as typed, before validation normalises it
        // through numlist, which keeps 13 digits (WP-29 P0.6, S4-D5).
        if "`ptype'" == "function" mata: st_local("_fn_rtyped", st_global("s(range)"))
        // lowess's logit, or its off form, on another plot type: refused
        // naming the word as typed, as twoway names it -- scatter mpg
        // weight, lo is "option lo not allowed", r(198) -- where the flag
        // rule below named logit whatever was typed, and nolo, nologi and
        // nologit were taken in silence.  log and nolog are logging.
        if "`ptype'" != "lowess" {
            mata: st_local("_lt_typed", _dash_logit_typed(st_local("opts_raw")))
            if `: length local _lt_typed' {
                mata: _dash_say("err", "option ", st_local("_lt_typed"), " not allowed")
                display as error "      logit is an option of lowess alone; log is twoway's graph option logging."
                exit 198
            }
        }
        // barwidth() on rcap and rcapsym: refused naming the spelling as typed,
        // as twoway refuses it -- "option barw() not allowed", r(198) (measured
        // 03oct2026; WP-30 P1.17a).  bw() is left to _dash_fold_bw.
        local _cap_types rcap rcapsym
        if `: list ptype in _cap_types' {
            mata: st_local("_bwt_typed", _dash_barwidth_typed(st_local("opts_raw")))
            if `: length local _bwt_typed' {
                mata: _dash_say("err", "option ", st_local("_bwt_typed"), "() not allowed")
                exit 198
            }
        }
        // mlabvposition() (WP-30 P1.24): checked and counted as twoway
        // counts it, before mlabel()'s own rule (_dash_fold_mlab).
        _dash_fold_mlabv "`ptype'" "`yvar1' `yvar2' `yvar' `xvar'"
        _dash_fold_mlabr "`ptype'" "`yvar1' `yvar2' `yvar' `xvar'"
        _dash_fold_bw "`_rc_own'"
        if `"`_seg_weight'"' != "" & `: list ptype in _wt_honoured' {
            _dash_seg_weight_s "`_seg_weight'" "`_seg_wexp'"
        }
        local _sl_n 1
        if `"`yvarlist'"' != "" local _sl_n : word count `yvarlist'
        // WP-31 C5: the types twoway takes gap(), baroffset(), area(),
        // boundary and droplines() on; on any other "option gap() not
        // allowed", r(198), before any value is read (measured 14oct2026,
        // test/fixtures/kde_hist_fn_truth.json applies; nodropbase is
        // taken on every type).  Then, as twoway's parsers check them
        // before a value: boundary beside range() on kdensity, and
        // function's base() that is not a number -- twoway prints its
        // sentence and stops at the class's assignment, r(4026) (F04).
        local _c5_types_gap "histogram"
        local _c5_types_baroffset "area bar spike dropline dot rbar histogram"
        local _c5_types_area "kdensity"
        local _c5_types_boundary "kdensity"
        local _c5_types_droplines "function"
        foreach _c5o in gap baroffset area boundary droplines {
            mata: st_local("_c5v", strofreal(st_global("s(`_c5o')") != ""))
            if `_c5v' & !`: list _rc_own in _c5_types_`_c5o'' {
                local _c5p = cond("`_c5o'" == "boundary", "", "()")
                display as error "option `_c5o'`_c5p' not allowed"
                exit 198
            }
        }
        mata: st_local("_c5v", strofreal(st_global("s(boundary)") != "" & st_global("s(range)") != ""))
        if `_c5v' & "`_rc_own'" == "kdensity" {
            display as error "only one of options range() or boundary is allowed"
            exit 198
        }
        if "`_rc_own'" == "function" {
            mata: st_local("_c5b", st_global("s(base)"))
            if `: length local _c5b' {
                capture confirm number `_c5b'
                if _rc {
                    mata: _dash_say("err", "option base() incorrectly specified, ", st_local("_c5b"), " is not a number")
                    exit 4026
                }
            }
        }
        // WP-31 B4b: contour's options on contour and contourline only,
        // read as twoway's zyx2view parser reads them.
        _dash_contour_check "`_rc_own'"
        // WP-31 C8a: colorvar() dropped, unchecked, where twoway drops it.
        _dash_cv_drop "`_rc_own'" "`_cn_ptype'"
        _dash_validate_opts "`_rc_own'" `_sl_n'
        // lpoly's note when n() passes the rows in memory (WP-35 basic:PT-9,
        // value_codes_truth.json lpoly_n_100: twoway prints "(n() set to
        // 74)"): the rule of the renderer's _lpoly_grid_plan, which caps
        // the grid at the rows from 50 rows on.
        local _lpn "lpoly lpolyci"
        if `: list _rc_own in _lpn' {
            mata: st_local("_lpn", strofreal(c("N") >= 50 & strtoreal(st_global("s(n)")) < . & strtoreal(st_global("s(n)")) > c("N")))
            if `_lpn' display as text "(n() set to " c(N) ")"
        }
        // The fit options (WP-31 C4): on the types twoway takes them on,
        // their pairs with range(), fitplot()/ciplot() canonicalised.
        _dash_fit_opts_check "`_rc_own'"
        // WP-31 C5: twoway's bounds on gap() (0 <= # < 100) and area()
        // (# > 0), in its words (kde_hist_fn_truth H02 H03 K02 K06).
        mata: st_local("_c5v", st_global("s(gap)"))
        if `: length local _c5v' {
            if real("`_c5v'") < 0 | real("`_c5v'") >= 100 {
                display as error "option gap() must be between 0 and 100"
                exit 198
            }
        }
        mata: st_local("_c5v", st_global("s(area)"))
        if `: length local _c5v' {
            if !(real("`_c5v'") > 0) {
                display as error "option area() expects a positive number"
                exit 198
            }
        }
        // range(varname) read as two numbers over the plot's sample
        // (WP-31 C10a).
        tempname _fr_s
        mata: st_strscalar("`_fr_s'", st_local("_psq"))
        _dash_fold_range "`_rc_own'" `_fr_s'
        _dash_stylelist_check "`_cn_ptype'" `_sl_n'
        if "`ptype'" == "function" {
            mata: st_local("_fn_rnorm", st_global("s(range)"))
            mata: st_local("_fn_nval", st_global("s(n)"))
        }
        // Options dash draws on some types only, named on the others, and
        // colorvar() with several y variables refused (WP-31 C8a) -- after
        // the validation above, so a bad value is refused first, as twoway
        // refuses it (WP-23).
        _dash_fold_typed "`_cn_ptype'" `_sl_n' "`ptype'"
        // sort(varlist): checked as twoway checks it, after the repeats
        // are reduced, and honoured on the six joining types (WP-29 P0.1).
        // A time-series source recast joins in time order, as tsline's
        // sort(t) (twoway_tsline_parse.class:32; WP-30 P1.8b).
        if "`_rc_kind'" == "ts" | "`_rc_ts'" == "1" {
            local _so_six "line connected area rline rarea rconnected"
            if `: list ptype in _so_six' _dash_recast_s sort1 "`xvar'"
        }
        _dash_sort_opt "`_cn_ptype'"
        // twoway__histogram_gen.ado:102-107: a start() above the variable's
        // minimum over the plot's sample is r(198), discrete or not.  dash
        // drew it, the observations below start() silently left out of
        // every bar (the WP-18 review, 23sep2026).
        if "`ptype'" == "histogram" & `"`s(start)'"' != "" {
            // The plot's sample, the graph's qualifier in it (_psq).
            local _hq : copy local _psq
            quietly summarize `yvar' `macval(_hq)', meanonly
            if r(N) > 0 {
                if r(min) < `s(start)' & reldif(r(min), `s(start)') > 1e-5 {
                    display as error "option start() may not be larger than minimum of `yvar'"
                    exit 198
                }
            }
        }
    }

    // ---- A sample twoway's statistical command cannot draw ----
    // Measured 24sep2026 with the console binary, on no observations, on
    // a sample the plot's if/in or the graph's qualifier empties, on one
    // observation, and on samples missing values and weights empty
    // (test_parser.cscript P1A-80; BUGS.md, S3):
    //   histogram  _N == 0: "observation numbers out of range", r(198),
    //              whatever the qualifier or option; a sample emptied by
    //              a qualifier or by missing values is drawn, rc 0
    //   lpoly(ci)  none in the sample: "no observations", r(2000); one:
    //              "insufficient observations", r(2001)
    //   lfit(ci)   one: "(note:  regress could not fit model)", then
    //              "insufficient observations", r(2001)
    //   kdensity   one: "insufficient observations", r(2001)
    //   fpfit(ci)  none the if and in select: "(note:  fracpoly could not
    //              fit model)", then "observation numbers out of range",
    //              r(198); emptied by missing values, the note, rc 0
    //   mspline,   none the if and in select, and no bands(): "bands must
    //   mband      be between 1 and 200", r(198)
    // The sample is _psq -- the plot's if and in and the graph's
    // qualifier -- and, where it is counted, the rows whose variables are
    // not missing and, weighted, whose weight is above zero (a zero
    // fweight or a missing aweight leaves lpoly "no observations").  dash
    // registered each and drew an empty layer, rc 0.  What twoway draws
    // with a note -- lfit on none, qfit, fpfit on one -- the renderer
    // notes (GlyphMapper._mark_unfit).  Under by() twoway answers panel by
    // panel -- lfit with one car in a panel notes it and leaves the panel
    // out, rc 0 -- and _dash_plot answers it so, once the graph's by() is
    // known (P1A-83).  The qualifier is run as
    // -syntax- read it, by value (macval), once per count.
    mata: st_local("_ss_bands", st_global("s(bands)"))
    local _pt_fpfam "fpfit fpfitci"
    local _pt_bands "mspline mband"
    local _pt_lpfam "lpoly lpolyci"
    local _ss_types "histogram lpoly lpolyci lfit lfitci kdensity fpfit fpfitci mspline mband"
    mata: st_local("_ss_by", st_global("s(g_by)") + st_global("dash__g_by"))
    // Time-series operators (WP-30 P1.7), as twoway refuses them: by()
    // sorts the data on its variables, so an operated plot variable in any
    // layer is "not sorted", r(5) (measured on StataNow 19.5); and a bare
    // sort with an operated x is refused on the 18 types that sort on x,
    // in twoway's two lines, r(198).  Before anything is registered.
    local _ts_first ""
    foreach _tv in `yvarlist' `yvar' `yvar1' `yvar2' `xvar' `y1var' `x1var' `y2var' `x2var' {
        if strpos("`_tv'", ".") & "`_ts_first'" == "" local _ts_first `_tv'
    }
    if "`_ts_first'" != "" & `: length local _ss_by' {
        display as error "not sorted"
        mata: _dash_say("txt", "dash: twoway refuses by() with a time-series operator in a plot variable; generate the variable first, for example: generate double ", ///
            usubstr(strlower(subinstr(st_local("_ts_first"), ".", "", .)), 1, 32) + " = " + st_local("_ts_first"), "")
        exit 5
    }
    local _ts_sortx "scatter line connected area bar spike dropline dot mspline mband rarea rbar rspike rcap rline rconnected rcapsym rscatter rpcap rpspike"
    mata: st_local("_ts_sort", strofreal(st_global("s(sort)") != ""))
    if `_ts_sort' & strpos("`xvar'", ".") & `: list ptype in _ts_sortx' {
        display as error "factor-variable and time-series operators not allowed"
        display as error "option sort() incorrectly specified"
        exit 198
    }
    if `: list ptype in _ss_types' & !`: length local _ss_by' {
        local _ss_ifin ""
        if `: length local _ps_in' {
            local _ss_ifin `"in `macval(_ps_in)'"'
        }
        if "`ptype'" == "histogram" {
            if _N == 0 {
                display as error "observation numbers out of range"
                exit 198
            }
        }
        else if `: list ptype in _pt_fpfam' | ///
            (`: list ptype in _pt_bands' & !`: length local _ss_bands') {
            quietly count `macval(_psq)'
            if r(N) == 0 {
                if `: list ptype in _pt_fpfam' {
                    display as text "(note:  fracpoly could not fit model)"
                    display as error "observation numbers out of range"
                }
                else {
                    display as error "bands must be between 1 and 200"
                }
                exit 198
            }
        }
        else if !`: list ptype in _pt_bands' & !`: list ptype in _pt_fpfam' {
            local _ss_c "!missing(`yvar')"
            if "`ptype'" != "kdensity" local _ss_c "!missing(`yvar', `xvar')"
            if `"`_seg_weight'"' != "" {
                local _ss_c "`_ss_c' & !missing((`_seg_wexp')) & (`_seg_wexp') > 0"
            }
            if `: length local _ps_if' {
                local _ss_c `"`_ss_c' & `macval(_ps_if)'"'
            }
            quietly count if `macval(_ss_c)' `macval(_ss_ifin)'
            local _ss_n = r(N)
            if `_ss_n' == 0 & `: list ptype in _pt_lpfam' {
                display as error "no observations"
                exit 2000
            }
            if `_ss_n' == 1 {
                if "`ptype'" == "lfit" | "`ptype'" == "lfitci" {
                    display as text "(note:  regress could not fit model)"
                }
                display as error "insufficient observations"
                exit 2001
            }
        }
    }

    // ---- The weight text as twoway's views read it (WP-31 A5b) ----
    // scatter, line and every other yxview type, mspline and mband among
    // them, read a weight text that -syntax varlist(min=1 max=1)- takes as
    // one variable as typed (_dash_wexp_yx): [aw=price-price] is "- not
    // allowed", r(101), [aw=(price)] "( invalid name", r(198), where the
    // fits, kdensity, histogram, lpoly and function evaluate it.  twoway
    // judges it when it builds the plot's data: after the options, before
    // the weights' values (weighted_markers_truth.json X_*).
    local _wt_ownparse "lfit qfit lfitci qfitci fpfit fpfitci lpoly lpolyci kdensity histogram lowess function"
    if `"`_seg_weight'"' != "" & !`: list ptype in _wt_ownparse' & !`: list ptype in _pt_imm' {
        _dash_wexp_yx `macval(_seg_wexp_typed)'
    }

    // ---- A weighted marker layer with no weight above zero (WP-31 C9) ----
    // twoway's _draw_weighted_points scales by 1.5/sqrt(min) or 10/sqrt(max)
    // of the plot's weights; with none above zero both are missing and the
    // graph stops, r(198), without a word -- unless the markers are not
    // drawn (msymbol(none)) or are labelled (mlabel() takes the labelled
    // path, which ignores the weight): weighted_markers_truth.json W06.
    // Under by() twoway answers panel by panel; that is not judged here.
    if `"`_seg_weight'"' != "" & `: list ptype in _wt_markers' & !`: length local _ss_by' {
        mata: st_local("_wm_lab", st_global("s(mlabel)"))
        mata: st_local("_wm_sym", strlower(strtrim(st_global("s(msymbol)") + st_global("s(marker)"))))
        if `"`macval(_wm_lab)'"' == "" & !inlist(`"`_wm_sym'"', "none", "i") {
            local _wm_c "!missing((`_seg_wexp')) & (`_seg_wexp') > 0"
            if `: length local _ps_if' {
                local _wm_c `"`_wm_c' & `macval(_ps_if)'"'
            }
            local _wm_in ""
            if `: length local _ps_in' local _wm_in `"in `macval(_ps_in)'"'
            quietly count if `macval(_wm_c)' `macval(_wm_in)'
            if r(N) == 0 exit 198
        }
    }

    // Accumulate this segment's unsupported options so _dash_plot can report
    // them once for the whole command rather than once per plot segment.
    // c_local cannot read the caller's local, so hand back only THIS
    // segment's list and let _dash_plot append it.
    // A weight is never named (WP-31 C9): a type that honours it
    // (`_wt_honoured') has it in the spec, and on any other twoway accepts
    // it, draws nothing different and says nothing.
    // WP-32: a pending name is written with "()" when it takes a value
    // (_dash_pending_note), so the note names each word as twoway does.
    // An option twoway takes and draws nothing different with on this
    // type is taken as twoway takes it, without a note (WP-32,
    // _dash_silent_drop).
    mata: st_local("_seg_ign", _dash_pending_note(_dash_silent_drop(st_global("s(_pending)"), st_local("ptype"))) + " " + st_global("s(_unknown)"))
    if `: length local _pa_named' mata: st_local("_seg_ign", st_local("_seg_ign") + " " + st_local("_pa_named"))
    c_local _seg_ignored_out : copy local _seg_ign
    // The graph-wide options dash does not declare that this segment gave
    // (clegend(), pcycle(), notitling, ...): twoway takes each once from
    // the whole command, so _dash_plot counts them across segments.
    c_local _seg_gund_out : copy local _rp_gund_out
    // Whether this segment gave name(): _dash_plot counts them across the
    // command and refuses a second (_dash_refuse_second_name).
    mata: st_local("_seg_named", strofreal(st_global("s(g_name)") != ""))
    c_local _seg_named_out `_seg_named'
    // The axes this segment's layers are drawn on (yaxis(), xaxis(); 1 when
    // not given), for _dash_plot's axis check (WP-29 P0.5).
    // s(yaxis) is the axes kind's sorted list (WP-31 C10b): yaxis(1 2)
    // puts the layers on both, so _seg_y/xaxes_out carry the list for the
    // axis check and _seg_y/xaxis_out the highest number.
    mata: st_local("_seg_yas", st_global("s(yaxis)"))
    mata: st_local("_seg_xas", st_global("s(xaxis)"))
    if !`: word count `_seg_yas'' local _seg_yas 1
    if !`: word count `_seg_xas'' local _seg_xas 1
    local _seg_ya : word `: word count `_seg_yas'' of `_seg_yas'
    local _seg_xa : word `: word count `_seg_xas'' of `_seg_xas'
    c_local _seg_yaxis_out `_seg_ya'
    c_local _seg_xaxis_out `_seg_xa'
    c_local _seg_yaxes_out `_seg_yas'
    c_local _seg_xaxes_out `_seg_xas'
    // Whether this segment draws a colorvar() layer, and says
    // colorallowmultiple, for twoway's one-layer check in _dash_plot
    // (WP-31 C8b).
    mata: st_local("_seg_cv", strofreal(st_global("s(colorvar)") != ""))
    mata: st_local("_seg_cvam", strofreal(st_global("s(colorallowmultiple)") != ""))
    c_local _seg_cv_out `_seg_cv'
    c_local _seg_cvam_out `_seg_cvam'
    // The variable this segment's x axis takes its label format from, for
    // the t-options' date literals (WP-30 P1.6, _dash_taxis_fold): the x of
    // the yx and range types (tsline and tsrline: the tsset variable), the
    // variable of histogram and kdensity, x1 of the pc types; none for
    // function, scatteri, pci and pcarrowi.  An operated x (L.t) keeps its
    // variable's format, as twoway reads it: the name after the last dot.
    if `: list ptype in _pt_univar' local _seg_xv `"`yvar'"'
    else if `: list ptype in _pt_pc' local _seg_xv `"`x1var'"'
    else if `: list ptype in _pt_literal' local _seg_xv ""
    else local _seg_xv `"`xvar'"'
    if strrpos(`"`_seg_xv'"', ".") local _seg_xv = substr(`"`_seg_xv'"', strrpos(`"`_seg_xv'"', ".") + 1, .)
    capture confirm variable `_seg_xv', exact
    if _rc local _seg_xv ""
    c_local _seg_xvar_out `_seg_xv'

    // Hand the graph-level options found in this segment to _dash_plot as
    // _sg_* locals (they live in its frame, not here -- c_local propagates
    // them); _dash_plot merges each into its g_* accumulator as twoway
    // merges a repeated option (_dash_rep_merge).  They were c_local'ed
    // over the accumulator, so a later group's legend(label(2 "B")) threw
    // away an earlier group's legend(label(1 "A")), which twoway keeps.
    foreach gkey in title subtitle note caption name saving xtitle ytitle xlabel ///
            ylabel xline yline legend clegend plegend pcycle by xscale yscale aspectratio scheme ///
            plotregion graphregion bgcolor plotbgcolor link filter ytitle2 ///
            xtitle2 ylabel2 xlabel2 xmlabel2 ymlabel2 xmtick2 ymtick2 yscale2 xscale2 ytick2 xtick2 yline2 xline2 ///
            xsize ysize fxsize fysize ///
            scale text ttext hover xtick ytick xmtick ymtick xmlabel ymlabel tlabel ttick tmlabel tmtick tscale ttitle tline tlabel2 ttick2 tline2 tscale2 ttitle2 t1title ///
            t2title b1title b2title l1title l2title r1title r2title ///
            zlabel ztitle zscale aspectplacement xoverhangs yoverhangs nodraw play replace table {
        mata: st_local("gval", st_global("s(g_" + st_local("gkey") + ")"))
        if `: length local gval' {
            c_local _sg_`gkey' : copy local gval
        }
    }

    // ---- build plot JSON ----
    // Variable fields
    local vfields ""

    if `: list ptype in _pt_univar' {
        _dash_json_str "`yvar'" _jyv
        local vfields `""var":"`_jyv'""'
    }
    else if `: list ptype in _pt_range' {
        _dash_json_str "`yvar1'" _jy1
        _dash_json_str "`yvar2'" _jy2
        _dash_json_str "`xvar'"  _jxv
        local vfields `""yvar1":"`_jy1'","yvar2":"`_jy2'","xvar":"`_jxv'""'
    }
    else if `: list ptype in _pt_pc' {
        _dash_json_str "`y1var'" _jy1
        _dash_json_str "`x1var'" _jx1
        _dash_json_str "`y2var'" _jy2
        _dash_json_str "`x2var'" _jx2
        local vfields `""y1var":"`_jy1'","x1var":"`_jx1'","y2var":"`_jy2'","x2var":"`_jx2'""'
    }
    else if `: list ptype in _pt_rangept' {
        // WP-31 B1: the range's ends, its marker (y3) and x.
        _dash_json_str "`yvar1'" _jy1
        _dash_json_str "`yvar2'" _jy2
        _dash_json_str "`yvar'"  _jyv
        _dash_json_str "`xvar'"  _jxv
        local vfields `""yvar1":"`_jy1'","yvar2":"`_jy2'","yvar":"`_jyv'","xvar":"`_jxv'""'
    }
    else if `: list ptype in _pt_contour' {
        // WP-31 B4b: the variable cut into levels, then the plane.
        _dash_json_str "`zvar'" _jzv
        _dash_json_str "`yvar'" _jyv
        _dash_json_str "`xvar'" _jxv
        local vfields `""zvar":"`_jzv'","yvar":"`_jyv'","xvar":"`_jxv'""'
    }
    else if "`ptype'" == "function" {
        _dash_json_str `"`macval(expr)'"' _jex
        _dash_json_str "`_fn_yname'" _jyn
        local vfields `""expr":"`_jex'","yname":"`_jyn'""'
    }
    else if `: list ptype in _pt_imm' {
        // scatteri, pci and pcarrowi: read and checked with the varlist
        // above, one record per point, segment or arrow, every coordinate
        // a JSON number or null.  The array holds no apostrophe, backtick
        // or dollar sign -- a label carries each as a JSON unicode escape
        // (u0027, u0060, u0024 after a backslash) -- so it expands safely
        // inside any quotes.  scatteri's was built here token by token, as
        // typed, a label cut at its first blank (P1A-60).
        local vfields `""values":`_pci_json'"'
    }
    else {
        _dash_json_str "`yvar'" _jyv
        _dash_json_str "`xvar'" _jxv
        local vfields `""yvar":"`_jyv'","xvar":"`_jxv'""'
    }

    // Options JSON
    // recast(): the typed type, when the layer is drawn as another
    // (WP-30 P1.8b); the renderer keys nothing on it.
    local _rcf ""
    if "`ptype'" != "`_ptype_typed'" local _rcf `","recast_from":"`_ptype_typed'""'
    _dash_plot_opts_to_json _opts_json 1
    // sort(varlist) on a joining type: the names unab gave
    // (_dash_sort_opt), which dash.ado ranks at export (_dash_sort_gen).
    // A plot without it writes nothing new.
    mata: st_local("_jsv", st_global("s(sortvars)"))
    local _jsvf ""
    if "`_jsv'" != "" {
        _dash_json_str "`_jsv'" _jsv2
        local _jsvf `","sortvars":"`_jsv2'""'
    }

    // if/in, in compound quotes.  In plain quotes a qualifier holding a
    // double quote was split at it: -args- in _dash_json_str took the text
    // before the first inner quote as the value and the word after it as
    // the name to store under, so  if make != "AMC Concord" & foreign == 1
    // stored "if_expr":"" -- the qualifier gone, every row drawn, no word
    // (measured 23sep2026 at ad13a0f) -- and  make != "<b>"  stopped with
    // "_< invalid name".
    _dash_json_str `"`macval(if_expr)'"' _jif
    _dash_json_str `"`macval(in_expr)'"' _jin

    // Assemble.  A standard varlist with several y-variables produces ONE plot
    // object per y-variable; they are comma-joined here and the caller splices
    // them into the plots array exactly as it does separate segments, so each
    // gets its own scheme style index downstream.
    if `"`yvarlist'"' != "" {
        local seg_json ""
        local _nyv : word count `yvarlist'
        forvalues _yi = 1/`_nyv' {
            _dash_plot_opts_to_json _opts_json `_yi'
            local _thisy = word(`"`yvarlist'"', `_yi')
            _dash_json_str "`_thisy'" _jyv
            _dash_json_str "`xvar'"   _jxv
            local vfields `""yvar":"`_jyv'","xvar":"`_jxv'""'
            if `_yi' > 1 local seg_json `"`seg_json',"'
            // A scatter y given a connect() element is connected (P1.8a).
            local _yt "`ptype'"
            if `"`_cn_types'"' != "" local _yt : word `_yi' of `_cn_types'
            local seg_json `"`seg_json'{"type":"`_yt'"`_rcf',`vfields',"options":`_opts_json',"if_expr":"`_jif'","in_expr":"`_jin'"`_jsvf'}"'
        }
    }
    else {
        local _nyv = 1
        local _yt "`ptype'"
        if `"`_cn_types'"' != "" local _yt : word 1 of `_cn_types'
        local seg_json `"{"type":"`_yt'"`_rcf',`vfields',"options":`_opts_json',"if_expr":"`_jif'","in_expr":"`_jin'"`_jsvf'}"'
    }

    c_local `plottype_out' "`ptype'"
    c_local `json_out'     `"`seg_json'"'
    // How many plot objects seg_json holds, for _dash_plot's running total
    // against the plot limit (WP-19).
    c_local _seg_nplots_out `_nyv'
    // The plot's own if and in, as -syntax- read them (abbreviations
    // written out), and whether it gave bands(): _dash_plot answers a by()
    // graph's panels from them once every segment, and the graph's by(),
    // is known (_dash_by_refuse).
    c_local _seg_if_out : copy local if_expr
    c_local _seg_in_out : copy local in_expr
    c_local _seg_bands_out = `: length local _ss_bands' > 0
    // The plotted variables and the weight's, which a panel's sample
    // leaves out when missing (and a weight not above zero).
    c_local _seg_vars_out `yvar' `xvar'
    local _seg_wv ""
    // An expression in parentheses (WP-31 A5): the by() sample reads it.
    // The marker types' weights size markers and leave the sample alone.
    if `"`_seg_weight'"' != "" & `: list ptype in _wt_honoured' & !`: list ptype in _wt_markers' local _seg_wv (`_seg_wexp')
    c_local _seg_wvar_out `_seg_wv'
    // A function layer's text and the generator's range() and n(): the
    // typed range when it is two plain numbers (numlist keeps 13 digits,
    // the generator all 17), else the validated one, else twoway's 0 1;
    // n() or twoway's 300 (WP-29 P0.6).
    if "`ptype'" == "function" {
        local _fn_lo 0
        local _fn_hi 1
        local _fn_ok 0
        if `: word count `_fn_rtyped'' == 2 {
            local _fn_a : word 1 of `_fn_rtyped'
            local _fn_b : word 2 of `_fn_rtyped'
            capture confirm number `_fn_a'
            local _fn_ok = !_rc
            capture confirm number `_fn_b'
            local _fn_ok = `_fn_ok' & !_rc
            if `_fn_ok' {
                local _fn_lo `_fn_a'
                local _fn_hi `_fn_b'
            }
        }
        if !`_fn_ok' & `: word count `_fn_rnorm'' == 2 {
            local _fn_lo : word 1 of `_fn_rnorm'
            local _fn_hi : word 2 of `_fn_rnorm'
        }
        local _fn_n 300
        if "`_fn_nval'" != "" local _fn_n `_fn_nval'
        c_local _seg_fnraw_out : copy local _fn_raw
        // subchar(): the expression's variable (WP-35 stat:PT-6).
        mata: st_local("_fn_x", st_global("s(subchar)"))
        if !`: length local _fn_x' local _fn_x "x"
        c_local _seg_fnx_out "`_fn_x'"
        c_local _seg_fnlo_out `_fn_lo'
        c_local _seg_fnhi_out `_fn_hi'
        c_local _seg_fnn_out `_fn_n'
        // droplines() as validated (an expanded numlist), for the
        // generator (WP-31 C5).
        mata: st_local("_fn_drops", st_global("s(droplines)"))
        c_local _seg_fndrops_out `_fn_drops'
    }
    // estopts(), predopts(), estcmd() (WP-31 C4): the layer's points, made
    // by twoway's own generator over the plot's sample (_psq) and weight,
    // into the string scalar _dash_plot names in $dash__ftsc.  Last: the
    // generator leaves s() empty, and the JSON above reads it.
    local _ft_types "lfit qfit lfitci qfitci fpfit fpfitci"
    // A negative n() on lfit, qfit, lfitci and qfitci, and one above the
    // renderers' own 10,000-point grid (WP-35 stat:PT-9): twoway's
    // generator makes the points twoway draws -- none for a negative one.
    mata: st_local("_ft_on", strofreal(st_global("dash__ftsc") != "" & ((st_global("s(estopts)") + st_global("s(predopts)") + st_global("s(estcmd)")) != "" | ((strtoreal(st_global("s(n)")) < 0 | (strtoreal(st_global("s(n)")) > 10000 & strtoreal(st_global("s(n)")) < .)) & anyof(("lfit", "qfit", "lfitci", "qfitci"), st_local("ptype"))))))
    if `_ft_on' & `: list ptype in _ft_types' {
        mata: st_local("_ft_e", st_global("s(estopts)"))
        mata: st_local("_ft_p", st_global("s(predopts)"))
        mata: st_local("_ft_c", st_global("s(estcmd)"))
        mata: st_local("_ft_sc", st_global("dash__ftsc"))
        mata: st_local("_ft_n", st_global("s(n)"))
        mata: st_local("_ft_r", st_global("s(range)"))
        mata: st_local("_ft_l", st_global("s(level)"))
        mata: st_local("_ft_s", st_global("s(stdp)") + st_global("s(stdf)") + st_global("s(stdr)"))
        mata: st_local("_ft_a", st_global("s(atobs)"))
        local _ft_w ""
        if `"`_seg_weight'"' != "" local _ft_w "[`_seg_weight'=`_wx']"
        local _ft_o ""
        if "`_ft_n'" != "" local _ft_o "`_ft_o' n(`_ft_n')"
        if "`_ft_r'" != "" local _ft_o "`_ft_o' range(`_ft_r')"
        if "`_ft_l'" != "" local _ft_o "`_ft_o' level(`_ft_l')"
        if "`_ft_s'" != "" local _ft_o "`_ft_o' std(`_ft_s')"
        _dash_fit_points `yvar' `xvar' `macval(_psq)' `_ft_w', sc(`_ft_sc') ptype(`ptype') ///
            estopts(`macval(_ft_e)') predopts(`macval(_ft_p)') estcmd(`macval(_ft_c)') ///
            `_ft_o' `_ft_a'
    }
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
// modified.  The writer that replaced it (_dash_write_data) writes stored
// values only, so the formats still travel here.
// ================================================================
program define _dash_formats_json
    version 19
    args varlist_in out_macro datevars_macro bcal_macro

    local parts ""
    local nparts = 0
    local datevars ""
    local seen ""
    // WP-31 G7: the business calendars the %tb formats name, read once
    // here (_dash_bcal_table) and embedded as build_options "bcal".
    local bcals ""
    local bcal_seen ""

    foreach v of local varlist_in {
        capture confirm variable `v'
        if _rc continue
        // The variable as Stata stores it, once.  A qualifier may
        // abbreviate one -- `if dis > 100' reads displacement -- and the
        // words of a qualifier's string literal are among the names read,
        // so `if make != "d"' names d too.  st_varformat() takes no
        // abbreviation, and every render of such a command stopped with
        // r(3500) "invalid Stata variable name" (measured 24sep2026,
        // test_program_coverage.cscript PC-31).  The format is keyed by
        // the stored name, the column the renderer reads.
        capture unab v : `v', max(1)
        if _rc continue
        if `: list v in seen' continue
        local seen `seen' `v'

        // The format is read, escaped and classified in Mata, by value,
        // never as macro text.  A display format is user text: Stata
        // accepts %td!" and %td!` (a ! puts any character into a date
        // picture) and %tdDD!$DD.  Read with `: format', the backtick
        // opened a compound quote that the test below never closed --
        // r(132), "too few quotes", on every render of the variable -- and
        // $DD was expanded as a global, so the spec said %tdDD! (measured
        // 24sep2026; test_program_coverage.cscript PC-03).
        // Under set dp comma a numeric format's decimal point is a comma
        // (display %9.2f prints 3,14, as %9,2f does; WP-31 G2), so the
        // format the page writes with is the comma one.
        mata: st_local("_fjv", _dash_json_escape(_dash_dp_format(st_varformat(st_local("v")))))
        // %t and %-t followed by one of the eight kind letters, case
        // sensitively: %tc and %tC are different formats.
        // %d is %td's old name (WP-31 G7).
        mata: st_local("_fdate", strofreal(regexm(st_varformat(st_local("v")), "^%-?(t[cCdhmqwy]|d)")))

        if `nparts' > 0 local parts `"`parts',"'
        local parts `"`parts'"`v'":"`_fjv'""'
        local nparts = `nparts' + 1
        if `_fdate' local datevars `"`datevars' `v'"'
        mata: st_local("_fbc", (regexm(st_varformat(st_local("v")), "^%tb([A-Za-z_][A-Za-z0-9_]*)") ? regexs(1) : ""))
        if "`_fbc'" != "" & !`: list _fbc in bcal_seen' {
            local bcal_seen `bcal_seen' `_fbc'
            _dash_bcal_table `v' `_fbc' _fbt
            if `"`_fbt'"' != "" {
                if `"`bcals'"' != "" local bcals `"`bcals',"'
                local bcals `"`bcals'"`_fbc'":`_fbt'"'
            }
        }
    }

    c_local `out_macro'      `"{`parts'}"'
    c_local `datevars_macro' `"`datevars'"'
    if "`bcal_macro'" != "" {
        if `"`bcals'"' != "" c_local `bcal_macro' `","bcal":{`bcals'}"'
        else c_local `bcal_macro' ""
    }
end

// ================================================================
// _dash_bcal_table var cal out  -- a business calendar as the spec holds
// it (WP-31 G7)
//
// Stata writes a %tb<cal> value as its business day's %td date (display
// %tbu46 5 is 08jan2024; measured 16oct2026) and one outside the calendar
// as the bare number.  The calendar is read here, at registration, by
// Stata itself -- bcal describe for its range, Mata's dofb() for each
// day -- and never again at render: <out> becomes
// {"min":k0,"td":[...]} for the calendar's whole range when it holds at
// most 10,000 business days, else for the variable's range widened by a
// quarter of its span each side (at most 10,000); empty when the
// calendar cannot be read (its values are then written as numbers).
// ================================================================
program define _dash_bcal_table
    version 19
    args var cal out
    c_local `out' ""
    capture quietly bcal describe `cal'
    if _rc exit
    local lo = r(min_date_tb)
    local hi = r(max_date_tb)
    if missing(`lo') | missing(`hi') exit
    if `hi' - `lo' + 1 > 10000 {
        quietly summarize `var', meanonly
        if r(N) == 0 exit
        local span = r(max) - r(min)
        local lo = max(`lo', floor(r(min) - 0.25 * `span'))
        local hi = min(`hi', floor(r(max) + 0.25 * `span'))
        if `hi' - `lo' + 1 > 10000 local hi = `lo' + 9999
    }
    mata: st_local("_bct", _dash_bcal_json(st_local("cal"), `lo', `hi'))
    c_local `out' `"`_bct'"'
end


// ================================================================
// _dash_graph_set_fonts <macro> -- the faces graph set svg gives the
// three font tags, as build_options keys (WP-31 G2)
//
// {stSans}, {stSerif} and {stMono} draw in graph set's fontfacesans,
// fontfaceserif and fontfacemono (measured: graph set svg fontfacesans
// Courier makes {stSans:a} Courier; fontface alone does not).  The
// faces are read with translator query, which changes no setting and
// prints nothing; each is escaped in Mata, by value.  <macro> becomes
// ,"fontfacesans":"..."... or empty when the query fails.
// ================================================================
program define _dash_graph_set_fonts
    version 19
    args out
    local json ""
    capture quietly translator query gph2svg
    if !_rc {
        foreach k in fontfacesans fontfaceserif fontfacemono {
            local _gf `"`r(`k')'"'
            mata: st_local("_gfe", _dash_json_escape(st_local("_gf")))
            local json `"`json',"`k'":"`_gfe'""'
        }
    }
    c_local `out' `"`json'"'
end


// ================================================================
// _dash_empty_data  — the data file of a dashboard that exports no
// variable
// ================================================================
// A dashboard whose graphs are all scatteri, pci, pcarrowi and function
// draws from its own values, as twoway draws them with no data in memory.
// jsonio needs a varlist, so dash.ado writes the file itself: jsonio's
// layout holding no variable and no observation, which both renderers read
// as an empty dataset (test_immediate_dashboards.py pins the same text).
// `dash build' refused such a dashboard, "no variables identified across
// registered graphs", r(198); the one-line form exported one observation
// of the first variable in memory, which no layer read, and with no data
// in memory was refused too (test_parser.cscript P1A-72).
program define _dash_empty_data
    version 19
    args path
    // Written from Python, 0600 and never through a link, a FIFO or another
    // account's file (WP-29 P0.12b): Stata's `file write' wrote it with the
    // umask (0644, measured D7) and followed a link at the name (D9).  The
    // text crosses by value (Macro.getLocal), with its trailing newline
    // (P1A-75 reads one line, then r(eof); A8).  No error branch: an
    // anti-hijack refusal or an OSError ends the python: line, r(7102).
    _dash_require_python
    _dash_xm_load
    local _ed `"{"values":[],"variableIsString":{},"variableNames":[],"variableLabels":{},"valueLabelNames":{},"valueLabels":{},"numberOfRecords":0,"numberOfVariables":0}"'
    python: import sys
    python: from sfi import Macro as _dash_M
    python: _dash_xm = sys.modules["_dash_render_export"]
    python: _dash_ed = _dash_xm._dash_tmp_write_text(_dash_M.getLocal("path"), _dash_M.getLocal("_ed") + chr(10))
end


// ================================================================
// _dash_stata_ticks_gen <request>[;<request>...]  -- Stata's own #N ticks
// ================================================================
// WP-31 D15.  Runs _dash_axis_ticks_stata once per request
// dash_render.py's _dash_stata_tick_plan wrote (names, digits, unit
// letters, - + : only) and gathers each answer's entries through
// _dash_stata_ticks_take, read from r() in full precision.  Leaves the
// JSON array in the caller's local _dash_st_json ("" for none).
program define _dash_stata_ticks_gen
    version 19
    local reqs `"`0'"'
    local acc ""
    // The loader too, not _dash_require_python alone: the module it reads
    // is the one _dash_xm_load keeps, and both guards run first
    // (test_env_guards.cscript ENV-12, test_dependency_guards.py).
    _dash_require_python
    _dash_xm_load
    python: import sys
    python: from sfi import Macro as _dash_M
    python: _dash_xm = sys.modules["_dash_render_export"]
    while `: length local reqs' {
        gettoken _rq reqs : reqs, parse(";")
        if `"`_rq'"' == ";" continue
        capture _dash_axis_ticks_stata `_rq'
        if _rc continue
        local _e ""
        python: _dash_M.setLocal("_e", _dash_xm._dash_stata_ticks_take(_dash_M.getLocal("_rq")))
        if `: length local _e' {
            if `: length local acc' local acc `"`acc',`_e'"'
            else local acc `"`_e'"'
        }
    }
    if `: length local acc' c_local _dash_st_json `"[`acc']"'
    else c_local _dash_st_json ""
end


// ================================================================
// _dash_axis_ticks_stata -- the ticks Stata's own _natscale/_tsnatscale
//                            give over an axis's data range (WP-31 D15)
// ================================================================
// _dash_axis_ticks_stata <n> <unit> <byvar> <layer> [<layer> ...]
//
// Called through dash_render.py's _dash_stata_ticks_run at export, while
// the qualifier columns exist, once per drawn axis, unit and count its
// _dash_stata_tick_requests names.  <unit> is - for _natscale (a number,
// %tc or %tC) or d w m q h y for _tsnatscale; <byvar> is - or the by()
// variable, whose groups are asked for one by one (a rescaled panel);
// each <layer> is <var>[+<var>...]:[<mark>[+<mark>...]][:<cc>[+<cc>...]]
// -- the series' variables on the axis, the __dashq<k> columns that
// select its rows, and (WP-34 TR-4) its complete-case variables: every
// variable the series draws a point from.  Every word is a Stata name
// dash wrote or a variable's: the qualifier TEXT is never read here
// (DECISIONS A25); a row is the series' when each of its marker columns
// is 1 and none of its complete-case variables is missing (. or .a-.z),
// the rows both renderers draw -- so a missing y in the first or last row
// counts for no axis.  A layer of two parts (no cc) keeps every marked row.
//
// For each group g: r(lo<g>) and r(hi<g>), the least and greatest value
// summarize finds over every layer's variables and rows, and the
// routine's answer over them: r(min<g>) r(max<g>) r(delta<g>) r(n<g>) and
// _tsnatscale's r(list<g>).  r(ng) counts the groups.  A group with no
// value or a single value is returned with lo missing; the renderer then
// uses its model.  At most 64 groups.
program define _dash_axis_ticks_stata, rclass
    version 19
    gettoken n    0 : 0
    gettoken unit 0 : 0
    gettoken byv  0 : 0
    local layers `0'
    confirm integer number `n'
    local word ""
    if "`unit'" != "-" {
        local word : word `=strpos("dwmqhy", "`unit'")' of daily weekly monthly quarterly halfyearly yearly
        if "`word'" == "" | strlen("`unit'") != 1 exit 198
    }
    tempvar grp lu
    if "`byv'" != "-" {
        confirm variable `byv', exact
        quietly egen long `grp' = group(`byv')
    }
    else quietly generate byte `grp' = 1
    quietly summarize `grp', meanonly
    local ng = min(cond(r(N), r(max), 0), 64)
    forvalues g = 1/`ng' {
        tempname lo`g' hi`g'
        scalar `lo`g'' = .
        scalar `hi`g'' = .
    }
    foreach L of local layers {
        local vs = subinstr(substr("`L'", 1, strpos("`L'", ":") - 1), "+", " ", .)
        local r1 = substr("`L'", strpos("`L'", ":") + 1, .)
        local ms = subinstr(cond(strpos("`r1'", ":"), substr("`r1'", 1, strpos("`r1'", ":") - 1), "`r1'"), "+", " ", .)
        local cs = cond(strpos("`r1'", ":"), subinstr(substr("`r1'", strpos("`r1'", ":") + 1, .), "+", " ", .), "")
        capture drop `lu'
        quietly generate byte `lu' = 1
        foreach m of local ms {
            confirm numeric variable `m', exact
            quietly replace `lu' = 0 if `m' != 1
        }
        foreach c of local cs {
            confirm numeric variable `c', exact
            quietly replace `lu' = 0 if missing(`c')
        }
        foreach v of local vs {
            confirm numeric variable `v', exact
            forvalues g = 1/`ng' {
                quietly summarize `v' if `lu' & `grp' == `g', meanonly
                if r(N) == 0 continue
                if r(min) < `lo`g'' scalar `lo`g'' = r(min)
                if `hi`g'' >= . | r(max) > `hi`g'' scalar `hi`g'' = r(max)
            }
        }
    }
    local out ""
    forvalues g = 1/`ng' {
        local a = strofreal(`lo`g'', "%21x")
        local b = strofreal(`hi`g'', "%21x")
        if `lo`g'' >= . | `hi`g'' >= . | `lo`g'' >= `hi`g'' {
            local out `out' lo`g' .
            continue
        }
        if "`word'" == "" capture _natscale `a' `b' `n'
        else              capture _tsnatscale `a' `b' `n', `word'
        if _rc {
            local out `out' lo`g' .
            continue
        }
        foreach w in min max delta n {
            tempname `w'`g'
            scalar ``w'`g'' = r(`w')
        }
        local list`g' `"`r(list)'"'
        local out `out' lo`g' `lo`g'' hi`g' `hi`g'' min`g' `min`g'' max`g' `max`g'' delta`g' `delta`g'' n`g' `n`g''
    }
    while `: length local out' {
        gettoken nm out : out
        gettoken sc out : out
        return scalar `nm' = `sc'
    }
    forvalues g = 1/`ng' {
        return local list`g' `"`list`g''"'
    }
    return scalar ng = `ng'
end


// ================================================================
// _dash_write_data <path> <varlist>  -- the data file both renderers read
// ================================================================
// Written from Python through the Stata Function Interface, by
// dash_render.py's _dash_write_stata_data, in jsonio's layout.  dash
// exported with jsonio, whose ado returns the JSON it wrote in a macro and
// expands it inside compound quotes: a string value, value label or
// variable label holding an unclosed compound quote or a lone backtick
// stopped every export with r(132) "too few quotes", and one holding the
// closing pair or a lone apostrophe with r(109) -- whatever the qualifier,
// so any dashboard over such data failed; and every strL arrived as "null"
// (measured 24sep2026; test_string_values.cscript).  sfi reads each value
// by value, so nothing the user typed passes through a macro here: the
// path and the names reach Python through Macro.getLocal(), never as code.
//
// Text that is not UTF-8 is read through Stata's ustrfix() -- each invalid
// sequence U+FFFD, as jsonio wrote it -- with a note naming the variable or
// label.  A binary strL, which is not text, is refused, r(198), naming the
// variable; the file is not written then.  The renderer's module is loaded
// once and kept, keyed by its path, size and time, so a second export in a
// session costs nothing to load.
program define _dash_write_data
    version 19
    gettoken _dw_path _dw_vars : 0
    // As Stata stores them, once each -- what jsonio's varlist gave.
    unab _dw_vars : `_dw_vars'
    local _dw_vars : list uniq _dw_vars
    _dash_require_python
    _dash_xm_load
    local _dw_err ""
    // One statement per line: a python: block inside a program fails to
    // load from the ado-path (see _dash_do_render).  Each program binds
    // sys, _dash_M and _dash_xm in its own python: lines.
    python: import sys
    python: from sfi import Macro as _dash_M
    python: _dash_xm = sys.modules["_dash_render_export"]
    python: _dash_M.setLocal("_dw_err", _dash_xm._dash_write_stata_data(_dash_M.getLocal("_dw_path"), _dash_M.getLocal("_dw_vars")))
    if `: length local _dw_err' {
        mata: _dash_say("err", st_local("_dw_err"), "", "")
        exit 198
    }
end


// ================================================================
// _dash_xm_load  -- load dash_render.py as _dash_render_export, once
// ================================================================
// Moved verbatim out of _dash_write_data (WP-29 P0.12b), which still calls
// it, so the private-file programs below load the same module the same
// way.  The dash_render.py installed beside dash.ado first: the one the
// package ships.  A renderer found earlier on the ado-path -- a stand-in a
// test puts there to watch what it is handed -- replaces the render, never
// the export (test_json_escaping.cscript runs such a stand-in).  Then the
// ado-path, as the render looks.  The module is kept in sys.modules, keyed
// by its realpath, size and time, so a second command costs nothing to
// load.  The guard first: no python: line runs before it (A7, ENV-12).
program define _dash_xm_load
    version 19
    _dash_require_python
    _dash_require_deps
    local _dw_py ""
    capture findfile dash.ado
    if _rc == 0 {
        mata: st_local("_dw_py", substr(st_global("r(fn)"), 1, ///
            strlen(st_global("r(fn)")) - strlen("dash.ado")) + "dash_render.py")
        capture confirm file `"`_dw_py'"'
        if _rc local _dw_py ""
    }
    if `"`_dw_py'"' == "" {
        _dash_find_render
        local _dw_py `"`r(fn)'"'
    }
    // One statement per line: a python: block inside a program fails to
    // load from the ado-path (see _dash_do_render).
    python: import sys, os, importlib.util
    python: from sfi import Macro as _dash_M
    python: _dash_rp = _dash_M.getLocal("_dw_py")
    python: _dash_st = os.stat(_dash_rp)
    python: _dash_key = (os.path.realpath(_dash_rp), _dash_st.st_size, _dash_st.st_mtime_ns)
    python: _dash_xm = sys.modules.get("_dash_render_export")
    // A single-line python: takes no compound statement, so the load is
    // written as expressions.  Every value is assigned: a bare expression
    // echoes its value into the log.  The module is kept only once it has
    // loaded.
    python: _dash_ok = _dash_xm is not None and getattr(_dash_xm, "_dash_export_key", None) == _dash_key
    // WP-31 I7: no bytecode is written for the renderer -- an installed
    // PLUS/py would keep a __pycache__ that ado uninstall leaves behind --
    // as for dash_setup_lib below; the flag is put back on every path.
    python: import sys, sfi; sfi.Macro.setLocal("_dwb", "1" if sys.dont_write_bytecode else "0"); sys.dont_write_bytecode = True
    python: import sys, os; _dash_sp = list(sys.path); sys.path[:] = [p for p in sys.path if p not in ("", os.getcwd())]
    python: _dash_xs = None if _dash_ok else importlib.util.spec_from_file_location("_dash_render_export", _dash_rp)
    python: _dash_xm = _dash_xm if _dash_ok else importlib.util.module_from_spec(_dash_xs)
    // WP-30 P1.32: the renderer's import guard puts its one line in
    // _dd_err (_dash_dep_fail), so the load decides by that value.  A
    // failure that is not a dependency runs again uncaptured, so its
    // traceback shows as it did.  _dd_err, _dd_refuse and _dd_note hold
    // text from the environment: tested by length, shown through Mata only.
    local _dd_err ""
    capture python: _dash_xr = _dash_ok or _dash_xs.loader.exec_module(_dash_xm)
    if _rc {
        local _dd_n : length local _dd_err
        if `_dd_n' > 0 {
            mata: _dash_say("err", "", st_local("_dd_err"), "")
            python: import sys; sys.path[:] = _dash_sp
            python: import sys, sfi; sys.dont_write_bytecode = sfi.Macro.getLocal("_dwb") == "1"
            exit 198
        }
        capture noisily python: _dash_xr = _dash_xs.loader.exec_module(_dash_xm)
        local _dd_rc = _rc
        if `_dd_rc' {
            python: import sys; sys.path[:] = _dash_sp
            python: import sys, sfi; sys.dont_write_bytecode = sfi.Macro.getLocal("_dwb") == "1"
            exit `_dd_rc'
        }
    }
    python: _dash_xm._dash_export_key = _dash_key
    python: sys.modules["_dash_render_export"] = _dash_xm
    python: import sys; sys.path[:] = _dash_sp
    python: import sys, sfi; sys.dont_write_bytecode = sfi.Macro.getLocal("_dwb") == "1"
    // numpy or pandas below dash_setup's minimum: a note once per fresh
    // load (A121); the refusal slot is bokeh's window (S41).
    python: _dash_dv = _dash_xm._dash_dep_versions()
    python: _dash_M.setLocal("_dd_refuse", _dash_dv[0])
    python: _dash_M.setLocal("_dd_note", "" if _dash_ok else _dash_dv[1])
    python: del _dash_dv
    local _dd_n : length local _dd_refuse
    if `_dd_n' > 0 {
        mata: _dash_say("err", "", st_local("_dd_refuse"), "")
        exit 198
    }
    local _dd_n : length local _dd_note
    if `_dd_n' > 0 {
        mata: _dash_note("", st_local("_dd_note"), "")
    }
end


// ================================================================
// _dash_tmp_open, _dash_tmp_preview, _dash_tmp_close, _dash_tmp_clear
// -- dash's private temporary folder (WP-29 P0.12b, P0.14)
// ================================================================
// Measured at 7421d3d (section 08, D1-D9): every temporary copy of the data
// -- the spec and data files of each render, dash serve's application and
// the one-line preview -- was a Stata tempfile written with the umask
// (0644; 0664 under umask 002) in c(tmpdir), a link at its name was
// followed, and the preview was never deleted.  These programs put every
// copy in c(tmpdir)dash-<uid>/run-<pid>-<random>/ (0700, files 0600),
// remove it when the command ends, and keep the previews in .../previews/
// under unique names, five a session (dash_render.py's _dash_run_open,
// _dash_run_close, _dash_preview_path, _dash_tmp_clear).  A location that
// cannot be private is never refused: the command prints ONE note naming
// it and the remedy, and goes on (section 08 R-8, ratified 01oct2026).
// Only an operating-system failure to make the folder at all ends r(603),
// Stata's own code for a file it cannot create.  Each program calls
// _dash_require_python before its first python: line (A7); every python:
// line is an import, an assignment or a setLocal (A11); every path and
// text crosses by value through Macro.getLocal/setLocal.  Callers read
// r() on the very next line (A12).

// _dash_tmp_open: opens the command's run folder; returns r(rundir),
// r(spec), r(data), r(app), and r(noted) "1" when it printed the note.
program define _dash_tmp_open, rclass
    version 19
    _dash_require_python
    _dash_xm_load
    local _to_tmp `"`c(tmpdir)'"'
    python: import sys
    python: from sfi import Macro as _dash_M
    python: _dash_xm = sys.modules["_dash_render_export"]
    python: _dash_to = _dash_xm._dash_run_open(_dash_M.getLocal("_to_tmp"))
    python: _dash_M.setLocal("_to_err", _dash_to["err"])
    python: _dash_M.setLocal("_to_note", _dash_to["note"])
    python: _dash_M.setLocal("_to_dir", _dash_to["rundir"])
    python: _dash_M.setLocal("_to_spec", _dash_to["spec"])
    python: _dash_M.setLocal("_to_data", _dash_to["data"])
    python: _dash_M.setLocal("_to_app", _dash_to["app"])
    local _to_noted ""
    // The privacy class (R-8): printed, never an error.
    if `: length local _to_note' {
        mata: _dash_note("", st_local("_to_note"), "")
        local _to_noted "1"
    }
    // The operating-system class, never a privacy refusal: the folder could
    // not be made at all (c(tmpdir) missing, read-only or full), where
    // Stata's own `file open' gives 603 (measured, §3a S1).
    if `: length local _to_err' {
        mata: _dash_say("err", "", st_local("_to_err"), "")
        exit 603
    }
    return local rundir `"`_to_dir'"'
    return local spec   `"`_to_spec'"'
    return local data   `"`_to_data'"'
    return local app    `"`_to_app'"'
    return local noted  "`_to_noted'"
end

// _dash_tmp_preview, opened() [noted()]: names the one-line preview page in
// previews/ (0600 once written: main(private_output)); returns r(path).
// Its note is printed only when _dash_tmp_open printed none for this
// command (noted() is not "1"): one note per command.
program define _dash_tmp_preview, rclass
    version 19
    syntax, OPENED(string) [NOTED(string)]
    _dash_require_python
    _dash_xm_load
    local _tp_tmp `"`c(tmpdir)'"'
    python: import sys
    python: from sfi import Macro as _dash_M
    python: _dash_xm = sys.modules["_dash_render_export"]
    python: _dash_tp = _dash_xm._dash_preview_path(_dash_M.getLocal("_tp_tmp"), _dash_M.getLocal("opened"))
    python: _dash_M.setLocal("_tp_err", _dash_tp["err"])
    python: _dash_M.setLocal("_tp_note", _dash_tp["note"])
    python: _dash_M.setLocal("_tp_path", _dash_tp["path"])
    if "`noted'" != "1" {
        if `: length local _tp_note' {
            mata: _dash_note("", st_local("_tp_note"), "")
        }
    }
    // The operating-system class, as in _dash_tmp_open.
    if `: length local _tp_err' {
        mata: _dash_say("err", "", st_local("_tp_err"), "")
        exit 603
    }
    return local path `"`_tp_path'"'
end

// _dash_tmp_close, dir(): removes the run folder _dash_tmp_open made.  A
// path that is not one is named and left; it never changes the return
// code.  A folder an error leaves behind is swept by the next command.
program define _dash_tmp_close
    version 19
    syntax, DIR(string)
    _dash_require_python
    _dash_xm_load
    local _tc_tmp `"`c(tmpdir)'"'
    python: import sys
    python: from sfi import Macro as _dash_M
    python: _dash_xm = sys.modules["_dash_render_export"]
    python: _dash_tc = _dash_xm._dash_run_close(_dash_M.getLocal("dir"), _dash_M.getLocal("_tc_tmp"))
    python: _dash_M.setLocal("_tc_err", _dash_tc)
    if `: length local _tc_err' {
        mata: _dash_note("", st_local("_tc_err"), "")
    }
end

// _dash_tmp_clear: dash clear's pruning -- this session's previews (but a
// page a browser was asked to open in the last minute) and stale run
// folders, in dash-<uid> and every fallback root.  With no dash* folder in
// c(tmpdir), Mata says so and no Python runs (A15).
program define _dash_tmp_clear
    version 19
    _dash_require_python
    mata: st_local("_tcl_has", strofreal(rows(dir(c("tmpdir"), "dirs", "dash*")) > 0))
    if "`_tcl_has'" != "1" exit
    // WP-30 P1.32: the pruning code is compiled from dash_render.py's own
    // text with the standard-library imports alone
    // (dash_setup_lib.stdlib_entry), so the same code and the same checks
    // run with numpy, pandas or bokeh missing.
    local _tcl_dir ""
    capture findfile dash.ado
    if _rc == 0 {
        mata: st_local("_tcl_dir", substr(st_global("r(fn)"), 1, strlen(st_global("r(fn)")) - strlen("dash.ado")))
    }
    local lib `"`_tcl_dir'dash_setup_lib.py"'
    local _tcl_py `"`_tcl_dir'dash_render.py"'
    capture confirm file `"`lib'"'
    if _rc {
        local lib ""
        capture findfile dash_setup_lib.py
        if _rc == 0 local lib `"`r(fn)'"'
    }
    capture confirm file `"`_tcl_py'"'
    if _rc {
        local _tcl_py ""
        capture _dash_find_render
        if _rc == 0 local _tcl_py `"`r(fn)'"'
    }
    if `"`lib'"' == "" | `"`_tcl_py'"' == "" exit
    mata: st_local("lib", pathresolve(pwd(), st_local("lib")))
    python: import sys, sfi; sfi.Macro.setLocal("_dwb", "1" if sys.dont_write_bytecode else "0"); sys.dont_write_bytecode = True
    capture python: import importlib.util as _dsl_iu, sys, sfi; _dsl_p = sfi.Macro.getLocal("lib"); _dsl_m = sys.modules.get("_dash_setup_lib"); _dsl_new = _dsl_m is None or getattr(_dsl_m, "__file__", None) != _dsl_p; _dsl_s = _dsl_iu.spec_from_file_location("_dash_setup_lib", _dsl_p) if _dsl_new else None; _dsl_m = _dsl_iu.module_from_spec(_dsl_s) if _dsl_new else _dsl_m; (_dsl_s.loader.exec_module(_dsl_m) if _dsl_new else None); sys.modules["_dash_setup_lib"] = _dsl_m
    local _lrc = _rc
    python: import sys, sfi; sys.dont_write_bytecode = sfi.Macro.getLocal("_dwb") == "1"
    if `_lrc' != 0 exit
    local _tcl_tmp `"`c(tmpdir)'"'
    python: import sys
    python: from sfi import Macro as _dash_M
    python: _dash_sl = sys.modules.get("_dash_setup_lib")
    python: _dash_xp = _dash_sl.stdlib_entry(_dash_M.getLocal("_tcl_py"), "_dash_tmp_clear") if _dash_sl is not None else None
    python: _dash_tcl = _dash_xp(_dash_M.getLocal("_tcl_tmp")) if _dash_xp is not None else ""
end


// ================================================================
// _dash_maxvar_room q s t w cmdname kx [frame]  -- room for the working
// columns (WP-31 G3d; WP-35 DT-19)
// ================================================================
program define _dash_maxvar_room
    // WP-31 G3d: the working columns a dashboard makes, counted against
    // the room c(maxvar) leaves before any of them is generated.  The
    // count is the most that exist at once: q qualifier columns (and one
    // row index while a by() graph's ordered ones are made), s join-order
    // columns (and their row index), t time-series columns (each beside
    // the temporary tsrevar makes until the last is copied) and w weight
    // columns.  A by()-free qualifier is counted with the index too, so
    // the count can exceed the true peak by one, never fall short of it.
    // WP-35 DT-19: with room beside the data's c(k) variables the columns
    // are made in place (_mv_plan inplace); else, with room beside the kx
    // variables the export reads, in a temporary frame holding only those
    // (_mv_plan frame), as twoway draws such data; else refused, r(900),
    // before the data are touched.  The plan comes back in the caller's
    // local _mv_plan.  frame names the frame on a build of several frames.
    version 19
    args q s t w cmdname kx frame
    if "`kx'" == "" local kx = c(k)
    local n = max(0, `q' + (`q' > 0), `q' + `s' + (`s' > 0), `q' + `s' + 2 * `t', `q' + `s' + `t' + `w')
    _dash_maxvar_plan `n' `c(k)' `kx' `c(maxvar)'
    if "`_mv_plan'" != "refuse" {
        c_local _mv_plan "`_mv_plan'"
        exit
    }
    local room = c(maxvar) - c(k)
    local roomx = c(maxvar) - `kx'
    local pl = cond(`n' == 1, "", "s")
    local inf ""
    if `"`frame'"' != "" local inf " in frame `frame'"
    display as error "`cmdname': the dashboard needs `n' working column`pl' beside the data's `c(k)' variables`inf', and set maxvar allows `c(maxvar)', which leaves room for `room', or `roomx' beside the `kx' variables the dashboard exports."
    display as error "      Raise the limit (set maxvar; see help memory) or drop variables the dashboard does not use, then run it again."
    exit 900
end

// ================================================================
// _dash_maxvar_plan n k kx maxvar  -- where the working columns are made
// (WP-35 DT-19).  inplace when the n columns fit beside the data's k
// variables, frame when they fit beside the kx variables a temporary
// frame would hold, else refuse; into the caller's local _mv_plan.  The
// internal global dash__force_frame (1) answers frame whatever the room,
// so certification reaches that branch without set maxvar.
// ================================================================
program define _dash_maxvar_plan
    version 19
    args n k kx maxvar
    if "${dash__force_frame}" == "1" {
        c_local _mv_plan "frame"
        exit
    }
    if `n' <= `maxvar' - `k' c_local _mv_plan "inplace"
    else if `n' <= `maxvar' - `kx' c_local _mv_plan "frame"
    else c_local _mv_plan "refuse"
end

// ================================================================
// _dash_esample_copy <prefix> <cmdname>  -- the export's copy of e(sample)
// (WP-35 DT-19).  When a qualifier or weight expression of the table
// names e(sample) outside its string literals, the byte variable
// <prefix>esample = e(sample) is made in the frame this runs in -- the
// estimation sample in the frame the estimation ran in, 0 in any other,
// as twoway reads e(sample) -- before the estimates are held, so the
// generators read it in e(sample)'s place.  Its name comes back in the
// caller's local _dash_es ("" when none was made); the caller drops it.
// ================================================================
program define _dash_esample_copy
    version 19
    args prefix cmdname
    local _need 0
    local _dq_n = 0
    mata: _dash_qual_export()
    forvalues k = 1/`_dq_n' {
        mata: st_local("_h", strofreal(_dash_esample_sub(st_local("_dq_if_`k'"), "x") != st_local("_dq_if_`k'")))
        if `_h' local _need 1
    }
    local _dwx_n = 0
    mata: _dash_wexp_export()
    forvalues k = 1/`_dwx_n' {
        mata: st_local("_h", strofreal(_dash_esample_sub(st_local("_dwx_e`k'"), "x") != st_local("_dwx_e`k'")))
        if `_h' local _need 1
    }
    if !`_need' {
        c_local _dash_es ""
        exit
    }
    _dash_maxvar_room 0 0 0 1 "`cmdname'" `c(k)'
    quietly generate byte `prefix'esample = e(sample)
    c_local _dash_es "`prefix'esample"
end

// ================================================================
// _dash_frame_put <frame> <varlist>  -- put varlist of the data in memory
// into the new frame <frame> (WP-35 DT-19), in the data's order, sorted
// as the data are (frame put keeps the order but not the sort marker
// tsrevar reads: the longest leading part of the sort order the frame
// holds is set again, which moves no row), and append the frame put from
// to the internal global dash__frame_trace.
// ================================================================
program define _dash_frame_put
    version 19
    gettoken xf 0 : 0
    local _sb : sortedby
    frame put `0', into(`xf')
    local _keep ""
    foreach v of local _sb {
        if !`: list v in 0' continue, break
        local _keep `_keep' `v'
    }
    if "`_keep'" != "" frame `xf': sort `_keep'
    global dash__frame_trace ${dash__frame_trace} `c(frame)'
end

// ================================================================
// _dash_frame_vars <prefix> <frame> <varlist>  -- the variables a
// temporary export frame holds (WP-35 DT-19): varlist (the variables the
// data file exports), every variable a qualifier, by() order, sort(),
// time-series or weight expression of the table names (of frame's entries
// when frame is given), the tsset panel and time variables, and the
// export's e(sample) copy <prefix>esample.  Into the caller's local
// _mv_vars; their count into _mv_kx.
// ================================================================
program define _dash_frame_vars
    version 19
    gettoken prefix 0 : 0
    gettoken frame 0 : 0
    local _w `0'
    local _dq_n = 0
    mata: _dash_qual_export()
    forvalues k = 1/`_dq_n' {
        if `: length local frame' & "`_dq_fr_`k''" != "`frame'" continue
        mata: st_local("_x", _dash_expr_words(st_local("_dq_if_`k'")))
        local _w `_w' `_x' `_dq_by_`k''
    }
    local _ds_n = 0
    mata: _dash_sort_export()
    forvalues k = 1/`_ds_n' {
        if `: length local frame' & !strpos("`_ds_f`k''", " `frame' ") continue
        local _w `_w' `_ds_v`k''
    }
    local _dts_n = 0
    mata: _dash_tsop_export()
    forvalues k = 1/`_dts_n' {
        if `: length local frame' & "`_dts_f`k''" != "`frame'" continue
        mata: st_local("_x", _dash_expr_words(st_local("_dts_e`k'")))
        local _w `_w' `_x'
    }
    local _dwx_n = 0
    mata: _dash_wexp_export()
    forvalues k = 1/`_dwx_n' {
        if `: length local frame' & "`_dwx_f`k''" != "`frame'" continue
        mata: st_local("_x", _dash_expr_words(st_local("_dwx_e`k'")))
        local _w `_w' `_x'
    }
    local _w `_w' `: char _dta[_TSpanel]' `: char _dta[_TStvar]' `prefix'esample
    local out ""
    foreach v of local _w {
        capture unab _u : `v'
        if _rc continue
        foreach u of local _u {
            if !`: list u in out' local out `out' `u'
        }
    }
    local _kx : word count `out'
    c_local _mv_vars "`out'"
    c_local _mv_kx "`_kx'"
end


// ================================================================
// _dash_qual_gen <cmdname>  -- evaluate each distinct qualifier in Stata
//
// The table _dash_qual_rewrite and _dash_qual_take filled (dash_parse.mata)
// holds every distinct (if, in) pair the dashboard's plots, graphs and KPIs
// carry.  Each is evaluated here, once, against the data in memory in their
// order, into the byte variable __dashq<k>: 1 where Stata selects the row,
// 0 elsewhere -- `if' true where its expression is not zero, a missing
// value included, as Stata reads every qualifier.  The caller exports these
// with its variables and drops them at once, whether or not the export
// succeeded; the names come back in the caller's local _dash_qual_vars.
//
// Evaluating the qualifiers here is what makes the rows drawn Stata's: the
// renderers used to translate each into a pandas query, which read a
// missing value, a subscript, a function or a date otherwise than Stata
// (test_qualifier_in_stata.cscript).  A dashboard with no qualifier makes
// no variable.
//
// Every column dash makes is named with the export's prefix (WP-35 DT-19,
// _dash_reserved_prefix): __dash, or __dsh<k>_ when a variable of the
// data starts with __dash, so no column is a name the data hold and every
// variable -- __dashq1 included -- is read as data, as twoway reads it;
// the renderers read the prefix from the spec (_dash_prefix).  An
// e(sample) of the if reads the export's copy <prefix>esample
// (_dash_esample_copy).  The if is read
// by value -- macval() -- inside the
// parentheses _dash_qual_refusal proved it cannot leave, and the in is a
// range that check proved is one; a qualifier Stata cannot evaluate against
// the data now in memory (a variable dropped since the graph was
// registered) is refused with Stata's own error, as twoway refuses it, and
// nothing is left behind.
//
// A by() graph's qualifier that can depend on the order of the rows is
// evaluated in the order twoway evaluates it, sorted on the by()
// variables (_dash_qual_gen_by, below; _dash_qual_rewrite).
// ================================================================
program define _dash_qual_gen
    version 19
    // frame (WP-33 33-07): when given, only the columns of that frame's
    // entries (_dq_fr_<k>) are made; the column numbers stay the table's.
    // prefix (WP-35 DT-19): the export's working-column prefix
    // (_dash_reserved_prefix), which no variable of the data starts with.
    args cmdname frame prefix
    if "`prefix'" == "" local prefix "__dash"
    // An e(sample) copy the export made before holding the estimates.
    capture confirm variable `prefix'esample, exact
    local _dq_es = (_rc == 0)

    local _dq_n = 0
    mata: _dash_qual_export()
    local made ""
    forvalues k = 1/`_dq_n' {
        if `: length local frame' & "`_dq_fr_`k''" != "`frame'" continue
        quietly generate byte `prefix'q`k' = 0
        local made `made' `prefix'q`k'
    }
    // The data's own order: every column no by() graph sorts.
    forvalues k = 1/`_dq_n' {
        if `: length local _dq_by_`k'' continue
        if `: length local frame' & "`_dq_fr_`k''" != "`frame'" continue
        local v "`prefix'q`k'"
        local _qx : copy local _dq_if_`k'
        if `_dq_es' mata: st_local("_qx", _dash_esample_sub(st_local("_qx"), st_local("prefix") + "esample"))
        local _qn : copy local _dq_in_`k'
        local _qr ""
        if `: length local _qn' {
            local _qr "in `_qn'"
        }
        if `: length local _qx' {
            capture noisily quietly replace `v' = 1 if (`macval(_qx)') `_qr'
        }
        else {
            capture noisily quietly replace `v' = 1 `_qr'
        }
        local rc = _rc
        if `rc' {
            drop `made'
            mata: _dash_say("err", "`cmdname': Stata cannot evaluate the qualifier ", ///
                strtrim((st_local("_qx") != "" ? "if " + st_local("_qx") : "") + " " + st_local("_qr")), ///
                " against the data in memory.")
            exit `rc'
        }
    }
    // A by() graph's columns, in its by() order: once per distinct order,
    // each column evaluated once (_dash_qual_gen_by).
    local _dq_nord = 0
    mata: _dash_qual_orders()
    forvalues j = 1/`_dq_nord' {
        capture noisily _dash_qual_gen_by "`cmdname'" "`frame'" "`prefix'" `_dq_ord_`j''
        local rc = _rc
        if `rc' {
            drop `made'
            exit `rc'
        }
    }
    c_local _dash_qual_vars "`made'"
end

// ================================================================
// _dash_qual_gen_by <cmdname> <varlist>  -- the columns of one by() order
//
// Each __dashq<k> _dash_qual_export gives varlist as its order
// (_dash_qual_by_of named the variables, each a Stata name) is evaluated
// with the data sorted as twoway sorts a by() graph's: bygraph_g.class
// runs `bysort varlist (sortedby obsnum)', a stable sort on the by()
// variables -- ties keep the data's order, missing values sort last --
// and every plot's if and in, and the graph's, are evaluated once over
// the whole sorted data, _n never restarting within a group (measured
// 24sep2026 from each panel's serset; test_qualifier_in_stata.cscript
// QS-16..).  Only the by() variables the data hold are sorted on: the
// renderers facet on those alone.  sortpreserve gives the data their
// order back; a sort marks nothing changed.  The if is read by value, as
// in _dash_qual_gen, and each column is evaluated once.
// ================================================================
program define _dash_qual_gen_by, sortpreserve
    version 19
    gettoken cmdname order : 0
    // The frame whose columns are made, "" for every column (WP-33 33-07).
    gettoken frame order : order
    // The export's working-column prefix (WP-35 DT-19).
    gettoken prefix order : order
    if "`prefix'" == "" local prefix "__dash"
    capture confirm variable `prefix'esample, exact
    local _dq_es = (_rc == 0)
    local order : list retokenize order
    local _dq_n = 0
    mata: _dash_qual_export()
    local _sv ""
    foreach _b of local order {
        capture confirm variable `_b', exact
        if _rc == 0 local _sv `_sv' `_b'
    }
    if "`_sv'" != "" {
        tempvar _obs
        quietly generate double `_obs' = _n
        sort `_sv' `_obs'
    }
    forvalues k = 1/`_dq_n' {
        local _o : copy local _dq_by_`k'
        if !`: list _o == order' continue
        if `: length local frame' & "`_dq_fr_`k''" != "`frame'" continue
        local v "`prefix'q`k'"
        local _qx : copy local _dq_if_`k'
        if `_dq_es' mata: st_local("_qx", _dash_esample_sub(st_local("_qx"), st_local("prefix") + "esample"))
        local _qn : copy local _dq_in_`k'
        local _qr ""
        if `: length local _qn' {
            local _qr "in `_qn'"
        }
        if `: length local _qx' {
            capture noisily quietly replace `v' = 1 if (`macval(_qx)') `_qr'
        }
        else {
            capture noisily quietly replace `v' = 1 `_qr'
        }
        local rc = _rc
        if `rc' {
            mata: _dash_say("err", "`cmdname': Stata cannot evaluate the qualifier ", ///
                strtrim((st_local("_qx") != "" ? "if " + st_local("_qx") : "") + " " + st_local("_qr")), ///
                " against the data in memory.")
            exit `rc'
        }
    }
end

// ================================================================
// _dash_sort_gen <cmdname>  -- sort(varlist)'s rank columns, made in Stata
//
// twoway joins line, connected, area, rline, rarea and rconnected in the
// order -sort varlist- gives (strings byte by byte, . before .a before
// .b), which the data writer cannot carry: it writes every missing value
// as null.  So for each distinct varlist the table holds
// (_dash_sort_scan, _dash_sort_export) one double column __dashs<k> is
// made here, the rank of each row under -sort varlist obs-: ties keep the
// data's order.  The caller exports the columns with its variables and
// drops them at once, whether or not the export succeeded; the names come
// back in the caller's local _dash_sort_vars.  The sort variables
// themselves are never exported.  sortpreserve gives the data its order
// back.  The columns are <prefix>s<k> (WP-35 DT-19).  A sort()
// variable that is gone -- dropped or renamed since its graph was
// registered -- is refused in twoway's words, r(198), with nothing left
// behind (WP-29 P0.1).  Every name was checked to be a Stata name by
// _dash_sort_scan before it reaches the sort command.
// ================================================================
program define _dash_sort_gen, sortpreserve
    version 19
    // frame (WP-33 33-07): when given, only the lists that frame's graphs
    // use (_ds_f<k>) are ranked, over its own rows.
    args cmdname frame prefix
    if "`prefix'" == "" local prefix "__dash"
    local _ds_n = 0
    mata: _dash_sort_export()
    if `_ds_n' == 0 {
        c_local _dash_sort_vars ""
        exit
    }
    tempvar _ds_obs
    quietly generate double `_ds_obs' = _n
    local made ""
    forvalues k = 1/`_ds_n' {
        if `: length local frame' & !strpos("`_ds_f`k''", " `frame' ") continue
        foreach _ds_nm of local _ds_v`k' {
            capture confirm variable `_ds_nm', exact
            if _rc {
                if "`made'" != "" drop `made'
                mata: _dash_say("err", "variable ", st_local("_ds_nm"), " not found")
                display as error "option sort() incorrectly specified"
                display as error "      `cmdname': the variable was dropped or renamed after the graph was registered."
                exit 198
            }
        }
        sort `_ds_v`k'' `_ds_obs'
        quietly generate double `prefix's`k' = _n
        local made `made' `prefix's`k'
    }
    c_local _dash_sort_vars "`made'"
end

// ================================================================
// _dash_tsop_gen <cmdname>  -- the time-series columns, made in Stata
// (WP-30 P1.7)
//
// For each expression of the table (_dash_tsop_rewrite, _dash_tsop_export)
// one column __dasht<k> is made with tsrevar, as twoway computes the
// series it draws: over every observation, under the tsset in force now,
// gaps and panels included -- twoway scatter D.close t if t>5 & t<9 holds
// close[6]-close[5] at t = 6 (measured on StataNow 19.5).  The column
// takes tsrevar's storage type (D. of a float is float, L. of an int is
// int: a double would shift a float series off twoway's serset), and the
// base's display format and value label, as twoway draws L.foreign with
// foreign's labels and D.date in %td.  Each expression is held to the
// canonical form again (_dash_tsop_canon): the registry is a set of
// globals a do-file can edit since the rewrite read it.  Data not sorted
// by the time variable are refused by tsrevar in twoway's words, "not
// sorted", r(5).  Not sortpreserve: tsrevar reads the user's sort, which
// _dash_qual_gen_by and _dash_sort_gen give back.  Any error drops what was
// made; the names come back in the caller's local _dash_tsop_vars.  The
// columns are <prefix>t<k> (WP-35 DT-19).
// ================================================================
program define _dash_tsop_gen
    version 19
    // frame (WP-33 33-07): when given, only that frame's expressions
    // (_dts_f<k>) are made, under its own tsset.
    args cmdname frame prefix
    if "`prefix'" == "" local prefix "__dash"
    local _dts_n = 0
    mata: _dash_tsop_export()
    local _dt_mine 0
    forvalues k = 1/`_dts_n' {
        if !`: length local frame' | "`_dts_f`k''" == "`frame'" local ++_dt_mine
    }
    if `_dt_mine' == 0 {
        c_local _dash_tsop_vars ""
        exit
    }
    if `"`: char _dta[_TStvar]'"' == "" {
        display as error "time variable not set"
        exit 111
    }
    local made ""
    forvalues k = 1/`_dts_n' {
        if `: length local frame' & "`_dts_f`k''" != "`frame'" continue
        mata: st_local("_dt_ok", strofreal(_dash_tsop_canon(st_local("_dts_e`k'"))))
        if !`_dt_ok' {
            if "`made'" != "" drop `made'
            mata: _dash_say("err", "`cmdname': registry entry ", st_local("_dts_e`k'"), " holds a variable dash cannot read")
            exit 198
        }
        capture noisily tsrevar `_dts_e`k''
        if _rc {
            local rc = _rc
            if "`made'" != "" drop `made'
            exit `rc'
        }
        local _dt_src `r(varlist)'
        local _dt_ty : type `_dt_src'
        quietly generate `_dt_ty' `prefix't`k' = `_dt_src'
        local made `made' `prefix't`k'
        local _dt_base = substr("`_dts_e`k''", strpos("`_dts_e`k''", ".") + 1, .)
        mata: st_varformat(st_local("prefix") + "t`k'", st_varformat(st_local("_dt_base")))
        local _dt_vl : value label `_dt_base'
        if "`_dt_vl'" != "" label values `prefix't`k' `_dt_vl'
    }
    c_local _dash_tsop_vars "`made'"
end

// ================================================================
// _dash_wexp_gen <cmdname>  -- the weight-expression columns, made in
// Stata at export (WP-31 A5).  The twin of _dash_tsop_gen: each
// expression of the table (_dash_wexp_rewrite, _dash_wexp_export) becomes
// one column __dashw<k> = (expression), made by generate as twoway
// evaluates the weight -- over every observation -- with Stata's own
// message and code when generate refuses it ("nosuch not found", r(111);
// "time variable not set" for L.price+1 on data not tsset).  The table is
// a set of globals a do-file can edit, so each expression is held to
// _dash_wexp_ok again before generate sees it.  What was made is dropped
// on a refusal; the names come back in the caller's local
// _dash_wexp_vars.
// ================================================================
// _dash_wexp_yx <weight text>  -- twoway's yxview views (WP-31 A5b).
// serset.class's new uses a weight text that -syntax varlist(min=1 max=1
// numeric)- takes as one variable as typed (_genwt), and reads each of its
// words as a series name (series.class new: -syntax [anything]-, then the
// variable's type), so price-price, pri-pri, "price - price", (price) and
// "( price )" are refused with Stata's own words and code, as twoway
// refuses them, and any other text -- price+1, price-mpg, ((price)), pri
// -- is generated and taken.  Measured: weighted_markers_truth.json X_*.
program define _dash_wexp_yx
    version 19
    local _wy_x `"`macval(0)'"'
    capture syntax varlist(min=1 max=1 numeric)
    if _rc exit
    foreach _wy_t of local _wy_x {
        local 0 `"`macval(_wy_t)'"'
        capture syntax [anything]
        if _rc {
            local _wy_rc = _rc
            capture noisily syntax [anything]
            exit `_wy_rc'
        }
        capture local _wy_ty : type `_wy_t'
        if _rc {
            local _wy_rc = _rc
            capture noisily local _wy_ty : type `_wy_t'
            exit `_wy_rc'
        }
    }
end

program define _dash_wexp_gen
    version 19
    // frame (WP-33 33-07): when given, only that frame's expressions
    // (_dwx_f<k>) are made, from its own variables.
    args cmdname frame prefix
    if "`prefix'" == "" local prefix "__dash"
    local _dwx_n = 0
    mata: _dash_wexp_export()
    if `_dwx_n' == 0 {
        c_local _dash_wexp_vars ""
        exit
    }
    capture confirm variable `prefix'esample, exact
    local _dw_es = (_rc == 0)
    local made ""
    forvalues k = 1/`_dwx_n' {
        if `: length local frame' & "`_dwx_f`k''" != "`frame'" continue
        mata: st_local("_dw_ok", strofreal(_dash_wexp_ok(st_local("_dwx_e`k'"))))
        if !`_dw_ok' {
            if "`made'" != "" drop `made'
            mata: _dash_say("err", "`cmdname': registry entry [", st_local("_dwx_e`k'"), "] holds a weight dash cannot evaluate")
            exit 198
        }
        // An e(sample) of the weight reads the export's copy (WP-35 DT-19).
        if `_dw_es' mata: st_local("_dwx_e`k'", _dash_esample_sub(st_local("_dwx_e`k'"), st_local("prefix") + "esample"))
        capture quietly generate double `prefix'w`k' = (`macval(_dwx_e`k')')
        if _rc {
            local rc = _rc
            if "`made'" != "" drop `made'
            capture noisily generate double `prefix'w`k' = (`macval(_dwx_e`k')')
            capture drop `prefix'w`k'
            exit `rc'
        }
        local made `made' `prefix'w`k'
    }
    c_local _dash_wexp_vars "`made'"
end

// ================================================================
// _dash_play_check `"<play() text>"'  -- play() as twoway reads it
// ================================================================
// WP-32 (BUGS.md "play() is named in the note, where twoway refuses a
// recording it cannot find or read").  twoway plays a Graph Editor
// recording on the graph it has drawn (gr_play.ado; measured 19oct2026 in
// StataNow 19.5): ".grec" is added to a name whose last part has no ".",
// the name is looked for as given and then in PERSONAL's grec/ folder,
// never elsewhere on the ado-path, and none found is "recording <name>
// not found in either PERSONAL or working directory", r(601); a file
// without the GREC header is "<file> is not a Graph Recorder file",
// r(198) (_gs_rec_rdfilehdr.ado); play() empty plays nothing.  dash
// refuses as twoway does, and a recording twoway can read is refused
// too, r(198): its edits address twoway's graph objects, which a
// dashboard does not have, and a page drawn without them would not be the
// graph the command asks for.  The text is the user's, read by value and
// echoed through _dash_say.
program define _dash_play_check
    version 19
    mata: _dash_text_args(0, 0, 0)
    local pl : copy local _dash_txt
    mata: st_local("pl", strtrim(st_local("pl")))
    if !`: length local pl' exit
    mata: st_local("_pf", _dash_play_find(st_local("pl"), st_global("c(sysdir_personal)")))
    if !`: length local _pf' {
        mata: _dash_say("err", "recording ", st_local("pl"), " not found in either PERSONAL or working directory")
        exit 601
    }
    mata: st_local("_pok", strofreal(_dash_grec_ok(st_local("_pf"))))
    if !`_pok' {
        mata: _dash_say("err", "", st_local("_pf"), " is not a Graph Recorder file")
        exit 198
    }
    mata: _dash_say("err", "play(): ", st_local("_pf"), " is a Graph Editor recording, and dash cannot apply its Graph Editor edits to a dashboard; play it on the graph twoway draws")
    exit 198
end

// ================================================================
// _dash_report_ignored  — one note per command naming every option
//                         dash accepted but did not honour
// ================================================================
program define _dash_report_ignored
    version 19
    // Read by value (_dash_text_args): the unmatched options are the user's
    // text, and -args- cut foo("'x") bar(1) at its "', so bar() went
    // unnamed (test_json_escaping.cscript JSE-46).
    mata: _dash_text_args(0, 0, 0)
    local raw : copy local _dash_txt
    // An empty mlabfontface() is taken by twoway in silence (MLF-01).
    mata: st_local("raw", _dash_mlabff_strip(st_local("raw")))

    // `raw' mixes bare option names (pending, from the declared set) with the
    // verbatim text Stata could not match (unknown, from the trailing *).  Cut
    // each token at its opening parenthesis so the user sees option names, not
    // the values they supplied.
    // Walk the string with paren depth, so an option's argument is consumed
    // with its key.  `foreach tok of local raw' splits on whitespace and
    // parentheses are not grouping characters to it, so an unknown option
    // carrying a multi-word argument was reported as several options:
    //     dash scatter y x, addplot(line y2 x)
    //     dash: ignoring unsupported option(s): addplot() y2() x)()
    // naming two options that do not exist.
    // WP-32: the names typed with a value, which alone are written with
    // "()": twoway names a word as typed -- "option titling not allowed",
    // "option xsize() not allowed" -- where the note wrote titling().
    mata: st_local("_dash_valued", _dash_valued_names(st_local("raw")))
    mata: _dash_option_names("raw", "_dash_optnames")
    local raw : copy local _dash_optnames

    // Each name is cut, compared and joined in Mata, by value: a name is the
    // user's text -- a bare string dash could not match, "\$G", is one --
    // and in the quotes it was tested and copied in, a macro in it was
    // expanded again (test_json_escaping.cscript JSE-69).
    local seen " "
    local out  ""
    foreach tok of local raw {
        mata: st_local("tok", strtrim(st_local("tok")))
        mata: st_local("tok", strtrim(substr(st_local("tok"), 1, ///
            (strpos(st_local("tok"), "(") ? strpos(st_local("tok"), "(") - 1 : .))))
        if !`: length local tok' continue
        mata: st_local("dup", strofreal(strpos(st_local("seen"), " " + st_local("tok") + " ") > 0))
        if `dup' continue
        mata: st_local("seen", st_local("seen") + st_local("tok") + " ")
        // A weight is not an option and takes no argument: [aweight], not
        // aweight().
        mata: st_local("out", st_local("out") + " " + st_local("tok") + ///
            (anyof(tokens(st_local("_dash_valued")), st_local("tok")) ? "()" : ""))
    }
    if !`: length local out' exit

    // The names are the user's text: shown as written, never as SMCL.
    mata: _dash_note("dash: ignoring unsupported option(s):", st_local("out"), "")
end

// ================================================================
// _dash_plot  — parse and route a plot definition (0.1.0)
// ================================================================
program define _dash_plot
    version 19
    // WP-30 P1.28a: a path left by a command interrupted between its write
    // and its result must never reach a later command's r().
    capture macro drop dash__rfile
    // WP-30 P1.6: no earlier command's t-option units reach this graph.
    capture macro drop dash__tunit
    // WP-32: no earlier command's held refusal (_dash_pend).
    global dash__pend ""
    global dash__pend_msg ""
    // WP-35 syn:SD-3: no earlier command's p#() pairs (_dash_p_seg).
    global dash__pnum ""
    global dash__poff ""
    // WP-35 DT-15: no earlier command's held p#() spelling (_dash_p_apply).
    global dash__dop ""

    // ---- UTF-8 safety check ----
    // The command is read by value, here and at every command's gate: put
    // inside compound quotes in the Mata line, a text holding "' --
    // title(`"'90s cars"') -- ended them early, and the command stopped
    // with a Mata syntax error before anything was stored (measured
    // 24sep2026: r(3000) "'90s' found where almost anything else expected").
    mata: _dash_check_utf8(strtrim(st_local("0")))

    // A quoted string standing alone among the options is refused as
    // twoway refuses it, r(198), in its words (WP-31 D16b); the catch-all
    // kept it and named it in the note.  The text is never echoed.
    mata: st_local("_bsr", _dash_bare_string_refusal(st_local("0")))
    if `: length local _bsr' {
        display as error "`_bsr'"
        exit 198
    }

    // ---- Split on || / () into segments + graph opts ----
    // dash replaces twoway: with no plot it draws twoway's empty graph
    // (`dash', `dash, title(T)', `dash if foreign==1', `dash ||'; measured
    // 13oct2026, test/fixtures/bare_prefix_truth.json bare.*; maintainer
    // decision 14oct2026), so no plot is not an error here.
    mata: _dash_split_segs(strtrim(st_local("0")), 1)
    // Now locals _n_segs, _seg_1 .. _seg_N, _graph_opts_raw are set.

    // From here to the registry every piece of the command is the user's
    // text, and it is handed on by value.  Tested as  if `"`x'"' != "",  a
    // text holding "' -- title("'90s cars"), if make == "' or 1 or '" --
    // ended the quotes early, and the command stopped with r(109) or r(198),
    // or ran on with the test wrong (measured 24sep2026;
    // test_json_escaping.cscript JSE-42..49).  Copied as  local y `"`x'"'
    // or handed to a program on a command line, a macro in it was expanded
    // a second time (JSE-65..69).  So emptiness is `: length local', a copy
    // is `: copy local' or read in Mata, and a text handed to a program goes
    // through macval(), never on a one-line if, whose command Stata expands
    // again.
    local n_segs   = `_n_segs'
    local gopts_raw : copy local _graph_opts_raw


    // ---- The qualifier written between or after the plot groups ----
    // `dash (scatter y x) (line y x) if foreign==1': twoway applies it to
    // every plot (measured: 22 of auto's 74 in both), and dash.sthlp's
    // Syntax shows it, `dash plot_specs [if] [in]'.  The splitter used to
    // walk past it and drop it, so the graph drew every observation with
    // rc 0.  It is the graph's own qualifier now, read here with -syntax-,
    // which refuses what twoway refuses -- two ifs, a word or a plot group
    // after it -- before anything is parsed or reported.  A qualifier in a
    // bare plot of the || form is that plot's own, as in twoway; one in a
    // || piece with no plot, `a || b || if foreign==1', is the graph's.
    local _gq_if ""
    local _gq_in ""
    if `: length local _graph_qual_raw' {
        _dash_graph_qualifier `macval(_graph_qual_raw)'
    }
    // The checks _dash_process_segment makes over a plot's sample -- a
    // weight's values, histogram's start() -- read the graph's qualifier
    // as part of that sample, as twoway does: `(lfit mpg weight
    // [fw=halfint]) if foreign==1' was checked on every row and refused,
    // r(401), where twoway draws it (WP-27; test_help_claims_6.cscript
    // HC6-56).  Handed over in two globals, set by value for every command
    // -- empty when there is no qualifier -- and dropped after the loop.
    mata: st_global("dash__gq_if", st_local("_gq_if"))
    mata: st_global("dash__gq_in", st_local("_gq_in"))
    // by() written after the plot groups' comma is the graph's: a plot's
    // sample is then counted panel by panel, which _dash_process_segment
    // leaves to the renderer (P1A-80).  Set below, once that comma's
    // options are read.
    global dash__g_by ""
    // The axis options recorded for twoway's axis check (WP-29 P0.5):
    // emptied for this command, filled per segment, checked and emptied
    // again after the options after the comma are merged.
    mata: _dash_axreq_clear()
    // The axis options for axes 3-9, taken out of the option text by
    // _dash_route_axis2, for the graph's "axisn" object (WP-31 C10c).
    mata: _dash_axisn_clear()
    local _g_ys ""
    local _g_cvn 0
    local _g_hascont 0
    local _g_hascl 0
    local _g_xs ""
    local _tx_list ""
    // The by() panels drawn, for the added_text count (WP-30 P1.10).
    local _at_panels 1

    // ---- Initialise graph-level option accumulators ----
    foreach gk in title subtitle note caption name saving xtitle ytitle xlabel ///
          ylabel xline yline legend clegend plegend pcycle by xscale yscale aspectratio scheme ///
          plotregion graphregion bgcolor plotbgcolor link filter ytitle2 ///
          xtitle2 ylabel2 xlabel2 xmlabel2 ymlabel2 xmtick2 ymtick2 yscale2 xscale2 ytick2 xtick2 yline2 xline2 ///
            xsize ysize fxsize fysize ///
          scale text ttext hover xtick ytick xmtick ymtick xmlabel ymlabel tlabel ttick tmlabel tmtick tscale ttitle tline tlabel2 ttick2 tline2 tscale2 ttitle2 t1title ///
          t2title b1title b2title l1title l2title r1title r2title ///
          zlabel ztitle zscale aspectplacement xoverhangs yoverhangs nodraw play replace table {
        local g_`gk' ""
    }

    // ---- Parse graph-level opts from paren-mode suffix (if any) ----
    // _gund_acc: the graph-wide options dash does not declare given so far
    // (_dash_rep_und_scan's words), which twoway takes once from the whole
    // command -- after the comma, in any plot group or || segment.
    local _gund_acc ""
    local _rp_gund_out ""
    // WP-35 syn:SD-3: p1() .. p20() after the comma go to the plot of that
    // number, taken out before the graph options are parsed and handed to
    // each segment in $dash__pnum (_dash_p_seg); p21() and above are
    // refused after the segment loop, as twoway refuses them after every
    // plot group's refusal (test/fixtures/pnum_truth.json order_p21).
    mata: st_local("gopts_raw", _dash_p_take(st_local("gopts_raw")))
    local _pt_gbad : copy local _pt_bad
    mata: st_global("dash__pnum", st_local("_pt_pairs"))
    local _gopts_axraw : copy local gopts_raw
    // WP-35 DT-15: the first spelling twoway refuses that dash once took,
    // after the comma, as typed; refused after the segment loop.
    mata: st_local("_do_g", _dash_dashonly_typed(st_local("gopts_raw"), 0))
    local _do_gpre : copy local _do_pre
    if `: length local gopts_raw' {
        mata: st_local("gopts_raw", _dash_route_axis2(st_local("gopts_raw")))
        _dash_parse_graph_opts , `macval(gopts_raw)'
        // The refusals of the options after the comma (_dash_gopts_checks)
        // come after every plot group's, as twoway reads them (WP-32): run
        // quietly here, and when one refuses, the list is parsed again and
        // the refusal given after the segment loop, once no group's is.
        local _rp_gund_out ""
        capture _dash_gopts_checks `"`macval(gopts_raw)'"'
        local _gac_rc = _rc
        if `_gac_rc' {
            sreturn clear
            _dash_parse_graph_opts , `macval(gopts_raw)'
            local _rp_gund_out ""
        }
        local _gund_acc : copy local _rp_gund_out
        mata: st_local("_g_names_n", strofreal(st_global("s(name)") != ""))
        foreach gk in title subtitle note caption name saving xtitle ytitle xlabel ///
              ylabel xline yline legend clegend plegend pcycle by xscale yscale aspectratio scheme ///
              plotregion graphregion bgcolor plotbgcolor link filter ytitle2 ///
              xtitle2 ylabel2 xlabel2 xmlabel2 ymlabel2 xmtick2 ymtick2 yscale2 xscale2 ytick2 xtick2 yline2 xline2 ///
            xsize ysize fxsize fysize ///
              scale text ttext hover xtick ytick xmtick ymtick xmlabel ymlabel tlabel ttick tmlabel tmtick tscale ttitle tline tlabel2 ttick2 tline2 tscale2 ttitle2 t1title ///
              t2title b1title b2title l1title l2title r1title r2title ///
              zlabel ztitle zscale aspectplacement xoverhangs yoverhangs nodraw play replace table {
            mata: st_local("_gv", st_global("s(" + st_local("gk") + ")"))
            if `: length local _gv' {
                // Kept apart and merged in after the segment loop: an option
                // written after the top-level comma applies to the GRAPH,
                // and twoway reads it after every plot's copy:
                //     twoway (scatter y x, title("INSIDE")) (line y x), title("AFTER")
                // stores "AFTER" -- measured from the saved .gph -- and
                // (scatter y x, title(A)), title(, color(red)) draws A in
                // red (measured 24sep2026 from the SVG export).
                local _gafter_`gk' : copy local _gv
            }
        }
        // The graph-level options dash cannot honour, captured HERE.
        //
        // _dash_parse_graph_opts sreturns them, and nothing read them: the
        // accumulator was initialised to "" just below, and the first thing
        // the segment loop does is `sreturn clear', which destroys s().  So
        // in paren mode -- `dash (scatter y x) (line y x), fxsize(30)' --
        // an unsupported graph-level option was dropped in complete
        // silence, which is the one thing the reporter exists to prevent,
        // while the identical option in comma mode was named correctly.
        mata: st_local("_dash_gopt_ignored", _dash_pending_note(st_global("s(_pending)")) + " " + st_global("s(_unknown)"))
    }

    local _dash_ignored_acc : copy local _dash_gopt_ignored
    if "`_g_names_n'" == "" local _g_names_n 0
    // The by() after the comma is held in _gafter_by until the segments
    // are merged: g_by, read here before, is still empty, so a plot group's
    // sample was counted as if there were no by() -- `(scatter mpg weight
    // if mpg > 1000) (lpoly mpg weight if mpg > 1000), by(foreign)' was
    // "no observations", r(2000), where twoway says "nothing to graph",
    // r(198) (P1A-83).
    mata: st_global("dash__g_by", st_local("_gafter_by"))
    // A by() given in any segment is the graph's too: twoway reads it from
    // every || segment and plot group before it draws a plot, so a plot in
    // a segment before the one that gives it -- `lfit mpg weight if _n==1
    // || scatter mpg weight, by(foreign)', rc 0 -- or after it is answered
    // panel by panel.  Read here, by value, before any segment is checked:
    // the other segments were checked as graphs of their own, r(2001)
    // "insufficient observations" (measured 24sep2026; test_parser.cscript
    // P1A-84).
    if !`: length global dash__g_by' {
        forvalues k = 1/`n_segs' {
            mata: st_local("_pre_by", _dash_seg_by(st_local("_seg_`k'")))
            if `: length local _pre_by' {
                mata: st_global("dash__g_by", st_local("_pre_by"))
                continue, break
            }
        }
    }

    // ---- Parse each plot segment ----
    // WP-19: a graph holds at most `plots' plot entries -- one per y
    // variable of a varlist, one for any other segment.  A single segment
    // over the limit is refused inside _dash_process_segment, before its
    // plot objects are built; the running total across segments is kept
    // here.  The limit is read once, before any segment is parsed, so a bad
    // dash_max_plots is refused first.  Refused here, nothing is registered.
    _dash_limit, name(plots)
    local _dash_plot_lim  = r(value)
    local _dash_plot_ceil = r(ceiling)
    local _dash_nplots    = 0
    local plots_json ""
    // The graph-level options twoway takes once from the whole command:
    // a second copy, in another plot group, another || segment or after
    // the comma, is "option scheme() not allowed", r(198) (measured
    // 24sep2026 for each; name() has its own check, above and below).
    local _g_unique "saving scheme aspectratio aspectplacement xsize ysize scale fxsize fysize nodraw play table"
    // The function layers, collected for evaluation after the loop.
    local _fn_m 0
    // The fit layers' points (WP-31 C4): each segment's in _ft_sc
    // (_dash_process_segment, named in $dash__ftsc), kept as "<k>":{..} in
    // _ft_acc beside the function layers' points.
    tempname _ft_sc _ft_acc
    mata: st_strscalar(st_local("_ft_acc"), "")
    global dash__ftsc `_ft_sc'
    foreach gk of local _g_unique {
        local _gseen_`gk' = `: length local _gafter_`gk'' > 0
    }
    // WP-32: the random-number state before the first segment, put back
    // before a held refusal is given (_dash_pend), as twoway refuses
    // before it evaluates a function plot.
    local _pend_rng = c(rngstate)
    forvalues k = 1/`n_segs' {
        local seg : copy local _seg_`k'

        local _seg_ignored_out ""
        local _seg_gund_out    ""
        local _seg_nplots_out  1
        local _seg_named_out   0
        local _seg_if_out      ""
        local _seg_in_out      ""
        local _seg_bands_out   0
        local _seg_vars_out    ""
        local _seg_wvar_out    ""
        local _seg_fnraw_out   ""
        local _seg_fnx_out     ""
        local _seg_fnlo_out    ""
        local _seg_fnhi_out    ""
        local _seg_fnn_out     ""
        local _seg_axreq_raw   ""
        local _seg_yaxis_out   1
        local _seg_xaxis_out   1
        local _seg_yaxes_out   1
        local _seg_xaxes_out   1
        local _seg_xvar_out    ""
        local _seg_cv_out      0
        local _seg_cvam_out    0
        foreach gk in title subtitle note caption name saving xtitle ytitle xlabel ///
              ylabel xline yline legend clegend plegend pcycle by xscale yscale aspectratio scheme ///
              plotregion graphregion bgcolor plotbgcolor link filter ytitle2 ///
              xtitle2 ylabel2 xlabel2 xmlabel2 ymlabel2 xmtick2 ymtick2 yscale2 xscale2 ytick2 xtick2 yline2 xline2 ///
            xsize ysize fxsize fysize ///
              scale text ttext hover xtick ytick xmtick ymtick xmlabel ymlabel tlabel ttick tmlabel tmtick tscale ttitle tline tlabel2 ttick2 tline2 tscale2 ttitle2 t1title ///
              t2title b1title b2title l1title l2title r1title r2title ///
              zlabel ztitle zscale aspectplacement xoverhangs yoverhangs nodraw play replace table {
            local _sg_`gk' ""
        }
        mata: st_strscalar(st_local("_ft_sc"), "")
        global dash__poff `_dash_nplots'
        _dash_process_segment `"`macval(seg)'"' _pt_k _json_k `n_segs'
        // twoway draws one colorvar() layer a graph: a later one is
        // refused unless it says colorallowmultiple itself (WP-31 C8b,
        // colorvar_options_truth.json R03, R03b, R03c).
        // WP-31 B4b: one contour and one contourline a graph, and no
        // colorvar() layer after a contour unless it says
        // colorallowmultiple (twowaygraph_g.class:349-394, measured
        // 15oct2026, contour_truth.json refuse.two_*; a contour and a
        // contourline together draw).
        if "`_pt_k'" == "contour" {
            if 0`_g_hascont' {
                display as error "multiple contour, heatmap, or patch plots not allowed"
                exit 198
            }
            local _g_hascont 1
        }
        if "`_pt_k'" == "contourline" {
            if 0`_g_hascl' {
                display as error "multiple contourline plots not allowed"
                exit 198
            }
            local _g_hascl 1
        }
        if `_seg_cv_out' {
            if (`_g_cvn' | 0`_g_hascont') & !`_seg_cvam_out' {
                display as error "multiple contour, patch, or colorvar plots not allowed"
                exit 198
            }
            local ++_g_cvn
        }
        // This segment's axis options, as typed, and its layers' axes, for
        // twoway's axis check after the loop (WP-29 P0.5).
        mata: _dash_axreq_add(st_local("_seg_axreq_raw"), `k')
        // Its options as typed and its type, for the graph-wide omit
        // check after the loop (WP-35 basic:PT-8).
        mata: st_local("_g_omraw", st_local("_g_omraw") + " " + st_local("_seg_axreq_raw"))
        local _g_axraw_`k' : copy local _seg_axreq_raw
        local _g_ompt `_g_ompt' `_pt_k'
        local _g_ys `_g_ys' `_seg_yaxes_out'
        local _g_ys : list uniq _g_ys
        local _g_xs `_g_xs' `_seg_xaxes_out'
        local _g_xs : list uniq _g_xs
        // Each segment's type, x variable and x axis, for the t-options'
        // units (WP-30 P1.6): "type:variable:axis", "." for no variable.
        local _tx_list `"`_tx_list' `_pt_k':`=cond("`_seg_xvar_out'" == "", ".", "`_seg_xvar_out'")':`_seg_xaxis_out'"'
        // Kept for the by() answer below, by value.
        local _byq_pt_`k' `_pt_k'
        local _byq_if_`k' : copy local _seg_if_out
        local _byq_in_`k' : copy local _seg_in_out
        local _byq_bd_`k' `_seg_bands_out'
        local _byq_vv_`k' `_seg_vars_out'
        local _byq_wv_`k' `_seg_wvar_out'

        // A graph takes one name(): a second, in another group or ||
        // segment than the first, or beside the one after the comma, is
        // refused as twoway refuses it -- before this segment's name() can
        // overwrite the first and before anything is registered.
        local _g_names_n = `_g_names_n' + `_seg_named_out'
        if `_g_names_n' > 1 _dash_refuse_second_name

        // A graph-wide option dash does not declare, given in this segment
        // and in an earlier one or after the comma: refused as twoway
        // refuses it -- (scatter y x, notitling) (line y x, notitling) is
        // "option notitling not allowed", r(198) (measured 24sep2026).
        if `: length local _seg_gund_out' {
            mata: _dash_rep_und_cross("_gund_acc", "_seg_gund_out")
            if `: length local _rp_refuse' _dash_pend _dash_refuse_repeat `_rp_refuse'
        }

        local _dash_nplots = `_dash_nplots' + `_seg_nplots_out'
        // A fit layer's points, under its place in the plots (WP-31 C4).
        mata: st_strscalar(st_local("_ft_acc"), st_strscalar(st_local("_ft_acc")) + ///
            (st_strscalar(st_local("_ft_sc")) == "" ? "" : ///
            (st_strscalar(st_local("_ft_acc")) == "" ? "" : ",") + char(34) + ///
            st_local("_dash_nplots") + char(34) + ":" + st_strscalar(st_local("_ft_sc"))))
        // A function layer: its place in the plots array (from 1), its
        // text, range() and n(), for _dash_fn_points below (WP-29 P0.6).
        if "`_pt_k'" == "function" {
            local ++_fn_m
            local _fn_k_`_fn_m' `_dash_nplots'
            local _fn_raw_`_fn_m' : copy local _seg_fnraw_out
            local _fn_x_`_fn_m' "`_seg_fnx_out'"
            local _fn_lo_`_fn_m' : copy local _seg_fnlo_out
            local _fn_hi_`_fn_m' : copy local _seg_fnhi_out
            local _fn_n_`_fn_m' : copy local _seg_fnn_out
            local _fn_d_`_fn_m' : copy local _seg_fndrops_out
        }
        if `_dash_nplots' > `_dash_plot_lim' {
            // The graph's total is known only once its last segment is in.
            if `k' == `n_segs' {
                _dash_plot_cap_refuse `_dash_plot_lim' `_dash_plot_ceil' `_dash_nplots'
            }
            else _dash_plot_cap_refuse `_dash_plot_lim' `_dash_plot_ceil'
        }

        if `: length local _seg_ignored_out' {
            mata: st_local("_dash_ignored_acc", st_local("_dash_ignored_acc") + " " + st_local("_seg_ignored_out"))
        }

        // _dash_process_segment hands back this segment's graph-level
        // options as _sg_* locals; each is merged into its g_* accumulator
        // as twoway merges a repeated option -- the last copy of most, the
        // copies joined for title() legend() xlabel() and the like -- and a
        // second copy of one twoway takes once is refused as twoway
        // refuses it.  The key is a word of the list and the values are
        // read by value, in Mata.
        foreach gk in title subtitle note caption name saving xtitle ytitle xlabel ///
              ylabel xline yline legend clegend plegend pcycle by xscale yscale aspectratio scheme ///
              plotregion graphregion bgcolor plotbgcolor link filter ytitle2 ///
              xtitle2 ylabel2 xlabel2 xmlabel2 ymlabel2 xmtick2 ymtick2 yscale2 xscale2 ytick2 xtick2 yline2 xline2 ///
            xsize ysize fxsize fysize ///
              scale text ttext hover xtick ytick xmtick ymtick xmlabel ymlabel tlabel ttick tmlabel tmtick tscale ttitle tline tlabel2 ttick2 tline2 tscale2 ttitle2 t1title ///
              t2title b1title b2title l1title l2title r1title r2title ///
              zlabel ztitle zscale aspectplacement xoverhangs yoverhangs nodraw play replace table {
            if !`: length local _sg_`gk'' continue
            if `: list gk in _g_unique' {
                if `_gseen_`gk'' _dash_pend _dash_refuse_gunique `gk'
                local _gseen_`gk' 1
            }
            mata: _dash_rep_merge_locals(st_local("gk"), "g_`gk'", "_sg_`gk'", "g_`gk'")
        }

        if `k' > 1 local plots_json `"`plots_json',"'
        local plots_json `"`plots_json'`_json_k'"'
    }
    global dash__pnum ""
    global dash__poff ""
    local _do_held : copy global dash__dop
    global dash__dop ""

    // WP-32: the refusals twoway gives only once every plot's options are
    // read -- held by _dash_pend -- before any function layer is evaluated;
    // the options after the plot groups' comma, which twoway reads last,
    // below (test/fixtures/
    // unknown_option_truth.json orders: (kdensity mpg, gaussian epan2),
    // bogus is the kernel's refusal, (scatter mpg weight, bogus), xsize(3)
    // xsize(4) names bogus).
    if `"${dash__pend}"' != "" {
        local _pend_cmd `"${dash__pend}"'
        global dash__pend ""
        if `: length local _pend_rng' set rngstate `_pend_rng'
        `_pend_cmd'
    }

    macro drop dash__gq_if dash__gq_in dash__g_by

    // ---- An after-comma option comes after every segment's ----
    // Merged after the segment loop, as twoway reads it: the last copy of
    // a rightmost option, so the after-comma one outranks a segment's, and
    // the copies joined for a merged one.  Only keys the after-comma parse
    // set are merged, so a graph that names an option only inside a
    // segment keeps that value.
    foreach gk in title subtitle note caption name saving xtitle ytitle xlabel ///
              ylabel xline yline legend clegend plegend pcycle by xscale yscale aspectratio scheme ///
              plotregion graphregion bgcolor plotbgcolor link filter ytitle2 ///
              xtitle2 ylabel2 xlabel2 xmlabel2 ymlabel2 xmtick2 ymtick2 yscale2 xscale2 ytick2 xtick2 yline2 xline2 ///
            xsize ysize fxsize fysize ///
              scale text ttext hover xtick ytick xmtick ymtick xmlabel ymlabel tlabel ttick tmlabel tmtick tscale ttitle tline tlabel2 ttick2 tline2 tscale2 ttitle2 t1title ///
              t2title b1title b2title l1title l2title r1title r2title ///
              zlabel ztitle zscale aspectplacement xoverhangs yoverhangs nodraw play replace table {
        if `: length local _gafter_`gk'' {
            mata: _dash_rep_merge_locals(st_local("gk"), "g_`gk'", "_gafter_`gk'", "g_`gk'")
        }
    }

    // ---- Two omit options in one command (WP-35 basic:PT-8) ----
    // twoway refuses omitanymiss, omitallmiss, omitdupmiss and omitnothing
    // given twice or more anywhere in the command -- one list, two lists,
    // after the comma -- r(198), "option omitanymissomitallmiss not
    // allowed", unless every plot is one that takes them (lfit, qfit,
    // fpfit and their ci forms, scatteri, pci, pcarrowi; measured,
    // test/fixtures/graph_refusal_truth.json omit.*).
    mata: st_local("_omp", _dash_omit_pair(st_local("_g_omraw") + " " + st_local("_gopts_axraw"), st_local("_g_ompt")))
    if `: length local _omp' {
        mata: _dash_say("err", "option ", st_local("_omp"), " not allowed")
        exit 198
    }

    // ---- maxaxes() as twoway checks it (WP-35 GW-3) ----
    // The last maxaxes() of the command: one that is no integer is refused,
    // r(198); a yaxis() or xaxis() number above it, in any list, r(125),
    // the layers in order and xaxis() before yaxis() in one; any integer is
    // taken, and not named, when no axis given is above it (measured,
    // graph_refusal_truth.json maxaxes.*).
    mata: st_local("_mxa", _dash_maxaxes_val(st_local("_g_omraw") + " " + st_local("_gopts_axraw"), "maxaxes"))
    if `: length local _mxa' {
        mata: st_local("_mxok", strofreal(ustrregexm(st_local("_mxa"), "^[+-]?[0-9]+$")))
        if !`_mxok' {
            display as error "option maxaxes() not allowed"
            exit 198
        }
        forvalues k = 1/`n_segs' {
            foreach _mxw in xaxis yaxis {
                mata: st_local("_mxn", _dash_maxaxes_val(st_local("_g_axraw_`k'"), "`_mxw'"))
                mata: st_local("_mxhi", st_local("_mxn") == "" ? "." : strofreal(max(strtoreal(tokens(st_local("_mxn"))))))
                if `_mxhi' < . & `_mxhi' > `_mxa' {
                    display as error "`_mxw'() invalid -- invalid numlist has elements outside of allowed range"
                    exit 125
                }
            }
        }
        mata: st_local("_dash_ignored_acc", _dash_maxaxes_val(st_local("_dash_ignored_acc"), "drop"))
    }

    // ---- aspectratio() with an overhang (WP-35 GW-2) ----
    // twoway refuses aspectratio() with xoverhangs or yoverhangs wherever
    // each is given, r(198) (twowaygraph_g.class; graph_refusal_truth.json
    // asp.*).
    if `: length local g_aspectratio' & (`: length local g_xoverhangs' | `: length local g_yoverhangs') {
        display as error "may not combine option aspectratio() with xoverhangs or yoverhangs"
        exit 198
    }

    // ---- A title with notitling (WP-35 sil:SD-8) ----
    // twoway fails, r(4018), on notitling with title(), subtitle(), note()
    // or caption() anywhere in the command, naming the first of note,
    // caption, subtitle, title given and its text before its comma as
    // typed (twowaygraph_g.class; graph_refusal_truth.json notitling.*).
    // The text is the user's: read by value and cut to 200 characters.
    mata: st_local("_ntl", strofreal(anyof(_dash_opt_tokens(st_local("_g_omraw") + " " + st_local("_gopts_axraw")), "notitling")))
    if `_ntl' {
        foreach _ntk in note caption subtitle title {
            if !`: length local g_`_ntk'' continue
            mata: _dash_comma_pos(st_local("g_`_ntk'"), "_ntc")
            mata: st_local("_ntx", usubstr(strtrim(`_ntc' ? substr(st_local("g_`_ntk'"), 1, `_ntc' - 1) : st_local("g_`_ntk'")), 1, 200))
            mata: _dash_say("err", "`_ntk'.edit , mtextq(" + char(96) + char(34), st_local("_ntx"), char(34) + char(39) + ") : class type not found")
            exit 4018
        }
    }

    // ---- axis(#) as twoway checks it (WP-29 P0.5) ----
    // twoway's ParseAndLogAxes refuses an axis option whose axis(#) names
    // an axis no layer is drawn on, an axis() in capitals or given twice,
    // and a second comma, r(198), side by side, family by family, the
    // segments before the options after the comma.  The options after the
    // comma are read last, as segment n_segs+1.
    mata: _dash_axreq_add(st_local("_gopts_axraw"), `n_segs' + 1)
    // graphregion() then plotregion() before legend() and the axes, as
    // twoway parses them (WP-30 P1.20a).
    _dash_subopt_check region
    _dash_subopt_check legend
    mata: st_local("_axrc", strofreal(_dash_axreq_check(st_local("_g_ys"), st_local("_g_xs"))))
    // A line's positions go to Stata's own numlist, one copy at a time, in
    // twoway's order (WP-30 P1.21a): -1 hands one back in _ln_text/_ln_row.
    while `_axrc' == -1 {
        _dash_line_check `_ln_row' `"`macval(_ln_text)'"'
        mata: st_local("_axrc", strofreal(_dash_axreq_check(st_local("_g_ys"), st_local("_g_xs"))))
    }
    if `_axrc' exit `_axrc'
    // ---- The graph with no plot has no axis (WP-35 plot:PT-4) ----
    // twoway draws no axis when no plot is given, and refuses an axis,
    // scale, line, tick or title option there, or by(), r(198), "xlabels(1
    // 2) not allowed, xaxis1 does not exist" -- the option as twoway names
    // it, its text, the axis -- the first in this order whatever the order
    // typed (test/fixtures/command_grammar_truth.json empty.*,
    // empty.order_names).  by() is refused for the x labels it sets.  The
    // text is read by value and cut to 80 characters.
    if `n_segs' == 0 {
        foreach _ek in xscale xlabel by xmlabel xtick xtitle xline tlabel ttitle yscale ylabel ytitle yline {
            if !`: length local g_`_ek'' continue
            if "`_ek'" == "by" {
                mata: _dash_say("err", "", "", "xlabels(#4) not allowed, xaxis1 does not exist")
                exit 198
            }
            local _en "`_ek'"
            if inlist("`_ek'", "xlabel", "ylabel", "xline", "yline", "xtick", "xmlabel", "tlabel") local _en "`_ek's"
            local _eax = cond(substr("`_ek'", 1, 1) == "y", "yaxis1", "xaxis1")
            mata: st_local("_ea", st_local("g_`_ek'") == char(34) + char(34) ? "" : usubstr(st_local("g_`_ek'"), 1, 80))
            mata: _dash_say("err", st_local("_en") + "(", st_local("_ea"), ") not allowed, " + st_local("_eax") + " does not exist")
            exit 198
        }
    }
    foreach _lx in g_xline g_yline g_xline2 g_yline2 {
        if `"`macval(`_lx')'"' != "" _dash_line_expand `_lx' `"`macval(`_lx')'"'
    }
    // WP-31 H2t: table()'s sub-options, rows(#) and open (_dash_table_check).
    if `"`macval(g_table)'"' != "" _dash_table_check `"`macval(g_table)'"'
    _dash_subopt_check zlabel
    // The label forms twoway refuses, in its words (WP-31 D6; measured,
    // test/fixtures/axis_look_truth.json ref_*): r(198) "invalid label
    // specifier, :  <the part>:" (two blanks, as twoway writes it).
    foreach _alo in xlabel ylabel xtick ytick xlabel2 ylabel2 xtick2 ytick2 {
        mata: st_local("_alr", _dash_axlabel_refusal(st_local("g_`_alo'")))
        if `"`macval(_alr)'"' != "" {
            mata: _dash_say("err", "invalid label specifier, :  ", st_local("_alr"), ":")
            exit 198
        }
    }
    _dash_subopt_check title

    // ---- The t-options onto the x axis (WP-30 P1.6) ----
    // twoway reads tlabel() .. tline() after every x option, each date
    // literal in the unit of the x axis's label format, and refuses a date
    // literal written in an x option (_dash_taxis_fold).  The values go
    // over by value, in globals, and come back as the g_ locals; the spec
    // never carries a t key.  tm() and ts() are no option of twoway's.
    // The y label, tick and scale options go over too, for the date
    // literals twoway refuses there (WP-31 A8).
    foreach _tk in name xlabel xtick xmlabel xmtick xline xscale xtitle xlabel2 ///
            xtick2 xmlabel2 xmtick2 xline2 xscale2 xtitle2 tlabel ttick tmlabel tmtick tscale ttitle ///
            tline tlabel2 ttick2 tline2 tscale2 ttitle2 ///
            ylabel ytick ymlabel ymtick ylabel2 ytick2 yscale yscale2 {
        mata: st_global("dash__tf_`_tk'", st_local("g_`_tk'"))
    }
    mata: st_global("dash__tf_ign", st_local("_dash_ignored_acc"))
    capture noisily _dash_taxis_fold `_tx_list'
    local _tf_rc = _rc
    if !`_tf_rc' {
        foreach _tk in xlabel xtick xmlabel xmtick xline xscale xtitle xlabel2 ///
                xtick2 xmlabel2 xmtick2 xline2 xscale2 xtitle2 tlabel ttick tmlabel tmtick tscale ///
                ttitle tline tlabel2 ttick2 tline2 tscale2 ttitle2 ///
                ylabel ytick ymlabel ymtick ylabel2 ytick2 yscale yscale2 {
            mata: st_local("g_`_tk'", st_global("dash__tf_`_tk'"))
        }
        mata: st_local("_dash_ignored_acc", st_global("dash__tf_ign"))
    }
    capture macro drop dash__tf_*
    if `_tf_rc' exit `_tf_rc'

    // ---- Validate the graph-level values (WP-15) ----
    // After the restore above, so the value checked is the one that will
    // be written, and before the report below, so a refused value is never
    // half-reported.  The rules live in _dash_option_rules; a normalised
    // value (an expanded variable name) is written back to its g_ local.
    //
    // twoway's order (WP-29 P0.6, measured): every plot's variables and
    // options and the by() variables are checked, then each function
    // layer is evaluated, in order, then the graph options are checked.
    // So by() is validated alone first, the layers are evaluated
    // (_dash_fn_points, which advances the random-number state as twoway
    // does), and the other graph rules follow.  A pre-check of every layer
    // would refuse (function y=runiform()) (function y=nosuch(x)) before
    // the first layer draws, where twoway has drawn it.
    _dash_option_rules
    foreach _vrule of local _dash_rules_graph {
        local _veq   = strpos("`_vrule'", "=")
        local _vopt  = substr("`_vrule'", 1, `_veq' - 1)
        if "`_vopt'" != "by" continue
        local _vspec = substr("`_vrule'", `_veq' + 1, .)
        local _vval : copy local g_`_vopt'
        if !`: length local _vval' continue
        _dash_validate_value "dash" "`_vopt'" "`_vspec'" `"`macval(_vval)'"' ""
        local g_`_vopt' : copy local _dash_vnorm
    }
    // Each function layer's points, as one JSON object keyed by the
    // layer's place, held in a string scalar -- never a macro, which a
    // dashboard of 10,000-point layers would overflow (_dash_register_graph
    // checks it against c(macrolen)).
    tempname _fp_sc _fx_raw
    mata: st_strscalar(st_local("_fp_sc"), "")
    // Under by(), twoway evaluates each function layer once per panel, in
    // panel order, over the same range() (WP-31 C12, measured: function
    // y = runiform(), by(foreign) draws different points in each panel):
    // the layer's points become {"panels": {"<i>": points}}, i the panel's
    // place from 0, which the renderers read per panel
    // (_dash_fn_panel_spec).  One panel, or none, keeps the flat form.
    local _fn_np 0
    if `_fn_m' & `: length local g_by' {
        // The panels by() draws over the graph's if and in.
        tempvar _fn_tu
        quietly generate byte `_fn_tu' = 0
        local _fn_q ""
        if `: length local _gq_if' local _fn_q `"if (`macval(_gq_if)')"'
        if `: length local _gq_in' local _fn_q `"`macval(_fn_q)' in `macval(_gq_in)'"'
        quietly replace `_fn_tu' = 1 `macval(_fn_q)'
        mata: st_local("_fn_np", strofreal(_dash_fn_panel_count(st_local("g_by"), st_local("_fn_tu"))))
        drop `_fn_tu'
    }
    if `_fn_np' > 1 {
        forvalues _m = 1/`_fn_m' {
            tempname _fpl_`_m'
            mata: st_strscalar(st_local("_fpl_`_m'"), "")
        }
        forvalues _p = 1/`_fn_np' {
            forvalues _m = 1/`_fn_m' {
                mata: st_strscalar(st_local("_fx_raw"), st_local("_fn_raw_`_m'"))
                _dash_fn_points `_fx_raw' `_fn_lo_`_m'' `_fn_hi_`_m'' `_fn_n_`_m'' `=`_p'-1' `_fpl_`_m'' "`_fn_d_`_m''" `_fn_x_`_m''
            }
        }
        forvalues _m = 1/`_fn_m' {
            mata: st_strscalar(st_local("_fp_sc"), st_strscalar(st_local("_fp_sc")) + ///
                (st_strscalar(st_local("_fp_sc")) == "" ? "" : ",") + char(34) + ///
                st_local("_fn_k_`_m'") + char(34) + ":{" + char(34) + "panels" + ///
                char(34) + ":{" + st_strscalar(st_local("_fpl_`_m'")) + "}}")
        }
    }
    else {
        forvalues _m = 1/`_fn_m' {
            mata: st_strscalar(st_local("_fx_raw"), st_local("_fn_raw_`_m'"))
            _dash_fn_points `_fx_raw' `_fn_lo_`_m'' `_fn_hi_`_m'' `_fn_n_`_m'' `_fn_k_`_m'' `_fp_sc' "`_fn_d_`_m''" `_fn_x_`_m''
        }
    }
    // The fit layers' points join the function layers' (WP-31 C4).
    mata: st_strscalar(st_local("_fp_sc"), st_strscalar(st_local("_fp_sc")) + ///
        (st_strscalar(st_local("_fp_sc")) == "" | st_strscalar(st_local("_ft_acc")) == "" ? "" : ",") + ///
        st_strscalar(st_local("_ft_acc")))
    global dash__ftsc ""
    mata: st_strscalar(st_local("_fp_sc"), (st_strscalar(st_local("_fp_sc")) == "" ? "" : "{" + st_strscalar(st_local("_fp_sc")) + "}"))
    macro drop dash__uv
    // WP-32: the options after the plot groups' comma refused here, after
    // every plot's and after the function layers are evaluated, as twoway
    // refuses a graph option (test_parser.cscript FX-02: a runiform()
    // layer advances the random-number state).
    // WP-35 DT-15: a spelling twoway refuses inside a p#() text, held by
    // _dash_p_apply ($dash__dop, taken into _do_held after the segment
    // loop): after every plot group's refusal, before the options
    // after the comma (dash_only_words_truth.json order.p_*).
    if `: length local _do_held' {
        mata: _dash_dashonly_say(substr(st_local("_do_held"), 1, strpos(st_local("_do_held"), char(1)) - 1), substr(st_local("_do_held"), strpos(st_local("_do_held"), char(1)) + 1, .))
    }
    if `: length local _pt_gbad' {
        // pnum_truth.json g_p21: scatter mpg weight, p21(mcolor(red)) is
        // "p21(mcolor(red)):  too many arguments", r(103).
        mata: _dash_say("err", "", st_local("_pt_gbad"), ":  too many arguments")
        exit 103
    }
    // WP-35 DT-15: the spelling after the comma found before the loop,
    // after the refusal of any word typed before it there.
    if `: length local _do_g' {
        if `: length local _do_gpre' {
            sreturn clear
            _dash_parse_graph_opts , `macval(_do_gpre)'
            _dash_gopts_checks `"`macval(_do_gpre)'"'
        }
        mata: _dash_dashonly_say(st_local("_do_g"), "")
    }
    if 0`_gac_rc' {
        sreturn clear
        _dash_parse_graph_opts , `macval(gopts_raw)'
        _dash_gopts_checks `"`macval(gopts_raw)'"'
        exit `_gac_rc'
    }
    foreach _vrule of local _dash_rules_graph {
        local _veq   = strpos("`_vrule'", "=")
        local _vopt  = substr("`_vrule'", 1, `_veq' - 1)
        if "`_vopt'" == "by" continue
        local _vspec = substr("`_vrule'", `_veq' + 1, .)
        local _vval : copy local g_`_vopt'
        if !`: length local _vval' continue
        _dash_validate_value "dash" "`_vopt'" "`_vspec'" `"`macval(_vval)'"' ""
        local g_`_vopt' : copy local _dash_vnorm
    }
    // WP-30 P1.18a: the bounds twoway checks when it draws, on the merged
    // options, in its order (y1, x1, y2, x2; the scale's lwidth() before
    // a label's or tick's angle()): an angle() outside -360..360 and a
    // scale lwidth() outside 0..10000, r(198) in twoway's words.  dash
    // always draws the page, so it checks under nodraw too.
    mata: _dash_axbound_list()
    forvalues _j = 1/`_axb_n' {
        local _axv : copy local _axb_v`_j'
        if "`_axb_k`_j''" == "l" {
            _dash_validate_value "dash: `_axb_o`_j''()" "lwidth" "style,0,10000,u" `"`macval(_axv)'"' ""
        }
        else {
            mata: _dash_say("err", "textangle must be between -360.000 and 360.000", "", "")
            mata: _dash_say("err", "dash: `_axb_o`_j''(): angle() must be an anglestyle or a number from -360 to 360 (got: ", st_local("_axv"), ")")
            exit 198
        }
    }
    // legend()'s direction words, refused as twoway refuses them -- here for
    // the legend() written after the graph's comma, which no segment's
    // validation sees (WP-23).  A block, not a one-line if: Stata expands a
    // one-line if's command again, macval() or not (JSE-69).
    if `: length local g_legend' {
        _dash_check_legend `"`macval(g_legend)'"'
    }

    // ---- A by() graph: its panels, as twoway answers them ----
    // Measured 24sep2026 with the console binary (graph.ado, and
    // bygraph_g.class RunGraph; test_parser.cscript P1A-83).  The panels
    // are the by() groups -- the by() variables not missing, unless
    // missing is given -- holding a row the graph's qualifier selects, or,
    // with none and one plot, that plot's if and in; with several plots
    // and no graph qualifier, every group of the data.  None is "nothing
    // to graph", r(198).  Each panel is then drawn plot by plot, and the
    // first plot that cannot be drawn in it decides:
    //   fpfit, fpfitci   its if and in select no row of the panel: "(note:
    //                    fracpoly could not fit model)", then "observation
    //                    numbers out of range", r(198) -- the command stops
    //   mspline, mband   the same, with no bands(): "bands must be between
    //                    1 and 200", r(198)
    //   lpoly, lpolyci   one observation in the panel's sample, or none: the
    //                    panel is left out, in silence
    //   lfit, lfitci     one: the panel is left out, after "(note:  regress
    //                    could not fit model)" and "insufficient
    //                    observations" (the renderer gives them)
    //   kdensity         one: the panel is left out, in silence
    // The sample counts rows whose plotted variables are not missing and
    // whose weight is above zero.  With every panel left out, "nothing to
    // graph", r(198).  The renderer leaves the same panels out
    // (_dash_by_panel_dropped) and answers every other one
    // (GlyphMapper._mark_unfit, _mark_silent).  dash drew every panel, rc
    // 0.  An immediate plot or a function reads no observations, and a
    // graph holding one is left as it was.  The qualifiers are run as
    // -syntax- read them, by value, once each.
    _dash_plottype_families
    local _by_lit 0
    forvalues k = 1/`n_segs' {
        if `: list _byq_pt_`k' in _pt_literal' local _by_lit 1
    }
    if `: length local g_by' & !`_by_lit' {
        // The by() variables and missing, read from the validated value
        // through a string scalar (_dash_by_parts).
        tempname _by_txt
        mata: st_strscalar(st_local("_by_txt"), st_local("g_by"))
        _dash_by_parts `_by_txt'
        // Every qualifier here is evaluated as twoway evaluates a by()
        // graph's: with the data sorted, stably, on the by() variables --
        // `bysort varlist (sortedby obsnum)' in bygraph_g.class -- and over
        // the whole sorted data, so `if _n == 1', `in 1/10' and `if mpg >
        // mpg[_n-1]' count rows in that order; by(, total)'s Total panel
        // evaluates them again in the data's own order (measured 24sep2026
        // from each panel's serset; test_qualifier_in_stata.cscript
        // QS-16..).  They were evaluated in the data's order alone, so on
        // data not sorted on the by() variables the panels were counted
        // over other rows than twoway draws.  _dash_qual_mark sorts, reads
        // the qualifier by value from a scalar, and gives the data their
        // order back.  Pass s is the by() order; pass t, under total alone,
        // the data's.
        local _by_passes "s"
        if `_by_total' local _by_passes "s t"
        tempname _by_sif _by_sin
        // The plots that can stop the command or leave a panel out, and
        // their rules.
        local _by_rules ""
        local _by_ks ""
        local _by_fpfam "fpfit fpfitci"
        local _by_bdfam "mspline mband"
        local _by_d0 "lpoly lpolyci"
        local _by_d1 "kdensity"
        local _by_n1 "lfit lfitci"
        forvalues k = 1/`n_segs' {
            local _pk `_byq_pt_`k''
            local _rule ""
            if `: list _pk in _by_fpfam' local _rule "R"
            if `: list _pk in _by_bdfam' & !`_byq_bd_`k'' local _rule "R"
            if `: list _pk in _by_d0' local _rule "D0"
            if `: list _pk in _by_d1' local _rule "D1"
            if `: list _pk in _by_n1' local _rule "N1"
            if "`_rule'" == "" continue
            local _by_ks `_by_ks' `k'
            local _by_rules `_by_rules' `_rule'
            local _by_seg_`: word count `_by_ks'' `k'
        }
        foreach _bp of local _by_passes {
            local _ord ""
            if "`_bp'" == "s" local _ord `_by_vars'
            // The rows the graph's qualifier selects.
            tempvar _by_gq_`_bp'
            quietly gen byte `_by_gq_`_bp'' = 0
            mata: st_strscalar(st_local("_by_sif"), st_local("_gq_if"))
            mata: st_strscalar(st_local("_by_sin"), st_local("_gq_in"))
            _dash_qual_mark `_by_gq_`_bp'' 1 `_by_sif' `_by_sin' `_ord'
            // The rows that make the panels: the graph's qualifier, or the
            // one plot's own.
            tempvar _by_base_`_bp'
            quietly gen byte `_by_base_`_bp'' = `_by_gq_`_bp''
            if `n_segs' == 1 & !`: length local _gq_if' & !`: length local _gq_in' {
                if `: length local _byq_if_1' | `: length local _byq_in_1' {
                    quietly replace `_by_base_`_bp'' = 0
                    mata: st_strscalar(st_local("_by_sif"), st_local("_byq_if_1"))
                    mata: st_strscalar(st_local("_by_sin"), st_local("_byq_in_1"))
                    _dash_qual_mark `_by_base_`_bp'' 1 `_by_sif' `_by_sin' `_ord'
                }
            }
            // Each such plot's sample.
            local _by_chk_`_bp' ""
            foreach k of local _by_ks {
                local _rule : word `: list posof "`k'" in _by_ks' of `_by_rules'
                tempvar _by_c`k'_`_bp'
                quietly gen byte `_by_c`k'_`_bp'' = 0
                mata: st_strscalar(st_local("_by_sif"), st_local("_byq_if_`k'"))
                mata: st_strscalar(st_local("_by_sin"), st_local("_byq_in_`k'"))
                _dash_qual_mark `_by_c`k'_`_bp'' `_by_gq_`_bp'' `_by_sif' `_by_sin' `_ord'
                if "`_rule'" != "R" {
                    // Rows with a plotted variable missing, or a weight
                    // missing or not above zero, are not in the sample.
                    foreach _v of local _byq_vv_`k' {
                        quietly replace `_by_c`k'_`_bp'' = 0 if missing(`_v')
                    }
                    if `: length local _byq_wv_`k'' {
                        quietly replace `_by_c`k'_`_bp'' = 0 if missing(`_byq_wv_`k'') | `_byq_wv_`k'' <= 0
                    }
                }
                local _by_chk_`_bp' `_by_chk_`_bp'' `_by_c`k'_`_bp''
            }
        }
        local _by_mopt ""
        if `_by_miss' local _by_mopt "missing"
        // by(, total): the Total panel is one more panel, answered as the
        // groups are -- `lfit mpg weight if _n==1 | _n==60, by(foreign,
        // total)' draws it alone, rc 0 (P1A-84) -- over the rows pass t
        // selects.
        if `_by_total' {
            local _by_mopt "`_by_mopt' total tpanel(`_by_base_t')"
            if `: length local _by_chk_t' local _by_mopt "`_by_mopt' tcheck(`_by_chk_t')"
        }
        local _by_copt ""
        if `: length local _by_chk_s' local _by_copt "check(`_by_chk_s') rules(`_by_rules')"
        _dash_by_panels `_by_vars', panel(`_by_base_s') `_by_mopt' `_by_copt'
        local _at_panels = max(r(kept), 1)
        if r(n) == 0 {
            display as error "nothing to graph"
            exit 198
        }
        if r(refuse) > 0 {
            local k `_by_seg_`r(refuse)''
            if `: list _byq_pt_`k' in _by_fpfam' {
                display as text "(note:  fracpoly could not fit model)"
                display as error "observation numbers out of range"
            }
            else {
                display as error "bands must be between 1 and 200"
            }
            exit 198
        }
        if r(kept) == 0 {
            // lfit and lfitci on one observation say so as they stop.
            if r(d1note) {
                display as text "(note:  regress could not fit model)"
                display as text "insufficient observations"
            }
            display as error "nothing to graph"
            exit 198
        }
    }

    // ---- saving() as typed, and its grammar (WP-30 P1.27) ----
    // The parsers' SAVing(string) drops every pair of quotes, so
    // saving("n, replace") arrived as saving(n, replace) and wrote n.html
    // with replace applied, and saving(n1, asis) wrote "n1, asis.html"
    // (measured).  The text is read again as typed from the list that gave
    // it -- the after-comma list first, else the one segment that gives it
    // (_g_unique refuses a second) -- and put to the one grammar here, so a
    // saving() twoway refuses is refused before anything is registered or
    // written, on the named route too.
    mata: st_local("_sv_typed", _dash_seg_saving("," + st_local("_gopts_axraw")))
    if !`: length local _sv_typed' {
        forvalues k = 1/`n_segs' {
            if !`: length local _sv_typed' {
                mata: st_local("_sv_typed", _dash_seg_saving(st_local("_seg_`k'")))
            }
        }
    }
    if `: length local _sv_typed' local g_saving : copy local _sv_typed
    local _sv_replace ""
    local _sv_comma ""
    if `: length local g_saving' {
        mata: _dash_saving_parse(st_local("g_saving"), "html")
    }

    // ---- Report unsupported options, once, naming every one ----
    // dash accepts every twoway option so a pasted command never aborts; an
    // option it cannot honour is named here instead of vanishing.  One note
    // per command listing all of them.
    // saving() is honoured on the immediate route only: a named graph is
    // written by `dash build, saving()'.  Measured 22sep2026: name(g3)
    // saving(x.html) registered g3, wrote nothing and said nothing.  Named
    // here rather than on a pending list, because the immediate route
    // honours it and the note must not say otherwise there.
    if `: length local g_name' & `: length local g_saving' {
        mata: st_local("_dash_ignored_acc", st_local("_dash_ignored_acc") + " saving()")
    }
    // A bare replace is refused before this, in the list's order, as
    // twoway refuses it in every position (WP-32; maintainer ruling
    // 19oct2026: the one-line form's saving(f, replace) writes over a file,
    // as twoway's does, and a bare replace beside it is refused too).
    if `: length local g_replace' {
        display as error "option replace not allowed"
        exit 198
    }
    // play() last, as twoway plays a recording once the graph is drawn
    // (WP-32): after every other refusal of the command.
    if `: length local g_play' _dash_play_check `"`macval(g_play)'"'
    if `: length local _dash_ignored_acc' {
        _dash_report_ignored `"`macval(_dash_ignored_acc)'"'
    }

    // ---- The graph's name, as it will be registered ----
    // name()'s text may end in ", replace", which tells the registry to
    // overwrite; it is not part of the name.  The stored graph carries the
    // name alone, split by the rule _dash_register_graph applies, because
    // both renderers key every item by the stored name: written as
    // "g1, replace" it matched nothing layout(), tabs(), link() or exclude()
    // named (P20-33).  _dash_register_graph is still handed name()'s own
    // text, below, and decides replace from that text alone.
    //
    // name[, replace] is letters, digits, _, blanks and a comma, and a text
    // holding anything else is no name: it is left whole, for
    // _dash_register_graph to refuse, and never put on _dash_name_split's
    // command line, where a macro in it is expanded again and an =exp
    // evaluated -- name(\`=filewrite(...)') wrote its file (measured
    // 24sep2026; test_json_escaping.cscript JSE-68).  The KPI registrar
    // reads name() the same way.
    local _g_name_text : copy local g_name
    if `: length local g_name' {
        mata: st_local("_g_name_ok", strofreal(!ustrregexm(st_local("g_name"), "[^A-Za-z0-9_, \t]")))
        if `_g_name_ok' {
            _dash_name_split `"`g_name'"' g_name _g_name_replace
        }
    }

    // ---- Assemble graph_options JSON ----
    // Build JSON from the accumulated g_* locals
    // pcycle(#) (WP-31 C8b): twoway numbers series mod(serid - 1, #) + 1
    // and draws that p#.  A value that is not a number is "option pcycle()
    // not allowed"; one that leaves a series no whole p# -- 0, -1, 1.5 on
    // three series -- "option seriesid() not allowed", r(198) for each
    // (colorvar_options_truth.json P02).  A fraction is drawn where every
    // series' number is whole (WP-31 C8d, pcycle_fraction_truth.json:
    // 1.5 on one or two series, 2.2 on three, 0.5 on any number), as
    // _dash_pcycle_bad counts the series of plots_json.  Read by value.
    if `: length local g_pcycle' {
        mata: st_local("_pcv", strofreal(strtoreal(strtrim(st_local("g_pcycle")))))
        if missing(`_pcv') {
            display as error "option pcycle() not allowed"
            exit 198
        }
        mata: st_local("_pcbad", strofreal(_dash_pcycle_bad(st_local("plots_json"), `_pcv')))
        if `_pcbad' {
            display as error "option seriesid() not allowed"
            exit 198
        }
    }
    local gopts_json "{"
    local gfirst = 1
    local _gt_textkeys title subtitle note caption xtitle ytitle xlabel ylabel ///
        legend clegend plegend by ytitle2 xtitle2 ylabel2 xlabel2 xmlabel2 ///
        ymlabel2 xmlabel ymlabel tlabel tmlabel ttitle tlabel2 ttitle2 ///
        t1title t2title b1title b2title l1title l2title r1title r2title ///
        zlabel ztitle
    local _gt_labelkeys xlabel ylabel xmlabel ymlabel tlabel tmlabel xlabel2 ///
        ylabel2 xmlabel2 ymlabel2 tlabel2 zlabel
    foreach gk in title subtitle note caption name saving xtitle ytitle xlabel ///
          ylabel xline yline legend clegend plegend pcycle by xscale yscale aspectratio scheme ///
          plotregion graphregion bgcolor plotbgcolor link filter ytitle2 ///
          xtitle2 ylabel2 xlabel2 xmlabel2 ymlabel2 xmtick2 ymtick2 yscale2 xscale2 ytick2 xtick2 yline2 xline2 ///
            xsize ysize fxsize fysize ///
          scale text ttext hover xtick ytick xmtick ymtick xmlabel ymlabel tlabel ttick tmlabel tmtick tscale ttitle tline tlabel2 ttick2 tline2 tscale2 ttitle2 t1title ///
          t2title b1title b2title l1title l2title r1title r2title ///
          zlabel ztitle zscale aspectplacement xoverhangs yoverhangs nodraw play replace table {
        // text() and ttext() are written as added_text records below
        // (WP-30 P1.10), never as their raw values.
        if inlist("`gk'", "text", "ttext") continue
        local gv : copy local g_`gk'
        // A $name or ${name} that reaches dash in a graph text option is
        // the global's value, as twoway reads the option's whole text
        // again before its quotes and sub-options (WP-31 D13b,
        // global_text_truth.json): by text through _dash_at_globals, never
        // evaluated, and refused past 4,000 characters as text() is.
        // Then {ccl name} is c(name), as twoway's graph text draws it
        // (WP-31 E9).  Both read here, by value, because the renderer
        // cannot read globals or c().
        if `: length local gv' & `: list gk in _gt_textkeys' {
            mata: st_local("_gtg", _dash_at_globals(st_local("gv"))); ///
                st_local("_gtl", strofreal(st_local("_gtg") != st_local("gv") & strlen(st_local("_gtg")) > 4000))
            if `_gtl' {
                mata: _dash_say("err", st_local("gk"), "(): expanded text is too long", "")
                exit 198
            }
            // A global holding a double quote splits a tick label's
            // string, and twoway refuses the label specifier (WP-31 D13b,
            // measured: "invalid label specifier, :  3000 "a say "hi" b":").
            if `: list gk in _gt_labelkeys' {
                mata: st_local("_gtq", _dash_gt_qadded(st_local("gv")))
                if `: length local _gtq' {
                    mata: _dash_say("err", "invalid label specifier, :  ", st_local("_gtq"), ":")
                    exit 198
                }
            }
            mata: st_local("gv", _dash_gt_ccl(st_local("_gtg")))
        }
        if `: length local gv' {
            _dash_json_str `"`macval(gv)'"' _gjv
            if !`gfirst' local gopts_json `"`gopts_json',"'
            local gopts_json `"`gopts_json'"`gk'":"`_gjv'""'
            local gfirst = 0
        }
    }
    // text() (WP-30 P1.10): each point a record, read by value and
    // refused as twoway refuses it (_dash_added_text); the count of texts
    // times by() panels first, so _dash_json_first_num finds dash's own
    // key, then the records.  Both are appended in Mata, never expanded.
    local _at_cnt 0
    local _at_all ""
    if `: length local g_text' {
        // A global holding a double quote splits a text() string, as
        // twoway reads it again before its quotes (WP-31 D13b).
        mata: st_local("_gtq", strofreal(_dash_gt_qtexts(st_local("g_text"))))
        if `_gtq' _dash_at_quote_refuse text
        _dash_added_text text "`_g_ys'" "`_g_xs'" "" "" `"`macval(g_text)'"'
        local _at_all `"`_at_json'"'
        local _at_cnt = `_at_total'
    }
    // ttext() (WP-30 P1.10): its x is a number or a date literal of the x
    // axis's time format, read as twoway reads it (get_time_format): the
    // first %t or %d among the axis's label, minor label, tick and minor
    // tick formats, each the first plot's x variable's format on that axis
    // unless its option's format() replaces it.  The literal is converted
    // by S51's gated converter (_dash_tdate_value), never run.
    if `: length local g_ttext' {
        local _at_num "lfit qfit lfitci qfitci lpoly lpolyci kdensity function scatteri pci pcarrowi"
        forvalues a = 1/2 {
            local s2 = cond(`a' == 2, "2", "")
            local _at_f ""
            local _at_seen 0
            foreach s of local _tx_list {
                tokenize "`s'", parse(":")
                if "`5'" != "`a'" | `_at_seen' continue
                local _at_seen 1
                if `: list 1 in _at_num' | "`3'" == "." continue
                capture confirm variable `3', exact
                if !_rc local _at_f : format `3'
            }
            local _at_tf ""
            foreach ts in label mlabel tick mtick {
                local _at_ff : copy local _at_f
                if !(`a' == 2 & inlist("`ts'", "mlabel", "mtick")) {
                    mata: st_local("_at_x", _dash_taxis_fmt(st_local("g_x`ts'`s2'")))
                    if `: length local _at_x' local _at_ff : copy local _at_x
                }
                mata: st_local("_at_ok", strofreal(st_local("_at_tf") == "" & ///
                    anyof(("%t", "%d"), substr(st_local("_at_ff"), 1, 2))))
                if `_at_ok' local _at_tf : copy local _at_ff
            }
            mata: st_local("_at_u`a'", _dash_taxis_unit(st_local("_at_tf"), 1))
        }
        mata: st_local("_gtq", strofreal(_dash_gt_qtexts(st_local("g_ttext"))))
        if `_gtq' _dash_at_quote_refuse ttext
        _dash_added_text ttext "`_g_ys'" "`_g_xs'" "`_at_u1'" "`_at_u2'" `"`macval(g_ttext)'"'
        if `_at_total' {
            mata: st_local("_at_all", st_local("_at_all") + (st_local("_at_all") != "" ? "," : "") + st_local("_at_json"))
            local _at_cnt = `_at_cnt' + `_at_total'
        }
    }
    if `_at_cnt' > 0 {
        _dash_limit, name(by_groups)
        local _at_cnt = `_at_cnt' * min(`_at_panels', r(value))
        _dash_added_text_cap `_at_cnt' `"`macval(g_name)'"'
        mata: st_local("gopts_json", st_local("gopts_json") + (`gfirst' ? "" : ",") + char(34) + "added_text_n" + char(34) + ":" + char(34) + "`_at_cnt'" + char(34) + "," + char(34) + "added_text" + char(34) + ":[" + st_local("_at_all") + "]")
        local gfirst = 0
    }
    // Axes 3-9 (WP-31 C10c): their title, label, tick, line and scale
    // options, as one "axisn" object; appended in Mata, never expanded.
    mata: st_local("_axn", _dash_axisn_json())
    if `: length local _axn' {
        mata: st_local("gopts_json", st_local("gopts_json") + (`gfirst' ? "" : ",") + char(34) + "axisn" + char(34) + ":" + st_local("_axn"))
        local gfirst = 0
    }
    local gopts_json `"`gopts_json'}"'

    // ---- Assemble full single-graph JSON ----
    // Promote if_expr / in_expr from the first plot segment to the graph level.
    // The renderer looks for graph-level "if_expr"/"in_expr" in graph_options or
    // at the top level.  BOTH renderers also read each plot's own qualifier and
    // apply it to that layer alone -- the saved dashboard has always done so,
    // and the served one does since WP-10 -- so the promotion below exists only
    // to give a single-segment command a graph-level qualifier as well.
    // We use _dash_json_get_str to extract the first occurrence from plots_json —
    // this correctly handles \" escape sequences inside the value.
    local if_expr ""
    local in_expr ""
    // A qualifier written after the plot groups IS the graph's: both
    // renderers apply the graph's qualifier to every layer and a layer's
    // own on top of it, as twoway does -- `(scatter y x if mpg>25)
    // (line y x) if foreign==1' draws 7 foreign cars and 22 (measured).
    // The layers keep their own; nothing is promoted over it.
    if `: length local _gq_if' | `: length local _gq_in' {
        local if_expr : copy local _gq_if
        local in_expr : copy local _gq_in
    }
    // Otherwise promote only when there is ONE segment, in which case the
    // qualifier was written on the command as a whole.  With several
    // segments each layer carries its own if_expr and the renderer applies
    // it per layer; promoting the FIRST layer's qualifier here used to apply
    // it to every layer, so
    //   dash (scatter y x) (scatter y x if foreign)
    // filtered both layers or neither.
    else if `n_segs' == 1 {
        mata: _dash_json_get_str(`"`plots_json'"', "if_expr", "if_expr")
        mata: _dash_json_get_str(`"`plots_json'"', "in_expr", "in_expr")
    }
    _dash_json_str `"`macval(if_expr)'"' _jif_top
    _dash_json_str `"`macval(in_expr)'"' _jin_top

    local graph_json `"{"plots":[`plots_json'],"graph_options":`gopts_json',"if_expr":"`_jif_top'","in_expr":"`_jin_top'"}"'

    // ---- Route: named or immediate ----
    // name()'s own text, ", replace" and all: _dash_register_graph splits
    // it by the same rule and needs the sub-option to decide whether an
    // existing name may be overwritten.  The whole command, handed over as
    // well, is stored for the record and never read for a replace.
    //
    // The three go to _dash_register_graph in string scalars, read there by
    // value.  They were three compound-quoted arguments read with -args-,
    // so a command holding "' ended the second early and the next of its
    // words became the third: after the plot groups  if make != "'x"
    // registered, rc 0, with the graph stored as the one word x and the
    // command cut at the quote (measured 24sep2026;
    // test_json_escaping.cscript JSE-45, JSE-47).  The immediate route
    // reads the graph JSON alone, which holds no apostrophe, backtick or
    // dollar sign; the command was handed to it as well, read by nothing,
    // and on its command line an =exp in it was evaluated (JSE-67).
    local graph_name : copy local _g_name_text

    if `: length local graph_name' {
        tempname _rg_name _rg_json _rg_spec
        mata: st_strscalar(st_local("_rg_name"), st_local("graph_name"))
        mata: st_strscalar(st_local("_rg_json"), st_local("graph_json"))
        mata: st_strscalar(st_local("_rg_spec"), st_local("0"))
        _dash_register_graph `_rg_name' `_rg_json' `_rg_spec' `_fp_sc'
    }
    else {
        _dash_render_immediate `"`graph_json'"' `_fp_sc'
    }
end

// ================================================================
// _dash_taxis_fold <type:variable:axis> ...  -- tlabel(), ttick(),
// tmlabel(), tmtick(), ttitle(), tscale() and tline() onto the x axes, as
// twoway reads them (WP-30 P1.6)
//
// Called by _dash_plot after the axis check, with each plot segment's
// type, the variable its x axis takes its format from ("." for none) and
// its x axis; the graph's x and t values come in the globals
// dash__tf_<key> (and its name and ignored options in dash__tf_name and
// dash__tf_ign) and go back the same way, so no value is ever put on a
// command line.  Measured on StataNow 19.5 (test/fixtures/
// taxis_truth.json, scripts/extract_taxis_truth.do):
//   * tm() and ts() are no option of twoway's: "option tm() not allowed",
//     r(198) (ab_tm, ab_ts);
//   * an x option reads no date literal: xlabel(2000m1) is "invalid label
//     specifier, :  2000m1:", r(198), xscale(range(1999m1)) r(121) (c11,
//     c13, xl1-xsc2; xline() is refused by _dash_line_check already, c12);
//     nor does a y option, ylabel(2000m1) and yscale(range(2000m1)) alike
//     (WP-31 A8, weight_operator_truth.json ydates.*);
//   * the unit is the first plot's x variable's label format, and none
//     (numbers only) after lfit, qfit, lfitci, qfitci, lpoly, lpolyci,
//     kdensity, function, scatteri, pci or pcarrowi (m6_*), x1's for the pc
//     types (pc1, pc2), an operated x's variable's (op1-op3);
//   * each t-option is read after every x option, scale, label, mlabel,
//     tick, mtick, title, line, and merges into its x twin as a second copy
//     of it would (c14, c15, c34-c36, c46, c48);
//   * a tline() list goes through numlist, whose cap gives twoway's r(123)
//     "invalid numlist has too many elements" (m8);
//   * axis(2) puts them on the second x axis, read in its own unit (f07,
//     f08); _dash_route_axis2 writes those copies as tlabel2() .. ttitle2(),
//     and _dash_axreq_check refuses an axis no layer uses, X then T then Y
//     (f09, f10, f12, f13);
//   * a format() decides the unit as twoway's ticksets do (k01-k07), and a
//     %-t format reads dates in labels and ticks only (g01-g04).
// The converter is Mata's (_dash_taxis_unit, _dash_taxis_fmt,
// _dash_tdate_ticks, _dash_tdate_lines, _dash_tdate_range,
// _dash_xdate_find): a date token is read by Mata's string date functions
// only, and the one command line built here is numlist over the numbers
// it wrote (_tf_nl).  The units read are kept in dash__tunit for
// _dash_register_graph, and dash build notes a later change of a
// variable's date format.
// ================================================================
program define _dash_taxis_fold
    version 19
    local _tf_segs `0'

    // tm() and ts(), before anything is read.
    mata: st_local("_tf_ign", st_global("dash__tf_ign"))
    if `: length local _tf_ign' {
        mata: _dash_option_names("_tf_ign", "_tf_names")
        foreach tok of local _tf_names {
            mata: st_local("tok", strtrim(st_local("tok")))
            mata: st_local("tok", strtrim(substr(st_local("tok"), 1, ///
                (strpos(st_local("tok"), "(") ? strpos(st_local("tok"), "(") - 1 : .))))
            mata: st_local("_tf_x", strofreal(anyof(("tm", "ts"), st_local("tok"))))
            if `_tf_x' {
                display as error "option `tok'() not allowed"
                exit 198
            }
        }
    }

    // A date literal in an x option.
    foreach c in xlabel:1 xtick:1 xmlabel:1 xmtick:1 xlabel2:1 xtick2:1 xscale:3 xscale2:3 {
        gettoken k f : c, parse(":")
        local f = substr("`f'", 2, .)
        mata: st_local("_tf_hit", strofreal(_dash_xdate_find(st_global("dash__tf_`k'"), `f')))
        if `_tf_hit' {
            if `f' == 3 {
                display as error "range() invalid -- invalid numlist"
                exit 121
            }
            mata: _dash_say("err", "invalid label specifier, :  ", st_local("_xd_tok"), ":")
            exit 198
        }
    }

    // A date literal in a y option (WP-31 A8): twoway refuses it as it
    // refuses the x form, in the same words and codes, on a %t-formatted
    // y variable too (test/fixtures/weight_operator_truth.json ydates.*:
    // ylabel(2000m1) "invalid label specifier, :  2000m1:", r(198);
    // yscale(range(2000m1)) "range() invalid -- invalid numlist", r(121)).
    // yline() is _dash_line_check's.
    foreach c in ylabel:1 ytick:1 ymlabel:1 ymtick:1 ylabel2:1 ytick2:1 yscale:3 yscale2:3 {
        gettoken k f : c, parse(":")
        local f = substr("`f'", 2, .)
        mata: st_local("_tf_hit", strofreal(_dash_xdate_find(st_global("dash__tf_`k'"), `f')))
        if `_tf_hit' {
            if `f' == 3 {
                display as error "range() invalid -- invalid numlist"
                exit 121
            }
            mata: _dash_say("err", "invalid label specifier, :  ", st_local("_xd_tok"), ":")
            exit 198
        }
    }

    // Each x axis in turn (WP-30 P1.6 part 2): its base format, the first
    // plot's on it; the four tickset formats -- major (xlabel), minor
    // (xmlabel), major ticks (xtick), minor ticks (xmtick) -- each the
    // base until the last format() of its merged x option replaces it
    // (k01, k02, k07); then each family in twoway's order, the label and
    // tick families read in their own tickset's format, which their own
    // format() replaces only after their positions (k03, k04), and the
    // scale and lines in the first of the four that is a %t or %d format
    // (axis.class get_time_format; k05, %-tm g02-g04).  Axis 2 has its own
    // base and takes tlabel2() .. ttitle2(), axis(2)'s routed forms.
    local _tf_num "lfit qfit lfitci qfitci lpoly lpolyci kdensity function scatteri pci pcarrowi"
    local _tf_unit ""
    // WP-31 C10e: axes 3-9 (and axis 2's tmlabel()/tmtick(), which no
    // dash key holds) come from the graph's axisn record as globals
    // dash__tf_<x|t><family>_<n>, are folded as axes 1 and 2 are, and go
    // back as its x rows (_dash_axisn_tf_out, _dash_axisn_tf_in).
    mata: _dash_axisn_tf_out()
    forvalues a = 1/9 {
        local s2 = cond(`a' == 1, "", cond(`a' == 2, "2", "_`a'"))
        if `a' >= 3 {
            // An axis no layer and no option names is skipped.
            local _tf_any 0
            foreach s of local _tf_segs {
                tokenize "`s'", parse(":")
                if "`5'" == "`a'" local _tf_any 1
            }
            if !`_tf_any' continue
        }
        local _tf_fmt ""
        local _tf_var ""
        local _tf_seen 0
        foreach s of local _tf_segs {
            tokenize "`s'", parse(":")
            if "`5'" != "`a'" | `_tf_seen' continue
            local _tf_seen 1
            if `: list 1 in _tf_num' | "`3'" == "." continue
            capture confirm variable `3', exact
            if _rc continue
            local _tf_fmt : format `3'
            local _tf_var `3'
        }
        foreach ts in label mlabel tick mtick {
            local _tf_f_`ts' : copy local _tf_fmt
            mata: st_local("_tf_x", _dash_taxis_fmt(st_global("dash__tf_x`ts'`s2'")))
            if `: length local _tf_x' local _tf_f_`ts' : copy local _tf_x
        }
        local _tf_used 0
        local _tf_fams "scale label mlabel tick mtick title line"
        foreach fam of local _tf_fams {
            mata: st_local("_td_in", st_global("dash__tf_t`fam'`s2'"))
            if !`: length local _td_in' continue
            // get_time_format: the first time format of the four.
            local _tf_tf ""
            foreach ts in label mlabel tick mtick {
                mata: st_local("_tf_ok", strofreal(st_local("_tf_tf") == "" & ///
                    anyof(("%t", "%d"), substr(st_local("_tf_f_`ts'"), 1, 2))))
                if `_tf_ok' local _tf_tf : copy local _tf_f_`ts'
            }
            mata: st_local("_tf_u2", _dash_taxis_unit(st_local("_tf_tf"), 2))
            local _td_rc 0
            if "`fam'" == "title" local _td_out : copy local _td_in
            else if "`fam'" == "scale" {
                mata: _dash_tdate_range(st_local("_tf_u2"))
                local _tf_used 1
            }
            else if "`fam'" == "line" {
                mata: _dash_tdate_lines(st_local("_tf_u2"))
                if !`_td_rc' {
                    local _td_out ""
                    local _tf_sep ""
                    forvalues i = 1/`_td_n' {
                        if "`_td_k`i''" == "1" {
                            local _tf_nl : copy local _td_s`i'
                            if `: length local _tf_nl' {
                                capture noisily numlist "`_tf_nl'", max(2500)
                                if _rc exit _rc
                                local _tf_out `r(numlist)'
                                local _tf_out : list uniq _tf_out
                            }
                            else local _tf_out ""
                            local _td_out `"`macval(_td_out)'`_tf_sep'`_tf_out'"'
                        }
                        else local _td_out `"`macval(_td_out)'`_tf_sep'`macval(_td_s`i')'"'
                        local _tf_sep ", "
                    }
                }
                local _tf_used 1
            }
            else {
                mata: st_local("_tf_u1", _dash_taxis_unit(st_local("_tf_f_`fam'"), 1))
                mata: _dash_tdate_ticks("t`fam'", st_local("_tf_u1"))
                mata: st_local("_tf_x", _dash_taxis_fmt(st_local("_td_in")))
                if `: length local _tf_x' local _tf_f_`fam' : copy local _tf_x
                local _tf_used 1
            }
            if `_td_rc' {
                mata: _dash_say("err", "", st_local("_td_msg"), "")
                exit `_td_rc'
            }
            mata: st_local("_tf_x", st_global("dash__tf_x`fam'`s2'"))
            mata: _dash_rep_merge_locals("x`fam'`s2'", "_tf_x", "_td_out", "_tf_x")
            mata: st_global("dash__tf_x`fam'`s2'", st_local("_tf_x"))
            global dash__tf_t`fam'`s2' ""
        }
        // The unit this axis's variable gave the dates, for the registry.
        mata: st_local("_tf_u1", _dash_taxis_unit(st_local("_tf_fmt"), 1))
        if `_tf_used' & "`_tf_var'" != "" & "`_tf_u1'" != "" {
            local _tf_unit `_tf_unit' `a':`_tf_var':`_tf_u1'
        }
    }
    mata: _dash_axisn_tf_in()
    if "`_tf_unit'" != "" global dash__tunit "`: list retokenize _tf_unit'"
end

// ----------------------------------------------------------------
// _dash_line_check <row> <text>  -- one xline()/yline() copy's positions
// through Stata's own numlist (WP-30 P1.21a)
//
// twoway's _gs_parse_and_log_lines (1.1.6) reads a line's positions with
// numlist and refuses any failure as "invalid line argument, <text>",
// r(198) (its 2,500 cap included: xline(1(1)2501)).  _dash_axreq_check
// hands the text back only after _dash_so_unsafe passed, and it is only
// ever expanded inside macval(); on success the row is marked read.
// ----------------------------------------------------------------
program define _dash_line_check
    version 19
    args row t
    capture numlist `"`macval(t)'"'
    if _rc {
        mata: _dash_axreq_clear()
        mata: _dash_say("err", "invalid line argument, ", st_local("t"), "")
        exit 198
    }
    mata: _dash_axreq_accept_line(`row')
end

// ----------------------------------------------------------------
// _dash_table_fold "<flag>" "<text>"  -- table's two declarations as one
// value (WP-31 H2t)
//
// -syntax- cannot declare one option both bare and with parentheses, so
// both parsers declare TABLE, the bare word, and TABLE2(string asis), the
// argument form (measured 17oct2026: table sets the flag, table(rows(5))
// the text, table() neither).  Written in full, as dash's own option: a
// shorter spelling would be shared by the two declarations.  The caller's
// local _tb_val is "on" for the bare word, else the text typed; both
// together are refused, r(198).  The text is read by value.
// ----------------------------------------------------------------
program define _dash_table_fold
    version 19
    args flag t
    if "`flag'" != "" & `"`macval(t)'"' != "" {
        display as error "dash: table may not be combined with table()"
        exit 198
    }
    if "`flag'" != "" c_local _tb_val on
    else c_local _tb_val `"`macval(t)'"'
end

// ----------------------------------------------------------------
// _dash_table_check <text>  -- table()'s sub-options (WP-31 H2t)
//
// table is dash's own (twoway has no data table): "on" (the bare word) or
// table(rows(#) open), rows(#) a whole number from 1 to 100,000 -- the
// rows the table lists at most -- and open the table unfolded.  Any other
// word is refused, r(198), echoed by value and cut to 40 characters.  The
// tokens are read with _dash_opt_tokens, by value, never by -syntax-.
// ----------------------------------------------------------------
program define _dash_table_check
    version 19
    args t
    mata: st_local("_tb_t", strtrim(st_local("t")))
    if `"`macval(_tb_t)'"' == "on" exit
    mata: _dash_tb_tok = _dash_opt_tokens(st_local("_tb_t"))
    mata: st_local("_tb_n", strofreal(cols(_dash_tb_tok)))
    forvalues _ti = 1/`_tb_n' {
        mata: st_local("_tb_w", _dash_tb_tok[`_ti'])
        if `"`macval(_tb_w)'"' == "open" continue
        mata: st_local("_tb_r", strofreal(regexm(st_local("_tb_w"), "^rows[(](.*)[)]$")))
        if `_tb_r' {
            mata: st_local("_tb_v", strtrim(regexs(1)))
            mata: st_local("_tb_ok", strofreal(strlen(st_local("_tb_v")) >= 1 & strlen(st_local("_tb_v")) <= 6 & !strlen(subinstr(subinstr(subinstr(subinstr(subinstr(subinstr(subinstr(subinstr(subinstr(subinstr(st_local("_tb_v"), "0", ""), "1", ""), "2", ""), "3", ""), "4", ""), "5", ""), "6", ""), "7", ""), "8", ""), "9", ""))))
            if `_tb_ok' {
                if `_tb_v' >= 1 & `_tb_v' <= 100000 continue
            }
            mata: _dash_say("err", "dash: table(rows()) takes an integer from 1 to 100,000; got '", (ustrlen(st_local("_tb_v")) <= 40 ? st_local("_tb_v") : usubstr(st_local("_tb_v"), 1, 40) + "..."), "'")
            mata: mata drop _dash_tb_tok
            exit 198
        }
        mata: _dash_say("err", "dash: table() takes rows(#) and open; '", (ustrlen(st_local("_tb_w")) <= 40 ? st_local("_tb_w") : usubstr(st_local("_tb_w"), 1, 40) + "..."), "' is not one of them")
        mata: mata drop _dash_tb_tok
        exit 198
    }
    mata: mata drop _dash_tb_tok
end

// ----------------------------------------------------------------
// _dash_line_expand <local> <value>  -- each copy's positions as numlist
// expands them, each value once (WP-30 P1.21a)
//
// value is one option's copies joined ", " (_dash_rep_merge); the result
// is written to the caller's local.  A top-level-comma segment whose first non-blank byte
// is a digit, +, -, . or ( starts a copy: it is replaced by its positions
// as numlist writes them, duplicates dropped (twoway's list uniq); other
// segments are kept as typed.  Every copy was already accepted by
// _dash_line_check, so this never refuses.
// ----------------------------------------------------------------
program define _dash_line_expand
    version 19
    args L v
    if `"`macval(v)'"' == "" exit
    local rest : copy local v
    local out ""
    local sep ""
    local any 0
    while `"`macval(rest)'"' != "" {
        mata: _dash_comma_pos(st_local("rest"), "cpos")
        if `cpos' {
            mata: st_local("seg", substr(st_local("rest"), 1, `cpos' - 1))
            mata: st_local("rest", substr(st_local("rest"), `cpos' + 1, .))
        }
        else {
            local seg : copy local rest
            local rest ""
        }
        mata: st_local("seg", strtrim(st_local("seg")))
        mata: st_local("_lx_c", strofreal(strpos("0123456789+-.(", substr(st_local("seg"), 1, 1)) > 0 & st_local("seg") != ""))
        if `_lx_c' {
            numlist `"`macval(seg)'"'
            local nl `r(numlist)'
            local nl : list uniq nl
            local seg `nl'
            local any 1
        }
        local out `"`macval(out)'`sep'`macval(seg)'"'
        local sep ", "
    }
    if `any' c_local `L' `"`macval(out)'"'
end

// ----------------------------------------------------------------
// _dash_reflines_of <gjson>  -- r(n): one graph's reference-line
// positions times its by() panels (WP-30 P1.21a)
//
// Positions are counted in the JSON, already expanded
// (_dash_reflines_positions); the panels over every observation
// (_dash_refline_panels), an upper bound of what is drawn.
// ----------------------------------------------------------------
program define _dash_reflines_of, rclass
    version 19
    args gjson
    mata: st_local("_rl_p", strofreal(_dash_reflines_positions(st_local("gjson"))))
    local _rl_k 1
    if `_rl_p' > 0 {
        mata: _dash_json_get_str(st_local("gjson"), "by", "_rl_by")
        if `"`macval(_rl_by)'"' != "" {
            _dash_refline_panels `"`macval(_rl_by)'"'
            local _rl_k = max(r(n), 1)
        }
    }
    return scalar n = `_rl_p' * `_rl_k'
end

// ----------------------------------------------------------------
// _dash_refline_panels <by>  -- r(n): the panels a by() value asks for,
// counted over every observation (WP-30 P1.21a)
//
// The groups of the by() variables (missing keeps a group holding a
// missing value), one more for total, capped at the by_groups limit.
// The names were validated when the spec was built; the value is read
// through _dash_by_parts from a string scalar.
// ----------------------------------------------------------------
program define _dash_refline_panels, rclass
    version 19
    args by
    tempname V
    mata: st_strscalar(st_local("V"), st_local("by"))
    _dash_by_parts `V'
    tempvar tag one
    local n 0
    capture confirm variable `_by_vars'
    if !_rc {
        quietly gen byte `one' = 1
        if !`_by_miss' markout `one' `_by_vars', strok
        quietly egen byte `tag' = tag(`_by_vars') if `one'
        quietly count if `tag' == 1
        local n = r(N) + `_by_total'
    }
    _dash_limit, name(by_groups)
    return scalar n = min(`n', r(value))
end

// ----------------------------------------------------------------
// _dash_reflines_cap <n>  -- refuse r(134) a dashboard whose reference
// lines pass the reflines limit (WP-30 P1.21a, A68)
// ----------------------------------------------------------------
program define _dash_reflines_cap
    version 19
    args n
    _dash_limit, name(reflines)
    local lim = r(value)
    local ceil = r(ceiling)
    if `n' <= `lim' exit
    _dash_count_fmt _n_s `n'
    _dash_count_fmt _lim_s `lim'
    _dash_count_fmt _ceil_s `ceil'
    display as error "dash: this dashboard asks for up to `_n_s' reference lines (positions times by() panels), more than the `_lim_s' one dashboard draws."
    display as error "      Draw fewer lines, or set global dash_max_reflines to a higher value (at most `_ceil_s')."
    exit 134
end


// ----------------------------------------------------------------
// _dash_at_opts "<ys>" "<xs>" <state> `"<options>"'  -- one text() or
// ttext() copy's sub-options, read as twoway reads them (WP-30 P1.10)
//
// twoway's _parse_log_1textbox (twowaygraph_g.class) reads AXes()
// YAXis() XAXis() TSTYle() first and refuses an axis pair no plot region
// has -- even for a copy with no point -- then, for a copy with a point,
// hands the rest to the textbox chain (_fr_sztextbox_parse_and_log,
// _fr_textbox_parse_and_log, _fr_tbstyle_parse_and_log), each level
// passing its unknown words on and the last refusing them: one syntax
// statement holding every level's options, with no catch-all, accepts and
// refuses what the chain does.  <ys> and <xs> are the axes the graph's
// layers use (dash's own digits); <state> is _dash_at_parse's for the
// copy (0 no point, 1 valid, 2 its first point invalid: stop after the
// axis pair, 3 a later one).  The options are read by value
// (_dash_text_args) and reach syntax only through st_local("0"), never
// a command line.  Returns by c_local only digits, option names and
// _dash_json_escape() output: _ao_y, _ao_x (the axis pair), _ao_canon (the
// drawn sub-options, _dash_at_canon), _ao_noted (the names given that
// dash does not draw).  An unknown placement() or orientation() is noted
// here in twoway's words, so the name never crosses a program boundary.
// ----------------------------------------------------------------
program define _dash_at_opts
    version 19
    mata: _dash_text_args(3, 0, 0)
    local _ys `_dash_a1'
    local _xs `_dash_a2'
    local _st `_dash_a3'
    mata: st_local("0", ", " + st_local("_dash_txt"))
    syntax [, AXes(string) YAXis(integer 1) XAXis(integer 1) TSTYle(string) *]
    local _ay `yaxis'
    local _ax `xaxis'
    if `: length local axes' {
        mata: st_local("_aw", strofreal(cols(tokens(st_local("axes")))))
        if `_aw' != 2 {
            mata: _dash_say("err", "invalid axes(", st_local("axes"), ")")
            exit 198
        }
        mata: st_local("_ay", tokens(st_local("axes"))[1]); st_local("_ax", tokens(st_local("axes"))[2])
        mata: st_local("_ay", st_local("_ay") == "." ? "1" : st_local("_ay")); st_local("_ax", st_local("_ax") == "." ? "1" : st_local("_ax"))
    }
    mata: st_local("_okp", strofreal(anyof(tokens(st_local("_ys")), st_local("_ay")) & anyof(tokens(st_local("_xs")), st_local("_ax"))))
    if !`_okp' {
        mata: _dash_say("err", "text() option invalid, specified axis pair (", st_local("_ay") + " " + st_local("_ax"), ") not in graph")
        exit 198
    }
    c_local _ao_y `_ay'
    c_local _ao_x `_ax'
    c_local _ao_canon ""
    c_local _ao_noted ""
    if inlist(`_st', 0, 2) exit
    mata: st_local("0", ", " + st_local("options"))
    syntax [, WIDTH(string) HEIGHT(string) NOASTextbox NOBEXpand ///
        ASTextbox BEXpand ORIENTation(string) DRAWVIEW(string) ///
        XOFFSET(real -99999) YOFFSET(real -99999) ASCIRCLE ANGLE(string) ///
        Size(string) Color(string) Justification(string) ///
        Alignment(string) Margin(string) LINEGAP(string) NOBox Box ///
        BMargin(string) PLACEment(string) BFColor(string) FColor(string) ///
        BColor(string) BLSTyle(string) BLWidth(string) BLColor(string) ///
        BLPattern(string) BLAlign(string) LSTyle(string) LWidth(string) ///
        LColor(string) LPattern(string) LAlign(string)]
    if `: length local placement' {
        mata: st_local("_pl", _dash_at_place(st_local("placement")))
        if "`_pl'" == "" {
            mata: _dash_note("named style ", st_local("placement"), " not found in class compass2dir, default attributes used")
        }
    }
    if `: length local orientation' {
        mata: st_local("_or", _dash_at_orient(st_local("orientation")))
        if "`_or'" == "" {
            mata: _dash_note("named style ", st_local("orientation"), " not found in class tb_orientstyle, default attributes used")
        }
    }
    local _nt ""
    foreach _n in width height astextbox noastextbox bexpand nobexpand ///
        drawview ascircle angle alignment linegap bmargin lpattern ///
        lstyle lalign blpattern blstyle blalign {
        if `: length local `_n'' local _nt `_nt' `_n'
    }
    if `xoffset' != -99999 local _nt `_nt' xoffset
    if `yoffset' != -99999 local _nt `_nt' yoffset
    mata: st_local("_cn", _dash_at_canon())
    c_local _ao_canon `"`_cn'"'
    c_local _ao_noted `_nt'
end

// ----------------------------------------------------------------
// _dash_added_text <kind> "<ys>" "<xs>" "<u1>" "<u2>" `"<copies>"'  -- a
// graph's text() or ttext() copies as added_text records (WP-30 P1.10)
//
// <kind> is text or ttext; <ys> and <xs> the axes the graph's layers use;
// <u1> and <u2> the date units of x axes 1 and 2 (ttext(); "" for none,
// _dash_taxis_unit), its literals converted by _dash_at_dates and refused
// "<x> is not a number" as twoway refuses one the axis cannot read;
// <copies> the option's value, its copies joined by char(30)
// (_dash_rep_merge), read by value (_dash_text_args).  Mata reads every
// copy's points and lines (_dash_at_parse); each copy's sub-options are
// read as twoway reads them (_dash_at_opts), and the command is refused
// r(198) in twoway's words on a malformed point, a missing axis pair or a
// sub-option twoway does not take.  The sub-options dash does not draw are
// named once in a note.  Returns by c_local _at_json, the records joined
// by commas (_dash_at_json; JSON-escaped, safe inside compound quotes),
// and _at_total, their number.
// ----------------------------------------------------------------
program define _dash_at_quote_refuse
    // _dash_at_quote_refuse text|ttext: the points and lines in the global
    // dash__q (_dash_gt_qtexts: a copy whose globals added a double
    // quote) read as twoway's _parse_log_1textbox reads them --
    // gettoken by gettoken, numbers by _dash_at_isnum, a ttext() x any
    // unquoted word -- refused in its words, "invalid point, x y",
    // r(198), at the first point that is not one (WP-31 D13b, measured:
    // "invalid point,  hi" b"").  Read by value; nothing is run.  When
    // every point reads, dash goes on as before.
    version 19
    args kind
    mata: st_local("rest", st_global("dash__q")); st_global("dash__q", "")
    gettoken y rest : rest
    gettoken x rest : rest
    while `"`macval(y)'"' != "" {
        mata: st_local("ok", strofreal(_dash_at_isnum(st_local("y")) & ///
            (_dash_at_isnum(st_local("x")) | (st_local("kind") == "ttext" & ///
            st_local("x") != "" & !strpos(st_local("x"), char(34))))))
        if !`ok' {
            mata: _dash_say("err", "invalid point, ", st_local("x") + " " + st_local("y"), "")
            exit 198
        }
        gettoken txtq rest : rest, quotes
        gettoken txt : txtq
        while `"`macval(txtq)'"' != "" & `"`macval(txtq)'"' != `"`macval(txt)'"' {
            gettoken txtq rest : rest, quotes
            gettoken txt : txtq
        }
        local y : copy local txt
        gettoken x rest : rest
    }
end

program define _dash_added_text
    version 19
    mata: _dash_text_args(5, 0, 0)
    local _kind `_dash_a1'
    local _ys `_dash_a2'
    local _xs `_dash_a3'
    local _u1 `_dash_a4'
    local _u2 `_dash_a5'
    mata: st_local("_at_rc", strofreal(_dash_at_parse(st_local("_dash_txt"), st_local("_kind") == "ttext")))
    if `_at_rc' {
        mata: _dash_say("err", st_local("_kind"), "(): expanded text is too long", "")
        exit 198
    }
    local _noted ""
    forvalues k = 1/`_at_k' {
        mata: _dash_at_copy(`k')
        _dash_at_opts "`_ys'" "`_xs'" `_at_s' `"`macval(_at_o)'"'
        if inlist(`_at_s', 2, 3) {
            mata: _dash_say("err", "", st_local("_at_e"), "")
            exit 198
        }
        local _at_ya`k' `_ao_y'
        local _at_xa`k' `_ao_x'
        local _at_cn`k' `"`_ao_canon'"'
        local _noted : list _noted | _ao_noted
    }
    if "`_noted'" != "" {
        local _nl ""
        foreach _n of local _noted {
            local _nl "`_nl' `_n'()"
        }
        mata: _dash_note("dash: `_kind'() draws no", st_local("_nl"), "; see help dash##added_text")
    }
    // ttext()'s date literals, in the unit of each record's x axis.
    if "`_kind'" == "ttext" {
        mata: st_local("_at_rc", strofreal(_dash_at_dates(st_local("_u1"), st_local("_u2"))))
        if `_at_rc' {
            mata: _dash_say("err", "", st_local("_at_err"), " is not a number")
            exit 198
        }
    }
    mata: _dash_at_records(st_local("_kind"))
    c_local _at_json `"`_at_json'"'
    c_local _at_total `_at_n'
end

// ----------------------------------------------------------------
// _dash_added_text_cap <n> ["<graph>"]  -- refuse r(134) a graph, or with
// no name a dashboard, whose added texts (text() and ttext() points times
// by() panels) pass the added_text limit (WP-30 P1.10, A28)
// ----------------------------------------------------------------
program define _dash_added_text_cap
    version 19
    mata: _dash_text_args(1, 0, 0)
    local n `_dash_a1'
    _dash_limit, name(added_text)
    local lim = r(value)
    local ceil = r(ceiling)
    if `n' <= `lim' exit
    _dash_count_fmt _n_s `n'
    _dash_count_fmt _lim_s `lim'
    _dash_count_fmt _ceil_s `ceil'
    if `: length local _dash_txt' {
        mata: _dash_say("err", "dash: graph '", st_local("_dash_txt"), "' draws `_n_s' added texts (text() and ttext() points times by() panels), more than the `_lim_s' dash draws.")
    }
    else {
        display as error "dash: this dashboard draws `_n_s' added texts (text() and ttext() points times by() panels), more than the `_lim_s' dash draws."
    }
    display as error "      Set global dash_max_added_text to draw more (at most `_ceil_s')."
    exit 134
end


// ================================================================
// _dash_display_on given mode graphics seam  -- may dash open a window?
//
// twoway builds its graph and displays nothing in batch (c(mode) batch)
// and after `set graphics off' (measured, StataNow 19.5), so dash opens no
// window there (WP-30 P1.27, A88); interactive Stata, the console
// included, opens one (A89).  A pure function of its arguments, which are
// compared by value in Mata: given is a display() option, "", on or off
// (anything else r(198)), and decides when given; else seam, the value of
// an undocumented test global, decides when it is exactly on or off; else
// r(on) is 0 in batch or with graphics off, 1 otherwise.
// ================================================================
program define _dash_display_on, rclass
    version 19
    args given mode graphics seam
    mata: st_local("_do_g", st_local("given"))
    mata: st_local("_do_ok", strofreal(anyof(("", "on", "off"), st_local("given"))))
    if "`_do_ok'" != "1" {
        display as error "dash: display() is on or off."
        exit 198
    }
    mata: st_local("_do_on", ///
        st_local("given") != "" ? strofreal(st_local("given") == "on") : ///
        (anyof(("on", "off"), st_local("seam")) ? strofreal(st_local("seam") == "on") : ///
        strofreal(!(st_local("mode") == "batch" | st_local("graphics") == "off"))))
    return scalar on = `_do_on'
end

// ================================================================
// _dash_browser_wanted  — should this render open a browser window?
//
// r(open) is 1 only when no saving() was given, $dash_nobrowser is empty,
// the spec does not carry Stata's own nodraw, and _dash_display_on allows a
// window (not batch, graphics not off; WP-30 P1.27).  nodraw means "build it
// but do not display it", and opening a window is displaying it; it is a
// flag, so its serialised value is the word itself, and an unset flag
// serialises as an empty string, which must NOT suppress.
// ================================================================
program define _dash_browser_wanted, rclass
    version 19
    syntax , SPEC(string asis) [SAVing(string) DISPlay(string)]
    local open = 1
    if `"`saving'"' != "" local open = 0
    if "${dash_nobrowser}" != "" local open = 0
    if strpos(`"`spec'"', `""nodraw":"nodraw""') > 0 local open = 0
    // No window in batch or with graphics off (WP-30 P1.27): _dash_display_on.
    mata: st_local("_bw_seam", st_global("dash__display"))
    _dash_display_on `"`display'"' "`c(mode)'" "`c(graphics)'" `"`macval(_bw_seam)'"'
    if r(on) == 0 local open = 0
    return scalar open = `open'
end

// ================================================================
// _dash_registry_nodraw  — does any registered graph carry nodraw?
//
// dash.sthlp says a graph's nodraw keeps the browser shut on `dash build'
// as nobrowser does; measured 22sep2026 it did not -- the registry's
// graph_options were never read for it.  r(nodraw) is 1 when one is.
// ================================================================
program define _dash_registry_nodraw, rclass
    version 19
    local hit = 0
    foreach _rn in ${dash_graph_registry} {
        if strpos(`"${dash_json_`_rn'}"', `""nodraw":"nodraw""') > 0 local hit = 1
    }
    return scalar nodraw = `hit'
end

// ================================================================
// _dash_dashboard_browser [, nobrowser]  — does a dashboard of the whole
// registry open a browser window?
//
// The one rule `dash build' and `dash serve' decide by.  r(open) is 1
// unless the command's own nobrowser option was given, $dash_nobrowser is
// set (an empty global is an unset one), a registered graph carries
// Stata's nodraw, or _dash_display_on refuses a window (batch, or graphics
// off; WP-30 P1.27).  r(flag) is what `dash serve' hands the launcher:
// "--no-browser" when r(open) is 0, else empty.
//
// `dash serve' used to decide from its nobrowser option alone, so the
// global dash.sthlp says "suppresses the window for a whole session" did
// not: `global dash_nobrowser 1' then `dash serve, port(5006)' launched
// the app without --no-browser, and dash_render.py's launcher added --show
// and opened a window.  A registered graph's nodraw, which kept `dash
// build' shut, did not keep `dash serve' shut either.
// ================================================================
program define _dash_dashboard_browser, rclass
    version 19
    syntax [, NOBRowser DISPlay(string)]
    _dash_registry_nodraw
    // r(nodraw) is copied before _dash_display_on, an rclass call, runs.
    local _db_nd = r(nodraw)
    // No window in batch or with graphics off (WP-30 P1.27): _dash_display_on.
    mata: st_local("_db_seam", st_global("dash__display"))
    _dash_display_on `"`display'"' "`c(mode)'" "`c(graphics)'" `"`macval(_db_seam)'"'
    local open = ("`nobrowser'" == "" & "${dash_nobrowser}" == "" ///
                  & `_db_nd' == 0 & r(on) == 1)
    return scalar open = `open'
    if `open' return local flag ""
    else      return local flag "--no-browser"
end

// ================================================================
// _dash_open_page , path(string) [os(string) dryrun]  -- open a saved page
// in the system's browser: the one opener the one-line form and `dash
// build' share, once their decider has said a window is wanted.
//
// r(cmd) is the shell command: open '<path>' on a Mac, xdg-open '<path>'
// on Unix, start "" "<path>" on Windows, where start reads its first
// quoted argument as a window title.  r(os) is the platform it is for,
// os() or, when that is omitted, this machine's.  r(opened) is 1 when the
// command went to the shell.  dryrun builds and returns the command and
// runs nothing, and so does a set $dash_nobrowser, whichever caller asks.
// r(why) is "metachar" when a Windows path holds a character cmd.exe would
// read, so no command was built and the path was printed instead.
// r(rc) is the opener's exit status (WP-31 H4): 0 when nothing ran, and
// when it is not 0 the path is printed for the user to open.
//
// The two callers each carried their own three shell lines, and the
// Windows line ran only where Stata reports Windows, so no test ran it;
// the checks read dash.ado's text and passed with that branch unable to
// run at all.  With the platform an argument and dryrun, each platform's
// command is checked on any machine (test_serve_browser.cscript SB-13..20).
//
// The path is quoted for the shell that reads it, and built and run by
// value: in Mata, then through _stata() with macro expansion off, since a
// `$' or a backquote in the text `shell' is given is expanded again first
// (measured 24sep2026: shell `c' ran a single-quoted /tmp/q$PROBEGz.html
// as /tmp/q.html).  bash, which Stata's shell runs on a Mac and Unix, takes
// everything inside single quotes as written but the apostrophe itself,
// which is written '\''.  cmd.exe takes & ; and spaces inside double
// quotes as written, but a double quote there would end the argument; no
// Windows file name can hold one, so such a path is refused.  So is a line
// break, which would end the command, and a platform other than the three
// Stata reports.  The callers pass paths _dash_validate_path has already
// cleared; these refusals hold the program to itself.
// ================================================================
program define _dash_open_page, rclass
    version 19
    syntax , PATH(string) [OS(string) DRYrun]

    // A Mac is a Mac whichever binary runs.  The console binary reports
    // c(os) as "Unix" (c(machine_type) "Mac (Apple Silicon)", measured
    // 23sep2026), and dash ran xdg-open there, which macOS does not have --
    // "/bin/bash: xdg-open: command not found", no window, and no word of
    // where the file went.  os() is measured by its length, never read
    // inside quotes before it is known to be one of the three.
    local _op_osl : length local os
    if `_op_osl' == 0 {
        local os "`c(os)'"
        if "`c(os)'" == "MacOSX" | substr("`c(machine_type)'", 1, 3) == "Mac" {
            local os "MacOSX"
        }
    }
    mata: st_local("_op_known", strofreal(anyof(("MacOSX", "Unix", "Windows"), st_local("os"))))
    if `_op_known' == 0 {
        display as error "dash: cannot open a page on that platform; os() is MacOSX, Unix or Windows."
        exit 198
    }
    mata: st_local("_op_nl", strofreal(strpos(st_local("path"), char(10)) + strpos(st_local("path"), char(13)) > 0))
    if `_op_nl' {
        display as error "dash: a path holding a line break cannot be handed to the shell; the page was not opened."
        exit 198
    }

    if "`os'" == "Windows" {
        mata: st_local("_op_dq", strofreal(strpos(st_local("path"), char(34)) > 0))
        if `_op_dq' {
            display as error "dash: a Windows path cannot hold a double quote; the page was not opened."
            exit 198
        }
        // WP-30 P1.29 (M11): start runs inside cmd.exe, which expands
        // %NAME% even inside double quotes, ! under delayed expansion, and
        // reads ^ & | < > ; as its escape and separators, so start could
        // open another file than the one written.  For such a path no
        // command is built and nothing runs -- with or without dryrun,
        // under $dash_nobrowser too -- and the path is printed, through
        // _dash_say, which never parses it; the page is already written,
        // so the rc is 0.  twoway's saving() accepts % ! ^, so the
        // validator does not refuse them.
        mata: st_local("_op_meta", strofreal(_dash_cmd_metachar(st_local("path"))))
        if `_op_meta' {
            mata: _dash_say("txt", "dash: not opened, because Windows' command shell would read the " + char(`_op_meta') + " in ", st_local("path"), "; open the page yourself.")
            return local os "`os'"
            return local cmd ""
            return local why "metachar"
            return scalar opened = 0
            exit
        }
        mata: st_local("cmd", "start " + char(34) + char(34) + " " + char(34) + st_local("path") + char(34))
    }
    else {
        local _op_prog = cond("`os'" == "MacOSX", "open", "xdg-open")
        mata: st_local("cmd", st_local("_op_prog") + " " + char(39) + subinstr(st_local("path"), char(39), char(39) + char(92) + char(39) + char(39), .) + char(39))
    }

    // WP-31 H4: the opener's own exit status.  Stata's shell returns 0
    // whatever the command did (measured 18oct2026: shell false, shell
    // exit 3 and a command not found each give 0), so on a Mac and on Unix
    // the line run is the command, then the shell's $? written to a
    // tempfile, read back below; cmd.exe's start has no such status, so on
    // Windows it is what shell returns.  r(cmd) stays the command alone.
    local opened 0
    local _op_rc 0
    local _op_status 0
    local _op_run : copy local cmd
    if "`os'" != "Windows" {
        tempfile _op_st
        local _op_status 1
        mata: st_local("_op_run", st_local("cmd") + " ; echo " + char(36) + "? > " + char(39) + subinstr(st_local("_op_st"), char(39), char(39) + char(92) + char(39) + char(39), .) + char(39))
    }
    if "`dryrun'" == "" & "${dash_nobrowser}" == "" {
        mata: st_local("_op_rc", strofreal(_stata("shell " + st_local("_op_run"), 0, 1)))
        if `_op_rc' == 0 & `_op_status' {
            tempname _op_fh
            capture file open `_op_fh' using "`_op_st'", read text
            if _rc == 0 {
                file read `_op_fh' _op_line
                file close `_op_fh'
                mata: st_local("_op_rc", strofreal(max((0, editmissing(strtoreal(strtrim(st_local("_op_line"))), 0)))))
            }
        }
        local opened 1
        if `_op_rc' != 0 {
            mata: _dash_say("txt", "dash: the browser command returned " + st_local("_op_rc") + "; open ", st_local("path"), " yourself.")
        }
    }
    return local os "`os'"
    return local cmd : copy local cmd
    return scalar opened = `opened'
    return scalar rc = `_op_rc'
end

// ================================================================
// _dash_register_graph  — store named graph in global registry
// ================================================================
// ================================================================
// _dash_drop_item  — retire every global a registry item owns
//
// Graphs and KPIs share one registry and one namespace, so replacing an
// item of one kind with the other has to take the loser's globals with it.
// A name left carrying both a `dash_json_' and a `dash_kpi_' marker is
// drawn as the KPI -- _dash_prepare_spec's graph loop passes over any
// entry with a KPI marker -- so the item the user just registered would
// vanish from the dashboard.
//
// Only the item's own globals, by EXACT name: dash_json_<name> and
// dash_spec_<name>, the marker dash_kpi_<name> and the fields
// dash_kpi_<name>__<field>.  `macro drop dash_kpi_g1*' would also take
// g10's, and a prefix took other names' globals: replacing KPI a deleted
// KPI a_b's (measured 23sep2026 at 9f48cf7).  See _dash_item_globals and
// _dash_kpi_fields in dash_parse.mata.
// ================================================================
program define _dash_drop_item
    version 19
    args name

    mata: _dash_item_globals("`name'", "_dash_item_kill")
    foreach _g of local _dash_item_kill {
        capture macro drop `_g'
    }
end


// ================================================================
// _dash_name_split  -- a graph's name() text as a name and a replace flag
//
// Usage:  _dash_name_split `"`raw'"' <name_macro> <flag_macro>
// After:  <name_macro> holds the name; <flag_macro> is 1 when the text
//         ended in ", replace", else 0.  Both are set in the caller.
//
// twoway's name(name[, replace]).  Stata's name(string) captures the whole
// of "g1, replace", so the sub-option has to be split off before the text
// is used as a name -- and every place that uses it must split it the same
// way.  _dash_register_graph did, and registered g1; _dash_plot did not,
// and wrote "g1, replace" into the stored graph as its name.  Both renderers
// key every item by that stored name, so the registry said g1 while the
// dashboard knew only "g1, replace" (measured 23sep2026 at 9f48cf7):
// layout(g2:1,1 g1:1,2) warned that g1 was not registered and drew it
// below g2, tabs(A: g1) built no tabs, link(g1 g2) left two sources,
// exclude(g1) did not protect it, and a plain build drew it last.  Both
// programs now read the name here (test_adversarial.cscript P20-33,
// test_registry_collision.cscript REG-17), and so does _dash_kpi, which
// kept a copy of the regex of its own until 23sep2026.
//
// The flag is the only word on replace.  _dash_register_graph also
// searched the whole command for name(...,replace) when the flag said no,
// so a re-used name whose title or note held those characters overwrote
// the graph it named (test_registry_collision.cscript REG-29 to REG-36).
//
// Spaces around the comma are allowed, as twoway allows them: name(g1
// ,replace) and name( g1 , replace ) are g1 and a replace.  Anything else
// after the comma -- rep, REPLACE, replace x -- is left in the name, where
// the name check refuses it, as twoway refuses it.  The regex is the one
// _dash_register_graph always used, unchanged.  regexm() follows the
// CALLER's user version; the pattern has no bounded repetition, so both
// engines read it, but below 18 the class [ \t] is a space, a backslash or
// a t rather than a space or a tab (measured 23sep2026).  Spaces work under
// both (test_caller_version.cscript CV-02).
// ================================================================
program define _dash_name_split
    version 19
    args raw name_macro flag_macro

    local _nm = strtrim(`"`raw'"')
    local _rep = 0
    if regexm(`"`_nm'"', "^([^,]+)[ \t]*,[ \t]*replace[ \t]*$") {
        local _nm = strtrim(regexs(1))
        local _rep = 1
    }
    c_local `name_macro' `"`_nm'"'
    c_local `flag_macro' `_rep'
end

// ================================================================
// _dash_refuse_second_name  -- a command gives name() more than once
// ================================================================
// twoway refuses a second name() wherever it is written -- in another plot
// group, after a paren command's comma, in another || segment or in the
// same option list, spelled name() or nam(), naming the same graph or two --
// with "option name() not allowed", r(198).  Measured 24sep2026: only when
// its FIRST name() names a graph it already holds, without replace, does it
// say "graph g1 already exists", r(110), instead, and when the first says
// replace it drops that graph before it refuses.  dash took one of the two
// -- the last group's, the one after the comma over a group's, the first of
// one list -- and named the other in its ignoring note, so a command twoway
// refuses replaced a registered graph, or registered a name twoway never
// would (test_registry_collision.cscript REG-37 to REG-41).  Refused here
// in twoway's words, before anything is registered or dropped.  The words
// hold no user text.
program define _dash_refuse_second_name
    version 19
    display as error "option name() not allowed"
    display as error "      A graph takes one name(); this command gives it more than once, which twoway refuses as well."
    exit 198
end


// ================================================================
// _dash_fn_points raw_sc lo hi n k obj_sc [drops [xname]]  -- evaluate one function layer
//                                            with twoway's own generator
// ================================================================
// dash evaluated `function' itself, in Python, and lost Stata's grammar: ^
// was folded right to left (2^3^x drew 512 where twoway draws 64), / and
// * and - and + were grouped Python's way, and pi, e, x**2 and +x were
// drawn where twoway refuses them (WP-29 P0.6).  It now runs
// twoway__function_gen -- the generator twoway function itself calls --
// as twoway calls it, and keeps the points.
//
// raw_sc is a string scalar holding the layer's text as typed (`y =' and
// all); lo, hi and n are the generator's range() and n(); k is the layer's
// place in the graph's plots (from 1); obj_sc is a string scalar the
// points are appended to, as "<k>":{"x0":..,"dx":..,"y":[..]}, comma
// separated (_dash_fn_points_json).  drops is the layer's droplines()
// (WP-31 C5), an expanded numlist or empty: checked against range() as
// the generator checks it, passed to it, and its r(dropxy) pairs stored
// as "drops":[[x,y],..].
//
//   * A top-level comma in the text would reach the generator's own option
//     list -- y = x, generate(mpg weight, replace) -- so it is refused
//     before the command line is built, r(198), as twoway refuses the
//     expression (section 04 A7).
//   * ._Gr_Global.callerver is set to the user's version ($dash__uv, set
//     at dash's entry), as graph.ado sets it before every graph: the
//     generator evaluates under it, so runiform() draws the user's
//     version's numbers (section 04 S4-D6, M6).
//   * Like twoway (twoway_function_parse.class), the data are preserved
//     only when they hold fewer than n observations, where the generator
//     adds some; otherwise it works in them, through tempvars, and the
//     data are marked changed as twoway marks them (K1-K4).  Observations
//     without a variable end as twoway ends them: none.
//   * The text reaches the command line only through macval(): the one
//     expansion it gets is the generator's own, as under twoway (M11).
//   * A refusal is echoed in twoway's one line, "error in expression: "
//     and the text after the `=' as typed (at most 200 characters), through
//     _dash_say so SMCL in it is shown, not obeyed, and ends with the
//     generator's code.  Break (r(1)) ends the command at once, unechoed.
program define _dash_fn_points
    version 19
    args raw_sc lo hi n k obj_sc drops xname
    // xname: the expression's variable, subchar() (WP-35 stat:PT-6); x
    // when it is not given.
    if "`xname'" == "" local xname x
    mata: st_local("_fx_raw", st_strscalar(st_local("raw_sc")))
    mata: st_local("_fx_echo", (ustrregexm(st_local("_fx_raw"), ///
        "^([A-Za-z_][A-Za-z0-9_]*)?[ \t]*=") ? ///
        substr(st_local("_fx_raw"), strlen(ustrregexs(0)) + 1, .) : st_local("_fx_raw")))
    mata: st_local("_fx_echo", (ustrlen(st_local("_fx_echo")) > 200 ? ///
        usubstr(st_local("_fx_echo"), 1, 197) + "..." : st_local("_fx_echo")))
    // WP-31 C12: a bare `=' before the expression (function =x) is
    // refused r(198) as twoway refuses it -- its words name a temporary
    // object ("__00000I.get_plot_count invalid name"), so dash gives the
    // last two.
    mata: st_local("_fx_beq", strofreal(ustrregexm(st_local("_fx_raw"), "^[ \t]*=")))
    if `_fx_beq' {
        display as error "invalid name"
        exit 198
    }
    mata: _dash_comma_pos(st_local("_fx_raw"), "_fx_cpos")
    // A "' with no `" open before it ends a compound quote that was never
    // opened: twoway's own parse of its command refuses it, r(198), before
    // the generator is reached (y = strlen("'x"); the generator alone
    // takes it; measured, test_json_escaping.cscript JSE-47).  A balanced
    // compound string, strlen(`"ab"'), is drawn (Q1).
    mata: st_local("_fx_cq", strofreal(_dash_fn_stray_close(st_local("_fx_raw"))))
    if `_fx_cq' local _fx_cpos 1
    if `_fx_cpos' != 0 {
        mata: _dash_say("err", "error in expression: ", st_local("_fx_echo"), "")
        exit 198
    }
    local uv : copy global dash__uv
    if "`uv'" == "" local uv = string(c(version))
    if "`._Gr_Global.isa'" == "" {
        ._Gr_Global = .global_g.new
    }
    ._Gr_Global.callerver = "`uv'"
    // Data with observations and no variable hold nothing to keep: twoway
    // leaves none there (its tempvars go, and _N with them; measured,
    // section 04 A5), so they are not preserved.
    if _N < `n' & c(k) > 0 {
        preserve
    }
    // droplines() (WP-31 C5): each x held as a float, as the generator
    // holds it, must lie within range(): "some droplines not within
    // range() option", r(198), as twoway__function_gen refuses it
    // (kde_hist_fn_truth F02, F08).  Then the generator evaluates the
    // expression there too, and its r(dropxy) pairs are stored.
    local _fx_dopt ""
    if `: length local drops' {
        local _fx_dlo .
        local _fx_dhi .
        foreach _fx_d of local drops {
            local _fx_f = float(`_fx_d')
            if `_fx_dlo' == . | `_fx_f' < `_fx_dlo' local _fx_dlo `_fx_f'
            if `_fx_dhi' == . | `_fx_f' > `_fx_dhi' local _fx_dhi `_fx_f'
        }
        if `_fx_dlo' < `lo' | `hi' < `_fx_dhi' {
            display as error "some droplines not within range() option"
            exit 198
        }
        local _fx_dopt "droplines(`drops')"
    }
    tempvar fy fx
    capture twoway__function_gen `macval(_fx_raw)', range(`lo' `hi') x(`xname') n(`n') generate(`fy' `fx') `_fx_dopt'
    local rc = _rc
    if `rc' == 1 exit 1
    if `rc' {
        mata: _dash_say("err", "error in expression: ", st_local("_fx_echo"), "")
        exit `rc'
    }
    local _fx_dxy ""
    if `: length local drops' local _fx_dxy `"`r(dropxy)'"'
    mata: st_strscalar(st_local("obj_sc"), st_strscalar(st_local("obj_sc")) + ///
        (st_strscalar(st_local("obj_sc")) == "" ? "" : ",") + ///
        char(34) + st_local("k") + char(34) + ":" + ///
        _dash_fn_points_json(st_local("fy"), strtoreal(st_local("n")), ///
        st_numscalar("r(min)"), st_numscalar("r(delta)"), st_local("_fx_dxy")))
end

// ================================================================
// _dash_fit_opts_check ptype  -- twoway's fit options, as twoway reads
//                                them (WP-31 C4)
// ================================================================
// Measured on StataNow 19.5 (test/fixtures/fit_options_truth.json,
// scripts/extract_fit_options_truth.do), each on the forty types:
//   * the types each is taken on are the _fo_<option> lists below; on any
//     other twoway's syntax refuses it, "option atobs not allowed" or
//     "option estopts() not allowed", r(198) (fpfit refuses atobs; fpfitci
//     takes it and draws as without it);
//   * with range(), on lfit, qfit, lfitci and qfitci: "may not combine
//     atobs with range()", and a predopts() holding one of predict's
//     observation-level options (residuals, cooksd, ...) "may not combine
//     residuals with range()", r(198) (twoway_lfit_parse.class, which
//     reads that predopts() at the observations, as atobs);
//   * fitplot() names one of yxtype's eight, at twoway's spellings, and
//     ciplot() a range type at its spellings or a yx type in full; any
//     other name prints twoway's two notes and draws the default line,
//     or for ciplot() a line at the lower limit; smoothplot() is declared
//     by twoway_lpolyci_parse.class and never read (the graph is the one
//     without it), so it is taken, kept in the spec under its own key
//     (WP-35 syn:SD-20c) and drawn as nothing.
// Called by _dash_process_segment after _dash_validate_opts, with s() in
// place; it sets s(fitplot) and s(ciplot) and nothing
// else.  Names are echoed through _dash_note, never as SMCL.
program define _dash_fit_opts_check, sclass
    version 19
    args ptype
    local _fo_atobs "lfit qfit lfitci qfitci fpfitci"
    local _fo_nofit "lfitci qfitci fpfitci lpolyci"
    local _fo_fitplot "lfitci qfitci fpfitci lpolyci"
    local _fo_ciplot "lfitci qfitci fpfitci lpolyci"
    local _fo_smoothplot "lpolyci"
    local _fo_estopts "lfit qfit lfitci qfitci fpfit fpfitci"
    local _fo_predopts "lfit qfit lfitci qfitci fpfit fpfitci"
    local _fo_estcmd "fpfit fpfitci"
    foreach o in atobs nofit fitplot ciplot smoothplot estopts predopts estcmd {
        mata: st_local("_fo_v", strofreal(st_global("s(" + st_local("o") + ")") != ""))
        if `_fo_v' & !`: list ptype in _fo_`o'' {
            if inlist("`o'", "atobs", "nofit") display as error "option `o' not allowed"
            else display as error "option `o'() not allowed"
            exit 198
        }
    }
    // The text handed to regress, predict and fracpoly: refused before any
    // data are touched when it holds what may not reach a command line.
    foreach o in estopts predopts estcmd {
        mata: st_local("_fo_bad", strofreal(_dash_fit_opt_bad(st_global("s(" + st_local("o") + ")"))))
        if `_fo_bad' {
            display as error "option `o'() incorrectly specified"
            exit 198
        }
    }
    local _fo_lf "lfit qfit lfitci qfitci"
    mata: st_local("_fo_rng", strofreal(strtrim(st_global("s(range)")) != ""))
    if `_fo_rng' & `: list ptype in _fo_lf' {
        mata: st_local("_fo_pr", st_global("s(predopts)"))
        local _fo_popts ""
        if `: length local _fo_pr' {
            local 0 , `macval(_fo_pr)'
            capture syntax [, Cooksd Hat Leverage Residuals RSTAndared RSTUdent COVRatio DFBeta(passthru) DFIts Welsch * ]
            if !_rc local _fo_popts = itrim(strtrim("`cooksd' `hat' `leverage' `residuals' `rstandared' `rstudent' `covratio' `dfbeta' `dfits' `welsch'"))
        }
        if `: length local _fo_popts' {
            mata: _dash_say("err", "may not combine ", st_local("_fo_popts"), " with range()")
            exit 198
        }
        if `"`s(atobs)'"' != "" {
            display as error "may not combine atobs with range()"
            exit 198
        }
    }
    mata: st_local("_fo_fp", strtrim(st_global("s(fitplot)")))
    if `: length local _fo_fp' {
        mata: st_local("_fo_c", _dash_recast_canon(st_local("_fo_fp"), "scatter:2 line:2 connected:2 bar:1 area:4 spike:5 dropline:8 dot:3"))
        if "`_fo_c'" == "" {
            mata: _dash_note("named style ", st_local("_fo_fp"), " not found in class yxtype, default attributes used")
            mata: _dash_note("yxtype not found in scheme, default attributes used", "", "")
        }
        sreturn local fitplot "`_fo_c'"
    }
    mata: st_local("_fo_cp", strtrim(st_global("s(ciplot)")))
    if `: length local _fo_cp' {
        local _fo_c ""
        if "`_fo_cp'" == "rbarm" local _fo_c rbar
        else mata: st_local("_fo_c", _dash_recast_canon(st_local("_fo_cp"), "rscatter:3 rline:3 rconnected:3 rarea:5 rbar:4 rcap:4 rcapsym:7 rspike:6 scatter:7 line:4 connected:9 area:4 bar:3 spike:5 dropline:8 dot:3"))
        if "`_fo_c'" == "" {
            mata: _dash_note("named style ", st_local("_fo_cp"), " not found in class y2xtype, default attributes used")
            mata: _dash_note("y2xtype not found in scheme, default attributes used", "", "")
            local _fo_c line
        }
        sreturn local ciplot "`_fo_c'"
    }
end

// ================================================================
// _dash_fit_points y x [if] [in] [weight], sc() ptype() [options]
//                  -- a fit layer drawn with estopts(), predopts() or
//                     estcmd(), run through twoway's own generator
//                     (WP-31 C4)
// ================================================================
// twoway hands estopts() to regress (or to fracpoly, with estcmd(), on
// fpfit and fpfitci) and predopts() to predict (fracpred): what they
// compute cannot be reproduced outside Stata.  So the layer's points are
// made here, at registration, by the generator twoway itself runs --
// twoway__lfit_serset, twoway__qfit_serset or twoway__fpfit_serset --
// with the arguments its parser hands it: n() points (lfit 3, the others
// 100; qfit reads 3 as 100), range() as min() and max(), atobs (forced by
// a predopts() of predict's observation-level options, as
// twoway_lfit_parse.class forces it), level() and the band's stdp, stdf
// or stdr.  The serset it builds is read back (serset use, under
// preserve) and its columns appended to the string scalar sc() as
// {"x":..,"y":..[,"lo":..,"hi":..],"nobs":..} (_dash_fit_points_json),
// the renderer draws them as stored and never refits them (maintainer
// decision D3).  e() is held and restored by the generator.  The text of
// the three options was checked by _dash_fit_opts_check
// (_dash_fit_opt_bad) and reaches the generator only through macval();
// a failure is the generator's own, with its note and code -- twoway's
// "(note:  regress could not fit model)" then regress's error.
program define _dash_fit_points
    version 19
    syntax varlist(min=2 max=2 numeric ts) [if] [in] [fw aw pw iw] , ///
        SC(name) PType(name) [ESTopts(string asis) PREDopts(string asis) ///
        ESTCmd(string asis) N(string) RAnge(string) ATObs LEVel(string) ///
        STD(string)]
    marksample touse
    gettoken y x : varlist
    local x = strtrim(`"`x'"')
    quietly count if `touse'
    local nobs = r(N)
    local pts 100
    if "`ptype'" == "lfit" local pts 3
    if "`n'" != "" local pts `n'
    if "`ptype'" == "qfit" & "`pts'" == "3" local pts 100
    local lo .
    local hi .
    if `"`range'"' != "" {
        local lo : word 1 of `range'
        local hi : word 2 of `range'
    }
    local _fp_ci "lfitci qfitci fpfitci"
    if !`: list ptype in _fp_ci' local std ""
    else if "`std'" == "" local std stdp
    if "`level'" == "" local level = c(level)
    local ao = ("`atobs'" != "")
    if `"`macval(predopts)'"' != "" {
        local 0 , `macval(predopts)'
        capture syntax [, Cooksd Hat Leverage Residuals RSTAndared RSTUdent COVRatio DFBeta(passthru) DFIts Welsch * ]
        if !_rc & strtrim("`cooksd'`hat'`leverage'`residuals'`rstandared'`rstudent'`covratio'`dfbeta'`dfits'`welsch'") != "" local ao 1
    }
    local w ""
    if "`weight'" != "" local w "`weight'`exp'"
    capture classutil drop .__dash_fit_ss
    local _fp_fp "fpfit fpfitci"
    if `: list ptype in _fp_fp' {
        if `"`macval(estcmd)'"' == "" local estcmd regress
        capture noisily twoway__fpfit_serset, sersetname(__dash_fit_ss) ///
            x(`x') y(`y') touse(`touse') cmd(`macval(estcmd)') ///
            regopts(`macval(estopts)') predopts(`macval(predopts)') ///
            weight(`w') level(`level') std(`std')
    }
    else {
        local gen twoway__lfit_serset
        local _fp_q "qfit qfitci"
        if `: list ptype in _fp_q' local gen twoway__qfit_serset
        capture noisily `gen', sersetname(__dash_fit_ss) x(`x') y(`y') ///
            touse(`touse') regopts(`macval(estopts)') ///
            predopts(`macval(predopts)') atobs(`ao') points(`pts') ///
            min(`lo') max(`hi') weight(`w') std(`std') level(`level')
    }
    local rc = _rc
    if `rc' {
        capture classutil drop .__dash_fit_ss
        exit `rc'
    }
    local id = `.__dash_fit_ss.id'
    preserve
    quietly serset set `id'
    quietly serset use, clear
    mata: st_strscalar(st_local("sc"), _dash_fit_points_json(`nobs'))
    restore
    capture classutil drop .__dash_fit_ss
end

// ================================================================
// _dash_refuse_unbound <parser> `"<options>"'  -- an option dash declares
//                      whose value Stata's -syntax- cannot bind
// ================================================================
// -syntax- leaves a declared option in the parser's catch-all when it
// cannot bind the value to the declared string: jitter(x"' _dup(3) "INJ"
// `") and msize() alike (measured 24sep2026).  dash then named it as an
// unsupported option -- "ignoring unsupported option(s): jitter()" -- and
// registered the graph without it, where twoway refuses the command:
// "type mismatch", r(109), for a value holding "', and "parentheses do not
// balance", r(198), for one like a" "b (measured on sixteen values;
// _dash_unbound_cands keeps the rule).  Refused here with twoway's return
// code, naming the option, before anything is registered.
//
// Called right after <parser> (_dash_parse_plot_opts or
// _dash_parse_graph_opts) read <options>, with its s() in place.  Each
// candidate from s(_unknown) is put to the parser twice, under capture:
// alone, as written -- if it binds then, it was a second copy of an option
// the list already gave, which -syntax- leaves to the catch-all and twoway
// accepts, so it stays in the note -- and as <name>(x), which binds only
// when the parser declares <name> with a value.  A flag written with a
// value, horizontal(x), binds neither way and stays in the note.  At most
// 50 candidates are put to the parser (each costs two parses); any beyond
// are named in the note as before.  When nothing is refused, <options> is
// parsed once more so the caller finds the s() it had.  The option text is
// read by value (_dash_text_args) and only reaches a command line through
// macval(); the name is a Stata name (_dash_unbound_cands checks it), and
// the message is printed through _dash_say.
program define _dash_refuse_unbound
    version 19
    mata: _dash_text_args(1, 0, 0)
    local parser : copy local _dash_a1
    local opts : copy local _dash_txt
    if !inlist("`parser'", "_dash_parse_plot_opts", "_dash_parse_graph_opts") exit
    mata: _dash_unbound_cands(st_global("s(_unknown)"), 50)
    if `_ru_n' == 0 exit
    local refuse 0
    forvalues i = 1/`_ru_n' {
        capture `parser' , `macval(_ru_tok`i')'
        if _rc continue
        mata: st_local("_ru_alone", strofreal(strtrim(st_global("s(_unknown)")) != ""))
        if !`_ru_alone' continue
        capture `parser' , `_ru_nm`i''(x)
        if _rc continue
        mata: st_local("_ru_decl", strofreal(strtrim(st_global("s(_unknown)")) == ""))
        if `_ru_decl' {
            local refuse `i'
            continue, break
        }
    }
    if `refuse' {
        local nm : copy local _ru_nm`refuse'
        local rc `_ru_rc`refuse''
        local why = cond(`rc' == 109, "type mismatch", "parentheses do not balance")
        mata: _dash_say("err", "dash: option ", st_local("nm"), ///
            "() has a value Stata cannot read, as twoway reads it: " + st_local("why") + ".")
        exit `rc'
    }
    `parser' , `macval(opts)'
end


// ================================================================
// _dash_refuse_mlabff <graph>  -- mlabfontface(), which twoway refuses
// ================================================================
// twoway_yxview_parse.class factors MLABFontface into the marker label's
// textstyle, which has no fontface: mlabfon() .. mlabfontface() holding a
// value are "option(s) fontface(<its first word>) not allowed", r(198),
// on every plot type, the rightmost copy named (mlabf() and mlabfo() are
// mlabformat(), which it reads first); a bare mlabfontface is "option
// mlabfontface not allowed"; after the paren-mode comma a spelling is
// "option mlabfontface() not allowed"; a quoted value is read to its
// closing quote, one with a blank r(111); an empty mlabfontface() is
// taken in silence, and _dash_report_ignored leaves it out of the note
// (measured 18oct2026, test_abbreviations.cscript MLF-01).  dash does not
// declare it, so it reached the catch-all and the note named it.  Called
// right after _dash_refuse_jit with the parser's s() in place: <graph> 0
// for a plot's options, 1 after the paren-mode comma.  The words are
// read by value (_dash_mlabff_refusal) and echoed through _dash_say.
// ================================================================
program define _dash_refuse_mlabff
    version 19
    args graph pend
    mata: _dash_mlabff_refusal(st_global("s(_unknown)"), `graph')
    if !`_mf_on' exit
    // pend (WP-32): held as the graph's pending refusal, its words kept
    // by value in $dash__pend_msg, and raised after the last segment.
    if "`pend'" == "pend" {
        if "${dash__pend}" == "" {
            mata: st_global("dash__pend_msg", st_local("_mf_msg"))
            global dash__pend "_dash_refuse_pendmsg `_mf_rc'"
        }
        exit
    }
    mata: _dash_say("err", "", st_local("_mf_msg"), "")
    exit `_mf_rc'
end

// _dash_pend <command>  -- hold a refusal twoway gives only after every
// plot's own options are read (WP-32): two kernels, mlabfontface(), an
// option given twice that the graph takes once.  The first held stands;
// _dash_plot clears it before the first segment and raises it after the
// last one.  <command> is a refusal program and Stata names only.
program define _dash_pend
    version 19
    if "${dash__pend}" == "" global dash__pend `"`0'"'
end

// _dash_refuse_pendmsg <rc>  -- the held mlabfontface() refusal: its words,
// kept by value in $dash__pend_msg, echoed as text, and twoway's code.
program define _dash_refuse_pendmsg
    version 19
    args rc
    mata: _dash_say("err", "", st_global("dash__pend_msg"), "")
    exit `rc'
end

// _dash_refuse_gunique <name>  -- a graph option twoway takes once from
// the whole command, given in a second plot group, || segment or after
// the comma: "option xsize() not allowed", r(198).
program define _dash_refuse_gunique
    version 19
    args gk
    display as error "option `gk'() not allowed"
    if "`gk'" == "table" display as error "      A graph takes one table; this command gives it more than once."
    else display as error "      A graph takes one `gk'(); this command gives it more than once, which twoway refuses as well."
    exit 198
end

// ================================================================
// _dash_refuse_jit  -- jitter() spelled shorter than twoway's minimum
// ================================================================
// WP-31 A3d.  twoway's minimum for jitter() is the full name: j(5),
// ji(5), jit(5), jitt(5) and jitte(5) are "option <word>() not allowed",
// and a bare jit "option jit not allowed", r(198); a value -syntax-
// cannot bind, jit(x"' ...), is "type mismatch", r(109) (measured
// 14oct2026, test_abbreviations.cscript U15-06).  dash declared JITter and
// took them; it declares JITTER now, so -syntax- leaves them to the
// catch-all, where the note would name them.  Called by
// _dash_process_segment right after _dash_refuse_unbound, with the plot
// parser's s() in place, and after the paren-mode comma right after
// _dash_refuse_foreign, with the graph parser's: the first such word of
// s(_unknown), read by value, is refused in twoway's words
// ("(scatter mpg weight), jit(5)" is "option jit() not allowed", r(198)).
// It touches nothing in s().
// ================================================================
program define _dash_refuse_jit
    version 19
    mata: st_local("_rj_w", ustrregexm(" " + st_global("s(_unknown)") + " ", "[ ,](j|ji|jit|jitt|jitte)(\(|[ ,])") ? ustrregexs(1) + (ustrregexs(2) == "(" ? "()" : "") : "")
    if "`_rj_w'" == "" exit
    mata: _dash_unbound_cands(st_global("s(_unknown)"), 50)
    forvalues i = 1/`_ru_n' {
        if inlist("`_ru_nm`i''", "j", "ji", "jit", "jitt", "jitte") & `_ru_rc`i'' == 109 {
            display as error "type mismatch"
            exit 109
        }
    }
    mata: _dash_say("err", "option ", st_local("_rj_w"), " not allowed")
    exit 198
end

// ================================================================
// _dash_refuse_asp  -- aspectratio() spelled shorter than twoway's minimum
// ================================================================
// WP-31 A3c.  twoway's minimum for aspectratio() is aspect: asp(1),
// aspe(1) and aspec(1) are "option asp() not allowed" and the like, and a
// bare asp "option asp not allowed", r(198) (measured 15oct2026,
// test/fixtures/sizing_truth.json abbrev_*, test_abbreviations.cscript
// U32-10).  dash declared ASPectratio and took them; it declares
// ASPECTratio now, so -syntax- leaves them to the catch-all.  Called
// right after _dash_refuse_nam in a plot's options and after the
// paren-mode comma, with the parser's s() in place: the first such word
// of s(_unknown), read by value, is refused in twoway's words.  It
// touches nothing in s().
// ================================================================
program define _dash_refuse_asp
    version 19
    mata: st_local("_ra_w", ustrregexm(" " + st_global("s(_unknown)") + " ", "[ ,](asp|aspe|aspec)(\(|[ ,])") ? ustrregexs(1) + (ustrregexs(2) == "(" ? "()" : "") : "")
    if "`_ra_w'" == "" exit
    mata: _dash_say("err", "option ", st_local("_ra_w"), " not allowed")
    exit 198
end

// ================================================================
// _dash_refuse_nam  -- name() spelled shorter than twoway's minimum
// ================================================================
// WP-31 A3b.  twoway's minimum for name() is the full name: na(zq) and
// nam(zq) are "option na() not allowed" and "option nam() not allowed",
// and a bare nam "option nam not allowed", r(198), in a plot's options,
// after the paren-mode comma and after a || segment's comma alike
// (measured 15oct2026, test/fixtures/edge_title_truth.json refuse_nam*,
// test_abbreviations.cscript U27-10).  dash declared NAMe and took nam()
// as name(); it declares NAME now, so -syntax- leaves them to the
// catch-all.  Called by _dash_process_segment right after
// _dash_refuse_jit, and after the paren-mode comma right after
// _dash_refuse_unbound (before the second-name() check, which would read
// nam() as a second name()), with the parser's s() in place: the first
// such word of s(_unknown), read by value, is refused
// in twoway's words.  It touches nothing in s().
// ================================================================
program define _dash_refuse_nam
    version 19
    mata: st_local("_rn_w", ustrregexm(" " + st_global("s(_unknown)") + " ", "[ ,](na|nam)(\(|[ ,])") ? ustrregexs(1) + (ustrregexs(2) == "(" ? "()" : "") : "")
    if "`_rn_w'" == "" exit
    mata: _dash_say("err", "option ", st_local("_rn_w"), " not allowed")
    exit 198
end

// ================================================================
// _dash_refuse_title2 <prefix> `"<options>"'  -- title2() and subtitle2()
// ================================================================
// WP-31 D2.  twoway has no title2() or subtitle2(): "option title2() not
// allowed" and "option subtitle2() not allowed", r(198), after the comma,
// inside a plot's parentheses and after a || segment's comma alike, and a
// bare title2 is "option title2 not allowed" (measured 15oct2026,
// test/fixtures/edge_title_truth.json refuse_*).  dash declared both and
// named them as unsupported.  They stay declared, so the spelling binds
// here and is refused rather than reaching the catch-all (a bare title2,
// which -syntax- cannot bind, is read from s(_unknown)); the check runs
// after _dash_opts_repeats, because the parser's first pass binds the
// second copy of title(A) title(B) to TITLE2(), which the repeat merge
// then folds back into title() -- twoway draws B (merged_title).  <prefix>
// is - for the graph parser's s(title2), g_ for the plot parser's
// s(g_title2).  The first such word of <options>, read by value, is named.
// WP-31 D2b: then span or nospan inside an edge title, refused as twoway
// refuses it, "option(s) t1title_span(yes) not allowed" (_dash_edge_span;
// textbox_truth.json e_t1_span).
// ================================================================
program define _dash_refuse_title2
    version 19
    mata: _dash_text_args(1, 0, 0)
    local pre : copy local _dash_a1
    if "`pre'" == "-" local pre ""
    mata: st_local("_rt_on", strofreal(st_global("s(`pre'title2)") != "" | st_global("s(`pre'subtitle2)") != "" | ustrregexm(" " + st_global("s(_unknown)") + " ", "[ ,](sub)?title2[ ,]")))
    if `_rt_on' {
        mata: st_local("_rt_w", ustrregexm(" " + st_local("_dash_txt"), "[ ,]((sub)?title2)[ ]*(\(?)") ? ustrregexs(1) + (ustrregexs(3) == "(" ? "()" : "") : (st_global("s(`pre'title2)") != "" ? "title2()" : "subtitle2()"))
        mata: _dash_say("err", "option ", st_local("_rt_w"), " not allowed")
        exit 198
    }
    // span or nospan inside an edge title (WP-31 D2b), which twoway
    // refuses when it draws: "option(s) t1title_span(yes) not allowed".
    mata: _dash_edge_span(st_local("pre"))
    if `"`_es_msg'"' != "" {
        mata: _dash_say("err", "", st_local("_es_msg"), "")
        exit 198
    }
end

// ================================================================
// _dash_opts_repeats <parser> <ptype> `"<options>"'  -- an option given
//                    more than once, read as twoway reads it
// ================================================================
// twoway takes most options more than once: the last copy of a rightmost
// one (mcolor(red) mcolor(blue) draws blue, and mc(red) mcolor(blue) too),
// the copies merged for title(), xlabel(), legend(), xscale(), by(),
// xline() and the like, and a unique one -- scheme(), saving(), xsize(), a
// bare sort, bwidth() on kdensity -- refused, "option scheme() not
// allowed", r(198) (measured 24sep2026 from twoway's SVG export; the rules
// are in dash_parse.mata beside _dash_rep_merge).  -syntax- bound the
// FIRST copy and left the others to the catch-all, which named them as
// unsupported -- or, for title(A) title(B), bound the second to title2()
// and the second xlabel() to xlabel2(), the second axis.
//
// Called right after <parser> read <options> (and _dash_refuse_unbound and
// the name() check ran), with its s() in place.  When the list may give an
// option twice (_dash_rep_scan: the catch-all is not empty, or one typed
// name is another's prefix), each distinct typed name, at most 100, is put
// to the parser alone, and the s() it sets is the option it spells
// (_dash_rep_keyof); _dash_rep_reduce writes the list again with one copy
// of each option, or names a unique one given twice, and the list is
// parsed once more so the caller finds the s() of the list twoway reads.
// Otherwise nothing is parsed again.  <ptype> is the plot type, or - for
// the graph parser.  The option text is read by value (_dash_text_args)
// and reaches a command line only through macval(); the refusal names an
// option by a Stata name.
program define _dash_opts_repeats
    version 19
    mata: _dash_text_args(2, 0, 0)
    local parser : copy local _dash_a1
    local ptype : copy local _dash_a2
    local opts : copy local _dash_txt
    if !inlist("`parser'", "_dash_parse_plot_opts", "_dash_parse_graph_opts") exit
    if "`ptype'" == "-" local ptype ""
    // First the options dash does not declare -- named in the note, one
    // copy at a time -- that twoway takes once: atobs twice on lfit is
    // "option atobs not allowed", r(198) (_dash_rep_und_tab).  The
    // graph-wide ones the list gives go back to the caller as
    // _rp_gund_out, which counts them across the command's lists.
    // WP-32: the caller's _rp_gref names a graph-wide option given twice,
    // which twoway refuses only after the plots' own options, their
    // kernel and mlabfontface() (test/fixtures/unknown_option_truth.json
    // orders: kdensity mpg, gaussian epan2 xsize(3) xsize(4) is "only one
    // kernel may be specified"), and _rp_kref two kernels ("<kind>
    // <ptype>" for _dash_refuse_kernel), which twoway refuses only after
    // every plot's own options are read (kdensity mpg, gaussian epan2 ||
    // scatter mpg weight, bogus names bogus); _rp_why is "rep" when this
    // list was refused for a plot's option given twice.
    c_local _rp_gref ""
    c_local _rp_why ""
    c_local _rp_kref ""
    local _rp_gref ""
    mata: _dash_rep_und_scan(st_local("opts"), st_local("ptype"))
    c_local _rp_gund_out : copy local _rp_gund
    if `: length local _rp_refuse' {
        if "`_rp_refuse_g'" == "1" local _rp_gref : copy local _rp_refuse
        else {
            c_local _rp_why "rep"
            _dash_refuse_repeat `_rp_refuse'
        }
    }
    // Two kernels on lpoly, lpolyci or kdensity -- gaussian epan2, or
    // gaussian beside kernel() -- refused in twoway's words once no
    // repeated option is (_dash_kernel_clash): twoway refuses bwidth(1)
    // bwidth(2) gaussian epan2 for bwidth() first.
    mata: st_local("_rp_kern", _dash_kernel_clash(st_local("opts"), st_local("ptype")))
    mata: _dash_rep_scan(st_local("opts"), strtrim(st_global("s(_unknown)")) != "", 100)
    if !`_rp_go' {
        if `: length local _rp_kern' c_local _rp_kref "`_rp_kern' `ptype'"
        c_local _rp_gref : copy local _rp_gref
        exit
    }
    forvalues i = 1/`_rp_n' {
        local _rp_key`i' ""
        sreturn clear
        capture `parser' , `macval(_rp_tok`i')'
        if _rc continue
        local _rp_sm : s(macros)
        mata: st_local("_rp_key`i'", _dash_rep_keyof(st_local("_rp_sm")))
        // An empty style copy, mcolor(""), sets no s() and so had no key:
        // mcolor(red) mcolor("") kept red and named the second unsupported,
        // where twoway draws the default (measured p2_2, WP-30 P1.1a).
        if !`: length local _rp_key`i'' & "`parser'" == "_dash_parse_plot_opts" {
            mata: st_local("_rp_pr", _dash_stylelist_probe(st_local("_rp_tok`i'")))
            if `: length local _rp_pr' {
                sreturn clear
                capture `parser' , `_rp_pr'
                if !_rc {
                    local _rp_sm : s(macros)
                    mata: st_local("_rp_pk", _dash_rep_keyof(st_local("_rp_sm")))
                    mata: st_local("_rp_slk", _dash_stylelist_keys())
                    if `: list _rp_pk in _rp_slk' & `: word count `_rp_pk'' == 1 local _rp_key`i' : copy local _rp_pk
                }
            }
        }
    }
    mata: st_local("_rp_out", _dash_rep_reduce(st_local("opts"), st_local("ptype")))
    if `: length local _rp_refuse' {
        if "`_rp_refuse_g'" == "1" {
            if !`: length local _rp_gref' local _rp_gref : copy local _rp_refuse
        }
        else {
            c_local _rp_why "rep"
            _dash_refuse_repeat `_rp_refuse'
        }
    }
    if `: length local _rp_kern' c_local _rp_kref "`_rp_kern' `ptype'"
    c_local _rp_gref : copy local _rp_gref
    sreturn clear
    // A graph-wide option given twice is left in the list: the caller
    // refuses it (_rp_gref) before anything reads the list.
    if `: length local _rp_gref' `parser' , `macval(opts)'
    else `parser' , `macval(_rp_out)'
end


// _dash_refuse_repeat <name>  -- refuse a second copy of an option twoway
// takes once, in twoway's words and with its code: "option atobs not
// allowed", r(198).  <name> is the copy twoway names, a Stata name as
// typed, "()" after it when it took a value (_dash_rep_reduce,
// _dash_rep_und_scan); it is echoed as text.
program define _dash_refuse_repeat
    version 19
    args nm
    mata: _dash_say("err", "option ", st_local("nm"), " not allowed")
    display as error "      twoway takes this option once; this command gives it more than once."
    exit 198
end


// _dash_refuse_kernel <kind> <ptype>  -- two kernels in one option list of
// lpoly, lpolyci or kdensity (_dash_kernel_clash), refused in twoway's
// words, which differ on kdensity, with its code, r(198).
program define _dash_refuse_kernel
    version 19
    args kind ptype
    if "`kind'" == "one" {
        display as error "only one kernel may be specified"
    }
    else {
        local pre ""
        if "`ptype'" == "kdensity" local pre "option "
        display as error "`pre'kernel(): old syntax may not be combined with new syntax"
        display as error "      A kernel written as an option of its own, such as gaussian, and kernel() may not be given together."
    }
    exit 198
end


// _dash_refuse_foreign <parser> <ptype> `"<options>"'  -- a word twoway
// refuses even once, where dash would name it in its note.
// ================================================================
// twoway's option names are lower case: ATOBS, MCOLOR(red), Title(x) and
// dash's own HOVER() are no options, "option MCOLOR() not allowed",
// r(198).  And after the plot groups' comma twoway takes graph options
// only: (lfit mpg weight), atobs -- or mcolor(red), kernel(), lo -- is
// "option atobs not allowed", r(198), even once, though clegend(), below
// and logging are taken there.  Either way twoway names the first word of
// the list it does not take: (lfit mpg weight), bogus atobs is "option
// bogus not allowed" (measured 24sep2026).  dash named every one in its
// note and drew the graph.
//
// Called right after <parser> read <options>, with its s() in place, and
// before _dash_opts_repeats; <ptype> is the plot type, or - for the list
// after the paren-mode comma.  When the catch-all may hold such a word
// (_dash_foreign_scan), each option word twoway does not take on dash's
// behalf is put to the parser alone: one the parser takes (a repeat
// -syntax- left to the catch-all, or an option of dash's own, such as
// hover()) is skipped.  The first word left is the one twoway names, and
// the command is refused when some word left is in upper case, or -- after
// the comma -- is a plot option: a row of _dash_rep_und_tab for a plot, or
// a word the plot parser takes alone.  Otherwise the list is parsed again,
// so the caller finds its s() as it left it, and the note names the words
// as before.  The option text is read by value (_dash_text_args); the
// refusal names an option by a Stata name, echoed as text.
program define _dash_refuse_foreign
    version 19
    mata: _dash_text_args(2, 0, 0)
    local parser : copy local _dash_a1
    local ptype : copy local _dash_a2
    local opts : copy local _dash_txt
    if !inlist("`parser'", "_dash_parse_plot_opts", "_dash_parse_graph_opts") exit
    local graph = ("`ptype'" == "-")
    if `graph' local ptype ""
    mata: _dash_foreign_scan(st_local("opts"), st_local("ptype"), st_global("s(_unknown)"), `graph')
    if !`_fs_go' exit
    local first ""
    local trig 0
    forvalues i = 1/`_fs_n' {
        if `_fs_acc`i'' continue
        sreturn clear
        capture `parser' , `macval(_fs_tok`i')'
        if _rc continue
        mata: st_local("_fs_u", strofreal(strtrim(st_global("s(_unknown)")) != ""))
        if !`_fs_u' continue
        if !`: length local first' local first : copy local _fs_nm`i'
        local trig = `_fs_uc`i'' | (`graph' & `_fs_plot`i'')
        if `graph' & !`trig' {
            sreturn clear
            capture _dash_parse_plot_opts , `macval(_fs_tok`i')'
            if !_rc {
                mata: st_local("trig", strofreal(strtrim(st_global("s(_unknown)")) == ""))
            }
        }
        if `trig' continue, break
    }
    if `trig' {
        mata: _dash_say("err", "option ", st_local("first"), " not allowed")
        if `graph' {
            display as error "      After the plot groups' comma twoway takes graph options only; a plot's own options go inside its parentheses, and option names are lower case."
        }
        else display as error "      twoway does not take this option; its option names are lower case."
        exit 198
    }
    sreturn clear
    `parser' , `macval(opts)'
end


// _dash_gopts_checks `"<options>"'  -- the refusals of the options after
// the plot groups' comma, in twoway's order, with the graph parser's s()
// for <options> in place; s() is left as the parser leaves the list
// twoway reads, and the caller's _rp_gund_out holds its graph-wide
// options dash does not declare.  WP-32: _dash_plot runs it quietly
// before the segments and again, to refuse, after them.
program define _dash_gopts_checks
    version 19
    mata: _dash_text_args(0, 0, 0)
    local gopts_raw : copy local _dash_txt
    _dash_refuse_unbound _dash_parse_graph_opts `"`macval(gopts_raw)'"'
    // The first word twoway does not take after the comma, in the
    // list's order (WP-32): an unknown word, a plot's option, one in
    // upper case, a spelling short of twoway's minimum.
    _dash_refuse_unknown _dash_parse_graph_opts - `"`macval(gopts_raw)'"'
    // name() spelled shorter than twoway's minimum (WP-31 A3b), before
    // the second-name() check would read nam() as a second name().
    _dash_refuse_nam
    // aspectratio() spelled shorter than twoway's minimum (WP-31 A3c).
    _dash_refuse_asp
    // A second name() in the options after the comma, and whether they
    // gave one at all: a group's name() is then a second one too.
    mata: st_local("_g_name2", strofreal(_dash_has_name_opt(st_global("s(_unknown)"))))
    if `_g_name2' _dash_refuse_second_name
    // A plot option after the comma -- (lfit mpg weight), atobs -- or
    // an option in upper case: refused as twoway refuses it, even once,
    // naming the first word it does not take (_dash_refuse_foreign).
    _dash_refuse_foreign _dash_parse_graph_opts - `"`macval(gopts_raw)'"'
    // jitter() spelled shorter than twoway's minimum after the comma
    // (WP-31 A3d): refused there too, as twoway refuses it.
    _dash_refuse_jit
    // mlabfontface() after the comma, as twoway refuses it (MLF-01).
    _dash_refuse_mlabff 1
    // An option given twice after the comma, read as twoway reads it.
    _dash_opts_repeats _dash_parse_graph_opts - `"`macval(gopts_raw)'"'
    if `: length local _rp_gref' _dash_refuse_repeat `_rp_gref'
    // title2() and subtitle2(), which twoway has not (WP-31 D2).
    _dash_refuse_title2 - `"`macval(gopts_raw)'"'
    c_local _rp_gund_out : copy local _rp_gund_out
end


// _dash_refuse_unknown <parser> <ptype> `"<options>"'  -- the first word
// of a list twoway does not take, refused as twoway refuses it
// ================================================================
// WP-32 (BUGS.md "In a few mixed lists dash names another word than
// twoway names first, and an unknown lower-case word is noted where
// twoway refuses it").  twoway takes no option it does not know: bogus,
// bogus(1), xreverse, cl(red) and bargap() on scatter are "option bogus
// not allowed", r(198), and it names the first word of the list it does
// not take, before two kernels, mlabfontface() and a graph option given
// twice -- gaussian epan2 bogus is "option bogus not allowed" -- and in
// a list's own order among the words it does not know (ATOBS jit(5) names
// ATOBS, jit(5) title2(a) jit()) and a plot's option given twice
// (bwidth(1) bwidth(2) bogus names bwidth(); measured 19oct2026,
// test/fixtures/unknown_option_truth.json).  dash named an unknown
// lower-case word in its note and drew the graph; TP-07's rule that it
// should is superseded (no DECISIONS.md row keeps it).
//
// Called right after <parser> read <options> and _dash_refuse_unbound
// ran, with its s() in place; <ptype> is the plot type, or - for the list
// after the paren-mode comma.  The words are classed by
// _dash_unknown_scan: a word the catch-all holds that twoway does not take
// here (_dash_tw_takes) is put to the parser alone, and one it takes then
// (a second copy of an option dash declares, or one of dash's own) is
// skipped.  When an earlier word is a plot option given twice -- or,
// after the comma, any option given twice -- the list is left to
// _dash_opts_repeats, which names it.  The word is named as typed, echoed
// through _dash_say; s() is left as the parser left it.
// ================================================================
program define _dash_refuse_unknown
    version 19
    mata: _dash_text_args(2, 0, 0)
    local parser : copy local _dash_a1
    local ptype : copy local _dash_a2
    local opts : copy local _dash_txt
    if !inlist("`parser'", "_dash_parse_plot_opts", "_dash_parse_graph_opts") exit
    local graph = ("`ptype'" == "-")
    if `graph' local ptype ""
    mata: _dash_unknown_scan(st_local("opts"), st_global("s(_unknown)"), st_local("ptype"), `graph')
    if !`_uk_go' exit
    local k 0
    forvalues i = 1/`_uk_n' {
        if "`_uk_cls`i''" == "" continue
        if "`_uk_cls`i''" == "cand" {
            sreturn clear
            capture `parser' , `macval(_uk_tok`i')'
            if _rc continue
            mata: st_local("_uk_u", strofreal(strtrim(st_global("s(_unknown)")) != ""))
            if !`_uk_u' continue
        }
        local k `i'
        continue, break
    }
    sreturn clear
    `parser' , `macval(opts)'
    if !`k' exit
    if `k' > 1 {
        mata: st_local("_uk_pre", _dash_rep_prefix(st_local("opts"), `k' - 1))
        local _rp_why ""
        local _rp_gref ""
        local _uk_pt "`ptype'"
        if `graph' local _uk_pt "-"
        capture {
            sreturn clear
            `parser' , `macval(_uk_pre)'
            _dash_opts_repeats `parser' `_uk_pt' `"`macval(_uk_pre)'"'
        }
        local _uk_prc = _rc
        sreturn clear
        `parser' , `macval(opts)'
        if (`_uk_prc' & "`_rp_why'" == "rep") | (`graph' & `: length local _rp_gref') exit
    }
    if "`_uk_cls`k''" == "jit" {
        _dash_refuse_jit
        exit
    }
    mata: _dash_say("err", "option ", st_local("_uk_nm`k'"), " not allowed")
    if "`_uk_cls`k''" == "uc" {
        display as error "      twoway does not take this option; its option names are lower case."
    }
    else if `graph' {
        display as error "      After the plot groups' comma twoway takes graph options only; a plot's own options go inside its parentheses."
    }
    else display as error "      twoway does not take this option here."
    exit 198
end


// _dash_p_apply <ptype> <number of ys> <option text> -- WP-35 syn:SD-3:
// the plot's own p<j>() and the graph's p<k>() for this plot merged into
// its option text (_dash_p_seg, dash_parse.mata), read by value
// (_dash_text_args).  An option of a p#() value that twoway does not
// take is refused as twoway refuses it (_dash_p_unknown).  Hands back the
// caller's opts_raw and _pa_named (the p#() words not drawn, for the
// note).
program define _dash_p_apply
    version 19
    mata: _dash_text_args(2, 0, 0)
    local ptype : copy local _dash_a1
    local n : copy local _dash_a2
    mata: st_local("_pa_opts", _dash_p_seg(st_local("_dash_txt"), st_local("ptype"), strtoreal(st_local("n"))))
    forvalues i = 1/`_pa_nv' {
        sreturn clear
        capture _dash_parse_plot_opts , `macval(_pa_v`i')'
        if !_rc mata: _dash_p_unknown(st_global("s(_unknown)"), st_local("ptype"))
        sreturn clear
    }
    // WP-35 DT-15: a spelling twoway refuses inside a p#() text is
    // refused after every plot group's own options and before the options
    // after the comma, the lowest plot first, as twoway reads p#() texts
    // (dash_only_words_truth.json order.p_*): the first plot's hit is held
    // in $dash__dop, "<hit>" char(1) "<its p#() words, as twoway lists
    // them>", for _dash_plot.  Each y's own p<j>() first, then the graph's.
    if !`: length global dash__dop' & 0`_pa_nv' {
        forvalues j = 1/`n' {
            local _do_hit ""
            local _do_toks ""
            forvalues i = 1/`_pa_nv' {
                if "`_pa_k`i''" != "`j'" continue
                mata: st_local("_do_h", _dash_dashonly_typed(st_local("_pa_v`i'"), 1))
                if `: length local _do_h' & !`: length local _do_hit' local _do_hit : copy local _do_h
                mata: st_local("_do_toks", strtrim(st_local("_do_toks") + " " + st_local("_do_all")))
            }
            if `: length local _do_hit' {
                mata: st_global("dash__dop", st_local("_do_hit") + char(1) + st_local("_do_toks"))
                continue, break
            }
        }
    }
    c_local opts_raw : copy local _pa_opts
    c_local _pa_named : copy local _pa_named
end


// _dash_register_graph <name text> <graph JSON> <command>, each argument the
// name of a string scalar holding it.  All three are read by value: they
// were three compound-quoted arguments read with -args-, and a command
// holding "' ended the second early, its next word becoming the third --
// if make != "'x" after the plot groups registered with rc 0, the graph
// stored as the one word x and the command cut at the quote (measured
// 24sep2026; test_json_escaping.cscript JSE-45, JSE-47).
program define _dash_register_graph
    version 19
    args name_sc json_sc spec_sc fp_sc
    mata: st_local("name", st_strscalar(st_local("name_sc")))
    mata: st_local("json_spec", st_strscalar(st_local("json_sc")))
    mata: st_local("raw_spec", st_strscalar(st_local("spec_sc")))

    // Split off a ", replace" sub-option BEFORE validating the name.  Stata's
    // name(string) captures the whole of "g1, replace", which then failed the
    // name regex below -- so name(g1, replace) was impossible, and the error
    // message further down told the user to type the very syntax that could
    // not work.  _dash_plot splits the stored graph's name by the same rule,
    // so the name registered here is the name the stored JSON carries, and
    // the flag is the only word on replace (see below).  raw_spec, the
    // whole command, is stored and never read for it.
    //
    // Only a text that can be name[, replace] -- letters, digits, _, blanks
    // and a comma -- is split; any other is refused below as the name it is
    // not.  Split, it was expanded again on _dash_name_split's command line:
    // name(\$m) registered under whatever $m held, and an =exp in it was
    // evaluated (measured 24sep2026; test_json_escaping.cscript JSE-68).
    mata: st_local("_nm_raw_ok", strofreal(!ustrregexm(st_local("name"), "[^A-Za-z0-9_, \t]")))
    local replace_flag 0
    if `_nm_raw_ok' {
        _dash_name_split `"`name'"' _nm replace_flag
        local name `"`_nm'"'
    }

    // Validate name format.  No bounded repetition such as {0,31}: regexm()
    // follows the CALLER's user version, and below 18 it runs Stata's old
    // engine, which does not know it -- every name was refused in a do-file
    // that began `version 16' (test_caller_version.cscript).  The length is
    // checked on its own, and it is 22, not 32: the name becomes part of the
    // globals dash_json_<name> and dash_spec_<name>, and a global's name is
    // at most 32 characters.  A 23- to 32-character name used to pass here
    // and then fail on the global with Stata's bare "invalid name".  Until
    // it passes, the name is read through a string scalar: in plain quotes a
    // name holding a double quote ended them -- name(`"q"7"') stopped with
    // r(303), "equation [a-zA-Z_] not found" (measured 24sep2026;
    // test_json_escaping.cscript JSE-47, JSE-68).  After, it is letters,
    // digits and underscores.
    tempname NS
    mata: st_strscalar(st_local("NS"), st_local("name"))
    if !`_nm_raw_ok' | !regexm(scalar(`NS'), "^[a-zA-Z_][a-zA-Z0-9_]*$") | strlen(scalar(`NS')) > 22 {
        // Echoed as text: a refused name may hold anything, and shown raw
        // name(a{bf:X}) printed a bold X -- the user's text drawn as SMCL.
        mata: st_local("_name_safe", ustrregexra(usubstr( ///
            st_local("name"), 1, 40), "[^A-Za-z0-9_.\-]", "?"))
        display as error "dash: invalid graph name '`_name_safe''. " ///
            "Names must start with a letter or underscore, contain only " ///
            "letters, digits, and underscores, and be at most 22 characters."
        exit(198)
    }

    // Two underscores in a row are dash's own.  The renderer names what it
    // generates with them -- a by() graph g1's panels are g1__by__0,
    // g1__by__1, ..., a KPI's per-panel cards the same, and the saved
    // layout(bs) page keys its tab strip and filters __tabs__ and __fw_0__
    // -- so a name holding them took one of those places without a word
    // (measured 23sep2026: name(g1__by__0) beside by(foreign) name(g1) was
    // drawn as g1's first panel).  A rule of its own, after the format
    // check, so the message names the one rule broken; by now the name is
    // letters, digits and underscores.  The renderer refuses such a name in
    // a spec that did not come through here (_dash_named_once).
    if strpos("`name'", "__") {
        mata: _dash_say("err", "dash: graph name '", st_local("name"), ///
            "' holds two underscores in a row, which dash keeps for the " + ///
            "names it generates, such as a by() graph's panels. " + ///
            "Choose a name without __.")
        exit(198)
    }

    // _all is link()'s word for every graph: a graph named _all made
    // link(_all g2) build, linking every graph when saved and two when
    // served (measured 23sep2026).  Stata itself keeps the word.
    if "`name'" == "_all" {
        display as error "dash: graph name '_all' is the word link(_all) " ///
            "uses for every graph. Choose another name."
        exit(198)
    }

    // name()'s own text, split above, is the only thing that decides a
    // replace.  This program also searched the WHOLE command for
    // name(...,replace) whenever that text held none -- lower-cased and
    // anywhere, rename( included -- so a re-used name overwrote the graph
    // it named when a title, note, caption, text(), an if qualifier or an
    // unsupported NAME() option held those characters.  Measured 23sep2026
    // at ad13a0f: rc 0 in silence, and a graph given a KPI's name deleted
    // the card, where twoway refuses every one with r(110).  The search was
    // this program's first way of reading replace (25mar2026, the first
    // commit): meant to read name()'s value, it read the whole command, and
    // the name check before it refused any name() text holding a replace,
    // so it only ever acted on text outside name().
    // Stata's name(string) captures name()'s whole text on every route --
    // a plot's options, a paren command's graph options, any || segment --
    // so the search decided nothing that text did not, except to say yes
    // where it said no: text elsewhere, or a second name() dash does not
    // read, which twoway refuses as well (test_registry_collision.cscript
    // REG-29 to REG-36).

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

    // A function graph's points are kept in one global, which holds
    // c(macrolen) characters; st_global() past that truncates in silence
    // (WP-29 P0.6, section 04 E6).  Refused before anything is stored.
    local _fp_len 0
    if "`fp_sc'" != "" {
        mata: st_local("_fp_len", strofreal(strlen(st_strscalar(st_local("fp_sc")))))
    }
    if `_fp_len' > c(macrolen) {
        _dash_count_fmt _fp_len_s `_fp_len'
        display as error "dash: graph '`name'' holds `_fp_len_s' characters of function points, more than the `c(macrolen)' one Stata macro holds."
        display as error "      Use a smaller n(), put the function layers in separate graphs, or raise c(macrolen) with set maxvar."
        exit 134
    }

    // WP-19: the registry holds at most `graphs' graphs and KPI cards.  A
    // NEW name past the limit is refused here, before any global is set or
    // retired; a name already registered is a replace and never counts.
    _dash_graph_cap `already'

    // Retire whatever held this name before.  Without this a graph that
    // replaced a KPI kept the KPI's marker, and _dash_prepare_spec then
    // skipped the graph -- the user replaced an item and lost both.
    if `already' == 1 {
        _dash_drop_item "`name'"
    }

    // Store spec and JSON, by value: through compound quotes the command
    // was expanded again, and an =exp in it evaluated (JSE-67).
    mata: st_global("dash_spec_" + st_local("name"), st_local("raw_spec"))
    mata: st_global("dash_json_" + st_local("name"), st_local("json_spec"))
    // The graph's function points (WP-29 P0.6), or none: a graph that
    // replaced a function graph keeps no points of it.
    if `_fp_len' {
        mata: st_global("dash_fpts_" + st_local("name"), st_strscalar(st_local("fp_sc")))
    }
    else {
        capture macro drop dash_fpts_`name'
    }
    // The unit the t-options' dates were read in (WP-30 P1.6,
    // _dash_taxis_fold), for dash build's note when it has changed.
    // dash_tu_<name> is 8 + 22 characters, within a global's 32
    // (dash_tunit_<name> was 33 at the longest name).
    mata: st_local("_tu_reg", st_global("dash__tunit"))
    if `: length local _tu_reg' {
        mata: st_global("dash_tu_" + st_local("name"), st_global("dash__tunit"))
    }
    else capture macro drop dash_tu_`name'
    capture macro drop dash__tunit
    // The frame the graph was registered in (WP-33 33-07, P4-7): dash build
    // draws it from there, as twoway draws from the current frame.
    // dash_frm_<name> is 9 + 22 characters, within a global's 32.
    mata: st_global("dash_frm_" + st_local("name"), c("frame"))

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
    version 19
    // The graph JSON alone; the command, handed over as well, was read by
    // nothing (see _dash_plot).  fp_sc is the string scalar holding the
    // graph's function points (WP-29 P0.6), "" when it has none.
    args json_spec fp_sc

    // ---- Extract saving() path from JSON ----
    local saving_path ""
    local open_browser = 0

    // Read it as JSON, not as text.  This used to slice the raw document at
    // the first quote after "saving":" -- but the value had been written by
    // _dash_json_str, so every backslash in it was doubled and the result was
    // then used as a FILESYSTEM PATH.  Measured: saving("<dir>a\b.html")
    // returned rc 0 and wrote "<dir>a\\b.html"; the file the user asked for
    // did not exist.  Every Windows saving() path on this route landed
    // somewhere other than where it was meant to.  Slicing at the first quote
    // also truncated any path containing one, since \" is a quote in the
    // document but not in the value.
    //
    // _dash_json_get_str already does this correctly, escapes and all -- it
    // is the same reader dash uses for every other spec value.
    mata: _dash_json_get_str(st_local("json_spec"), "saving", "saving_path")

    if `: length local saving_path' {
        // twoway accepts saving(name), saving(name.gph) and
        // saving(name, replace).  Normalise all three to a .html path BEFORE
        // validating: validation demands a .html suffix, and it used to run
        // before the suffix was appended, so every twoway-shaped saving()
        // aborted with r(198).  The path is the user's text, read through
        // the string scalar P until the validator has judged it: a macro in
        // it was expanded again here, so saving("\$D/x.html") wrote the page
        // where $D pointed (measured 24sep2026; test_json_escaping.cscript
        // JSE-68).
        // WP-30 P1.27: one grammar, twoway's (_dash_saving_parse), shared
        // with dash build.  Only a trailing ", replace" was read here, so
        // saving(n1, asis) wrote "n1, asis.html" and saving(n4, bogus)
        // "n4, bogus.html" (measured).  The text is the one _dash_plot read
        // as typed, read by value.
        local _sv_gph ""
        mata: _dash_saving_parse(st_local("saving_path"), "html")
        local replace : copy local _sv_replace
        local saving_path : copy local _sv_file
        local _gph = ("`_sv_gph'" == "1")
        _dash_validate_path `"`macval(saving_path)'"'
        local saving_path `"`_dash_vpath'"'   // `~/' expanded, if it was there
        if `_gph' {
            mata: _dash_note("dash: saving() writes HTML, not a Stata .gph; using ", st_local("saving_path"), "")
        }
        // WP-30 P1.28a: a suffix graph export writes is replaced too.
        if "`_sv_img'" != "" {
            mata: _dash_note("dash: saving() writes HTML, not a ." + st_local("_sv_img") + " image; using ", st_local("saving_path"), "")
        }
        // A file that is there already is kept unless replace was given --
        // saving(name, replace), twoway's form, or replace after the comma,
        // dash build's, which _dash_plot folds into saving() -- and a
        // directory in its place is never written (_dash_saving_clobber).
        // This route wrote over the user's file with rc 0 (measured
        // 24sep2026 by WP-24; test_path_validation.cscript PV-22..27).  The
        // directory is checked first: one that does not exist holds no file.
        _dash_saving_dir `"`saving_path'"'
        _dash_saving_clobber `"`saving_path'"' "`replace'" "dash"
    }
    else {
        // No saving(): the preview page.  It is named once the data are
        // exported (_dash_tmp_preview, below), in c(tmpdir)dash-<uid>/
        // previews/, 0600, under a name no other preview has (WP-29 P0.14).
        // It was a Stata tempfile plus .html, a name Stata never registered:
        // never deleted, 0644, and each preview overwrote the last (D1-D3).
        local _dash_preview 1
        local open_browser = 1
    }

    if "`_dash_preview'" != "1" {
        if !regexm(lower("`saving_path'"), "\.html$") {
            local saving_path = "`saving_path'.html"
        }
    }

    // ---- The qualifiers, evaluated in Stata ----
    // Each if/in pair of the graph and its plots becomes the column that
    // holds Stata's answer (_dash_qual_rewrite, _dash_qual_gen); the spec
    // carries the column's name and no qualifier text.  The graph as
    // registered is kept for a graph that needs no data, below.
    local _json_orig : copy local json_spec
    local _dq_err ""
    // WP-35 DT-19: the prefix of every column this export makes, chosen so
    // that no variable of the data starts with it (_dash_reserved_prefix):
    // a variable named __dash... is then data, as twoway reads it.
    capture unab _rp_all : __d*
    if _rc local _rp_all ""
    mata: st_local("_dash_rp", _dash_reserved_prefix(tokens(st_local("_rp_all"))))
    mata: _dash_qual_reset()
    mata: st_local("json_spec", _dash_qual_rewrite(st_local("_json_orig"), "_dq_err", 1))
    if `: length local _dq_err' {
        mata: _dash_say("err", "dash: the graph's qualifier cannot be evaluated: ", st_local("_dq_err"), ".")
        exit 198
    }

    // ---- Time-series operators in plot variables (WP-30 P1.7) ----
    // Each expression (L.close) becomes the column __dasht<k> Stata fills
    // with tsrevar at export (_dash_tsop_gen); the spec names the column
    // and carries the expression and twoway's text in "ts_cols".
    // A weight expression (WP-31 A5) becomes the column __dashw<k> Stata
    // fills with generate at export (_dash_wexp_gen), first, so a
    // canonical time-series weight is left to the table below.
    local _dts_err ""
    mata: _dash_wexp_reset()
    mata: st_local("json_spec", _dash_wexp_rewrite(st_local("json_spec"), "_dts_err"))
    if `: length local _dts_err' {
        mata: _dash_say("err", "dash: ", st_local("_dts_err"), ".")
        exit 198
    }
    mata: _dash_tsop_reset()
    mata: st_local("json_spec", _dash_tsop_rewrite(st_local("json_spec"), "_dts_err"))
    if `: length local _dts_err' {
        mata: _dash_say("err", "dash: ", st_local("_dts_err"), ".")
        exit 198
    }
    local _dts_n = 0
    mata: _dash_tsop_export()
    local _dwx_n = 0
    mata: _dash_wexp_export()
    local _dts_names ""
    forvalues _dtk = 1/`_dts_n' {
        local _dts_names `_dts_names' `_dash_rp't`_dtk'
    }
    forvalues _dtk = 1/`_dwx_n' {
        local _dts_names `_dts_names' `_dash_rp'w`_dtk'
    }

    // ---- Determine variables needed ----
    local needed_vars ""
    mata: _dash_extract_vars(`"`json_spec'"', "needed_vars")
    // The time-series columns do not exist until _dash_tsop_gen makes
    // them; they reach the writer through _dash_tsop_vars.
    local needed_vars : list needed_vars - _dts_names

    // ...including the ones named only in by().  A qualifier's variables
    // are not exported: its answer is (_dash_qual_gen), and the rewritten
    // spec holds no qualifier text for _dash_extract_qual_vars to read.
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
    // WP-29 P0.10: every variable hover() names is exported -- it was
    // not, so a variable named only there was left out of the tooltip
    // with rc 0 and no note.  Read and checked in Mata
    // (_dash_extract_hover_vars) before it reaches any command.
    local _hvars ""
    local _hv_bad ""
    local _hv_why ""
    mata: _dash_extract_hover_vars(st_local("json_spec"), "_hvars", "_hv_bad", "_hv_why")
    if "`_hv_why'" == "name" {
        mata: _dash_say("err", "dash: hover() must name variables (got: ", st_local("_hv_bad"), ")")
        exit 198
    }
    if "`_hv_why'" == "var" {
        mata: _dash_say("err", "dash: hover(): variable ", st_local("_hv_bad"), " not found")
        exit 111
    }
    if "`_hvars'" != "" {
        local needed_vars : list needed_vars | _hvars
    }
    local needed_vars = strtrim("`needed_vars'")

    // The literal family -- scatteri, pci, pcarrowi and function -- takes
    // literal coordinates or an expression rather than variables, so having
    // no varlist is correct for them; this guard used to reject those plot
    // types outright.  The list comes from _dash_plottype_families, so a
    // literal type added there is admitted here: this list was written out
    // by hand and did not know pcarrowi (WP-22).  pcscatter was on it, from
    // when it was parsed as literals; it takes four variables and has no
    // need.
    //
    // A graph that names no variable is drawn when EVERY plot in it is of
    // that family (_dash_spec_types_in), and its data file holds no
    // variable (_dash_empty_data).  One literal plot used to be enough, so
    // a spec holding a scatteri beside a line with no variables was drawn
    // and the render died in Python, r(7102) -- a spec dash no longer
    // writes (P1A-69), but this program reads whatever spec it is handed
    // (P1A-74).  And the file held ONE observation of the first variable
    // in memory, a placeholder no layer read, so with no data in memory
    // `dash scatteri 1 2 3 4, saving(f)' was refused here, where twoway
    // draws it (measured 24sep2026; P1A-72).
    _dash_plottype_families
    local _varfree = 0
    if "`needed_vars'" == "" & `_dts_n' == 0 {
        // A graph with no plot (bare dash, as bare twoway) needs no
        // variable either: twoway draws it empty.
        mata: st_local("_varfree", strofreal(_dash_spec_types_in( ///
            st_local("json_spec"), st_local("_pt_literal")) | ///
            !_dash_spec_has_plots(st_local("json_spec"))))
        if !`_varfree' {
            display as error "dash: no variables identified in plot specification."
            exit(198)
        }
        // No data are exported, so no qualifier column: the literal family
        // draws its own values, which twoway's if and in do not reach.
        mata: _dash_qual_reset()
        mata: st_local("json_spec", _dash_qual_rewrite(st_local("_json_orig"), "_dq_err", 0))
    }

    // ---- Write the data file (_dash_write_data) ----
    // Into this command's private run folder (_dash_tmp_open, below, once
    // every limit has been checked), not Stata tempfiles (WP-29 P0.12b).

    // Always export ALL rows for the needed variables.  Do NOT pre-filter with
    // if/in qualifiers here: multiple plots in the same graph can have different
    // qualifiers, and applying only the first plot's qualifier would silently
    // discard rows needed by other plots.  Each distinct qualifier -- the
    // graph's, promoted to the graph JSON by _dash_plot, and each plot's own --
    // is exported instead as the 0/1 column that holds Stata's answer
    // (_dash_qual_gen), and both renderers select a layer's rows with it.

    // The data file is written from Python through sfi (_dash_write_data):
    // jsonio, which wrote it until 24sep2026, is no longer needed.

    // ---- Resource limits (WP-19), before anything is exported ----
    // Every dash_max_* global the session has set is validated here -- a
    // bad one is refused before the export, not after it -- and travels to
    // the renderer as build_options.limits.
    _dash_limits_json
    local _dash_lim_json `"`r(json)'"'
    // Each qualifier column is embedded with the data, and counted.
    mata: _dash_qual_export()
    // sort(varlist)'s join-order columns (WP-29 P0.1): each distinct
    // "sortvars" list the plots carry, checked again to be names
    // (_dash_sort_scan; the registry is a global a do-file can set), one
    // rank column each, embedded with the data and counted.
    local _ds_bad ""
    mata: _dash_sort_reset()
    mata: _dash_sort_scan(st_local("json_spec"))
    mata: st_local("_ds_isbad", strofreal(st_local("_ds_bad") != ""))
    if `_ds_isbad' {
        display as error "option sort() incorrectly specified"
        display as error "      dash: a sort() list in the registered graph is not Stata names."
        exit 198
    }
    local _ds_n = 0
    mata: _dash_sort_export()
    local _ds_json ""
    forvalues _dsk = 1/`_ds_n' {
        _dash_json_str "`_ds_v`_dsk''" _ds_vj
        local _ds_sep ""
        if `_dsk' > 1 local _ds_sep ","
        local _ds_json `"`_ds_json'`_ds_sep'"`_ds_vj'":"`_dash_rp's`_dsk'""'
    }
    if `_ds_n' > 0 local _ds_json `","sort_cols":{`_ds_json'}"'
    // Reference lines: positions times by() panels (WP-30 P1.21a).
    _dash_reflines_of `"`macval(json_spec)'"'
    _dash_reflines_cap `r(n)'

    // Collect display formats.  Each travels in the spec's formats map;
    // the data file carries every number as stored, whatever its format.
    _dash_formats_json "`needed_vars'" _dash_fmt_json _dash_date_vars _dash_bcal_json
    // The time-series columns: their bases' formats, and the spec's map
    // from each column to its expression and twoway's text.
    local _dts_json ""
    if `_dts_n' + `_dwx_n' > 0 {
        mata: st_local("_dts_obj", _dash_tsop_meta("_dash_fmt_json"))
        local _dts_json `","ts_cols":`macval(_dts_obj)'"'
    }

    // ---- The private run folder (WP-29 P0.12b) ----
    // After every refusal above, so a refused command makes no folder.  r()
    // is read on the very next lines (A12); r(noted) says whether the
    // command's one note was printed.
    _dash_tmp_open
    local _dash_run      `"`r(rundir)'"'
    local spec_json_path `"`r(spec)'"'
    local data_json_path `"`r(data)'"'
    local _dash_noted    `"`r(noted)'"'
    local _dash_jrc = 0
    if `_varfree' {
        _dash_empty_data "`data_json_path'"
    }
    else {
        // The qualifier columns, made first: a qualifier Stata refuses
        // stops here, before any format is touched.  Dropped the moment
        // the file is written, or fails to be.  Estimates in memory are
        // held meanwhile, and restored when this program ends: with an
        // e(sample) present, jsonio named the first variable made after
        // it "(e)" rather than __dashq1, and the renderer refused the
        // spec (measured 24sep2026; test_qualifier_in_stata.cscript QS-15).
        local _dash_qual_vars ""
        local _dash_sort_vars ""
        local _dash_tsop_vars ""
        local _dash_wexp_vars ""
        // WP-35 DT-19: a qualifier or weight naming e(sample) reads the
        // estimation sample, as twoway reads it: a byte copy made before
        // the estimates are held (held, e(sample) reads 0), which the
        // generators read in its place (_dash_esample_sub).
        local _dash_es ""
        _dash_esample_copy `_dash_rp' "dash"
        // WP-31 G3d, WP-35 DT-19: every working column counted against
        // c(maxvar) before the first is made: made in place with room
        // beside the data's variables, else in a temporary frame of the
        // variables the export reads (_mv_plan frame), else refused in
        // dash's words with the data left as they were.
        _dash_frame_vars `_dash_rp' "" `needed_vars'
        capture noisily _dash_maxvar_room `_dq_n' `_ds_n' `_dts_n' `_dwx_n' "dash" `_mv_kx'
        if _rc {
            local _dt_rc = _rc
            if "`_dash_es'" != "" capture drop `_dash_es'
            _dash_tmp_close, dir(`"`_dash_run'"')
            exit `_dt_rc'
        }
        if `_dq_n' + `_ds_n' + `_dts_n' + `_dwx_n' > 0 {
            tempname _dash_eh
            _estimates hold `_dash_eh', restore nullok
        }
        local _xfp ""
        if "`_mv_plan'" == "frame" {
            tempname _dash_xf
            _dash_frame_put `_dash_xf' `_mv_vars'
            local _xfp "frame `_dash_xf':"
            // The copy travels in the frame; the user's data keep nothing.
            if "`_dash_es'" != "" capture drop `_dash_es'
        }
        capture noisily `_xfp' _dash_qual_gen "dash" "" "`_dash_rp'"
        if _rc {
            local _dt_rc = _rc
            if "`_dash_es'" != "" capture drop `_dash_es'
            capture frame drop `_dash_xf'
            _dash_tmp_close, dir(`"`_dash_run'"')
            exit `_dt_rc'
        }
        // The join-order columns after the qualifier columns; a sort()
        // variable gone since registration drops what was made.
        capture noisily `_xfp' _dash_sort_gen "dash" "" "`_dash_rp'"
        if _rc {
            local _ds_rc = _rc
            if "`_dash_qual_vars'" != "" capture `_xfp' drop `_dash_qual_vars'
            if "`_dash_es'" != "" capture drop `_dash_es'
            capture frame drop `_dash_xf'
            _dash_tmp_close, dir(`"`_dash_run'"')
            exit `_ds_rc'
        }
        // The time-series columns last, under the user's sort (WP-30
        // P1.7); tsrevar's refusal drops what was made.
        capture noisily `_xfp' _dash_tsop_gen "dash" "" "`_dash_rp'"
        if _rc {
            local _dt_rc = _rc
            capture `_xfp' drop `_dash_qual_vars' `_dash_sort_vars'
            if "`_dash_es'" != "" capture drop `_dash_es'
            capture frame drop `_dash_xf'
            _dash_tmp_close, dir(`"`_dash_run'"')
            exit `_dt_rc'
        }
        // The weight-expression columns (WP-31 A5); generate's refusal
        // drops what was made.
        capture noisily `_xfp' _dash_wexp_gen "dash" "" "`_dash_rp'"
        if _rc {
            local _dt_rc = _rc
            capture `_xfp' drop `_dash_qual_vars' `_dash_sort_vars' `_dash_tsop_vars'
            if "`_dash_es'" != "" capture drop `_dash_es'
            capture frame drop `_dash_xf'
            _dash_tmp_close, dir(`"`_dash_run'"')
            exit `_dt_rc'
        }
        local _dst_names json_spec
        local _dash_st_json ""
        // WP-31 D15: Stata's own #N ticks over each axis's rows, asked of
        // _natscale/_tsnatscale while the qualifier columns exist
        // (_dash_axis_ticks_stata); carried as build_options.stata_ticks.
        // Captured: a failure leaves every axis to the renderer's model.
        // The Python guard first, uncaptured, as dash ran it on entry, so
        // every python: line stands below it (test_env_guards ENV-12).
        _dash_require_python
        capture _dash_xm_load
        if _rc == 0 {
            capture python: import sys
            capture python: from sfi import Macro as _dash_M
            capture python: _dash_xm = sys.modules["_dash_render_export"]
            capture python: _dash_M.setLocal("_dst_reqs", _dash_xm._dash_stata_tick_plan(_dash_M.getLocal("_dst_names"), _dash_M.getLocal("_dash_fmt_json")))
            if _rc == 0 & `: length local _dst_reqs' {
                capture `_xfp' _dash_stata_ticks_gen `_dst_reqs'
                if _rc local _dash_st_json ""
            }
        }
        // Captured, so the qualifier columns are dropped when the export
        // fails too.  The writer reads each stored value whatever its
        // display format, so no format is touched (until 24sep2026 jsonio
        // needed each date variable %12.0g for the call, and a failed
        // export left it so: test_program_coverage.cscript PC-11).  Its
        // message is still shown and its code returned; no value is
        // expanded on the way (test_string_values.cscript).
        capture noisily `_xfp' _dash_write_data "`data_json_path'" `needed_vars' `_dash_qual_vars' `_dash_sort_vars' `_dash_tsop_vars' `_dash_wexp_vars'
        local _dash_jrc = _rc
        if "`_dash_qual_vars'`_dash_sort_vars'`_dash_tsop_vars'`_dash_wexp_vars'" != "" {
            capture `_xfp' drop `_dash_qual_vars' `_dash_sort_vars' `_dash_tsop_vars' `_dash_wexp_vars'
        }
        if "`_dash_es'" != "" capture drop `_dash_es'
        capture frame drop `_dash_xf'
    }
    if `_dash_jrc' {
        _dash_tmp_close, dir(`"`_dash_run'"')
        exit `_dash_jrc'
    }

    // The file itself is the witness that the export ran.
    capture confirm file "`data_json_path'"
    if _rc != 0 {
        _dash_tmp_close, dir(`"`_dash_run'"')
        display as error "dash: the data could not be written. " ///
            "Check that all variables exist and the data is loaded."
        exit(198)
    }

    // ---- Write spec JSON to temp file ----
    // Carry the session confidence level so the renderer does not have to
    // assume 95.  A per-plot level() overrides it.
    local _dash_lvl = c(level)
    // c(dp) before the font query: read inside it, it gave "period"
    // under set dp comma (measured 16oct2026).
    local _dash_dp = c(dp)
    _dash_graph_set_fonts _dash_gsf
    local _dash_sess_scheme = c(scheme)
    _dash_json_str `"`_dash_sess_scheme'"' _sess_scheme_esc
    _dash_scheme_dirs
    // The final } is written by _dash_fn_spec_tail, after the function
    // points (WP-29 P0.6).
    // WP-31 D15: Stata's own #N ticks, when the export asked for any.
    local _dash_st_bo ""
    if `: length local _dash_st_json' local _dash_st_bo `","stata_ticks":`_dash_st_json'"'
    local master_json = `"{"graphs": [`json_spec'], "_dash_prefix": "`_dash_rp'", "build_options": {"layout": "1 1", "theme": "", "session_scheme": "`_sess_scheme_esc'", "scheme_dirs": `macval(_dash_sdirs)', "level": "`_dash_lvl'", "dp": "`_dash_dp'", "adoarchive": "`c(adoarchive)'"`_dash_gsf', "formats": `_dash_fmt_json'`_dash_st_bo'`_dash_bcal_json', "limits": `_dash_lim_json'`_ds_json'`macval(_dts_json)'}"'

    // Written from Python, 0600 and never through a link (WP-29 P0.12b):
    // Stata's `file write' wrote it with the umask (D4) and expanded a macro
    // reference inside the value a second time (A9).  By value, with no
    // newline added.  No error branch: a refusal or an OSError ends the
    // python: line, r(7102), and the folder it leaves is swept later.
    _dash_require_python
    _dash_xm_load
    python: import sys
    python: from sfi import Macro as _dash_M
    python: _dash_xm = sys.modules["_dash_render_export"]
    // WP-31 E10 (A24): the rows of the style files the spec's named
    // styles reach on this machine, embedded as build_options._style_rows.
    // c(adoarchive) is undefined in StataNow 19.5 (r(133)) and writes "".
    python: _dash_wsp = _dash_xm._dash_tmp_write_text(_dash_M.getLocal("spec_json_path"), _dash_xm._dash_embed_style_rows(_dash_M.getLocal("master_json")))
    mata: _dash_fn_spec_tail(st_local("spec_json_path"), "", st_local("fp_sc"))

    // ---- Locate dash_render.py ----
    _dash_find_render
    local render_py `"`r(fn)'"'

    // ---- Name the preview page (WP-29 P0.14) ----
    // The browser decision first: whether a browser will be asked to open
    // the page is part of its name (b or q), which the pruning reads.  One
    // decision, in a program a certification script can call without
    // launching anything: saving() given, $dash_nobrowser set, or the
    // graph's own nodraw each keep the window shut.  nodraw is honoured
    // here, and is therefore NOT on either _dash_pending list.
    local _dash_priv ""
    if "`_dash_preview'" == "1" {
        _dash_browser_wanted, spec(`"`json_spec'"')
        local open_browser = r(open)
        _dash_tmp_preview, opened(`open_browser') noted(`_dash_noted')
        local saving_path `"`r(path)'"'
        local _dash_priv "private"
    }

    // ---- Invoke Python renderer via helper ----
    // (python:...end must be in a dedicated program; see _dash_do_render)
    _dash_do_render, spec("`spec_json_path'") data("`data_json_path'") ///
        output("`saving_path'") renderpy("`render_py'") `_dash_priv'
    _dash_tmp_close, dir(`"`_dash_run'"')

    // ---- Open in browser if no explicit saving() ----
    // The same suppression as `dash build'.  This path sets open_browser
    // only when no saving() was given, and the decision also reads batch
    // mode and set graphics off (_dash_display_on, WP-30 P1.27).  The decision was made above, where the
    // preview page was named, and is read again here, beside the opener
    // (_dash_browser_wanted is pure, so both reads agree), so the opener
    // never runs without a decision next to it (test_packaging.py).  The
    // note used to say "ignoring unsupported option(s): nodraw()" for an
    // option this decision had just applied.
    if "`open_browser'" == "1" {
        _dash_browser_wanted, spec(`"`json_spec'"')
        local open_browser = r(open)
    }
    if "`open_browser'" == "1" {
        // The one opener, shared with dash build: the platform's command,
        // a Mac known by its machine type as well (see _dash_open_page).
        _dash_open_page, path(`"`saving_path'"')
    }
    else {
        // Shown as written: braces are legal in a file name (P20-07).
        mata: _dash_say("txt", "dash: dashboard saved to ", st_local("saving_path"), "")
        // A preview not opened (batch, graphics off, nodraw, the global) is
        // pruned by later previews; say so (WP-30 P1.27).
        if "`_dash_preview'" == "1" {
            display as text "dash: this page is a temporary preview that later previews may remove; use saving() to keep it."
        }
    }
    // WP-30 P1.28a: the last statement -- the path written, absolute, for
    // r(filename) (_dash_result).
    mata: st_global("dash__rfile", _dash_abs_path(st_local("saving_path"), c("pwd"), c("os")))
end


// ================================================================
// _dash_clear  — reset global registry
// ================================================================
program define _dash_clear
    version 19

    // Sweep dash's whole global namespace, not an enumerated list.
    //
    // Two things were wrong with enumerating.  The wildcard below it read
    //     macro drop _dash_*
    // -- globals with a LEADING underscore -- and dash's globals are named
    // `dash_*' with none, so it matched nothing and only the enumeration ran.
    // And an enumeration goes stale: the list named dash_kpi_<name>_stat
    // through _upd and did NOT name _if or _in, which carry a KPI's own
    // qualifier, so
    //     dash kpi mean(mpg) if foreign==1, name(k1)
    //     dash clear
    //     dash kpi mean(mpg), name(k1)
    // left the qualifier in place and the second, unqualified KPI displayed
    // the conditional mean.  A stale qualifier is worse than a stale label:
    // the number is wrong and looks plausible.
    //
    // The registry loop could only ever drop what the registry still named,
    // so a global belonging to a graph whose name had left the registry
    // survived indefinitely.  A prefix sweep has neither problem and needs
    // no maintenance when a new per-graph global is added.
    //
    // These five prefixes are dash's own namespace.  A user global that
    // happens to start with one of them is not distinguishable from dash's
    // and is cleared too; that is what `dash clear' means.
    //
    // The dash_max_* globals are deliberately NOT swept, and none of the
    // patterns here matches them.  They are the session's resource limits
    // (WP-19) -- settings the user chose, like $dash_nobrowser -- not
    // registry state: a do-file that raises dash_max_graphs once and runs
    // `dash clear' between dashboards must keep the limit it set.
    capture macro drop dash_spec_*
    capture macro drop dash_json_*
    capture macro drop dash_opts_*
    capture macro drop dash_kpi_*
    capture macro drop dash_img_*
    capture macro drop dash_fpts_*
    capture macro drop dash_tu_*
    capture macro drop dash_frm_*

    capture macro drop dash_graph_registry
    // Leading-underscore globals, if any command ever sets one.
    capture macro drop _dash_*

    // The session's preview pages and stale run folders (WP-29 P0.14):
    // captured, so dash clear still clears the registry with no Python.
    capture _dash_tmp_clear

    display as text "dash: registry cleared."
end


// ================================================================
// _dash_kpi  — KPI subcommand
// ================================================================
program define _dash_kpi
    version 19

    // Rule 16: text reaching the spec must be well-formed UTF-8 BEFORE it
    // leaves Stata.  The gate was applied at exactly one entry point --
    // _dash_plot -- so KPI titles, build titles and subtitles, tabs() and
    // filter labels had no gate at all, and a malformed sequence in any of
    // them went straight to Python.
    mata: _dash_check_utf8(strtrim(st_local("0")))

    // WP-31 H2k: the weight classes summarize takes; a pweight is named
    // here so it is refused in summarize's words below, not syntax's.
    syntax anything(name=statspec) [if] [in] [aweight fweight iweight pweight] , ///
        TItle(string)           ///
        NAMe(string)            ///
        [ FMT(string)           ///
          SUBtitle(string)      ///
          COLOR(string)         ///
          BGCOLOR(string)       ///
          UPDate(string)        ///
        ]

    // The statistic may carry a point: p97.5 (below).  Read by value, in
    // Mata, in one statement so regexs() reads this match: expanded in the
    // expression, a statistic holding $name or `...' was read again for
    // macros and taken for what it expanded to -- mean(\$v) for mean(price)
    // (measured 24sep2026; test_json_escaping.cscript JSE-58).  Mata's own
    // ustrregexm/ustrregexs, not Stata's regexm/regexs, which follows the
    // caller's version (5629 below): ICU is the same engine whatever
    // version this program runs under.  The variable name accepts Unicode
    // letters (G5, WP-28: 2916's rule) and is capped at 32 characters,
    // checked once the match has already set _kst_ok and kpi_var so a
    // failed match never reaches ustrregexs().
    mata: st_local("_kst_ok", strofreal(ustrregexm(st_local("statspec"), ///
        "^([a-zA-Z0-9.]+)\(([\p{L}_][\p{L}\p{N}_]*)\)$"))); ///
        st_local("stat", st_local("_kst_ok") == "1" ? ustrregexs(1) : ""); ///
        st_local("kpi_var", st_local("_kst_ok") == "1" ? ustrregexs(2) : ""); ///
        st_local("_kst_ok", strofreal(st_local("_kst_ok") == "1" & ///
            ustrlen(st_local("kpi_var")) <= 32))
    if !`_kst_ok' {
        display as error "dash kpi: syntax is stat(varname), e.g. mean(mpg)."
        exit(198)
    }

    local valid_stats "mean sum count dcount min max median sd var cv iqr skewness kurtosis semean range p25 p50 p75"
    // p# for any percentile Stata's _pctile computes -- p10, p97.5, p0.5 --
    // not only the three in the list.  Measured at 4ede074, p97.5 stopped at
    // the pattern above, which had no point in it, and the rule here read
    // whole numbers from 1 to 99 only, although the help promised p97.5 and
    // both renderers compute it.  _dash_kpi_pctile reads the number byte by
    // byte, keeps it to what _pctile accepts (greater than 0, less than 100)
    // and to 15 digits, and writes it once, so p097.50 is stored, echoed and
    // rendered as p97.5 (test_help_claims_4.cscript HC4-01..07).
    mata: _dash_kpi_pctile(st_local("stat"), "_pct_num", "_pct_why")
    // Any echo of the statistic is bounded: it holds only letters, digits
    // and points here, but it may be as long as a command line.
    mata: st_local("_stat_safe", usubstr(st_local("stat"), 1, 40) + ///
        (strlen(st_local("stat")) > 40 ? "..." : ""))
    if "`_pct_why'" == "form" {
        display as error "dash kpi: '`_stat_safe'' is not a percentile. " ///
            "Write p# with # a decimal number greater than 0 and less " ///
            "than 100, such as p97.5."
        exit(198)
    }
    if "`_pct_why'" == "digits" {
        display as error "dash kpi: the percentile in '`_stat_safe'' has " ///
            "more than 15 digits."
        exit(198)
    }
    if "`_pct_why'" == "range" {
        display as error "dash kpi: percentile must be greater than 0 and " ///
            "less than 100, as _pctile requires (got '`_stat_safe'')."
        exit(198)
    }
    local is_pctile = ("`_pct_why'" == "ok")
    if `is_pctile' local stat "p`_pct_num'"
    if !`: list stat in valid_stats' & !`is_pctile' {
        display as error "dash kpi: unsupported statistic '`_stat_safe''. " ///
            "Choose from: `valid_stats', or p# for any percentile."
        exit(198)
    }

    confirm variable `kpi_var'

    // WP-31 H2k: the weight, as summarize takes it (measured,
    // scripts/extract_kpi_weights_truth.do).  summarize refuses a pweight,
    // r(101) "pweights not allowed", and summarize, detail and tabstat an
    // iweight, r(101) "iweights not allowed" -- so an iweight goes only
    // with the statistics plain summarize returns.  The weight is a
    // variable, which the page carries as a column: dash evaluates no
    // expression.  A string weight is refused by syntax above, r(109)
    // "type mismatch"; a negative or noninteger frequency weight by
    // summarize itself, below, in its words.
    local _kw ""
    if "`weight'" != "" {
        if "`weight'" == "pweight" {
            display as error "pweights not allowed"
            exit 101
        }
        // syntax returns exp as "= weight", a blank after the =; read by
        // value, in Mata, so the text is never expanded.
        mata: st_local("_kw", strtrim(substr(st_local("exp"), 2, .)))
        mata: st_local("_kw_ok", strofreal(ustrregexm(st_local("_kw"), ///
            "^[\p{L}_][\p{L}\p{N}_]*$") & ustrlen(st_local("_kw")) <= 32))
        if `_kw_ok' {
            // An abbreviation, as summarize takes one, written out: the
            // page's column is the variable's own name.
            capture unab _kwf : `_kw', max(1)
            if _rc local _kw_ok 0
            else local _kw : copy local _kwf
        }
        if `_kw_ok' {
            capture confirm numeric variable `_kw', exact
            if _rc local _kw_ok 0
        }
        if !`_kw_ok' {
            mata: _dash_say("err", "dash kpi: the weight must be a " + ///
                "variable name; dash does not evaluate '", ///
                usubstr(st_local("_kw"), 1, 40) + ///
                (ustrlen(st_local("_kw")) > 40 ? "..." : ""), "'.")
            exit 198
        }
        // The statistics summarize computes with an iweight; a family list,
        // as a string inlist() takes at most ten arguments.
        local _kpi_iw "mean sum count dcount min max sd var cv range"
        if "`weight'" == "iweight" & !`: list stat in _kpi_iw' {
            display as error "iweights not allowed"
            exit 101
        }
        // summarize proves the weights as it would for the statistic:
        // negative weights r(402), a noninteger fweight r(401).
        quietly summarize `_kw' `macval(if)' `macval(in)' [`weight'=`_kw']
    }
    local _kwc = cond("`_kw'" == "", "", "[`weight'=`_kw']")

    // count and dcount take a string variable -- its non-missing and its
    // distinct values -- and every other statistic needs a number.  A
    // string used to pass: summarize skips it, so mean(make) was stored as
    // "." and drawn as ".", and count(make) was stored as 0 while the card
    // counted every value, empty strings included (measured 23sep2026).
    capture confirm numeric variable `kpi_var'
    if _rc & !inlist("`stat'", "count", "dcount") {
        display as error "dash kpi: `stat'() needs a numeric variable; " ///
            "`kpi_var' is a string.  Only count() and dcount() take a " ///
            "string variable."
        exit(109)
    }

    // Split off a ", replace" sub-option BEFORE validating the name, by the
    // rule the graph registrar applies: syntax's name(string) captures the
    // whole of "k1, replace", which would then fail the name regex below.
    // This program kept a copy of that rule's regex; it reads name() through
    // _dash_name_split now, so one rule reads it for a graph and a KPI card
    // alike, and its flag is the only word on replace
    // (test_registry_collision.cscript REG-35, REG-36).
    //
    // name() is read by value.  name[, replace] is made of letters,
    // digits, _, blanks and a comma, and a text holding anything else is
    // refused below as the name it is not -- before _dash_name_split, which
    // takes its text as an argument, reads it: expanded in the name check,
    // name(`"q"7"') stopped here with r(303) "equation [a-zA-Z_] not
    // found", and name(\$m) was read again for macros and registered under
    // whatever $m held (measured 24sep2026; test_json_escaping.cscript
    // JSE-58).  twoway refuses a name holding a quote, r(198) (measured).
    mata: st_local("_nm_raw_ok", ///
        strofreal(!ustrregexm(st_local("name"), "[^A-Za-z0-9_, \t]")))
    local replace_flag 0
    if `_nm_raw_ok' {
        _dash_name_split `"`name'"' _nm replace_flag
        local name `"`_nm'"'
    }

    // The graph registrar's rule, without bounded repetition (see there).
    // A KPI's longest globals are its fields, dash_kpi_<name>__<field> with
    // a field of three letters (_dash_kpi_fields in dash_parse.mata): 14
    // characters around the name, so its limit is 18.
    mata: st_local("_nm_ok", strofreal(st_local("_nm_raw_ok") == "1" & ///
        regexm(st_local("name"), "^[a-zA-Z_][a-zA-Z0-9_]*$") & ///
        strlen(st_local("name")) <= 18))
    if !`_nm_ok' {
        // Echoed as text, as the graph registrar does (see there).
        mata: st_local("_name_safe", ustrregexra(usubstr( ///
            st_local("name"), 1, 40), "[^A-Za-z0-9_.\-]", "?"))
        display as error "dash kpi: invalid name '`_name_safe''. " ///
            "Names must start with a letter or underscore, contain only " ///
            "letters, digits, and underscores, and be at most 18 characters."
        exit(198)
    }
    // Two underscores in a row are dash's own, as for a graph (see there).
    if strpos("`name'", "__") {
        mata: _dash_say("err", "dash kpi: name '", st_local("name"), ///
            "' holds two underscores in a row, which dash keeps for the " + ///
            "names it generates, such as a by() graph's panels. " + ///
            "Choose a name without __.")
        exit(198)
    }
    // _all is link()'s word for every graph, as for a graph (see there).
    if "`name'" == "_all" {
        display as error "dash kpi: name '_all' is the word link(_all) " ///
            "uses for every graph. Choose another name."
        exit(198)
    }

    // Every option is proven BEFORE anything is retired: measured
    // 22sep2026, `name(k, replace) fmt(bogus)' was refused correctly but
    // had already dropped the old KPI's globals while the registry still
    // listed k, and the next `dash build' died on the corrupt registry
    // with a JSON traceback (update(bogus) did the same).
    //
    // update() is read by value: compared inside quotes, update(`"a"b"')
    // stopped with r(132) "too few quotes" and update(`"filter" name(x)"')
    // with r(109) "type mismatch", and update(\$m) was taken for whatever
    // $m held (measured 24sep2026; test_json_escaping.cscript JSE-55,
    // JSE-58).
    local _ulen : length local update
    if `_ulen' == 0 local update "filter"
    mata: st_local("_upd_ok", ///
        strofreal(anyof(("filter", "brush", "both"), st_local("update"))))
    if !`_upd_ok' {
        display as error "dash kpi: update() must be filter, brush, or both."
        exit(198)
    }
    // fmt() is proven a single numeric display format here, before any
    // computation, so `: display' below can stay the formatter (WP-15).
    // Measured by length and handed over through macval(), so a fmt(\$m)
    // is judged as the text it is, not as what $m holds (JSE-58).  In a
    // block: the one-line form `if exp command' expands its command a
    // second time, and macval() protects only the first -- measured
    // 24sep2026, fmt(\$m) reached the validator as %9.2f that way.
    local _fmlen : length local fmt
    if `_fmlen' > 0 {
        _dash_validate_value "dash kpi" "fmt" "format" `"`macval(fmt)'"' ""
    }

    // Graphs and KPIs share ONE registry and one namespace.
    // _dash_register_graph has always refused a duplicate unless replace was
    // given; this program checked nothing, so a KPI could quietly take a
    // name a graph already held -- and then win it, because the build's
    // graph loop passes over any entry carrying a KPI marker.  Measured:
    //     dash scatter mpg weight, name(g1)
    //     dash kpi mean(mpg), name(g1) title("Avg")
    //     dash build, saving(out.html) replace
    // returned rc 0 at every step, said nothing, and wrote a dashboard with
    // the KPI's text and no graph at all.  A second KPI of the same name
    // overwrote the first just as quietly.
    local _kpi_registry = "${dash_graph_registry}"
    local _kpi_already  = 0
    local _kpi_ntok : word count `_kpi_registry'
    forvalues k = 1/`_kpi_ntok' {
        if "`:word `k' of `_kpi_registry''" == "`name'" local _kpi_already = 1
    }
    if `_kpi_already' == 1 & `replace_flag' == 0 {
        display as error "dash kpi: name '`name'' already exists. " ///
            "Use name(`name', replace) to overwrite."
        exit(198)
    }
    // WP-19: the same registry limit as a graph, checked before any global
    // is set or retired and before the statistic is computed.  A KPI
    // replacing a registered name never counts.
    _dash_graph_cap `_kpi_already'
    // Retire whatever held the name before, so the entry does not end up
    // carrying a graph's JSON and a KPI's marker at the same time.
    if `_kpi_already' == 1 {
        _dash_drop_item "`name'"
    }

    // The qualifier is handed to each command through macval(), as typed:
    // expanded plainly, it was read again for macros, so if make !=
    // "\$m" was computed as make != <whatever $m held> while Stata's own
    // summarize, given the same line, compares make with the text $m
    // (measured 24sep2026; test_json_escaping.cscript JSE-58).
    local kpi_value ""

    // WP-31 H2k: under a weight every summarize and _pctile below takes
    // it (`_kwc'), and a missing or zero weight drops its observation.
    if inlist("`stat'", "mean", "sum", "min", "max", "sd", "range", "semean") {
        quietly summarize `kpi_var' `macval(if)' `macval(in)' `_kwc'
        if      "`stat'" == "mean"  local kpi_value = r(mean)
        else if "`stat'" == "sum"   local kpi_value = r(sum)
        else if "`stat'" == "min"   local kpi_value = r(min)
        else if "`stat'" == "max"   local kpi_value = r(max)
        else if "`stat'" == "sd"    local kpi_value = r(sd)
        else if "`stat'" == "range" local kpi_value = r(max) - r(min)
        // tabstat's se(mean): r(sd)/sqrt(r(N)), r(N) the sum of an
        // fweight and the observation count otherwise (measured).
        else if "`stat'" == "semean" local kpi_value = r(sd) / sqrt(r(N))
    }
    else if "`stat'" == "count" {
        // The non-missing values, as count if !missing() counts them: for a
        // number that is summarize's r(N), and a string, which summarize
        // skips, has its values that are not "" counted too.  Under a
        // weight, summarize's r(N) of that marker: an fweight's sum, else
        // the observations the weight keeps.
        tempvar _dash_nm
        quietly generate byte `_dash_nm' = !missing(`kpi_var') `macval(if)' `macval(in)'
        if "`_kw'" == "" {
            quietly count if `_dash_nm' == 1
        }
        else {
            quietly summarize `_dash_nm' if `_dash_nm' == 1 `_kwc'
        }
        local kpi_value = r(N)
    }
    else if "`stat'" == "dcount" {
        // codebook is NOT r-class: r(unique) is always missing, so this
        // statistic has never produced a value.  Measured alternatives:
        // inspect gives r(N_unique) but stops reporting at 100 distinct and
        // is numeric-only; tabulate dies at 200k distinct; levelsof fails
        // once r(levels) exceeds c(macrolen).  egen group() has no ceiling,
        // works for string and numeric alike, and was the fastest measured.
        // A weight is not used, but its missing and zero weights drop
        // their observations, as summarize drops them (WP-31 H2k).
        tempvar _dash_grp
        quietly egen `_dash_grp' = group(`kpi_var') `macval(if)' `macval(in)'
        if "`_kw'" != "" {
            quietly replace `_dash_grp' = . if missing(`_kw') | `_kw' == 0
        }
        quietly summarize `_dash_grp', meanonly
        local kpi_value = cond(r(N) == 0, 0, r(max))
    }
    else if "`stat'" == "median" {
        quietly _pctile `kpi_var' `macval(if)' `macval(in)' `_kwc', p(50)
        local kpi_value = r(r1)
    }
    else if "`stat'" == "iqr" {
        quietly _pctile `kpi_var' `macval(if)' `macval(in)' `_kwc', p(25 75)
        local kpi_value = r(r2) - r(r1)
    }
    else if `is_pctile' {
        // Any percentile, not the three p(25 50 75) was frozen at.  The
        // number as _dash_kpi_pctile wrote it, which is the text the
        // renderers parse, so all three read the same double.
        quietly _pctile `kpi_var' `macval(if)' `macval(in)' `_kwc', p(`_pct_num')
        local kpi_value = r(r1)
    }
    else if inlist("`stat'", "var", "cv") {
        // Plain summarize, which takes an iweight (detail does not).
        quietly summarize `kpi_var' `macval(if)' `macval(in)' `_kwc'
        if      "`stat'" == "var"      local kpi_value = r(Var)
        else if "`stat'" == "cv"       local kpi_value = cond(r(mean)==0, ., r(sd)/r(mean))
    }
    else if inlist("`stat'", "skewness", "kurtosis") {
        quietly summarize `kpi_var' `macval(if)' `macval(in)' `_kwc', detail
        if      "`stat'" == "skewness" local kpi_value = r(skewness)
        else if "`stat'" == "kurtosis" local kpi_value = r(kurtosis)
    }

    local kpi_display = "`kpi_value'"
    if `_fmlen' > 0 {
        local kpi_display : display `fmt' `kpi_value'
        local kpi_display = strtrim("`kpi_display'")
    }

    // Store each KPI field in its own global so multi-word titles/subtitles
    // are preserved.  A marker global (value "1") allows the registry to
    // detect that this name is a KPI rather than a graph.
    //
    // The fields are dash_kpi_<name>__<field>, two underscores, and are the
    // fields _dash_kpi_fields() in dash_parse.mata lists -- the list
    // _dash_item_globals retires.  With one underscore, dash_kpi_a_stat,
    // KPI a's statistic was the marker of any item named a_stat: measured
    // 23sep2026 at 9f48cf7, a graph a_stat beside KPI a was drawn as a
    // blank KPI card and no figure, and a KPI a_stat set KPI a's statistic
    // to "1".  No name may hold two underscores in a row (above), so no
    // name reaches these.
    global dash_kpi_`name'       "1"
    global dash_kpi_`name'__sta  "`stat'"
    global dash_kpi_`name'__var  "`kpi_var'"
    global dash_kpi_`name'__val  "`kpi_value'"
    global dash_kpi_`name'__dsp  "`kpi_display'"
    global dash_kpi_`name'__upd  "`update'"
    // WP-31 H2k: the weight's class and variable; empty, no global.
    global dash_kpi_`name'__wgt  "`weight'"
    global dash_kpi_`name'__wex  "`_kw'"
    // The user's text is stored by value, from Mata.  global ... "`title'"
    // read it again for macros -- A\$g B \`=1+1' C was stored as "A<what $g
    // held> B 2 C", and a \`=filewrite(...)' in a title wrote a file -- and
    // the qualifier was cut where a "' closed the compound quotes it was
    // put in: if make == "' or 1 or '" was stored as "make ==", and the
    // saved page, finding no qualifier it could read, showed the
    // unconditional mean, 6165.26, where Stata's summarize gives .
    // (measured 24sep2026; test_json_escaping.cscript JSE-51, JSE-58).
    mata: st_global("dash_kpi_" + st_local("name") + "__fmt", st_local("fmt"))
    mata: st_global("dash_kpi_" + st_local("name") + "__tit", st_local("title"))
    mata: st_global("dash_kpi_" + st_local("name") + "__sub", st_local("subtitle"))
    mata: st_global("dash_kpi_" + st_local("name") + "__col", st_local("color"))
    mata: st_global("dash_kpi_" + st_local("name") + "__bg",  st_local("bgcolor"))
    // The KPI's own if/in.  Stata computes the right value above and
    // stores it, but the renderer recomputes from the full frame, so
    // without these `dash kpi mean(mpg) if foreign==1` displayed the
    // UNCONDITIONAL mean.
    // Its abbreviations written out, as a graph's are (QL-22).
    mata: st_global("dash_kpi_" + st_local("name") + "__if", ///
        _dash_qual_expand(strtrim(regexr(st_local("if"), "^[ ]*if[ ]+", ""))))
    mata: st_global("dash_kpi_" + st_local("name") + "__in", ///
        strtrim(regexr(st_local("in"), "^[ ]*in[ ]+", "")))

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
// _dash_image  — image panel subcommand (WP-33 33-06)
// ================================================================
// dash image using <file.svg>, name(<n>) [caption() alt() link(<page>.html)]
// registers an SVG picture that layout() and tabs() place like a KPI card.
// The file is checked here and again at build (_dash_image_check in
// dash_render.py): well-formed SVG with no script, event handler,
// foreignObject, DOCTYPE, entity or external reference.  Its bytes are
// never put in a global (c(macrolen) would bound them); the build reads
// the file.  No file is refused for its size (DECISIONS A-18); only the
// number of images is bounded, by $dash_max_images (_dash_image_cap).
program define _dash_image
    version 19
    mata: _dash_check_utf8(strtrim(st_local("0")))
    syntax using/ , NAMe(string) [CAPtion(string) ALT(string) LINK(string)]

    // name() by dash kpi's rules and bound (see _dash_kpi): an image's
    // longest globals, dash_img_<name>__lnk and its siblings, put 14
    // characters around the name, so it is at most 18 characters.
    mata: st_local("_nm_raw_ok", ///
        strofreal(!ustrregexm(st_local("name"), "[^A-Za-z0-9_, \t]")))
    local replace_flag 0
    if `_nm_raw_ok' {
        _dash_name_split `"`name'"' _nm replace_flag
        local name `"`_nm'"'
    }
    mata: st_local("_nm_ok", strofreal(st_local("_nm_raw_ok") == "1" & ///
        regexm(st_local("name"), "^[a-zA-Z_][a-zA-Z0-9_]*$") & ///
        strlen(st_local("name")) <= 18))
    if !`_nm_ok' {
        mata: st_local("_name_safe", ustrregexra(usubstr( ///
            st_local("name"), 1, 40), "[^A-Za-z0-9_.\-]", "?"))
        display as error "dash image: invalid name '`_name_safe''. " ///
            "Names must start with a letter or underscore, contain only " ///
            "letters, digits, and underscores, and be at most 18 characters."
        exit(198)
    }
    if strpos("`name'", "__") {
        mata: _dash_say("err", "dash image: name '", st_local("name"), ///
            "' holds two underscores in a row, which dash keeps for the " + ///
            "names it generates, such as a by() graph's panels. " + ///
            "Choose a name without __.")
        exit(198)
    }
    if "`name'" == "_all" {
        display as error "dash image: name '_all' is the word link(_all) " ///
            "uses for every graph. Choose another name."
        exit(198)
    }

    // The file, read by value: a missing file in Stata's words, r(601).
    mata: st_local("_im_path", _dash_abs_path(st_local("using"), c("pwd"), c("os")))
    mata: st_local("_im_ex", strofreal(fileexists(st_local("_im_path"))))
    if `_im_ex' != 1 {
        mata: _dash_say("err", "file ", st_local("using"), " not found")
        exit 601
    }
    // The SVG check, from the renderer: "" or "<rc> <text>".
    _dash_require_python
    _dash_xm_load
    python: import sys
    python: from sfi import Macro as _dash_M
    python: _dash_xm = sys.modules["_dash_render_export"]
    python: _dash_M.setLocal("_im_err", _dash_xm._dash_image_check(_dash_M.getLocal("_im_path")))
    local _im_elen : length local _im_err
    if `_im_elen' > 0 {
        mata: st_local("_im_rc", substr(st_local("_im_err"), 1, 3)); ///
            st_local("_im_err", substr(st_local("_im_err"), 5, .))
        mata: _dash_say("err", "", st_local("_im_err"), "")
        exit `_im_rc'
    }
    // link(): the file name of a page in the same folder, by the rule the
    // page's markup applies (_dash_image_link_ok); the text is not echoed.
    local _im_llen : length local link
    if `_im_llen' > 0 {
        python: _dash_M.setLocal("_im_lok", "1" if _dash_xm._dash_image_link_ok(_dash_M.getLocal("link")) else "0")
        if "`_im_lok'" != "1" {
            display as error "dash image: link() takes the file name of a " ///
                "page in the same folder: letters, digits, _ or -, then .html."
            exit 198
        }
    }

    // The registry, shared with graphs and KPI cards (see _dash_kpi).
    local _im_registry = "${dash_graph_registry}"
    local _im_already  = 0
    local _im_isimg    = 0
    local _im_ntok : word count `_im_registry'
    forvalues k = 1/`_im_ntok' {
        if "`:word `k' of `_im_registry''" == "`name'" local _im_already = 1
    }
    if `_im_already' == 1 & `replace_flag' == 0 {
        display as error "dash image: name '`name'' already exists. " ///
            "Use name(`name', replace) to overwrite."
        exit(198)
    }
    if `_im_already' == 1 & "${dash_img_`name'}" == "1" local _im_isimg = 1
    _dash_image_cap `_im_isimg'
    if `_im_already' == 1 {
        _dash_drop_item "`name'"
    }

    // alt() defaults to the caption, else the name.  Every field by value.
    mata: st_local("alt", st_local("alt") != "" ? st_local("alt") : ///
        (st_local("caption") != "" ? st_local("caption") : st_local("name")))
    global dash_img_`name' "1"
    mata: st_global("dash_img_" + st_local("name") + "__pth", st_local("_im_path"))
    mata: st_global("dash_img_" + st_local("name") + "__cap", st_local("caption"))
    mata: st_global("dash_img_" + st_local("name") + "__alt", st_local("alt"))
    mata: st_global("dash_img_" + st_local("name") + "__lnk", st_local("link"))

    if `_im_already' == 0 {
        if "${dash_graph_registry}" == "" global dash_graph_registry "`name'"
        else global dash_graph_registry "${dash_graph_registry} `name'"
    }
    display as text "dash: image '`name'' registered."
end


// ================================================================
// Graphs from several frames (WP-33 33-07, P4-4, P4-7)
// ================================================================
// A graph registered under Stata's own prefix, frame f: dash ...,
// name(g), is drawn from frame f, as frame f: twoway ... draws from it;
// _dash_register_graph records the frame in dash_frm_<g>.  dash never
// changes the working frame: every command that reads another frame runs
// under the frame prefix, which gives the frame back when it fails.
//
// _dash_frames_plan <cmdname> <link>  (rclass) -- the build's frames.
// r(multi) is 0 when every graph was registered in the frame dash build
// runs in (a graph with no dash_frm_<g> counts as that frame): the build
// is then exactly as before.  r(frames) lists the frames in the order the
// stack is made, the build's own first when a graph or KPI uses it;
// r(of_<k>) is registry entry k's frame.  Refused: a graph whose frame is
// gone (Stata's "frame <f> not found", r(111), naming the graph), and a
// link() group joining graphs of two frames (r(198)).
program define _dash_frames_plan, rclass
    version 19
    args cmdname link
    local reg "${dash_graph_registry}"
    local cur = c(frame)
    local multi 0
    local frames ""
    local n : word count `reg'
    local _own 0
    forvalues k = 1/`n' {
        local g : word `k' of `reg'
        if "${dash_img_`g'}" == "1" {
            return local of_`k' "`cur'"
            continue
        }
        if "${dash_kpi_`g'}" == "1" {
            local _own 1
            return local of_`k' "`cur'"
            continue
        }
        mata: st_local("_f", st_global("dash_frm_" + st_local("g")))
        if `"`_f'"' == "" local _f "`cur'"
        if "`_f'" == "`cur'" local _own 1
        else {
            local multi 1
            capture confirm frame `_f'
            if _rc {
                mata: _dash_say("err", "frame ", st_local("_f"), " not found")
                mata: _dash_say("err", "`cmdname': graph ", st_local("g"), ///
                    " was registered in frame " + st_local("_f") + ".")
                exit 111
            }
            if !`: list _f in frames' local frames `frames' `_f'
        }
        local _of_`k' "`_f'"
        return local of_`k' "`_f'"
    }
    if `_own' local frames `cur' `frames'
    if `multi' {
        local _lklen : length local link
        if `_lklen' > 0 {
            mata: st_local("_lkg", strofreal(cols(_dash_link_split(st_local("link")))))
            forvalues j = 1/`_lkg' {
                mata: st_local("_lkw", invtokens(_dash_blank_words(_dash_link_split(st_local("link"))[`j'])))
                if "`_lkw'" == "_all" local _lkw `reg'
                local _lkf ""
                foreach _lg of local _lkw {
                    local _lk : list posof "`_lg'" in reg
                    if `_lk' == 0 continue
                    if "${dash_kpi_`_lg'}" == "1" | "${dash_img_`_lg'}" == "1" continue
                    if "`_lkf'" == "" local _lkf "`_of_`_lk''"
                    else if "`_of_`_lk''" != "`_lkf'" {
                        mata: _dash_say("err", "`cmdname': link() joins graphs from frames ", ///
                            st_local("_lkf") + " and " + st_local("_of_`_lk'"), ///
                            "; a link group draws from one frame")
                        exit 198
                    }
                }
            }
        }
    }
    return local multi "`multi'"
    return local frames "`frames'"
end

// _dash_frames_one <cmdname> <file> <q> <s> <t> <w> <prefix>  -- one frame's part of the stack,
// run as frame <f>: _dash_frames_one ...  In a preserved copy of the
// frame: the frame's own qualifier, join-order, time-series and weight
// columns, made from its own rows, tsset and sort order; then each
// variable its graphs use that an earlier frame holds differently
// renamed to its split column <prefix>m<k> (DECISIONS A-23), each value
// label whose name an earlier frame used for other contents moved to its
// copy <prefix>l<j>, and every label set no kept variable uses dropped (so
// append never meets a set of one name and two contents); the kept
// variables and the made columns saved to <file>.  The preserve gives the
// frame back as it was.  The made and split columns come back in the
// caller's locals.  WP-35 DT-19: prefix is the build's working-column
// prefix; when the frame has no room for the columns beside its own
// variables they are made in a temporary frame put from it holding only
// the variables the export reads (_dash_maxvar_room's plan).
program define _dash_frames_one
    version 19
    args cmdname file _dq_n _ds_n _dts_n _dwx_n prefix
    if "`prefix'" == "" local prefix "__dash"
    local F = c(frame)
    mata: st_local("_keep", _dash_frames_keep_of(st_local("F")))
    // Each time-series column's base, whose label and format name the
    // column (_dash_tsop_meta).
    local _dts_n = 0
    mata: _dash_tsop_export()
    forvalues k = 1/`_dts_n' {
        if "`_dts_f`k''" != "`F'" continue
        local _b = substr("`_dts_e`k''", strpos("`_dts_e`k''", ".") + 1, .)
        if !`: list _b in _keep' local _keep `_keep' `_b'
    }
    // WP-31 G3d in each frame: the build's working columns (every frame's,
    // so never fewer than this frame makes) counted against the room this
    // frame's c(maxvar) leaves, before the first is made; WP-35 DT-19:
    // beside the variables this frame exports when its own leave none.
    _dash_frame_vars `prefix' `F' `_keep'
    _dash_maxvar_room `_dq_n' `_ds_n' `_dts_n' `_dwx_n' "`cmdname'" `_mv_kx' `F'
    local _dash_fr_qual ""
    local _dash_fr_split ""
    if "`_mv_plan'" == "frame" {
        tempname _dash_xf
        _dash_frame_put `_dash_xf' `_mv_vars'
        capture noisily frame `_dash_xf': _dash_frames_part "`cmdname'" "`file'" "`F'" "`prefix'" `_keep'
        local rc = _rc
        capture frame drop `_dash_xf'
        if `rc' exit `rc'
    }
    else {
        preserve
        _dash_frames_part "`cmdname'" "`file'" "`F'" "`prefix'" `_keep'
    }
    c_local _dash_fr_qual "`_dash_fr_qual'"
    c_local _dash_fr_split "`_dash_fr_split'"
end

// _dash_frames_part <cmdname> <file> <F> <prefix> <keep>  -- the body of
// _dash_frames_one, run on the data in memory: frame F's own columns
// (its entries of the tables), its split columns and label copies, the
// kept variables and the made columns saved to <file>.  The data are a
// preserved copy of F, or a temporary frame put from it (WP-35 DT-19).
program define _dash_frames_part
    version 19
    gettoken cmdname 0 : 0
    gettoken file 0 : 0
    gettoken F 0 : 0
    gettoken prefix 0 : 0
    local _keep `0'
    local _dash_qual_vars ""
    local _dash_sort_vars ""
    local _dash_tsop_vars ""
    local _dash_wexp_vars ""
    _dash_qual_gen "`cmdname'" "`F'" "`prefix'"
    _dash_sort_gen "`cmdname'" "`F'" "`prefix'"
    _dash_tsop_gen "`cmdname'" "`F'" "`prefix'"
    _dash_wexp_gen "`cmdname'" "`F'" "`prefix'"
    local _out ""
    local _split ""
    foreach v of local _keep {
        confirm variable `v', exact
        mata: st_local("_col", _dash_frames_take(st_local("F"), st_local("v")))
        if "`_col'" != "" {
            rename `v' `_col'
            local _out `_out' `_col'
            local _split `_split' `_col'
        }
        else local _out `_out' `v'
    }
    local _made `_dash_qual_vars' `_dash_sort_vars' `_dash_tsop_vars' `_dash_wexp_vars'
    quietly keep `_out' `_made'
    // The value-label sets: each kept variable's, under a name no other
    // frame used for other contents.
    local _used ""
    foreach v of varlist _all {
        local _vl : value label `v'
        if "`_vl'" == "" continue
        mata: st_local("_nl", _dash_frames_lset(st_local("_vl")))
        if "`_nl'" != "" {
            capture label list `_nl'
            if _rc label copy `_vl' `_nl'
            label values `v' `_nl'
            local _vl `_nl'
        }
        if !`: list _vl in _used' local _used `_used' `_vl'
    }
    quietly label dir
    local _all_l `r(names)'
    local _drop : list _all_l - _used
    if "`_drop'" != "" label drop `_drop'
    quietly save "`file'", replace
    c_local _dash_fr_qual "`_dash_qual_vars'"
    c_local _dash_fr_split "`_split'"
end

// _dash_frames_stack <cmdname> <stack> <frames> <q> <s> <t> <w> <prefix>  -- the build's data from
// every frame of the plan, in its order, appended into the frame <stack>
// (a tempname of the caller's, dropped when the caller ends): each frame's
// part made by _dash_frames_one in that frame, each qualifier column 0 on
// every other frame's rows.  The working columns come back in the
// caller's locals in column-number order, the split columns in k order.
program define _dash_frames_stack
    version 19
    // prefix (WP-35 DT-19): the build's working-column prefix.
    args cmdname stack frames nq ns nt nw prefix
    if "`prefix'" == "" local prefix "__dash"
    local _qall ""
    local _sall ""
    local _i 0
    foreach F of local frames {
        local ++_i
        tempfile _fp`_i'
        local _dash_fr_qual ""
        local _dash_fr_split ""
        frame `F': _dash_frames_one "`cmdname'" "`_fp`_i''" `nq' `ns' `nt' `nw' `prefix'
        local _qall `_qall' `_dash_fr_qual'
        local _sall `_sall' `_dash_fr_split'
    }
    frame create `stack'
    forvalues j = 1/`_i' {
        if `j' == 1 frame `stack': quietly use "`_fp`j''", clear
        else {
            frame `stack': local _off`j' = _N
            frame `stack': quietly append using "`_fp`j''"
        }
    }
    local _off1 0
    frame `stack': local _offend = _N
    foreach q of local _qall {
        frame `stack': quietly replace `q' = 0 if missing(`q')
    }
    // A join-order column holds each frame's ranks on its own rows; the
    // renderers take it as distinct whole numbers over every row, so a
    // frame's ranks are moved past the rows above it, and a row of a frame
    // that does not rank by it takes its row number.  The order within a
    // frame, the only order a graph reads, is unchanged.
    capture frame `stack': unab _sv_all : `prefix's*
    if !_rc {
        foreach sv of local _sv_all {
            forvalues j = 1/`_i' {
                local _a = `_off`j'' + 1
                local _jn = `j' + 1
                local _b = cond(`j' < `_i', "`_off`_jn''", "`_offend'")
                if `_a' > `_b' continue
                frame `stack': quietly replace `sv' = `sv' + `_off`j'' in `_a'/`_b' if !missing(`sv')
            }
            frame `stack': quietly replace `sv' = _n if missing(`sv')
        }
    }
    // Every column the table holds, in column-number order: each is made
    // in the frames its entries name.
    local _dq_n = 0
    mata: _dash_qual_export()
    local _ds_n = 0
    mata: _dash_sort_export()
    local _dts_n = 0
    mata: _dash_tsop_export()
    local _dwx_n = 0
    mata: _dash_wexp_export()
    local _qv ""
    forvalues k = 1/`_dq_n' {
        local _qv `_qv' `prefix'q`k'
    }
    local _sv ""
    forvalues k = 1/`_ds_n' {
        local _sv `_sv' `prefix's`k'
    }
    local _tv ""
    forvalues k = 1/`_dts_n' {
        local _tv `_tv' `prefix't`k'
    }
    local _wv ""
    forvalues k = 1/`_dwx_n' {
        local _wv `_wv' `prefix'w`k'
    }
    local _sall : list uniq _sall
    local _sord ""
    forvalues k = 1/99999 {
        if !`: list posof "`prefix'm`k'" in _sall' continue, break
        local _sord `_sord' `prefix'm`k'
    }
    c_local _dash_qual_vars "`_qv'"
    c_local _dash_sort_vars "`_sv'"
    c_local _dash_tsop_vars "`_tv'"
    c_local _dash_wexp_vars "`_wv'"
    c_local _dash_split_vars "`_sord'"
    mata: st_local("_map", _dash_frames_cols_json())
    c_local _dash_fcols_map `"`_map'"'
end


// ================================================================
// _dash_build  — build dashboard
// ================================================================
// ================================================================
// _dash_prepare_spec  — everything `dash build' and `dash serve' do
// before they hand the spec to Python: validate the build options,
// work out which variables have to be serialized, write them, and
// assemble the master JSON.
//
// WHY THIS PROGRAM EXISTS
//
// There were two copies of this, and they had drifted.  `dash build'
// carried every option the user gave it.  `dash serve' declared three
// options -- port(), nobrowser(), timeout() -- and wrote build_options
// that were literal constants:
//
//     "layout":"auto","link":"","filter":"","theme":"","title":"","subtitle":""
//
// with no scheme, tabs or filter_position key present at all.  So
// `dash serve' could not be given a filter and could not inherit one,
// which means the live server -- whose entire selling point is that a
// filter recomputes aggregates rather than masking precomputed ones --
// could never have a filter in it.  dash.sthlp documents the sequence
//
//     . dash build, saving(dashboard.html) filter(foreign, type(dropdown)) replace
//     . * -- or launch live server (filter recomputes aggregates) --
//     . dash serve, port(5006)
//
// which produced a served dashboard with no filter and no message.
//
// The caller owns the paths: specpath() and datapath() come in from the
// caller rather than being created here -- _dash_build's private run
// folder (WP-29 P0.12b), or a test seam's own files.
//
// The option list below is the full build surface.  It is repeated in
// `_dash_build' and `_dash_serve' because each of those also has
// options of its own; test_serve_options.py asserts the three lists
// agree, so they cannot drift again the way these two did.
// ================================================================
program define _dash_prepare_spec, rclass
    version 19

    // Rule 16: text reaching the spec must be well-formed UTF-8 BEFORE it
    // leaves Stata.  The gate was applied at exactly one entry point --
    // _dash_plot -- so KPI titles, build titles and subtitles, tabs() and
    // filter labels had no gate at all, and a malformed sequence in any of
    // them went straight to Python.
    mata: _dash_check_utf8(strtrim(st_local("0")))

    // filter() is taken out of the command here, by _dash_extract_filters,
    // which reads quotes -- the way dash build and dash serve take it out
    // of the user's command -- and not by -syntax-.  They hand it on as
    // filter(<the text as the user wrote it>).  It went in filter(`"..."'),
    // and a group holding "' closed that compound quote: label("'90s") was
    // lost, rc 0, and a label could put the rest of its text on this
    // command line as options -- label("') csv title(pwned) subtitle(")
    // titled the page "pwned" and turned the CSV download of every row on
    // (measured 24sep2026; test_json_escaping.cscript JSE-57).  FILTer()
    // stays declared, and never sees a value.
    mata: _dash_extract_filters("_filter_parts", "_cmd_nofilter")
    local 0 : copy local _cmd_nofilter
    // WP-31 H2l: link() may be given more than once, one link group a
    // copy; two or more are taken out here and joined with " || ".
    mata: _dash_extract_links("_link_parts", "_cmd_nolink")
    local _lkparts : length local _link_parts
    if `_lkparts' > 0 local 0 : copy local _cmd_nolink

    syntax [, ///
        CMDname(string)         ///
        SPECpath(string)        ///
        DATApath(string)        ///
        INHERIT                 ///
        FILTer(string)          ///
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
        CSV                     ///
        BRush(string)           ///
    ]
    local filter : copy local _filter_parts
    if `_lkparts' > 0 local link : copy local _link_parts

    if `"`cmdname'"' == "" local cmdname "dash build"

    // ---- inherit the preceding dash build's options ----
    //
    // Only what the user did not specify on this command.  An option
    // given here always wins; an option given on neither is empty, as
    // it was before.  Read through Mata rather than by expanding the
    // global inside quotes: these carry the user's own title() and
    // label() text, and expanding a value containing a double quote is
    // the failure this file has already been bitten by twice.  Kept by
    // copy: local `_bo' `"`_bo_val'"' read the value again for macros, so
    // an inherited title holding $m or `...' was expanded after all
    // (measured 24sep2026; test_json_escaping.cscript JSE-58).
    if "`inherit'" != "" {
        foreach _bo in title subtitle layout link theme scheme tabs filterposition filter csv brush {
            local _cur : length local `_bo'
            if `_cur' == 0 {
                mata: st_local("_bo_val", st_global("dash_opts_" + st_local("_bo")))
                local _bolen : length local _bo_val
                if `_bolen' > 0 local `_bo' : copy local _bo_val
            }
        }
    }

    // ---- check registry is not empty ----
    // saving(), replace and server describe writing a FILE.  That is what
    // `dash build' does and what `dash serve' does not -- dash.sthlp lists
    // serve's surface as port(), nobrowser(), timeout() and the dashboard
    // options, and none of these three is on it.  They arrive here through
    // the trailing * of _dash_serve_spec, are declared below for dash
    // build's sake, and were read by nobody, so
    //     . dash serve, saving(out.html)
    //     served a dashboard and wrote no file, in silence.
    //
    // The check lives HERE rather than in _dash_serve_spec because
    // test_serve_options.py requires that program to forward the build
    // surface untouched rather than enumerate it -- enumerating it is how
    // the two copies drifted apart in the first place.  This program already
    // declares all three, and already knows which command called it.
    if "`cmdname'" == "dash serve" {
        local _srv_na ""
        if `"`saving'"' != "" local _srv_na `"`_srv_na' saving()"'
        if "`replace'" != ""  local _srv_na `"`_srv_na' replace"'
        if "`server'"  != ""  local _srv_na `"`_srv_na' server"'
        if `"`_srv_na'"' != "" {
            mata: _dash_note("dash serve: ignoring option(s) that only apply to dash build:", st_local("_srv_na"), ". dash serve streams the dashboard and writes no file.")
        }
    }

    if "${dash_graph_registry}" == "" {
        display as error "`cmdname': no graphs registered. Define graphs with name() before running `cmdname'."
        exit(198)
    }
    local registry = "${dash_graph_registry}"

    // ---- validate layout ----
    local _llen : length local layout
    if `_llen' == 0 local layout "auto"
    if `"`layout'"' != "auto" {
        // Require strictly positive integers in "N M" grid layout.
        // ^[1-9][0-9]* rejects zero and leading-zero forms (e.g. "0 0", "0 2").
        if !regexm(`"`layout'"', "^[1-9][0-9]* [1-9][0-9]*$") & ///
           !regexm(`"`layout'"', "^[a-zA-Z_][a-zA-Z0-9_]*:[0-9]+,[0-9]+") & ///
           !regexm(lower(`"`layout'"'), "^bs") {
            display as error "`cmdname': layout() must be 'auto', 'N M' grid (N and M >= 1), 'name:row,col' placement, or 'bs[: name=span ...]' Bootstrap layout."
            exit(198)
        }

        // The whole value, not only its start.  A placement or Bootstrap
        // spec the renderer could not read, and a name the registry does
        // not hold, were handed on and drawn some other way, in silence:
        // measured at f2ecdd4, layout(p:1,1 junk) and layout(bs\) were
        // drawn as auto, layout(nosuch:1,1) was a 3 x 1 grid saved and
        // 1 x 2 served, and a Bootstrap span of 13 was clamped to 12
        // (P20-30).  A name must be in the registry, as link() and
        // exclude() require.  Read in Mata, by value; the refusal is
        // echoed through _dash_say.
        mata: st_local("_lref", _dash_layout_refusal(st_local("layout"), st_local("registry")))
        local _lreflen : length local _lref
        if `_lreflen' > 0 {
            mata: _dash_say("err", "`cmdname': ", st_local("_lref"), "")
            exit(198)
        }

        // The grid's size.  The saved page pads its grid out to rows x
        // cols cells before drawing it: measured 23sep2026, a 4000 x 4000
        // grid of two graphs peaked at 1.5 GB, and layout(99999 99999) --
        // ten billion cells -- could not finish.  No grid needs more cells
        // than a dashboard can hold graphs and KPI cards, so its cells are
        // held to the graphs limit.  _dash_layout_cells() is the
        // renderer's rule (dash_render.py's _dash_layout_cells), read in
        // Mata so the value is never expanded into an expression.
        mata: st_local("_lcells", strofreal(_dash_layout_cells(st_local("layout")), "%21.0f"))
        if "`_lcells'" != "." {
            _dash_limit, name(graphs)
            local _glim  = r(value)
            local _gceil = r(ceiling)
            if `_lcells' > `_glim' {
                _dash_count_fmt _glim_s  `_glim'
                _dash_count_fmt _gceil_s `_gceil'
                if `_lcells' >= 1e15 local _lcells_s "more than 999,999,999,999,999"
                else                 _dash_count_fmt _lcells_s `_lcells'
                display as error "`cmdname': layout() asks for a grid of `_lcells_s' cells, more than the `_glim_s' graphs and KPI cards one dashboard draws."
                display as error "      Use a smaller grid, or set global dash_max_graphs to a higher value (at most `_gceil_s')."
                exit(198)
            }
        }
    }

    // ---- validate tabs() (WP-31 D14) ----
    // Every name in the registry, as layout() requires, and a tab's own
    // layout() whole over that tab's names: a name the registry does not
    // hold was dropped from its tab without a word.  Read in Mata, by
    // value; the refusal is echoed through _dash_say.
    // A value written in quotes, tabs("Main: s1"), is read without them:
    // the names ended in a quote and were dropped, and now would be
    // refused (_dash_tabs_unwrap).
    local _tblen : length local tabs
    if `_tblen' > 0 {
        mata: st_local("tabs", _dash_tabs_unwrap(st_local("tabs")))
        mata: st_local("_tref", _dash_tabs_refusal(st_local("tabs"), st_local("registry")))
        local _treflen : length local _tref
        if `_treflen' > 0 {
            mata: _dash_say("err", "`cmdname': ", st_local("_tref"), "")
            exit(198)
        }
    }

    // ---- validate filter_position ----
    // By value: compared inside quotes, filterposition(`"le"ft"') stopped
    // dash build with r(132) "too few quotes", and filterposition(\$m) was
    // taken for whatever $m held (measured 24sep2026;
    // test_json_escaping.cscript JSE-55, JSE-58).
    local _fplen : length local filterposition
    if `_fplen' == 0 local filterposition "top"
    mata: st_local("_fpok", ///
        strofreal(anyof(("top", "left"), st_local("filterposition"))))
    if !`_fpok' {
        // The option is declared FILTERPOSition(); naming it filter_position()
        // here sent the user to an option -syntax- does not accept.
        display as error "`cmdname': filterposition() must be 'top' (default) or 'left' (sidebar)."
        exit(198)
    }

    // ---- validate theme() and scheme() (WP-17) ----
    // Before anything is written, through the program that gates a
    // graph-level scheme(): theme() is one of the six aliases, scheme() a
    // shipped translation, a theme, or a scheme Stata finds along the
    // ado-path (WP-30 P1.25b).  Measured 22sep2026: scheme(nosuchthing) and
    // theme(nosuchtheme) went through with rc 0 and a warning and were
    // drawn as s2color, and a hostile theme() reached the spec (escaped,
    // but reached it).  The session's c(scheme) is not validated -- it was
    // not asked for -- and the renderer warns once when it cannot
    // translate it.  Lengths, not expansions, decide whether a value is
    // present: these carry the user's own text.
    local _tlen : length local theme
    if `_tlen' > 0 {
        _dash_shipped_schemes
        local _tsorted : list sort _dash_themes
        local _tspec : subinstr local _tsorted " " "|", all
        _dash_validate_value "`cmdname'" "theme" "enum,`_tspec'" `"`macval(theme)'"' ""
        local theme `"`macval(_dash_vnorm)'"'
    }
    local _slen : length local scheme
    if `_slen' > 0 {
        _dash_validate_value "`cmdname'" "scheme" "scheme" `"`macval(scheme)'"' ""
    }

    // ---- validate link() names ----
    // Read by value, word by word as the renderer reads them, in Mata
    // (_dash_link_refusal): compared inside quotes and split by Stata's
    // word functions, link(`"g1"x"') stopped dash build with r(132) "too
    // few quotes" and link(`"g1" "g2"') with r(109) "type mismatch", and
    // link(`""g1""') passed as g1 while the renderer looks for a graph
    // named "g1", quotes and all (measured 24sep2026;
    // test_json_escaping.cscript JSE-56).
    // _all links every graph, so beside names it is a contradiction.  The
    // refusal is shown as written, never as SMCL (P20-09).
    local _lklen : length local link
    if `_lklen' > 0 {
        mata: st_local("_lkref", _dash_link_refusal(st_local("link"), ///
            st_local("registry")))
        local _lkreflen : length local _lkref
        if `_lkreflen' > 0 {
            mata: _dash_say("err", "`cmdname': ", st_local("_lkref"), "")
            exit(198)
        }
    }

    // ---- brush(): highlight (the default) or filter (WP-31 H2l) ----
    // Read by value and compared in Mata, so no word of it is run.
    local _brlen : length local brush
    local _dash_brush_json ""
    if `_brlen' > 0 {
        mata: st_local("_brok", strofreal(anyof(("highlight", "filter"), ///
            strlower(strtrim(st_local("brush"))))))
        if "`_brok'" != "1" {
            display as error "`cmdname': brush() takes highlight or filter"
            exit(198)
        }
        mata: st_local("brush", strlower(strtrim(st_local("brush"))))
        local _dash_brush_json `","brush":"`brush'""'
    }

    // ---- validate the filter() groups: exclude() names, variable names ----
    // Read in Mata, by value (_dash_filter_refusal): the filter string is
    // the user's text, label("...") included, and each group ends only at a
    // "||" or ";" outside quotes and parentheses.  This used to split the
    // string at EVERY "||" and ";" and take every "exclude(" for the
    // sub-option, wherever it stood: measured at 4ede074, label("A;B") and
    // label("A||B") stopped dash build with "too few quotes" r(132),
    // label(A;B) was refused as naming a variable 'B)', and
    // label("exclude(nosuch) me") as an exclude() of a graph named nosuch.
    // exclude() is still read in any case, as the renderer reads it, so
    // EXCLUDE(nosuch) is refused like exclude(nosuch) (P20-24).  Both
    // refusals are shown as written, never as SMCL (P19-24, P20-10); the
    // variables of the groups come back in _fvars, each an ASCII name, for
    // the serialisation below.
    local _fvars ""
    local _flen0 : length local filter
    if `_flen0' > 0 {
        mata: st_local("_fref", _dash_filter_refusal(st_local("filter"), ///
            st_local("registry"), "_fvars"))
        local _freflen : length local _fref
        if `_freflen' > 0 {
            mata: _dash_say("err", "`cmdname': ", st_local("_fref"), "")
            exit(198)
        }
    }

    // Do NOT substitute "default" for an unspecified theme.  "default" is a
    // real theme name that resolves to s2color, so writing it here made the
    // session's own c(scheme) unreachable -- the renderer's precedence is
    // scheme() then theme() then c(scheme), and a theme was always present.
    // An empty theme means "the user did not ask", which is the truth.

    // ---- graphs from several frames (WP-33 33-07) ----
    // Each graph is drawn from the frame it was registered in (Stata's
    // frame prefix; dash_frm_<g>).  When all of them share the frame this
    // build runs in, nothing below changes (_dash_fr_multi 0).  Otherwise
    // each graph's registry entry is read in its own frame (_fpx, the
    // frame prefix), every column is keyed by its frame, and the data are
    // a stack of the frames, made in the frame _dash_stk names.
    tempname _dash_stk
    _dash_frames_plan "`cmdname'" `"`macval(link)'"'
    local _dash_fr_multi = r(multi)
    local _dash_fr_frames "`r(frames)'"
    local _fr_n : word count `registry'
    forvalues k = 1/`_fr_n' {
        local _fof_`k' "`r(of_`k')'"
    }
    local _fpx ""
    // WP-35 DT-19: the prefix of every column this build makes, chosen
    // over the variable and value-label set names of every frame it reads
    // (_dash_reserved_prefix), so no frame's variable or label set starts
    // with it: a variable named __dash... is then data, as twoway reads it.
    local _rp_fr "`_dash_fr_frames'"
    if "`_rp_fr'" == "" local _rp_fr = c(frame)
    local _rp_all ""
    foreach _rpf of local _rp_fr {
        local _rp_v ""
        capture frame `_rpf': unab _rp_v : __d*
        local _rp_all `_rp_all' `_rp_v'
        frame `_rpf': quietly label dir
        local _rp_all `_rp_all' `r(names)'
    }
    mata: st_local("_dash_rp", _dash_reserved_prefix(tokens(st_local("_rp_all"))))

    // ---- determine all variables needed ----
    // And each distinct qualifier, which is evaluated in Stata and exported
    // as a column (_dash_qual_rewrite, _dash_qual_take, _dash_qual_gen).
    local all_vars ""
    // WP-29 P0.10: hover()'s variables are always exported: in all_vars
    // as each graph is read when one of its layers can show them (or
    // under csv), and _hv_hide holds the others, appended after every
    // other variable -- the partition fixes the data file's column order.
    local _hv_hide ""
    _dash_plottype_families
    mata: _dash_qual_reset()
    // The time-series table, one for the dashboard (WP-30 P1.7), and the
    // weight-expression table (WP-31 A5).
    mata: _dash_tsop_reset()
    mata: _dash_wexp_reset()
    if `_dash_fr_multi' {
        mata: _dash_frames_reset()
        mata: _dash_frame_set_all(1)
    }
    local _rl_sum 0
    local _at_sum 0
    local ntok_reg : word count `registry'
    forvalues k = 1/`ntok_reg' {
        local gname : word `k' of `registry'
        // The entry's frame (WP-33 33-07): its columns are keyed by it,
        // and a frame other than this build's is read under its prefix.
        if `_dash_fr_multi' {
            mata: _dash_frame_set(st_local("_fof_`k'"))
            local _fpx ""
            if "`_fof_`k''" != "`c(frame)'" local _fpx "frame `_fof_`k'':"
        }

        // A KPI is exactly its marker: the global dash_kpi_<name> holding
        // "1", the one global _dash_kpi writes under that name -- here and
        // in the two loops that assemble the spec.  No other item's global
        // has that name: a KPI's fields are dash_kpi_<name>__<field>, and
        // no name holds two underscores in a row.  While they were
        // dash_kpi_<name>_stat, ..., a graph a_stat beside KPI a found KPI
        // a's statistic here, "mean", and was drawn as a blank KPI card
        // (measured 23sep2026 at 9f48cf7).
        // An image panel (WP-33 33-06) exports no data; it is checked and
        // written with the images below.
        if "${dash_img_`gname'}" == "1" continue
        if "${dash_kpi_`gname'}" == "1" {
            // _dash_kpi always stores a statistic and a variable.  A KPI
            // without them was not registered by this dash -- its marker
            // set by hand, or a KPI an older dash left in the session under
            // the one-underscore names, which are no longer read -- and it
            // was drawn as a blank card, in silence.  Measured by length,
            // so a hand-set value is never expanded.
            local _ksl : strlen global dash_kpi_`gname'__sta
            local _kvl : strlen global dash_kpi_`gname'__var
            if `_ksl' == 0 | `_kvl' == 0 {
                mata: _dash_say("err", "`cmdname': registry entry '", ///
                    st_local("gname"), "' holds a KPI with no statistic " + ///
                    "or variable. Run dash clear and register it again.")
                exit(198)
            }
            local kpi_var = "${dash_kpi_`gname'__var}"
            if !`: list kpi_var in all_vars' local all_vars "`all_vars' `kpi_var'"
            // WP-31 H2k: a weighted card's weight is exported beside its
            // variable, so both renderers recompute it weighted.
            local _kwv = "${dash_kpi_`gname'__wex}"
            if "`_kwv'" != "" {
                capture confirm numeric variable `_kwv', exact
                if _rc {
                    mata: _dash_say("err", "`cmdname': KPI '", ///
                        st_local("gname"), "' is weighted by a variable " + ///
                        "the data no longer holds as a number. Run dash " + ///
                        "clear and register it again.")
                    exit 198
                }
                if !`: list _kwv in all_vars' local all_vars "`all_vars' `_kwv'"
            }
            if `_dash_fr_multi' {
                mata: _dash_frames_keep_add(c("frame"), "", st_local("kpi_var") + " " + st_local("_kwv"))
            }
            // The KPI's own if and in: the column that will hold Stata's
            // answer (_dash_qual_gen), read by value from the registry.
            // Its variables are not exported -- the answer is.  They used
            // to be, so the renderer could translate the qualifier, and a
            // qualifier it read otherwise than Stata showed a card Stata
            // would not (test_qualifier_in_stata.cscript QS-03).
            local _dq_err ""
            mata: st_local("_kqc_`k'", _dash_qual_take( ///
                st_global("dash_kpi_" + st_local("gname") + "__if"), ///
                st_global("dash_kpi_" + st_local("gname") + "__in"), "_dq_err", 1))
            if `: length local _dq_err' {
                mata: _dash_say("err", "`cmdname': registry entry '", ///
                    st_local("gname"), "' holds a qualifier dash cannot evaluate: " + ///
                    st_local("_dq_err") + ". Run dash clear and register it again.")
                exit 198
            }
            continue
        }

        // Use strlen to check if JSON global is set WITHOUT embedding JSON in a
        // double-quoted expression (which would break when JSON contains " chars)
        local _chk : strlen global dash_json_`gname'

        // Neither a KPI nor a graph: the registry names an item dash does
        // not hold.  No registrar leaves one -- each retires exactly the
        // item it replaces -- but the registry is ordinary globals.  Such
        // an entry went into the spec as an empty graph and the renderer
        // died on the JSON: measured 23sep2026 at 9f48cf7, r(7102) and a
        // Python JSONDecodeError on "[, {" or on a trailing comma.  Refused
        // here, by name, before anything is exported; the name is echoed
        // as text, since a hand-set registry may hold anything.
        if `_chk' == 0 {
            mata: _dash_say("err", "`cmdname': registry entry '", ///
                st_local("gname"), "' holds neither a graph nor a KPI. " + ///
                "Run dash clear and register it again.")
            exit(198)
        }
        if `_chk' > 0 {
            // The graph as the spec will carry it: each if/in pair replaced
            // by the column that holds Stata's answer, and no qualifier
            // text left for a renderer to translate.  Read by value.
            local _dq_err ""
            `_fpx' mata: st_local("_qg_`k'", _dash_qual_rewrite( ///
                st_global("dash_json_" + st_local("gname")), "_dq_err", 1))
            if `: length local _dq_err' {
                mata: _dash_say("err", "`cmdname': registry entry '", ///
                    st_local("gname"), "' holds a qualifier dash cannot evaluate: " + ///
                    st_local("_dq_err") + ". Run dash clear and register it again.")
                exit 198
            }
            // Time-series operators (WP-30 P1.7): each expression becomes
            // the column __dasht<k> _dash_tsop_gen fills at export.
            local _dts_err ""
            // A weight expression first (WP-31 A5): the column __dashw<k>
            // _dash_wexp_gen fills at export.
            `_fpx' mata: st_local("_qg_`k'", _dash_wexp_rewrite(st_local("_qg_`k'"), "_dts_err"))
            if `: length local _dts_err' {
                mata: _dash_say("err", "`cmdname': ", st_local("_dts_err"), ". Run dash clear and register it again.")
                exit 198
            }
            `_fpx' mata: st_local("_qg_`k'", _dash_tsop_rewrite(st_local("_qg_`k'"), "_dts_err"))
            if `: length local _dts_err' {
                mata: _dash_say("err", "`cmdname': ", st_local("_dts_err"), ". Run dash clear and register it again.")
                exit 198
            }
            // Reference lines (WP-30 P1.21a): this graph's positions times
            // its by() panels, summed for _dash_reflines_cap below.
            mata: st_local("_rl_json", st_global("dash_json_" + st_local("gname")))
            _dash_reflines_of `"`macval(_rl_json)'"'
            local _rl_sum = `_rl_sum' + r(n)
            // Added text (WP-30 P1.10): this graph's texts times panels,
            // as registered, summed for _dash_added_text_cap below.
            mata: st_local("_atn", strofreal(_dash_json_first_num(st_local("_rl_json"), "added_text_n")))
            if `_atn' < . local _at_sum = `_at_sum' + `_atn'
            local _rl_json ""
            // The t-options' unit (WP-30 P1.6): read at registration; a
            // date format of the axis variable changed since is noted
            // once, and the registered values are drawn.
            mata: st_local("_tu", st_global("dash_tu_" + st_local("gname")))
            local _tu_said 0
            foreach _tu_t of local _tu {
                tokenize "`_tu_t'", parse(":")
                local _tu_v `3'
                local _tu_u `5'
                local _tu_now "?"
                `_fpx' capture confirm variable `_tu_v', exact
                if !_rc {
                    `_fpx' local _tu_f : format `_tu_v'
                    mata: st_local("_tu_now", _dash_taxis_unit(st_local("_tu_f"), 1))
                }
                if "`_tu_now'" != "`_tu_u'" & !`_tu_said' {
                    local _tu_said 1
                    mata: _dash_note("dash: graph " + st_local("gname") + ": the t-options' dates were read as " + st_local("_tu_u") + "() dates when it was registered; " + st_local("_tu_v"), " now has another date format, and they are drawn at the registered values", "")
                }
            }

            local gvars ""
            mata: _dash_extract_vars(st_local("_qg_`k'"), "gvars")
            // Less the time-series columns, which _dash_tsop_gen makes, and
            // the weight columns, _dash_wexp_gen's.
            local _gv_keep ""
            foreach v of local gvars {
                local _rpl = strlen("`_dash_rp'") + 1
                if !inlist(substr("`v'", 1, `_rpl'), "`_dash_rp't", "`_dash_rp'w") local _gv_keep `_gv_keep' `v'
            }
            local gvars `_gv_keep'
            foreach v of local gvars {
                if !`: list v in all_vars' local all_vars "`all_vars' `v'"
            }
            // Also extract variables referenced only in faceting (by) -- these
            // may not appear in any plot-variable key but must be serialised
            // so the renderer can facet on them.  Read from the rewritten
            // graph, which holds no qualifier text: a qualifier's variables
            // are not exported, its answer is.
            local qvars ""
            mata: _dash_extract_qual_vars(st_local("_qg_`k'"), "qvars")
            local _qv_ok ""
            foreach v of local qvars {
                `_fpx' capture confirm variable `v'
                if _rc == 0 {
                    local _qv_ok `_qv_ok' `v'
                    if !`: list v in all_vars' local all_vars "`all_vars' `v'"
                }
            }

            // WP-29 P0.10: every variable hover() names is exported -- a
            // variable named only there was left out with rc 0 and no
            // note.  Read and checked in Mata from the registry (ordinary
            // globals a user can edit) before it reaches any command; a
            // name no longer in memory is refused as a dropped plotted
            // variable is.  Counted on the saved page only when a layer
            // of this graph can show it, or csv puts it in the download
            // (design review A1).
            local _hv_k ""
            local _hv_bad ""
            local _hv_why ""
            `_fpx' mata: _dash_extract_hover_vars(st_local("_qg_`k'"), "_hv_k", "_hv_bad", "_hv_why")
            if "`_hv_why'" == "name" {
                mata: _dash_say("err", "`cmdname': registry entry '" + ///
                    st_local("gname") + "' holds a hover() value that is " + ///
                    "not a list of variable names (got: ", st_local("_hv_bad"), ///
                    "). Run dash clear and register it again.")
                exit 198
            }
            if "`_hv_why'" == "var" {
                mata: _dash_say("err", "`cmdname': graph '" + ///
                    st_local("gname") + "': hover(): variable ", ///
                    st_local("_hv_bad"), " not found")
                exit 111
            }
            local _hv_show_`k' = 1
            if "`_hv_k'" != "" & "`csv'" == "" {
                mata: st_local("_hv_show_`k'", strofreal(!_dash_spec_types_in( ///
                    st_local("_qg_`k'"), "`_pt_univar' `_pt_onefit' `_pt_contour' `_pt_literal'")))
            }
            if `_hv_show_`k'' {
                local all_vars : list all_vars | _hv_k
            }
            else {
                local _hv_hide : list _hv_hide | _hv_k
            }
            // What this graph's frame keeps for it (WP-33 33-07).
            if `_dash_fr_multi' {
                mata: _dash_frames_keep_add(st_local("_fof_`k'"), st_local("gname"), ///
                    st_local("gvars") + " " + st_local("_qv_ok") + " " + st_local("_hv_k"))
            }
        }
    }
    local _fpx ""
    if `_dash_fr_multi' mata: _dash_frame_set(c("frame"))

    // Reference lines: positions times by() panels over every graph
    // (WP-30 P1.21a), refused before any export.
    _dash_reflines_cap `_rl_sum'
    // Added text over every graph (WP-30 P1.10).
    _dash_added_text_cap `_at_sum'

    // ---- also include filter variables in the serialization ----
    // Filter variables (e.g. foreign from filter(foreign, type(dropdown)))
    // may not appear in any graph or KPI spec.  Without explicit inclusion,
    // the export would never write them, so the Python filter widgets would
    // be silently skipped.  _fvars holds each group's variable, read and
    // proven a name by _dash_filter_refusal above -- a top-level ";"
    // separates two groups as "||" does (BUG-45).  A filter must name a
    // real variable: silently skipping one meant
    //     dash build, filter(<script>alert, type(dropdown))
    // returned rc 0 with a filter that did nothing, and every other Stata
    // command rejects a name it cannot resolve.
    //
    // An abbreviation is the variable it abbreviates, as a varname is
    // anywhere in Stata, and the renderer is handed the full name: it looks
    // the name up in the data the export writes, which carries the full one, so
    // filter(fore) built with rc 0 and no widget -- "the variable is not in
    // the data" (measured at 4ede074).
    local _ffull ""
    local _fgi 0
    foreach _fvar of local _fvars {
        local ++_fgi
        if `_dash_fr_multi' {
            // A build of several frames (WP-33 33-07): the variable is
            // resolved in every frame; each frame that holds it must give
            // the same full name and kind (DECISIONS A-28), and every
            // graph whose frame does not hold it is excluded.
            local _fhave ""
            local _fvfull ""
            local _fkind ""
            local _ff1 ""
            foreach _F of local _dash_fr_frames {
                frame `_F': capture confirm variable `_fvar'
                if _rc continue
                frame `_F': unab _fu : `_fvar'
                frame `_F': capture confirm string variable `_fu', exact
                local _fk = cond(_rc, "numeric", "a string")
                if "`_ff1'" == "" {
                    local _ff1 "`_F'"
                    local _fvfull "`_fu'"
                    local _fkind "`_fk'"
                }
                else if "`_fu'" != "`_fvfull'" {
                    mata: _dash_say("err", "`cmdname': filter() variable ", st_local("_fvar"), ///
                        " abbreviates " + st_local("_fvfull") + " in frame " + st_local("_ff1") + ///
                        " and " + st_local("_fu") + " in frame " + st_local("_F"))
                    exit 198
                }
                else if "`_fk'" != "`_fkind'" {
                    mata: _dash_say("err", "`cmdname': filter() variable ", st_local("_fvfull"), ///
                        " is " + st_local("_fkind") + " in frame " + st_local("_ff1") + ///
                        " and " + st_local("_fk") + " in frame " + st_local("_F"))
                    exit 109
                }
                local _fhave `_fhave' `_F'
                mata: _dash_frames_keep_add(st_local("_F"), "", st_local("_fu"))
            }
            if "`_ff1'" == "" {
                display as error "`cmdname': filter() variable `_fvar' not found."
                exit(111)
            }
            local _fxg ""
            forvalues k = 1/`ntok_reg' {
                local gname : word `k' of `registry'
                if "${dash_img_`gname'}" == "1" | "${dash_kpi_`gname'}" == "1" continue
                if !`: list _fof_`k' in _fhave' local _fxg `_fxg' `gname'
            }
            local _fxadd_`_fgi' "`_fxg'"
        }
        else {
            capture confirm variable `_fvar'
            if _rc != 0 {
                display as error "`cmdname': filter() variable `_fvar' not found."
                exit(111)
            }
            unab _fvfull : `_fvar'
        }
        local _ffull `_ffull' `_fvfull'
        if !`: list _fvfull in all_vars' {
            local all_vars "`all_vars' `_fvfull'"
        }
    }
    if !`: list _ffull == _fvars' {
        mata: st_local("filter", _dash_filter_setvars(st_local("filter"), ///
            st_local("_ffull")))
    }
    if `_dash_fr_multi' {
        forvalues j = 1/`_fgi' {
            if "`_fxadd_`j''" != "" {
                mata: st_local("filter", _dash_filter_exclude_add(st_local("filter"), ///
                    `j', st_local("_fxadd_`j'")))
            }
        }
    }

    local all_vars = strtrim("`all_vars'")

    local all_vars : list all_vars | _hv_hide
    local all_vars = strtrim("`all_vars'")

    // No variable to export: every graph must draw from its own values --
    // scatteri, pci, pcarrowi and function alone, which twoway draws with
    // no data in memory -- and the data file then holds no variable
    // (_dash_empty_data).  Such a dashboard was refused here whatever it
    // held: after `dash scatteri 1 2, name(a1)', `dash build' said "no
    // variables identified across registered graphs", r(198), saved and
    // served (measured 24sep2026; test_parser.cscript P1A-72).  A graph of
    // any other type that names no variable -- one dash no longer
    // registers (P1A-69), but the registry is ordinary globals -- is still
    // refused (P1A-74).  A KPI always names its variable.
    local _dts_n = 0
    mata: _dash_tsop_export()
    local _dwx_n = 0
    mata: _dash_wexp_export()
    local _novars = ("`all_vars'" == "" & `_dts_n' == 0)
    if `_novars' {
        _dash_plottype_families
        forvalues k = 1/`ntok_reg' {
            local gname : word `k' of `registry'
            if "${dash_img_`gname'}" == "1" continue
            if "${dash_kpi_`gname'}" == "1" continue
            mata: st_local("_gvf", strofreal(_dash_spec_types_in( ///
                st_global("dash_json_" + st_local("gname")), ///
                st_local("_pt_literal")) | ///
                !_dash_spec_has_plots(st_global("dash_json_" + st_local("gname")))))
            if !`_gvf' {
                display as error "`cmdname': no variables identified across registered graphs."
                exit(198)
            }
        }
        // No data are exported, so no qualifier column: the literal family
        // draws its own values, which twoway's if and in do not reach.
        mata: _dash_qual_reset()
        forvalues k = 1/`ntok_reg' {
            local gname : word `k' of `registry'
            if "${dash_img_`gname'}" == "1" continue
            if "${dash_kpi_`gname'}" == "1" continue
            mata: st_local("_qg_`k'", _dash_qual_rewrite( ///
                st_global("dash_json_" + st_local("gname")), "_dq_err", 0))
        }
    }

    // ---- write the data file (_dash_write_data) ----
    // From Python through sfi, as on the immediate route; jsonio is no
    // longer needed.

    // ---- resource limits (WP-19), before anything is exported ----
    // As on the immediate route: every dash_max_* global the session has
    // set is validated and carried to the renderer as build_options.limits.
    _dash_limits_json
    local _dash_lim_json `"`r(json)'"'
    // Each qualifier column is embedded with the data, and counted.
    mata: _dash_qual_export()
    // sort(varlist)'s join-order columns (WP-29 P0.1): each distinct
    // "sortvars" list the plots carry, checked again to be names
    // (_dash_sort_scan; the registry is a global a do-file can set), one
    // rank column each, embedded with the data and counted.
    local _ds_bad ""
    mata: _dash_sort_reset()
    forvalues k = 1/`ntok_reg' {
        local gname : word `k' of `registry'
        if "${dash_img_`gname'}" == "1" continue
        if "${dash_kpi_`gname'}" == "1" continue
        if `_dash_fr_multi' mata: _dash_frame_set(st_local("_fof_`k'"))
        mata: _dash_sort_scan(st_local("_qg_`k'"))
    }
    mata: st_local("_ds_isbad", strofreal(st_local("_ds_bad") != ""))
    if `_ds_isbad' {
        display as error "option sort() incorrectly specified"
        display as error "      `cmdname': a sort() list in the registered graph is not Stata names."
        exit 198
    }
    local _ds_n = 0
    mata: _dash_sort_export()
    local _ds_json ""
    forvalues _dsk = 1/`_ds_n' {
        _dash_json_str "`_ds_v`_dsk''" _ds_vj
        local _ds_sep ""
        if `_dsk' > 1 local _ds_sep ","
        local _ds_json `"`_ds_json'`_ds_sep'"`_ds_vj'":"`_dash_rp's`_dsk'""'
    }
    if `_ds_n' > 0 local _ds_json `","sort_cols":{`_ds_json'}"'

    // Collect display formats, as on the immediate route.  A build of
    // several frames reads them from its stack, below (WP-33 33-07).
    local _dts_json ""
    local _dash_fcols_map "{}"
    local _dash_fr_stack = `_dash_fr_multi' & !`_novars'
    if !`_dash_fr_stack' {
        _dash_formats_json "`all_vars'" _dash_fmt_json _dash_date_vars _dash_bcal_json
        // The time-series columns' formats and the spec's map (WP-30 P1.7).
        if `_dts_n' + `_dwx_n' > 0 {
            mata: st_local("_dts_obj", _dash_tsop_meta("_dash_fmt_json"))
            local _dts_json `","ts_cols":`macval(_dts_obj)'"'
        }
    }
    local _dash_jrc = 0
    if `_novars' {
        _dash_empty_data "`datapath'"
    }
    else if `_dash_fr_stack' {
        // The stack (WP-33 33-07): each frame's rows and columns, made in
        // that frame (_dash_frames_stack); formats, Stata's ticks and the
        // data file read from it.  The working frame is never changed.
        // WP-35 DT-19: each frame's copy of e(sample), made before the
        // estimates are held (_dash_esample_copy): the sample in the frame
        // the estimation ran in, 0 in every other, as twoway reads it.
        local _dash_es_fr ""
        foreach _esf of local _dash_fr_frames {
            local _dash_es ""
            capture noisily frame `_esf': _dash_esample_copy `_dash_rp' "`cmdname'"
            if _rc {
                local _es_rc = _rc
                foreach _esg of local _dash_es_fr {
                    capture frame `_esg': drop `_dash_rp'esample
                }
                exit `_es_rc'
            }
            if "`_dash_es'" != "" local _dash_es_fr `_dash_es_fr' `_esf'
        }
        if `_dq_n' + `_ds_n' + `_dts_n' + `_dwx_n' > 0 {
            tempname _dash_eh
            _estimates hold `_dash_eh', restore nullok
        }
        local _dash_split_vars ""
        capture noisily _dash_frames_stack "`cmdname'" `_dash_stk' "`_dash_fr_frames'" `_dq_n' `_ds_n' `_dts_n' `_dwx_n' `_dash_rp'
        local _es_rc = _rc
        foreach _esg of local _dash_es_fr {
            capture frame `_esg': drop `_dash_rp'esample
        }
        if `_es_rc' exit `_es_rc'
        frame `_dash_stk': _dash_formats_json "`all_vars' `_dash_split_vars'" _dash_fmt_json _dash_date_vars _dash_bcal_json
        if `_dts_n' + `_dwx_n' > 0 {
            frame `_dash_stk': mata: st_local("_dts_obj", _dash_tsop_meta("_dash_fmt_json"))
            local _dts_json `","ts_cols":`macval(_dts_obj)'"'
        }
        local _dst_names ""
        forvalues _dstk = 1/`ntok_reg' {
            if `: length local _qg_`_dstk'' local _dst_names `_dst_names' _qg_`_dstk'
        }
        local _dash_st_json ""
        _dash_require_python
        _dash_require_deps
        capture _dash_xm_load
        if _rc == 0 {
            capture python: import sys
            capture python: from sfi import Macro as _dash_M
            capture python: _dash_xm = sys.modules["_dash_render_export"]
            capture python: _dash_M.setLocal("_dst_reqs", _dash_xm._dash_stata_tick_plan(_dash_M.getLocal("_dst_names"), _dash_M.getLocal("_dash_fmt_json"), _dash_M.getLocal("_dash_fcols_map")))
            if _rc == 0 & `: length local _dst_reqs' {
                capture frame `_dash_stk': _dash_stata_ticks_gen `_dst_reqs'
                if _rc local _dash_st_json ""
            }
        }
        capture noisily frame `_dash_stk': _dash_write_data "`datapath'" `all_vars' `_dash_split_vars' `_dash_qual_vars' `_dash_sort_vars' `_dash_tsop_vars' `_dash_wexp_vars'
        local _dash_jrc = _rc
    }
    else {
        // The qualifier columns, as on the immediate route: made first,
        // exported with the data, dropped the moment the file is written, the
        // estimates in memory held meanwhile (QS-15).
        local _dash_qual_vars ""
        local _dash_sort_vars ""
        local _dash_tsop_vars ""
        local _dash_wexp_vars ""
        // WP-35 DT-19: e(sample) read as twoway reads it, as on the
        // immediate route (_dash_esample_copy).
        local _dash_es ""
        _dash_esample_copy `_dash_rp' "`cmdname'"
        // WP-31 G3d, WP-35 DT-19: in place with room, else in a temporary
        // frame of the variables the export reads, else refused, as on
        // the immediate route.
        _dash_frame_vars `_dash_rp' "" `all_vars'
        capture noisily _dash_maxvar_room `_dq_n' `_ds_n' `_dts_n' `_dwx_n' "`cmdname'" `_mv_kx'
        if _rc {
            local _dt_rc = _rc
            if "`_dash_es'" != "" capture drop `_dash_es'
            exit `_dt_rc'
        }
        if `_dq_n' + `_ds_n' + `_dts_n' + `_dwx_n' > 0 {
            tempname _dash_eh
            _estimates hold `_dash_eh', restore nullok
        }
        local _xfp ""
        if "`_mv_plan'" == "frame" {
            tempname _dash_xf
            _dash_frame_put `_dash_xf' `_mv_vars'
            local _xfp "frame `_dash_xf':"
            if "`_dash_es'" != "" capture drop `_dash_es'
        }
        capture noisily `_xfp' _dash_qual_gen "`cmdname'" "" "`_dash_rp'"
        if _rc {
            local _dt_rc = _rc
            if "`_dash_es'" != "" capture drop `_dash_es'
            capture frame drop `_dash_xf'
            exit `_dt_rc'
        }
        // The join-order columns, as on the immediate route.
        capture noisily `_xfp' _dash_sort_gen "`cmdname'" "" "`_dash_rp'"
        if _rc {
            local _ds_rc = _rc
            if "`_dash_qual_vars'" != "" capture `_xfp' drop `_dash_qual_vars'
            if "`_dash_es'" != "" capture drop `_dash_es'
            capture frame drop `_dash_xf'
            exit `_ds_rc'
        }
        // The time-series columns, as on the immediate route.
        capture noisily `_xfp' _dash_tsop_gen "`cmdname'" "" "`_dash_rp'"
        if _rc {
            local _dt_rc = _rc
            capture `_xfp' drop `_dash_qual_vars' `_dash_sort_vars'
            if "`_dash_es'" != "" capture drop `_dash_es'
            capture frame drop `_dash_xf'
            exit `_dt_rc'
        }
        // The weight-expression columns, as on the immediate route.
        capture noisily `_xfp' _dash_wexp_gen "`cmdname'" "" "`_dash_rp'"
        if _rc {
            local _dt_rc = _rc
            capture `_xfp' drop `_dash_qual_vars' `_dash_sort_vars' `_dash_tsop_vars'
            if "`_dash_es'" != "" capture drop `_dash_es'
            capture frame drop `_dash_xf'
            exit `_dt_rc'
        }
        local _dst_names ""
        forvalues _dstk = 1/`ntok_reg' {
            if `: length local _qg_`_dstk'' local _dst_names `_dst_names' _qg_`_dstk'
        }
        local _dash_st_json ""
        // WP-31 D15: Stata's own #N ticks over each axis's rows, asked of
        // _natscale/_tsnatscale while the qualifier columns exist
        // (_dash_axis_ticks_stata); carried as build_options.stata_ticks.
        // Captured: a failure leaves every axis to the renderer's model.
        // The guards first, uncaptured: dash ran them on entry, so they
        // cannot refuse here, and every python: line stands below them
        // (test_env_guards.cscript ENV-12, test_dependency_guards.py).
        _dash_require_python
        _dash_require_deps
        capture _dash_xm_load
        if _rc == 0 {
            capture python: import sys
            capture python: from sfi import Macro as _dash_M
            capture python: _dash_xm = sys.modules["_dash_render_export"]
            capture python: _dash_M.setLocal("_dst_reqs", _dash_xm._dash_stata_tick_plan(_dash_M.getLocal("_dst_names"), _dash_M.getLocal("_dash_fmt_json")))
            if _rc == 0 & `: length local _dst_reqs' {
                capture `_xfp' _dash_stata_ticks_gen `_dst_reqs'
                if _rc local _dash_st_json ""
            }
        }
        // Captured for the same reason as on the immediate route.
        capture noisily `_xfp' _dash_write_data "`datapath'" `all_vars' `_dash_qual_vars' `_dash_sort_vars' `_dash_tsop_vars' `_dash_wexp_vars'
        local _dash_jrc = _rc
        if "`_dash_qual_vars'`_dash_sort_vars'`_dash_tsop_vars'`_dash_wexp_vars'" != "" {
            capture `_xfp' drop `_dash_qual_vars' `_dash_sort_vars' `_dash_tsop_vars' `_dash_wexp_vars'
        }
        if "`_dash_es'" != "" capture drop `_dash_es'
        capture frame drop `_dash_xf'
    }
    if `_dash_jrc' exit `_dash_jrc'

    capture confirm file "`datapath'"
    if _rc != 0 {
        display as error "`cmdname': the data could not be written."
        exit(198)
    }

    // ---- assemble master JSON ----
    local graphs_json ""
    local n_graphs = 0

    forvalues k = 1/`ntok_reg' {
        local gname : word `k' of `registry'
        if "${dash_img_`gname'}" == "1" continue
        if "${dash_kpi_`gname'}" == "1" {
            // An entry should never hold a graph AND a KPI: both registrars
            // retire whatever held the name before.  If one does, this loop
            // would drop the graph from the dashboard in silence, which is
            // exactly the defect that used to be reachable through
            // `dash kpi ..., name(<an existing graph>)'.  The registry lives
            // in ordinary Stata globals, so a do-file that sets dash_* by
            // hand can still produce this; say so rather than swallow it.
            if `"${dash_json_`gname'}"' != "" {
                display as text "`cmdname': '`gname'' is registered as both " ///
                    "a graph and a KPI; drawing the KPI." 
                display as text "  Run {cmd:dash clear} and register it once, " ///
                    "or use {cmd:name(`gname', replace)}."
            }
            continue
        }

        if `n_graphs' > 0 local graphs_json `"`graphs_json', "'
        // The graph with its qualifiers replaced by their columns
        // (_dash_qual_rewrite, above), joined by value.
        mata: st_local("graphs_json", st_local("graphs_json") + st_local("_qg_`k'"))
        local n_graphs = `n_graphs' + 1
        local _fp_names `_fp_names' `gname'
    }

    // assemble KPIs JSON
    local kpis_json ""
    local n_kpis = 0
    forvalues k = 1/`ntok_reg' {
        local gname : word `k' of `registry'
        if "${dash_kpi_`gname'}" != "1" continue

        // Read each KPI field from its dedicated global (preserves multi-word values)
        // then JSON-escape the string fields before insertion.  The fields
        // are dash_kpi_<name>__<field> (_dash_kpi_fields in dash_parse.mata).
        //
        // Every field is read and escaped by value, in Mata.  Expanded into
        // a command line, "${dash_kpi_<name>__tit}" was read again for
        // macros, so a title dash kpi had stored as written -- A$m B
        // `=1+1' C -- reached the spec expanded, and ran; so did a string
        // literal in the qualifier (measured 24sep2026;
        // test_json_escaping.cscript JSE-58).  _dash_json_escape writes ` $ and '
        // as \u escapes, so each can be expanded inside the compound quotes
        // of the line below.  The statistic, variable, value and update()
        // are dash's own words, and are escaped all the same.
        mata: st_local("kstat",       _dash_json_escape(st_global("dash_kpi_" + st_local("gname") + "__sta")))
        mata: st_local("kvar",        _dash_json_escape(st_global("dash_kpi_" + st_local("gname") + "__var")))
        mata: st_local("kval",        _dash_json_escape(st_global("dash_kpi_" + st_local("gname") + "__val")))
        mata: st_local("_kdisp_esc",  _dash_json_escape(st_global("dash_kpi_" + st_local("gname") + "__dsp")))
        mata: st_local("_kfmt_esc",   _dash_json_escape(st_global("dash_kpi_" + st_local("gname") + "__fmt")))
        mata: st_local("_ktitle_esc", _dash_json_escape(st_global("dash_kpi_" + st_local("gname") + "__tit")))
        mata: st_local("_ksub_esc",   _dash_json_escape(st_global("dash_kpi_" + st_local("gname") + "__sub")))
        mata: st_local("_kcol_esc",   _dash_json_escape(st_global("dash_kpi_" + st_local("gname") + "__col")))
        mata: st_local("_kbg_esc",    _dash_json_escape(st_global("dash_kpi_" + st_local("gname") + "__bg")))
        mata: st_local("kupdate",     _dash_json_escape(st_global("dash_kpi_" + st_local("gname") + "__upd")))
        mata: st_local("kweight",     _dash_json_escape(st_global("dash_kpi_" + st_local("gname") + "__wgt")))
        mata: st_local("kwexp",       _dash_json_escape(st_global("dash_kpi_" + st_local("gname") + "__wex")))
        // The KPI's if and in travel as the column that holds Stata's
        // answer (_dash_qual_take, above), and as no text.
        local _kqc : copy local _kqc_`k'

        if `n_kpis' > 0 local kpis_json `"`kpis_json', "'
        local kpis_json `"`kpis_json'{"name":"`gname'","stat":"`kstat'","var":"`kvar'","value":"`kval'","display":"`_kdisp_esc'","fmt":"`_kfmt_esc'","title":"`_ktitle_esc'","subtitle":"`_ksub_esc'","color":"`_kcol_esc'","bgcolor":"`_kbg_esc'","update":"`kupdate'","weight":"`kweight'","wexp":"`kwexp'","if_expr":"","in_expr":"","qual_col":"`_kqc'"}"'
        local n_kpis = `n_kpis' + 1
    }

    // assemble images JSON (WP-33 33-06): each image's file checked again
    // (it may have changed since it was registered) and its fields read
    // and escaped by value.  The renderer reads the file and draws it from
    // a data address; the spec carries its path.
    local images_json ""
    local n_images = 0
    forvalues k = 1/`ntok_reg' {
        local gname : word `k' of `registry'
        if "${dash_img_`gname'}" != "1" continue
        if `n_images' == 0 {
            _dash_require_python
            _dash_xm_load
            python: import sys
            python: from sfi import Macro as _dash_M
            python: _dash_xm = sys.modules["_dash_render_export"]
        }
        mata: st_local("_im_path", st_global("dash_img_" + st_local("gname") + "__pth"))
        python: _dash_M.setLocal("_im_err", _dash_xm._dash_image_check(_dash_M.getLocal("_im_path")))
        local _im_elen : length local _im_err
        if `_im_elen' > 0 {
            mata: st_local("_im_rc", substr(st_local("_im_err"), 1, 3)); ///
                st_local("_im_err", substr(st_local("_im_err"), 5, .))
            mata: _dash_say("err", "", st_local("_im_err"), "")
            exit `_im_rc'
        }
        mata: st_local("_im_pth", _dash_json_escape(st_local("_im_path")))
        mata: st_local("_im_cap", _dash_json_escape(st_global("dash_img_" + st_local("gname") + "__cap")))
        mata: st_local("_im_alt", _dash_json_escape(st_global("dash_img_" + st_local("gname") + "__alt")))
        mata: st_local("_im_lnk", _dash_json_escape(st_global("dash_img_" + st_local("gname") + "__lnk")))
        if `n_images' > 0 local images_json `"`images_json', "'
        local images_json `"`images_json'{"name":"`gname'","path":"`_im_pth'","caption":"`_im_cap'","alt":"`_im_alt'","link":"`_im_lnk'"}"'
        local n_images = `n_images' + 1
    }
    // The key only when an image is registered: a dashboard with none is
    // unchanged byte for byte.
    local _im_part ""
    if `n_images' > 0 local _im_part `","images":[`images_json']"'

    // JSON-escape it, like every other string that goes into master_json.
    // It did not used to be: filter(weight, type(range) label("Curb weight"))
    // put bare double quotes straight into the document and broke it, which
    // is why label() could not be used even once the renderer learned to
    // parse it.
    local filter_json ""
    // `: length local' rather than a comparison: the value contains the
    // user's label("...") text, and expanding it inside an expression is the
    // hazard this file has already been bitten by twice.
    //
    // The user's text reaches _dash_json_str through macval(), here and
    // below: expanded plainly, the command line read it again for macros,
    // so a title holding $m or `=1+1' reached the page expanded and a
    // `=filewrite(...)' in one ran (measured 24sep2026;
    // test_json_escaping.cscript JSE-58).  layout(), link() and
    // filterposition() are proven to hold neither before this point, and
    // theme() to be one of its six names.
    // In a block, as the one-line `if exp command' expands its command a
    // second time (see _dash_kpi's fmt()).
    local _flen : length local filter
    if `_flen' > 0 {
        _dash_json_str `"`macval(filter)'"' filter_json
    }

    // Escape build-level title and subtitle for JSON safety
    _dash_json_str `"`macval(title)'"'    _title_esc
    _dash_json_str `"`macval(subtitle)'"' _subtitle_esc
    // Escape tabs string for JSON embedding
    _dash_json_str `"`macval(tabs)'"' _tabs_esc
    // Carry the session confidence level so the renderer does not have to
    // assume 95.  A per-plot level() overrides it.
    local _dash_lvl = c(level)
    // c(dp) before the font query: read inside it, it gave "period"
    // under set dp comma (measured 16oct2026).
    local _dash_dp = c(dp)
    _dash_graph_set_fonts _dash_gsf
    // The session's own scheme.  A Stata user has already chosen how their
    // graphs should look; without this dash was the one command in the
    // session that ignored it.  An explicit scheme() or theme() still wins --
    // the renderer applies them in that order.
    local _dash_sess_scheme = c(scheme)
    // scheme() may be a .scheme file of the working directory, whose name
    // is the user's text: through macval() as well (JSE-58).
    _dash_json_str `"`macval(scheme)'"'    _scheme_esc
    _dash_json_str `"`_dash_sess_scheme'"' _sess_scheme_esc
    _dash_scheme_dirs
    // theme() was the one user string on the master-spec line that went in
    // raw while every other went through _dash_json_str.  Measured:
    // theme("C:\temp\x"), theme("a\q"), theme("a\") and a theme()
    // containing a double quote each gave r(7102) and a Python
    // JSONDecodeError traceback, with no message from dash; theme("a\b")
    // gave rc 0 and silently delivered a BACKSPACE, because \b happens to
    // be a valid JSON escape.  The same values in scheme() were all fine.
    _dash_json_str `"`theme'"'             _theme_esc
    // layout() went in raw too, on the belief that its check had refused
    // any such value.  The check reads only the START of the value (bs...,
    // or name:r,c...), so layout("bs\") passed it and its backslash escaped
    // the closing quote of the JSON string: measured 23sep2026, r(7102) and
    // a JSONDecodeError traceback (P20-17).  link() and filterposition()
    // are proven to be registry names and top or left before this line,
    // and are escaped all the same, so no value on it goes in raw.
    _dash_json_str `"`layout'"'            _layout_esc
    _dash_json_str `"`link'"'              _link_esc
    _dash_json_str `"`filterposition'"'    _fpos_esc
    // csv (WP-21): offer a download of the rows the filters leave.  Opt-in,
    // because it hands any viewer every row of every variable the dashboard
    // uses -- a served dashboard otherwise sends the browser only what it
    // plots.  A flag, so only "1" or "0" reaches the spec.
    local _csv_flag = cond("`csv'" != "", "1", "0")
    // The final } is written by _dash_fn_spec_tail, after the function
    // points (WP-29 P0.6).
    // WP-31 D15: Stata's own #N ticks, when the export asked for any.
    local _dash_st_bo ""
    if `: length local _dash_st_json' local _dash_st_bo `","stata_ticks":`_dash_st_json'"'
    // The split columns' map (WP-33 33-07): only when a variable was split.
    local _dash_fcols_bo ""
    if `"`macval(_dash_fcols_map)'"' != "{}" local _dash_fcols_bo `","frame_cols":`macval(_dash_fcols_map)'"'
    if `_dash_fr_multi' {
        mata: _dash_frame_set("")
        mata: _dash_frame_set_all(0)
    }
    local master_json `"{"graphs":[`graphs_json'],"kpis":[`kpis_json']`_im_part',"_dash_prefix":"`_dash_rp'","build_options":{"layout":"`_layout_esc'","link":"`_link_esc'","filter":"`filter_json'","theme":"`_theme_esc'","scheme":"`_scheme_esc'","session_scheme":"`_sess_scheme_esc'","scheme_dirs":`macval(_dash_sdirs)',"title":"`_title_esc'","subtitle":"`_subtitle_esc'","registry":"`registry'","tabs":"`_tabs_esc'","filter_position":"`_fpos_esc'","csv":"`_csv_flag'","level":"`_dash_lvl'","dp":"`_dash_dp'","adoarchive":"`c(adoarchive)'"`_dash_gsf',"formats":`_dash_fmt_json'`_dash_st_bo'`_dash_bcal_json',"limits":`_dash_lim_json'`_ds_json'`macval(_dts_json)'`_dash_fcols_bo'`_dash_brush_json'}"'

    // Written from Python, 0600 and never through a link (WP-29 P0.12b;
    // see _dash_render_immediate's spec writer).  Callers hand the path:
    // _dash_build and _dash_serve their run folder's spec.json, a test seam
    // its own file; so this opens no run and prints no note.  No error
    // branch: a refusal or an OSError ends the python: line, r(7102).
    _dash_require_python
    _dash_xm_load
    python: import sys
    python: from sfi import Macro as _dash_M
    python: _dash_xm = sys.modules["_dash_render_export"]
    // WP-31 E10 (A24): the style rows, as _dash_render_immediate embeds them.
    python: _dash_wsp = _dash_xm._dash_tmp_write_text(_dash_M.getLocal("specpath"), _dash_xm._dash_embed_style_rows(_dash_M.getLocal("master_json")))
    mata: _dash_fn_spec_tail(st_local("specpath"), st_local("_fp_names"), "")

    return local layout          `"`layout'"'
    return local filterposition  `"`filterposition'"'
    return local n_graphs        = `n_graphs'
    return local n_kpis          = `n_kpis'
    return local vars            `"`all_vars'"'
end


program define _dash_build
    version 19
    // WP-30 P1.28a: a path left by a command interrupted between its write
    // and its result must never reach a later command's r().
    capture macro drop dash__rfile

    // Rule 16: text reaching the spec must be well-formed UTF-8 BEFORE it
    // leaves Stata.  The gate was applied at exactly one entry point --
    // _dash_plot -- so KPI titles, build titles and subtitles, tabs() and
    // filter labels had no gate at all, and a malformed sequence in any of
    // them went straight to Python.
    mata: _dash_check_utf8(strtrim(st_local("0")))

    // Pre-extract ALL filter() options from `0' before -syntax- runs.
    // Stata's -syntax- only accepts one option of a given name; using two
    // filter() options (as in full_dashboard.do) would trigger an error.
    // _dash_extract_filters() scans `0', removes every filter(...) group,
    // joins their contents with " || ", and stores them in `_filter_parts'.
    // The cleaned command is stored in `_cmd_nofilter' and assigned back to
    // `0' so that -syntax- sees only the remaining options.  Both by copy:
    // local 0 `"`_cmd_nofilter'"' read the whole command again for macros,
    // so link(\$m), filterposition(\$m) and saving(\$m/x.html) were taken
    // for whatever $m held and a `=filewrite(...)' in a title ran, and local
    // filter `"`_filter_parts'"' drew a label holding $m as what $m held
    // (measured 24sep2026; test_json_escaping.cscript JSE-58).
    mata: _dash_extract_filters("_filter_parts", "_cmd_nofilter")
    local filter : copy local _filter_parts
    local 0      : copy local _cmd_nofilter
    // WP-31 H2l: two or more link() copies, one link group each, joined
    // with " || " (_dash_extract_links); handed on as one link().
    mata: _dash_extract_links("_link_parts", "_cmd_nolink")
    local _lkparts : length local _link_parts
    if `_lkparts' > 0 local 0 : copy local _cmd_nolink

    syntax [, ///
        SAVing(string asis)     ///
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
        CSV                     ///
        BRush(string)           ///
    ]
    if `_lkparts' > 0 local link : copy local _link_parts

    // ---- check registry is not empty ----
    if "${dash_graph_registry}" == "" {
        display as error "dash build: no graphs registered. Define graphs with name() before running dash build."
        exit(198)
    }

    // ---- validate saving() ----
    // Measured by its length, never read inside quotes before the validator
    // has seen it: `if "`saving'" == ""' ended its quotes at a double quote
    // in the path, r(132) "too few quotes", on both routes, and the
    // validator's "disallowed characters" was never reached (measured
    // 24sep2026; test_path_validation.cscript PV-21).
    local _svl : length local saving
    if `_svl' == 0 {
        display as error "dash build: saving() is required."
        exit(198)
    }
    // WP-30 P1.27: one grammar, twoway's, shared with the one-line form
    // (_dash_saving_parse), read from the text as typed (SAVing(string
    // asis): syntax's string form drops every pair of quotes).  The whole
    // text, ", replace" and all, was validated as the path, so
    // saving(b1.html, replace) was refused "must end in .html (got:
    // b1.html, replace)" and saving(b2) was refused where the one-line form
    // writes b2.html (measured).  .html (.py with server) is appended and a
    // .gph suffix replaced, as on the one-line form; asis is accepted and
    // has no effect.
    local _sv_ext = cond("`server'" != "", "py", "html")
    mata: _dash_saving_parse(st_local("saving"), st_local("_sv_ext"))
    if "`_sv_replace'" != "" local replace "replace"
    local saving : copy local _sv_file
    // The one validator for both branches; the server branch used to check
    // the extension and nothing else (PV-20; ROADMAP AC-08.4).  The path
    // goes to it as written, through macval(): a saving(\$m/x.html) was
    // read again for macros and written wherever $m pointed, where the
    // validator refuses a $ (JSE-58).
    _dash_validate_path `"`macval(saving)'"' "`_sv_ext'"
    local saving `"`_dash_vpath'"'
    if "`_sv_gph'" == "1" {
        local _sv_what = cond("`server'" != "", "a server app", "HTML")
        mata: _dash_say("txt", "dash build: saving() writes " + st_local("_sv_what") + ", not a Stata .gph; using ", st_local("saving"), "")
    }
    // WP-30 P1.28a: a suffix graph export writes is replaced too.
    if "`_sv_img'" != "" {
        mata: _dash_note("dash build: saving() writes " + (st_local("server") != "" ? "a server app" : "HTML") + ", not a ." + st_local("_sv_img") + " image; using ", st_local("saving"), "")
    }
    // Before the file is looked for: a directory that does not exist is
    // not a file that "already exists" (JSE-52).
    _dash_saving_dir `"`saving'"'

    // An existing file without replace, r(198), and a directory in the
    // file's place with it, r(608): _dash_saving_clobber, shared with the
    // one-line form.  The path is shown as written (P20-08).
    _dash_saving_clobber `"`saving'"' "`replace'" "dash build"

    // ---- validate, collect, serialize and assemble ----
    //
    // Shared with `dash serve', which used to do all of this itself with
    // the build options hardcoded to blanks.  The spec and data go in this
    // command's private run folder (WP-29 P0.12b), opened here and removed
    // after the render; r() is read on the very next lines (A12).  It
    // prints the command's one note, if any location is not private.
    //
    // `0' is the command's own option string with the filter() groups
    // already removed by _dash_extract_filters, so it is forwarded as
    // written rather than reassembled option by option -- reassembling
    // would expand the user's title() and label() text a second time.
    _dash_tmp_open
    local _dash_run        `"`r(rundir)'"'
    local master_json_path `"`r(spec)'"'
    local data_json_path   `"`r(data)'"'

    // -syntax- leaves `0' as it found it, which means it still carries the
    // leading comma.  Forwarding it after options of our own produced two
    // commas on one line, and everything after the second was read as a
    // positional argument: `invalid 'saving''.  `: subinstr local' replaces
    // the FIRST occurrence unless told otherwise, which is the leading
    // comma.  Both extended functions work on the macro's VALUE, so neither
    // expands the user's title() or label() text a second time.
    local _fwd_opts : copy local 0
    local _fwd_opts : subinstr local _fwd_opts "," ""
    if `_lkparts' > 0 local _fwd_opts `"`macval(_fwd_opts)' link(`macval(link)')"'

    // Everything is handed on as the user wrote it: the options through
    // macval(), so the line is not read again for macros, and filter() as
    // filter(<its text>), which _dash_prepare_spec takes out again with
    // the same scanner.  It went in filter(`"..."'), and a group holding "'
    // closed that compound quote: label("'90s") was lost, and label("')
    // csv title(pwned) subtitle(") put csv and title(pwned) on this line
    // (measured 24sep2026; test_json_escaping.cscript JSE-57).
    _dash_prepare_spec, cmdname("dash build") ///
        specpath("`master_json_path'") datapath("`data_json_path'") ///
        filter(`macval(filter)') `macval(_fwd_opts)'

    // ---- remember these for a later dash serve ----
    //
    // dash.sthlp documents building a dashboard and then serving it live
    // with a bare `dash serve, port()'.  That only means anything if the
    // options survive the first command, so they are recorded here and
    // `dash serve' inherits any the user does not restate.
    //
    // The user's text is recorded by value, from Mata: global ...
    // `"`title'"' read it again for macros, so a title holding $m or
    // `=1+1' was recorded expanded, and a `=filewrite(...)' in one ran
    // (measured 24sep2026; test_json_escaping.cscript JSE-58).  layout()
    // and filterposition() come back from _dash_prepare_spec validated.
    global dash_opts_layout         `"`r(layout)'"'
    global dash_opts_filterposition `"`r(filterposition)'"'
    global dash_opts_csv            "`csv'"
    foreach _bo in title subtitle link theme scheme tabs filter brush {
        mata: st_global("dash_opts_" + st_local("_bo"), st_local(st_local("_bo")))
    }

    // ---- Locate dash_render.py ----
    _dash_find_render
    local render_py `"`r(fn)'"'

    local render_mode "standalone"
    if "`server'" != "" local render_mode "server"

    // ---- Invoke Python renderer via helper ----
    // (python:...end must be in a dedicated program; see _dash_do_render)
    _dash_do_render, spec("`master_json_path'") data("`data_json_path'") ///
        output("`saving'") renderpy("`render_py'") mode("`render_mode'")
    _dash_tmp_close, dir(`"`_dash_run'"')

    if "`server'" != "" {
        mata: _dash_say("txt", "dash build: server app written to ", st_local("saving"), "")
        // Point at the app's OWN launcher, not `bokeh serve'.  Both work for
        // the dashboard now, but `bokeh serve' owns its Tornado application
        // and gives an app script no supported way to register a route, so
        // the /health endpoint project rule 17 asks for exists only when the
        // app serves itself.  Running it directly also honours --port and
        // the websocket origins, and opens no browser unless asked.
        // Single-quoted on a Mac and Unix, so a pasted line runs the file it
        // names (double quotes left ! to history expansion); on Windows the
        // line says when cmd.exe would expand % or ! (WP-30 P1.27).
        local _lh_os = cond("`c(os)'" == "Windows", "Windows", "Unix")
        mata: _dash_say("txt", "  To launch: python ", _dash_launch_quote(st_local("saving"), st_local("_lh_os")), "")
        mata: st_local("_lh_w", _dash_launch_warn(st_local("saving"), st_local("_lh_os")))
        if `: length local _lh_w' mata: _dash_say("txt", "", st_local("_lh_w"), "")
        // WP-29 P0.12a: the served dashboard opens only through its key.
        display as text `"  Access:    the app makes a new key for each launch unless DASH_SERVE_TOKEN gives one, writes the link that holds it to a file only you can read, and prints that file's path; only that link opens the dashboard"'
        display as text `"  Options:   --port N  --show  --timeout MINUTES  (--help lists them all)"'
        display as text `"  Limits:    --sessions-per-client N  --new-clients-per-minute N  --sessions-per-minute N  --max-sessions N  --idle-timeout MINUTES"'
    }
    else {
        mata: _dash_say("txt", "dash: dashboard saved to ", st_local("saving"), "")
        // nobrowser, or the global the certification runner sets once.
        // There was no way to suppress this at all: a suite that builds
        // twenty dashboards opened twenty browser tabs, and so did any
        // do-file run in batch.
        // A registered graph's nodraw keeps the window shut too, as the
        // help has always said it does -- the rule `dash serve' uses.
        _dash_dashboard_browser, `nobrowser'
        if r(open) {
            // The one opener, shared with the one-line form (see
            // _dash_open_page).
            _dash_open_page, path(`"`saving'"')
        }
    }
    // WP-30 P1.28a: the last statement -- the path written, absolute, for
    // r(filename) (_dash_result).
    mata: st_global("dash__rfile", _dash_abs_path(st_local("saving"), c("pwd"), c("os")))
end


// ================================================================
// _dash_serve_spec  — everything `dash serve' does except the launch.
//
// Separated so the option pass-through can be certified without a
// certification script starting a server, which it must never do.
// test_serve_options.cscript calls this directly and reads the master
// JSON it writes.
//
// The caller owns the two paths: _dash_serve hands those of its private
// run folder (WP-29 P0.12b), which outlives this program, so the app can
// be built from them.
// ================================================================
program define _dash_serve_spec, rclass
    version 19

    // Rule 16: text reaching the spec must be well-formed UTF-8 BEFORE it
    // leaves Stata.  The gate was applied at exactly one entry point --
    // _dash_plot -- so KPI titles, build titles and subtitles, tabs() and
    // filter labels had no gate at all, and a malformed sequence in any of
    // them went straight to Python.
    mata: _dash_check_utf8(strtrim(st_local("0")))

    // Pre-extract every filter() group before -syntax- runs, exactly as
    // `dash build' does: -syntax- accepts one option of a given name, and
    // a dashboard may legitimately have several filters.  Both by copy, as
    // dash build takes them (see there; JSE-58).
    mata: _dash_extract_filters("_filter_parts", "_cmd_nofilter")
    local filter : copy local _filter_parts
    local 0      : copy local _cmd_nofilter

    // Only the options `dash serve' owns are named here.  The trailing *
    // collects every build option into `options' exactly as the user
    // wrote it, so this program never has to enumerate the build surface
    // -- which is how the two copies drifted apart in the first place.
    syntax [, ///
        SPECpath(string)    ///
        DATApath(string)    ///
        PORT(string)        ///
        NOBRowser           ///
        TIMEOUT(string)     ///
        MAXSESSIONS(string) ///
        IDLETIMEOUT(string) ///
        *                   ///
    ]

    // port() and timeout() go into the one-line python: statement that
    // launches the server, so each must be digits and nothing else.  They
    // are tested byte by byte (_dash_is_digits) and never by a regular
    // expression: StataNow's regexm() matches "^[0-9]+$" against "7" +
    // char(10), so timeout(7<LF>) was accepted and handed a newline to that
    // statement (P20-14).  timeout() is at most nine digits: a 400-digit
    // timeout() was accepted, and the launcher, multiplying it by 60 into a
    // float, died with OverflowError after binding its port (P20-19).  A
    // port of more than nine digits is out of range without being read.
    // Values are tested by length, never expanded into an expression, and
    // a refused one is echoed through _dash_say, as written.
    local _plen : length local port
    if `_plen' == 0 local port "5006"
    local _tlen : length local timeout
    if `_tlen' == 0 local timeout "0"

    mata: st_local("_pdig", strofreal(_dash_is_digits(st_local("port"), .)))
    if !`_pdig' {
        mata: _dash_say("err", "dash serve: port() must be a positive integer (got: ", st_local("port"), ")")
        exit(198)
    }
    local _plen : length local port
    local port_int = .
    if `_plen' <= 9 local port_int = real("`port'")
    if `port_int' < 1024 | `port_int' > 65535 {
        mata: _dash_say("err", "dash serve: port() must be between 1024 and 65535 (got: ", st_local("port"), ")")
        exit(198)
    }
    mata: st_local("_tdig", strofreal(_dash_is_digits(st_local("timeout"), 9)))
    if !`_tdig' {
        mata: _dash_say("err", "dash serve: timeout() must be a non-negative integer in minutes, at most nine digits (got: ", st_local("timeout"), ")")
        exit(198)
    }
    // Written as a plain integer: 007 goes to the launcher as 7.
    local timeout = strofreal(real("`timeout'"), "%12.0f")

    // WP-30 P1.31a: the open-session cap and the idle close, by the same
    // byte-level rules as port() and timeout(): digits only, bounded
    // length, never a regular expression or an expression; empty when
    // not given, so the app keeps its own defaults (20 and 60).
    // Threat: memory exhaustion of the served app by open sessions.
    if `: length local maxsessions' {
        mata: st_local("_mdig", strofreal(_dash_is_digits(st_local("maxsessions"), 7)))
        local _mval = .
        if `_mdig' local _mval = real("`maxsessions'")
        if !`_mdig' | `_mval' < 1 | `_mval' > 1000000 {
            mata: _dash_say("err", "dash serve: maxsessions() must be an integer from 1 to 1,000,000 (got: ", st_local("maxsessions"), ")")
            exit(198)
        }
        local maxsessions = strofreal(`_mval', "%12.0f")
    }
    if `: length local idletimeout' {
        mata: st_local("_idig", strofreal(_dash_is_digits(st_local("idletimeout"), 6)))
        local _ival = .
        if `_idig' local _ival = real("`idletimeout'")
        if !`_idig' | `_ival' > 525600 {
            mata: _dash_say("err", "dash serve: idletimeout() must be a whole number of minutes from 0 to 525600 (got: ", st_local("idletimeout"), ")")
            exit(198)
        }
        local idletimeout = strofreal(`_ival', "%12.0f")
    }

    if `"`specpath'"' == "" | `"`datapath'"' == "" {
        display as error "dash serve: internal error — specpath() and datapath() are required."
        exit(198)
    }

    // inherit: reuse the options of a `dash build' earlier in this session
    // for anything not restated here.  dash.sthlp documents exactly that
    // sequence, and without this the served dashboard silently lost the
    // filter the documented example builds it with.  Handed on as written,
    // as dash build hands them on (see there): through macval(), and
    // filter(<its text>), which label("') csv title(pwned) subtitle(")
    // could close as filter(`"..."') (measured 24sep2026;
    // test_json_escaping.cscript JSE-57, JSE-58).
    _dash_prepare_spec, cmdname("dash serve") inherit ///
        specpath(`"`specpath'"') datapath(`"`datapath'"') ///
        filter(`macval(filter)') `macval(options)'

    return local master_json_path `"`specpath'"'
    return local data_json_path   `"`datapath'"'
    return local port             "`port_int'"
    return local timeout          "`timeout'"
    return local nobrowser        "`nobrowser'"
    return local maxsessions      "`maxsessions'"
    return local idletimeout      "`idletimeout'"
    return local layout           `"`r(layout)'"'
    return local filterposition   `"`r(filterposition)'"'
end


// ================================================================
// _dash_serve  — launch Bokeh Server for live interactive mode
// ================================================================
program define _dash_serve
    version 19

    // Rule 16: text reaching the spec must be well-formed UTF-8 BEFORE it
    // leaves Stata.  The gate was applied at exactly one entry point --
    // _dash_plot -- so KPI titles, build titles and subtitles, tabs() and
    // filter labels had no gate at all, and a malformed sequence in any of
    // them went straight to Python.
    mata: _dash_check_utf8(strtrim(st_local("0")))

    // The private run folder (WP-29 P0.12b): spec, data and the app go in
    // c(tmpdir)dash-<uid>/run-<pid>-<random>/ (0700, files 0600), removed
    // when the command ends.  Opened before _dash_serve_spec, whose rclass
    // results would clobber r() (A12).  The command's one note, if any
    // location is not private, prints here, before the announcement.
    _dash_tmp_open
    local _dash_run        `"`r(rundir)'"'
    local master_json_path `"`r(spec)'"'
    local data_json_path   `"`r(data)'"'
    local serve_app_path   `"`r(app)'"'

    // `0' still carries the leading comma -syntax- left on it, so forwarding
    // it after options of our own put TWO commas on one line and everything
    // past the second was read as a positional argument:
    //     . dash serve, port(5006)
    //     invalid 'port'
    //     r(198);
    // -- every option dash.sthlp documents for this command, including the
    // port(5006) example it gives.  Only the bare form ran.  _dash_build has
    // fixed exactly this at its own forwarding site for some time; this path
    // never got the same treatment.  `: copy local' and `: subinstr local'
    // both work on the macro's VALUE, so neither expands the user's title()
    // or label() text a second time, and subinstr replaces only the FIRST
    // occurrence, which is the leading comma.
    local _srv_fwd : copy local 0
    local _srv_fwd : subinstr local _srv_fwd "," ""

    // Through macval(), so the line is not read again for macros: a
    // title(\$m) was served as whatever $m held (measured 24sep2026;
    // test_json_escaping.cscript JSE-58).
    _dash_serve_spec, specpath("`master_json_path'") datapath("`data_json_path'") `macval(_srv_fwd)'

    local port_int   "`r(port)'"
    local timeout    "`r(timeout)'"
    local _srv_maxs  "`r(maxsessions)'"
    local _srv_idle  "`r(idletimeout)'"
    // The browser, by the rule `dash build' uses: its nobrowser option,
    // the session's $dash_nobrowser, or a registered graph's nodraw keeps
    // it shut.  This read the option alone (test_serve_browser.cscript).
    local _srv_nobr "`r(nobrowser)'"
    _dash_dashboard_browser, `_srv_nobr'
    local no_browser_flag "`r(flag)'"

    // ---- Locate dash_render.py ----
    // Before the announcement below, and before `python:'.  `dash serve'
    // used to print "starting Bokeh Server on port NNNN. Stata is blocked
    // until the server stops" and only then discover it could not run.
    _dash_require_python
    _dash_find_render
    local render_py `"`r(fn)'"'
    // The module that runs the renderer (_dash_run_renderer; see
    // _dash_do_render), also before the announcement.
    _dash_xm_load

    // The generated Bokeh Server app is app.py in the private run folder
    // opened above (WP-29 P0.12b): written 0600 by the renderer, which
    // erases the spec and data once it is written (they are embedded in
    // it), and removed with the folder when the command ends.  It used to
    // be a Stata tempfile, 0644 under umask 022 and 0664 under 002 (D5,
    // U2) -- and before that an unregistered .py that Stata never erased
    // (142 orphans, 18 MB, measured).  The launcher starts it from the
    // bytes it verified, never by name (R-9).

    // Escape paths for safe Python string literal interpolation (see _dash_do_render).
    _dash_json_str `"`master_json_path'"' _py_master
    _dash_json_str `"`data_json_path'"'   _py_data
    _dash_json_str `"`serve_app_path'"'   _py_serve
    _dash_json_str `"`render_py'"'        _py_render

    // Break, not Ctrl+C: Ctrl+C is only console Stata's Break key, and GUI
    // users were told to press it (WP-29 P0.13 F4, F9c).
    display as text "dash serve: starting Bokeh Server on port `port_int'." ///
        "  Stata waits while it runs; press Break (Ctrl+C in console Stata) to stop it."

    // Single-line python: calls to avoid ado-path IndentationError (see _dash_do_render).
    python: import sys
    // --launch: `dash serve' is the path whose job IS to run a server.  The
    // renderer no longer starts one as a side effect of writing a file,
    // because `dash build, server' used that same entry point and was left
    // blocking forever with an orphaned server behind it.
    // WP-31 H7: argv saved, and put back after the run before any exit, as
    // _dash_do_render does.
    python: _dash_saved_argv = list(sys.argv)
    python: sys.argv = ["dash_render.py", "--spec", "`_py_master'", "--data", "`_py_data'", "--output", "`_py_serve'", "--mode", "server", "--launch", "--port", "`port_int'", "--timeout", "`timeout'"]
    if "`no_browser_flag'" != "" {
        python: sys.argv.append("--no-browser")
    }
    // WP-30 P1.31a: digits only, checked by _dash_serve_spec.
    if "`_srv_maxs'" != "" {
        python: sys.argv += ["--max-sessions", "`_srv_maxs'"]
    }
    if "`_srv_idle'" != "" {
        python: sys.argv += ["--idle-timeout", "`_srv_idle'"]
    }
    // GAPS2 F1: dash serve used to report success (rc 0) whatever the
    // launched app actually did -- a port already held by another program
    // failed only on the child's own process stderr, unseen here, after
    // about 1.7 seconds.  _dash_srv_rep is a dict shared by reference with
    // the executed module (a `python:' line inside an ado program takes
    // one statement per line and no compound statement, so a try/except
    // cannot be written here, and an exception escaping the run is
    // r(7102) plus a traceback -- the opposite of a clean message).
    // dash_render.py's __main__ writes _dash_launch_app's failure text
    // into this dict instead of raising, when the dict is present; it
    // reaches the run as run_path's init_globals did.
    python: _dash_srv_rep = {}
    python: _dash_xm = sys.modules["_dash_render_export"]
    // Assign the result.  A single-line `python:' echoes the value of the
    // expression, and the run returns the module globals dict, so this
    // line used to dump dash_render.py's whole namespace into the Stata log
    // on every render -- roughly 10 KB of noise per command.
    capture noisily python: _dash_serve_ns = _dash_xm._dash_run_renderer("`_py_render'", {"_dash_launch_report": _dash_srv_rep})
    local _rrc = _rc
    python: sys.argv = _dash_saved_argv
    python: [globals().pop(_n, None) for _n in ('_dash_serve_ns', '_dash_saved_argv', '_dash_xm')].clear()
    if `_rrc' exit `_rrc'
    python: from sfi import Macro as _dash_srv_M
    python: _dash_srv_M.setLocal("_srv_err", str(_dash_srv_rep.get("error", ""))[:4096])
    // WP-29 P0.13 F4: Break (or Ctrl+C) stopped the server; the launcher
    // put "interrupted" in the box rather than raise, so it ends here as
    // any command interrupted by Break does: --Break--, r(1).
    python: _dash_srv_M.setLocal("_srv_brk", "1" if _dash_srv_rep.get("interrupted") else "")
    if `: length local _srv_err' {
        _dash_tmp_close, dir(`"`_dash_run'"')
        mata: _dash_say("err", "dash serve: ", st_local("_srv_err"), "")
        exit 198
    }
    _dash_tmp_close, dir(`"`_dash_run'"')
    if "`_srv_brk'" == "1" error 1
end
